"""
LLM abstraction for cases the deterministic templates (templates.py)
don't cover. Kept separate from the template engine on purpose: the
knowledge graph + templates are the source of truth for *what* changed
and *how* to fix known cases; the LLM here only ever explains or
handles the long tail, and its output should still be diffed and
reviewed like any other patch — never trusted blindly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from settings import Settings


class LLMProvider(ABC):
    @abstractmethod
    async def generate_patch(self, *, file_content: str, migration_hint: str, api_name: str) -> str:
        """Return the full new file content. Implementations should be
        conservative — change only what's needed for the migration hint."""


class TemplateOnlyProvider(LLMProvider):
    """The default provider. Deliberately refuses anything outside the
    template engine rather than guessing — this is what makes the whole
    pipeline runnable end-to-end with zero API keys and zero network calls,
    for every API this project has actually seeded a template for.
    """
    async def generate_patch(self, *, file_content: str, migration_hint: str, api_name: str) -> str:
        raise NotImplementedError(
            f"No template for '{api_name}' and LLM_PROVIDER=template (no LLM configured). "
            "Set LLM_PROVIDER=openai and OPENAI_API_KEY to handle this case automatically, "
            "or migrate it manually."
        )


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, cheap_model: str, strong_model: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.strong_model = strong_model  # code transformation always uses the stronger model

    async def generate_patch(self, *, file_content: str, migration_hint: str, api_name: str) -> str:
        prompt = (
            f"You are migrating a code file because of this change: {api_name}.\n"
            f"Instruction: {migration_hint}\n\n"
            "Return ONLY the complete, corrected file content. No explanation, no markdown fences.\n\n"
            f"--- ORIGINAL FILE ---\n{file_content}"
        )
        resp = await self.client.chat.completions.create(
            model=self.strong_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp.choices[0].message.content


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai requires OPENAI_API_KEY")
        return OpenAIProvider(settings.openai_api_key, settings.cheap_model, settings.strong_model)
    return TemplateOnlyProvider()
