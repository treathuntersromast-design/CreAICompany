# 01_board — 取締役会

会社の最高意思決定機関の記録を置く。

- `members.md` — 取締役一覧
- `minutes/YYYY-MM-DD.md` — 取締役会議事録
- `decisions.md` — 決議事項の通し番号付きログ（`D-NNN`）
- `agenda.md` — 次回議題スタック

## 運用ルール

- 重要決定はすべて `decisions.md` に `D-NNN` で記録する。
- 議事録と決議は相互参照する（議事録に決議番号を列挙、決議に該当議事録のリンク）。
- 月次取締役会は月末に開催し、`minutes/YYYY-MM-EOM.md` として保存。
