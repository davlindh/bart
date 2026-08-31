"""Real sampling algorithms for autoregressive language model decoding."""

from __future__ import annotations

import bisect
import math
import random
from typing import List, Optional, Sequence, Tuple, Union

from .models import GenerationConfig


def apply_repetition_penalty(
    logits: Sequence[float],
    generated_tokens: Sequence[int],
    penalty: float,
) -> List[float]:
    """
    Apply repetition penalty to logits for previously generated tokens.
    
    Args:
        logits: Raw output logits for vocabulary.
        generated_tokens: Sequence of token IDs generated so far.
        penalty: Penalty factor (> 1.0 penalizes repetitions).
        
    Returns:
        List[float]: Modified logits.
    """
    if penalty == 1.0 or not generated_tokens:
        return list(logits)

    result = list(logits)
    vocab_size = len(result)
    seen_tokens = set(generated_tokens)

    for token_id in seen_tokens:
        if 0 <= token_id < vocab_size:
            val = result[token_id]
            if val > 0:
                result[token_id] = val / penalty
            else:
                result[token_id] = val * penalty

    return result


def apply_temperature(logits: Sequence[float], temperature: float) -> List[float]:
    """
    Scale logits by temperature parameter.
    
    Args:
        logits: Raw output logits.
        temperature: Temperature value (> 0.0).
        
    Returns:
        List[float]: Scaled logits.
    """
    if temperature <= 0.0:
        return list(logits)
    temp = max(temperature, 1e-6)
    return [l / temp for l in logits]


def apply_top_k(logits: Sequence[float], top_k: int) -> List[float]:
    """
    Filter logits to retain only the top-k highest scoring tokens.
    
    Args:
        logits: Scaled logits.
        top_k: Number of highest probability tokens to keep.
        
    Returns:
        List[float]: Masked logits with non-top-k tokens set to -inf.
    """
    if top_k <= 0 or top_k >= len(logits):
        return list(logits)

    result = list(logits)
    # Find k-th largest value
    sorted_logits = sorted(result, reverse=True)
    cutoff = sorted_logits[top_k - 1]

    neg_inf = -float("inf")
    for i in range(len(result)):
        if result[i] < cutoff:
            result[i] = neg_inf

    return result


def apply_top_p(logits: Sequence[float], top_p: float) -> List[float]:
    """
    Apply nucleus (top-p) filtering, keeping only the smallest set of tokens
    whose cumulative probability exceeds top_p.
    
    Args:
        logits: Scaled and/or top-k filtered logits.
        top_p: Cumulative probability threshold in (0.0, 1.0].
        
    Returns:
        List[float]: Masked logits.
    """
    if top_p >= 1.0 or top_p <= 0.0:
        return list(logits)

    # Compute softmax probabilities over non-infinite logits
    finite_indices = [i for i, l in enumerate(logits) if not math.isinf(l) and not math.isnan(l)]
    if not finite_indices:
        return list(logits)

    max_logit = max(logits[i] for i in finite_indices)
    exp_logits = {i: math.exp(logits[i] - max_logit) for i in finite_indices}
    sum_exp = sum(exp_logits.values())
    if sum_exp <= 0.0:
        return list(logits)

    probs = {i: exp_logits[i] / sum_exp for i in finite_indices}

    # Sort indices by probability descending
    sorted_indices = sorted(finite_indices, key=lambda idx: probs[idx], reverse=True)

    # Cumulative sum cutoff
    cum_sum = 0.0
    keep_indices = set()
    for idx in sorted_indices:
        keep_indices.add(idx)
        cum_sum += probs[idx]
        if cum_sum >= top_p:
            break

    neg_inf = -float("inf")
    result = list(logits)
    for i in range(len(result)):
        if i not in keep_indices:
            result[i] = neg_inf

    return result


def softmax(logits: Sequence[float]) -> List[float]:
    """Numerically stable softmax over a list of logits."""
    finite_vals = [l for l in logits if not math.isinf(l) and not math.isnan(l)]
    if not finite_vals:
        n = len(logits)
        return [1.0 / n] * n

    max_val = max(finite_vals)
    exps = [math.exp(l - max_val) if not math.isinf(l) and l != -float("inf") else 0.0 for l in logits]
    total = sum(exps)
    if total <= 0.0:
        n = len(logits)
        return [1.0 / n] * n
    return [e / total for e in exps]


