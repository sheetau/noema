"""Bind current histories to the complete material-section scope."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_charge_transport_current import ROOT,read,ELECTRIC,MATCH as SINGLE,MOTION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-charge-transport-current.noema'
PARENT_BASIS='data/charge-transport-current-basis-v1.json'
FULL='examples/v014/einstein-current-distribution.noema'
CORE='examples/v014/current-distribution-core.noema'
BASIS='data/current-distribution-basis-v1.json'
ANNOTATIONS='data/current-distribution-identifiers-v1.json'
SCOPE='h[a a] c';FAMILY='h[a a] '+F
SCOPE_FIELDS=[('body','a'),('context','d'),('sections',SCOPE)]
HISTORY=[('body','a'),('frame','a'),('context','d'),('timeunit','a'),('quantityunit','a'),
    ('lower',R),('upper',R),('sections',SCOPE),('cumulative',FAMILY),('current',FAMILY)]
PAIR=[('body','a'),('timeunit','a'),('quantityunit','a'),('sections',SCOPE)]+[
    (c+n,t) for c in ('first','second') for n,t in [('frame','a'),('context','d'),('lower',R),('upper',R),('cumulative',FAMILY),('current',FAMILY)]]+[('offset',R)]
EXTRA=[('quantityunit','a'),('sections',SCOPE)]+[(c+n,FAMILY) for c in ('first','second') for n in ('cumulative','current')]
MEANINGS={
 'eibe':'指定物体・文脈の全適用可能な物体付き有向断面eirjと、sectionsの断面・向きの組を双方向に一致させ、空でないことを要求する。結果の一致した断面だけを残した範囲や、向きを落とした断面名一覧を完全範囲としない。',
 'eibf':'eibeの全ての断面・向きについて、同じ物体・系・文脈・単位・時間区間のeibaを要求する。累積量と電流の関数族から同じ断面・向きの関数を選ぶ。断面ごとの値は異なってよく、一断面の値を全体に代用しない。',
 'eibg':'同じ物体・単位・断面と向きの全範囲を使う二場合のeibfと、eiavの経過時間対応を結ぶ。各場合の物理的な全断面範囲が共有範囲に一致することも要求する。二場合の電流値の一致はまだ含まない。',
 'eibh':'eibgの下で対象範囲に属する同じ一断面・向きと二場合の電流関数を選び、第一時刻と対応第二時刻のeibbを検査する。一時刻の照合で全履歴一致を代用しない。',
 'eibi':'eibgの全断面・向きそれぞれに既存eibcの完全な二場合の電流履歴一致を要求する。端子の一箇所、全体の和、同じ形の別断面、逆向きの対応では代用しない。定義された全範囲内の分布比較であり、電流密度場や微分方程式の同値定理ではない。',
 'eibj':'相対運動と運動/静止の二役割eia3へ、同じ右側物体・両系・両文脈・単位・両区間について全断面の電流分布一致eibiを同時に結ぶ。運動から電流一致を導く法則や磁石と導体の種類の判定を加えない。',
}
PRIMITIVE_MEANING='指定物体を同じ物質部分として追跡する記述において、その物体に付随するsectionと、その断面に固定された正方向orientationの組が、当該マクロ尺度・幾何学的適用範囲の全有向断面に属するという物理的入力。sectionの同一性は同じ物質部分に付随する断面の同一性であり、座標位置が同じ別断面ではない。orientationの同一性は同じ物質的側を正とする向きで、系や場合を替えたことによる符号反転を含まない。記述尺度と適用範囲は電流の結果を見る前に固定し、全適用可能な断面を含むものとして与える。観測点だけの有限一覧や一致した場所だけの選択から完全性を推定しない。零面積など通過の断面として不適格なものの除外理由は物理的な範囲規約に属する。この関係自体は電流の存在・導電性・磁石であることを意味しない。'
LIMITS=[
 'eirjは完全な物理的断面範囲の入力であり、Noema処理系が有限例から空間全体の断面族を復元するものではない。原文の適用時には尺度・範囲の採用理由を明示する。今回の構成は与えられた範囲の抜け・余計な組・場合間の不一致を検査する。',
 '同じ断面・向きの識別を二場合で保存する。別物体への一般的な断面同型、向き反転を伴う単位換算、任意の時間再対応は含めない。',
 '全断面の通過率という分布記述であり、局所的な電流密度ベクトル場の構成・積分との同値・電荷保存の導出を主張しない。各断面で既存のマクロ微分可能な履歴の読みを引き継ぐ。',
 '磁石・導体の性質、電気量の作用との基礎接続、実際のマクロ尺度と断面範囲、二場合で保つ物理的性質、電場・起電力・エネルギー、著者の説明への帰属と全文接続は未完。新たな著者主張を追加せず207主張と既存判断を保持する。',
]

def selected(name):return app(v(name),v('section'),v('orientation'))
def every(body):return q('f','section','a',q('f','orientation','a',op('y',app(v('sections'),v('section'),v('orientation')),body)))
def history(case):return [v(case+n) if n in ('frame','context','lower','upper','cumulative','current') else v(n) for n,_ in HISTORY]

def definitions():
    scope=app(v('sections'),v('section'),v('orientation'))
    text='r eirj[a a a d] c.\n'
    text+=define('eibe',SCOPE_FIELDS,both(k('zm',v('body')),q('g','section','a',q('g','orientation','a',scope)),
        q('f','section','a',q('f','orientation','a',op('z',scope,k('eirj',v('body'),v('section'),v('orientation'),v('context')))))))
    single=[selected(n) if n=='cumulative' else v(n) for n,_ in ELECTRIC]+[selected('current')]
    text+=define('eibf',HISTORY,both(k('eibe',*args(SCOPE_FIELDS)),every(k('eiba',*single))))
    clock=[v(n) for n in ('firstlower','firstupper','secondlower','secondupper','offset')]
    text+=define('eibg',PAIR,both(k('eiav',*clock),k('eibf',*history('first')),k('eibf',*history('second'))))
    text+=define('eibh',PAIR+[('section','a'),('orientation','a'),('time',R)],both(k('eibg',*args(PAIR)),scope,
        k('eibb',*clock,selected('firstcurrent'),selected('secondcurrent'),v('time'))))
    comparison=[selected(n) if n in ('firstcumulative','firstcurrent','secondcumulative','secondcurrent') else v(n) for n,_ in SINGLE]
    text+=define('eibi',PAIR,both(k('eibg',*args(PAIR)),every(k('eibc',*comparison))))
    text+=define('eibj',MOTION+EXTRA,both(k('eia3',*args(MOTION)),k('eibi',*[v('right') if n=='body' else v(n) for n,_ in PAIR])))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|{'eirj'})&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):];p=added[0]
    basis=dict(status='complete_material_section_current_distribution_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'eirj':dict(parameters=p['parameters'],result=p['result'],arguments=['body','section','orientation','context'],meaning_ja=PRIMITIVE_MEANING)},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/charge-transport-current-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Full section scope and current distribution composed')
