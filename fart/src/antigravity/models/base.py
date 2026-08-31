"""Abstract base class interface for local model inference engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Union

from .models import (
    ChatMessage,
    GenerationConfig,
    GenerationResult,
    ModelConfig,
    ModelInfo,
    StreamChunk,
)


class BaseModelEngine(ABC):
    """
    Abstract interface for all local model inference engines.
    Ensures a uniform lifecycle and generation contract across all backends.
    """

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        self.config = config or ModelConfig(model_id="default")
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Whether model weights and assets are loaded in memory."""
        return self._is_loaded

    @property
    def model_id(self) -> str:
        """The identifier of the underlying model."""
        return self.config.model_id

    @abstractmethod
    def load(self, config: Optional[ModelConfig] = None) -> bool:
        """
        Load model weights, tokenizer, and allocate execution resources.
        
        Args:
            config: Optional override configuration.
            
        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        pass

    @abstractmethod
    def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None, **kwargs: Any
    ) -> GenerationResult:
        """
        Perform autoregressive text generation for a prompt.
        
        Args:
            prompt: Input text prompt.
            config: Optional generation configuration.
            **kwargs: Extra parameters overriding GenerationConfig.
            
        Returns:
            GenerationResult: Output text, token counts, and latency.
        """
        pass

    def generate_stream(
        self, prompt: str, config: Optional[GenerationConfig] = None, **kwargs: Any
    ) -> Iterator[StreamChunk]:
        """
        Stream generated token chunks incrementally.
        Default implementation yields the full generation result as a chunk.
        """
        result = self.generate(prompt, config=config, **kwargs)
        tokens = result.tokens or self.tokenize(result.text)
        if tokens:
            for i, tok in enumerate(tokens):
                is_last = i == len(tokens) - 1
                chunk_text = self.decode([tok])
                yield StreamChunk(
                    text=chunk_text,
                    token_id=tok,
                    is_finished=is_last,
                    finish_reason=result.finish_reason if is_last else None,
                )
        else:
            yield StreamChunk(
                text=result.text,
                token_id=0,
                is_finished=True,
                finish_reason=result.finish_reason,
            )

    def chat(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Format messages using chat templating and generate a response.
        
        Args:
            messages: List of ChatMessage objects or dicts with 'role' and 'content'.
            config: Optional generation configuration.
            **kwargs: Extra parameters.
            
        Returns:
            GenerationResult: The assistant response.
        """
        formatted_prompt = self.format_chat_prompt(messages)
        return self.generate(formatted_prompt, config=config, **kwargs)

    def chat_stream(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        config: Optional[GenerationConfig] = None,
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """
        Stream response for a multi-turn chat.
        """
        formatted_prompt = self.format_chat_prompt(messages)
        yield from self.generate_stream(formatted_prompt, config=config, **kwargs)

    def format_chat_prompt(
        self, messages: List[Union[ChatMessage, Dict[str, str]]]
    ) -> str:
        """
        Format conversation turns into a model prompt.
        Default fallback uses a generic ChatML format.
        """
        lines = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = msg.role
                content = msg.content
            lines.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        lines.append("<|im_start|>assistant\n")
        return "\n".join(lines)

    @abstractmethod
    def tokenize(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        pass

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """Decode token IDs back to string."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Release weights and free memory allocations."""
        pass

    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Retrieve metadata describing the model engine."""
        pass
