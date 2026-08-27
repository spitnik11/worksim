# AGENTS.md — WorkSim conventions (single source of truth)

Three agents build WorkSim in one shared git repo: **Claude** (hard seams), **Codex**
(mechanical breadth), **Grok** (UI + scenario content). `CLAUDE.md`, `CODEX.md`, and
`GROK.md` all defer to THIS file so conventions never diverge. Read this before writing code.

## What WorkSim is

A company simulation engine driven by Job Cards. Pipeline:

```
JobCard + EmployeeProfile + CompanyState + Scenario
  -> TaskGenerator -> TaskPacket -> AgentAssignment -> Agent work (chat + tools)
  -> Deliverables on disk -> Evaluator (rubric) -> CompanyState mutated
  -> TrainingRecord appended (JSONL, the dataset)
```

It is also a **data-generation system**: every completed task must end up as a
`TrainingRecord` in `data/training/*.jsonl`. Don't add a code path that produces graded
work without logging it.

## The one non-negotiable rule

**Job descriptions are DATA, not prompts.** Roles/scenarios/employees are YAML under
`cards/`, validated by `worksim/schema.py`. Never hardcode `if role == "analyst": prompt=...`.
Persona prompts are *built from* cards in `worksim/personas.py`.

## Stack & conventions (match, don't reinvent)

- **Python 3.10+** (installed interpreter is 3.10.11 — no 3.11-only syntax).
- **Schemas**: pydantic v2 models in `worksim/schema.py`. Validate at load; fail loudly.
- **State**: SQLite via **raw `sqlite3`** (module-level `SCHEMA` string + a `MIGRATIONS`
  list of guarded `ALTER TABLE ADD COLUMN`). No ORM. Mirror Trawl's `core/store.py` style.
- **Web**: FastAPI + uvicorn, `127.0.0.1`, **port 8500**. All routes under an `/api/v1`
  router (the stable seam). Serve one self-contained `worksim/web/index.html` (inline CSS +
  vanilla JS, no build step). One fetch helper `api(p,o)=fetch('/api/v1'+p,o)`.
- **Chat = background thread + transcript polling, NOT SSE.** A run appends persona messages
  to `runs/<id>/transcript.jsonl`; the UI polls `GET /api/v1/runs/<id>/messages?since=N`.
- **Deliverables**: dashboards/covers = single-file HTML from `string.Template`; spreadsheets
  = `openpyxl`; docs = `python-docx`. Output must look designed (see the `trawl-design` bar),
  not AI-slop. Write into `runs/<id>/deliverables/`.
- **AgentBrain**: all LLM/persona calls go through the `worksim/brain/` interface. One cloud
  impl now (`brain/llm.py`, Anthropic via httpx). The trained-model impl lands in the same seam.

## Two number scales (do not confuse)

- Job Card `core_competencies` and Task `required_skills`: **0.0–1.0** weights.
- Employee `skills` and `traits`: **0–100** proficiency scores.

## Hidden truth

`Scenario.hidden_truth` and `TaskPacket.hidden_truth` are **engine-only**. Personas never see
them; only the Evaluator does. Always send `TaskPacket.worker_view()` (strips it) to a persona.

## Git rules (from global policy — enforced)

- Commit author is **Gabriel Pina** only. **No Claude co-author trailer.** No `--no-verify`.
- Repo stays **private**. Never commit secrets, API keys, `.env`, or `*.local.yaml`
  (`.gitignore` covers these — keep it that way).
- Small, focused commits. Run `python -m pytest -q` green before committing.
- **Shared working tree — stage only your OWN files.** All three agents share this one git
  checkout. Never `git add -A` / `git add .` — you would sweep another agent's in-progress work
  into your commit. Stage explicit paths only (e.g. `git add worksim/assign.py tests/test_assign.py`).
  `git commit` (no `-a`). If `git status` shows files you didn't touch, leave them unstaged.

## How to claim work

1. Open `TASKS.md`. Find a `TODO` task tagged for your agent.
2. Change its status to `CLAIMED (<you>)` in the same commit you start with.
3. When done and tests pass, mark it `DONE (<you>)`.
4. Don't edit files owned by another agent's in-flight task; if a seam is unclear, add a note
   under the task rather than guessing.

## Run

```
python -m pytest -q          # tests
python -m worksim.cards      # sanity: list loaded cards
# (M5+) uvicorn worksim.app:app --port 8500
```
