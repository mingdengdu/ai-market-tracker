#!/usr/bin/env python3
"""
AI Product & MCP Ecosystem Signal Fetcher
Runs daily via GitHub Actions. Fetches from:
  - GitHub API (repos, releases, topics)
  - Hacker News Algolia API
  - Product Hunt API (public)
  - RSS feeds (company blogs)
  - pypi/npm package trackers

Outputs: data/signals.json (raw), data/digest.json (structured for HTML inject)
"""

import json
import urllib.request
import urllib.parse
import datetime
import time
import os
import sys
import re
from pathlib import Path

TODAY = datetime.date.today().isoformat()
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────
# TRACKED COMPANIES & KEYWORDS
# ──────────────────────────────────────────────

COMPANIES = {
    # --- Domestic China ---
    "tencent":    {"name": "Tencent", "zh": "腾讯",   "github_orgs": ["Tencent", "TencentARC", "TencentCloud"], "keywords": ["tencent mcp", "workbuddy", "QClaw", "腾讯 MCP"]},
    "alibaba":    {"name": "Alibaba", "zh": "阿里",    "github_orgs": ["alibaba", "aliyun", "alibaba-cloud-mcp-servers"],  "keywords": ["alibaba mcp", "qwen mcp", "阿里 MCP", "bailian mcp", "HiClaw", "dingtalk mcp"]},
    "bytedance":  {"name": "ByteDance","zh": "字节",   "github_orgs": ["bytedance", "coze-dev"],  "keywords": ["coze mcp", "ArkClaw", "bytedance mcp", "doubao mcp", "字节 MCP"]},
    "baidu":      {"name": "Baidu",   "zh": "百度",    "github_orgs": ["baidu", "PaddlePaddle", "baidu-qianfan"],  "keywords": ["ernie mcp", "qianfan mcp", "百度 MCP", "文心 MCP"]},
    "ant":        {"name": "Ant Group","zh": "蚂蚁",   "github_orgs": ["ant-design", "antgroup", "alipay"],  "keywords": ["ant mcp", "alipay mcp", "bailing agent", "蚂蚁 MCP"]},
    "huawei":     {"name": "Huawei",  "zh": "华为",    "github_orgs": ["huaweicloud", "huawei-noah"],  "keywords": ["huawei mcp", "pangu mcp", "modelarts mcp", "华为 MCP"]},
    "xiaomi":     {"name": "Xiaomi",  "zh": "小米",    "github_orgs": ["MiCode", "XiaoMi"],  "keywords": ["xiaomi mcp", "xiaoai mcp", "小爱 MCP"]},
    "jd":         {"name": "JD.com",  "zh": "京东",    "github_orgs": ["jd-platform-github", "jd-opensource"],  "keywords": ["jd mcp", "京东 MCP", "言犀 MCP"]},
    "netease":    {"name": "NetEase", "zh": "网易",    "github_orgs": ["NetEase"],  "keywords": ["netease mcp", "网易 MCP"]},
    "kuaishou":   {"name": "Kuaishou","zh": "快手",    "github_orgs": ["KwaiVGI"],  "keywords": ["kuaishou mcp", "kling mcp", "快手 MCP"]},
    "iflytek":    {"name": "iFlytek", "zh": "科大讯飞","github_orgs": [],           "keywords": ["iflytek mcp", "spark mcp", "讯飞 MCP"]},
    "minimax":    {"name": "MiniMax", "zh": "MiniMax", "github_orgs": ["MiniMax-AI"],  "keywords": ["minimax mcp", "hailuoai mcp", "海螺 MCP"]},
    "moonshot":   {"name": "Moonshot","zh": "月之暗面","github_orgs": ["MoonshotAI"],  "keywords": ["kimi mcp", "moonshot mcp", "Kimi MCP"]},
    "sensetime":  {"name": "SenseTime","zh": "商汤",   "github_orgs": ["SenseTime"],  "keywords": ["sensetime mcp", "商汤 MCP", "日日新 MCP"]},
    "meituan":    {"name": "Meituan", "zh": "美团",    "github_orgs": [],           "keywords": ["meituan mcp", "美团 MCP"]},
    "360":        {"name": "360",     "zh": "360",     "github_orgs": ["Qihoo360"],  "keywords": ["360 mcp", "360ai mcp"]},
    "wps":        {"name": "WPS",     "zh": "金山",    "github_orgs": ["wps-dev"],   "keywords": ["wps mcp", "wps ai mcp", "金山 MCP"]},
    "zhipu":      {"name": "Zhipu",   "zh": "智谱",    "github_orgs": ["THUDM"],     "keywords": ["glm mcp", "zhipu mcp", "智谱 MCP", "chatglm mcp"]},
    # --- Risk / Fintech ---
    "tongdun":    {"name": "TongDun", "zh": "同盾",    "github_orgs": [],           "keywords": ["tongdun mcp", "同盾 MCP"]},
    "datavisor":  {"name": "DataVisor","zh": "DataVisor","github_orgs": [],          "keywords": ["datavisor mcp", "datavisor agent"]},
    "seon":       {"name": "SEON",    "zh": "SEON",    "github_orgs": [],           "keywords": ["seon mcp", "seon fraud mcp"]},
    "sift":       {"name": "Sift",    "zh": "Sift",    "github_orgs": [],           "keywords": ["sift mcp", "sift fraud mcp"]},
    "sardine":    {"name": "Sardine", "zh": "Sardine", "github_orgs": [],           "keywords": ["sardine mcp", "sardine fraud"]},
    "stripe":     {"name": "Stripe",  "zh": "Stripe",  "github_orgs": ["stripe"],   "keywords": ["stripe mcp", "stripe radar mcp"]},
    "unit21":     {"name": "Unit21",  "zh": "Unit21",  "github_orgs": [],           "keywords": ["unit21 mcp", "unit21 agent"]},
    # --- Global AI Platforms ---
    "anthropic":  {"name": "Anthropic","zh": "Anthropic","github_orgs": ["anthropics"], "keywords": ["claude mcp", "mcp protocol", "anthropic mcp server"]},
    "openai":     {"name": "OpenAI",  "zh": "OpenAI",  "github_orgs": ["openai"],   "keywords": ["openai mcp", "gpt mcp", "openai agent"]},
    "google":     {"name": "Google",  "zh": "Google",  "github_orgs": ["google-deepmind", "google"],  "keywords": ["gemini mcp", "google mcp", "adk mcp"]},
    "microsoft":  {"name": "Microsoft","zh": "微软",   "github_orgs": ["microsoft", "github"],  "keywords": ["copilot mcp", "azure mcp", "github mcp"]},
    "sea":        {"name": "Sea Group","zh": "Sea",    "github_orgs": [],           "keywords": ["sea mcp", "seamoney mcp", "shopee ai"]},
    "grab":       {"name": "Grab",    "zh": "Grab",    "github_orgs": ["grab"],     "keywords": ["grab mcp", "grab ai agent"]},
}

