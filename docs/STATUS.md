# 現在地

採用済みconcept2 v7の円文字による、二作品全402主張の最終文書統合が完了しました。[二作品の閲覧版](../output/two-work-final-v2/index.html)、[完成版の選択記録](../data/two-work-publication-v1.json)、[最終照合](../reports/two-work-final-publication-v1.json)が入口です。宣言と補助注記を含む10,946記録の図形復号が一致し、原文302単位、識別表記、数式、著者脚注を保持しています。既存の意味判断を引き継ぎ、新しい意味判断は追加していません。

残件1の共通書記・復号基盤は維持しています。[本文見本・字形表](../output/noema-writing-v2/index.html)、[共通規則](circle-writing-v2.md)、[固定記録](../data/writing-freeze-v2.json)を参照してください。

引き継ぎの正本は `.noema-project/ledger.sqlite`。`python -X utf8 -m scripts.project_notes brief` で現在地と詳細記録のキーを読みます。[更新・検索・復旧](project-records.md)を参照してください。Markdownに詳細を重複保存しません。

旧文書252件をSQLiteへ保存して通常の `docs/` から退避しました。現行の意味判断が参照するMarkdown 501件・旧本文1,135件などは保持しています。[保持理由と移行一覧](../reports/document-retention-v1.json)に各文書の区分を記録しました。旧版をすべて実行時の互換資産とは扱わず、現行判断・草案監査・旧検証・文書参照を分けています。

旧 `output/kant-page-script-v3/` と固定記録v1は比較・検証のため保存しています。現行の入口は [書記体系](writing-system.md)にまとめています。

カント20単位・119主張、アインシュタイン282単位・283主張、計51,127非空白本文文字の判断を保持しています。[完成範囲と根拠](two-work-completion-v1.md)はアシスタントによる採用解釈の確認であり、独立査読や万能性の証明とは区別します。

本文と証拠の選択は [work-state.json](../data/work-state.json)、検証は [WORKFLOW](WORKFLOW.md)。旧STATUSは[当時の記録](status-history-through-20261025.md)として保存しています。
