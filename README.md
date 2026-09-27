# Noema

Noemaの初期実装。人が読み書きする形式言語と、凍結した多言語エンコーダーから意味を抽出する実験系を分離している。生成モデル、指示プロンプト、自然言語への逆翻訳、VQは使わない。

`parse`・`format`・`render` はモデルなしで動作する。自然言語の `analyze` は学習済みの小型分類器を必要とし、低確信度や構造不整合を返す。**現時点の分類器は採用基準を満たしていない。** 実測値と制約は [実験報告](docs/experiments.md) を参照。

## 実行

Python 3.11以上。リポジトリのルートで実行する。

```powershell
python -m pip install -e ".[test]"
python -m noema parse --input examples/chase.noema
python -m noema format --input examples/chase.json
python -m noema render --input examples/chase.noema --output artifacts/chase.svg
python -m noema alphabet --output artifacts/alphabet.svg
python -m pytest -q
```

入力は `--text`、UTF-8ファイルの `--input`、標準入力のいずれかで渡す。`--output` を省略すると標準出力に書く。正常終了は0、文法違反・入出力エラーなどは2。`analyze` の未確定・未対応は正常な解析状態なので終了コード0となる。

「犬が猫を追う」のNoema表記は次のとおり。`aa` は犬、`ab` は猫、`ba` は追う出来事を表す。

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

[文章のSVG表示](examples/chase.svg) は、同じ文字単位を独自字形へ置き換えたもの。字形は試作段階であり、読みやすさの利用者評価、発音体系、完成フォントは未実施。

## 自然言語の解析と実験

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
