"""WorkSim web app — FastAPI + /api/v1 + single-file UI.

Run (M5+): uvicorn worksim.app:app --host 127.0.0.1 --port 8500

The run lifecycle is not wired yet (blocked on M3/M4). `/api/v1/health` and
`GET /` (the shell) are live. Every other `/api/v1` route is a 501 stub whose
`todo` string is the proposed contract. Agree the list in TASKS.md before
replacing a stub with a real call — do not wire live data from this file
until then.
"""

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

WEB_DIR = Path(__file__).resolve().parent / "web"

api = APIRouter(prefix="/api/v1")


def _todo(what: str) -> JSONResponse:
    return JSONResponse({"ok": False, "todo": what}, status_code=501)


# --------------------------------------------------------------------------- #
# Live                                                                         #
# --------------------------------------------------------------------------- #

@api.get("/health")
def health() -> dict:
    return {"ok": True, "service": "worksim"}


# --------------------------------------------------------------------------- #
# Card library — stubbed until the M5 contract is agreed                       #
# --------------------------------------------------------------------------- #

@api.get("/scenarios")
def list_scenarios() -> JSONResponse:
    return _todo("GET scenarios: [{scenario_id, title, summary, company}] from CardLibrary")


@api.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> JSONResponse:
    return _todo(f"GET scenario {scenario_id!r} (strip hidden_truth before serving)")


@api.get("/jobs")
def list_jobs() -> JSONResponse:
    return _todo("GET jobs: [{role_id, title, family, level}] from CardLibrary")


@api.get("/employees")
def list_employees() -> JSONResponse:
    return _todo("GET employees: [{employee_id, name, primary_role, level}] from CardLibrary")


# --------------------------------------------------------------------------- #
# Runs — stubbed; create_run lives in Claude's state.py                        #
# --------------------------------------------------------------------------- #

@api.post("/runs")
async def create_run(request: Request) -> JSONResponse:
    return _todo("POST /runs {scenario_id, title?} → CompanyStore.create_run; blocked on M3/M4")


@api.get("/runs")
def list_runs() -> JSONResponse:
    return _todo("GET /runs: [{run_id, scenario_id, title, status, created_at}]")


@api.get("/runs/{run_id}")
def get_run(run_id: str) -> JSONResponse:
    return _todo(f"GET /runs/{run_id} CompanyState snapshot + status; cash is money.py's job")


@api.post("/runs/{run_id}/start")
def start_run(run_id: str) -> JSONResponse:
    return _todo(f"POST /runs/{run_id}/start — scenario engine kickoff; blocked on M3/M4")


@api.post("/runs/{run_id}/stop")
def stop_run(run_id: str) -> JSONResponse:
    return _todo(f"POST /runs/{run_id}/stop")


# Transcript polling (NOT SSE). UI polls ?since=N against runs/<id>/transcript.jsonl
# Proposed shape: {messages:[{seq, ts, speaker, role, text}], next_since: int}

@api.get("/runs/{run_id}/messages")
def run_messages(run_id: str, since: int = 0) -> JSONResponse:
    return _todo(
        f"GET /runs/{run_id}/messages?since={since} "
        "→ {messages:[{seq,ts,speaker,role,text}], next_since}; blocked on M3/M4"
    )


@api.post("/runs/{run_id}/messages")
async def post_message(run_id: str, request: Request) -> JSONResponse:
    return _todo(f"POST /runs/{run_id}/messages {{text}} operator chat; blocked on M3/M4")


@api.get("/runs/{run_id}/deliverables")
def list_deliverables(run_id: str) -> JSONResponse:
    return _todo(f"GET /runs/{run_id}/deliverables list of files in runs/<id>/deliverables/")


@api.get("/runs/{run_id}/deliverables/{name}")
def get_deliverable(run_id: str, name: str) -> JSONResponse:
    return _todo(f"GET /runs/{run_id}/deliverables/{name} download; Codex renderers")


@api.get("/runs/{run_id}/money")
def run_money(run_id: str) -> JSONResponse:
    return _todo(
        f"GET /runs/{run_id}/money {{opening_cash, balance, entries}} "
        "(Codex money.py: balance = opening_cash + SUM(ledger))"
    )


app = FastAPI(title="WorkSim", version="0.0.1")
app.include_router(api)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
