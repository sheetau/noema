# Noema landing page

Noema 1.0の紹介サイトです。Next.js 15（Pages Router）、React 19、Lenisを使い、日本語・英語のLPを静的出力します。Noema本体リポジトリの`gh-pages`ブランチで管理します。

## 開発

Node.js 22以降で実行します。

```powershell
npm install
npm run dev
```

[日本語](http://localhost:4173/noema/ja/) / [English](http://localhost:4173/noema/)

既定の待受先は127.0.0.1:4173です。CSSとReactコンポーネントはNext.jsのFast Refreshで更新されます。辞書の検索語・絞り込み・ページ、開いたモーダル、スクロール位置をReactの状態とDOMに保持します。CSS・本文・コンポーネントを変更する実ブラウザ検査で、ドキュメントの再読み込みなしにこれらが維持されることを確認しています。Next.jsの設定や依存パッケージを変更した場合は再起動が必要です。

別ポートは`npm run dev -- --port 4174`で指定します。配信パスは`NEXT_PUBLIC_BASE_PATH`で変更でき、既定値は`/noema`です。`BASE_PATH`も互換入力として扱います。

## 静的出力を確認する

```powershell
npm run build
npm run check
npm run preview
```

生成先は`out/`です。開発用の`.next-dev/`と本番ビルド用の`.next/`を分離しています。`preview`は静的出力をローカル配信します。devと同時に使う場合は`npm run preview -- --port 4174`を使います。LANから見る場合だけ`npm run preview:lan`を使います。

日英LPは`/noema/`と`/noema/ja/`です。旧辞書URLは検索条件を保って各LPの`#dictionary`へ転送します。404、canonical、hreflang、OG、構造化データ、sitemapを含みます。公開操作はビルドに含みません。

## 構成

| ファイル | 役割 |
| --- | --- |
| `pages/` | 日英ページ、旧辞書URL、404、共通CSS・フォント |
| `src/ui/LandingPage.jsx` | セクション、ナビ、モーダルの選択状態 |
| `src/ui/Dictionary.jsx` | 検索・カスタムドロップダウン・ページ切替 |
| `src/ui/Details.jsx` | 解釈・ソース・辞書の詳細モーダル |
| `src/ui/ScrollArea.jsx` | 共通補間と、レイアウト幅を取らない半透明のつまみ |
| `src/ui/RootMarquee.jsx` | 語根の自動移動・ドラッグ・左右キー操作 |
| `src/content.mjs` / `examples.mjs` | 日英の紹介と例文・明示した解釈 |
| `src/page.mjs` | 静的生成時に渡す辞書の初期60件 |
| `src/dictionary-data.mjs` | 検索と詳細の共通ロジック |
| `src/site/web.mjs` / `config.mjs` | ブラウザ用とビルド用のURL・パス |
| `public/style.css` | ユーザー調整を含む配色・書体・余白・レスポンシブ表示 |
| `public/design/` | デザイン由来の画像、新ロゴ、変更記録とハッシュ |
| `public/glyphs/` / `examples/` | 検証済み円文字、宣言とソース |
| `public/diagrams/` | 読み方の説明図 |
| `public/data/dictionary.json` | 1,952項目の完成版辞書 |

## 見た目と操作

`plan.md`で指定されたFigmaフレーム`PJTgbYYwz0NcwojFai5lnO / 288:2`と追記に従います。ABOUT、STRUCTURE、PRIMITIVES、READING & WRITING、DICTIONARY、EXAMPLES、MOREの7セクションです。例文は日英とも10件で、先頭3件は表示言語の固有例、4件目はもう一方の言語の例です。詳細はパネル全体のクリックまたはキーボード操作で開きます。

30語根は全て同じ140×140の座標系で、中心を(70,70)に置きます。円の半径・罫線基準を保持して一律に表示し、個別画像の大きさへ合わせて拡大しません。毎秒30pxで移動し、ドラッグ中のみ停止します。動きを減らす設定では自動移動を止めます。

補間はtowavueと同じLenis・係数0.1を使い、辞書・モーダル・ソースにも適用します。辞書が上下端に達したときや内容が短いときはページへ引き継ぎます。モーダル表示中は背景を固定します。スクロールバーはつまみのみを前面に重ね、表示幅を取りません。

## 円文字と本体の対応

本体の正本は`../noema/data/language-release-v1.json`です。言語版1.0、採用字体concept2 v7、書記固定記録`data/writing-freeze-v2.json`を参照します。カタログは基本宣言1,489と合成定義463で、作品内参照補助27を含みます。原典の語義は日本語のまま掲載しています。

```powershell
npm run sync:release
npm run glyphs
python -X utf8 -B scripts/check-examples.py
python -X utf8 -B scripts/generate-presentation-assets.py
python -X utf8 -B scripts/generate-reading-diagrams.py
python -X utf8 -B scripts/generate-kant-spread.py
```

本体は読み取り専用です。例文のSVGは宣言から順に読み戻し、元の構文と照合します。SVG属性の色は認識処理に必要なため、原本を維持してCSSで白く表示します。

ABOUT末尾のA5見開きは、同じ冒頭4段落の英訳と採用円文字を比較します。英訳は本体の`data/kant-page-english-v2.json`（John Richardson、1798年）を保持。円文字は4300単位幅で改行し直し、40項目の構文を図形から読み戻して照合しています。紙面の線幅は縮小表示に合わせ、原図形の2倍です。`public/specimens/provenance.json`に対応段落とハッシュを記録します。

heroは元の円文字から、線幅を含む図形の外周まで余白を詰めた`public/glyphs/hero.svg`です。READINGの3つ目は共有語homeを囲む引用式として、語末・接続を含めて生成し、ガイドを足す前のSVGを復号しています。証拠は`output/reading-scope/`に保存します。

サイト外の名詞表記は`output/noema-name/noema.svg`です。「Noema」を指す個体型・引数なしの局所的な固有名として宣言した表記で、公式辞書の既存表記や音写ではありません。宣言、使用した語根、復号確認を同じフォルダーに保存しています。サイトの公開ファイルには含めません。

## 検査と素材

`npm run check`はビルド後に実行し、静的出力の日英リンク・アンカー、辞書、10例、円文字の出典ハッシュと語根の共通座標を検査します。ブラウザの記録は`output/playwright/next-*.png`などです。Fast RefreshはCSS・本文・JSXを一時的に編集し、元のファイルへ復元して確認します。

共有用PNGは`public/og.png`、再生成用HTMLは`scripts/og.html`です。Helvetica Now TextとM PLUS 1 Codeは既存ファイルを維持しています。M PLUSのOFLは`public/fonts/m-plus-1-code-OFL.txt`です。新規テキストはUTF-8 BOMなし。ユーザーの`plan.md`は変更しません。

## 公開

公開先は https://sheetau.github.io/noema/ （日本語は `/noema/ja/`）です。

`sheetau/noema`の`gh-pages`ブランチへのpushで`.github/workflows/deploy.yml`が動き、依存関係のインストール、静的ビルド、検査を経て`out/`のみをGitHub Pagesへ配信します。Pagesの配信元はGitHub Actionsです。本体の`main`ブランチはLPの更新では変更しません。
