# System Wiring

## 1. High-level component map

```
┌───────────────────────────┐        ┌────────────────────────────┐
│         USER SIDE          │        │          ADMIN SIDE          │
│                             │        │                              │
│  Mock-Aadhaar login         │        │  Admin dashboard (web)       │
│  Upload UI (photo + text,   │        │   - queue, priority sort,    │
│   no location field)        │        │     days-pending column      │
│  Confirmation screen        │        │   - heatmap                 │
│  Status tracker + agent     │        │   - officer assignment       │
│   update log                │        │                              │
└──────────────┬──────────────┘        └───────────────┬──────────────┘
               │ POST /issues                            │ reads/writes
               ▼                                          ▼
        ┌─────────────────────────────────────────────────────────┐
        │                    BACKEND API / SERVICES                │
        │                                                            │
        │  Ingest pipeline (async job queue):                      │
        │   1. pHash compute                                        │
        │   2. Cluster match (pHash + GPS + issue-type)              │
        │   3. Moondream inference (local model)                    │
        │   4. Citizen confirmation                                  │
        │   5. → Agent 1 (Classification + Geo-Routing)              │
        │                                                            │
        │  Contractor completion pipeline:                          │
        │   - Parse email attachment → Agent 4 (Verification)        │
        └───────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │       Issue database            │
                     │  (single source of truth for    │
                     │   citizens, admin dashboard,     │
                     │   all four agents, and the       │
                     │   MCP server below)              │
                     └───────────────┬───────────────────┘
                                     │ read/write via defined tools
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
     ┌─────────────────┐   ┌─────────────────┐    ┌─────────────────┐
     │ Agent 2           │   │ Agent 3           │    │ Agent 4           │
     │ Communication      │   │ Escalation         │    │ Verification       │
     │ (citizen updates)  │   │ (SLA watchdog)     │    │ (post-resolution)  │
     └─────────────────┘   └─────────────────┘    └─────────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │          MCP server              │
                     │  Exposes scoped tools (below)    │
                     └───────────────┬───────────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │     Claude (admin's chat client) │
                     │  Q&A + drafts contractor email    │
                     │  (HITL: admin approves send)      │
                     └───────────────────────────────────┘
```

Agent 1 (Classification + Geo-Routing) runs inline in the ingest pipeline, right after citizen confirmation. Agents 2, 3, and 4 run continuously/event-driven against the issue database independently of any single request — Agent 2 on every status change, Agent 3 on a timer against every open ticket, Agent 4 when a completion photo arrives.

## 2. Tech stack (prototype-appropriate choices)

| Layer | Choice | Why |
|---|---|---|
| Perceptual hashing | `imagehash` (Python, pHash) | Simple, well-tested, no GPU needed |
| Vision model | Moondream (local, quantized) | Small enough to self-host, fast enough for near-real-time inference |
| Classification (Agent 1) | Sentence-embedding similarity (e.g. a small sentence-transformer) between merged text + a category taxonomy | Cheap, explainable, no need for a large LLM here |
| Geocoding (Agent 1) | A reverse-geocoding API/local dataset mapping lat/long → postal code/zone | Needed to resolve `match_authority` |
| Translation (Agent 2) | A small multilingual translation model or hosted translation API | Keeps citizen notifications in their preferred language without a large LLM per message |
| Image diffing (Agent 4) | Structured Moondream re-inference on the after-photo + simple pixel/embedding diff for `object_delta` | Reuses the same model already running for intake, rather than a separate vision pipeline |
| Backend | Python (FastAPI) + async task queue (e.g. Celery/RQ) | Ingest pipeline and all four agents should run as background jobs, never inline with a blocking HTTP request |
| Database | PostgreSQL + PostGIS extension | PostGIS gives real geo-radius queries for clustering and the heatmap, instead of hand-rolled distance math |
| MCP server | Python `mcp[cli]` (FastMCP), `streamable-http` transport | Matches the earlier MCP walkthrough; lets Claude (or any MCP client) connect over HTTP |
| Admin frontend | Any standard SPA framework + a mapping library (e.g. Leaflet/Mapbox) for the heatmap | — |
| Scheduler (Agent 3) | Cron-style periodic job (e.g. Celery beat) running `check_sla_timer` across all open tickets | SLA watching needs to run continuously, not just react to events |

## 3. Data model (core tables, not exhaustive)

```
users          (id, mock_aadhaar_id, phone, preferred_lang, created_at)
issue_clusters (id, category, severity_hint, confidence, department_id, zone,
                postal_code, lat, lng, reference_image_id, affected_count,
                priority_score, sla_deadline, escalation_tier, status, created_at)
issue_images   (id, cluster_id, uploaded_by_user_id, image_url, phash,
                exif_lat, exif_lng, device_lat, device_lng, moondream_output,
                created_at)
departments    (id, name, parent_tier_id)
officers       (id, department_id, name, email, active)
assignments    (id, cluster_id, officer_id, assigned_at)
contractor_emails (id, cluster_id, contractor_email, sent_at, approved_by_admin_id)
completion_evidence (id, cluster_id, image_url, exif_lat, exif_lng, timestamp,
                      moondream_recheck_output, diff_score, object_delta,
                      passed_automated_checks, confirmed_by_admin_id)
citizen_confirmation (id, cluster_id, status, submitted_at)  -- confirmed / pending / disputed
citizen_feedback (id, cluster_id, satisfied_bool, submitted_at)
notifications  (id, cluster_id, citizen_id, template, lang, sent_at, status)
escalation_log (id, cluster_id, reason, from_tier, to_tier, notified_authority_id, logged_at)
```

