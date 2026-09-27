# Noema

Noemaの初期実装。人が読み書きする形式言語と、凍結した多言語エンコーダーから意味を抽出する実験系を分離している。生成モデル、指示プロンプト、VQは使わない。逆方向は、既存15概念の単文を定型文にする限定実装である。

[未解決の必須課題](docs/open-problems.md)として、短文に対する文字数の膨張、通常のLLMが理解できる文への広い対応、辞書・ハードコードに依存しない翻訳を追加した。現行の定型文による逆変換は最終方式に適合せず、置換が必要である。非生成型・プロンプト不使用の制約は維持する。

[短縮記法](docs/compact-notation.md)では、版指定を2文字にし、主体・対象を語順で区別する。`e:ih mu si.` と従来形式は同じ意味構造に戻る。12例の全文字数は305→161となったが、短い日本語より長い問題と、人による読みやすさの検証は残る。

文語0.5では、[状態から変化の語を作る規則](docs/writing-v05.md)を追加した。「開いている」に共通の形態素を組み合わせ、「開く」「開ける」を構成する。13種類の状態に適用でき、派生語の個別登録は不要。[型・作用範囲・旧版との互換性](docs/spec-v05.md)を検査する。自然言語解析器の対応範囲が0.5全体に広がったことを意味しない。

[文字版2](docs/alphabet-v2.md)では、文法の働きが近い文字を共通の骨格から構成する。画面とCLIに新字形を接続し、旧字形の文章も引き続き読める。字形の似た組が増えるため、人が読みやすくなったかは未検証である。

[既存の語義モデルを追加学習せず使う比較](docs/bem-probe-results.md)も実装した。語彙ごとの分類器を作らず概念定義を候補にできるが、新しい日英資料では精度が不足し、本番採用を見送った。概念選択と文全体の意味構造一致は区別して測定している。

続く[共通の小型判定器](docs/shared-matcher-results.md)では、概念数に依存しない3係数と双線形射影を比較した。学習に使わない50概念で3係数方式は日本語66%・英語70%となったが、状態や関係の区別、未知判定は精度不足で、本番への接続には至っていない。

[既存の意味役割モデルの転用](docs/srl-transfer-results.md)では、語別の追加学習なしで原文から述語と項を予測する実験系を実装した。日英の出来事の分類は19組中15組で一致したが、項が助詞や前置詞に付く問題と、日本語の受動態などでの誤分類が残った。広い自然文を翻訳する部品として検証中で、主画面には接続していない。

続く[学習済みモデルによる句の抽出](docs/srl-span-results.md)では、前置詞を含む句全体を取得できた。指定した36範囲は日本語24件・英語35件が完全一致したが、日本語の受動態・従属節と語境界の整合性に問題が残る。これは部分条件の検査であり、全文の意味構造一致率ではない。

[語境界の整合性](docs/srl-boundary-results.md)を改善し、語の途中で句が始まらない共通の推定処理を追加した。日本語の指定範囲は既存資料で26/36、新しい8組で11/19になった。受動態や修飾節の役割の誤りは残り、広い自然文への翻訳は未完成である。

[日本語の学習済み解析器の転用](docs/japanese-pas-results.md)では、KWJAの分類器を生成・辞書補完なしで動かす部品を追加した。元の格・節関係は得られるが、受動態の意味役割への対応と、明示されない主体の推測を切り分ける必要がある。

[語彙クラスと独立した役割ヘッド](docs/role-transfer-results.md)も追加した。新しい動詞のために出力クラスを増やさず主体・対象等を判定できるが、未学習8述語群では検出漏れ込み31/42項にとどまった。受け手の誤分類と、格解析段階で候補から落ちる主体が課題である。

[文中の基本句へ候補を広げる処理](docs/role-candidates-results.md)で、旧評価・新評価とも42項すべてが候補に入った。ただし新評価の役割正解は31/42で、受け手・場所の誤りや、一つの事物が複数の基本句へ分かれる問題は残る。

[語句の範囲と役割を分けて学習する処理](docs/mention-scope-results.md)では、従来の評価で範囲と役割が39/42項一致した。一方、新しい複合語の評価では7/20項にとどまった。学習・開発資料に長い範囲が少なく、誤った範囲を役割判定で退ける学習条件も不足していた。一般の自然文へ対応できたとはせず、失敗を保存している。

