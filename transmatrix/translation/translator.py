"""
Motor de traducción usando modelos de HuggingFace.
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field
import re


@dataclass
class TranslationConfig:
    """Configuración para el traductor."""
    source_lang: str
    target_lang: str
    max_length: int = 512
    batch_size: int = 8
    preserve_patterns: list[str] = field(default_factory=lambda: [
        r'\d+[.,]\d+',
        r'\d+',
        r'm²|m2|km|cm|mm',
        r'€|\$|£',
        r'[A-Z]{2,}',
        r'\b[A-Z]\d+\b',
    ])


class Translator(ABC):
    """Clase base abstracta para traductores."""

    @abstractmethod
    def translate(self, text: str) -> str:
        pass

    @abstractmethod
    def translate_batch(self, texts: list[str]) -> list[str]:
        pass


class NLLBTranslator(Translator):
    """Traductor usando NLLB-200 de Meta."""

    LANG_MAP = {
        "es": "spa_Latn",
        "en": "eng_Latn",
        "fr": "fra_Latn",
        "de": "deu_Latn",
        "it": "ita_Latn",
        "pt": "por_Latn",
        "zh": "zho_Hans",
        "ar": "arb_Arab",
        "ru": "rus_Cyrl",
        "ja": "jpn_Jpan",
        "ko": "kor_Hang",
    }

    def __init__(
        self,
        config: TranslationConfig,
        model_name: str = "facebook/nllb-200-distilled-600M",
        device: Optional[str] = None,
    ):
        self.config = config
        self.model_name = model_name
        self.src_lang = self._get_nllb_code(config.source_lang)
        self.tgt_lang = self._get_nllb_code(config.target_lang)
        self._model = None
        self._tokenizer = None
        self._device = device
        self._preserve_patterns = [
            re.compile(p) for p in config.preserve_patterns
        ]

    def _get_nllb_code(self, lang: str) -> str:
        lang = lang.lower().strip()
        if lang in self.LANG_MAP:
            return self.LANG_MAP[lang]
        if "_" in lang:
            return lang
        raise ValueError(f"Código de idioma no reconocido: {lang}")

    def _load_model(self):
        if self._model is not None:
            return

        print(f"Cargando modelo {self.model_name}...")

        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        import torch

        if self._device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Usando dispositivo: {self._device}")

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            src_lang=self.src_lang,
        )

        self._model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
        ).to(self._device)

        print("Modelo cargado.")

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return text
        results = self.translate_batch([text])
        return results[0] if results else text

    def translate_batch(self, texts: list[str]) -> list[str]:
        self._load_model()

        if not texts:
            return []

        non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]

        if not non_empty:
            return texts

        protected = []
        texts_to_translate = []
        for _, text in non_empty:
            prot, clean = self._protect_patterns(text)
            protected.append(prot)
            texts_to_translate.append(clean)

        translated = []
        for i in range(0, len(texts_to_translate), self.config.batch_size):
            batch = texts_to_translate[i:i + self.config.batch_size]
            batch_translated = self._translate_batch_internal(batch)
            translated.extend(batch_translated)

        restored = []
        for trans, prot in zip(translated, protected):
            restored.append(self._restore_patterns(trans, prot))

        results = list(texts)
        for (orig_idx, _), trans in zip(non_empty, restored):
            results[orig_idx] = trans

        return results

    def _translate_batch_internal(self, texts: list[str]) -> list[str]:
        import torch

        inputs = self._tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.config.max_length,
        ).to(self._device)

        with torch.no_grad():
            generated = self._model.generate(
                **inputs,
                forced_bos_token_id=self._tokenizer.convert_tokens_to_ids(self.tgt_lang),
                max_length=self.config.max_length,
            )

        translated = self._tokenizer.batch_decode(
            generated,
            skip_special_tokens=True,
        )

        return translated

    def _protect_patterns(self, text: str) -> tuple[dict[str, str], str]:
        protected = {}
        clean = text

        for i, pattern in enumerate(self._preserve_patterns):
            for j, match in enumerate(pattern.finditer(text)):
                placeholder = f"__PROT_{i}_{j}__"
                protected[placeholder] = match.group()
                clean = clean.replace(match.group(), placeholder, 1)

        return protected, clean

    def _restore_patterns(self, text: str, protected: dict[str, str]) -> str:
        for placeholder, original in protected.items():
            text = text.replace(placeholder, original)
        return text


class DummyTranslator(Translator):
    """Traductor de prueba que no traduce realmente."""

    def __init__(self, prefix: str = "[TRANSLATED] "):
        self.prefix = prefix

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return text
        return f"{self.prefix}{text}"

    def translate_batch(self, texts: list[str]) -> list[str]:
        return [self.translate(t) for t in texts]