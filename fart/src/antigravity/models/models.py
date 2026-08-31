"""Data models and configuration schemas for Antigravity Local Model Inference Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class ModelType(str, Enum):
    """Supported model architecture families."""
    NEMOTRON = "nemotron"
    CAUSAL_LM = "causal_lm"
    ONNX = "onnx"
    TRANSFORMER = "transformer"
    GGUF = "gguf"
    AUTO = "auto"


# --- Exceptions ---

class ModelError(Exception):
    """Base exception for model subsystem errors."""
    pass


class ModelNotFoundError(ModelError, KeyError):
    """Raised when a requested model is not found."""
    pass


class ModelLoadError(ModelError):
    """Raised when loading model weights or assets fails."""
    pass


class ModelInferenceError(ModelError):
    """Raised when text generation or chat completion fails."""
    pass


class DeviceType(str, Enum):
    """Target execution compute device."""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"
    AUTO = "auto"


class PrecisionType(str, Enum):
    """Numerical precision for model parameters."""
    FLOAT32 = "float32"
    FLOAT16 = "float16"
    BFLOAT16 = "bfloat16"
    INT8 = "int8"
    INT4 = "int4"
    AUTO = "auto"


class ModelBackend(str, Enum):
    """Inference execution backend."""
    NEMOTRON = "nemotron"
    LIGHTWEIGHT = "lightweight"
    TRANSFORMERS = "transformers"
    ONNX = "onnx"
    AUTO = "auto"


# Alias for compatibility with survey analysis
InferenceBackend = ModelBackend


class ChatMessage(BaseModel):
    """A single turn in a conversational exchange."""
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'.")
    content: str = Field(..., description="Message text content.")

    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class GenerationConfig(BaseModel):
    """Configuration parameters controlling autoregressive decoding and sampling."""
    max_new_tokens: int = Field(256, ge=1, description="Maximum number of tokens to generate.")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling cumulative probability threshold.")
    top_k: int = Field(50, ge=0, description="Top-k filtering threshold (0 to disable).")
    repetition_penalty: float = Field(1.1, ge=1.0, description="Penalty multiplier for repeated tokens.")
    stop_sequences: List[str] = Field(default_factory=list, description="Text sequences that halt generation.")
    do_sample: bool = Field(True, description="Whether to perform categorical sampling or greedy argmax.")
    pad_token_id: Optional[int] = Field(None, description="Padding token identifier.")
    eos_token_id: Optional[Union[int, List[int]]] = Field(None, description="End of sequence token ID(s).")
    seed: Optional[int] = Field(None, description="Deterministic pseudo-random generator seed.")

    model_config = ConfigDict(extra="ignore")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ModelConfig(BaseModel):
    """Configuration for initializing and loading a model engine."""
    model_id: str = Field(..., description="Model identifier, repo ID, or local file/directory path.")
    backend: ModelBackend = Field(ModelBackend.AUTO, description="Inference engine backend.")
    model_type: ModelType = Field(ModelType.AUTO, description="Architecture type family.")
    model_path: Optional[str] = Field(None, description="Local path to model weights or checkpoint.")
    tokenizer_path: Optional[str] = Field(None, description="Local path to tokenizer assets.")
    device: str = Field("cpu", description="Target device: 'cpu', 'cuda', 'mps', or 'auto'.")
    precision: str = Field("float32", description="Weight precision: 'float32', 'float16', 'bfloat16', etc.")
    max_context_length: int = Field(4096, ge=1, description="Maximum context window in tokens.")
    chat_template: Optional[str] = Field(None, description="Chat template override (e.g. 'nemotron', 'chatml').")
    trust_remote_code: bool = Field(False, description="Allow custom modeling code execution.")
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="Backend-specific parameters.")
    extra_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Additional custom kwargs.")

    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class GenerationResult(BaseModel):
    """Output returned from a model generation or chat turn."""
    text: str = Field(..., description="Generated text completion.")
    tokens_generated: int = Field(0, ge=0, description="Number of tokens generated.")
    prompt_tokens: int = Field(0, ge=0, description="Number of tokens in the input prompt.")
    finish_reason: str = Field("stop", description="Reason generation finished: 'stop', 'length', or 'eos'.")
    duration_ms: float = Field(0.0, ge=0.0, description="Generation latency in milliseconds.")
    model_id: str = Field("", description="Model identifier used for inference.")
    tokens: Optional[List[int]] = Field(None, description="Raw generated token IDs.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Auxiliary execution metadata.")

    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


@dataclass
class StreamChunk:
    """A streaming token chunk emitted incrementally during generation."""
    text: str
    token_id: int
    is_finished: bool = False
    finish_reason: Optional[str] = None


class ModelInfo(BaseModel):
    """Metadata describing a loaded model engine."""
    model_id: str = Field(..., description="Model identifier.")
    model_type: str = Field("auto", description="Model architecture type.")
    backend: str = Field("auto", description="Underlying inference backend.")
    device: str = Field("cpu", description="Execution compute device.")
    precision: str = Field("float32", description="Model precision.")
    parameter_count: int = Field(0, description="Total parameter count.")
    vocab_size: int = Field(0, description="Vocabulary size.")
    max_context_length: int = Field(4096, description="Context length.")
    is_loaded: bool = Field(False, description="Whether weights are currently resident in memory.")

    model_config = ConfigDict(extra="allow")
