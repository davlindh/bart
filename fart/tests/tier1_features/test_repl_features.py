"""Tier 1: Feature Tests for Persistent REPL Subsystem."""

import pytest

from antigravity.sandbox import LocalSandbox


def test_multi_turn_variable_persistence(local_sandbox: LocalSandbox):
    """Verify variables defined in Turn 1 persist in Turn 2 and Turn 3."""
    res1 = local_sandbox.execute("x = 100\ny = 50")
    assert res1.is_success is True

    res2 = local_sandbox.execute("z = x + y")
    assert res2.is_success is True
    assert res2.state.get("z", {}).get("repr") == "150"

    res3 = local_sandbox.execute("z * 2")
    assert res3.is_success is True
    assert res3.result == "300"


def test_multi_turn_function_and_class_persistence(local_sandbox: LocalSandbox):
    """Verify function and class definitions persist across execution turns."""
    code_fn = """
def calculate_factorial(n):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)
"""
    res1 = local_sandbox.execute(code_fn)
    assert res1.is_success is True

    res2 = local_sandbox.execute("calculate_factorial(5)")
    assert res2.is_success is True
    assert res2.result == "120"

    code_cls = """
class DataContainer:
    def __init__(self, items):
        self.items = list(items)
    def total(self):
        return sum(self.items)
"""
    res3 = local_sandbox.execute(code_cls)
    assert res3.is_success is True

    res4 = local_sandbox.execute("container = DataContainer([10, 20, 30, 40])\ncontainer.total()")
    assert res4.is_success is True
    assert res4.result == "100"


def test_repl_expression_vs_statement_evaluation(local_sandbox: LocalSandbox):
    """Verify that statements have no return value but expressions evaluate."""
    res_stmt = local_sandbox.execute("a = 5", repl=True)
    assert res_stmt.is_success is True
    assert res_stmt.result is None

    res_expr = local_sandbox.execute("a + 10", repl=True)
    assert res_expr.is_success is True
    assert res_expr.result == "15"


def test_session_reset(local_sandbox: LocalSandbox):
    """Verify that reset_session clears user variables from the namespace."""
    local_sandbox.execute("secret_var = 'super_secret'")
    res1 = local_sandbox.execute("secret_var")
    assert res1.result == "'super_secret'"

    local_sandbox.reset_session()

    res2 = local_sandbox.execute("secret_var")
    assert res2.is_success is False
    assert "NameError" in res2.stderr or "NameError" in str(res2.error)


def test_get_variables_inspection(local_sandbox: LocalSandbox):
    """Verify that get_variables returns the summary of user-defined variables."""
    local_sandbox.execute("num = 42\nname = 'antigravity'\nitems = [1, 2, 3]")
    vars_dict = local_sandbox.get_variables()
    assert "num" in vars_dict
    assert vars_dict["num"]["type"] == "int"
    assert vars_dict["num"]["repr"] == "42"
    assert "name" in vars_dict
    assert vars_dict["name"]["type"] == "str"
    assert "items" in vars_dict


def test_artifact_collection(local_sandbox: LocalSandbox):
    """Verify explicit artifact generation and capture via __artifacts__."""
    artifact_code = (
        "__artifacts__.append({\n"
        "    'type': 'application/json',\n"
        "    'name': 'metrics.json',\n"
        "    'data': '{\"accuracy\": 0.98}'\n"
        "})\n"
    )
    res = local_sandbox.execute(artifact_code)
    assert res.is_success is True
    assert len(res.artifacts) == 1
    assert res.artifacts[0]["name"] == "metrics.json"
    assert res.artifacts[0]["type"] == "application/json"
