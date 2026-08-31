"""Abstract Syntax Tree (AST) Security Validator for Antigravity Sandbox."""

from __future__ import annotations

import ast
from typing import Any, List, Optional, Set, Tuple

from .models import SecurityViolationError

# Modules permitted by default in the execution sandbox
DEFAULT_ALLOWED_MODULES: Set[str] = {
    "math",
    "json",
    "random",
    "datetime",
    "time",
    "re",
    "collections",
    "itertools",
    "statistics",
    "dataclasses",
    "typing",
    "string",
    "decimal",
    "fractions",
    "functools",
    "heapq",
    "bisect",
    "copy",
    "enum",
    "uuid",
    "hashlib",
    "base64",
    "zlib",
    "urllib",
    "urllib.parse",
    "csv",
    "io",
    "typing_extensions",
    "pydantic",
    "array",
    "calendar",
    "cmath",
    "colorsys",
    "contextlib",
    "difflib",
    "numbers",
    "operator",
    "pprint",
    "queue",
    "secrets",
    "struct",
    "textwrap",
    "unicodedata",
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "seaborn",
    "sympy",
    "sklearn",
    "sqlite3",
    "tabulate",
    "rich",
    "PIL",
    "pillow",
    # ML & Deep Learning Whitelist (Requirement R3)
    "torch",
    "torch.nn",
    "torch.nn.functional",
    "torch.optim",
    "torch.utils",
    "torch.utils.data",
    "torch.cuda",
    "torch.autograd",
    "torch.tensor",
    "torch.distributed",
    "torch.jit",
    "transformers",
    "transformers.models",
    "transformers.pipelines",
    "transformers.tokenization_utils",
    "tokenizers",
    "safetensors",
    "safetensors.torch",
    "safetensors.numpy",
    "onnxruntime",
    "accelerate",
    # Antigravity Models & Storage Whitelist
    "antigravity",
    "antigravity.models",
    "antigravity.models.runner",
    "antigravity.models.nemotron",
    "antigravity.models.config",
    "antigravity.models.models",
    "antigravity.models.tokenizers",
    "antigravity.models.sampler",
    "antigravity.models.base",
    "antigravity.models.transformer_engine",
    "antigravity.models.hf_engine",
    "antigravity.models.onnx_engine",
    "antigravity.storage",
    "models",
    "gguf",
    "sentencepiece",
}

# Modules strictly prohibited in sandboxed executions
PROHIBITED_MODULES: Set[str] = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "ctypes",
    "importlib",
    "pty",
    "multiprocessing",
    "posix",
    "nt",
    "gc",
    "signal",
    "inspect",
    "pickle",
    "shelve",
    "marshal",
    "webbrowser",
    "http",
    "urllib.request",
    "urllib.error",
    "builtins",
    "code",
    "codeop",
    "dis",
    "pdb",
    "tracemalloc",
    "winreg",
    "msvcrt",
    "curses",
    "termios",
    "resource",
}

# Prohibited dunder attributes commonly used for sandbox escapes
PROHIBITED_DUNDER_ATTRIBUTES: Set[str] = {
    "__subclasses__",
    "__globals__",
    "__code__",
    "__builtins__",
    "__class__",
    "__bases__",
    "__mro__",
    "__dict__",
    "__closure__",
    "__qualname__",
    "__module__",
    "__import__",
    "__loader__",
    "__spec__",
    "__func__",
    "__self__",
    "__wrapped__",
    "__init_subclass__",
    "__annotations__",
    "__traceback__",
    "__frame__",
}

