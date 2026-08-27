# GROK.md

Read **[AGENTS.md](AGENTS.md)** first — single source of truth for conventions, stack, git
rules, and the task-claiming workflow. This file only notes Grok's lane.

**Grok owns UI + scenario content:** `worksim/app.py` (FastAPI `/api/v1` routes + transcript
polling), `worksim/web/index.html` (single self-contained split-pane UI — chat panel, run
browser, money dashboard), and scenario *content* (fake clients, market datasets, event copy)
as new `cards/scenarios/*.yaml`. See `TASKS.md` for the current board.

UI rules that matter: no framework/build step, one fetch helper `api(p,o)=fetch('/api/v1'+p,o)`,
CSS custom properties + `prefers-color-scheme` dark mode, system-font stack, chat via polling
(NOT SSE). Mirror the Job Radar `index.html` pattern.
