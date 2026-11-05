# 現在地

concept2 v7のアルファベットを利用者が採用し、残件1の共通書記・復号基盤を整合させました。[現行の本文・字形表](../output/noema-writing-v2/index.html)、[共通規則](circle-writing-v2.md)、[固定記録](../data/writing-freeze-v2.json)が入口です。空辞書から宣言・綴りを順に読み、カント40項目と追加対照を含む2,168 SVGで構文の一致を確認しています。二作品全402主張の新字体による最終文書統合は別の残件です。

引き継ぎの正本は `.noema-project/ledger.sqlite`。`python -X utf8 -m scripts.project_notes brief` で現在地と詳細記録のキーを読みます。[更新・検索・復旧](project-records.md)を参照してください。Markdownに詳細を重複保存しません。

旧文書252件をSQLiteへ保存して通常の `docs/` から退避しました。現行の意味判断が参照するMarkdown 501件・旧本文1,135件などは保持しています。[保持理由と移行一覧](../reports/document-retention-v1.json)に各文書の区分を記録しました。旧版をすべて実行時の互換資産とは扱わず、現行判断・草案監査・旧検証・文書参照を分けています。

旧 `output/kant-page-script-v3/` と固定記録v1は比較・検証のため保存しています。現行の入口は [書記体系](writing-system.md)にまとめています。

カント20単位・119主張、アインシュタイン282単位・283主張、計51,127非空白本文文字の判断を保持しています。[完成範囲と根拠](two-work-completion-v1.md)はアシスタントによる採用解釈の確認であり、独立査読や万能性の証明とは区別します。

本文と証拠の選択は [work-state.json](../data/work-state.json)、検証は [WORKFLOW](WORKFLOW.md)。旧STATUSは[当時の記録](status-history-through-20261025.md)として保存しています。
