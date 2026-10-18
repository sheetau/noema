"""Bind missing permission for undertaking to the same earlier obstruction."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_confinement_depiction import ROOT,closure

PARENT='examples/v016/kant-confinement-depiction.noema'
PARENT_BASIS='data/confinement-depiction-basis-v1.json'
FULL='examples/v016/kant-unpermitted-undertaking.noema'
CORE='examples/v016/unpermitted-undertaking-core.noema'
BASIS='data/unpermitted-undertaking-basis-v1.json'
ANNOTATIONS='data/unpermitted-undertaking-identifiers-v1.json'
MEANINGS={
 'hzta':'閉じた目標記述を固定し、一個体だけの引数列から本人を取って、同じ本人による勇気を伴う取り組みhzs4を返す関数。目標記述は引用の内側でも保持し、別人や余分な引数を混ぜない。',
 'hztb':'hztaへ渡す引数列が一個体だけであるという長さ規約。規範を否定する前にも確認する。',
 'hztc':'同じ出所・本人・立場・目標記述・状況について、勇気を伴う取り組みhztaへの積極的な許容がないというrjpの内容。取り組みを実行評価せず、反対要求、身体的不能、現在の勇気不足や不実行をこの条件だけから導かない。',
 'hzte':'先行する二段階hzsoと同じ対象者・同じ第二時点について、同じ後見人群を出所とするhztcの許容欠如を結ぶ。許容欠如が阻止の唯一の原因だとは主張しない。',
 'hztf':'危険提示ewと、対象者を提示時点で固定したhzteの先行段階を結ぶ。二つの先行段階相互の厳密な順序は増やさない。',
 'hztg':'複文hzsqの部分記述hztfを著者へ帰属させ、先行する監督の文dqより後に結ぶ。帰属から引用内容を実行評価しない。',
 'hzth':'提示時点でqjの監督対象となる同じ本人について、先行する同じ時点で後見人群による非試行の因果hzsnと、勇気を伴う取り組みの許容欠如hztcがあるという比喩の対象側。',
 'hzti':'関係節hzstで、更新した対象側hzthを既存の閉じ込め描写zbfへ対応させる非字義的な提示。対象と描写を現実の同値な内容と認定しない。',
}


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|{'hztd'})&set(old.entries)
    doc=parse(format_graph(doc,'compact')+'''
d hztb[bindings j[a]] c[k rdr[v bindings n p b b]].
d hzta[goal i[h[a] e]] h[j[a]] e[i[bindings j[a]][b scene[w[k hztb[v bindings]][g person a[w[a[v bindings][n p a b][v person]][t[k hzs4[v person v goal]][v scene]]]]]]].
d hztc[source a person a role a goal i[h[a] e]] e[b scene[
 k rjp[v source v person v role o a[r[p hzta]][o r[v goal]] l[a][v person] e[n p a b][n p a b] v scene p hztb p h7k p h7l]
]].
r hztd[] a.
d hzte[group a anchor d first d second d] c[w[k hzso[v group v anchor v first v second]][
 f person a[y[k dj[v person v anchor]][t[k hztc[v group v person k hztd[] r[p bb]]][v second]]]
]].
d hztf[group a] e[b anchor[w[t[k ew[v group]][v anchor]][g first d[g second d[k hzte[v group v anchor v first v second]]]]]].
d hztg[] c[w[k uc[k hzsq[] k wa[] r[k hztf[k db[]]] k wh[]]][k ue[k dq[] k hzsq[] k wh[]]]].
d hzth[person a] e[b anchor[w[t[k qj[v person]][v anchor]][g prior d[w[k dd[v prior v anchor]][w[t[k hzsn[k db[] v person]][v prior]][t[k hztc[k db[] v person k hztd[] r[p bb]]][v prior]]]]]]].
d hzti[] c[k qh[k hzst[] k wa[] r[p hzth] r[p zbf] k wh[]]].
''')
    doc['statements']=deepcopy(statements)
    assert len(statements)==37
    doc['statements'][35:]=parse(format_graph(doc,'compact')+'s[k hztg[]].s[k hzti[]].')['statements'][-2:]
    doc=parse(format_graph(doc,'compact'));core=deepcopy(doc);core['declarations']=closure(doc,['hztg','hzti']);core['statements']=doc['statements'][35:]
    added=doc['declarations'][size:];reference=next(d for d in added if d['name']=='hztd')
    basis=dict(status='explicit_missing_permission_reading_of_undertaking',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'hztd':dict(parameters=reference['parameters'],result=reference['result'],arguments=[],meaning_ja='この段落で、後見人群の監督下に置かれた人として許容を受ける立場。同じ許容の対象に用いる局所参照であり、制度上の正当な資格や法的権利を認定しない。')},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        limitations=['wagen durftenの対象側を、勇気を伴う取り組みへの許容がないものとして読む。身体的な一歩の描写やjaの強調は別に残る。',
            '許容の欠如は明示的な禁止命令や、反対要求と衝突する許容とは別である。現代語の文法資料は区別の参考であり、歴史的原文の唯一の読解を証明しない。',
            '許容の出所を同じ後見人群へ固定する読み。法令、制裁、正当な権威、特定の制度を補わず、実行機会の全理論を代用しない。',
            '勇気を伴う取り組みを規範の対象として引用する。取り組みへの許容がないことから、本人の勇気がないことや現実の試みの成否は導かない。',
            '本文35・36番の二文を更新し、他の35文と既存九単位の意味判断を保持する。旧候補は定義として保存する。',
            '身体的な歩行・転倒、慎重さ・穏順さ、皮肉、学習と萎縮の接続、第二段落全体の意味確認は残る。'])
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/confinement-depiction-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Undertaking permission tied to the same earlier obstruction',flush=True)


if __name__=='__main__':main()
