"""Index ability profiles by task and connect bodily acquisition and expectation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-falling-depiction.noema'
PARENT_BASIS='data/falling-depiction-basis-v1.json'
FULL='examples/v016/kant-bodily-acquisition.noema'
CORE='examples/v016/bodily-acquisition-core.noema'
LIBRARY='examples/v016/task-indexed-capacity.noema'
BASIS='data/bodily-acquisition-basis-v1.json'
ANNOTATIONS='data/bodily-acquisition-identifiers-v1.json'
GOAL='i[h[a] e]'
PROFILES=[('cases','hzuq','h[a '+GOAL+' d d] c'),('preserved','hzur','h[a '+GOAL+' d d] c'),
    ('opportunity','hzus','h[a '+GOAL+' d] c'),('preferred','hzut','h[a '+GOAL+' d d d] c'),
    ('scope','hzuu','h[a '+GOAL+' a d d] c'),('checked','hzuv','h[a '+GOAL+' a d d] c')]
PRIMITIVES={
 'hzuq':(['person','task','anchor','candidate'],'同じ本人・閉じた活動記述・基準状況について、行使能力の評価に採る機会の候補。別活動の候補を無条件に流用せず、実際に起きた状況とは限らない。'),
 'hzur':(['person','task','anchor','candidate'],'同じ活動の行使能力の評価で、本人側の技能・習慣・身体状態などの基盤が基準から保持される。能力そのものの同一性を仮定せず、将来の取得後の基盤へ置換しない。'),
 'hzus':(['person','task','candidate'],'同じ活動を行う外的な機会が本人に与えられる。技能や成功、規範上の許可とは別の条件。'),
 'hzut':(['person','task','anchor','preferred','other'],'同じ本人・活動記述・基準で、行使能力の評価候補の通常性を厳密に優先する関係。成功する候補だけを後から通常と選び直さない。'),
 'hzuu':(['person','task','method','anchor','execution'],'同じ活動について、基準時点の本人側の基盤を行使する方法の範囲。新たな技能基盤を先に習得する準備計画を、既有の行使方法に数えない。'),
 'hzuv':(['person','task','method','anchor','execution'],'同じ活動・方法・基準・実行状況でhzuuの範囲内外が評価済みである。範囲外と未知を区別する。'),
 'hzv2':(['person','task','anchor','candidate'],'同じ本人が同じ活動の能力を経験から得ると仮定的に見込む候補。活動記述と基準を保持し、実現済みの出来事や全可能性の集合、数値確率とはしない。'),
}
MEANINGS={
 'rqvv':'同じ閉じた活動記述を六つの能力評価入力へ渡し、既存rqvmで評価条件の整合性を調べる。達成内容と記述の対応は呼出側の明示的な契約であり、この一般形が意味同一性を自動判定するものではない。',
 'rqvw':'rqvvと同じ活動・本人・基準に結んだ入力を既存rqvnへ渡し、通常機会での現在の行使能力を判定する。既存の評価不足・準備方法・現在の外的障害の区別を保持する。',
 'hzuw':'同じ本人のzalについて、活動を明示した入力と既存の利用可能方法・結果・選択結果をrqvvへ渡す。知的活動専用のhzsc等を使わない。',
 'hzux':'hzuwと同じ活動・本人・基準・評価入力によるrqvwの行使能力。活動内容は同じ本人のzal、活動記述もzalに固定する。',
 'hzv5':'同じ本人・経験・試行時点でzalを試み、その経験の一つの結果が実際にrqvuの転倒を満たし、その同じ結果時点が取得の終点以前である。早い非転倒の結果と遅い転倒の結果を混ぜない。',
 'hzuy':'同じ本人・取得過程の少数回の経験列をr5へ渡し、各転倒hzv5が終点までにあり、各経験が同じ取得へ寄与する。両端のhzuwが整い、hzuxの能力がない前状態からある後状態へ移る。',
 'hzuz':'指定本人と回数基準の文脈について、hzuyの取得過程が終わる状況の内容。過程を人や見込み候補の間で一つに固定しない。',
 'hzv3':'同じ本人・zal・基準で選ぶ非空の将来候補の全てにhzuzが成立するという見込み。実際の転倒・学習の発生は断言せず、回数の基準は元の文脈に保つ。',
 'hzv4':'同じ学習節fvで、自立的活動の取得見込みfrを身体的活動の取得見込みhzv3で非字義的に提示する。本人を対応させ、両内容の実際の真理や完全同一性は要求しない。',
}
LIMITS=[
 '六つの評価関係と取得見込みを活動記述で区別する。個別の身体技能を一語の未知述語へ置換せず、同じ一般能力条件へ接続するための文脈入力である。',
 '一般形では達成内容と活動記述を別に受ける。呼出側が同じ活動と本人に結ぶ必要があり、身体側ではzal(person)と記述zalを使う。任意の同義な記述への自動移行は行わない。',
 '能力の現在の基盤と、事前に別の基盤を学習する準備方法を区別する。通常性・基盤・方法区分・結果範囲の具体的な評価モデルを原文が一意に指定しているとはしない。',
 '転倒は取得の終点までに完了する一つの同じ結果で判定する。傷害や全結果での転倒、各経験が単独で十分・必要な原因であることは要求しない。',
 '能力の不在から取得への変化という既存の読解を身体側へ構成する。熟達の程度的な改善、身体移動zalの歩行と走行の区別、würden・wohlの語用論の全ては未確定。',
 '身体側と知的活動側は別の内容記述である。比喩の提示が実際の学習を証明することはなく、著者の心理・教育上の主張の実証を言語の完成条件にしない。',
 '既存39文と九単位の意味判断を保ち、学習の比喩帰属を一文加える。部分草案の範囲と全体確認済み587文字は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def additions():
    fields='person a goal e description '+GOAL+' anchor d '+' '.join(n+' '+t for n,_,t in PROFILES)
    fields+=' available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c'
    callbacks=['i[p a a d s d][c[v '+n+'][v p v description v a v s]]' for n in ('cases','preserved')]
    callbacks+=['i[p a s d][c[v opportunity][v p v description v s]]',
        'i[p a a d x d y d][c[v preferred][v p v description v a v x v y]]']
    callbacks+=['i[p a m a a d s d][c[v '+n+'][v p v description v m v a v s]]' for n in ('scope','checked')]
    args='v person v goal v anchor '+' '.join(callbacks)+' v available v outcomes v selected'
    text=''.join('d '+new+'['+fields+'] c[k '+old+'['+args+']].' for new,old in [('rqvv','rqvm'),('rqvw','rqvn')])
    text+=''.join('r '+symbol+'['+typ[2:typ.rfind(']')]+'] c.' for _,symbol,typ in PROFILES)
    profile='v person k zal[v person] r[p zal] v scene '+' '.join('p '+n for _,n,_ in PROFILES)+' p ae p af p ap'
    text+='d hzuw[person a] e[b scene[k rqvv['+profile+']]].d hzux[person a] e[b scene[k rqvw['+profile+']]].'
    text+='''
d hzv5[person a experience a start d end d] c[w[k f5[v person v experience r[p zal] v start]][g finish d[w[k f6[v experience v finish]][w[
 k rqvu[v person v experience v start v finish p dd p dg p ag p la p hzui p hzuj p hzuk p hzul]
][x[e[v finish][v end]][k dd[v finish v end]]]]]]].
d hzuy[person a process a end d context d] c[w[k fm[d[k fh[v process]] v context]][k r5[
 v person v process k fh[v process] p f7 p dd k fi[v process] v end
 i[p a s d][t[k hzuw[v p]][v s]] i[p a s d][t[k hzux[v p]][v s]] p ag p la
 i[p a e a s d][k hzv5[v p v e v s v end]] p fk
]]].
d hzuz[person a context d] e[b end[g process a[k hzuy[v person v process v end v context]]]].
r hzv2[a i[h[a] e] d d] c.
d hzv3[person a] e[b context[k ri[k hzuz[v person v context] v context i[end d][k hzv2[v person r[p zal] v context v end]] p tx]]].
d hzv4[] c[k qh[k fv[] k wa[] r[p fr] r[p hzv3] k wh[]]].
'''
    return text


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzv4[]].');doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['declarations']=closure(doc,['hzv4']);core['statements']=doc['statements'][-1:]
    library=deepcopy(doc);library['declarations']=closure(doc,['rqvv','rqvw','r5']);library['statements']=[]
    added=doc['declarations'][size:];by_name={d['name']:d for d in added}
    basis=dict(status='task_indexed_capacity_and_prospective_bodily_acquisition',document=FULL,library=LIBRARY,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=args,meaning_ja=meaning) for n,(args,meaning) in PRIMITIVES.items()},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/falling-depiction-identifiers-v1.json').read_text(encoding='utf-8'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Task-indexed ability, bodily acquisition and prospective depiction composed',flush=True)


if __name__=='__main__':main()
