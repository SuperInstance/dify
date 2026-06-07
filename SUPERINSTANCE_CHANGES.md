# SuperInstance Changes — Dify Fork

> This document tracks all modifications made to the [Dify](https://github.com/langgenius/dify) upstream by [SuperInstance](https://github.com/SuperInstance).

---

## Fork Purpose

SuperInstance customizes Dify as our primary LLM app development platform, replacing default OpenAI/Anthropic providers with **z.ai GLM-5.1** as the primary model and **DeepInfra** as the fallback provider.

## Changes

### 1. Budget Watchdog (Existing)
- Added per-workflow and team-level budget management
- Auto-downgrade when budgets are exceeded
- RingBuffer-based alert store
- See [INTEGRATION.md](./INTEGRATION.md) for full details

### 2. Provider Configuration Swap

**Primary Provider:** z.ai GLM-5.1
**Fallback Provider:** DeepInfra with model roster:
- `deepinfra/seed-2.0-mini` — Fast, lightweight tasks
- `deepinfra/gemma-4` — General-purpose
- `deepinfra/nemotron-120b` — High-complexity reasoning
- `deepinfra/qwen-3.6` — Balanced performance
- `deepinfra/hermes-405b` — Maximum capability

**Removed from defaults:**
- OpenAI as default provider (still available as optional)
- Anthropic as default provider (still available as optional)

### 3. Environment Variable Changes

New variables in `docker/.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SIA_DEFAULT_PROVIDER` | `zai` | Primary LLM provider |
| `SIA_DEFAULT_MODEL` | `glm-5.1` | Default model for new apps |
| `SIA_FALLBACK_PROVIDER` | `deepinfra` | Fallback when primary unavailable |
| `SIA_FALLBACK_MODELS` | *(comma-separated)* | Model roster for fallback |

### 4. Model Roster Configuration

Added `docker/envs/superinstance-models.env.example` with full model roster configuration for z.ai and DeepInfra providers.

### 5. README Updates

- Added fork notice banner at the top of README.md
- Added SuperInstance section with provider configuration details

## Provider Architecture

```
┌─────────────────────────────────────┐
│         SuperInstance Dify          │
│                                     │
│  ┌─────────────┐  ┌──────────────┐  │
│  │   z.ai      │  │  DeepInfra   │  │
│  │   GLM-5.1   │  │  (fallback)  │  │
│  │  (primary)  │  │              │  │
│  └──────┬──────┘  └──────┬───────┘  │
│         │                │          │
│  ┌──────▼────────────────▼───────┐  │
│  │     Dify Plugin Manager       │  │
│  │  (zhipuai / deepinfra plugin) │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │    Budget Watchdog Layer      │  │
│  │  (cost management + alerts)   │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Upstream Sync

```bash
git remote add upstream https://github.com/langgenius/dify.git
git fetch upstream
git rebase upstream/main
```

## License

This fork maintains the same Apache-2.0 license (with additional conditions) as the upstream Dify project.
