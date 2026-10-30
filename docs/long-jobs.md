# 長時間処理の進捗と再開

5分以上かかる見込みの処理と、大量の入力を扱い所要時間が不明な処理は、実行前に進捗ログと中断・再開を実装する。生成、解析、意味の検査、画像読み取り、全体監査に共通して適用する。

`scripts.long_run.LongRun` は、実行専用フォルダーへ次を保存する。

- `manifest.json`: 入力、実装、実行条件の固定情報。
- `events.jsonl` / `status.json`: 現在の段階・対象、完了件数と既知の総数、経過時間。既定15秒のheartbeat。件数の割合を時間の割合としない。
- `steps.sqlite`: 正常に完了した手順のJSON結果。書き込み途中の結果は再利用しない。
- `owner.lock`: OSの排他ロック。同じ実行を同時に再開できない。異常終了時にはOSが解除する。

処理の区切りで `run.step(key, input_hashes, action, validate=...)` を呼ぶ。入力には関連ファイルの内容ハッシュ・実装版・処理条件を含める。`validate` は出力ファイル等のハッシュを再確認する。生成物は一時ファイルから原子的に確定し、中断で残った未確定ファイルを安全に扱えるよう各処理を設計する。長い外部コマンド全体を一つのstepに包むだけでは、中断・再開対応とはしない。

`PAUSE` という空ファイルを実行フォルダーに置くと、次の手順境界で停止する。処理中の一手順は完了を待つ。Ctrl+Cやプロセス終了では確定済み手順を保持し、実行中の未確定手順を再実行する。大きい一手順は事前に分割する。プロセスの途中の命令位置やメモリー全体は保存しない。

再開前に `PAUSE` を取り除き、同じ入力・実装・条件で `resume=True` を指定する。入力の変更は時刻やサイズではなく内容で検出する。条件が変わった場合は新しい実行を作る。履歴・正式な証拠・台帳と、再計算可能な中間結果を区別する。

## 再開できる監査

新しい監査入口は共有キャッシュを使わず、新規実行用の空のDBから開始する。同じ実行の途中結果だけを保存・再利用し、元のレビュー検査・解析器・最終集計比較を呼ぶ。レビュー単位、カタログ、文書解析の境界で状態を記録する。

```powershell
python -X utf8 -m scripts.quiet_run -m scripts.resumable_audit --run-dir .noema-project/runs/audit-new --index data/semantic-review-index-v457.json --verify reports/written-progress-v433.json
New-Item -ItemType File -Path .noema-project/runs/audit-new/PAUSE
# 停止後、利用者が再開を指示した場合
Remove-Item -LiteralPath .noema-project/runs/audit-new/PAUSE
python -X utf8 -m scripts.quiet_run -m scripts.resumable_audit --run-dir .noema-project/runs/audit-new --index data/semantic-review-index-v457.json --verify reports/written-progress-v433.json --resume
```

この方式は途中結果を使うため、永続結果を全面迂回する旧 `project_work audit --full` とは区別し、結果に `legacy_full: false` を記録する。既存のfull監査を要求する最終条件を自動で置き換えない。検証基盤変更後の独立した照合には、小さい固定コーパスで旧full方式と新方式の一致を確認する。実コーパスの新方式は、その実行と照合を終えるまで完了扱いにしない。

既に起動した旧監査の途中状態を、新方式へ移す機能はない。旧監査を止めたり、その固定入力を書き換えたりして新方式へ切り替えない。
