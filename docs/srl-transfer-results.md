# 学習済み意味役割モデルの転用結果

**Noema側で単語や例文を追加学習せず、日英の原文から述語と項の関係を取り出す実験系を実装した。** ただし、出力が助詞や前置詞に付くことが多く、対象となる事物をそのまま取り出す部品としては不十分だった。日本語の受動態などでは出来事の分類も誤った。本番の翻訳器への置換は行っていない。

## 利用したモデル

[Unify-SRL](https://github.com/SapienzaNLP/unify-srl)の公開重み `xlmr_ft_full_all` を固定して使った。[原論文](https://aclanthology.org/2021.naacl-main.31/)は多言語の意味役割を分類する方式で、指示プロンプトや文章生成は使わない。公開された学習設定に日本語は含まれない。日本語入力は、学習済み多言語表現の転用として試した。

重みには、XLM-R-base、系列を符号化する層、述語検出、語義分類、項ごとの役割分類がある。英語PropBankは9,229、VerbAtlasは419の出力ラベルを持ち、どちらも未指定などを含む。これはNoemaの完成語彙数ではない。モデル内部の分類クラスは固定だが、今回Noemaの各単語に例文を追加したり、単語別にモデルを学習したりはしていない。

推論は入力の単語列を符号化し、述語位置を分類した後、その位置ごとに語義と役割を分類する。学習時の対訳資料や見出し語から候補を選ぶ表は参照しない。学習済み重みの出力番号をラベル名に戻す一覧は使用するため、「あらゆる一覧が存在しない」という意味ではない。

文と単語の境界は[Stanzaのトークン分類器](https://stanfordnlp.github.io/stanza/tokenize.html)で予測し、原文の文字位置を残した。MWT展開、見出し語化、依存構造解析は起動していない。意味の対応を補う個別規則も追加していない。

## 原文からの試験

[事前条件](srl-transfer-protocol.md)と[入力16組](../data/srl-transfer-v1.json)をコミット `e5debc3` で固定してから予測した。正解の単語分割、述語位置、項の位置はモデルへ渡していない。Noemaの既存91概念へ候補を絞ってもいない。

| 確認した項目 | 日本語 | 英語 |
| --- | ---: | ---: |
| 指定した述語位置の検出 | 19/19 | 19/19 |
| 指定した内容語に指定役割が付いた数 | 13/34 | 31/34 |
| 文内の指定条件がすべて成立 | 1/16 | 13/16 |

これは部分的な条件への一致数であり、SRLの標準評価の精度・再現率や、Noemaの全文意味構造一致率ではない。位置は文字範囲の重なりで照合し、同じ位置の語義が正しいことまでは上表で要求していない。余分な述語・役割も全予測に残した。

## 分かった不足

英語の受動文では、主体役割が `dog` ではなく `by` に付き、授与文では受け手役割が `student` ではなく `to` に付いた。日本語の能動文でも、対象役割が「猫」ではなく「を」に付く。依存型SRLの出力は句の内容語を指すとは限らないため、これらの不一致すべてをモデルの意味役割誤りとは断定できない。しかし、この出力だけではNoemaの対象ノードを構成できないことは確認できた。

日本語の受動文「猫が犬に追われる」では、「猫」を主体側に置く予測と、VerbAtlasで `THROW` を返す予測があった。これは内容語と機能語の位置の違いだけでは説明できない。「受賞」を `APPROVE_PRAISE` とする例もあり、日本語の意味の転用はまだ不安定である。

英語の「鳥が飛び去った」に相当する文では、鳥に `A1` を付けた。今回の注釈は `A0` である。[PropBank 3.4のfly.01](https://propbank.github.io/v3.4.0/frames/fly.html)は自力で飛ぶ鳥をARG0の説明に含める。ただし、学習時の古い体系との違いもあり得るため、この試験をそのまま元モデルのベンチマーク成績とは比較しない。

省略例では、両言語とも主体のA0を出力しなかった。ただし、これだけで一般の省略を正しく扱う保証にはならない。日本語では同じ対象役割を「猫」と「を」の両方へ付けた。英語の授与文では `book` を別の述語としても出力した。部分条件に一致しても余分な出力は残る。

## 語義の言語間一致

事後診断として、指定した述語位置のVerbAtlas分類を比較した。19組中15組で、日英がそれぞれ単一の同じラベルを返した。「製造」「承認」「発見」「修理」「辞任」「延期」なども一致した。Noema側への語別登録なしで、既存モデルから共有する出来事の分類が得られる例はあった。

これは言語間の一致であり、正しい語義だった割合ではない。また、上位フレームだけでは意味の細かな区別を失う可能性がある。ラベルをNoemaの語へ機械的に置き換えれば翻訳が完成する、という判断には使わない。[全組の診断](../reports/srl-transfer-v1/frame-agreement.json)

## 移植と再現性の検査

古いLightning・torch-scatterに依存せず、現行のPyTorch・Transformersで推論できるアダプターを実装した。旧チェックポイントは `weights_only=True` と、メタデータ型を組込みdictとして読む限定設定で読み込み、推論用のsafetensorsへ変換した。旧フレームワークの任意コードは読み込んでいない。重み・設定・分かち書きモデルのハッシュを保存した。

元の公開 `forward` 関数と、同じ固定モジュールを使う新しい計算を照合した。述語・語義・役割のロジットは `rtol=1e-5, atol=1e-6` で一致し、最大絶対差は約0.000061だった。これはヘッドの組合せの互換検査で、旧ランタイム全体の再現実行ではない。最後のSEPを注意マスクから外す元の前処理も、学習条件に合わせて保持した。

32入力をそれぞれ2回処理し、すべての出力が一致した。実行はCPU・float32である。502サブワードを超える文は黙って切らずに拒否する。この上限や日本語の転用の弱さを、完成条件の縮小には使わない。

全207テストが通過し、別プロセスでの再実行でも全予測・集計・数値照合が一致した。チェックポイント変換コマンドも実行し、最初に使ったsafetensors・設定とSHA-256が一致した。[再現検査](../reports/srl-transfer-v1/reproducibility.json)、[変換結果](../reports/srl-transfer-v1/conversion.json)

## 次の判断

今回の結果は、既存モデルから広い述語の知識を利用する方向を支持する一方、依存型の役割ラベルだけをNoemaへ直結する案は支持しない。次は、項の句全体を予測する学習済みモデルと、否定・数量・時間・節の作用範囲を保持する構造を検討する。助詞の直前の単語を拾うような個別補正では解決しない。

名詞の概念、複合的な意味、文間の参照、辞書・ハードコードなしの逆方向は今回実装していない。意味構造一致率95%以上と、通常の自然文の広い翻訳という目標は未達のままである。

## 再実行

重みと公開コードはGit管理外。初回は[公式配布リンク](https://drive.google.com/file/d/1hF6z22yOoyW0qK7gIL6KNH2T4JSl0mP-/view)から取得したアーカイブのチェックポイントと `processor_config.json` を使う。チェックポイントを推論用へ変換し、同じ出力先へラベル設定を配置する。

```powershell
python -m pip install -e ".[ml,srl,test]"
python -m scripts.prepare_srl_transfer "artifacts/unify-srl-model/checkpoint_epoch=026-val_f1=0.9028.ckpt" --output artifacts/unify-srl-model
python -m scripts.probe_srl_transfer --output reports/srl-transfer-reproduction
python -m noema.srl_transfer --language en --text "The factory manufactures batteries." --output artifacts/srl-example.json
```

試験スクリプトの既定値は `artifacts/unify-srl-model` と `artifacts/stanza-srl`。Stanza 1.14.0の `en/tokenize/ewt.pt` と `ja/tokenize/gsd.pt`、XLM-Rの固定版トークナイザーのキャッシュも必要となる。公開コードは `artifacts/unify-srl-source` に指定コミットで取得する。既存の結果・変換済み重みは上書きしない。

分かち書きモデルと参照コードの初回準備は次のとおり。トークナイザーの固定版は `FacebookAI/xlm-roberta-base` の `e73636d4f797dec63c3081bb6ed5c7b0bb3f2089` で、同版のAutoConfigと低速AutoTokenizerをHugging Faceの標準キャッシュへ取得する。推論はキャッシュだけを読み、接続やモデル更新を行わない。

```powershell
git clone https://github.com/SapienzaNLP/unify-srl.git artifacts/unify-srl-source
git -C artifacts/unify-srl-source checkout 6d4fe9fadc90be22ed5eeaab12771c4fdc1939eb
python -c "import stanza; stanza.download('en', model_dir='artifacts/stanza-srl', processors={'tokenize':'ewt','mwt':[]}, package=None); stanza.download('ja', model_dir='artifacts/stanza-srl', processors={'tokenize':'gsd'}, package=None)"
```

[実行条件](../reports/srl-transfer-v1/run.json)、[配布物と参照コードのハッシュ](../reports/srl-transfer-v1/provenance.json)、[互換検査](../reports/srl-transfer-v1/adapter-verification.json)、[集計](../reports/srl-transfer-v1/summary.json)、[全予測](../reports/srl-transfer-v1/predictions.json)、[各条件の判定](../reports/srl-transfer-v1/assessment.json)を保存した。
