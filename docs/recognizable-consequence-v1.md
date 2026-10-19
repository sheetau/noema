# 仮定下の帰結を、認めやすいものとして提示する

三つの代行例を含む条件文では、後件の `ja` の働きが未記述だった。今回、代行例を仮定すれば本人の対象となる努力は不要になるという帰結を、受け手も認めやすく、新しい争点として扱わずに済むものとして提示する、という読みを追加した。既存の条件文の真偽条件は変えず、提示の扱いを独立した文として記述する。

[AdelungのJa項目](https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_5_0_2)には、ある条件が成り立つなら恐れる必要はない、という後件でこの語を使う並行例がある。同じ項目は回答、驚き、強調などの用法も区別しており、一つの意味へまとめる根拠にはならない。[IDSの説明](https://grammis.ids-mannheim.de/systematische-grammatik/1348)は、話し手が内容を一般に受け入れられたものとして扱う用法を述べる。この二資料を、原刊482頁の該当後件を読む手がかりにした。現代の説明だけから1784年の唯一の意図を確定したとはしない。

出典は[資料記録](../data/recognizable-consequence-evidence-v1.json)に保存した。歴史辞典は本文を抽出したHTMLと元バイト列のハッシュを保存する。IDSは短い引用と取得ページのハッシュを保存し、ページ全文は保存しない。後者のハッシュは取得時の記録であり、保存した全文からオフラインで再計算できる証拠とは扱わない。通常の検証はネットワークへアクセスしない。

基本関係 `hzwx` は、提示者・文章箇所・仮定の記述・帰結の記述・提示文脈を受け取る。二つの記述の人物引数は同じ仮定例の本人を指す。提示者が帰結を認めやすいものとして扱うことを述べ、仮定や帰結の現実の真理、推論の必然性、読者の実際の知識・理解・同意は要求しない。著者がその生活態度を推奨することも導かない。

一般定義 `rqxq` は、同じ箇所・提示者・文脈に、仮定例の提示と帰結の扱いを結ぶ。条件文記述とその前件・後件の対応は呼出側で指定するため、この一般形だけで内容の整合性が保証されるわけではない。本文への接続 `hzwy` は、条件文 `sy`、前件 `sv`、後件 `sx` を固定して渡す。検査では実際の `sy` の定義が `rc` にこの二つを前件・後件として渡すことも確認する。

新しい文42は、既存の一人称仮定例の提示と、この帰結の扱いを要求する。既存42文と全宣言・意味規約は保持するため、能力や所持、努力、結果についての条件は変わらない。本文は合わせて43文となる。これは語を追加の接続詞へ機械的に置換する翻訳規則ではなく、この箇所で選んだ提示関係をNoemaで直接記述したものである。

一般検査では、例の提示、帰結の扱い、仮定の真偽、帰結の真偽の16組合せを別々に変える。本文の十二対照では、著者・箇所・仮定・帰結・文脈の取り違え、前後の反転、既存の列挙・順序を検査する。さらに実際の条件文の定義を用い、その真偽と帰結の提示の四組合せを評価する。失敗結果を含む条件文が偽でも、帰結を認めやすいものとして提示したという記述は真であり得る。計算結果を再利用した評価に加え、その反例を通常評価でも確認する。

検証では、提示だけを評価するときに世界の事実は未知のままにする。提示関係自体が未知なら補完せず、通常表記・簡略表記・独自文字v2の往復も確認する。確認済み十一単位の選択範囲と意味のハッシュは変わらず、文書と根拠の所在を登録簿v51へ更新する。1,001文字の確認済み分量は増やさない。

三名詞や仕事のこの文での語義の最終選択、目的と努力の範囲、`selbst` の焦点、反語と提示態度の相互関係が残る。各語の全用法を定義する課題と、この文を意味を保って記述する課題は分けて進める。今回の追加だけで条件文や第二段落全体を確認済みにはしない。

成果物は[一般定義](../examples/v016/scoped-recognizability.noema)、[本文の抽出](../examples/v016/recognizable-consequence-core.noema)、[累積本文](../examples/v016/kant-recognizable-consequence.noema)、[意味規約](../data/recognizable-consequence-basis-v1.json)、[検査記録](../reports/recognizable-consequence-v1.json)である。

```powershell
python -X utf8 -m scripts.fetch_recognizable_consequence_evidence
python -X utf8 -m scripts.compose_recognizable_consequence
python -X utf8 -m pytest -q tests/test_recognizable_consequence.py
python -X utf8 -m scripts.check_recognizable_consequence
python -X utf8 -m scripts.register_recognizable_consequence
python -X utf8 -m scripts.audit_written_progress_reviewed --index data/semantic-review-index-v51.json
```
