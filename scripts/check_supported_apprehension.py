"""Check the candidate reading; never replace the full description domain silently."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from unittest.mock import patch
from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts import check_interpreted_depiction as previous
from scripts.compose_supported_apprehension import ROOT,PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,REVIEW,build,basis,review
from scripts.compose_qualified_utterance import closure

REPORT=ROOT/'reports/supported-apprehension-v1.json'
DOMAIN=('person','other','state','second','reason','secondreason','entity')
SCENES=('anchor','imagined','other')
CONTRASTS=('other_person','other_episode','other_anchor','other_reason','other_support_anchor','other_prospect','alias_support')


@lru_cache(maxsize=5)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def restrict(doc,symbols):
    """Instantiate the *actual* stored universal body, only for this diagnostic."""
    node=next(d for d in doc['declarations'] if d['name']=='rvy')['body']
    assert node['kind']=='forall' and node['sort']['kind']=='description'
    instances=[dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],
        body=deepcopy(node['body'])),arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=s))]) for s in symbols]
    assert len(instances)==2
    node.clear();node.update(kind='and',arguments=instances)
    prefix=closure(doc,symbols)
    names={d['name'] for d in prefix}
    doc['declarations']=prefix+[d for d in doc['declarations'] if d['name'] not in names]
    return parse(format_graph(doc,'compact'))


def model(flags,variant='baseline',*,prefix='jl',person='person',episode='state',reason='reason',anchor='anchor',
          prospect='imagined',other='other',second='second',secondreason='secondreason',topic='jltopic',alias='jlalias'):
    experienced,directed,aversive,anticipated,adverse,available,supports=flags
    def experience(p,e,c):
        if variant=='unknown_experience':raise ValueError('Unknown experience')
        return experienced and (p,c)==(person,anchor) and (e==episode or variant=='second_unsupported' and e==second)
    def direction(e,code,c):
        return directed and c==anchor and (e==episode or variant=='second_unsupported' and e==second) and json.loads(code.syntax)==dict(kind='function_ref',symbol=topic)
    def affect(e,c):return aversive and c==anchor and (e==episode or variant=='second_unsupported' and e==second)
    def anticipate(e,c,end):
        return anticipated and c==anchor and ((e,end)==(episode,prospect) or variant=='second_unsupported' and (e,end)==(second,other))
    def harm(p,c):return adverse and p==person and (c==prospect or variant=='second_unsupported' and c==other)
    def access(p,r,c):
        if variant=='unknown_available':raise ValueError('Unknown available reason')
        return available and (p,r,c)==(other if variant=='other_person' else person,reason,other if variant=='other_anchor' else anchor)
    def support(r,code,c,end):
        if variant=='unknown_support':raise ValueError('Unknown support')
        return supports and (r,c,end)==(secondreason if variant=='other_reason' else reason,
            other if variant=='other_support_anchor' else anchor,other if variant in ('other_prospect','other_episode') else prospect) and json.loads(code.syntax)==dict(kind='function_ref',symbol=alias if variant=='alias_support' else topic)
    return {prefix+n:f for n,f in dict(experienced=experience,directed=direction,aversive=affect,
        anticipated=anticipate,adverse=harm,available=access,supports=support).items()}


def values(flags=(True,)*7,*,actual_target=False,actual_harm=False,variant='baseline',indices=None,restricted=True,memoize=True):
    doc=deepcopy(document(EXAMPLE))
    if restricted:doc=restrict(doc,('jltopic','jlalias'))
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    primitives=model(flags,variant)
    def creature(entity,point):
        if variant=='unknown_target':raise ValueError('Unknown target')
        return actual_target and (entity,point)==('entity','anchor')
    primitives.update(jlperson=lambda:'person',jlepisode=lambda:'state',jlanchor=lambda:'anchor',jlcreature=creature,
        jlwings=lambda e,c:(e,c)==('entity','anchor'),jlactualharm=lambda p,c:actual_harm and (p,c)==('person','anchor'))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives,
        max_steps=2_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def expected(flags,target=False,harm=False):
    fear=all(flags[:5]);grounds=all(flags[i] for i in (3,4,5,6));unsupported=fear and not grounds
    return [fear,grounds,unsupported,not unsupported,target,harm,True]


@lru_cache(maxsize=2)
def source_setup(restricted=True):
    doc,expected=previous.setup();doc=deepcopy(doc)
    names={d['name'] for d in doc['declarations']}
    for decl in closure(document(SOURCE),['hzwonly']):
        if decl['name'] not in names:doc['declarations'].append(decl);names.add(decl['name'])
    def replace(node):
        if isinstance(node,dict):
            if node.get('symbol')=='jktarget':node['symbol']='hzwtarget'
            for value in node.values():replace(value)
        elif isinstance(node,list):
            for value in node:replace(value)
    replace(doc['statements'])
    doc['statements'][0]['body']=dict(kind='call',symbol='hzwonly',arguments=doc['statements'][0]['body']['arguments'][1:])
    if restricted:doc=restrict(doc,('hzvshadow','jktarget'))
    return parse(format_graph(doc,'compact')),expected


def source_values(*,fear=True,available=True,supports=True,mapped=True,remaining=True,owned=True,success=True,
                  variant='baseline',indices=(0,1,2,3,4,5),restricted=True):
    fixture=source_setup(restricted)
    def evaluate(doc,**kwargs):
        primitives=kwargs['primitives']
        primitives.update(model((fear,True,True,True,True,available,supports),variant,prefix='hzw',person='speaker',
            episode='a',reason='b',prospect='left',other='right',second='listener',secondreason='other',topic='hzvshadow',alias='jktarget'))
        def mapping(node,author,target,depiction,context):
            if variant=='unknown_mapping':raise ValueError('Unknown mapping')
            return mapped and (node,author,context)==('a','listener','right') and json.loads(target.syntax)==dict(kind='function_ref',symbol='hzwtarget') and json.loads(depiction.syntax)==dict(kind='function_ref',symbol='hzvdepiction')
        primitives['qa']=mapping
        return evaluate_document(doc,**kwargs)
    with patch.object(previous,'setup',return_value=fixture),patch.object(previous,'evaluate_document',side_effect=evaluate):
        return previous.values(mapped=mapped,remaining=remaining,owned=owned,success=success,indices=indices)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Candidate interpretation executed while attributing it')
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def annotation(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='hzwonly')
    primitives.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',hzwannotation=annotation)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=primitives)]


def full_domain_refused():
    for call in (lambda:values(restricted=False,indices=(3,)),lambda:source_values(restricted=False,indices=(0,))):
        try:call()
        except ValueError as error:assert 'description domain' in str(error),str(error)
        else:raise AssertionError('Full description domain was silently limited')
    assert values(restricted=False,indices=(6,))==[True]
    assert source_values(restricted=False,indices=(3,))==[True]
    return True


def alignment():
    result=previous.alignment()
    result.update(definitions=['hzwtarget','hzwonly','hzwattribution'],intended_meaning_open=False,
        intended_meaning_status='explicit_candidate_with_unresolved_basis',figurative_reading_confirmed=False)
    return result


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    for path,expected_data in [(BASIS,basis()),(REVIEW,review())]:assert json.loads((ROOT/path).read_text(encoding='utf-8'))==expected_data
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    matrix=[]
    for flags in product((False,True),repeat=7):
        result=values(flags);assert result==expected(flags),(flags,result)
        matrix.append(dict(flags=flags,result=result))
    actuality=[]
    for grounds,target,harm in product((False,True),repeat=3):
        flags=(True,)*6+(grounds,);result=values(flags,actual_target=target,actual_harm=harm)
        assert result==expected(flags,target,harm)
        actuality.append(dict(bits=[grounds,target,harm],result=result))
    contrasts={name:values(variant=name) for name in CONTRASTS}
    assert all(r==[True,False,True,False,False,False,True] for r in contrasts.values()),contrasts
    assert values(variant='second_unsupported')==[True,True,True,False,False,False,True]
    assert values(variant='unknown_target',indices=(0,1,2,3,6))==[True,True,False,True,True]
    for variant in ('unknown_available','unknown_support','unknown_experience'):
        assert values(variant=variant,indices=(6,))==[True]
        try:values(variant=variant,indices=(3,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown relation became absence')
    assert values(memoize=False)==expected((True,)*7)
    source=[]
    for fear,grounds,mapped,remaining,owned,success in product((False,True),repeat=6):
        result=source_values(fear=fear,supports=grounds,mapped=mapped,remaining=remaining,owned=owned,success=success)
        target=not fear or grounds
        assert result==[mapped and (not success or owned and target and remaining),mapped and target and remaining,owned,True,mapped,target],(fear,grounds,mapped,remaining,owned,success,result)
        source.append(dict(bits=[fear,grounds,mapped,remaining,owned,success],result=result))
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    paths=[PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,REVIEW,'scripts/compose_supported_apprehension.py',
        'scripts/check_supported_apprehension.py','tests/test_supported_apprehension.py','scripts/check_interpreted_depiction.py',
        'scripts/check_qualified_utterance.py','scripts/check_restricted_utterance.py','scripts/check_anchored_ability.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='candidate_reading_with_finite_diagnostics_only',documents=documents,matrix=matrix,
        actuality=actuality,contrasts=contrasts,source_matrix=source,roundtrips=True,full_domain_refused=full_domain_refused(),
        full_domain_verified=False,source_alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},
        unresolved=basis()['unresolved'],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Candidate grounds, independent actuality, source connection and full-domain refusal verified')


if __name__=='__main__':main()
