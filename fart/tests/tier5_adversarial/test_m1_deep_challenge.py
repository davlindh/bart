"""Milestone 1 Deep Adversarial Challenge Test Suite."""

import pytest
import time
import base64
from antigravity.sandbox import (
    ASTSecurityValidator,
    LocalSandbox,
    SandboxState,
    SecurityViolationError,
    get_sanitized_builtins,
)
from antigravity.sandbox.builtins_sanitizer import (
    create_safe_importer,
    safe_getattr,
    safe_setattr,
    safe_delattr,
    safe_hasattr,
)

# ---------------------------------------------------------------------------
# Category A: Import Security & Transitive Module Leaks
# ---------------------------------------------------------------------------

def test_ast_prohibits_direct_system_imports():
    """Direct imports of system-level modules must fail static AST validation."""
    validator = ASTSecurityValidator()
    prohibited = [
        "import os",
        "import sys",
        "import subprocess",
        "import socket",
        "import shutil",
        "import ctypes",
        "import importlib",
        "import pty",
        "import gc",
        "from os import path",
        "from sys import modules",
        "from subprocess import Popen",
    ]
    for code in prohibited:
        is_safe, violations = validator.check_code(code)
        assert not is_safe, f"Expected {code} to be blocked by AST validator"
        assert len(violations) > 0

def test_runtime_safe_importer_blocks_top_level_unauthorized():
    """create_safe_importer must raise SecurityViolationError for prohibited top-level modules."""
    importer = create_safe_importer()
    unauthorized = ["os", "sys", "subprocess", "socket", "ctypes", "http", "builtins", "importlib"]
    for mod in unauthorized:
        with pytest.raises(SecurityViolationError):
            importer(mod)

# ---------------------------------------------------------------------------
# Category B: Prohibited Dunders & Attribute Traversal
# ---------------------------------------------------------------------------

def test_ast_blocks_prohibited_dunders():
    """Static AST validator must block all prohibited dunder attributes."""
    validator = ASTSecurityValidator()
    payloads = [
        "x = obj.__class__",
        "x = obj.__bases__",
        "x = obj.__mro__",
        "x = obj.__subclasses__()",
        "x = obj.__globals__",
        "x = obj.__code__",
        "x = obj.__builtins__",
        "x = obj.__dict__",
        "x = obj.__closure__",
        "x = obj.__qualname__",
        "x = obj.__module__",
        "x = obj.__import__",
        "x = obj.__loader__",
        "x = obj.__spec__",
        "x = obj.__func__",
        "x = obj.__self__",
        "x = obj.__wrapped__",
        "x = obj.__init_subclass__",
        "x = obj.__annotations__",
        "x = obj.__traceback__",
        "x = obj.__frame__",
    ]
    for code in payloads:
        is_safe, violations = validator.check_code(code)
        assert not is_safe, f"Expected {code} to be blocked"

def test_ast_allows_safe_dunders_in_classes():
    """AST validator must allow standard operator and lifecycle dunders."""
    validator = ASTSecurityValidator()
    safe_class_code = """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point({self.x}, {self.y})"
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    def __len__(self):
        return 2
"""
    is_safe, violations = validator.check_code(safe_class_code)
    assert is_safe, f"Safe dunders unexpectedly blocked: {violations}"

def test_runtime_safe_getattr_blocks_dynamic_dunders():
    """safe_getattr, safe_setattr, safe_delattr, safe_hasattr must block blocked dunders."""
    blocked_dunders = ["__subclasses__", "__globals__", "__code__", "__builtins__", "__class__", "__dict__"]
    for dunder in blocked_dunders:
        with pytest.raises(SecurityViolationError):
            safe_getattr(object, dunder)
        with pytest.raises(SecurityViolationError):
            safe_setattr(object, dunder, 1)
        with pytest.raises(SecurityViolationError):
            safe_delattr(object, dunder)
        assert safe_hasattr(object, dunder) is False

# ---------------------------------------------------------------------------
# Category C: Prohibited Builtin Function Calls
# ---------------------------------------------------------------------------

def test_ast_prohibits_dangerous_builtins():
    """Static AST validator must block calls to eval, exec, compile, open, globals, locals, etc."""
    validator = ASTSecurityValidator()
    calls = [
        "eval('1 + 1')",
        "exec('a = 1')",
        "compile('a = 1', '<test>', 'exec')",
        "open('test.txt', 'r')",
        "globals()",
        "locals()",
        "vars()",
        "memoryview(b'abc')",
        "input()",
        "breakpoint()",
        "exit()",
        "quit()",
    ]
    for code in calls:
        is_safe, violations = validator.check_code(code)
        assert not is_safe, f"Expected {code} to be blocked"

