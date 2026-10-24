"""Compose a distant electromagnetic source and its local wave approximation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read,FIELDS as PHYSICAL
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import POINT,REGION,FIELD,ROLES
from scripts.compose_plane_waveforms import PROFILE,AMPLITUDES
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-seat-questions.noema';PARENT_BASIS='data/seat-questions-basis-v1.json'
FULL='examples/v014/einstein-distant-wave-source.noema';CORE='examples/v014/distant-wave-source-core.noema'
BASIS='data/distant-wave-source-basis-v1.json';ANNOTATIONS='data/distant-wave-source-identifiers-v1.json';INDEX=363
SPACE='h['+' '.join([R]*3)+'] c'
PATCH=[('space',SPACE)]+[(n,R) for n in ('inner','outer','lower','upper')]
SOURCE=[(n,'a') for n in ('source','process','frame','lengthunit','timeunit')]+[('context','d')]
EMISSION=[(n,'a') for n in ('source','process','wave','frame','lengthunit','timeunit','electricunit','magneticunit')]+[('electricfield',FIELD),('magneticfield',FIELD),('region',REGION),('context','d')]
NUMERIC=[('sine',PROFILE),('cosine',PROFILE)]+[(n,R) for n in ('light','rate','ax','ay','az',*AMPLITUDES,'electricbound','magneticbound')]+[('electricfield',FIELD),('magneticfield',FIELD),('region',REGION)]
SETTING=[(n,'a') for n in ('source','process','wave','frame','lengthunit','timeunit','chargeunit','electricunit','magneticunit','forceunit','scope')]+[('context','d')]+PATCH+[('multiple',R)]+[(n,t) for n,t in NUMERIC if n!='region']
WITNESSES=[(n,t) for n,t in SETTING if n not in ('frame','scope','context','light')]
code=lambda fields:'i[h['+' '.join(t for _,t in fields)+'] c]'
PRIMITIVES={
 'eisrt':(SOURCE+[('point',POINT)],'同じsourceが同じprocessの放射に関与する物理的な源として占める全ての関連位置・時刻の範囲にpointが入る。同じframe・校正された長さ時間単位・contextで四座標を与える。これは源の物理的支持範囲であり、便宜的な代表点や成功した放出点だけに範囲を縮めない。対象領域へ届く波に関与する源の履歴を対象とし、源が一点、全時刻静止、単一の瞬間に放出済みであるとは要求しない。任意の数値関数から物理的位置を認定しない。'),
 'eisru':(EMISSION,'同じsourceが物理的な電気・磁気の作用を通じて外へ伝わる振動的な電磁過程processを発生させ、その放射に由来する同じ波waveが、regionでelectricfieldとmagneticfieldとして記述されるという源と波の物理的帰属。離れた場の数値の偶然の一致、単なる静電場、源を伴わない任意の正弦関数とは区別する。frame・長さ時間・二場の単位・contextを共有し、場の物理的同定はejsnへ別に結ぶ。特定の材質・放射機構・可視周波数・等方放射・点源・実験の実施を要求しない。光源の運動を静止と補わず、距離から近似の十分性を自動的に導く関係でもない。'),
 'eisrv':([('multiple',R),('scope','a'),('context','d')],'scopeの局所的な空間考察で、比較する長さの比に対しmultipleを非常に大きいとする文脈上の基準値として採る。数値は原文が指定しないため引数に保ち、実際の距離が大きいことや近似の成功をこの関係だけに含めない。結果に合わせて任意に低い境界へ変更せず、同じ考察の空間尺度に対する非常に大きい程度として解釈する。multipleが有効かつ1より大きいことは別に要求する。'),
 'eisrw':([('wave','a'),('frame','a'),('region',REGION),('scope','a'),('electricbound',R),('magneticbound',R),('electricunit','a'),('magneticunit','a'),('context','d')],'同じ波・系・全領域・用途scope・二場の単位・文脈に対して、electricboundとmagneticboundの一様な成分絶対誤差以内の表現が、その考察で扱う周波数・方向・振幅の結論に十分な精度と見なされるという用途上の規約。単に誤差上限があること、原点の一点で一致すること、源が遠いことから自動認定しない。全領域と同じ単位の上限を使い、原文にない具体的な数値や誤差の零を補わない。近似の実際の成立は別に要求する。'),
 'eisrx':([], 'この論説の第七節。u0178の見出しから第八節の直前までの、波の周波数・方向・振幅の系間比較を扱う区分。見出しの全主題の構成はこの参照だけで代用しない。'),
 'eisry':([], '固定原文einstein-1905:u0179で遠方の源と原点を含む局所領域の波形近似を仮定する箇所。'),
 'eisrz':([], '固定原文einstein-1905:u0180のM0320という後続の表示式の箇所。数式自体の内容は既存の位相と六成分の波形構成へ別に結ぶ。'),
 'eissa':([('node','a'),('display','a'),('construction',code(NUMERIC)),('document','a'),('context','d')],'同じdocumentのnodeがコロンで先へ示す表示式がdisplayにあり、その場の数値表現を閉じたconstructionの規約で解釈するという前方参照。constructionは同じ正弦・余弦、位相の速度と率・方向・六振幅、二場・領域・二誤差の引数を持ち、仮定内容への適用ではそれらの値を共有する。表示の綴りだけで波形を代用せず、この参照だけで引用した内容の真理や物理的な近似を断言しない。'),
}
MEANINGS={
 'ekat':'同じ有効な三座標について、空間集合の各点が外半径以内にあり、内半径より原点に近い点は全て集合に入るという二つの含意。原点の近傍を含む有界な空間部分の局所条件であり、球形だけへ固定しない。',
 'ekau':'固定されたspaceと閉時間区間の積を四座標領域として構成する。全座標の実数妥当性を保持し、空間と時刻の引数を交換しない。',
 'ekav':'正の内半径とそれ以上の有限な外半径、正の長さの時間区間、全有効三座標でekatを満たす空間部分。全区間で原点の空間近傍を保つ一つの局所的な読み。',
 'ekaw':'源の同じ四座標が有効で、原点からの三空間成分の距離二乗が、外半径と指定倍率の積の二乗以上である。時間座標を距離へ混ぜず、外半径が正で倍率が1より大きいことを要求する。',
 'ekax':'源の物理的な関連支持範囲が非空であり、同じ系・単位・文脈でその全点がekawの距離条件を満たす。非常に大きい倍率は用途の同じ文脈基準eisrvに結ぶ。単一の代表点だけが遠い場合を許さない。',
 'ekay':'正弦・余弦と同じ位相・方向・六振幅から二つの近似場を構成し、同じ実際の二場が全指定領域で二上限以内にある。数式の波形と十分性の判断を区別し、原点だけの一致を全領域へ広げない。',
 'ekaz':'源の全支持範囲の遠さ、固定した原点近傍と時間区間、物理的な源と同じ二場の帰属、校正された場と単位、同じ波形近似、その用途に対する十分性を一つの設定へ結ぶ。',
 'ekba':'同じK・第七節・光速度Vについてekazを満たす源と波・場・領域尺度・波形値・誤差・単位があるという仮定内容。数値や点源を本文へ補わない。',
 'ekbb':'ekbaを同じ著者の仮定提示として帰属し、コロンが示す後続の六成分・位相の表示へ前方参照する。実際に源が設置されたという報告にしない。',
 'ekbc':'遠方源と局所近似を仮定する提示ekbbを述べるメッセージ。',
 'ekbd':'同じ著者・論説にu0179の仮定提示を帰属し、第六節末尾に続く箇所として本文へ接続する。第七節見出しの内容自体はこの順序関係から認定しない。',
}
LIMITS=[
 'u0179のbefinde sichとdargestellt seiは同じ仮定設定の導入として読む。Kは既存ra、Vはtc、第七節の考察範囲はeisrxであり、実験実施・実在源の発見・源の静止を追加しない。',
 '源は、同じ物理的な電磁過程と領域の二場を放射として発生させる対象として解釈する。可視光だけ、点源、球対称波、単一時刻の放出又は特定物質へ限定しない。源の支持範囲と作用の帰属を単なる座標値や関数形へ縮めない。',
 'sehr ferneは、考察する局所空間部分の外側尺度に比べ、源の関連支持範囲の全点が文脈上非常に大きい倍率以上の原点距離にあるという読み。原文に比の数値はない。正の尺度と1より大きい倍率、実際の距離、程度基準を別に要求する。',
 'Raumteilは、原点の正の開近傍を含む有界な空間集合を、正の長さの時間区間にわたって固定して使う局所的な読みを採る。全空間・全時刻の近似や球形への限定ではない。この読みは一時刻だけの包含より強い明示的な理想化である。',
 '十分な近似は二場の成分ごとの一様絶対誤差と用途上の十分性を分ける既存の読みを使い、源が遠いことから誤差評価を自動導出しない。二つの誤差の単位は物理的な場の単位と同じに保つ。全域の十分性を原点の一点の一致にしない。',
 'M0320の正弦・共通位相・六振幅はsd24/sdx2を再利用する。横波の振幅関係seajや全場の方程式を、ここで表示する六波形の式だけに追加しない。表示式単位u0180の個別の記号と数式の全照合は別に行う。',
 '既存seaw/seaxは光信号cfと横波条件seajを含むため、そのまま全意味を流用しない。正弦波形・全領域の誤差seat・校正された物理場ejsnを再利用し、電磁放射の帰属と領域・十分性を同じ引数へ結び直す。',
 '有限検査は局所幾何学と引数接続を診断するもので、全実数・全関数域や放射の物理理論を証明するものではない。見出しu0178と表示式u0180の全意味判断はこの文の構成と区別する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');square=lambda x:k('shv',x,x)
    xyz=[v(n) for n in ('x','y','z')];norm=k('seag',*xyz);valid=both(*(k('ba',x) for x in xyz));inside=app(v('space'),*xyz)
    text+=define('ekat',PATCH[:3]+[(n,R) for n in ('x','y','z')],op('y',valid,both(op('y',inside,k('bc',norm,square(v('outer')))),op('y',k('bg',norm,square(v('inner'))),inside))))
    region=both(valid,k('ba',v('time')),inside,k('lg',v('lower'),v('upper'),v('time')))
    text+=define('ekau',[('space',SPACE),('lower',R),('upper',R)],'i['+' '.join(n+' '+R for n in ('x','y','z','time'))+']['+region+']',REGION)
    local=k('ekat',v('space'),v('inner'),v('outer'),*xyz)
    for n in reversed(('x','y','z')):local=q('f',n,R,local)
    text+=define('ekav',PATCH,both(*(k('ba',v(n)) for n in ('inner','outer','lower','upper')),k('bg',zero,v('inner')),k('bc',v('inner'),v('outer')),k('bg',v('lower'),v('upper')),local))
    coords=[app(v('point'),k(n)) for n in ROLES]
    text+=define('ekaw',[('point',POINT),('outer',R),('multiple',R)],both(*(k('ba',x) for x in coords+[v('outer'),v('multiple')]),k('bg',zero,v('outer')),k('bg',one,v('multiple')),k('bc',square(k('shv',v('outer'),v('multiple'))),k('seag',*coords[:3]))))
    selected=k('eisrt',*args(SOURCE),v('point'))
    text+=define('ekax',SOURCE+[('outer',R),('multiple',R),('scope','a')],both(k('eisrv',v('multiple'),v('scope'),v('context')),q('g','point',POINT,selected),q('f','point',POINT,op('y',selected,k('ekaw',v('point'),v('outer'),v('multiple'))))))
    base=[v(n) for n in ('sine','light','rate','ax','ay','az')];amps=[v(n) for n in AMPLITUDES]
    text+=define('ekay',NUMERIC,both(k('sd24',v('sine'),v('cosine'),v('light'),zero,v('rate'),v('ax'),v('ay'),v('az'),*amps),k('seat',v('electricfield'),v('magneticfield'),k('sdx2',*base,*amps[:3]),k('sdx2',*base,*amps[3:]),v('electricbound'),v('magneticbound'),v('region'))))
    region=k('ekau',v('space'),v('lower'),v('upper'));get=lambda n:region if n=='region' else one if n=='electricconversion' else k('sjd',v('light')) if n=='magneticconversion' else v(n)
    physical=k('ejsn',*[get(n) for n,_ in PHYSICAL])
    text+=define('ekaz',SETTING,both(k('ekav',*args(PATCH)),k('ekax',*args(SOURCE),v('outer'),v('multiple'),v('scope')),physical,k('eiscc',v('frame'),v('lengthunit'),v('timeunit'),k('tb'),v('context')),k('eispn',v('process'),v('frame'),v('electricfield'),v('magneticfield'),region,v('context')),k('eisru',*[get(n) for n,_ in EMISSION]),k('ekay',*[get(n) for n,_ in NUMERIC]),k('eisrw',v('wave'),v('frame'),region,v('scope'),v('electricbound'),v('magneticbound'),v('electricunit'),v('magneticunit'),v('context'))))
    override={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')}
    text+=content('ekba',bind(WITNESSES,k('ekaz',*[override.get(n,v(n)) for n,_ in SETTING])))
    text+=content('ekbb',both(k('ug',k('eisry'),k('rd'),quote('ekba'),k('eisrx'),v('point')),k('eissa',k('eisry'),k('eisrz'),'r[p ekay]',k('eirf'),v('point'))))
    text+='d ekbc[] f[j s[k ekbb[]]].\n'
    text+=define('ekbd',[],both(k('eir3',k('eisry'),k('rd'),k('eirf'),quote('ekbc'),k('ri')),k('ue',k('eisrs'),k('eisry'),k('ri')),op('u',op('e',k('eisrs'),k('eisry')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekbd',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='distant_physical_source_and_local_wave_approximation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/seat-questions-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
