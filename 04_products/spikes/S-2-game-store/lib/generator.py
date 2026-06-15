"""Claude API を呼び出して 4 タスク（説明文・タグ・配置案・トレーラー台本）を生成する。

設計:
- 4 タスクは独立なので asyncio.gather で並列実行
- ゲーム情報（システム共通部）に cache_control を付け、4 タスク間でキャッシュ共有
- ダミーモード時は固定サンプルを返し、API キー無しでも UI が触れる
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from anthropic import AsyncAnthropic

from .screenshots import Screenshot

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8192
PROMPT_DIR = Path(__file__).parent.parent / "prompts"


@dataclass
class GameInfo:
    """ゲーム情報入力。"""

    title: str
    genre: str
    core_mechanics: str
    target_audience: str
    developer_intro: str
    release_date: str
    existing_store_url: Optional[str] = None

    def to_block(self) -> str:
        return (
            f"- タイトル: {self.title}\n"
            f"- ジャンル: {self.genre}\n"
            f"- コアメカニクス: {self.core_mechanics}\n"
            f"- ターゲット層: {self.target_audience}\n"
            f"- 開発者紹介: {self.developer_intro}\n"
            f"- リリース予定日: {self.release_date}"
        )


@dataclass
class GenerationResult:
    """4 タスクの結果。各値は dict（JSON パース済）または str（パース失敗時生テキスト）。"""

    descriptions: Any
    tags: Any
    layout: Any
    trailer: Any
    raw_responses: dict[str, str]  # デバッグ用に生レスポンスも保持


def _load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def _format_screenshots_block(screenshots: list[Screenshot]) -> str:
    if not screenshots:
        return "（スクリーンショット情報なし）"
    return "\n".join(f"- {s.to_text_summary()}" for s in screenshots)


def _build_user_blocks(
    prompt_template: str,
    game_info: GameInfo,
    screenshots: list[Screenshot],
) -> list[dict]:
    """ユーザーメッセージの content blocks を構築。

    プロンプトテンプレートにゲーム情報・URL・スクショ情報を差し込む。
    Vision 対応のため、画像データがあれば image block も追加。
    """
    existing_url_block = (
        f"参考 URL: {game_info.existing_store_url}"
        if game_info.existing_store_url
        else "（参考 URL なし）"
    )
    text = prompt_template.format(
        game_info_block=game_info.to_block(),
        existing_url_block=existing_url_block,
        screenshots_block=_format_screenshots_block(screenshots),
    )

    blocks: list[dict] = []
    for s in screenshots:
        if s.has_image():
            blocks.append(s.to_vision_block())
    blocks.append({"type": "text", "text": text})
    return blocks


def _extract_json(text: str) -> Any:
    """レスポンスから JSON ブロックを抽出してパース。

    ```json ... ``` で囲まれていればそこから、なければテキスト全体をパース。
    失敗時は元テキストを返す。
    """
    fence = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else text.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # 最初の { から最後の } までを試す
        m = re.search(r"\{.*\}", candidate, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return text  # パース失敗、生テキストを返す


async def _call_claude(
    client: AsyncAnthropic,
    system_prompt: str,
    user_blocks: list[dict],
) -> str:
    """1 タスク分の Claude 呼び出し。system にキャッシュ制御を付ける。"""
    response = await client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_blocks}],
    )
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


# ダミーモード用の固定サンプル ---------------------------------------------------

_DUMMY_DESCRIPTIONS = {
    "descriptions": {
        "ja": {
            "short": "光と闇の記憶を辿る 2D メトロイドヴァニア。失われた声を取り戻し、沈んだ王国を再構築せよ。",
            "long": "## Lumencraft Echo について\n\n**Lumencraft Echo** は、記憶を音として収集するメカニクスを核に据えた 2D メトロイドヴァニアです。プレイヤーは失語の少女エコーとなり、沈んだ王国の各地に散らばった「声の欠片」を集め、世界に色と意味を取り戻していきます。\n\n## 主な特徴\n\n- **音響パズル:** ステージのギミックは音で動く。BGM とリンクしたパズルを解け\n- **声で広がる世界:** 集めた声でマップが変化。同じ場所も訪れる度に違う顔を見せる\n- **手描きアートワーク:** 全 60 種類以上のロケーション、手描きで描画\n- **無声主人公:** 表情とジェスチャーで物語る、言葉を使わない演出\n- **約 15 時間のキャンペーン + ニューゲーム+ モード**\n\n沈黙の世界に、もう一度音楽を。",
        },
        "en": {
            "short": "A 2D metroidvania where memories are music. Recover lost voices and rebuild a sunken kingdom.",
            "long": "## About Lumencraft Echo\n\n**Lumencraft Echo** is a 2D metroidvania built around a unique memory-as-sound collection mechanic. Play as Echo, a mute girl in a kingdom drowned in silence, and gather scattered 'voice fragments' to restore color, meaning, and movement to the world.\n\n## Features\n\n- **Acoustic Puzzles:** Stage mechanics respond to sound — solve puzzles synced to the soundtrack\n- **A World That Grows:** Each collected voice transforms the map. Revisiting rewards exploration\n- **Hand-Painted Art:** Over 60 unique locations, all illustrated by hand\n- **Silent Protagonist:** Storytelling through expression and gesture, without dialogue\n- **15+ hour campaign with New Game+**\n\nBring music back to a silent world.",
        },
        "zh-Hans": {
            "short": "以记忆为声的 2D 银河战士恶魔城。寻回失落的声音，重塑沉没的王国。",
            "long": "## 关于《Lumencraft Echo》\n\n**Lumencraft Echo** 是一款以「将记忆作为声音收集」为核心机制的 2D 银河战士恶魔城游戏。扮演失语少女 Echo，在被沉默淹没的王国中收集散落的「声音碎片」，重新赋予世界色彩与意义。\n\n## 主要特色\n\n- **声响谜题:** 关卡机关随声响而动\n- **声音改变世界:** 收集的声音让地图发生变化\n- **手绘美术:** 超过 60 个独特场景，全部手绘\n- **无声主角:** 通过表情与肢体讲述故事\n- **约 15 小时的剧情 + 二周目模式**",
        },
        "zh-Hant": {
            "short": "以記憶為聲的 2D 銀河戰士惡魔城。尋回失落的聲音，重塑沉沒的王國。",
            "long": "## 關於《Lumencraft Echo》\n\n**Lumencraft Echo** 是一款以「將記憶作為聲音收集」為核心機制的 2D 銀河戰士惡魔城。扮演失語少女 Echo，在被沉默淹沒的王國中收集散落的「聲音碎片」，重新賦予世界色彩與意義。\n\n## 主要特色\n\n- **聲響謎題:** 關卡機關隨聲響而動\n- **聲音改變世界:** 收集的聲音讓地圖發生變化\n- **手繪美術:** 超過 60 個獨特場景，全部手繪\n- **無聲主角:** 透過表情與肢體講述故事\n- **約 15 小時劇情 + 二週目模式**",
        },
        "ko": {
            "short": "기억을 소리로 모으는 2D 메트로배니아. 잃어버린 목소리를 되찾고 가라앉은 왕국을 다시 세우자.",
            "long": "## Lumencraft Echo 소개\n\n**Lumencraft Echo** 는 「기억을 소리로 수집」하는 메커니즘을 핵심으로 한 2D 메트로배니아예요. 침묵에 잠긴 왕국에서 실어증의 소녀 에코가 되어 흩어진 '목소리 조각'을 모으고, 세계에 색과 의미를 되돌립니다.\n\n## 주요 특징\n\n- **음향 퍼즐:** 스테이지 기믹이 사운드에 반응\n- **소리로 변하는 세계:** 모은 목소리에 따라 맵이 변화\n- **수작업 아트워크:** 60곳 이상의 로케이션을 손으로 그려냄\n- **무언의 주인공:** 표정과 몸짓으로 이야기를 전함\n- **약 15시간의 캠페인 + 뉴게임+ 모드**",
        },
    }
}

_DUMMY_TAGS = {
    "tags": [
        {"rank": 1, "tag": "Metroidvania", "reason": "コアジャンル。最重要発見導線。"},
        {"rank": 2, "tag": "2D Platformer", "reason": "広いジャンルでリーチ取り。"},
        {"rank": 3, "tag": "Atmospheric", "reason": "音響と手描きアートの強みを表現。"},
        {"rank": 4, "tag": "Hand-drawn", "reason": "アートスタイルへの直接的な発見導線。"},
        {"rank": 5, "tag": "Puzzle Platformer", "reason": "音響パズルメカニクス。"},
        {"rank": 6, "tag": "Story Rich", "reason": "失語の少女、世界復興の物語性。"},
        {"rank": 7, "tag": "Exploration", "reason": "メトロイドヴァニアの探索要素。"},
        {"rank": 8, "tag": "Singleplayer", "reason": "標準的だが必須。"},
        {"rank": 9, "tag": "Soundtrack", "reason": "音をテーマにしたゲームへの強い親和性。"},
        {"rank": 10, "tag": "Female Protagonist", "reason": "ターゲット層拡大。"},
        {"rank": 11, "tag": "Cute", "reason": "アート好きへの訴求。"},
        {"rank": 12, "tag": "Mystery", "reason": "記憶探索という物語構造。"},
        {"rank": 13, "tag": "Pixel Graphics", "reason": "（注: 実際は手描きなので外す候補）"},
        {"rank": 14, "tag": "Indie", "reason": "ベースタグ。優先度低。"},
        {"rank": 15, "tag": "Adventure", "reason": "広めの傘タグ。"},
    ]
}

_DUMMY_LAYOUT = {
    "layout": [
        {"order": 1, "screenshot_id": "dummy_001", "role": "フック", "reason": "光のエフェクトとキャラクターの後ろ姿が「これは何のゲームか」を 0.5 秒で伝える。"},
        {"order": 2, "screenshot_id": "dummy_003", "role": "メカニクス", "reason": "音響パズルの実プレイ画面。プレイヤーが「何をするゲームか」を確定できる。"},
        {"order": 3, "screenshot_id": "dummy_002", "role": "演出", "reason": "手描きアートワークの強みが最も伝わる夜景ショット。"},
        {"order": 4, "screenshot_id": "dummy_004", "role": "ストーリー", "reason": "主人公とサブキャラクターの対話シーン。物語の深さを示唆。"},
        {"order": 5, "screenshot_id": "dummy_005", "role": "プレイ感", "reason": "マップ画面で「どれだけ広いか」「どれだけ長く遊べるか」を示す。"},
    ],
    "general_advice": "全体としてフック→メカニクス→演出→物語→ボリュームの流れで、訪問者の意思決定に必要な情報が順序立てて提示される構成になっています。",
}

_DUMMY_TRAILER = {
    "trailer_30s": {
        "bgm_direction": "静寂から始まり、徐々にピアノとストリングスが重なる。終盤でリズムが入り疾走感を出す。",
        "shots": [
            {"time_range": "0:00-0:03", "visual": "真っ黒な画面に小さな光の粒。少女が振り返るシルエット。", "text_overlay": "声を、もう一度。", "narration": None},
            {"time_range": "0:03-0:10", "visual": "音響パズルを解くプレイ画面、エフェクトが連鎖する", "text_overlay": "音で世界を動かす", "narration": None},
            {"time_range": "0:10-0:20", "visual": "様々なロケーションを高速カット、手描きアートを見せる", "text_overlay": None, "narration": None},
            {"time_range": "0:20-0:27", "visual": "ボス戦の決め技シーン", "text_overlay": "沈んだ王国を、響かせろ", "narration": None},
            {"time_range": "0:27-0:30", "visual": "タイトルロゴ + リリース日", "text_overlay": "Lumencraft Echo / 2026 Q4 / ウィッシュリスト登録受付中", "narration": None},
        ],
    },
    "trailer_60s": {
        "bgm_direction": "30 秒版を拡張。中盤で音楽が一度静まり、世界観の静謐さを見せてから再び盛り上げる。",
        "shots": [
            {"time_range": "0:00-0:05", "visual": "失語の少女が初めて声の欠片に触れるシーン", "text_overlay": "声を失った少女が、王国に音を取り戻す", "narration": None},
            {"time_range": "0:05-0:15", "visual": "様々なロケーション（森・遺跡・水中都市）", "text_overlay": None, "narration": None},
            {"time_range": "0:15-0:30", "visual": "音響パズル各種を畳み掛ける", "text_overlay": "声で動く世界", "narration": None},
            {"time_range": "0:30-0:40", "visual": "サブキャラクターとの対話・サイレント演出", "text_overlay": None, "narration": None},
            {"time_range": "0:40-0:55", "visual": "ボス戦・大規模イベントシーン", "text_overlay": "沈黙の世界に、響け", "narration": None},
            {"time_range": "0:55-1:00", "visual": "タイトルロゴ + リリース日 + CTA", "text_overlay": "Lumencraft Echo / Wishlist Now", "narration": None},
        ],
    },
    "wishlist_hooks": [
        "「音で世界を動かす」音響パズル × 手描きメトロイドヴァニア",
        "セリフゼロ、表情とジェスチャーだけで紡ぐ少女の物語",
        "60 種類以上の手描きロケーション、訪れる度に変化する世界",
    ],
}


def _dummy_result() -> GenerationResult:
    return GenerationResult(
        descriptions=_DUMMY_DESCRIPTIONS,
        tags=_DUMMY_TAGS,
        layout=_DUMMY_LAYOUT,
        trailer=_DUMMY_TRAILER,
        raw_responses={
            "descriptions": "[DUMMY MODE]",
            "tags": "[DUMMY MODE]",
            "layout": "[DUMMY MODE]",
            "trailer": "[DUMMY MODE]",
        },
    )


# 公開 API ---------------------------------------------------------------------


def is_dummy_mode() -> bool:
    return os.environ.get("DUMMY_MODE", "").lower() in {"1", "true", "yes"}


async def generate_all_async(
    game_info: GameInfo,
    screenshots: list[Screenshot],
) -> GenerationResult:
    """4 タスクを並列実行して結果を返す。"""
    if is_dummy_mode():
        return _dummy_result()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY が未設定です。.env を確認するか、DUMMY_MODE=true で起動してください。"
        )

    client = AsyncAnthropic(api_key=api_key)

    prompts = {
        "descriptions": _load_prompt("description_prompt.md"),
        "tags": _load_prompt("tags_prompt.md"),
        "layout": _load_prompt("layout_prompt.md"),
        "trailer": _load_prompt("trailer_prompt.md"),
    }

    async def run_one(key: str) -> tuple[str, str]:
        system = (
            "あなたはインディーゲーム開発者を支援する Steam ストア最適化アシスタントです。"
            "与えられたプロンプトに厳密に従い、指定された JSON 構造で出力します。"
        )
        user_blocks = _build_user_blocks(prompts[key], game_info, screenshots)
        raw = await _call_claude(client, system, user_blocks)
        return key, raw

    results = await asyncio.gather(*(run_one(k) for k in prompts.keys()))
    raw_map = dict(results)

    return GenerationResult(
        descriptions=_extract_json(raw_map["descriptions"]),
        tags=_extract_json(raw_map["tags"]),
        layout=_extract_json(raw_map["layout"]),
        trailer=_extract_json(raw_map["trailer"]),
        raw_responses=raw_map,
    )


def generate_all(game_info: GameInfo, screenshots: list[Screenshot]) -> GenerationResult:
    """同期インターフェース。CLI / Streamlit から呼ぶ用。"""
    return asyncio.run(generate_all_async(game_info, screenshots))
