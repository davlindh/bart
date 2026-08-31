# Empirical Adversarial Challenge Report: Milestone 1 Iteration 2 (Re-verification)

**Target**: `ASTSecurityValidator`, `get_sanitized_builtins()`, `create_safe_importer()`, `LocalREPLWorker`, `LocalSandbox`, `SandboxManager`  
**Challenger**: Empirical Challenger (critic, specialist)  
**Date**: 2026-08-29  
**Overall Verdict**: **APPROVE**  
**Overall Risk Assessment**: **LOW**

---

## 1. Executive Summary

In Milestone 1 Iteration 1, four key vulnerabilities/flaws were identified:
1. **CRITICAL Escape 1**: Transitive module leaks exposing `sys`/`os` (`fractions.sys`, `contextlib.os`, `uuid.os`).
2. **CRITICAL Escape 2**: Active generator/coroutine call-stack frame traversal (`gen.gi_frame.f_back.f_globals`).
3. **HIGH Escape 3**: Submodule prohibited import bypass (`from urllib import request`).
4. **MEDIUM Flaw 4**: Missing OOP builtins (`object`, `super`, `property`, `classmethod`, `staticmethod`).

Worker M1 (Iteration 2) implemented comprehensive security hardening across `src/antigravity/sandbox/ast_security.py` and `src/antigravity/sandbox/builtins_sanitizer.py`.

In this re-verification cycle, an extensive empirical suite of white-box adversarial stress tests, exploit probes, and boundary checks was executed against `LocalSandbox` and `ASTSecurityValidator`.

**Key Verification Outcomes**:
- **Transitive Module Leaks**: 100% BLOCKED. `PROHIBITED_MODULE_ATTRIBUTES` and runtime `safe_getattr` proactively catch static and dynamic attribute accesses to `os`, `sys`, `modules`, `subprocess`, `socket`, `ctypes`, and related system interfaces across all allowed stdlib modules (`fractions`, `contextlib`, `uuid`, `calendar`, `dataclasses`, `enum`, `statistics`, `typing`, `urllib.parse`).
- **Call-Stack Frame Introspection**: 100% BLOCKED. All generator (`gi_frame`, `gi_code`, `gi_yieldfrom`), coroutine (`cr_frame`, `cr_code`), async generator (`ag_frame`, `ag_code`), traceback (`tb_frame`, `tb_next`), frame (`f_back`, `f_globals`, `f_locals`, `f_builtins`, `f_code`), and bytecode code object attributes (`co_code`, `co_consts`, `co_names`, `co_varnames`, `cell_contents`) are blocked.
- **Submodule Import Hardening**: 100% BLOCKED. `visit_ImportFrom` validates each alias and composite path (`f"{node.module}.{alias.name}"`), while `create_safe_importer` inspects `fromlist` elements at runtime, closing bypasses like `from urllib import request` or `__import__("urllib", fromlist=["request"])`.
- **OOP Builtins Restored**: 100% FUNCTIONAL. `@property`, `@classmethod`, `@staticmethod`, `super()`, `object`, and standard metaclass initialization execute without error.
- **Automated Test Suite**: 134 passed, 5 skipped (0 failures) across Tiers 1–5.

---

## 2. Empirical Re-Verification Results (Prior Vulnerabilities)

| Vulnerability ID | Attack Vector / Probe | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| **VULN-1A** | `import fractions; fractions.sys.modules['os'].getcwd()` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'sys' is blocked) | **FIXED** |
| **VULN-1B** | `import contextlib; contextlib.os.getcwd()` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'os' is blocked) | **FIXED** |
| **VULN-1C** | `import uuid; uuid.os.getcwd()` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'os' is blocked) | **FIXED** |
| **VULN-1D** | `import calendar; calendar.datetime.sys.modules` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'sys' is blocked) | **FIXED** |
| **VULN-1E** | `import dataclasses; dataclasses.sys.modules` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'sys' is blocked) | **FIXED** |
| **VULN-1F** | `import enum; enum.sys.modules` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'sys' is blocked) | **FIXED** |
| **VULN-1G** | `import statistics; statistics.math.sys.modules` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'sys' is blocked) | **FIXED** |
| **VULN-1H** | `import typing; typing.sys.modules` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'sys' is blocked) | **FIXED** |
| **VULN-1I** | `import urllib.parse; urllib.parse.sys.modules` | Blocked (`SecurityViolationError`) | Blocked (Line 2: Access to prohibited attribute 'sys' is blocked) | **FIXED** |
| **VULN-2A** | `gen_holder[0].gi_frame.f_back.f_globals` | Blocked (`SecurityViolationError`) | Blocked (Line 5: Access to prohibited attribute 'gi_frame' is blocked) | **FIXED** |
| **VULN-2B** | `coro().cr_frame` | Blocked (`SecurityViolationError`) | Blocked (Line 5: Access to prohibited attribute 'cr_frame' is blocked) | **FIXED** |
| **VULN-2C** | `agen().ag_frame` | Blocked (`SecurityViolationError`) | Blocked (Line 5: Access to prohibited attribute 'ag_frame' is blocked) | **FIXED** |
| **VULN-2D** | `f.__code__.co_consts` | Blocked (`SecurityViolationError`) | Blocked (Line 3: Access to prohibited attribute '__code__' is blocked) | **FIXED** |
| **VULN-2E** | `try: 1/0; except Exception as e: e.__traceback__.tb_frame` | Blocked (`SecurityViolationError`) | Blocked (Line 5: Access to prohibited attribute '__traceback__' is blocked) | **FIXED** |
| **VULN-3A** | `from urllib import request` | Blocked (`SecurityViolationError`) | Blocked (Line 1: Import of prohibited symbol 'request' is forbidden) | **FIXED** |
| **VULN-3B** | `from urllib import error` | Blocked (`SecurityViolationError`) | Blocked (Line 1: Import of prohibited symbol 'error' is forbidden) | **FIXED** |
| **VULN-3C** | `import urllib.request` | Blocked (`SecurityViolationError`) | Blocked (Line 1: Import of prohibited module 'urllib.request' is forbidden) | **FIXED** |
| **VULN-3D** | `from os import path` | Blocked (`SecurityViolationError`) | Blocked (Line 1: Import from prohibited module 'os' is forbidden) | **FIXED** |
| **VULN-3E** | `from sys import modules` | Blocked (`SecurityViolationError`) | Blocked (Line 1: Import from prohibited module 'sys' is forbidden) | **FIXED** |
| **FLAW-4** | `class Base: @property ...; super().__init__()` | Exit code 0, return value 42 | Exit code 0, return value 42 | **FIXED** |

