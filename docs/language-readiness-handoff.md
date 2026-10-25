# 言語完成への引き継ぎ

引き継ぎの正本を `.noema-project/ledger.sqlite` へ移しました。このファイルは入口だけです。

```powershell
python -X utf8 -m scripts.project_notes brief
python -X utf8 -m scripts.project_notes get writing-identity
python -X utf8 -m scripts.project_notes get next-sequence
```

`brief` に全記録のキーが出ます。移行前の全文は `project_notes document docs/language-readiness-handoff.md` で確認できます。[記録の更新・検索・復旧手順](project-records.md)を参照してください。
