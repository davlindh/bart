# Milestone 1 (M1) Challenger Handoff Report

**Target**: MicroVM Sandbox & Execution Engine (M1)  
**Agent**: Challenger 1 (critic, specialist)  
**Verdict**: **REQUEST_CHANGES**  
**Risk Level**: **CRITICAL**

---

## 1. Observation
- Inspected the M1 implementation files:
  - `src/antigravity/sandbox/ast_security.py`
  - `src/antigravity/sandbox/builtins_sanitizer.py`
  - `src/antigravity/sandbox/local_repl_worker.py`
  - `src/antigravity/sandbox/local_sandbox.py`
  - `src/antigravity/sandbox/manager.py`
  - `src/antigravity/sandbox/base.py`
- Executed the full automated test suite: `python -m pytest -v` (94 passed, 5 skipped across tiers 1-5).
- Executed empirical adversarial attack harnesses directly against `LocalSandbox` and observed the following verbatim outputs:
  1. **Transitive Module Escape via Permitted Modules**:
     - Payload: `import fractions; print(fractions.sys.modules['os'].getcwd())`
     - Verbatim Output: `C:\Users\info\OneDrive\Dokument\GitHub\fart` (exit code: 0, no error).
     - Payload: `import contextlib; print(contextlib.os.getcwd())`
     - Verbatim Output: `C:\Users\info\OneDrive\Dokument\GitHub\fart` (exit code: 0, no error).
  2. **Generator Frame Call-Stack Escape**:
     - Payload: Active generator walking `gen.gi_frame.f_back.f_back` into `execute_code` globals.
     - Verbatim Output: `FOUND OS in worker frame: C:\Users\info\OneDrive\Dokument\GitHub\fart` (exit code: 0, no error).
  3. **Submodule Import Prohibited Bypass**:
     - Payload: `from urllib import request; print(request.os.name)`
     - Verbatim Output: `request.os: nt` (exit code: 0, no error).
  4. **Missing OOP Builtins**:
     - Payload: `class A:\n    @property\n    def x(self): return 1`
     - Verbatim Output: `NameError: name 'property' is not defined` (exit code: 1).
     - Similar failures for `super()`, `classmethod`, `staticmethod`, `object`.

---

## 2. Logic Chain
1. Requirement R1 specifies a secure local fallback execution engine with AST security validation and runtime builtins sanitization preventing host escape.
2. In `src/antigravity/sandbox/ast_security.py`, `ASTSecurityValidator` inspects direct `Import` / `ImportFrom` statements and dunder attribute accesses matching `PROHIBITED_ATTRIBUTES`, but does not inspect general attribute accesses against prohibited module names (such as `.os`, `.sys`, `.subprocess`, `.modules`), nor does it block frame introspection attributes (`gi_frame`, `f_back`, `f_globals`).
3. Standard library modules in `DEFAULT_ALLOWED_MODULES` (like `fractions`, `contextlib`, `uuid`) import `os` and `sys` internally. In Python runtime, these become attributes on the imported module object. When user code accesses `fractions.sys.modules['os']`, Python resolves it via bytecode `LOAD_ATTR` (bypassing `builtins.getattr`), granting unrestricted access to `os.system()`, file operations, and host execution.
4. Python generator objects expose `gi_frame`, and executing frames expose `f_back` and `f_globals`. Traversing the call stack from an active generator yields the global namespace of `local_repl_worker.py`, containing un-sanitized references to `os` and `sys`.
5. In `visit_ImportFrom` (line 210) and `create_safe_importer` (line 170), only the root package name is evaluated against whitelist/prohibited sets. As a result, submodules like `urllib.request` bypass prohibition checks.
6. In `builtins_sanitizer.py`, `SAFE_BUILTIN_NAMES` lacks core OOP builtins (`object`, `super`, `property`, `classmethod`, `staticmethod`), breaking standard idiomatic Python classes inside the sandbox.
7. Therefore, while REPL state retention and lifecycle mechanisms are solid, the sandbox boundary has critical escape vulnerabilities and requires targeted remediation before approval.

---

## 3. Caveats
- Direct syntax exploits (`import os`, `().__class__.__subclasses__()`, `eval()`, `exec()`) are properly blocked by `ASTSecurityValidator`.
- Full REPL state persistence across turns, snapshots/rollback, error recovery, output capping, and timeout aborts are fully functional and pass all stress benchmarks.
- String formatting `"{0.__class__}".format(1)` leaks class string representations (e.g. `<class 'int'>`), but does not return mutable object handles.

---

## 4. Conclusion
**Verdict: REQUEST_CHANGES**

The M1 sandbox engine must be updated to address:
1. Block prohibited module attribute names (`"os"`, `"sys"`, `"subprocess"`, `"socket"`, `"ctypes"`, `"shutil"`, `"importlib"`, `"modules"`) in `ASTSecurityValidator.visit_Attribute`.
2. Block generator/coroutine/frame introspection attributes (`gi_frame`, `gi_code`, `cr_frame`, `cr_code`, `ag_frame`, `ag_code`, `f_back`, `f_globals`, `f_locals`, `f_builtins`, `f_code`, `tb_frame`, `tb_next`, `co_code`) in `ASTSecurityValidator`.
3. Fix `visit_ImportFrom` and `create_safe_importer` to validate imported submodules and `fromlist` symbols against `PROHIBITED_MODULES`.
4. Add `"object"`, `"super"`, `"property"`, `"classmethod"`, `"staticmethod"` to `SAFE_BUILTIN_NAMES` in `builtins_sanitizer.py`.

---

## 5. Verification Method
After applying the fixes, run the following verification harness to ensure all escapes are eliminated and the full test suite passes:

```bash
# 1. Verify escape payloads are blocked
python -c "
import sys; sys.path.insert(0, 'src')
from antigravity.sandbox import LocalSandbox
sb = LocalSandbox()
res1 = sb.execute('import fractions\nfractions.sys.modules[\"os\"].getcwd()')
assert res1.exit_code == 1, 'fractions.sys exploit must be blocked'

res2 = sb.execute('from urllib import request')
assert res2.exit_code == 1, 'urllib.request import must be blocked'

res3 = sb.execute('class A:\n    @property\n    def p(self): return 1\n    def init(self): super().__init__()')
assert res3.exit_code == 0, 'property and super must succeed'
sb.terminate()
print('Security verification successful!')
"

# 2. Run full pytest suite
python -m pytest -v
```
Expected result: All tests pass with exit code 0, and all escape attempts are blocked with `SecurityViolationError`.
