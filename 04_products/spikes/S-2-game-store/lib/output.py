"""GenerationResult を Markdown / JSON に整形する。"""

from __future__ import annotations

import json
from typing import Any

from .generator import GenerationResult

LANG_LABELS = {
    "ja": "日本語",
    "en": "English",
    "zh-Hans": "中文（简体）",
    "zh-Hant": "中文（繁體）",
    "ko": "한국어",
}


def to_json(result: GenerationResult) -> str:
    return json.dumps(
        {
            "descriptions": result.descriptions,
            "tags": result.tags,
            "layout": result.layout,
            "trailer": result.trailer,
        },
        ensure_ascii=False,
        indent=2,
    )


def _fmt_descriptions(desc: Any) -> str:
    if not isinstance(desc, dict) or "descriptions" not in desc:
        return f"```\n{desc}\n```"
    out = []
    for lang, label in LANG_LABELS.items():
        block = desc["descriptions"].get(lang)
        if not block:
            continue
        out.append(f"### {label} ({lang})\n")
        out.append("**Short Description:**\n")
        out.append(block.get("short", "（なし）"))
        out.append("\n**About This Game:**\n")
        out.append(block.get("long", "（なし）"))
        out.append("\n---\n")
    return "\n".join(out)


def _fmt_tags(tags: Any) -> str:
    if not isinstance(tags, dict) or "tags" not in tags:
        return f"```\n{tags}\n```"
    rows = ["| 順位 | タグ | 選定理由 |", "|---|---|---|"]
    for t in tags["tags"]:
        rows.append(
            f"| {t.get('rank', '?')} | `{t.get('tag', '')}` | {t.get('reason', '')} |"
        )
    return "\n".join(rows)


def _fmt_layout(layout: Any) -> str:
    if not isinstance(layout, dict) or "layout" not in layout:
        return f"```\n{layout}\n```"
    rows = ["| 順序 | スクショ ID | 役割 | 理由 |", "|---|---|---|---|"]
    for item in layout["layout"]:
        rows.append(
            f"| {item.get('order', '?')} | {item.get('screenshot_id', '')} "
            f"| {item.get('role', '')} | {item.get('reason', '')} |"
        )
    advice = layout.get("general_advice", "")
    return "\n".join(rows) + (f"\n\n**全体アドバイス:** {advice}" if advice else "")


def _fmt_trailer(trailer: Any) -> str:
    if not isinstance(trailer, dict):
        return f"```\n{trailer}\n```"
    out = []
    for variant_key, variant_label in [
        ("trailer_30s", "30 秒版"),
        ("trailer_60s", "60 秒版"),
    ]:
        v = trailer.get(variant_key)
        if not v:
            continue
        out.append(f"### {variant_label}")
        out.append(f"**BGM 方針:** {v.get('bgm_direction', '')}\n")
        out.append("| 時間 | 画面 | テキスト/字幕 | ナレーション |")
        out.append("|---|---|---|---|")
        for shot in v.get("shots", []):
            out.append(
                f"| {shot.get('time_range', '')} "
                f"| {shot.get('visual', '')} "
                f"| {shot.get('text_overlay') or '—'} "
                f"| {shot.get('narration') or '—'} |"
            )
        out.append("")
    hooks = trailer.get("wishlist_hooks", [])
    if hooks:
        out.append("### ウィッシュリスト訴求ポイント")
        for h in hooks:
            out.append(f"- {h}")
    return "\n".join(out)


def to_markdown(result: GenerationResult, game_title: str = "") -> str:
    title_line = f"# Steam ストア最適化結果: {game_title}" if game_title else "# Steam ストア最適化結果"
    sections = [
        title_line,
        "",
        "## 1. ストア説明文（多言語）",
        _fmt_descriptions(result.descriptions),
        "",
        "## 2. Steam タグ推奨",
        _fmt_tags(result.tags),
        "",
        "## 3. スクリーンショット配置案",
        _fmt_layout(result.layout),
        "",
        "## 4. トレーラー台本",
        _fmt_trailer(result.trailer),
    ]
    return "\n".join(sections)
