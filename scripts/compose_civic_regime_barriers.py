"""Tie causal inability to the same two civic regimes in every intervention."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-advantage-appearance-basis-v1.json'
MAIN='data/whole-view-sentence-basis-v1.json'
OLD='examples/v016/assessed-barriers.noema';OLD_BASIS='data/assessed-barriers-basis-v1.json'
LIBRARY='examples/v016/civic-regime-barriers.noema';BASIS='data/civic-regime-barriers-basis-v1.json'
STATE='h[a] c';EQUATIONS='h[a '+STATE+'] c'
CONTEXT=('community','lowerorder','higherorder','reference','anchor')
FIELDS='community a lowerorder a higherorder a reference d anchor d';ARGS=' '.join('v '+n for n in CONTEXT)
SIGNATURE='a a a d d';TRUE='e[n p a b][n p a b]';FALSE='u['+TRUE+']'
PRIMITIVES={
 'h26y3':('['+SIGNATURE+'] j[a]',list(CONTEXT),'同じ共同体・二法秩序・固定基準・比較起点での因果比較に使う二値変数の全範囲。市民的自由の制度条件と、その条件での精神的活動の機会に関わる要因を扱う。重複又は範囲外に真の値を持つ割当ては既存の構造方程式の検査に従い拒否し、都合のよい結果だけを変数範囲へ含めない。'),
 'h26y4':('['+SIGNATURE+' a '+STATE+'] c',list(CONTEXT)+['variable','state'],'同じ比較において、この変数に構造方程式が与える真偽値。変数の実際の値はstateが与え、その値と方程式の値の一致をruが検査する。両介入で同じ機構と外生的な背景を保ち、因果的な適合は公開するモデルの仮定として説明する。単なる二変数の相関を因果機構に自動変換しない。'),
 'h26y5':('['+SIGNATURE+'] a',list(CONTEXT),'同じ比較モデルで、真なら指定した高い側、偽なら指定した低い側の市民的自由の制度条件を選ぶ要因。単なる高低の名札ではなく、全介入解の対応する制度と実際の許可集合をr6htで照合する。人物・課題・固定基準又は規範的な役割を切り替える変数ではない。'),
 'h26y6':('['+SIGNATURE+' '+STATE+'] d',list(CONTEXT)+['state'],'同じ比較モデルのこの割当てに対応する、選ばれた一方の制度条件を評価する状況。高い側と低い側は同じ比較起点で固定した二法秩序に対応させ、全解の許可集合を基準の側と照合する。精神的課題の内容と本人を変更せず、下流の機会がどう変わるかをその状況で評価する。'),
 'h26y7':('['+SIGNATURE+'] '+STATE,list(CONTEXT),'同じ比較起点の高い側の制度状況に対応する観測割当て。元の非介入方程式への適合、高い側の要因が真であること、状況対応の一致と現在の評価済みの不能をrwxで別に確かめる。任意の介入後の成功例を観測として置き換えない。'),
 'h26za':('['+SIGNATURE+' a a] c',list(CONTEXT)+['person','task'],'同じ比較で、越えがたい制限が及ぶ対象として指定する人と精神的判断課題の全範囲。範囲の非空性、同じ人間の成員への帰属、課題の全事項と各対象の因果的な達成不能を合成側で確認する。全ての精神活動が不能だとはせず、検査が通る対象だけへ事後選別しない。'),
}
MEANINGS={
 'r6ht':'同じ因果割当ての要因が真なら高い側、偽なら低い側を選び、その側の法秩序が対応状況で運用されることを要求する。固定した全成員・市民的行為について、対応状況の許可集合が比較起点の同じ側の集合と双方向に一致する。',
 'r6hu':'比較起点で同じ二法秩序の市民的自由にr6hgの大小があり、選択要因が変数範囲に属し、その要因を真・偽それぞれへ介入した非空の全解がr6htを満たす。観測点だけ又は一つの好都合な解だけの照合で済ませない。',
 'r6hv':'同じ人間の成員・非空の精神的課題と二制度の因果比較を保持する。低い側へ介入した解の少なくとも一つには同じr6hhの目標の達成方法があり、高い側へ介入した非空の全解では全方法の整合した評価の下で達成不能になるという既存rwxを使う。高い側の観測割当て・現状の不能と状況対応も一致させる。',
 'r6hw':'同じ二制度の因果対応r6huを保持し、制限の対象となる人と課題が非空で、その全組にr6hvが成立する。制限の及ばない他の課題を禁止せず、一部の対象の成功で他の対象の欠落を補わない。',
 'r6hx':'同じ人の観点・共同体・二法秩序・固定基準・比較点で、r6hsの有利に見える内容とr6hwの実際の因果的な制限を連言する。見かけの候補から制限の不在を導かず、二つの内容を同じ比較へ置く。dochの提示や低い側の発展機会は後続で追加する。',
}
LIMITS=[
 'u0017第三文のund setzt ihr … unübersteigliche Schrankenに向けた依存群。制限を、指定した二制度条件の因果比較で、同じ人・同じ判断課題の達成機会を高い側が閉ざすこととして読む。原文の唯一の語義又は現実の社会の因果機構を実証したという主張ではない。',
 '各介入解の選択要因を、公的な法秩序の運用と全関連行為への実際の許可集合へ照合する。真なら高い側、偽なら低い側の既定の集合と一致させ、変数名だけで自由を表さない。人物・役割・行為記述・基準は固定し、未知の規範を不許可へ補わない。',
 '同じ機構と外生的背景の二値構造方程式を用いる強い比較である。低い側の少なくとも一解で達成機会があり、高い側の非空の全解で評価済みの不能を要求する。全ての低い側の解で成功すること、全能力の同時発展又は一般的な確率傾向をこの条件に混ぜない。',
 '越えがたさは指定された制度条件・方法・結果評価に相対的な達成不能とする。未知又は未評価の方法を不可能に数えず、未来全体・全論理的可能性・未発見の技術にわたる絶対的不可能は要求しない。現に行為したことも意味しない。',
 '同じ高い側の観測が元の方程式を満たし、選択要因と対応状況が一致することを要求する。介入解の比較だけを実際の制限の成立へ流用しない。対象範囲は非空の指定課題であり、民衆の全精神活動が不可能という主張へ広げない。',
 '有利に見える内容と一部の実際の制限は論理的に両立し得る。dochの期待との対照は別に提示する。低い側による全能力に応じた発展の余地、hingegenの対照、jener/diesemとRaumの読み、全文帰属は未統合であり、意味確認文字数は増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def main_catalog():return load_catalog(ROOT,MAIN)
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rwx',))
    ms=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions'];return ds,{n:ms[n] for n in ('rww','rwx')}
def definitions():
    factor='k h26y5['+ARGS+']';selected='c[v state]['+factor+']';mapped='k h26y6['+ARGS+' v state]'
    high='k h26yz[v community v reference v anchor]';low='k h26yy[v community v reference v anchor]'
    def option(order,point):return 'k r6hf[v community v '+order+' v person v activity v reference '+point+']'
    expected='x['+both(selected,option('higherorder',high))+']['+both('u['+selected+']',option('lowerorder',low))+']'
    actual='x['+both(selected,option('higherorder',mapped))+']['+both('u['+selected+']',option('lowerorder',mapped))+']'
    civic='x['+both(selected,'k r6fr[v community v higherorder v reference '+mapped+']')+']['+both('u['+selected+']','k r6fr[v community v lowerorder v reference '+mapped+']')+']'
    scope='k r6he[v community v person v activity v reference]'
    text='d r6ht['+FIELDS+' state '+STATE+'] c['+both(civic,'f person a[f activity a[y['+scope+'][e['+expected+']['+actual+']]]]')+'].\n'
    variables='k h26y3['+ARGS+']';equations='i[variable a state '+STATE+'][k h26y4['+ARGS+' v variable v state]]'
    mask='i[variable a][e[v variable]['+factor+']]'
    text+='d r6hu['+FIELDS+'] c['+both('k r6hg[v community v lowerorder v higherorder v reference '+low+' '+high+']','k rz['+variables+' '+factor+']',
      *['k rw['+variables+' '+equations+' '+mask+' i[variable a]['+flag+'] i[state '+STATE+'][k r6ht['+ARGS+' v state]]]' for flag in (FALSE,TRUE)])+'].\n'
    providers=' '.join(('i[actor a method a point d][k h26yv[v community v task v reference v actor v method v point]]',
      'i[actor a method a point d outcome d][k h26yw[v community v task v reference v actor v method v point v outcome]]',
      'i[actor a method a point d outcome d][k h26yx[v community v task v reference v actor v method v point v outcome]]'))
    barrier='k rwx[v person k r6hh[v person v task v reference] '+variables+' '+equations+' '+factor+' i[state '+STATE+']['+mapped+'] '+providers+' '+high+' k h26y7['+ARGS+']]'
    text+='d r6hv['+FIELDS+' person a task a] c['+both('k r6hu['+ARGS+']','k r6hd[v person v community v reference]',
      'k h26ys[v community v person v task v reference]','g matter a[k h26yt[v task v matter v reference]]',barrier)+'].\n'
    target='k h26za['+ARGS+' v person v task]'
    text+='d r6hw['+FIELDS+'] c['+both('k r6hu['+ARGS+']','g person a[g task a['+target+']]',
      'f person a[f task a[y['+target+'][k r6hv['+ARGS+' v person v task]]]]')+'].\n'
    text+='d r6hx[observer a community a lowerorder a higherorder a reference d] e[b anchor['+both(
      't[k r6hs[v observer v community v lowerorder v higherorder v reference]][v anchor]','k r6hw['+ARGS+']')+']].\n'
    return text
def build():
    p=parent();doc=deepcopy(p.document);doc['statements']=[];imported=dict(p.entries);ds,means=legacy()
    for d in ds:
        n=d['name']
        if n in imported:
            assert d==imported[n]['declaration'],n
            if n in means:assert means[n]==imported[n]['meaning_ja'],n
        else:
            doc['declarations'].append(d)
            if n not in means:
                e=main_catalog().entries[n];assert d==e['declaration'],n;imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(p.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|set(main_catalog().source_sha256)|{OLD,OLD_BASIS}
    basis=dict(status='same_civic_regimes_causal_assessed_barriers_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{n:OLD_BASIS for n in means},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
