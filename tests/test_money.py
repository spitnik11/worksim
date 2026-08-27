"""Bank ledger arithmetic checks."""

import pytest

from worksim.cards import CardLibrary
from worksim.money import MoneyStore
from worksim.state import CompanyStore


@pytest.fixture()
def ledger(tmp_path):
    db_path = tmp_path / "worksim.db"
    company = CompanyStore(db_path)
    run = company.create_run(CardLibrary().scenario("q3_revenue_decline"))
    company.close()
    money = MoneyStore(db_path)
    yield money, run
    money.close()


def test_income_cost_and_balance(ledger):
    money, run = ledger
    money.add_entry(run.run_id, 5_000, "Client payment", "income")
    money.add_entry(run.run_id, 1_250, "Software", "cost")

    assert [entry["amount"] for entry in money.entries(run.run_id)] == [5_000, -1_250]
    assert money.balance(run.run_id) == run.opening_cash + 3_750
    assert money.summary(run.run_id) == {
        "opening_cash": run.opening_cash,
        "income": 5_000,
        "costs": 1_250,
        "balance": run.opening_cash + 3_750,
    }


def test_entry_validation(ledger):
    money, run = ledger
    with pytest.raises(ValueError):
        money.add_entry(run.run_id, 1, "", "income")
    with pytest.raises(ValueError):
        money.add_entry(run.run_id, 1, "Adjustment", "other")
