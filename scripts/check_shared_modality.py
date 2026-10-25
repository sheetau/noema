"""Provenance-aware shared definitions and finite semantic contrasts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import hashlib
import json

from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_modality import (ROOT,LIBRARY,ABILITY_SOURCE,MODAL_SOURCE,ABILITY_NAMES,MODAL_NAMES,
                                     composed,active_catalogs,inventory,renamed,call,v)

CANDIDATES=('candidateexists','candidateempty','candidatepossible','candidatenecessary',
            'candidateexcluded','candidatecontingent','necessaryactual')
ABILITIES=('methodpossible','methodguaranteed','assessedability','methodsassessable',
           'assessmentdecisive','assessedinability')


@lru_cache(maxsize=1)
def source_mapping():
    catalogs=active_catalogs()
    rows=inventory(catalogs)
    expected={'ud','ue','uf','ug','uh','s5k','zac','zai'}
    if {r['symbol'] for r in rows}!=expected: raise ValueError('Current declaration intersection changed')
    if {r['symbol'] for r in rows if r['decision']=='keep_distinct_meanings'}!={'zac','zai'}:
        raise ValueError('Known semantic collision disappeared or changed')
    target=next(d for d in composed()['declarations'] if d['name']=='candidatenecessary')
    old=renamed(target,{'candidatenecessary':'s5k'})
    baseline_path=json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))['progress_report']
    baseline=json.loads((ROOT/baseline_path).read_text(encoding='utf-8'))['source_sha256']
    checked=set(); uses={}
    for work,catalog in catalogs.items():
        if catalog.entries['s5k']['declaration']!=old: raise ValueError('Shared candidate body differs')
        for path,digest in catalog.source_sha256.items():
            if baseline.get(path)!=digest: raise ValueError('Catalog dependency differs from preserved audit: '+path)
            checked.add(path)
        direct,_=catalog._dependencies()
        def closure(names):
            result=set(); pending=list(names)
            while pending:
                n=pending.pop()
                if n not in result: result.add(n); pending.extend(direct[n]-result)
            return result
        from noema.meaning_catalog import _references
        used=[i for i,s in enumerate(catalog.document['statements']) if 's5k' in closure(_references(s))]
        if not used: raise ValueError('Candidate definition is not used in selected manuscript')
        uses[work]=dict(document=catalog.document_path,basis=catalog.basis_path,statement_indices=used)
    return dict(intersection=rows,selected_definition='s5k',source_uses=uses,
                prior_dependency_report=baseline_path,checked_prior_dependencies=len(checked))


@lru_cache(maxsize=2)
def harness(ability=False):
    d=deepcopy(composed())
    signatures={'actor':([],'individual'),'context':([],'situation'),'goal':(['situation'],'truth'),
        'candidates':(['content','situation','situation'],'truth'),
        'available':(['individual','individual','situation'],'truth'),
        'outcomes':(['individual','individual','situation','situation'],'truth'),
        'selected':(['individual','individual','situation','situation'],'truth')}
    d['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items()]
    content=dict(kind='content',variable='world',body=call('goal',v('world')))
    ref=lambda n:dict(kind='function_ref',symbol=n)
    for name in ABILITIES if ability else CANDIDATES:
        if name in CANDIDATES: args=[content,call('context'),ref('candidates')]
        elif name=='methodsassessable': args=[call('actor'),call('context'),ref('available'),ref('outcomes'),ref('selected')]
        else:
            args=[call('actor'),content,call('context'),ref('available'),ref('outcomes')]
            if name not in ('methodpossible','methodguaranteed'): args.append(ref('selected'))
        d['statements'].append(dict(kind='ask',body=call(name,*args)))
    return normalize_document(d)


def interpret(*,candidate,success,actual=False,available=(),outcomes=None,selected=None,ability=False):
    if candidate is None or success is None: raise ValueError('Missing interpretation is not an empty set')
    outcomes={} if outcomes is None else outcomes
    selected={} if selected is None else selected
    primitives={'actor':lambda:'actor','context':lambda:'now',
        'goal':lambda world:actual if world=='now' else world in success,
        'candidates':lambda content,context,world:context=='now' and world in candidate,
        'available':lambda person,method,context:person=='actor' and context=='now' and method in available,
        'outcomes':lambda person,method,context,world:person=='actor' and context=='now' and world in outcomes.get(method,set()),
        'selected':lambda person,method,context,world:person=='actor' and context=='now' and world in selected.get(method,set())}
    rows=evaluate_document(harness(ability),individuals=('actor','plan','backup'),situations=('now','left','right'),primitives=primitives)
    return dict(zip(ABILITIES if ability else CANDIDATES,(r['value'] for r in rows)))


@lru_cache(maxsize=1)
def finite_checks():
    sets=[{w for i,w in enumerate(('left','right')) if mask&(1<<i)} for mask in range(4)]
    candidate_cases=[]
    for chosen,truth,actual in product(sets,sets,(False,True)):
        expected=(bool(chosen),not chosen,bool(chosen&truth),bool(chosen) and chosen<=truth,
                  bool(chosen) and not(chosen&truth),bool(chosen&truth) and bool(chosen-truth),
                  bool(chosen) and chosen<=truth and actual)
        observed=interpret(candidate=chosen,success=truth,actual=actual)
        if tuple(observed.values())!=tuple(map(bool,expected)): raise ValueError('Candidate model differs')
        candidate_cases.append(dict(candidates=sorted(chosen),success=sorted(truth),actual=actual,values=observed))
    ability_cases=0
    for available,outcomes,selected,truth in product((False,True),sets,sets,sets):
        valid=bool(selected) and selected<=outcomes
        witness=available and valid and selected<=truth
        assessable=not available or valid
        expected=(available and bool(outcomes&truth),available and bool(outcomes) and outcomes<=truth,
                  witness,assessable,assessable or witness,assessable and not witness)
        result=interpret(candidate=outcomes,success=truth,available={'plan'} if available else set(),
                         outcomes={'plan':outcomes},selected={'plan':selected},ability=True)
        if tuple(result.values())!=tuple(map(bool,expected)): raise ValueError('Ability model differs')
        ability_cases+=1
    return dict(candidate_models=candidate_cases,ability_models=ability_cases,
                candidate_domain_size=2,maximum_available_methods_in_exhaustive_check=1)


@lru_cache(maxsize=1)
def contexts():
    cases=[
        ('travel_without_an_available_route','移動',{'left','right'},{'left'},set(),{'plan':{'left','right'}},{'plan':{'left','right'}}),
        ('travel_possible_but_not_guaranteed','移動',{'left','right'},{'left'},{'plan'},{'plan':{'left','right'}},{'plan':{'left','right'}}),
        ('device_missing_assessment','装置操作',{'left','right'},{'left'},{'plan'},{'plan':{'left','right'}},{'plan':set()}),
        ('device_failure_in_assessed_results','装置操作',{'left','right'},{'left'},{'plan'},{'plan':{'left','right'}},{'plan':{'right'}}),
        ('device_alternative_method','装置操作',{'left','right'},{'left'},{'plan','backup'},
             {'plan':{'right'},'backup':{'left'}},{'plan':{'right'},'backup':{'left'}}),
    ]
    rows=[]
    for name,topic,candidate,success,available,outcomes,selected in cases:
        kwargs=dict(candidate=candidate,success=success,available=available,outcomes=outcomes,selected=selected)
        rows.append(dict(name=name,topic=topic,candidates=interpret(**kwargs),ability=interpret(**kwargs,ability=True)))
    return rows


@lru_cache(maxsize=1)
def binding_diagnostics():
    rows=[]
    # Two values per relevant sort; vary one slot while other witnesses are
    # fixed. This is binding diagnosis, not an exhaustive tuple-domain proof.
    for ability,arity in ((False,3),(True,4)):
        document=deepcopy(harness(ability))
        name='methodpossible' if ability else 'candidatepossible'
        document['statements']=[s for s in document['statements'] if s['body']['symbol']==name]
        baseline=('actor','plan','now','after') if ability else ((False,True),'now','after')
        replacements=('plan','actor','after','now') if ability else ((True,False),'after','now')
        for slot in range(-1,arity):
            wanted=list(baseline)
            if slot>=0: wanted[slot]=replacements[slot]
            target=tuple(wanted)
            model={'actor':lambda:'actor','context':lambda:'now','goal':lambda w:w=='after',
                'available':lambda a,m,c:(a,m,c)==('actor','plan','now'),
                'outcomes':lambda a,m,c,w:(a,m,c,w)==target,
                'selected':lambda *args:False,
                'candidates':lambda p,c,w:(p.values,c,w)==target}
            actual=evaluate_document(document,individuals=('actor','plan'),situations=('now','after'),primitives=model)[0]['value']
            if actual!=(slot==-1): raise ValueError('Binding slot differs: '+name+' '+str(slot))
            rows.append(dict(function=name,changed_slot=None if slot<0 else slot,value=actual))
    return rows


def build_report():
    source=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    if source!=composed(): raise ValueError('Shared source differs from composed definitions')
    from noema.meaning_catalog import load_catalog
    catalog=load_catalog(ROOT,'data/shared-modality-basis-v1.json')
    if catalog.document!=source: raise ValueError('Public contracts refer to another module')
    origins=source_mapping()
    paths=[LIBRARY,ABILITY_SOURCE,MODAL_SOURCE,'data/shared-modality-basis-v1.json',
           'data/contextual-ability-basis-v1.json','data/derivation-modalities-basis-v1.json',
           'scripts/shared_modality.py','scripts/check_shared_modality.py','tests/test_shared_modality.py',
           'docs/shared-modality-v1.md','data/work-state.json',origins['prior_dependency_report']]
    # Pin the evaluator/parser implementations used here. The large unchanged
    # historical provenance is checked against the existing aggregate above,
    # rather than copied into another full handoff/evidence bundle.
    import sys
    for name,module in tuple(sys.modules.items()):
        if name=='noema' or name.startswith('noema.'):
            path=getattr(module,'__file__',None)
            if path and ROOT in __import__('pathlib').Path(path).resolve().parents:
                paths.append(__import__('pathlib').Path(path).resolve().relative_to(ROOT).as_posix())
    return dict(schema='noema-shared-modality-evidence-1',status='shared_candidate_and_ability_module',
        declarations=len(source['declarations']),new_primitives=0,source_mapping=origins,
        finite_checks=finite_checks(),context_contrasts=contexts(),binding_diagnostics=binding_diagnostics(),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))},
        limits=['Finite interpretations do not prove general natural-language equivalence',
                'Candidate, availability and assessment relations remain explicit interpretation inputs',
                'Shared circular lexical names and other semantic domains remain unfinished',
                'Original manuscripts and their semantic judgments are unchanged'])
