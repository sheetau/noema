# 必要な定義だけを持つ独立文書（2026-10-14）

累積草案から、指定した定義と本文が参照する宣言だけを取り出せるようにした。本文、定義の中身、記号名、引用内の式は変更しない。依存先を含めたNoema文書を出力するため、取り出した文書も単独で解析・型検査・表示できる。

| 文書 | 文字数 | 基本関係 | 定義 | 本文主張 |
| --- | ---: | ---: | ---: | ---: |
| 元の累積草案 | 81,515 | 252 | 505 | 15 |
| [同じ本文と指定定義を保持した文書](../examples/v014/kant-compact-library.noema) | 35,908 | 186 | 243 | 15 |
| [公的発言の定義ライブラリ](../examples/v014/public-speech-core.noema) | 3,434 | 19 | 23 | 0 |

第二行では元の15件の本文主張をすべて保持し、公的発言の例に使う13定義も明示的に保持した。未使用の宣言を除くことで、正規形の文字数は約56%減った。第三行は定義だけを使うためのライブラリであり、元の本文を保持した短縮訳ではない。

この削減は、文書へ同梱する定義の量を減らした結果である。個々のNoema文を短くする規則、同義表現の圧縮、原文との翻訳文字数比の改善を実証したものではない。全文記述を進める際にも、定義の再利用に必要な量と、本文自体の長さを分けて測る。

## 保持するもの

抽出の起点は、利用者が指定する記号と、残す本文の文である。定義や本文から参照する宣言をたどり、それらの依存先もすべて保持する。引用の内部、関数参照、列、集計、入れ子の仮定の内部も対象にする。実行時に内容を評価しない引用であっても、参照する宣言を削除しない。

記号を付け替えず、定義を展開・簡約せず、同じ内容を返す別名も統合しない。元の宣言順、本文の順序・重複、仮定の範囲を保持する。本文の一部を選ぶ場合も、入れ子の仮定の内部だけを切り出して無条件の主張にはしない。選択できるのは最上位の文単位である。

意味説明も、残した基本関係と定義に対応する項目をそのまま保持する。原文書の未解決事項は、関連性を自動判断して削除せず全て残す。旧文書のリンク対応表などは、そのまま新文書の対応表として扱わず、出典情報を付けて除外する。抽出しても基本概念の意味が新たに確立されるわけではない。

## 使用方法

CLIは既定で本文の全ての文を保持する。`--root`を追加すると、本文から参照されない定義でも利用入口として残せる。既存ファイルには上書きしない。出力先の親フォルダーは事前に存在している必要がある。

```powershell
python -X utf8 -m scripts.extract_document --input examples/v014/kant-public-assessment.noema --output artifacts/kant-extracted.noema --root hzy --root reu
```

定義だけの文書を作る場合は、`--definitions-only`を明示する。意味説明と抽出記録も一緒に出せる。

```powershell
python -X utf8 -m scripts.extract_document --input examples/v014/kant-public-assessment.noema --output artifacts/public-assessment-extracted.noema --definitions-only --root hzy --root reu --basis-input data/kant-public-assessment-basis-v1.json --basis-output artifacts/public-assessment-extracted-basis.json --manifest artifacts/public-assessment-extracted-manifest.json
```

本文を選ぶ場合は`--statement 0 --statement 2`のように、0から始まる最上位の文番号を指定する。指定順にかかわらず元の本文順を保持する。文番号の重複、範囲外、未知の記号、空文書になる選択を拒否する。`--statement`と`--definitions-only`は同時に使えない。

Pythonでは`noema.extraction.extract_document`を使える。返り値には文書、保持・除外した記号、起点、本文の番号が含まれる。元の文書は変更しない。`extract_basis`は元の意味説明を検査した上で、同じ抽出に対応する項目を保存する。

## 検証と限界

既存の職務・公的発言、禁止に対する保護、判断の目的の検査を再実行し、それぞれの評価対象から必要な宣言だけを抽出した場合と比較した。145件の評価結果と、未知の情報による8件の評価拒否が一致した。比較では対象領域と状況領域を変えず、基本関係の解釈も同じものを使う。

APIとCLI、引用内の依存、別名、入れ子の仮定、本文の順序・重複、誤った選択、出力先の衝突・上書き拒否を含め、48テストが通った。二つの保存文書について、全文・短縮記法と固有文字の往復、CLI解析結果の一致、SVGのXML妥当性を確認した。抽出CLIで意味説明とマニフェストも出力し、その対応を検査した。今回は字形の目視確認は行っていない。

構文上の依存を閉じて保存する仕組みであり、意味の同義性を判定する仕組みではない。原文に対する新しい意味確認や対応範囲の追加もしていない。二作品の意味確認済み全文単位は0のままである。[検査記録](../reports/compact-library-v1.json)には元文書と出力のハッシュ、保持した記号、文字数、比較結果を保存した。

```powershell
python -X utf8 -m scripts.check_compact_library --verify-only
python -X utf8 -m pytest tests/test_extraction.py tests/test_compact_library.py tests/test_linking.py tests/test_written_progress.py -q
python -X utf8 -m scripts.audit_written_progress --verify-only
```