# 全局 MCP 关键词（独立于公司）
GLOBAL_KEYWORDS = [
    "MCP server",
    "model context protocol",
    "mcp-server",
    "claude desktop",
    "AI agent fintech",
    "regtech AI",
    "fraud detection MCP",
    "compliance AI agent",
    "payment fraud AI",
    "risk engine MCP",
]

# ──────────────────────────────────────────────
# FETCHERS
# ──────────────────────────────────────────────

def fetch_url(url, headers=None, timeout=15):
    h = {"User-Agent": "Mozilla/5.0 (compatible; tracker-bot/1.0)"}
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠️  fetch error {url}: {e}", file=sys.stderr)
        return None

def fetch_github_repos(org, limit=10):
    """Fetch recently updated repos for a GitHub org"""
    url = f"https://api.github.com/orgs/{org}/repos?sort=updated&per_page={limit}&type=public"
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    data = fetch_url(url, headers)
    if not data or not isinstance(data, list):
        return []
    results = []
    for r in data:
        pushed = r.get("pushed_at", "")[:10]
        if pushed >= "2025-01-01":  # 只要2025年以后的
            results.append({
                "type": "github_repo",
                "company": org,
                "title": r["full_name"],
                "desc": r.get("description") or "",
                "url": r["html_url"],
                "date": pushed,
                "stars": r.get("stargazers_count", 0),
                "topics": r.get("topics", []),
            })
    return results

