# AION — Development Report

**Prepared:** 2026-07-26 · **Updated:** 2026-07-28 (verified live per role against the running backend on :8001)
**Scope:** the items listed in the build instruction and the handwritten notes
(`Handwritten_Notes_Verbatim_Transcription.pdf`). Nothing outside those items is included.

> This revision replaces the earlier "to build / 40 to create" status. The workforce and the
> workplace layer described in the notes were built and seeded since the first draft; every
> claim below was re-checked against the live application and its database, and each section
> now carries a **Further improvements** note listing only what genuinely remains.

---

## 0. Role structure — each role sees only what it needs (2026-07-28)

The dashboard is a **role-aware tab strip**, scoped so an employee sees their department, a
head sees what they manage, and the admin sees the whole company. No feature was removed —
the tabs decide what is on screen for each role. Verified live per role:

| Area (tab) | Employee | Dept Head | Admin | Contents |
|---|---|---|---|---|
| **My Work** | ✓ | ✓ | ✓ | Profile, leave, project/policy requests, add-a-document, Axon assistant |
| **My Department** | ✓ | ✓ | ✓ | **Who is in the department, who does what, current policies** (dept-scoped), your department's health and standing, your department's AI agent |
| **Intelligence** | — | ✓ | ✓ | Org-wide: health index, **organizational diseases (5)**, **knowledge graph**, MRI, knowledge decay |
| **My Team** | — | ✓ | ✓ | Approval queue (leave + requests), message the department, **message another department**, fund chain, who-writes-what |
| **Finance** | — | Finance head | ✓ | Payroll, funding, profit |
| **Organization** | — | ✓ (overview) | ✓ (full) | Org overview, all-department scorecards, simulation, self-healing, succession, risks, marketplace, learning; **Command Centre admin-only** |

- **Employee** sees **2 areas — My Work + My Department** — their department's people,
  projects, policies, health and agent, and nothing of other departments. They do **not** see
  the organisation-wide analytics. Matches notes i–vii and "he just needs his department's
  details".
- **Dept Head** sees 6 areas — their department plus the org-wide Intelligence, their team's
  approvals, Finance (if Finance), and the organisation overview. Command Centre stays hidden.
- **Admin** sees everything, including the Command Centre and every department's scorecard.
- The department roster/projects/policies view (`/workplace/department`) was **wired for the
  first time** this pass — it existed in the backend but was never on screen. The all-team
  scorecard was **removed from the employee's view** because it exposed peer departments.
- Zero console errors; zero horizontal overflow at 375px and 1440px on all six tabs; design
  audit clean. Verified with mock logins for all three roles.

---

## 0b. Admin as the centre, and departments talking to each other (2026-07-28)

**The admin is now a central "boss" view, attached to no department.** Instead of a personal
department, the admin sees:

| Admin tab | Contents |
|---|---|
| **Overview** | Overall growth (command centre), organisation standing, **the org-wide AI agent (Atlas)**, add-a-document |
| **Departments** | Every department's scorecard — **click one to drill into its people, their projects, and its policies** |
| **Approvals** | The department heads' leave and requests, the fund chain, document approvals |
| **Intelligence** | Org-wide diseases, knowledge graph, MRI, decay |
| **Finance** | Payroll, funding, profit |
| **Organization** | Simulation, self-healing, succession, risks, marketplace, learning |

- The admin has **no personal leave and no "my department"** — normally he oversees: approvals
  to heads, overall growth, and monitoring every department. When he needs detail, he **clicks a
  department and sees its employees and their work** (verified: Human Resources → led by Priya
  Nair, 10 people, 2 projects, 6 policies). Backed by `GET /workplace/department?dept_id=`
  (admin-only cross-department read).

**Departments can now ask each other for things and get an answer.** From **My Team → "Reach
another department"** a head can either **Message** another department's head (a heads-up) or
**Ask for approval** — a formal request that lands in that head's queue for a yes/no, with the
outcome returned to the asker. Verified end to end: Finance → R&D, approved, outcome shown to
Finance. (`POST /workplace/interdept-request`.)

