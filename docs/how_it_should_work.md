# How It Should Work

## Agent overview

Four agents sit inside this pipeline, each scoped to one job with its own tools:

| Agent | Role | Where it acts |
|---|---|---|
| **Agent 1 — Classification + Geo-Routing** | Merges image caption + user text, geotags, routes to the correct authority | User system, at submission (A6→A8) |
| **Agent 2 — Communication** | Notifies the citizen whenever their ticket's status changes | User system, Track tab (A9) |
| **Agent 3 — Escalation** | Watches SLA timers, escalates overdue tickets | Admin system (B7) |
| **Agent 4 — Verification** | Confirms a claimed fix is real, reopens or closes the ticket | Admin + User system (B6) |

Full tool definitions for each are in system-wiring.md §6.

---

## Part A — User system

### A1. Login
- Citizen logs in via a mock Aadhaar-style flow: enters name/DOB/12-digit ID → fake OTP screen → session created.
- This creates (or matches) exactly one account per real person, which is what makes the affected-count in A4 trustworthy.

### A2. Upload
- Citizen photographs the issue and optionally types a short description.
- No location is shown or asked for on this screen — geotagging is handled entirely by Agent 1 downstream (A6), not by the citizen.

### A3. Duplicate detection & clustering (not discarding)
An uploaded image is compared against existing open issue clusters. It is added to an **existing cluster** (incrementing that cluster's affected-count) if **all three** hold:
1. Perceptual hash (pHash) distance to the cluster's reference image is below threshold, **or** the new image's Moondream issue-type matches the cluster **and** GPS is very close (handles same-issue-different-angle cases pHash alone would miss)
2. GPS coordinates (from Agent 1's `extract_geotag`) are within a small radius (~15–20m) of the cluster's location
3. The Moondream-detected issue type overlaps with the cluster's issue type

If all three don't hold, a **new cluster** is created instead. Every image added to a cluster is kept as an additional reference photo — nothing is discarded, only grouped.

### A4. Issue detection (Moondream)
- The unique/clustered image is run through a locally hosted Moondream model with the fixed system prompt: *"in the given image tell me all the issue that needs to be fixed by municipal corp."*
- Output: a list of detected issues in the image (the "caption" Agent 1 consumes next).

### A5. Confirmation (human-in-the-loop, citizen side)
- The citizen is shown Moondream's detected issue list and must click **"Yes, send this to the concerned authority"** before anything is submitted.
- This is a confirm-only step in v1 — the citizen can approve or decline, but cannot manually override which department it's routed to (that's Agent 1's job, next).

### A6. Agent 1 — Classification + Geo-Routing
Runs immediately after confirmation, before the ticket lands in any queue:
1. `classify_issue(text, caption)` — merges the user's typed description with Moondream's caption to produce `category`, `severity_hint`, `confidence`.
2. `extract_geotag(image_meta)` — pulls GPS from EXIF; if EXIF GPS is missing or invalid (common with forwarded images, screenshots, privacy-stripped photos), falls back to device geolocation captured silently at upload time. If neither is available, the citizen is prompted to drop a pin on a map before the ticket can proceed — geotagging is not optional, nothing downstream works without it, it's simply no longer a field the citizen fills in manually.
3. `reverse_geocode(lat, long)` — resolves coordinates to `postal_code`, `zone`.
4. `match_authority(postal_code, category)` — determines the correct `department_id`.
5. `build_issue_object()` — assembles the structured payload (category, severity_hint, confidence, geotag, zone, department_id, images, affected_count) that becomes the ticket.
- Officer-level assignment is still **not automatic** in v1 — Agent 1 routes to the department; a department admin manually assigns a specific officer from that department's pool.

### A7. Submission
- The structured issue object from Agent 1 is sent to that department's admin queue.

### A8. Status tracking + Agent 2 — Communication (citizen side)
- The citizen's Track tab shows current status (submitted → in review → assigned → in progress → pending confirmation → closed) **and** a running log of updates written by Agent 2:
  1. `detect_status_change(issue_id)` — polls/subscribes for any status change on the ticket.
  2. `translate_message(text, lang)` — renders the update in the citizen's preferred language.
  3. `send_notification(citizen_id, template, lang)` — delivers it (in-app log entry + push/SMS).
- When Agent 4 (Verification) determines a fix is likely real (B6), Agent 2 is what actually notifies the citizen and asks them to confirm.

---

## Part B — Admin system

### B1. Incoming queue
- New issues land in the relevant department's queue, already classified, geotagged, and clustered with an affected-count — all produced by Agent 1.

### B2. Priority scoring (rubric-based)
Priority is computed, not eyeballed:
```
priority_score = base_severity[issue_type] × affected_count_multiplier(affected_count)
```
- `base_severity` — a fixed lookup table per issue type (e.g. exposed wiring > open manhole > pothole > garbage pile), set by department policy. Agent 1's `severity_hint` seeds this but the table is the authority.
- `affected_count_multiplier` — grows with the cluster's affected-count, but should taper (e.g. diminishing returns past a threshold) so one extremely popular but minor issue doesn't outrank a rare but serious one.
- This score sorts the admin's queue and drives the heatmap intensity.

### B3. Officer assignment
- Admin manually assigns each issue to an officer from the department's pool, informed by the priority score and officer workload.

### B4. Heatmap
- Admin views a map showing raw complaint density (v1: not population-normalized) so they can see where issues are concentrating.

### B5. Agentic Q&A (MCP-connected)
- Admin can ask natural-language questions ("how many unresolved issues in ward 4 this week?", "summarize open issues by type") and the agent answers by querying the real issue database through MCP tools — not from memory or guesswork.

### B6. Contractor dispatch, completion, and Agent 4 — Verification
1. Admin (with agent help) drafts a batch email to relevant contractors listing assigned tasks.
2. **Admin explicitly approves before send** — the agent never sends mass email autonomously.
3. Contractor performs the fix and replies by email with a completion ("after") photo (no contractor portal in v1).
4. **Agent 4 — Verification** runs:
   1. `compare_images(before, after)` — produces `diff_score` and `object_delta` between the intake photo and the completion photo (does the originally-flagged object/issue still appear present?).
   2. `check_citizen_confirmation(ticket_id)` — reads whether the citizen (notified by Agent 2) has responded confirmed / pending / disputed.
   3. If the image comparison and GPS/timestamp checks pass **and** the citizen confirms → `close_ticket()`.
   4. If the citizen disputes the fix, or the image comparison shows the issue is still present → `reopen_ticket(reason)`, sending it back into the department queue with the dispute reason attached.
5. The admin still sees and can override Agent 4's close/reopen decision — it is not a fully silent auto-close, but it is what drives the recommendation instead of the admin parsing the raw email themselves.
6. Agent 2 delivers the final "your issue has been marked resolved — please confirm" and "your issue was reopened" notifications either way.

### B7. Agent 3 — Escalation
Runs continuously against every open ticket, not just at intake:
1. `check_sla_timer(issue_id)` — computes time remaining before the ticket breaches its SLA (SLA length scaled by severity — high-severity tickets get a shorter window).
2. On breach: `escalate_ticket(issue_id, reason)` — moves the ticket to the next tier (e.g. officer → department head → municipal commissioner) and returns the `new_tier`.
3. `notify_higher_authority(department_id)` — alerts the next tier up that an escalated ticket now needs attention.
4. `log_escalation(issue_id, reason)` — writes an audit trail entry so every escalation is traceable to a reason and timestamp, not silent.
- The admin dashboard's queue shows days-pending and current tier per ticket (driven by this agent) so escalation risk is visible before it actually fires, not just after.
