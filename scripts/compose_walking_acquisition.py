"""Compose bodily acquisition and its prospect from existing capacity and learning."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure

PARENT='examples/v016/kant-modal-prevention.noema'
PARENT_BASIS='data/modal-prevention-basis-v1.json'
FULL='examples/v016/kant-walking-acquisition.noema'
CORE='examples/v016/walking-acquisition-core.noema'
BASIS='data/walking-acquisition-basis-v1.json'
ANNOTATIONS='data/walking-acquisition-identifiers-v1.json'
PRIMITIVES={
 'hzyf':(['subject','task','anchor','candidate'],'指定した活動記述について、その主体の基準状態で能力を評価するための機会候補。候補は実際の履歴の断言ではない。同じ主体・活動・基準を保つ。'),
 'hzyg':(['subject','task','anchor','candidate'],'指定活動の能力基盤として採る主体側の状態が、同じ基準から候補へ保持される。身体や技能の状態を含み得るが、能力の結論自体の同一性を前提とせず、学習後の基盤で学習前を評価しない。'),
 'hzyh':(['subject','task','candidate'],'その主体が指定活動を試みる外的機会が候補にある。技能、実行成功、許容の成立を代用しない。'),
 'hzyi':(['subject','task','anchor','preferred','other'],'同じ主体・活動・基準の能力評価で、機会候補の通常性を比較する厳密な優先関係。結果の成功を見て通常性を選び直したことを正当化しない。'),
 'hzyj':(['subject','task','method','anchor','candidate'],'同じ主体の基準時点の活動基盤を行使する方法として評価範囲に入る。別の技能を先に習得する方法を、まだない技能の行使能力へ流用しない。'),
 'hzyk':(['subject','task','method','anchor','candidate'],'同じ主体・活動・方法・基準・候補についてhzyjの範囲判定ができる。既知の範囲外と未分類を区別する。'),
}
MEANINGS={
 'r2at':'同じ身体主体の補助なしの足移動zalについて、活動記述に結び付いた機会・保持基盤・通常性・方法範囲を用い、既存rqvmの能力評価条件が整う。未評価を不能とは扱わない。',
 'r2au':'同じ身体主体の補助なしの足移動zalについて、r2atと同じ評価プロフィールの通常機会全体で、基準時点の技能を行使して達成する方法がある。現在の移動実行や将来の訓練可能性とは分ける。',
 'r2av':'同じ本人・経験・経験時点について、既存hzumの身体的な転倒経験をr5へ渡す。別人や別の経験の転倒を流用しない。',
 'r2aw':'同じ本人の同じ過程で、文脈上少数回の転倒経験列が順序を保ち、各経験がその人の補助なしの足移動能力の取得へ寄与する。評価済みの前状態で能力がなく、後状態であることを既存r5で結ぶ。単なる反復や時の経過は取得ではない。',
 'r2ax':'指定した本人と回数基準文脈について、r2awを満たす過程が終わる状況の内容。候補ごとの過程の存在を要求するが、各候補が同じ実際の出来事とはしない。',
 'r2ay':'同じ本人について、既存frと対応する非空の将来候補の全てでr2axが成立するという見込み。回数基準は見込みの基準文脈を保ち、現在や現実に取得が起きたとは断言しない。',
 'r2az':'学習の理由節fvで、同じ本人の知的活動の能力取得見込みfrを、転倒を通じた補助なしの足移動能力の取得見込みr2ayとして非字義的に提示する。両記述の真偽一致や実現を主張しない。',
}
LIMITS=[
 '能力・経験による取得・将来の見込み・非字義的な提示を既存の構成で結ぶ。新しい六関係は活動を明示した能力評価の文脈入力であり、歩く・学ぶという一語を不透明な関係へ置き換えるものではない。',
 'r2atとr2auは同じzalの内容と記述、同じ評価プロフィールを使う。活動記述を動的に実行する構文は追加しない。',
 '外部支持のない足による位置の変更という既採用の読みを継ぐ。特定の歩容、傷害、訓練機構、遺伝的な能力理論は追加しない。',
 '非空で順序付きの少数回の経験列から、評価済みの能力欠如から保有への取得を読む。熟達度の連続的改善、同時の経験、経験の全列挙とは分ける。',
 '経験列・過程・時点・見込み候補の索引は既存のfh・fi・f7・flを用いて対応させる。知的側と身体側の成立・実現・因果的同一性は追加しない。',
 'würden・wohl・endlichの語用論、危険の程度、萎縮と通常の回避を含む末尾一文の意味確認は残る。今回の追加だけで最後の一文や段落全体を完成扱いにしない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def additions():
    text='''r hzyf[a i[h[a] e] d d] c.r hzyg[a i[h[a] e] d d] c.
r hzyh[a i[h[a] e] d] c.r hzyi[a i[h[a] e] d d d] c.
r hzyj[a i[h[a] e] a d d] c.r hzyk[a i[h[a] e] a d d] c.
'''
    profile='''v person k zal[v person] v anchor
 i[subject a ref d scene d][k hzyf[v subject r[p zal] v ref v scene]]
 i[subject a ref d scene d][k hzyg[v subject r[p zal] v ref v scene]]
 i[subject a scene d][k hzyh[v subject r[p zal] v scene]]
 i[subject a ref d first d second d][k hzyi[v subject r[p zal] v ref v first v second]]
 i[subject a method a ref d scene d][k hzyj[v subject r[p zal] v method v ref v scene]]
 i[subject a method a ref d scene d][k hzyk[v subject r[p zal] v method v ref v scene]]
 p ae p af p ap'''
    for name,operation in (('r2at','rqvm'),('r2au','rqvn')):
        text+='d '+name+'[person a] e[b anchor[k '+operation+'['+profile+']]].'
    text+='''
d r2av[person a experience a point d] c[t[k hzum[v person v experience]][v point]].
d r2aw[person a process a end d context d] c[w[k fm[d[k fh[v process]] v context]][
 k r5[v person v process k fh[v process] p f7 p dd k fi[v process] v end
 i[subject a point d][t[k r2at[v subject]][v point]]
 i[subject a point d][t[k r2au[v subject]][v point]] p ag p la p r2av p fk]
]].
d r2ax[person a context d] e[b end[g process a[k r2aw[v person v process v end v context]]]].
d r2ay[person a] e[b context[k ri[k r2ax[v person v context] v context i[end d][k fl[v person v context v end]] p tx]]].
d r2az[] c[k qh[k fv[] k wa[] r[p fr] r[p r2ay] k wh[]]].
'''
    return text


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+additions()+'s[k r2az[]].')
    doc['statements']=statements+doc['statements'];doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core['statements']=doc['statements'][-1:]
    core['declarations']=closure(doc,_references(core['statements']))
    added=doc['declarations'][size:];by_name={d['name']:d for d in added};assert len(added)==13
    basis=dict(status='bodily_acquisition_and_prospect_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=args,meaning_ja=meaning) for n,(args,meaning) in PRIMITIVES.items()},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/modal-prevention-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda value:json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print('Bodily learning prospect composed: seven definitions, six task-indexed assessment relations; 51 statements',flush=True)


if __name__=='__main__':main()
