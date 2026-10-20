# Noema

32文字の固有アルファベットと、定義・量化・数式・引用・言説を扱う独自言語です。現在は自動翻訳器を保留し、カント『啓蒙とは何か』とアインシュタイン『運動物体の電気力学について』の全文記述を進めています。

## 開発の再開

```powershell
python -X utf8 -m scripts.project_work brief
```

[現在地](docs/STATUS.md) → [作業・検証手順](docs/WORKFLOW.md) → 必要な個別仕様・判断記録の順に読みます。正本と次の作業の参照先は [work-state.json](data/work-state.json) にあります。

## 意味と完成の基準

- [言語本体の完成条件](docs/language-completion.md)
- [原文単位の意味確認](docs/semantic-review-v1.md)
- [進捗の読み方](docs/written-progress-v1.md)
- [直近の第四文の通し確認](docs/fourth-sentence-v1.md)

任意の内容に対する表現率は未測定です。構文・型・往復・有限モデルの検査を、原文との意味一致の自動証明とは扱いません。

## 過去の記録

従来のREADMEは、内容と改行を変えずに [README.history.md](README.history.md) に保存しています。全履歴を毎回読み込まず、必要な話題を検索します。

```powershell
python -X utf8 -m scripts.project_work history "因果"
```

SQLiteはローカルの検証キャッシュ・実行記録・履歴検索索引に使用します。言語仕様・意味判断・原文との対応・履歴本文はファイルとGitに保存します。
