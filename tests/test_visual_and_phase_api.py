"""Verification test for newly expanded endpoints: constellation, evolutionary phase advance, and ERD node injection."""

import urllib.request
import json

BASE_URL = "http://localhost:8765"

def test_constellation_api():
    req = urllib.request.Request(f"{BASE_URL}/api/agents/constellation")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "constellation" in data
        assert data["count"] == 12
        assert data["constellation"][0]["id"] == "ObserverAgent"
        assert data["constellation"][11]["id"] == "MetaLearningAgent"

def test_orchestrator_phase_advance():
    payload = json.dumps({
        "current_window": "W5",
        "previous_outcome": {"freed_capacity_sek": 18800.0, "current_status": "CONVERGED_STABLE"}
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/orchestrator/phase/advance", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "phase_id" in data
        assert data["window_id"] == "W8"
        assert "target_entity" in data

def test_erd_node_create():
    payload = json.dumps({
        "id": "exp_battery_diagnostics_unit_test",
        "name": "Batteridiagnostik Test",
        "type": "Experiment",
        "domain": "Tools",
        "linked_to": "TX-1001",
        "relation": "MONITORS"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/erd/node/create", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["success"] is True
        assert data["node"]["id"] == "exp_battery_diagnostics_unit_test"

    # Verify presence in /api/erd/graph
    req_erd = urllib.request.Request(f"{BASE_URL}/api/erd/graph")
    with urllib.request.urlopen(req_erd) as resp:
        assert resp.status == 200
        erd = json.loads(resp.read().decode("utf-8"))
        node_ids = [n["id"] for n in erd["nodes"]]
        assert "exp_battery_diagnostics_unit_test" in node_ids
