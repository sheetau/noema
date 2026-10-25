# 回答と会話記録を含む円文字辞書第9版

[回答の20定義](shared-answers-v1.md)と[会話の新14定義](shared-conversation-v1.md)を円文字へ接続した。第9版は252語で、30単独語と222複合語、21基本宣言と231構成定義からなる。旧218語の綴り・型・定義・意味規約を保持する。会話の本文が再利用する発話5定義と有理数加算は、既存辞書との一致を照合して使う。新しい基本字形・基本宣言は追加していない。

[公開綴り](../noema/resources/visible-conversation-vocabulary-v1.json)では、一個体の回答を主にbook/aki、二個体の回答をbook/fruit、会話記録をbook/townから始まる複合語とする。これは共有定義を指す命名規約であり、部品の語義から回答の正しさや社会的認定を導く規則ではない。同じ版番号で意味・綴りを変更した辞書は拒否する。

## 九つの本文

| 文書 | 確認する区別 |
| --- | --- |
| [部分回答](../examples/v016/visible-conversation-partial-answer-v1.noema) | 正しい肯定情報、網羅の欠如、まだ肯定も否定もしていない候補 |
| [全回答](../examples/v016/visible-conversation-complete-answer-v1.noema) | 実際の網羅と網羅の明示、明示された空の全回答 |
| [二対象の回答](../examples/v016/visible-conversation-paired-answer-v1.noema) | 順序付きの組についての部分回答・全回答・未言及 |
| [二対象の射影](../examples/v016/visible-conversation-paired-projection-v1.noema) | 第一・第二の候補を挙げることと、その組が答えになること |
| [受諾](../examples/v016/visible-conversation-accepted-v1.noema) | 同じ提示・受領・理解・受諾から、受け手の同じ発話記述を記録する |
| [訂正](../examples/v016/visible-conversation-corrected-v1.noema) | 指定人物の旧記述だけを新記述へ置き換える |
| [撤回](../examples/v016/visible-conversation-withdrawn-v1.noema) | 指定記述を除き、他人物・他記述を保持する |
| [履歴の連結](../examples/v016/visible-conversation-linked-v1.noema) | 各段階の後状態と次段階の前状態、同じ会話、三時点の前後関係 |
| [内容の真理](../examples/v016/visible-conversation-claim-truths-v1.noema) | 受諾した全回答は偽、訂正した部分回答は真という内容を別に評価する |

後半の五文書は同じ発話関数と状態の構成を使う。受諾前、受諾後、訂正後、撤回後の記録を本文に残し、共通の関数は局所定義として再利用する。三段階の履歴を複数文書に分けることで、固定された字形・図形上限を維持する。

回答条件と社会的な関係は本文のNative関数で定義し、外部モデルは既存の二個体名と有理数加算だけを解釈する。受諾例の認定関係は全状況で成立する検査用の設定とし、履歴の前後関係は連結文書で明示する。二個体・三状況の領域で、相異なる値を要求する前件が実際に満たされる割当を含めて評価する。現実の人物の受諾・訂正・撤回を認定する根拠や、回答内容の経験的な真理を与える例ではない。

## 復号と意味の対照

[検証報告](../reports/visible-conversation-v1.json)は新34語の型付き呼出し・引用と、語彙文書を含む十文書の図形復号を記録する。円と線から本文を復元し、正本のASTとの一致を確認した後で意味を評価する。受諾関数自体の引用は、内部で対象記述を評価するため段階1にする。他の新33関数は段階0で引用する。

回答範囲を変える、人物列だけを変える、対象記述を別人へ変える、前後関係の引数を反転するという対照では、復号本文の主張が偽になる。引用した回答内容を真に変えても、受諾・訂正・撤回・連結の判定は変わらず、内容の真理を検査する文書だけが変わる。高階関数や無限に長い列を量化する呼出しの往復は構文の検査であり、それらの全値を列挙して意味を証明したものではない。

```powershell
python -X utf8 -m scripts.visible_conversation_page render examples/v016/visible-conversation-accepted-v1.noema output/visible-conversation-library-v1/accepted-copy.svg --width 4800 --public-names
python -X utf8 -m scripts.visible_conversation_page decode output/visible-conversation-library-v1/accepted-copy.svg --native --public-names
```

可視ヘッダーで第1〜9版を読み分ける。旧版の局所名と新しい共有語が同じ綴りでも、旧文書は旧版の意味で読む。SVGの要素順に頼らず復号し、旧入口・旧証拠・固定字体・字形768・図形4096・行128等の上限を保持する。

画像OCR、人による学習と第三者読解、二作品全体の新書式化は未完である。約束の期限・解除・不履行、知識と情報構造、一般的な同義・多義も引き続き扱う。
