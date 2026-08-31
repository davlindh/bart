"""Tier 2 Boundary Tests: Local Model Inference Engine Boundaries & Stress."""

import concurrent.futures
import pytest
from antigravity.models import (
    ChatMessage,
    GenerationConfig,
    GenerationResult,
    LightweightTransformerEngine,
    LocalModelRunner,
    ModelConfig,
    NemotronEngine,
    apply_repetition_penalty,
    apply_temperature,
    apply_top_k,
    apply_top_p,
    sample_token,
)


class TestSamplingBoundaries:
    """Test edge cases and mathematical boundaries in sampling."""

    def test_temperature_zero_greedy(self):
        logits = [1.0, 10.0, 2.0]
        # Temperature = 0.0 must always pick argmax index 1
        for _ in range(20):
            idx = sample_token(logits, temperature=0.0)
            assert idx == 1

    def test_temperature_high_entropy(self):
        logits = [5.0, 5.1, 4.9]
        scaled = apply_temperature(logits, temperature=2.0)
        assert scaled[0] == 2.5
        assert scaled[1] == 2.55

    def test_top_k_zero_disabled(self):
        logits = [1.0, 2.0, 3.0, 4.0]
        assert apply_top_k(logits, top_k=0) == logits

    def test_top_k_one_pure_greedy(self):
        logits = [1.0, 9.0, 3.0]
        filtered = apply_top_k(logits, top_k=1)
        assert filtered[1] == 9.0
        assert filtered[0] == -float("inf")
        assert filtered[2] == -float("inf")

    def test_top_p_zero_and_one_boundaries(self):
        logits = [1.0, 2.0, 3.0]
        assert apply_top_p(logits, top_p=1.0) == logits
        assert apply_top_p(logits, top_p=0.0) == logits

    def test_repetition_penalty_edge_cases(self):
        logits = [0.0, 0.0]
        # Zero logits remain 0.0
        assert apply_repetition_penalty(logits, [0], 1.5) == [0.0, 0.0]
        # Empty previous tokens
        assert apply_repetition_penalty([2.0, 3.0], [], 1.5) == [2.0, 3.0]


class TestModelGenerationBoundaries:
    """Test engine generation with boundary inputs."""

    def test_empty_prompt_generation(self):
        eng = LightweightTransformerEngine(
            vocab_size=256, hidden_dim=64, num_layers=2, num_heads=4, num_kv_heads=2, intermediate_dim=128
        )
        eng.load()
        res = eng.generate("", GenerationConfig(max_new_tokens=5))
        assert isinstance(res, GenerationResult)
        assert res.tokens_generated > 0

    def test_stop_sequence_clamping(self):
        eng = LightweightTransformerEngine(
            vocab_size=256, hidden_dim=64, num_layers=2, num_heads=4, num_kv_heads=2, intermediate_dim=128
        )
        eng.load()
        res = eng.generate(
            "Hello",
            GenerationConfig(max_new_tokens=20, stop_sequences=["o", "l", " "]),
        )
        assert res.finish_reason in ("stop", "eos", "length")

    def test_max_new_tokens_exact_bound(self):
        eng = LightweightTransformerEngine(
            vocab_size=256, hidden_dim=64, num_layers=2, num_heads=4, num_kv_heads=2, intermediate_dim=128
        )
        eng.load()
        res = eng.generate("Count", GenerationConfig(max_new_tokens=3, do_sample=False))
        assert res.tokens_generated <= 3


class TestConcurrentModelExecution:
    """Test multi-threaded concurrent generation through LocalModelRunner."""

    def test_concurrent_multithreaded_generation(self):
        runner = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")

        def worker_task(idx: int):
            return runner.generate(f"Thread prompt {idx}", max_new_tokens=5, temperature=0.7, seed=idx)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker_task, i) for i in range(8)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 8
        for res in results:
            assert isinstance(res, GenerationResult)
            assert res.tokens_generated > 0

    def test_unload_and_reload_cycle(self):
        runner = LocalModelRunner()
        model_id = "test_cycle_model"
        eng1 = runner.load_model(model_id)
        assert eng1.is_loaded

        # Unload
        assert runner.unload_model(model_id)
        assert runner.get_model(model_id) is None

        # Re-load
        eng2 = runner.load_model(model_id)
        assert eng2.is_loaded
        assert eng2 != eng1 or eng2.is_loaded
