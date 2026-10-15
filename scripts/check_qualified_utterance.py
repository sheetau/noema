"""Verify an actual autonomous-use condition within the source speech restriction."""
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
from scripts import check_restricted_utterance as previous
from scripts.compose_qualified_utterance import ROOT,PARENT,SOURCE,CORE,BASIS,NAMES,closure,build,basis

REPORT=ROOT/'reports/qualified-utterance-v1.json'
UNITS='artifacts/written-units-v1/kant-1784.json'


@lru_cache(maxsize=3)
def source_document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=32)
def setup(speaker=True,context=True,variant='baseline'):
    doc,expected=previous.setup(speaker,context,variant);doc=deepcopy(doc);doc['statements']=[]
    source=source_document(CORE);names={d['name']:d for d in doc['declarations']}
    for decl in closure(source,['h4l']):
        if decl['name'] in names:assert decl==names[decl['name']],decl['name']
        else:doc['declarations'].append(decl)
    doc['declarations'] += [deepcopy(d) for d in source['declarations'] if d['name'] in NAMES[:2]]
    expression='k hzuonly[p jzcriterion k juanchor[]]';code='r c['+expression+']'
    questions=[expression,'k hzuqualification[p jzcriterion k juperson[] k juanchor[]]',
        't[k h4l[k juperson[]]][k juanchor[]]','e['+code+']['+code+']',
        't[k up[k juperson[]]][k juanchor[]]','t[k fo[k juperson[]]][k juanchor[]]',
        't[k h4l[k juother[]]][k juanchor[]]','t[k bb[k juperson[]]][k juanchor[]]']
    return parse(format_graph(doc,'compact')+''.join('q['+q+'].' for q in questions)),expected


def values(*,owned=True,used=True,guided=False,assessed=True,remaining=True,success=True,
           speaker=True,hearers=True,context=True,variant='baseline',indices=(0,1,2,3),memoize=True):
    fixture=setup(speaker,context,variant)
    def evaluate(doc,**kwargs):
        model=kwargs['primitives'];kwargs['individuals']=(*kwargs['individuals'],'faculty','method','judgment')
        person='other' if variant=='other_capable_person' else 'speaker'
        start='right' if variant=='other_ability_anchor' else 'anchor'
        def ownership(faculty,owner,point):
            if variant=='unknown_ownership':raise ValueError('Unknown faculty ownership')
            return owned and (faculty,owner)==('faculty','other' if variant=='other_owner' else person) and (
                point=='anchor' if variant=='ownership_only_at_anchor' else True)
        def use(actor,faculty,act,point):
            return used and (actor,faculty,act,point)==(person,'plan' if variant=='other_faculty' else 'faculty','judgment','left')
        def guidance(guide,actor,act,point):
            return (guided or variant in ('self_guidance','other_guided_actor','other_guided_act')) and (
                guide,actor,act,point)==('speaker' if variant=='self_guidance' else 'other',
                    'listener' if variant=='other_guided_actor' else person,
                    'a' if variant=='other_guided_act' else 'judgment','left')
        def available(actor,method,point):
            return variant!='no_method' and actor==person and point==start and (
                method=='method' or variant=='unassessed_extra_method' and method=='plan')
        def outcome(actor,method,first,last):
            return (actor,method,first,last)==(person,'method',start,'left')
        def selected(actor,method,first,last):
            if variant=='unknown_assessment':raise ValueError('Unknown capacity assessment')
            return assessed and (actor,method,first,last)==(person,'method',start,'right' if variant=='selected_nonoutcome' else 'left')
        model.update(aa=lambda actor:variant!='not_person' and actor in ('speaker','other'),ab=ownership,ac=use,ad=guidance,
            ae=available,af=outcome,ap=selected)
        return evaluate_document(doc,**kwargs)
    with patch.object(previous,'setup',return_value=fixture),patch.object(previous,'evaluate_document',side_effect=evaluate):
        return previous.values(speaker=speaker,hearers=hearers,context=context,success=success,eligible=remaining,
            variant=variant,indices=indices,memoize=memoize)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(source_document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Quoted qualification was evaluated during annotation')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def report(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='hzuonly')
    model.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',hztannotation=report)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=model)]


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    segments=[]
    for text in ('nur derjenige','selbst aufgeklärt','kann das sagen'):
        start=unit['text'].index(text);segments.append(dict(start=start,end=start+len(text),text=text))
    return dict(work='kant-1784',unit=unit['id'],text_sha256=unit['text_sha256'],segments=segments,
        definitions=list(NAMES),status='explicit_interpretive_annotation',semantic_completion=False,
        remaining_qualification_open=True,self_emphasis_complete=False)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    old,new=source_document(PARENT),source_document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1] and len(new['statements'])==len(old['statements'])
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for owned,used,guided,assessed,remaining,success in product((False,True),repeat=6):
        capable=owned and used and not guided and assessed
        result=values(owned=owned,used=used,guided=guided,assessed=assessed,remaining=remaining,success=success)
        assert result==[not success or capable and remaining,capable and remaining,capable,True]
        matrix.append(dict(bits=[owned,used,guided,assessed,remaining,success],result=result))
    contrasts={}
    for name in ('other_owner','other_faculty','other_capable_person','other_ability_anchor','ownership_only_at_anchor',
                 'no_method','unassessed_extra_method','selected_nonoutcome','not_person'):
        result=values(variant=name);assert result==[False,False,False,True],(name,result);contrasts[name]=result
    for name in ('self_guidance','other_guided_actor','other_guided_act','alias_references','later_audience'):
        result=values(variant=name);assert result==[True,True,True,True],(name,result);contrasts[name]=result
    for args in (dict(speaker=False),dict(hearers=False),dict(context=False)):
        assert values(**args)==[False,True,True,True]
    for name in ('criterion_wrong_person','criterion_wrong_anchor'):
        assert values(variant=name)==[False,False,True,True]
    diagnostics={}
    for name,expected in [('baseline',[True,True,True,False,False]),
                          ('unassessed_extra_method',[False,True,False,False,False]),
                          ('other_capable_person',[False,False,True,True,False]),
                          ('no_method',[False,False,True,False,False])]:
        result=values(variant=name,indices=(2,4,5,6,7));assert result==expected,(name,result)
        diagnostics[name]=result
    for name in ('unknown_ownership','unknown_assessment','unknown_criterion'):
        assert values(variant=name,indices=(3,))==[True]
        try:values(variant=name,indices=(1,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown qualification was treated as a known truth value')
    assert values(memoize=False,indices=(0,1,2))==[True,True,True]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for name in ('node','author','scope','context'):assert attribution(path,name)==[False]
    paths=[PARENT,SOURCE,CORE,BASIS,UNITS,'data/kant-qualified-princes-basis-v1.json',
        'scripts/compose_qualified_utterance.py','scripts/check_qualified_utterance.py','tests/test_qualified_utterance.py',
        'scripts/check_restricted_utterance.py','scripts/check_anchored_ability.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='partial_qualification_connected_to_existing_autonomous_use_capacity',
        documents=documents,new_definitions=3,new_primitives=0,earlier_statements_preserved=True,last_annotation_replaced=True,
        matrix=matrix,contrasts=contrasts,capacity_diagnostics=diagnostics,roundtrips=True,annotation_does_not_execute_qualification=True,
        source_alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},unresolved=basis()['unresolved'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Same-person autonomous capacity, remaining qualification and quoted speech verified')


if __name__=='__main__':main()
