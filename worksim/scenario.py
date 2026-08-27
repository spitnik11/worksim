"""Scenario engine — turn scenario events into tasks, and enforce the info boundary.

Two jobs (DESIGN-SOURCE.md §17-20):

1. **Task generation.** An event becomes a `TaskPacket` shaped for a target role: the
   role's competencies become the task's required_skills, the role's outputs become the
   expected deliverables, and the scenario's `hidden_truth` rides along on the packet
   (engine-only) so the Evaluator can grade against ground truth.

2. **Information boundary.** No agent gets the whole truth. The `InformationBroker`
   serves scenario `documents` on request (the raw evidence a worker must synthesize)
   but NEVER serves `hidden_truth` — that is the conclusion, exposed only to the
   Evaluator via `ground_truth()`.

Run `python -m worksim.scenario` for a self-check.
"""

from dataclasses import dataclass
from typing import Any, Optional

from worksim.schema import JobCard, Scenario, TaskPacket

# Generic acceptance criteria applied to every generated task. Role-specific criteria
# get layered on from the job card's KPIs. (M4 personas/evaluator can refine further.)
_BASE_CRITERIA = [
    "identify the primary driver and support it with evidence",
    "quantify the business impact",
    "recommend a clear next action",
]


class InformationBroker:
    """Serves requestable evidence for one scenario while hiding the conclusion."""

    def __init__(self, scenario: Scenario):
        self._docs = dict(scenario.documents)
        self._truth = scenario.hidden_truth or ""

    def available_inputs(self) -> list[str]:
        return sorted(self._docs)

    def request(self, name: str) -> str:
        """Return a document's content, or a refusal a worker must act on (ask/escalate).
        Never returns the hidden truth, even if asked for it by name."""
        if name in self._docs:
            return self._docs[name]
        return (
            f"No document named {name!r} is available. Request one of "
            f"{self.available_inputs()} or escalate to the requester."
        )

    def ground_truth(self) -> str:
        """Evaluator-only. Do NOT call this from persona/worker code paths."""
        return self._truth


@dataclass
class ScenarioEngine:
    scenario: Scenario

    def events(self) -> list[dict[str, Any]]:
        return self.scenario.events

    def broker(self) -> InformationBroker:
        return InformationBroker(self.scenario)

    def generate_task(self, job: JobCard, event_id: Optional[str] = None) -> TaskPacket:
        """Build a TaskPacket for `job` from a scenario event (first event by default)."""
        event = self._pick_event(event_id)
        required = dict(job.core_competencies)  # task inherits the role's competency weights
        deliverables = job.outputs[:3] if job.outputs else []
        criteria = _BASE_CRITERIA + [f"address KPI: {k}" for k in job.kpis[:2]]
        return TaskPacket(
            task_id=f"{self.scenario.scenario_id}:{event.get('id', 'event')}:{job.role_id}",
            scenario=self.scenario.scenario_id,
            title=self._title(event, job),
            requester=event.get("requester", "Management"),
            priority=event.get("priority", "high"),
            business_context=(event.get("summary") or self.scenario.summary or "").strip(),
            required_skills=required,
            inputs=self.broker().available_inputs(),
            deliverables=deliverables,
            acceptance_criteria=criteria,
            deadline=event.get("deadline", "1 simulated day"),
            hidden_truth=self.scenario.hidden_truth,  # engine-only; worker_view() strips it
        )

    # -- helpers ---------------------------------------------------------- #

    def _pick_event(self, event_id: Optional[str]) -> dict[str, Any]:
        if not self.scenario.events:
            return {"id": "start", "summary": self.scenario.summary}
        if event_id is None:
            return self.scenario.events[0]
        for e in self.scenario.events:
            if e.get("id") == event_id:
                return e
        raise KeyError(f"no event {event_id!r} in scenario {self.scenario.scenario_id!r}")

    @staticmethod
    def _title(event: dict[str, Any], job: JobCard) -> str:
        summary = (event.get("summary") or "").strip().replace("\n", " ")
        short = (summary[:60] + "…") if len(summary) > 60 else summary
        return short or f"{job.title} task"


def _main() -> None:
    from worksim.cards import CardLibrary

    lib = CardLibrary()
    eng = ScenarioEngine(lib.scenario("q3_revenue_decline"))
    job = lib.job("data_reporting_analyst")
    task = eng.generate_task(job)
    print(f"task {task.task_id}")
    print(f"  requester : {task.requester}  priority : {task.priority}")
    print(f"  required  : {sorted(task.required_skills)}")
    print(f"  inputs    : {task.inputs}")
    print(f"  worker_view has hidden_truth? {'hidden_truth' in task.worker_view()}")
    broker = eng.broker()
    print(f"  request(product_mix_q2_q3): {broker.request('product_mix_q2_q3')[:70]}...")
    print(f"  request(secret_answer): {broker.request('secret_answer')[:60]}...")


if __name__ == "__main__":
    _main()
