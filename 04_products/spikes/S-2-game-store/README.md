# S-2: Steam ストア最適化 MVP

スパイク S-2（[../../ideas/spike-S-2-game-store.md](../../ideas/spike-S-2-game-store.md) / [D-008](../../../01_board/decisions.md)）の MVP プロトタイプ。

> **これはスパイク MVP であり、本番運用は想定しない。**
> 目的は「5 名のインディーゲーム開発者ヒアリングで *払いたい意思* を測ること」。

## 何が動くか

ゲーム情報 + スクリーンショット説明を入力すると、Claude API が以下 4 つを並列生成します。

1. **ストア説明文（日 / 英 / 中簡 / 中繁 / 韓 の 5 言語）** — Short Description + About This Game
2. **Steam タグ推奨**（最大 20 個 / 優先順位 + 選定理由付き）
3. **スクリーンショット配置案**（5 枚の役割ラベリング + 順序提案）
4. **トレーラー台本**（30 秒版 + 60 秒版 + ウィッシュリスト訴求 3 ポイント）

## セットアップ

### 必要なもの
- Python 3.10 以上
- Anthropic API キー（実 API モードのみ。ダミーモードなら不要）

### 手順

```bash
cd 04_products/spikes/S-2-game-store
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
copy .env.example .env    # Windows
# cp .env.example .env    # macOS / Linux
# .env を編集して ANTHROPIC_API_KEY を入れる（任意）
```

## 実行方法

### 1. CLI

```bash
# 実 API モード（要 ANTHROPIC_API_KEY）
python cli.py sample_data/dummy_game.json sample_data/screenshots

# ダミーモード（API キー不要）
# Windows PowerShell:
$env:DUMMY_MODE="true"; python cli.py sample_data/dummy_game.json sample_data/screenshots
# bash:
DUMMY_MODE=true python cli.py sample_data/dummy_game.json sample_data/screenshots

# JSON 出力
python cli.py sample_data/dummy_game.json sample_data/screenshots --json -o result.json
```

### 2. Streamlit デモ UI（ヒアリング時はこちらを使用）

```bash
streamlit run app.py
# ダミーモード:
# Windows PowerShell:
$env:DUMMY_MODE="true"; streamlit run app.py
# bash:
DUMMY_MODE=true streamlit run app.py
```

ブラウザが自動で開く（`http://localhost:8501`）。

操作:
1. 左サイドバーで「サンプルをロード」を押す（Lumencraft Echo のダミーデータが入る）
2. または直接ゲーム情報を入力
3. 必要に応じてスクショ画像をアップロード（任意）
4. 「生成」ボタン
5. タブ切り替えで結果確認

## 動作確認手順（ダミーモード）

```bash
$env:DUMMY_MODE="true"
streamlit run app.py
# → ブラウザで「サンプルをロード」→「生成」
# → 4 タブそれぞれにダミー結果が表示されることを確認
```

API キー無しで UI 全体が触れる状態になっています。ヒアリング当日に API 障害があってもダミーモードで継続可能。

## ヒアリング時のデモ

[demo_scenario.md](demo_scenario.md) を参照。5 分デモの進行台本。

## ディレクトリ構造

```
S-2-game-store/
├── README.md              # 本ファイル
├── demo_scenario.md       # ヒアリング 5 分デモ台本
├── requirements.txt
├── .env.example
├── .gitignore
├── cli.py                 # CLI エントリポイント
├── app.py                 # Streamlit デモ UI
├── lib/
│   ├── screenshots.py     # スクショ読み込み / Vision 変換
│   ├── generator.py       # Claude API 呼び出し（asyncio 並列）
│   └── output.py          # Markdown / JSON 整形
├── prompts/
│   ├── description_prompt.md
│   ├── tags_prompt.md
│   ├── layout_prompt.md
│   └── trailer_prompt.md
└── sample_data/
    ├── dummy_game.json
    ├── expected_output_sample.md
    └── screenshots/
        └── dummy_descriptions.json
```

## 技術メモ

