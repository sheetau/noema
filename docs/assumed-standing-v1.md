# 発言上の立場と、その条件の不足

カントu0012の *vorwitziger Tadel* について、前版で引数として残していた評価性質を、既存の文法から合成する読解候補を追加した。同じ人が同じ批判行為で発言上の立場を自ら取り、その立場を取るために明示した条件の少なくとも一つが不足する、という構成である。カントの語の必要十分条件を確定したものではない。

語義資料では二つの点を確認した。Adelungの1811年版は形容詞を名詞 *Vorwitz* によって説明し、その名詞を性急な知的欲求から説明している。一方、DWBは出過ぎた発言・振舞いを非難する用法と批評の用例も記録する。このため、単なる知識欲や、許可されていない行為という定義には固定しなかった。[Adelungの形容詞項目](https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_5_1_1903)、[名詞項目](https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_5_1_1902)、[DWBの項目](https://www.dwds.de/wb/dwb/vorwitzig)を設計の根拠として用いた。

「自ら取った立場」と「その立場の条件不足」へ分けるのは、これらの用例を踏まえた設計上の推論である。辞書にこの論理式が示されているわけではない。Adelungの利用した版は編者の補訂を含む1811年版であり、DWBの項目は1951年刊の歴史的用例整理である。どちらも、カントの1784年の当該使用を一意に解説した資料ではない。取得先・版・日時・短い引用・原データのハッシュは[資料記録](../data/vorwitzig-reading-v1.json)に保存した。

| 記号 | 内容 |
| --- | --- |
| `rfp` | 同じ人・発言上の立場について、指定条件列の少なくとも一つが文脈内で不成立である内容。 |
| `rfq` | その人がその行為でその立場を自ら取り、同じ文脈で`rfp`が成立する内容。 |
| `rfr` | 本人・立場・条件列・立場を取る関係を固定し、行為から`rfq`の内容への関数を作る。 |
| `hza4` | 先行する批判の前件`hzay`へ、評価性質として`rfr`を渡す。 |
| `hza5` / `hza6` | 同じ合成した評価性質を、条件文`hza2`と前件の実例の存在`hza3`へ渡す。 |

立場は正式な役職に限らず、その場で何を判断・指図する側として振舞うかを含む。条件は人と立場から命題内容への関数の列で与える。例えば別の共同体や活動について記述する際には、条件列と立場を取る関係を説明して差し替える。語の固定表や新しい「僭越」という基本記号は追加していない。

条件が一つ不足していても、その人が当該行為でその立場を取っていなければ`rfq`は成立しない。また、別人や別の立場についての不足を流用しない。空列から不足を導かず、条件の真偽が未知なら評価を停止する。重複や順序は不足の有無を変えない。条件を満たすことが正当な立場を保証するか、条件列が必要な条件を尽くすかは別の問題として残す。

前件と帰結を含む64通り、引数の対応を変えた7対照例、条件列の4対照例を検査した。全文草案と独立抽出文書の結果は一致する。旧評価性質の入力、発言内容の真偽、処罰の許可を未評価のままにしても、新しい式は評価できる。資料は設計時の根拠であり、Noemaの解析・評価時に外部辞書を検索したり、自然言語の語を個別規則で変換したりはしない。

この候補では、未展開だった評価性質を二つの条件へ分解した。立場を取る関係の基礎説明、評価条件の採用根拠、非難の強さや語用論、別の語義候補を排除できるかという確認は残る。*Skandal*、*sogar*、*demohngeachtet* と制度の説明も未完である。原文範囲の追加はなく、意味確認済みの区間も増やしていない。

6定義を追加し、基本記号と著者主張は追加していない。全文草案は90,928代用文字で、親からの増分は1,277文字、独立抽出文書は5,352文字である。

- [全文草案](../examples/v014/kant-assumed-standing.noema)と[意味基盤](../data/kant-assumed-standing-basis-v1.json)
- [一般例](../examples/v014/assumed-standing.noema)と[独立抽出文書](../examples/v014/assumed-standing-core.noema)
- [検査結果](../reports/assumed-standing-v1.json)、[検査器](../scripts/check_assumed_standing.py)、[回帰検査](../tests/test_assumed_standing.py)

```powershell
python -X utf8 -m scripts.check_assumed_standing --verify-only
python -X utf8 -m pytest tests/test_assumed_standing.py -q
python -X utf8 -m noema parse -i examples/v014/assumed-standing-core.noema -o artifacts/assumed-standing.json
python -X utf8 -m noema render -i examples/v014/assumed-standing-core.noema -o artifacts/assumed-standing.svg
```
