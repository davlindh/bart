# Survey & Architectural Analysis: Requirements R2 & R3
**Date**: 2026-08-29  
**Surveyed By**: Explorer 2 (Survey R2 & R3)  
**Target Subsystems**:
- **R2**: Real Local Model Inference Engine (`src/antigravity/models/`)
- **R3**: Sandbox Integration & Security Whitelist (`src/antigravity/sandbox/ast_security.py`, `builtins_sanitizer.py`, `local_repl_worker.py`, `local_sandbox.py`)

---

## Executive Summary
This survey establishes the complete technical blueprint, interface contracts, model loader strategies, and security rules for **Requirement R2 (Real Local Model Inference Engine)** and **Requirement R3 (Sandbox Integration & Security Whitelist)**.

Key findings:
1. **Zero Mock Policy**: The inference engine (`src/antigravity/models/`) must implement real weight loading, real tokenization, real autoregressive generation with nucleus (top-p)/top-k/temperature sampling, and device placement (`CPU`/`CUDA`), with dedicated architecture support for **NVIDIA Nemotron** (`nvidia/Nemotron-Mini-4B-Instruct`, NeMo checkpoints) and lightweight real Transformer/ONNX models.
2. **Multi-Backend Architecture**: A tiered backend design (`NemotronEngine`, `HuggingFaceEngine`, `ONNXRuntimeEngine`, `LightweightTransformerEngine`) guarantees real inference execution across diverse environments: high-performance CUDA/Transformers when packages are present, ONNX Runtime for quantized graphs, and a standalone pure-math/NumPy/Torch real Transformer engine for zero-network / lightweight execution.
3. **AST Security Whitelist & Bug Remediation**:
   - `DEFAULT_ALLOWED_MODULES` must be expanded to whitelist `torch`, `transformers`, `tokenizers`, `safetensors`, `onnxruntime`, `accelerate`, `antigravity`, `antigravity.models`, and `models`.
   - **Crucial Bug Identified**: `PROHIBITED_MODULE_ATTRIBUTES` currently contains `"modules"`, which immediately breaks PyTorch's fundamental `model.modules()` and `model.named_modules()` with a false-positive `SecurityViolationError`. Removing `"modules"` from `PROHIBITED_MODULE_ATTRIBUTES` resolves this without compromising security (since `sys` and `importlib` are prohibited).
4. **Builtins & REPL Worker Hardening**:
   - `LocalREPLWorker` state extraction and snapshotting must safely handle `torch.Tensor` and model instances (avoiding `deepcopy` failures on CUDA tensors/pointers).
   - Session reset should perform memory reclamation (`torch.cuda.empty_cache()` and `gc.collect()`).

---

## Part 1: Requirement R2 — Real Local Model Inference Engine

### 1.1 Architecture & Subsystem Layout

```
src/antigravity/models/
├── __init__.py                # Public API exports (LocalModelRunner, NemotronEngine, ModelConfig, etc.)
├── config.py                  # Pydantic schemas for configs, messages, and results
├── base.py                    # BaseModelEngine abstract base class definition
├── runner.py                  # LocalModelRunner (unified entry point & model cache)
├── nemotron.py                # NemotronEngine (specialized for NVIDIA Nemotron & NeMo)
├── tokenizers.py              # Tokenizer abstractions (HF Fast Tokenizer, BPE, ByteTokenizer)
├── sampler.py                 # Real sampling loop (greedy, temperature, top-k, top-p, penalties)
└── backends/
    ├── __init__.py            # Backend registry
    ├── hf_engine.py           # HuggingFace transformers backend (AutoModelForCausalLM)
    ├── onnx_engine.py         # ONNX Runtime backend (InferenceSession)
    └── lightweight_engine.py  # Standalone real Transformer math engine (weights + forward pass)
```

---

### 1.2 Core Data Models & Schemas (`config.py`)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class ModelType(str, Enum):
    NEMOTRON = "nemotron"
    CAUSAL_LM = "causal_lm"
    ONNX = "onnx"
    TRANSFORMER = "transformer"
    GGUF = "gguf"
    AUTO = "auto"


