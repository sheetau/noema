# 作品と例

[English](../guide/works.md) · **日本語** · [文書一覧](README.md)

二作品の全文を、明示した読みの下でNoemaに記述しています。「全文」は数式・著者注を含む選択した原文範囲についてのもので、著者の論証や科学的主張の真理を認めるという意味ではありません。

| 作品 | 原文単位 | 主な主張 | Git管理下の本文 |
| --- | ---: | ---: | --- |
| カント『啓蒙とは何か』（1784） | 20 | 119 | [カント本文](../../examples/v016/kant-reviewed-complete-v1.noema) |
| アインシュタイン『運動物体の電気力学について』（1905） | 282 | 283 | [アインシュタイン本文](../../examples/v014/einstein-auxiliary-reference-order-v1.noema) |

二作品の出版物には、ほかに97の補助主張があります。一つの原文単位を複数のNoema文で表す場合があるため、原文単位と主張数は別の集計です。アインシュタインでは原文の数式446出現を対応付け、数式画像だけを埋め込んで済ませずNoemaで記述しています。

[意味判断の登録簿](../../data/semantic-review-index-v457.json)が本文・語義規約・識別注記・個別判断を選び、[出版記録](../../data/two-work-publication-v1.json)が描画版への統合を記録します。記録内には別途保存した成果物へのパスもあり、記録自体が参照先全ファイルの配布物というわけではありません。

## Gitで取得できるもの

- `examples/` のNoema本文、`data/` の辞書・語義記録、`reports/` の選択された検査結果。
- `noema/` の処理系、`scripts/` の出版・検証ツール、`tests/` の回帰試験。
- `docs/` の現在の日英ガイドと、保存した過去の仕様・判断記録。

大容量の生成物である `output/` と `artifacts/` は、通常のGit cloneには含まれません。非公開の引き継ぎDB `.noema-project/` も別です。記録内のこれらのパスは制作環境の保存場所であり、ダウンロードリンクではありません。導入の構文解析例は、いずれも不要です。

## 描画済みの読書版

描画成果物のコピーをローカルに持っている場合は、次のHTMLをブラウザで開けます。Git取得で存在を保証するファイルではなく、ローカルのパスです。

| ローカルパス | 内容 |
| --- | --- |
| `output/noema-1.0/index.html` | 固定した完成版。作品・辞書・仕様・証拠 |
| `output/two-work-final-v2/index.html` | 原文対応・数式・注記・固定円文字を備えた二作品 |
| `output/general-language-v1/index.html` | 以前の1,909項目の共通辞書 |
| `output/semantic-boundaries-v1/index.html` | 追加43定義と対照例 |
| `output/noema-writing-v2/index.html` | 採用した字形表と例 |

保存済みHTMLと原文・語義説明は、今回の文書整理では翻訳していません。現在のガイドを英語標準とし、固定完成版を書き換えない構成です。描画版がなければ、上記のGit管理下の本文と例から参照できます。このガイドを読むために退役プレビューを再生成する必要はありません。

## 小さな例

| 話題 | ファイル・記録 | 示す区別 |
| --- | --- | --- |
| 量化順 | [導入の作用域例](../../examples/intro/scope.noema) | 対象ごとの存在と共通の存在 |
| 日常の言説 | [条件付きの働きかけ](../../examples/v010/conditional-directive.noema) | 雨の仮定、依頼、別の質問 |
| 読書と配送 | [作用域対照](../../data/general-scope-contrasts-v1.json) | 明示した解釈と読みの違い |
| 確率 | [確率対照](../../data/general-probability-contrasts-v1.json) | 抽選事例と仮説更新 |
| 記述の合成 | [人物ごとの発話と目的](../../examples/v016/personal-message-purpose.noema) | 特定の発話を目的記述内で保持する |
| 意味の境界 | [境界の例](../../examples/v016/semantic-boundaries-v1.noema) | 実在・情報・報告・合成の区別 |

[作品横断の整理](../../reports/general-language-review-v2.json)は36分野へ構成を対応付けています。応用可能性の説明自体を、新しく意味審査した翻訳とは扱いません。例・診断・原文判断の違いは[証拠ガイド](evidence.md)で説明します。
