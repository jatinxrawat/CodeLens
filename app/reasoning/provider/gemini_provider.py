"""Gemini LLM Provider using the official Google GenAI SDK."""

import os
import re
import json
from typing import List, Dict, Any, Optional, Iterator
import numpy as np
from app.config import settings
from app.reasoning.provider.base import LLMProvider
from app.services.cache_service import cache_service
from app.utils.logger import logger


class GeminiProvider(LLMProvider):
    """Google Gemini LLM & Embedding provider using official Google GenAI SDK."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self._client = None
        if self._api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI client: {e}")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _get_client(self):
        if not self._client:
            self._api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
            if not self._api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your environment, or switch to 'Local' mode in settings."
                )
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _resolve_model(self, model_tier: str) -> str:
        if model_tier == "pro":
            return settings.GEMINI_PRO_MODEL
        return settings.GEMINI_FLASH_MODEL

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> str:
        client = self._get_client()
        model_name = self._resolve_model(model_tier)

        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_prompt:
            config.system_instruction = system_prompt

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini generate_content error: {e}")
            raise

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Iterator[str]:
        client = self._get_client()
        model_name = self._resolve_model(model_tier)

        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_prompt:
            config.system_instruction = system_prompt

        try:
            stream_resp = client.models.generate_content_stream(
                model=model_name,
                contents=prompt,
                config=config,
            )
            for chunk in stream_resp:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 768), dtype=np.float32)

        # 1. Check persistent SQLite cache first
        cached_dict, missing_indices = cache_service.get_cached_embeddings(texts)
        if not missing_indices:
            # All found in cache!
            ordered = [cached_dict[i] for i in range(len(texts))]
            return np.array(ordered, dtype=np.float32)

        client = self._get_client()
        missing_texts = [texts[i] for i in missing_indices]
        batch_size = 100
        newly_computed: List[np.ndarray] = []

        try:
            for start_idx in range(0, len(missing_texts), batch_size):
                batch = missing_texts[start_idx : start_idx + batch_size]
                response = client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=batch,
                )
                for item in response.embeddings:
                    vec = np.array(item.values, dtype=np.float32)
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm
                    newly_computed.append(vec)

            # Save newly computed embeddings to cache
            cache_service.set_cached_embeddings(missing_texts, np.array(newly_computed, dtype=np.float32))

            for m_idx, vec in zip(missing_indices, newly_computed):
                cached_dict[m_idx] = vec

            ordered = [cached_dict[i] for i in range(len(texts))]
            return np.array(ordered, dtype=np.float32)

        except Exception as e:
            logger.error(f"Gemini embed_content error: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        schema: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        **kwargs,
    ) -> Dict[str, Any]:
        client = self._get_client()
        model_name = self._resolve_model(model_tier)

        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        )
        if system_prompt:
            config.system_instruction = system_prompt
        if schema:
            config.response_schema = schema

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            raw = response.text or "{}"
            # Clean possible markdown wrap
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned.strip())
            return json.loads(cleaned)
        except json.JSONDecodeError as jde:
            logger.warning(f"Gemini returned non-JSON text: {jde}, trying cleanup")
            json_match = re.search(r"\{.*\}", response.text or "", re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise
        except Exception as e:
            logger.error(f"Gemini generate_json error: {e}")
            raise