**AI agents, confirmed:** each of the six departments has its **own** agent (Finance = *Ledger*,
HR = *Compass*, IT = *Relay*, Manufacturing = *Forge*, R&D = *Prism*, Sales = *Signal*); the
**admin holds an organisation-wide agent, *Atlas*.** **Axon** is the common assistant everyone
can use. A head or employee opens on their own department's agent by default.

---

## 0c. Text and files in every conversation (2026-07-28)

Everywhere people communicate, they can now send **text, a file, or both** — and the file
reaches the other person's login, so it works across different computers and places.

| Communication | Text | File | Where the recipient sees it |
|---|---|---|---|
| Message to your department | ✓ | ✓ | recipient's **Messages** inbox (download link) |
| Message another department's head | ✓ | ✓ | that head's **Messages** inbox |
| Ask another department for approval | ✓ | ✓ | that head's **Approvals** queue |
| Send a project / policy to your head | ✓ | ✓ | head's **Approvals** queue |
| Leave request | ✓ | ✓ (e.g. a medical note) | head's leave queue |

- A new **Messages inbox** was added for every role (for the admin it sits under *Overview*) —
  before this, messages were only hinted at in notifications with no way to open a file.
- Files are stored server-side and streamed back only to people in the same organisation, with
  the login token attached to every download (`POST/GET /workplace/attachments`).
- **Verified across two different logins, through the real interface:** an employee attached a
  proposal file to a request → the head opened it from her queue and got the exact file; a head
  sent the department a message with a notes file → an employee opened it from their inbox and
  got the exact file. File-only messages (no text) also work.

---

## 0d. Login routing, security, and clarity (2026-07-28)

- **Sign-in routes to the right dashboard, and a security bug was fixed.** The login form used to
  pre-fill the admin's credentials, so signing out and back in silently logged you in as the admin.
  Removed. Verified: head → head dashboard, admin → admin, employee → employee; signing out fully
  clears the session. Each of the 61 accounts lands on its own role's dashboard.
- **A head's knowledge graph now shows only their own team.** The brain-map is scoped: a department
  head sees only their department's people and their work (documents they wrote, projects they are on);
  the admin still sees the whole organisation. Verified live (head: 10 Finance people; admin: org-wide).
- **"What our knowledge is about" is now readable.** The block that showed bare numbers in a grid full
  of empty space now opens with a plain explanation, a summary row (total documents, number of topics,
  a health reading, how many are unlinked), topic bars sorted largest-first with a count and a percentage,
  and three risk cards each explained in one sentence. No feature changed — only how it reads.
- **No 5xx errors for any role.** Employee, head and admin were swept across two dozen endpoints each;
  every denial is an intentional need-to-know block, never a crash.

---

## 0e. Two-way messaging, everywhere (2026-07-28)

Messages were always delivered — the "shows approved" was a mix-up between two buttons. In the
"reach another department" area the prominent button used to be **Ask for approval** (which files a
yes/no request, not a message), so it was easy to hit by accident. **Send message** is now the main
button, **Request approval** the secondary one, each labelled with what it does.

Messaging is now genuinely two-way at every level, verified live from one login to another:

| From → To | Works | Where it lands |
|---|---|---|
| Employee → their head *(new)* | ✓ | head's Messages inbox |
| Head → employee / whole department | ✓ | employee's inbox |
| Head ↔ another department's head | ✓ both ways | each head's inbox |
| Admin → any head | ✓ | head's inbox |
| Employee → everyone (broadcast) | blocked | employees message their head, not the whole company |

Employees now have a **"Message your head"** box in their inbox (with an optional file). A head's inbox
shows everything sent to them — from their team, other heads, and the admin. All live data.

---

## 1. Existing features are inherited, not changed

**Rule for this phase:** no existing feature is modified, replaced, or dropped. Everything
below is carried forward exactly as it behaves today, and every new item is added alongside it.

**Measured live (`/openapi.json`): 98 operations across 17 modules** — up from the 77/14 of
the first draft. The count only grew; nothing was removed.

