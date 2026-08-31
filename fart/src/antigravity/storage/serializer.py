"""Multi-tiered variable serialization (JSON, Safetensors/NPY, Safe Pickle, Unrestorable fallback)."""

from __future__ import annotations

import collections
import datetime
import decimal
import fractions
import importlib
import io
import json
import logging
import pickle
import sys
import time
import types
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from .disk_store import DiskStateStore
from .models import (
    CodecType,
    DeserializationError,
    SerializationError,
    StateVectorManifest,
    VariableDescriptor,
)

logger = logging.getLogger("antigravity.storage.serializer")

# Optional ML libraries
try:
    import numpy as np
except ImportError:
    np = None

try:
    import torch
except ImportError:
    torch = None

try:
    import safetensors.torch
except ImportError:
    safetensors = None


# Whitelist of safe modules and classes for RestrictedUnpickler
SAFE_MODULES: Dict[str, Union[Set[str], str]] = {
    "builtins": {
        "int", "float", "str", "bool", "bytes", "bytearray", "list", "dict",
        "set", "frozenset", "tuple", "complex", "slice", "range", "object",
        "type", "getattr", "setattr", "Exception", "ValueError", "TypeError",
        "KeyError", "IndexError", "AttributeError", "RuntimeError", "NoneType",
    },
    "_codecs": {"encode"},
    "collections": {"deque", "OrderedDict", "defaultdict", "Counter", "namedtuple"},
    "datetime": {"date", "time", "datetime", "timedelta", "timezone"},
    "decimal": {"Decimal"},
    "fractions": {"Fraction"},
    "uuid": {"UUID"},
    "dataclasses": "ALL",
    "antigravity.sandbox.models": "ALL",
    "antigravity.scheduler.models": "ALL",
    "antigravity.storage.models": "ALL",
    "__main__": "ALL",
}

BLOCKED_MODULES = {
    "os", "posix", "nt", "sys", "subprocess", "shutil", "socket", "pty",
    "importlib", "builtins.eval", "builtins.exec", "builtins.open", "builtins.__import__",
}


class RestrictedUnpickler(pickle.Unpickler):
    """
    Subclassed unpickler that restricts loading to whitelisted standard types
    and project data structures, strictly blocking dangerous system invocation objects.
    """

    def find_class(self, module: str, name: str) -> Any:
        # Check explicit blocklist
        if module in BLOCKED_MODULES or f"{module}.{name}" in BLOCKED_MODULES:
            raise DeserializationError(f"Security violation: RestrictedUnpickler blocked '{module}.{name}'")

        if module.startswith("subprocess") or module.startswith("os.") or module.startswith("sys."):
            raise DeserializationError(f"Security violation: RestrictedUnpickler blocked '{module}.{name}'")

        # Allow safe builtins
        if module == "builtins":
            allowed_builtins = SAFE_MODULES["builtins"]
            if isinstance(allowed_builtins, set) and name in allowed_builtins:
                return getattr(importlib.import_module("builtins"), name)
            raise DeserializationError(f"RestrictedUnpickler blocked builtin '{name}'")

        # Check declared safe modules
        if module in SAFE_MODULES:
            allowed = SAFE_MODULES[module]
            if allowed == "ALL" or (isinstance(allowed, set) and name in allowed):
                mod = sys.modules.get(module) or importlib.import_module(module)
                return getattr(mod, name)

        # Allow antigravity internal models
        if module.startswith("antigravity."):
            try:
                mod = sys.modules.get(module) or importlib.import_module(module)
                return getattr(mod, name)
            except Exception as e:
                raise DeserializationError(f"Failed loading class '{module}.{name}': {e}") from e

        # Allow numpy & torch primitives if installed
        if module.startswith("numpy") or module.startswith("torch"):
            try:
                mod = sys.modules.get(module) or importlib.import_module(module)
                return getattr(mod, name)
            except Exception as e:
                raise DeserializationError(f"Failed loading class '{module}.{name}': {e}") from e

        # Allow user-defined classes in main module
        if module == "__main__":
            main_mod = sys.modules.get("__main__")
            if main_mod and hasattr(main_mod, name):
                return getattr(main_mod, name)

        # By default, reject unknown global classes
        raise DeserializationError(f"RestrictedUnpickler blocked class '{module}.{name}'")


