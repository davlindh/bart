# Worker M6 Dispatch

## 2026-08-29T02:39:04Z

<USER_REQUEST>
You are Worker M6 implementing Milestone M6 (Requirement R2: Real Local Model Inference Engine & Requirement R3: Sandbox Security Whitelist).
Working directory: c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\worker_m6
Original Request: c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\ORIGINAL_REQUEST.md
Survey Analysis: c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\explorer_survey_r2_r3\analysis.md
Project Architecture: c:\Users\info\OneDrive\Dokument\GitHub\fart\PROJECT.md
Project Root: c:\Users\info\OneDrive\Dokument\GitHub\fart

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Ownership:
You have exclusive write ownership of:
- `src/antigravity/models/` (all files: `__init__.py`, `models.py`, `base.py`, `sampler.py`, `tokenizers.py`, `nemotron.py`, `transformer_engine.py`, `hf_engine.py`, `onnx_engine.py`, `runner.py`)
- `src/antigravity/sandbox/ast_security.py` (add ML modules to whitelist and fix `"modules"` attribute false-positive)
- `src/antigravity/sandbox/builtins_sanitizer.py` (ensure ML libraries and tensor attributes operate safely)

Tasks:
1. Implement the complete `src/antigravity/models/` package per `PROJECT.md` and `explorer_survey_r2_r3/analysis.md`:
   - `models.py`: Data models (`ModelConfig`, `GenerationConfig`, `ChatMessage`, `GenerationResult`, `ModelBackend`).
   - `base.py`: Abstract `BaseModelEngine` interface.
   - `sampler.py`: Real sampling algorithms (temperature, top_k, top_p nucleus sampling, repetition penalty, greedy argmax).
   - `tokenizers.py`: Real tokenizers (BPE / Character / Nemotron ChatML tokenizer / HuggingFace AutoTokenizer wrapper).
   - `nemotron.py`: `NemotronEngine` supporting NVIDIA Nemotron architectures (`Nemotron-Mini-4B-Instruct`, NeMo checkpoints, prompt formatting with `<extra_id_0>System...` and ChatML, RoPE, SwiGLU, GQA).
   - `transformer_engine.py`: `LightweightTransformerEngine` executing pure mathematical causal self-attention, RMSNorm, SwiGLU FFN, RoPE embeddings, calibrated weights for zero-mock standalone CPU/CUDA local inference.
   - `hf_engine.py`: `HuggingFaceEngine` wrapping `transformers.AutoModelForCausalLM` and `AutoTokenizer` when installed.
   - `onnx_engine.py`: `ONNXRuntimeEngine` wrapping `onnxruntime.InferenceSession` when installed.
   - `runner.py`: `LocalModelRunner` factory and registry managing loaded models, thread-safe generation, chat completions, device selection (CPU/CUDA/Auto), memory offloading, and listing.
   - `__init__.py`: Clean package exports.
2. Update `ast_security.py`:
   - Add `torch`, `transformers`, `tokenizers`, `safetensors`, `onnxruntime`, `accelerate`, `antigravity.models`, `antigravity.storage` to `DEFAULT_ALLOWED_MODULES`.
   - Remove `"modules"` from `PROHIBITED_MODULE_ATTRIBUTES` to eliminate the false-positive on `model.modules()`.
3. Update `builtins_sanitizer.py` to ensure imports and tensor operations execute cleanly.
4. Run tests with `python -m pytest` to verify baseline stability and local model execution.
5. Write your detailed handoff report to `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\worker_m6\handoff.md` and send a message when complete.
</USER_REQUEST>
