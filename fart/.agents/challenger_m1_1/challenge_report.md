# Empirical Adversarial Challenge Report: Milestone 1 (M1)

**Target**: `ASTSecurityValidator`, `get_sanitized_builtins()`, `LocalREPLWorker`, `LocalSandbox`, `SandboxManager`  
**Challenger**: Empirical Challenger 1 (critic, specialist)  
**Date**: 2026-08-29  
**Overall Verdict**: **REQUEST_CHANGES**  
**Overall Risk Assessment**: **CRITICAL**

---

## 1. Executive Summary

Milestone 1 introduces the MicroVM sandbox architecture with Firecracker microVM support and a local fallback sandbox (`LocalSandbox`) backed by AST validation, runtime builtins sanitization, and a stateful stdio JSON-RPC worker subprocess.

While the fundamental REPL state persistence, snapshotting, timeout handling, crash recovery, and baseline AST/dunder blocking mechanisms function reliably, an extensive empirical adversarial challenge revealed **two CRITICAL sandbox escape vulnerabilities**, **one HIGH import bypass vulnerability**, and **one MEDIUM functional regression**:

1. **CRITICAL Escape 1 (Transitive Module Leak)**: Standard library modules in `DEFAULT_ALLOWED_MODULES` (e.g. `fractions`, `contextlib`, `uuid`, `calendar`, `dataclasses`, `datetime`, `enum`, `statistics`, `typing`, `urllib.parse`) expose `os` and `sys` as top-level module attributes. Because `ASTSecurityValidator` only checks direct `import` statements and dunders, executing `fractions.sys.modules['os'].system(...)` or `contextlib.os.getcwd()` allows complete arbitrary host OS execution from within `LocalSandbox`.
2. **CRITICAL Escape 2 (Active Generator Call-Stack Frame Traversal)**: Active generators expose `gi_frame`. Traversal via `gen.gi_frame.f_back.f_back.f_globals` escapes into `LocalREPLWorker.execute_code` module globals, directly exposing the un-sanitized worker process `os` and `sys` modules.
3. **HIGH Escape 3 (Submodule Prohibited Import Bypass)**: `ASTSecurityValidator.visit_ImportFrom` and `builtins_sanitizer.create_safe_importer` only validate the root module name (`"urllib"`), ignoring `node.names` and `fromlist`. Thus, `from urllib import request; request.os.getcwd()` bypasses all security checks.
4. **MEDIUM Functional Flaw 4 (Missing Standard OOP Builtins)**: `SAFE_BUILTIN_NAMES` omits `object`, `super`, `property`, `classmethod`, and `staticmethod`. Any standard user class using `@property`, `@classmethod`, or `super()` raises `NameError` inside the sandbox.

---

## 2. Empirical Escape Vulnerabilities & Proofs of Concept

### Finding 1 [CRITICAL]: Transitive Sandbox Escape via Permitted Modules (`fractions.sys`, `contextlib.os`, `uuid.os`)

- **Vulnerability**: Python standard library modules internally import `os` or `sys`. When user code imports an allowed module (e.g. `import fractions`), `fractions.sys` and `fractions.sys.modules['os']` become accessible.
- **Root Cause**:
  - `src/antigravity/sandbox/ast_security.py` only inspects `ast.Import` and `ast.ImportFrom` and dunders (`PROHIBITED_ATTRIBUTES`). It does not prohibit attribute accesses to `"os"`, `"sys"`, `"subprocess"`, `"modules"`, etc. on imported objects.
  - Python attribute lookup `obj.os` is handled by bytecode (`LOAD_ATTR`), bypassing `builtins.getattr`.
- **Empirical PoC**:
  ```python
  from antigravity.sandbox import LocalSandbox
  sb = LocalSandbox()
  code = """
  import fractions
  os_mod = fractions.sys.modules['os']
  print('CWD:', os_mod.getcwd())
  print('Files:', os_mod.listdir('.')[:3])
  """
  res = sb.execute(code)
  print(res.stdout)
  # Output:
  # CWD: C:\Users\info\OneDrive\Dokument\GitHub\fart
  # Files: ['.agents', '.pytest_cache', 'demo.py']
  ```
- **Blast Radius**: Full sandbox escape; arbitrary host command execution and file system access.
- **Recommended Remediation**:
  1. In `ASTSecurityValidator.visit_Attribute`:
     ```python
     if node.attr in PROHIBITED_MODULES or node.attr in {"os", "sys", "subprocess", "socket", "ctypes", "modules", "shutil"}:
         self.violations.append(f"Line {node.lineno}: Access to prohibited module attribute '{node.attr}' is blocked")
     ```
  2. In `LocalREPLWorker._init_session` or module loader, prune or sanitize leaked attributes (`os`, `sys`) from imported modules or restrict `DEFAULT_ALLOWED_MODULES`.

