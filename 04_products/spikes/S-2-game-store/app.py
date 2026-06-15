"""Streamlit デモ UI。

起動: streamlit run app.py
ダミーモード: DUMMY_MODE=true streamlit run app.py
"""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from lib.generator import GameInfo, generate_all, is_dummy_mode
from lib.output import LANG_LABELS, to_json, to_markdown
from lib.screenshots import Screenshot, load_screenshots

load_dotenv()

st.set_page_config(
    page_title="Steam ストア最適化 MVP (S-2)",
    layout="wide",
)

st.title("Steam ストア最適化 MVP")
st.caption("スパイク S-2 / CreAICompany")

if is_dummy_mode():
    st.info(
        "**DUMMY MODE で起動中**: Claude API は呼びません。固定サンプルが返ります。"
        "実 API を使うには `.env` の `DUMMY_MODE=false` + `ANTHROPIC_API_KEY` 設定。"
    )

# --- 入力 ---------------------------------------------------------------------

with st.sidebar:
    st.header("ゲーム情報")

    # サンプルプリロード
    sample_path = Path("sample_data/dummy_game.json")
    sample_defaults = {}
    if sample_path.exists():
        sample_defaults = json.loads(sample_path.read_text(encoding="utf-8"))
        if st.button("サンプルをロード"):
            for k, v in sample_defaults.items():
                st.session_state[f"input_{k}"] = v or ""
            st.rerun()

    title = st.text_input(
        "タイトル", value=st.session_state.get("input_title", ""), key="input_title"
    )
    genre = st.text_input(
        "ジャンル", value=st.session_state.get("input_genre", ""), key="input_genre"
    )
    core_mechanics = st.text_area(
        "コアメカニクス",
        value=st.session_state.get("input_core_mechanics", ""),
        key="input_core_mechanics",
        height=100,
    )
    target_audience = st.text_input(
        "ターゲット層",
        value=st.session_state.get("input_target_audience", ""),
        key="input_target_audience",
    )
    developer_intro = st.text_area(
        "開発者紹介",
        value=st.session_state.get("input_developer_intro", ""),
        key="input_developer_intro",
        height=80,
    )
    release_date = st.text_input(
        "リリース予定日",
        value=st.session_state.get("input_release_date", ""),
        key="input_release_date",
    )
    existing_store_url = st.text_input(
        "既存ストア URL（任意）",
        value=st.session_state.get("input_existing_store_url", "") or "",
        key="input_existing_store_url",
    )

    st.header("スクリーンショット")
    use_sample_screenshots = st.checkbox("サンプル説明テキストを使う", value=True)
    uploaded_files = st.file_uploader(
        "画像をアップロード（任意・Vision に投げる）",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    run_button = st.button("生成", type="primary", use_container_width=True)

# --- 生成 ---------------------------------------------------------------------

if run_button:
    if not title:
        st.error("タイトルは必須です。")
        st.stop()

    game_info = GameInfo(
        title=title,
        genre=genre,
        core_mechanics=core_mechanics,
        target_audience=target_audience,
        developer_intro=developer_intro,
        release_date=release_date,
        existing_store_url=existing_store_url or None,
    )

    screenshots: list[Screenshot] = []
    if use_sample_screenshots:
        sample_dir = Path("sample_data/screenshots")
        if sample_dir.exists():
            screenshots.extend(load_screenshots(sample_dir))

    if uploaded_files:
        for i, f in enumerate(uploaded_files):
            data = base64.standard_b64encode(f.read()).decode("utf-8")
            media_type, _ = mimetypes.guess_type(f.name)
            screenshots.append(
                Screenshot(
                    screenshot_id=f"upload_{i+1:03d}",
                    description=f"ユーザーアップロード: {f.name}",
                    media_type=media_type or "image/png",
                    base64_data=data,
                )
            )

    with st.spinner("生成中（4 タスク並列実行）..."):
        try:
            result = generate_all(game_info, screenshots)
        except Exception as e:
            st.error(f"生成エラー: {e}")
            st.stop()

    st.session_state["last_result"] = result
    st.session_state["last_title"] = game_info.title

# --- 結果表示 -----------------------------------------------------------------

result = st.session_state.get("last_result")
if result is None:
    st.write("左サイドバーでゲーム情報を入力し、「生成」を押してください。")
    st.write("（サンプルをロードするボタンで Lumencraft Echo のダミーデータが入ります）")
else:
    game_title = st.session_state.get("last_title", "")

    tab_desc, tab_tags, tab_layout, tab_trailer, tab_raw = st.tabs(
        ["説明文", "タグ", "スクショ配置", "トレーラー", "Raw JSON"]
    )

    with tab_desc:
        st.subheader("ストア説明文（5 言語）")
        desc = result.descriptions
        if isinstance(desc, dict) and "descriptions" in desc:
            for lang, label in LANG_LABELS.items():
                block = desc["descriptions"].get(lang)
                if not block:
                    continue
                with st.expander(f"{label} ({lang})", expanded=(lang == "ja")):
                    st.markdown("**Short Description**")
                    st.code(block.get("short", ""), language=None)
                    st.markdown("**About This Game**")
                    st.markdown(block.get("long", ""))
        else:
            st.code(str(desc))

    with tab_tags:
        st.subheader("Steam タグ推奨（最大 20、優先順位付き）")
        if isinstance(result.tags, dict) and "tags" in result.tags:
            st.table(
                [
                    {"順位": t.get("rank"), "タグ": t.get("tag"), "理由": t.get("reason")}
                    for t in result.tags["tags"]
                ]
            )
        else:
            st.code(str(result.tags))

    with tab_layout:
        st.subheader("スクリーンショット配置案")
        if isinstance(result.layout, dict) and "layout" in result.layout:
            st.table(
                [
                    {
                        "順序": item.get("order"),
                        "スクショ": item.get("screenshot_id"),
                        "役割": item.get("role"),
                        "理由": item.get("reason"),
                    }
                    for item in result.layout["layout"]
                ]
            )
            advice = result.layout.get("general_advice")
            if advice:
                st.info(f"**全体アドバイス:** {advice}")
        else:
            st.code(str(result.layout))

    with tab_trailer:
        st.subheader("トレーラー台本")
        trailer = result.trailer
        if isinstance(trailer, dict):
            for key, label in [("trailer_30s", "30 秒版"), ("trailer_60s", "60 秒版")]:
                v = trailer.get(key)
                if not v:
                    continue
                with st.expander(label, expanded=True):
                    st.markdown(f"**BGM 方針:** {v.get('bgm_direction', '')}")
                    st.table(
                        [
                            {
                                "時間": shot.get("time_range"),
                                "画面": shot.get("visual"),
                                "テキスト": shot.get("text_overlay") or "—",
                                "ナレーション": shot.get("narration") or "—",
                            }
                            for shot in v.get("shots", [])
                        ]
                    )
            hooks = trailer.get("wishlist_hooks", [])
            if hooks:
                st.markdown("**ウィッシュリスト訴求ポイント**")
                for h in hooks:
                    st.markdown(f"- {h}")
        else:
            st.code(str(trailer))

    with tab_raw:
        st.subheader("Raw JSON / Markdown ダウンロード")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Markdown でダウンロード",
                data=to_markdown(result, game_title),
                file_name=f"{game_title or 'output'}_store.md",
                mime="text/markdown",
            )
        with col2:
            st.download_button(
                "JSON でダウンロード",
                data=to_json(result),
                file_name=f"{game_title or 'output'}_store.json",
                mime="application/json",
            )
        with st.expander("Raw JSON プレビュー"):
            st.code(to_json(result), language="json")