def sample_token(
    logits: Sequence[float],
    temperature: float = 0.7,
    top_k: int = 50,
    top_p: float = 0.9,
    repetition_penalty: float = 1.0,
    generated_tokens: Optional[Sequence[int]] = None,
    do_sample: bool = True,
    rng: Optional[random.Random] = None,
) -> int:
    """
    Full sampling pipeline: repetition penalty -> temperature -> top-k -> top-p -> categorical sampling.
    
    Args:
        logits: Raw next-token logits from model forward pass.
        temperature: Softmax temperature.
        top_k: Top-k filtering rank.
        top_p: Nucleus sampling threshold.
        repetition_penalty: Repetition penalty multiplier.
        generated_tokens: Previously generated token sequence.
        do_sample: If False or temperature == 0.0, performs greedy decoding.
        rng: Optional seeded random.Random instance.
        
    Returns:
        int: Selected next token ID.
    """
    if not logits:
        return 0

    # 1. Greedy decoding shortcut
    if not do_sample or temperature == 0.0:
        # Repetition penalty can still apply in greedy mode if specified
        if repetition_penalty > 1.0 and generated_tokens:
            logits = apply_repetition_penalty(logits, generated_tokens, repetition_penalty)
        best_idx = 0
        best_val = logits[0]
        for i in range(1, len(logits)):
            if logits[i] > best_val:
                best_val = logits[i]
                best_idx = i
        return best_idx

    # 2. Apply Repetition Penalty
    cur_logits = list(logits)
    if repetition_penalty > 1.0 and generated_tokens:
        cur_logits = apply_repetition_penalty(cur_logits, generated_tokens, repetition_penalty)

    # 3. Apply Temperature
    cur_logits = apply_temperature(cur_logits, temperature)

    # 4. Apply Top-K
    if top_k > 0:
        cur_logits = apply_top_k(cur_logits, top_k)

    # 5. Apply Top-P Nucleus
    if top_p < 1.0:
        cur_logits = apply_top_p(cur_logits, top_p)

    # 6. Softmax Probabilities
    probs = softmax(cur_logits)

    # 7. Categorical Sampling via Cumulative Distribution
    rand_func = rng.random if rng is not None else random.random
    r = rand_func()

    cum_sum = 0.0
    for idx, p in enumerate(probs):
        cum_sum += p
        if r <= cum_sum:
            return idx

    return len(probs) - 1


class GenerationSampler:
    """Stateful sampler managing pseudo-random generation parameters and stop checks."""

    def __init__(self, config: Optional[GenerationConfig] = None) -> None:
        self.config = config or GenerationConfig()
        self.rng = random.Random(self.config.seed) if self.config.seed is not None else random.Random()

    def sample_next(
        self,
        logits: Sequence[float],
        generated_tokens: Optional[Sequence[int]] = None,
    ) -> int:
        """Sample the next token given model logits."""
        return sample_token(
            logits=logits,
            temperature=self.config.temperature,
            top_k=self.config.top_k,
            top_p=self.config.top_p,
            repetition_penalty=self.config.repetition_penalty,
            generated_tokens=generated_tokens,
            do_sample=self.config.do_sample,
            rng=self.rng,
        )

    def is_eos(self, token_id: int) -> bool:
        """Check if token matches EOS token configuration."""
        if self.config.eos_token_id is None:
            return False
        if isinstance(self.config.eos_token_id, list):
            return token_id in self.config.eos_token_id
        return token_id == self.config.eos_token_id

    def check_stop_sequences(
        self, text: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if any configured stop sequence occurs in the generated text.
        
        Returns:
            (has_stopped, matched_stop_sequence)
        """
        if not self.config.stop_sequences:
            return False, None

        for stop_seq in self.config.stop_sequences:
            if stop_seq and stop_seq in text:
                return True, stop_seq

        return False, None
