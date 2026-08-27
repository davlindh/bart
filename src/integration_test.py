"""Live integration test — hits every REST endpoint and validates the production fixes."""
import urllib.request
import urllib.error
import json
import time

BASE = "http://localhost:8765"
PASS = []
FAIL = []

def check(name, ok, detail=""):
    if ok:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}" + (f": {detail}" if detail else ""))

def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

def post(path, data):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(BASE + path, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

print("\n=== BART Integration Test Suite ===\n")

# Wait for server to be up
for _ in range(5):
    h = get("/api/health")
    if h: break
    time.sleep(0.5)

# 1. Health endpoint
h = get("/api/health")
check("GET /api/health", h is not None and h.get("status") == "online")
check("Version 3.0.0", h is not None and h.get("version") == "3.0.0",
      f"got {h.get('version') if h else 'None'}")

# 2. Scenarios
sc = get("/api/scenarios")
check("GET /api/scenarios", isinstance(sc, list) and len(sc) == 2)

sc1 = get("/api/scenario/mixed_q3")
check("GET /api/scenario/mixed_q3", sc1 is not None and sc1.get("id") == "mixed_q3")
check("Scenario has transactions", isinstance(sc1.get("transactions"), list) and len(sc1["transactions"]) == 4)

# 3. Graph API with focal_id
g = get("/api/graph?scenario_id=mixed_q3&scope=D1&role=CFO")
check("GET /api/graph (basic)", g is not None and "nodes" in g and "links" in g)
check("Graph returns focal_id", "focal_id" in g, f"keys={list(g.keys()) if g else 'None'}")
check("Graph nodes have financial_impact", any(n.get("financial_impact", 0) > 0 for n in g["nodes"]))

g2 = get("/api/graph?scenario_id=mixed_q3&scope=D2&role=CFO&focal_id=TX-1001")
check("GET /api/graph with focal_id param", g2 is not None and g2.get("focal_id") == "TX-1001")

g3 = get("/api/graph?scenario_id=mixed_q3&scope=D3&role=CFO")
check("Graph D3 scope (meta nodes)", g3 is not None and any(n.get("type") == "meta" for n in g3["nodes"]))

# 4. Context resolve
ctx = post("/api/context/resolve", {
    "role": "CFO", "scope": "D1",
    "purpose": "Skatterevision", "task": "Identifiera momsläckage",
    "target_entity": {"id": "TX-1001", "title": "Automower VMB"}
})
check("POST /api/context/resolve", ctx is not None and "context_id" in ctx)
check("Context has recommended_next_nodes", isinstance(ctx.get("recommended_next_nodes"), list))

# 5. Window audit
audit = post("/api/window/audit", {
    "transactions": sc1["transactions"],
    "input_vat_total": 5400.0,
    "period": "2026-Q3"
})
check("POST /api/window/audit", audit is not None and "total_gross_turnover_sek" in audit)
check("Audit has momsdeklaration", "momsdeklaration" in audit)
check("Audit has observations", isinstance(audit.get("observations"), list))
check("Audit savings > 0", (audit.get("tax_evaluation") or {}).get("total_potential_savings_sek", 0) > 0)

# 6. Agent step
step_res = post("/api/agent/step", {
    "step": "observe", "role": "CFO", "scope": "D1", "context": {}
})
check("POST /api/agent/step", step_res is not None)
check("Step result has output key", step_res is not None and "output" in step_res,
      f"keys={list(step_res.keys()) if step_res else 'None'}")

# 7. Agent full run
run_res = post("/api/agent/run", {"role": "CFO", "scope": "D1", "context": {}})
check("POST /api/agent/run", run_res is not None and "recommendations" in run_res)
check("Agent run has metrics_summary", run_res is not None and "metrics_summary" in run_res)

# 8. Voucher approve
vr = post("/api/voucher/approve", {
    "opportunity_id": "opp_TX-1001",
    "transaction_id": "TX-1001",
    "rule": "VMB_MARGIN_TAX_ML9A",
    "amount": 16000.0,
    "cost": 10000.0
})
check("POST /api/voucher/approve", vr is not None and vr.get("success") is True)
check("Voucher has rows", vr is not None and len(vr.get("record", {}).get("voucher", {}).get("rows", [])) == 3)

# 9. Static files
import urllib.error
for fname in ["index.html", "index.css", "canvas.js", "app.js", "toast.js"]:
    try:
        with urllib.request.urlopen(BASE + "/" + fname, timeout=5) as r:
            size = len(r.read())
            check(f"Static: {fname}", size > 500, f"size={size}")
    except Exception as e:
        check(f"Static: {fname}", False, str(e))

# Summary
total = len(PASS) + len(FAIL)
print(f"\n{'='*40}")
print(f"  {len(PASS)}/{total} passed  |  {len(FAIL)} failed")
if FAIL:
    print(f"  FAILED: {', '.join(FAIL)}")
print(f"{'='*40}\n")
