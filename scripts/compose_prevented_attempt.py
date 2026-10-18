"""Connect factual caused nonattempt and later warning without requiring an SCM."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-contextual-motto.noema'
PARENT_BASIS='data/contextual-motto-basis-v1.json'
FULL='examples/v016/kant-prevented-attempt.noema'
CORE='examples/v016/prevented-attempt-core.noema'
BASIS='data/prevented-attempt-basis-v1.json'
ANNOTATIONS='data/prevented-attempt-identifiers-v1.json'
MEANINGS={
 'hzsm':'同じ本人が同じ状況で自立的理解力使用bbを試みていないという内容。eiの既知の否定であり、試みの評価不足を否定へ補わない。実行不能や規範上の禁止とは別である。',
 'hzsn':'同じ後見人群の非空の人々が参加する生起した行為が、同じ本人についてhzsmの非試行を結果として生じさせる。raaで実際の結果・行為・行為者・因果関係を結ぶ。単なる不実行や制約の適用だけでは成立しない。特定の因果方程式モデルを前提にしない。',
 'hzso':'提示時点で固定した非空の対象者群全員について、同じ後見人群によるg4の働きかけとhzsnの試みの阻止が、それぞれ提示より前に成立する。二つの先行状況の相互順序は追加しない。',
 'hzsp':'同じ後見人群の危険提示ewと、同じ対象者に対するhzsoの先行する二つの働きかけを結ぶ。提示した条件内容の真偽や実際の危険を、提示の成立から導かない。対象側の部分記述であり、身体的比喩や許可の全意味は別に残る。',
 'hzsr':'第二段落の働きかけと後続の危険提示の箇所hzsqで、著者がhzspの部分解釈を提示する。その箇所を先行する監督の文dqより後に結ぶ。著者への帰属から内容の真理を認定しない。',
}


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|{'hzsq'})&set(old.entries)
    doc=parse(format_graph(doc,'compact')+'''
d hzsm[person a] e[b scene[u[t[k ej[v person]][v scene]]]].
d hzsn[group a person a] e[b scene[w[k aa[v person]][w[k hi[k mp[v group] p aa]][
 k raa[i[agent a][k hg[k mp[v group] v agent]] v person k hzsm[v person] r[p hzsm] v scene p dg p df p g3]
]]]].
d hzso[group a anchor d first d second d] c[
 w[k dd[v first v anchor]][w[k dd[v second v anchor]][w[g person a[k dj[v person v anchor]]][
  f person a[y[k dj[v person v anchor]][w[k g4[v group v person v first]][t[k hzsn[v group v person]][v second]]]]
 ]]]
].
d hzsp[group a] e[b anchor[w[t[k ew[v group]][v anchor]][g first d[g second d[k hzso[v group v anchor v first v second]]]]]].
r hzsq[] a.
d hzsr[] c[w[k uc[k hzsq[] k wa[] r[k hzsp[k db[]]] k wh[]]][k ue[k dq[] k hzsq[] k wh[]]]].
''')
    doc['statements']=statements+parse(format_graph(doc,'compact')+'s[k hzsr[]].')['statements']
    doc=parse(format_graph(doc,'compact'));core=deepcopy(doc);core['declarations']=closure(doc,['hzsr']);core['statements']=[doc['statements'][-1]]
    added=doc['declarations'][size:];ref=next(d for d in added if d['name']=='hzsq')
    basis=dict(status='factual_prevention_and_prior_warning_partial_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzsq':dict(parameters=ref['parameters'],result=ref['result'],arguments=[],meaning_ja='第二段落の、先行する働きかけとその後の危険提示を述べる複文の箇所。文全体の完成を表す印ではない。')},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        limitations=['妨害の対象側を、他者の行為が試みの不成立を生じさせることとして記述する。許可・機会・勇気の全意味を非試行だけに還元しない。',
            '因果関係g3は既存の意味規約を使う。単なる共存を因果と推論せず、特定の反事実モデルや物理機構を原文へ補わない。',
            'zuerstとnachherを、先行する二つの働きかけから後続の提示への対比として読む。二つの働きかけの厳密な相互順序を必須にする旧g5とは別の明示的な読み。',
            'g4の理解の不足の評価、身体的な家畜・歩行器・歩行の描写、慎重さ、穏順さ、許可、強調は未完であり、第二段落の全体確認とはしない。',
            '旧erとg6は比較用のモデル相対的構成として保存する。既存35文と九単位の意味判断は変更しない。'])
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/contextual-motto-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Caused nonattempt and preceding stages connected to the later presentation',flush=True)


if __name__=='__main__':main()
