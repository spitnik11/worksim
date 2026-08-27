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
- [x] **DONE (Codex)** author the remaining 7 canonical Job Cards from the source doc, each with a matching
      employee or two. Copy the shape of the two reference cards. Validate with `python -m worksim.cards`.
      Roles: `technical_business_analyst`, `ai_business_analyst`, `ai_quality_analyst`,
      `application_support_analyst`, `business_applications_analyst`, `project_coordinator`,
      `resiliency_analyst`.

## M2 — Company state + money
- [x] **DONE (Claude)** `worksim/state.py` — CompanyState + raw-sqlite3 (`CompanyStore`), each run is a
      save (no bleed on swap), `create_run`/`load`/`save`/`patch`/`reset_to_scenario`/active-run pointer.
- [ ] **TODO (Codex)** `worksim/money.py` — bank/ledger keyed by `run_id`. **Seam (fixed):** cash is NOT in
      CompanyState. Opening balance = `CompanyStore.opening_cash(run_id)`; **current balance = opening_cash +
      SUM(ledger entries)**. API to build: `add_entry(run_id, amount, reason, kind)` (income=+, cost=−),
      `balance(run_id)`, `entries(run_id)`, `summary(run_id)`. Own its own table in a raw-sqlite3 module (may
      reuse `state.connect`/`init_db` pattern; coordinate if you want to share the DB file — `data/worksim.db`).
      Tests for the arithmetic (income up, cost down, balance nets correctly).
- [ ] **TODO (Codex)** add an optional `economics` block to the Job Card schema + reference cards
      (salary/day, task income range) — **coordinate the schema field with Claude first** (don't edit
      `worksim/schema.py` solo; propose the fields in a TASKS.md note and Claude adds them).

## M3 — Scenario engine + assignment
- [x] **DONE (Claude)** `worksim/scenario.py` — `ScenarioEngine.generate_task(job, event)` + `InformationBroker`
      (serves scenario `documents` on request, never the hidden truth; `ground_truth()` is evaluator-only).
      Added `documents` field to Scenario schema + evidence docs on the q3 scenario.
- [x] **DONE (Claude)** `worksim/assign.py` — weighted score (§16) + `assign()` primary/support/independent
      reviewer + risk gates. (Roster add/remove worker lives with the run object, wired at M4.)

## M4 — Brain + one role end-to-end
- [x] **DONE (Claude)** `worksim/brain/__init__.py` — `AgentBrain` interface + deterministic `FakeBrain`
      + `get_brain()` factory (the swap seam for the future trained model). WORKSIM_BRAIN env selects.
- [x] **DONE (Claude)** `worksim/brain/llm.py` — `AnthropicBrain` via the official `anthropic` SDK (lazy import;
      key from env, never committed). Model defaults to `claude-opus-5`, override with WORKSIM_BRAIN_MODEL.
- [x] **DONE (Claude)** `worksim/personas.py` — `worker_system` + `task_prompt`, data-driven from cards; always
      uses `worker_view()`. Test enforces hidden_truth can't leak into any persona string.
- [x] **DONE (Claude)** `worksim/run.py` — full loop wired: scenario→task→assign→persona→brain→deliverable(.md)
      +transcript. **Runs offline today via FakeBrain** (34 tests green). Real-LLM run needs a key
      (`WORKSIM_BRAIN=anthropic`); richer deliverables swap in at the marked seam once the renderers land.
- [ ] **TODO (Codex)** `worksim/deliverables/xlsx.py` + `dashboard.py` — real `.xlsx` + single-file HTML dashboard
      into `runs/<id>/deliverables/`. **Integration seam:** `worksim/run.py` writes the brain's output as `.md`
      today; extend it to call your renderer(s) so the Data Analyst emits a real spreadsheet + dashboard.

## M5 — Web app
- [ ] **CLAIMED (Grok)** `worksim/app.py` — FastAPI, `/api/v1` router, serve `web/index.html`, run lifecycle,
      transcript polling endpoint
- [ ] **CLAIMED (Grok)** `worksim/web/index.html` — split-pane UI: chat panel (poll), run/deliverable browser
      (download links), money dashboard. Job Radar pattern, no build step.

      **M5 contract (proposed — not wired live).** Static shell + 501 stubs may land before M3/M4.
      Agree this list before Grok wires real calls. Response shapes in comments on the stubs.

      - `GET  /api/v1/health`
      - `GET  /api/v1/scenarios` · `GET /api/v1/scenarios/{id}`
      - `GET  /api/v1/jobs` · `GET /api/v1/employees`  (CardLibrary lists)
      - `POST /api/v1/runs` `{scenario_id, title?}` → create_run (Claude `state.py`)
      - `GET  /api/v1/runs` · `GET /api/v1/runs/{id}`
      - `POST /api/v1/runs/{id}/start` · `POST /api/v1/runs/{id}/stop`
      - `GET  /api/v1/runs/{id}/messages?since=N`  transcript poll (`{messages, next_since}`)
      - `POST /api/v1/runs/{id}/messages` `{text}` operator chat
      - `GET  /api/v1/runs/{id}/deliverables` · `GET .../deliverables/{name}`
      - `GET  /api/v1/runs/{id}/money`  balance + ledger (Codex `money.py`)


## M6 — Evaluator + training capture
- [ ] **TODO (Claude)** `worksim/evaluate.py` — multi-score rubric via AgentBrain against acceptance_criteria +
      hidden_truth; role-specific weighting -> final grade
- [ ] **TODO (Claude)** `worksim/trainlog.py` — append TrainingRecord JSONL per completed task
- [ ] **TODO (Codex)** `worksim/deliverables/docx.py` + `md.py`

## M7 — Breadth
- [ ] **TODO (Codex)** deliverable renderers for the remaining role output types
- [ ] **CLAIMED (Grok)** more scenarios (fake clients, market datasets, event copy)
- [ ] **TODO (Claude)** worker skill growth after graded tasks; seamless scenario swap polish
