"""Card system checks — the M1 foundation must be solid before anything else.

Run: python -m pytest    (from the repo root)
"""

import pytest

from worksim.cards import CardError, CardLibrary
from worksim.schema import JobCard, TaskPacket


def test_library_loads_repo_cards():
    lib = CardLibrary()
    assert lib.jobs, "expected at least one Job Card"
    assert "data_reporting_analyst" in lib.jobs
    assert "business_systems_analyst" in lib.jobs
    assert lib.employees, "expected at least one employee"
    assert lib.scenarios, "expected at least one scenario"


def test_employee_roles_resolve():
    lib = CardLibrary()
    for emp in lib.employees.values():
        # _check_refs already enforces this at load; assert it explicitly too.
        assert emp.primary_role in lib.jobs


def test_job_card_round_trips_through_yaml(tmp_path):
    lib = CardLibrary()
    jc = lib.job("data_reporting_analyst")
    dumped = jc.model_dump()
    again = JobCard.model_validate(dumped)
    assert again == jc


def test_competency_weights_must_be_unit_range():
    with pytest.raises(ValueError):
        JobCard.model_validate(
            {
                "role_id": "bad",
                "title": "Bad",
                "family": "x",
                "mission": {"summary": "s"},
                "core_competencies": {"sql": 1.5},  # out of 0..1
            }
        )


def test_employee_scores_must_be_0_100():
    from worksim.schema import EmployeeProfile

    with pytest.raises(ValueError):
        EmployeeProfile.model_validate(
            {
                "employee_id": "X",
                "name": "X",
                "primary_role": "data_reporting_analyst",
                "skills": {"sql": 130},  # out of 0..100
            }
        )


def test_missing_card_raises_carderror():
    lib = CardLibrary()
    with pytest.raises(CardError):
        lib.job("does_not_exist")


def test_task_worker_view_strips_hidden_truth():
    task = TaskPacket(
        task_id="T1",
        scenario="q3_revenue_decline",
        title="Investigate decline",
        requester="VP Operations",
        hidden_truth="product mix shift",
    )
    view = task.worker_view()
    assert "hidden_truth" not in view
    assert view["title"] == "Investigate decline"
