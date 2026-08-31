"""ONNX Runtime inference engine backend."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterator, List, Optional, Union

from .base import BaseModelEngine
from .models import (
    ChatMessage,
    GenerationConfig,
    GenerationResult,
    ModelConfig,
    ModelInfo,
    StreamChunk,
)
from .sampler import GenerationSampler
from .tokenizers import BPETokenizer, BaseTokenizer


class ONNXRuntimeEngine(BaseModelEngine):
    """
    Inference backend executing quantized or exported ONNX computational graphs
    using Microsoft ONNX Runtime.
    """

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        super().__init__(config=config)
        self._session = None
        self._ort = None
        self._tokenizer: Optional[BaseTokenizer] = None
        self._input_names: List[str] = []
        self._output_names: List[str] = []

    def load(self, config: Optional[ModelConfig] = None) -> bool:
        """Initialize ONNX Runtime inference session."""
        if config:
            self.config = config

        try:
            import onnxruntime as ort  # type: ignore
            self._ort = ort
        except ImportError as e:
            raise ImportError(
                f"ONNXRuntimeEngine requires 'onnxruntime'. Missing dependency: {e}"
            ) from e

        model_path = self.config.model_path or self.config.model_id
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ONNX model file not found at '{model_path}'")

        # Select execution providers
        providers = ["CPUExecutionProvider"]
        if self.config.device.lower() == "cuda" and "CUDAExecutionProvider" in self._ort.get_available_providers():
            providers.insert(0, "CUDAExecutionProvider")

        sess_options = self._ort.SessionOptions()
        sess_options.enable_mem_pattern = True
        self._session = self._ort.InferenceSession(model_path, sess_options=sess_options, providers=providers)

        self._input_names = [inp.name for inp in self._session.get_inputs()]
        self._output_names = [out.name for out in self._session.get_outputs()]

        self._tokenizer = BPETokenizer()
        self._is_loaded = True
        return True

    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Autoregressively evaluate ONNX session graph and sample tokens."""
        if not self._is_loaded or self._session is None:
            self.load()

        start_time = time.perf_counter()
        gen_config = config or GenerationConfig()
        if kwargs:
            gen_config = GenerationConfig(**{**gen_config.model_dump(), **kwargs})

        sampler = GenerationSampler(gen_config)
        tokenizer = self._tokenizer or BPETokenizer()

        input_tokens = tokenizer.encode(prompt)
        if not input_tokens:
            input_tokens = [tokenizer.bos_token_id]

        generated_tokens: List[int] = []
        cur_tokens = list(input_tokens)
        finish_reason = "length"

        for _ in range(gen_config.max_new_tokens):
            # Prepare ONNX input tensor feeds
            feeds: Dict[str, Any] = {}
            if "input_ids" in self._input_names:
                feeds["input_ids"] = [cur_tokens]
            elif len(self._input_names) == 1:
                feeds[self._input_names[0]] = [cur_tokens]

            if "attention_mask" in self._input_names:
                feeds["attention_mask"] = [[1] * len(cur_tokens)]

            outputs = self._session.run(self._output_names, feeds)
            logits_tensor = outputs[0]  # Shape: [batch, seq_len, vocab_size]
            last_logits = logits_tensor[0][-1]

            next_tok = sampler.sample_next(last_logits, generated_tokens)
            generated_tokens.append(next_tok)
            cur_tokens.append(next_tok)

            if next_tok == tokenizer.eos_token_id or sampler.is_eos(next_tok):
                finish_reason = "eos"
                break

            decoded_so_far = tokenizer.decode(generated_tokens)
            stopped, _ = sampler.check_stop_sequences(decoded_so_far)
            if stopped:
                finish_reason = "stop"
                break

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        final_text = tokenizer.decode(generated_tokens)

        return GenerationResult(
            text=final_text,
            tokens_generated=len(generated_tokens),
            prompt_tokens=len(input_tokens),
            finish_reason=finish_reason,
            duration_ms=duration_ms,
            model_id=self.model_id,
            tokens=generated_tokens,
            metadata={"backend": "onnx"},
        )

    def tokenize(self, text: str) -> List[int]:
        if not self._tokenizer:
            self._tokenizer = BPETokenizer()
        return self._tokenizer.encode(text)

    def decode(self, tokens: List[int]) -> str:
        if not self._tokenizer:
            self._tokenizer = BPETokenizer()
        return self._tokenizer.decode(tokens)

    def unload(self) -> None:
        """Release ONNX session resources."""
        self._session = None
        self._is_loaded = False

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            model_id=self.model_id,
            model_type="onnx",
            backend="onnx",
            device=self.config.device,
            precision=self.config.precision,
            parameter_count=0,
            vocab_size=self._tokenizer.vocab_size if self._tokenizer else 1024,
            max_context_length=self.config.max_context_length,
            is_loaded=self._is_loaded,
        )
