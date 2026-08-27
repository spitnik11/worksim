"""Agent assignment — score every worker against a task, pick primary/support/reviewer.

Implements the weighted score from the design doc (DESIGN-SOURCE.md §16). The weights
are the doc's; each component is computed from data we actually have (JobCard,
EmployeeProfile, TaskPacket), with a few honest heuristics flagged inline where the
schema doesn't carry a perfect signal.

    role match            0.30
    skill match           0.22
    tool match            0.12
    domain knowledge      0.10
    capacity              0.10
    prior performance     0.08
    project continuity    0.05
    development opportunity 0.03
                          -----
                          1.00

Run `python -m worksim.assign` for a self-check.
"""

from dataclasses import dataclass, field
from typing import Optional

from worksim.schema import EmployeeProfile, JobCard, TaskPacket

WEIGHTS = {
    "role": 0.30,
    "skill": 0.22,
    "tool": 0.12,
    "domain": 0.10,
    "capacity": 0.10,
    "performance": 0.08,
    "continuity": 0.05,
    "development": 0.03,
}

_LEVELS = {"junior": 0.4, "mid": 0.7, "senior": 1.0, "lead": 1.0, "principal": 1.0}


def _norm(s: str) -> str:
    return s.strip().lower().replace(" ", "_").replace("-", "_")


def _level_score(level: str) -> float:
    return _LEVELS.get(_norm(level), 0.5)


def _role_match(role_id: str, emp: EmployeeProfile) -> float:
    if emp.primary_role == role_id:
        return 1.0
    if role_id in emp.secondary_roles:
        return 0.6
    return 0.2


def _skill_match(required: dict[str, float], emp: EmployeeProfile) -> float:
    """Weighted overlap of task required_skills (0-1 weights) with employee skills
    (0-100). Neutral 0.5 if the task names no skills."""
    if not required:
        return 0.5
    skills = {_norm(k): v for k, v in emp.skills.items()}
    w_sum = sum(required.values())
    if w_sum <= 0:
        return 0.5
    got = sum(w * (skills.get(_norm(k), 0.0) / 100.0) for k, w in required.items())
    return got / w_sum


def _tool_match(job: JobCard, emp: EmployeeProfile) -> float:
    """ponytail: heuristic — employees carry no tool list in the schema, so a tool
    counts as 'covered' if a same-named token appears among the worker's skills or
    permissions. Good enough to nudge ranking; upgrade to an explicit emp.tools field
    only if it measurably matters."""
    required = job.tools.required
    if not required:
        return 0.5
    have = {_norm(k) for k in emp.skills} | {_norm(k) for k in emp.permissions}
    covered = sum(1 for t in required if _norm(t) in have)
    return covered / len(required)


def _domain(role_id: str, emp: EmployeeProfile) -> float:
    return 0.5 * _role_match(role_id, emp) + 0.5 * _level_score(emp.level)


def _capacity(emp: EmployeeProfile) -> float:
    return min(1.0, max(0.0, emp.capacity.available_hours / 40.0))


def _performance(emp: EmployeeProfile) -> float:
    ph = emp.performance_history
    return 0.5 * (ph.average_quality / 100.0) + 0.5 * ph.task_success_rate


@dataclass
class Assessment:
    employee_id: str
    name: str
    score: float                       # 0-100
    breakdown: dict[str, float] = field(default_factory=dict)


def score_employee(
    job: JobCard,
    emp: EmployeeProfile,
    task: TaskPacket,
    *,
    on_project: Optional[set[str]] = None,
) -> Assessment:
    role_id = job.role_id
    on_project = on_project or set()
    skill = _skill_match(task.required_skills, emp)
    comps = {
        "role": _role_match(role_id, emp),
        "skill": skill,
        "tool": _tool_match(job, emp),
        "domain": _domain(role_id, emp),
        "capacity": _capacity(emp),
        "performance": _performance(emp),
        "continuity": 1.0 if emp.employee_id in on_project else 0.0,
        "development": 1.0 - skill,     # a stretch assignment is a growth opportunity
    }
    total = sum(WEIGHTS[k] * v for k, v in comps.items()) * 100.0
    return Assessment(emp.employee_id, emp.name, round(total, 2), {k: round(v, 3) for k, v in comps.items()})


def rank(
    job: JobCard,
    employees: list[EmployeeProfile],
    task: TaskPacket,
    *,
    on_project: Optional[set[str]] = None,
) -> list[Assessment]:
    scored = [score_employee(job, e, task, on_project=on_project) for e in employees]
    scored.sort(key=lambda a: a.score, reverse=True)
    return scored


@dataclass
class Assignment:
    primary: Optional[Assessment] = None
    support: Optional[Assessment] = None
    reviewer: Optional[Assessment] = None
    needs_independent_reviewer: bool = False
    needs_manager_approval: bool = False
    ranked: list[Assessment] = field(default_factory=list)


def assign(
    job: JobCard,
    employees: list[EmployeeProfile],
    task: TaskPacket,
    *,
    on_project: Optional[set[str]] = None,
    risk: float = 0.0,
    emp_by_id: Optional[dict[str, EmployeeProfile]] = None,
) -> Assignment:
    """Pick primary (top score), support (runner-up), and an independent reviewer
    (highest-scoring worker whose primary_role differs from the primary's, for a fresh
    perspective — falls back to the runner-up). Risk gates follow the doc (§16)."""
    ranked = rank(job, employees, task, on_project=on_project)
    result = Assignment(
        ranked=ranked,
        needs_independent_reviewer=risk >= 0.70,
        needs_manager_approval=risk >= 0.90,
    )
    if not ranked:
        return result
    result.primary = ranked[0]
    if len(ranked) > 1:
        result.support = ranked[1]

    emp_by_id = emp_by_id or {e.employee_id: e for e in employees}
    primary_role = emp_by_id[ranked[0].employee_id].primary_role
    for a in ranked[1:]:
        if emp_by_id[a.employee_id].primary_role != primary_role:
            result.reviewer = a
            break
    if result.reviewer is None:
        result.reviewer = result.support
    return result


def _main() -> None:
    from worksim.cards import CardLibrary

    lib = CardLibrary()
    employees = list(lib.employees.values())
    job = lib.job("data_reporting_analyst")
    task = TaskPacket(
        task_id="T-demo",
        scenario="q3_revenue_decline",
        title="Investigate Q3 revenue decline",
        requester="VP Operations",
        priority="high",
        required_skills={"data_analysis": 0.9, "sql": 0.8, "communication": 0.6},
    )
    result = assign(job, employees, task, risk=0.4)
    print(f"task role = {job.role_id}")
    for a in result.ranked:
        print(f"  {a.score:6.2f}  {a.employee_id:8} {a.name}")
    print(f"primary  = {result.primary.name}")
    print(f"support  = {result.support.name if result.support else None}")
    print(f"reviewer = {result.reviewer.name if result.reviewer else None}")


if __name__ == "__main__":
    _main()
