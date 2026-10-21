# 敬称付きの自己呼称

`ehrwürdige Klassis (wie sie sich unter den Holländern selbst nennt)`を、会議体の制度的内容と、敬称付きの自己呼称の両方を持つ名詞句として構成した。[classis-self-name.noema](../examples/v016/classis-self-name.noema)の`r46o`が、同じ会議体・基準について二つを結ぶ。本文の問い全体はまだ統合していない。

Klassisの制度的内容には[地区会議の構成](church-councils-v1.md)`r46k`を使い、`r46l`で名称が保持する閉じた性質記述にする。既存`hw2`へその記述を渡すため、名称の原語表記だけで制度的な意味を代用しない。敬称形式と慣用的な名称採用を、別の基本関係`h254t`と`h254s`で保持する。

`r46m`は使用主体・対象・名称・用法共同体を明示する一般構成で、`r46n`は使用主体と対象を同じ会議体へ固定する。著者や第三者だけが呼ぶ場合は、自己呼称の条件を満たさない。用法共同体は採用読解で十八世紀のネーデルラントの人々の間の用法を指す。これは会議体の所在地や成員全員の国籍を指定する条件ではない。

ehrwürdigは、呼称に敬意を示す定型的な形式が含まれることとして読む。[デュースブルク改革派の議事録集](https://www.archive.nrw.de/sites/default/files/media/files/Duisburg_Classis_3__1736_1768.pdf)の略語表と本文に、この種の敬称を伴うClassisへの言及があり、形式を読む補助根拠とした。[取得記録](../data/classis-title-evidence-v1.json)にはPDFと該当ページの短い照合箇所を固定した。この史料をオランダの特定会議と同一視せず、カントの敬愛や皮肉の証明にも使わない。

採用する括弧の読みでは、自己呼称の説明は敬称付きの名辞全体にかかる。形式上の敬称を保持しつつ、対象が実際に尊敬に値すること、著者が心理的に敬愛していること、永久拘束の権限があることは補わない。原文の綴りと範囲は[読解記録](../data/classis-self-name-reading-v1.json)に保持した。

[検査](../reports/classis-self-name-v1.json)は、使用主体と対象の入れ替え、別の名称・用法共同体・基準・意味記述・引用段階・敬称形式を区別する。名称の採用だけでは分類の真理が成立しないことも、二つの独立した条件で検査する。制度的分類の実評価には前回の検査記録を使い、自己呼称の評価時には引用された制度内容を実行しない。

次はetwaの例示と一般の団体への位置付け、否定疑問の権限、同じ不変信条への相互誓約、全成員とそれを介する人民への上位後見・持続、直後の回答を統合する。名詞句の構成と全文の意味判断を区別し、今回も確認済み文字数を加算しない。

```powershell
python -X utf8 -m scripts.project_work check --module scripts.check_classis_self_name --tests tests/test_classis_self_name.py --prepare --verify reports/classis-self-name-v1.json
```
