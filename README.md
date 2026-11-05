# Noema

円と線が接続・分岐する書記体系と、定義・量化・数式・引用・言説を扱う独自言語です。**Noema 1.0として言語本体を完成しました。** [完成版の入口](output/noema-1.0/index.html)、[仕様・根拠・完成範囲](docs/language-edition-v1.md)を参照してください。共通辞書1,952項目と、カント20単位・アインシュタイン282単位の全文、原文対応、固定円文字、検証証拠を保存しています。自動翻訳器は引き続き保留しています。

## 開発の再開

```powershell
python -X utf8 -m scripts.project_notes brief
```

見た目は[現行書記体系](docs/writing-system.md)で固定しました。次の課題と着手順はSQLite台帳の `brief` / `get` で読みます。[記録の管理手順](docs/project-records.md)を参照してください。

[現在地](docs/STATUS.md) → [作業・検証手順](docs/WORKFLOW.md) → 必要な個別仕様・判断記録の順に読みます。言語本文と検証の参照先は [work-state.json](data/work-state.json)、次の作業は `.noema-project/ledger.sqlite` にあります。

## 意味と完成の基準

- [言語本体の完成条件](docs/language-completion.md)
- [原文単位の意味確認](docs/semantic-review-v1.md)
- [進捗の読み方](docs/written-progress-v1.md)
- [二作品の完成監査](docs/two-work-completion-v1.md)

任意の内容に対する表現率は未測定です。構文・型・往復・有限モデルの検査を、原文との意味一致の自動証明とは扱いません。

## 過去の記録

従来のREADMEは、内容と改行を変えずに [README.history.md](README.history.md) に保存しています。全履歴を毎回読み込まず、必要な話題を検索します。

```powershell
python -X utf8 -m scripts.project_work history "因果"
```

SQLiteは引き継ぎ・退役文書の正本と、検証キャッシュ・実行記録を別DBで管理します。言語仕様・意味判断・原文との対応はファイルとGitに保存します。台帳はキャッシュと一緒に削除しないでください。
