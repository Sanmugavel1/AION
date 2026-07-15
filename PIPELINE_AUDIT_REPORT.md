# AION Pipeline Audit — Round 2

**Date:** 2026-07-11
**Scope:** Every backend API endpoint (44 routes across 10 modules), traced from computation → API response → frontend consumption. Round 1 (prior audit) found and fixed 6 bugs; this round verifies all 44 endpoints individually, closes out the two items Round 1 explicitly left open, and finds 4 additional real bugs Round 1 didn't reach.

## Executive summary

- **44 endpoints tested live** with a real auth token against the real demo data (Nova Robotics: 16 people, 21 knowledge items, 4 projects, 8 departments).
- **4 new bugs found and fixed**, on top of the 6 from Round 1 (all reverified still fixed).
- **2 previously-flagged stubs closed out**: the MRI timeline forecast and the AI Advisor's risks/opportunities feeds are now computed from real data instead of hardcoded text.
- **2 known data gaps honestly documented**, not papered over with fake data.
- Auth enforcement verified correct (401/403 on missing/bad tokens, all protected routes require a valid token).
- The LLM upgrade (`llama-3.3-70b-versatile` → `openai/gpt-oss-120b`) is live and verified — the AI Advisor gives noticeably more substantive, correctly-grounded answers.

## Bugs found and fixed this round

