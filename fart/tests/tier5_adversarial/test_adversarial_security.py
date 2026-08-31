"""Tier 5: Adversarial Security & Boundary Probe Tests."""

import pytest

from antigravity.sandbox import (
    ASTSecurityValidator,
    LocalSandbox,
    SecurityViolationError,
    get_sanitized_builtins,
)
from antigravity.sandbox.builtins_sanitizer import (
    create_safe_importer,
    safe_delattr,
    safe_getattr,
    safe_hasattr,
    safe_setattr,
)


def test_adversarial_runtime_getattr_obfuscation():
    """Verify runtime safe_getattr blocks computed/obfuscated dunder attribute access."""
    # Obfuscated string concatenation that evades static AST
    blocked_attrs = [
        "__" + "subclasses__",
        "__" + "globals__",
        "__" + "code__",
        "__" + "builtins__",
        "__" + "class__",
        "__" + "bases__",
        "__" + "mro__",
        "__" + "dict__",
    ]

    for attr in blocked_attrs:
        with pytest.raises(SecurityViolationError, match="blocked"):
            safe_getattr(object, attr)

        with pytest.raises(SecurityViolationError, match="blocked"):
            safe_setattr(object, attr, "exploit")

        with pytest.raises(SecurityViolationError, match="blocked"):
            safe_delattr(object, attr)

        assert safe_hasattr(object, attr) is False


def test_adversarial_runtime_import_hook():
    """Verify runtime safe_importer blocks prohibited and non-whitelisted modules."""
    importer = create_safe_importer()

    prohibited = ["os", "sys", "subprocess", "socket", "ctypes", "shutil", "importlib", "gc"]
    for mod in prohibited:
        with pytest.raises(SecurityViolationError, match="blocked by sandbox"):
            importer(mod)

    # Safe modules succeed
    math_mod = importer("math")
    assert hasattr(math_mod, "sqrt")
    json_mod = importer("json")
    assert hasattr(json_mod, "dumps")


def test_adversarial_sandbox_execution_probes(local_sandbox: LocalSandbox):
    """Test various sandbox escape vectors executed through LocalSandbox."""
    escape_payloads = [
        # Attempt to reach subclasses
        "cls = ().__class__",
        # Attempt to reach object dict
        "d = object.__dict__",
        # Attempt to use builtins open
        "f = open('test.txt', 'w')",
        # Attempt to use eval
        "e = eval('1 + 1')",
        # Attempt to use exec
        "exec('a = 1')",
        # Attempt to import os
        "import os",
        # Attempt to import subprocess
        "from subprocess import call",
        # Transitive module leaks
        "import fractions\nos_mod = fractions.sys.modules['os']",
        "import contextlib\ncwd = contextlib.os.getcwd()",
        "import uuid\nuuid.os.getcwd()",
        # Frame and generator traversal
        """
gen_holder = []
def g():
    (yield 1)
    frame = gen_holder[0].gi_frame
    f = frame
    while f:
        if 'os' in f.f_globals:
            break
        f = f.f_back
gen = g()
gen_holder.append(gen)
next(gen)
""",
        # Submodule import bypasses
        "from urllib import request",
        "from urllib import error",
        "from fractions import sys",
        "from contextlib import os",
    ]

    for payload in escape_payloads:
        res = local_sandbox.execute(payload)
        assert res.is_success is False
        assert res.exit_code == 1
        assert "SecurityViolationError" in str(res.error) or "SecurityViolationError" in res.stderr


def test_adversarial_submodule_import_runtime_hook():
    """Verify runtime create_safe_importer blocks prohibited submodules and symbols via fromlist."""
    importer = create_safe_importer()

    with pytest.raises(SecurityViolationError, match="blocked by sandbox"):
        importer("urllib", fromlist=("request",))

    with pytest.raises(SecurityViolationError, match="blocked by sandbox"):
        importer("urllib", fromlist=("error",))

    with pytest.raises(SecurityViolationError, match="blocked by sandbox"):
        importer("fractions", fromlist=("sys",))

    with pytest.raises(SecurityViolationError, match="blocked by sandbox"):
        importer("contextlib", fromlist=("os",))

    # Allowed submodules succeed
    parse_mod = importer("urllib", fromlist=("parse",))
    assert parse_mod is not None


def test_sandbox_oop_builtins_support(local_sandbox: LocalSandbox):
    """Verify standard OOP classes, properties, super, classmethod, and staticmethod work in sandbox."""
    oop_code = """
class BaseEntity(object):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def get_kind(cls) -> str:
        return "entity"

    @staticmethod
    def get_version() -> int:
        return 1

class User(BaseEntity):
    def __init__(self, name: str, age: int):
        super().__init__(name)
        self._age = age

    @property
    def age(self) -> int:
        return self._age

u = User("Alice", 30)
res = (u.name, u.age, u.get_kind(), u.get_version())
res
"""
    res = local_sandbox.execute(oop_code)
    assert res.exit_code == 0
    assert res.is_success is True
    assert res.result == "('Alice', 30, 'entity', 1)"

