"""Verify described targets without existential or factual import into affect."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_described_apprehension import ROOT,LIBRARY,EXAMPLE,BASIS,REVIEW,build,basis,review

REPORT=ROOT/'reports/described-apprehension-v1.json'
DOMAIN=('person','other','state','second','entity')
SCENES=('anchor','imagined','safe')


@lru_cache(maxsize=1)
def document():return parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))


def values(flags=(True,True,True,True,True),*,actual_target=False,actual_harm=False,variant='baseline',indices=None,memoize=True):
    experienced,directed,aversive,anticipated,harmful=flags;doc=deepcopy(document())
    seq=doc['statements'][2]['body']['arguments'][1]
    items=seq['items']
    if variant=='reverse_topics':seq['items']=list(reversed(items))
    if variant=='repeat_topics':seq['items']=[items[0],items[0],items[1]]
    if variant=='alias_only':seq['items']=[items[1]]
    if variant=='empty_topics':seq['items']=[]
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    def experience(person,state,point):
        if variant=='unknown_experience':raise ValueError('Unknown experience')
        return experienced and (person,state,point)==('other' if variant=='other_experiencer' else 'person','state','anchor')
    def direction(state,code,point):
        if variant=='unknown_direction':raise ValueError('Unknown directed description')
        return directed and (state,point)==('second' if variant=='split_episode' else 'state','safe' if variant=='other_direction_context' else 'anchor') and json.loads(code.syntax)==dict(kind='function_ref',symbol='jxalias' if variant=='alias_attitude' else 'jxtopic')
    def affect(state,point):
        return aversive and (state,point)==('second' if variant=='other_affect_episode' else 'state','safe' if variant=='other_affect_context' else 'anchor')
    def prospect(state,anchor,result):
        return anticipated and (state,anchor,result)==('second' if variant=='other_prospect_episode' else 'state',
            'safe' if variant=='other_prospect_context' else 'anchor','imagined')
    def adverse(person,point):
        if variant=='unknown_adverse':raise ValueError('Unknown disadvantage')
        if point=='anchor':return actual_harm and person=='person'
        return harmful and (person,point)==('other' if variant=='other_harmed_person' else 'person','safe' if variant=='split_outcome' else 'imagined')
    def creature(entity,point):
        if variant=='unknown_target':raise ValueError('Unknown target interpretation')
        return actual_target and (entity,point)==('entity','anchor')
    model=dict(jxperson=lambda:'person',jxanchor=lambda:'anchor',jxexperienced=experience,jxdirected=direction,
        jxaversive=affect,jxanticipated=prospect,jxadverse=adverse,jxcreature=creature,
        jxwings=lambda entity,point:variant!='missing_wings' and (entity,point)==('entity','anchor'))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=1_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def expected(flags,actual_target=False,actual_harm=False):
    fear=all(flags)
    return [fear,False,not fear,actual_target,actual_target,True,True,actual_harm]


def lower_rank_refused():
    doc=deepcopy(document());doc['statements']=[]
    # rvo explicitly evaluates a rank-zero description, so its call cannot be
    # hidden inside another rank-zero quotation.
    text=format_graph(doc,'compact')
    expr='k rvo[r[p jxtopic] k jxanchor[]]'
    try:parse(text+'q[e[r['+expr+']][r['+expr+']]].')
    except ValueError as error:assert 'strictly lower ranks' in str(error)
    else:raise AssertionError('Same-rank evaluation was hidden in a quote')
    parse(text+'q[e[r b['+expr+']][r b['+expr+']]].')
    return True


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==review()
    matrix=[]
    for bits in product((False,True),repeat=7):
        flags=bits[:5];target,harm=bits[5:];result=values(flags,actual_target=target,actual_harm=harm)
        assert result==expected(flags,target,harm),(bits,result)
        matrix.append(dict(bits=list(bits),result=result))
    contrasts={}
    for name in ('other_experiencer','split_episode','other_direction_context','other_affect_episode','other_affect_context',
                 'other_prospect_episode','other_prospect_context','other_harmed_person','split_outcome'):
        result=values(variant=name);assert result==[False,False,True,False,False,True,True,False],(name,result);contrasts[name]=result
    for name in ('reverse_topics','repeat_topics'):
        result=values(variant=name);assert result==expected((True,)*5);contrasts[name]=result
    for name in ('alias_only','empty_topics'):
        result=values(variant=name);assert result==[True,False,True,False,False,True,True,False];contrasts[name]=result
    assert values(variant='alias_attitude')==[False,True,False,False,False,True,True,False]
    assert values(actual_target=True,variant='missing_wings')==expected((True,)*5)
    assert values(variant='unknown_target',indices=(0,1,2,5,6))==[True,False,False,True,True]
    try:values(variant='unknown_target',indices=(3,))
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown target was silently treated as nonexistent')
    for name in ('unknown_experience','unknown_direction','unknown_adverse'):
        assert values(variant=name,indices=(5,))==[True]
        for index in (0,2):
            try:values(variant=name,indices=(index,))
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError('Unknown state was silently treated as absence')
    assert values(memoize=False)==expected((True,)*5)
    paths=[LIBRARY,EXAMPLE,BASIS,REVIEW,'scripts/compose_described_apprehension.py','scripts/check_described_apprehension.py',
        'tests/test_described_apprehension.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='described_aversive_anticipation_not_source_translation',documents=documents,
        new_definitions=3,new_library_primitives=0,matrix=matrix,contrasts=contrasts,roundtrips=True,
        lower_rank_refused=lower_rank_refused(),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_ranges_added=False,limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Aversive anticipation, description identity, scoped negation and actuality verified')


if __name__=='__main__':main()
