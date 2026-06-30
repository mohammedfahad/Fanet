#!/usr/bin/env python3
"""
Pulls recent items from a handful of AI news RSS feeds and writes them
to dispatches.json at the repo root, in the format index.html expects.

Run manually with: python scripts/update_dispatches.py
Runs automatically via .github/workflows/update-dispatches.yml
"""

import json
import re
import datetime
import html
import feedparser

# Add or remove feeds here. Each must be a standard RSS/Atom feed URL.
FEEDS = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "tag": "news"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "tag": "news"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "tag": "research"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "tag": "tool"},
]

MAX_ITEMS = 8           # how many dispatches to keep on the site
MAX_PER_FEED = 4        # cap any single feed so it can't flood the list
SUMMARY_LENGTH = 160    # characters

TAG_CLASS = {
    "news": "",
    "research": "",
    "tool": "",
    "model": "model",
}


def clean_text(raw):
    """Strip HTML tags and excess whitespace from a feed summary."""
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > SUMMARY_LENGTH:
        text = text[:SUMMARY_LENGTH].rsplit(" ", 1)[0] + "…"
    return text


def parse_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime.datetime(*value[:6], tzinfo=datetime.timezone.utc)
    return datetime.datetime.now(datetime.timezone.utc)


def main():
    items = []

    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        count = 0
        for entry in parsed.entries:
            if count >= MAX_PER_FEED:
                break
            title = clean_text(entry.get("title", "")).rstrip(".")
            summary = clean_text(entry.get("summary", "") or entry.get("description", ""))
            link = entry.get("link", "#")
            if not title or not link:
                continue
            items.append({
                "date": parse_date(entry).isoformat(),
                "tag": feed["tag"],
                "tag_class": TAG_CLASS.get(feed["tag"], ""),
                "title": title,
                "summary": summary,
                "source": feed["name"],
                "link": link,
            })
            count += 1

    # newest first, then trim
    items.sort(key=lambda x: x["date"], reverse=True)
    items = items[:MAX_ITEMS]

    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "items": items,
    }

    with open("dispatches.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(items)} dispatches to dispatches.json")


if __name__ == "__main__":
    main()
