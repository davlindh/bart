# Sampling Parameters & Hyperparameter Tuning

## 1. Parameter Specifications

| Parameter | Type | Default | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `max_new_tokens` | integer | 256 | `1` to `8192` | Maximum count of newly generated output tokens. |
| `temperature` | float | 0.7 | `0.0` to `2.0` | Softmax logit scale. `0.0` enables greedy argmax decoding. |
| `top_p` | float | 0.9 | `0.0` to `1.0` | Cumulative probability cutoff for nucleus sampling. |
| `top_k` | integer | 50 | `0` to `1000` | Filters vocabulary to top-k highest probability tokens. |
| `repetition_penalty`| float | 1.1 | `1.0` to `2.0` | Discount factor penalizing previously generated tokens. |
| `stop_sequences` | list[str]| `[]` | N/A | Text strings that halt token generation immediately. |

---

## 2. Recommended Configuration Presets

### A. Deterministic Code & Data Parsing
```python
GenerationConfig(
    temperature=0.0,
    top_p=1.0,
    top_k=0,
    repetition_penalty=1.05,
    max_new_tokens=512,
)
```

### B. Analytical Reasoning & Plan Synthesis
```python
GenerationConfig(
    temperature=0.3,
    top_p=0.9,
    top_k=40,
    repetition_penalty=1.1,
    max_new_tokens=512,
)
```

### C. Conversational Dialogue & Ideation
```python
GenerationConfig(
    temperature=0.7,
    top_p=0.95,
    top_k=50,
    repetition_penalty=1.15,
    max_new_tokens=256,
)
```
