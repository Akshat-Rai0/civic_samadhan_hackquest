# Roadmap

Phased for a prototype build — each phase should produce something demoable, not just internal plumbing.

## Phase 0 — Foundations
- [ ] Set up Postgres + PostGIS
- [ ] Core schema: `users`, `departments`, `officers`, `issue_clusters`, `issue_images`
- [ ] Mock-Aadhaar login flow (fake OTP screen, session creation) — stated explicitly in the UI as simulated
- [ ] Basic FastAPI backend skeleton + async task queue wired up (even with a no-op job first)

**Demoable at end of phase**: a user can log in and the DB has real tables.

## Phase 1 — Ingest pipeline (no AI yet)
- [ ] Photo upload endpoint — upload UI has no location field; geotagging happens entirely server-side
- [ ] EXIF GPS extraction + device-geolocation fallback captured client-side at upload time (silent, not shown to the citizen)
- [ ] pHash computation on upload
- [ ] Cluster-matching logic using pHash + GPS radius only (issue-type check added in Phase 2 once Moondream exists)
- [ ] Manual "drop a pin" fallback flow if no geo signal is available at all

**Demoable**: uploading the same photo twice from nearby locations correctly increments one cluster's affected-count instead of creating two issues.

## Phase 2 — Vision + Agent 1 (Classification + Geo-Routing)
- [ ] Stand up local Moondream inference (confirm it runs at acceptable latency on your hardware — this is a real risk to test early, not assume)
- [ ] Wire Moondream output into the clustering check (issue-type match)
- [ ] Citizen-facing confirmation screen showing Moondream's detected issues
- [ ] Build Agent 1's tools: `classify_issue`, `extract_geotag`, `reverse_geocode`, `match_authority`, `build_issue_object`
- [ ] Severity rubric table (base severity per issue type) and priority score calculation, seeded by `severity_hint`

**Demoable**: a full citizen flow — upload → detect → confirm → Agent 1 classifies and routes → lands in the right department queue with a real priority score.

## Phase 3 — Admin dashboard + Agent 3 (Escalation)
- [ ] Queue view sorted by priority score, with a days-pending / escalation-tier column
- [ ] Manual officer assignment from department pool
- [ ] Heatmap (raw density) using PostGIS + a mapping library
- [ ] Citizen-facing status tracker reading the same status field
- [ ] Build Agent 3's tools: `check_sla_timer`, `escalate_ticket`, `notify_higher_authority`, `log_escalation`, run on a scheduled job (e.g. hourly) against all open tickets

**Demoable**: an admin can see a prioritized, mapped backlog with visible days-pending; assign officers; and watch a deliberately-aged test ticket auto-escalate and log the escalation.

## Phase 4 — Agent 2 (Communication) + MCP Q&A layer
- [ ] Build Agent 2's tools: `detect_status_change`, `translate_message`, `send_notification`; wire it to fire on every status write
- [ ] Citizen Track tab shows the resulting notification log, not just the status stepper
- [ ] Build the MCP server with `list_issues`, `get_issue`, `summarize_backlog`, `get_escalation_status` (read-only tools first)
- [ ] Connect Claude to it, verify Q&A works against real data
- [ ] Add `draft_contractor_email` (still read/compose only, no send)
- [ ] Add the admin-approval UI step, then wire `send_contractor_email` behind it
- [ ] Audit logging on every write path, including agent-triggered ones

**Demoable**: a citizen sees a live notification the moment an admin changes their ticket's status; an admin asks the MCP agent a real backlog question and gets a correct, data-grounded answer; a contractor email is drafted by the agent and only goes out after an explicit approve click.

## Phase 5 — Agent 4 (Verification) + completion loop
- [ ] Email-parsing job for contractor replies (attachment extraction)
- [ ] Build Agent 4's tools: `compare_images`, `check_citizen_confirmation`, `reopen_ticket`, `close_ticket`
- [ ] Run GPS/timestamp checks + `compare_images` on completion photos as a first-pass filter
- [ ] Citizen confirmation UI (confirm / dispute) feeding `check_citizen_confirmation`, triggered by Agent 2's notification
- [ ] Wire the reopen path — a disputed or failed verification sends the ticket back into the department queue, not into limbo
- [ ] `get_completion_status` MCP tool for the agent's "completed/pending" reporting

**Demoable**: the full loop — citizen reports → admin dispatches → contractor replies with photo → Agent 4 verifies and Agent 2 notifies the citizen → citizen confirms or disputes → ticket closes or reopens accordingly.

## Explicitly deferred (not phased in — post-prototype)
- Real Aadhaar/UIDAI integration
- Contractor portal (replacing email-only contact)
- Automatic officer-level assignment
- Population-normalized heatmap
- Anti-gaming measures beyond one-account-per-login (e.g. detecting coordinated fake reports)
- Multi-tier escalation beyond a fixed chain (e.g. dynamic routing based on department head availability)

## Suggested build order rationale
Ingest-before-AI (Phase 1 before 2) lets you validate the clustering logic — the load-bearing piece the rest of the system depends on for accurate affected-counts and priority — against real test photos before adding model latency and inference cost on top. Admin dashboard (Phase 3) before the agent layer (Phase 4) ensures there's a real dashboard the agent's actions and audit log can be checked against, rather than trusting the agent's own reporting as the only view into what happened.
