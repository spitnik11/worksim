"""Per-run bank ledger backed by the WorkSim SQLite database."""

from pathlib import Path
from typing import Any

from worksim.state import DB_PATH, connect, init_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id   TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    amount   REAL NOT NULL,
    reason   TEXT NOT NULL,
    kind     TEXT NOT NULL CHECK (kind IN ('income', 'cost')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ledger_run_id ON ledger(run_id, entry_id);
"""


class MoneyStore:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.conn = connect(db_path)
        init_db(self.conn)
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def add_entry(self, run_id: str, amount: float, reason: str, kind: str) -> dict[str, Any]:
        if kind not in {"income", "cost"}:
            raise ValueError("kind must be 'income' or 'cost'")
        if not reason.strip():
            raise ValueError("reason must not be empty")
        signed_amount = abs(float(amount)) * (1 if kind == "income" else -1)
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO ledger(run_id, amount, reason, kind) VALUES (?,?,?,?)",
                (run_id, signed_amount, reason.strip(), kind),
            )
        return dict(self.conn.execute(
            "SELECT * FROM ledger WHERE entry_id=?", (cursor.lastrowid,)
        ).fetchone())

    def entries(self, run_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.conn.execute(
            "SELECT * FROM ledger WHERE run_id=? ORDER BY entry_id", (run_id,)
        )]

    def balance(self, run_id: str) -> float:
        opening = self._opening_cash(run_id)
        delta = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM ledger WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        return opening + delta

    def summary(self, run_id: str) -> dict[str, float]:
        opening = self._opening_cash(run_id)
        income, costs = self.conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN amount > 0 THEN amount END), 0), "
            "COALESCE(-SUM(CASE WHEN amount < 0 THEN amount END), 0) "
            "FROM ledger WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return {
            "opening_cash": opening,
            "income": income,
            "costs": costs,
            "balance": opening + income - costs,
        }

    def _opening_cash(self, run_id: str) -> float:
        row = self.conn.execute(
            "SELECT opening_cash FROM company_state WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no company_state for run_id={run_id!r}")
        return row[0]
