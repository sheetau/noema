# 証拠と情報更新の円文字接続

円文字辞書第11版は312語である。第10版の267語に、信念・証拠の25定義、情報更新の19定義、閉じた内容記述の選択関数`claimchoice`を加えた。構成定義289語と基本宣言23語、語形では単独語30語と複合語282語となる。文字の形と接続規則は既存の固定方式を使う。

[語形の登録](../noema/resources/visible-evidence-vocabulary-v1.json)は、証拠群を`book/rain`、更新群を`book/round`から始まる複合語として指定する。部品名は共有された綴りであり、それだけから語義を計算する方式ではない。意味は[証拠語彙](shared-evidence-v1.md)と[更新語彙](shared-revision-v1.md)の本文・型・引数役割・解釈規約へ対応する。新しい文字や文ごとの基本演算子は追加しない。

## 保存する意味

以前の267語は、語形、定義本体、引数、意味を保持する。証拠と更新の両ファイルに含まれる8つの依存定義も、本体と契約を照合して一度だけ登録する。受領・採用・信念変化・実際の真理・情報増加を一つの判定にまとめない。引用記述を評価する語は引用段階1、評価を含まない語は段階0で呼出し・引用を検査する。

`claimchoice`は条件に応じて既に構成された二つの記述の一方を返す。内容の真理を決めたり、同義の別記述へ置き換えたりしない。本文の命題項目と記述の対応をこの語で構成し、候補や根拠の関係はNativeの定義として残す。

## 図形から読む文書

辞書の輸入文書1件と、次の8文書を円と線へ描画し、SVGの図形から宣言・輸入・本文を復号してから評価する。文書ごとの見えないASTや名前対応表は復号に渡さない。共有辞書と文法は版番号から選ぶ。

| 群 | 本文 | 保持する区別 |
| --- | --- | --- |
| 証拠 | [再伝聞](../examples/v016/visible-evidence-relay-v1.noema)、[別起源](../examples/v016/visible-evidence-separate-v1.noema)、[推論](../examples/v016/visible-evidence-inference-v1.noema) | 観察・伝聞・推論、依存順序、起源の重複、根拠付き誤信念 |
| 更新 | [絞込み](../examples/v016/visible-revision-filter-v1.noema)、[訂正](../examples/v016/visible-revision-reversal-v1.noema)、[再受領](../examples/v016/visible-revision-repeat-v1.noema)、[支持の増加](../examples/v016/visible-revision-supportgain-v1.noema)、[誤った採用](../examples/v016/visible-revision-misleading-v1.noema) | 受領・採用・状態変化と、情報の増加・誤りの除去 |

全8文書で各14判定を保つ。外部解釈は、Aki・Nao・文脈の指定する一羽の鳥という既存の対象名、状況アドレス、記述選択に限る。証拠の3個体モデルの第三主体には`birdone`を用いる。これは明示的な関係を仮定した有限モデルであり、現実の鳥の観察・伝聞・推論能力を主張する例ではない。対象を数値アドレスで暗黙に増やしたり、語義を外部ホストの関係へ置き換えたりしない。

状況は既存の`situationslot`により本文で参照する。アドレスの大小は時間順序や内容の真理を決めず、実際の順序・候補・認識・証拠の利用可能性・前提・起源は本文にある。前後状態を保存したまま、復号後に同じ比較を行う。

## ページと実行入口

新しい入口は第1〜11版を選択できる。旧入口は元の対応版と制限を保つ。第10版のローカル定義に使われていた綴りを、第11版の共通語へ勝手に読み替えない。

```powershell
python -X utf8 -m scripts.visible_evidence_book render examples/v016/visible-revision-filter-v1.noema output/my-revision-pages --width 6400 --public-names
python -X utf8 -m scripts.visible_evidence_book decode output/my-revision-pages/page-1.svg output/my-revision-pages/page-2.svg output/my-revision-pages/page-3.svg output/my-revision-pages/page-4.svg --native --public-names
```

各ページは本文768字形・4,096図形以内、文書全体は8ページ・128行・共有展開8,192節点以内という従来の制限を保持する。行番号は文書通算で図形に記し、末尾マーカーは最終ページの最終行だけに置く。ページの欠落・重複・交換・途中切断を拒否する。SVG要素の格納順ではなく、図形の配置と接続から読む。

生成済みのSVGは`output/visible-evidence-library-v1/`、本文と検査入力のハッシュおよびページごとの図形数は[検査報告](../reports/visible-evidence-v1.json)に保存する。全45語の型付き呼出し・引用と、8例の112判定を検証する。有限の例の通過は任意領域の意味同値の証明ではない。図形の復号を、画像OCRや第三者による読解の達成と数えない。
