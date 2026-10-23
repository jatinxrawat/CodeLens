"""Local 100% Offline LLM Provider (SentenceTransformer + LocalCodeReasoner)."""

import json
import re
from typing import List, Dict, Any, Optional, Iterator
import numpy as np
from app.config import settings
from app.reasoning.provider.base import LLMProvider
from app.reasoning.local_llm import LocalCodeReasoner
from app.embeddings.embedding_model import SentenceTransformerEmbeddingModel
from app.services.cache_service import cache_service
from app.utils.logger import logger


class LocalProvider(LLMProvider):
    """100% offline, local ML provider using SentenceTransformers and local reasoning engine."""

    def __init__(self):
        self._reasoner = LocalCodeReasoner()
        self._embedding_model = None

    @property
    def provider_name(self) -> str:
        return "local"

    def _get_embedding_model(self) -> SentenceTransformerEmbeddingModel:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformerEmbeddingModel(
                model_name=settings.EMBEDDING_MODEL_NAME,
                device=settings.EMBEDDING_DEVICE,
            )
        return self._embedding_model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> str:
        # Use local deterministic code reasoning engine
        return self._reasoner.synthesize_general_answer(prompt)

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Iterator[str]:
        full_text = self.generate(
            prompt,
            system_prompt=system_prompt,
            model_tier=model_tier,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        # Yield words in chunks to simulate streaming
        words = full_text.split(" ")
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            yield " ".join(words[i : i + chunk_size]) + " "

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        # Check cache
        cached_dict, missing_indices = cache_service.get_cached_embeddings(texts)
        if not missing_indices:
            ordered = [cached_dict[i] for i in range(len(texts))]
            return np.array(ordered, dtype=np.float32)

        model = self._get_embedding_model()
        missing_texts = [texts[i] for i in missing_indices]
        newly_computed = model.encode(
            missing_texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
        )

        cache_service.set_cached_embeddings(missing_texts, newly_computed)

        for m_idx, vec in zip(missing_indices, newly_computed):
            cached_dict[m_idx] = vec

        ordered = [cached_dict[i] for i in range(len(texts))]
        return np.array(ordered, dtype=np.float32)

    def generate_json(
        self,
        prompt: str,
        schema: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        **kwargs,
    ) -> Dict[str, Any]:
        """Provides heuristic JSON extraction for offline local mode."""
        prompt_lower = prompt.lower()
        # Default heuristic analysis for issue difficulty and skills
        difficulty = "medium"
        if any(w in prompt_lower for w in ["typo", "docs", "readme", "comment", "spelling", "formatting", "good first"]):
            difficulty = "easy"
        elif any(w in prompt_lower for w in ["memory leak", "deadlock", "architecture", "concurrency", "refactor core", "distributed"]):
            difficulty = "hard"

        skills = []
        for lang in ["Python", "TypeScript", "JavaScript", "Go", "Rust", "React", "Docker", "FastAPI", "CSS"]:
            if lang.lower() in prompt_lower:
                skills.append(lang)
        if not skills:
            skills = ["General Programming", "Git"]

        likely_files = re.findall(r"[\w\-\/\.]+\.(?:py|ts|tsx|js|jsx|go|rs|cpp|h|html|css|json|md)", prompt)
        likely_files = list(dict.fromkeys(likely_files))[:5]

        # Extract first 2 sentences for summary
        sentences = [s.strip() for s in prompt.split(".") if s.strip()]
        summary = ". ".join(sentences[:2]) + "." if sentences else "Open source contribution issue."

        return {
            "difficulty": difficulty,
            "skills": skills[:4],
            "likely_files": likely_files,
            "summary": summary,
        }
