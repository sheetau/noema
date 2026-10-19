"""Represent unspecified goal roles by existential slots, not placeholder objects."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_grounded_step import ROOT,closure,both

PARENT='examples/v016/kant-bound-undertaking.noema'
PARENT_BASIS='data/bound-undertaking-basis-v1.json'
FULL='examples/v016/kant-quantified-step-goals.noema'
CORE='examples/v016/quantified-step-goals-core.noema'
LIBRARY='examples/v016/existential-pair-slots.noema'
BASIS='data/quantified-step-goals-basis-v1.json'
MEANINGS={
 'rqzm':'二つの対象位置を、空列なら存在量化、一個体の列ならその個体への固定として指定する。両位置を満たす同じ二個体に、与えた内容関数を適用する。二個以上の列は不適合とし、未知個体を表す代用記号を作らない。片方ずつ別の組の証拠を集めて成立させない。',
 'rqzn':'身体と装置だけを指定し、足と移動過程を存在量化したrqzgの一歩の目標。どの足か、どの過程かを指定済みの目標とは引用内容を区別する。実際の目標評価では、同じ二対象の組がrqzgを満たすことを要求する。',
 'rqzo':'身体・装置・足を指定し、移動過程だけを存在量化した一歩の目標。指定した足を別の足の成功で代用しない。',
 'rqzp':'身体・装置・移動過程を指定し、足だけを存在量化した一歩の目標。指定した過程を別の過程の成功で代用しない。',
 'rqzq':'指定個数の対象列の第一位置にいる本人が、その同じ列に適用される閉じた目標を勇気を伴って試みる内容。列の長さと本人を保持し、引用した目標の存在量化や達成を実行しない。',
 'rqzr':'rqznの足・過程が未指定の一歩を、同じ身体・装置の二対象を保って勇気を伴って試みる。試みの成立から、本人が特定の足・過程を目標として名指したことを導かない。',
 'rqzs':'rqzoの足だけを指定した一歩を、同じ身体・装置・足を保って勇気を伴って試みる。目標の移動過程を予め指定することや、実際の成功は要求しない。',
 'rqzt':'rqzpの過程だけを指定した一歩を、同じ身体・装置・過程を保って勇気を伴って試みる。目標の足を予め指定することや、実際の成功は要求しない。',
 'rqzu':'同じ身体・装置について、両位置未指定の試み、選択した各足だけを指定した試み、各過程だけを指定した試み、両方を指定した全組の試みの四形への積極的許容が全てない。足と過程の範囲は明示的に受け、実際の試み・成功を範囲の条件にしない。選択範囲が原文の全該当対象を尽くすかは別の確認事項。',
}
LIMITS=[
 '目標の二位置における存在量化を追加する。足・過程の両方を指定した旧rqzg/rqzkも保持し、四つの指定形を区別する。全ての可能な目標記述や同義表現を列挙したとはしない。',
 '未指定の目標への勇気・試み・許容から、特定の対象を指定した目標への同じ態度や許容を推論しない。存在量化の作用範囲は、引用された目標の内側に置く。',
 '目標を実際に評価する場合の存在証拠と、その目標を試みまたは許容の対象として引用することを区別する。引用時に存在証拠や目標の成功を要求しない。',
 '許容の全候補範囲には未指定の形も必要となる。具体的な四引数候補だけの無許容が真でも、未指定の目標への取り組みが許容されている解釈を構成できる。',
 '原文への候補範囲、先行時点の阻止、比喩への結合は引き続き必要。比較構成として保存し、採用中の47文と十一単位の意味判断を変更しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def bind_goal(name,parameters,body):
    count=len(parameters);names=['slot'+chr(97+i) for i in range(count)]
    target='i['+' '.join(p+' a' for p in parameters)+']['+body+']'
    consume='i[acc h['+' '.join('a' for _ in parameters)+'] e item a][i['+' '.join(n+' a' for n in names)+']['+\
        'c[v acc][v item '+' '.join('v '+n for n in names[:-1])+']]]'
    fold='g seed a[t[c[q[v bindings]['+target+']['+consume+']]['+' '.join('v seed' for _ in parameters)+']][v scene]]'
    return 'd '+name+'[bindings j[a]] e[b scene[w[k rdr[v bindings n p '+chr(97+count)+' b]]['+fold+']]].\n'


def additions():
    shape=lambda name:'x[k rdr[v '+name+' n p a b]][k rdr[v '+name+' n p b b]]'
    match=lambda name,value:'x[k rdr[v '+name+' n p a b]][a[v '+name+'][n p a b][v '+value+']]'
    body=both(shape('first'),shape('second'),'g left a[g right a['+both(match('first','left'),match('second','right'),
        't[c[v predicate][v left v right]][v scene]')+']]')
    text='d rqzm[first j[a] second j[a] predicate h[a a] e] e[b scene['+body+']].\n'
    predicate='i[foot a process a][k rqzg[l[a][v body v carrier v foot v process]]]'
    text+=bind_goal('rqzn',['body','carrier'],'k rqzm[l[a][] l[a][] '+predicate+']')
    text+=bind_goal('rqzo',['body','carrier','foot'],'k rqzm[l[a][v foot] l[a][] '+predicate+']')
    text+=bind_goal('rqzp',['body','carrier','process'],'k rqzm[l[a][] l[a][v process] '+predicate+']')
    text+='''
d rqzq[goal i[h[j[a]] e] count b bindings j[a]] e[b scene[
 w[k rdr[v bindings v count]][g person a[w[a[v bindings][n p a b][v person]][
  t[k rqzj[v person v goal v bindings i[items j[a]][k rdr[v items v count]]]][v scene]
 ]]]
]].
d rqzr[bindings j[a]] e[k rqzq[r[p rqzn] n p c b v bindings]].
d rqzs[bindings j[a]] e[k rqzq[r[p rqzo] n p d b v bindings]].
d rqzt[bindings j[a]] e[k rqzq[r[p rqzp] n p d b v bindings]].
'''
    def denied(target,items):
        count=len(items)
        return 'k rjp[v source v person v role r[p '+target+'] l[a]['+' '.join('v '+x for x in items)+'] '+\
            'e[n p a b][n p a b] v scene i[bindings j[a]][k rdr[v bindings n p '+chr(97+count)+' b]] p h7k p h7l]'
    body=both(denied('rqzr',['person','carrier']),
        'f foot a[y[c[v feet][v foot]]['+denied('rqzs',['person','carrier','foot'])+']]',
        'f process a[y[c[v processes][v process]]['+denied('rqzt',['person','carrier','process'])+']]',
        'f foot a[f process a[y[w[c[v feet][v foot]][c[v processes][v process]]]['+
            denied('rqzk',['person','carrier','foot','process'])+']]]')
    text+='d rqzu[source a person a role a carrier a feet h[a] c processes h[a] c scene d] c['+body+'].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions());doc['statements']=statements
    core=deepcopy(doc);core.update(declarations=closure(doc,['rqzr','rqzs','rqzt','rqzl','rqzu']),statements=[])
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqzm']),statements=[])
    basis=dict(status='existential_goal_slots_and_scope_comparison',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Existential goal slots composed; adopted manuscript unchanged',flush=True)


if __name__=='__main__':main()
