# REPL State Persistence & Namespace Management Patterns

This guide details best practices for maintaining state across multi-turn agent execution workflows in Antigravity sandboxes.

---

## 1. REPL Lifetime & State Model

Each sandbox maintains an isolated Python interpreter instance. When `repl_mode=True` is supplied to `execute_code`, state is retained in the global execution namespace across consecutive tool calls:

```
[Agent Turn 1] --> execute_code("data = load_dataset()") --> [REPL Session (data in memory)]
[Agent Turn 2] --> execute_code("model = train(data)")   --> [REPL Session (data, model in memory)]
[Agent Turn 3] --> execute_code("eval_res = test(model)") --> [REPL Session (data, model, eval_res)]
```

### Namespace Invariants:
1. **Variable Retention**: Variables, objects, DataFrames, and tensors assigned at module level remain accessible in subsequent turns.
2. **Function & Class Definitions**: User-defined functions, generator definitions, classes, and helper lambdas remain callable.
3. **Module Imports**: Imported libraries (`import json`, `import math`) persist; repeated imports in subsequent turns are no-ops.

---

## 2. Recommended Multi-Turn Patterns

### Pattern A: Data Ingestion & Transformation Pipeline
```python
# Turn 1: Ingest and validate data structures
import json
payload = '[{"id": 1, "score": 92}, {"id": 2, "score": 85}, {"id": 3, "score": 98}]'
items = json.loads(payload)
print(f"Loaded {len(items)} records.")
```

```python
# Turn 2: Define calculation logic on previously loaded items
def get_top_performers(records, threshold=90):
    return [r for r in records if r["score"] >= threshold]

top_tier = get_top_performers(items)
print(f"Top tier count: {len(top_tier)}")
```

```python
# Turn 3: Final aggregation and formatting
summary = {
    "total_records": len(items),
    "top_records": len(top_tier),
    "avg_top_score": sum(r["score"] for r in top_tier) / len(top_tier)
}
print(json.dumps(summary, indent=2))
```

---

## 3. Namespace Hygiene & Anti-Patterns

### Anti-Pattern 1: Re-reading and Re-parsing Data Every Turn
*Avoid*:
```python
# Turn 2 - Unnecessary overhead
import json
items = json.loads('[{"id": 1, "score": 92}...]') # Wasteful re-parse
```
*Prefer*:
```python
# Turn 2 - Rely on existing state
top_items = [i for i in items if i["score"] > 90]
```

### Anti-Pattern 2: Global State Variable Shadowing
*Avoid*: Reusing ubiquitous variable names (`data`, `res`, `x`, `temp`) across unrelated tasks.
*Prefer*: Descriptive domain variable names (`customer_records`, `filtered_metrics_df`, `trained_regressor`).

### Anti-Pattern 3: In-Place Mutation Regressions
When modifying shared collections, prefer immutable transformations or take a snapshot before mutating in-place:
```python
# Prefer creating new transformed variables
clean_items = [dict(item, score=max(item["score"], 0)) for item in raw_items]
```

---

## 4. Inspecting and Debugging REPL State

If an agent needs to inspect what variables are currently resident in the sandbox namespace:

```python
# List user-defined variables (excluding built-in dunders)
user_vars = [k for k in dir() if not k.startswith('_')]
print("Active variables in session:", user_vars)
```

To clear a specific variable and free its memory:
```python
del large_dataframe
```

---

## 5. Exception Recovery in REPL Sessions

If a Python runtime exception (`IndexError`, `KeyError`, `ZeroDivisionError`) occurs during a turn:
- The exception is captured and returned with `isError: true`.
- **Existing session state is preserved**. Variables defined before the exception occurred remain intact.
- Correct the erroneous line of code and re-execute without needing to re-run preceding setup turns.
