# 現行の書記体系

円と線が接続・分岐・融合する現在の見た目を、利用者の指定により固定した。基準は `contextual-opening-10-draft` と[カント四段落の現行画像](kant-page-script-v3.md)。固定対象と内容ハッシュは [writing-freeze-v1.json](../data/writing-freeze-v1.json) にある。「固定」は字形設計の基準を決めたという意味であり、画像からの一意な読み戻しが完成したという意味ではない。

現行成果物は `output/kant-page-script-v3/` のみ。NoemaのPNG・SVG、対応する英訳PNG、出典と範囲の記録を残した。カント冒頭四段落、原文592語に対応する40主張を18行で配置している。宣言・語義定義の全展開を画像へ載せたものではない。

描画入口は `scripts/contextual_opening_script.py`、ページ生成は `scripts/proof_kant_page_script_v3.py`。前者は過去の描画モジュールの幾何・探索処理を利用するため、旧モジュールをまとめて削除してはいけない。再生成は必要な場合のみ行う。

```powershell
python -X utf8 -m scripts.proof_kant_page_script_v3
```

画像の語の識別、枝の読み順、結合の範囲、文境界と行継続を、不可視のAST・JSON・SVG属性なしで復元する規則は未完成。学習した共通の文法・語彙は利用してよいが、文書ごとの番号対応表を読者に渡して解決してはいけない。具体的な衝突と次の作業は [言語完成への引き継ぎ](language-readiness-handoff.md) にまとめた。

旧32文字の `alphabet-v1.json`、`alphabet-v2.json`、`NoemaWritten.ttf` は処理系の互換資産。旧固有文字の往復試験が成功しても、この円文字の読み戻しを保証しない。旧字体の生成画像は整理したが、互換資産・本文・意味判断・旧検証器は残している。

整理後は固定対象の全ハッシュと旧文字の回帰7件を確認し、全体監査が `reports/written-progress-v432.json` と一致した。読み戻しの衝突を含む検査は次で再現できる（現在の非一意性を診断するもので、復号の完成試験ではない）。

```powershell
python -X utf8 -m scripts.project_work check --module scripts.check_writing_freeze --tests tests/test_script.py tests/test_script_v2.py --verify reports/writing-readiness-v1.json
```

旧字体・出力267ファイルの整理は[前回の記録](../reports/writing-cleanup-v1.json)を参照。削除用一覧と退避フォルダは現在存在しません。文書と引き継ぎは[SQLite台帳](project-records.md)へ整理しました。現行画像と依存コードは維持し、旧画像を一括再生成しません。
