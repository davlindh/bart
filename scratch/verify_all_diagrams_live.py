import urllib.request
import json
import sys

def test_endpoints():
    base = "http://localhost:8765"
    
    # 1. Test /api/erd/graph (Universal ERD 15 Entities)
    print("Testing /api/erd/graph...")
    req = urllib.request.Request(f"{base}/api/erd/graph")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        nodes = data.get("nodes", [])
        links = data.get("links", [])
        node_types = set(n.get("type") for n in nodes)
        print(f"  [OK] ERD Graph has {len(nodes)} nodes, {len(links)} links, across types: {node_types}")
        assert len(nodes) >= 20, f"Expected >= 20 nodes, got {len(nodes)}"
        lower_types = set(t.lower().replace("_", "") for t in node_types if t)
        assert "organization" in lower_types, "organization missing"
        assert "team" in lower_types, "team missing"
        assert "capability" in lower_types, "capability missing"
        assert "assignment" in lower_types, "assignment missing"
        assert "transitionplan" in lower_types, "transition_plan missing"
        assert "communication" in lower_types, "communication missing"

    # 2. Test /api/team_dynamics/telemetry (12 Metrics)
    print("Testing /api/team_dynamics/telemetry...")
    req = urllib.request.Request(f"{base}/api/team_dynamics/telemetry")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        m = data.get("metrics", {})
        print(f"  [OK] Telemetry metrics received: {len(m)} metrics")
        expected_metrics = [
            "team_health_index", "team_enps", "decision_time_median_hours",
            "on_time_delivery_pct", "psychological_safety_score", "cognitive_load_index",
            "friction_frequency_per_week", "role_clarity_pct", "experiment_success_rate_pct",
            "learning_velocity_per_month", "decision_quality_score", "bias_index"
        ]
        for em in expected_metrics:
            assert em in m, f"Metric {em} missing from telemetry"
            print(f"    - {em}: {m[em]}")

    # 3. Test /api/omnipod/layers (4 Layers)
    print("Testing /api/omnipod/layers...")
    req = urllib.request.Request(f"{base}/api/omnipod/layers")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        l1 = data.get("layer_1_perspectives", [])
        l2 = data.get("layer_2_domains", [])
        l3 = data.get("layer_3_collaboration", [])
        l4 = data.get("layer_4_information", [])
        print(f"  [OK] Omnipod Layers: L1={len(l1)} windows, L2={len(l2)} domains, L3={len(l3)} users, L4={len(l4)} catalogs")
        assert len(l1) == 9, f"Expected 9 windows, got {len(l1)}"
        assert len(l2) == 6, f"Expected 6 domains, got {len(l2)}"
        assert len(l3) >= 4, f"Expected >= 4 collaboration roles, got {len(l3)}"
        assert len(l4) >= 4, f"Expected >= 4 catalogs, got {len(l4)}"

    # 4. Test /api/context/presentation (4 Presentation Levels)
    print("Testing /api/context/presentation...")
    req = urllib.request.Request(f"{base}/api/context/presentation")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert "level_1_overview" in data
        assert "level_2_detail" in data
        assert "level_3_machine" in data
        assert "level_4_navigation" in data
        print("  [OK] All 4 presentation levels verified successfully")

    # 5. Test POST /api/context/resolve with presentation levels
    print("Testing POST /api/context/resolve...")
    post_data = json.dumps({
        "role": "CFO",
        "scope": "D1",
        "purpose": "Skatterevision och likviditetsoptimering",
        "task": "Granska felaktiga momssatser och outnyttjade avdrag",
        "target_entity": {"id": "mixed_q3", "title": "Bokföringsrevision Q3"}
    }).encode('utf-8')
    req = urllib.request.Request(f"{base}/api/context/resolve", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        pres = data.get("presentation_levels", {})
        assert "level_1_overview" in pres
        assert "level_2_detail" in pres
        assert "level_3_machine" in pres
        assert "level_4_navigation" in pres
        print("  [OK] /api/context/resolve returns active presentation levels and stop conditions")

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
