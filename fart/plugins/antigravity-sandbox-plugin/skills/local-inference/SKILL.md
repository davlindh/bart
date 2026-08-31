---
name: local-inference
description: Load and execute real local open-weight language models (NVIDIA Nemotron-Mini-4B, NeMo checkpoints, Transformers, GGUF, ONNX) with CPU/CUDA device placement, token generation, and multi-turn chat completions directly inside the Antigravity sandbox. Use when performing local ML inference, offline text generation, Nemotron chat formatting, or in-sandbox model synthesis.
---

# Local Inference Skill

## Overview
The `local-inference` skill equips autonomous agents with real, open-weight local model inference capabilities integrated directly into the Antigravity platform. Utilizing `LocalModelRunner` and specialized architecture backends (including `NemotronEngine` and zero-mock mathematical causal attention transformers), agents can load models on local CPUs, CUDA GPUs, or Apple MPS, perform low-latency text completion, execute multi-turn conversational chat turns, and synthesize code without third-party API dependencies.

---

## Tool Reference

| Tool | Primary Purpose | Required Parameters | Optional Parameters |
| :--- | :--- | :--- | :--- |
| `load_model` | Load an open-weight model / checkpoint into memory | `model_path` | `model_id`, `model_format` (`auto`, `nemotron`, `transformers`, `onnx`, `lightweight`), `device` (`auto`, `cpu`, `cuda`), `precision` (`auto`, `fp16`, `bf16`, `fp32`, `int8`, `int4`), `max_seq_length`, `trust_remote_code`, `offload_folder` |
| `model_generate` | Generate text completions with sampling hyperparameters | `model_id`, `prompt` | `max_new_tokens`, `temperature`, `top_p`, `top_k`, `repetition_penalty`, `stop_sequences`, `stream` |
| `model_chat` | Perform conversational chat with structured templates | `model_id`, `messages` | `chat_template` (`auto`, `nemotron`, `chatml`, `llama3`, `mistral`), `system_prompt`, `max_new_tokens`, `temperature`, `top_p`, `top_k`, `repetition_penalty`, `stop_sequences` |

---

## Standard Step-by-Step Workflow

### Step 1: Discover & Load Model
Select an appropriate open-weight model checkpoint and invoke `load_model`:

```json
{
  "tool": "load_model",
  "arguments": {
    "model_path": "nvidia/Nemotron-Mini-4B-Instruct",
    "model_id": "nemotron-mini",
    "model_format": "nemotron",
    "device": "auto",
    "precision": "fp16",
    "max_seq_length": 4096
  }
}
```

**Response Example**:
```json
{
  "model_id": "nemotron-mini",
  "model_path": "nvidia/Nemotron-Mini-4B-Instruct",
  "backend": "nemotron",
  "device": "cpu",
  "precision": "fp16",
  "status": "loaded",
  "parameter_count": 4160000000,
  "max_seq_length": 4096
}
```

---

### Step 2: Autoregressive Text Completion
For single-turn completion tasks, structured JSON schema generation, or code continuation, call `model_generate`:

```json
{
  "tool": "model_generate",
  "arguments": {
    "model_id": "nemotron-mini",
    "prompt": "def calculate_moving_average(data: list[float], window_size: int) -> list[float]:\n    \"\"\"Compute rolling moving average with zero padding.\"\"\"\n",
    "max_new_tokens": 128,
    "temperature": 0.2,
    "top_p": 0.95,
    "repetition_penalty": 1.1
  }
}
```

**Response Example**:
```json
{
  "model_id": "nemotron-mini",
  "text": "    if not data or window_size <= 0:\n        return []\n    res = []\n    for i in range(len(data)):\n        start_idx = max(0, i - window_size + 1)\n        window = data[start_idx : i + 1]\n        res.append(sum(window) / len(window))\n    return res",
  "prompt_tokens": 32,
  "tokens_generated": 68,
  "finish_reason": "stop",
  "duration_ms": 142.5
}
```

---

### Step 3: Multi-Turn Conversational Chat with Chat Templates
For interactive agent dialogue, call `model_chat` with structured messages. The engine automatically applies the appropriate template delimiters:

```json
{
  "tool": "model_chat",
  "arguments": {
    "model_id": "nemotron-mini",
    "messages": [
      {
        "role": "system",
        "content": "You are a senior quantitative analyst specializing in algorithmic risk assessment."
      },
      {
        "role": "user",
        "content": "What are the primary differences between Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR)?"
      }
    ],
    "chat_template": "nemotron",
    "max_new_tokens": 256,
    "temperature": 0.7
  }
}
```

**Response Example**:
```json
{
  "model_id": "nemotron-mini",
  "message": {
    "role": "assistant",
    "content": "Value-at-Risk (VaR) measures the maximum expected loss over a specific time horizon at a given confidence level (e.g. 99%). However, VaR does not assess tail risk beyond the threshold. In contrast, Conditional Value-at-Risk (CVaR), also known as Expected Shortfall, calculates the expected loss given that the loss exceeds the VaR threshold, providing a coherent and sub-additive risk metric."
  },
  "tokens_generated": 84,
  "finish_reason": "stop",
  "duration_ms": 198.2
}
```

---

### Step 4: Direct In-Sandbox Model Execution
Sandboxed Python scripts can import and execute `LocalModelRunner` directly inside `execute_code` without AST security restrictions:

```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-analysis-01",
    "code": "from antigravity.models import LocalModelRunner\n\nrunner = LocalModelRunner.load('nvidia/Nemotron-Mini-4B-Instruct')\nsummary = runner.generate('Summarize key findings from anomaly detection', max_new_tokens=60)\nprint('SUMMARY:', summary.text)",
    "repl_mode": true
  }
}
```

---

## Detailed References
- [NVIDIA Nemotron Architecture & NeMo Checkpoints](references/nemotron-architecture.md)
- [Device Selection, Precision & Memory Budgeting](references/device-and-precision.md)
- [Chat Templates & Prompt Delimiters](references/chat-templates.md)
- [Sampling Parameters & Hyperparameter Tuning](references/generation-parameters.md)
