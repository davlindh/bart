"""Tier 1 Feature Tests: Local Model Inference Engine (Requirement R2)."""

import pytest
from antigravity.models import (
    BaseTokenizer,
    BPETokenizer,
    CharacterTokenizer,
    ChatMessage,
    DeviceType,
    GenerationConfig,
    GenerationResult,
    GenerationSampler,
    LightweightTransformerEngine,
    LocalModelRunner,
    ModelBackend,
    ModelConfig,
    ModelInfo,
    ModelType,
    NemotronEngine,
    NemotronTokenizer,
    PrecisionType,
    apply_repetition_penalty,
    apply_temperature,
    apply_top_k,
    apply_top_p,
    sample_token,
)


class TestModelConfigAndSchemas:
    """Test data models and configuration schemas."""

    def test_model_config_defaults(self):
        cfg = ModelConfig(model_id="nvidia/Nemotron-Mini-4B-Instruct")
        assert cfg.model_id == "nvidia/Nemotron-Mini-4B-Instruct"
        assert cfg.backend == ModelBackend.AUTO
        assert cfg.device == "cpu"
        assert cfg.precision == "float32"
        assert cfg.max_context_length == 4096

    def test_model_config_serialization(self):
        cfg = ModelConfig(
            model_id="test_model",
            backend=ModelBackend.NEMOTRON,
            device="cuda",
            precision="float16",
            max_context_length=2048,
        )
        data = cfg.to_dict()
        assert data["model_id"] == "test_model"
        assert data["backend"] == "nemotron"
        assert data["device"] == "cuda"
        assert data["precision"] == "float16"

    def test_generation_config_constraints(self):
        gen_cfg = GenerationConfig(
            max_new_tokens=128,
            temperature=0.8,
            top_p=0.95,
            top_k=40,
            repetition_penalty=1.2,
            stop_sequences=["</s>", "<|im_end|>"],
            seed=42,
        )
        assert gen_cfg.max_new_tokens == 128
        assert gen_cfg.temperature == 0.8
        assert len(gen_cfg.stop_sequences) == 2

    def test_chat_message_schema(self):
        msg = ChatMessage(role="user", content="Hello AI")
        assert msg.role == "user"
        assert msg.content == "Hello AI"
        d = msg.to_dict()
        assert d == {"role": "user", "content": "Hello AI"}

    def test_generation_result_model(self):
        res = GenerationResult(
            text="Quantum tunneling is a quantum mechanical effect.",
            tokens_generated=8,
            prompt_tokens=5,
            finish_reason="stop",
            duration_ms=45.2,
            model_id="nemotron",
        )
        assert res.tokens_generated == 8
        assert res.prompt_tokens == 5
        assert res.finish_reason == "stop"
        assert res.duration_ms == 45.2


class TestSamplingAlgorithms:
    """Test genuine mathematical sampling functions."""

    def test_repetition_penalty(self):
        logits = [2.0, 4.0, -2.0, 0.0]
        # Token 1 and 2 were generated before
        penalized = apply_repetition_penalty(logits, generated_tokens=[1, 2], penalty=2.0)
        assert penalized[0] == 2.0  # untouched
        assert penalized[1] == 2.0  # 4.0 / 2.0
        assert penalized[2] == -4.0  # -2.0 * 2.0
        assert penalized[3] == 0.0

    def test_temperature_scaling(self):
        logits = [1.0, 2.0, 3.0]
        scaled = apply_temperature(logits, temperature=0.5)
        assert scaled == [2.0, 4.0, 6.0]

    def test_top_k_filtering(self):
        logits = [1.0, 5.0, 3.0, 2.0, 4.0]
        # Top 2 are 5.0 (idx 1) and 4.0 (idx 4)
        filtered = apply_top_k(logits, top_k=2)
        assert filtered[1] == 5.0
        assert filtered[4] == 4.0
        assert filtered[0] == -float("inf")
        assert filtered[2] == -float("inf")
        assert filtered[3] == -float("inf")

    def test_top_p_nucleus_filtering(self):
        # Softmax of [10.0, 1.0, 1.0] makes index 0 take > 99% probability
        logits = [10.0, 1.0, 1.0]
        filtered = apply_top_p(logits, top_p=0.9)
        assert filtered[0] == 10.0
        assert filtered[1] == -float("inf")
        assert filtered[2] == -float("inf")

    def test_greedy_decoding(self):
        logits = [0.1, 0.2, 5.5, 0.3]
        idx = sample_token(logits, do_sample=False)
        assert idx == 2

    def test_deterministic_seeded_sampling(self):
        import random
        logits = [1.0, 2.0, 3.0, 4.0, 5.0]
        rng1 = random.Random(1337)
        idx1 = sample_token(logits, temperature=0.7, top_p=0.9, rng=rng1)

        rng2 = random.Random(1337)
        idx2 = sample_token(logits, temperature=0.7, top_p=0.9, rng=rng2)

        assert idx1 == idx2


