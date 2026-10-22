"""Integrate the contrasting, figurative presentation of present progress signs."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_present_epoch_sentence import SETTINGS,CODES,FRAME,POINT,ACTUAL,REF,CTX,AUTHOR

PARENT='examples/v016/kant-present-shortfall-sentence.noema';PARENT_BASIS='data/present-shortfall-sentence-basis-v1.json'
FULL='examples/v016/kant-progress-indications-sentence.noema';CORE='examples/v016/progress-indications-sentence-core.noema'
BASIS='data/progress-indications-sentence-basis-v1.json';ANNOTATIONS='data/progress-indications-sentence-identifiers-v1.json'
C3='i d[e]';C4='i e[e]'
SCORE_SETTINGS={'cases':'k h26l2[]','selected':'p h26l3','weight':'p h26l4','threshold':'k h26l5[]',
    'classified':'p h26l6','contents':'p h26l7','linked':'p h26ma','accessible':'p h26mb'}
SCORES=' '.join(SCORE_SETTINGS.values())
FIRST='k h26ko['+ACTUAL+']';CANDIDATE='k h26kl['+ACTUAL+']'
PROCESSES='i[person a work a][k h26kp['+ACTUAL+' v person v work]]'
OPEN_ARGS=FRAME+' k h26kk[] '+FIRST+' '+PROCESSES
MAP_ARGS=' '.join(SETTINGS[n] for n in ('variables','equations','factors','worlds','matches','frames'))
DECLINE_ARGS='k h26kh[] '+REF+' '+CANDIDATE+' '+FIRST+' '+POINT+' k h26kq[] p h26kr k h26ks[] '+MAP_ARGS
PRIMITIVES={
 'h26ly':('[a d] c',['area','point'],'この描写で、場所が地表の広がりを持ち、人がその中で身体を動かし活動する領域として区分される。部屋の扉や抽象的な論点そのものとは区別する。耕作地・戦場・特定の所有者・物理的境界の形は限定しない。活動への接近可能性や開放の変化は別に構成する。'),
 'h26lz':('[a a d] c',['person','area','point'],'同じ人が指定した地表の活動域へ入り、その中で自分の動作や仕事を行える実践上の接近・利用可能性。場所の存在、現にそこにいること、許可だけ、能力獲得や仕事の成功とは区別する。前後の変化・同じ過程との接続は別に構成する。'),
 'h26l2':('[] j[d]',[],'第七段落の徴候の識別力を比較する全比較例の有限列。実際の例h26kmを含み、h26l3と過不足なく一致する。真偽の両群を都合よく選び直さず、対応する人口・現在・過程の規則は第一文の設定を保つ。'),
 'h26l3':('[d] c',['case'],'同じ徴候評価で比較する代替的な状況の全範囲。実際の時刻列そのものとは区別し、徴候の出現や進行の真理を見て例を採否しない。'),
 'h26l4':('[d] b',['case'],'同じ比較例へ事前に与えた正の比較重み。原文に実測確率・頻度を補わず、全例の正値と対象真偽の両群はrmbで確認する。'),
 'h26l5':('[] b',[],'同じ比較規則で、徴候が対象成立側に十分偏ると判定する1より大きい文脈係数。deutlicheの識別力による明示的な読みの基準で、原文が具体値を述べたとはしない。'),
 'h26l6':('[a d] c',['item','case'],'同じ候補項目と比較例で、徴候内容と進行仮説の識別力を評価する入力が判明している。観測されない内容を偽で埋めず、対象の実際の真理・項目の出現・同意とは別に扱う。'),
 'h26l7':('[a] e',['item'],'同じ徴候候補の命題内容。何を観察又は記録した項目なのかをNoemaの命題として与え、名前や文番号を真理の代用にしない。比較例での出現はこの内容を評価し、元の進行対象そのものや同じ一定真偽で置換しない。原文は個々の徴候一覧を列挙していない。'),
 'h26ma':('[a '+C3+' d] c',['item','target','current'],'同じ現在の徴候候補が、指定された閉じた段階3の対象内容についての証拠として対応する。対象はr5upで固定した同じ進行であり、別の引用・対象の真理・因果的十分性・主体の肯定判断をこの対応だけから導かない。'),
 'h26mb':('[a a d] c',['observer','item','current'],'同じ観察主体側に、同じ現在の徴候項目が観察・記録・報告等を通じて利用可能である。物理的所有、全人類の認識、全読者の同意、項目への確信や対象の真理は要求しない。'),
 'h26mc':('[a a '+C4+' '+C3+' i[e] i[h[a] e] d] c',['node','author','whole','target','depiction','people','context'],'著者が同じ全体内の対象内容を、地表の活動域が人々に開かれるという別の描写内容で非字義的に提示する。指定した同じ人々を両側へ対応させる。物理的な領域やそこでの動作の現実の存在、両内容の真理同一性、機会から能力獲得への推論を追加しない。対象と描写は別々に合成した記述で渡す。'),
 'h26md':('[a a '+C4+' '+C3+' a a i d[h[a d a d d] b] a d d] c',['node','author','whole','decline','term_node','expansion_node','measure','group','reference','context'],'著者が同じ障害減少の内容において、第一箇所の一般的啓蒙を第二箇所の自己に帰責される未成熟からの離脱として説明的に言い換える。渡した同じ離脱の集団尺度・人口・基準を両箇所の対象に保つ。二つの選択肢の選言、別々の障害群、宗教的な質付き能力への強化とはしない。語句の表面的一致を意味の代用にしない。'),
 'h26me':('[a a '+C4+' d] c',['node','author','content','context'],'著者が同じ箇所・提示文脈で、閉じた段階4の内容記述を主張するという帰属。h236iと同じ非事実的な帰属を一段高い内容に適用し、低い段階へ強制変換しない。徴候の現実の存在やその対象の真理を、帰属関係の評価だけから実行しない。'),
 'h26mf':('[a a a '+C3+' a '+C4+' i[h[a] e] d] c',['node','author','prior_node','prior','next_node','next','viewpoint','context'],'著者が同じ文脈・共通観点において、先行箇所の内容と後続箇所の内容をこの順で対照する。段階3の不足と段階4の徴候内容をそれぞれの段階に保つ。前者の撤回、両者の論理的矛盾、引用内容の真理、単なる本文順序だけにはしない。'),
 'h26mg':('[a a '+C4+' '+C3+' '+C4+' d] c',['node','author','whole','background','focus','context'],'著者が同じ全体の内側で、指定した先行の不足から焦点内容まで退ける見通しに対して、なお焦点を保つものとして取り立てる。先行内容の否定、読者の実際の期待、演繹的反証や焦点の現実の真理を追加しない。焦点が対象節か徴候を述べる主節かを同じ引用で区別する。'),
 'h26mh':('[a a '+C4+' '+C3+' d d] c',['node','author','whole','process_content','current','context'],'著者が同じ全体の対象節で、指定した変化内容を同じ現在まで進む過程として提示する。前後と過程は渡す内容で構成し、将来予測だけ又は時点を失った恒常状態にしない。現在より後の継続、未完の一定の終着点、能力の達成、特定行為者を受動表現から補わない。'),
 'h26mi':('[a a '+C4+' '+C3+' '+C3+' '+C3+' d] c',['node','author','whole','target','first','second','context'],'著者が同じ全体で徴候の指示対象を、直前の第一・第二内容の同じ連言へ照応させる。対象は同じ閉じた進行記述で固定し、片側だけ、原文の語名、別の比較例、対象の実際の真理へ置換しない。二内容と対象の接続は別の合成定義で保持する。'),
}
NODE_INFO={
 'h26mj':([413,674],'第三文全体。'), 'h26mk':([413,420],'Alleinによる第二文への対照。'),
 'h26ml':([442,464],'das Feld geöffnet wirdの場の開放という描写。'), 'h26mm':([437,441],'対象節のdoch。'),
 'h26mn':([425,495],'同じ現在に人々の自由な取り組みへ機会が開かれる節。'),
 'h26mo':([497,632],'一般的な離脱への障害が次第に減る節。'),
 'h26mp':([517,543],'一般的啓蒙という説明される表現。'),
 'h26mq':([545,607],'oderによる自己に帰責される未成熟からの離脱という説明。'),
 'h26mr':([634,639],'davonの二節への照応。'), 'h26ms':([650,654],'主節のdoch。'),
 'h26mt':([634,674],'同じ話者側に明瞭な複数の徴候があるという主節。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0014['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
MEANINGS={
 'r5vk':'同じ本人・地表の活動域・過程・前後について、前後の領域性、前にはない接近利用可能性が後にはあること、同じ過程agと本人la・後端生起dgを結ぶ。描写側の開放を場所名一語で代用しない。',
 'r5vl':'同じ固定集団が非空で全員人間であり、一つの地表の活動域について各人にr5vkの開放過程があるという描写内容。各人の過程や開始点は異なってよい。現実の機会や能力の主張としては実行しない。',
 'r5vm':'第七段落と同じ人々・基準にr5vlを結んだ場の開放の描写内容。物理的な一つの場の共有を実際の社会の必要条件へ移さない。',
 'r5vn':'第一文の進行r5u4と同じ現在人口・時代・主題・先行点・本人別過程によるr5t3を閉じた、自由な取り組み機会の開放側。dahinの目標は同じ質付き宗教能力である。',
 'r5vo':'r5vnと同じ現在人口枠と比較規則によるr5uhの、自己に帰責される未成熟からの離脱への障害漸減側。一般的啓蒙とその説明を別の障害群へ分けない。',
 'r5vp':'同じ閉じた進行族r5uxと実際の例をr5upへ渡した段階3の対象記述。第一文のr5u4と同じ進行を選び、davonと徴候の対応先をこの同じ記述へ固定する。',
 'r5vq':'第一文と同じ全設定に比較例・重み・識別係数・分類・徴候内容・対象対応・利用可能性を供給したr5uu。話者側の同じ現在に、評価された全比較例に基づく複数の明瞭な徴候がある内容。対象が現に真であることとは区別する。',
 'r5vr':'第三文全体と主節の同じ徴候内容を段階4で著者へ帰属する。第二文の不足とのAllein、対象節と主節の二つのdoch、場の比喩、開放・漸減の現在進行、oderの説明、davonの二節照応、本文順序を保持する。引用内容の真理を実行しない。',
}
LIMITS=[
 'u0014第三文[413,674)の225非空白文字を対象とする。開放と障害減少は第一文と同じr5ux進行族の実際の例に固定し、徴候の識別力には同じ族の各比較例を使う。対象の真理と徴候の存在は同一視しない。',
 '前文の大きな不足を認めても進行と徴候を退けない、という対照としてAlleinと二つのdochを保持する。対象節のdochは開放、主節のdochは徴候の存在を取り立てる。実際の読者の期待や先行内容の撤回は補わない。',
 'das Feldは、人が活動する地表の広がりへ新たに接近・利用できるという空間的描写を、同じ人々が自ら取り組む機会へ対応させる比喩と読む。耕作・軍事・所有・具体的地名には限定しない。描写側の一つの場や身体動作を現実の必要条件へ移さない。',
 'jetztとwird/werdenは現在まで進む変化の提示に保つ。開放は同じ前後の新規機会と変化過程、漸減は既存の段階的な減少で構成する。現在より後にも必ず続く、特定終着点に未達である、誰か特定人物が開いたとは補わない。',
 'sich dahin frei zu bearbeitenは同じ本人による宗教的な質付き能力への学習・探究・吟味の機会を指す。禁止・強制・権威的介入の不在と実践機会を用い、積極的許可・現在の実行・能力獲得・全員同時の一政策は加えない。',
 'allgemeine Aufklärungを、同じ人口についての自己に帰責される未成熟からの離脱の普及として読む。oderは同じ対象の説明であり選言ではない。障害の対象を質付き宗教能力の獲得へ強化せず、既存のbeとr5t7を保つ。allmäligは途中の増加を許す段階的減少である。',
 'davonは機会開放と障害漸減の両節を受ける。deutlicheは事前固定した比較範囲で十分な識別力を持つ徴候という既採用の読み。複数の別項目を要求するが独立性・確率値・演繹保証は加えず、原文に具体的な徴候一覧を捏造しない。',
 'wir/habenは著者を含む話者側の同じ現在での徴候の利用可能性と読む。ihnenと障害の対象は同じ全現在人口に保ち、全人類の認識や同意は要求しない。徴候の命題内容はNoemaで与える解釈入力であり、語名や真偽不明な項目を成功に数えない。',
 '閉じた徴候内容の引用を段階4に保ち、先行内容の段階3を黙って落とさない。局所検査・既存依存証拠・全語句照合と通読判断は異なる根拠である。最後の時代名と第七段落全体、二作品全体の確認は残る。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
def definitions():
    physical=both('k aa[v person]','k dd[v first v last]','k h26ly[v area v first]','k h26ly[v area v last]',
        'u[k h26lz[v person v area v first]]','k h26lz[v person v area v last]',
        'k ag[v process v first v last]','k la[v person v process v first v last]','k dg[v process v last]')
    text='d r5vk[person a area a process a first d last d] c['+physical+'].\n'
    each='f person a[y[k h246c[v group v person v reference]][g process a[g first d[k r5vk[v person v area v process v first v point]]]]]'
    text+='d r5vl[group a reference d] e[b point['+both('k r5ty[v group v reference]','g area a['+each+']')+']].\n'
    text+='d r5vm[] e[k r5vl[k h26kh[] '+REF+']].\n'
    text+='d r5vn[] e[b outer[k r5t3['+OPEN_ARGS+']]].\n'
    text+='d r5vo[] e[b outer['+both('k r5sc['+FRAME+']','k r5uh['+DECLINE_ARGS+']')+']].\n'
    text+='d r5vp[] '+C3+'[k r5up[k r5ux[] r['+ACTUAL+']]].\n'
    text+='d r5vq[] e[k r5uu['+CODES+' r['+ACTUAL+'] '+SCORES+']].\n'
    whole='r e[k r5vq[]]';prior='r d[k r5vg[]]';opening='r d[k r5vn[]]';decline='r d[k r5vo[]]'
    parts=['k h26me[k '+n+'[] '+AUTHOR+' '+whole+' '+CTX+']' for n in ('h26mj','h26mt')]
    parts+=['k h26mf[k h26mk[] '+AUTHOR+' k h26lr[] '+prior+' k h26mj[] '+whole+' r[p r5u6] '+CTX+']',
        'k h26mc[k h26ml[] '+AUTHOR+' '+whole+' '+opening+' r[k r5vm[]] r[p r5u6] '+CTX+']',
        'k h26md[k h26mq[] '+AUTHOR+' '+whole+' '+decline+' k h26mp[] k h26mq[] r d[p r5t7] k h26kh[] '+REF+' '+CTX+']',
        'k h26mi[k h26mr[] '+AUTHOR+' '+whole+' k r5vp[] '+opening+' '+decline+' '+CTX+']']
    for node,focus in (('h26mm','r e[k r5vn[]]'),('h26ms',whole)):
        parts.append('k h26mg[k '+node+'[] '+AUTHOR+' '+whole+' '+prior+' '+focus+' '+CTX+']')
    for node,body in (('h26mn',opening),('h26mo',decline)):
        parts.append('k h26mh[k '+node+'[] '+AUTHOR+' '+whole+' '+body+' '+POINT+' '+CTX+']')
    for a,b in (('h26lr','h26mj'),('h26mn','h26mo'),('h26mp','h26mq'),('h26mo','h26mt')):
        parts.append('k ue[k '+a+'[] k '+b+'[] '+CTX+']')
    nodes=('h26lr',*NODE_INFO)
    parts+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    text+='d r5vr[] c['+both(*parts)+'].\n';return text
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[]
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5vr',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()}
    basis=dict(status='progress_indications_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=MEANINGS,primitives=prims,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/present-shortfall-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
