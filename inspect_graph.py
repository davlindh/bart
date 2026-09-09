import urllib.request, json

r = urllib.request.urlopen('http://localhost:8000/api/graph/nodes')
nodes = json.loads(r.read())
print(f'Total nodes: {len(nodes)}')
for n in nodes:
    dom = n.get('domain', {})
    dom_val = dom.get('value', dom) if isinstance(dom, dict) else dom
    print(f"  {n['id']} | {n['type']} | {dom_val} | {n['label']}")

print()
r2 = urllib.request.urlopen('http://localhost:8000/api/graph/edges')
edges = json.loads(r2.read())
print(f'Total edges: {len(edges)}')
for e in edges:
    print(f"  {e['source']} --[{e['rel_type']}]--> {e['target']}")
