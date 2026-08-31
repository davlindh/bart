"""HuggingFace Transformers inference engine backend."""

from __future__ import annotations

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


class HuggingFaceEngine(BaseModelEngine):
    """
    Inference backend leveraging Hugging Face transformers.AutoModelForCausalLM
    and AutoTokenizer for real GPU/CPU model execution.
    """

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        super().__init__(config=config)
        self._model = None
        self._tokenizer = None
        self._torch = None
        self._transformers = None
        self._device = "cpu"

    def _resolve_device(self, requested_device: str) -> str:
        """Resolve requested device against available hardware."""
        import torch  # type: ignore
        req = requested_device.lower()
        if req == "cuda" or (req == "auto" and torch.cuda.is_available()):
            return "cuda" if torch.cuda.is_available() else "cpu"
        if req == "mps" or (req == "auto" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
            return "mps"
        return "cpu"

    def _resolve_dtype(self, precision: str) -> Any:
        """Resolve PyTorch dtype from precision string."""
        import torch  # type: ignore
        prec = precision.lower()
        if prec in ("float16", "fp16"):
            return torch.float16
        if prec in ("bfloat16", "bf16"):
            return torch.bfloat16
        return torch.float32

    def load(self, config: Optional[ModelConfig] = None) -> bool:
        """Load model and tokenizer using transformers."""
        if config:
            self.config = config

        try:
            import torch  # type: ignore
            import transformers  # type: ignore
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

            self._torch = torch
            self._transformers = transformers
        except ImportError as e:
            raise ImportError(
                f"HuggingFaceEngine requires 'torch' and 'transformers'. Missing dependency: {e}"
            ) from e

        model_ref = self.config.model_path or self.config.model_id
        tokenizer_ref = self.config.tokenizer_path or model_ref

        self._device = self._resolve_device(self.config.device)
        dtype = self._resolve_dtype(self.config.precision)

        self._tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_ref,
            trust_remote_code=self.config.trust_remote_code,
            **self.config.extra_kwargs,
        )

        if self._tokenizer.pad_token_id is None:
            self._tokenizer.pad_token_id = self._tokenizer.eos_token_id or 0

        self._model = AutoModelForCausalLM.from_pretrained(
            model_ref,
            torch_dtype=dtype,
            trust_remote_code=self.config.trust_remote_code,
            **self.config.extra_kwargs,
        )
        self._model.to(self._device)
        self._model.eval()

        self._is_loaded = True
        return True

    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Execute text generation with PyTorch model."""
        if not self._is_loaded or self._model is None or self._tokenizer is None:
            self.load()

        start_time = time.perf_counter()
        gen_config = config or GenerationConfig()
        if kwargs:
            gen_config = GenerationConfig(**{**gen_config.model_dump(), **kwargs})

        inputs = self._tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(self._device)
        attention_mask = inputs.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(self._device)

        prompt_len = input_ids.shape[1]

        generate_kwargs: Dict[str, Any] = {
            "input_ids": input_ids,
            "max_new_tokens": gen_config.max_new_tokens,
            "do_sample": gen_config.do_sample,
            "temperature": gen_config.temperature if gen_config.do_sample else 1.0,
            "top_p": gen_config.top_p if gen_config.do_sample else 1.0,
            "top_k": gen_config.top_k if gen_config.top_k > 0 else None,
            "repetition_penalty": gen_config.repetition_penalty,
            "pad_token_id": gen_config.pad_token_id or self._tokenizer.pad_token_id,
            "eos_token_id": gen_config.eos_token_id or self._tokenizer.eos_token_id,
        }
        if attention_mask is not None:
            generate_kwargs["attention_mask"] = attention_mask

        # Filter out None values
        generate_kwargs = {k: v for k, v in generate_kwargs.items() if v is not None}

        with self._torch.no_grad():
            output_ids = self._model.generate(**generate_kwargs)

        generated_slice = output_ids[0][prompt_len:]
        tokens_list = generated_slice.cpu().tolist()
        generated_text = self._tokenizer.decode(tokens_list, skip_special_tokens=True)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        finish_reason = "length"
        if tokens_list and tokens_list[-1] == self._tokenizer.eos_token_id:
            finish_reason = "eos"

        return GenerationResult(
            text=generated_text,
            tokens_generated=len(tokens_list),
            prompt_tokens=prompt_len,
            finish_reason=finish_reason,
            duration_ms=duration_ms,
            model_id=self.model_id,
            tokens=tokens_list,
            metadata={"backend": "transformers", "device": self._device},
        )

    def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """Stream generation output token by token."""
        result = self.generate(prompt, config=config, **kwargs)
        tokens = result.tokens or []
        for i, tok in enumerate(tokens):
            is_last = i == len(tokens) - 1
            chunk_str = self._tokenizer.decode([tok], skip_special_tokens=False)
            yield StreamChunk(
                text=chunk_str,
                token_id=tok,
                is_finished=is_last,
                finish_reason=result.finish_reason if is_last else None,
            )

    def tokenize(self, text: str) -> List[int]:
        if not self._is_loaded or self._tokenizer is None:
            self.load()
        return self._tokenizer.encode(text, add_special_tokens=False)

    def decode(self, tokens: List[int]) -> str:
        if not self._is_loaded or self._tokenizer is None:
            self.load()
        return self._tokenizer.decode(tokens, skip_special_tokens=False)

    def unload(self) -> None:
        """Clear model weights and GPU allocations."""
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        if self._torch is not None and self._torch.cuda.is_available():
            self._torch.cuda.empty_cache()
        self._is_loaded = False

    def model_info(self) -> ModelInfo:
        param_count = 0
        if self._model is not None:
            param_count = sum(p.numel() for p in self._model.parameters())
        vocab_sz = len(self._tokenizer) if self._tokenizer is not None else 0

        return ModelInfo(
            model_id=self.model_id,
            model_type="causal_lm",
            backend="transformers",
            device=self._device,
            precision=self.config.precision,
            parameter_count=param_count,
            vocab_size=vocab_sz,
            max_context_length=self.config.max_context_length,
            is_loaded=self._is_loaded,
        )
