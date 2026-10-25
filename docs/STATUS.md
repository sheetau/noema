# 現在地

二作品は明示した解釈の下で全文の意味確認を完了し、円と線の見た目は固定しています。利用者の依頼により言語完成へ進行中です。[測定量・単位換算・容器の個数](shared-quantities-v1.md)を、既存の量・次元と[複数の定義](shared-plurality-v1.md)から構成しました。容器数、内容物の量、部分の完全性と非重複、同じ種類・次元の換算を区別します。共通Native定義は重複を除いて151、既存の有理数算術4基本宣言も共通化しました。[円文字辞書第4版](visible-scope-library-v1.md)は120語で、複数・量の51語が登録待ちです。総称・発話行為など他の意味領域、学習用文書と第三者読解、二作品全体の新書式化は残っています。

引き継ぎの正本は `.noema-project/ledger.sqlite`。`python -X utf8 -m scripts.project_notes brief` で現在地と詳細記録のキーを読みます。[更新・検索・復旧](project-records.md)を参照してください。Markdownに詳細を重複保存しません。

旧文書252件をSQLiteへ保存して通常の `docs/` から退避しました。現行の意味判断が参照するMarkdown 501件・旧本文1,135件などは保持しています。[保持理由と移行一覧](../reports/document-retention-v1.json)に各文書の区分を記録しました。旧版をすべて実行時の互換資産とは扱わず、現行判断・草案監査・旧検証・文書参照を分けています。

現行画像は `output/kant-page-script-v3/`。[書記体系](writing-system.md)と[固定記録](../data/writing-freeze-v1.json)を保持します。前回の削除用一覧と退避フォルダは今回の確認時点でなくなっており、復元していません。

カント20単位・119主張、アインシュタイン282単位・283主張、計51,127非空白本文文字の判断を保持しています。[完成範囲と根拠](two-work-completion-v1.md)はアシスタントによる採用解釈の確認であり、独立査読や万能性の証明とは区別します。

本文と証拠の選択は [work-state.json](../data/work-state.json)、検証は [WORKFLOW](WORKFLOW.md)。旧STATUSは[当時の記録](status-history-through-20261025.md)として保存しています。