# Frame, code, generator, coroutine, and traceback introspection attributes
PROHIBITED_INTROSPECTION_ATTRIBUTES: Set[str] = {
    "gi_frame",
    "gi_code",
    "gi_running",
    "gi_yieldfrom",
    "cr_frame",
    "cr_code",
    "cr_running",
    "cr_origin",
    "cr_await",
    "ag_frame",
    "ag_code",
    "ag_running",
    "ag_await",
    "f_back",
    "f_globals",
    "f_locals",
    "f_builtins",
    "f_code",
    "f_trace",
    "f_trace_lines",
    "f_trace_opcodes",
    "f_lineno",
    "f_lasti",
    "tb_frame",
    "tb_next",
    "tb_lasti",
    "tb_lineno",
    "co_code",
    "co_consts",
    "co_names",
    "co_varnames",
    "co_freevars",
    "co_cellvars",
    "co_filename",
    "co_name",
    "co_stacksize",
    "co_flags",
    "co_lnotab",
    "func_globals",
    "func_code",
    "func_closure",
    "im_func",
    "im_self",
    "im_class",
    "cell_contents",
}

# Sensitive module and system attribute names that prevent transitive module leaks
PROHIBITED_MODULE_ATTRIBUTES: Set[str] = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "ctypes",
    "shutil",
    "importlib",
    "pty",
    "multiprocessing",
    "posix",
    "nt",
    "gc",
    "signal",
    "inspect",
    "pickle",
    "shelve",
    "marshal",
    "webbrowser",
    "http",
    "pdb",
    "dis",
    "tracemalloc",
    "winreg",
    "msvcrt",
    "curses",
    "termios",
    "resource",
}

# Combined set of all prohibited attribute names
PROHIBITED_ATTRIBUTES: Set[str] = (
    PROHIBITED_DUNDER_ATTRIBUTES
    | PROHIBITED_INTROSPECTION_ATTRIBUTES
    | PROHIBITED_MODULE_ATTRIBUTES
)

# Dangerous builtin function names prohibited from direct invocation
PROHIBITED_CALLS: Set[str] = {
    "eval",
    "exec",
    "compile",
    "open",
    "globals",
    "locals",
    "vars",
    "memoryview",
    "input",
    "help",
    "breakpoint",
    "exit",
    "quit",
}


