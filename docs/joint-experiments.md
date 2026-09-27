# 共同役割割当てと学習資料の拡張

役割を各対象で別々に選ぶと、主体が2個になり、文全体として成立しない出力が生じた。新しい復号処理では、学習した役割の確率と文の役割構成を使い、型が成立する全割当ての中から最も確率が高いものを選ぶ。割当てが同率なら未確定にする。対象を補ったり、予測した役割構成を変更したりはしない。

確信度には、成立する割当て間の相対確率だけでなく、元の役割確率も残す。制約によって候補が1個になっただけで確信度を1に上げない。数量の対象は引き続き学習した関係分類器で選び、共同割当てで決まった対象の役割へ結び付ける。数字列の一部だけを数量として取り出した場合も棄却する。

## 復号処理だけを変更した比較

既存のv4重みを固定したまま、新しい処理を開発資料で再校正した。その後、すでに失敗分析に使ったcorpus-v2の旧最終評価を回帰資料として測定した。[全結果](../reports/joint-v5.json) に開発・回帰の値を保存した。

| 入力モデル | 言語 | 回帰資料の確定率 | 確定出力の完全一致率 |
|---|---|---:|---:|
| XLM-R | 日本語 | 78.57% | 99.83% |
| XLM-R | 英語 | 74.10% | 76.25% |
| MiniLM | 日本語 | 89.29% | 81.04% |
| MiniLM | 英語 | 85.09% | 83.53% |

確定率は上がったが、英語では誤った役割を確定する件数も増えた。制約を満たす割当てが、原文の正しい意味とは限らない。この結果だけでは新しい処理を標準採用できないため、旧v4の復号処理・重み・選択記録を保持し、新版とは別に実行できるようにした。

## 学習資料の拡張

既存の学習用組合せから11,640件を追加した。数量は1桁から5桁へ広げ、12種類の新しい名前を用いた。肯否・時間・数量・態の選択を独立に抽選し、対象を先に置いた文と括弧付きの場所句も含めた。これらは学習資料の作成規則であり、解析器には読み込まない。

開発用・回帰用の文章と正解は変更せず、分割ごとのハッシュが一致することを確認した。追加例でも実際の注釈付き表面形を比較し、保留分割の構文パターンや概念の組合せを学習へ混ぜない。固定した名前や数量は [マニフェスト](../reports/corpus-v2-augmented-manifest.json) に記録した。

全22,362件について、文字範囲と概念・役割・数量・固有名が正解構造と整合すること、同義グループの正解が一致することを [内部監査](../reports/corpus-v2-augmented-audit.json) で確認した。この監査だけでは、日本語や英語の文自体が正解の意味を表すかは証明できない。

```powershell
python -m noema.augment --output artifacts/corpus-v2-augmented.jsonl --manifest reports/corpus-v2-augmented-manifest.json
python -m noema.annotation_audit artifacts/corpus-v2-augmented.jsonl
python -m noema features --dataset artifacts/corpus-v2-augmented.jsonl --model minilm --output artifacts/corpus-v2-augmented-minilm.pt --offline --batch-size 32
python -m noema.train_structured --dataset artifacts/corpus-v2-augmented.jsonl --features artifacts/corpus-v2-augmented-minilm.pt --epochs 30 --decoder joint-v1 --regression-test --output artifacts/joint-v6-minilm
```

XLM-Rも同じ条件で比較する。基盤モデルは固定したまま、分類器だけを学習する。以前のモデルや資料を上書きせず、別の出力先を使う。新しい確認評価については、予測を取得する前に [固定条件](confirmation-protocol.md) と [そのハッシュ](../reports/confirmation-protocol-record.json) を記録した。確認資料の作成・点検・実行はまだ完了していない。
