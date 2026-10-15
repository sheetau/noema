"""Check guaranteed-goal improvement and nonfactive self-benefit appraisal."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,evaluate_document
from noema.script import transcribe
from scripts.compose_self_benefit import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,BENEFIT,build,basis,reading_review
from scripts.compose_restricted_utterance import primitive
from scripts.compose_qualified_utterance import closure
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts import check_political_consequence as previous
from scripts import check_thinking_disposition as thinking

REPORT=ROOT/'reports/self-benefit-v1.json'
GOALS=('first','second')
SCENES=('now','on','off','extra')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8');args=[]
    for name,sort in BENEFIT:
        if name=='policy':args.append('r[p jupolicy]');continue
        provider=not sort.startswith('h[')
        text+=primitive('ju'+name,'h[] '+sort if provider else sort)
        args.append('k ju'+name+'[]' if provider else 'p ju'+name)
    text+='r jurealized[d] c.d jupolicy[bindings j[a]] e[b point[k jurealized[v point]]].'
    return parse(text+''.join('q[k '+name+'['+' '.join(args)+']].' for name in ('rx6','rx7')))


def values(off=1,on=3,*,variant='baseline',memoize=True):
    catalogue=() if variant=='empty_goals' else GOALS+('first',) if variant=='duplicate_goals' else GOALS[:1] if variant=='omitted_goal' else GOALS
    def outcomes(actor,policy,sign,context,outcome):
        if variant=='unknown_outcomes':raise ValueError('Unknown outcome candidates')
        if (actor,context)!=('actor','now') or not thinking.code_is(policy,'jupolicy'):return False
        if variant=='empty_on' and sign:return False
        if variant=='empty_off' and not sign:return False
        if variant=='mixed_on' and sign and outcome=='extra':return True
        return outcome==('on' if sign else 'off')
    def holds(beneficiary,goal,point):
        if variant=='unknown_goals':raise ValueError('Unknown goal satisfaction')
        if beneficiary!='beneficiary' or goal not in GOALS:return False
        mask=on if point=='on' else off
        return bool(mask&(1<<GOALS.index(goal)))
    def classified(beneficiary,goal,point):
        if variant=='unknown_classification':raise ValueError('Unknown goal assessment')
        return (beneficiary=='beneficiary' and goal in GOALS and point in SCENES
            and not (variant=='unreviewed_off' and point=='off'))
    p=dict(arithmetic(),juactor=lambda:'actor',jubeneficiary=lambda:'beneficiary',jucontext=lambda:'now',
        jugoals=lambda:SequenceValue(catalogue,'"individual"'),juscope=lambda goal:variant!='empty_goals' and goal in GOALS,
        juholds=holds,juclassified=classified,juoutcomes=outcomes,
        jurealized=lambda point:point in ('on','extra') and variant!='wrong_realization')
    doc=fixture();p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,GOALS+('actor','beneficiary'),SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(previous.source_fixture());old=doc['statements'];doc['statements']=[]
    names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iatschema','iatbenefit']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    doc=parse(format_graph(doc,'compact')+'r jppolicy[d] c.r juanchor[] d.')
    declared=next(d for d in doc['declarations'] if d['name']=='jppolicy')
    doc['declarations'].remove(declared);doc['declarations'].insert(0,declared)
    policy=next(d for d in doc['declarations'] if d['name']=='jpnew')
    treatment=policy['body']['function']['arguments'][-1]
    treatment['body']=dict(kind='call',symbol='jppolicy',arguments=[dict(kind='variable',name=treatment['parameters'][-1]['name'])])
    queries='''
q[k iatappraisal[k jpactor[] r[p jpnew] k juanchor[]]].
q[k iatbenefit[k jpactor[] k jpactor[] r[p jpnew] k juanchor[] k juanchor[]]].
q[k iatbenefit[k jpactor[] k jpactor[] r[p jpnew] k juanchor[] k wh[]]].
'''
    doc=parse(format_graph(doc,'compact')+queries)
    for index in (3,4):
        query=deepcopy(old[index]);query['body']['symbol']='iatschema';doc['statements'].append(query)
    return doc


def source_values(*,variant='baseline',indices=(0,1),calls=None):
    p,domain,scenes=previous.source_model()
    goals=('topicone','topictwo')
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    def catalogue(beneficiary,anchor):
        log('goals',beneficiary,anchor)
        return SequenceValue(goals if (beneficiary,anchor)==('government','political') else (), '"individual"')
    def signature(assessor,actor,beneficiary,policy,recipe,context):
        expected='person' if variant=='other_beneficiary' else 'government'
        return (assessor,actor,beneficiary,context)==('government','government',expected,'political') and thinking.code_is(
            policy,'jpold' if variant=='other_policy' else 'jpnew') and thinking.code_is(recipe,'iatbenefit',1)
    def views(*args):
        log('view',*args)
        if variant=='unknown_views':raise ValueError('Unknown judgment candidates')
        return variant!='empty_views' and signature(*args[:-1]) and args[-1]=='outside'
    def awareness(*args):
        log('awareness',*args)
        return variant!='unrecognized' and signature(*args)
    def outcomes(actor,policy,sign,context,outcome):
        log('outcome',actor,policy,sign,context,outcome)
        if variant=='unknown_outcomes':raise ValueError('Unknown prospective outcomes')
        if actor!='government' or not thinking.code_is(policy,'jpnew'):return False
        if context not in ('outside','political'):return False
        if variant=='empty_off' and not sign:return False
        if variant=='mixed_on' and sign and context=='outside' and outcome=='normchanged':return True
        return outcome==('normbase' if context=='outside' and sign else 'normchanged' if sign else 'normkept')
    def holds(beneficiary,goal,point):
        if variant=='unknown_goal':raise ValueError('Unknown prospective goal')
        if beneficiary!='government' or goal not in goals:return False
        if goal=='topicone':return not (variant=='goal_exchange' and point=='normbase')
        return (point=='normbase' and variant!='no_benefit') or (point=='normchanged' and variant=='actual_benefit')
    def classified(beneficiary,goal,point):
        if variant=='unknown_review':raise ValueError('Unknown prospective assessment')
        return beneficiary=='government' and goal in goals and not (variant=='unreviewed_off' and point=='normkept')
    p.update(juanchor=lambda:'political',jppolicy=lambda point:point in ('normbase','normchanged'),
        iatgoals=catalogue,iatscope=lambda beneficiary,anchor,goal:(beneficiary,anchor)==('government','political') and goal in goals,
        iatholds=holds,iatclassified=classified,iatoutcomes=outcomes,iatviews=views,iatawareness=awareness)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,domain,scenes,budget=60_000_000)


def attribution(path=CORE):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'node',wa=lambda:'author',iagscope=lambda:'scope',wh=lambda:'end',
        iatreport=lambda n,a,c,s,t:(n,a,s,t)==('node','author','scope','end') and thinking.code_is(c,'iatschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


def alignment():
    review=reading_review()
    return dict(unit=review['source_unit'],text_sha256=review['source_sha256'],status='explicit_interpretive_annotation',
        definitions=['iatbenefit','iatappraisal','iatschema','iatattribution'],adds_new_text_coverage=False,
        semantic_completion=False,self_benefit_appraisal_connected=True,dignity_content_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==reading_review()
    for off,on in product(range(4),repeat=2):assert values(off,on)==[True,off&~on==0 and off!=on]
    assert values(memoize=False)==values()
    assert source_values()==[True,False]
    assert source_values(indices=(3,))==[True]
    for path in (CORE,SOURCE):assert attribution(path)==[True]
    parent,child=document(PARENT),document(SOURCE)
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations'] and child['statements'][:-1]==parent['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,REVIEW,UNITS,'scripts/compose_self_benefit.py','scripts/check_self_benefit.py',
        'tests/test_self_benefit.py','scripts/check_political_consequence.py','scripts/check_caused_choice.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='self_benefit_judgment_connected_without_asserting_actual_benefit',documents=documents,
        guarantee_comparisons=16,roundtrips=True,source_alignment=alignment(),limitations=basis()['limitations'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Nonfactive self-benefit appraisal checked; dignity and full source equivalence remain incomplete')


if __name__=='__main__':main()
