"""Check that the mapped interpretation, not an unrelated content, is evaluated."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from unittest.mock import patch
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts import check_qualified_utterance as previous
from scripts.compose_qualified_utterance import closure
from scripts.compose_interpreted_depiction import ROOT,PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,OPTICS,AFFECT,build,basis

REPORT=ROOT/'reports/interpreted-depiction-v1.json'
UNITS='artifacts/written-units-v1/kant-1784.json'


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def generic_values(mapped=True,target=True,arbitrary=True,variant='baseline',indices=(0,1,2)):
    doc=deepcopy(document(EXAMPLE));doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args):raise AssertionError('Depiction was evaluated')
    def truth(person,point):
        if variant=='unknown_target':raise ValueError('Unknown interpretation')
        return target and (person,point)==('other' if variant=='other_person' else 'person','mapping' if variant=='other_anchor' else 'anchor')
    def mapping(node,author,goal,picture,point):
        return mapped and (node,author,point)==('other' if variant=='other_node' else 'node','other' if variant=='other_author' else 'author','anchor' if variant=='other_mapping_context' else 'mapping') and json.loads(goal.syntax)==dict(kind='function_ref',symbol='jkdepiction' if variant=='reversed_mapping' else 'jktarget') and json.loads(picture.syntax)==dict(kind='function_ref',symbol='jktarget' if variant=='reversed_mapping' else 'jkdepiction')
    model=dict(jknode=lambda:'node',jkauthor=lambda:'author',jkperson=lambda:'person',jkcontext=lambda:'mapping',jkanchor=lambda:'anchor',
        jktruth=truth,jkpictured=forbidden,jkarbitrary=lambda point:arbitrary,qa=mapping)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','person','other'),situations=('mapping','anchor','other'),primitives=model)]


@lru_cache(maxsize=8)
def setup(speaker=True,context=True,variant='baseline'):
    doc,expected=previous.setup(speaker,context,variant);doc=deepcopy(doc);doc['statements']=[]
    names={d['name'] for d in doc['declarations']}
    for decl in closure(document(SOURCE),['hzvonly','rvo']):
        # Retain the previous fixture's concrete quoted speaker references.
        if decl['name'] not in names:doc['declarations'].append(decl);names.add(decl['name'])
    text=format_graph(doc,'compact')+'r jktruth[a d] c.d jktarget[person a] e[b point[k jktruth[v person v point]]].'
    expr='k hzvonly[r[p jktarget] p jzcriterion k juanchor[]]'
    qs=[expr,'k hzvcondition[r[p jktarget] p jzcriterion k juperson[] k juanchor[]]',
        't[k h4l[k juperson[]]][k juanchor[]]','e[r c['+expr+']][r c['+expr+']]',
        'k qh[k hztnode[] k wa[] r[p jktarget] r[p hzvdepiction] k wh[]]',
        't[k jktarget[k juperson[]]][k juanchor[]]','t[k hzvdepiction[k juperson[]]][k juanchor[]]',
        'k rvo[r[p hzvshadow] k juanchor[]]']
    return parse(text+''.join('q['+q+'].' for q in qs)),expected


def values(*,mapped=True,target=True,remaining=True,owned=True,success=True,literal_fear=True,
           speaker=True,hearers=True,context=True,variant='baseline',indices=(0,1,2,3,4,5,6),memoize=True):
    fixture=setup(speaker,context,variant)
    def evaluate(doc,**kwargs):
        model=kwargs['primitives']
        def truth(person,point):
            if variant=='unknown_target':raise ValueError('Unknown interpretation')
            return target and (person,point)==('other' if variant=='other_target_person' else 'speaker','left' if variant=='other_target_anchor' else 'anchor')
        def mapping(node,author,goal,picture,point):
            if variant=='unknown_mapping':raise ValueError('Unknown figurative mapping')
            return mapped and (node,author,point)==('b' if variant=='other_node' else 'a','other' if variant=='other_author' else 'listener','left' if variant=='other_mapping_context' else 'right') and json.loads(goal.syntax)==dict(kind='function_ref',symbol='hzvdepiction' if variant=='reversed_mapping' else 'jktarget') and json.loads(picture.syntax)==dict(kind='function_ref',symbol='jktarget' if variant=='reversed_mapping' else 'hzvdepiction')
        def experienced(person,state,point):
            if variant=='unknown_literal_fear':raise ValueError('Unknown literal fear')
            return literal_fear and (person,state,point)==('speaker','a','anchor')
        def directed(state,code,point):
            return (state,point)==('a','anchor') and json.loads(code.syntax)==dict(kind='function_ref',symbol='hzvshadow')
        def optical(*args):raise ValueError('Unknown optical interpretation')
        model.update(jktruth=truth,qa=mapping,hztnode=lambda:'a',wa=lambda:'listener',wh=lambda:'right',
            hzvexperienced=experienced,hzvdirected=directed,hzvaversive=lambda state,point:(state,point)==('a','anchor'),
            hzvanticipated=lambda state,anchor,end:(state,anchor,end)==('a','anchor','left'),
            hzvadverse=lambda person,point:(person,point)==('speaker','left'))
        for name in ('source','blocker','contains','emits','route','otherwiseclear','intercepts','opaque'):model['hzv'+name]=optical
        return evaluate_document(doc,**kwargs)
    with patch.object(previous,'setup',return_value=fixture),patch.object(previous,'evaluate_document',side_effect=evaluate):
        return previous.values(owned=owned,remaining=remaining,success=success,speaker=speaker,hearers=hearers,context=context,
            variant=variant,indices=indices,memoize=memoize)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Interpretation or depiction executed during attribution')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def annotation(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='hzvonly')
    model.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',hzvannotation=annotation)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=model)]


def lower_rank_refused():
    for doc,index,rank in [(deepcopy(document(EXAMPLE)),2,0),(deepcopy(setup()[0]),3,1)]:
        doc['statements']=[doc['statements'][index]]
        for node in doc['statements'][0]['body']['arguments']:node['rank']=rank
        try:parse(format_graph(doc,'compact'))
        except ValueError as error:assert 'strictly lower ranks' in str(error)
        else:raise AssertionError('Same-rank evaluation hidden in a quotation')
    return True


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    text='sich nicht vor Schatten fürchtet';start=unit['text'].index(text)
    return dict(work='kant-1784',unit=unit['id'],text_sha256=unit['text_sha256'],segments=[dict(start=start,end=start+len(text),text=text)],
        definitions=['hzvshadow','hzvdepiction','hzvcondition','hzvonly','hzvattribution'],status='explicit_interpretive_annotation',
        semantic_completion=False,intended_meaning_open=True,figurative_reading_confirmed=False)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    generic=[]
    for mapped,target,arbitrary in product((False,True),repeat=3):
        result=generic_values(mapped,target,arbitrary);assert result==[mapped and target,mapped and arbitrary,True]
        generic.append(dict(bits=[mapped,target,arbitrary],result=result))
    matrix=[]
    for mapped,target,remaining,owned,success,literal in product((False,True),repeat=6):
        result=values(mapped=mapped,target=target,remaining=remaining,owned=owned,success=success,literal_fear=literal)
        assert result==[mapped and (not success or owned and target and remaining),mapped and target and remaining,owned,True,mapped,target,not literal]
        matrix.append(dict(bits=[mapped,target,remaining,owned,success,literal],result=result))
    for name in ('other_node','other_author','other_mapping_context','reversed_mapping'):
        assert values(variant=name)==[False,False,True,True,False,True,False]
    for name in ('other_target_person','other_target_anchor'):
        assert values(variant=name)==[False,False,True,True,True,False,False]
    for flags in (dict(speaker=False),dict(hearers=False),dict(context=False)):
        assert values(**flags)==[False,True,True,True,True,True,False]
    assert values(mapped=False,success=False)==[False,False,True,True,False,True,False]
    assert values(variant='empty_population',mapped=False,indices=(0,))==[False]
    assert values(variant='unknown_literal_fear',indices=(0,1,2,3,4,5))==[True]*6
    for name,index in [('unknown_target',0),('unknown_mapping',0),('unknown_literal_fear',6),('baseline',7)]:
        assert values(variant=name,indices=(3,))==[True]
        try:values(variant=name,indices=(index,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown input was silently completed')
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for name in ('node','author','scope','context'):assert attribution(path,name)==[False]
    assert values(memoize=False,indices=(0,1))==[True,True]
    paths=[PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,OPTICS,AFFECT,UNITS,'data/cast-shadow-basis-v1.json','data/described-apprehension-basis-v1.json',
        'scripts/compose_interpreted_depiction.py','scripts/check_interpreted_depiction.py','tests/test_interpreted_depiction.py',
        'scripts/check_qualified_utterance.py','scripts/check_restricted_utterance.py','scripts/check_anchored_ability.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='partial_depiction_with_explicitly_unfilled_interpretation',documents=documents,generic=generic,matrix=matrix,
        roundtrips=True,lower_rank_refused=lower_rank_refused(),source_alignment=alignment(),parent_declarations_preserved=True,
        last_annotation_replaced=True,verified_full_units={'kant-1784':0,'einstein-1905':0},unresolved=basis()['unresolved'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Exact interpreted content, unasserted depiction and partial source connection verified')


if __name__=='__main__':main()
