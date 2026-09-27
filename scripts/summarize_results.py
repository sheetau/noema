"""Generate a human-readable report from measured results, not hand-entered scores."""
import json
from pathlib import Path


def percent(value):
    return "—" if value is None else f"{value * 100:.2f}%"


def main():
    runs = json.loads(Path("reports/experiments.json").read_text(encoding="utf-8"))
    lines = ["# 初期実験の結果", "", "## 採用判定", "",
             "凍結エンコーダー2種と小型分類器を使い、6条件を実測した。対応例を確定した割合80%以上、確定出力の意味構造完全一致率95%以上を、日英の両方で満たす条件はなかった。自然言語解析器は未採用とする。形式言語の実装・往復検査とは別の判定である。", "",
             "最終評価は各言語で対応例554件、未対応例7件。確定例が0件の場合、精度は計算不能なので「—」と表記する。高い精度が少数の出力に限られる場合も、採用基準を満たしたとは扱わない。", "",
             "| エンコーダー / ヘッド / 学習量 | 言語 | 確定数 | 確定率 | 確定出力の完全一致率 | 未対応の誤確定 |", "|---|---|---:|---:|---:|---:|"]
    for name, report in runs.items():
        for lang in ("ja", "en"):
            m = report["test"]["selective"][lang]
            lines.append(f"| {name} | {lang} | {m['confirmed']}/{m['in_scope']} | {percent(m['coverage'])} | {percent(m['confirmed_exact_match'])} | {m['unsupported_false_accepts']}/{m['unsupported']} |")
    lines += ["", "## 棄却前に見える失敗", "",
              "次は正解注釈のある位置で測った分類正解率。範囲・概念・役割・数量はトークン単位、否定・時間・文全体の述語概念は文単位となる。範囲の値にはOラベルも含むため、厳密な範囲一致率ではない。概念分類ができても、主体・対象の関係や範囲の列が正しいとは限らない。", "",
              "| 条件 | 言語 | 範囲 | 概念 | 役割 | 数量 | 肯否 | 時間 | 文ベクトルの述語概念 |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, report in runs.items():
        for lang in ("ja", "en"):
            m = report["test"]["heads_before_rejection"][lang]
            scores = " | ".join(percent(m[key]["accuracy"]) for key in ("span", "concept", "role", "quantity", "polarity", "time", "sentence_concept"))
            lines.append(f"| {name} | {lang} | {scores} |")
    lines += ["", "文ベクトルの述語概念分類は、1文が「追う」「眠る」などのどれに属するかだけを測る基準である。トークン表現からの構造抽出と同じ課題ではない。MiniLMの高い文分類成績を、意味構造の抽出成功と読み替えることはできない。", "",
              "確信度の閾値を外しても、支持判定と構造検査は残る。その状態で組み立てられた意味構造を、診断用に次に示す。CLIの採用設定を緩めた結果ではなく、失敗の所在を調べる補助集計である。", "",
              "| 条件 | 言語 | 組立成功率 | その完全一致率 | 主体の誤り | 対象の誤り |", "|---|---|---:|---:|---:|---:|"]
    for name, report in runs.items():
        for lang in ("ja", "en"):
            m = report["test"]["without_confidence_gate"][lang]
            errors = m["component_errors_on_confirmed"]
            lines.append(f"| {name} | {lang} | {percent(m['coverage'])} | {percent(m['confirmed_exact_match'])} | {errors['agent']} | {errors['patient']} |")
    lines += ["", "役割の重複、BIO列の不整合、述語の複数抽出も棄却理由となった。整合しない出力を個別ルールで修正する処理は追加していない。線形分類器の学習量を25%から100%へ増やしても、今回の資料・検証によるエポック選択では大幅な改善は確認できなかった。浅いMLPでも採用基準には達していない。", "",
              "## 手書き例と再現性", "",
              "役割交換、能動・受動、否定、数量2と3、今日と明日、主体省略、名前、受け手、場所、状態を含む手書きの対応例28件と、未対応例14件を別に検証した。生成資料と語彙・基本表現が重なるので、完全に独立した実文書評価ではなく必須事例の点検として扱う。", "",
              "| 線形100%のモデル | jaの確定数 | enの確定数 | 未対応の誤確定 | 反復結果の一致 |", "|---|---:|---:|---:|---|"]
    for model in ("minilm", "xlmr"):
        data = json.loads(Path(f"reports/challenge-{model}.json").read_text(encoding="utf-8"))
        m = data["metrics"]
        lines.append(f"| {model} | {m['ja']['confirmed']}/{m['ja']['in_scope']} | {m['en']['confirmed']}/{m['en']['in_scope']} | {m['ja']['unsupported_false_accepts'] + m['en']['unsupported_false_accepts']}/14 | {data['repeat_identical_results']}（{data['repeated_examples']}例） |")
    meta = next(iter(runs.values()))["metadata"]["encoder"]
    lines += ["", "全例棄却では、日英や能動・受動の意味一致を達成したことにはならない。未対応の誤確定0件も、検査した少数例とこの厳しい棄却設定に限る結果である。", "",
              f"実測環境はPython {meta['python']}、PyTorch {meta['torch']}、Transformers {meta['transformers']}、{meta['platform']}。CPU、float32、8スレッド、eager attention、種17で実行した。モデルをevalにし、勾配とドロップアウト、サンプリングを無効にしている。", "",
              "両エンコーダーについて日英各1入力の特徴量を同じバッチサイズで反復し、テンソルの完全一致を確認した。手書き例の4入力でも解析結果全体が反復一致した。全入力・異なるGPU・ランタイム・バッチ形状にまたがる一致を保証する検査ではない。", "",
              "## 学習条件と解釈の限界", "",
              "モデルとトークナイザーは `noema/resources/models.json` のコミットへ固定した。AutoModelからトークン特徴量を取得し、attention mask内の平均から文特徴量を作る。トークンヘッドへはトークン特徴量と文特徴量を連結する。意味役割は各実体範囲に対する分類であり、一般の複数命題グラフの関係解析ではない。", "",
              "線形ヘッドと、隠れ層128・tanhのMLPを比較した。AdamW、30エポック、学習率は線形0.005・MLP0.001、重み減衰0.01。検証損失が最小のエポックを保存する。未対応判定の学習ではクラス頻度を重みに反映し、単一クラスのバッチでその重みが相殺されない平均を使う。最終評価で閾値やエポックを選んではいない。", "",
              "確定の閾値は事前に0.9へ固定した。構造に必要な分類とトークン範囲のsoftmax値の最小値を採用する。これは校正された意味構造の正解確率ではなく、文が長くなるほど低くなりやすい保守的な指標である。未対応判定が0.5未満なら未対応、型・参照・BIO列の不整合とその他の低確信度は未確定になる。", "",
              "学習・検証・最終評価では概念組合せとテンプレート族を分離した。ただし人工文の展開であり、言語分布は狭い。名前や数値・時間の注釈にも偏りがある。詳細は [評価資料](../data/README.md) を参照。未学習の数量や名前を扱えないことを、そのままエンコーダーの表現能力の限界と結論づけることはできない。", "",
              "今回の見直し対象は、文型と未対応例を増やした人手注釈、明示数量・名前の範囲、BIO境界の抽出方法、述語と実体の関係分類、検証資料による確信度の校正である。それでも必要な精度が得られない場合に、対応範囲の縮小やエンコーダーの追加学習の可否を改めて判断する。追加学習は今回の実装・実験では行っていない。", "",
              "## 再実行", "", "```powershell", "python -m noema dataset", "python -m scripts.run_experiments", "python -m scripts.verify_checkpoint artifacts/minilm-linear-100 --output reports/challenge-minilm.json --offline", "python -m scripts.verify_checkpoint artifacts/xlmr-linear-100 --output reports/challenge-xlmr.json --offline", "python -m scripts.summarize_results", "```", "",
              "集計の原本は [experiments.json](../reports/experiments.json)、手書き例の各予測は [MiniLM](../reports/challenge-minilm.json) と [XLM-R](../reports/challenge-xlmr.json)。特徴量と重みは `artifacts/` に置き、Git管理から除外した。モデルのハッシュ、データのハッシュ、エポック、環境、要素ごとの混同行列を報告に含めている。", ""]
    Path("docs").mkdir(exist_ok=True)
    Path("docs/experiments.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
