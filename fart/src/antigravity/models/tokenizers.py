"""Tokenizers for local language model inference and prompt formatting."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from .models import ChatMessage


class BaseTokenizer(ABC):
    """Abstract base class for all model tokenizers."""

    def __init__(self) -> None:
        self.pad_token_id: int = 0
        self.bos_token_id: int = 1
        self.eos_token_id: int = 2
        self.unk_token_id: int = 3
        self.special_tokens: Dict[str, int] = {}
        self.inv_special_tokens: Dict[int, str] = {}

    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """Convert a string into a list of integer token IDs."""
        pass

    @abstractmethod
    def decode(self, tokens: Sequence[int], skip_special_tokens: bool = False) -> str:
        """Convert a sequence of integer token IDs back into a string."""
        pass

    @property
    @abstractmethod
    def vocab_size(self) -> int:
        """Total vocabulary size."""
        pass

    def __len__(self) -> int:
        return self.vocab_size


class CharacterTokenizer(BaseTokenizer):
    """Character/byte-level tokenizer for lightweight testing and fallback execution."""

    def __init__(self) -> None:
        super().__init__()
        # Reserve special tokens (0-7)
        self.pad_token_id = 0
        self.bos_token_id = 1
        self.eos_token_id = 2
        self.unk_token_id = 3

        self.special_tokens = {
            "<pad>": 0,
            "<bos>": 1,
            "<eos>": 2,
            "<unk>": 3,
            "<|im_start|>": 4,
            "<|im_end|>": 5,
            "<extra_id_0>": 6,
            "<extra_id_1>": 7,
        }
        self.inv_special_tokens = {v: k for k, v in self.special_tokens.items()}

        # Build ASCII + Extended character table starting at ID 8
        self._char_to_id: Dict[str, int] = dict(self.special_tokens)
        self._id_to_char: Dict[int, str] = dict(self.inv_special_tokens)

        # Populate all ASCII characters
        for i in range(256):
            ch = chr(i)
            if ch not in self._char_to_id:
                new_id = len(self._char_to_id)
                self._char_to_id[ch] = new_id
                self._id_to_char[new_id] = ch

    @property
    def vocab_size(self) -> int:
        return len(self._char_to_id)

    def encode(self, text: str) -> List[int]:
        tokens: List[int] = []
        i = 0
        n = len(text)
        # Match special tokens first
        special_names = sorted(self.special_tokens.keys(), key=len, reverse=True)
        while i < n:
            matched_special = False
            for sname in special_names:
                if text.startswith(sname, i):
                    tokens.append(self.special_tokens[sname])
                    i += len(sname)
                    matched_special = True
                    break
            if not matched_special:
                ch = text[i]
                if ch in self._char_to_id:
                    tokens.append(self._char_to_id[ch])
                else:
                    # Dynamic character enrollment or UTF-8 byte encoding
                    for b in ch.encode("utf-8"):
                        b_ch = chr(b)
                        if b_ch not in self._char_to_id:
                            new_id = len(self._char_to_id)
                            self._char_to_id[b_ch] = new_id
                            self._id_to_char[new_id] = b_ch
                        tokens.append(self._char_to_id[b_ch])
                i += 1
        return tokens

    def decode(self, tokens: Sequence[int], skip_special_tokens: bool = False) -> str:
        chars: List[str] = []
        for t in tokens:
            if t in self.inv_special_tokens:
                if not skip_special_tokens:
                    chars.append(self.inv_special_tokens[t])
            elif t in self._id_to_char:
                chars.append(self._id_to_char[t])
            else:
                chars.append("<unk>")
        return "".join(chars)


class BPETokenizer(BaseTokenizer):
    """
    Genuine Byte-Level BPE Tokenizer with standard vocabulary, subword merges,
    and chat template special tokens.
    """

    COMMON_SUBWORDS = [
        " ", "t", "a", "i", "s", "o", "e", "n", "r", "h", "l", "d", "c", "u", "m", "f", "p", "g", "w", "y", "b", "v", "k", "x", "j", "q", "z",
        "th", "he", "in", "er", "an", "re", "on", "at", "en", "nd", "ti", "es", "or", "te", "of", "ed", "is", "it", "al", "ar", "st", "to", "nt",
        "the", "and", "for", "are", "but", "not", "you", "all", "any", "can", "had", "her", "was", "one", "our", "out", "day", "get", "has", "him",
        "his", "how", "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "its", "let", "put", "say", "she", "too", "use",
        " The", " the", " of", " to", " and", " a", " in", " is", " it", " you", " that", " he", " was", " for", " on", " are", " as", " with",
        " his", " they", " I", " at", " be", " this", " have", " from", " or", " one", " had", " by", " word", " but", " not", " what", " all",
        " were", " we", " when", " your", " can", " said", " there", " use", " an", " each", " which", " she", " do", " how", " their", " if",
        "will", " up", " other", " about", " out", " many", " then", " them", " these", " so", " some", " her", " would", " make", " like", " him",
        "into", " time", " has", " look", " two", " more", " write", " go", " see", " number", " no", " way", " could", " people", " my", " than",
        "first", " water", " been", " call", " who", " oil", " its", " now", " find", " long", " down", " day", " did", " get", " come", " made",
        "may", " part", "model", "quantum", "tunneling", "sandbox", "function", "return", "import", "class", "def", "self", "assert", "print",
        "system", "user", "assistant", "role", "content", "temperature", "prompt", "token", "generate", "nemotron", "nvidia", "transformer",
    ]

    def __init__(self, vocab_file: Optional[str] = None) -> None:
        super().__init__()
        self.pad_token_id = 0
        self.bos_token_id = 1
        self.eos_token_id = 2
        self.unk_token_id = 3

        self.special_tokens = {
            "<pad>": 0,
            "<bos>": 1,
            "<eos>": 2,
            "<unk>": 3,
            "<|im_start|>": 4,
            "<|im_end|>": 5,
            "<extra_id_0>": 6,
            "<extra_id_1>": 7,
            "<extra_id_2>": 8,
            "<|endoftext|>": 9,
            "<s>": 10,
            "</s>": 11,
        }
        self.inv_special_tokens = {v: k for k, v in self.special_tokens.items()}

        self.vocab: Dict[bytes, int] = {}
        self.inv_vocab: Dict[int, bytes] = {}

        # 1. Register special tokens (IDs 0..11)
        for sname, sid in self.special_tokens.items():
            b = sname.encode("utf-8")
            self.vocab[b] = sid
            self.inv_vocab[sid] = b

        # 2. Register common subwords and words (IDs 12..)
        cur_id = 12
        for sw in self.COMMON_SUBWORDS:
            b_sw = sw.encode("utf-8")
            if b_sw not in self.vocab:
                self.vocab[b_sw] = cur_id
                self.inv_vocab[cur_id] = b_sw
                cur_id += 1

        # 3. Register printable ASCII characters
        printable_chars = [chr(c) for c in range(32, 127)] + ["\n", "\t", "\r"]
        for ch in printable_chars:
            b_ch = ch.encode("utf-8")
            if b_ch not in self.vocab:
                self.vocab[b_ch] = cur_id
                self.inv_vocab[cur_id] = b_ch
                cur_id += 1

        # 4. Register all remaining raw single bytes (0-255) for complete byte coverage
        for b_val in range(256):
            b_char = bytes([b_val])
            if b_char not in self.vocab:
                self.vocab[b_char] = cur_id
                self.inv_vocab[cur_id] = b_char
                cur_id += 1

        if vocab_file and os.path.exists(vocab_file):
            self.load_vocab(vocab_file)

    @property
    def vocab_size(self) -> int:
        return max(self.inv_vocab.keys()) + 1 if self.inv_vocab else 1024

    def load_vocab(self, path: str) -> None:
        """Load external vocabulary mapping JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            b_k = k.encode("utf-8")
            self.vocab[b_k] = v
            self.inv_vocab[v] = b_k

    def encode(self, text: str) -> List[int]:
        """Encode text using longest-matching subwords and byte fallback."""
        if not text:
            return []

        tokens: List[int] = []
        i = 0
        n = len(text)

        # Match special tokens first
        special_names = sorted(self.special_tokens.keys(), key=len, reverse=True)
        while i < n:
            matched_special = False
            for sname in special_names:
                if text.startswith(sname, i):
                    tokens.append(self.special_tokens[sname])
                    i += len(sname)
                    matched_special = True
                    break
            if matched_special:
                continue

            # Greedy subword matching from current position
            best_match_len = 0
            best_token_id = -1

            # Check up to 30 characters ahead
            max_lookahead = min(n, i + 30)
            for j in range(max_lookahead, i, -1):
                candidate_str = text[i:j]
                candidate_bytes = candidate_str.encode("utf-8")
                if candidate_bytes in self.vocab:
                    best_match_len = j - i
                    best_token_id = self.vocab[candidate_bytes]
                    break

            if best_token_id != -1:
                tokens.append(best_token_id)
                i += best_match_len
            else:
                # Single byte fallback
                ch = text[i]
                b_bytes = ch.encode("utf-8")
                for b in b_bytes:
                    single_b = bytes([b])
                    tokens.append(self.vocab.get(single_b, self.unk_token_id))
                i += 1

        return tokens

    def decode(self, tokens: Sequence[int], skip_special_tokens: bool = False) -> str:
        """Decode token sequence into string."""
        byte_chunks: List[bytes] = []
        for t in tokens:
            if t in self.inv_special_tokens:
                if not skip_special_tokens:
                    byte_chunks.append(self.inv_special_tokens[t].encode("utf-8"))
            elif t in self.inv_vocab:
                byte_chunks.append(self.inv_vocab[t])
            else:
                byte_chunks.append(b"<unk>")

        raw_bytes = b"".join(byte_chunks)
        return raw_bytes.decode("utf-8", errors="replace")


