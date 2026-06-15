"""CLI エントリポイント。

使用例:
    python cli.py sample_data/dummy_audio_info.json sample_data/dummy_metadata_input.json
    python cli.py path/to/track.wav path/to/input.json --out ./out

DUMMY_MODE=true で起動すれば API キー無しでも動く。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from lib.audio import extract_audio_info
from lib.generator import generate_metadata
from lib.stores import write_all_stores


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="楽曲メタデータ生成 MVP (S-1)",
    )
    parser.add_argument(
        "audio",
        type=str,
        help="音声ファイル (wav/mp3/flac/m4a) または dummy_audio_info.json",
    )
    parser.add_argument(
        "metadata_input",
        type=str,
        help="ユーザー入力テキストの JSON ファイル",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="./output",
        help="CSV 出力ディレクトリ (default: ./output)",
    )
    args = parser.parse_args()

    audio_info = extract_audio_info(args.audio)
    with Path(args.metadata_input).open(encoding="utf-8") as f:
        metadata_input = json.load(f)

    print(f"[*] 音声情報: {audio_info.get('filename')} ({audio_info.get('duration_seconds')}s)")
    print("[*] Claude にメタデータ生成を依頼中...")

    result, stats = generate_metadata(audio_info, metadata_input)

    print(f"[+] 完了 ({stats['elapsed_seconds']}s, mode={stats['mode']}, model={stats['model']})")
    if stats.get("input_tokens") is not None:
        print(
            f"    トークン: input={stats['input_tokens']} "
            f"output={stats['output_tokens']} "
            f"cache_read={stats.get('cache_read_input_tokens', 0)}"
        )

    written = write_all_stores(result, args.out)
    out_dir = Path(args.out)
    metadata_path = out_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n[+] 統合メタデータ: {metadata_path}")
    for store, path in written.items():
        print(f"[+] {store}: {path}")

    print("\n--- クリエイター向けサマリ ---")
    print(result.get("summary", "(サマリなし)"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
