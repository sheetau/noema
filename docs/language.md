# Noema a/a：文法と意味構造

## 対応する意味

一つの出来事または状態を記述する。関係は主体 `agent`、対象 `patient`、受け手 `recipient`、場所 `location` の4種。出来事の肯否と時間、実体の数量と名前を保持する。否定は出来事・状態全体に作用する。実体や数量だけを否定する構文、複雑な量化、複数の命題、入れ子、照応の解決は扱わない。

意味構造のJSONは `schema_version`、`lexicon_version`、`nodes`、`relations` からなる。対応しない追加フィールドはエラーにする。`format` で情報を落として見かけ上の往復を成立させる処理はしない。

実体ノードは `id, kind, concept, quantity, name`、出来事・状態ノードは `id, kind, concept, polarity, time` を持つ。関係は `source, role, target`。未指定の役割は `target: null` とする。省略した関係は正規化時にこの形へ展開される。1つの実体を複数の役割から参照でき、その同一性も往復で保持する。

場所の対象は `place` 型、それ以外の対象は `entity` 型に限る。述語ごとの許容役割も検査する。たとえば `sleep` に対象や受け手を与えた構造は受理しない。宣言だけ存在して参照されない実体、参照切れ、重複した役割・識別子もエラーとなる。

## 代用文字による記法

基本文字は `abcdefghijklmnopqrstuvwxyz234567` の32文字。空白と `{ } ; ?` が構造を区切る。名前と絶対日付はJSON形式の引用文字列を使う。引用文字列の内容は外部文字のリテラルであり、32文字の制約から除外する。

```ebnf
document = "noema", "a", "a", "{", { clause }, "}" ;
clause = event | entity | relation ;
event = "ev", reference, concept, polarity, time, ";" ;
entity = "en", reference, concept, quantity, name, ";" ;
relation = role, reference, (reference | "?"), ";" ;
polarity = "pos" | "neg" | "unspec" ;
time = "unspec" | "past" | "present" | "future"
     | "yesterday" | "today" | "tomorrow" | "date", json_string ;
role = "agent" | "patient" | "recipient" | "location" ;
quantity = unsigned_base32 | "?" ;
name = json_string | "?" ;
reference = basic_letter, { basic_letter } ;
```

先頭の二つの `a` はそれぞれ文法版0.1と語彙版0.1を示す。他の版は推測で読まずエラーにする。予約語も32文字から構成される。`ev` は出来事と状態の両方を宣言し、型は概念定義で決まる。1文書に1宣言だけ置ける。

数量は32進の非負整数。`a=0`、`b=1`、`c=2`、`d=3`、`7=31`、`ba=32`。先頭の余計な0は許さない。数量の `?` は未指定であり、0や1とは異なる。単数形や冠詞から数量1を補完しない。

名前はUnicodeをそのまま保持する。たとえば `en na ag ? "Aki";` と書く。引用符とバックスラッシュにはJSONのエスケープを使う。`ag` は名前によって指定された人物で、名前の省略を許さない。名前の音訳、翻訳、表記の統合は行わない。

`tomorrow` は `{ "kind": "relative", "value": "tomorrow" }` に対応する。現在日時や実行日時に置き換えない。`date "2026-09-27"` は明示された絶対日付。時間は1属性で、相対日付と時制を同時に独立指定する構文はない。その区別が必要な自然文は現行の対応範囲から外れる。基準日時による解決機能も初期版には設けていない。

## 概念一覧

識別子は学習クラスタから独立した永続語彙。意味の変更には新しい版または識別子を割り当て、既存IDへ別の意味を上書きしない。機械可読の定義は `noema/resources/lexicon.json` に置く。

| ID | 概念 | 型 |
|---|---|---|
| aa | 犬 | entity |
| ab | 猫 | entity |
| ac | 子供 | entity |
| ad | 先生 | entity |
| ae | 鳥 | entity |
| af | 本 | entity |
| ag | 名前で指定された人物 | entity |
| ah | 公園 | place |
| ai | 家 | place |
| ba | 追う | event |
| bb | 見る | event |
| bc | 助ける | event |
| bd | 渡す | event |
| be | 眠る | event |
| bf | 空腹である | state |

これはNoema自身の概念定義であり、自然文を語の照合で翻訳する対訳辞書ではない。日英の表現は学習・評価資料にだけ現れ、`analyze` から資料作成用テンプレートや名詞表を呼び出す処理はない。

## 正規形と往復

正規形では命題を `e`、実体を役割の初出順に `na, nb, ...` と名付ける。宣言を先、関係を主体・対象・受け手・場所の順に置く。元の参照名、宣言順、余白は意味に含めない。

検査対象は次の性質となる。

```python
parse(format_graph(graph)) == normalize(graph)
format_graph(parse(format_graph(graph))) == format_graph(graph)
```

自然言語と意味構造の間には、この往復保証を適用しない。異なる自然文が同じ意味構造になるかは学習器の測定対象である。名前の表記、主体と対象、数量、時間、共有参照を正規化で同一視することもない。

## SVG

8種の骨格と4位置の短い補助線から、固定した32字形を作る。各代用文字とSVG字形の対応は一対一。意味概念の数とは独立している。構造記号と引用リテラルは通常の文字で表示する。SVG内の `metadata` には正規形NoemaをXMLエスケープして保存する。

`render` は入力を検査・正規化してから描画する。画像からのOCRや、任意のSVGを逆解析する機能は提供しない。現在の字形は文字数・語長・識別性の検証を始めるための試作である。