| Module | Endpoints | Status |
|---|---|---|
| `intelligence` — Organizational Intelligence Index, 12 dimensions, trends, history | 3 | inherited unchanged |
| `diseases` — 5-disease scan, report, timeline | 4 | inherited unchanged |
| `mri` — brain map, knowledge flow, bottlenecks, dependencies, black holes, innovation centres, timeline forecast | 7 | inherited unchanged |
| `decay` — entropy, decay report, forgotten, conflicts, half-life | 5 | inherited unchanged |
| `graph` — nodes, relationships, departments, policies, search, traverse | 11 | inherited unchanged |
| `advisor` — risks, briefing, opportunities, Axon chat | 5 | inherited unchanged |
| `ocsie` — successor intelligence, business impact, continuity report, roadmap, unfinished work | 7 | inherited unchanged |
| `healing` — recommendations, generate, approve/complete/reject | 5 | inherited unchanged |
| `simulation` — scenarios, run | 2 | inherited unchanged |
| `ingestion` — document upload, recent | 2 | inherited unchanged |
| `workflow` — approval chain, queue, stats, history | 7 | inherited unchanged |
| `enterprise` — command centre, scorecards, org overview, my team, risk prediction, marketplace, timeline, notifications, learning, search | 14 | inherited unchanged |
| `auth` — login, refresh, register, me | 4 | inherited unchanged |
| `public` — platform facts | 1 | inherited unchanged |
| **`workplace`** — profile, department, leave, requests, funds, messages, finance overview | **14** | **added this phase** |
| **`agents`** — department AI agent directory + per-agent chat | **2** | **added this phase** |

**Carry-forward checklist — re-run before every future change:**

- [x] Endpoint inventory ≥ 77 → **now 98**, never lower
- [ ] Re-run the cross-endpoint consistency checks after any further change; all must still pass
- [ ] Re-run the role matrix; no role loses access it has today
- [ ] Landing page and dashboard sections must all still render with zero console errors

---

## 2. 61 login IDs and passwords, one pattern

**Target:** 61 accounts. **Status: met.**

```
6 departments × 10 members  = 60   ✓ built
1 administrator             =  1    ✓ demo@aion.ai (org_admin)
                              ---
                              61     ✓
```

**Measured live (main org `a1f793b3…`):** 60 members across the 6 active departments, exactly
**one `dept_head` per department**, plus one `org_admin`.

| Department | Members | Head | Others (employee + manager) |
|---|---|---|---|
| Finance | 10 | 1 | 9 |
| Human Resources | 10 | 1 | 9 |
| Information Technology | 10 | 1 | 9 |
| Manufacturing | 10 | 1 | 9 |
| Research & Development | 10 | 1 | 9 |
| Sales & Marketing | 10 | 1 | 9 |

**Pattern in force:**

| Field | Pattern | Verified |
|---|---|---|
| Login / email | `firstname.lastname@<domain>` | ✓ e.g. `priya.raman@novatech.example` |
| Password | one shared value, hashed (`DemoPass123!`), never stored in plain text | ✓ all 61 log in |
| Role | `dept_head` ×1 per department; the other 9 are `employee`/`manager`; `org_admin` ×1 | ✓ |
| Department | one of the six | ✓ |

**Further improvements:**

- [ ] **Email domain is not uniform** — 49 members on `novatech.example`, 11 (including all
      6 heads) on `novarobotics.ai`, admin on `aion.ai`. The *format* matches, but the
      instruction asked for "the same pattern." Normalise all 61 to a single company domain.
- [ ] The 9 non-head members are a mix of `employee` and `manager`. The notes name only
      **Employee** and **Head**; if the manager tier is unwanted here, reassign those to
      `employee`. (It came from the SRS role model already in the system.)
- [ ] Produce the deliverable credential sheet: 61 rows — ID / name / department / role /
      email / password — for handover.

---

## 3. Employee details and department structure

Each of the six departments holds **10 members: 1 head + 9 others.** — **built.**

