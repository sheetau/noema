"""Connect examples, failed detection and qualified prior results to a conjecture."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_conjecture_laws import ROOT,read
from scripts.compose_material_body_motion import FIELDS as MOTION
from scripts.compose_apparent_asymmetry import FIELDS as ASYMMETRY
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-conjecture-laws.noema';PARENT_BASIS='data/conjecture-laws-basis-v1.json'
FULL='examples/v014/einstein-relativity-conjecture.noema';CORE='examples/v014/relativity-conjecture-core.noema'
BASIS='data/relativity-conjecture-basis-v1.json';ANNOTATIONS='data/relativity-conjecture-identifiers-v1.json';INDEX=213
SCHEMA='i[h['+' '.join(t for _,t in ASYMMETRY)+'] c]'
DISCOURSE=[('node','a'),('author','a'),('first','i[e]'),('second','i[e]'),('scope','a'),('context','d')]
PRIMITIVES={
 'eisbn':([('claim','i[e]'),('parameter','a'),('order','b'),('reference','d')],'閉じたclaimの量的な法則・比較を、parameterが指定する小量による展開で非負整数order次までの項を保持する範囲に限って成り立つものとして読む。一次では定数項と線形項を保ち、二次以上の差があっても排除しない。比較対象・全ての適用設定・方向と同じ物理量・単位の対応はclaimから引き継ぎ、ある一方向や観測例だけへ範囲を縮めない。展開が定義されることを要し、微分や係数が未知なら無条件に真としない。この制限された成立と、無制限のclaimの成立・証明は別である。一般の任意文を自動近似する演算子ではなく、量的内容と展開規約の対応を与える基礎関係である。'),
 'eisbo':([], 'ここで一次の量と呼ぶ展開の小量への参照。系又は物体の相対的な運動速度を光の伝播速度の尺度で無次元化した比として読む。同じ運動方向を保って速度の尺度を小さくし、全適用方向で定数項・一次項を比較する規約である。零速度の一点だけの比較ではなく、光源の運動からの独立性という次の仮定をこの規約から導かない。'),
 'eisbp':([('document','a'),('claim','i[e]'),('reference','d')],'指定論説の記述時点より前に、同じclaimがこの論点の知識において根拠を備えた成立事項として既に確立されているという帰属。単に予想されていること、今後証明される予定、検査プログラムの成功とは区別する。実験的・理論的な確立のどちらか一方に原文を限定せず、特定の証明者や実験名を補わない。成立内容そのものは別の内容評価で保持し、この帰属だけで引用を実行しない。'),
 'eisbq':([('document','a'),('grounds','i[e]'),('claim','i[e]'),('reference','d')],'この論説の論点で、groundsの事柄がclaimを考える理由となり、その推測へ思考を導くという根拠付けの関係。内容の向きと同一性を保ち、単なる並置や時系列ではない。演繹的な含意、決定的な証明、根拠の唯一性や十分性までは要求しない。根拠の成立と結論への態度は別に記述し、この関係からclaimを真として実行しない。'),
 'eisbr':([('document','a'),('claim','i[e]'),('reference','d')],'この論説で同じclaimが、根拠に導かれたが全範囲で確立済みとはまだされない推測として取り上げられるという認識的な位置付け。断定済みの定理、単なる引用、偽と分かった主張、数値的確率へ替えない。claimの真偽をこの態度から決めず、根拠と既証の限定範囲は別に保持する。'),
 'eisbs':([('example','a'),('anchor','a'),('kind',SCHEMA),('reference','d')],'exampleが、先行するanchorの例と同じ論点でkindの比較構造を持つ同種の例である。ここで渡す型は、通常の理論適用で説明上の区別が生じても現象にはその区別が属さないように見える構造を明示する。対象・配置・物理量の具体値が先行例と同じであることや、磁石と導体だけであることは要求しない。綴りの類似や無関係な類推ではなく、論点を共有する例としての関係である。思考上の設定も許し、実行済みの実験とは限らない。'),
 'eisbt':([('example','a'),('document','a'),('reference','d')],'この論説が同じ論点で指す類似例の範囲にexampleが属する。先行例を含んでもよいが一例だけへ縮めず、論点と時点で指定される全範囲を用いる。類似の成立や推測の正しさを見て後から成功例だけを選ぶ条件ではない。'),
 'eisbu':([('attempt','a'),('document','a'),('reference','d')],'この論説で話題にする過去の試行の全範囲にattemptが属する。何を確かめようとしたか、成功したかは別関係で述べ、失敗したものだけを結果から選別しない。世界のあらゆる試行や未来の全試行までを指す量化範囲ではない。'),
 'eisbv':([('attempt','a'),('goal','i[e]'),('reference','d')],'同じattemptが、goalに記述された事柄を観測・実験によって確かめることを目的とした意図的な試行である。目標内容を定め、単にそれについて考えたこと、試行の計画だけ、既に確かめ終えたこととは区別する。goalの物理的成立を試行の実施から認定しない。'),
 'eisbw':([('attempt','a'),('goal','i[e]'),('reference','d')],'同じattemptが、同じgoalの事柄を観測・実験的な根拠によって確かめるという目的を達成した。単に測定値や報告があることとは異なる。達成の否定は目的の不達成であり、goal自体の否定、装置の不存在、未知入力からの失敗認定とは区別する。'),
 'eisbx':([], '原文のErdeが指す地球。特定の実験装置・観測者や太陽との静止を補わず、地球の運動の内容は同じ対象へ別に結ぶ。'),
 'eisby':([], '原文が引用符付きのLichtmediumとして取り上げる、光の伝達を担うと仮定される媒体への談話上の参照。光の現象を媒介すると想定する対象であり、説明のない空間名や地球そのものとはしない。その物理的実在や静止する絶対空間はこの参照だけで断言しない。'),
 'eisbz':([('frame','a'),('medium','a'),('reference','d')],'仮定するmediumを静止の基準として位置と時間を与える座標系がframeであるという、媒体に相対的な運動を記述する設定。任意の系を媒体の系と呼ぶだけではなく、同じ媒体に対する静止規約を共有する。媒体の実在やその系の絶対的な特権は含意しない。'),
 'eisb2':(DISCOURSE,'著者が同じ箇所・範囲でfirstを保持した上で、その成立範囲をsecondにも拡張するという追加の提示を行う。not only/but alsoのように第一の内容を否定せず、第一だけでは尽くされないことを示す。引用内容をこの談話帰属で実行せず、二つの範囲の同一視や全分野への拡張は要求しない。'),
 'eisb3':(DISCOURSE,'著者が同じ箇所・論点でfirstの否定的な特徴付けに続けてsecondをむしろ採るべき積極的な定式化として示す。第一の否定を撤回すること、二内容の論理的矛盾や厳密な同義性は要求しない。単なる二項の併置とは区別し、引用された推測をこの提示関係から事実にしない。'),
 'eisb4':([], '固定原文einstein-1905:u0004[0,522)の、類似例と検出失敗から推測へ進み、一次の量での既証を付記する第一文の箇所。'),
}
MEANINGS={
 'eifk':'指定範囲に異なる少なくとも二個体が属するという複数性。範囲の全成員への条件や全世界での件数は別に記述する。',
 'eifl':'地球eisbxが、仮定した光媒体eisbyの静止系に対して全物質点・全区間のeiagの意味で運動するという検出目標の内容。系・単位・時刻区間・物質点と軌跡は存在量化し、特定の数値・装置を補わない。これを試行の目標として引用することは、運動や媒体の現実的成立を要求しない。',
 'eifm':'同じ論説が取り上げる例が複数あり、その全てが同じ先行例eisacと一般比較eiewの論点を共有する類似例であるという根拠内容。先行例と数値や物体を同一視しない。',
 'eifn':'同じ論説で取り上げる過去の試行が複数あり、その全てが同じeiflを確かめようとしたが、その同じ目的を達成しなかったという根拠内容。否定は成功にかかり、地球の運動の不存在へはかからない。',
 'eifo':'類似例eifmと、検出を目指した試行の失敗eifnの両方を同じ評価点で結ぶ根拠。片方だけを根拠の全体に替えない。',
 'eifp':'全力学適格系での共通法則というeifgを、同じ速度比の展開の一次までに制限した成立内容。原文のdiesを直前の法則の共通性に結び、絶対静止の不存在や推測全体が無制限に証明されたことへ広げない。',
 'eifq':'一次までの同じ成立eifpと、それが論説の時点で既に確立しているというeisbpを結ぶ。既証の名札だけで内容を省略しない。',
 'eifr':'両根拠eifoが成立し、それが同じeifjの推測へ導くこと、eifjが推測として取り上げられること、限定したeifqが既証であることを同じ点で結ぶ第一文の内容。推測eifj又は検出目標eiflそのものの真偽をここで要求しない。',
 'eifs':'eifrの認識的な叙述を主張するメッセージ。eifjを定理や仮定として採用するメッセージへは替えない。前提化は次の文で別に記述する。',
 'eift':'力学における絶対静止への対応特性がないというeifhの閉じた内容。nicht nurの第一の範囲を同じ概念へ結ぶ。',
 'eifu':'電気力学における絶対静止への対応特性がないというeifhの閉じた内容。sondern auchによる拡張の第二の範囲を同じ概念へ結ぶ。',
 'eifv':'著者・論説へのeifsの帰属、力学から電気力学への追加、否定的な特徴付けから積極的な共通法則への定式化、法則の共通性への一次での既証という補足、先行段落末尾からの本文順序を保持する。引用した物理内容を提示関係の評価時に実行しない。',
}
LIMITS=[
 '類似例と試行の複数形をそれぞれ非単一の範囲として読む。件数、実験名、著者自身の実験実施や全世界の全試行は指定しない。',
 'Lichtmediumは仮定される伝達媒体として読む。検出目標への参照からその実在、絶対静止、地球の実際の運動又は静止を導かない。',
 '一次の量は速度と光の伝播速度の尺度の比による展開の一次までと読む。定数項と線形項を保ち、高次の一致を要求しない。原文が省略する展開規約の明示的な採用解釈であり、唯一の歴史的解釈や具体的な実験の再現とはしない。',
 '推測の内容eifjは前回の全法則・全候補・全適格系と絶対静止の否定の規約を引き継ぐ。既証の限定は直前の法則共通性eifgに結び、推測全体を証明済みとしない。',
 '第一文全体の記述であり、次の前提化・光速度の仮定・二前提の十分性・光エーテル不要と段落全体の確認は残る。',
]

def content(name,body):return 'd '+name+'[] e[b point['+body+']].\n'
def evaluate(name):return 't[k '+name+'[]][v point]'
def selected(symbol,person):return k(symbol,person,k('eirf'),v('point'))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eifk',[('scope','h[a] c')],q('g','first','a',q('g','second','a',both(op('u',op('e',v('first'),v('second'))),app(v('scope'),v('first')),app(v('scope'),v('second'))))))
    motion=both(k('eisbz',v('frame'),k('eisby'),v('point')),k('eiag',*[k('eisbx') if n=='body' else v('point' if n=='context' else n) for n,_ in MOTION]))
    for n,t in reversed(MOTION):
        if n not in ('body','context'):motion=q('g',n,t,motion)
    text+=content('eifl',motion)
    for name,selector,condition in (
        ('eifm','eisbt',k('eisbs',v('item'),k('eisac'),'r[p eiew]',v('point'))),
        ('eifn','eisbu',both(k('eisbv',v('item'),'r[k eifl[]]',v('point')),op('u',k('eisbw',v('item'),'r[k eifl[]]',v('point')))))):
        text+=content(name,both(k('eifk','i[item a]['+selected(selector,v('item'))+']'),q('f','item','a',op('y',selected(selector,v('item')),condition))))
    text+=content('eifo',both(evaluate('eifm'),evaluate('eifn')))
    text+=content('eifp',k('eisbn','r[k eifg[]]',k('eisbo'),'n p b b',v('point')))
    text+=content('eifq',both(evaluate('eifp'),k('eisbp',k('eirf'),'r[k eifp[]]',v('point'))))
    text+=content('eifr',both(evaluate('eifo'),k('eisbq',k('eirf'),'r[k eifo[]]','r[k eifj[]]',v('point')),k('eisbr',k('eirf'),'r[k eifj[]]',v('point')),evaluate('eifq')))
    text+='d eifs[] f[j s[k eifr[]]].\n'
    for name,branch in (('eift','eisbl'),('eifu','eisbf')):text+=content(name,k('eifh',k(branch),v('point')))
    text+=define('eifv',[],both(k('eir3',k('eisb4'),k('rd'),k('eirf'),'r[k eifs[]]',k('ri')),
        k('eisb2',k('eisb4'),k('rd'),'r[k eift[]]','r[k eifu[]]',k('eirf'),k('ri')),
        k('eisb3',k('eisb4'),k('rd'),'r[k eifi[]]','r[k eifg[]]',k('eirf'),k('ri')),
        k('eisa5',k('eisb4'),k('rd'),'r[k eifg[]]','r[k eifq[]]',k('ri')),
        k('ue',k('eisav'),k('eisb4'),k('ri')),op('u',op('e',k('eisav'),k('eisb4')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eifv',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='grounds_for_conjecture_with_first_order_prior_establishment',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/conjecture-laws-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
