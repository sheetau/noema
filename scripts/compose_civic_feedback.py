"""Connect the same collective development to a changing causal profile contrast."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-disposition-profile-basis-v1.json';GERM='data/germ-figurative-connection-basis-v1.json';MAIN='data/civic-spirit-sentence-basis-v1.json'
LIBRARY='examples/v016/civic-feedback.noema';BASIS='data/civic-feedback-basis-v1.json'
STATE='h[a] c';PROFILE='h[a a d] c';TRUE='e[n p a b][n p a b]';FALSE='u['+TRUE+']';ZERO='n p a b'
SCOPE='community a lowerorder a higherorder a reference d'
SARGS='v community v lowerorder v higherorder v reference'
FIELDS=SCOPE+' start d end d';ARGS=SARGS+' v start v end';SIGNATURE='a a a d d d'
C='v community v reference';PAIR=C+' v person v feature'
PRIMITIVES={
 'h27ck':('[a a a d] j[a]',['community','lowerorder','higherorder','reference'],'この固定した比較組で、前件の発達を共同に評価する原因側の全成員列。非空・重複なし・h27clとの一致を検査する。全員が同じ影響先共同体の成員であるが、その民衆の全員であるとは限らない。結果から不要だった人だけを除外しない。'),
 'h27cl':('[a a a d a] c',['community','lowerorder','higherorder','reference','person'],'この比較で前件の原因側に指定した成員の全範囲。時点・介入解・作用の成否で変更しない。構成員ごとの不可欠性をこの所属だけから導かない。'),
 'h27cm':('['+SIGNATURE+'] j[a]',['community','lowerorder','higherorder','reference','start','end'],'同じ比較組と後続区間に用いる二値構造モデルの全変数列。機構と外生的背景を固定し、原因側の集団的発達と心的応答傾向の経過を扱う。変数だけを反転した無内容な名札を許さず、全解の実際の内容を照合する。'),
 'h27cn':('['+SIGNATURE+' a '+STATE+'] c',['community','lowerorder','higherorder','reference','start','end','variable','state'],'同じ因果モデルのこの変数に構造方程式が与える値。値とstateの一致はruで検査する。原因要因への介入以外の機構・外生背景・基準を両側で保持するという公開モデルの仮定を伴う。相関表だけから機構の妥当性を導かない。'),
 'h27co':('['+SIGNATURE+'] a',['community','lowerorder','higherorder','reference','start','end'],'同じモデルで、指定した原因側の全成員に前件r6jdが共通始点で成立することを表す要因。真偽と実際の発達内容の同値を全介入解で検査する。偽は全員の発達がそろってはいないことを表し、全員の未発達までは要求しない。'),
 'h27cp':('['+SIGNATURE+'] '+STATE,['community','lowerorder','higherorder','reference','start','end'],'同じ区間の観測割当て。非介入の方程式、前件の成立、基準履歴との時点対応を検査する。後件の好都合な介入解を観測として取り直さない。'),
 'h27cq':('['+SIGNATURE+' '+STATE+' d] d',['community','lowerorder','higherorder','reference','start','end','state','point'],'同じモデル解における、基準履歴のこの時点に対応する状況。人物・特徴・重み・比較基準を変えず、全履歴への一対一かつ全射の対応と順序一致を検査する。観測解の対応は基準履歴上で恒等とする。介入を時刻のずらしや時点の欠落で代用しない。'),
}
MEANINGS={
 'r6j7':'同じ固定した全成員・全特徴・重みを使い、渡された真偽プロフィールの二点の距離を合成する。各人・特徴の真偽が異なる重みの総和であり、同じ総件数での交換を相殺しない。',
 'r6ka':'同じ有効な全区間と完全な対象範囲で、渡されたプロフィールとその評価済み条件を用いる漸次的変化。r6j5と同じ固定段階上限・中間状態条件を、内容を指定できる形に一般化する。',
 'r6kb':'前文と同じ固定基準・比較組と、同じ民衆の全心的特徴を保つ。前件の原因側の範囲を完全かつ非空に列挙し、その全員が影響先の民衆に属することを要求する。民衆へ戻る作用の指示をこの同じ共同体へ接続する。',
 'r6kc':'一つのモデル解について、基準履歴から解の履歴への全射・一対一・順序保存を要求し、解の全区間の心的傾向の評価可能性を確認する。原因要因の真偽を、同じ原因側の全員についての既存r6jdの実際の発達内容と照合する。',
 'r6kd':'観測解と指定した比較解の同じ時点・同じ人・同じ特徴で、応答傾向が異なる真偽プロフィールを構成する。その差のプロフィール自体がr6kaで漸次的に変化する。初めからある一定の差や両側に共通する変化だけでは成立しない。',
 'r6ke':'同じ原因側・民衆・比較組で、観測が元の方程式を満たし、原因要因が真で、同じ基準時点を指し、観測された心的経過がr6j5を満たす。真偽双方の非空の全介入解で内容と履歴を照合し、原因要因を偽にした全解との間で差のプロフィールが漸次的に変化することを要求する。各人の必要性、後件の完全な消失、完全媒介は加えない。',
 'r6kf':'同じ共同体・二制度・開始点における後続の反作用経過を、前文の固定基準h26zjで終点ごとの内容にする。第四文の全条件文や政府・尊厳の後半を代用する文ではない。',
}
LIMITS=[
 '同じ集団に育った思考への傾向・促しが、その集団の経験的な心的傾向へ作用を返すという読み。原因側は固定した非空の成員範囲で、影響先の民衆全員と同一であることや各参加者の不可欠性を要求しない。人数の読みは条件文全体の統合時にも明示する。',
 '作用は同じ機構・外生背景の二値構造モデルによる比較として公開する。全介入解で要因とr6jdの内容を照合する。原文が構造方程式や観測データを与えているとはせず、現実の社会的因果を同定した証拠ではない。',
 '原因側全員の発達がそろう場合を真、その連言が成立しない場合を偽とする一つの集団要因で比較する。旧rxsの一人ずつの必要性やrxrの完全媒介を継承しない。偽側でも心的変化や別の原因による変化はあり得る。',
 '観測された経過の変化だけでなく、原因要因が偽の場合との差のプロフィール自体の漸次的変化を要求する。単なる共通の時間変化と一定の既存差は作用の漸進と区別する。始点で差が零とは限らず、発達した二性向そのものが初めから異なることを許す。',
 '基準履歴と各解の全履歴を一対一・全射かつ同順序に対応させる。人物・特徴・正の重み・段階上限は固定し、結果による範囲・単位・時点の変更を許さない。未知の内容を偽に補わない。',
 '全ての偽側の解で観測との差の変化を要求する頑健な比較であり、同じ背景の非決定性だけから作用を作らない。確率的寄与や代替的な実際原因の全理論を尽くすとはしない。前回の有限特徴の粒度と段階上限に関する限定を引き継ぐ。',
 '前件の比喩はgerm-figurative-connectionで保持し、今回の因果比較では対象側r6jdの内容を使う。比喩提示の成立から因果的内容の真理を導かない。Wenn/soの全体量化、行為能力・政府原則・自己利益・機械以上の人間・尊厳・著者注参照は未統合。全文の意味確認文字数は増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def germ():return load_catalog(ROOT,GERM)
@lru_cache(None)
def main_catalog():return load_catalog(ROOT,MAIN)

def definitions():
    pop='k h27b5['+C+']';features='k h27b6['+C+' v person]'
    diff='u[z[c[v profile][v person v feature v left]][c[v profile][v person v feature v right]]]'
    inner='q['+features+']['+ZERO+'][i[subtotal b feature a][k ha[v subtotal k hb[k h27cg['+PAIR+'] k hd['+diff+']]]]]'
    text='d r6j7[community a reference d profile '+PROFILE+' left d right d] b[q['+pop+']['+ZERO+'][i[total b person a][k ha[v total '+inner+']]]].\n'
    hist='i[point d][k h27ch['+C+' v start v end v point]]';order='i[left d right d][k h27ci['+C+' v start v end v left v right]]'
    inside=lambda t:'c[k rlz['+hist+' '+order+' v start v end]][v '+t+']'
    before=lambda l,r:'k h27ci['+C+' v start v end v '+l+' v '+r+']'
    distance=lambda l,r:'k r6j7['+C+' v profile v '+l+' v '+r+']'
    middle=lambda l,r:'g middle d['+both(inside('middle'),before(l,'middle'),before('middle',r),
      *['k hc['+ZERO+' '+d+']' for d in (distance(l,'middle'),distance('middle',r))],
      *['k hc['+d+' '+distance(l,r)+']' for d in (distance(l,'middle'),distance('middle',r))])+']'
    assessed='f point d[y['+inside('point')+'][f person a[y[k r6hd[v person v community v reference]][f feature a[y[k h27b7['+PAIR+']][c[v assessed][v person v feature v point]]]]]]]'
    large=both(inside('left'),inside('right'),before('left','right'),'k hc[k h27cj['+C+'] '+distance('left','right')+']')
    text+='d r6ka[community a reference d start d end d profile '+PROFILE+' assessed '+PROFILE+'] c['+both('k r6jz['+C+']',
      'k ta['+hist+' '+order+']','k h27ch['+C+' v start v end v start]','k h27ch['+C+' v start v end v end]',before('start','end'),assessed,
      'k hc['+ZERO+' k h27cj['+C+']]','k hc['+ZERO+' '+distance('start','end')+']',middle('start','end'),
      'f left d[f right d[y['+large+']['+middle('left','right')+']]]')+'].\n'
    people='k h27cl['+SARGS+' v person]'
    text+='d r6kb['+SCOPE+'] c['+both('e[v reference][k h26zj[]]','k h26zi['+SARGS+']','k r6jz['+C+']',
      'k rcm[k h27ck['+SARGS+'] i[person a]['+people+']]','f person a[y['+people+'][k r6hd[v person v community v reference]]]')+'].\n'
    mapped=lambda state,point:'k h27cq['+ARGS+' '+state+' '+point+']'
    start=mapped('v state','v start');end=mapped('v state','v end')
    history=lambda point:'k h27ch['+C+' v start v end '+point+']'
    mh=lambda point:'k h27ch['+C+' '+start+' '+end+' '+point+']'
    image='g point d['+both(history('v point'),'e['+mapped('v state','v point')+'][v image]')+']'
    onto='f image d[z['+mh('v image')+']['+image+']]'
    pairs=both(history('v left'),history('v right'))
    aligned=both('z[e[v left][v right]][e['+mapped('v state','v left')+']['+mapped('v state','v right')+']]',
      'z['+before('left','right')+'][k h27ci['+C+' '+start+' '+end+' '+mapped('v state','v left')+' '+mapped('v state','v right')+']]')
    premise='f person a[y['+people+'][t[k r6jd[v community v lowerorder v higherorder v person]]['+start+']]]'
    factor='k h27co['+ARGS+']'
    text+='d r6kc['+FIELDS+' state '+STATE+'] c['+both(onto,'f left d[f right d[y['+pairs+']['+aligned+']]]',
      'k r6j3['+C+' '+start+' '+end+']','z[c[v state]['+factor+']]['+premise+']')+'].\n'
    observed='k h27cp['+ARGS+']';on=mapped(observed,'v point');off=mapped('v state','v point')
    profile='i[person a feature a point d][u[z[k r6jy['+PAIR+' '+on+']][k r6jy['+PAIR+' '+off+']]]]'
    checked='i[person a feature a point d]['+both('k r6jx['+PAIR+' '+on+']','k r6jx['+PAIR+' '+off+']')+']'
    text+='d r6kd['+FIELDS+' state '+STATE+'] c[k r6ka['+C+' v start v end '+profile+' '+checked+']].\n'
    variables='k h27cm['+ARGS+']';equations='i[variable a state '+STATE+'][k h27cn['+ARGS+' v variable v state]]'
    mask='i[variable a][e[v variable]['+factor+']]'
    def side(flag,body):return 'k rw['+variables+' '+equations+' '+mask+' i[variable a]['+flag+'] i[state '+STATE+']['+body+']]'
    text+='d r6ke['+FIELDS+'] c['+both('k r6kb['+SARGS+']','k r6j5['+C+' v start v end]',
      'k rz['+variables+' '+factor+']','k ru['+variables+' '+equations+' i[variable a]['+FALSE+'] i[variable a]['+FALSE+'] '+observed+']',
      'c['+observed+']['+factor+']','k r6kc['+ARGS+' '+observed+']',
      'f point d[y['+history('v point')+'][e['+mapped(observed,'v point')+'][v point]]]',
      side(TRUE,'k r6kc['+ARGS+' v state]'),side(FALSE,both('k r6kc['+ARGS+' v state]','k r6kd['+ARGS+' v state]')))+'].\n'
    text+='d r6kf[community a lowerorder a higherorder a start d] e[b end[k r6ke[v community v lowerorder v higherorder k h26zj[] v start v end]]].\n'
    return text

def build():
    catalogs=((parent(),('r6jx','r6jy','r6jz','r6j3','r6j5')),(germ(),('r6jd','h26zi','h26zj')),(main_catalog(),('ru','rw','rz')))
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
    basis=dict(status='same_community_causal_feedback_and_gradual_contrast_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imports.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imports.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
