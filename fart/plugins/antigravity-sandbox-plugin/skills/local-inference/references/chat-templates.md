# Chat Templates & Prompt Delimiters

## 1. Overview of Chat Templates
Modern instruction-tuned language models require structured token formatting to distinguish system directives, user turns, and assistant replies. `model_chat` formats multi-turn dialogue according to established template standards.

---

## 2. Supported Chat Templates

### 1. NVIDIA Nemotron Template (`chat_template="nemotron"`)
Used by `nvidia/Nemotron-Mini-4B-Instruct` and NeMo family models.

```
<extra_id_0>System
{system_message}
<extra_id_1>User
{user_message}
<extra_id_1>Assistant
{assistant_message}
<extra_id_1>User
{next_user_message}
<extra_id_1>Assistant
```

### 2. OpenAI ChatML Template (`chat_template="chatml"`)
Used by Qwen, Yi, and general ChatML fine-tunes.

```
<|im_start|>system
{system_message}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_message}<|im_end|>
<|im_start|>user
{next_user_message}<|im_end|>
<|im_start|>assistant
```

### 3. Meta Llama 3 Template (`chat_template="llama3"`)
Used by Llama-3-Instruct checkpoints.

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_message}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

### 4. Mistral Template (`chat_template="mistral"`)
Used by Mistral-7B-Instruct and Mixtral models.

```
<s>[INST] <<SYS>>
{system_message}
<</SYS>>

{user_message} [/INST] {assistant_message}</s>[INST] {next_user_message} [/INST]
```

---

## 3. Invocation in MCP

```json
{
  "tool": "model_chat",
  "arguments": {
    "model_id": "nemotron-mini",
    "chat_template": "nemotron",
    "messages": [
      {"role": "system", "content": "You are a code optimization assistant."},
      {"role": "user", "content": "Optimize this matrix multiplication routine."}
    ]
  }
}
```
