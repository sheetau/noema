# 導入

[English](../guide/getting-started.md) · **日本語** · [文書一覧](README.md)

## リポジトリから実行する

Python 3.11以降をインストールし、リポジトリを取得して、そのルートで実行します。構文解析と整形は標準ライブラリだけで動き、学習モデル、ネットワークサービス、保守担当者のDBを必要としません。

```sh
git clone https://github.com/sheetau/noema.git
cd noema
python -X utf8 -m noema.constructed parse -i examples/intro/scope.noema
python -X utf8 -m noema.constructed format -i examples/intro/scope.noema --notation full
```

リポジトリ内で使う場合は必須ではありませんが、編集可能なパッケージとしてインストールすることもできます。

```sh
python -m pip install -e .
```

記述合成を含む構文0.16には `python -m noema.constructed` を使います。`noema` コマンドと `python -m noema` は以前の入口であり、すべての文書で置き換えられるわけではありません。文書中の構文版と、言語の完成版番号は別です。

## 例を読む

[scope.noema](../../examples/intro/scope.noema) の内容は次のとおりです。

```text
p:
r aa[a a] c.
s[f x a[g y a[k aa[v x v y]]]].
s[g y a[f x a[k aa[v x v y]]]].
```

`p:` は構文0.16を選びます。`r aa[a a] c.` は、二つの個体を引数に取り、真理値を返す関係の宣言です。`aa` はこの例の局所名で、宣言だけでは経験的な意味を与えたことになりません。

`s[...]` は主張、`f` は全称束縛、`g` は存在束縛です。`k aa[...]` は関係の適用、`v x` は束縛変数の使用を表します。二つの文は、それぞれ次を述べます。

1. すべてのxについて、aa(x, y)を満たすyがある。
2. すべてのxについてaa(x, y)を満たす、共通のyがある。

違いは存在量化の作用域です。二対象の領域でaaを同一性と解釈すると、前者は真、後者は偽になります。これは例示の解釈であり、辞書全体で `aa` にその意味を与えるものではありません。「各人が何か本を読んだ」と述べるには、人・本の条件と読む関係を加えます。[言語ガイド](language.md)で説明します。

出力JSONは束縛名を正規化しながら、量化順と参照先を保持します。解析成功は構造と型の確認であり、解釈が与えられていることや、文が真であることを保証しません。

## 保存とAPI

CLIでは `-o` で新しいファイルへ保存できます。既存ファイルは上書きしないため、まだ存在しないパスを指定します。

```sh
python -X utf8 -m noema.constructed parse -i examples/intro/scope.noema -o scope.json
python -X utf8 -m noema.constructed format -i examples/intro/scope.noema -o scope-formatted.noema
```

Python APIはテキストのNoemaを受け取り、正規化済み文書を返します。

```python
from pathlib import Path
from noema.constructed import parse, format_graph

document = parse(Path("examples/intro/scope.noema").read_text(encoding="utf-8"))
text = format_graph(document, notation="compact")
assert parse(text) == document
```

これはテキスト構文の往復確認であり、図形復号の検査ではありません。

## テキスト記法と円文字

短い文字と括弧の記法は、編集用のテキスト表現です。採用円文字には別の幾何規則と範囲付き省略があります。CLIの `--script` と `render` は旧来の文字フォントを使い、**採用した接続円文字の出力ではありません**。

現在の読取・符号化APIは[円文字ガイド](writing.md)、描画済みの版は[作品と例](works.md)を参照してください。ここでは、円文字の全出版物を再構築する単一のインストール済みCLIコマンドは案内していません。生成スクリプトは固定した原本と証拠を使うもので、言語を試すために再生成する必要はありません。

次は[言語ガイド](language.md)と[語彙ガイド](vocabulary.md)へ進めます。
