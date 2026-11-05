# 引き継ぎと文書の保存

現在の引き継ぎの正本は `.noema-project/ledger.sqlite`。検証用の `.noema-cache/validation.sqlite` とは別であり、キャッシュとして削除してはいけない。ダッシュボード・常駐プロセス・goalの自動起動は設けない。

```powershell
python -X utf8 -m scripts.project_notes brief
python -X utf8 -m scripts.project_notes get writing-identity
python -X utf8 -m scripts.project_notes get semantic-coverage
python -X utf8 -m scripts.project_notes search "反事実" --limit 5
```

`brief` は現在の短い引き継ぎ、詳細記録のキー、正本・検証の参照先を返す。必要なキーだけ `get` で読む。`search` は台帳の引き継ぎと退役文書を検索する。残した仕様・証拠のファイルは必要に応じて `rg` で検索する。

## 更新と復旧

引き継ぎの変更は、UTF-8の一時JSONファイルに `key`・`title`・`body`・`expected_revision` を入れて行う。`get` で読んだ版番号を指定し、競合時は再読する。元の記述と更新履歴は同じキーのまま保存する。記録へ追加した未着手案を、利用者が実行を依頼した作業と混同しない。

```powershell
python -X utf8 -m scripts.project_notes put --file .noema-project/update.json
python -X utf8 -m scripts.project_notes revisions writing-identity --limit 3
python -X utf8 -m scripts.project_notes backup --output .noema-project/backups/<new-name>.sqlite
```

更新はSQLiteのトランザクションで保存される。作業の区切りで新しい名前のバックアップを `.noema-project/backups/` に作り、その場所を台帳の `current` に記録する。古い重複バックアップは完成後の整理で削除したため、復旧には現在記録されているバックアップを使う。DB・バックアップ・退役原本はGit対象外であり、別端末への移行にはDBのバックアップも必要。DBがなければコマンドは失敗し、空の引き継ぎを自動作成しない。復旧時は台帳を使うコマンドが終了した状態で、既存DBを別名で保全してからバックアップを `ledger.sqlite` に戻す。

Markdownの引き継ぎは入口だけにし、本文を二重に編集しない。`data/work-state.json` は検証対象の登録簿・集計の選択、`docs/STATUS.md` は短い公開チェックポイントとして残す。詳細な作業履歴は追加しない。

## 旧版を残す理由と今回の整理

以前は `docs` 直下にMarkdownが1,216件あった。現在の意味判断302件を検証する依存には、このうち501件と旧本文1,135件が含まれる。全体の草案監査にはMarkdown 502件が必要で、過去の記録まで含めると829件がハッシュで参照されていた。通常の構文解析がMarkdownをすべて読むという意味ではない。

追跡対象のJSON・Pythonコードと、残す文書からのリンクを調べ、参照されていない252件を通常の `docs/` から外した。内容・元パス・ハッシュは台帳へ保存し、原本を `.noema-project/archive/docs/` に退避した。不要な作業ファイルを一覧から外しながら、内容は検索・復元できる。[個別の保持理由と移行一覧](../reports/document-retention-v1.json)に判定根拠を保存している。動的なパス生成まで完全に証明する解析ではないため、移行後に現行監査も実行する。

```powershell
python -X utf8 -m scripts.project_notes why docs/unit-semantic-review-v1.md
python -X utf8 -m scripts.project_notes document docs/open-problems.md
python -X utf8 -m scripts.project_notes restore-document docs/open-problems.md
```

`restore-document` はハッシュを確認し、元のパスへ元のバイト列を戻す。既存ファイルは上書きしない。旧文書に残る過去のリンクが見つからない場合も、元パスで `document` を指定して読める。

`examples/v014/` と `examples/v016/` はアインシュタイン・カントの現行正本を含む。`v011`・`v013` には現行判断が使う旧本文もある。`v08`・`v09`等は言語仕様の版であり、すべてが古い字体の版ではない。旧構文の回帰試験・草案監査が読む例は残した。現在の円描画器も以前の幾何処理を呼ぶため、旧描画コードはフォルダ名だけで削除できない。

旧版依存をさらに減らす場合は、現在の意味判断への直接依存と、過去の草案監査のためだけの依存を分けて移行する必要がある。参照を消したりハッシュを更新しただけで同じ判断が成立したことにはしない。今回、処理系・旧検証器・意味判断・原典は変更していない。
