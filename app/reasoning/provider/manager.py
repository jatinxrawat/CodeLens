"""LLM Provider Manager and Registry."""

import os
from typing import Optional, Dict, Any
from app.config import settings
from app.reasoning.provider.base import LLMProvider
from app.reasoning.provider.gemini_provider import GeminiProvider
from app.reasoning.provider.local_provider import LocalProvider
from app.utils.logger import logger


class ProviderManager:
    """Manages active LLM provider (Gemini default, Local optional)."""

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        # Default configured provider from settings or env
        default_mode = settings.LLM_PROVIDER.lower()
        if default_mode == "gemini" and not (settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")):
            logger.info("GEMINI_API_KEY not found in environment; falling back to 'local' mode.")
            self._active_provider_name = "local"
        else:
            self._active_provider_name = default_mode if default_mode in ("gemini", "local") else "gemini"

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        target_name = (name or self._active_provider_name).lower()
        if target_name not in self._providers:
            if target_name == "gemini":
                self._providers["gemini"] = GeminiProvider()
            elif target_name == "local":
                self._providers["local"] = LocalProvider()
            else:
                logger.warning(f"Unknown provider '{target_name}', falling back to 'gemini'")
                self._providers["gemini"] = GeminiProvider()
                target_name = "gemini"
        return self._providers[target_name]

    def set_active_provider(self, name: str) -> LLMProvider:
        clean_name = name.lower()
        if clean_name not in ("gemini", "local"):
            raise ValueError(f"Invalid provider '{name}'. Must be 'gemini' or 'local'.")
        self._active_provider_name = clean_name
        return self.get_provider(clean_name)

    @property
    def active_provider_name(self) -> str:
        return self._active_provider_name

    def get_provider_status(self) -> Dict[str, Any]:
        has_gemini_key = bool(settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY"))
        return {
            "active_provider": self._active_provider_name,
            "gemini_available": has_gemini_key,
            "gemini_flash_model": settings.GEMINI_FLASH_MODEL,
            "gemini_pro_model": settings.GEMINI_PRO_MODEL,
            "gemini_embedding_model": settings.GEMINI_EMBEDDING_MODEL,
            "local_model": settings.LLM_MODEL,
            "local_embedding_model": settings.EMBEDDING_MODEL_NAME,
        }


provider_manager = ProviderManager()


def get_llm_provider(name: Optional[str] = None) -> LLMProvider:
    return provider_manager.get_provider(name)
