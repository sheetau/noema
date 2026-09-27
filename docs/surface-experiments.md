# 文型の追加・未知範囲の学習と確認評価v2

予測前に固定した新しい人工文で、日英とも確定率80%以上・確定出力の完全一致率95%以上・未対応の誤確定率5%以下を満たした。ただし、別の手書き回帰資料では代名詞などの誤確定が増えた。15概念の指定した短文に関する数値条件の達成と、自由な入力で使えるかという判定を分ける。

## 学習資料と選択

前回の [確認評価v1](joint-experiments.md) では、英語の場所句を途中に挿入した文と、日本語の未知概念の判定が不足していた。今回は一般的な文型の変化として、英語の場所句の挿入と大文字開始、句点なし、日本語受動態の「に」、主体を省いた能動文を追加した。推論時に使う修正規則は追加していない。

未知概念には24種類の名詞を学習用に用意し、文全体の未対応ラベルだけでなく、未知語の文字範囲にも既存の「概念なし」クラスを教えた。訓練と開発に使う文字特徴量・分類器・共同役割割当ては前版と同じで、XLM-RとMiniLMのエンコーダーも固定している。追加17,816文のうち、未知概念の範囲注釈を持つ例は2,757文となった。全40,178文の [構成数と監査](../reports/corpus-v7-manifest.json) を保存した。旧開発・回帰分割の文と正解は変更していない。

両候補を30エポック学習した。開発用の選択条件による保存時点はMiniLMが15、XLM-Rが20エポック。分類器のパラメーター数はそれぞれ308,403個、374,451個で、CPUの実測学習時間は約20.6分、22.4分だった。日英とも開発用成績でXLM-Rが選ばれた。[モデル別結果](../reports/joint-v7.json) と [選択記録](../reports/routed-v7-selection.json) を保持した。

## 新規事例での確認

v1と同じ構文系統から、新しい数量・名前などを組み合わせた300種類の意味構造を作り、日英各2表現で計1,200文とした。学習・開発・旧回帰・v1の完全な意味構造および入力文との重複はない。未知概念には学習に使っていない狼・栗鼠・ハムスターを用いた。[事前条件](confirmation-v2-protocol.md)、[予測前点検](confirmation-v2-review.md)、[重みと資料の固定記録](../reports/confirmation-v2-manifest.json) は、v2の予測を取得する前に作成した。

| 言語 | 確定／対応範囲内 | 確定率 | 正解／確定 | 完全一致率 | 未対応の誤確定 |
|---|---:|---:|---:|---:|---:|
| 日本語 | 579 / 600 | 96.50% | 566 / 579 | 97.75% | 0 / 72 |
| 英語 | 541 / 600 | 90.17% | 541 / 541 | 100.00% | 0 / 72 |

[確認評価の全集計](../reports/confirmation-v2-result.json) では両言語が固定条件を通過した。英語で場所句を主語と動詞の間に挿入した129文は、全件を正しく確定した。日本語の誤確定13件は主体・対象の取り違え12件と時間1件だった。「犬は子供を家で追った」のような主題を先に置く文でも取り違えが残る。

同義グループ300組のうち全4文を確定したものは230組、その中で構造が一致したのは218組。個々の言語の完全一致率が条件を通っても、すべての言い換えを同じ意味へ変換できたことにはならない。両言語6文ずつの反復、単独／一括実行の意味一致、全確定出力のNoema往復も確認した。

## 回帰結果と残る後退

| 資料 | 日本語の確定率／完全一致率 | 英語の確定率／完全一致率 | 未対応の誤確定（日／英） |
|---|---:|---:|---:|
| 旧corpus-v2 | 98.68% / 100% | 98.43% / 100% | 0 / 109、1 / 116 |
| v1確認資料の再測定 | 96.33% / 97.23% | 92.50% / 100% | 0 / 72、0 / 72 |
| 従来の手書き例 | 100% / 100% | 100% / 100% | 1 / 7、2 / 7 |

[旧回帰集計](../reports/routed-v7-regression.json)、[v1の再測定](../reports/confirmation-v1-v7-regression.json)、[手書き回帰](../reports/routed-v7-hand-regression.json) を保存した。手書き例の対応範囲内28文はすべて正解で、「猫が犬に追われる」「猫を追う」の従来の失敗も解消した。

一方、未対応と注釈した「彼女が眠る」「She sleeps」「Hope sleeps」を確定した。旧v6ではこの3文を棄却しており、未対応判定の後退である。「Hope」は人名にも抽象名詞にもなり得るため、文脈のない入力の解釈が一意かという注釈上の問題も含む。代名詞・抽象概念・名前の曖昧さを分けて検証し、特定の入力文字列に対する例外規則で補正しない。

今回の確認は既知の構文系統での新規事例であり、人が自由に書いた文章の評価ではない。解析語彙も15概念のままで、直接記述できる文語0.3の91概念とは範囲が異なる。これらの未対応判定と文語の利用者評価が残るため、全体の完成は宣言しない。

## 再現する操作

```powershell
python -m noema.surface_corpus --output artifacts/corpus-v7.jsonl --manifest reports/corpus-v7-manifest.json
python -m noema features --dataset artifacts/corpus-v7.jsonl --model xlmr --output artifacts/corpus-v7-xlmr.pt --offline --batch-size 32
python -m noema.train_structured --dataset artifacts/corpus-v7.jsonl --features artifacts/corpus-v7-xlmr.pt --epochs 30 --decoder joint-v1 --regression-test --output artifacts/joint-v7-xlmr
```

MiniLMも同じ条件でモデル名と出力先を変えて比較する。次の資料作成は学習中に行い、モデル選択から先は両モデルの学習完了後に実行した。記録済みの出力先は上書きせず、最初の実行結果を保持する。

```powershell
python -m scripts.build_confirmation_v2
python -m scripts.select_routes artifacts/joint-v7-xlmr artifacts/joint-v7-minilm --output artifacts/routed-v7 --record reports/routed-v7-selection.json
python -m scripts.freeze_confirmation_v2
python -m noema.evaluate_confirmation --dataset artifacts/confirmation-v2.jsonl --manifest reports/confirmation-v2-manifest.json --checkpoint artifacts/routed-v7 --protocol docs/confirmation-v2-protocol.md --selection reports/routed-v7-selection.json --output artifacts/confirmation-v2-evaluation
python -m noema analyze --checkpoint artifacts/routed-v7 --language ja --text "猫が犬に追われる" --offline
```

確認後にこの資料の結果を使って改善する場合、以後の再測定は回帰評価とする。保存済みのv2結果を新しいモデルの「独立した最終評価」に付け替えない。
