export const repository = "https://github.com/sheetau/noema";
export const languages = {
  ja: "日本語",
  en: "English",
  zh: "中文",
  fr: "Français",
  es: "Español",
  de: "Deutsch",
  ar: "العربية",
  math: "Mathematics",
};
// Text pairs are ordered [English, Japanese].
export const content = {
  title: ["Noema — Compose meaning in circles and lines", "Noema — 意味を組み立て、円と線で記す言語"],
  description: [
    "Noema 1.0: a language for relations, quotations and mathematics, with syntax recoverable from its circle writing. Explore 1,952 catalogue entries, writing rules, multilingual examples and two complete works.",
    "Noema 1.0。関係・引用・数式を同じ体系で記述し、円と線の図形から構文を読み戻せる言語。1,952項目の辞書、読み書きの仕組み、多言語の例文、二作品の全文記述を紹介します。",
  ],
  skip: ["Skip to content", "本文へ"],
  language: ["Page language", "表示言語"],
  hero: [
    "A language in circles and lines. Compose relations and scope, from everyday events to beliefs, assumptions, and mathematics.",
    "日常の出来事から、信念、仮定、数学まで。意味の関係と範囲を組み立て、円と線で記す言語。",
  ],
  specimen: ["Opening of Kant’s What Is Enlightenment?", "カント『啓蒙とは何か』の冒頭"],
  specimenNote: ["Enlarge the adopted circle writing", "完成版の円文字を拡大する"],
  aboutTitle: ["Compose what you mean.", "伝えたい意味を、組み立てる。"],
  aboutIntro: [
    "Noema describes content through relations between objects and combinations of words. Facts, beliefs, assumptions, and what remains unknown can be written with their distinctions intact.",
    "Noemaは、対象どうしの関係を定め、語を組み合わせて内容を表します。事実だけでなく、誰かの信念や仮定、まだ分からないことも、その違いを保って記述できます。",
  ],
  features: [
    [
      ["Keep the distinctions", "意味の違いを残す"],
      [
        "“Not everyone” and “no one.” “They believe it” and “it is so.” Explicit scopes for negation and quotation preserve the intended reading in the syntax.",
        "「全員ではない」と「誰もいない」。「そう信じている」と「そうである」。否定や引用の範囲を定め、文が意図する区別を構文に残します。",
      ],
    ],
    [
      ["Extend through definitions", "定義から語を増やす"],
      [
        "Combine shared vocabulary into new concepts. Introduce relations particular to a field or culture with explicit argument roles and contextual conditions.",
        "共有する語を組み合わせ、新しい概念を定義します。分野や文化に固有の関係も、引数の役割と必要な文脈を明示して導入できます。",
      ],
    ],
    [
      ["Read the structure back", "書いた構造を読み戻す"],
      [
        "Spellings, branches, and references follow reading rules. Recover the same syntax from circle writing and its dictionary, moving between visible writing and parsable notation.",
        "語の綴り、枝、参照には読み方の規則があります。円文字と辞書から同じ構文を復元し、見える形と解析できる記述を行き来できます。",
      ],
    ],
  ],
  structureTitle: ["Read one statement, step by step.", "ひとつの文を、順に読む。"],
  structureIntro: [
    "Start with the relation “give.” Identify three objects and their roles, then follow the correspondence between a statement and its circle writing.",
    "まずは「渡す」という関係から。三つの対象とその役割を決め、文の構造と円文字の対応を見ます。",
  ],
  simple: ["Aki gives Nao a book.", "アキが、ナオに本を渡す。"],
  simpleNote: [
    "Interpret give with arguments in the order giver, object, recipient. This example does not specify tense.",
    "giveの引数を「渡す人・渡す物・受け取る人」の順とする解釈。時制はこの例では指定しません。",
  ],
  structureSteps: [
    [
      ["Identify the objects", "対象を決める"],
      [
        "aki names Aki, book names the object given, and nao names Nao. The relation give connects all three.",
        "akiはアキ、bookは渡す本、naoはナオを指す名前。giveは三つの対象を結ぶ「渡す」という関係です。",
      ],
    ],
    [
      ["Compose the relation", "関係を組み立てる"],
      [
        "give(aki, book, nao). The argument order is giver, object, recipient. Reordering the same objects changes the meaning.",
        "give(aki, book, nao)。引数は渡す人・渡す物・受け取る人の順。同じ対象でも、並びを変えると意味が変わります。",
      ],
    ],
    [
      ["Declare, then write", "宣言と本文を書く"],
      [
        "Declare the words’ types and spellings before the assertion. Click the panel to inspect the declarations, interpretation, and text notation corresponding to the writing.",
        "語の型と綴りを先に宣言し、続けて本文を記します。パネルをクリックすると、円文字に対応する宣言・解釈・テキスト記法を確認できます。",
      ],
    ],
  ],
  source: ["View source and interpretation", "解釈とソースを見る"],
  download: ["Save explanatory source", "説明用ソースを保存"],
  formula: ["Structural reading aid", "構造の補助表記"],
  sourceLabel: ["Text notation with short explanatory names", "説明用の短い名前によるテキスト記法"],
  glossary: ["Interpretation of the example’s vocabulary", "この例での語の解釈"],
  primitivesTitle: ["An alphabet of arcs, lines, and dots.", "円弧、線、ドットの文字。"],
  primitivesIntro: [
    "Thirty roots combine into word spellings, alongside forms for syntax. Circle dimensions, guide levels, and line directions distinguish words and their relations.",
    "30の語根を綴って語を作り、構文を表す字形と組み合わせます。円の寸法、置く高さ、線の方向を揃えることで、語と関係を読み分けます。",
  ],
  primitives: [
    [
      ["Four scales", "四段階の寸法"],
      [
        "The small circle S determines the radii M, L, and F. F appears as lateral arcs; small circles remain complete.",
        "小円Sを基準に、中円M・大円L・外周Fの半径を定めます。Fは側面の円弧に使い、小円は完全な円として保ちます。",
      ],
    ],
    [
      ["Three guides", "三本の基準線"],
      [
        "Centers follow upper, middle, and lower levels. Large circles and F sit on the middle guide. Lines connect to circles at right angles.",
        "中心を上・中央・下の三段に揃えます。大円とFは中央に置き、線は円と直交するように接続します。",
      ],
    ],
    [
      ["Connections and references", "接続と参照"],
      [
        "Lines are vertical, horizontal, or at 45°. Branches encode argument order. Paired dots identify references within a scope, without lines connected directly to them.",
        "線は縦・横・45度を基本とします。枝が引数の順序を示し、ドットの対が範囲内の参照を示します。ドットには線を直接つなぎません。",
      ],
    ],
  ],
  primitivesLink: ["Dimensions, layout, and connections", "円文字の寸法・配置・接続規則"],
  languagePrimitiveTitle: ["Primitives of the language", "言語のプリミティブ"],
  languagePrimitiveIntro: [
    "Alongside the geometric elements are the basic operations of a statement. Relations and operations apply to typed values, including individuals, rational numbers, and truth values.",
    "図形の部品とは別に、文の基本操作があります。対象・有理数・真理値などの型を持つ値に、関係や演算を適用します。",
  ],
  operations: [
    [
      ["Relations & definitions", "関係・定義"],
      ["k / d", "k / d"],
      [
        "Apply a declared relation; define a word using existing expressions.",
        "宣言した関係の適用と、既存の式による語の定義。",
      ],
    ],
    [
      ["Negation & connectives", "否定・結合"],
      ["u / w / x / y", "u / w / x / y"],
      [
        "Negation, conjunction, disjunction, and implication. Implication alone does not express causation.",
        "否定、論理積、論理和、含意。含意だけで因果は表しません。",
      ],
    ],
    [
      ["Quantification & identity", "量化・同一性"],
      ["f / g / e", "f / g / e"],
      [
        "For all, there exists, and equality. Both the order and scope of quantifiers matter.",
        "すべて、存在する、等しい。量化の順序と範囲を区別します。",
      ],
    ],
    [
      ["Quotation & sequences", "引用・列"],
      ["r[…] / l[…]", "r[…] / l[…]"],
      [
        "Quote an expression as a description; form a finite sequence retaining order and repetitions.",
        "式を記述として扱う引用と、順序・重複を保つ有限列。",
      ],
    ],
  ],
  readingTitle: ["Follow spellings, branches, and scope.", "綴りを追い、枝と範囲を読む。"],
  readingIntro: [
    "Read a sequence of roots, follow the branches, and check the scope of a reference. Shape and placement show how the statement is composed.",
    "語根の並びを読み、枝の順序をたどり、参照の範囲を確かめる。文字の形と配置が、文の組み立てを示します。",
  ],
  readingSteps: [
    [
      ["Identify the word", "語を識別する"],
      [
        "Read roots and ligatures, then an end marker separating spellings. Here, book and home form one spelling. The dictionary or a prior declaration supplies its meaning and type.",
        "語根と合字を読み、語末符で綴りを区切ります。下の例はbookとhomeを並べた綴り。語の意味と型は辞書や先行する宣言で確かめます。",
      ],
    ],
    [
      ["Follow the branches", "枝を順にたどる"],
      [
        "Read from the trunk into the branches in argument order. Upper, middle, and lower placement and separators identify which argument you are reading.",
        "幹線から枝へ、引数の順序に沿って読みます。上・中央・下の配置と区切りの符号を使い、どの引数を読んでいるかを識別します。",
      ],
    ],
    [
      ["Respect reference scope", "参照の範囲を守る"],
      [
        "Quotations and bindings establish scopes. Paired dots and shared expressions connect within those bounds; a reference does not carry into a different quotation.",
        "引用や束縛は範囲を持ちます。対になったドットや共有する部分は、その範囲の中で結びます。別の引用へ参照を持ち越しません。",
      ],
    ],
  ],
  readingDiagramNote: [
    "Schematic reading order and scope. White marks the focus; fine gray lines are placement guides.",
    "読み順と範囲を示す模式図。白は注目する部分、細い灰色は配置のガイドです。",
  ],
  examplesTitle: ["From language to structure.", "言葉から、構造へ。"],
  examplesIntro: [
    "Different word orders and expressions can be described through relations, quantification, and negation. Ten examples bring natural languages and mathematics together, each with an explicit reading and its circle writing.",
    "異なる語順や表現も、関係・量化・否定を使って記述します。自然言語と数式の10例を並べ、各例で採った読みと円文字の対応を示します。",
  ],
  resourcesTitle: ["Read the specifications.", "仕様と記述を読む。"],
  resourcesIntro: [
    "Two works in philosophy and physics are described with correspondences for prose, equations, and notes. Explore the complete texts, then the specifications for syntax, meaning, and writing.",
    "哲学と物理学の二作品を、本文・数式・注の対応を保って記述しました。作品の全文と、構文・意味・円文字の仕様から、Noemaをさらに詳しく読めます。",
  ],
  resources: [
    [
      ["Edition 1.0", "完成版1.0"],
      ["Scope of completion, artifacts, release selection, and evidence.", "完成の範囲、成果物、版の選択と証拠。"],
      ["docs/language-edition-v1.md", "docs/language-edition-v1.md"],
    ],
    [
      ["Circle writing", "円文字の仕様"],
      ["Spelling, arcs, branching, sharing, and decoding.", "綴り・円弧・分岐・共有・読み戻し。"],
      ["docs/circle-writing-v2.md", "docs/circle-writing-v2.md"],
    ],
    [
      ["Meaning and vocabulary", "意味と語彙の組立て"],
      ["Types, interpretations, extension, and reuse across domains.", "型、解釈、語の拡張と分野をまたぐ利用。"],
      ["docs/general-language-v1.md", "docs/general-language-v1.md"],
    ],
    [
      ["Semantic boundaries", "意味の境界"],
      [
        "Unknown and undefined values, conflicting reports, nonexistence, and self-reference.",
        "未知、未定義、相反する情報、非実在、自己言及。",
      ],
      ["docs/semantic-boundaries-v1.md", "docs/semantic-boundaries-v1.md"],
    ],
    [
      ["Syntax and types", "構文と型"],
      ["Relations, functions, quantification, and sequences.", "関係、関数、量化、列を記す基本仕様。"],
      ["docs/spec-v014.md", "docs/spec-v014.md"],
    ],
    [
      ["Quotation and evaluation", "引用と評価"],
      ["Distinguish describing content from evaluating it.", "記述することと、内容を評価することの区別。"],
      ["docs/ranked-quotation-v1.md", "docs/ranked-quotation-v1.md"],
    ],
  ],
  works: [
    [
      ["1784 · IMMANUEL KANT", "1784 · IMMANUEL KANT"],
      ["What Is Enlightenment?", "啓蒙とは何か"],
      ["20 source units · 119 assertions", "20の原文単位 · 119の主張"],
      [
        "An argument about autonomy, reason, and public life, retaining quotation and conditional scope.",
        "自立、理性、公共性をめぐる議論を、引用や条件の範囲とともに記述。",
      ],
    ],
    [
      ["1905 · ALBERT EINSTEIN", "1905 · ALBERT EINSTEIN"],
      ["On the Electrodynamics of Moving Bodies", "運動物体の電気力学について"],
      ["282 source units · 283 assertions", "282の原文単位 · 283の主張"],
      [
        "Prose, equations, and author’s notes aligned with their objects, conditions, and quantitative relations.",
        "本文・数式・著者注を対応づけ、対象、条件、量の関係を記述。",
      ],
    ],
  ],
  worksLink: ["Read the complete Noema text", "Noemaの全文を読む"],
  close: ["Close", "閉じる"],
  specimenDialog: ["Kant’s opening · four paragraphs in the adopted script", "カントの冒頭 · 採用字体による四段落"],
  alphabetTitle: ["Thirty roots", "30の語根"],
  alphabetIntro: [
    "Each shape identifies a root. Sequences of roots spell a larger vocabulary.",
    "それぞれの形が語根を表し、その並びが語の綴りになります。",
  ],
  dictionaryTitle: ["Share definitions. Compose further.", "定義を共有し、さらに組み立てる。"],
  dictionaryIntro: [
    "Explore 1,952 entries for meanings, spellings, types, and context. Search by name or meaning, then click an entry to inspect argument roles and the source of a definition.",
    "1,952項目の共通カタログから、語の意味・綴り・型・文脈を調べられます。名前や語義で検索し、項目をクリックすると引数の役割と定義の出典を確認できます。",
  ],
  visibleTitle: ["Declarations in circle writing", "円文字に書いた宣言"],
  visibleIntro: [
    "Read these declarations in order, then read the assertion. The short name on the left is explanatory; the root sequence on the right is the spelling declared for this example.",
    "以下の宣言を順に読み、その後で本文を読みます。左の短い名前は説明用、右はこの例で宣言した語根の綴りです。",
  ],
  visibleDownload: ["Save the source matching the circle writing", "円文字と対応するソースを保存"],
  svgDownload: ["Open the assertion SVG", "本文のSVGを開く"],
  pause: ["Pause", "一時停止"],
  resume: ["Play", "再生"],
};

// Every text pair is [English, Japanese], including headings and paragraphs in lists.
export function getContent(locale) {
  const index = locale === "ja" ? 1 : 0;
  const localize = (value) => (typeof value[0] === "string" ? value[index] : value.map(localize));
  return Object.fromEntries(Object.entries(content).map(([key, value]) => [key, localize(value)]));
}
