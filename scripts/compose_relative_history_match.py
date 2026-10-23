"""Match two material-relative histories without rescaling elapsed time."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_material_relative_frame import ROOT,read,R,F,FAMILY,AXES,ENAMES,define,args
from scripts.compose_limits import v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-material-relative-frame.noema'
PARENT_BASIS='data/material-relative-frame-basis-v1.json'
FULL='examples/v014/einstein-relative-history-match.noema'
CORE='examples/v014/relative-history-match-core.noema'
BASIS='data/relative-history-match-basis-v1.json'
ANNOTATIONS='data/relative-history-match-identifiers-v1.json'
COMMON=[('left','a'),('right','a'),('lengthunit','a'),('timeunit','a'),
    ('leftmembers','h[a] c'),('rightmembers','h[a] c')]+[(n,'a') for n in ('origin','guide','plane')]
CASE=[('frame','a'),('context','d'),('lower',R),('upper',R)]+[(s+a,FAMILY) for s in ('left','right') for a in AXES]+[(n,F) for n in ENAMES]
FIELDS=COMMON+[(c+n,t) for c in ('first','second') for n,t in CASE]+[('offset',R)]
MEANINGS={
 'eiav':'二つの有効な非零幅閉区間の始点と終点が、同じ時間単位で一つの定数offsetだけずれる。負の差や零の差を許すが、時間の逆転・引き伸ばし・切り縮めを許さない。時刻原点の差を保持した経過時間対応である。',
 'eiaw':'同じ物質点の二つの指定時刻における二系列の三相対座標が有効で、対応する全成分が等しい。別の点との交換、距離の等しさ、時刻を無視した軌道集合の一致を代用しない。時刻と物理的な履歴の対応は呼び出し側が結ぶ。',
 'eiax':'同じ二物体・全成員範囲・三標識点・長さと時間単位を使う二場合それぞれのeiarと、eiavの時間対応を結ぶ。場合ごとの評価系・文脈・座標族・軸・区間を保持する。異なる名前の物体への一般的な同型比較ではなく、同じ物体を二場合へ置く読みである。',
 'eiay':'eiaxの二場合で、参照物体の全成員の物体軸における位置がそれぞれの始点で等しい。各場合のeiaqがその配置の全区間不変性を要求するため、標識以外の参照物体の形や寸法の変更を比較へ混入しない。',
 'eiaz':'eiaxの二場合で、相手側の同じ成員について第一時刻とoffsetだけずれた第二時刻の全相対成分を照合する。両時刻が各閉区間に入り、物質点が完全な対象範囲に属することを要求する単一時刻の照合である。',
 'eia2':'参照物体の形も一致するeiayの下で、対象側の全成員・第一閉区間の全実時刻についてeiazを要求する同じ相対配置履歴。定数差で第二区間を尽くし、速度や途中の経過を変える任意の時間再対応を許さない。双方の相対静止も同一履歴として比較でき、これだけで非零の運動を要求しない。',
 'eia3':'eia2の同じ相対履歴に、第一の場合の左側運動・右側静止、第二の場合の左側静止・右側運動を、それぞれ同じ系・文脈・単位・区間・完全な点範囲と座標へ結ぶ。磁石と導体という種類、電流の同一性、著者の帰属はこの補助条件に含めない。',
}
LIMITS=[
 '二場合には同じ二物体・同じ物質点識別・同じ標識点と正方向を用いる。単なる同形の別物体へ比較を広げず、その場合は物質点と物理的性質の明示した対応が別途必要。',
 '同じ長さ単位・時間単位を用い、時刻原点だけの定数差を許す。任意の時間再パラメータ化、時間反転、異なる速度での同形軌道を同じ履歴としない。単位換算を含む一般形は追加しない。',
 '両場合の参照側は非共線な三標識を持つ剛な物体という既存eiaqの読みを引き継ぐ。対象側の形・位置・向き・変形は全物質点の相対座標で比較する。磁化や導電率などの物理的性質は座標一致だけでは一致と認めない。',
 'eia3は二つの想定に与える条件である。二場合が現実に共に発生したこと、全ての相対運動に同じ電流が生じること、一般の基準系間のLorentz同値や物理的な回転効果の不存在を主張しない。',
 '新しい著者主張・原始関係は追加しない。原文の比較範囲・マクロ尺度・剛性の読み、磁石・導体・電磁相互作用・電流・起電力、通常の理解への帰属と全文の意味判断は未完。',
]


def pair(case):
    return [v('left'),v('right'),v(case+'frame'),v(case+'context'),v('lengthunit'),v('timeunit'),
        v(case+'lower'),v(case+'upper'),v('leftmembers'),v('rightmembers'),
        *(v(case+s+a) for s in ('left','right') for a in AXES),
        *(v(n) for n in ('origin','guide','plane')),*(v(case+n) for n in ENAMES)]


def history(case,side):
    return [v(side),v(case+'frame'),v(case+'context'),v('lengthunit'),v('timeunit'),
        v(case+'lower'),v(case+'upper'),v(side+'members'),*(v(case+side+a) for a in AXES)]


def relative(case,side):
    values=[v('origin'),*(v(case+s+a) for s in ('left',side) for a in AXES),*(v(case+n) for n in ENAMES)]
    return [k(n,*values) for n in ('eian','eiao','eiap')]


def definitions():
    interval=[(n,R) for n in ('firstlower','firstupper','secondlower','secondupper','offset')]
    text=define('eiav',interval,both(*(k('ba',v(n)) for n,_ in interval),
        k('bg',v('firstlower'),v('firstupper')),k('bg',v('secondlower'),v('secondupper')),
        k('sca',v('secondlower'),k('bd',v('firstlower'),v('offset'))),
        k('sca',v('secondupper'),k('bd',v('firstupper'),v('offset')))))
    point_fields=[('point','a'),('firsttime',R),('secondtime',R)]+[(c+a,FAMILY) for c in ('first','second') for a in AXES]
    values=[[app(app(v(c+a),v('point')),v(c+'time')) for a in AXES] for c in ('first','second')]
    text+=define('eiaw',point_fields,both(k('ba',v('firsttime')),k('ba',v('secondtime')),
        *(k('ba',x) for row in values for x in row),*(k('sca',x,y) for x,y in zip(*values))))
    text+=define('eiax',FIELDS,both(k('eiav',*args(interval)),k('eiar',*pair('first')),k('eiar',*pair('second'))))
    text+=define('eiay',FIELDS,both(k('eiax',*args(FIELDS)),q('f','point','a',
        op('y',app(v('leftmembers'),v('point')),k('eiaw',v('point'),v('firstlower'),v('secondlower'),
            *relative('first','left'),*relative('second','left'))))))
    shifted=k('bd',v('time'),v('offset'))
    text+=define('eiaz',FIELDS+[('point','a'),('time',R)],both(k('eiax',*args(FIELDS)),
        app(v('rightmembers'),v('point')),k('lg',v('firstlower'),v('firstupper'),v('time')),
        k('lg',v('secondlower'),v('secondupper'),shifted),
        k('eiaw',v('point'),v('time'),shifted,*relative('first','right'),*relative('second','right'))))
    text+=define('eia2',FIELDS,both(k('eiay',*args(FIELDS)),q('f','point','a',q('f','time',R,
        op('y',both(app(v('rightmembers'),v('point')),k('lg',v('firstlower'),v('firstupper'),v('time'))),
            k('eiaz',*args(FIELDS),v('point'),v('time')))))))
    text+=define('eia3',FIELDS,both(k('eia2',*args(FIELDS)),
        k('eiag',*history('first','left')),k('eiah',*history('first','right')),
        k('eiah',*history('second','left')),k('eiag',*history('second','right'))))
    return text


def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_material_relative_history_with_elapsed_time_preserved',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/material-relative-frame-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Same relative histories and opposite moving/resting cases composed')
