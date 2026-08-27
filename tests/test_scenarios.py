"""New scenario content — load, evidence docs, hidden_truth stays engine-only."""

from worksim.cards import CardLibrary
from worksim.scenario import ScenarioEngine

NEW_SCENARIOS = (
    "five_users_app_down",
    "support_ai_prompt_ship",
    "crm_migration_500",
)

# Phrases that are the *conclusion*, not raw evidence. Must not leak into documents.
CONCLUSION_MARKERS = {
    "five_users_app_down": "not an outage and not five independent problems",
    "support_ai_prompt_ship": "Do not ship v3.4",
    "crm_migration_500": "executive wish, not a feasible plan",
}


def test_new_scenarios_load_with_company_events_docs_and_truth():
    lib = CardLibrary()
    for sid in NEW_SCENARIOS:
        sc = lib.scenario(sid)
        assert sc.title
        assert sc.summary
        assert sc.company.get("cash") is not None
        assert sc.company.get("name")
        assert sc.events, sid
        assert sc.documents, sid
        assert sc.hidden_truth, sid
        for event in sc.events:
            assert event.get("id")
            assert event.get("trigger")
            assert event.get("requester")
            assert event.get("summary")


def test_hidden_truth_is_not_in_any_document():
    lib = CardLibrary()
    for sid, marker in CONCLUSION_MARKERS.items():
        sc = lib.scenario(sid)
        blob = " ".join(sc.documents.values()).lower()
        assert marker.lower() not in blob, f"{sid}: conclusion leaked into documents"
        assert marker.lower() in (sc.hidden_truth or "").lower()


def test_broker_serves_docs_not_truth_for_new_scenarios():
    lib = CardLibrary()
    for sid in NEW_SCENARIOS:
        eng = ScenarioEngine(lib.scenario(sid))
        broker = eng.broker()
        assert broker.available_inputs()
        assert broker.ground_truth()
        assert "no document" in broker.request("hidden_truth").lower()
        first = broker.available_inputs()[0]
        body = broker.request(first)
        assert body
        assert "no document" not in body.lower()
