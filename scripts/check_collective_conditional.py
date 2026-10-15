"""Check a fixed coalition conditional and its integrated causal consequence."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_collective_conditional import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,REST,FIELDS,WITNESS,build,basis
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts import check_joint_development as previous
from scripts import check_thinking_disposition as thinking

REPORT=ROOT/'reports/collective-conditional-v1.json'
PEOPLE=('person','other')
CASES=('first','second')
SCENES=('first','second','firstend','secondend','outside')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    from scripts.compose_restricted_utterance import primitive
    text=(ROOT/LIBRARY).read_text(encoding='utf-8');args={}
    for name,sort in FIELDS:
        if name=='reading':args[name]='r b[p jgproperty]';continue
        text+=primitive('jg'+name,sort if sort.startswith('h[') else 'h[] '+sort)
        args[name]='p jg'+name if sort.startswith('h[') else 'k jg'+name+'[]'
    text+='r jgtruth[a d] c.d jgproperty[person a] e[b point[k jgtruth[v person v point]]].'
    return parse(text+'q[k rxt['+' '.join(args[n] for n,t in FIELDS)+']].q[k rxu['+' '.join(args[n] for n,t in WITNESS)+']].')


def values(masks=(3,0),results=3,*,variant='baseline',memoize=True,calls=None):
    catalogue=() if variant=='empty_people' else PEOPLE+('person',) if variant=='duplicate' else PEOPLE[:1] if variant=='omitted' else PEOPLE
    def cases(scene):
        if variant=='unknown_cases':raise ValueError('Unknown cases')
        return variant!='empty_cases' and scene in CASES
    def valid(scene):
        if variant=='unknown_valid':raise ValueError('Unknown case scope')
        return not (variant=='invalid_second' and scene=='second')
    def history(scene,point):
        if variant=='unknown_history':raise ValueError('Unknown case history')
        return scene in CASES and point in ((scene,) if variant=='no_later' else (scene,scene+'end'))
    def before(scene,left,right):
        if variant=='reflexive' and left==right:return True
        return scene in CASES and (left,right)==(scene,scene+'end')
    def truth(person,scene):
        if variant=='unknown_premise':raise ValueError('Unknown premise')
        return person in PEOPLE and scene in CASES and bool(masks[CASES.index(scene)]&(1<<PEOPLE.index(person)))
    def result(reading,people,start,end):
        if calls is not None:calls.append((reading,people.items,start,end))
        if variant=='unknown_result':raise ValueError('Unknown consequence')
        return (thinking.code_is(reading,'jgproperty',1) and people.items==PEOPLE and start in CASES and end==start+'end'
            and bool(results&(1<<CASES.index(start))) and variant!='wrong_identity')
    p=dict(arithmetic(),jgcontributors=lambda:SequenceValue(catalogue,'"individual"'),jgpeople=lambda p:p in PEOPLE and variant!='empty_people',
        jgcases=cases,jgvalid=valid,jghistory=history,jgbefore=before,jgtruth=truth,jgresult=result)
    doc=fixture();p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,PEOPLE+('outsider',),SCENES,memoize=memoize,budget=5_000_000)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    from scripts.compose_qualified_utterance import closure
    names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iaqwitness']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    return parse(format_graph(doc,'compact')+f'r jgrest[{HIGH} a j[a] d d d] c.'+'''
r jgcommunity[] a.r jgcase[] d.
q[k iaqschema[r b[p iahinner] p jgrest]].
q[k iaqschema[r b[p iahvocation] p jgrest]].
q[t[k iaqwitness[r b[p iahinner] k jgcommunity[]]][k wh[]]].
q[k iaqfixed[k jgcommunity[] k wh[] k jgcase[]]].
q[k iaqschema[r b[p iahthinking] p jgrest]].
''')


def source_model(*,variant='baseline',all_false=False,remaining=True,calls=None):
    p,domain,scenes=previous.source_model(variant=variant)
    starts=tuple(previous.BEGINS.values());selected=starts[1:] if all_false else starts
    original=dict(p)
    for name,position in (
        ('iapcontributors',1),('iappeople',2),('ianpopulation',1),('ianmembers',2),('iantopics',2),
        ('ianscope',2),('ianbound',1),('iaoactivities',2),('iaoscope',2),('iaobound',1)):
        fn=original[name]
        def anchored(*args,_fn=fn,_position=position):
            args=list(args)
            if args[_position] in starts:args[_position]='end'
            return _fn(*args)
        p[name]=anchored
    old=dict(p)
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    def contributors(community,point):
        log('contributors',community,point)
        if variant=='empty_contributors':return SequenceValue((), '"individual"')
        if variant=='changed_contributors' and point=='onlyone':return SequenceValue(PEOPLE[:1], '"individual"')
        items=old['iapcontributors'](community,point).items
        return SequenceValue(tuple(reversed(items)) if variant=='reordered' and point=='onlyone' else items, '"individual"')
    def people(community,person,point):
        if variant=='unknown_scope' and point=='onlyone':raise ValueError('Unknown coalition scope')
        return old['iappeople'](community,person,point) and not (variant=='changed_contributors' and point=='onlyone' and person=='other')
    def topics(community,person,point):
        if variant=='changed_topics' and point=='onlyone' and person=='person':return SequenceValue(('topictwo',),'"individual"')
        return old['iantopics'](community,person,point)
    def scope(community,person,point,topic):
        if variant=='changed_topics' and point=='onlyone' and person=='person':return topic=='topictwo'
        return old['ianscope'](community,person,point,topic)
    def activities(community,person,point):
        if variant=='changed_activities' and point=='onlyone' and person=='other':return SequenceValue(('beta',),'"individual"')
        return old['iaoactivities'](community,person,point)
    def activity_scope(community,person,point,activity):
        if variant=='changed_activities' and point=='onlyone' and person=='other':return activity=='beta'
        return old['iaoscope'](community,person,point,activity)
    def path(scene):
        if scene not in starts:return ()
        if variant=='no_later':return (scene,)
        return (scene,'middle','after','outside') if variant=='different_history' and scene=='end' else (scene,'middle','after')
    def history(community,anchor,scene,point):
        if variant=='unknown_history':raise ValueError('Unknown conditional history')
        return (community,anchor)==('community','end') and point in path(scene)
    def before(community,anchor,scene,left,right):
        seq=path(scene)
        return (community,anchor)==('community','end') and left in seq and right in seq and seq.index(left)<seq.index(right)
    def rest(reading,community,contributors,anchor,start,end):
        log('remaining',reading,community,contributors.items,anchor,start,end)
        if variant=='unknown_remaining':raise ValueError('Unknown political remainder')
        return remaining and community=='community' and contributors.items==PEOPLE and (anchor,start,end)==('end','end','after') and any(
            thinking.code_is(reading,name,1) for name in ('iahinner','iahvocation'))
    p.update(jgcommunity=lambda:'community',jgcase=lambda:'onlyone',jgrest=rest,
        iapcontributors=contributors,iappeople=people,iantopics=topics,ianscope=scope,iaoactivities=activities,iaoscope=activity_scope,
        ianbound=lambda community,point:Fraction(2) if variant=='changed_bound' and point=='onlyone' else old['ianbound'](community,point),
        iaqcommunities=lambda community,anchor:variant!='empty_communities' and (community,anchor)==('community','end'),
        iaqcases=lambda community,anchor,scene:variant!='empty_cases' and (community,anchor)==('community','end') and scene in selected,
        iaqhistory=history,iaqbefore=before)
    return p,domain,scenes


def source_values(*,indices=(0,2),**options):
    p,domain,scenes=source_model(**options)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,budget=40_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iaqreport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and thinking.code_is(code,'iaqschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


CONTRASTS=('empty_people','duplicate','omitted','empty_cases','invalid_second','no_later','reflexive','wrong_identity')
UNKNOWNS=('unknown_cases','unknown_valid','unknown_history','unknown_premise','unknown_result')
SOURCE_CONTRASTS=('empty_contributors','empty_communities','empty_cases','changed_contributors','changed_topics','changed_activities','changed_bound','no_later','different_history')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iaqinventory','iaqfixed','iaqaligned','iaqconditional','iaqwitness','iaqschema','iaqattribution'],
        adds_new_text_coverage=False,semantic_completion=False,collective_conditional_unfilled=False,remaining_political_content_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for first,second,result in product(range(4),repeat=3):
        masks=(first,second)
        want=all(mask!=3 or bool(result&(1<<i)) for i,mask in enumerate(masks))
        assert values(masks,result)==[want,3 in masks],(masks,result)
    assert values(memoize=False)==values()
    assert source_values()==[True,True]
    assert source_values(all_false=True,variant='unknown_single')==[True,False]
    assert source_values(variant='changed_contributors',all_false=True)==[False,False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_collective_conditional.py','scripts/check_collective_conditional.py',
        'tests/test_collective_conditional.py','scripts/check_joint_development.py','scripts/check_caused_choice.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='collective_conditional_and_mediation_connected',documents=documents,conditional_combinations=64,
        source_alignment=alignment(),roundtrips=True,uncached_generic_baseline_checked=True,source_uses_closure_cache=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Collective conditional verified; political content and source semantic review remain incomplete')


if __name__=='__main__':main()
