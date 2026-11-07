# 語彙と定義

[English](../guide/vocabulary.md) · **日本語** · [文書一覧](README.md)

[日英辞書](../dictionary/index.html?lang=ja)は全1,952項目の語義・引数役割・文脈と、関連する公開規約・命名規則を収録します。既定表示は英語で、日本語へ切り替えられます。単独のローカルHTMLとして開け、閲覧に翻訳モデルやネットワークサービスは不要です。

[英語カタログJSON](../../data/general-language-catalog-en-v1.json)は、基本宣言1,489項目と合成定義463項目です。以前の1,909項目に意味境界の43定義を統合しました。項目数は辞書の収録数であり、表現力の点数ではありません。[日本語の原カタログ](../../data/general-language-catalog-v2.json)も変更せず保存します。

| 再利用区分 | 項目数 | 使い方 |
| --- | ---: | --- |
| 共通語 | 375 | 語義・型・順序付きの役割・文脈を保持する |
| 共通追加 | 62 | 確率・解釈・意味境界の合成を再利用する |
| 分野別の意味規約 | 1,488 | 単位・尺度・制度・比較域など、必要な条件を保持する |
| 作品内参照補助 | 27 | 固定事例の対象を指す。参照先を汎用概念として流用しない |

## 項目を読む

カタログの `entries` は名前から宣言・綴り・語義・出典へ対応します。主なフィールドは次のとおりです。

| フィールド | 内容 |
| --- | --- |
| `declaration` | 基本記号の型、または型付き引数・結果・本体を持つ定義 |
| `spelling`, `symbol` | 根による綴りとテキスト記号 |
| `meaning`, `roles` | 語義と順序付きの引数役割 |
| `context`, `contrast` | 必要な条件と保持する区別 |
| `sources` | 項目を支える原本ファイル |
| `portability`, `usage` | 再利用区分と制約 |
| `naming_convention`（プロファイル） | 語群の根による綴りの決め方 |
| `public_contracts`（語義規約） | 項目ごとの引数条件・結果型・`interpretation_inputs` |
| `meaning_en`, `meaning_ja`（対訳付き規約） | 英語の説明と保存した日本語の原文 |

英訳には語義・役割・解釈入力・引数ごとの条件・命名規則・制限と、選択した公開辞書原本内の日本語の説明を含めます。閲覧ページの「規約と原本」で参照でき、各項目にも対応する公開規約があれば表示します。

訳文は原本の内容に結び付けた別の説明層です。日本語の意味規約・識別子・型・定義・元の証拠を保持します。英訳にはローカルモデルの補助を使い、全件の被覆・構造検査と一部の対訳点検を行っていますが、全件の独立した翻訳審査は行っていません。[翻訳範囲の記録](../../reports/dictionary-localization-v3.json)に点検範囲を記載します。新しい意味同値の判断を成立させるものではありません。

例えば `above` は、個体二つを取り真理値を返す基本記号です。指定した空間的な上下軸と比較方法で、第1対象が第2対象より上にあることを表します。接触・支持・順位の優越は含みません。位置と時点も文脈に関わり、引数の型が同じでも交換すれば意味が変わります。

既定で英語を返し、明示すれば日本語を返します。

```sh
python -X utf8 -m noema.dictionary --entry above
python -X utf8 -m noema.dictionary --entry above --language ja
python -X utf8 -m noema.dictionary --source noema/resources/visible-action-occurrence-visible-profile-v1.json
python -X utf8 -m noema.dictionary --source data/action-occurrence-visible-profile-basis-v1.json
```

後半のコマンドでは、翻訳した `naming_convention`・`meaning_en`・引数条件・`interpretation_inputs` を参照できます。`meaning_ja` を英語へ変えて誤った名前にせず、日本語のまま保持します。`--language ja` は選んだ原文書を返します。`-o NEW_FILE.json` で既存ファイルを上書きせず保存できます。原本が変わった場合や訳の欠損時は拒否し、古い訳や未翻訳の文を黙って返しません。

モデルや台帳を必要としないリポジトリAPIもあります。

```python
from noema.dictionary import read_source

catalog = read_source()  # English by default
entry = catalog["entries"]["above"]
print(entry["declaration"])
print(entry["meaning"])
print(entry["roles"])
```

## 新しい概念を導入する

1. 必要な対象・状況・引数の順序と役割・型を決めます。
2. 既存の定義を探し、その条件を保って組み合わせます。
3. 合成できる部分をNoemaで定義します。残る経験的関係や文化規約には、何を認め、何を認めず、どの文脈を使うかを説明します。
4. 小さな対照例を確認します。参加者・時点・記述・作用域を変えたとき、意図した意味の違いが残るかを調べます。

新しい制度なら、参加者・役割・成立手続・義務・時期などが必要になります。感覚なら経験者と経験を区別する条件が必要で、物理量へ還元することまでは求めません。どちらも名前を付けただけでは説明になりません。

原文の一文の結論だけを判定する基本語を設けたり、原文を引用文字列として保存しただけで意味を合成したことにしたりしません。定義は別の文でも同じ意味で再利用できるものにします。

## よく使う合成

**確率。** 有限確率は、重複のない事例列、非負の有理数の重み、総和1から構成します。事象の確率は条件を満たす事例の重みの和です。条件付き確率は条件の重みが正の場合に限り、0で既定値を補いません。未知入力を拒否します。無限分布には測度などの条件を明示し、有限標本を全体の代用にしません。[確率の規約](../dictionary/index.html?lang=ja&view=sources&q=general-probability-basis-v1.json)と[対照例](../../data/general-probability-contrasts-v1.json)を参照してください。

**解釈と社会的行為。** 比喩は源と先の特徴・対応・字義・意図した記述・読みの根拠を保持できます。皮肉を、偽の字義の単純な否定へ限定しません。謝意・約束・助言・制度上の宣言は、特定の行為へ参加者・内容・規約・条件を結びます。基本発話の三種だけで社会的な成功は決まりません。[語用の規約](../dictionary/index.html?lang=ja&view=sources&q=general-pragmatics-basis-v1.json)を参照してください。

**実在と情報。** `actualtargetwitness` は記述された性質と同じ状況での実在を結びます。`uniquevalue…`・`missingvalue…` は適用条件と完全性を保ち、列版は有限候補を扱います。`reportedsupport` は出所付きの支持を記録し、`valueconflict…` は関連する値の一意性も要求します。それぞれ別の構成であり、「不明」を示す交換可能なラベルではありません。[意味境界の定義](../dictionary/index.html?lang=ja&view=sources&q=semantic-boundaries-basis-v1.json)を参照してください。

**束縛された内容。** `boundcontent…` は閉じた内容関数の記述と型付き引数値を組にします。`boundcontentholds…` で初めて、その値と指定状況で評価します。引用内に自由変数を捕獲せず、有限の型付き引数列へ一般化できます。

作用域と型は[言語ガイド](language.md)、これらの構成検査と新しい翻訳の意味審査の違いは[証拠ガイド](evidence.md)を参照してください。
