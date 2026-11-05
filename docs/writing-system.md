# 現行の書記体系

利用者は2026年11月5日にconcept2 v7のアルファベットを採用した。現行の [カント四段落と字形表](../output/noema-writing-v2/index.html) は、元のkant-pageの40項目とv4／v7の幹を保ち、共有・長い枝・辞書記録の不足を補ったもの。残件1の共通書記・復号基盤は [共通規則v2](circle-writing-v2.md) と [固定記録v2](../data/writing-freeze-v2.json) に統合した。

本文の語・構文は、公開辞書とSVGの円弧・直線・ドットから読む。文書ごとの番号表、不可視の構文やSVG属性、元の配置記録を復号器へ渡さない。語義・参照先と回収した構文が変わらなければ、確認済みの意味判断を引き継ぐ。詳しい検証の区分は [検証範囲](verification-boundaries.md)に従う。

規則と実装の入口は次のとおりである。

| 対象 | 規則・実装 |
| --- | --- |
| 半径線、円弧の重なり、方向線の上限 | [幾何規則](alphabet-concept2-refined-v4.md)、`scripts/concept2_geometry_v5.py` |
| ドット、方向付き段選択、任意の合流表記 | [合流規則](alphabet-concept2-confluence-v5.md) |
| 型・束縛・引用・式 | [型と構文](alphabet-concept2-typed-v6.md) |
| 既定の幹の参照順、語参照の後方線 | [v7の採用形](alphabet-concept2-trunk-v7.md) |
| 宣言・定義・綴り登録、仮定範囲、反復の補完 | [文書・辞書規則](alphabet-concept2-document-v8.md)、`scripts/concept2_document.py`、`scripts/concept2_compact.py` |
| 範囲内の共有、長い枝、統合入口 | [共通規則v2](circle-writing-v2.md)、`scripts.concept2_writing.WritingReader` |

旧版の文書にある「外観未承認」は、その版を提案した時点の記録である。現行の採用状態は冒頭の利用者指定に従う。残件1全体の進行と未解決事項は [プロジェクト台帳](project-records.md)の `current` を正本とする。

```powershell
python -X utf8 -m scripts.project_notes brief
python -X utf8 -m scripts.project_work check --tests tests/test_concept2_release.py tests/test_concept2_assembly.py tests/test_concept2_definition_depth.py
```

復号APIは `WritingReader()` を空辞書で作り、順序どおりに `reader.read_page(svg_text)` へ渡す。宣言・別綴りも可視記録から登録され、`reader.result()` が回収した文書と綴りを返す。改行した一文は同じSVG内に置く。保存済みの統合確認は [2,168 SVGの報告](../output/concept2-unified-reader-v1.json)。入力が変わらない検証は再実行せず、ハッシュの一致する結果を使う。

旧kant-pageと [writing-freeze-v1.json](../data/writing-freeze-v1.json) は、過去の外観基準と証拠として保存する。旧字体の `alphabet-v1.json`、`alphabet-v2.json`、`NoemaWritten.ttf` も処理系の互換資産として残す。旧字体の往復試験は現行円文字の復号確認とは区別し、保存済みの画像や旧検証器を一括再生成しない。
