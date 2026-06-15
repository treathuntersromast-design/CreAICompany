# CreAICompany

オーナーと AI 役員で運営する **バーチャル会社** のリポジトリです。

## このリポは何か

- AI CEO **シャチョー** が日々の経営を担い、オーナー（人間）が取締役として方針判断に関与します。
- シャチョー配下に AI 経営陣（CTO / CFO / COO）がいて、必要に応じて呼び出します。
- 経営に関わるすべての知識・記録・決定がここに集約されます。

## 使い方（オーナー向け）

1. **Claude Code をこのリポで起動**するとシャチョーが応答します。
2. 「事業アイデアを出して」「ビジョンを決めよう」「今週のレビューを」など、CEO に話すように依頼してください。
3. 他の役員と話したいときは `@cto` `@cfo` `@coo` を付けて呼び出します。
4. 決定事項は自動的に [01_board/decisions.md](01_board/decisions.md) と [06_operations/daily-log/](06_operations/daily-log/) に記録されます。

## ディレクトリ構成

詳細は [CLAUDE.md](CLAUDE.md) の「ディレクトリの歩き方」を参照。

| 上位 | 用途 |
|---|---|
| [00_company/](00_company/) | 憲章・ビジョン・ミッション |
| [01_board/](01_board/) | 取締役会記録 |
| [02_strategy/](02_strategy/) | 戦略・OKR |
| [03_finance/](03_finance/) | 財務 |
| [04_products/](04_products/) | 事業・プロダクト |
| [05_hr/](05_hr/) | 組織・人事 |
| [06_operations/](06_operations/) | 日常運営 |
| [07_legal/](07_legal/) – [10_knowledge/](10_knowledge/) | 法務・リスク・対外・知識 |

## 最初の一歩

事業ドメイン未確定の状態でスタートしています。最初にやることは：

1. **キックオフ取締役会** — シャチョーと共にビジョン・ミッション・事業探索方針を決める。
2. 結果を [00_company/vision.md](00_company/vision.md) ほかに反映、議事録を [01_board/minutes/](01_board/minutes/) に保存。
3. 翌日から daily-log 運用を開始。
