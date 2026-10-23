"""Preserve the author's universal reading and methodological conclusions."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_observer_contrast import ROOT,read,TRUE,FALSE
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_kinematics_headings import SIM
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-observer-contrast.noema';PARENT_BASIS='data/observer-contrast-basis-v1.json'
FULL='examples/v014/einstein-simultaneity-conclusion.noema';CORE='examples/v014/simultaneity-conclusion-core.noema'
BASIS='data/simultaneity-conclusion-basis-v1.json';ANNOTATIONS='data/simultaneity-conclusion-identifiers-v1.json';INDEX=265
LOCAL=[(n,'a') for n in ('event','clock','place','frame','unit')]+[('value',R),('context','d')]
VALUE=[(n,'a') for n in ('event','frame','unit')]+[('value',R),('context','d')]
EVENT=[(n,'a') for n in ('event','frame','unit')]+[('context','d')]
SAME=[(n,'a') for n in ('first','second','frame','unit')]+[('context','d')]
COMPARE=[(n,'a') for n in ('first','second','frame','other')]+[('context','d')]
PRIMITIVES={
 'eismo':([('agent','a'),('concept',SIM),('attribute','i[e]'),('permitted','c'),('document','a'),('context','d')], 'agentが同じdocumentの論点でconceptの意味にattributeという適用上の性格を与える解釈についての、方法上の許否の要請。permittedが偽ならその解釈をしてはならず、真ならその解釈を許容するという明示的な規範的極性である。実際にその解釈をしたか、属性自体が真か、法的な禁止かとは分ける。概念と属性を閉じた記述で同定し、語形だけの拒否や単なる未知・許可情報の不在にしない。'),
 'eismp':([('agent','a'),('first','a'),('second','a'),('frame','a'),('unit','a'),('relation',SIM),('polarity','c'),('document','a'),('context','d')], 'agentが同じ議論における適切な捉え方として、同じ二対象をframe・unit・contextにおけるrelationの適用対象としてpolarityの肯否で判断すべきだという認識上の要請。否定なら非成立と捉える要請であり、実際の判断や発言の発生、関係の真偽、未定義だから偽であるという扱いとは別である。適用可能性と関係の内容は合成側で保持する。'),
 'eismq':([('node','a'),('author','a'),('restriction','i[e]'),('replacement','i[e]'),('document','a'),('context','d')], 'authorがnodeでrestrictionにより退けた捉え方に対し、replacementを採るべき積極的な捉え方として置く訂正的な対置。否定的な制限を撤回せず、それだけで終わらない説明として後項を置く。単なる二項の並列、両立しない真理値の主張、時間的な後続だけへ替えない。引用内容の成立は別に合成する。'),
}
MEANINGS={
 'eiui':'同じ出来事・局所静止時計・場所・任意の指定系と時間単位について、safの共通参照zbhへの同期と実数表示、eisb7の時刻規約、同所の表示出来事eisgm/ceを結ぶ。既存eingの局所表示という内容を、固定ra/rc以外にも同じ型で適用する。',
 'eiuj':'同じ出来事・系・単位・値についてeiuiを満たす局所時計と場所が存在する。時計又は場所の名前だけ、別系の表示、候補値だけで時刻付与を認定しない。',
 'eiuk':'既存sehの候補zbeの付与と全値の一意性を保持し、同じ候補がeiujの局所表示にも対応することを要求する。全実数の唯一性を有限候補一覧へ替えない。',
 'eiul':'既存eihmの同時性と同じ二出来事・系・時間単位・文脈について、双方のeiukによる局所的表示対応を保つ同時性。第一節の概念を値の単なる偶然の等しさへ替えない。',
 'eium':'同じ出来事と系の時刻付与eiukを共通の時間単位rbで与える、比較域の利用可能性条件。',
 'eiun':'同じ二出来事と系の同時性eiulを時間単位rbへ接続する比較条件。',
 'eiuo':'既存eiokの全固定配置・全比較時点の等速並進に、同じ二系・尺度の共通速度三成分の有効性と少なくとも一成分の非零を加える。方向や軸の一致、出来事の運動方向の位置差は要求しない。',
 'eiup':'二出来事の同時性を比べる二系が、同じ文脈でeiuoの非零相対運動にあるという比較域。出来事の選別は別のsdxに委ね、位置差で成功例だけを選ばない。',
 'eiuq':'同じ比較設定zbjの全有効な出来事対・相対運動する系対で同時性が不変であるという、絶対的な意味の適用上の性格をseaで記述した内容。空の比較域での真を絶対性の証拠とはしない。',
 'eiur':'同じ比較域の全有効な組について第一系で同時なら第二系では非同時となるという、sedによる原文の全称的な内容。旧sem/sepの原文にない位置差条件は加えない。この内容の真理を処理系が証明したとはしない。',
 'eius':'同時性eiulの概念へeiuqの系に独立な不変性を意味として与えてはならないという、著者の議論の声に対する方法上の要請。物理的な不変性の否定だけや現実の誤解の発生に還元しない。',
 'eiut':'全有効な比較の同じ二出来事について、第一系で同時なら、相対運動する第二系では同時ではないものと捉えるべきだという認識上の要請。両系の全四時刻の利用可能性を保ち、系の変更を時間的な後日の変化にしない。',
 'eiuu':'原文後半の全称的な非同時性eiurと、それに即して捉える認識上の要請eiutを合わせる。単なる変化例の存在へ弱めず、対象の時刻値だけで要請の役割を省かない。',
 'eiuv':'同時性に絶対的な意味を与える解釈の禁止eiusと、相対運動する系からの非同時性の捉え方eiuuを合わせた結論内容。',
 'eiuw':'eiuvを述べ、先行する観測者の判断対比eiueを理由に見いだす結論としてeisdkへ結び、sondernの訂正的対置をeismqで保持する。視覚実験や一般化の自動証明へ替えない。',
 'eiux':'同時性の非絶対的な理解と相対運動する系からの捉え方の結論eiuwを述べるメッセージ。',
 'eiuy':'u0041の一文全体を同じ著者・論説の箇所zbkへ帰属し、観測者の対比zbbからの本文順序を保持する。',
}
LIMITS=[
 '原刊897頁のu0041全325文字・283非空白文字を対象とする。Wir sehen also、keine absolute Bedeutung beimessen dürfen、sondern、二出来事と相対運動する別系、nicht mehr ... aufzufassenを保持する。',
 '後半は文面の全称的な読みを採り、有効な比較の第一系で同時な二出来事が第二系では非同時となり、そのように捉えるべきだという著者の結論として記述する。旧部分草案sem/sepの運動方向の位置差を足して一般化を限定しない。存在する一例や単に保存が保証されないという弱い条件にも置き換えない。',
 'この全称的な内容が物理的に正しいと自動認定する課題ではない。偽になる比較モデルも区別できる形で内容と著者への帰属を分ける。後段の時刻変換、特定方向の出来事の離隔、光速度による速度上限をこの文へ新たな前提として加えない。',
 '二座標系はこの節の比較文脈の等速並進する系として読む。非零の速度ベクトルを用い、標準配置の軸一致や正のx方向に限らない。非慣性的な加速系一般までの主張へ拡張しない。第一節の時間規約と第二節の系の比較という共有文脈を保持する。',
 '絶対的な意味は、同じ出来事の同時性が比較する系に依存せず保存されるという適用上の性格として読む。全系の数値時刻が同じという意味や、出来事そのものの実在否定ではない。絶対性の概念一般をこの物理的比較以外の哲学全域へ定義しない。',
 'dürfenとaufzufassen sindはこの論証における解釈・認識上の要請である。禁止は許可情報の欠如や単なる不変性の偽ではなく、肯否の規範を明示する。著者の論述上のわれわれを同じ議論の声として保持し、法律・道徳・読者の心理的な実行の事実を補わない。',
 '全四時刻が同じ系・単位・共通参照時計の規約で有効かつ一意に付与された範囲を比べる。局所時計の表示は同じ場所の出来事と対応し、未付与を非同時と判定しない。物理的に異なる二出来事を両系で同じ対象として追い、別の出来事や別の尺度を代入しない。',
 'nicht mehrは相対運動する系からの捉え方へ移ることを表し、二出来事の同時性が後日変化するという順序を加えない。sondernは否定的な制限に対する積極的な捉え方の訂正的対置で、先行の否定を撤回しない。',
 '有限検査は局所表示・時刻候補と一意性の骨格・比較域・量化・規範的な肯否・引用の非実行を調べる。全実数、全物理系、論証の妥当性、意味同値の自動証明ではない。u0042以降と二作品全体は未完。',
]

def args(fs):return [v(n) for n,_ in fs]
def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    event=v('event');frame=v('frame');unit=v('unit');c=v('context');val=v('value');clock=v('clock');place=v('place');ref=k('zbh',frame,c)
    display=q('g','display','a',both(k('zbd',v('display')),k('cb',v('display'),place,frame),k('eisgm',event,v('display'),clock,frame,c),k('ce',clock,v('display'),frame,unit,val)))
    text+=define('eiui',LOCAL,both(k('zbd',event),k('va',frame),k('ba',val),k('eisb7',frame,ref,unit,c),k('saf',event,clock,place,ref,frame,unit,val,c,'p ca','p cb','p cc','p ci','p ce','p qo'),display))
    text+=define('eiuj',VALUE,q('g','clock','a',q('g','place','a',k('eiui',*args(LOCAL)))))
    stamp=k('zbe',event,frame,unit,c)
    text+=define('eiuk',EVENT,both(k('seh',*args(EVENT),'p qo','p ba','p sca'),k('eiuj',event,frame,unit,stamp,c)))
    text+=define('eiul',SAME,both(k('eihm',*args(SAME)),*(k('eiuk',v(e),frame,unit,c) for e in ('first','second'))))
    text+=define('eium',[('event','a'),('frame','a'),('context','d')],k('eiuk',event,frame,k('rb'),c))
    text+=define('eiun',[(n,'a') for n in ('first','second','frame')]+[('context','d')],k('eiul',v('first'),v('second'),frame,k('rb'),c))
    pair=[('first','a'),('second','a'),('context','d')];pa=args(pair)
    speed=lambda axis:k('eislc',v('first'),v('second'),k('eisli',*pa),k('eislj',*pa),k(axis),c)
    nonzero=lambda axis:op('u',k('sca',speed(axis),k('bb','n p a b')))
    text+=define('eiuo',pair,both(k('eiok',*pa),*(k('ba',speed(a)) for a in ('yn','yo','yp')),op('x',nonzero('yn'),op('x',nonzero('yo'),nonzero('yp')))))
    text+=define('eiup',COMPARE,k('eiuo',frame,v('other'),c))
    common=[k('zbj'),'p zbd','p va','p eiup','p eium','p eiun']
    text+=content('eiuq',k('sea',*common));text+=content('eiur',k('sed',*common))
    text+=content('eius',k('eismo',k('rd'),'r[p eiul]',quote('eiuq'),FALSE,k('eirf'),v('point')))
    selected=k('sdx',v('first'),v('second'),frame,v('other'),k('zbj'),'p zbd','p va','p eiup','p eium')
    before=k('eiun',v('first'),v('second'),frame,k('zbj'))
    norm=k('eismp',k('rd'),v('first'),v('second'),v('other'),k('rb'),'r[p eiul]',FALSE,k('eirf'),k('zbj'))
    body=op('y',both(selected,before),norm)
    for name in reversed(('first','second','frame','other')):body=q('f',name,'a',body)
    text+=content('eiut',body)
    for name,first,second in (('eiuu','eiur','eiut'),('eiuv','eius','eiuu')):text+=content(name,both('t['+k(first)+'][v point]','t['+k(second)+'][v point]'))
    text+=content('eiuw',both('t[k eiuv[]][v point]',k('eismq',k('zbk'),k('rd'),quote('eius'),quote('eiuu'),k('eirf'),v('point')),k('eisdk',k('eirf'),quote('eiue'),quote('eiuv'),v('point'))))
    text+='d eiux[] f[j s[k eiuw[]]].\n'
    text+=define('eiuy',[],both(k('eir3',k('zbk'),k('rd'),k('eirf'),quote('eiux'),k('ri')),k('ue',k('zbb'),k('zbk'),k('ri')),op('u',op('e',k('zbb'),k('zbk')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eiuy',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='frame_relative_simultaneity_and_interpretive_conclusion',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/observer-contrast-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
