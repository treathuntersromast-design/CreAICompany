"""配信ストア向け CSV 整形ユーティリティ。

generator.py の出力には既に各ストアの header/row が文字列で含まれているが、
ファイル保存や追加のクレンジングを行うためのレイヤーをここに分離する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

STORE_NAMES = ("spotify_for_artists", "tunecore_japan", "distrokid")


def format_store_csv(payload: dict[str, str]) -> str:
    """{"header": "...", "row": "..."} → CSV テキスト 2 行。"""
    header = payload.get("header", "").strip()
    row = payload.get("row", "").strip()
    return f"{header}\n{row}\n"


def write_all_stores(result: dict[str, Any], out_dir: str | Path) -> dict[str, Path]:
    """生成結果から 3 ストア分の CSV をディレクトリへ書き出す。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    payloads = result.get("store_payloads", {})
    for store in STORE_NAMES:
        if store not in payloads:
            continue
        path = out / f"{store}.csv"
        path.write_text(format_store_csv(payloads[store]), encoding="utf-8")
        written[store] = path
    return written
