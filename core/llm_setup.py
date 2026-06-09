"""Gemini LLM and Embedding model initialisation.

Sets the LlamaIndex global ``Settings`` so that every index and query engine
automatically uses Gemini 1.5 Flash for generation and ``embedding-001``
for vector embeddings.  No key is ever hardcoded — everything comes from
``os.getenv``.
"""

import os
import logging
import time
import asyncio
from typing import Optional, List, Any

from llama_index.core import Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from tenacity import retry, stop_after_attempt, wait_exponential

from core.resilience import resilient_call

logger = logging.getLogger("inayat")

_MODEL_NAME = "gemini-flash-lite-latest"
_EMBED_MODEL = "gemini-embedding-001"


class ResilientGoogleGenAIEmbedding(GoogleGenAIEmbedding):
    """Subclass of GoogleGenAIEmbedding with exponential backoff retries and rate-limiting."""

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
    """Subclass of GoogleGenAI with exponential backoff retries and rate-limiting."""

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


def _get_api_key() -> str:
    """Return the Gemini API key or raise."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is missing from the environment.")
    return key


def get_gemini_llm(temperature: float = 0.25) -> ResilientGoogleGenAI:
    """Create a Gemini LLM instance.

    Args:
        temperature: Sampling temperature (0 = deterministic, 1 = creative).

    Returns:
        A ``ResilientGoogleGenAI`` LLM ready for use.
    """
    return ResilientGoogleGenAI(
        model=_MODEL_NAME,
        api_key=_get_api_key(),
        temperature=temperature,
    )


def get_gemini_embedding() -> ResilientGoogleGenAIEmbedding:
    """Create a Gemini embedding model instance.

    Returns:
        A ``ResilientGoogleGenAIEmbedding`` configured with the project embedding model.
    """
    return ResilientGoogleGenAIEmbedding(
        model_name=_EMBED_MODEL,
        api_key=_get_api_key(),
    )


def configure_llama_settings() -> None:
    """Set the LlamaIndex global ``Settings`` to use Gemini.

    Call once at application start.  Subsequent LlamaIndex operations
    (indexing, querying) will automatically pick up these models.
    """
    Settings.llm = get_gemini_llm()
    Settings.embed_model = get_gemini_embedding()
    Settings.chunk_size = 512
    Settings.chunk_overlap = 64
    logger.info(
        "LlamaIndex Settings configured → LLM=%s  Embed=%s",
        _MODEL_NAME,
        _EMBED_MODEL,
    )


@resilient_call(max_attempts=2, min_wait=1, max_wait=5)
def ping_gemini() -> bool:
    """Send a tiny prompt to Gemini to verify the API key works.

    Returns:
        True on success.

    Raises:
        Exception: Propagated on failure (handled by resilient_call retries).
    """
    llm = get_gemini_llm()
    resp = llm.complete("Say OK")
    logger.debug("Gemini ping response: %s", str(resp)[:80])
    return True