def fetch_github_search(query, limit=10):
    """Search GitHub for repos/code matching keywords"""
    q = urllib.parse.quote(f"{query} pushed:>2025-01-01")
    url = f"https://api.github.com/search/repositories?q={q}&sort=updated&per_page={limit}"
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    data = fetch_url(url, headers)
    if not data or "items" not in data:
        return []
    results = []
    for r in data["items"]:
        pushed = r.get("pushed_at", "")[:10]
        results.append({
            "type": "github_search",
            "query": query,
            "title": r["full_name"],
            "desc": r.get("description") or "",
            "url": r["html_url"],
            "date": pushed,
            "stars": r.get("stargazers_count", 0),
            "topics": r.get("topics", []),
        })
    return results

def fetch_hackernews(query, limit=10):
    """Search Hacker News via Algolia API"""
    q = urllib.parse.quote(query)
    url = f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage={limit}&numericFilters=created_at_i>1735689600"
    data = fetch_url(url)
    if not data or "hits" not in data:
        return []
    results = []
    for h in data["hits"]:
        ts = h.get("created_at", "")[:10]
        results.append({
            "type": "hackernews",
            "query": query,
            "title": h.get("title", ""),
            "desc": f"HN score: {h.get('points',0)} | comments: {h.get('num_comments',0)}",
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
            "date": ts,
            "score": h.get("points", 0),
        })
    return results