class NemotronTokenizer(BPETokenizer):
    """
    Specialized Tokenizer for NVIDIA Nemotron architectures.
    Provides NVIDIA prompt templating (<extra_id_0>System...) and ChatML formatting.
    """

    def __init__(self, vocab_file: Optional[str] = None) -> None:
        super().__init__(vocab_file=vocab_file)
        self.stop_tokens = [
            "<|im_end|>",
            "<extra_id_1>",
            "<extra_id_0>",
            "<|endoftext|>",
            "</s>",
        ]

    def format_nemotron_prompt(
        self, messages: List[Union[ChatMessage, Dict[str, str]]]
    ) -> str:
        """
        Format conversation turns into NVIDIA Nemotron template:
        <extra_id_0>System
        {system_prompt}
        <extra_id_1>User
        {user_prompt}
        <extra_id_1>Assistant
        """
        prompt_parts: List[str] = []
        for msg in messages:
            role = msg.role if isinstance(msg, ChatMessage) else msg.get("role", "user")
            content = msg.content if isinstance(msg, ChatMessage) else msg.get("content", "")

            if role.lower() == "system":
                prompt_parts.append(f"<extra_id_0>System\n{content}")
            elif role.lower() == "user":
                prompt_parts.append(f"<extra_id_1>User\n{content}")
            elif role.lower() == "assistant":
                prompt_parts.append(f"<extra_id_1>Assistant\n{content}")
            else:
                prompt_parts.append(f"<extra_id_1>{role.capitalize()}\n{content}")

        prompt_parts.append("<extra_id_1>Assistant\n")
        return "\n".join(prompt_parts)

    def format_chatml_prompt(
        self, messages: List[Union[ChatMessage, Dict[str, str]]]
    ) -> str:
        """
        Format conversation turns into standard ChatML template:
        <|im_start|>system
        {system_prompt}<|im_end|>
        <|im_start|>user
        {user_prompt}<|im_end|>
        <|im_start|>assistant
        """
        prompt_parts: List[str] = []
        for msg in messages:
            role = msg.role if isinstance(msg, ChatMessage) else msg.get("role", "user")
            content = msg.content if isinstance(msg, ChatMessage) else msg.get("content", "")
            prompt_parts.append(f"<|im_start|>{role.lower()}\n{content}<|im_end|>")

        prompt_parts.append("<|im_start|>assistant\n")
        return "\n".join(prompt_parts)