[設計の見直し](docs/design-review.md) では、利用者の指定により非生成型を今後も維持する。状態からの語形成と文法機能による字形分類を導入したが、基本語全体を意味から構成する設計と、分類器の語彙拡張は未解決である。元のコンセプトを実現済みとはしていない。

言語として使える段階に向けて開発を継続している。[開発目標](docs/development-goal.md) に必須条件を記載した。文語0.4は、[基本の文法](docs/writing-v03.md) の91概念と8種類の役割、複数文の参照、質問・依頼・条件・否定範囲に加え、[語を組み合わせる規則](docs/writing-v04.md) を持つ。「本＋赤い」などを辞書へ個別登録せずに書ける。[厳密な仕様](docs/spec-v04.md)、[語彙参照](docs/lexicon-v03.md)、[対訳読本](docs/readings.md)、[練習と解答](docs/lessons.md) を用意した。0.1〜0.3の文章も引き続き読める。

`parse`・`format`・`render` と文語の編集はモデルなしで動作する。自然言語の `analyze` と画面での自然言語からの変換は、学習済みの小型分類器を必要とする。**最新の対照実験v9は英語の確定率が51.00%で、採用基準未達となった。** [最新報告](docs/context-experiments.md) に失敗を含めて記録した。以前の [v7の限定した人工文評価](docs/surface-experiments.md) では、日本語の確定率96.50%・完全一致率97.75%、英語90.17%・100%で条件を通過したが、別の手書き回帰で代名詞など3文を誤確定した。自由記述全般への対応や、言語全体の完成を宣言する段階には至っていない。[以前の確認評価の失敗](docs/joint-experiments.md)、[関係分類器](docs/structured-experiments.md)、[線形・MLP](docs/experiments.md) の結果も保持している。

## 実行

Python 3.11以上。リポジトリのルートで実行する。

```powershell
python -m pip install -e ".[test]"
python -m noema edit
```

ブラウザーで `http://127.0.0.1:8765` を開くと、日本語／英語とNoemaの2入力欄があるダークモードの変換画面を使える。自然言語からの変換には学習済みの分類器が必要で、この環境では保存済みのv7を使う。別のチェックポイントは `python -m noema edit --checkpoint <path>` で指定する。逆方向は15概念の単文を定型文にする処理で、未対応の構造は内容を省かず拒否する。

