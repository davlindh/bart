"""
Independent Forensic Verification Script for Milestone 1.
Tests the authentic implementation of AST security, REPL persistence,
builtins sanitization, timeout enforcement, snapshotting, and SandboxManager routing.
"""

import math
import os
from pathlib import Path
import random
import sys
import time

SRC_PATH = str(Path(__file__).resolve().parent.parent.parent / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from antigravity.sandbox import (
    ASTSecurityValidator,
    BaseSandbox,
    E2BSandbox,
    ExecutionResult,
    LocalSandbox,
    SandboxExecutionError,
    SandboxManager,
    SandboxMode,
    SandboxState,
    SandboxTimeoutError,
    SecurityViolationError,
    SnapshotError,
    get_sanitized_builtins,
)


def run_checks():
    print("==================================================")
    print("Starting Forensic Integrity Check for Milestone 1")
    print("==================================================")

    # 1. AST Security Analysis Checks
    print("\n--- Check 1: AST Security Validator ---")
    validator = ASTSecurityValidator()
    
    # Safe code
    safe_snippets = [
        "x = 1 + 2",
        "import math\nval = math.sqrt(25)",
        "import json\ndata = json.loads('{\"a\": 1}')",
        "import re\nm = re.match(r'\\d+', '123')",
        "class Foo:\n    def __init__(self):\n        self.val = 1\n    def __repr__(self):\n        return 'Foo()'",
    ]
    for s in safe_snippets:
        is_safe, violations = validator.check_code(s)
        assert is_safe, f"Safe snippet failed: {s} -> {violations}"
    print("  [PASS] Safe code snippets accepted.")

    # Malicious / prohibited code
    forbidden_snippets = [
        "import os",
        "import sys",
        "import subprocess",
        "import socket",
        "import ctypes",
        "import shutil",
        "import importlib",
        "from os import path",
        "().__class__",
        "().__class__.__bases__[0].__subclasses__()",
        "(lambda: 1).__globals__",
        "(lambda: 1).__code__",
        "eval('1+1')",
        "exec('x=1')",
        "open('test.txt', 'w')",
        "getattr(object, '__subclasses__')",
        "setattr(object, '__code__', 1)",
    ]
    for f in forbidden_snippets:
        is_safe, violations = validator.check_code(f)
        assert not is_safe, f"Forbidden snippet was NOT blocked: {f}"
    print("  [PASS] Forbidden snippets rejected.")

    # 2. Sanitized Builtins Table Checks
    print("\n--- Check 2: Builtins Sanitizer ---")
    builtins_dict = get_sanitized_builtins()
    prohibited_names = ["open", "eval", "exec", "compile", "globals", "locals", "vars", "breakpoint"]
    for p in prohibited_names:
        assert p not in builtins_dict, f"Prohibited builtin '{p}' present in sanitized builtins!"
    
    safe_names = ["print", "len", "range", "abs", "sum", "min", "max", "dict", "list", "str", "int", "float"]
    for s in safe_names:
        assert s in builtins_dict, f"Safe builtin '{s}' missing from sanitized builtins!"
    print("  [PASS] Sanitized builtins table verified.")

    # 3. Dynamic Non-Hardcoded Execution in LocalSandbox
    print("\n--- Check 3: Dynamic Computation in LocalSandbox ---")
    sandbox = LocalSandbox(timeout=5.0)
    
    # Generate random test cases
    for _ in range(5):
        a = random.randint(100, 9999)
        b = random.randint(100, 9999)
        op = random.choice(["+", "-", "*"])
        code = f"{a} {op} {b}"
        expected = str(eval(code))
        res = sandbox.execute(code)
        assert res.is_success, f"Execution failed: {res.stderr}"
        assert res.result == expected, f"Calculated {res.result} != expected {expected}"
    print("  [PASS] 5 dynamic random arithmetic operations matched expected results.")

    # 4. Multi-Turn REPL State Accumulation
    print("\n--- Check 4: Stateful REPL Multi-Turn ---")
    res1 = sandbox.execute("accumulator = []")
    assert res1.is_success
    for i in range(1, 6):
        res = sandbox.execute(f"accumulator.append({i * 10})")
        assert res.is_success
    res_final = sandbox.execute("accumulator")
    assert res_final.result == "[10, 20, 30, 40, 50]"
    print("  [PASS] Multi-turn state accumulation verified.")

    # 5. Snapshot and State Rollback
    print("\n--- Check 5: Snapshot & Restore ---")
    snap_id = sandbox.create_snapshot("checkpoint_alpha")
    sandbox.execute("accumulator.clear()\naccumulator.append(999)")
    res_dirty = sandbox.execute("accumulator")
    assert res_dirty.result == "[999]"
    sandbox.restore_snapshot(snap_id)
    res_restored = sandbox.execute("accumulator")
    assert res_restored.result == "[10, 20, 30, 40, 50]"
    print("  [PASS] Snapshot checkpoint and restore verified.")

    # 6. Timeout and Self-Healing
    print("\n--- Check 6: Timeout Enforcement & Recovery ---")
    t0 = time.time()
    t_res = sandbox.execute("while True: pass", timeout=1.0)
    elapsed = time.time() - t0
    assert not t_res.is_success
    assert 0.9 <= elapsed <= 3.0, f"Elapsed time {elapsed}s outside expected timeout window"
    assert "SandboxTimeoutError" in str(t_res.error) or "timed out" in t_res.stderr

    # Self healing / crash recovery
    heal_res = sandbox.execute("recovered_var = 'OK'\nrecovered_var")
    assert heal_res.is_success
    assert heal_res.result == "'OK'"
    print("  [PASS] Timeout terminated infinite loop and sandbox auto-recovered.")

    # 7. Lifecycle (Pause, Resume, Terminate)
    print("\n--- Check 7: Sandbox Lifecycle ---")
    sandbox.pause()
    assert sandbox.status == SandboxState.PAUSED
    try:
        sandbox.execute("1 + 1")
        assert False, "Should have raised SandboxExecutionError while paused"
    except SandboxExecutionError:
        pass
    sandbox.resume()
    assert sandbox.status == SandboxState.RUNNING
    res_resumed = sandbox.execute("2 + 2")
    assert res_resumed.result == "4"
    sandbox.terminate()
    assert sandbox.status == SandboxState.TERMINATED
    print("  [PASS] Lifecycle states (RUNNING, PAUSED, TERMINATED) verified.")

    # 8. SandboxManager Routing & Auto-Fallback
    print("\n--- Check 8: SandboxManager Orchestration ---")
    with SandboxManager() as mgr:
        sb_local = mgr.create_sandbox(mode=SandboxMode.LOCAL)
        assert sb_local.mode == SandboxMode.LOCAL
        assert sb_local.status == SandboxState.RUNNING

        sb_auto = mgr.create_sandbox(mode=SandboxMode.AUTO)
        assert sb_auto.mode == SandboxMode.LOCAL  # Fallback when E2B_API_KEY is not set
        assert sb_auto.status == SandboxState.RUNNING

        listed = mgr.list_sandboxes()
        assert len(listed) == 2
        
        destroyed = mgr.destroy_sandbox(sb_local.sandbox_id)
        assert destroyed is True
        assert len(mgr.list_sandboxes()) == 1

    print("  [PASS] SandboxManager factory, auto-fallback, and context manager cleanup verified.")

    print("\n==================================================")
    print("VERDICT: ALL 8 FORENSIC INTEGRITY CHECKS PASSED")
    print("==================================================")


if __name__ == "__main__":
    run_checks()
