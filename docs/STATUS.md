# 現在地

[名称と人物を区別した著者表示](einstein-name-presentation-v1.md)を接続しました。アインシュタインの著者表示の1主張を参照定義とともに円文字へ記述し、既存の識別注記「de／A. Einstein」も本文から復元できる形にしました。19宣言・2主張を3ページから復号し、19テスト・22文脈診断・20選択子診断・独立CLI・全体監査を確認済みです。共通基盤375語と旧辞書を保持し、任意プロファイルとして一般的な参照・表記機能と旧関係の意味規約を使います。名称から人物や真正性を推論しません。[カントの本文順序](kant-text-reference-v1.md)と合わせて、次は本文の設定・仮定・内容を含む依存群へ進みます。二論文全文の可視化と第三者読解は未完です。

引き継ぎの正本は `.noema-project/ledger.sqlite`。`python -X utf8 -m scripts.project_notes brief` で現在地と詳細記録のキーを読みます。[更新・検索・復旧](project-records.md)を参照してください。Markdownに詳細を重複保存しません。

旧文書252件をSQLiteへ保存して通常の `docs/` から退避しました。現行の意味判断が参照するMarkdown 501件・旧本文1,135件などは保持しています。[保持理由と移行一覧](../reports/document-retention-v1.json)に各文書の区分を記録しました。旧版をすべて実行時の互換資産とは扱わず、現行判断・草案監査・旧検証・文書参照を分けています。

現行画像は `output/kant-page-script-v3/`。[書記体系](writing-system.md)と[固定記録](../data/writing-freeze-v1.json)を保持します。前回の削除用一覧と退避フォルダは今回の確認時点でなくなっており、復元していません。

カント20単位・119主張、アインシュタイン282単位・283主張、計51,127非空白本文文字の判断を保持しています。[完成範囲と根拠](two-work-completion-v1.md)はアシスタントによる採用解釈の確認であり、独立査読や万能性の証明とは区別します。

本文と証拠の選択は [work-state.json](../data/work-state.json)、検証は [WORKFLOW](WORKFLOW.md)。旧STATUSは[当時の記録](status-history-through-20261025.md)として保存しています。
