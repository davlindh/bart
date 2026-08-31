"""Sanitized runtime builtins table and runtime security hooks for sandboxed execution."""

from __future__ import annotations

import builtins
from typing import Any, Dict, List, Optional, Set

from .ast_security import DEFAULT_ALLOWED_MODULES, PROHIBITED_ATTRIBUTES, PROHIBITED_MODULES
from .models import SecurityViolationError

# Safe dunder attributes that user code may legitimately inspect or call
SAFE_DUNDERS: Set[str] = {
    "__init__",
    "__str__",
    "__repr__",
    "__len__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__iter__",
    "__next__",
    "__enter__",
    "__exit__",
    "__eq__",
    "__ne__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
    "__add__",
    "__sub__",
    "__mul__",
    "__truediv__",
    "__floordiv__",
    "__mod__",
    "__pow__",
    "__call__",
    "__contains__",
    "__hash__",
    "__bool__",
    "__name__",
    "__doc__",
    "__build_class__",
    "__matmul__",
    "__rmatmul__",
    "__radd__",
    "__rsub__",
    "__rmul__",
    "__rtruediv__",
    "__neg__",
    "__pos__",
    "__abs__",
    "__int__",
    "__float__",
    "__index__",
}

# Standard safe builtin function and type names to preserve
SAFE_BUILTIN_NAMES: Set[str] = {
    "__build_class__",
    # Primitives & math
    "abs",
    "bin",
    "bool",
    "bytes",
    "bytearray",
    "complex",
    "divmod",
    "float",
    "hex",
    "int",
    "max",
    "min",
    "oct",
    "pow",
    "round",
    "sum",
    # Collections & iteration
    "all",
    "any",
    "dict",
    "enumerate",
    "filter",
    "frozenset",
    "iter",
    "len",
    "list",
    "map",
    "next",
    "range",
    "reversed",
    "set",
    "slice",
    "sorted",
    "str",
    "tuple",
    "zip",
    # Type inspection & formatting
    "callable",
    "chr",
    "dir",
    "format",
    "hash",
    "id",
    "isinstance",
    "issubclass",
    "ord",
    "repr",
    "type",
    # OOP & descriptors
    "object",
    "super",
    "property",
    "classmethod",
    "staticmethod",
    # Output
    "print",
    # Constants
    "True",
    "False",
    "None",
    "Ellipsis",
    "NotImplemented",
    # Safe exceptions
    "ArithmeticError",
    "AssertionError",
    "AttributeError",
    "BaseException",
    "BufferError",
    "BytesWarning",
    "DeprecationWarning",
    "EOFError",
    "Exception",
    "FloatingPointError",
    "FutureWarning",
    "GeneratorExit",
    "ImportError",
    "ImportWarning",
    "IndentationError",
    "IndexError",
    "KeyError",
    "KeyboardInterrupt",
    "LookupError",
    "MemoryError",
    "ModuleNotFoundError",
    "NameError",
    "NotImplementedError",
    "OverflowError",
    "PendingDeprecationWarning",
    "RecursionError",
    "ReferenceError",
    "RuntimeError",
    "RuntimeWarning",
    "StopAsyncIteration",
    "StopIteration",
    "SyntaxError",
    "SyntaxWarning",
    "SystemError",
    "TabError",
    "TypeError",
    "UnboundLocalError",
    "UnicodeDecodeError",
    "UnicodeEncodeError",
    "UnicodeError",
    "UnicodeTranslateError",
    "UnicodeWarning",
    "UserWarning",
    "ValueError",
    "Warning",
    "ZeroDivisionError",
}


