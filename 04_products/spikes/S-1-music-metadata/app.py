"""Streamlit デモ UI。

ヒアリング時にシャチョーが画面共有する前提の構成:
- 左カラム: 入力（音声 + テキスト）
- 右カラム: 結果（統合メタデータ表 + 3 ストア CSV + サマリ）
- 上部に「通常 30-60 分 → XX 秒」を大きく表示（"払いたい意思" を引き出すフック）

起動:
    streamlit run app.py
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from lib.audio import extract_audio_info
from lib.generator import generate_metadata
from lib.stores import STORE_NAMES, format_store_csv

load_dotenv()

SAMPLE_DIR = Path(__file__).parent / "sample_data"

st.set_page_config(
    page_title="楽曲メタデータ AI (S-1 MVP)",
    page_icon="🎵",
    layout="wide",
)

st.title("🎵 楽曲メタデータ AI")
st.caption(
    "1 曲 30-60 分のメタデータ整理を、AI が数秒で。"
    " 各配信ストア向け CSV まで自動生成します。"
)

# モード表示
dummy_mode = os.getenv("DUMMY_MODE", "false").lower() == "true"
api_key_present = bool(os.getenv("ANTHROPIC_API_KEY"))
if dummy_mode:
    st.info("**ダミーモード**: 固定サンプルを返します（API キー不要）", icon="🧪")
elif not api_key_present:
    st.warning(
        "ANTHROPIC_API_KEY が未設定です。.env を作成するか、"
        "DUMMY_MODE=true で起動してください。",
        icon="⚠️",
    )
else:
    st.success("**本番モード**: Claude API を使用します", icon="✅")

left, right = st.columns([1, 1])

# ─────────────────────────────────────────
# 左カラム: 入力
# ─────────────────────────────────────────
with left:
    st.subheader("1. 楽曲ファイル")

    use_dummy_audio = st.checkbox(
        "ダミー音声情報を使う（実ファイルなし）",
        value=True,
        help="ヒアリングでは実ファイルを差し替えてください",
    )

    audio_info = None
    if use_dummy_audio:
        dummy_path = SAMPLE_DIR / "dummy_audio_info.json"
        audio_info = extract_audio_info(dummy_path)
        st.json(audio_info, expanded=False)
    else:
        uploaded = st.file_uploader(
            "wav / mp3 / flac / m4a",
            type=["wav", "mp3", "flac", "m4a"],
        )
        if uploaded is not None:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{uploaded.name.split('.')[-1]}"
            ) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            try:
                audio_info = extract_audio_info(tmp_path)
                st.json(audio_info, expanded=False)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    st.subheader("2. ユーザー入力テキスト")

    # ダミーフォームからプリフィル
    with (SAMPLE_DIR / "dummy_metadata_input.json").open(encoding="utf-8") as f:
        defaults = json.load(f)

    title = st.text_input("曲タイトル", value=defaults["title"])
    artist = st.text_input("アーティスト名", value=defaults["artist"])
    genre_hint = st.text_input("ジャンルヒント", value=defaults["genre_hint"])
    mood = st.text_area("雰囲気・情景", value=defaults["mood"], height=80)
    col_a, col_b = st.columns(2)
    with col_a:
        release_date = st.text_input(
            "リリース予定日", value=defaults["release_date_planned"]
        )
        language = st.text_input("歌詞言語 (ISO 639-1)", value=defaults["language_of_lyrics"])
    with col_b:
        composer = st.text_input("作曲", value=defaults["composer"])
        lyricist = st.text_input("作詞", value=defaults["lyricist"])
    vocalist = st.text_input("ボーカル", value=defaults["vocalist"])
    lyrics_origin = st.selectbox(
        "歌詞の出所",
        options=["original", "cover_with_permission", "public_domain", "unknown"],
        index=0,
    )
    notes = st.text_area("補足メモ", value=defaults["notes"], height=80)

    metadata_input = {
        "title": title,
        "artist": artist,
        "genre_hint": genre_hint,
        "mood": mood,
        "release_date_planned": release_date,
        "language_of_lyrics": language,
        "composer": composer,
        "lyricist": lyricist,
        "vocalist": vocalist,
        "lyrics_origin": lyrics_origin,
        "notes": notes,
    }

    run = st.button(
        "🚀 メタデータを生成",
        type="primary",
        use_container_width=True,
        disabled=audio_info is None,
    )

# ─────────────────────────────────────────
# 右カラム: 結果
# ─────────────────────────────────────────
with right:
    st.subheader("生成結果")

    if not run:
        st.info("左側で入力を完了して「メタデータを生成」を押してください。")
    else:
        try:
            with st.spinner("Claude にメタデータを生成依頼中..."):
                result, stats = generate_metadata(audio_info, metadata_input)
        except Exception as e:  # noqa: BLE001 — MVP の素朴さを優先
            st.error(f"生成失敗: {e}")
            st.stop()

        # ─ 価値提示（ヒアリングの主役）
        elapsed = stats["elapsed_seconds"]
        manual_minutes = 45  # 30-60 分の中央値
        manual_seconds = manual_minutes * 60
        saved_pct = round((1 - elapsed / manual_seconds) * 100, 1)
        st.markdown(
            f"### 通常 **{manual_minutes} 分** → 今回 **{elapsed:.1f} 秒** "
            f"（**{saved_pct}%** 削減）"
        )
        st.caption(
            f"mode={stats['mode']} / model={stats['model']}"
            + (
                f" / input={stats['input_tokens']} tok"
                f" / output={stats['output_tokens']} tok"
                f" / cache_read={stats.get('cache_read_input_tokens', 0)}"
                if stats.get("input_tokens") is not None
                else ""
            )
        )

        # ─ 統合メタデータ
        st.markdown("#### 統合メタデータ")
        st.json(result.get("metadata", {}))

        # ─ ストア別 CSV
        st.markdown("#### 各配信ストア向け CSV")
        tabs = st.tabs(["Spotify for Artists", "TuneCore Japan", "DistroKid"])
        payloads = result.get("store_payloads", {})
        for tab, store in zip(tabs, STORE_NAMES):
            with tab:
                if store in payloads:
                    csv_text = format_store_csv(payloads[store])
                    st.code(csv_text, language="csv")
                    st.download_button(
                        label=f"📥 {store}.csv をダウンロード",
                        data=csv_text,
                        file_name=f"{store}.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning(f"{store} のペイロードが生成されませんでした")

        # ─ サマリ
        st.markdown("#### クリエイター向けサマリ")
        st.success(result.get("summary", "(サマリなし)"))
