"""Gemini LLM and embedding model initialisation.

Configures LlamaIndex global ``Settings`` for generation and embeddings.
This module must not index documents or answer queries.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, List, Optional

from llama_index.core import Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from core.resilience import resilient_call
from core.settings import InayatSettings, get_settings

logger = logging.getLogger("inayat")


class ResilientGoogleGenAIEmbedding(GoogleGenAIEmbedding):
    """GoogleGenAIEmbedding with exponential backoff retries and rate-limiting."""

    def _get_text_embedding(self, text: str) -> List[float]:
        from tenacity import Retrying, stop_after_attempt, wait_exponential

        for attempt in Retrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=20),
            reraise=True,
        ):
            with attempt:
                time.sleep(0.2)
                return super()._get_text_embedding(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        from tenacity import Retrying, stop_after_attempt, wait_exponential

        for attempt in Retrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=20),
            reraise=True,
        ):
            with attempt:
                time.sleep(0.25)
                return super()._get_text_embeddings(texts)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=20),
            reraise=True,
        ):
            with attempt:
                await asyncio.sleep(0.2)
                return await super()._aget_text_embedding(text)

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=20),
            reraise=True,
        ):
            with attempt:
                await asyncio.sleep(0.25)
                return await super()._aget_text_embeddings(texts)


class ResilientGoogleGenAI(GoogleGenAI):
    """GoogleGenAI with exponential backoff retries and rate-limiting."""

    def complete(self, prompt: str, **kwargs: Any) -> Any:
        from tenacity import Retrying, stop_after_attempt, wait_exponential

        for attempt in Retrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=30),
            reraise=True,
        ):
            with attempt:
                time.sleep(0.25)
                return super().complete(prompt, **kwargs)

    async def acomplete(self, prompt: str, **kwargs: Any) -> Any:
        from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=30),
            reraise=True,
        ):
            with attempt:
                await asyncio.sleep(0.25)
                return await super().acomplete(prompt, **kwargs)

    def chat(self, messages: List[Any], **kwargs: Any) -> Any:
        from tenacity import Retrying, stop_after_attempt, wait_exponential

        for attempt in Retrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=30),
            reraise=True,
        ):
            with attempt:
                time.sleep(0.25)
                return super().chat(messages, **kwargs)

    async def achat(self, messages: List[Any], **kwargs: Any) -> Any:
        from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=2, min=2, max=30),
            reraise=True,
        ):
            with attempt:
                await asyncio.sleep(0.25)
                return await super().achat(messages, **kwargs)


def get_gemini_llm(
    temperature: float = 0.25,
    settings: Optional[InayatSettings] = None,
) -> ResilientGoogleGenAI:
    """Create a Gemini LLM instance from settings."""
    cfg = settings or get_settings()
    return ResilientGoogleGenAI(
        model=cfg.llm_model,
        api_key=cfg.gemini_api_key,
        temperature=temperature,
    )


def get_gemini_embedding(
    settings: Optional[InayatSettings] = None,
) -> ResilientGoogleGenAIEmbedding:
    """Create a Gemini embedding model instance from settings."""
    cfg = settings or get_settings()
    return ResilientGoogleGenAIEmbedding(
        model_name=cfg.embed_model,
        api_key=cfg.gemini_api_key,
    )


def configure_llama_settings(settings: Optional[InayatSettings] = None) -> None:
    """Set LlamaIndex global ``Settings`` from application configuration."""
    cfg = settings or get_settings()
    Settings.llm = get_gemini_llm(settings=cfg)
    Settings.embed_model = get_gemini_embedding(settings=cfg)
    Settings.chunk_size = cfg.chunk_size
    Settings.chunk_overlap = cfg.chunk_overlap
    logger.info(
        "LlamaIndex Settings configured → LLM=%s  Embed=%s  chunk=%s/%s",
        cfg.llm_model,
        cfg.embed_model,
        cfg.chunk_size,
        cfg.chunk_overlap,
    )


@resilient_call(max_attempts=2, min_wait=1, max_wait=5)
def ping_gemini() -> bool:
    """Send a tiny prompt to Gemini to verify the API key works."""
    cfg = get_settings()
    llm = GoogleGenAI(
        model=cfg.llm_model,
        api_key=cfg.gemini_api_key,
        temperature=0.25,
    )
    resp = llm.complete("Say OK")
    logger.debug("Gemini ping response: %s", str(resp)[:80])
    return True
