"""Compose courageous attempts at explicitly bound goals and quote them in norms."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_grounded_step import ROOT,closure,both

PARENT='examples/v016/kant-grounded-step.noema'
PARENT_BASIS='data/grounded-step-basis-v1.json'
FULL='examples/v016/kant-bound-undertaking.noema'
CORE='examples/v016/bound-undertaking-core.noema'
LIBRARY='examples/v016/bound-undertaking.noema'
BASIS='data/bound-undertaking-basis-v1.json'
PRIMITIVES={
 'hzxz':(['person','goal','bindings','scene'],'同じ本人が、閉じた目標関数の記述と順序付き対象列で指定された内容に向け、同じ状況で文脈上十分な勇気を持つ。恐れ・困難に直面して行動へ向かう態度の十分さであり、客観的危険・実際の試み・目標の成立を含意しない。記述、対象列、本人、状況のいずれも別のものから流用しない。'),
 'hzya':(['person','act','goal','bindings','scene'],'同じ本人が、その同じ行為で、閉じた目標関数の記述と順序付き対象列で指定された内容を同じ状況で試みる。本人の勇気、成功、能力、許容とは別の関係。対象列を行為個体の別名に縮めず、別の行為や同じ記述の別引数への試みを流用しない。'),
}
MEANINGS={
 'rqzi':'適合する対象列を持つ閉じた目標関数記述について、同じ本人・状況の勇気と、本人が行う同じ試みの行為の生起を結ぶ一般形。勇気・試み・行為者・生起・対象列の適合性は関係として受け取る。目標の成立を実行評価せず、失敗した取り組みも表せる。',
 'rqzj':'rqziへ、対象列を保持する勇気hzxzと試みhzya、既存の行為者dfと生起dgを接続する。個人一人についての性質記述を扱うhzs4とは目標の型を区別し、既存基本関係の引数や意味を変更しない。',
 'rqzk':'身体・装置・足・移動過程の四個体列を受け、第一位置の本人が、その同じ列のrqzgを目標として勇気を伴って試みる内容。目標側の移動過程と、試みを行う行為は区別し、失敗した試みに架空の成功過程を生起させない。',
 'rqzl':'同じ身体と装置を持つ指定候補の全てについて、rqzkの勇気を伴う試みへの積極的許容がない。出所・名宛人・役割・正極性・文脈と候補の引数列を保持する。勇気、試み、身体的成功、禁止の成立はこの規範から導かない。',
}
LIMITS=[
 '勇気と試みの関係を、目標の記述と明示的な対象列を取る形へ拡張する。旧hzioとf5を再解釈せず、一般形を旧関係へ接続した場合の一致を検査する。新旧の独立した関係解釈が自動的に一致するとは主張しない。',
 '目標の記述と対象列を構文上保持する。同義な記述や別名を自動的に同一化せず、個体の値を新しい引用文字列に変換しない。',
 '試みの行為と目標の移動過程は同一でなくてもよい。同じである場合も許すが、試みから目標過程の生起・成功を要求しない。',
 '候補の範囲は明示的に渡す。有限の例や実際に成功した移動だけを、原文の全ての候補と同一視しない。範囲の根拠と先行時点の阻止・比喩への結合は残る。',
 '比較構成として保存する。採用中の47文、十一単位の意味判断、原文全体の確認済み分量は変更しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def additions():
    return '''
d rqzi[person a goal i[h[j[a]] e] bindings j[a] valid h[j[a]] c
 courage h[a i[h[j[a]] e] j[a] d] c tries h[a a i[h[j[a]] e] j[a] d] c
 performs h[a a d] c occurs h[a d] c] e[b scene[
 w[c[v valid][v bindings]][w[c[v courage][v person v goal v bindings v scene]][g act a[
  w[c[v tries][v person v act v goal v bindings v scene]][w[c[v performs][v person v act v scene]][c[v occurs][v act v scene]]]
 ]]]
]].
r hzxz[a i[h[j[a]] e] j[a] d] c.
r hzya[a a i[h[j[a]] e] j[a] d] c.
d rqzj[person a goal i[h[j[a]] e] bindings j[a] valid h[j[a]] c] e[
 k rqzi[v person v goal v bindings v valid p hzxz p hzya p df p dg]
].
d rqzk[bindings j[a]] e[b scene[w[k rqzf[v bindings]][g person a[
 w[a[v bindings][n p a b][v person]][t[k rqzj[v person r[p rqzg] v bindings p rqzf]][v scene]]
]]]].
d rqzl[source a person a role a carrier a members h[a] c arguments h[a] j[a] scene d] c[
 k rqy6[v source v person v role v members i[item a][r[p rqzk]] v arguments e[n p a b][n p a b] v scene
  i[bindings j[a]][w[k rqzf[v bindings]][w[a[v bindings][n p a b][v person]][a[v bindings][n p b b][v carrier]]]] p h7k p h7l]
].
'''


def build():
    old=parent();doc=deepcopy(old.document)
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions());doc['statements']=statements
    core=deepcopy(doc);core.update(declarations=closure(doc,['rqzk','rqzl']),statements=[])
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqzi']),statements=[])
    added=doc['declarations'][size:]
    basis=dict(status='bound_courageous_attempt_and_quoted_permission_comparison',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],
            meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Bound courageous attempt composed; adopted manuscript unchanged',flush=True)


if __name__=='__main__':main()
