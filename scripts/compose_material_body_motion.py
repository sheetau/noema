"""Compose interval motion from complete material-point worldlines."""
from copy import deepcopy
import json
from scripts.compose_einstein_author_credit import ROOT, read
from scripts.compose_limits import R, F, v, call as k, app, op, both, quant as q, definition
from noema.grammar import parse, format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest

PARENT='examples/v014/einstein-author-credit.noema'
PARENT_BASIS='data/einstein-author-credit-basis-v1.json'
FULL='examples/v014/einstein-material-body-motion.noema'
CORE='examples/v014/material-body-motion-core.noema'
BASIS='data/material-body-motion-basis-v1.json'
ANNOTATIONS='data/material-body-motion-identifiers-v1.json'
FAMILY='h[a] '+F
FIELDS=[('body','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a'),
    ('lower',R),('upper',R),('members','h[a] c')]+[(axis,FAMILY) for axis in ('x','y','z')]
PARAMS=' '.join(n+' '+t for n,t in FIELDS)
ARGS=[v(n) for n,_ in FIELDS]
MEANINGS={
 'eiac':'同じ物体・文脈の全物質点とmembersの範囲を双方向に一致させ、空でないことを要求する。物体は既存zmの形状を持つ対象であり、標本だけの部分集合を全物体としない。',
 'eiad':'同じ物体の非空の全物質点それぞれについて、同じ基準系・文脈・長さと時間単位・始終時刻に既存seの全区間軌跡を要求する。三座標関数は同じ物質点を引数に選び、同じ点の全出来事へ結ぶ。長さ単位と時間単位は別個体。剛性、等速、並進、連続性をこの合成だけで加えない。',
 'eiae':'同じ物質点の二時刻の三座標を取り出し、時刻と六座標が有効な実切断であり、少なくとも一成分に厳密な大小差がある。時間順序や実際の物理的履歴は別条件。物体の占有集合、中心座標、別の点への交換によって同一性を代用しない。',
 'eiaf':'eiadの全物質点履歴の下で、同じmembersの一点と同じ閉区間内の厳密に前後する二時刻を指定し、その同じ点にeiaeの位置差を要求する運動の証人。区間外、逆順、同時刻、別の物体の点を証人にしない。',
 'eiag':'全物質点・全区間履歴eiadが成立し、eiafを満たす物質点と二時刻が存在するという区間内の運動。途中で動いて元の位置に戻る場合も含む。瞬間速度や剛体の並進速度の定義ではない。',
 'eiah':'全物質点・全区間履歴eiadの下で、全成員の区間内の任意の二時刻間にeiaeの位置差がない。情報欠落や無効な履歴のため運動を認められないことから静止を推論しない。同じ基準系に対する区間全体の静止であり絶対静止ではない。',
 'eiai':'同じ物体の物質点とその出来事について、既存sbを通じて世界線所属zzbvと単位付き座標zzbuを結ぶ。時刻と三座標は同じ点の三関数から取り出す。単一の観測接続であり、これだけで全区間の履歴や運動を認定しない。',
}
LIMITS=[
 '物体は指定文脈で同一物質点を追跡する連続体として読む。eirhはその完全な物質点対応の物理的入力であり、有限標本からその完全性・物質性を推測しない。物質点は原子や幾何学的な空間位置と同一ではない。',
 'この層は固定された物体の構成を追跡する区間を扱う。物質の出入りで構成が変わる物体や生成消滅は、可変構成の別の記述が必要。剛体・点状物体・単純並進だけに狭めない。',
 '運動と静止は指定基準系に対する区間の性質で、微視的熱運動を常に含めるとはせず、原文への接続時に採用する物理的記述尺度と全物質点の範囲を明示する。瞬間速度、二物体間の相対運動、同じ相対運動の比較は後続課題。',
 'seは同じ物質点の全時刻での出来事存在と全座標対応を要求する。実数・関数全域の量化を有限サンプルへ置き換えない。有限検査は明示した有理数埋込みと引数接続、単一出来事のsb本体、全域評価の拒否を対象とする。',
 '既存207主張と著者表示の判断を保持する補助定義で、表題・導入の語句を新しく意味確認済みにしない。物体・物質点・座標割当の物理的充足と原文への接続は別の判断。',
]


def coord(axis,point,time):
    return app(app(v(axis),point),time)


def definitions():
    member=lambda p:app(v('members'),p)
    text='r eirh[a a d] c.\n'
    text+=definition('eiac','body a context d members h[a] c',both(
        k('zm',v('body')),q('g','point','a',member(v('point'))),
        q('f','point','a',op('z',member(v('point')),k('eirh',v('body'),v('point'),v('context'))))))
    trajectory=k('se',v('point'),*[v(n) for n in ('frame','context','lengthunit','timeunit','lower','upper')],
        *(app(v(axis),v('point')) for axis in ('x','y','z')))
    text+=definition('eiad',PARAMS,both(k('eiac',v('body'),v('context'),v('members')),
        op('u',op('e',v('lengthunit'),v('timeunit'))),
        q('f','point','a',op('y',member(v('point')),trajectory))))
    point=v('point');first=v('first');second=v('second')
    pairs=[(coord(a,point,first),coord(a,point,second)) for a in ('x','y','z')]
    different=[op('x',k('zzbg',a,b),k('zzbg',b,a)) for a,b in pairs]
    point_fields='point a first '+R+' second '+R+' '+' '.join(a+' '+FAMILY for a in ('x','y','z'))
    text+=definition('eiae',point_fields,both(k('zzba',first),k('zzba',second),
        *(k('zzba',p) for pair in pairs for p in pair),op('x',different[0],op('x',*different[1:]))))
    difference=k('eiae',point,first,second,*(v(a) for a in ('x','y','z')))
    inside=both(k('lg',v('lower'),v('upper'),first),k('lg',v('lower'),v('upper'),second))
    witness_fields=PARAMS+' point a first '+R+' second '+R
    text+=definition('eiaf',witness_fields,both(k('eiad',*ARGS),member(point),inside,k('zzbg',first,second),difference))
    text+=definition('eiag',PARAMS,both(k('eiad',*ARGS),q('g','point','a',q('g','first',R,q('g','second',R,
        k('eiaf',*ARGS,point,first,second))))))
    text+=definition('eiah',PARAMS,both(k('eiad',*ARGS),q('f','point','a',q('f','first',R,q('f','second',R,
        op('y',both(member(point),inside),op('u',difference)))))))
    observation_fields='body a point a event a frame a context d lengthunit a timeunit a time '+R+' '+' '.join(a+' '+FAMILY for a in ('x','y','z'))
    text+=definition('eiai',observation_fields,both(k('zm',v('body')),k('eirh',v('body'),point,v('context')),
        k('sb',point,v('event'),*[v(n) for n in ('frame','context','lengthunit','timeunit','time')],
          *(coord(a,point,v('time')) for a in ('x','y','z')))))
    return text


def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|{'eirh'})&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):];d=added[0]
    basis=dict(status='material_point_interval_motion_dependency',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,definitions=MEANINGS,
        primitives={'eirh':dict(parameters=d['parameters'],result=d['result'],arguments=['body','point','context'],
            meaning_ja='指定文脈で固定された物体を構成し、同じ物体の履歴を通じて追跡する物質点である。全物質点への関係として与え、測定済み標本だけの一覧ではない。時刻ごとに場所が一致する別の点への付け替えや、同じ空間位置という意味ではない。')},
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/einstein-author-credit-identifiers-v1.json'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    encoded=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:encoded(basis),ANNOTATIONS:encoded(ann)}


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Material-point interval motion composed; 207 assertions unchanged')