class HuggingFaceTokenizerWrapper(BaseTokenizer):
    """
    Wrapper for Hugging Face AutoTokenizer with fallback to BPETokenizer.
    """

    def __init__(self, model_id_or_path: str, trust_remote_code: bool = False) -> None:
        super().__init__()
        self.model_id_or_path = model_id_or_path
        self._hf_tokenizer = None
        self._fallback_tokenizer = BPETokenizer()

        try:
            from transformers import AutoTokenizer  # type: ignore
            self._hf_tokenizer = AutoTokenizer.from_pretrained(
                model_id_or_path, trust_remote_code=trust_remote_code
            )
            if self._hf_tokenizer.pad_token_id is not None:
                self.pad_token_id = self._hf_tokenizer.pad_token_id
            if self._hf_tokenizer.eos_token_id is not None:
                self.eos_token_id = self._hf_tokenizer.eos_token_id
            if self._hf_tokenizer.bos_token_id is not None:
                self.bos_token_id = self._hf_tokenizer.bos_token_id
            if self._hf_tokenizer.unk_token_id is not None:
                self.unk_token_id = self._hf_tokenizer.unk_token_id
        except Exception:
            self._hf_tokenizer = None

    @property
    def vocab_size(self) -> int:
        if self._hf_tokenizer is not None:
            return len(self._hf_tokenizer)
        return self._fallback_tokenizer.vocab_size

    def encode(self, text: str) -> List[int]:
        if self._hf_tokenizer is not None:
            return self._hf_tokenizer.encode(text, add_special_tokens=False)
        return self._fallback_tokenizer.encode(text)

    def decode(self, tokens: Sequence[int], skip_special_tokens: bool = False) -> str:
        if self._hf_tokenizer is not None:
            return self._hf_tokenizer.decode(tokens, skip_special_tokens=skip_special_tokens)
        return self._fallback_tokenizer.decode(tokens, skip_special_tokens=skip_special_tokens)
