# 実数の積・逆数・平方根と定義域

実数切断の積・逆数・平方根を共有語と円文字辞書第14版へ接続した。選択中のアインシュタイン正本から10定義を改名だけで保持し、結果と定義域を明示する5定義を合成した。辞書は399語、376定義、23基本宣言で、旧384語の意味・型・本体・綴りは変わらない。基本関係と基本字形の追加はない。

## 候補を作る関数と演算の成立条件

有理数上の性質を受け取る関数には、空の性質や閉じた境界も入力できる。型だけでは有効な実数切断と分からない。次の候補関数は元の本体を保ち、実数演算として使うための条件を意味規約に明記する。

| 共有語 | 内容・利用条件 |
| --- | --- |
| cutmutualrelation | 指定した関係を左右の両方向で要求する。関係自体が包含だとは決めない |
| cutvalueequal | cutincludedを両方向で要求する。引用名の同一性ではない |
| cutnonnegative | 零の切断が入力に含まれる。有効性は別の条件 |
| cutabsolute | 非負なら入力を、それ以外なら符号反転した性質を返す |
| cutnonnegativeproduct | 非負の有効な二切断の積に使う候補 |
| cutproduct | 絶対値の積と符号判定を組み合わせる |
| cutpositivereciprocal | 正の有効な切断に対する逆数候補 |
| cutpositivequotient | 有効な分子と、正の有効な分母の逆数候補との積 |
| cutreciprocal | 非零の有効な切断に対して符号付き逆数を作る |
| cutsqrtcandidate | q<0または入力(q*q)という性質。非負の有効な入力が必要 |

新しいcutquotientは、分子と分母のcutreciprocalの積であり、負の分母も扱う。cutproductrelation、cutreciprocalrelation、cutquotientrelation、cutsqrtrelationは入力と結果のcutvalidを要求し、結果と候補の外延的一致を結ぶ。逆数と除算では入力または分母が零でないこと、平方根では入力が非負であることも要求する。

たとえば負の有理数を入力したcutsqrtcandidateは零の切断を返す。この候補関数の動作を、負数に実平方根があるという主張へ変えてはいけない。cutsqrtrelationは非負条件によってその入力を拒否する。条件の不成立は、例外処理や仮の数値ではなく関係の偽として表す。

## 正本の保存

[対応記録](../data/einstein-cut-products-correspondence-v1.json)はsag・sah・sca・shu・shv・sjd・sje・sju・sjt・skyを対象とする。前版13宣言と合わせた23宣言の改名が、正本全文で単射であり、未変更名を捕獲せず逆変換できることを検査する。依存先の改名以外に本体を変えない。過去の別名を同じ語へまとめたり、カントの同名宣言へ対応を流用したりしない。

新しい5定義は共有語の合成であり、正本に元からあった定義として記録しない。正本・原文の意味判断・登録簿はそのまま保持する。物理的な時計や基準系の条件も数学語の意味へ追加しない。

## 検証の範囲

[円文字の検証文書](../examples/v016/visible-cut-products-v1.noema)には28宣言と10の検査式を収め、保存SVGから復号した本体を検査する。七つの有理多項式の補題が成立し、三つの誤った平方根の主張には正確な有理数反例がある。成立する式だけを並べた理論ではなく、反例を含む検証用文書である。

多項式検証器は、実数反例が存在しない場合に有理数上の成立を認める。反例は全て有理数で、代入によって偽になると確かめた場合だけ採用する。無理数の反例しか得られない場合はunknownとし、非線形の存在量化を実数量化へ置換しない。Native 0.16から既存検証器用の0.14への投影は版ヘッダーだけを変え、宣言と式を保持する。

結果関係の引数と条件は、下位演算を明示したテスト用解釈へ差し替えて診断する。各入力・結果の有効性、零分母、零分子、負の平方根入力、左右反転、不一致の結果を区別する。タグに使う一元集合は実数切断ではなく、この診断は実数演算の一般証明ではない。下位の平方根候補自体は別に、元のNative本体と正確な算術で境界を調べる。相互関係の本体も、両方向の四つの真偽の組合せで調べる。

全実切断についての体の法則・存在・一意性・完備性の機械的証明や、二作品全体の新しい円文字への移行は今回の成果に含めない。語形は`round/red`を共通接頭部に、積・逆数・平方根・成立条件の部品を続ける。番号や登録順を語形に使わず、公開された型と定義から学習する。

```powershell
python -X utf8 -m scripts.project_work check --module scripts.check_shared_cut_products --prepare --tests tests/test_shared_cut_products.py --verify reports/shared-cut-products-v1.json
$productPages = Get-ChildItem -LiteralPath output/visible-cut-products-v1 -Filter 'page-*.svg' | Sort-Object Name | ForEach-Object FullName
python -X utf8 -m scripts.visible_products_collection decode @productPages --public-names
```

[意味規約](../data/shared-cut-products-basis-v1.json)、[公開語形](../noema/resources/visible-products-vocabulary-v1.json)、[検証報告](../reports/shared-cut-products-v1.json)を併せて参照する。旧版の辞書・描画入口・証拠は保存する。
