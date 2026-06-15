# S-1: 楽曲メタデータ整理 MVP

> ⚠️ **これはスパイク MVP です。本番運用は想定していません。**
> 目的は完成度評価ではなく、5 名のクリエイターヒアリング（2026-06-16 〜 06-29）で
> 「**払いたい意思**」を測ること。MVP は道具に過ぎません。

## 何が動くか

楽曲ファイル（または音声情報の JSON）と簡易テキストを入力すると、Claude が以下を生成します:

1. **統合メタデータ表**（タイトル / ISRC プレースホルダ / ジャンル / 雰囲気タグ / BPM / クレジット / 著作権表示 / 歌詞ライセンス区分 等）
2. **配信ストア向け CSV ペイロード 3 種**（Spotify for Artists / TuneCore Japan / DistroKid）
3. **顧客提示用サマリ**（「通常 30-60 分 → 今回 XX 秒」の価値訴求）

## セットアップ

```sh
cd 04_products/spikes/S-1-music-metadata
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定
# API キーが無くてもデモは動く: DUMMY_MODE=true に設定
```

## 実行方法

### Streamlit UI（ヒアリングで使う本命）

```sh
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開く。左カラムで入力、右カラムで結果確認。

### CLI（バッチ検証用）

```sh
python cli.py sample_data/dummy_audio_info.json sample_data/dummy_metadata_input.json --out ./output
```

### ダミーモードでの動作確認（API キー不要）

```sh
# Windows PowerShell
$env:DUMMY_MODE = "true"
streamlit run app.py

# Bash
DUMMY_MODE=true streamlit run app.py
```

`sample_data/expected_output_sample.json` を固定で返す。UI 全体の動作確認・スクリーンショット取得に便利。

## 想定デモシナリオ

[demo_scenario.md](./demo_scenario.md) を参照。5 分のタイムテーブルと、避けるべきアンチパターンを記載。

## ディレクトリ構造

```
S-1-music-metadata/
├── README.md                    # 本ファイル
├── demo_scenario.md             # ヒアリング 5 分デモ台本
├── requirements.txt
├── .env.example
├── .gitignore
├── cli.py                       # CLI エントリポイント
├── app.py                       # Streamlit デモ UI
├── lib/
│   ├── audio.py                 # 音声ファイル解析 (mutagen)
│   ├── generator.py             # Claude API 呼び出し
│   └── stores.py                # 配信ストア CSV 整形
├── prompts/
│   └── metadata_prompt.md       # メタデータ生成プロンプト本体
└── sample_data/
    ├── dummy_audio_info.json    # ダミー音声情報
    ├── dummy_metadata_input.json # ダミーユーザー入力
    ├── expected_output_sample.json  # ダミーモード時の固定出力
    └── expected_output_sample.md    # before/after 比較資料