**Per-employee record now held** (notes, Employee i–iv), verified via `GET /workplace/me/profile`:

- Profile: name, role, job title, department, head of department
- Department detail: department projects, member count, who is working on what
- Current policies and regulations in their department
- Their department's data accessible to AION

**Further improvements:**

- [ ] Spot-check every one of the 60 profiles for populated projects/policies (verified on a
      sample, not exhaustively).

---

## 3a. Approval hierarchy — who signs off whom (2026-07-28)

Built and verified per role, exactly as instructed:

| Requester | Leave / requests go to | Notes |
|---|---|---|
| Employee / Manager | their **Department Head** | approver shown on their dashboard |
| **Department Head** | the **Admin** | a head cannot approve their own leave, so it escalates one level |
| **Admin** | — | admins do not take leave; the leave panel is hidden for them |

- A head's approval queue shows **only their team**; the **admin's queue shows only the six
  heads**. No one ever sees their own request. Verified live through the UI: a head's leave
  reached the admin's queue and the admin approved it.
- **Cross-department messaging** ("when one department needs another"): a head (or the admin)
  can message any other department's head from **My Team → "Message another department"**.
  Verified: a message was delivered to another head and showed in their notifications.
- **Per-department AI agent** delivers each department's special function (Finance's agent
  *Ledger* covers salary/funding/profit; HR's *Compass*; IT's *Relay*; and so on). A head
  lands on **their own department's agent** by default. **Axon** remains the common
  organisation-wide assistant available to everyone.

---

## 4. Employee → Head request flow, usable live — **verified end to end**

Logged in as an employee (`priya.raman@novatech.example`), sent requests, logged in as the
head (`grace.osei@…`), acted on them, confirmed the employee dashboard updated.

| Capability | Endpoint | Verified live |
|---|---|---|
| Submit project / policy to head | `POST /workplace/requests` | ✓ created, status `pending`, `sent_to` head |
| Submit leave request | `POST /workplace/leave` | ✓ 3-day request, `remaining_after_approval` shown |
| Head sees pending items | `GET /workplace/leave/queue`, `/requests/queue` | ✓ both appeared in Grace's queue |
| Head approves / rejects with note | `POST …/{id}/decide` (`{approve, note}`) | ✓ both returned status `approved` |
| Employee sees the outcome | `GET /workplace/leave/me` | ✓ balance moved to taken 3 / remaining 24 |
| Employee is notified | `GET /enterprise/notifications` | ✓ 2 unread: "Leave approved", "…policy approved" |

**Leave rules from the notes (Employee vii) — all present:** 30-day annual entitlement,
request to HOD, approve/reject message back, balance and days-taken shown and kept updated
(`entitlement_days 30`, `taken_days`, `pending_days`, `remaining_days`).

**Notification tab** — present; approval messages land there for the employee.

**Further improvements:**

- [ ] Surface the leave/request outcome inside the **`/workplace/messages`** inbox too, not
      only the notifications tab, so both channels agree (today the direct-message inbox
      returned 0 for the employee while notifications held the approvals).

---

## 5. Head of department — **built**

From the notes, all present:

- Profile section like an employee, plus complete details of all employees and all projects
- All employee privileges
- Approve / give feedback to employees under them (`/requests/{id}/decide`, `/leave/{id}/decide`)
- Notification tab
- Message all employees at once, or a single employee (`POST /workplace/messages`)
- Company growth and the department's contribution shown (inherited `enterprise` modules,
  now department-scoped)

**Inter-department fund chain (notes):** requesting department → Finance → Admin → intimation
back. Built as `POST /workplace/funds` → Finance decides (`stage=finance`) → Admin decides
(`stage=admin`) → `stage=intimated` with a notification back to the requesting department.

**Further improvements:**

- [ ] Exercise the full fund chain end to end through the UI with a real login at each stage
      (endpoints and stage transitions verified in code; not yet click-tested like §4).

---

## 6. Finance department — additional features — **built, real data**

`GET /workplace/finance/overview` returns real, record-derived figures — verified live:

- **Payroll:** 60 people, **annual total $6,375,000**, broken down by department
- Company funding and profit management surfaced in the same overview
- Finance receives and approves fund requests from other departments (§5 chain, `stage=finance`)

**Further improvements:**

- [ ] Confirm the profit/funding figures trace to stored records the same way payroll does
      (payroll confirmed real; profit/funding not yet traced to source in this pass).

---

## 7. Admin privileges — **built**

From the notes, all present (org_admin role, verified in the role matrix and inherited modules):

- All access held by heads and employees; all 7-layer features
- Individually inspect all departments (`/enterprise/command-center`, `/enterprise/departments/scorecards`)
- Approve items escalated by heads (workflow head stage; fund chain admin stage)
- Communicate with all heads; full organisation view, growth and risk (`/advisor/risks`, briefing)

**Further improvements:**

- [ ] Nothing outstanding against the notes; keep on the §1 carry-forward checklist.

---

## 8. Department AI agents — **built**

`GET /agents/directory` returns one dedicated agent per department, plus per-agent chat
(`POST /agents/{key}/chat`). Verified live: Finance = **Ledger** ("salaries, funding, profit,
spend approvals and financial risk"), HR = Compass, IT = Relay, Manufacturing = Forge, etc.,
each scoped to its department; the admin dashboard carries the organisation-wide agent (Axon).

**Further improvements:**

- [ ] Confirm each department agent answers **only** from its own scope (isolation click-test).

---

## 9. Multi-company registration

From the notes: registering a company should create this whole structure for it, with its own
admin, HOD and employee dashboards, and no data crossing between companies.

**Status:** registration (`POST /auth/register`) and per-org isolation exist and are used by
several test orgs (`testcorp.io`, `freshcorp.io`, `zerocorp.io`, `verifyco.io`). The full
6×10 structure is currently seeded for the main org only.

**Further improvements:**

- [ ] Make registration reproduce the same 6-department / 10-member scaffold for a new company
      automatically (today it creates the org + admin, not the populated departments).
- [ ] Confirm one company's data never appears in another's, live, for the workplace layer.

---

## 10. Real data, not simulation — **holds**

Spot-verified: finance payroll ($6.375M) is computed from the 60 seeded salaries; leave
balances move when a request is approved; profiles read real assignments. No hardcoded figures
were reintroduced into the frontend for the workplace features.

**Further improvements:**

- [ ] Repeat the "change one record → watch every dependent figure move" check across profit,
      funding and department metrics (done for leave and payroll).

---

## 11. Open item from the notes — resolved

The ambiguous phrase in the "Head of each dept." section is **"knowledge graph"**. The author
confirmed they wrote a placeholder because they did not know the exact name; it simply refers to
the **knowledge graph** feature, which already exists in the product (the live brain-map in the
**Intelligence** area). No separate "diseases knowledge graph" is needed. **Closed.**

---

## Summary of work

| # | Item | Status |
|---|---|---|
| 0 | Employee / Head / Admin structure, scoped to need-to-know | ✓ role tabs; employee = own department only; verified live per role |
| 1 | Existing features inherited unchanged | ✓ 98 ops / 17 modules (≥ 77) |
| 2 | 61 logins in one pattern | ✓ 60 members + 1 admin; **domain not yet uniform** |
| 3 | 6 departments × 10 (1 head + 9) | ✓ built, 1 head each |
| 4 | Employee → head requests, live | ✓ verified end to end |
| 5 | Head privileges + fund chain | ✓ built; fund chain UI test pending |
| 6 | Finance: salary, funding, profit | ✓ real payroll; funding/profit source to confirm |
| 7 | Admin privileges | ✓ built |
| 8 | Per-department AI agents + org agent | ✓ built; isolation test pending |
| 9 | Multi-company registration | partial — auto-scaffold the 6×10 structure |
| 10 | Real data throughout | ✓ holds; extend the change-propagation check |
| 11 | Transcription phrase ("knowledge graph") | ✓ resolved — it's the existing knowledge graph |