class DeviceType(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"
    AUTO = "auto"


class PrecisionType(str, Enum):
    FLOAT32 = "float32"
    FLOAT16 = "float16"
    BFLOAT16 = "bfloat16"
    INT8 = "int8"
    INT4 = "int4"
    AUTO = "auto"


class InferenceBackend(str, Enum):
    AUTO = "auto"
    NEMOTRON = "nemotron"
    TRANSFORMERS = "transformers"
    ONNX = "onnx"
    LIGHTWEIGHT = "lightweight"


class ModelConfig(BaseModel):
    """Configuration for loading and initializing a model."""
    model_id: str = Field(..., description="Model identifier, repo ID, or local file/directory path.")
    model_type: ModelType = Field(ModelType.AUTO, description="Architecture type.")
    backend: InferenceBackend = Field(InferenceBackend.AUTO, description="Inference engine backend.")
    device: DeviceType = Field(DeviceType.AUTO, description="Target execution device.")
    precision: PrecisionType = Field(PrecisionType.AUTO, description="Weight precision.")
    max_context_length: int = Field(4096, description="Maximum context window.")
    model_path: Optional[str] = Field(None, description="Local path to model weights.")
    tokenizer_path: Optional[str] = Field(None, description="Local path to tokenizer file/dir.")
    trust_remote_code: bool = Field(False, description="Allow custom modeling code.")
    extra_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Backend-specific options.")

    model_config = ConfigDict(extra="allow")


class GenerationConfig(BaseModel):
    """Configuration parameters for autoregressive text generation."""
    max_new_tokens: int = Field(128, description="Maximum number of tokens to generate.")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling probability threshold.")
    top_k: int = Field(50, ge=0, description="Top-k filtering threshold (0 to disable).")
    repetition_penalty: float = Field(1.1, ge=1.0, description="Repetition penalty multiplier.")
    stop_sequences: List[str] = Field(default_factory=list, description="Text sequences that halt generation.")
    do_sample: bool = Field(True, description="Whether to sample or perform greedy decoding.")
    pad_token_id: Optional[int] = Field(None, description="Pad token identifier.")
    eos_token_id: Optional[Union[int, List[int]]] = Field(None, description="End of sequence token ID(s).")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility.")

    model_config = ConfigDict(extra="ignore")


class ChatMessage(BaseModel):
    """A single turn in a chat conversation."""
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'.")
    content: str = Field(..., description="Message text content.")


class GenerationResult(BaseModel):
    """Output returned from a model generation run."""
    text: str = Field(..., description="Generated text completion.")
    tokens_generated: int = Field(0, description="Number of tokens generated.")
    prompt_tokens: int = Field(0, description="Number of tokens in prompt.")
    duration_ms: float = Field(0.0, description="Generation latency in milliseconds.")
    model_id: str = Field(..., description="Model identifier used for inference.")
    finish_reason: str = Field("stop", description="Reason: 'stop', 'length', 'eos'.")
    tokens: Optional[List[int]] = Field(None, description="Raw generated token IDs.")


@dataclass
class StreamChunk:
    """A streaming token chunk emitted during generation."""
    text: str
    token_id: int
    is_finished: bool = False
    finish_reason: Optional[str] = None


class ModelInfo(BaseModel):
    """Metadata describing a loaded model."""
    model_id: str
    model_type: str
    backend: str
    device: str
    precision: str
    parameter_count: int
    vocab_size: int
    max_context_length: int
    is_loaded: bool
```

---

### 1.3 Interface Contract: `BaseModelEngine` (`base.py`)

```python
from abc import ABC, abstractmethod
from typing import Iterator, List, Optional
from .config import ChatMessage, GenerationConfig, GenerationResult, ModelConfig, ModelInfo, StreamChunk


class BaseModelEngine(ABC):
    """Abstract interface for all real model inference backends."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @abstractmethod
    def load(self) -> None:
        """Load model weights, tokenizer, and allocate execution resources."""
        pass

    @abstractmethod
    def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """Perform autoregressive token generation for a prompt."""
        pass

    @abstractmethod
    def generate_stream(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> Iterator[StreamChunk]:
        """Stream generated token chunks incrementally."""
        pass

    @abstractmethod
    def chat(
        self, messages: List[ChatMessage], config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """Format messages with chat template and generate response."""
        pass

    @abstractmethod
    def chat_stream(
        self, messages: List[ChatMessage], config: Optional[GenerationConfig] = None
    ) -> Iterator[StreamChunk]:
        """Stream response for a multi-turn chat."""
        pass

    @abstractmethod
    def tokenize(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        pass

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """Decode token IDs back to string."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Release weights and memory allocations."""
        pass

    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Retrieve model metadata."""
        pass
```

---

### 1.4 Specialized NVIDIA Nemotron Engine (`nemotron.py`)

The `NemotronEngine` provides architecture-aware loading and prompt templating for NVIDIA Nemotron models:

1. **Target Models & Formats**:
   - `nvidia/Nemotron-Mini-4B-Instruct`
   - `nvidia/nemotron-4-340b-instruct` / `nvidia/Nemotron-Nano`
   - NeMo `.nemo` checkpoint archives (extracting `model_config.yaml` and weights)
   - Hugging Face / SafeTensors format Nemotron checkpoints.
2. **Chat Template & Token Formatting**:
   - **Nemotron Format**:
     ```
     <extra_id_0>System
     {system_prompt}
     <extra_id_1>User
     {user_prompt}
     <extra_id_1>Assistant
     ```
   - **Nemotron ChatML Format**:
     ```
     <|im_start|>system
     {system_prompt}<|im_end|>
     <|im_start|>user
     {user_prompt}<|im_end|>
     <|im_start|>assistant
     ```
   - Standard stop tokens: `["<|im_end|>", "<extra_id_1>", "<|endoftext|>"]`.
3. **Nemotron Architectural Specifications**:
   - **Attention**: Grouped-Query Attention (GQA) with 32 query heads, 8 key-value heads.
   - **Activation**: SwiGLU / GeGLU non-linear activations.
   - **Position Encoding**: Rotary Position Embeddings (RoPE) with base frequency $\theta = 500000.0$.
   - **Normalization**: RMSNorm with epsilon $10^{-5}$.
4. **Execution Strategy**:
   - When `transformers` and `torch` are available, instantiates `AutoModelForCausalLM` and `AutoTokenizer` with device placement (`cuda` if available, `cpu` otherwise) and `bfloat16`/`float16`.
   - When operating in lightweight test mode or zero-dependency environment, runs a native real Nemotron Transformer computation graph using real loaded weights or calibrated local weights without mock stubs.

---

### 1.5 Standalone Real Math Inference Engine (`backends/lightweight_engine.py`)

To ensure real model execution without relying on multi-gigabyte internet downloads during automated tests, `LightweightTransformerEngine` implements:
1. **Real Autoregressive Transformer Forward Pass**:
   - Embedding lookup: $X = W_e[tokens] + W_{pos}$ (or RoPE rotation: $R_{\Theta} Q, R_{\Theta} K$).
   - Multi-Head / GQA Self-Attention: $\text{Softmax}\left(\frac{Q K^T}{\sqrt{d_k}} + M\right) V$ with causal masking.
   - RMSNorm: $x_{\text{norm}} = \frac{x}{\sqrt{\frac{1}{d}\sum x_i^2 + \epsilon}} \odot \gamma$.
   - SwiGLU Feed-Forward Network: $FFN(x) = (W_{gate} x \odot \text{silu}(W_{gate} x)) W_{down}$.
   - Output Projection: $\text{logits} = W_{out} x_L$.
2. **Real Sampling Loop (`sampler.py`)**:
   - Repetition penalty applied to previous token logits.
   - Temperature scaling: $\text{logits} \leftarrow \text{logits} / T$.
   - Top-K filtering: masking logits below rank $K$.
   - Top-P (Nucleus) filtering: sorting probabilities and truncating cumulative sum $> P$.
   - Categorical sampling via `torch.multinomial` or `np.random.choice` / cumulative distribution.
3. **Real Byte-Level BPE Tokenizer (`tokenizers.py`)**:
   - Byte-level encoding mapping UTF-8 bytes to vocabulary tokens.
   - Real merge table resolution and exact round-trip decoding.

---

### 1.6 Unified Entry Point: `LocalModelRunner` (`runner.py`)

```python
class LocalModelRunner:
    """
    Unified manager and runner for local model inference.
    Maintains an in-memory cache of loaded model engines.
    """
    _cache: Dict[str, BaseModelEngine] = {}

    def __init__(self, model_id: str, **kwargs: Any) -> None:
        self.model_id = model_id
        self.config = ModelConfig(model_id=model_id, **kwargs)
        self.engine = self._resolve_engine(self.config)

    @classmethod
    def load(cls, model_id: str, **kwargs: Any) -> LocalModelRunner:
        """Factory method to load or retrieve cached runner."""
        return cls(model_id=model_id, **kwargs)

    @classmethod
    def from_pretrained(cls, model_id: str, **kwargs: Any) -> LocalModelRunner:
        """Alias matching standard HuggingFace convention."""
        return cls.load(model_id=model_id, **kwargs)

    def _resolve_engine(self, config: ModelConfig) -> BaseModelEngine:
        # Check in-memory cache
        cache_key = f"{config.model_id}_{config.device.value}_{config.backend.value}"
        if cache_key in self._cache and self._cache[cache_key].is_loaded:
            return self._cache[cache_key]

        # Dispatch engine based on model_id and environment
        if "nemotron" in config.model_id.lower() or config.model_type == ModelType.NEMOTRON:
            engine = NemotronEngine(config)
        elif config.model_id.endswith(".onnx") or config.backend == InferenceBackend.ONNX:
            engine = ONNXRuntimeEngine(config)
        elif config.backend == InferenceBackend.TRANSFORMERS:
            engine = HuggingFaceEngine(config)
        else:
            # Auto fallback: try HuggingFace -> fallback to LightweightEngine
            engine = self._auto_dispatch(config)

        engine.load()
        self._cache[cache_key] = engine
        return engine

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        gen_config = GenerationConfig(**kwargs) if kwargs else GenerationConfig()
        return self.engine.generate(prompt, gen_config)

    def chat(self, messages: List[Union[ChatMessage, Dict[str, str]]], **kwargs: Any) -> GenerationResult:
        parsed_msgs = [
            m if isinstance(m, ChatMessage) else ChatMessage(**m) for m in messages
        ]
        gen_config = GenerationConfig(**kwargs) if kwargs else GenerationConfig()
        return self.engine.chat(parsed_msgs, gen_config)

    def tokenize(self, text: str) -> List[int]:
        return self.engine.tokenize(text)

    def decode(self, tokens: List[int]) -> str:
        return self.engine.decode(tokens)

    def unload(self) -> None:
        self.engine.unload()
```

---

## Part 2: Requirement R3 — Sandbox Integration & Security Whitelist

### 2.1 AST Security Validator Updates (`src/antigravity/sandbox/ast_security.py`)

#### 1. Expanded `DEFAULT_ALLOWED_MODULES`
The default allowed modules set must be updated to include all essential ML, tensor, and model packages:
```python
DEFAULT_ALLOWED_MODULES: Set[str] = {
    # Existing standard library and utility modules...
    "math", "json", "random", "datetime", "time", "re", "collections", "itertools",
    "statistics", "dataclasses", "typing", "string", "decimal", "fractions", "functools",
    "heapq", "bisect", "copy", "enum", "uuid", "hashlib", "base64", "zlib", "urllib",
    "urllib.parse", "csv", "io", "typing_extensions", "pydantic", "array", "calendar",
    "cmath", "colorsys", "contextlib", "difflib", "numbers", "operator", "pprint",
    "queue", "secrets", "struct", "textwrap", "unicodedata", "numpy", "pandas",
    "scipy", "matplotlib", "seaborn", "sympy", "sklearn", "sqlite3", "tabulate",
    "rich", "PIL", "pillow",

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
    "antigravity.models.tokenizers",
    "antigravity.models.sampler",
    "antigravity.models.base",
    "antigravity.storage",
    "models",
    "gguf",
    "sentencepiece",
}
```

#### 2. False Positive Bug Fix in `PROHIBITED_MODULE_ATTRIBUTES`
In `ast_security.py` line 188:
- Currently: `"modules"` is in `PROHIBITED_MODULE_ATTRIBUTES`.
- Impact: When executing standard PyTorch code like `for m in model.modules():` or `model.named_modules()`, the AST validator flags line 15 with `Access to prohibited attribute 'modules' is blocked`.
- **Fix**: Remove `"modules"` from `PROHIBITED_MODULE_ATTRIBUTES`.
- **Security Justification**: The original intent was to block `sys.modules`. However, `sys` is already completely forbidden in `PROHIBITED_MODULES` and `PROHIBITED_MODULE_ATTRIBUTES`. Therefore, `sys.modules` cannot be accessed via `sys`. Blocking the generic word `modules` is an overreach that breaks standard PyTorch operations.

---

### 2.2 Builtins Sanitizer Updates (`src/antigravity/sandbox/builtins_sanitizer.py`)

1. **Safe Importer Propagation**:
   - `create_safe_importer` must inherit the updated `DEFAULT_ALLOWED_MODULES`, ensuring that `import torch`, `from transformers import AutoModelForCausalLM`, and `from antigravity.models import LocalModelRunner` execute without `SecurityViolationError` inside the sandboxed runtime.
2. **Safe Attribute Guarding (`safe_getattr`, `safe_setattr`, `safe_hasattr`)**:
   - Verify that tensor methods and attributes (`.shape`, `.dtype`, `.device`, `.parameters()`, `.state_dict()`, `.to()`, `.cuda()`, `.cpu()`, `.generate()`, `.chat()`) pass through `safe_getattr` without interference.
   - Continue strictly enforcing blocked dunder attributes (`__subclasses__`, `__globals__`, `__code__`, `__builtins__`, `__mro__`).

---

### 2.3 Local REPL Worker & Memory Isolation (`src/antigravity/sandbox/local_repl_worker.py`)

1. **State Summary Extraction**:
   - In `_extract_state_summary()`, tensors and model runner instances should format compact repr summaries:
     ```python
     if hasattr(v, "shape") and hasattr(v, "dtype"):
         val_repr = f"Tensor(shape={v.shape}, dtype={v.dtype})"
     ```
   - Prevents memory-intensive string conversions of large weight matrices over stdio JSON pipes.
2. **Snapshotting Resilience**:
   - In `create_snapshot()`: PyTorch models or unpicklable CUDA tensors will raise on `copy.deepcopy(v)`. The existing fallback catches exceptions and retains references or serializes state dicts, preventing worker crashes.
3. **Session Reset & Resource Cleanup**:
   - In `reset_session()`: Add explicit CUDA cache emptying and garbage collection:
     ```python
     try:
         import torch
         if torch.cuda.is_available():
             torch.cuda.empty_cache()
     except Exception:
         pass
     import gc
     gc.collect()
     ```

---

## Part 3: MCP Tools & Skills Integration (R4 Connection)

The model engine directly interfaces with the Antigravity MCP Server by exposing new inference tools:
1. `load_model(model_id: str, device: Optional[str], precision: Optional[str])`
2. `model_generate(model_id: str, prompt: str, max_new_tokens: Optional[int], temperature: Optional[float])`
3. `model_chat(model_id: str, messages: List[ChatMessage], max_new_tokens: Optional[int])`

Sandboxed code executed via `execute_code` or background service workers spawned via `spawn_worker` can invoke `LocalModelRunner` directly in Python scripts:
```python
from antigravity.models import LocalModelRunner, NemotronEngine

# Real local generation inside LocalSandbox
runner = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")
result = runner.chat([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum tunneling in one sentence."}
])
print(result.text)
```

---

## Part 4: Verification & Test Plan

1. **Unit Tests (`tests/test_models.py` / `tests/tier1_features/test_model_features.py`)**:
   - Test `LocalModelRunner` loading, configuration validation, device placement resolution.
   - Test `NemotronEngine` prompt formatting, ChatML conversion, stop token detection.
   - Test real autoregressive generation with temperature, top-k, and top-p sampling.
   - Test tokenization and round-trip decoding.
2. **Sandbox Integration Tests (`tests/tier1_features/test_sandbox_model_execution.py`)**:
   - Execute Python scripts inside `LocalSandbox` importing `torch`, `transformers`, `antigravity.models`.
   - Verify `model.modules()` and `model.parameters()` execute without AST security violations.
   - Verify attempted system escapes (e.g. `import os`, accessing `__subclasses__`) remain blocked.
3. **Performance & Memory Tests**:
   - Verify `reset_session()` frees memory allocations.
   - Verify snapshotting works when model runners and tensors reside in session globals.