同じポートでの二重起動はエラーで停止する。Windowsではポートの再利用設定によって複数のサーバーへ接続が分かれるため、排他的に起動する。[Microsoftのソケット仕様](https://learn.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse)に従い、古い実装へ接続される問題を防ぐ。

従来の編集機能は `/writing` にある。文法検査、固有文字への切替、語彙検索、文章・意味JSON・SVGの保存ができる。「文章を開く」で64 KiB以下のUTF-8文書を読み込み、「開く前に戻す」で直前の文章に戻せる。終了はターミナルでCtrl+C。CLIで扱う場合は次を使う。

「複合語を作る」で対象と性質を選んで挿入できる。「読み書きを試す」では18問に回答し、意味の一致と固有文字の読み方を確認できる。[利用者確認の方法](docs/usability.md) に、実際の利用者の結果と自動テストの区別を記載した。

```powershell
python -m noema parse --input examples/school.noema
python -m noema render --input examples/school.noema --output artifacts/school.svg
python -m noema parse --input examples/chase.noema
python -m noema format --input examples/chase.json
python -m noema render --input examples/chase.noema --output artifacts/chase.svg
python -m noema alphabet --output artifacts/alphabet.svg
python -m pytest -q
```

入力は `--text`、UTF-8ファイルの `--input`、標準入力のいずれかで渡す。`--output` を省略すると標準出力に書く。正常終了は0、文法違反・入出力エラーなどは2。`analyze` の未確定・未対応は正常な解析状態なので終了コード0となる。

「犬が猫を追う」は現在の文語では次のように書く。`ih` が追う、`mu` が犬、`si` が猫、`i` が主体、`j` が対象である。

```text
noema d d
ih i mu j si.
```

同じ意味の旧0.1形式も保存している。`aa` は犬、`ab` は猫、`ba` は追う出来事の概念IDを表す。

```text
noema a a {
  ev e ba pos unspec;
  en na aa ? ?;
  en nb ab ? ?;
  agent e na;
  patient e nb;
  recipient e ?;
  location e ?;
}
```

`?` は未指定。犬の数量を1と推定したり、受け手や場所を補ったりしない。節と宣言の順序、参照名は変えて書ける。正規化すると一定の順序・参照名になる。[文法と意味構造](docs/language.md) に語彙、数量、固有名、時間、参照の規則を記載した。

![32文字の一覧](examples/alphabet.svg)

[学校での本のSVG表示](examples/school.svg) と [固有アルファベット・フォント](docs/alphabet.md) を参照。0.1の文章表示は旧字形を保持する。新字形の32文字の描画とフォントの生成は検査済みで、読みやすさの利用者評価は未実施。発音体系は文語を優先する今回の対象に含めない。

## 自然言語の解析と実験

確認評価を通ったv7の実行方法と検証範囲は [実験報告](docs/surface-experiments.md) に記載した。その後の [v8](docs/reference-experiments.md) と [v9の対照実験](docs/context-experiments.md) は、英語の確定率が約半分に下がり、不合格となった。v9の新規確認は日本語91.67%・99.64%、英語51.00%・100%で、未対応区分にも誤確定が残る。この作業環境では、以前の限定した確認条件を通ったv7を次のコマンドで実行できる。重みはGit管理外のローカル成果物なので、別の環境では先に再現手順で学習する。

```powershell
python -m noema analyze --language ja --text "犬が猫を追う" --checkpoint artifacts/routed-v7 --offline
```

以下は比較のために保持した旧ベースラインの実行方法である。

```powershell
python -m pip install -e ".[ml,test]"
python -m noema dataset
python -m scripts.run_experiments
python -m noema analyze --language ja --text "犬が猫を追う" --checkpoint artifacts/xlmr-linear-100 --offline
python -m scripts.verify_checkpoint artifacts/xlmr-linear-100 --output artifacts/challenge.json --offline
```

初回は公開モデルをHugging Faceの標準キャッシュへダウンロードする。認証トークンは不要。`scripts.run_experiments` はXLM-RとMiniLMそれぞれで、線形ヘッドの学習量25%・100%、浅いMLPの100%を比較する。モデルの重みは変更せず、特徴量を保存してから分類器だけを学習する。処理済みの実験は再利用し、明示的な `--rerun` で派生成果物を置き換える。

段階別に実行する場合は次を使う。

```powershell
python -m noema features --model xlmr --output artifacts/xlmr-features.pt
python -m noema train --features artifacts/xlmr-features.pt --architecture linear --output artifacts/xlmr-linear-100
```

`--device cuda` は特徴量抽出と解析で指定できる。今回の実測環境はCPU版PyTorchであり、GPU間・CPU/GPU間の一致は検証していない。実行環境、モデルとトークナイザーの固定コミット、精度、学習条件、データと重みのハッシュは各チェックポイントの `metadata.json` に残す。

`analyze` の戻り値は `status`、`graph`、`diagnostics`。`confirmed` のときだけ意味構造を返す。確信度、原文の文字範囲、モデル情報は `diagnostics` に置き、Noemaの意味本体へ混ぜない。チェックポイントがなければ `checkpoint_required` として未確定を返し、推測で翻訳しない。

## ファイル

| 場所 | 内容 |
|---|---|
| `noema/semantics.py`, `grammar.py` | 型・参照検査、正規化、厳密な構文解析 |
| `noema/resources/lexicon.json` | 永続的な概念識別子と定義、語彙版 |
| `noema/render.py` | 32基本文字とSVG出力 |
| `noema/encoder.py`, `model.py`, `training.py` | 凍結エンコーダー、小型ヘッド、学習・評価 |
| `noema/dataset.py`, `data/challenge.jsonl` | 再生成可能な注釈資料と手書きの検証例 |
| `reports/` | 実測値、環境情報、失敗の内訳 |
| `artifacts/` | ローカルの特徴量・分類器・詳細予測。Git管理外 |

基準モデルの根拠と実装方法は [XLM-Rモデル説明](https://huggingface.co/FacebookAI/xlm-roberta-base)、[MiniLMモデル説明](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)、[Transformers Auto classes](https://huggingface.co/docs/transformers/model_doc/auto) を参照。旧構想の `concept.md` は参考資料としてそのまま残し、現行仕様はこのREADMEと `docs/` に分離した。
