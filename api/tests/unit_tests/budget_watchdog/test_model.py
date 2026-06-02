"""Tests for model identification and downgrade chain."""

from controllers.service_api.budget_watchdog.model import (
    ModelId,
    ModelTier,
    downgrade_model,
    resolve_model_id,
)


class TestDowngradeChain:
    def test_gpt4o_chain(self):
        assert downgrade_model(ModelId.GPT4O) == ModelId.GPT4O_MINI
        assert downgrade_model(ModelId.GPT4O_MINI) == ModelId.GPT35_TURBO
        assert downgrade_model(ModelId.GPT35_TURBO) is None

    def test_claude_chain(self):
        assert downgrade_model(ModelId.CLAUDE_3_OPUS) == ModelId.CLAUDE_3_SONNET
        assert downgrade_model(ModelId.CLAUDE_3_SONNET) == ModelId.CLAUDE_3_HAIKU
        assert downgrade_model(ModelId.CLAUDE_3_HAIKU) is None

    def test_gemini_chain(self):
        assert downgrade_model(ModelId.GEMINI_PRO) == ModelId.GEMINI_FLASH
        assert downgrade_model(ModelId.GEMINI_FLASH) is None

    def test_llama_chain(self):
        assert downgrade_model(ModelId.LLAMA3_70B) == ModelId.LLAMA3_8B
        assert downgrade_model(ModelId.LLAMA3_8B) is None


class TestModelLabels:
    def test_labels(self):
        assert ModelId.GPT4O.label() == "GPT-4o"
        assert ModelId.GPT4O_MINI.label() == "GPT-4o-mini"
        assert ModelId.GPT35_TURBO.label() == "GPT-3.5 Turbo"


class TestModelTiers:
    def test_tiers(self):
        assert ModelId.GPT4O.tier() == ModelTier.PREMIUM
        assert ModelId.GPT4O_MINI.tier() == ModelTier.STANDARD
        assert ModelId.GPT35_TURBO.tier() == ModelTier.BUDGET


class TestResolveModelId:
    def test_openai_mapping(self):
        assert resolve_model_id("openai", "gpt-4o") == ModelId.GPT4O
        assert resolve_model_id("openai", "gpt-4o-mini") == ModelId.GPT4O_MINI
        assert resolve_model_id("openai", "gpt-3.5-turbo") == ModelId.GPT35_TURBO

    def test_anthropic_mapping(self):
        assert resolve_model_id("anthropic", "claude-3-opus") == ModelId.CLAUDE_3_OPUS
        assert resolve_model_id("anthropic", "claude-3-sonnet") == ModelId.CLAUDE_3_SONNET

    def test_unknown_falls_back(self):
        result = resolve_model_id("unknown", "my-model")
        assert result == ModelId.GPT4O_MINI  # default fallback
