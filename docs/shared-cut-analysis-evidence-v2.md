# 実数解析語群の依存記録の補完

[解析語群の仕様と検査範囲](shared-cut-analysis-v1.md)は変更しない。検証用の有理数式を構成する旧compose_limitsは、実数積の意味規約ファイルも読み込むため、[検証報告第2版](../reports/shared-cut-analysis-v2.json)にその依存を追加した。定義・語義・判断・検査結果の変更ではない。

第1版の報告、検証コード、SVG、Native文書は保存する。第2版の検証器は、第1版の報告を再構成して保存内容との一致を確認した後、追加した依存ファイルと第1版報告自身のハッシュを記録する。

```powershell
python -X utf8 -m scripts.project_work check --module scripts.check_shared_cut_analysis_v2 --tests tests/test_shared_cut_analysis.py --verify reports/shared-cut-analysis-v2.json
```
