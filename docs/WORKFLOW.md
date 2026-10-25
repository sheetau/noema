# 作業と検証

## 再開と作業単位

```powershell
python -X utf8 -m scripts.project_notes brief
python -X utf8 -m scripts.project_work history "不慣れ" --limit 3
```

次の作業と引き継ぎは `.noema-project/ledger.sqlite` が正本です。[台帳の更新・検索・復旧](project-records.md)に従い、`brief` の後に必要なキーだけを `get` します。`data/work-state.json` は本文・登録簿・集計の選択、STATUSは短い公開チェックポイント、個別の意味判断と検査報告は証拠です。会話が圧縮されても、これらを読めば再開できます。長い履歴全体を毎回読む必要はありません。

一文または関連する意味要素群について、原文範囲・必要な関係・既存定義・不足・統合先を先に整理します。関連する定義をまとめて本文へ接続し、局所検査の後で一文全体を確認します。内部の小変更ごとに登録簿・全体集計・進捗説明を更新しません。未処理の意味要素を除いて完成にすることもありません。

## 局所検証

テストと報告の検査を同一プロセスで行い、モジュール内の既存キャッシュとSQLiteの解析・意味規約キャッシュを再利用します。テスト自体は実行します。

```powershell
python -X utf8 -m scripts.project_work check --module scripts.check_fourth_sentence --tests tests/test_fourth_sentence.py --verify reports/fourth-sentence-v1.json
```

新しい検査モジュールが既存の `prepare()` / `build_report()` 方式を使う場合、`--prepare` と `--write-report reports/<new-version>.json` を指定できます。`--write-report` は異なる既存証拠を上書きしません。一般のpytest検査は `check --tests <files...>` で実行できます。検証基盤自体のテストは通常の `python -X utf8 -m pytest ...` で実行し、必要に応じてキャッシュ有無の双方を比較します。

新しいチェックは共有できる検査関数に `lru_cache` を付けるか、一回の検査結果から報告を作る構成にします。既存の原文判断を再利用するときは依存関係の一致を検証します。テストの通過を新しい原文の意味判断へ変換しません。

新しい検査モジュールでは `noema.review_registry.load_reviews(root, index)` を使います。このAPIは両形式の登録簿を扱い、新しい実行入口の中ではキャッシュも利用します。登録簿v2の `reviews` を旧形式のパス文字列配列として直接処理しないでください。新しい本文ごとに旧 `register_*.py` をコピーする必要はありません。

## 判断の登録

元の判断記録はそのまま残します。登録簿v2には元記録への参照と現行文番号を記載し、履歴を複製しません。元の判断の全検査に加え、現行の文・依存定義と意味規約・関連する識別表記の一致を検査します。

```powershell
python -X utf8 -m scripts.project_work register --index data/semantic-review-index-v113.json --work kant-1784 --basis data/<new>-basis-v1.json --annotations data/<new>-identifiers-v1.json --output data/semantic-review-index-v114.json
```

`<new>` は実際のファイル名へ置き換えます。識別表記がない作品は `--annotations` を省略します。本文の文番号が移動した場合は登録簿の `statements` に明示し、内容一致を検証します。変更された判断は引き継ぎを拒否します。新しく通し確認した記録は従来の `noema-semantic-review-1` 形式で作り、`--review data/<review>.json` を付けて同じ原文単位の判断を置き換えます。複数ならオプションを繰り返します。

旧登録簿からの一度きりの移行も `register --index <old> --output <new>` で行えます。新しい登録簿は過去の登録簿のコピーを累積せず、必要な元判断を直接参照します。新たな判断がない限り完成件数は増えません。

## 全体監査

一文・段落の統合、判断の登録変更、作業の引き渡し時に実行します。通常は変更していない入力に関する検証結果を再利用します。

```powershell
python -X utf8 -m scripts.project_work audit --verify reports/written-progress-v2.json
```

次の集計は `--output reports/written-progress-v3.json` など新しい名前で保存し、成功後に `data/work-state.json` の参照先を更新します。旧集計を上書きしません。

`--full` は永続キャッシュを全面的に迂回し、原来の解析・レビュー・草案監査を実行します。検証器・キャッシュの変更後、定期的な区切り、または不一致の調査に使います。同じ入力で通常監査と出力が一致することも確認します。毎回の小変更やコミットごとに繰り返す必要はありません。

```powershell
python -X utf8 -m scripts.project_work audit --full --verify reports/written-progress-v2.json
python -X utf8 -m scripts.project_work runs
```

## SQLiteと証拠の保存

`.noema-cache/validation.sqlite` には、圧縮JSONによる解析結果・カタログ・監査結果、実行の所要時間と成否、履歴検索索引を保存します。pickleやコード実行可能な形式は使いません。検証器群とPythonの版が変わるとキャッシュを分離し、再利用時は依存ファイルの内容ハッシュを読み直します。ファイル一覧の増減も全体集計に反映します。

仕様・原文・Noema本文・意味規約・判断理由・検査報告の正本はGit管理のファイルと既存の原文保存先です。`.noema-cache/validation.sqlite` は再生成できます。一方、`.noema-project/ledger.sqlite` の引き継ぎ・退役文書は正本なので削除せずバックアップします。旧判断が直接読むファイルは元パスと内容を保持し、参照のない旧文書だけを台帳へ移しました。

キャッシュの破損した値は再計算します。DB自体を開けない場合は原因を確認し、DBを退避して再構築するか `--full` を使います。キャッシュを削除する際は、そのDBを使う検証が終了していることを確認します。複数プロセスはSQLiteのWALを利用できますが、一つのプロセス内のアダプターは並列スレッドに対応しません。

旧スクリプトは過去の証拠がハッシュを固定しているため変更しません。新しい入口は必要な関数だけを実行中に置き換え、失敗時にも元へ戻します。旧コマンドを直接実行すれば、以前の検証をそのまま再現できます。
