"""Separate hypothetical backgrounds from plausibility and learning outcomes."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT='examples/v016/kant-fear-proneness.noema'
PARENT_BASIS='data/fear-proneness-basis-v1.json'
FULL='examples/v016/kant-defeasible-learning.noema'
CORE='examples/v016/defeasible-learning-core.noema'
LIBRARY='examples/v016/defeasible-future.noema'
BASIS='data/defeasible-learning-basis-v1.json'
ANNOTATIONS='data/defeasible-learning-identifiers-v1.json'
MAPPING={'fr':'r2bz','r2ay':'r2ca','r2az':'r2cb','fs':'r2cc','ft':'r2cd','r2bx':'r2ce'}
REMOVED=39
PRIMITIVES={
 'hzyu':(['person','task','anchor','candidate'],'同じ本人・活動記述・基準から、本人がその活動の試みに取り組むという仮定の背景に適合する候補状況。学習の成功・能力取得・著者の予想の正しさで選別しない。未取得のままの経過も候補になり得る。候補の将来への位置付けは別のtxで検査し、現実に試みが起きたとは断言しない。'),
 'hzyv':(['observer','person','task','anchor','preferred','other'],'同じ観察者・対象者・活動記述・基準で、仮定した経過の認識的なもっともらしさを比べる厳密な優先関係。観察者の背景知識や推論に基づく判断であり、取得の真偽を読み取って結果が成功するものを自動的に上位へ置く規則ではない。比較不能な候補を保持する。'),
}
MEANINGS={
 'r2by':'指定した仮定候補の全てが基準自身とは異なる将来状況として位置付けられ、rqt4の整合した優先順序における非空の極小候補すべてで内容が成立する。劣後した候補の不成立を許す。現在の内容の真理、全候補での成功、数値確率とは区別する。',
 'r2bz':'同じ本人の知的活動bbの試行背景hzyuと、著者waによる同じ背景のもっともらしさhzyvを分け、少数回の不成功経験から能力を得るfqをr2byへ渡す。回数基準は元の文脈に保持する。',
 'r2ca':'同じ本人の身体活動zalについて、試行背景と著者のもっともらしさを分け、少数回の転倒から能力を得る既存r2axをr2byへ渡す。知的側とは活動記述を区別し、実現や真偽の一致を要求しない。',
 'r2cb':'学習節fvで、同じ本人の知的な取得見込みr2bzを身体的な取得見込みr2caとして非字義的に提示する。著者と文脈を保ち、引用した見込みを事実として実行しない。',
 'r2cc':'非空の同じ基準の対象範囲djに属する全員についてr2bzの見込みを述べる。仮定候補ごとに対象者を選び直さない。',
 'r2cd':'著者に危険の程度e4と学習の見込みr2ccを帰属し、後者を前者の理由とする談話関係と本文順を保持する。見込みから安全の論理的含意は導かない。',
 'r2ce':'恐れやすさ・回避頻度・期待背景の既存内容を保持し、学習の理由にr2cdの新しい見込みを接続する。',
}
LIMITS=[
 'würden ... wohlを、試みを続ける仮定について著者が見込む、反証され得る推量として読む。もっともらしい仮定での成立を採用し、語句から数値確率、現実の履歴、無条件の必然性を補わない。',
 '将来への位置付けは、経験の後に能力を得るという文脈と既存txで明示する。würdeという形だけが未来時制を意味するとはしない。',
 'endlichは少数回の経験を経た終点での取得として読む。既存r4/r5の順序・開始時の能力欠如・終点での能力保有を保持し、長い期間や無限の反復を追加しない。',
 '仮定背景hzyuと認識的な優先hzyvは別の解釈入力である。前者を成功例だけに絞ったり、後者を取得結果から自動生成したりすることを正当化しない。原著者の学習予測を経験的に実証する形式ではない。',
 '知的活動と身体活動の候補は、同じ本人と基準に結ぶが、それぞれの活動記述を持つ。二つの実際の履歴や因果関係を同一視しない。',
 '旧第39文の身体取得見込みhzv4は、後の旧第50文で現在の能力・転倒定義へ改訂済みのため、本文から取り除く。宣言と過去の文書は保持し、旧第50文の描写を更新して残す。',
 '末尾一文と段落全体の通し判断は別に行う。今回だけで新たな意味確認済み分量は加算しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def new_index(index):
    assert index!=REMOVED
    return index-(index>REMOVED)


def reindex_binding(binding):
    out=deepcopy(binding)
    for row in out['statements']:row['index']=new_index(row['index'])
    return out


def definitions():
    text='''
d r2by[content e anchor d candidates h[d] c preferred h[d d] c later h[d d] c] c[
 w[f scene d[y[c[v candidates][v scene]][w[u[e[v anchor][v scene]]][c[v later][v anchor v scene]]]]][
 k rqt4[v candidates v preferred i[scene d][t[v content][v scene]]]
]].
r hzyu[a i[h[a] e] d d] c.r hzyv[a a i[h[a] e] d d d] c.
'''
    for name,goal,content in [('r2bz','bb','fq'),('r2ca','zal','r2ax')]:
        text+='d '+name+'[person a] e[b anchor[k r2by[k '+content+'[v person v anchor] v anchor '+\
            'i[scene d][k hzyu[v person r[p '+goal+'] v anchor v scene]] '+\
            'i[first d last d][k hzyv[k wa[] v person r[p '+goal+'] v anchor v first v last]] p tx]]].'
    return text


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    size=len(doc['declarations']);doc=parse(format_graph(doc,'compact')+definitions())
    for name in ('r2az','fs','ft','r2bx'):
        row=replace_symbols(deepcopy(old.entries[name]['declaration']),MAPPING)
        row['name']=MAPPING[name];doc['declarations'].append(row)
    assert statements[39]['body']['symbol']=='hzv4' and statements[50]['body']['symbol']=='r2az'
    doc['statements']=[replace_symbols(s,MAPPING) if i in (37,50) else deepcopy(s) for i,s in enumerate(statements) if i!=REMOVED]
    doc=parse(format_graph(doc,'compact'));core=deepcopy(doc)
    core.update(declarations=closure(doc,['r2ce','r2cb']),statements=[doc['statements'][37],doc['statements'][49]])
    library=deepcopy(doc);library.update(declarations=closure(doc,['r2by']),statements=[])
    added=doc['declarations'][size:];by_name={d['name']:d for d in added};assert len(added)==9
    basis=dict(status='hypothetical_background_and_learning_plausibility_separated',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=args,meaning_ja=meaning)
            for n,(args,meaning) in PRIMITIVES.items()},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/fear-proneness-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p,body in build().items():write_exact(ROOT/p,body)
    print('Learning prospect separated; redundant old statement 39 removed; 51 statements',flush=True)


if __name__=='__main__':main()
