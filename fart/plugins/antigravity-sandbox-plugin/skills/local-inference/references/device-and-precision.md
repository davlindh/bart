# Device Selection, Precision & Memory Budgeting

## 1. Hardware Placement Matrix

`LocalModelRunner` supports dynamic and explicit compute placement:

| Target Device | Parameter | Acceleration Runtime | Best Suited For |
| :--- | :--- | :--- | :--- |
| **CUDA GPU** | `device="cuda"` or `device="cuda:0"` | NVIDIA Tensor Cores / cuDNN | High-throughput batch inference, sub-50ms latency |
| **Host CPU** | `device="cpu"` | AVX-512 / OpenMP multi-threading | Air-gapped environments, lightweight models (1B–4B) |
| **Apple Silicon** | `device="mps"` | Metal Performance Shaders | macOS development workstations |
| **Automatic** | `device="auto"` | Dynamic Hardware Probe | Automatically selects CUDA if available, falls back to CPU |

---

## 2. Numerical Precision & Memory Footprint

Model parameter precision directly dictates RAM/VRAM consumption:

| Precision Type | Bytes / Parameter | VRAM for 4B Model | Recommended Hardware |
| :--- | :--- | :--- | :--- |
| `fp32` | 4 bytes | ~16 GB | High-RAM CPU servers |
| `fp16` / `bf16` | 2 bytes | ~8 GB | NVIDIA RTX 3080/4080 (10GB+ VRAM) |
| `int8` (Quantized) | 1 byte | ~4.5 GB | Standard laptops (8GB–16GB RAM) |
| `int4` (Quantized) | 0.5 bytes | ~2.5 GB | Ultra-low power edge devices |

---

## 3. VRAM Budgeting & Offloading Best Practices

1. **Context Window Sizing**: Limit `max_seq_length` to actual task requirements (e.g. 2048 instead of 4096) to reduce KV-cache footprint.
2. **Explicit Garbage Collection**: When switching model instances in sandbox REPLs, delete active variables and trigger Python `gc.collect()` and `torch.cuda.empty_cache()` if available.
3. **Disk Offloading**: If VRAM is insufficient, specify `offload_folder="./offload"` in `load_model` to spill inactive layers to NVMe disk.
