"""WorkSim data schemas.

The core rule of this project: **job descriptions are DATA, not prompts.** Every
Job Card, Employee Profile, Task Packet, and Scenario is an author-written YAML
file validated against the pydantic models below. If a card is malformed, we want
a loud, precise error at load time (Codex/Grok author these by hand), so validation
lives here rather than being hand-rolled at each call site.

Two scales are used deliberately and must not be confused:
  - Job Card `core_competencies` and Task `required_skills` are 0.0-1.0 weights
    (how important a skill is to the role / task).
  - Employee `skills` and `traits` are 0-100 proficiency scores (how good a
    particular worker is).
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _all_in_unit_range(d: dict[str, float]) -> dict[str, float]:
    for k, v in d.items():
        if not 0.0 <= float(v) <= 1.0:
            raise ValueError(f"weight {k}={v} must be within 0.0-1.0")
    return d


def _all_in_0_100(d: dict[str, float]) -> dict[str, float]:
    for k, v in d.items():
        if not 0.0 <= float(v) <= 100.0:
            raise ValueError(f"score {k}={v} must be within 0-100")
    return d


# --------------------------------------------------------------------------- #
# Job Card                                                                     #
# --------------------------------------------------------------------------- #

class Mission(BaseModel):
    summary: str


class Tools(BaseModel):
    required: list[str] = Field(default_factory=list)
    common: list[str] = Field(default_factory=list)


class Handoffs(BaseModel):
    receives_from: list[str] = Field(default_factory=list)
    sends_to: list[str] = Field(default_factory=list)


class JobCard(BaseModel):
    """What a position normally does. The save-file's role contract."""

    role_id: str
    title: str
    family: str
    level: str = "junior"
    department: Optional[str] = None

    mission: Mission
    business_value: list[str] = Field(default_factory=list)

    core_competencies: dict[str, float] = Field(default_factory=dict)
    tools: Tools = Field(default_factory=Tools)
    daily_workflows: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    handoffs: Handoffs = Field(default_factory=Handoffs)

    simulation_permissions: dict[str, bool] = Field(default_factory=dict)
    escalation_rules: list[str] = Field(default_factory=list)
    task_archetypes: list[str] = Field(default_factory=list)

    _check_competencies = field_validator("core_competencies")(_all_in_unit_range)


# --------------------------------------------------------------------------- #
# Employee / Agent Profile                                                     #
# --------------------------------------------------------------------------- #

class Capacity(BaseModel):
    available_hours: float = 40.0


class PerformanceHistory(BaseModel):
    task_success_rate: float = 0.0
    average_quality: float = 0.0


class EmployeeProfile(BaseModel):
    """How good a particular simulated worker is at their role(s)."""

    employee_id: str
    name: str
    primary_role: str  # -> JobCard.role_id
    secondary_roles: list[str] = Field(default_factory=list)
    level: str = "junior"

    skills: dict[str, float] = Field(default_factory=dict)   # 0-100
    traits: dict[str, float] = Field(default_factory=dict)   # 0-100
    capacity: Capacity = Field(default_factory=Capacity)
    permissions: dict[str, str] = Field(default_factory=dict)
    performance_history: PerformanceHistory = Field(default_factory=PerformanceHistory)

    _check_skills = field_validator("skills")(_all_in_0_100)
    _check_traits = field_validator("traits")(_all_in_0_100)


# --------------------------------------------------------------------------- #
# Task Packet                                                                  #
# --------------------------------------------------------------------------- #

class TaskPacket(BaseModel):
    """A specific piece of work. `hidden_truth` is engine-only and must be
    stripped before anything reaches a persona (see personas.py)."""

    task_id: str
    scenario: str
    title: str
    requester: str
    priority: str = "medium"
    business_context: str = ""

    required_skills: dict[str, float] = Field(default_factory=dict)
    inputs: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    deadline: str = ""

    hidden_truth: Optional[str] = None  # engine-only; never shown to workers

    _check_required = field_validator("required_skills")(_all_in_unit_range)

    def worker_view(self) -> dict[str, Any]:
        """Serialization safe to hand to a persona: hidden_truth removed."""
        return self.model_dump(exclude={"hidden_truth"})


# --------------------------------------------------------------------------- #
# Scenario                                                                     #
# --------------------------------------------------------------------------- #

class Scenario(BaseModel):
    """The business context that produces tasks. `company` seeds CompanyState
    (formalized in state.py at M2); kept as a flexible mapping for now so the
    scenario engine and money system can evolve the shape without a schema churn.
    """

    scenario_id: str
    title: str
    summary: str = ""
    company: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    # Requestable evidence: name -> content. A worker may request these by name
    # (the information broker serves them); they hold the raw evidence a worker must
    # synthesize. Distinct from `hidden_truth`, which is the conclusion and is never served.
    documents: dict[str, str] = Field(default_factory=dict)
    hidden_truth: Optional[str] = None  # engine-only
