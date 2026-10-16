"""Finite checks for qualitative modal order, endpoints and conditional scope."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_graded_modality import ROOT,LIBRARY,BASIS,build

REPORT=ROOT/'reports/graded-modality-v1.json'
DOMAIN=('zero','low','middle','near','top','outside')
SCENES=('now','a','b','c','copy')
VARIANTS=('baseline','empty_cases','empty_condition','condition_outside','impossible','necessary','necessary_top',
    'possible_bottom','outside_degree','equal_degrees','reversed_degrees','subset_reversal','equal_events',
    'conditioned_low','conditioned_top','empty_near','near_hole','near_top','near_bottom','near_outside',
    'broader_near','reflexive','cycle','incomparable','duplicate_candidate','actual_goal','actual_condition')


@lru_cache(maxsize=1)
def document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zscale[a] c.r zless[a a] c.r znear[a] c.
r zcases[d] c.r zcondition[d] c.r zfirst[d] c.r zsecond[d] c.
r zlow[] a.r zhigh[] a.r zfirstdegree[] a.r zseconddegree[] a.r zconditioneddegree[] a.
q[k rqsq[p zscale p zless k zlow[] k zhigh[]]].
q[k rqsr[p zcases p zfirst p zscale k zfirstdegree[] k zlow[] k zhigh[]]].
q[k rqss[p zscale p zless p znear k zlow[] k zhigh[]]].
q[k rqst[p zcases p zfirst p zsecond p zscale p zless k zlow[] k zhigh[] k zfirstdegree[] k zseconddegree[]]].
q[k rqsu[p zcases p zcondition p zfirst p zscale p zless p znear k zlow[] k zhigh[] k zconditioneddegree[]]].
q[k rqsv[p zcases p zcondition p zfirst p zsecond p zscale p zless p znear k zlow[] k zhigh[] k zfirstdegree[] k zseconddegree[] k zconditioneddegree[]]].
''')


def interpretation(variant='baseline'):
    scale=set(DOMAIN[:-1]);edges={(a,b) for i,a in enumerate(DOMAIN[:-1]) for b in DOMAIN[i+1:-1]}
    cases={'a','b','c'};condition={'a','b'};first={'a','c'};second={'c'};near={'near'}
    fd,sd,cd='middle','low','near'
    if variant=='empty_cases':cases=set()
    if variant=='empty_condition':condition=set()
    if variant=='condition_outside':condition={'now'}
    if variant=='impossible':first=set()
    if variant in ('necessary','necessary_top'):first=set(cases)
    if variant=='necessary_top':fd='top'
    if variant=='possible_bottom':fd='zero'
    if variant=='outside_degree':fd='outside'
    if variant=='equal_degrees':sd=fd
    if variant=='reversed_degrees':fd,sd='low','middle'
    if variant=='subset_reversal':first,second={'c'},{'a','c'}
    if variant=='equal_events':first=set(second)
    if variant=='conditioned_low':cd='low'
    if variant=='conditioned_top':cd='top'
    if variant=='empty_near':near=set()
    if variant=='near_hole':near={'middle'}
    if variant=='near_top':near.add('top')
    if variant=='near_bottom':near=set(scale)
    if variant=='near_outside':near.add('outside')
    if variant=='broader_near':near={'middle','near'};cd='middle'
    if variant=='reflexive':edges.add(('middle','middle'))
    if variant=='cycle':edges.add(('near','low'))
    if variant=='incomparable':edges.remove(('low','middle'))
    if variant=='duplicate_candidate':cases.add('copy');first.add('copy');condition.add('copy')
    if variant=='actual_goal':first.add('now')
    if variant=='actual_condition':condition.add('now')
    return dict(scale=scale,edges=edges,cases=cases,condition=condition,first=first,second=second,near=near,
        fd=fd,sd=sd,cd=cd,low='zero',high='top')


def model(data):
    values={n:lambda v=v:v for n,v in dict(zlow=data['low'],zhigh=data['high'],zfirstdegree=data['fd'],
        zseconddegree=data['sd'],zconditioneddegree=data['cd']).items()}
    for key in ('scale','cases','condition','first','second','near'):
        values['z'+key]=lambda value,key=key:value in data[key]
    values['zless']=lambda a,b:(a,b) in data['edges']
    return values


def evaluate(values,doc=None,domain=DOMAIN,scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc or document(),individuals=domain,situations=scenes,
        primitives=values,max_steps=2000000,memoize_definitions=False,memoize_expressions=False)]


def oracle(d):
    # Independent set/order calculation, with modal truth as event inclusion.
    scale,edges,low,high=d['scale'],d['edges'],d['low'],d['high']
    valid=low in scale and high in scale and low!=high
    valid &= all((x,x) not in edges for x in scale)
    valid &= all(x==y or ((x,y) in edges)!=((y,x) in edges) for x in scale for y in scale)
    valid &= all((x,z) in edges for x in scale for y in scale for z in scale if (x,y) in edges and (y,z) in edges)
    valid &= all(x==low or (low,x) in edges for x in scale) and all(x==high or (x,high) in edges for x in scale)
    def grounded(cases,event,degree):
        return bool(cases) and degree in scale and ((degree==low)==cases.isdisjoint(event)) and ((degree==high)==(cases<=event))
    near=d['near']
    valid_near=bool(near) and near<=scale-{low,high} and all(y in near for x in near for y in scale-{high} if (x,y) in edges)
    first=grounded(d['cases'],d['first'],d['fd'])
    greater=valid and first and grounded(d['cases'],d['second'],d['sd']) and (d['sd'],d['fd']) in edges and bool(d['cases']&(d['first']-d['second']))
    conditional=valid and valid_near and grounded(d['cases']&d['condition'],d['first'],d['cd']) and d['cd'] in near
    return [bool(x) for x in (valid,first,valid_near,greater,conditional,greater and conditional)]


def checks():
    rows={}
    for variant in VARIANTS:
        d=interpretation(variant);actual=evaluate(model(d));assert actual==oracle(d),(variant,actual,oracle(d))
        rows[variant]=actual
    assert rows['baseline']==[True]*6
    for variant in ('duplicate_candidate','actual_goal','actual_condition','broader_near'):assert rows[variant]==[True]*6
    for variant in ('empty_condition','condition_outside','conditioned_low','conditioned_top'):
        assert rows[variant][3] and not rows[variant][4]
    assert not rows['subset_reversal'][3] and rows['subset_reversal'][1]
    # Exhaust all binary relations on a three-element scale, including cycles,
    # reflexive edges, incomplete comparisons and misplaced endpoints.
    orderdoc=deepcopy(document());orderdoc['statements']=orderdoc['statements'][:1]
    subset=('zero','middle','top');pairs=list(product(subset,repeat=2))
    accepted=0
    for mask in range(1<<len(pairs)):
        d=interpretation();d['scale']=set(subset);d['edges']={p for i,p in enumerate(pairs) if mask&(1<<i)}
        actual=evaluate(model(d),orderdoc);expected=oracle(d)[0];assert actual==[expected],mask;accepted+=expected
    assert accepted==1
    d=interpretation();assert evaluate(model(d),domain=tuple(reversed(DOMAIN)),scenes=tuple(reversed(SCENES)))==[True]*6
    unknowns=[]
    def unknown(*args):raise ValueError('Unknown modal interpretation')
    for name in ('zfirst','zcondition','zless'):
        values=model(d);values[name]=unknown
        try:evaluate(values)
        except ValueError as e:assert 'Unknown' in str(e);unknowns.append(name)
        else:raise AssertionError(name)
    return dict(contrasts=rows,exhaustive_scale_relations=512,valid_scale_relations=accepted,
        domain_and_candidate_reordering_invariant=True,duplicate_candidate_not_a_frequency_vote=True,
        unknown_inputs_refused=unknowns,semantic_evaluation_uncached=True)


def integration():
    active=load_catalog(ROOT,'data/cross-reference-basis-v1.json')
    extra=load_catalog(ROOT,BASIS)
    assert not set(active.entries)&set(extra.entries)
    combined=deepcopy(active.document);statements=combined['statements'];combined['statements']=[]
    source=format_graph(combined,'compact')
    library=format_graph(extra.document,'compact')
    combined=parse(source+library[2:])
    combined['statements']=statements
    combined=parse(format_graph(combined,'compact'))
    assert combined['declarations'][:-6]==active.document['declarations']
    assert combined['statements']==active.document['statements']
    assert parse(transcribe(format_graph(combined,'compact'),alphabet='v2'))==combined
    return dict(active_document=active.document_path,existing_statements_preserved=len(statements),
        compatible_definitions_added=6,existing_meaning_basis_unchanged=True)


def build_report():
    for name,body in build().items():assert (ROOT/name).read_text(encoding='utf-8')==body
    cat=load_catalog(ROOT,BASIS);assert set(cat.entries)=={'rqsq','rqsr','rqss','rqst','rqsu','rqsv'}
    for notation in ('compact','full'):
        text=format_graph(cat.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==cat.document
    inventory='artifacts/written-units-v1/kant-1784.json'
    u=next(u for u in json.loads((ROOT/inventory).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0011')
    active=load_catalog(ROOT,'data/cross-reference-basis-v1.json')
    paths=set(build())|set(active.source_sha256)|{inventory,'scripts/compose_graded_modality.py','scripts/check_graded_modality.py',
        'tests/test_graded_modality.py','docs/graded-modality-v1.md','docs/intragroup-change-v1.md','data/semantic-review-index-v22.json'}
    return dict(status='qualitative_modal_schema_checked_source_binding_incomplete',document=LIBRARY,checks=checks(),integration=integration(),roundtrips=True,
        definitions=6,new_primitives=0,characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        source_motivation=dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],
            interpretation='Comparative possibility and condition-restricted near necessity; no numerical probability claimed.',
            remaining=['public self-enlightenment content','individual comparison baseline','liberty condition',
                'source comparison scale and near-endpoint reading','reinforcement and author attribution']),
        source_coverage_advanced=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        active_manuscript_and_review_index_unchanged=True,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:
        stored=json.loads(REPORT.read_text(encoding='utf-8'));validate_hashes(ROOT,stored['source_sha256']);assert stored==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Modal degree endpoints, comparative order and conditional scope checked')


if __name__=='__main__':main()