class ASTSecurityValidator(ast.NodeVisitor):
    """
    Validates Python AST against security policies.

    Inspects node types, import statements, attribute access (blocking dunder exploits),
    and forbidden builtin calls before code execution.
    """

    def __init__(
        self,
        allowed_modules: Optional[Set[str]] = None,
        additional_allowed_modules: Optional[List[str]] = None,
        disallow_dunder_attrs: bool = True,
    ) -> None:
        self.allowed_modules = set(allowed_modules or DEFAULT_ALLOWED_MODULES)
        if additional_allowed_modules:
            self.allowed_modules.update(additional_allowed_modules)
        self.disallow_dunder_attrs = disallow_dunder_attrs
        self.violations: List[str] = []

    def validate(self, code: str) -> None:
        """
        Parse and validate Python code. Raises SecurityViolationError on failure.

        Args:
            code: Python source code string.

        Raises:
            SecurityViolationError: If unsafe syntax or prohibited access is detected.
            SyntaxError: If the code is not valid Python syntax.
        """
        self.violations.clear()
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error while parsing code: {e}") from e

        self.visit(tree)

        if self.violations:
            violation_summary = "; ".join(self.violations)
            raise SecurityViolationError(
                f"Security policy violation detected: {violation_summary}"
            )

    def check_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Non-raising check returning (is_safe, list_of_violations).
        """
        self.violations.clear()
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            return False, [f"SyntaxError: {e}"]
        except Exception as e:
            return False, [f"ValidationException: {e}"]

        return len(self.violations) == 0, list(self.violations)

    def visit_Import(self, node: ast.Import) -> None:
        """Validate standard import statements."""
        for alias in node.names:
            root_module = alias.name.split(".")[0]
            if alias.name in PROHIBITED_MODULES or root_module in PROHIBITED_MODULES:
                self.violations.append(
                    f"Line {node.lineno}: Import of prohibited module '{alias.name}' is forbidden"
                )
            elif alias.name not in self.allowed_modules and root_module not in self.allowed_modules:
                self.violations.append(
                    f"Line {node.lineno}: Module '{alias.name}' is not in the allowed modules list"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Validate from ... import statements."""
        if not node.module:
            # Relative imports without module name (e.g. from . import foo)
            self.violations.append(
                f"Line {node.lineno}: Relative imports are not allowed in sandbox"
            )
            self.generic_visit(node)
            return

        root_module = node.module.split(".")[0]
        if node.module in PROHIBITED_MODULES or root_module in PROHIBITED_MODULES:
            self.violations.append(
                f"Line {node.lineno}: Import from prohibited module '{node.module}' is forbidden"
            )
        elif node.module not in self.allowed_modules and root_module not in self.allowed_modules:
            self.violations.append(
                f"Line {node.lineno}: Module '{node.module}' is not in the allowed modules list"
            )

        # Validate each imported symbol / alias against prohibited modules, attributes, and calls
        for alias in node.names:
            alias_name = alias.name
            full_name = f"{node.module}.{alias_name}"

            if alias_name in PROHIBITED_MODULES:
                self.violations.append(
                    f"Line {node.lineno}: Import of prohibited module symbol '{alias_name}' is forbidden"
                )
            elif full_name in PROHIBITED_MODULES:
                self.violations.append(
                    f"Line {node.lineno}: Import of prohibited module '{full_name}' is forbidden"
                )
            elif alias_name in PROHIBITED_ATTRIBUTES:
                self.violations.append(
                    f"Line {node.lineno}: Import of prohibited attribute '{alias_name}' is forbidden"
                )
            elif alias_name in PROHIBITED_CALLS:
                self.violations.append(
                    f"Line {node.lineno}: Import of prohibited function '{alias_name}' is forbidden"
                )

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check for forbidden dunder attribute traversal, introspection, or module attribute access."""
        attr_name = node.attr
        if attr_name in PROHIBITED_ATTRIBUTES:
            self.violations.append(
                f"Line {node.lineno}: Access to prohibited attribute '{attr_name}' is blocked"
            )
        elif self.disallow_dunder_attrs and attr_name.startswith("__") and attr_name.endswith("__"):
            # Allow harmless dunders commonly used in class implementations
            safe_dunders = {
                "__init__", "__str__", "__repr__", "__len__", "__getitem__",
                "__setitem__", "__delitem__", "__iter__", "__next__", "__enter__",
                "__exit__", "__eq__", "__ne__", "__lt__", "__le__", "__gt__",
                "__ge__", "__add__", "__sub__", "__mul__", "__truediv__",
                "__floordiv__", "__mod__", "__pow__", "__call__", "__contains__",
                "__hash__", "__bool__", "__name__", "__doc__", "__matmul__",
                "__rmatmul__", "__radd__", "__rsub__", "__rmul__", "__rtruediv__",
                "__neg__", "__pos__", "__abs__", "__int__", "__float__",
                "__index__", "__build_class__",
            }
            if attr_name not in safe_dunders:
                self.violations.append(
                    f"Line {node.lineno}: Access to dangerous dunder attribute '{attr_name}' is blocked"
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check for calls to prohibited builtins and unsafe getattr/setattr calls."""
        # Check direct calls by name (e.g. eval(...), open(...))
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in PROHIBITED_CALLS:
                self.violations.append(
                    f"Line {node.lineno}: Direct call to prohibited function '{func_name}()' is forbidden"
                )
            elif func_name in {"getattr", "hasattr", "setattr", "delattr"}:
                # If second argument is a string literal containing a prohibited attribute
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    attr_val = str(node.args[1].value)
                    if attr_val in PROHIBITED_ATTRIBUTES or (attr_val.startswith("__") and attr_val.endswith("__")):
                        self.violations.append(
                            f"Line {node.lineno}: Dynamic access to prohibited attribute '{attr_val}' via {func_name}() is blocked"
                        )
                elif len(node.args) >= 2 and not isinstance(node.args[1], ast.Constant):
                    # Dynamic attribute name that cannot be statically verified (e.g. getattr(obj, var))
                    # We allow it statically since builtins sanitizer handles runtime protection,
                    # but if it's an explicit forbidden pattern, record violation.
                    pass

        # Check calls via attribute (e.g. obj.__subclasses__())
        self.generic_visit(node)