`issue_clusters` is the entity the counter, priority score, heatmap, SLA deadline, and MCP tools all revolve around — clustering (A3 in how_it_should_work.md) writes to this table, not `issue_images` directly. `sla_deadline` and `escalation_tier` are what Agent 3 reads and updates; `citizen_confirmation` and `notifications` are Agent 2/4's tables.

## 4. MCP server — tool surface (admin-facing Q&A agent)

Exposed to the admin's Claude session, scoped to that admin's department (see §7 on auth):

| Tool | Type | Purpose |
|---|---|---|
| `list_issues(department, status, min_priority)` | read | Pull a filtered set of open issues |
| `get_issue(cluster_id)` | read | Full detail on one issue cluster, including image refs |
| `summarize_backlog(department)` | read | Aggregate counts/priority breakdown for Q&A |
| `draft_contractor_email(cluster_ids, contractor_email)` | read/compose | Generates a draft — does **not** send |
| `send_contractor_email(draft_id)` | write, requires admin approval flag | Only executes after the admin has clicked approve in the dashboard, not from a bare model decision |
| `get_completion_status(cluster_id)` | read | Returns Agent 4's verification result + parsed contractor-reply status, for the "report on completed/pending tasks" ask |
| `get_escalation_status(cluster_id)` | read | Returns Agent 3's current tier + days-pending for a ticket, for Q&A like "what's about to breach SLA" |

The write tool (`send_contractor_email`) is intentionally the only non-read tool on this list — everything else the agent can do is look things up and draft, never unilaterally act. See how_it_should_work.md B6 for the approval flow this maps to.

## 5. Agent architecture (the four pipeline agents)

These are distinct from the MCP Q&A agent above — they're background workers, not something the admin chats with directly, though their outputs (escalation tier, verification status) are readable through the MCP tools above.

### Agent 1 — Classification + Geo-Routing
Runs once per confirmed submission. Merges caption + user text, routes to the correct authority.
| Tool | Signature | Purpose |
|---|---|---|
| `classify_issue` | `(text, caption) → category, severity_hint, confidence` | Determine issue category and a starting severity estimate |
| `extract_geotag` | `(image_meta) → lat, long` | EXIF-first, device-location fallback, manual-pin last resort |
| `reverse_geocode` | `(lat, long) → postal_code, zone` | Resolve coordinates to an administrative zone |
| `match_authority` | `(postal_code, category) → department_id` | Determine which department owns this issue |
| `build_issue_object` | `() → structured payload` | Assembles the final ticket from the above outputs |

### Agent 2 — Communication
Event-driven off status changes; keeps the citizen informed without an admin having to manually message them.
| Tool | Signature | Purpose |
|---|---|---|
| `detect_status_change` | `(issue_id) → bool` | Fires when a ticket's status field changes |
| `translate_message` | `(text, lang) → translated_text` | Renders the update in the citizen's preferred language |
| `send_notification` | `(citizen_id, template, lang) → status` | Delivers the update (in-app log + push/SMS) |

### Agent 3 — Escalation
Runs on a schedule (e.g. hourly) against every open ticket, not just at intake.
| Tool | Signature | Purpose |
|---|---|---|
| `check_sla_timer` | `(issue_id) → time_remaining` | How long until this ticket breaches its SLA (SLA length scaled by severity) |
| `escalate_ticket` | `(issue_id, reason) → new_tier` | Moves an overdue ticket to the next authority tier |
| `notify_higher_authority` | `(department_id) → status` | Alerts the next tier up |
| `log_escalation` | `(issue_id, reason) → trace_entry` | Writes an auditable escalation record |

Days-pending and current tier from this agent are what populate the new "Escalation" column on the admin queue (§1 diagram, UI.html).

### Agent 4 — Verification (post-resolution)
Runs when a contractor's completion photo arrives; confirms the fix before the ticket can close.
| Tool | Signature | Purpose |
|---|---|---|
| `compare_images` | `(before, after) → diff_score, object_delta` | Does the originally-flagged issue still appear present in the after-photo? |
| `check_citizen_confirmation` | `(ticket_id) → confirmed/pending/disputed` | Has the citizen (notified via Agent 2) responded? |
| `reopen_ticket` | `(reason) → status` | Sends the ticket back into the department queue with a dispute/failure reason |
| `close_ticket` | `() → status` | Marks the ticket resolved once image comparison and citizen confirmation both pass |

## 6. Cross-cutting concerns

- **Auth/authorization**: MCP tool calls run with the same department-scoped permissions as the admin's own dashboard session — a department-A admin's Claude session cannot list department-B's issues. The same scoping applies to Agent 3's `notify_higher_authority` — it can only escalate within the correct department's tier chain.
- **Audit logging**: every write action (priority change, officer assignment, contractor email send, confirm-closed, escalation, reopen) is logged with an actor ID (admin or agent name) and timestamp — `escalation_log` and the general audit trail cover the agent-triggered writes, not just human ones.
- **Async by design**: the ingest pipeline and all four agents run as background jobs, never inline with a blocking HTTP request — the confirmation screen (A5 in how_it_should_work.md) polls/waits for Agent 1 to finish rather than blocking on it.
- **Escalation**: now wired in as Agent 3 — no longer a deferred gap (previously noted as out of scope; reversed based on this round of requirements).
