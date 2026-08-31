"""Tier 2: Boundary Tests for AST Security and Builtins Sanitizer."""

import pytest

from antigravity.sandbox import (
    ASTSecurityValidator,
    LocalSandbox,
    SecurityViolationError,
    get_sanitized_builtins,
)


@pytest.fixture
def validator() -> ASTSecurityValidator:
    return ASTSecurityValidator()


def test_prohibited_module_imports(validator: ASTSecurityValidator):
    """Verify that dangerous system modules are blocked by AST analysis."""
    prohibited_snippets = [
        "import os",
        "import sys",
        "import subprocess",
        "import socket",
        "import ctypes",
        "import shutil",
        "import importlib",
        "import gc",
        "import signal",
        "import pickle",
        "import marshal",
        "from os import system",
        "from subprocess import Popen",
        "from sys import modules",
        "import os.path",
    ]
    for code in prohibited_snippets:
        is_safe, violations = validator.check_code(code)
        assert is_safe is False, f"Code '{code}' should have been rejected by validator"
        assert len(violations) > 0

        with pytest.raises(SecurityViolationError):
            validator.validate(code)


def test_allowed_module_imports(validator: ASTSecurityValidator):
    """Verify that safe utility modules are permitted by AST analysis."""
    allowed_snippets = [
        "import math\nval = math.sqrt(16)",
        "import json\nd = json.dumps({'key': 123})",
        "import random\nr = random.randint(1, 10)",
        "import datetime\nnow = datetime.datetime.now()",
        "import time\nt = time.time()",
        "import re\nm = re.match(r'\\d+', '123')",
        "import collections\nc = collections.Counter([1, 2, 2])",
        "import itertools\nit = itertools.chain([1], [2])",
        "import statistics\nmean = statistics.mean([1, 2, 3])",
        "import dataclasses\n@dataclasses.dataclass\nclass Point: x: int",
        "import typing\nx: typing.List[int] = [1, 2]",
        "import csv\nimport io",
        "import hashlib\nh = hashlib.sha256(b'test').hexdigest()",
        "import base64\nb = base64.b64encode(b'test')",
        "import zlib",
        "import urllib.parse\np = urllib.parse.urlparse('https://example.com')",
    ]
    for code in allowed_snippets:
        is_safe, violations = validator.check_code(code)
        assert is_safe is True, f"Code '{code}' failed check with violations: {violations}"


def test_prohibited_dunder_attribute_traversals(validator: ASTSecurityValidator):
    """Verify that dunder introspection exploits are blocked by AST analysis."""
    escape_snippets = [
        "x = [].__class__",
        "x = ().__class__.__bases__[0].__subclasses__()",
        "f = (lambda: None).__globals__",
        "c = (lambda: None).__code__",
        "b = ().__class__.__builtins__",
        "m = [].__class__.__mro__",
        "d = object.__dict__",
        "cl = (lambda: None).__closure__",
    ]
    for code in escape_snippets:
        is_safe, violations = validator.check_code(code)
        assert is_safe is False, f"Escape snippet '{code}' should have been rejected"
        with pytest.raises(SecurityViolationError):
            validator.validate(code)


def test_prohibited_builtin_calls(validator: ASTSecurityValidator):
    """Verify that direct invocations of dangerous builtins are blocked."""
    prohibited_calls = [
        "eval('1 + 1')",
        "exec('x = 10')",
        "compile('x = 1', '<string>', 'exec')",
        "open('test.txt', 'w')",
        "globals()",
        "locals()",
        "vars()",
        "getattr(object, '__subclasses__')",
        "getattr(object, '__globals__')",
        "setattr(object, '__code__', None)",
        "delattr(object, '__doc__')",
    ]
    for code in prohibited_calls:
        is_safe, violations = validator.check_code(code)
        assert is_safe is False, f"Call '{code}' should have been rejected"
        with pytest.raises(SecurityViolationError):
            validator.validate(code)


def test_safe_user_classes_with_standard_dunders(validator: ASTSecurityValidator):
    """Verify that legitimate class implementations with safe dunders are permitted."""
    valid_class_code = """
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Vector({self.x}, {self.y})"
    def __len__(self):
        return 2
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

v1 = Vector(1, 2)
v2 = Vector(3, 4)
v3 = v1 + v2
"""
    is_safe, violations = validator.check_code(valid_class_code)
    assert is_safe is True, f"Valid class failed with violations: {violations}"


def test_builtins_sanitizer_dictionary():
    """Verify that get_sanitized_builtins provides safe tools and omits dangerous primitives."""
    sanitized = get_sanitized_builtins()

    # Dangerous builtins must NOT exist
    for dangerous in ["open", "eval", "exec", "compile", "globals", "locals", "vars", "breakpoint"]:
        assert dangerous not in sanitized, f"Dangerous builtin '{dangerous}' found in sanitized dict!"

    # Safe builtins must exist
    for safe in [
        "abs", "len", "print", "range", "sum", "min", "max", "dict", "list", "str", "int",
        "object", "super", "property", "classmethod", "staticmethod"
    ]:
        assert safe in sanitized, f"Safe builtin '{safe}' missing from sanitized dict!"

    # Guarded hooks exist
    assert callable(sanitized["__import__"])
    assert callable(sanitized["getattr"])
    assert callable(sanitized["setattr"])


def test_prohibited_module_and_introspection_attributes(validator: ASTSecurityValidator):
    """Verify that transitive module leaks and call-stack introspection attributes are blocked."""
    prohibited_snippets = [
        "import fractions\nx = fractions.sys",
        "import contextlib\nx = contextlib.os",
        "import uuid\nx = uuid.os",
        "x = gen.gi_frame",
        "x = f.f_back",
        "x = f.f_globals",
        "x = f.f_locals",
        "x = f.f_code",
        "x = fn.co_code",
        "from urllib import request",
        "from urllib import error",
    ]
    for code in prohibited_snippets:
        is_safe, violations = validator.check_code(code)
        assert is_safe is False, f"Code '{code}' should have been rejected by validator"
        assert len(violations) > 0

        with pytest.raises(SecurityViolationError):
            validator.validate(code)


def test_custom_authorized_imports():
    """Verify that custom authorized_imports extends the allowed module set."""
    val = ASTSecurityValidator(additional_allowed_modules=["sqlite3"])
    is_safe, violations = val.check_code("import sqlite3\nconn = sqlite3.connect(':memory:')")
    assert is_safe is True, f"sqlite3 should be allowed with authorized_imports, got {violations}"


def test_local_sandbox_rejects_security_violations(local_sandbox: LocalSandbox):
    """Verify LocalSandbox returns a failed ExecutionResult on security violations."""
    res = local_sandbox.execute("import os\nos.system('echo test')")
    assert res.is_success is False
    assert res.exit_code == 1
    assert "SecurityViolationError" in res.stderr or "SecurityViolationError" in str(res.error)

