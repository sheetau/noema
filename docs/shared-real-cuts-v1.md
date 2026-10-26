# 実数の下側切断を共有語と円文字へ接続する

アインシュタイン正本にある実数の下側切断の9定義を、共通の名前と円文字の綴りへ接続した。有理数の比較・和・加法逆元・積は既存の4基本関係をそのまま使う。新しい基本関係は追加しない。円文字辞書第13版は384語、361定義、23基本宣言になり、旧375語の型・意味規約・綴りを保持する。

## 定義と利用条件

| 共有語 | 意味と条件 |
| --- | --- |
| cutvalid | 有理数上の性質が非空・全域でない・下方閉・最大元なしを満たす |
| rationalcut | 有理数rを、q<rという性質で表す。境界rは含めない |
| cutincluded | 左の性質が右に含まれる。両方が切断なら左の値は右以下 |
| cutadd | 左の元xと右の元yがあり、q<x+yとなるqの性質 |
| cutnegate | 元に含まれないuがあり、q<-uとなるqの性質 |
| cutdifference | 左に、右のcutnegateを加える |
| cutless | 左が右に含まれ、右は左に含まれない |
| cutmidpoint | 中間−先頭と最後−中間が全有理数で同じ性質 |
| cutpositivescale | 正の有理数尺度による拡大。尺度が0以下なら空の性質 |

型は有理数から真偽への関数であり、この型だけで実数の切断とは決まらない。空の性質、全域で真となる性質、最大元を含む性質も同じ型を持つ。実数として演算する場合はcutvalidなどの利用条件を別に要求する。cutmidpointの等式から時計・単位・基準系・光信号の物理条件は導かない。

## 正本との対応

[対応記録](../data/einstein-real-cuts-correspondence-v1.json)は、選択中のアインシュタイン正本の13宣言を対象にする。四つの基本関係は、型の一致に加え、正確な有理数演算という意味規約と引数順が既存共有語に一致することを確認した。九つの定義は、依存先を含む名前の変更以外に型と本体の変更がない。

対応を全文の宣言集合に対して単射に保ち、逆変換によって元の構造へ戻ることを確認する。異なる名前を同じ共有語へ統合せず、未変更の名前も捕獲しない。引用内部の名前もこの規則で対応させる。同じ記号を使うカントの宣言へ、この対応表を流用してはいけない。

正本、原文単位の意味判断、登録簿は変更しない。共有定義の意味説明は数学的な関係として書き直し、時計同期に適用する条件と分けた。この一般化は型と定義本体に基づくもので、原文の物理的な主張を増減する変更ではない。本文の使用箇所も対応記録に残す。今回の13宣言だけで全文の語形対応が完了したとはしない。

## 円文字と検証

新しい語形は `round/red` を切断語群の接頭部とし、包含に `inside`、加算に `give`、符号反転に `candidateexcluded`、順序に `above`、正の拡大に `treeone` を使う。綴りは型と定義を思い出す手掛かりであり、その部品だけから真理を推論しない。番号、ハッシュ、登録順から名前を生成していない。

[検証文書](../examples/v016/visible-real-cuts-v1.noema)は、13宣言と16の算術検査式を含む。保存SVGを文書群書式から読み戻し、その復号結果を補助検証器へ渡す。16式のうち12式は有理数埋込みの法則として成立し、4式は空・全域・閉境界・差の逆転に関する意図的な誤った主張である。検査式の全てを真な理論として採用する例ではない。

補助検証器は線形の有理数量化を扱う。Native 0.16から検証器が受け取る0.14への明示的な投影を行い、版ヘッダー以外の宣言と式が変わらないことを確認する。数の領域を有限標本へ置換せず、非線形な有理数量化は拒否する。有理数埋込みについての結果を、全実切断の体の法則や完備性の機械的証明とはしない。境界の所属は有限評価器でも別に確認する。

成果物は[共有Native定義](../examples/v016/shared-real-cuts-v1.noema)、[意味規約](../data/shared-real-cuts-basis-v1.json)、[円文字語形](../noema/resources/visible-cuts-vocabulary-v1.json)、[検証報告](../reports/shared-real-cuts-v1.json)、`output/visible-real-cuts-v1/` のSVGである。旧版の辞書・ページ・文書群の入口は保持する。

```powershell
python -X utf8 -m scripts.project_work check --module scripts.check_shared_real_cuts --prepare --tests tests/test_shared_real_cuts.py --verify reports/shared-real-cuts-v1.json
$cutPages = Get-ChildItem -LiteralPath output/visible-real-cuts-v1 -Filter 'page-*.svg' | Sort-Object Name | ForEach-Object FullName
python -X utf8 -m scripts.visible_cuts_collection decode @cutPages --public-names
```

二作品の残る語形と基本関係、全文の図形復号、独立した読者による確認は続く課題である。