---

### Finding 2 [CRITICAL]: Generator Frame Call-Stack Escape (`gi_frame.f_back.f_globals`)

- **Vulnerability**: Active generators expose `gi_frame`. An executing generator can walk `f_back` up the stack to `LocalREPLWorker.execute_code` and read its `f_globals`.
- **Root Cause**:
  - `ast_security.py` blocks `__frame__` and `__traceback__`, but does not block `gi_frame`, `cr_frame`, `ag_frame`, `f_back`, `f_globals`, `f_locals`, `f_builtins`, `f_code`, `tb_frame`, `tb_next`.
- **Empirical PoC**:
  ```python
  from antigravity.sandbox import LocalSandbox
  sb = LocalSandbox()
  code = """
  gen_holder = []
  def g():
      (yield 1)
      frame = gen_holder[0].gi_frame
      f = frame
      while f:
          if 'os' in f.f_globals:
              print('FOUND OS in worker frame:', f.f_globals['os'].getcwd())
              break
          f = f.f_back

  gen = g()
  gen_holder.append(gen)
  next(gen)
  try:
      gen.send(None)
  except StopIteration:
      pass
  """
  res = sb.execute(code)
  print(res.stdout)
  # Output: FOUND OS in worker frame: C:\Users\info\OneDrive\Dokument\GitHub\fart
  ```
- **Blast Radius**: Complete sandbox escape to worker process global namespace.
- **Recommended Remediation**:
  In `ASTSecurityValidator`, block all frame and code introspection attributes:
  ```python
  FRAME_INTROSPECTION_ATTRS = {
      "gi_frame", "gi_code", "gi_yieldfrom",
      "cr_frame", "cr_code", "cr_origin",
      "ag_frame", "ag_code",
      "f_back", "f_globals", "f_locals", "f_builtins", "f_code", "f_trace",
      "tb_frame", "tb_next", "tb_lasti", "tb_lineno",
      "co_code", "co_consts", "co_names", "co_varnames",
  }
  ```

---

### Finding 3 [HIGH]: Submodule Import Bypass (`from urllib import request`)

- **Vulnerability**: `PROHIBITED_MODULES` lists `"urllib.request"`, but `from urllib import request` executes without error and imports `urllib.request`.
- **Root Cause**:
  - `ASTSecurityValidator.visit_ImportFrom` checks `node.module` (`"urllib"`), which is in `allowed_modules`, and ignores `node.names` (`"request"`).
  - `builtins_sanitizer.create_safe_importer` checks `name.split(".")[0]` (`"urllib"`), ignoring `name` and `fromlist`.
- **Empirical PoC**:
  ```python
  from antigravity.sandbox import LocalSandbox
  sb = LocalSandbox()
  res = sb.execute("from urllib import request\nprint('request.os:', request.os.name)")
  print(res.stdout)
  # Output: request.os: nt
  ```
- **Blast Radius**: Unrestricted network connections (`urllib.request.urlopen`) and OS access via `request.os`.
- **Recommended Remediation**:
  1. In `ASTSecurityValidator.visit_ImportFrom`:
     ```python
     for alias in node.names:
         full_name = f"{node.module}.{alias.name}" if node.module else alias.name
         if full_name in PROHIBITED_MODULES or alias.name in PROHIBITED_MODULES:
             self.violations.append(f"Line {node.lineno}: Import of prohibited symbol '{full_name}' is forbidden")
     ```
  2. In `builtins_sanitizer.create_safe_importer`:
     ```python
     if name in PROHIBITED_MODULES:
         raise SecurityViolationError(f"Runtime import of prohibited module '{name}' is blocked.")
     for item in fromlist:
         if f"{name}.{item}" in PROHIBITED_MODULES or item in PROHIBITED_MODULES:
             raise SecurityViolationError(f"Runtime import of prohibited submodule '{name}.{item}' is blocked.")
     ```

---

### Finding 4 [MEDIUM]: Missing Python OOP Builtins (`object`, `super`, `property`, etc.)

- **Vulnerability**: Legitimate object-oriented Python code using `@property`, `@classmethod`, `@staticmethod`, `super()`, or `class X(object):` fails with `NameError`.
- **Root Cause**:
  `SAFE_BUILTIN_NAMES` in `builtins_sanitizer.py` omitted these standard builtins.