class VariableSerializer:
    """
    4-Tier Variable Serializer:
    1. JSON (primitives, lists, dicts) -> Inline or JSON blob
    2. Safetensors / NPY (NumPy arrays, Torch tensors) -> Binary blob
    3. Safe Pickle (Custom objects, sets, complex types) -> Protocol 5 blob + RestrictedUnpickler
    4. Unrestorable Fallback (File descriptors, locks, sockets) -> Metadata repr
    """

    def __init__(
        self,
        disk_store: DiskStateStore,
        max_inline_bytes: int = 4096,
    ) -> None:
        self.disk_store = disk_store
        self.max_inline_bytes = max_inline_bytes

    def _is_json_primitive(self, value: Any) -> bool:
        """Check if value is a pure JSON primitive."""
        if value is None or isinstance(value, (int, float, str, bool)):
            return True
        if isinstance(value, list):
            return all(self._is_json_primitive(v) for v in value)
        if isinstance(value, dict):
            return all(isinstance(k, str) and self._is_json_primitive(v) for k, v in value.items())
        return False

    def _is_unrestorable(self, value: Any) -> bool:
        """Identify runtime objects that cannot be restored across process boundaries."""
        if isinstance(value, (io.IOBase, types.GeneratorType, types.ModuleType)):
            return True
        # Check locks, threads, sockets
        type_str = str(type(value))
        if "lock" in type_str.lower() or "socket" in type_str.lower() or "thread" in type_str.lower():
            return True
        return False

    def serialize_variable(self, name: str, value: Any) -> VariableDescriptor:
        """
        Serialize a Python object into a VariableDescriptor, saving blob if needed.
        """
        type_name = type(value).__name__
        val_repr = repr(value)
        if len(val_repr) > 500:
            val_repr = val_repr[:500] + "... [truncated]"

        # Tier 4: Unrestorable
        if self._is_unrestorable(value):
            return VariableDescriptor(
                name=name,
                type_name=type_name,
                codec=CodecType.UNRESTORABLE,
                repr_str=val_repr,
                is_restorable=False,
                size_bytes=len(val_repr.encode("utf-8")),
            )

        # Tier 2: Safetensors / NumPy
        if np is not None and isinstance(value, np.ndarray):
            try:
                buf = io.BytesIO()
                np.save(buf, value, allow_pickle=False)
                blob_bytes = buf.getvalue()
                blob_hash = self.disk_store.write_blob(blob_bytes, ext="npy", mime_type="application/x-numpy")
                return VariableDescriptor(
                    name=name,
                    type_name="ndarray",
                    codec=CodecType.NUMPY,
                    blob_hash=blob_hash,
                    size_bytes=len(blob_bytes),
                    repr_str=val_repr,
                    is_restorable=True,
                    metadata={"shape": list(value.shape), "dtype": str(value.dtype)},
                )
            except Exception as e:
                logger.warning("Failed npy serialization for %s: %s", name, e)

        if torch is not None and isinstance(value, torch.Tensor):
            try:
                if safetensors is not None:
                    # Save via safetensors
                    tensors_dict = {"tensor": value.contiguous()}
                    blob_bytes = safetensors.torch.save(tensors_dict)
                    blob_hash = self.disk_store.write_blob(
                        blob_bytes, ext="safetensors", mime_type="application/octet-stream"
                    )
                    codec = CodecType.SAFETENSORS
                else:
                    buf = io.BytesIO()
                    torch.save(value, buf)
                    blob_bytes = buf.getvalue()
                    blob_hash = self.disk_store.write_blob(blob_bytes, ext="pt", mime_type="application/octet-stream")
                    codec = CodecType.SAFETENSORS

                return VariableDescriptor(
                    name=name,
                    type_name="Tensor",
                    codec=codec,
                    blob_hash=blob_hash,
                    size_bytes=len(blob_bytes),
                    repr_str=val_repr,
                    is_restorable=True,
                    metadata={"shape": list(value.shape), "dtype": str(value.dtype)},
                )
            except Exception as e:
                logger.warning("Failed torch serialization for %s: %s", name, e)

        # Tier 1: JSON
        if self._is_json_primitive(value):
            try:
                # Wrap tuples so they deserialize back to tuples
                metadata = {}
                if isinstance(value, tuple):
                    metadata["is_tuple"] = True
                
                json_str = json.dumps(value, ensure_ascii=False)
                json_bytes = json_str.encode("utf-8")
                size_bytes = len(json_bytes)

                if size_bytes <= self.max_inline_bytes:
                    return VariableDescriptor(
                        name=name,
                        type_name=type_name,
                        codec=CodecType.JSON,
                        inline_data=json_str,
                        size_bytes=size_bytes,
                        repr_str=val_repr,
                        is_restorable=True,
                        metadata=metadata,
                    )
                else:
                    blob_hash = self.disk_store.write_blob(
                        json_bytes, ext="json", mime_type="application/json"
                    )
                    return VariableDescriptor(
                        name=name,
                        type_name=type_name,
                        codec=CodecType.JSON,
                        blob_hash=blob_hash,
                        size_bytes=size_bytes,
                        repr_str=val_repr,
                        is_restorable=True,
                        metadata=metadata,
                    )
            except Exception as e:
                logger.debug("Falling back from JSON for variable %s: %s", name, e)

        # Tier 3: Safe Pickle
        try:
            pkl_bytes = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            size_bytes = len(pkl_bytes)
            blob_hash = self.disk_store.write_blob(
                pkl_bytes, ext="pkl", mime_type="application/x-pickle"
            )
            return VariableDescriptor(
                name=name,
                type_name=type_name,
                codec=CodecType.PICKLE,
                blob_hash=blob_hash,
                size_bytes=size_bytes,
                repr_str=val_repr,
                is_restorable=True,
            )
        except Exception as e:
            # Fallback to Tier 4 if pickle fails
            logger.warning("Pickle failed for variable %s: %s", name, e)
            return VariableDescriptor(
                name=name,
                type_name=type_name,
                codec=CodecType.UNRESTORABLE,
                repr_str=val_repr,
                is_restorable=False,
                size_bytes=len(val_repr.encode("utf-8")),
            )

    def deserialize_variable(self, descriptor: VariableDescriptor) -> Any:
        """
        Deserialize a VariableDescriptor into an active Python object.
        """
        if not descriptor.is_restorable or descriptor.codec == CodecType.UNRESTORABLE:
            logger.debug("Variable '%s' is marked unrestorable, skipping.", descriptor.name)
            return None

        codec = descriptor.codec
        if isinstance(codec, str):
            try:
                codec = CodecType(codec)
            except ValueError:
                pass

        # 1. JSON
        if codec == CodecType.JSON or codec == "json":
            if descriptor.inline_data is not None:
                val = json.loads(descriptor.inline_data)
            elif descriptor.blob_hash is not None:
                blob_bytes = self.disk_store.read_blob(descriptor.blob_hash)
                val = json.loads(blob_bytes.decode("utf-8"))
            else:
                return None

            if descriptor.metadata.get("is_tuple") and isinstance(val, list):
                val = tuple(val)
            return val

        # 2. NumPy
        if codec == CodecType.NUMPY or codec == "npy":
            if descriptor.blob_hash is None:
                raise DeserializationError(f"Missing blob hash for NumPy variable '{descriptor.name}'")
            blob_bytes = self.disk_store.read_blob(descriptor.blob_hash)
            if np is None:
                # If numpy not installed, return raw bytes or list
                logger.warning("numpy is not installed; returning raw bytes for '%s'", descriptor.name)
                return blob_bytes
            buf = io.BytesIO(blob_bytes)
            return np.load(buf, allow_pickle=False)

        # 3. Safetensors / PyTorch
        if codec == CodecType.SAFETENSORS or codec == "safetensors":
            if descriptor.blob_hash is None:
                raise DeserializationError(f"Missing blob hash for tensor variable '{descriptor.name}'")
            blob_bytes = self.disk_store.read_blob(descriptor.blob_hash)
            if safetensors is not None:
                loaded_dict = safetensors.torch.load(blob_bytes)
                return loaded_dict.get("tensor")
            elif torch is not None:
                buf = io.BytesIO(blob_bytes)
                return torch.load(buf, weights_only=True)
            else:
                logger.warning("torch / safetensors not installed; returning raw bytes for '%s'", descriptor.name)
                return blob_bytes

        # 4. Safe Pickle
        if codec == CodecType.PICKLE or codec == "pickle":
            if descriptor.blob_hash is None:
                raise DeserializationError(f"Missing blob hash for pickled variable '{descriptor.name}'")
            blob_bytes = self.disk_store.read_blob(descriptor.blob_hash)
            buf = io.BytesIO(blob_bytes)
            unpickler = RestrictedUnpickler(buf)
            try:
                return unpickler.load()
            except Exception as e:
                raise DeserializationError(f"Failed to safe-unpickle '{descriptor.name}': {e}") from e

        # Unknown / default
        raise DeserializationError(f"Unknown codec '{codec}' for variable '{descriptor.name}'")

    def serialize_namespace(
        self, namespace: Dict[str, Any], sandbox_id: str = ""
    ) -> StateVectorManifest:
        """
        Serialize an entire namespace dictionary into a StateVectorManifest.
        """
        excluded = {
            "__builtins__", "__doc__", "__name__", "__package__", "__loader__",
            "__spec__", "__artifacts__", "save_artifact", "__TASK_CONTEXT__"
        }
        manifest_vars: Dict[str, VariableDescriptor] = {}

        for k, v in namespace.items():
            if k in excluded or k.startswith("_LocalREPLWorker"):
                continue
            manifest_vars[k] = self.serialize_variable(k, v)

        return StateVectorManifest(
            sandbox_id=sandbox_id,
            timestamp=time.time(),
            variables=manifest_vars,
        )

    def deserialize_namespace(self, manifest: StateVectorManifest) -> Dict[str, Any]:
        """
        Deserialize a StateVectorManifest back into a dictionary of active variables.
        """
        namespace: Dict[str, Any] = {}
        for var_name, descriptor in manifest.variables.items():
            try:
                val = self.deserialize_variable(descriptor)
                if val is not None or descriptor.is_restorable:
                    namespace[var_name] = val
            except Exception as e:
                logger.error("Failed deserializing variable '%s': %s", var_name, e)
        return namespace
