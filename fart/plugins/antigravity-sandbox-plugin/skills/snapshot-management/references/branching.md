# Agent Branching & Tree Exploration Reference Guide

This guide details methodologies for using snapshot management to support speculative execution, tree-based problem-solving, and error recovery in autonomous agent workflows.

---

## 1. Tree Search & Speculative Branching

Complex multi-step problems (e.g. hyperparameter optimization, code refactoring, data pipeline design) often benefit from branching exploration where an agent explores competing strategies from a shared root state.

```
                  [Root: Dataset Loaded] (snap-001)
                         /              \
                        /                \
        [Branch A: Method 1]         [Branch B: Method 2]
        (snap-002: Score 0.88)       (snap-003: Score 0.94)
                                              |
                                     [Refinement B.1]
                                     (Final: Score 0.97)
```

### Branching Execution Pattern:
1. **Initialize & Checkpoint Root**:
   - Ingest data and perform foundational setup.
   - Take snapshot `snap-root`.
2. **Explore Branch A**:
   - Apply Approach 1 modifications and evaluate performance score.
   - Snapshot as `snap-branch-a`.
3. **Reset to Root & Explore Branch B**:
   - Restore `snap-root`.
   - Apply Approach 2 modifications and evaluate performance score.
   - Snapshot as `snap-branch-b`.
4. **Select Optimal Branch**:
   - Compare results between branches.
   - Restore the superior snapshot (`snap-branch-b`) to continue downstream execution.

---

## 2. Checkpoint Storage Mechanics

### Firecracker MicroVM Backend:
- In E2B microVMs, snapshots capture the complete guest OS state (RAM memory image, process table, filesystem delta) using Firecracker VM snapshot primitives.
- Restoration provides exact byte-for-byte state recreation within tens of milliseconds.

### Local AST Fallback Backend:
- In the local AST sandbox, snapshots serialize the REPL symbol table, variable state dictionaries (including JSON-serializable structures, primitive values, and custom data representations), and sandbox execution metadata.
- Restoration atomically resets the local REPL process namespace to the recorded checkpoint state.

---

## 3. Snapshot Naming & Hygiene Best Practices

1. **Semantic Names**: Use descriptive kebab-case or snake_case names:
   - `post_feature_engineering`
   - `model_checkpoint_epoch_10`
   - `pre_destructive_reindex`
2. **Snapshot Lifecycle**: Delete intermediate exploratory snapshots once an optimal branch is selected to avoid unbounded memory accumulation.
3. **Metadata Documentation**: Include the `description` parameter when creating snapshots to record metrics, assumptions, or dataset shapes for reference across agent turns.
