"""A stated fictional custom: reuse definitions, norms and quoted descriptions."""
from functools import lru_cache
import json
from pathlib import Path
from itertools import product
from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import digest

ROOT=Path(__file__).resolve().parents[1]
FULL='examples/v016/local-reciprocity-custom.noema'
BASIS='data/local-reciprocity-custom-basis-v1.json'
DOC='docs/local-reciprocity-custom-v1.md'

def call(n,*xs):return 'k '+n+'['+' '.join(xs)+']'
def var(n):return 'v '+n
def both(a,b):return 'w['+a+']['+b+']'
def quote(n):return 'r[p '+n+']'
def define(n,args,result,body):return 'd '+n+'['+args+'] '+result+'['+body+'].\n'

PRIMITIVES={
 'aa':(['giver','recipient','object','context'],'本人の意思による物の無償の譲渡。返礼義務や感謝の存在を含めない。'),
 'ab':(['actor','target','context'],'相手へ向けて上体を短く傾ける意図的な身体行為。敬意や謝意の文化的意味を含めない。'),
 'ac':(['community','person','context'],'その場面での共同体の構成員という関係。全人類への規則適用を意味しない。'),
 'ad':(['community','person','action_description','target','context'],'指定共同体の規約の下で、本人が相手に指定された二人の行為型を行う義務を負う関係。行為型は閉じた記述で指定し、実行や内容の真理を要求しない。'),
 'ae':(['community','form_description','meaning_description','context'],'同じ共同体の規約が、二人の行為型を、その同じ二人についての意味内容の表示として取り扱う関係。二つの型を閉じた記述で指定し、両者の実際の成立を要求しない。'),
 'af':(['person','benefactor','context'],'相手から受けた利益を謝意をもって認めている状態。金銭債務や身体動作と区別する。'),
 'ag':([], '例で取り上げる共同体の指示対象。'),
 'ah':([], '例の贈与者の指示対象。'),
 'ai':([], '例の受領者の指示対象。'),
 'aj':([], '例の場面の指示対象。'),
}
MEANINGS={
 'ba':'同じ二人についての上体を傾ける行為を、状況ごとの内容として構成する。',
 'bb':'同じ二人についての利益への謝意を、状況ごとの内容として構成する。',
 'bc':'同じ共同体の構成員二人の間に物の贈与がある場合、受領者が贈与者へbaの行為を行う義務を、その共同体の規約として要求する。',
 'bd':'その共同体でbaの身体行為型が、同じ二人のbbの謝意内容の表示として認められること。',
 'be':'bcの条件付き返礼義務とbdの表示規約の組合せ。例で定義した局所的な返礼作法であり、物の返却・購入代金・実行済みの返礼とは違う。',
 'bf':'選んだ共同体と場面においてbeの作法が成立するかを照会する閉じた条件。',
 'bg':'受領者と贈与者の閉じた記述から、その二人のbaの行為内容の記述を型付きに合成する。内容を実行する操作ではない。',
}

@lru_cache(None)
def build():
    body='''p:
r aa[a a a d] c.
r ab[a a d] c.
r ac[a a d] c.
r ad[a a i[h[a a] e] a d] c.
r ae[a i[h[a a] e] i[h[a a] e] d] c.
r af[a a d] c.
r ag[] a.
r ah[] a.
r ai[] a.
r aj[] d.
'''
    for n,primitive in [('ba','ab'),('bb','af')]:
        body+=define(n,'actor a target a','e','b w['+call(primitive,var('actor'),var('target'),var('w'))+']')
    c,g,r,t,w=map(var,['community','giver','recipient','token','context'])
    condition=both(call('ac',c,g,w),both(call('ac',c,r,w),call('aa',g,r,t,w)))
    rule='y['+condition+']['+call('ad',c,r,quote('ba'),g,w)+']'
    for name in ['token','recipient','giver']:rule='f '+name+' a['+rule+']'
    body+=define('bc','community a context d','c',rule)
    body+=define('bd','community a context d','c',call('ae',c,quote('ba'),quote('bb'),w))
    body+=define('be','community a context d','c',both(call('bc',c,w),call('bd',c,w)))
    body+=define('bf','','c',call('be',call('ag'),call('aj')))
    body+=define('bg','','i[e]','o a['+quote('ba')+'][r[k ai[]] r[k ah[]]]')
    body+='q[k bf[]].\nq[t[k ba[k ai[] k ah[]]][k aj[]]].\nq[e[k bg[]][r[c[p ba][k ai[] k ah[]]]]].\n'
    doc=parse(body)
    basis=dict(status='explicit_fictional_local_custom_example',document=FULL,
               primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],meaning_ja=PRIMITIVES[d['name']][1]) for d in doc['declarations'] if d['kind']=='primitive'},
               definitions=MEANINGS,limitations=['架空の共同体の局所規約として定義する例。現実の民族・宗教・国の慣習や語の全語義を記述したものではない。','条件の前件に該当する贈与がない場合、条件付き義務は空虚に成立し得る。身体行為の実行、謝意の本心、普遍的な道徳義務を補わない。'])
    return {FULL:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def symbol(description):return json.loads(description.syntax)['symbol']

def evaluate(*,gift=True,members=True,norm=True,convention=True,performed=False,unknown=False):
    def obligation(c,person,description,target,w):
        if unknown:raise ValueError('Unknown obligation interpretation')
        return norm and (c,person,symbol(description),target,w)==('a','b','ba','a','now')
    m=dict(aa=lambda g,r,t,w:gift and (g,r,t,w)==('a','b','a','now'),
           ab=lambda p,t,w:performed and (p,t,w)==('b','a','now'),
           ac=lambda c,p,w:members and c=='a' and w=='now',ad=obligation,
           ae=lambda c,f,m,w:convention and (c,symbol(f),symbol(m),w)==('a','ba','bb','now'),
           af=lambda *xs:False,ag=lambda:'a',ah=lambda:'a',ai=lambda:'b',aj=lambda:'now')
    return [r['value'] for r in evaluate_document(parse(build()[FULL]),individuals=('a','b'),situations=('now','other'),primitives=m)]

@lru_cache(None)
def contrasts():
    cases=0
    for gift,members,norm,convention,performed in product((False,True),repeat=5):
        result=evaluate(gift=gift,members=members,norm=norm,convention=convention,performed=performed)
        assert result==[(not(gift and members) or norm) and convention,performed,True]
        cases+=1
    try:evaluate(unknown=True)
    except ValueError as e:assert 'Unknown obligation' in str(e)
    else:raise AssertionError('Unknown interpretation silently accepted')
    return dict(cases=cases+1,custom_separated_from_actual_performance=True,
                membership_and_gift_scope_explicit=True,physical_and_conventional_meanings_distinct=True,
               _constructed_description_identical_to_literal=True,unknown_input_refused=True)

def build_report():
    result=contrasts();catalog=load_catalog(ROOT,BASIS)
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for style in ('compact','full'):
        text=format_graph(catalog.document,style)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==catalog.document
    paths={FULL,BASIS,DOC,'scripts/check_local_custom_example.py','tests/test_local_custom_example.py'}
    paths.update(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'noema').glob('*.py'))
    return dict(status='fictional_cultural_convention_composed_with_existing_language',**result,
                language_syntax_added=False,real_world_cultural_description_claimed=False,
                original_work_semantic_judgments_added=0,
                source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
