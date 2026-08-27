# CODEX.md

Read **[AGENTS.md](AGENTS.md)** first — single source of truth for conventions, stack, git
rules, and the task-claiming workflow. This file only notes Codex's lane.

**Codex owns mechanical breadth:** author the remaining Job Card / Employee / Scenario YAMLs
under `cards/` (from the source design doc), the deliverable renderers in
`worksim/deliverables/` (`xlsx.py`, `docx.py`, `dashboard.py`, `md.py`), `worksim/money.py`
(bank/ledger), and pytest suites. See `TASKS.md` for the current board.

Reference cards already exist to copy the shape from: `cards/jobs/data_reporting_analyst.yaml`
and `cards/jobs/business_systems_analyst.yaml`. Validate every new card with
`python -m worksim.cards` before committing.
