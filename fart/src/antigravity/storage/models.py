"""Data models, configuration, descriptors, and exception hierarchy for disk persistence."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# --- Exceptions ---

class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class StorageNotFoundError(StorageError, KeyError):
    """Raised when a requested entity or blob is not found in storage."""
    pass


class SerializationError(StorageError):
    """Raised when an object fails serialization."""
    pass


class DeserializationError(StorageError):
    """Raised when data cannot be deserialized or security constraint is violated."""
    pass


class CorruptionError(StorageError):
    """Raised when stored data fails integrity verification or is corrupted."""
    pass


# Compatibility aliases for persistence errors
PersistenceError = StorageError
PersistenceNotFoundError = StorageNotFoundError
PersistenceWriteError = SerializationError
PersistenceReadError = DeserializationError


# --- Enums & Config ---

class CodecType(str, Enum):
    """Supported serialization codec types."""
    JSON = "json"
    SAFETENSORS = "safetensors"
    NUMPY = "npy"
    PICKLE = "pickle"
    BYTES = "bytes"
    STR = "str"
    UNRESTORABLE = "unrestorable"


@dataclass
class StorageConfig:
    """Configuration for local disk persistence engine."""
    base_dir: str = "~/.antigravity/storage"
    db_name: str = "state.db"
    max_inline_bytes: int = 4096  # Store inline in SQLite if <= 4KB
    wal_mode: bool = True
    busy_timeout_ms: int = 10000
    auto_vacuum: bool = True

    def get_base_path(self) -> Path:
        """Resolve and expand base directory path."""
        expanded = os.path.expanduser(os.path.expandvars(self.base_dir))
        return Path(expanded).resolve()

    def get_db_path(self) -> Path:
        """Resolve full path to SQLite database file."""
        return self.get_base_path() / self.db_name

    def get_blobs_dir(self) -> Path:
        """Resolve directory for content-addressed binary blobs."""
        return self.get_base_path() / "blobs"

    def get_artifacts_dir(self) -> Path:
        """Resolve directory for execution artifacts."""
        return self.get_base_path() / "artifacts"

    def get_models_dir(self) -> Path:
        """Resolve directory for local model configurations and weights."""
        return self.get_base_path() / "models"

    def get_locks_dir(self) -> Path:
        """Resolve directory for cross-process locks."""
        return self.get_base_path() / "locks"


# --- Descriptors & State Vector ---

@dataclass
class VariableDescriptor:
    """Descriptor for a serialized REPL variable."""
    name: str
    type_name: str
    codec: Union[CodecType, str]
    inline_data: Optional[str] = None
    blob_hash: Optional[str] = None
    size_bytes: int = 0
    repr_str: str = ""
    is_restorable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def encoding(self) -> str:
        """Compatibility alias for codec string representation."""
        return self.codec.value if isinstance(self.codec, CodecType) else str(self.codec)

    @property
    def value_json(self) -> Optional[str]:
        """Compatibility alias for inline_data."""
        return self.inline_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert descriptor to JSON-serializable dictionary."""
        return {
            "name": self.name,
            "type_name": self.type_name,
            "codec": self.encoding,
            "inline_data": self.inline_data,
            "blob_hash": self.blob_hash,
            "size_bytes": self.size_bytes,
            "repr_str": self.repr_str,
            "is_restorable": self.is_restorable,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VariableDescriptor:
        """Construct descriptor from dictionary."""
        codec_raw = data.get("codec") or data.get("encoding", "json")
        try:
            codec = CodecType(codec_raw)
        except ValueError:
            codec = codec_raw
        return cls(
            name=data["name"],
            type_name=data.get("type_name", "object"),
            codec=codec,
            inline_data=data.get("inline_data") or data.get("value_json"),
            blob_hash=data.get("blob_hash"),
            size_bytes=int(data.get("size_bytes", 0)),
            repr_str=data.get("repr_str", ""),
            is_restorable=bool(data.get("is_restorable", True)),
            metadata=data.get("metadata", {}),
        )


# Compatibility alias
VariableRecord = VariableDescriptor


@dataclass
class StateVectorManifest:
    """State vector manifest containing metadata and all serialized variable descriptors."""
    sandbox_id: str
    timestamp: float = field(default_factory=time.time)
    variables: Dict[str, VariableDescriptor] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to JSON-serializable dictionary."""
        return {
            "sandbox_id": self.sandbox_id,
            "timestamp": self.timestamp,
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StateVectorManifest:
        """Construct manifest from dictionary."""
        vars_raw = data.get("variables", {})
        variables = {k: VariableDescriptor.from_dict(v) for k, v in vars_raw.items()}
        return cls(
            sandbox_id=data.get("sandbox_id", ""),
            timestamp=float(data.get("timestamp", time.time())),
            variables=variables,
            metadata=data.get("metadata", {}),
        )


# --- Persisted Records ---

@dataclass
class PersistedSandboxRecord:
    """Record representing a persisted sandbox session."""
    sandbox_id: str
    mode: str = "local"
    status: str = "running"
    config_json: str = "{}"
    work_dir: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    current_branch_id: Optional[str] = None
    variable_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def active_snapshot_id(self) -> Optional[str]:
        """Compatibility alias for current_branch_id."""
        return self.current_branch_id

    @property
    def env_json(self) -> str:
        """Compatibility alias for config_json."""
        return self.config_json

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "sandbox_id": self.sandbox_id,
            "mode": self.mode,
            "status": self.status,
            "config_json": self.config_json,
            "work_dir": self.work_dir,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_active_at": self.last_active_at,
            "current_branch_id": self.current_branch_id,
            "variable_count": self.variable_count,
            "metadata": self.metadata,
        }


@dataclass
class PersistedSnapshotRecord:
    """Record representing a persisted multi-branch snapshot."""
    snapshot_id: str
    sandbox_id: str
    name: str = ""
    parent_snapshot_id: Optional[str] = None
    branch_name: str = "main"
    created_at: float = field(default_factory=time.time)
    state_vector: Optional[StateVectorManifest] = None
    variable_count: int = 0
    description: str = ""
    blob_manifest: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def variables(self) -> Dict[str, VariableDescriptor]:
        """Accessor for state vector variables."""
        return self.state_vector.variables if self.state_vector else {}

    @property
    def state_metadata(self) -> Dict[str, Any]:
        """Compatibility accessor for metadata."""
        return self.metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "sandbox_id": self.sandbox_id,
            "name": self.name,
            "parent_snapshot_id": self.parent_snapshot_id,
            "branch_name": self.branch_name,
            "created_at": self.created_at,
            "variable_count": self.variable_count,
            "description": self.description,
            "blob_manifest": self.blob_manifest,
            "metadata": self.metadata,
        }


# Compatibility alias
SnapshotRecord = PersistedSnapshotRecord


@dataclass
class PersistedModelConfig:
    """Record representing a registered local model configuration."""
    model_id: str
    name: str
    architecture: str
    model_path: str
    tokenizer_path: Optional[str] = None
    device: str = "cpu"
    dtype: str = "float32"
    quantization: Optional[str] = None
    context_window: int = 4096
    generation_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model config to dictionary."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "architecture": self.architecture,
            "model_path": self.model_path,
            "tokenizer_path": self.tokenizer_path,
            "device": self.device,
            "dtype": self.dtype,
            "quantization": self.quantization,
            "context_window": self.context_window,
            "generation_params": self.generation_params,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class BlobRecord:
    """Record representing a content-addressed binary blob entry."""
    blob_hash: str
    relative_path: str
    size_bytes: int
    mime_type: str = "application/octet-stream"
    ref_count: int = 1
    created_at: float = field(default_factory=time.time)
