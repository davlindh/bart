# NVIDIA Nemotron Architecture & NeMo Checkpoints

## 1. Architectural Foundation
NVIDIA's Nemotron family (including `nvidia/Nemotron-Mini-4B-Instruct` and larger NeMo checkpoints) is engineered for high-throughput, low-latency reasoning and conversational instruction following on standard compute hardware.

### Key Architectural Specifications:
- **Attention Mechanism**: Grouped-Query Attention (GQA) with 32 query heads and 8 key/value heads, reducing KV-cache memory overhead by 75% relative to multi-head attention.
- **Positional Encoding**: Rotary Position Embedding (RoPE) parameterized for context lengths up to 4,096 tokens (extensible to 8,192 tokens via YaRN / dynamic RoPE scaling).
- **Feed-Forward Layers**: SwiGLU non-linear gated activations with hidden intermediate dimension of 10,752.
- **Normalization**: Root Mean Square Layer Normalization (RMSNorm) with pre-normalization stability across deep transformer stacks.

---

## 2. Checkpoint Loading Modalities

`LocalModelRunner` natively inspects the target model path and automatically resolves weights:
1. **HuggingFace SafeTensors**: Loads sharded or monolithic `model.safetensors` tensors directly via memory mapping.
2. **NeMo Checkpoints (`.nemo`)**: Extracts manifest JSON and PyTorch state dicts from tar archives.
3. **ONNX & GGUF Quantized Checkpoints**: Integrates with hardware-accelerated runtimes when available.
4. **Lightweight Fallback Engine**: Mathematical zero-mock causal transformer engine executing exact self-attention without heavy third-party framework overhead.

---

## 3. Python Integration Example

```python
from antigravity.models import LocalModelRunner, ModelConfig, ModelBackend

# Initialize runner with specific backend
config = ModelConfig(
    model_id="nemotron-mini",
    model_path="nvidia/Nemotron-Mini-4B-Instruct",
    backend=ModelBackend.NEMOTRON,
    device="auto",
    precision="fp16",
    max_context_length=4096,
)

runner = LocalModelRunner()
engine = runner.load_model(config)

# Autoregressive generation
res = runner.generate("nemotron-mini", "Explain SwiGLU activation functions:")
print(res.text)
```