| # | Endpoint | Bug | Fix |
|---|----------|-----|-----|
| 1 | `GET /mri/timeline-forecast` | 100% hardcoded forecast text ("-5 to -8 points", "technology domain") regardless of org_id or real data — literally the same output for every organization | Now computes a real domain-weighted decay rate (reusing the Knowledge Half-Life algorithm's `DOMAIN_VOLATILITY` model) from the org's actual knowledge distribution, and projects it forward exponentially against the real current OII score. Confidence is deliberately conservative (0.35–0.54) since only one historical OII snapshot exists — stated explicitly in a `methodology` field rather than pretending precision it doesn't have. |
| 2 | `GET /advisor/risks` | Fully hardcoded — 2 fixed fake risks returned for every org, every time, **and actively rendered on the Board page** (this isn't dead code — confirmed `useBoardRisks()` is called in `board/page.tsx`) | Now derived from the live disease scan (any disease at critical/warning severity becomes a risk) plus real single-owner knowledge bottleneck counts. |
| 3 | `GET /advisor/opportunities` | Same as above — hardcoded fake opportunities ("3 teams solving the same problem independently") with no connection to real data, also actively rendered on the Board page | Now derived from real isolated/unused knowledge items and real department knowledge-distribution imbalance. Opportunity types requiring data this project doesn't track yet (genuine duplicate-effort detection across teams) are intentionally *not* fabricated. |
| 4 | `GET /advisor/briefing/latest` sections 3–6 and `top_priority` | `health_trend` hardcoded `"stable"`, sections `4_future_critical_areas` / `5_innovation_opportunities` hardcoded fixed arrays, `6_departments_becoming_isolated` hardcoded empty, and — most importantly — `top_priority` only checked bottleneck count, so it said *"Organization is operating within normal parameters"* even while Communication Stroke was at 85% (critical) | `health_trend` now pulled from the real trend service; sections 4/5 now derived from the real disease scan and the fixed `/advisor/opportunities` logic; section 6 now derived from real department communication-graph isolation; `top_priority` now checks active critical diseases first, before bottleneck count. |
| 5 | `POST /healing/recommendations/{id}/approve` | Malformed/garbage ID → unhandled `ValueError` from `UUID(id)` → raw `500 Internal Server Error` instead of a clean error | Malformed ID now returns `404 Recommendation not found`. |
| 6 | `POST /healing/recommendations/{id}/reject` | Same 500-on-malformed-ID bug, **plus** a separate bug: it never checked whether the recommendation existed at all — rejecting a nonexistent ID silently returned `200 {"status": "rejected"}` with no actual row updated | Now validates the ID format and existence before updating; nonexistent/malformed IDs return `404`, matching `approve`'s behavior. |
| 7 | `POST /ocsie/transition/{employee_id}` | Same 500-on-malformed-ID bug (unguarded `UUID(user_id)` in `ocsie_service.initiate_departure`) | Malformed ID now returns `404 Employee not found` instead of crashing. |

*(Numbered 1–7 for this round's report; combined with Round 1's 6, that's 13 real bugs fixed across both audit passes.)*

## Verified correct (no changes needed)

- **Core algorithms**: Knowledge Half-Life, Knowledge Entropy, Cognitive Resilience Score, Organizational DNA, OII 12-dimension scorer — reconfirmed real, non-trivial computation on real inputs.
- **Disease scan, decay entropy, healing recommendations, simulation impact** (Round 1 fixes) — reconfirmed still correct after two backend restarts and the LLM model swap.
- **Graph search & traverse** (`/graph/search`, `/graph/traverse`) — initially looked broken in my own testing (422 errors) but that was my test using the wrong query-param names; the actual frontend (`lib/api/graph.ts`) already uses the correct `q` / `from_node_id` params and both endpoints work correctly end-to-end.
- **`/mri/innovation-centers`** returns `[]` — confirmed this is a real, correctly-implemented graph query (nodes need ≥3 `RELATES_TO` neighbors to count as an innovation center) legitimately finding none in the current sparse demo graph, not a stub.
- **Auth enforcement**: no token → 403, invalid token → 401, valid token → 200, wrong password → 401, all consistent with expected behavior across every module tested.
- **AI Advisor grounding**: re-verified with the new `gpt-oss-120b` model — it correctly cites the real 85% Communication Stroke severity and other live figures; the LLM-failure fallback path (if Groq is ever unreachable) still degrades gracefully to a real-data text summary instead of a generic error.
- **Simulation engine**: initial test showed "0 employees depart," which looked like a bug — turned out to be my own malformed test request (top-level `target_id` instead of the correct `{"parameters": {"employee_ids": [...]}}` shape). Retested correctly: departure simulation properly computes cascade impact, knowledge-at-risk, and project delays from the real graph. Frontend's `SimulationRequest` type already matches the correct backend shape.

## Known data gaps (honestly reported, not fabricated)

- **Knowledge Obesity's "unused ratio" is always ~100%** in the demo data — not because the scoring logic is wrong, but because the seeded Knowledge nodes have no `access_count`/`last_accessed_at` history at all (verified directly: every one of the 21 knowledge nodes returns `access_count: null`). The math is doing exactly what it should with the data it's given; the data itself doesn't yet simulate realistic access patterns. This would need richer seed data or real usage tracking to produce a meaningful score, not a code fix.
- **3 of 5 diseases** (Memory Alzheimer's, Innovation Paralysis, Knowledge Cancer) still can't be genuinely detected — confirmed again this round — because departure history, idea/initiative tracking, and embedding-similarity infrastructure don't exist in the current graph schema. They correctly report "insufficient data" rather than a fake score (this was fixed in Round 1 and is still holding).
- **MRI timeline forecast confidence is capped at ~0.35–0.54** by design (see fix #1 above) because the org has only one historical OII snapshot. This isn't a bug — it's the forecast being honest about its own uncertainty. Confidence will rise naturally as more weekly snapshots accumulate.

## Verification performed

- All 44 endpoints called live with a real bearer token, response bodies inspected for plausibility (not just status code).
- Backend restarted 3 times across this audit; all fixes reconfirmed working after each restart.
- `npm run type-check` — 0 errors (no frontend files were touched this round; all fixes are backend-only, so nothing to regress on the frontend).
- Malformed-ID and nonexistent-ID edge cases tested for every mutation endpoint (`approve`, `reject`, `transition`, `department create`).
- No frontend `page.tsx` or `components/` files were touched — four other agents were doing visual-polish passes on those concurrently during this audit.

## Round 3 — Exhaustive Sweep

**Date:** 2026-07-11. **Scope:** everywhere Rounds 1–2 hadn't individually verified: every algorithm/service file, the GraphRAG engine, embedding service, all five `workers/`, `document_processor.py`, and a re-check of the OCSIE/succession logic. Plus a fresh model-choice verification.

### Found and fixed

**`ocsie_service.py::_analyze_knowledge_gaps`** (used by continuity reports and departure planning) unconditionally returned `[]` for three of its six fields — `missing_technical_skills`, `missing_customer_knowledge`, `missing_certifications` — regardless of the real employee. Confirmed via grep across `graph_repository.py` and `app/models/` that AION doesn't capture any technical-skill, customer-knowledge, or certification data at all — so this wasn't a computation bug, it's a genuine data gap. But an empty list reads as "no gaps found" (a positive, reassuring signal) when the truth is "we don't track this." Same failure shape as the disease-severity bug from Round 1. Fixed: these three fields now return `null` instead of `[]`, plus a `not_tracked` field naming them and a `not_tracked_reason` string explaining why — so a consumer can't mistake "not measured" for "measured and clean."

### Found, not a bug — flagging for awareness

**Dead code depending on decommissioned infrastructure.** `app/ai/graph_rag/graph_rag_engine.py` (a full hybrid Neo4j + Qdrant retrieval-augmented-generation pipeline), `app/integrations/document_processor.py`, and all five files in `app/workers/` are leftovers from AION's original enterprise architecture, from before the 2026-07-06 lightweight rewrite to SQLite + NetworkX (per the project's own history, Neo4j/Redis/Kafka/Qdrant/MinIO/Celery were all removed). Confirmed:
- Nothing in the live API calls `graph_rag_answer()` — zero call sites outside its own file.
- `app/core/config.py` has no `NEO4J_URI` or `QDRANT_*` settings at all, so `neo4j_client.py`/`qdrant_client.py` would throw `AttributeError` on first use if anything ever called them.
- `main.py` starts no scheduler/worker process — the `workers/` modules are never invoked.
This isn't producing wrong output to any user today (it's unreachable), so it wasn't touched. But it's worth a deliberate decision later: either delete it, or clearly mark it `# LEGACY — pre-rewrite, non-functional` so a future contributor doesn't assume GraphRAG or background workers are live features.

### Model verification

Re-pulled the live Groq model list. `openai/gpt-oss-120b` (currently configured) is confirmed still the largest reasoning-capable model available — the only other `reasoning`-tagged options are `qwen/qwen3-32b`, `qwen/qwen3.6-27b`, `openai/gpt-oss-20b`, and `openai/gpt-oss-safeguard-20b`, all meaningfully smaller. No change warranted.

Checked `max_tokens` headroom on every LLM call site: `chat()` and `generate_board_narrative()` were already bumped to 1536 earlier this session. `analyze_disease_pattern`, `generate_summary`, and `generate_recommendations` all go through `complete()`, whose default (2048) was never reduced and is already generous — no further change needed there.

### Verdict

App-wide, real user-facing output is now free of hardcoded/fabricated values: every endpoint either computes from live data or explicitly reports that it can't (rather than faking a plausible-looking number). The one exception found this round (OCSIE knowledge-gap fields) is fixed above. The dead GraphRAG/worker code is inert, not misleading anyone today, and is a cleanup decision rather than a bug fix.

**Verification:** backend restarted and re-tested after the `ocsie_service.py` fix; `openapi.json` and `/graph/departments` confirmed responding normally post-restart. No frontend files touched.
