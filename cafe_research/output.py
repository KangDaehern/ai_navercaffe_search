"""Report and raw data persistence."""

import json
import re
import time
from dataclasses import asdict
from pathlib import Path
from .models import CafePost

def _base_name(query: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", query).strip("_")[:40] or "search"
    return f"{time.strftime('%Y%m%d-%H%M%S')}-{safe}"

def write_results(directory: Path, query: str, cafe_url: str,
                  posts: list[CafePost], report: str) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    base = _base_name(query)
    md_path, json_path = directory / f"{base}.md", directory / f"{base}.json"
    header = (f"# 네이버 카페 조사: {query}\n\n- 카페: {cafe_url}\n"
              f"- 수집 글 수: {len(posts)}\n- 생성 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    md_path.write_text(header + report + "\n", encoding="utf-8")
    data = {"query": query, "cafe_url": cafe_url, "posts": [asdict(post) for post in posts]}
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path
