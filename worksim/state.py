"""Company state — the persisted world a scenario runs in.

Raw sqlite3 (no ORM), mirroring Trawl's `core/store.py` style: a module-level SCHEMA
string plus a MIGRATIONS list of guarded `ALTER TABLE ADD COLUMN`. DB at `data/worksim.db`.

Save-file model: **each run is its own row.** Creating a run seeds a fresh company
snapshot from a Scenario, so swapping scenarios never bleeds state between saves. One
run is `active` at a time; switching the active run resumes that save.

Seam with money.py (M2, Codex): **cash is NOT owned here.** state.py seeds the opening
cash figure (`opening_cash`) from `Scenario.company['cash']`; the live bank balance is
`opening_cash + sum(ledger entries)`, computed by money.py. CompanyState mutations here
cover everything else (customers, markets, products, projects, risks, competitors).

Run `python -m worksim.state` for a self-check.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from worksim.schema import Scenario

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "worksim.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'open',
    active      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS company_state (
    run_id       TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
    scenario_id  TEXT NOT NULL,
    opening_cash REAL NOT NULL DEFAULT 0,
    data         TEXT NOT NULL DEFAULT '{}',   -- JSON: company world minus live cash
    updated_at   TEXT NOT NULL
);
"""

# (column, type-with-default) — applied idempotently via guarded ALTER TABLE.
MIGRATIONS: list[tuple[str, str, str]] = [
    # ("company_state", "new_col", "TEXT DEFAULT ''"),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_run_id() -> str:
    return "run-" + uuid.uuid4().hex[:12]


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for table, col, decl in MIGRATIONS:
        if col not in _existing_columns(conn, table):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    conn.commit()


@dataclass
class CompanyState:
    """A snapshot of one run's world. `company` is the flexible blob (customers,
    markets, products, projects, risks, competitors, ...). Cash is opening-only here."""

    run_id: str
    scenario_id: str
    opening_cash: float = 0.0
    company: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.company.get(key, default)


class CompanyStore:
    """Persistence + save-file lifecycle for company state."""

    def __init__(self, db_path: Path | str = DB_PATH):
        self.conn = connect(db_path)
        init_db(self.conn)

    def close(self) -> None:
        self.conn.close()

    # -- lifecycle -------------------------------------------------------- #

    def create_run(self, scenario: Scenario, title: str = "", make_active: bool = True) -> CompanyState:
        run_id = _new_run_id()
        seed = json.loads(json.dumps(scenario.company or {}))  # deep copy off the card
        opening_cash = float(seed.pop("cash", 0) or 0)          # cash moves to the ledger's domain
        now = _now()
        with self.conn:
            self.conn.execute(
                "INSERT INTO runs(run_id, scenario_id, title, status, active, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (run_id, scenario.scenario_id, title or scenario.title, "open", 0, now),
            )
            self.conn.execute(
                "INSERT INTO company_state(run_id, scenario_id, opening_cash, data, updated_at) "
                "VALUES (?,?,?,?,?)",
                (run_id, scenario.scenario_id, opening_cash, json.dumps(seed), now),
            )
        if make_active:
            self.set_active(run_id)
        return self.load(run_id)

    def reset_to_scenario(self, run_id: str, scenario: Scenario) -> CompanyState:
        """Clean reload: re-seed an existing run's world from the scenario card."""
        seed = json.loads(json.dumps(scenario.company or {}))
        opening_cash = float(seed.pop("cash", 0) or 0)
        with self.conn:
            self.conn.execute(
                "UPDATE company_state SET scenario_id=?, opening_cash=?, data=?, updated_at=? "
                "WHERE run_id=?",
                (scenario.scenario_id, opening_cash, json.dumps(seed), _now(), run_id),
            )
        return self.load(run_id)

    # -- read/write ------------------------------------------------------- #

    def load(self, run_id: str) -> CompanyState:
        row = self.conn.execute(
            "SELECT * FROM company_state WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no company_state for run_id={run_id!r}")
        return CompanyState(
            run_id=row["run_id"],
            scenario_id=row["scenario_id"],
            opening_cash=row["opening_cash"],
            company=json.loads(row["data"]),
        )

    def save(self, state: CompanyState) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE company_state SET opening_cash=?, data=?, updated_at=? WHERE run_id=?",
                (state.opening_cash, json.dumps(state.company), _now(), state.run_id),
            )

    def patch(self, run_id: str, changes: dict[str, Any]) -> CompanyState:
        """Shallow top-level merge into the company world (scenario events / task
        outcomes call this). Returns the updated snapshot."""
        state = self.load(run_id)
        state.company.update(changes)
        self.save(state)
        return state

    # -- active-run pointer (the "which save is loaded" seam) ------------- #

    def set_active(self, run_id: str) -> None:
        with self.conn:
            self.conn.execute("UPDATE runs SET active=0 WHERE active=1")
            self.conn.execute("UPDATE runs SET active=1 WHERE run_id=?", (run_id,))

    def active_run(self) -> Optional[str]:
        row = self.conn.execute("SELECT run_id FROM runs WHERE active=1").fetchone()
        return row["run_id"] if row else None

    def list_runs(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC"
        )]

    def opening_cash(self, run_id: str) -> float:
        """The ledger's opening balance for this run (money.py builds on this)."""
        return self.load(run_id).opening_cash


def _main() -> None:
    import tempfile
    from worksim.cards import CardLibrary

    lib = CardLibrary()
    scen = next(iter(lib.scenarios.values()))
    with tempfile.TemporaryDirectory() as tmp:
        store = CompanyStore(Path(tmp) / "t.db")
        st = store.create_run(scen)
        print(f"created {st.run_id} from {scen.scenario_id}: opening_cash={st.opening_cash:,.0f}")
        print(f"  world keys: {sorted(st.company)}")
        store.patch(st.run_id, {"customers": 79})
        print(f"  active run = {store.active_run()}; customers now {store.load(st.run_id).get('customers')}")
        store.close()


if __name__ == "__main__":
    _main()
