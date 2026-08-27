"""Scenario engine + information-boundary checks (M3)."""

from worksim.cards import CardLibrary
from worksim.scenario import ScenarioEngine


def _engine():
    lib = CardLibrary()
    return ScenarioEngine(lib.scenario("q3_revenue_decline")), lib


def test_generate_task_shapes_from_role_and_event():
    eng, lib = _engine()
    job = lib.job("data_reporting_analyst")
    task = eng.generate_task(job)
    assert task.scenario == "q3_revenue_decline"
    assert task.required_skills  # inherited from the role's competencies
    assert task.deliverables     # from the role's outputs
    assert task.acceptance_criteria
    assert task.requester == "VP Operations"


def test_task_carries_hidden_truth_but_worker_view_strips_it():
    eng, lib = _engine()
    task = eng.generate_task(lib.job("data_reporting_analyst"))
    assert task.hidden_truth and "product mix" in task.hidden_truth.lower()
    assert "hidden_truth" not in task.worker_view()


def test_broker_serves_documents_but_never_the_truth():
    eng, _ = _engine()
    broker = eng.broker()
    inputs = broker.available_inputs()
    assert "product_mix_q2_q3" in inputs
    # a real document returns its content
    assert "attach rate" in broker.request("product_mix_q2_q3").lower()
    # the conclusion is not requestable, even by a truthy-looking name
    assert "product mix shift" not in broker.request("hidden_truth").lower()
    # ...but the evaluator-only channel exposes it
    assert broker.ground_truth()


def test_unknown_document_returns_actionable_refusal():
    eng, _ = _engine()
    msg = eng.broker().request("does_not_exist")
    assert "no document" in msg.lower()
    assert "escalate" in msg.lower()


def test_generate_task_for_any_role_loads():
    """Task generation must work for every job card Codex authored, not just the two
    reference roles."""
    lib = CardLibrary()
    eng = ScenarioEngine(lib.scenario("q3_revenue_decline"))
    for job in lib.jobs.values():
        task = eng.generate_task(job)
        assert task.task_id.endswith(job.role_id)