- **モデル**: `claude-sonnet-4-6`（多言語生成の品質要求が高め）
- **並列実行**: 4 タスクを `asyncio.gather` で並列。実 API モードで合計 30-60 秒見込み
- **プロンプトキャッシュ**: system プロンプトに `cache_control` を付与。4 タスク間で共通部分をキャッシュ共有
- **Vision**: 画像があれば base64 化して image block で送信。なければスクショ説明テキストのみ使用
- **エラーハンドリング**: API キー欠落 / ファイル欠落のみ明示エラー。リトライ等は未実装

## 守っていること

- `.env`（実 API キー）はコミットしない（`.gitignore` で除外）
- 実スクショ PNG はコミットしない（`.gitignore` で除外）
- 外部送信先は Anthropic API のみ

## CTO 自己批判

### ヒアリングで露呈する弱点（3 つ）

1. **「ウィッシュリスト改善」の効果を実数値で見せられない**
   このスパイク MVP は「提案」しか出さない。実際にストアページに反映してウィッシュリスト数が増えたか、を測れるのはリリース後数週間後。ヒアリングでは「提案の質」だけしか見せられず、「払いたい」と言わせる決定打が弱い。
   - **どう補うか**: (a) 既存 Steam タイトルでの「もし当時これが使えていたら」シミュレーション形式の質問に切り替える、(b) コンバージョン率が高い既存タイトルのストアページを 1-2 個分析して「あなたのゲームと比べてここが違う」を AI に語らせる差分分析機能を追加、を検討。

2. **スクショ「配置案」が説明テキストベースで、視覚情報が薄い**
   ヒアリング時、開発者が自分のスクショを 5 枚アップロードしても、AI は Vision で「内容」までしか見ない。「このショットは構図がイマイチ」のような視覚的指摘ができない。日本語圏の開発者は「アートワーク命」の層が多いので、視覚指摘ができないのは痛い。
   - **どう補うか**: 配置案タブで「もしこのスクショを差し替えるなら、どんな構図が望ましいか」をテキストで提案させるよう、プロンプトを 1 段追加する余地あり。

3. **既存ストア URL を参考にする機能が、現状 URL 文字列だけ渡す形でスクレイピングしていない**
   「既存ストア URL」を入力欄に置いたが、実際は Claude にテキストとして渡すだけで Steam ページの実コンテンツを読み込んでいない。「既存と比較して改善」が口だけになるリスク。
   - **どう補うか**: WebFetch ツール（Claude の web_fetch）を有効化すれば対応可能だが、レート制限と Steam の robots.txt 配慮で MVP では除外した。本格化フェーズでは要対応。

### 2 週間で間に合わなかった機能と、それで問題ない理由

- **A/B テスト機能**: 「同じ入力から複数案を生成して比較できる」機能。**問題ない理由**: スパイクの問いは「払うか」であり、提案の品質を磨くフェーズではない。多変量比較は本契約後に実装すれば足りる。
- **実 Steam ページへの自動投稿 / 下書き連携**: Steamworks API 連携。**問題ない理由**: 開発者が「自分で貼り付ける」摩擦の高さがむしろ "1 回 （非公開）" の妥当性を訴求する材料になる。摩擦を残したまま価値を測る方が判断が早い。
- **画像生成 / スクショ自動修正**: 視覚的に「こうした方が良い」と画像で見せる機能。**問題ない理由**: 画像生成は Claude のスコープ外。スパイク段階ではテキスト指摘で十分意思を測れる。

### 本格化したらどう作り直すか

ヒアリングで 3 名以上「払いたい」が出た場合、本格化フェーズでは以下に作り直す。**配信プラットフォームを Streamlit から Web SaaS（Next.js + FastAPI）へ移行し、認証 / 課金（Stripe）/ 履歴保存（PostgreSQL）/ 既存 Steam ページの実スクレイピング（Vision + Web Fetch）/ A/B 案生成 / ユーザー編集後の差分追跡（リジェネ時に「ここだけ書き直して」が言える）を最初に実装する。** 多言語対応は MVP で既に検証済みなので、英語圏 itch.io 開発者プールへの展開（[D-008](../../../01_board/decisions.md) の論点）を最優先の差別化軸として English-first の UI で出す。
