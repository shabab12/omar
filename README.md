# Miniflux MCP

خادم MCP يربط نسخة Miniflux الخاصة بك مع Claude.

## التثبيت

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

من Miniflux: Settings ← API Keys ← Create a new API key.

## Claude Code

```bash
claude mcp add miniflux \
  -e MINIFLUX_URL=https://rss.example.com \
  -e MINIFLUX_API_KEY=your_key \
  -- /absolute/path/to/.venv/bin/python /absolute/path/to/server.py
```

## Claude Desktop

أضف إلى `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "miniflux": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "MINIFLUX_URL": "https://rss.example.com",
        "MINIFLUX_API_KEY": "your_key"
      }
    }
  }
}
```

## الأدوات

| الأداة | وظيفتها |
|---|---|
| `list_entries` | المقالات (غير المقروءة افتراضيًا) مع بحث وفلترة بالتصنيف أو المصدر |
| `get_entry` | نص مقال كامل |
| `mark_entries` | وسم مقالات كمقروءة / غير مقروءة / محذوفة |
| `toggle_star` | تمييز مقال بنجمة |
| `list_feeds` / `list_categories` | المصادر والتصنيفات مع عدد غير المقروء |
| `add_feed` | اشتراك في مصدر جديد |
| `refresh_all_feeds` | تحديث كل المصادر |

## أمثلة على الطلب

- "لخّص لي غير المقروء في تصنيف التقنية، وأعطني أهم ثلاثة"
- "ابحث في Miniflux عن مقالات عن التوظيف وصنفها حسب الفكرة"
- "علّم كل ما هو أقدم من أسبوع كمقروء"
