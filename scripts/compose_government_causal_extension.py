"""Extend one civic causal model to later government principle changes."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=tuple('data/'+n+'-basis-v1.json' for n in ('civic-choice-mediation','government-principle-profile','government-benefit-appraisal','civic-human-agency'))
LIBRARY='examples/v016/government-causal-extension.noema';BASIS='data/government-causal-extension-basis-v1.json'
STATE='h[a] c';TRUE='e[n p a b][n p a b]';FALSE='u['+TRUE+']'
CONTEXT='community a lowerorder a higherorder a reference d start d end d'
CARGS='v community v lowerorder v higherorder v reference v start v end'
FIELDS=CONTEXT+' government a late d';ARGS=CARGS+' v government v late'
G='v government v community v reference';C='v community v reference'
PRIMITIVES={
 'h27dy':('[a a a d d d a d '+STATE+' d] d',
   ['community','lowerorder','higherorder','reference','start','end','government','late','state','point'],
   '同じ市民的因果モデルの解で、政治的終点まで延ばした基準履歴のこの点に対応する状況。元の心的・能力履歴上ではh27cqとの一致を要求し、延長履歴も全射・一対一・順序保存で照合する。別の因果モデルや別の背景へ取り替えず、政府・原則範囲・規範的立場も固定する。'),
 'h27dz':('[a a a d d d a d a d] a',
   ['community','lowerorder','higherorder','reference','start','end','government','late','rule','point'],
   '同じ固定モデルで、この政府の同じ規則内容の同値類が指定した基準点で採用されていることを表す二値変数。全候補規則の始点と政治的終点で、実際のr6k6の内容と解の値を照合する。原因変数と同一にはせず、内容が常に一致する複数箇所による変数共有は許す。単なる規則名の付け替えを内容変化にしない。'),
}
MEANINGS={
 'r6l2':'心的経過の始点・終点とそれより後の政治的終点を、同じ厳密な全順序の履歴に結ぶ。元の履歴の全点と順序を保持し、始点から心的終点までの区間を延長履歴と一致させる。各解への対応は全射・一対一・順序保存で、元の対応h27cqと一致する。',
 'r6l3':'同じ政府の全候補規則の始点と政治的終点について、採用内容を表す変数が同じ因果モデル内にあり、原因要因そのものと異なることを要求する。規則の範囲はr6k7で別に完全性を確認する。',
 'r6l4':'一つの解について、既存の心的・能力の内容照合r6kwと延長履歴r6l2を満たす。同じ政府の全原則を対応する始点・政治的終点で評価し、全内容同値類の採用r6k6とその同じモデル変数の値を照合する。',
 'r6l5':'同じ全候補のうち少なくとも一つで、観測解の前後の採用増減と、指定比較解の同じ前後の採用増減が異なる。二つの交差和で符号付き変化を比較し、同じ共通変化や一定の既存差を作用にせず、反対方向への変化は区別する。',
 'r6l6':'既存r6kzと同じ集団原因・機構・観測を保ち、政府原則の観測された変化r6laを要求する。政治的区間の観測対応は恒等であり、真偽両側の介入解が非空で全てr6l4を満たす。原因要因を偽にした全解でr6l5の異なる採用変化を要求する。後件の全消失や旧原則撤回と新原則採用の両方は要求しない。',
 'r6l7':'同じ政府原則への因果作用r6l6の政治的終点で、同じ全人間成員がr6ldの自分の理由による行為能力を持ち、同じ政府がr6lyの尊厳に応じた扱いへの自己利益判断を持つ。二つの関係節を別人口・別政府・別時点へ移さず、実際の履行やその方針の規範的採用は追加しない。',
 'r6ma':'同じ共同体・二制度・基準・始点・心的終点・政府を固定し、r6l7の後続する政治的終点ごとの内容を返す。Wenn/so全体の量化と談話上の強調は後続で接続する。',
}
LIMITS=[
 'und endlich auch sogar auf die Grundsätze der Regierungの政府原則への作用を、心的・能力の変化と同じ集団原因を持つ構造モデルにおける、後の規則内容の採用変化として読む。民衆の心的変化が政府作用を完全に媒介することや、各成員が個別に必要であることは要求しない。',
 'endlichは同じ経過の後の政治的評価点として、心的・能力変化を確認する点より後に置く。この中間点は民衆の変化の完全終了ではなく、政府への作用の初発点も断言しない。auch/sogarの追加と期待上の強調はこの時間条件に還元せず全文統合へ残す。',
 '原則の内容同値類の採用はr6k6、現実の前後変化はr6laを再利用する。範囲相対的な同値であり、任意の可能世界についての同値証明とはしない。追加のみ・撤回のみも変化であり、旧rx3の置換を必須にしない。',
 '因果比較は同じ規則内容の符号付き採用変化の差である。原因なしでも別の変更や同じ方向の一部の変更は起こり得る。対照側の変化全体の消失を要求せず、反対方向の変化を一定の差として相殺しない。始点から終点までに変化して元へ戻っただけの過程は、この終点比較だけでは捉えない。',
 '元の全履歴・順序・内容・介入機構を保持したまま政治的終点へ延長する。原則を表す変数を元の変数列に含めることが必要であり、モデルを別物に差し替える接続ではない。共有変数の内容は全介入解で一致しなければならない。機構と写像の妥当性を有限例から社会的因果の実証へ昇格させない。',
 '政府の利益判断は同じ終点に要求するが、その判断が実際に正しいこと、尊厳方針の規範的採用r6lp、実際の適合処遇r6lqを推論しない。原則の変更は同じ政府の全候補についての作用であり、この方針だけが新規採用されたと原文に補わない。',
 '人間の関係節は同じ全人間成員の能力についての追加内容であり、集団得点の増加だけから導かず、尊厳の対象を能力成功者へ絞る条件にしない。以前は理性や尊厳がなかったとも主張しない。',
 '前件の比喩、Wenn/soの全事例量化、談話の追加・強調、著者注参照・全文帰属・通読判断はまだ未統合。今回の接続を単位全体の意味判断へ加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    history=lambda p:'k h27ch['+C+' v start v late '+p+']'
    old=lambda p:'k h27ch['+C+' v start v end '+p+']'
    order=lambda l,r:'k h27ci['+C+' v start v late '+l+' '+r+']'
    oldorder=lambda l,r:'k h27ci['+C+' v start v end '+l+' '+r+']'
    hist='i[point d]['+history('v point')+']';before='i[left d right d]['+order('v left','v right')+']'
    ohist='i[point d]['+old('v point')+']';obefore='i[left d right d]['+oldorder('v left','v right')+']'
    mapped=lambda state,t:'k h27dy['+ARGS+' '+state+' '+t+']'
    start=mapped('v state','v start');late=mapped('v state','v late')
    image='g point d['+both(history('v point'),'e['+mapped('v state','v point')+'][v image]')+']'
    onto='f image d[z[k h27ch['+C+' '+start+' '+late+' v image]]['+image+']]'
    pairs=both(history('v left'),history('v right'))
    aligned=both('z[e[v left][v right]][e['+mapped('v state','v left')+']['+mapped('v state','v right')+']]',
      'z['+order('v left','v right')+'][k h27ci['+C+' '+start+' '+late+' '+mapped('v state','v left')+' '+mapped('v state','v right')+']]')
    oldpairs=both(old('v left'),old('v right'))
    prefix='f point d[z[c[k rlz['+ohist+' '+obefore+' v start v end]][v point]][c[k rlz['+hist+' '+before+' v start v end]][v point]]]'
    text='d r6l2['+FIELDS+' state '+STATE+'] c['+both('k ta['+hist+' '+before+']',*[history('v '+t) for t in ('start','end','late')],
      order('v start','v end'),order('v end','v late'),prefix,
      'f point d[y['+old('v point')+']['+both(history('v point'),'e['+mapped('v state','v point')+'][k h27cq['+CARGS+' v state v point]]')+']]',
      'f left d[f right d[y['+oldpairs+'][z['+oldorder('v left','v right')+']['+order('v left','v right')+']]]]',
      onto,'f left d[f right d[y['+pairs+']['+aligned+']]]')+'].\n'
    selected='k h27db['+G+' v rule]';endpoint='x[e[v point][v start]][e[v point][v late]]'
    each=lambda body:'f rule a[f point d[y['+both(selected,endpoint)+']['+body+']]]'
    variable='k h27dz['+ARGS+' v rule v point]';variables='k h27cm['+CARGS+']';factor='k h27co['+CARGS+']'
    text+='d r6l3['+FIELDS+'] c['+each(both('k rz['+variables+' '+variable+']','u[e['+variable+']['+factor+']]'))+'].\n'
    text+='d r6l4['+FIELDS+' state '+STATE+'] c['+both('k r6kw['+CARGS+' v state]','k r6l2['+ARGS+' v state]',
      'k r6k7['+G+' '+start+']','k r6k7['+G+' '+late+']',
      each('z[c[v state]['+variable+']][k r6k6['+G+' v rule '+mapped('v state','v point')+']]'))+'].\n'
    observed='k h27cp['+CARGS+']'
    status=lambda s,t:'k hd[k r6k6['+G+' v rule '+mapped(s,'v '+t)+']]'
    first='k ha['+status(observed,'late')+' '+status('v state','start')+']'
    second='k ha['+status(observed,'start')+' '+status('v state','late')+']'
    text+='d r6l5['+FIELDS+' state '+STATE+'] c[g rule a['+both(selected,'u[e['+first+']['+second+']]')+']].\n'
    equations='i[variable a state '+STATE+'][k h27cn['+CARGS+' v variable v state]]'
    mask='i[variable a][e[v variable]['+factor+']]'
    side=lambda flag,body:'k rw['+variables+' '+equations+' '+mask+' i[variable a]['+flag+'] i[state '+STATE+']['+body+']]'
    text+='d r6l6['+FIELDS+'] c['+both('k r6kz['+CARGS+']','k r6l3['+ARGS+']','k r6l4['+ARGS+' '+observed+']',
      'k r6la['+G+' v start v late]',
      'f point d[y['+history('v point')+'][e['+mapped(observed,'v point')+'][v point]]]',
      side(TRUE,'k r6l4['+ARGS+' v state]'),side(FALSE,both('k r6l4['+ARGS+' v state]','k r6l5['+ARGS+' v state]')))+'].\n'
    text+='d r6l7['+FIELDS+'] c['+both('k r6l6['+ARGS+']','k r6ld['+C+' v late]','k r6ly['+G+' v late]')+'].\n'
    text+='d r6ma['+CONTEXT+' government a] e[b late[k r6l7['+ARGS+']]].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imports={}
    for lib,roots in zip(libs,(('r6kz','r6kw'),('r6k6','r6k7','r6la'),('r6ly',),('r6ld',))):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imports:assert d==imports[n]['declaration'] and e['meaning_ja']==imports[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imports[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imports.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in libs))
    basis=dict(status='same_collective_cause_extended_to_later_government_principle_changes_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imports.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imports.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
