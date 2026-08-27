"""M4 checks — brain interface, personas (hidden-truth safety), and the run loop.
All offline via FakeBrain; no network or API key."""

import json
from pathlib import Path

import pytest

from worksim.brain import FakeBrain, get_brain
from worksim.cards import CardLibrary
from worksim.personas import task_prompt, worker_system
from worksim.run import run_task
from worksim.scenario import ScenarioEngine


# -- brain ----------------------------------------------------------------- #

def test_fake_brain_canned_in_order():
    b = FakeBrain(canned=["one", "two"])
    assert b.complete("s", [{"role": "user", "content": "x"}]) == "one"
    assert b.complete("s", [{"role": "user", "content": "x"}]) == "two"
    with pytest.raises(RuntimeError):
        b.complete("s", [{"role": "user", "content": "x"}])


def test_get_brain_factory():
    assert isinstance(get_brain("fake"), FakeBrain)
    with pytest.raises(ValueError):
        get_brain("nope")


# -- personas: hidden truth must never leak -------------------------------- #

def test_persona_prompts_never_leak_hidden_truth():
    lib = CardLibrary()
    eng = ScenarioEngine(lib.scenario("q3_revenue_decline"))
    job = lib.job("data_reporting_analyst")
    emp = lib.employee("EMP-023")
    task = eng.generate_task(job)
    secret = task.hidden_truth
    assert secret  # sanity: there IS a secret to leak

    sys = worker_system(job, emp)
    prompt = task_prompt(task)
    assert secret not in sys
    assert secret not in prompt
    assert "product mix" not in prompt.lower()  # the conclusion phrasing


def test_worker_system_is_data_driven():
    lib = CardLibrary()
    job = lib.job("business_systems_analyst")
    emp = lib.employee("EMP-014")
    sys = worker_system(job, emp)
    assert "Jordan Lee" in sys
    assert job.title in sys


# -- run loop end to end (offline) ----------------------------------------- #

def test_run_task_produces_deliverable_and_transcript(tmp_path):
    from worksim.state import CompanyStore

    canned = "# Findings\nRevenue mix shifted; recommend restoring the upsell."
    res = run_task(
        "q3_revenue_decline", "data_reporting_analyst",
        brain=FakeBrain(canned=[canned]),
        store=CompanyStore(tmp_path / "db.sqlite"),
        runs_dir=tmp_path / "runs",
    )
    assert res["worker"] == "Priya Nair"           # best-scored for the data role
    deliverable = Path(res["deliverable"])
    assert deliverable.is_file()
    assert deliverable.read_text(encoding="utf-8") == canned

    lines = Path(res["transcript"]).read_text(encoding="utf-8").strip().splitlines()
    kinds = [json.loads(l)["kind"] for l in lines]
    assert kinds == ["request", "assignment", "deliverable"]


def test_run_transcript_never_contains_hidden_truth(tmp_path):
    from worksim.state import CompanyStore

    lib = CardLibrary()
    secret = lib.scenario("q3_revenue_decline").hidden_truth
    res = run_task(
        "q3_revenue_decline", "data_reporting_analyst",
        brain=FakeBrain(canned=["safe generic deliverable text"]),
        store=CompanyStore(tmp_path / "db.sqlite"),
        runs_dir=tmp_path / "runs",
    )
    transcript = Path(res["transcript"]).read_text(encoding="utf-8")
    assert secret not in transcript
