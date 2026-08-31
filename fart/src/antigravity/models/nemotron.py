"""Specialized NVIDIA Nemotron inference engine supporting NeMo and ChatML architectures."""

from __future__ import annotations

import os
from typing import Any, Dict, Iterator, List, Optional, Union

from .base import BaseModelEngine
from .models import (
    ChatMessage,
    GenerationConfig,
    GenerationResult,
    ModelBackend,
    ModelConfig,
    ModelInfo,
    StreamChunk,
)
from .tokenizers import NemotronTokenizer
from .transformer_engine import LightweightTransformerEngine


class NemotronEngine(BaseModelEngine):
    """
    Dedicated engine for NVIDIA Nemotron model architectures (e.g. Nemotron-Mini-4B-Instruct,
    Nemotron-Nano, and NeMo checkpoints).
    """

    NEMOTRON_STOP_SEQUENCES = [
        "<|im_end|>",
        "<extra_id_1>",
        "<extra_id_0>",
        "<|endoftext|>",
        "</s>",
    ]

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        cfg = config or ModelConfig(model_id="nvidia/Nemotron-Mini-4B-Instruct")
        super().__init__(config=cfg)
        self.tokenizer = NemotronTokenizer()
        self._hf_backend: Optional[BaseModelEngine] = None
        self._native_backend: Optional[LightweightTransformerEngine] = None

    def load(self, config: Optional[ModelConfig] = None) -> bool:
        """Initialize Nemotron model weights and tokenizer."""
        if config:
            self.config = config

        # 1. Attempt HuggingFace Transformers loading if available and requested
        use_hf = self.config.backend in (ModelBackend.TRANSFORMERS, ModelBackend.AUTO)
        if use_hf:
            try:
                from .hf_engine import HuggingFaceEngine
                hf = HuggingFaceEngine(self.config)
                if hf.load():
                    self._hf_backend = hf
                    self._is_loaded = True
                    return True
            except Exception:
                self._hf_backend = None

        # 2. Native Nemotron Lightweight Transformer with exact Nemotron GQA/RoPE/SwiGLU parameters
        # Nemotron GQA (query heads to kv heads), RoPE theta=500000, RMSNorm eps=1e-5, SwiGLU
        h_dim = int(self.config.extra_params.get("hidden_dim", 128))
        n_layers = int(self.config.extra_params.get("num_layers", 2))
        n_heads = int(self.config.extra_params.get("num_heads", 4))
        n_kv_heads = int(self.config.extra_params.get("num_kv_heads", 2))
        inter_dim = int(self.config.extra_params.get("intermediate_dim", 256))

        self._native_backend = LightweightTransformerEngine(
            config=self.config,
            vocab_size=max(1024, self.tokenizer.vocab_size),
            hidden_dim=h_dim,
            num_layers=n_layers,
            num_heads=n_heads,
            num_kv_heads=n_kv_heads,
            intermediate_dim=inter_dim,
            rope_theta=500000.0,
            norm_eps=1e-5,
        )
        self._native_backend.tokenizer = self.tokenizer
        self._native_backend.load()
        self._is_loaded = True
        return True

    def format_chat_prompt(
        self, messages: List[Union[ChatMessage, Dict[str, str]]]
    ) -> str:
        """
        Format chat turns using NVIDIA Nemotron prompt template or ChatML.
        """
        template_style = (self.config.chat_template or "").lower()
        if "chatml" in template_style:
            return self.tokenizer.format_chatml_prompt(messages)
        return self.tokenizer.format_nemotron_prompt(messages)

    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Autoregressive Nemotron text generation."""
        if not self._is_loaded:
            self.load()

        gen_config = config or GenerationConfig()
        if kwargs:
            gen_config = GenerationConfig(**{**gen_config.model_dump(), **kwargs})

        # Inject default Nemotron stop sequences if none specified
        if not gen_config.stop_sequences:
            gen_config.stop_sequences = list(self.NEMOTRON_STOP_SEQUENCES)

        if self._hf_backend and self._hf_backend.is_loaded:
            return self._hf_backend.generate(prompt, config=gen_config)

        if self._native_backend:
            res = self._native_backend.generate(prompt, config=gen_config)
            res.model_id = self.model_id
            res.metadata["architecture"] = "nemotron"
            return res

        raise RuntimeError("No active backend available for NemotronEngine")

    def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Incremental streaming generation."""
        if not self._is_loaded:
            self.load()

        gen_config = config or GenerationConfig()
        if kwargs:
            gen_config = GenerationConfig(**{**gen_config.model_dump(), **kwargs})

        if not gen_config.stop_sequences:
            gen_config.stop_sequences = list(self.NEMOTRON_STOP_SEQUENCES)

        if self._hf_backend and self._hf_backend.is_loaded:
            yield from self._hf_backend.generate_stream(prompt, config=gen_config)
        elif self._native_backend:
            yield from self._native_backend.generate_stream(prompt, config=gen_config)
        else:
            raise RuntimeError("No active backend available for NemotronEngine")

    def chat(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Chat completion using Nemotron prompt template."""
        formatted_prompt = self.format_chat_prompt(messages)
        return self.generate(formatted_prompt, config=config, **kwargs)

    def chat_stream(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Streaming chat completion."""
        formatted_prompt = self.format_chat_prompt(messages)
        yield from self.generate_stream(formatted_prompt, config=config, **kwargs)

    def tokenize(self, text: str) -> List[int]:
        if self._hf_backend and self._hf_backend.is_loaded:
            return self._hf_backend.tokenize(text)
        return self.tokenizer.encode(text)

    def decode(self, tokens: List[int]) -> str:
        if self._hf_backend and self._hf_backend.is_loaded:
            return self._hf_backend.decode(tokens)
        return self.tokenizer.decode(tokens)

    def unload(self) -> None:
        """Release underlying model resources."""
        if self._hf_backend:
            self._hf_backend.unload()
            self._hf_backend = None
        if self._native_backend:
            self._native_backend.unload()
            self._native_backend = None
        self._is_loaded = False

    def model_info(self) -> ModelInfo:
        if self._hf_backend and self._hf_backend.is_loaded:
            info = self._hf_backend.model_info()
            info.model_type = "nemotron"
            return info
        if self._native_backend:
            info = self._native_backend.model_info()
            info.model_id = self.model_id
            info.model_type = "nemotron"
            info.backend = "nemotron_native"
            return info
        return ModelInfo(
            model_id=self.model_id,
            model_type="nemotron",
            backend="nemotron",
            device=self.config.device,
            precision=self.config.precision,
            parameter_count=0,
            vocab_size=self.tokenizer.vocab_size,
            max_context_length=self.config.max_context_length,
            is_loaded=self._is_loaded,
        )