class TestTokenizers:
    """Test character, BPE, and Nemotron tokenizer implementations."""

    def test_character_tokenizer_roundtrip(self):
        tok = CharacterTokenizer()
        text = "Hello, Antigravity Sandbox 2026!"
        encoded = tok.encode(text)
        assert len(encoded) > 0
        decoded = tok.decode(encoded)
        assert decoded == text

    def test_bpe_tokenizer_roundtrip(self):
        tok = BPETokenizer()
        text = "The quantum tunneling effect is observed in semiconductors."
        encoded = tok.encode(text)
        assert len(encoded) > 0
        decoded = tok.decode(encoded)
        assert decoded == text

    def test_nemotron_prompt_templating(self):
        tok = NemotronTokenizer()
        messages = [
            ChatMessage(role="system", content="You are an expert physicist."),
            ChatMessage(role="user", content="What is Hawking radiation?"),
        ]
        prompt = tok.format_nemotron_prompt(messages)
        assert "<extra_id_0>System" in prompt
        assert "You are an expert physicist." in prompt
        assert "<extra_id_1>User" in prompt
        assert "What is Hawking radiation?" in prompt
        assert prompt.endswith("<extra_id_1>Assistant\n")

    def test_chatml_prompt_templating(self):
        tok = NemotronTokenizer()
        messages = [
            ChatMessage(role="system", content="System instruction"),
            ChatMessage(role="user", content="User query"),
        ]
        prompt = tok.format_chatml_prompt(messages)
        assert "<|im_start|>system\nSystem instruction<|im_end|>" in prompt
        assert "<|im_start|>user\nUser query<|im_end|>" in prompt
        assert prompt.endswith("<|im_start|>assistant\n")


class TestLightweightTransformerEngine:
    """Test pure mathematical Transformer forward pass and generation."""

    def test_engine_load_and_info(self):
        eng = LightweightTransformerEngine(
            vocab_size=512,
            hidden_dim=64,
            num_layers=2,
            num_heads=4,
            num_kv_heads=2,
            intermediate_dim=128,
        )
        assert not eng.is_loaded
        assert eng.load()
        assert eng.is_loaded

        info = eng.model_info()
        assert info.is_loaded
        assert info.backend == "lightweight"
        assert info.parameter_count > 0

    def test_engine_text_generation(self):
        eng = LightweightTransformerEngine(
            vocab_size=512,
            hidden_dim=64,
            num_layers=2,
            num_heads=4,
            num_kv_heads=2,
            intermediate_dim=128,
        )
        eng.load()

        res = eng.generate(
            "Hello world",
            GenerationConfig(max_new_tokens=10, temperature=0.7, seed=42),
        )
        assert isinstance(res, GenerationResult)
        assert res.tokens_generated > 0
        assert res.prompt_tokens > 0
        assert res.duration_ms > 0.0

    def test_engine_streaming(self):
        eng = LightweightTransformerEngine(
            vocab_size=512,
            hidden_dim=64,
            num_layers=2,
            num_heads=4,
            num_kv_heads=2,
            intermediate_dim=128,
        )
        eng.load()

        chunks = list(eng.generate_stream("Test stream", GenerationConfig(max_new_tokens=5)))
        assert len(chunks) > 0
        assert any(c.is_finished for c in chunks)


class TestNemotronEngine:
    """Test NVIDIA Nemotron specialized engine."""

    def test_nemotron_initialization_and_chat(self):
        nemo = NemotronEngine(ModelConfig(model_id="nvidia/Nemotron-Mini-4B-Instruct"))
        assert nemo.load()
        assert nemo.is_loaded

        chat_res = nemo.chat(
            [
                ChatMessage(role="system", content="You are a helpful assistant."),
                ChatMessage(role="user", content="Explain quantum computing in one sentence."),
            ],
            GenerationConfig(max_new_tokens=15, temperature=0.0),
        )
        assert isinstance(chat_res, GenerationResult)
        assert chat_res.tokens_generated > 0
        assert chat_res.metadata.get("architecture") == "nemotron"

    def test_nemotron_stop_sequences(self):
        nemo = NemotronEngine()
        nemo.load()
        assert "<|im_end|>" in nemo.NEMOTRON_STOP_SEQUENCES
        assert "<extra_id_1>" in nemo.NEMOTRON_STOP_SEQUENCES


class TestLocalModelRunner:
    """Test unified LocalModelRunner manager and registry."""

    def test_runner_factory_and_cache(self):
        runner1 = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")
        assert runner1.engine is not None
        assert runner1.engine.is_loaded

        # Retrieve through registry
        registry = LocalModelRunner()
        model_eng = registry.get_model("nvidia/Nemotron-Mini-4B-Instruct")
        assert model_eng is not None
        assert model_eng.is_loaded

        loaded = registry.list_loaded_models()
        assert len(loaded) >= 1
        assert any(m["model_id"] == "nvidia/Nemotron-Mini-4B-Instruct" for m in loaded)

    def test_runner_generate_and_chat(self):
        runner = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")
        res = runner.generate("Test prompt", max_new_tokens=8)
        assert isinstance(res, GenerationResult)
        assert res.tokens_generated > 0

        chat_res = runner.chat(
            [{"role": "user", "content": "Tell me a joke."}],
            max_new_tokens=8,
        )
        assert isinstance(chat_res, GenerationResult)
        assert chat_res.tokens_generated > 0

    def test_runner_unload(self):
        runner = LocalModelRunner.load("test_unload_model")
        assert runner.get_model("test_unload_model") is not None
        assert runner.unload_model("test_unload_model")
        assert runner.get_model("test_unload_model") is None
