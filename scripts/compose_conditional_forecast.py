"""Keep the projected undertaking inside the payment-capacity supposition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-scoped-attitude.noema'
PARENT_BASIS='data/scoped-attitude-basis-v1.json'
FULL='examples/v016/kant-conditional-forecast.noema'
CORE='examples/v016/conditional-forecast-core.noema'
LIBRARY='examples/v016/joint-conditional-consequences.noema'
BASIS='data/conditional-forecast-basis-v1.json'
ANNOTATIONS='data/conditional-forecast-identifiers-v1.json'
MEANINGS={
 'rqxg':'非空の指定仮定範囲の全状況について、同じ本人の前件が成立するなら、同じ本人・同じ状況で二つの後件がともに成立する。後件の一方を仮定範囲外の現在へ移さない。前件の現実の成立や、その逆方向の含意は要求しない。',
 't3':'同じ仮定上の人物について、選んだ非空の仮定状況s2の各状況で支払能力tpがあるなら、本人の思考なしの達成tqと、その状況を基準とする他者の引受けの見込みt2がともに成立する。後半を支払える仮定に従属させる読み。支払能力がない状況や仮定外の現在に、引受けの見込みを追加しない。',
}

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)

def build():
    old=parent();doc=deepcopy(old.document)
    assert 'rqxg' not in old.entries
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='t3')
    prefix=deepcopy(doc);prefix.update(declarations=doc['declarations'][:at],statements=[])
    text='''d rqxg[person a premise h[a] e first h[a] e second h[a] e cases h[d] c] c[
 k rc[v person v premise i[who a][b scene[w[t[c[v first][v who]][v scene]][t[c[v second][v who]][v scene]]]] v cases]
].
d t3[person a] e[b context[
 k rqxg[v person p tp p tq p t2 i[scene d][k s2[v person v context v scene]]]
]].'''
    parsed=parse(format_graph(prefix,'compact')+text)
    doc['declarations']=parsed['declarations']+doc['declarations'][at+1:]
    doc=parse(format_graph(doc,'compact'))
    basis=dict(status='forecast_scoped_with_payment_capacity',document=FULL,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,primitives={},definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['セミコロン後の見込みを支払能力の仮定内へ置く明示的な読みであり、唯一の文法解析の証明ではない。',
            '支払能力・思考・仕事の語義、nurとschonの談話作用、代行の名詞と第二段落全体の確認は残る。',
            '条件が真でも、支払える仮定例が存在するとは限らない。現在の支払い・予想・履行を断言しない。'],
        unresolved=[dict(basis=r['basis'],historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n=d['name'];meaning=MEANINGS.get(n,old.entries.get(n,{}).get('meaning_ja'))
        if d['kind']=='primitive':basis['primitives'][n]=dict(parameters=d['parameters'],result=d['result'],arguments=old.entries[n]['arguments'],meaning_ja=meaning)
        else:basis['definitions'][n]=meaning
    core=deepcopy(doc);core['statements']=[doc['statements'][5]]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqxg']),statements=[])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/scoped-attitude-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

def main():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)
    print('Conditional forecast composed',flush=True)

if __name__=='__main__':main()
