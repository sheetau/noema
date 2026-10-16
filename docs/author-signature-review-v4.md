# 条件と帰責を分けた本文での署名の再確認

kant-conditional-imputation.noemaへの更新後、[前回の署名の確認](author-signature-review-v3.md)を再点検した。変更したbp・be・cpと新しい帰責関係は、署名hzilの依存先に含まれない。依存する10宣言の型・本体・意味規約・引数ラベル、17番目の文、名称の四表記は不変である。

原文u0018全体と八項目の理由を再読し、同じ名称使用が同じ人物を同じ文書の著者として示すという判断を維持した。頭文字の読みは固定転記の規約に従い、原刊の略記と電子版の展開を区別する。実際の掲出者や自筆の真正性は補わない。

[判断記録](../data/author-signature-review-v4.json)は新しい本文・意味規約・識別表記、前版の判断、今回の比較検査へ結ぶ。これは同じ短い署名についてのアシスタントの読解であり、新たな原文単位の完了や独立した査読ではない。冒頭の条件の読みは部分草案のままである。

```powershell
python -X utf8 -m scripts.audit_written_progress_reviewed --index data/semantic-review-index-v3.json --verify-only
```
