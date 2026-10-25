# 現在地

[文脈ごとの語義・同義・多義・置換](shared-senses-v1.md)を25の共通定義として追加し、共通Nativeは352定義になりました。候補の保持・選択・列挙完了と内容の真理を分け、同義でも引用の中で置換できない場合を保持します。42テスト、1,120モデル、36件の引数結合診断、四つのNative例を検証済みです。次は[情報構造](shared-focus-v1.md)の38語と合わせた63語を円文字へ接続します。[円文字辞書第11版](visible-evidence-v1.md)は312語（289構成定義＋23基本宣言）です。学習文書と第三者読解、二作品全体の新書式化も残っています。二作品の明示した解釈と固定した字体を保ち、言語完成へ進行中です。

引き継ぎの正本は `.noema-project/ledger.sqlite`。`python -X utf8 -m scripts.project_notes brief` で現在地と詳細記録のキーを読みます。[更新・検索・復旧](project-records.md)を参照してください。Markdownに詳細を重複保存しません。

旧文書252件をSQLiteへ保存して通常の `docs/` から退避しました。現行の意味判断が参照するMarkdown 501件・旧本文1,135件などは保持しています。[保持理由と移行一覧](../reports/document-retention-v1.json)に各文書の区分を記録しました。旧版をすべて実行時の互換資産とは扱わず、現行判断・草案監査・旧検証・文書参照を分けています。

現行画像は `output/kant-page-script-v3/`。[書記体系](writing-system.md)と[固定記録](../data/writing-freeze-v1.json)を保持します。前回の削除用一覧と退避フォルダは今回の確認時点でなくなっており、復元していません。

カント20単位・119主張、アインシュタイン282単位・283主張、計51,127非空白本文文字の判断を保持しています。[完成範囲と根拠](two-work-completion-v1.md)はアシスタントによる採用解釈の確認であり、独立査読や万能性の証明とは区別します。

本文と証拠の選択は [work-state.json](../data/work-state.json)、検証は [WORKFLOW](WORKFLOW.md)。旧STATUSは[当時の記録](status-history-through-20261025.md)として保存しています。
