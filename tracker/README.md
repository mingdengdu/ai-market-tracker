# Tracker — Automated Signal Pipeline

Runs daily at **00:00 CST** via GitHub Actions.  
Fetches signals from 30+ companies across GitHub, Hacker News, RSS, PyPI, and npm.  
Auto-injects into `04-dashboard/` HTML files and commits.

## What Gets Tracked

| Source | Coverage | Rate limit |
|--------|---------|-----------|
| **GitHub API** | 30 company orgs + keyword search | 5,000 req/hour (authenticated) |
| **Hacker News** | 5 MCP/fintech/regtech queries | Unlimited |
| **RSS Feeds** | Anthropic, OpenAI, Google, Microsoft, Stripe, HuggingFace, LangChain | Unlimited |
| **PyPI** | `mcp`, `anthropic`, `openai-agents`, `langchain-mcp` | Unlimited |
| **npm** | `@modelcontextprotocol/sdk`, `@anthropic-ai/sdk`, `mcp-client` | Unlimited |

## 30 Companies Monitored

**AI Platforms:** Anthropic · OpenAI · Google · Microsoft · Hugging Face  
**China T1:** Tencent · Alibaba · ByteDance · Baidu · Ant Group · Huawei  
**China T2:** Xiaomi · JD · NetEase · Kuaishou · iFlytek · MiniMax · Moonshot · SenseTime · Meituan · 360 · WPS · Zhipu  
**Risk/Fintech:** TongDun · DataVisor · SEON · Sift · Sardine · Stripe · Unit21  
**SEA:** Sea Group · Grab

## Run Locally

```bash
cd tracker
pip install -r requirements.txt   # no deps beyond stdlib
python fetch_signals.py            # outputs data/signals.json
python inject_signals.py           # updates 04-dashboard/ HTML
```

## CLI Usage (via mcporter MCP)

```bash
# Run as MCP tool — fetch and inject in one command
mcporter call tracker fetch_and_update

# Just fetch, no inject
mcporter call tracker fetch_signals

# Check last update
cat tracker/data/signals.json | python -c "import json,sys; d=json.load(sys.stdin); print(f\"Updated: {d['updated']} | Signals: {d['count']}\")"
```

## Output Files

- `data/signals.json` — raw signals (all sources, deduped, sorted by date)
- `data/digest.json` — summary for index.html
- `04-dashboard/product-tracker.html` — injected with `window.AUTO_SIGNALS`
- `04-dashboard/mcp-ecosystem-monitor.html` — injected with `window.AUTO_MCP_SIGNALS`