def create_safe_importer(allowed_modules: Optional[Set[str]] = None):
    """
    Creates a restricted __import__ hook that only allows importing whitelisted modules.
    """
    allowed = set(allowed_modules or DEFAULT_ALLOWED_MODULES)
    real_import = builtins.__import__

    def safe_import(
        name: str,
        globals: Optional[Dict[str, Any]] = None,
        locals: Optional[Dict[str, Any]] = None,
        fromlist: tuple = (),
        level: int = 0,
    ) -> Any:
        if level > 0:
            raise SecurityViolationError(
                "Runtime relative imports are blocked by sandbox."
            )

        root_module = name.split(".")[0]
        if name in PROHIBITED_MODULES or root_module in PROHIBITED_MODULES:
            raise SecurityViolationError(
                f"Runtime import of prohibited module '{name}' is blocked by sandbox."
            )
        if root_module not in allowed and name not in allowed:
            raise SecurityViolationError(
                f"Runtime import of unauthorized module '{name}' is blocked by sandbox. Allowed: {sorted(allowed)}"
            )

        if fromlist:
            for item in fromlist:
                if isinstance(item, str):
                    submodule_full = f"{name}.{item}"
                    if submodule_full in PROHIBITED_MODULES:
                        raise SecurityViolationError(
                            f"Runtime import of prohibited submodule '{submodule_full}' is blocked by sandbox."
                        )
                    if item in PROHIBITED_MODULES:
                        raise SecurityViolationError(
                            f"Runtime import of prohibited symbol '{item}' is blocked by sandbox."
                        )
                    if item in PROHIBITED_ATTRIBUTES:
                        raise SecurityViolationError(
                            f"Runtime import of prohibited attribute '{item}' is blocked by sandbox."
                        )

        return real_import(name, globals, locals, fromlist, level)

    return safe_import


def safe_getattr(obj: Any, name: str, *default: Any) -> Any:
    """
    Guarded getattr that blocks access to prohibited dunder attributes at runtime.
    """
    if isinstance(name, str):
        if name in PROHIBITED_ATTRIBUTES:
            raise SecurityViolationError(
                f"Runtime access to prohibited attribute '{name}' is blocked."
            )
        if name.startswith("__") and name.endswith("__") and name not in SAFE_DUNDERS:
            raise SecurityViolationError(
                f"Runtime access to dangerous dunder attribute '{name}' is blocked."
            )

    if default:
        return builtins.getattr(obj, name, default[0])
    return builtins.getattr(obj, name)


def safe_setattr(obj: Any, name: str, value: Any) -> None:
    """
    Guarded setattr that blocks modification of prohibited attributes at runtime.
    """
    if isinstance(name, str):
        if name in PROHIBITED_ATTRIBUTES:
            raise SecurityViolationError(
                f"Runtime mutation of prohibited attribute '{name}' is blocked."
            )
        if name.startswith("__") and name.endswith("__") and name not in SAFE_DUNDERS:
            raise SecurityViolationError(
                f"Runtime mutation of dangerous dunder attribute '{name}' is blocked."
            )

    builtins.setattr(obj, name, value)


def safe_delattr(obj: Any, name: str) -> None:
    """
    Guarded delattr that blocks deletion of prohibited attributes at runtime.
    """
    if isinstance(name, str):
        if name in PROHIBITED_ATTRIBUTES:
            raise SecurityViolationError(
                f"Runtime deletion of prohibited attribute '{name}' is blocked."
            )
        if name.startswith("__") and name.endswith("__") and name not in SAFE_DUNDERS:
            raise SecurityViolationError(
                f"Runtime deletion of dangerous dunder attribute '{name}' is blocked."
            )

    builtins.delattr(obj, name)


def safe_hasattr(obj: Any, name: str) -> bool:
    """
    Guarded hasattr that returns False or evaluates safely without exposing blocked dunders.
    """
    if isinstance(name, str):
        if name in PROHIBITED_ATTRIBUTES:
            return False
        if name.startswith("__") and name.endswith("__") and name not in SAFE_DUNDERS:
            return False
    return builtins.hasattr(obj, name)


def get_sanitized_builtins(
    allowed_modules: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Build a secure __builtins__ dictionary containing safe builtins and guarded hooks.
    """
    sanitized: Dict[str, Any] = {}

    # Copy safe functions and exceptions from Python builtins
    for name in SAFE_BUILTIN_NAMES:
        if hasattr(builtins, name):
            sanitized[name] = getattr(builtins, name)

    # Attach guarded functions
    sanitized["__import__"] = create_safe_importer(allowed_modules)
    sanitized["getattr"] = safe_getattr
    sanitized["setattr"] = safe_setattr
    sanitized["delattr"] = safe_delattr
    sanitized["hasattr"] = safe_hasattr

    # Register custom exception
    sanitized["SecurityViolationError"] = SecurityViolationError

    return sanitized