- **Empirical PoC**:
  ```python
  from antigravity.sandbox import LocalSandbox
  sb = LocalSandbox()
  res = sb.execute("class A:\n    @property\n    def val(self): return 1")
  # Result: NameError: name 'property' is not defined
  ```
- **Recommended Remediation**:
  Add `"object"`, `"super"`, `"property"`, `"classmethod"`, `"staticmethod"` to `SAFE_BUILTIN_NAMES`.

---

## 3. Stress Test & REPL Persistence Results

| Test Category | Tested Scenario | Expected Result | Actual Result | Status |
|---------------|-----------------|-----------------|---------------|--------|
| **REPL Persistence** | Multi-turn class definitions & method invocations | State persists across turns | Class instances & state persist across sequential turns | **PASS** |
| **REPL Persistence** | Closures, accumulators & mutable lists | Closures retain enclosed variables | State mutated across multiple turns correctly | **PASS** |
| **REPL Persistence** | Nested dicts, sets, tuples, dataclasses | Full data structure integrity | Complex nested structures preserved | **PASS** |
| **REPL Snapshotting** | Multi-branch snapshots & rollback | Exact state restoration | Deep copy snapshots branch and restore accurately | **PASS** |
| **REPL Session Reset** | `reset_session()` clears user globals | Clean namespace restored | User variables removed, sanitized builtins re-initialized | **PASS** |
| **Worker Crash Recovery**| Abrupt SIGKILL on worker process | Auto-respawn on next execute | Sandbox detects dead process and revives cleanly | **PASS** |
| **Timeout Enforcement**| Infinite loop (`while True: pass`) | Terminated at timeout (0.5s) | SandboxTimeoutError raised, next command succeeds | **PASS** |
| **Output Capping** | Massive stdout (>5MB generated) | Truncated to `max_output_bytes` | Output truncated cleanly, worker responsive | **PASS** |
| **Concurrency Stress** | 20 concurrent sandboxes in thread pool | Independent isolated lifecycles | 20/20 threads completed without deadlocks | **PASS** |
| **Direct Import Blocking**| `import os`, `import subprocess` | AST blocks syntax | Blocked with SecurityViolationError | **PASS** |
| **Direct Dunder Blocking**| `().__class__.__subclasses__()` | AST blocks dunders | Blocked with SecurityViolationError | **PASS** |
| **Unicode Obfuscation** | `__ｓｕｂｃｌａｓｓｅｓ__` | NFKC normalization catches dunder | Caught by AST parser & validator | **PASS** |
| **Indirect Transitive Leaks**| `fractions.sys.modules['os']` | Should be blocked | **VULNERABLE (Allowed)** | **FAIL** |
| **Frame Traversal** | `gen.gi_frame.f_back.f_globals` | Should be blocked | **VULNERABLE (Allowed)** | **FAIL** |
| **Submodule Import** | `from urllib import request` | Should be blocked | **VULNERABLE (Allowed)** | **FAIL** |
| **OOP Builtins Support**| `class X:\n @property\n def p(self): pass`| Builtins available | **FAIL (NameError: property)**| **FAIL** |

---

## 4. Remediation Checklist for Worker M1

- [ ] **Fix 1 (`src/antigravity/sandbox/ast_security.py`)**:
  - Add attribute blocking for prohibited modules and sensitive names (`"os"`, `"sys"`, `"subprocess"`, `"socket"`, `"ctypes"`, `"shutil"`, `"importlib"`, `"modules"`).
  - Add frame introspection attributes to `PROHIBITED_ATTRIBUTES` (`gi_frame`, `cr_frame`, `ag_frame`, `f_back`, `f_globals`, `f_locals`, `f_builtins`, `f_code`, `tb_frame`, `tb_next`, `co_code`, etc.).
  - In `visit_ImportFrom`, check each symbol in `node.names` against `PROHIBITED_MODULES` and ensure `f"{node.module}.{alias.name}"` is checked.
- [ ] **Fix 2 (`src/antigravity/sandbox/builtins_sanitizer.py`)**:
  - Add `"object"`, `"super"`, `"property"`, `"classmethod"`, `"staticmethod"` to `SAFE_BUILTIN_NAMES`.
  - In `create_safe_importer`, validate `name in PROHIBITED_MODULES` and check each element in `fromlist`.
- [ ] **Fix 3 (`tests/tier5_adversarial/test_adversarial_security.py`)**:
  - Add explicit unit tests asserting that `fractions.sys`, `contextlib.os`, `gen.gi_frame.f_back`, and `from urllib import request` are strictly rejected with `SecurityViolationError`.