# ---------------------------------------------------------------------------
# Category D: REPL State Persistence Across Multi-Turn Executions
# ---------------------------------------------------------------------------

def test_repl_state_persistence_classes_and_instances(local_sandbox: LocalSandbox):
    """Verify user-defined classes and instances persist across multi-turn executions."""
    r1 = local_sandbox.execute("""
class BankAccount:
    def __init__(self, owner, balance=0.0):
        self.owner = owner
        self.balance = balance
    def deposit(self, amount):
        self.balance += amount
        return self.balance
    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance
acc = BankAccount("Alice", 100.0)
""")
    assert r1.exit_code == 0

    r2 = local_sandbox.execute("acc.deposit(50.0)")
    assert r2.exit_code == 0
    assert r2.result == "150.0"

    r3 = local_sandbox.execute("acc.withdraw(30.0)")
    assert r3.exit_code == 0
    assert r3.result == "120.0"

    r4 = local_sandbox.execute("acc.balance")
    assert r4.exit_code == 0
    assert r4.result == "120.0"

def test_repl_state_persistence_closures_and_mutations(local_sandbox: LocalSandbox):
    """Verify closures, lambdas, and mutable structures persist across turns."""
    r1 = local_sandbox.execute("""
def make_accumulator(initial=0):
    val = [initial]
    def add(n):
        val[0] += n
        return val[0]
    return add
acc_fn = make_accumulator(10)
items = [1, 2, 3]
""")
    assert r1.exit_code == 0

    r2 = local_sandbox.execute("acc_fn(5)")
    assert r2.exit_code == 0
    assert r2.result == "15"

    r3 = local_sandbox.execute("items.append(4); len(items)")
    assert r3.exit_code == 0
    assert r3.result == "4"

    r4 = local_sandbox.execute("acc_fn(10)")
    assert r4.exit_code == 0
    assert r4.result == "25"

def test_repl_state_persistence_complex_data_structures(local_sandbox: LocalSandbox):
    """Verify dicts, sets, tuples, and nested structures retain integrity across turns."""
    r1 = local_sandbox.execute("""
data = {
    "users": [{"id": 1, "name": "Alice", "tags": {"admin", "dev"}}],
    "metadata": ("v1", 2026),
}
""")
    assert r1.exit_code == 0

    r2 = local_sandbox.execute('data["users"][0]["tags"].add("security"); len(data["users"][0]["tags"])')
    assert r2.exit_code == 0
    assert r2.result == "3"

    r3 = local_sandbox.execute('"security" in data["users"][0]["tags"]')
    assert r3.exit_code == 0
    assert r3.result == "True"

def test_repl_snapshot_branching_and_rollback(local_sandbox: LocalSandbox):
    """Verify snapshot creation and rollback across state changes."""
    local_sandbox.execute("val = 100; log = ['initial']")
    snap_id = local_sandbox.create_snapshot("checkpoint_1")
    assert snap_id is not None

    local_sandbox.execute("val = 999; log.append('modified')")
    r_mod = local_sandbox.execute("(val, log)")
    assert r_mod.result == "(999, ['initial', 'modified'])"

    local_sandbox.restore_snapshot(snap_id)
    r_restored = local_sandbox.execute("(val, log)")
    assert r_restored.result == "(100, ['initial'])"

def test_repl_reset_session(local_sandbox: LocalSandbox):
    """Verify session reset clears user defined state."""
    local_sandbox.execute("x = 42; y = 'hello'")
    vars_before = local_sandbox.get_variables()
    assert "x" in vars_before and "y" in vars_before

    local_sandbox.reset_session()
    vars_after = local_sandbox.get_variables()
    assert "x" not in vars_after and "y" not in vars_after

# ---------------------------------------------------------------------------
# Category E: Execution Engine Reliability & Lifecycle
# ---------------------------------------------------------------------------

def test_sandbox_crash_recovery():
    """Verify sandbox recovers if worker subprocess is forcibly killed."""
    sb = LocalSandbox()
    sb.execute("x = 10")
    # Kill the worker directly
    sb._kill_worker()
    assert sb._process is None
    # Next execution should automatically respawn worker
    res = sb.execute("y = 20; y")
    assert res.exit_code == 0
    assert res.result == "20"
    sb.terminate()
