"""CLI エントリポイント。

使い方:
    python cli.py sample_data/dummy_game.json sample_data/screenshots
    python cli.py sample_data/dummy_game.json sample_data/screenshots --json
    DUMMY_MODE=true python cli.py sample_data/dummy_game.json sample_data/screenshots
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from lib.generator import GameInfo, generate_all, is_dummy_mode
from lib.output import to_json, to_markdown
from lib.screenshots import load_screenshots


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Steam ストア最適化 MVP (S-2 spike)"
    )
    parser.add_argument(
        "game_info_json",
        help="ゲーム情報 JSON ファイル (sample_data/dummy_game.json)",
    )
    parser.add_argument(
        "screenshots_source",
        help="スクショ説明 JSON または画像ディレクトリ (sample_data/screenshots)",
    )
    parser.add_argument(
        "--json", action="store_true", help="JSON で出力（既定: Markdown）"
    )
    parser.add_argument(
        "--output", "-o", help="出力ファイル（指定なければ stdout）"
    )
    args = parser.parse_args()

    game_info_path = Path(args.game_info_json)
    if not game_info_path.exists():
        print(f"[ERROR] game info ファイルが見つかりません: {game_info_path}", file=sys.stderr)
        return 1

    screenshots_path = Path(args.screenshots_source)
    if not screenshots_path.exists():
        print(f"[ERROR] screenshots パスが見つかりません: {screenshots_path}", file=sys.stderr)
        return 1

    data = json.loads(game_info_path.read_text(encoding="utf-8"))
    game_info = GameInfo(
        title=data["title"],
        genre=data["genre"],
        core_mechanics=data["core_mechanics"],
        target_audience=data["target_audience"],
        developer_intro=data["developer_intro"],
        release_date=data["release_date"],
        existing_store_url=data.get("existing_store_url"),
    )

    screenshots = load_screenshots(screenshots_path)

    mode_label = "[DUMMY MODE]" if is_dummy_mode() else "[LIVE API]"
    print(f"{mode_label} ゲーム: {game_info.title} / スクショ {len(screenshots)} 枚で生成中...", file=sys.stderr)

    result = generate_all(game_info, screenshots)

    output = to_json(result) if args.json else to_markdown(result, game_info.title)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"出力先: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
