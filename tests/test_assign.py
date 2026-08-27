"""Assignment scoring checks (M3)."""

from worksim.assign import WEIGHTS, assign, rank, score_employee
from worksim.cards import CardLibrary
from worksim.schema import TaskPacket


def _lib():
    return CardLibrary()


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_data_task_favors_the_data_analyst():
    lib = _lib()
    job = lib.job("data_reporting_analyst")
    task = TaskPacket(
        task_id="T1", scenario="s", title="analyze", requester="VP",
        required_skills={"data_analysis": 0.9, "sql": 0.8, "communication": 0.6},
    )
    result = assign(job, list(lib.employees.values()), task)
    assert result.primary.employee_id == "EMP-023"  # Priya, primary data analyst


def test_bsa_task_favors_the_bsa():
    lib = _lib()
    job = lib.job("business_systems_analyst")
    task = TaskPacket(
        task_id="T2", scenario="s", title="requirements", requester="Finance",
        required_skills={"requirements_analysis": 0.9, "documentation": 0.8, "testing": 0.6},
    )
    result = assign(job, list(lib.employees.values()), task)
    assert result.primary.employee_id == "EMP-014"  # Jordan, primary BSA


def test_reviewer_is_independent_when_possible():
    lib = _lib()
    job = lib.job("data_reporting_analyst")
    task = TaskPacket(
        task_id="T3", scenario="s", title="analyze", requester="VP",
        required_skills={"data_analysis": 0.9},
    )
    result = assign(job, list(lib.employees.values()), task)
    # primary = data analyst; reviewer should have a different primary_role.
    prim = lib.employee(result.primary.employee_id)
    rev = lib.employee(result.reviewer.employee_id)
    assert rev.primary_role != prim.primary_role


def test_risk_gates_flag():
    lib = _lib()
    job = lib.job("data_reporting_analyst")
    task = TaskPacket(task_id="T4", scenario="s", title="x", requester="y")
    low = assign(job, list(lib.employees.values()), task, risk=0.3)
    hi = assign(job, list(lib.employees.values()), task, risk=0.75)
    crit = assign(job, list(lib.employees.values()), task, risk=0.95)
    assert not low.needs_independent_reviewer
    assert hi.needs_independent_reviewer and not hi.needs_manager_approval
    assert crit.needs_manager_approval


def test_score_is_0_100_and_has_breakdown():
    lib = _lib()
    job = lib.job("data_reporting_analyst")
    emp = lib.employee("EMP-023")
    task = TaskPacket(task_id="T5", scenario="s", title="x", requester="y",
                      required_skills={"sql": 1.0})
    a = score_employee(job, emp, task)
    assert 0.0 <= a.score <= 100.0
    assert set(a.breakdown) == set(WEIGHTS)


def test_continuity_bumps_score():
    lib = _lib()
    job = lib.job("data_reporting_analyst")
    emp = lib.employee("EMP-023")
    task = TaskPacket(task_id="T6", scenario="s", title="x", requester="y",
                      required_skills={"sql": 1.0})
    base = score_employee(job, emp, task).score
    bumped = score_employee(job, emp, task, on_project={"EMP-023"}).score
    assert bumped > base
