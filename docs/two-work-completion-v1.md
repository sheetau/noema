# 二作品の全文記述と完成範囲

カント『啓蒙とは何か』とアインシュタイン『運動物体の電気力学について』を、各意味判断で明示した解釈の下で全文記述した。カント20単位・15,513非空白本文文字、アインシュタイン282単位・35,614非空白本文文字が対象である。見出し、数式、著者注も原文単位との対応と判断に含む。

文字数には原文整理用の数式参照記号を含めず、数式の内容と対応は別に照合する。

## 本文と根拠

| 作品 | 本文 | 意味規約 | 採用した主張 |
| --- | --- | --- | --- |
| カント | [全文Noema](../examples/v016/kant-reviewed-complete-v1.noema) | [意味基盤](../data/kant-reviewed-complete-basis-v1.json) | 119 |
| アインシュタイン | [全文Noema](../examples/v014/einstein-reviewed-complete-v1.noema) | [意味基盤](../data/einstein-reviewed-complete-basis-v1.json) | 283 |

[原文順の対応表](../data/reviewed-works-assembly-v1.json)は、原文単位、元の意味判断、旧新の文番号を結ぶ。[登録簿v456](../data/semantic-review-index-v456.json)が現在の本文を固定し、[全体集計](../reports/written-progress-v432.json)と[完成監査](../reports/two-work-completion-v1.json)に結果を記録する。元判断の解釈・限界・出典・検査証拠は移し替えず、そのまま参照する。

累積稿には後の記述で置き換えられた部分草案の主張も残っていた。統合版では、現在の全文判断が選ぶ主張を収録する。定義の辞書と意味規約の出典は全て保持し、旧主張・旧稿・旧検証器も保存する。詳細は[統合手順](reviewed-works-assembly-v1.md)にある。未使用の旧定義が辞書にあることを、本文でその内容を追加主張することとは扱わない。

原刊との相違は各判断の固定証拠に残した。例えばM0427のμの欠落、小さいtと系kのτによる微分の区別を消さず、採用する読みと訂正の根拠を保持する。原文の曖昧さは、各判断に明記した解釈の下で扱う。

## 六成果物の確認

1. **仕様と意味基盤。** [0.8](spec-v08.md)から[0.14](spec-v014.md)までの仕様、[0.15の評価層付き引用](ranked-quotation-v1.md)、[0.16の記述合成](quotation-construction-v1.md)を参照する。カントの本文は0.16、アインシュタインは0.14である。基本関係の意味と引数、合成定義、過去からの出典をカタログで全宣言について確認した。
2. **モデル不要の処理。** 現行二作品の解析・型・正規化、長短形式と32文字の固有文字の往復を確認した。[115件の回帰検査](../reports/language-delivery-regression-v1.json)は旧版、明示的な版移行、CLI、フォント、引用と記述合成を含む。0.16を使うときは専用入口を明示する。
3. **二作品の本文。** 定義を含む二つの自己完結した文書に、採用した全主張を収録した。未定義の参照や、自然言語本文を文字列・リンクだけで置く代用は残さない。
4. **全原文との対応。** 著者本文の302単位を全て対応付け、元のハッシュと数式要素を保持した。後世の編集要素を著者の主張へ混ぜない。単位内の原文順を明示していない旧判断は、その不足した順序情報をnullで示し、新しく創作しない。判断対象の内容の欠落を意味するものではない。
5. **項目ごとの意味判断。** 原文固定、意味関係、参照、提示役割、余分な条件と欠落、意味規約、根拠と限界、単位全体の再読という八要求を満たす302判断を保持した。現行本文への再束縛では、文と推移的な依存意味・識別表記の一致を検証した。
6. **別話題への再利用。** [雨を条件とする呼びかけ](../examples/v010/conditional-directive.noema)、[人物別のメッセージと目的](../examples/v016/personal-message-purpose.noema)に加え、[局所的な返礼作法](local-reciprocity-custom-v1.md)を既存構文で定義した。架空の共同体について、身体動作、義務、謝意の表示規約、実行を33の対照で区別した。実在文化の調査結果や全語義の説明と取り違えない。

## 使用

```powershell
python -X utf8 -m scripts.project_work brief
python -X utf8 -m noema.constructed parse -i examples/v016/kant-reviewed-complete-v1.noema
python -X utf8 -m noema parse -i examples/v014/einstein-reviewed-complete-v1.noema
python -X utf8 -m noema.constructed format -i examples/v016/kant-reviewed-complete-v1.noema --script
python -X utf8 -m scripts.project_work audit --index data/semantic-review-index-v456.json --verify reports/written-progress-v432.json
python -X utf8 -m scripts.project_work check --module scripts.audit_two_work_completion --tests tests/test_two_work_completion.py --verify reports/two-work-completion-v1.json
```

毎回この全監査を再実行する必要はない。現在の入口と変更対象を読み、意味・本文・検証基盤を変更した範囲に応じて検査する。改訂で意味が変われば旧判断を再束縛せず、新しい判断を記録する。

## 完成の限界

これは明示した解釈と基本関係の規約の下での、アシスタントによる意味判断である。独立した人間の査読、原著者の理論の真理、原文との同義性の自動証明ではない。構文往復や有限の対照例は、それぞれの検査範囲の証拠として扱う。

0.15/0.16には実行時の評価層検査と評価回数上限があり、任意の高階関数についての静的な効果・停止性の証明や、無限領域を一般に評価する処理系は提供しない。仕様で説明する式と、有限モデルで実行できる範囲を区別する。これらの限界を、未記述の原文を埋めたことにするための免除には使わない。

二作品の完成は、あらゆる人間の意味を網羅した証明ではない。未知の話題は、説明した基本関係と定義の合成を通じて今後も拡張する。自動翻訳器とモデル比較は引き続き保留する。
