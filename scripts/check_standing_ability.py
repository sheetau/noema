"""Check held-fixed opportunity profiles against present practical ability."""
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
from scripts.compose_standing_ability import ROOT,SOURCE,SOURCE_BASIS,LIBRARY,EXAMPLE,BASIS,EXAMPLE_BASIS,MEANINGS,build,catalog

REPORT=ROOT/'reports/standing-ability-v1.json'
SCENES=('anchor','first','second','success','failure')
DOMAIN=('person','method','backup','faculty','act','guide','other')


def unknown(*args):raise ValueError('Unknown standing-ability input')


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=6000000,memoize_definitions=False,memoize_expressions=False)]


@lru_cache(None)
def generic():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zperson[] a.r zanchor[] d.r zcases[a d d] c.r zpreserved[a d d] c.r zopportunity[a d] c.r zpreferred[a d d d] c.
r zavailable[a a d] c.r zoutcomes[a a d d] c.r zselected[a a d d] c.r zsuccess[d] c.
d zgoal[] e[b scene[k zsuccess[v scene]]].
'''
    current='k zperson[] k zgoal[] k zanchor[] p zavailable p zoutcomes p zselected'
    args='k zperson[] k zgoal[] k zanchor[] p zcases p zpreserved p zopportunity p zpreferred p zavailable p zoutcomes p zselected'
    text+='q[k xd['+current+']].q[k xg['+current+']].'
    text+=''.join('q[k '+name+'['+args+']].' for name in ('rqva','rqvb','rqvc','rqvd'))
    text+='q[u[k rqva['+args+']]].'
    return parse(text)


def model(doc,*,now=False,now_passes=True,passes=(True,True),prefer_first=False,variant='baseline'):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    candidates=set() if variant=='empty_profile' else {'first','second'}
    person='other' if variant=='other_profile_person' else 'person'
    anchor='failure' if variant=='other_profile_anchor' else 'anchor'
    pairs={('first','second')} if prefer_first else set()
    if variant=='cyclic_order':pairs={('first','second'),('second','first')}
    def available(p,m,s):
        chosen='backup' if variant=='different_methods' and s=='second' else 'method'
        return p=='person' and m==chosen and (s in ('first','second') or now and s=='anchor')
    def outcomes(p,m,s,t):return available(p,m,s) and t in ('success','failure')
    def selected(p,m,s,t):
        if not available(p,m,s) or variant=='missing_assessment' and s=='second':return False
        if variant=='foreign_assessment' and s=='second':return t=='anchor'
        passed=now_passes if s=='anchor' else passes[0] if s=='first' else passes[1]
        return t==('success' if passed else 'failure')
    values.update(zperson=lambda:'person',zanchor=lambda:'anchor',
        zcases=lambda p,a,s:(p,a)==(person,anchor) and s in candidates,
        zpreserved=lambda p,a,s:(p,a)==('person','anchor') and not(variant=='changed_person_state' and s=='second'),
        zopportunity=lambda p,s:p=='person' and (s in ('first','second') or now and s=='anchor') and not(variant=='missing_external_opportunity' and s=='second'),
        zpreferred=lambda p,a,s,t:(p,a)==('person','anchor') and (s,t) in pairs,
        zavailable=available,zoutcomes=outcomes,zselected=selected,zsuccess=lambda s:s=='success')
    return values


def combinations():
    doc=generic();rows=[]
    for now,first,second,ordered in product((False,True),repeat=4):
        expected_ability=first and (ordered or second)
        expected_inability=not first and (ordered or not second)
        values=model(doc,now=now,passes=(first,second),prefer_first=ordered)
        assert values['zopportunity']('person','anchor')==now
        actual=evaluate(doc,values)
        expected=[now,not now,expected_ability,expected_inability,True,not expected_ability,not expected_ability]
        assert actual==expected,(now,first,second,ordered,actual)
        rows.append(dict(current_successful_method=now,first_success=first,second_success=second,
            first_preferred=ordered,values=actual))
    return dict(cases=rows,count=len(rows),current_block_does_not_erase_profile_ability=True,
        mixed_profile_failure_distinct_from_typical_inability=True,uncached_and_unlowered=True)


def profile_checks():
    doc=generic();rows={}
    cases={
        'baseline':({},[False,True,True,False,True,False,False]),
        'different_methods':({'variant':'different_methods'},[False,True,True,False,True,False,False]),
        'empty_profile':({'variant':'empty_profile'},[False,True,False,False,False,False,True]),
        'changed_person_state':({'variant':'changed_person_state','prefer_first':True},[False,True,False,False,False,False,True]),
        'missing_external_opportunity':({'variant':'missing_external_opportunity','prefer_first':True},[False,True,False,False,False,False,True]),
        'other_profile_person':({'variant':'other_profile_person'},[False,True,False,False,False,False,True]),
        'other_profile_anchor':({'variant':'other_profile_anchor'},[False,True,False,False,False,False,True]),
        'cyclic_order':({'variant':'cyclic_order'},[False,True,False,False,False,False,True]),
        'missing_assessment':({'variant':'missing_assessment'},[False,True,False,False,False,False,True]),
        'foreign_assessment':({'variant':'foreign_assessment'},[False,True,False,False,False,False,True]),
        'exceptional_failure':({'passes':(True,False),'prefer_first':True},[False,True,True,False,True,False,False]),
        'incomparable_failure':({'passes':(True,False)},[False,True,False,False,True,True,True]),
        'opportunity_without_ability':({'now':True,'now_passes':False,'passes':(False,False)},[False,True,False,True,True,True,True]),
    }
    for name,(options,expected) in cases.items():
        actual=evaluate(doc,model(doc,**options));assert actual==expected,(name,actual);rows[name]=actual
    for name in ('zcases','zpreserved','zopportunity','zpreferred','zavailable','zoutcomes','zselected'):
        values=model(doc);values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown standing-ability' in str(error)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=7,invalid_candidates_not_silently_dropped=True,
        raw_negation_not_certified_inability=True,per_case_method_selection_allowed=True)


def source_checks():
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'));rows={}
    for name,options,expected in [
        ('blocked_now_but_capable_with_opportunity',{},[False,True,True,False,True,False]),
        ('can_now_and_in_profile',{'now':True},[True,False,True,False,True,False]),
        ('cannot_in_profile_either',{'passes':(False,False)},[False,True,False,True,True,True]),
        ('opportunity_alone_is_not_ability',{'now':True,'now_passes':False,'passes':(False,False)},[False,True,False,True,True,True]),
        ('mixed_normal_opportunities',{'passes':(True,False)},[False,True,False,False,True,True]),
        ('learning_cannot_replace_fixed_person',{'variant':'changed_person_state'},[False,True,False,False,False,False]),
        ('same_own_faculty_still_guided',{},[False,True,False,True,True,True]),
    ]:
        values=model(doc,**options)
        values.update(ae=values['zavailable'],af=values['zoutcomes'],ap=values['zselected'],aa=lambda p:p=='person',
            ab=lambda f,p,s:(f,p)==('faculty','person'),
            ac=lambda p,f,a,s:(p,f,a,s)==('person','faculty','act','success'),
            ad=lambda guide,p,a,s:name=='same_own_faculty_still_guided' and (guide,p,a,s)==('guide','person','act','success'))
        actual=evaluate(doc,values);assert actual==expected,(name,actual);rows[name]=actual
    return dict(cases=rows,current_bb_bc_and_xd_bodies_executed=True,source_sense_not_chosen_automatically=True,
        canonical_manuscript_not_modified=True)


def structure():
    original=catalog();lib=load_catalog(ROOT,BASIS);example=load_catalog(ROOT,EXAMPLE_BASIS)
    assert all(d['kind']=='definition' for d in lib.document['declarations'])
    assert len(set(lib.entries)-set(original.entries))==6
    for current in (lib,example):
        for name,entry in current.entries.items():
            if name in original.entries:
                assert entry['declaration']==original.entries[name]['declaration']
                assert entry['meaning_ja']==original.entries[name]['meaning_ja']
    index=json.loads((ROOT/'data/semantic-review-index-v24.json').read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document']==SOURCE
    assert len(original.document['statements'])==35
    return dict(new_generic_definitions=6,new_generic_primitives=0,canonical_source_unchanged=True,
        library_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),example_queries=6,
        active_semantic_review_index='data/semantic-review-index-v24.json')


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    results={}
    for name,fn in [('combinations',combinations),('profiles',profile_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    for path in (LIBRARY,EXAMPLE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    prior=json.loads((ROOT/'reports/opening-scope-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    inventory='artifacts/written-units-v1/kant-1784.json'
    units=json.loads((ROOT/inventory).read_text(encoding='utf-8'))['units'];u=next(r for r in units if r['id']=='kant-1784:u0008')
    alignment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[86,181],source=u['text'][86:181],
        definitions=['bc','rqva','rqvb','rqvd'],status='partial_comparison_of_ability_senses',full_semantic_equivalence=False)
    from scripts.audit_written_progress_extended import collect_alignment
    collected=collect_alignment(dict(alignment=alignment),{r['id']:r for r in units},set(load_catalog(ROOT,EXAMPLE_BASIS).entries),'reports/standing-ability-v1.json')
    assert len(collected)==1 and collected[0]['status']=='partial'
    paths=set(outputs)|set(catalog().source_sha256)|set(prior['source_sha256'])|{SOURCE,SOURCE_BASIS,inventory,
        'reports/opening-scope-v1.json','data/opening-reading-status-v1.json','data/semantic-review-index-v24.json',
        'scripts/compose_standing_ability.py','scripts/check_standing_ability.py','tests/test_standing_ability.py','docs/standing-ability-v1.md'}
    return dict(status='opportunity_independent_profile_available_as_explicit_comparison',document=EXAMPLE,**results,
        roundtrips=True,alignment=alignment,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Ability profile, present opportunity and source comparison checked',flush=True)


if __name__=='__main__':main()
