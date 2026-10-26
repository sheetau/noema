# 円文字のCPU並列処理

円文字の描画とSVGからの復号を、既存の形・文法・意味規約を維持して複数のCPUプロセスで実行する。描画は冊ごと、復号はページごとに分担し、結果を入力順に取り出す。既定は4プロセスで、先行投入はプロセス数の2倍までに制限する。小さい文書では起動・転送の負担があるため、`workers=1`で従来の逐次処理を使える。

復号の各プロセスは、既存のSVG解析・行分割・幾何検査・字形認識を実行する。親プロセスは、認識済みの次の行と入力が完全一致した場合だけ、その結果を使う。不一致の場合は既存の認識処理を実行する。続く行番号、冊番号、継続位置、欠落、語彙、型、束縛、文書構造の検査は既存の処理が担当する。形の丸めや認識条件の緩和、意味判断のキャッシュは行わない。

描画は既存の本文符号化・ヘッダー生成・冊分割を使い、各冊を既存の`render_volume`へ渡す。したがって、並列化の対象は処理の分担であり、文字の選択規則や配置規則は変えない。歴史的な検証器とそのファイルのハッシュは維持する。

復号には次のコマンドを使う。ページは文書の順に指定する。Windowsでページ数が多い場合は、出力ディレクトリを作業ディレクトリにして短いファイル名を渡し、リポジトリを`PYTHONPATH`へ追加する。`--vocabulary`には使用する版のローカル語彙クラスを指定する。

```text
python -X utf8 -m scripts.visible_parallel_collection --workers 4 --vocabulary scripts.longitudinal_elimination_visible_profile:LongitudinalEliminationVisibleVocabulary page-00001.svg page-00002.svg ...
```

復号したNoema本文を標準出力へ、ページ数・プロセス数・所要時間を標準エラー出力へ出す。省略したページを補完する機能はない。標準の語彙を使う場合だけ`--vocabulary`を省略できる。

描画はPython APIから呼び出す。Windowsのプロセス起動に対応するため、呼び出しを`if __name__ == '__main__':`の内側へ置く。`iter_rendered_volumes`は既存の`iter_collection_volumes`と同じ形式の冊を順に返す。

```python
from scripts.visible_parallel_render import iter_rendered_volumes

if __name__ == '__main__':
    # document、label、vocabularyは使用する文書と語彙から構成する。
    for volume in iter_rendered_volumes(document, label, vocabulary,
                                        workers=4, payload=768):
        save_pages(volume['pages'])
```

追加試験では逐次・並列復号の一致、ページの並べ替え・欠落・重複・未知SVG要素の拒否、変更された行の再検査、例外後の復元、描画の全図形・SVGの一致、不正な配置条件の拒否を確認する。原文との意味同値や、人による読解の証拠は従来どおり別に管理する。

2026年10月27日、縦方向の光線と時刻消去を含む603ページで、逐次復号826.897秒、4プロセス復号313.857秒を測定した。所要時間は約62%減、速度は約2.63倍で、両方とも元のNoema本文と一致した。CPUはRyzen 9 9900X。他の検証も同時に動いていた単回測定であり、常に同じ倍率になるとは限らない。

4プロセス描画は745.367秒で603ページを生成し、すべてのSVGのSHA-256が従来の逐次描画と一致した。以前の逐次描画時間には本文準備も含まれるため、描画の速度倍率は算出していない。測定と検査の記録は[並列処理の確認結果](../reports/visible-parallel-work-v1.json)にまとめる。
