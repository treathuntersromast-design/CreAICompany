# 05_hr — 人事・組織

役割定義・メンバー名簿・採用・人事ポリシーを置く。

- `roles/<role>.md` — 役割定義（AI 役員含む、人間が読む文書）
- `members/<member>.md` — 在籍メンバーのプロフィール
- `hiring/` — 採用計画と進行中の採用
- `policies.md` — 人事ポリシー

## AI 役員の二層構造

役職は **役割定義 + Subagent 定義** の二層で管理する：

- 役割定義: `roles/<role>.md`（責任範囲・KPI・決裁権限）
- Subagent 定義: [.claude/agents/&lt;role&gt;.md](../.claude/agents/)（口調・判断軸・実装）

両者は相互リンクで結合する。
