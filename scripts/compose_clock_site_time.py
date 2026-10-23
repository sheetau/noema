"""Connect the second measurement sentence to each frame's local clock field."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_measured_space_sentence_v2 import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_material_axes import interval
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-measured-space-sentence-v2.noema';PARENT_BASIS='data/measured-space-sentence-basis-v2.json'
FULL='examples/v014/einstein-clock-site-time.noema';CORE='examples/v014/clock-site-time-core.noema'
BASIS='data/clock-site-time-basis-v1.json';ANNOTATIONS='data/clock-site-time-identifiers-v1.json';INDEX=271
PRIMITIVES={
 'eisnk':([('event','a'),('moment','a'),('frame','a'),('context','d')],'eventの生起が、同じframeの時刻規約でmomentという時点に属するという出来事と時点の対応。異なる場所の出来事が同じ時点に属する場合はその系での同時性に従い、全系共通の瞬間を仮定しない。同じ時点の複数の記述を許す。数値の一致だけで無関係な出来事をこの対応へ含めず、対応の存在、各時点の値の存在・一意性と局所時計の指示との一致は別に合成する。'),
 'eisnl':([], '移動系の時刻を指す記号τの呼称個体。印字形は識別表記へ置き、値と系の規則はeisloで別に結ぶ。静止系のtとの等値を含意しない。'),
}
MEANINGS={
 'eiye':'任意の指定系に相対的に静止する同じ時計の型・校正・時間単位と、完全な代表配置履歴eit2を結ぶ。初期raへ固定したeivjを各系の自系配置へ一般化し、針や内部の全物質点を停止させない。',
 'eiyf':'初期と同じ全配備時計を同期範囲qaへ結び、同じ系・時間単位・共通参照による規約の下で、全時計の校正・自系静止・全所在地点の空間内所属と光往復同期を要求する。全配備時計対にqoを適用し、§1の一つの整合的な時計網として扱う。空間の全地点に時計を置く条件ではない。',
 'eiyg':'同じ配備時計・空間内の場所・系・時間単位について、eiuiの同期と実際の同所表示にeiyeの校正された自系静止履歴を結ぶ局所時刻の関係。別時計の表示や遠隔信号の到着を代用しない。',
 'eiyh':'同じ出来事・場所・系・値について、eiygを満たす配備時計がその場所に存在する。時計だけ又は場所だけを別の候補で満たさない。',
 'eiyi':'同じ出来事の候補zbeがeiukの全実数にわたる存在・一意性と局所表示対応を満たし、その同じ値が指定場所の配備時計によるeiyhも満たす。',
 'eiyj':'同じ出来事の生起に対応する系内時点が存在し、その全対応時点についてzcf/ylの有効な一意時刻と同じ局所出来事時刻zbeが一致する。時点個体の一意性や異なる系の同時性は要求しない。',
 'eiyk':'eiyfの時計網を用い、時計のある全地点で起こる全対象出来事に、同じ場所のeiyiと時点へのeiyjを与える。sgiの対象出来事範囲は全範囲zczであり、成功標本への限定や時計のない地点への値の生成をしない。',
 'eiyl':'指定系の同じ時点・時間単位rbに対し、zcfで存在・一意性を確認したylと与えられた実数値が一致するという量の規則。',
 'eiym':'移動系zbmの時点におけるeiylをτの解釈規則とする。tの既存eiwtと同型だが、系を混同せず値の一致を要求しない。',
 'eiyn':'静止系raにおけるeiygを、出来事・時計・場所・値・状況の閉じた規則として引用できる形へ接続する。§1の同じ局所表示と光往復同期の手順の静止系への適用である。',
 'eiyo':'移動系zbmにおけるeiygの閉じた規則。§1の手順をその系に静止する同じ配備時計へ適用し、静止系の時刻や参照時計を代入しない。',
 'eiyp':'同じ移動後の設定zb6で、静止系と移動系のそれぞれについてeiykを満たす時計所在地の時刻設定内容。',
 'eiyq':'既出tのeiwtとτのeiymへの記号対応、ならびに両系の局所規則eiyn/eiyoについて第一節の同じ光信号法を参照する二つの対応を保持する。引用から物理的実行を導かない。',
 'eiyr':'先行する空間測定zc2へ、両系の時計時刻eiypを同じ節の思考設定としてさらに採用する内容。eiyqの二つの方法参照と記号対応を保つ。',
 'eiys':'両系の時計所在地へ時刻を定める追加設定eiyrへの指示メッセージ。実測完了や既に成立した事実の報告へ替えない。',
 'eiyt':'u0045第二文の指示を同じ著者・論説へ帰属し、第一文の空間測定からの順序を保持する。',
}
LIMITS=[
 'u0045第二文[241,761)の426本文文字を、第一文の同じ二系と計器・移動後設定に追加する思考上の指示として読む。Es werde fernerとebenso werdeを同じ二系の対称な時刻設定へ接続する。',
 '各系の全配備時計は初期と同じ対象で、自系に相対的に静止し校正される。代表位置の完全な静止履歴を使い、時計内部を停止させない。先行設定の共動は保持され、ここで加速機構や絶対静止を追加しない。',
 '時計のある全地点に限り、そこで起きる全対象出来事へ局所表示で時刻を付与する。全空間への実機配置や、空の場所で出来事を生成する条件は加えない。zczは有限測定標本でなく対象の全範囲である。',
 '§1の手順は同じ系の全配備時計対のqoによる光往復全試行の同期である。qlで全必要試行の範囲を指定し、異なる時計間は非空な試行と全試行のdbを要求する。共通参照時計も同じ配備範囲に属する。初期設定では参照時計の選定自体を指定していないため、初期のzbhとの等置は補わない。',
 'eiyn/eiyoは新しい同期方式ではなく、§1のsaf/qoと局所表示を指定系の配備・校正条件へ適用した規則である。二つの第一節参照を同じ文書区分eisdyに結ぶ。方法の適用条件は合成し、参照だけで同期・測定済みを認定しない。',
 '既出tはeiwtの時点規則を変更しない。出来事とその系の生起時点を一般関係eisnkで結び、全対応時点のylとその出来事のzbeを比較する。τは同型の移動系規則に結び、t=τや系間の同時性の一致を追加しない。',
 '時計所在地の全出来事についての時刻付与は想定内容であり、全実数の有限検査・物理的実現・原文同義性の自動証明ではない。二作品全体の目標は継続中。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    c=v('context');f=v('frame');cl=v('clock');p=v('place');e=v('event');val=v('value');ref=k('zbh',f,c)
    frame=[('frame','a'),('context','d')]
    tracks=[k('eismh',cl,f,k('ta'),k('rb'),k(a),c) for a in ('yn','yo','yp')]
    text+=define('eiye',[('clock','a')]+frame,both(k('ca',cl),k('va',f),k('ci',k('rb')),k('eisdf',cl,c),k('cc',cl,f),k('eit2',cl,f,c,k('ta'),k('rb'),*interval(f,c),*tracks)))
    pop=lambda cl:k('zbz',f,cl,c)
    places='i[place a]['+k('zcu',p,f,c)+']';clocks='i[clock a]['+pop(cl)+']';located='i[clock a place a]['+k('cb',cl,p,f)+']'
    net=k('sgg',places,clocks,located,'i[clock a]['+k('eiye',cl,f,c)+']','i[clock a reference a]['+k('qo',cl,v('reference'),f,k('rb'),c)+']',ref)
    pairs=q('f','first','a',q('f','second','a',op('y',both(pop(v('first')),pop(v('second'))),k('qo',v('first'),v('second'),f,k('rb'),c))))
    text+=define('eiyf',frame,both(k('va',f),k('ci',k('rb')),k('eisb7',f,ref,k('rb'),c),q('f','clock','a',both(op('z',pop(cl),k('zbz',f,cl,k('zb4'))),op('z',k('qa',cl,f,c),pop(cl)))),net,pairs))
    local=[(n,'a') for n in ('event','clock','place','frame')]+[('value',R),('context','d')]
    text+=define('eiyg',local,both(pop(cl),k('zcu',p,f,c),k('eiye',cl,f,c),k('eiui',e,cl,p,f,k('rb'),val,c)))
    value=[(n,'a') for n in ('event','place','frame')]+[('value',R),('context','d')]
    text+=define('eiyh',value,q('g','clock','a',k('eiyg',*[v(n) for n,_ in local])))
    assigned=[(n,'a') for n in ('event','place','frame')]+[('context','d')];stamp=k('zbe',e,f,k('rb'),c)
    text+=define('eiyi',assigned,both(k('eiuk',e,f,k('rb'),c),k('eiyh',e,p,f,stamp,c)))
    moment=v('moment');at=k('eisnk',e,moment,f,c);time=k('yl',moment,f,k('rb'),c)
    bridge=both(k('zcf',moment,f,k('rb'),c),k('ba',time),k('sca',time,stamp))
    text+=define('eiyj',[('event','a')]+frame,both(k('zbd',e),k('ba',stamp),q('g','moment','a',at),q('f','moment','a',op('y',at,bridge))))
    field=k('sgi',places,clocks,located,'i[event a]['+k('zcz',e,f,c)+']','i[event a place a]['+k('cb',e,p,f)+']','i[event a place a]['+both(k('eiyi',e,p,f,c),k('eiyj',e,f,c))+']')
    text+=define('eiyk',frame,both(k('eiyf',f,c),field))
    text+=define('eiyl',[('moment','a'),('frame','a'),('value',R),('context','d')],both(k('zcf',moment,f,k('rb'),c),k('ba',val),k('ba',time),k('sca',val,time)))
    text+=define('eiym',[('moment','a'),('value',R),('context','d')],k('eiyl',moment,k('zbm'),val,c))
    for name,fr in (('eiyn','ra'),('eiyo','zbm')):
        text+=define(name,[(n,t) for n,t in local if n!='frame'],k('eiyg',e,cl,p,k(fr),val,c))
    text+=content('eiyp',both(*(k('eiyk',k(fr),k('zb6')) for fr in ('ra','zbm'))))
    clauses=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),v('point')) for sign,rule in (('eism5','eiwt'),('eisnl','eiym'))]
    clauses += [k('eislp',k('zc3'),k('rd'),k('eisdy'),'r[p '+rule+']',k('eirf'),v('point')) for rule in ('eiyn','eiyo')]
    text+=content('eiyq',both(*clauses))
    text+=content('eiyr',both(k('ug',k('zc3'),k('rd'),quote('eiyp'),k('eisms'),v('point')),k('zao',k('zc2'),k('zc3'),k('eisms'),v('point')),'t[k eiyq[]][v point]'))
    text+='d eiys[] f[j m[k eiyr[]]].\n'
    text+=define('eiyt',[],both(k('eir3',k('zc3'),k('rd'),k('eirf'),quote('eiys'),k('ri')),k('ue',k('zc2'),k('zc3'),k('ri')),op('u',op('e',k('zc2'),k('zc3')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eiyt',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='clock_site_time_with_local_readings_and_moment_bridge',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/measured-space-sentence-identifiers-v2.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    template=deepcopy(next(e for e in ann['entries'] if e['symbol']=='eism5'));template.update(symbol='eisnl')
    template['forms']=[dict(text='τ',language='de',role='printed_identifying_form')]
    ann['entries'].append(template)
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
