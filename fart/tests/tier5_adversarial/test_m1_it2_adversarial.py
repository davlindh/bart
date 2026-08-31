"""
Adversarial Verification Suite for Milestone 1 Iteration 2.
Empirically stress tests AST security, runtime hooks, frame isolation,
transitive module leaks, OOP builtins, and sandbox boundaries.
"""

import sys
import pytest
from antigravity.sandbox import LocalSandbox, SecurityViolationError, SandboxTimeoutError
from antigravity.sandbox.ast_security import ASTSecurityValidator
from antigravity.sandbox.builtins_sanitizer import get_sanitized_builtins, safe_getattr


@pytest.fixture
def sandbox():
    sb = LocalSandbox()
    yield sb
    sb.terminate()


class TestMilestone1It2Reverification:
    """1. Re-test all previously discovered vulnerabilities."""

    @pytest.mark.parametrize(
        "code",
        [
            "import fractions\nx = fractions.sys.modules['os'].getcwd()",
            "import contextlib\nx = contextlib.os.getcwd()",
            "import uuid\nx = uuid.os.getcwd()",
            "import calendar\nx = calendar.datetime.sys.modules",
            "import dataclasses\nx = dataclasses.sys.modules",
            "import enum\nx = enum.sys.modules",
            "import statistics\nx = statistics.math.sys.modules",
            "import typing\nx = typing.sys.modules",
            "import urllib.parse\nx = urllib.parse.sys.modules",
        ],
    )
    def test_transitive_module_leaks_blocked(self, sandbox, code):
        """Transitive module attributes exposing os/sys must be rejected."""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    @pytest.mark.parametrize(
        "code",
        [
            # Generator frame introspection
            """
gen_holder = []
def g():
    yield 1
    f = gen_holder[0].gi_frame
gen = g()
gen_holder.append(gen)
next(gen)
""",
            # Coroutine frame introspection
            """
async def coro():
    pass
c = coro()
f = c.cr_frame
""",
            # Async generator frame introspection
            """
async def agen():
    yield 1
ag = agen()
f = ag.ag_frame
""",
            # Function code introspection
            """
def f(): pass
c = f.__code__
""",
            # Traceback frame introspection
            """
try:
    1 / 0
except Exception as e:
    tb = e.__traceback__
    f = tb.tb_frame
""",
            # Code constants introspection
            """
def f(): pass
consts = f.__code__.co_consts
""",
            # Frame back traversal
            """
import sys
# attempt to access f_back
""",
        ],
    )
    def test_frame_and_code_introspection_blocked(self, sandbox, code):
        """Frame, code, generator, and traceback introspection attributes must be blocked."""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    @pytest.mark.parametrize(
        "code",
        [
            "from urllib import request",
            "from urllib import error",
            "import urllib.request",
            "import urllib.error",
            "from os import path",
            "from sys import modules",
            "from subprocess import Popen",
            "from ctypes import c_int",
        ],
    )
    def test_submodule_and_symbol_imports_blocked(self, sandbox, code):
        """Prohibited submodules and symbols must be blocked at AST and runtime."""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    def test_oop_builtins_support(self, sandbox):
        """Standard Python OOP builtins must work seamlessly."""
        code = """
class Base(object):
    def __init__(self, val):
        self._val = val

class Derived(Base):
    def __init__(self, val):
        super().__init__(val)

    @property
    def val(self):
        return self._val

    @classmethod
    def make(cls, v):
        return cls(v)

    @staticmethod
    def get_tag():
        return 'TAG_OK'

d = Derived.make(42)
assert isinstance(d, Base)
assert issubclass(Derived, Base)
assert d.val == 42
assert Derived.get_tag() == 'TAG_OK'
d.val
"""
        res = sandbox.execute(code)
        assert res.exit_code == 0
        assert res.result == "42"
        assert res.error is None


