# WorkSim

A modular **company simulation engine** driven by **Job Cards**. Select a Job Card
(a save-file for a role + scenario) and WorkSim simulates a realistic slice of that
job: a fake company with a bank balance, fake clients and market, LLM-powered
co-workers who chatter in a chat panel, and **real graded deliverables written to
disk** (spreadsheets, docs, dashboards) you can present as real experience.

Every completed task is logged as a structured `(context → work → grade → reward)`
record — the long game is to train our own models on that dataset. The persona
"brain" is swappable (`AgentBrain`): cloud LLM now, our own model later.

## Quickstart (Windows / PowerShell, from this folder)

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m pytest -q            # foundation checks
.\.venv\Scripts\python -m worksim.cards        # list loaded cards
```

The web app (M5) will run on `http://127.0.0.1:8500`.

## Layout

- `cards/` — Job Cards, Employee Profiles, Scenarios (author-written YAML — the save files)
- `worksim/` — the package (schema, card loader, state, money, scenario, brain, deliverables, app)
- `runs/` — per-run output: `runs/<id>/{deliverables/, transcript.jsonl}`
- `data/` — `worksim.db` (state) and `training/*.jsonl` (the dataset)
- `tests/` — pytest

## For contributors (human or agent)

Read **[AGENTS.md](AGENTS.md)** first — it is the single source of truth for
conventions. Pick work from **[TASKS.md](TASKS.md)**. Three agents (Claude, Codex,
Grok) build this in one shared git repo.
