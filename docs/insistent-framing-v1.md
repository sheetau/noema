# 許容の内容と、緩めない姿勢の描写を分ける

カント第二段落の `ja keinen Schritt ... wagen durften` を、後見人側の「一歩も許容しない」という姿勢を強く描く提示として接続した。本文へ一文を追加し、既存の許容条件や目標の範囲は保持する。

## どこを強調するか

焦点は既存 `rqzx` の身体側の不許容全体である。足と過程を両方指定する形、片方指定する形、両方未指定の形について、一歩を敢えて試みることへの積極的な許容がないという内容を使う。その内容の人物・先行時点・基準時点は、同じ複文内の `rqzw` へ対応する。

追加した `hzye` は、提示者が指定した視点の担い手に帰属させる強い姿勢として、その焦点を緩めず維持するものとして示す関係である。箇所、提示者、主張、視点、焦点、文脈を別々の引数として持つ。本文では提示者は著者、描かれた視点は後見人群 `db` とする。著者がその規範を支持して命令したことや、後見人が実際に発話したことは追加しない。

一般形 `r2ab` は、同じ主張の帰属、同じ対象と描写の対応、その同じ描写への姿勢の帰属を結ぶ。本文用の `r2ac` は既存の主張 `hztr(db)`、対象側 `rqzw`、描写側 `rqzx` を渡す。内容は引用のままであり、真理値を評価してから提示を認める仕組みにはしない。

## この用例の読み

[Adelung の Ja 項目](https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_5_0_2)には、切実な依頼や禁止に伴う用法がある。[IDS の説明](https://grammis.ids-mannheim.de/systematische-grammatik/1322)も、警告や威嚇を強める働きと、命題の成立に対する修飾を区別している。歴史資料は既存の保存記録を参照し、現代文法の短い抜粋と取得時のハッシュを[出典記録](../data/insistent-framing-evidence-v1.json)へ保存した。ページ全体は保存していないため、その全体ハッシュだけからオフラインで内容を再検証できるとはしない。

この文は直接命令の引用ではなく、後見人の慎重な阻止を述べる文の内部にある。そこで、不許容を緩めない後見人側の姿勢を著者が強く描いているという文脈上の読みを採る。原刊の文字列から音声の強勢を確定したとはせず、辞典や現代文法がこの歴史的用例の読みを一意に証明するとも扱わない。

前の条件文にある `ja` の「帰結を認めやすいものとして示す」という構成や、前文 `schon` の確言とは分ける。また、強調される内容の論理条件を強くする操作でもない。量化範囲、実際の試み、成功、明示的な禁止、制裁、聞き手の同意は補わない。

## 検証

五テストで次を確認する。

- 主張・対応・強い姿勢の八組合せを、引用内容が真・偽・未知の三状態で評価する24例。
- 箇所・提示者・主張・対応・視点・焦点・文脈の十六対照。同じ箇所に別の主張がある場合も混ぜない。
- 本文の十三対照と、世界の内容が未知のまま関連七文を評価できること。
- 実際の許容定義と強調の提示を同時に評価する八例。許容がある世界でも不許容を強調する描写は表せ、許容がないだけでは強調は生じない。
- 未知入力の拒否、三記法の往復、既存49文と十一単位の意味依存関係の保持。

二定義と一つの提示関係を追加し、本文は50文となる。原文照合の `emphasis` は未接続から部分接続へ進む。各部分に何らかの対応が付いたことを、一文全体の意味一致とは数えない。家畜、局面上の落ち着き、歩行の語義範囲と節間の指示・時点・因果・描写を通して確認する作業が次に残る。

```powershell
python -X utf8 -m scripts.fetch_insistent_framing_evidence
python -X utf8 -m scripts.compose_insistent_framing
python -X utf8 -c "from scripts.check_insistent_framing import prepare; prepare()"
python -X utf8 -m pytest tests/test_insistent_framing.py -q
python -X utf8 -m scripts.check_insistent_framing
python -X utf8 -m scripts.register_insistent_framing
```

[本文](../examples/v016/kant-insistent-framing.noema)、[関連七文](../examples/v016/insistent-framing-core.noema)、[一般形](../examples/v016/depicted-insistence.noema)、[意味規約](../data/insistent-framing-basis-v1.json)、[原文照合](../data/insistent-framing-reading-v1.json)、[検査記録](../reports/insistent-framing-v1.json)を保存する。
