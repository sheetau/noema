# Noema landing page

Noemaの紹介サイト。英語は `/noema/`、日本語は `/noema/ja/`。
Noema本体と同じリモートの、独立した `gh-pages` ブランチ用チェックアウトです。
現在はローカル確認用です。リモートへのpushと公開は行っていません。

## ローカルで確認する

Node.js 22以降で実行します。npm依存パッケージのインストールは不要です。

```powershell
npm run preview
```

http://localhost:4173/noema/ja/ を開きます。起動時に静的ファイルを生成します。
編集後は別のターミナルで `npm run build` を実行し、ブラウザを再読み込みしてください。
`PORT`環境変数でポート、`BASE_PATH`で配信パスを変更できます。

```powershell
npm run build
npm run check
```

生成先は `dist/`。本番用サーバーや外部APIは不要です。

## ファイル構成

- `src/content.mjs`：日英の本文。
- `src/examples.mjs`：例文、採用した解釈、語義、Noemaソース。
- `src/page.mjs`：両言語に共通するHTML生成。
- `public/style.css`：色・書体・余白の変数と共通クラス。
- `public/site.js`：言語切替時の位置維持、例文フィルター、拡大表示、スクロール進捗。
- `public/glyphs/`：固定版の描画規則によるSVGと出典ハッシュ。
- `public/examples/`：保存可能なNoemaソース。

テキストはUTF-8（新規ファイルはBOMなし）、LFです。既存の `plan.md` は変更しません。

## 円文字の出典と再生成

`kant-page.png` に対応する `contextual-opening-10-draft` の描画器を使います。
カントの図は既存の固定SVGを流用し、表示色とヒーロー用の表示範囲だけを調整しています。
本文の例文はLP用に作成した解釈例です。描画は主張部分に限り、語の宣言と意味はソース欄に併記します。
画像単独の復号や自然言語との意味一致を、構文・幾何検査の成功で保証してはいません。

隣接する `../noema` が必要です。別の場所なら `NOEMA_SOURCE` を設定してください。

```powershell
node scripts/export-samples.mjs
python -X utf8 scripts/generate-glyphs.py
python -X utf8 scripts/check-examples.py
npm run build
npm run check
```

生成は15例だけを対象にし、言語側のスクリプトを読み取り専用で参照します。
Pythonバイトコードの出力を無効化し、固定ファイルのハッシュを生成前後で照合します。
言語本体の台帳・監査・既存出力には書き込みません。

## フォントと参照

`towavue_lp/public/media/fonts/` のHelvetica Now TextとM PLUS 1 Codeをコピーしています。
M PLUSのOFLは `public/fonts/m-plus-1-code-OFL.txt` に同梱しています。
配色・コンテナ幅・余白の考え方はtowavueとmonapadを参照しました。
スクロールはブラウザ標準のスムーズスクロールで、動きを減らす設定では無効になります。

## 公開する場合

ユーザーの確認後に、参照サイトと同じGitHub Pages構成へ接続できます。
リモートは `https://github.com/sheetau/noema.git`、サイト用ブランチは `gh-pages`。
ビルドコマンドは `npm run build`、公開ディレクトリは `dist/`、base pathは `/noema` です。
確認前に公開が走らないよう、自動デプロイworkflowはまだ追加していません。

## 確認済みの範囲

- 日英ページの表示を1440・768・390・320pxで確認。画像・フォントの読み込み、横方向のはみ出し、ソースを開いた状態も確認。
- 言語切替時のセクション維持、言語フィルター、拡大表示、Escapeでの閉じ方とフォーカス復帰、ソース保存をブラウザで確認。
- 静的検査3件で、ローカルリンク・アンカー・生成画像とソースのハッシュ・例文の言語構成を確認。
- 15件の構文・型・幾何検査と、否定・量化・引用などを区別する30件の小さな解釈検査を実施。有限の例による確認であり、一般的な意味一致の証明ではありません。

ブラウザ確認のスクリーンショットはローカルの `output/playwright/` にあります。
