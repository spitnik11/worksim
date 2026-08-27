"""Company state + save-file lifecycle checks (M2)."""

from pathlib import Path

import pytest

from worksim.cards import CardLibrary
from worksim.state import CompanyStore


@pytest.fixture()
def scenario():
    return CardLibrary().scenario("q3_revenue_decline")


@pytest.fixture()
def store(tmp_path):
    s = CompanyStore(tmp_path / "worksim.db")
    yield s
    s.close()


def test_create_run_seeds_world_and_moves_cash_to_opening(store, scenario):
    st = store.create_run(scenario)
    assert st.run_id.startswith("run-")
    assert st.opening_cash == 22400000            # from scenario.company['cash']
    assert "cash" not in st.company               # cash left to the ledger's domain
    assert st.get("competitors") == ["NovaWorks", "Ardent Systems"]


def test_run_is_active_and_persists(store, scenario):
    st = store.create_run(scenario)
    assert store.active_run() == st.run_id
    reloaded = store.load(st.run_id)
    assert reloaded.opening_cash == st.opening_cash
    assert reloaded.company == st.company


def test_patch_mutates_world_only(store, scenario):
    st = store.create_run(scenario)
    store.patch(st.run_id, {"customers": 79})
    assert store.load(st.run_id).get("customers") == 79


def test_scenario_swap_has_no_bleed(store, scenario):
    a = store.create_run(scenario, title="save A")
    store.patch(a.run_id, {"customers": 1})
    b = store.create_run(scenario, title="save B")   # a fresh save
    assert store.active_run() == b.run_id
    # New run has original seed, not save A's mutation.
    assert b.get("customers") == 82
    # Switching back resumes save A untouched.
    store.set_active(a.run_id)
    assert store.load(a.run_id).get("customers") == 1


def test_reset_to_scenario_reseeds(store, scenario):
    st = store.create_run(scenario)
    store.patch(st.run_id, {"customers": 5})
    store.reset_to_scenario(st.run_id, scenario)
    assert store.load(st.run_id).get("customers") == 82


def test_load_missing_run_raises(store):
    with pytest.raises(KeyError):
        store.load("run-doesnotexist")
