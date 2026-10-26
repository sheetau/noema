# 現在地

[実数の下側切断9定義を共有語と円文字へ接続](shared-real-cuts-v1.md)しました。辞書第13版は384語・361定義・23基本宣言で、新しい基本関係の追加はありません。アインシュタイン正本の13宣言との可逆な対応を確認し、16検査式を2冊3ページから復元しました。15テスト、12算術法則・4反例検査、CLI復号、全体監査を確認済みです。[文書群書式](visible-collection-v1.md)と[全宣言点検](manuscript-transfer-v1.md)を使って、残る語形と基本関係の接続を続けます。二作品の正本・意味判断・固定字体を保持しています。[375語の読本と読解課題](noema-reader-v1.md)は整備済みですが、全文移行と第三者読解は未完です。

引き継ぎの正本は `.noema-project/ledger.sqlite`。`python -X utf8 -m scripts.project_notes brief` で現在地と詳細記録のキーを読みます。[更新・検索・復旧](project-records.md)を参照してください。Markdownに詳細を重複保存しません。

旧文書252件をSQLiteへ保存して通常の `docs/` から退避しました。現行の意味判断が参照するMarkdown 501件・旧本文1,135件などは保持しています。[保持理由と移行一覧](../reports/document-retention-v1.json)に各文書の区分を記録しました。旧版をすべて実行時の互換資産とは扱わず、現行判断・草案監査・旧検証・文書参照を分けています。

現行画像は `output/kant-page-script-v3/`。[書記体系](writing-system.md)と[固定記録](../data/writing-freeze-v1.json)を保持します。前回の削除用一覧と退避フォルダは今回の確認時点でなくなっており、復元していません。

カント20単位・119主張、アインシュタイン282単位・283主張、計51,127非空白本文文字の判断を保持しています。[完成範囲と根拠](two-work-completion-v1.md)はアシスタントによる採用解釈の確認であり、独立査読や万能性の証明とは区別します。

本文と証拠の選択は [work-state.json](../data/work-state.json)、検証は [WORKFLOW](WORKFLOW.md)。旧STATUSは[当時の記録](status-history-through-20261025.md)として保存しています。
