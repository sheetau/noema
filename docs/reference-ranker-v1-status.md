# 共通の参照判定器の実装と特徴抽出

語彙ごとの分類クラスを増やさずに、語句が以前のどの対象を指すかを学習する部品を追加した。現在は公式学習資料の特徴抽出を進めている段階で、学習済み重みの選択と評価はまだ完了していない。参照精度が改善したという結果はまだない。

[固定した実験条件](reference-ranker-v1-protocol.md)に従い、比較する方式は5個の数値特徴を使う線形方式と、文脈ベクトルを共有の64次元へ射影する方式である。現在の768次元エンコーダーでは学習するパラメーター数は6と115,201で、語や概念を追加しても出力層は増えない。基盤モデルは固定し、生成処理・対訳表・語別の修正は使わない。

候補は予測された全ての先行主辞と「先行対象なし」である。複数の先行語句が同じ正解対象を指す場合は、そのどれかを選べる損失を使う。正解の候補が上流で欠けた場合や、予測主辞の範囲が正解と一致しない場合は、誤った負例を作らず損失から外して件数を記録する。開発評価では欠落した正解も分母に残す。複数対象・曖昧な参照はまだ単純な同一性グループで扱えず、未対応として保持する。

## 実装済みの操作

```powershell
artifacts/kwja-venv/Scripts/python.exe -m scripts.cache_reference_features --resume
artifacts/kwja-venv/Scripts/python.exe -m scripts.verify_reference_features --split train --output reports/reference-ranker-v1/train-feature-verification.json
artifacts/kwja-venv/Scripts/python.exe -m scripts.verify_reference_features --split dev --output reports/reference-ranker-v1/dev-feature-verification.json
artifacts/kwja-venv/Scripts/python.exe -m scripts.train_reference_ranker
artifacts/kwja-venv/Scripts/python.exe -m scripts.cache_reference_features --resume --splits test
artifacts/kwja-venv/Scripts/python.exe -m scripts.evaluate_reference_ranker
artifacts/kwja-venv/Scripts/python.exe -m scripts.verify_reference_ranker
```

抽出は公式train3,915文書とdev512文書が対象で、実行環境はCPU・float32である。各文書のJSONを、予測と特徴ファイルの保存が完了した印として最後に書く。再開時には、原文・注釈・モデル・コード・特徴ファイルのハッシュを検査し、完了済み文書を再推論せずに読み込む。OSのファイルロックで同じ保存先への同時抽出を防ぐ。

学習コマンドは全train・devの抽出完了を要求する。20エポックの学習後、devの参照ペアF1と損失で方式・エポックを選び、モデルと選択記録を保存する。testの特徴抽出は選択記録が作られるまで実行できない。現時点ではこの全資料学習とtest評価は未実行である。

最終評価の処理は、選択済みの重みと学習記録・判定方針を照合してから動く。学習本文と重複する文書を除いた結果も集計するが、解析できなかった文書や欠けた正解ペアは分母に残す。保存特徴からの開発・最終評価の再計算、最終評価先頭8文書の原文API照合、既存の参照12文の回帰確認を実装した。これらを全資料の保存モデルで実行する段階はまだ完了していない。

選択済みモデルを使う研究用APIとして`ReferenceRankerAnalyzer`も実装した。原文解析を`analysis`へ保持し、参照だけを再判定した解析と各候補の確率を別に返す。候補確率は全文の意味が正しい確率ではない。

## 完了した検査

- 最初のtrain4文書とdev4文書で抽出・保存・再読込みを確認した。各splitの先頭2文書は原文から再推論し、特徴と予測が完全一致した。
- 保存済みのtrain先頭64文書を検査し、既存モデルが採用した158の参照リンクについて、保存した照応スコアと採用先が一致した。[検査記録](../reports/reference-ranker-v1/feature-smoke.json)は64文書のみの検査であることを明示している。
- 候補の自己参照・未来参照を禁止すること、複数正解の損失、欠落主辞を負例にしないこと、特徴の保存破損の検出、中断した保存と完了済み保存の区別を検査した。
- 小さな固定特徴で文脈方式を二度学習し、選択・履歴・重み・評価の完全一致を確認した。これは全資料で学習したモデルの精度や再現性の検証ではない。
- 重複本文の除外で解析失敗を消さないこと、保存済みの選択・重み・判定方針の不一致を拒否することも含め、全316テストが通過した。特徴のスカラー計算より前に実行条件を固定し、学習と再評価で同じ数値条件を使う。

次の段階は全資料の特徴抽出完了、両方式の学習、独立した分割での評価である。全文意味構造95%以上、広い日英翻訳、辞書に依存しない逆変換、文字数の膨張の課題は維持する。
