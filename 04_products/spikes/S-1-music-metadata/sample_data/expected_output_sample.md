# 期待アウトプット例（ヒアリング時の before/after 比較資料）

## Before（クリエイターが手作業でやっている世界）

1 曲リリースするのに必要なメタデータ作業の典型例:

- 各ストアの管理画面に **同じ情報を 3〜4 回** 入力（Spotify for Artists / TuneCore / DistroKid / Apple Music for Artists ...）
- ジャンルタグの選定で 5〜15 分悩む（「これは Synthwave なのか Chillwave なのか」）
- クレジット表記の体裁を毎回コピペで揃える
- ISRC 採番ルールの確認
- 歌詞ライセンス区分の選択（original / cover / public_domain ...）
- ストアごとの細かいフィールド差異への対応

**合計 30〜60 分 / 曲。月 2 曲リリースなら 1〜2 時間/月。** ボカロ P やトラックメイカーは「曲を作る時間が削られる」と言う。

## After（本 MVP の出力例）

入力（クリエイターが Streamlit フォームに記入）:

```json
{
  "title": "Midnight Drive",
  "artist": "Aoi Tsukimi",
  "genre_hint": "シティポップ寄りのエレクトロニカ",
  "mood": "夜の高速道路、ネオンの残像、少しメランコリック",
  "release_date_planned": "2026-06-30",
  "language_of_lyrics": "ja",
  "composer": "Aoi Tsukimi",
  "lyricist": "Aoi Tsukimi",
  "vocalist": "Aoi Tsukimi",
  "lyrics_origin": "original",
  "notes": "ボカロではなく本人歌唱。BPMは112前後。"
}
```

出力（約 8 秒で生成）:

### 統合メタデータ表

| 項目 | 値 |
|---|---|
| タイトル | Midnight Drive |
| アーティスト | Aoi Tsukimi |
| ISRC（プレースホルダ） | JP-XXX-26-00001 |
| 主要ジャンル | Electronic |
| 補助タグ | City Pop / Synthwave / Chillwave / J-Pop |
| 雰囲気 | Nocturnal / Melancholic / Cinematic / Nostalgic |
| BPM 推定 | 112 |
| クレジット | 作詞作曲編曲歌唱: Aoi Tsukimi |
| 著作権表示 | © 2026 Aoi Tsukimi |
| 歌詞ライセンス | original |
| リリース日 | 2026-06-30 |

### Spotify for Artists 向け CSV

```csv
track_title,primary_artist,isrc,primary_genre,language,explicit,release_date
Midnight Drive,Aoi Tsukimi,JP-XXX-26-00001,Electronic,ja,false,2026-06-30
```

### TuneCore Japan 向け CSV

```csv
曲名,アーティスト名,ISRC,ジャンル,言語,クレジット,著作権表示,リリース日
Midnight Drive,Aoi Tsukimi,JP-XXX-26-00001,エレクトロニック,日本語,"作詞作曲編曲歌唱: Aoi Tsukimi",© 2026 Aoi Tsukimi,2026-06-30
```

### DistroKid 向け CSV

```csv
Track Title,Artist Name,ISRC,Genre,Subgenre,Language,Explicit,Release Date,Songwriter
Midnight Drive,Aoi Tsukimi,JP-XXX-26-00001,Electronic,Synthwave,Japanese,No,2026-06-30,Aoi Tsukimi
```

### クリエイター向けサマリ

> 通常 1 曲あたり 30〜60 分かかるメタデータ整理を、AI が約 8 秒で完了しました。ジャンルは『シティポップ寄りのエレクトロニカ』というヒントから Electronic を主軸に、City Pop / Synthwave / Chillwave を補助タグとして配置しています。雰囲気タグは『夜の高速道路、ネオン、メランコリック』を Nocturnal / Cinematic / Nostalgic に翻訳しました。
>
> **ご確認いただきたい点**:
> 1. ISRC はプレースホルダのため、ご自身で正式採番してください
> 2. クレジット情報が全て本人名義になっているかご確認ください
> 3. 歌詞のオリジナル性（サンプリング素材の使用有無等）を最終確認してください

## 数字での比較

| 指標 | 手作業 | 本 MVP |
|---|---|---|
| 所要時間 | 30〜60 分 | 約 8 秒 + ユーザー確認 2 分 = 約 2 分 |
| 削減率 | — | **約 93%** |
| 月 2 曲リリース時の月削減時間 | — | **約 1〜2 時間** |
| 月額 （非公開） SaaS と仮定した時給換算 | — | 時給 （非公開）〜2,000 のクリエイターでもペイ |
