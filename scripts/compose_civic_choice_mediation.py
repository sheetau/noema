"""Hold development on while replacing its complete mental trajectory."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_feedback import STATE,FIELDS,ARGS,SIGNATURE,TRUE,FALSE,C

PARENT='data/civic-feedback-basis-v1.json';CHOICE='data/self-directed-choice-basis-v1.json'
LIBRARY='examples/v016/civic-choice-mediation.noema';BASIS='data/civic-choice-mediation-basis-v1.json'
PRIMITIVES={
 'h27c5':('['+SIGNATURE+' a a d] a',['community','lowerorder','higherorder','reference','start','end','person','feature','point'],
  '同じ因果モデルで、この固定した人・心的特徴・基準時点の応答傾向を表す二値変数。全区間の全対象を照合し、原因要因とは異なるモデル内変数とする。複数の組が同じ変数を共有することは許すが、全ての関連する解でそれぞれの実際の応答内容との一致を要求する。変数対応を介入解や結果に応じて変更しない。'),
}
MEANINGS={
 'r6kt':'同じ完全な順序区間で、二つの数値経過の差が漸次的に増す。差の比較を交差和で構成し、終点増加・厳密な中間値・固定した能力段階上限を超す上下両方向の変化への中間値を要求する。始点差の零、差の非負、全点単調増加は要求しない。',
 'r6ku':'この同じ区間の民衆の全成員・全心的特徴・全時点に対応するモデル変数の範囲。存在量化で対応の像を構成し、特定の好都合な特徴だけを媒介対象に選ばない。',
 'r6kv':'全ての媒介対象に対応する変数が同じモデルに属し、原因側の集団要因とは異なることを要求する。変数共有は可能だが、各内容との同値はr6kwで別に照合する。',
 'r6kw':'同じモデル解で既存r6kcの原因内容・完全な時計対応・心的区間を保持し、同じ全人・全行為の能力評価r6kqを要求する。全媒介対象が評価済みで、その変数値と対応時点のr6jyの実際の応答傾向が一致する。',
 'r6kx':'観測経過と指定解の同じ時点での能力得点の差をr6ktへ渡す。差の漸次的増加は観測側の増加が比較側より大きくなる寄与を表し、比較側の能力やその増加が全面的に消えることは要求しない。',
 'r6ky':'同じ方程式と背景で、原因要因を真に保ち、全媒介変数だけを指定した原因偽側の解の値に固定する。残りの変数は方程式に従う。非空の全解でr6kwの内容照合とr6kxの能力への漸次的寄与を要求する。',
 'r6kz':'既存の心的反作用r6keと観測された能力増加r6krを、同じ民衆・基準・区間・構造モデルへ結ぶ。観測と原因真偽双方の全解で内容を照合し、全ての原因偽側の心的経過についてr6kyの媒介比較を行う。直接経路や他の原因による能力増加を禁止しない。',
 'r6k2':'同じ共同体・二制度・開始点について、前文の固定基準h26zjの下で、心的反作用から行為能力の増加へ至るr6kzを終点ごとの内容にする。条件文全体や後続の政府原則の代用ではない。',
}
LIMITS=[
 'wodurchを、同じ民衆の心的傾向の変化が行為の自由への能力増加に寄与する媒介として読む。前件の発達、心的傾向、能力を既存定義のまま一つのモデル・基準・時間区間へ結ぶ。',
 '原因を偽にした各解の全心的プロフィールを取り、原因を真に保ったモデルでそのプロフィールに固定する。これは明示した構造モデルの介入比較であり、原文が方程式や実験的同定の証拠を与えるという主張ではない。',
 '固定するのは同じ全人・全特徴・全区間の心的応答変数と原因変数である。能力を直接指定したり、別の法秩序・人口・行為・重み・基準へ変更したりしない。共有変数があれば関連する各内容の同値も必須で、名札だけの真偽操作を許さない。',
 '観測された能力の漸次的増加に加え、媒介経過を置換した全解との差自体が漸次的に増すことを要求する。比較側でも能力が増えてよい。一定の初期差や共通の時間変化だけでは寄与としない。局所的後退と停滞を許す。',
 '全ての原因偽側の解と全ての媒介介入解に成立を要求し、空の解集合を成功としない。非決定性に対する頑健な限定であり、確率的な媒介や全ての実際原因の理論を尽くさない。能力差にも事前の同じ段階上限を用いる。',
 '原因側の各個人の不可欠性、完全媒介、能力増加の全面消失を追加しない。比較側で心的傾向が変わることも許す。比喩の対象側の内容を使い、比喩提示から実際の因果的真理を導かない。',
 'Wenn/so全体の人口・時点量化、政府原則・自己利益・機械以上の人間・尊厳・著者注・全文帰属は未完。今回の部分接続で全文の意味確認文字数を増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def choice():return load_catalog(ROOT,CHOICE)

def definitions():
    hist='i[point d][k h27ch['+C+' v start v end v point]]'
    order='i[left d right d][k h27ci['+C+' v start v end v left v right]]'
    inside=lambda p:'c[k rlz['+hist+' '+order+' v start v end]][v '+p+']'
    before=lambda l,r:'k h27ci['+C+' v start v end v '+l+' v '+r+']'
    # score(x)-baseline(x) < score(y)-baseline(y), without subtraction inputs.
    cross=lambda x,y:'k ha[c[v score][v '+x+'] c[v baseline][v '+y+']]'
    less=lambda x,y:'k hc['+cross(x,y)+' '+cross(y,x)+']'
    middle=lambda l,r,up:'g middle d['+both(inside('middle'),before(l,'middle'),before('middle',r),
        less(l,'middle') if up else less('middle',l),less('middle',r) if up else less(r,'middle'))+']'
    limits=[]
    for up in (True,False):
        lo,hi=('left','right') if up else ('right','left')
        large=both(inside('left'),inside('right'),before('left','right'),
          'k hc[k ha['+cross(lo,hi)+' k h27c4['+C+']] '+cross(hi,lo)+']')
        limits.append('f left d[f right d[y['+large+']['+middle('left','right',up)+']]]')
    text='d r6kt[community a reference d start d end d score h[d] b baseline h[d] b] c['+both(
        'k ta['+hist+' '+order+']','k h27ch['+C+' v start v end v start]','k h27ch['+C+' v start v end v end]',before('start','end'),
        'k hc[n p a b k h27c4['+C+']]',less('start','end'),middle('start','end',True),*limits)+'].\n'
    scope=both('k r6hd[v person v community v reference]','k h27b7['+C+' v person v feature]',inside('point'))
    variable='k h27c5['+ARGS+' v person v feature v point]'
    every=lambda b:'f person a[f feature a[f point d[y['+scope+']['+b+']]]]'
    text+='d r6ku['+FIELDS+' variable a] c[g person a[g feature a[g point d['+both(scope,'e['+variable+'][v variable]')+']]]].\n'
    variables='k h27cm['+ARGS+']';factor='k h27co['+ARGS+']'
    text+='d r6kv['+FIELDS+'] c['+every(both('k rz['+variables+' '+variable+']','u[e['+variable+']['+factor+']]'))+'].\n'
    mapped=lambda state,point:'k h27cq['+ARGS+' '+state+' '+point+']'
    start=mapped('v state','v start');end=mapped('v state','v end');at=mapped('v state','v point')
    text+='d r6kw['+FIELDS+' state '+STATE+'] c['+both('k r6kc['+ARGS+' v state]','k r6kq['+C+' '+start+' '+end+']',
        every(both('k r6jx['+C+' v person v feature '+at+']','z[c[v state]['+variable+']][k r6jy['+C+' v person v feature '+at+']]')))+'].\n'
    observed='k h27cp['+ARGS+']'
    score=lambda state:'i[point d][k r6kp['+C+' '+mapped(state,'v point')+']]'
    text+='d r6kx['+FIELDS+' state '+STATE+'] c[k r6kt['+C+' v start v end '+score(observed)+' '+score('v state')+']].\n'
    equations='i[variable a state '+STATE+'][k h27cn['+ARGS+' v variable v state]]'
    mask='i[variable a][x[e[v variable]['+factor+']][k r6ku['+ARGS+' v variable]]]'
    values='i[variable a][x[e[v variable]['+factor+']][c[v source][v variable]]]'
    text+='d r6ky['+FIELDS+' source '+STATE+'] c[k rw['+variables+' '+equations+' '+mask+' '+values+' i[state '+STATE+']['+both('k r6kw['+ARGS+' v state]','k r6kx['+ARGS+' v state]')+']]].\n'
    mask='i[variable a][e[v variable]['+factor+']]'
    side=lambda sign,b:'k rw['+variables+' '+equations+' '+mask+' i[variable a]['+sign+'] i[state '+STATE+']['+b+']]'
    text+='d r6kz['+FIELDS+'] c['+both('k r6ke['+ARGS+']','k r6kr['+C+' v start v end]','k r6kv['+ARGS+']','k r6kw['+ARGS+' '+observed+']',
        side(TRUE,'k r6kw['+ARGS+' v state]'),side(FALSE,both('k r6kw['+ARGS+' v state]','k r6ky['+ARGS+' v state]')))+'].\n'
    text+='d r6k2[community a lowerorder a higherorder a start d] e[b end[k r6kz[v community v lowerorder v higherorder k h26zj[] v start v end]]].\n'
    return text

def build():
    catalogs=((parent(),('r6ke','r6kc','r6jx','r6jy','h27b7','h27cm','h27cn','h27co','h27cp','h27cq','h26zj')),
              (choice(),('r6kq','r6kp','r6kr','h27c4')))
    doc=deepcopy(parent().document);doc.update(declarations=[],statements=[]);imports={};paths=set()
    for c,roots in catalogs:
        paths.update(c.source_sha256)
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imports:assert d==imports[n]['declaration'] and e['meaning_ja']==imports[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imports[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(c.entries for c,_ in catalogs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imports.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='same_population_mental_trajectory_choice_mediation_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imports.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imports.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