def fetch_pypi_package(package_name):
    """Check if an MCP-related Python package was recently updated"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    data = fetch_url(url)
    if not data:
        return None
    info = data.get("info", {})
    releases = data.get("releases", {})
    latest = info.get("version", "")
    if latest in releases:
        upload_time = releases[latest][0].get("upload_time", "")[:10] if releases[latest] else ""
    else:
        upload_time = ""
    return {
        "type": "pypi",
        "title": f"PyPI: {package_name} v{latest}",
        "desc": info.get("summary", ""),
        "url": f"https://pypi.org/project/{package_name}/",
        "date": upload_time,
        "version": latest,
    }

def fetch_npm_package(package_name):
    """Check npm package update time"""
    url = f"https://registry.npmjs.org/{urllib.parse.quote(package_name)}"
    data = fetch_url(url)
    if not data:
        return None
    time_data = data.get("time", {})
    modified = time_data.get("modified", "")[:10]
    latest_ver = data.get("dist-tags", {}).get("latest", "")
    return {
        "type": "npm",
        "title": f"npm: {package_name}@{latest_ver}",
        "desc": data.get("description", ""),
        "url": f"https://www.npmjs.com/package/{package_name}",
        "date": modified,
        "version": latest_ver,
    }

def fetch_rss(url, limit=5):
    """Fetch and parse RSS feed"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8", errors="replace")
        # 简单解析 RSS
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        results = []
        for item in items[:limit]:
            title = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
            link = re.search(r'<link[^>]*>(.*?)</link>', item, re.DOTALL)
            pubdate = re.search(r'<pubDate>(.*?)</pubDate>', item, re.DOTALL)
            desc = re.search(r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
            if title:
                # 解析日期
                date_str = ""
                if pubdate:
                    try:
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(pubdate.group(1).strip())
                        date_str = dt.date().isoformat()
                    except:
                        date_str = pubdate.group(1).strip()[:10]
                results.append({
                    "type": "rss",
                    "source": url,
                    "title": re.sub(r'<[^>]+>', '', title.group(1)).strip(),
                    "desc": re.sub(r'<[^>]+>', '', (desc.group(1) if desc else "")).strip()[:200],
                    "url": link.group(1).strip() if link else "",
                    "date": date_str,
                })
        return results
    except Exception as e:
        print(f"  ⚠️  RSS error {url}: {e}", file=sys.stderr)
        return []

# ──────────────────────────────────────────────
# RSS SOURCES
# ──────────────────────────────────────────────

RSS_FEEDS = {
    "anthropic":  "https://www.anthropic.com/rss.xml",
    "openai":     "https://openai.com/blog/rss.xml",
    "google":     "https://blog.google/technology/ai/rss/",
    "microsoft":  "https://blogs.microsoft.com/ai/feed/",
    "stripe":     "https://stripe.com/blog/feed.rss",
    "huggingface":"https://huggingface.co/blog/feed.xml",
    "langchain":  "https://blog.langchain.dev/rss/",
}

# ──────────────────────────────────────────────
# MCP ECOSYSTEM SPECIFIC TRACKERS
# ──────────────────────────────────────────────

MCP_GITHUB_SEARCHES = [
    "mcp-server fraud",
    "mcp-server fintech",
    "mcp-server regtech",
    "mcp-server payment",
    "model context protocol risk",
    "mcp-server compliance",
    "mcp-server kyc",
    "mcp-server aml",
]

PYPI_PACKAGES = [
    "mcp",
    "anthropic",
    "openai-agents",
    "langchain-mcp",
]

NPM_PACKAGES = [
    "@modelcontextprotocol/sdk",
    "@anthropic-ai/sdk",
    "mcp-client",
]

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    all_signals = []
    
    print(f"[{TODAY}] Starting signal fetch...")

    # 1. GitHub org repos (key orgs only, avoid rate limit)
    priority_orgs = [
        ("anthropics", "anthropic"),
        ("alibaba-cloud-mcp-servers", "alibaba"),
        ("coze-dev", "bytedance"),
        ("modelcontextprotocol", "mcp_ecosystem"),
        ("openai", "openai"),
        ("google-deepmind", "google"),
        ("microsoft", "microsoft"),
        ("stripe", "stripe"),
    ]
    for org, company_key in priority_orgs:
        print(f"  GitHub org: {org}")
        signals = fetch_github_repos(org, limit=8)
        for s in signals:
            s["company_key"] = company_key
        all_signals.extend(signals)
        time.sleep(0.5)

    # 2. GitHub keyword search (MCP ecosystem)
    for query in MCP_GITHUB_SEARCHES[:6]:  # 限制数量避免rate limit
        print(f"  GitHub search: {query}")
        signals = fetch_github_search(query, limit=5)
        for s in signals:
            s["company_key"] = "mcp_ecosystem"
        all_signals.extend(signals)
        time.sleep(1)

    # 3. Hacker News
    hn_queries = [
        "MCP server",
        "model context protocol",
        "AI fraud detection",
        "regtech AI agent",
        "fintech MCP",
    ]
    for q in hn_queries:
        print(f"  HN search: {q}")
        signals = fetch_hackernews(q, limit=5)
        all_signals.extend(signals)
        time.sleep(0.3)

    # 4. RSS feeds
    for company, feed_url in RSS_FEEDS.items():
        print(f"  RSS: {company}")
        signals = fetch_rss(feed_url, limit=3)
        for s in signals:
            s["company_key"] = company
        all_signals.extend(signals)
        time.sleep(0.5)

    # 5. PyPI packages
    for pkg in PYPI_PACKAGES:
        print(f"  PyPI: {pkg}")
        result = fetch_pypi_package(pkg)
        if result:
            result["company_key"] = "mcp_ecosystem"
            all_signals.append(result)
        time.sleep(0.3)

    # 6. npm packages
    for pkg in NPM_PACKAGES:
        print(f"  npm: {pkg}")
        result = fetch_npm_package(pkg)
        if result:
            result["company_key"] = "mcp_ecosystem"
            all_signals.append(result)
        time.sleep(0.3)

    # 过滤: 只保留2025年以后
    all_signals = [s for s in all_signals if s.get("date", "") >= "2025-01-01"]
    
    # 去重 (by url)
    seen_urls = set()
    deduped = []
    for s in all_signals:
        url = s.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(s)
        elif not url:
            deduped.append(s)

    # 按日期排序
    deduped.sort(key=lambda x: x.get("date", ""), reverse=True)

    # 保存原始信号
    with open(OUTPUT_DIR / "signals.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated": TODAY,
            "count": len(deduped),
            "signals": deduped
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Fetched {len(deduped)} signals → data/signals.json")
    
    return deduped

if __name__ == "__main__":
    main()