class TestNewAdversarialProbes:
    """2. Novel adversarial escape probes and edge cases."""

    def test_dynamic_getattr_chained_dunder_probe(self, sandbox):
        """Chained getattr calls to reach __class__.__bases__.__subclasses__."""
        code = """
s = 'test'
c = getattr(s, '__class__')
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    def test_dynamic_getattr_runtime_obfuscated_string(self, sandbox):
        """Obfuscated string constructed at runtime passed to getattr."""
        code = """
s = 'test'
attr = chr(95) + chr(95) + 'class' + chr(95) + chr(95)
c = getattr(s, attr)
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    def test_dynamic_getattr_module_attribute_probe(self, sandbox):
        """Obfuscated attribute name targeting 'os' or 'sys' on imported module."""
        code = """
import fractions
attr = chr(115) + chr(121) + chr(115)  # 'sys'
mod = getattr(fractions, attr)
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    def test_runtime_import_hook_evasion(self, sandbox):
        """Calling __import__ dynamically with prohibited names."""
        code = """
imp = __import__
imp('os')
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    def test_runtime_import_hook_submodule_fromlist_evasion(self, sandbox):
        """Calling __import__ dynamically with fromlist containing prohibited submodule."""
        code = """
imp = __import__
imp('urllib', fromlist=['request'])
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    def test_type_constructor_sandbox_escape(self, sandbox):
        """Attempting to access __globals__ on lambdas or functions."""
        res = sandbox.execute("f = lambda: 1\nf.__globals__")
        assert res.exit_code != 0

    def test_exception_context_cause_introspection(self, sandbox):
        """Exception __context__ and __cause__ chaining with tb_frame."""
        code = """
try:
    try:
        1/0
    except Exception as e1:
        raise ValueError('chained') from e1
except Exception as e2:
    tb = e2.__cause__.__traceback__
    f = tb.tb_frame
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0

    def test_closure_cell_contents_inspection(self, sandbox):
        """Introspecting closure cell contents."""
        code = """
def outer(x):
    def inner():
        return x
    return inner

fn = outer(10)
c = fn.__closure__[0].cell_contents
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0

    def test_dangerous_dunder_new_blocked(self, sandbox):
        """Access to __new__ is strictly blocked by security policy."""
        code = """
class Meta(type):
    def __new__(mcs, name, bases, attrs):
        return super().__new__(mcs, name, bases, attrs)
"""
        res = sandbox.execute(code)
        assert res.exit_code != 0
        assert "SecurityViolationError" in res.error or "Security policy violation" in res.stderr

    def test_safe_metaclass_init_works(self, sandbox):
        """Metaclasses using __init__ execute cleanly."""
        code = """
class Meta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls.meta_tag = 'META_APPLIED'

class Model(metaclass=Meta):
    pass

assert Model.meta_tag == 'META_APPLIED'
Model.meta_tag
"""
        res = sandbox.execute(code)
        assert res.exit_code == 0
        assert res.result == "'META_APPLIED'"

    def test_safe_math_statistics_json_collections_still_work(self, sandbox):
        """Verify normal standard library usage works seamlessly."""
        code = """
import math
import json
import collections
import itertools
import statistics

d = collections.defaultdict(list)
d['key'].append(10)
d['key'].append(20)

mean_val = statistics.mean(d['key'])
json_str = json.dumps({'mean': mean_val, 'sqrt': math.sqrt(16)})
data = json.loads(json_str)
assert data['mean'] == 15
assert data['sqrt'] == 4.0
data
"""
        res = sandbox.execute(code)
        assert res.exit_code == 0
        assert res.error is None
        assert "'mean': 15" in res.result

    def test_repl_state_isolation_between_sandboxes(self):
        """Two separate sandbox instances must not share globals or state."""
        sb1 = LocalSandbox()
        sb2 = LocalSandbox()
        try:
            sb1.execute("shared_secret = 'SANDBOX_1_SECRET'")
            r1 = sb1.execute("shared_secret")
            assert r1.exit_code == 0
            assert "SANDBOX_1_SECRET" in r1.result

            r2 = sb2.execute("shared_secret")
            assert r2.exit_code != 0
            assert "NameError" in r2.stderr or "NameError" in str(r2.error)
        finally:
            sb1.terminate()
            sb2.terminate()
