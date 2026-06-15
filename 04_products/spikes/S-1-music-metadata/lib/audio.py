"""音声ファイルの最小限の解析。

MVP では BPM 検出やキー解析は行わない。
- 実ファイル: mutagen でファイル名・長さ・サンプリングレート・ビットレートを取得
- ダミー入力: sample_data/dummy_audio_info.json があればそれを返す

ヒアリング時の実音源差し替えを意識し、入出力を JSON 互換 dict に統一する。
"""

from __future__ import annotations

import json
from pathlib import Path


def extract_audio_info(audio_path: str | Path) -> dict:
    """音声ファイルから最小限のメタ情報を抽出する。

    .json を渡した場合はダミー入力モードとして中身をそのまま返す
    （API キー無しでもデモ全体が回るようにするため）。
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"音声ファイルが見つかりません: {path}")

    # ダミー入力モード
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    # 実ファイル解析（mutagen は wav/mp3/flac/m4a 等を扱える）
    from mutagen import File as MutagenFile  # type: ignore[import-untyped]

    audio = MutagenFile(str(path))
    if audio is None:
        # mutagen が認識できなくてもファイル名等は返せる
        return {
            "filename": path.name,
            "file_size_bytes": path.stat().st_size,
            "duration_seconds": None,
            "sample_rate_hz": None,
            "bitrate_kbps": None,
            "channels": None,
            "format": path.suffix.lstrip("."),
        }

    info = audio.info
    return {
        "filename": path.name,
        "file_size_bytes": path.stat().st_size,
        "duration_seconds": round(getattr(info, "length", 0) or 0, 2),
        "sample_rate_hz": getattr(info, "sample_rate", None),
        "bitrate_kbps": (
            round(getattr(info, "bitrate", 0) / 1000)
            if getattr(info, "bitrate", None)
            else None
        ),
        "channels": getattr(info, "channels", None),
        "format": path.suffix.lstrip("."),
    }
