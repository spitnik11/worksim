"""Run orchestrator — one task, end to end.

Ties the pieces together: pick scenario + role -> seed company state -> generate the
task -> assign the best worker -> build the persona -> the brain produces the deliverable
-> write it to disk and log the chatter to a transcript.

Offline by default (FakeBrain), so this whole loop is runnable and testable without a
key. Swap in the real brain with WORKSIM_BRAIN=anthropic. Deliverables are written as
Markdown here; the richer renderers (xlsx/dashboard) plug in at this seam once Codex's
`worksim/deliverables/` modules land.

Run `python -m worksim.run` for an offline self-check.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from worksim.assign import assign
from worksim.brain import AgentBrain, get_brain
from worksim.cards import CardLibrary
from worksim.personas import task_prompt, worker_system
from worksim.scenario import ScenarioEngine
from worksim.state import CompanyStore

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:48] or "deliverable").rstrip("-")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_task(
    scenario_id: str,
    role_id: str,
    *,
    brain: Optional[AgentBrain] = None,
    cards: Optional[CardLibrary] = None,
    store: Optional[CompanyStore] = None,
    runs_dir: Path | str = RUNS_DIR,
) -> dict:
    cards = cards or CardLibrary()
    brain = brain or get_brain()
    store = store or CompanyStore()

    scenario = cards.scenario(scenario_id)
    job = cards.job(role_id)
    state = store.create_run(scenario)
    run_dir = Path(runs_dir) / state.run_id
    deliverables_dir = run_dir / "deliverables"
    deliverables_dir.mkdir(parents=True, exist_ok=True)
    transcript = run_dir / "transcript.jsonl"

    def say(speaker: str, kind: str, text: str, **extra) -> None:
        entry = {"ts": _now(), "speaker": speaker, "kind": kind, "text": text, **extra}
        with transcript.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    eng = ScenarioEngine(scenario)
    task = eng.generate_task(job)

    result = assign(job, list(cards.employees.values()), task)
    worker = cards.employee(result.primary.employee_id)

    say(task.requester, "request", f"{task.title}\n\n{task.business_context}")
    say("HR", "assignment",
        f"Assigned to {worker.name} ({job.title}); "
        f"reviewer {result.reviewer.name if result.reviewer else 'none'}.")

    # The persona does the work. worker_view() guarantees hidden_truth never reaches it.
    system = worker_system(job, worker)
    output = brain.complete(system, [{"role": "user", "content": task_prompt(task)}])

    deliverable_path = deliverables_dir / f"{_slug(task.title)}.md"
    deliverable_path.write_text(output, encoding="utf-8")
    say(worker.name, "deliverable", output, file=str(deliverable_path))

    return {
        "run_id": state.run_id,
        "scenario_id": scenario_id,
        "role_id": role_id,
        "worker": worker.name,
        "task_id": task.task_id,
        "deliverable": str(deliverable_path),
        "transcript": str(transcript),
    }


def _main() -> None:
    # Offline: a canned deliverable proves the loop without a key.
    canned = ("# Q3 Revenue Decline — Findings\n\n"
              "Revenue fell 11% while volume rose 7%. Evidence points to a product-mix "
              "shift after the July release. Recommend restoring the add-on upsell path.")
    res = run_task("q3_revenue_decline", "data_reporting_analyst",
                   brain=get_brain("fake", canned=[canned]))
    print(json.dumps(res, indent=2))
    print("\ntranscript:")
    print(Path(res["transcript"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    _main()