---

## 3. New Adversarial Probes & Stress Test Results

| Category | Tested Attack Scenario | Expected Result | Actual Result | Verdict |
|---|---|---|---|---|
| **Dynamic Reflection** | `s = 'test'; getattr(s, '__class__')` | Blocked by runtime `safe_getattr` | `SecurityViolationError` raised | **PASS** |
| **Runtime Obfuscation**| `s = 'test'; getattr(s, chr(95)*2 + 'class' + chr(95)*2)` | Blocked by runtime `safe_getattr` | `SecurityViolationError` raised | **PASS** |
| **Transitive Obfuscation**| `import fractions; getattr(fractions, chr(115)+chr(121)+chr(115))` | Blocked by runtime `safe_getattr` | `SecurityViolationError` raised | **PASS** |
| **Dynamic Importer** | `__import__('os')` | Blocked by `create_safe_importer` | `SecurityViolationError` raised | **PASS** |
| **Dynamic Submodule** | `__import__('urllib', fromlist=['request'])` | Blocked by `create_safe_importer` | `SecurityViolationError` raised | **PASS** |
| **Lambda `__globals__`**| `(lambda: None).__globals__` | Blocked by AST & runtime | `SecurityViolationError` raised | **PASS** |
| **Exception Chaining** | `e.__cause__.__traceback__.tb_frame` | Blocked by AST | `SecurityViolationError` raised | **PASS** |
| **Closure Introspection**| `fn.__closure__[0].cell_contents` | Blocked by AST | `SecurityViolationError` raised | **PASS** |
| **Dangerous `__new__`**| `class M(type): def __new__(...): ...` | Blocked by AST dunder policy | Blocked (Line 3: Access to dangerous dunder '__new__' is blocked) | **PASS** |
| **Safe Metaclass** | `class M(type): def __init__(...): ...` | Successful execution | Succeeded (`'META_APPLIED'`) | **PASS** |
| **Stdlib Compatibility**| `math`, `statistics`, `json`, `collections`, `itertools` | Successful computations | Succeeded (`mean: 15, sqrt: 4.0`) | **PASS** |
| **Process Isolation** | Independent state across distinct `LocalSandbox` instances | No cross-sandbox contamination | Sandboxes completely isolated | **PASS** |

---

## 4. Test Suite Execution Summary

- **Total Test Cases**: 139 (134 passed, 5 skipped)
- **Tiers Tested**:
  - `tests/tier1_features/`: All PASSED
  - `tests/tier2_boundaries/`: All PASSED
  - `tests/tier3_cross_feature/`: All PASSED
  - `tests/tier4_workloads/`: All PASSED
  - `tests/tier5_adversarial/`: All PASSED
- **Skipped Tests**: 5 tests related to live E2B cloud microVM API credentials (`test_e2b_sandbox_start_and_execute`, `test_e2b_sandbox_pause_resume`, `test_e2b_snapshot_create_and_restore`, `test_e2b_sandbox_timeout_handling`, `test_e2b_sandbox_custom_template`), which correctly skip when `E2B_API_KEY` is not present in local test environments.

---

## 5. Conclusion & Recommendation

The sandbox implementation in Milestone 1 is robust, defensively layered (AST pre-filtering + runtime builtin table sanitization + subprocess stdio isolation + timeout watchdog), and free of known sandbox escape vulnerabilities.

**Milestone 1 is APPROVED.**
