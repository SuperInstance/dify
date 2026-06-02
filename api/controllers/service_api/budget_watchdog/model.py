"""
Models that Dify workflows commonly use, ordered by cost (descending).

Provides model identity, cost tiering, and automatic downgrade chains.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class ModelTier(Enum):
    """Broad cost tiers used for phase-based routing decisions."""

    PREMIUM = "premium"
    """Highest cost — use during normal phase."""

    STANDARD = "standard"
    """Mid cost."""

    BUDGET = "budget"
    """Lowest cost — use when budget is constrained."""


class ModelId(Enum):
    """Models that Dify workflows commonly use.

    Ordered by typical cost (descending). Custom models use the custom label.
    """

    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"
    LLAMA3_70B = "llama-3-70b"
    LLAMA3_8B = "llama-3-8b"

    def label(self) -> str:
        """Return a human-readable label."""
        return _LABELS[self]

    def tier(self) -> ModelTier:
        """Return the cost tier for this model."""
        return _TIERS[self]


_LABELS = {
    ModelId.GPT4O: "GPT-4o",
    ModelId.GPT4O_MINI: "GPT-4o-mini",
    ModelId.GPT35_TURBO: "GPT-3.5 Turbo",
    ModelId.CLAUDE_3_OPUS: "Claude 3 Opus",
    ModelId.CLAUDE_3_SONNET: "Claude 3 Sonnet",
    ModelId.CLAUDE_3_HAIKU: "Claude 3 Haiku",
    ModelId.GEMINI_PRO: "Gemini Pro",
    ModelId.GEMINI_FLASH: "Gemini Flash",
    ModelId.LLAMA3_70B: "Llama 3 70B",
    ModelId.LLAMA3_8B: "Llama 3 8B",
}

_TIERS = {
    ModelId.GPT4O: ModelTier.PREMIUM,
    ModelId.CLAUDE_3_OPUS: ModelTier.PREMIUM,
    ModelId.GEMINI_PRO: ModelTier.STANDARD,
    ModelId.GPT4O_MINI: ModelTier.STANDARD,
    ModelId.CLAUDE_3_SONNET: ModelTier.STANDARD,
    ModelId.LLAMA3_70B: ModelTier.STANDARD,
    ModelId.GEMINI_FLASH: ModelTier.BUDGET,
    ModelId.GPT35_TURBO: ModelTier.BUDGET,
    ModelId.CLAUDE_3_HAIKU: ModelTier.BUDGET,
    ModelId.LLAMA3_8B: ModelTier.BUDGET,
}

# Downgrade chain: expensive → cheaper
_DOWNGRADE_CHAIN: dict[ModelId, Optional[ModelId]] = {
    ModelId.GPT4O: ModelId.GPT4O_MINI,
    ModelId.GPT4O_MINI: ModelId.GPT35_TURBO,
    ModelId.GPT35_TURBO: None,
    ModelId.CLAUDE_3_OPUS: ModelId.CLAUDE_3_SONNET,
    ModelId.CLAUDE_3_SONNET: ModelId.CLAUDE_3_HAIKU,
    ModelId.CLAUDE_3_HAIKU: None,
    ModelId.GEMINI_PRO: ModelId.GEMINI_FLASH,
    ModelId.GEMINI_FLASH: None,
    ModelId.LLAMA3_70B: ModelId.LLAMA3_8B,
    ModelId.LLAMA3_8B: None,
}


def downgrade_model(model: ModelId) -> Optional[ModelId]:
    """Attempt to auto-downgrade a model one step.

    Returns None if no cheaper alternative exists.
    """
    return _DOWNGRADE_CHAIN.get(model)


def resolve_model_id(provider: str, model_name: str) -> ModelId:
    """Resolve a Dify provider/model pair to the nearest ModelId.

    Falls back to a generic mapping. Useful when the watchdog layer
    intercepts LLM calls with provider/model identity.
    """
    key = f"{provider}/{model_name}".lower()
    mapping = {
        "openai/gpt-4o": ModelId.GPT4O,
        "openai/gpt-4o-mini": ModelId.GPT4O_MINI,
        "openai/gpt-3.5-turbo": ModelId.GPT35_TURBO,
        "openai/gpt-3.5-turbo-16k": ModelId.GPT35_TURBO,
        "anthropic/claude-3-opus": ModelId.CLAUDE_3_OPUS,
        "anthropic/claude-3-sonnet": ModelId.CLAUDE_3_SONNET,
        "anthropic/claude-3-haiku": ModelId.CLAUDE_3_HAIKU,
        "google/gemini-pro": ModelId.GEMINI_PRO,
        "google/gemini-flash": ModelId.GEMINI_FLASH,
        "meta/llama-3-70b": ModelId.LLAMA3_70B,
        "meta/llama-3-8b": ModelId.LLAMA3_8B,
    }
    return mapping.get(key, ModelId.GPT4O_MINI)
