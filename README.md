# AI Market Tracker

**Automated market intelligence for AI Agent & MCP ecosystem.**  
Tracks 30 companies · GitHub · Hacker News · RSS · PyPI · npm  
Updated daily at **00:00 CST** via GitHub Actions.

---

## Live Dashboards

| Dashboard | Description |
|-----------|-------------|
| [🗺 MCP Ecosystem Monitor](https://mingdengdu.github.io/ai-market-tracker/mcp-ecosystem-monitor.html) | 18 companies · 380+ products · Risk/security competitive landscape |
| [📡 AI Agent Global Tracker](https://mingdengdu.github.io/ai-market-tracker/product-tracker.html) | Tencent · Alibaba · ByteDance · Global dynamics |

---

## What Gets Tracked

**30 companies across 5 categories:**

- 🇨🇳 **China T1:** Tencent · Alibaba · ByteDance · Baidu · Ant Group · Huawei
- 🇨🇳 **China T2:** Xiaomi · JD · NetEase · Kuaishou · iFlytek · MiniMax · Moonshot · SenseTime · Meituan · 360 · WPS · Zhipu
- 🛡️ **Risk/Fintech:** TongDun · DataVisor · SEON · Sift · Sardine · Stripe · Unit21
- 🌏 **SEA:** Sea Group · Grab
- 🌍 **Global:** Anthropic · OpenAI · Google · Microsoft

**5 data sources per run:**

```
GitHub API     → org repos + keyword search (MCP, fintech, regtech)
Hacker News    → Algolia API, 5 targeted queries
RSS Feeds      → Anthropic, OpenAI, Google, Microsoft, Stripe, HuggingFace, LangChain
PyPI           → mcp, anthropic, openai-agents, langchain-mcp
npm            → @modelcontextprotocol/sdk, @anthropic-ai/sdk, mcp-client
```

---

## Run Locally

```bash
git clone https://github.com/mingdengdu/ai-market-tracker
cd ai-market-tracker

# Fetch all signals
python tracker/fetch_signals.py

# Inject into dashboards
python tracker/inject_signals.py

# Check results
cat tracker/data/signals.json | python -c "
import json, sys
d = json.load(sys.stdin)
print(f\"Updated: {d['updated']} | Signals: {d['count\']}\")
for s in d['signals'][:5]:
    print(f\"  [{s['date']}] {s['title'][:70]}\")
"
```

---

## Key Finding

> **0 out of 20 risk/security products have MCP integration.**  
> Every other tech vertical (productivity, content, search, commerce) has MCP coverage.  
> Risk and compliance are the last unserved vertical — and the highest-value one for enterprise AI adoption.

This tracker was built to monitor when that changes.

→ See full analysis: [MCP Ecosystem Monitor](https://mingdengdu.github.io/ai-market-tracker/mcp-ecosystem-monitor.html)

---

*Built by [Martin Du](https://github.com/mingdengdu/ai-product-studio) · Signals update daily*
