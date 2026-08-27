"""Card system — the save-file layer.

A "card" is an author-written YAML file under `cards/`. The CardLibrary loads them
into id-keyed registries so a scenario can be selected like a save file: pick a
Job Card + Employees + Scenario, and you have a full run context. Reloadable so
editing a YAML and re-running picks up changes without a restart.

Run `python -m worksim.cards` to load the repo's cards/ dir and print a summary
(and fail loudly on any malformed card).
"""

from pathlib import Path
from typing import Type, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from worksim.schema import EmployeeProfile, JobCard, Scenario

# cards/ lives at the repo root, one level above the package.
CARDS_DIR = Path(__file__).resolve().parent.parent / "cards"

M = TypeVar("M", bound=BaseModel)


class CardError(Exception):
    """A card file was missing, unparseable, or failed validation."""


def _load_one(path: Path, model: Type[M]) -> M:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise CardError(f"{path.name}: invalid YAML: {e}") from e
    if not isinstance(raw, dict):
        raise CardError(f"{path.name}: expected a mapping at top level")
    try:
        return model.model_validate(raw)
    except ValidationError as e:
        raise CardError(f"{path.name}: does not match {model.__name__}:\n{e}") from e


def _load_dir(subdir: Path, model: Type[M], id_field: str) -> dict[str, M]:
    out: dict[str, M] = {}
    if not subdir.is_dir():
        return out
    for path in sorted(subdir.glob("*.yaml")):
        card = _load_one(path, model)
        cid = getattr(card, id_field)
        if cid in out:
            raise CardError(f"duplicate {id_field}={cid!r} ({path.name})")
        out[cid] = card
    return out


class CardLibrary:
    """All cards under a root dir, keyed by id. This is the interchangeable
    save-file registry the rest of the app selects from."""

    def __init__(self, root: Path | str = CARDS_DIR):
        self.root = Path(root)
        self.jobs: dict[str, JobCard] = {}
        self.employees: dict[str, EmployeeProfile] = {}
        self.scenarios: dict[str, Scenario] = {}
        self.reload()

    def reload(self) -> "CardLibrary":
        self.jobs = _load_dir(self.root / "jobs", JobCard, "role_id")
        self.employees = _load_dir(self.root / "employees", EmployeeProfile, "employee_id")
        self.scenarios = _load_dir(self.root / "scenarios", Scenario, "scenario_id")
        self._check_refs()
        return self

    def _check_refs(self) -> None:
        """Employees must reference a real primary_role. Warn-free hard check —
        a dangling role is an authoring bug we want surfaced early."""
        for emp in self.employees.values():
            if emp.primary_role not in self.jobs:
                raise CardError(
                    f"employee {emp.employee_id!r} primary_role "
                    f"{emp.primary_role!r} has no matching Job Card"
                )

    def job(self, role_id: str) -> JobCard:
        try:
            return self.jobs[role_id]
        except KeyError:
            raise CardError(f"no Job Card with role_id={role_id!r}") from None

    def employee(self, employee_id: str) -> EmployeeProfile:
        try:
            return self.employees[employee_id]
        except KeyError:
            raise CardError(f"no employee with id={employee_id!r}") from None

    def scenario(self, scenario_id: str) -> Scenario:
        try:
            return self.scenarios[scenario_id]
        except KeyError:
            raise CardError(f"no scenario with id={scenario_id!r}") from None

    def summary(self) -> str:
        return (
            f"{len(self.jobs)} job cards, {len(self.employees)} employees, "
            f"{len(self.scenarios)} scenarios"
        )


def _main() -> None:
    lib = CardLibrary()
    print(f"cards/ -> {lib.summary()}")
    for role_id, jc in lib.jobs.items():
        print(f"  job  {role_id:32} {jc.title}")
    for eid, emp in lib.employees.items():
        print(f"  emp  {eid:32} {emp.name} ({emp.primary_role})")
    for sid, sc in lib.scenarios.items():
        print(f"  scen {sid:32} {sc.title}")


if __name__ == "__main__":
    _main()
