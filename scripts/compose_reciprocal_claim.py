"""Present time-free spatial relations, mutual rest, identity and reciprocal scale."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_third_frame_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-third-frame-claim.noema';PARENT_BASIS='data/third-frame-claim-basis-v1.json'
FULL='examples/v014/einstein-reciprocal-claim.noema';CORE='examples/v014/reciprocal-claim-core.noema'
BASIS='data/reciprocal-claim-basis-v1.json';ANNOTATIONS='data/reciprocal-claim-identifiers-v1.json';INDICES=(312,313,314)
MEANINGS={
 'ejbq':'同じ第一系の尺度ta/rbで第二系の全固定配置・全比較時点を記述するeiojに、共通速度三成分の全てが零である条件を結ぶ。全配置が全時点対で変位しない相対静止。範囲や測定が欠ける場合を静止にせず、第一系と第二系の座標数値や時計率が同一とは要求しない。',
 'ejbr':'第一・最終記録の三位置成分だけを取り、指定倍率と第一の対応位置成分の積が最終成分に等しいという三式。各項の有効性と異なる三役割を要求する。各右辺の自由な座標引数はその位置成分だけで、時刻役割zc7を参照しない。',
 'ejbs':'現在の全四連鎖等式ejbkを指し、その同じ非空の全対象出来事の三記録について、最終の三位置関係を時刻引数のないejbrで表示する。倍率は同じ速度だけの関数積srhであり、時間tを含まない空間式という内容を保つ。',
 'ejbt':'Kから見たK′、K′から見たKの両向きに、全配置・全時点の零変位ejbqが成立する相互静止の内容。空間の再尺度化や時計の異なる進みを恒等変換と同一視しない。',
 'ejbu':'相異なる三系で全対象出来事に現在の記録が存在し、各系の値が一意であり、全対応三記録の第一と最終の四成分がshhで同値となる恒等変換の内容。時間成分を含め、記録名や基準系個体の同一性を要求しない。',
 'ejbv':'現在の二回変換の全四連鎖等式ejbkと、同じ三記録の恒等性ejbuを合わせた、相反積へ進む著者の前提内容。原文に書かれていない非零記録の証人や追加の校正条件を補わない。',
 'ejbw':'著者が現在の空間関係にtが現れないejbsを理由に、KとK′の相互静止ejbtが従わなければならないと述べる提示。',
 'ejbx':'著者が同じ相互静止ejbtからK→K′の恒等変換ejbuが従わなければならないと述べ、同じ恒等性を明らかだと提示する。必要性と明白さの帰属を、処理系による含意の証明に替えない。',
 'ejby':'現在の連鎖等式と恒等性ejbvに基づき、同じφの正負速度値の積が1であるsroを著者が結論する。積1から各値1を加えない。',
 'ejbz':'時間を含まない空間関係から相互静止へ進むejbwを述べるメッセージ。',
 'ejb2':'u0095前半の理由と相互静止を同じ著者・論説へ帰属し、二回変換の結果zgpからの順序を保持する。',
 'ejb3':'恒等変換の必要性と明白さejbxを述べるメッセージ。',
 'ejb4':'u0095後半の恒等変換への推論を同じ著者・論説へ帰属し、相互静止zgqからの順序を保持する。',
 'ejb5':'だから相反積1であるというejbyを述べるメッセージ。',
 'ejb6':'u0095末尾のEs ist alsoからu0096の積1の表示と句点までを同じ著者・論説へ帰属し、恒等性zgrからの順序を保持する。',
}
LIMITS=[
 '固定u0095とu0096を原刊901頁末から902頁冒頭へ照合する。空間式にtが現れない理由、二系の相互静止、恒等変換でなければならないという推論と明白さ、したがって同じφの正負値の積1という三段を保つ。',
 '時間を含まないは、既出四連鎖等式の最終三位置式が同じ位置成分と速度だけの倍率で書かれ、時刻値を右辺に取らないという読み。三式はejbrで実際に合成し、同じ現在の全対応記録へ適用する。時間式自体を無視又は削除する意味ではない。',
 '相互静止は、両向きのeiojによる全固定配置・全比較時点の履歴の共通速度三成分が零という読み。時計内部の針まで停止させず、相対静止だけで二系の尺度や時計率が同一とはしない。',
 '恒等変換は同じ対象出来事のKとK′の四座標値全ての一致。記録識別子や二系個体を同一とせず、同じ値の別記録を許す。原点だけの一致や三位置だけの一致へ弱めない。',
 'sein mußは既存zcの、その前提から結論が従わなければならないという推論の帰属で保持し、ist klarは既存zdgで同じ結論の明白さの提示として保つ。無条件の論理的真理、実験的実証又は処理系の証明認定に替えない。',
 '一般には相対静止と共通零点だけから尺度・時計率を含む恒等性は導けない。この点を原文にない校正条件で修理せず、著者が述べる推論を記述する。積1の導出にも原文にない非零証人を前提として補わない。',
 'sroは同じ正規化後φ=spcのvと−vの有効な値と積1。積が1でも各値は1とは限らず、負の組も式だけでは排除しない。後続の棒の長さによる対称性や符号規約を先取りしない。',
 '定義の意味と原刊の通読判断、有限対照・保存済み代数証拠、著者の主張の真理を区別する。未知入力の拒否と実切断の全域を有限標本で置換しない境界を保つ。',
]


def definitions():
    ctx=v('context');first=v('first');second=v('second');zero=k('bb','n p a b')
    text=define('ejbq',[('first','a'),('second','a'),('context','d')],both(k('eioj',first,second,k('ta'),k('rb'),ctx),*(k('sca',k('eislc',first,second,k('ta'),k('rb'),k(axis),ctx),zero) for axis in ('yn','yo','yp'))))
    clauses=[k('zc5',first),k('zc5',v('last')),k('ba',v('scale')),*(op('u',op('e',k(a),k(b))) for a,b in (('yn','yo'),('yn','yp'),('yo','yp')))]
    for axis in ('yn','yo','yp'):
        start=k('zc6',first,k(axis));end=k('zc6',v('last'),k(axis));rhs=k('spf',v('scale'),start)
        clauses += [k('ba',start),k('ba',end),k('ba',rhs),k('sca',end,rhs)]
    text+=define('ejbr',[('first','a'),('last','a'),('scale',R)],both(*clauses))
    setting=k('zb6');distinct=[op('u',op('e',k(a),k(b))) for a,b in (('ra','zbm'),('ra','zgi'),('zbm','zgi'))]
    def triples(body):
        value=op('y',k('eja4',v('event'),v('first'),v('middle'),v('last'),setting),body)
        for n in reversed(('event','first','middle','last')):value=q('f',n,'a',value)
        return value
    text+=content('ejbs',both(*distinct,op('t',k('ejbk'),v('point')),triples(k('ejbr',first,v('last'),k('srh')))))
    text+=content('ejbt',both(k('ejbq',k('ra'),k('zgi'),setting),k('ejbq',k('zgi'),k('ra'),setting)))
    text+=content('ejbu',both(*distinct,k('eja5',setting),triples(k('shh',first,v('last')))))
    text+=content('ejbv',both(*(op('t',k(n),v('point')) for n in ('ejbk','ejbu'))))
    for name,node,premise,result,clear in (('ejbw','zgq','ejbs','ejbt',False),('ejbx','zgr','ejbt','ejbu',True),('ejby','zgs','ejbv','sro',False)):
        clauses=[k('zc',k(node),k('rd'),quote(premise),quote(result),k('eisms'),v('point'))]
        if clear:clauses.append(k('zdg',k(node),k('rd'),quote(result),k('eisms'),v('point')))
        text+=content(name,both(*clauses))
    for message,claim,body,node,previous in (('ejbz','ejb2','ejbw','zgq','zgp'),('ejb3','ejb4','ejbx','zgr','zgq'),('ejb5','ejb6','ejby','zgs','zgr')):
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejb2','ejb4','ejb6')]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='time_free_spatial_relations_mutual_rest_identity_reciprocity',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/third-frame-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