```

## 技術スタック

- Python 3.10+
- `anthropic` SDK（モデル: `claude-sonnet-4-6` / `lib/generator.py` の `MODEL` で `claude-haiku-4-5` に切替可）
- `streamlit`（デモ UI）
- `mutagen`（音声ファイル解析）
- プロンプトキャッシュ: system プロンプトに `cache_control: ephemeral` を付与し、複数曲連続処理時のコストを削減

## 対象外（このスパイクではやらない）

- 認証 / 課金
- データベース永続化
- 本番デプロイ
- 詳細な音声解析（BPM 自動検出、キー検出等）
- 各配信ストア API への直接ポスト

## 関連ドキュメント

- スパイク定義: [spike-S-1-music-metadata.md](../../ideas/spike-S-1-music-metadata.md)
- ドメイン候補比較: [2026-06-15-domain-candidates.md](../../ideas/2026-06-15-domain-candidates.md)
- 決議: D-008（[01_board/decisions.md](../../../01_board/decisions.md)）

---

## CTO 自己批判

スパイク完了報告時に必ず読み返すこと。**この欠点を理解した上でヒアリングに臨むこと**。

### 1. ヒアリングで露呈する弱点（最低 3 つ）

#### 弱点 A: 「実音源を入れない」のがバレる
本 MVP は wav/mp3 を受け付けるが、**音声解析は mutagen で長さ・サンプリングレートを抜くだけ**。BPM もキーも歌詞も内部では一切見ていない。実際の生成判断は「ユーザーが入力したテキスト」のみに依存している。鋭いクリエイターは「結局自分が入力した情報を整形してるだけでは？」と気づく。**この問いに正直に答える準備が必要**（答え: その通り、Phase 1 はそれで十分価値があるという仮説の検証）。

#### 弱点 B: 各ストアの実フィールドが正確ではない
Spotify for Artists / TuneCore Japan / DistroKid の CSV ヘッダは「それらしい構造」であって、各サービスの実フォーマットと完全一致していない。実際にコピペして使おうとすると弾かれる可能性が高い。「これそのまま貼れますか？」と聞かれたら **本番化で正式対応する旨を即答** し、Phase 2 のスコープに移す必要がある。

#### 弱点 C: ジャンル/雰囲気タグの品質はモデル任せ
プロンプトに細かいガイドラインを書いていないため、Claude が生成するジャンルタグの粒度・選定根拠は不安定。同じ曲を 2 回投げると違う結果になる可能性がある（実際 5 名連続で見せると 5 名とも違う結果を見せることになる）。クリエイターは「**自分のジャンル感**」に強いこだわりを持つ層なので、ここで「**これは違う**」と言われた時の説得材料が薄い。再現性が低いのはバリュー「再現性 > 一回性のうまさ」に反する。

### 2. 2 週間で間に合わなかった機能と、それで問題ない理由

- **歌詞解析 / メタタグへの反映**: 歌詞の言語自動判定や explicit 判定を歌詞テキストから自動抽出する機能。ヒアリングでは「歌詞をどう扱うか」自体が論点になり得るため、まず空欄で見せて「歌詞をどう投入したいか」を相手に聞くほうが学習量が多い。
- **複数曲一括処理 / アルバム単位の整合チェック**: アルバムリリース時の曲順・ISRC 採番管理など。インディー層は シングル中心で「アルバム機能は将来のニーズ」。最初の 5 名で需要が確認できてから作るのが順序として正しい。
- **既存 DAW プロジェクトからの自動取り込み**: Logic / Cubase / FL Studio などからメタ情報を直接吸い出すコネクタ。実装コストが大きく、しかも DAW ごとに別実装が必要。本当に必要かはヒアリングで確かめてからで遅くない。
- **音声波形からの BPM / キー自動検出**: `librosa` 等で技術的に可能だが、計算コスト・パッケージ重さ・精度ばらつきを考えると、テキスト入力で BPM を聞けば 5 秒で済む話。「払う動機」がそこに依存しないなら遅延実装で問題ない。

### 3. 本格化したらどう作り直すか

ドメイン本確定（2026-07-13）後、5 名中 3 名以上で「払う」が出た場合の本格化方針: まず**マルチテナント Web SaaS** として再構築する（FastAPI + PostgreSQL + Auth0 + Stripe）。各配信ストアの実フォーマットを 1 つずつ正確に対応し、特に Spotify for Artists / TuneCore Japan の 2 つはコピペ可能な精度を保証する。プロンプト層は「ユーザーが過去に作ったメタデータ」を few-shot で読み込ませることでジャンルタグの個人最適化を実現する（=再現性の担保）。技術負債としては、本 MVP の「Claude 1 回呼ぶだけ」の構造から、「タグ候補生成 → ユーザー選択 → ストア別整形」の 3 段パイプラインに作り直す必要がある（現状の単発呼び出しは Phase 0 の検証用に過ぎない）。月額 （非公開）〜3,000 の SaaS として、最低 50 名 / 月（MRR （非公開）K-150K）を 6 ヶ月以内に到達できなければ撤退基準とする。
