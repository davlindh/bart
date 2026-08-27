"""Quick validation of server logic without starting HTTP server."""
import sys
sys.path.insert(0, '.')
from src.server import BARTRequestHandler, SCENARIOS

# Create a handler with no request (we call only the internal method)
class FakeHandler(BARTRequestHandler):
    def __init__(self):
        pass  # Skip super().__init__

h = FakeHandler()

# Test 1: financial_impact fields exist on nodes
g = h._generate_graph_data("mixed_q3", "D1", "CFO")
nodes_with_impact = [n for n in g["nodes"] if n.get("financial_impact", 0) > 0]
print(f"[{'PASS' if len(nodes_with_impact) >= 3 else 'FAIL'}] Nodes with financial_impact > 0: {len(nodes_with_impact)}")
for n in nodes_with_impact:
    print(f"   - {n['id']}: {n['financial_impact']} SEK")

# Test 2: focal_id returned
print(f"[{'PASS' if 'focal_id' in g else 'FAIL'}] focal_id in graph response: {g.get('focal_id')}")

# Test 3: focal_id pivot respected
g2 = h._generate_graph_data("mixed_q3", "D2", "CFO", focal_id="TX-1001")
print(f"[{'PASS' if g2.get('focal_id') == 'TX-1001' else 'FAIL'}] focal_id preserved: {g2.get('focal_id')}")

# Test 4: D3 scope has meta node
g3 = h._generate_graph_data("mixed_q3", "D3", "CFO")
meta_nodes = [n for n in g3["nodes"] if n.get("type") == "meta"]
print(f"[{'PASS' if meta_nodes else 'FAIL'}] D3 meta nodes: {len(meta_nodes)}")

# Test 5: version
print(f"[OK] Server validation complete")
