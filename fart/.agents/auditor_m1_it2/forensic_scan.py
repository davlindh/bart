"""Independent Forensic Analysis and Integrity Check Script for Milestone 1 Iteration 2."""

import ast
import os
import sys

def main():
    print("=== CHECK 1: PRE-POPULATED ARTIFACT DETECTION ===")
    suspicious_files = []
    for root, dirs, files in os.walk("."):
        if any(ignored in root for ignored in [".git", ".venv", "__pycache__", ".pytest_cache", ".agents"]):
            continue
        for f in files:
            if f.endswith(".log") or "result" in f.lower() or "output" in f.lower():
                suspicious_files.append(os.path.join(root, f))
    print(f"Suspicious log/result files found: {suspicious_files}")

    print("\n=== CHECK 2: SOURCE CODE FACADE & DUMMY IMPLEMENTATION SCAN ===")
    facades = []
    for root, dirs, files in os.walk("src"):
        for f in files:
            if f.endswith(".py"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8") as fh:
                    try:
                        tree = ast.parse(fh.read(), filename=p)
                    except Exception as e:
                        facades.append((p, "<parse_error>", str(e)))
                        continue
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(node.body) == 1:
                            stmt = node.body[0]
                            if isinstance(stmt, ast.Pass):
                                is_abstract = any(
                                    (isinstance(d, ast.Name) and d.id in ("abstractmethod", "override"))
                                    or (isinstance(d, ast.Attribute) and d.attr == "abstractmethod")
                                    for d in node.decorator_list
                                )
                                if not is_abstract:
                                    facades.append((p, node.name, "pass body"))
                            elif (
                                isinstance(stmt, ast.Expr)
                                and isinstance(stmt.value, ast.Constant)
                                and stmt.value.value is Ellipsis
                            ):
                                is_abstract = any(
                                    (isinstance(d, ast.Name) and d.id in ("abstractmethod", "override"))
                                    or (isinstance(d, ast.Attribute) and d.attr == "abstractmethod")
                                    for d in node.decorator_list
                                )
                                if not is_abstract:
                                    facades.append((p, node.name, "ellipsis body"))
                            elif isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                                # Check if it's a constant return in non-property or non-trivial func
                                facades.append((p, node.name, f"constant return: {stmt.value.value}"))

    print(f"Facade scan results (count: {len(facades)}):")
    for item in facades:
        print(" ", item)

    print("\n=== CHECK 3: HARDCODED TEST SPECIFIC LITERALS SCAN ===")
    test_literals = [
        "Alice",
        "('Alice', 30, 'entity', 1)",
        "Vector(1, 2)",
        "SecurityViolationError: fractions.sys",
    ]
    for lit in test_literals:
        matches = []
        for root, dirs, files in os.walk("src"):
            for f in files:
                if f.endswith(".py"):
                    p = os.path.join(root, f)
                    with open(p, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    if lit in content:
                        matches.append(p)
        print(f'Literal "{lit}" matches in src/: {matches}')

    print("\n=== CHECK 4: INDEPENDENT ADVERSARIAL BEHAVIORAL VERIFICATION ===")
    sys.path.insert(0, os.path.abspath("src"))
    from antigravity.sandbox import LocalSandbox, SecurityViolationError, ASTSecurityValidator
    from antigravity.sandbox.builtins_sanitizer import create_safe_importer, safe_getattr, get_sanitized_builtins

    # 1. Test AST security on transitive imports and frame access
    validator = ASTSecurityValidator()
    
    # Positive tests
    assert validator.check_code("import math\nx = math.sin(3.14)")[0] is True
    assert validator.check_code("import json\ny = json.loads('{}')")[0] is True
    assert validator.check_code("from urllib.parse import urlparse")[0] is True
    
    # Negative tests (Security)
    assert validator.check_code("import fractions\nx = fractions.sys")[0] is False
    assert validator.check_code("from urllib import request")[0] is False
    assert validator.check_code("from urllib import error")[0] is False
    assert validator.check_code("import contextlib\nx = contextlib.os")[0] is False
    assert validator.check_code("x = gen.gi_frame.f_back")[0] is False
    assert validator.check_code("x = obj.__class__.__subclasses__()")[0] is False
    assert validator.check_code("x = open('passwords.txt')")[0] is False
    print("AST Security Validator independent checks: ALL PASSED")

    # 2. Test Builtins Sanitizer and runtime safe importer
    importer = create_safe_importer()
    import pytest
    try:
        importer("os")
        raise AssertionError("importer('os') should have raised SecurityViolationError")
    except SecurityViolationError:
        pass

    try:
        importer("urllib", fromlist=("request",))
        raise AssertionError("importer('urllib', fromlist=('request',)) should have raised SecurityViolationError")
    except SecurityViolationError:
        pass

    try:
        importer("fractions", fromlist=("sys",))
        raise AssertionError("importer('fractions', fromlist=('sys',)) should have raised SecurityViolationError")
    except SecurityViolationError:
        pass

    # Allowed imports
    m = importer("math")
    assert hasattr(m, "sqrt")
    u = importer("urllib", fromlist=("parse",))
    assert hasattr(u, "parse")
    print("Builtins sanitizer importer independent checks: ALL PASSED")

    # 3. Test LocalSandbox subprocess execution
    sandbox = LocalSandbox()
    
    # Safe code with OOP, property, super, math, list comp
    code_oop = '''
class Counter:
    def __init__(self, init_val=0):
        self._val = init_val
    @property
    def val(self):
        return self._val
    def inc(self, step=1):
        self._val += step
        return self._val

class SuperCounter(Counter):
    def __init__(self, init_val=0, mult=2):
        super().__init__(init_val)
        self.mult = mult
    def step(self):
        super().inc(self.mult)
        return self.val

sc = SuperCounter(10, 5)
sc.step()
sc.val
'''
    res = sandbox.execute(code_oop)
    assert res.exit_code == 0, f"OOP execution failed: {res.stderr}"
    assert res.result == "15", f"Expected result 15, got {res.result}"
    print("LocalSandbox OOP execution test: PASSED (result = 15)")

    # Test that forbidden actions fail inside LocalSandbox
    res_bad1 = sandbox.execute("import fractions\nx = fractions.sys.modules")
    assert res_bad1.exit_code == 1
    assert "SecurityViolationError" in res_bad1.stderr or "SecurityViolationError" in str(res_bad1.error)
    print("LocalSandbox transitive escape blocked: PASSED")

    res_bad2 = sandbox.execute("from urllib import request")
    assert res_bad2.exit_code == 1
    assert "SecurityViolationError" in res_bad2.stderr or "SecurityViolationError" in str(res_bad2.error)
    print("LocalSandbox submodule escape blocked: PASSED")

    # Test state persistence across turns
    res_state = sandbox.execute("sc.step()\nsc.val")
    assert res_state.exit_code == 0
    assert res_state.result == "20"
    print("LocalSandbox state persistence: PASSED (result = 20)")

    sandbox.terminate()
    print("\n=== ALL INDEPENDENT FORENSIC CHECKS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
