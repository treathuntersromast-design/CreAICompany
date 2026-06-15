"""Claude API でメタデータを生成する。

- system プロンプトに metadata_prompt.md を載せ、cache_control で再利用を効かせる
  （複数曲を連続処理する想定。同一プロンプト → キャッシュヒット）
- DUMMY_MODE=true の場合は固定サンプルを返し、API キー無しでも動作確認できる
- モデルは claude-sonnet-4-6 を既定。コスト優先なら claude-haiku-4-5 に切替可
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

# プロンプト本体は外出し（運用中の改善サイクルを切り離すため）
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "metadata_prompt.md"
DUMMY_SAMPLE_PATH = Path(__file__).parent.parent / "sample_data" / "expected_output_sample.json"

# 切替したい場合: "claude-haiku-4-5" にすると 1/3 程度のコスト
MODEL = "claude-sonnet-4-6"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _load_dummy_output() -> dict[str, Any]:
    with DUMMY_SAMPLE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _build_user_message(audio_info: dict, metadata_input: dict) -> str:
    return (
        "以下の楽曲情報からメタデータを生成してください。\n\n"
        "## 音声ファイル情報\n"
        f"```json\n{json.dumps(audio_info, ensure_ascii=False, indent=2)}\n```\n\n"
        "## ユーザー入力\n"
        f"```json\n{json.dumps(metadata_input, ensure_ascii=False, indent=2)}\n```\n"
    )


def generate_metadata(
    audio_info: dict,
    metadata_input: dict,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """メタデータ生成。

    Returns:
        (生成結果 dict, 実行統計 dict)
        統計には経過時間・モード・トークン使用量を含む
    """
    started = time.perf_counter()

    if os.getenv("DUMMY_MODE", "false").lower() == "true":
        # 体感を出すための擬似ウェイト（実 API も数秒かかるため）
        time.sleep(1.5)
        result = _load_dummy_output()
        elapsed = time.perf_counter() - started
        return result, {
            "mode": "dummy",
            "elapsed_seconds": round(elapsed, 2),
            "model": "(dummy)",
            "input_tokens": None,
            "output_tokens": None,
            "cache_read_input_tokens": None,
        }

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY が未設定です。.env を作成するか DUMMY_MODE=true で起動してください。"
        )

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _load_system_prompt()

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                # 同じ system プロンプトで複数曲を処理する想定なのでキャッシュを効かせる
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": _build_user_message(audio_info, metadata_input),
            }
        ],
    )

    elapsed = time.perf_counter() - started

    # text ブロックのみ抽出（thinking ブロック等が混ざる可能性に備える）
    text = next((b.text for b in response.content if b.type == "text"), "")
    result = _parse_json_response(text)

    return result, {
        "mode": "live",
        "elapsed_seconds": round(elapsed, 2),
        "model": MODEL,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
        "cache_creation_input_tokens": getattr(
            response.usage, "cache_creation_input_tokens", 0
        ),
    }


def _parse_json_response(text: str) -> dict[str, Any]:
    """Claude が ```json フェンスを付ける場合に備えて両対応で剥がす。"""
    stripped = text.strip()
    if stripped.startswith("```"):
        # ```json\n...\n``` を剥がす
        lines = stripped.split("\n")
        # 先頭の ``` 行と末尾の ``` 行を除去
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines)

    return json.loads(stripped)
