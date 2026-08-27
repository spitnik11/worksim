# TASKS.md — WorkSim board

Status values: `TODO` · `CLAIMED (<agent>)` · `DONE (<agent>)` · `BLOCKED (reason)`.
Claim a task by editing its status in the same commit you start. See [AGENTS.md](AGENTS.md)
for rules. Milestones are foundation-first: don't start a milestone until its predecessor's
core tasks are `DONE`.

---

## M0 — Repo + agent coordination
- [x] **DONE (Claude)** git init, package skeleton, `.gitignore`, `requirements.txt`, `README.md`
- [x] **DONE (Claude)** `AGENTS.md` + `CLAUDE.md`/`CODEX.md`/`GROK.md` + this board

## M1 — Card system (the foundation)
- [x] **DONE (Claude)** `worksim/schema.py` — JobCard, EmployeeProfile, TaskPacket, Scenario (pydantic v2)
- [x] **DONE (Claude)** `worksim/cards.py` — CardLibrary loader/validator (the save-file registry)
- [x] **DONE (Claude)** reference cards: `data_reporting_analyst`, `business_systems_analyst`, 2 employees, 1 scenario
- [x] **DONE (Claude)** `tests/test_cards.py`
- [ ] **TODO (Codex)** author the remaining 7 canonical Job Cards from the source doc, each with a matching
      employee or two. Copy the shape of the two reference cards. Validate with `python -m worksim.cards`.
      Roles: `technical_business_analyst`, `ai_business_analyst`, `ai_quality_analyst`,
      `application_support_analyst`, `business_applications_analyst`, `project_coordinator`,
      `resiliency_analyst`.

## M2 — Company state + money
- [ ] **TODO (Claude)** `worksim/state.py` — CompanyState + raw-sqlite3 persistence (SCHEMA + MIGRATIONS),
      seed from `Scenario.company`, load/save, clean reload on scenario swap
- [ ] **TODO (Codex)** `worksim/money.py` — bank/ledger: append income/cost entries, current balance,
      per-run summary. Tests for the arithmetic.
- [ ] **TODO (Codex)** add an optional `economics` block to the Job Card schema + reference cards
      (salary/day, task income range) — coordinate the schema field with Claude first.

## M3 — Scenario engine + assignment
- [ ] **TODO (Claude)** `worksim/scenario.py` — event -> TaskPacket generation; holds hidden truth;
      reveals info only through requested inputs
- [ ] **TODO (Claude)** `worksim/assign.py` — weighted assignment score (role/skill/tool/capacity/history);
      add & remove workers. Test against a known fixture.

## M4 — Brain + one role end-to-end
- [ ] **TODO (Claude)** `worksim/brain/__init__.py` — AgentBrain interface (+ a fake/deterministic impl for tests)
- [ ] **TODO (Claude)** `worksim/brain/llm.py` — cloud LLM impl (Anthropic via httpx); reads key from env, never committed
- [ ] **TODO (Claude)** `worksim/personas.py` — build persona system prompts from JobCard + EmployeeProfile;
      always uses `TaskPacket.worker_view()`
- [ ] **TODO (Codex)** `worksim/deliverables/xlsx.py` + `dashboard.py` — enough for the Data Analyst to emit a
      real `.xlsx` + single-file HTML dashboard into `runs/<id>/deliverables/`
- [ ] **TODO (Claude)** wire the Data & Reporting Analyst through one full run of `q3_revenue_decline`

## M5 — Web app
- [ ] **TODO (Grok)** `worksim/app.py` — FastAPI, `/api/v1` router, serve `web/index.html`, run lifecycle,
      transcript polling endpoint
- [ ] **TODO (Grok)** `worksim/web/index.html` — split-pane UI: chat panel (poll), run/deliverable browser
      (download links), money dashboard. Job Radar pattern, no build step.

## M6 — Evaluator + training capture
- [ ] **TODO (Claude)** `worksim/evaluate.py` — multi-score rubric via AgentBrain against acceptance_criteria +
      hidden_truth; role-specific weighting -> final grade
- [ ] **TODO (Claude)** `worksim/trainlog.py` — append TrainingRecord JSONL per completed task
- [ ] **TODO (Codex)** `worksim/deliverables/docx.py` + `md.py`

## M7 — Breadth
- [ ] **TODO (Codex)** deliverable renderers for the remaining role output types
- [ ] **TODO (Grok)** more scenarios (fake clients, market datasets, event copy)
- [ ] **TODO (Claude)** worker skill growth after graded tasks; seamless scenario swap polish
