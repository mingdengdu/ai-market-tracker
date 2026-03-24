#!/usr/bin/env python3
"""
HTML Injector: reads data/signals.json + existing HTML templates,
injects fresh data, outputs updated HTML files.
"""

import json
import re
import datetime
from pathlib import Path

TODAY = datetime.date.today().isoformat()
DATA_DIR = Path("data")
DASHBOARD_DIR = Path("04-dashboard")

def load_signals():
    path = DATA_DIR / "signals.json"
    if not path.exists():
        return {"signals": [], "updated": TODAY}
    with open(path) as f:
        return json.load(f)

def build_event_entry(signal):
    """Convert a signal into a JS event object for the timeline"""
    title = signal.get("title", "")[:80]
    desc = signal.get("desc", "")[:120]
    url = signal.get("url", "")
    date = signal.get("date", TODAY)
    company = signal.get("company_key", "")
    sig_type = signal.get("type", "")
    
    # 格式化日期为 YYYY.MM
    date_short = date[:7].replace("-", ".")
    
    text = title
    if desc and desc != title:
        text += f" — {desc[:80]}"
    
    return {
        "d": date_short,
        "c": text,
        "url": url,
        "company": company,
        "type": sig_type,
        "full_date": date,
    }

def inject_into_tracker_html(html_content, signals_data):
    """Inject fresh signals into product-tracker.html"""
    updated = signals_data.get("updated", TODAY)
    
    # 更新日期戳
    html_content = re.sub(
        r'Data updated: \d{4}-\d{2}-\d{2}',
        f'Data updated: {updated}',
        html_content
    )
    
    # 构建新的动态条目 (GitHub + HN类型)
    new_entries = []
    for sig in signals_data.get("signals", [])[:30]:  # 最新30条
        if sig.get("type") in ("github_repo", "github_search", "hackernews", "rss"):
            entry = build_event_entry(sig)
            new_entries.append(entry)
    
    # 注入到 HTML 的 <head> 里，作为全局变量
    injection = f"""
    <!-- Auto-injected by tracker pipeline on {updated} -->
    <script>
    window.AUTO_SIGNALS = {json.dumps(new_entries, ensure_ascii=False, indent=2)};
    window.SIGNAL_UPDATED = "{updated}";
    </script>
"""
    # 插入到 </head> 之前
    html_content = html_content.replace("</head>", injection + "</head>", 1)
    
    return html_content

def inject_into_mcp_monitor_html(html_content, signals_data):
    """Inject MCP-specific signals into mcp-ecosystem-monitor.html"""
    updated = signals_data.get("updated", TODAY)
    
    # 过滤MCP相关信号
    mcp_signals = [
        s for s in signals_data.get("signals", [])
        if any(kw in (s.get("title","") + s.get("desc","")).lower() 
               for kw in ["mcp", "model context protocol", "mcp-server", "mcp server"])
    ][:20]
    
    # 更新最后更新时间
    html_content = re.sub(
        r'最后更新：\d{4} 年 \d+ 月',
        f'最后更新：{updated[:4]} 年 {int(updated[5:7])} 月',
        html_content
    )
    
    # 注入新MCP事件到events数组末尾
    new_events_js = []
    for sig in mcp_signals[:10]:
        title = sig.get("title","")[:100].replace('"', '\\"')
        date_short = sig.get("date","")[:7].replace("-",".")
        url = sig.get("url","")
        new_events_js.append(f'  {{d:"{date_short}",c:"{title}",url:"{url}"}}')
    
    auto_injection = f"""
    <!-- Auto-injected signals {updated} -->
    <script>
    window.AUTO_MCP_SIGNALS = {json.dumps([build_event_entry(s) for s in mcp_signals], ensure_ascii=False)};
    window.MCP_SIGNAL_UPDATED = "{updated}";
    </script>
"""
    html_content = html_content.replace("</head>", auto_injection + "</head>", 1)
    
    return html_content

def main():
    signals_data = load_signals()
    count = len(signals_data.get("signals", []))
    print(f"Loaded {count} signals (updated: {signals_data.get('updated')})")
    
    # 处理 product-tracker.html
    tracker_path = DASHBOARD_DIR / "product-tracker.html"
    if tracker_path.exists():
        with open(tracker_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = inject_into_tracker_html(html, signals_data)
        with open(tracker_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Updated product-tracker.html")
    
    # 处理 mcp-ecosystem-monitor.html
    mcp_path = DASHBOARD_DIR / "mcp-ecosystem-monitor.html"
    if mcp_path.exists():
        with open(mcp_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = inject_into_mcp_monitor_html(html, signals_data)
        with open(mcp_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Updated mcp-ecosystem-monitor.html")
    
    # 生成摘要 JSON (供 index.html 读取)
    digest = {
        "updated": signals_data.get("updated", TODAY),
        "total_signals": count,
        "top_stories": signals_data.get("signals", [])[:10],
        "by_type": {},
    }
    for s in signals_data.get("signals", []):
        t = s.get("type","other")
        digest["by_type"][t] = digest["by_type"].get(t,0) + 1
    
    with open(DASHBOARD_DIR / "digest.json", "w", encoding="utf-8") as f:
        json.dump(digest, f, ensure_ascii=False, indent=2)
    print(f"✅ Written digest.json")

if __name__ == "__main__":
    main()
