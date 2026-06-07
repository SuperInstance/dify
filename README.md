![cover-v5-optimized](./images/GitHub_README_if.png)

> **🏷️ SuperInstance Fork** — This is the [SuperInstance](https://github.com/SuperInstance) fork of [Dify](https://github.com/langgenius/dify), configured with **z.ai GLM-5.1** as the default provider and **DeepInfra** as fallback. Includes our Budget Watchdog for cost management. See [SUPERINSTANCE_CHANGES.md](./SUPERINSTANCE_CHANGES.md) for details.

<p align="center">
  <a href="https://cloud.dify.ai">Dify Cloud</a> ·
  <a href="https://docs.dify.ai/getting-started/install-self-hosted">Self-hosting</a> ·
  <a href="https://docs.dify.ai">Documentation</a> ·
  <a href="https://dify.ai/pricing">Dify edition overview</a>
</p>

<p align="center">
    <a href="https://dify.ai" target="_blank">
        <img alt="Static Badge" src="https://img.shields.io/badge/Product-F04438"></a>
    <a href="https://dify.ai/pricing" target="_blank">
        <img alt="Static Badge" src="https://img.shields.io/badge/free-pricing?logo=free&color=%20%23155EEF&label=pricing&labelColor=%20%23528bff"></a>
    <a href="https://discord.gg/FngNHpbcY7" target="_blank">
        <img src="https://img.shields.io/discord/1082486657678311454?logo=discord&labelColor=%20%235462eb&logoColor=%20%23f5f5f5&color=%20%235462eb"
            alt="chat on Discord"></a>
    <a href="https://reddit.com/r/difyai" target="_blank">  
        <img src="https://img.shields.io/reddit/subreddit-subscribers/difyai?style=plastic&logo=reddit&label=r%2Fdifyai&labelColor=white"
            alt="join Reddit"></a>
    <a href="https://twitter.com/intent/follow?screen_name=dify_ai" target="_blank">
        <img src="https://img.shields.io/twitter/follow/dify_ai?logo=X&color=%20%23f5f5f5"
            alt="follow on X(Twitter)"></a>
    <a href="https://www.linkedin.com/company/langgenius/" target="_blank">
        <img src="https://custom-icon-badges.demolab.com/badge/LinkedIn-0A66C2?logo=linkedin-white&logoColor=fff"
            alt="follow on LinkedIn"></a>
    <a href="https://hub.docker.com/u/langgenius" target="_blank">
        <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/langgenius/dify-web?labelColor=%20%23FDB062&color=%20%23f79009"></a>
    <a href="https://github.com/langgenius/dify/graphs/commit-activity" target="_blank">
        <img alt="Commits last month" src="https://img.shields.io/github/commit-activity/m/langgenius/dify?labelColor=%20%2332b583&color=%20%2312b76a"></a>
    <a href="https://github.com/langgenius/dify/" target="_blank">
        <img alt="Issues closed" src="https://img.shields.io/github/issues-search?query=repo%3Alanggenius%2Fdify%20is%3Aclosed&label=issues%20closed&labelColor=%20%237d89b0&color=%20%235d6b98"></a>
    <a href="https://github.com/langgenius/dify/discussions/" target="_blank">
        <img alt="Discussion posts" src="https://img.shields.io/github/discussions/langgenius/dify?labelColor=%20%239b8afb&color=%20%237a5af8"></a>
    <a href="https://insights.linuxfoundation.org/project/langgenius-dify" target="_blank">
        <img alt="LFX Health Score" src="https://insights.linuxfoundation.org/api/badge/health-score?project=langgenius-dify"></a>
    <a href="https://insights.linuxfoundation.org/project/langgenius-dify" target="_blank">
        <img alt="LFX Contributors" src="https://insights.linuxfoundation.org/api/badge/contributors?project=langgenius-dify"></a>
    <a href="https://insights.linuxfoundation.org/project/langgenius-dify" target="_blank">
        <img alt="LFX Active Contributors" src="https://insights.linuxfoundation.org/api/badge/active-contributors?project=langgenius-dify"></a>
</p>

<p align="center">
  <a href="./README.md"><img alt="README in English" src="https://img.shields.io/badge/English-d9d9d9"></a>
  <a href="./docs/zh-TW/README.md"><img alt="繁體中文文件" src="https://img.shields.io/badge/繁體中文-d9d9d9"></a>
  <a href="./docs/zh-CN/README.md"><img alt="简体中文文件" src="https://img.shields.io/badge/简体中文-d9d9d9"></a>
  <a href="./docs/ja-JP/README.md"><img alt="日本語のREADME" src="https://img.shields.io/badge/日本語-d9d9d9"></a>
  <a href="./docs/es-ES/README.md"><img alt="README en Español" src="https://img.shields.io/badge/Español-d9d9d9"></a>
  <a href="./docs/fr-FR/README.md"><img alt="README en Français" src="https://img.shields.io/badge/Français-d9d9d9"></a>
  <a href="./docs/tlh/README.md"><img alt="README tlhIngan Hol" src="https://img.shields.io/badge/Klingon-d9d9d9"></a>
  <a href="./docs/ko-KR/README.md"><img alt="README in Korean" src="https://img.shields.io/badge/한국어-d9d9d9"></a>
  <a href="./docs/ar-SA/README.md"><img alt="README بالعربية" src="https://img.shields.io/badge/العربية-d9d9d9"></a>
  <a href="./docs/tr-TR/README.md"><img alt="Türkçe README" src="https://img.shields.io/badge/Türkçe-d9d9d9"></a>
  <a href="./docs/vi-VN/README.md"><img alt="README Tiếng Việt" src="https://img.shields.io/badge/Ti%E1%BA%BFng%20Vi%E1%BB%87t-d9d9d9"></a>
  <a href="./docs/de-DE/README.md"><img alt="README in Deutsch" src="https://img.shields.io/badge/German-d9d9d9"></a>
  <a href="./docs/it-IT/README.md"><img alt="README in Italiano" src="https://img.shields.io/badge/Italiano-d9d9d9"></a>
  <a href="./docs/pt-BR/README.md"><img alt="README em Português do Brasil" src="https://img.shields.io/badge/Portugu%C3%AAs%20do%20Brasil-d9d9d9"></a>
  <a href="./docs/sl-SI/README.md"><img alt="README Slovenščina" src="https://img.shields.io/badge/Sloven%C5%A1%C4%8Dina-d9d9d9"></a>
  <a href="./docs/bn-BD/README.md"><img alt="README in বাংলা" src="https://img.shields.io/badge/বাংলা-d9d9d9"></a>
  <a href="./docs/hi-IN/README.md"><img alt="README in हिन्दी" src="https://img.shields.io/badge/Hindi-d9d9d9"></a>
</p>

Dify is an open-source LLM app development platform. Its intuitive interface combines AI workflow, RAG pipeline, agent capabilities, model management, observability features (including [Opik](https://www.comet.com/docs/opik/integrations/dify), [Langfuse](https://docs.langfuse.com), and [Arize Phoenix](https://docs.arize.com/phoenix)) and more, letting you quickly go from prototype to production. Here's a list of the core features:

## Quick start

> Before installing Dify, make sure your machine meets the following minimum system requirements:
>
> - CPU >= 2 Core
> - RAM >= 4 GiB

<br/>

The easiest way to start the Dify server is through [Docker Compose](docker/docker-compose.yaml). Before running Dify with the following commands, make sure that [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) are installed on your machine:

```bash
cd dify
cd docker
cp .env.example .env
docker compose up -d
```

After running, you can access the Dify dashboard in your browser at [http://localhost/install](http://localhost/install) and start the initialization process.

#### Seeking help

Please refer to our [FAQ](https://docs.dify.ai/getting-started/install-self-hosted/faqs) if you encounter problems setting up Dify. Reach out to [the community and us](#community--contact) if you are still having issues.

> If you'd like to contribute to Dify or do additional development, refer to our [guide to deploying from source code](https://docs.dify.ai/getting-started/install-self-hosted/local-source-code)

## Key features

**1. Workflow**:
Build and test powerful AI workflows on a visual canvas, leveraging all the following features and beyond.

**2. Comprehensive model support**:
Seamless integration with hundreds of proprietary / open-source LLMs from dozens of inference providers and self-hosted solutions, covering GPT, Mistral, Llama3, and any OpenAI API-compatible models. A full list of supported model providers can be found [here](https://docs.dify.ai/getting-started/readme/model-providers).

![providers-v5](https://github.com/langgenius/dify/assets/13230914/5a17bdbe-097a-4100-8363-40255b70f6e3)

**3. Prompt IDE**:
Intuitive interface for crafting prompts, comparing model performance, and adding additional features such as text-to-speech to a chat-based app.

**4. RAG Pipeline**:
Extensive RAG capabilities that cover everything from document ingestion to retrieval, with out-of-box support for text extraction from PDFs, PPTs, and other common document formats.

**5. Agent capabilities**:
You can define agents based on LLM Function Calling or ReAct, and add pre-built or custom tools for the agent. Dify provides 50+ built-in tools for AI agents, such as Google Search, DALL·E, Stable Diffusion and WolframAlpha.

**6. LLMOps**:
Monitor and analyze application logs and performance over time. You could continuously improve prompts, datasets, and models based on production data and annotations.

**7. Backend-as-a-Service**:
All of Dify's offerings come with corresponding APIs, so you could effortlessly integrate Dify into your own business logic.

## Using Dify

- **Cloud <br/>**
  We host a [Dify Cloud](https://dify.ai) service for anyone to try with zero setup. It provides all the capabilities of the self-deployed version, and includes 200 free GPT-4 calls in the sandbox plan.

- **Self-hosting Dify Community Edition<br/>**
  Quickly get Dify running in your environment with this [starter guide](#quick-start).
  Use our [documentation](https://docs.dify.ai) for further references and more in-depth instructions.

- **Dify for enterprise / organizations<br/>**
  We provide additional enterprise-centric features. [Send us an email](mailto:business@dify.ai?subject=%5BGitHub%5DBusiness%20License%20Inquiry) to discuss your enterprise needs. <br/>

  > For startups and small businesses using AWS, check out [Dify Premium on AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-t22mebxzwjhu6) and deploy it to your own AWS VPC with one click. It's an affordable AMI offering with the option to create apps with custom logo and branding.

## Staying ahead

Star Dify on GitHub and be instantly notified of new releases.

![star-us](https://github.com/langgenius/dify/assets/13230914/b823edc1-6388-4e25-ad45-2f6b187adbb4)

## Advanced Setup

### Custom configurations

If you need to customize the configuration, edit `docker/.env`. The essential startup defaults live in [`docker/.env.example`](docker/.env.example), and optional advanced variables are split under `docker/envs/` by theme. After making any changes, re-run `docker compose up -d` from the `docker` directory. You can find the full list of available environment variables [here](https://docs.dify.ai/getting-started/install-self-hosted/environments).

### Metrics Monitoring with Grafana

Import the dashboard to Grafana, using Dify's PostgreSQL database as data source, to monitor metrics in granularity of apps, tenants, messages, and more.

- [Grafana Dashboard by @bowenliang123](https://github.com/bowenliang123/dify-grafana-dashboard)

### Deployment with Kubernetes

If you'd like to configure a highly available setup, there are community-contributed [Helm Charts](https://helm.sh/) and YAML files which allow Dify to be deployed on Kubernetes.

- [Helm Chart by @LeoQuote](https://github.com/douban/charts/tree/master/charts/dify)
- [Helm Chart by @BorisPolonsky](https://github.com/BorisPolonsky/dify-helm)
- [Helm Chart by @magicsong](https://github.com/magicsong/ai-charts)
- [YAML file by @Winson-030](https://github.com/Winson-030/dify-kubernetes)
- [YAML file by @wyy-holding](https://github.com/wyy-holding/dify-k8s)
- [🚀 NEW! YAML files (Supports Dify v1.6.0) by @Zhoneym](https://github.com/Zhoneym/DifyAI-Kubernetes)

#### Using Terraform for Deployment

Deploy Dify to Cloud Platform with a single click using [terraform](https://www.terraform.io/)

##### Azure Global

- [Azure Terraform by @nikawang](https://github.com/nikawang/dify-azure-terraform)

##### Google Cloud

- [Google Cloud Terraform by @sotazum](https://github.com/DeNA/dify-google-cloud-terraform)

#### Using AWS CDK for Deployment

Deploy Dify to AWS with [CDK](https://aws.amazon.com/cdk/)

##### AWS

- [AWS CDK by @KevinZhao (EKS based)](https://github.com/aws-samples/solution-for-deploying-dify-on-aws)
- [AWS CDK by @tmokmss (ECS based)](https://github.com/aws-samples/dify-self-hosted-on-aws)

#### Using Alibaba Cloud Computing Nest

Quickly deploy Dify to Alibaba cloud with [Alibaba Cloud Computing Nest](https://computenest.console.aliyun.com/service/instance/create/default?type=user&ServiceName=Dify%E7%A4%BE%E5%8C%BA%E7%89%88)

#### Using Alibaba Cloud Data Management

One-Click deploy Dify to Alibaba Cloud with [Alibaba Cloud Data Management](https://www.alibabacloud.com/help/en/dms/dify-in-invitational-preview/)

#### Deploy to AKS with Azure Devops Pipeline

One-Click deploy Dify to AKS with [Azure Devops Pipeline Helm Chart by @LeoZhang](https://github.com/Ruiruiz30/Dify-helm-chart-AKS)

## Contributing

For those who'd like to contribute code, see our [Contribution Guide](https://github.com/langgenius/dify/blob/main/CONTRIBUTING.md).
At the same time, please consider supporting Dify by sharing it on social media and at events and conferences.

> We are looking for contributors to help translate Dify into languages other than Mandarin or English. If you are interested in helping, please see the [i18n README](https://github.com/langgenius/dify/blob/main/web/i18n-config/README.md) for more information, and leave us a comment in the `global-users` channel of our [Discord Community Server](https://discord.gg/8Tpq4AcN9c).

## Community & contact

- [GitHub Discussion](https://github.com/langgenius/dify/discussions). Best for: sharing feedback and asking questions.
- [GitHub Issues](https://github.com/langgenius/dify/issues). Best for: bugs you encounter using Dify.AI, and feature proposals. See our [Contribution Guide](https://github.com/langgenius/dify/blob/main/CONTRIBUTING.md).
- [Discord](https://discord.gg/FngNHpbcY7). Best for: sharing your applications and hanging out with the community.
- [X(Twitter)](https://twitter.com/dify_ai). Best for: sharing your applications and hanging out with the community.

**Contributors**

<a href="https://github.com/langgenius/dify/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=langgenius/dify" />
</a>

## 🏆 SuperInstance Enhancement: Budget Watchdog

47 AI workflows. $12,000 API bill. Nobody knows which workflow cost what.

The Budget Watchdog tracks per-workflow token and cost consumption, auto-downgrades models when budgets approach their limit, and surfaces exactly who spent what.

### 1. Hook it up

Add the layer to your workflow engine:

```python
from controllers.service_api.budget_watchdog.layer import BudgetWatchdogLayer

# The watchdog sits alongside the existing LLMQuotaLayer
self.graph_engine.layer(LLMQuotaLayer(tenant_id=tenant_id))
self.graph_engine.layer(BudgetWatchdogLayer(tenant_id=tenant_id))
```

### 2. Configure a budget

```python
from controllers.service_api.budget_watchdog.budget import BudgetWindow, WorkflowBudget
from controllers.service_api.budget_watchdog.model import ModelId

budget = WorkflowBudget.create(
    workflow_name="pdf-analyzer",
    model=ModelId.CLAUDE_3_OPUS,   # $0.15/$0.75 per 1K tokens
    token_limit=100_000,
    cost_limit_cents=50_000,        # $500/day
    window=BudgetWindow.DAILY,
)
```

Or via the REST API:

```bash
curl -X POST https://your-dify/v1/budgets \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "pdf-analyzer",
    "model": "claude-3-opus",
    "token_limit": 100000,
    "cost_limit_cents": 50000
  }'
```

### 3. Track team budgets

```python
from controllers.service_api.budget_watchdog.team import TeamBudget, TeamMember

team = TeamBudget(
    name="engineering",
    team_token_limit=10_000_000,
    team_cost_limit_cents=500_000,  # $5,000/30 days
    period_days=30,
)

team.add_member(TeamMember("engineer-a@co.com", token_quota=2_000_000, cost_quota_cents=100_000))
team.add_member(TeamMember("engineer-b@co.com", token_quota=2_000_000, cost_quota_cents=100_000))
```

### 4. Watch it downgrade automatically

Workflow `pdf-analyzer` hit 85% of $500. The watchdog triggered the Transitioning phase:

```python
phase, downgraded = budget.spend_and_downgrade(tokens=85_000, cost_cents=42_500)
assert phase == BudgetPhase.TRANSITIONING
assert downgraded == ModelId.CLAUDE_3_SONNET  # Opus → Sonnet
```

Remaining requests for the day run on Claude 3 Sonnet ($0.03/$0.15 per 1K tokens) instead of Opus ($0.15/$0.75). That saves roughly **$127** per budget window at current usage patterns.

### 5. The bill breakdown

Query the watchdog for real numbers:

```bash
curl https://your-dify/v1/budgets | jq .
```

```json
[
  {
    "workflow_name": "pdf-analyzer",
    "model": "claude-3-sonnet",
    "cost_limit_cents": 50000,
    "cost_consumed_cents": 48000,
    "cost_utilisation": 0.96,
    "downgrade_count": 1,
    "phase": "transitioning"
  },
  {
    "workflow_name": "customer-support",
    "cost_limit_cents": 30000,
    "cost_consumed_cents": 7500,
    "cost_utilisation": 0.25,
    "phase": "normal"
  },
  {
    "workflow_name": "data-extraction",
    "cost_limit_cents": 25000,
    "cost_consumed_cents": 24000,
    "cost_utilisation": 0.96,
    "phase": "transitioning"
  }
]
```

Team breakdown:

```bash
curl https://your-dify/v1/budgets/team | jq .
```

```json
{
  "name": "engineering",
  "team_cost_limit_cents": 500000,
  "team_cost_consumed_cents": 415000,
  "team_token_utilisation": 0.83,
  "member_count": 2,
  "workflow_count": 3,
  "members": [
    {
      "id": "engineer-a@co.com",
      "cost_quota_cents": 100000,
      "cost_consumed_cents": 78000,
      "cost_utilisation": 0.78
    },
    {
      "id": "engineer-b@co.com",
      "cost_quota_cents": 100000,
      "cost_consumed_cents": 55000,
      "cost_utilisation": 0.55
    }
  ]
}
```

**Engineer A**: $2,340 consumed. One workflow (pdf-analyzer) accounts for 40% of the total team bill.

### Ah-ha

That PDF analyzer costs more than everything else combined. The fix: switch Claude Opus → Sonnet when the PDF is over 10 pages. At current volume, that saves **$3,200/month**. The watchdog tells you exactly which workflow to fix — the data, not hunches.

### Alert webhook payload

When a budget transitions to PreTransition (≥60%) or Transitioning (≥85%), the watchdog fires alerts. Here's what gets sent:

```json
{
  "alerts": [
    {
      "timestamp": "2026-06-02T01:15:00+00:00",
      "workflow": "pdf-analyzer",
      "level": "critical",
      "message": "Workflow 'pdf-analyzer' — auto-downgraded from Claude 3 Opus to Claude 3 Sonnet"
    },
    {
      "timestamp": "2026-06-02T00:30:00+00:00",
      "workflow": "pdf-analyzer",
      "level": "warning",
      "message": "Workflow 'pdf-analyzer' at 72.5% token limit (72500/100000)"
    },
    {
      "timestamp": "2026-06-02T00:00:00+00:00",
      "workflow": "pdf-analyzer",
      "level": "info",
      "message": "Workflow 'pdf-analyzer' operating normally"
    }
  ]
}
```

### What it does under the hood

- Tracks token and cost consumption per workflow within configurable windows (daily/weekly/monthly)
- Three-phase conservation model: **Normal** (<60%) → **PreTransition** (≥60%, logged) → **Transitioning** (≥85%, auto-downgrade)
- When a window resets, the model upgrades back to the original
- Downgrade chains per provider: Opus→Sonnet→Haiku, GPT-4o→GPT-4o-mini→GPT-3.5 Turbo, Gemini Pro→Flash, Llama 70B→8B
- In-memory alert store with ring-buffer retention; swappable for Redis/PostgreSQL in production
- All state lives on the `BudgetWatchdogLayer` class — configure once, enforce everywhere

See [INTEGRATION.md](./INTEGRATION.md) for the full API reference and production migration guide.

---

## 🧬 SuperInstance Provider Configuration

This fork replaces OpenAI/Anthropic defaults with our own provider stack:

| Role | Provider | Model | Use Case |
|------|----------|-------|----------|
| **Primary** | z.ai | GLM-5.1 | All tasks — best quality |
| **Fallback** | DeepInfra | seed-2.0-mini | Fast/cheap tasks |
| **Fallback** | DeepInfra | gemma-4 | General purpose |
| **Fallback** | DeepInfra | nemotron-120b | Complex reasoning |
| **Fallback** | DeepInfra | qwen-3.6 | Multilingual |
| **Fallback** | DeepInfra | hermes-405b | Maximum capability |

**Quick setup:**

```bash
cp docker/envs/superinstance-models.env.example docker/envs/superinstance-models.env
# Edit with your API keys
vim docker/envs/superinstance-models.env
docker compose up -d
```

See [SUPERINSTANCE_CHANGES.md](./SUPERINSTANCE_CHANGES.md) for full details.

---

## Star history

[![Star History Chart](https://api.star-history.com/svg?repos=langgenius/dify&type=Date)](https://star-history.com/#langgenius/dify&Date)

## Security disclosure

To protect your privacy, please avoid posting security issues on GitHub. Instead, report issues to security@dify.ai, and our team will respond with detailed answer.

## License

This repository is licensed under the [Dify Open Source License](LICENSE), based on Apache 2.0 with additional conditions.
