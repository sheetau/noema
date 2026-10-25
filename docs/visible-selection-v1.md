# 数値選択と多部分の円文字本文

円文字辞書第6版は、[第5版](visible-quantity-library-v1.md)の171語を保持し、[数値選択](shared-selection-v1.md)の5語を加えた176語である。30の単独語と146の複合語、21の基本宣言と155の構成定義からなる。旧proportionsの真理値・数値対応を共有したもので、新しい基本関係や字形は導入していない。同じ版番号で語義・型・綴りを変更した辞書は拒否する。

| 語 | 役割 |
| --- | --- |
| truthindicator | 真を1、偽を0とする既存の基本宣言 |
| indicatorvalid | 上の対応を両真理値について確認する |
| occurrencecount | 列の該当箇所を数える。重複も数える |
| selectnumber | 条件によって二つの有理数値を選ぶ |
| countselected | 重複のない個体列について、条件を満たす個体を数える |

選択は遅延評価ではない。両方の数値を評価できることが必要であり、選ばれない枝の未知値を隠さない。共有語の詳細な型・役割・解釈は[登録資料](../data/shared-selection-basis-v1.json)にある。

## 二つの部分と全体

[可視本文のNative正本](../examples/v016/visible-multipart-amounts-v1.noema)は、異なる二部分の値を250、500、全体を750とする仮想例である。第二の図では400、600、1000を使う。どちらも正の無次元量を共通単位で述べる。水の体積・米の質量という物理的な種類や次元をこの図で指定したわけではない。

対象から値を選ぶ関数はNoemaのlambdaとselectnumberで定義する。その同じ関数を、測定関係とamountsumの読みへ渡す。単位登録・測定・部分・非重複・完全性の各関数も本文に含み、外部コールバックは共有された四つの算術・真理値基本宣言だけである。測定関係は二部分と全体だけを対象にするため、数値関数の既定値から未知対象の測定を認定しない。

対象、量の種類、単位、状況の変数は独立して束縛する。測定関数を一度定義し両方から参照することで、重複した本文の展開を避ける。描画幅4800で既存の図形数・文字数の上限に収まり、円・線だけのSVGから全変数と関数を復元する。字体・上限・旧デコーダは変更していない。

## 確認の範囲

[検証報告](../reports/visible-selection-v1.json)は、5語の型付き呼出しと引用、語彙文書、出現数と個体数を区別する文書、二つの合計文書の図形復号を記録する。復号したASTを正本と比較してから、Native本文の意味を検査する。全体の数値を誤らせる反例では合計が偽になる。

多部分の評価は束縛診断である。三対象の割当を保ち、量の種類と単位を一枠ずつ変えて五通りを調べ、状況は二値で検査する。他の枠を具体化するため、全役割の直積や任意領域の証明ではない。実際の測定の根拠、ラスター画像のOCR、第三者の読解も別の課題である。

```powershell
python -X utf8 -m scripts.visible_selection_page render examples/v016/visible-multipart-amounts-v1.noema output/visible-selection-library-v1/multipart-copy.svg --width 4800 --public-names
python -X utf8 -m scripts.visible_selection_page decode output/visible-selection-library-v1/multipart-copy.svg --native --public-names
```

第1〜6版は可視ヘッダーで区別する。第5版以前の本文と証拠は保持し、過去の局所定義を新しい共有語の意味へ置き換えない。
