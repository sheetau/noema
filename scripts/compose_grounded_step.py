"""Build an exterior single-foot relocation goal from contact and process relations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-unpermitted-families.noema'
PARENT_BASIS='data/unpermitted-families-basis-v1.json'
FULL='examples/v016/kant-grounded-step.noema'
CORE='examples/v016/grounded-step-core.noema'
LIBRARY='examples/v016/contact-relocation.noema'
BASIS='data/grounded-step-basis-v1.json'
PRIMITIVES={
 'hzxw':(['part','body','point'],'同じ身体の脚の末端で、地面への支持・接地を担う部位としての足である。手・身体全体・別の身体の足とは区別する。自然の部位か補綴かという材質の区別は固定せず、その時点での身体への所属と機能的な部位分類を与える。現在の接地や歩行の実行は含意しない。'),
 'hzxx':(['part','place','point'],'同じ身体部位が、その場所の地面または移動の支持面に直接接触している。近接、空中での投影位置、他の部位だけの接触とは区別する。荷重の数量、摩擦、身体全体の均衡、意図的な動作は含意しない。'),
 'hzxy':(['part','process','start','end'],'指定した部位の始点から終点への空間的位置変化が、その同じ過程を構成する変化である。別の過程による同時の位置変化や、その過程が部位の別の性質だけを変えることとは区別する。位置の値、接触、移動の意図や身体全体の移動は別条件とする。'),
}
MEANINGS={
 'rqzb':'指定した履歴内の欠落のない過程範囲で、同じ部位の初期位置と終端位置が異なり、両端でそこで接地し、厳密な中間時点が存在し、その全てでいずれの場所にも接地していない。一回の接地から次の接地までの移し替えの型。最初と最後が範囲の両端であり、途中の再接地や範囲の切抜きを認めない。部位が足か、身体が移動したかは別条件。',
 'rqzc':'同じ過程範囲の全時点で、指定した移動部位とは異なる、その同じ身体の足に地面側の接触が少なくとも一つある。身体の全足が離地する局面を区別する。どの足が接触するかは時点ごとに異なってよく、荷重・均衡や全ての歩容の分類をこの条件だけから導かない。',
 'rqzd':'同じ身体・足・実際の移動過程・前後状況へ、身体の脚による移動、過程の生起と状態移行、身体と足が同じ変化を受けること、足の位置変化がその過程を構成すること、足の継続した身体所属、rqzbの一回の接地更新とrqzcの他の足の接触を結ぶ。通常の一歩を構成する候補で、足を滑らせる型、片足跳び、走行の離地相を含む型はこの読みから分ける。',
 'rqze':'rqzdの同じ足・移動過程の終端で、その足の位置が指定した装置の外部qvにある。内部でないだけの境界位置は代用せず、身体の中心の位置や別の足の位置を着地点へ流用しない。出発位置が内部だったことは要求しない。',
 'rqzf':'身体・装置・足・移動過程の四個体だけを持つ引数列である。空・不足・余分な引数を捨てて解釈しない。',
 'rqzg':'順序付きの四引数を身体・装置・足・移動過程として受け、評価時点を同じ過程の終端とするrqzeの先行始点があるという目標内容。許容の対象として引用でき、引用されたことだけでは現実の一歩や装置外への到達を主張しない。',
 'rqzh':'指定候補の全てについて、同じ身体・装置を先頭二位置に持つ四引数のrqzgを、同じ出所・名宛人・役割・正極性・文脈で積極的に許容しない。rqy6へ閉じた目標関数と候補ごとの引数列を渡す。目標を実行評価せず、実際の不実行・禁止・身体的不能・勇気不足を補わない。',
}
LIMITS=[
 '地面側の接触を保ちながら一本の足を一回移す通常の一歩の候補。足を滑らせる歩き方、片足跳び、階段・不整地・補助具利用の全類型を網羅したとはしない。',
 '履歴と過程範囲は完全な意味上の範囲として指定する。有限の観測標本だけから現実の中間時点の全てを確認したとはしない。評価器には選択外を含む総関数の解釈が必要な場合がある。',
 '足の身体所属、地面側接触、部位の位置変化と同じ過程との結合という三つの関係を追加する。足という身体部位の分類は公開した基本規約であり、解剖学や接触力学の全説明をこの文語で完了したとはしない。',
 'rqzhは一歩の目標内容への許容欠如であり、勇気を伴ってその目標を試みることへの許容とまだ同一視しない。候補全体の指定、先行する阻止時点、原文の比喩への結合は残る。',
 '比較構成として保存し、採用中の47文と既存十一単位の判断は変更しない。原文一文全体の意味確認は増やさない。',
]


def both(*items):
    assert items
    return items[0] if len(items)==1 else 'w['+items[0]+']['+both(*items[1:])+']'


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def additions():
    body=both('u[e[v origin][v destination]]','k tb[v history v phase v before]',
        'c[v phase][v start]','c[v phase][v end]','c[v before][v start v end]',
        'e[c[v position][v part v start]][v origin]','e[c[v position][v part v end]][v destination]',
        'c[v contact][v part v origin v start]','c[v contact][v part v destination v end]',
        'f point d[y[c[v phase][v point]]['+both('x[e[v point][v start]][c[v before][v start v point]]',
            'x[e[v point][v end]][c[v before][v point v end]]')+']]',
        'g middle d['+both('c[v phase][v middle]','c[v before][v start v middle]','c[v before][v middle v end]')+']',
        'f point d[y['+both('c[v phase][v point]','c[v before][v start v point]','c[v before][v point v end]')+'][f place a[u[c[v contact][v part v place v point]]]]]')
    text='d rqzb[part a origin a destination a start d end d history h[d] c phase h[d] c before h[d d] c position h[a d] a contact h[a a d] c] c['+body+'].\n'
    support=both('u[e[v other][v movingpart]]','c[v foot][v other v body v point]',
        'c[v contact][v other v place v point]')
    text+='d rqzc[body a movingpart a phase h[d] c foot h[a a d] c contact h[a a d] c] c['+\
        'f point d[y[c[v phase][v point]][g other a[g place a['+support+']]]]].\n'
    text+='r hzxw[a a d] c.r hzxx[a a d] c.r hzxy[a a d d] c.\n'
    phase='i[point d][k h4x[v process v end v point]]'
    body=both('u[e[v body][v foot]]','k zai[v body v process v start]','k dg[v process v start]',
        'k ag[v process v start v end]','k la[v body v process v start v end]','k la[v foot v process v start v end]',
        'k hzxy[v foot v process v start v end]',
        'f point d[y[k h4x[v process v end v point]][k hzxw[v foot v body v point]]]',
        'k rqzb[v foot k qw[v foot v start] k qw[v foot v end] v start v end i[point d][k ia[v body v end v point]] '+phase+
            ' i[earlier d later d][k ic[v earlier v later v end]] p qw p hzxx]',
        'k rqzc[v body v foot '+phase+' p hzxw p hzxx]')
    text+='d rqzd[body a foot a process a start d end d] c['+body+'].\n'
    text+='''
d rqze[body a carrier a foot a process a start d end d] c[w[k rqzd[v body v foot v process v start v end]][k qv[v carrier k qw[v foot v end] v end]]].
d rqzf[bindings j[a]] c[k rdr[v bindings n p e b]].
'''
    # Consume four arguments in order using the existing sequence fold. Unlike
    # four existential lookups this does not search the entire object domain.
    predicate='i[body a carrier a foot a process a][b finish[g start d[k rqze[v body v carrier v foot v process v start v finish]]]]'
    consume='i[acc h[a a a a] e item a][i[x a y a z a unused a][c[v acc][v item v x v y v z]]]'
    body='g seed a[t[c[q[v bindings]['+predicate+']['+consume+']][v seed v seed v seed v seed]][v end]]'
    text+='d rqzg[bindings j[a]] e[b end[w[k rqzf[v bindings]]['+body+']]].\n'
    text+='''
d rqzh[source a person a role a carrier a members h[a] c arguments h[a] j[a] scene d] c[
 k rqy6[v source v person v role v members i[item a][r[p rqzg]] v arguments e[n p a b][n p a b] v scene
  i[bindings j[a]][w[k rqzf[v bindings]][w[a[v bindings][n p a b][v person]][a[v bindings][n p b b][v carrier]]]] p h7k p h7l]
].
'''
    return text


def build():
    old=parent();doc=deepcopy(old.document);assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions());doc['statements']=statements
    core=deepcopy(doc);core.update(declarations=closure(doc,['rqze','rqzg','rqzh']),statements=[])
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqzb','rqzc']),statements=[])
    added=doc['declarations'][size:]
    basis=dict(status='grounded_contact_relocation_and_bound_exterior_step_goal',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],
            meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Exterior single-foot relocation goal composed; adopted manuscript unchanged',flush=True)


if __name__=='__main__':main()
