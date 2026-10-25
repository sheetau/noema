# カントの範囲拡大と行間の調整

冒頭四段落（u0008–u0011）、原文592語を選択した。前版296語のちょうど2倍であり、対応する登録済み40主張をすべて描画する。NoemaとRichardson英訳を、それぞれ1600×2263ピクセルの一枚へ収める。

Noemaの行送りを、文字の拡大率を掛ける前の136から210へ広げた。ページに収まる文字サイズを選ぶため文字は縮小されるが、文字に対する行間の割合は増える。文の形と定義参照の扱いは前版と同じ。画像内には題名・注釈・罫線を描かない。

英訳は1798年版の3–5ページを版面と照合して転記した。第三段落に対応する箇所の段落分けはドイツ語原文に合わせ、第四段落末の`the thoughtless multitude.`まで収録。出典と転記方針は`data/kant-page-english-v2.json`、前版の説明と読み方は[kant-page-script-v1.md](kant-page-script-v1.md)を参照。

出力は`output/kant-page-script-v2/`の`kant-page.png`、`kant-page-english.png`、`kant-page.svg`、`provenance.json`。旧版と既存の意味判断・本文・描画器は保存する。

```powershell
python -X utf8 -m scripts.project_work check --module scripts.proof_kant_page_script_v2 --prepare --tests tests/test_kant_page_script_v2.py --write-report reports/kant-page-script-v2.json
```
