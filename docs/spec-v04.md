# 文語0.4の構文・意味構造の仕様

この仕様は、人が直接記述するNoemaの文語0.4を定める。自然言語解析器の予測精度とは独立した契約である。基本語と許容役割は0.3の版付き語彙、複合語の性質は `language-v04.json` で定める。旧版の文書を0.4の規則として黙って読むことはしない。

## 字句と構文

基本文字は `a–z, 2–7` の32文字で、固有文字のU+E000〜U+E01Fと一対一に対応する。以下の構文は代用文字で示す。引用文字列の内容は文字変換の対象にしない。

```ebnf
document = "noema", "d", "d", utterance, { utterance } ;
utterance = [ speech_act ], expression, "." ;
speech_act = "b" | "d" ;
expression = clause
           | "[", expression, "]"
           | "u", expression
           | connective, "[", expression, "]", "[", expression, "]" ;
connective = "w" | "x" | "y" ;
clause = { clause_modifier }, predicate_word, { role, term } ;
clause_modifier = time | "v" ;
time = "e" | "f" | "g" | "r" | "s" | "t" | "q", json_string ;
role = "i" | "j" | "k" | "l" | "z" | "2" | "3" | "4" ;
term = "?" | "c" | "p", reference | nominal, { entity_modifier } ;
nominal = entity_word, { "-", property_word } ;
entity_modifier = "m", unsigned_base32 | "n", json_string | "o", reference ;
reference = basic_letter, { basic_letter } ;
```

`predicate_word` は出来事か状態の基本語、`entity_word` は対象か場所の基本語である。`property_word` は指定された13種類の性質に限る。`-` の前後には空白を置かず、複合語を一つの字句として読む。その他の字句間には空白・改行を置ける。基本文字だけの字句は連続した文字を最長で取り込むため、語同士を区別するには空白が必要になる。

`json_string` はJSONの引用文字列で、引用符とバックスラッシュなどはエスケープする。名前は空文字列と不正なUnicodeを拒否する。日付には正確な `YYYY-MM-DD` 形式の実在する日を使う。数量は非負の32進整数で、`a` だけが0を表す。複数文字の数量の先頭に `a` は置けない。

構文に加え、次の制約を検査する。

- 一つの節で時間と肯否未指定の標識をそれぞれ1回まで使える。同じ役割を2回書けない。
- 一つの対象で数量・名前・参照登録をそれぞれ1回まで使える。複合語の同じ性質は重複できない。
- 未指定ではない役割は、その述語が許す役割と型を満たす必要がある。型の検査から現実の真偽は判定しない。
- `c` は質問文の役割に限る。`p` はそれ以前に登録した参照だけを使える。参照名の再定義は禁止する。
- 式の入れ子は実装上64段を上限とする。これを超える文を一部だけ読むことはしない。

## 文書と発話

文書JSONは `schema_version, lexicon_version, entities, utterances` だけを持ち、両版は `0.4` とする。`entities` は対象の配列、`utterances` は空でない発話の配列である。追加フィールドを無視して読み進めず、誤った版・型・キーをエラーにする。

各発話は `speech_act` と `content` を持つ。通常は `assertion`、先頭の `b` は `question`、`d` は `request` となる。同じ節を使っても、断定・質問・依頼は別の意味構造である。出来事が起きたかどうかと、それについて依頼・質問したことを混同しない。

`content` は次のいずれかの式となる。

| kind | フィールド | 解釈 |
|---|---|---|
| clause | predicate, polarity, time, roles | 述語に役割・肯否・時間を付けた節 |
| not | body | bodyの内容の否定 |
| and | left, right | 両方の内容 |
| or | left, right | 少なくとも一方の内容 |
| if | left, right | leftを条件とするright |

式には `kind` 自身も含める。`and/or/if` の左右、発話の順、否定の入れ子を正規化で入れ替えたり消したりしない。`or` は排他的な選択ではない。`if` に因果・反事実の意味を追加せず、文の順番を出来事の時間順にも読み替えない。

## 節・対象・参照

節の `predicate` は概念ID、`polarity` は `affirmed` または `unspecified`。否定は `not` 式で表す。時間は `kind, value` の対で、未指定、過去・現在・未来、昨日・今日・明日、絶対日付を区別する。基準日がない相対日を実行日に置き換えない。

`roles` のキーは主体・対象・受け手・場所・出発地・到着地・道具・受益者の8種類。値は対象ID、未指定の `null`、質問の `{"query": true}` のいずれかである。正規形では8種類すべてのキーを置く。省略と明示的な未指定は同じ構造へ正規化する。

対象は `id, kind, concept, qualifiers, quantity, name` を持つ。`kind` は基本語に従う `entity` または `place`、`concept` は基本概念ID、`qualifiers` は性質の概念ID列である。数量と名前は未指定なら `null`。複合語の数量は、基本概念とすべての性質を満たす個々の対象を数える。性質の日時や場所は未指定で、主節から自動的に補わない。

参照は文書内の同一対象を明示する。二つの別の対象IDから「現実にも必ず別物」とは推論せず、同じ名詞や同じ名前からIDを統合することもしない。条件や否定の中に参照を導入しただけで、独立した存在命題や肯定文を追加しない。複雑な量化や照応解決はこの版の機能に含めない。

## 正規化と版変換

正規化では役割順と初出順に従う対象IDを固定し、参照名を統一する。性質の列は概念IDで整列する。語順の変更、余白、元の参照名、性質の順序は、この規則の範囲で意味JSONに残さない。一方、型・数量・名前・共有参照・発話種別・式の構造は保持する。

保証する往復は次のとおり。

```python
parse(format_graph(graph)) == normalize_document(graph)
parse(encode(format_graph(graph))) == normalize_document(graph)
```

旧版から0.4へ変換すると、各対象に空の `qualifiers` を追加する。0.4から旧版へ戻すとき、性質のある対象は変換を拒否する。複合語を別の肯定文へ分解すると否定や質問の範囲が変わり得るため、自動変換で補わない。その他の旧版にない概念・役割・発話・式についても、その版への変換は拒否する。

新しい基本概念を追加する場合は、新しい版付き語彙・ID・語形・型・役割と正例／拒否例を定義する。既存版のIDの意味を変えない。既存の基本語と性質だけを組み合わせる場合は、個々の複合語の登録やモデルの変更は不要である。
