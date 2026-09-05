# Project Definition — Auto Grievance Raiser

## 1. What this is

A prototype civic-issue reporting system with two connected halves:

- **User system** — citizens photograph a civic issue (pothole, broken streetlight, garbage pile, etc.), the system automatically identifies the issue, geotags it, and routes it to the correct municipal department.
- **Admin system** — department staff triage, prioritize, and dispatch these issues, including an AI agent (via MCP) that can answer questions about the issue backlog and mass-email contractors, with completion verified through the same image pipeline used at intake.

This is a **prototype**, not a production government system. Identity verification is a mocked Aadhaar-style login (fake OTP, no real UIDAI integration) — this is stated explicitly so it isn't mistaken for real eKYC in review.

## 2. Problem statement

Civic issue reporting today is manual, slow, and disconnected:
- Citizens don't know which department or officer handles a given issue.
- The same issue gets reported multiple times with no way to tell that it's the same issue, so severity (how many people are affected) is invisible.
- Departments have no structured way to see issue concentration, prioritize by actual severity, or verify that contractor-reported fixes are real.
- Citizens get no visibility into whether their complaint was actioned.

## 3. Goals (v1 / prototype)

1. Let a citizen report an issue with a photo in under a minute, with the system doing the classification and routing work.
2. Avoid inflating or losing signal on duplicate reports — the same real-world issue reported by many people should count as *one issue with high affected-count*, not many separate low-priority issues, and not one report with the rest silently discarded.
3. Give admins a prioritized, geographically visualized backlog instead of a flat list.
4. Let admins use natural-language AI assistance (via MCP) to query the backlog and to mass-contact contractors, with a human always approving before anything is sent externally.
5. Close the loop: verify completion with evidence, not just a contractor's word, and let the citizen confirm satisfaction.

## 4. Non-goals (explicitly out of scope for v1)

- Real Aadhaar/UIDAI identity verification (mocked only).
- Automatic escalation / SLA enforcement — deferred, known gap.
- Officer-level automatic assignment — department admins manually assign from a pool.
- A dedicated contractor portal — contractors are reached by email only.
- Fully autonomous agent actions (sending mail, closing tickets) — every outward or closing action requires human approval.
- Population-normalized heatmaps — v1 uses raw complaint density.

## 5. Actors

| Actor | What they do |
|---|---|
| **Citizen** | Logs in (mock Aadhaar), uploads issue photos + description, confirms detected issues, tracks status, confirms satisfaction on completion |
| **Department admin** | Reviews incoming issues, sets/adjusts priority, assigns officers, monitors the heatmap, queries the AI agent, approves contractor emails, confirms closure |
| **AI agent (via MCP)** | Answers admin questions about the issue backlog, drafts contractor emails for approval, reads contractor replies and reports completion status |
| **Contractor** | Receives task emails, performs the fix, replies by email with a completion photo (no portal access) |

## 6. Success criteria for the prototype

- A photo uploaded by a citizen results in a correctly department-routed, geotagged issue without manual admin intervention (until priority-setting).
- Two citizens photographing the same real-world issue result in one clustered issue with an affected-count of 2, not two separate issues.
- An admin can ask the AI agent a backlog question ("how many open issues in ward 4?") and get a correct answer sourced from real data, not a guess.
- A mass contractor email is never sent without an explicit admin approval click.
- A completion claim without a valid, location-matching, timestamp-valid photo does not auto-close the issue.
