"""Compare dynamic and compiled claims, including the full appraisal pipeline."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.script import transcribe
from scripts.compose_closed_claim_policies import ROOT,PARENT,LIBRARY,SOURCE,CORE,EXAMPLE,BASIS,build,basis,example,definitions
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is,forbidden
from scripts.check_apparent_liberty import UNITS
from scripts import check_self_benefit as appraisal
from scripts import check_political_consequence as political

REPORT=ROOT/'reports/closed-claim-policies-v1.json'
SCENES=('now','low','high')
DOMAIN=('source','actor','office','person','other','first','second')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=8)
def fixture(names=('jvone','jvtwo')):return example((ROOT/LIBRARY).read_text(encoding='utf-8'),names)


def values(norms=(3,3,3),fulfilled=3,*,names=('jvone','jvtwo'),variant='baseline',memoize=True):
    def norm(source,actor,office,target,bindings,polarity,point):
        expected=('actor','other') if variant=='other_person' else ('actor','person')
        if (source,actor,office)!=('source','actor','office') or bindings.items!=expected or not polarity:return False
        mask=norms[SCENES.index(point)]
        return code_is(target,'jvone') and bool(mask&1) or code_is(target,'jvtwo') and bool(mask&2)
    def content(claim,actor,person,point):
        return actor=='actor' and person=='person' and bool(fulfilled&(1 if claim=='first' else 2))
    p=dict(arithmetic(),**{'jv'+n:(lambda n=n:n) for n in ('source','actor','office','person','first','second')},
        jvnow=lambda:'now',jvscope=lambda person:person=='person' and variant!='wrong_scope',
        jvcases=lambda point:variant!='empty_cases' and point in ('low','high'),jvcontent=content,jvrequired=norm)
    doc,_=fixture(names);p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(appraisal.source_fixture());statements,doc['statements']=doc['statements'],[]
    doc,trace=example(format_graph(doc,'compact')+definitions())
    doc['statements']=statements
    wrapper=next(d for d in doc['declarations'] if d['name']=='jvpolicy')
    target=next(d for d in doc['declarations'] if d['name']=='jpnew')
    target['body']=deepcopy(wrapper['body'])
    def norm_alias(value):
        if isinstance(value,dict):
            if value.get('kind')=='function_ref' and value.get('symbol')=='jvrequired':value['symbol']='h7k'
            for item in value.values():norm_alias(item)
        elif isinstance(value,list):
            for item in value:norm_alias(item)
    norm_alias(target['body'])
    doc['declarations'].remove(target);doc['declarations'].append(target)
    return parse(format_graph(doc,'compact')),trace


def source_values(*,variant='baseline',indices=(0,1,3),calls=None):
    p,domain,scenes=political.source_model()
    old=p['h7k'];goals=('topicone','topictwo')
    domain+=tuple(x for x in ('first','second') if x not in domain)
    def norm(source,actor,office,target,bindings,polarity,point):
        if calls is not None:calls.append(('norm',target,bindings.items,point))
        if code_is(target,'jvone') or code_is(target,'jvtwo'):
            if variant=='missing_requirement' and code_is(target,'jvtwo'):return False
            return (source,actor,office)==('norm','government','office') and bindings.items==('government','person') and polarity
        return old(source,actor,office,target,bindings,polarity,point)
    def content(claim,actor,person,point):
        if calls is not None:calls.append(('content',claim,actor,person,point))
        return (actor,person)==('government','person') and point in ('normbase','normchanged') and not (variant=='missing_fulfillment' and claim=='second')
    def signature(assessor,actor,beneficiary,policy,recipe,context):
        return (assessor,actor,beneficiary,context)==('government','government','government','political') and code_is(policy,'jpnew') and code_is(recipe,'iatbenefit',1)
    def outcomes(actor,policy,sign,context,outcome):
        if actor!='government' or not code_is(policy,'jpnew') or context not in ('outside','political'):return False
        return outcome==('normbase' if sign and context=='outside' else 'normchanged' if sign else 'normkept')
    p.update(jvsource=lambda:'norm',jvactor=lambda:'government',jvoffice=lambda:'office',jvperson=lambda:'person',
        jvfirst=lambda:'first',jvsecond=lambda:'second',jvnow=lambda:'political',jvscope=lambda person:person=='person',
        jvcases=lambda point:point in ('normbase','normchanged'),jvcontent=content,jvrequired=norm,h7k=norm,
        juanchor=lambda:'political',jppolicy=forbidden,
        iatgoals=lambda person,anchor:SequenceValue(goals if (person,anchor)==('government','political') else (), '"individual"'),
        iatscope=lambda person,anchor,goal:(person,anchor)==('government','political') and goal in goals,
        iatholds=lambda person,goal,point:person=='government' and (goal=='topicone' or goal=='topictwo' and point=='normbase'),
        iatclassified=lambda person,goal,point:person=='government' and goal in goals,
        iatoutcomes=outcomes,iatviews=lambda *args:signature(*args[:-1]) and args[-1]=='outside',iatawareness=signature)
    doc,_=source_fixture();doc=deepcopy(doc);doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,domain,scenes,budget=60_000_000)


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['ryg','ryh','ryi'],adds_new_text_coverage=False,semantic_completion=False,
        rank_zero_policy_bridge_demonstrated=True,dignity_content_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for norms in product(range(4),repeat=3):assert values(norms)==[norms==(3,3,3)]*2+[True]
    for fulfilled in range(4):assert values(fulfilled=fulfilled)==[fulfilled==3]*2+[True]
    assert values(memoize=False)==values()
    assert source_values()==[True,False,True]
    parent,child=document(PARENT),document(SOURCE)
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations'] and child['statements']==parent['statements']
    _,trace=fixture()
    paths=[PARENT,LIBRARY,SOURCE,CORE,EXAMPLE,BASIS,UNITS,'scripts/compose_closed_claim_policies.py','scripts/check_closed_claim_policies.py',
        'tests/test_closed_claim_policies.py','tests/test_constructed_specialization.py','noema/constructed_specialization.py',
        'scripts/check_self_benefit.py','scripts/check_political_consequence.py','scripts/check_caused_choice.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='closed_claims_specialized_and_composed_with_nonfactive_appraisal',documents=documents,
        norm_profiles=64,disquotations_removed=trace.disquotations_removed,literal_fold_steps=trace.literal_fold_steps,
        source_alignment=alignment(),roundtrips=True,limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Rank-zero claim policies verified; actual dignity criteria remain incomplete')


if __name__=='__main__':main()
