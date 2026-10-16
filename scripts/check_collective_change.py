"""Check exact target sets and native same-process capacity changes."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_scoped_counts import arithmetic
from scripts.check_self_achievement import source_model as predecessor_model
from scripts.check_described_explanations import symbol
from scripts.compose_collective_change import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,build

REPORT=ROOT/'reports/collective-change-v1.json'
PEOPLE=('person','other','third')
DOMAIN=PEOPLE+('group','process','part','faculty','plan','outsider','other_process','second_part')
SCENES=('before','end','anchor')
EXPECTED={
 'one':(1,False,False),'two':(2,True,False),'all':(3,True,True),
 'outside_second':(1,False,False),'different_process':(1,False,False),
 'different_start':(1,False,False),'different_end':(1,False,False),
 'missing_second_cause':(1,False,False),'guided_second':(1,False,False),
 'no_part':(0,False,False),'external_actor_only':(0,False,False),
 'single_member':(0,False,False),'duplicate_member':(0,False,False),
 'different_internal_parts':(2,True,False),'external_assistance':(2,True,False),
 'already_capable_second':(1,False,False),
}


def unknown(*args):raise ValueError('Unknown collective change condition')


def evaluate(doc,values,domain=DOMAIN,scenes=SCENES,memoize=False):
    values={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,primitives=values,
        max_steps=60000000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(maxsize=1)
def generic_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zmembers[a] c.r ztransition[a] c.r zextent[h[a] c h[a] c] c.
q[k rqsw[p zmembers p ztransition p zextent]].
q[k rqsw[p zmembers p ztransition p rqsy]].
q[k rqsw[p zmembers p ztransition p rqsx]].
''')


def generic_checks():
    doc=generic_document();domain=('a','b','outside');count=0
    for member_flags,transition_flags in product(product((False,True),repeat=3),repeat=2):
        members={p for p,yes in zip(domain,member_flags) if yes}
        transitions={p for p,yes in zip(domain,transition_flags) if yes}
        reached=members&transitions;observed=[]
        def extent(scope,changed):
            observed.append(({p for p in domain if scope(p)},{p for p in domain if changed(p)}))
            return True
        values=dict(zmembers=lambda p:p in members,ztransition=lambda p:p in transitions,zextent=extent)
        actual=evaluate(doc,values,domain,('now',))
        assert actual==[bool(reached),len(reached)>=2,bool(members) and reached==members],(members,transitions,actual)
        assert observed and all(pair==(members,reached) for pair in observed)
        count+=1
    for name in ('ztransition','zextent'):
        values=dict(zmembers=lambda p:p in ('a','b'),ztransition=lambda p:p=='a',zextent=lambda *args:True)
        values[name]=unknown
        try:evaluate(doc,values,domain,('now',))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(membership_and_transition_combinations=count,exact_scope_observed_in_every_case=True,
        empty_group_and_empty_change_refused=True,unknown_inputs_refused=2,semantic_evaluation_uncached=True)


@lru_cache(maxsize=1)
def source_document():
    return parse((ROOT/CORE).read_text(encoding='utf-8')+'''
r zgroup[] a.r zprocess[] a.r zstart[] d.r zend[] d.r zanchor[] d.
r zextent[h[a] c h[a] c] c.r zactor[] a.r ztarget[] a.r zpart[] a.
q[k hzmw[k zgroup[] k zprocess[] k zstart[] k zend[] k zanchor[] p zextent]].
q[k hzmw[k zgroup[] k zprocess[] k zstart[] k zend[] k zanchor[] p rqsy]].
q[k hzmw[k zgroup[] k zprocess[] k zstart[] k zend[] k zanchor[] p rqsx]].
''')


def source_model(doc,variant='two',observed=None):
    changed={'person'} if variant=='one' else set(PEOPLE) if variant=='all' else {'person','third'}
    members=('person','other') if variant=='outside_second' else ('person',) if variant=='single_member' else (
        PEOPLE+('third',) if variant=='duplicate_member' else PEOPLE)
    def endpoint(who):return 'anchor' if variant=='different_end' and who=='third' else 'end'
    def part_for(who):return 'second_part' if variant=='different_internal_parts' and who=='third' else 'part'
    def available(who,plan,point):
        if variant=='unknown_second_capacity' and who=='third':return unknown()
        return who in changed and plan=='plan' and (SCENES.index(point)>=SCENES.index(endpoint(who)) or
            variant=='already_capable_second' and who=='third' and point=='before')
    def outcome(who,plan,start,end):return available(who,plan,start) and end==endpoint(who)
    def extent(scope,targets):
        if variant=='unknown_extent':return unknown()
        pair=({p for p in DOMAIN if scope(p)},{p for p in DOMAIN if targets(p)})
        if observed is not None:observed.append(pair)
        return True
    values=predecessor_model(doc,'baseline');values.update(arithmetic())
    values.update(zgroup=lambda:'group',zprocess=lambda:'process',zstart=lambda:'before',zend=lambda:'end',zanchor=lambda:'anchor',
        zactor=lambda:'other',ztarget=lambda:'person',zpart=lambda:'part',zextent=extent,
        mp=lambda group:SequenceValue(members if group=='group' else (), '"individual"'),
        aa=lambda who:who in PEOPLE,
        ab=lambda faculty,who,point:who in changed and (faculty,point)==('faculty',endpoint(who)),
        ac=lambda who,faculty,act,point:who in changed and (faculty,act,point)==('faculty','process',endpoint(who)),
        ad=lambda guide,who,act,point:variant=='guided_second' and (guide,who,act,point)==('other','third','process','end'),
        ae=available,af=outcome,ap=outcome,
        ia=lambda who,anchor,point:who in PEOPLE and anchor=='anchor' and point in SCENES,
        ic=lambda first,last,anchor:SCENES.index(first)<SCENES.index(last),
        ag=lambda act,first,last:(act,first,last)==('process','before','end'),
        la=lambda who,act,first,last:who in changed and (act,first,last)==(
            'other_process' if variant=='different_process' and who=='third' else 'process',
            'end' if variant=='different_start' and who=='third' else 'before',endpoint(who)),
        dg=lambda act,point:act in ('process','part','second_part') and point=='end',
        df=lambda who,act,point:point=='end' and (
            (who,act) in (('other','part'),('person','second_part')) if variant=='different_internal_parts' else
            who in (('outsider',) if variant=='external_actor_only' else ('person','other','outsider') if variant=='external_assistance' else ('person','other')) and act=='part'),
        h6a=lambda part,process,point:variant!='no_part' and part in ({'part','second_part'} if variant=='different_internal_parts' else {'part'}) and (process,point)==('process','end'),
        g3=lambda act,who,description,point:who in changed and not (variant=='missing_second_cause' and who=='third') and (
            act,symbol(description),point)==(part_for(who),'h4l','end'))
    return values


def source_checks():
    doc=source_document();rows={}
    for variant,(count,plural,all_members) in EXPECTED.items():
        seen=[];actual=evaluate(doc,source_model(doc,variant,seen),memoize=True)
        assert actual==[count>0,plural,all_members],(variant,actual)
        expected_changed=set(PEOPLE) if count==3 else {'person','third'} if count==2 else {'person'} if count==1 else set()
        assert seen and all(changed==expected_changed for _,changed in seen),(variant,seen)
        assert all(changed<=members for members,changed in seen)
        rows[variant]=dict(values=actual,changed=sorted(seen[0][1]),members=sorted(seen[0][0]))
    for variant in ('unknown_second_capacity','unknown_extent'):
        try:evaluate(doc,source_model(doc,variant),memoize=True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    # Evaluate a native causal-change witness without caching as well; no
    # definition is replaced with a primitive or a shortened expression.
    witness=deepcopy(doc);witness['statements']=[]
    witness=parse(format_graph(witness,'compact')+'q[k h6b[k zgroup[] k zactor[] k ztarget[] k zprocess[] k zpart[] k zstart[] k zend[] k zanchor[]]].')
    witness_values=source_model(witness,'one')
    assert evaluate(witness,witness_values)==evaluate(witness,witness_values,memoize=True)==[True]
    return dict(cases=rows,source_definitions_evaluated_without_lowering=True,source_evaluation_memoized=True,
        native_change_witness_agrees_without_memoization=True,unknown_inputs_refused=2)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    modal=load_catalog(ROOT,'data/graded-modality-basis-v1.json')
    for n,e in modal.entries.items():
        assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    assert all(item in new.lineage[-1]['caveats']['limitations'] for item in modal.lineage[-1]['caveats']['limitations'])
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-10]==old.document['declarations']
    for n,e in old.entries.items():assert new.entries[n]==e,n
    for i in (16,17,27,28,29,30,31):assert selection_binding(old,[i])==selection_binding(new,[i])
    return dict(existing_statements_and_meanings_preserved=True,new_primitives=0,new_collective_definitions=4,
        prior_modal_definitions_integrated=6,reviewed_statement_bindings_preserved=7,
        prior_modal_interpretation_limits_preserved=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_full_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    for name,body in build().items():assert (ROOT/name).read_text(encoding='utf-8')==body
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    cat=load_catalog(ROOT,BASIS)
    for name in (CORE,):load_catalog(ROOT,BASIS,document_path=name)
    previous=json.loads((ROOT/'reports/intragroup-change-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,previous['source_sha256'])
    modal=json.loads((ROOT/'reports/graded-modality-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,modal['source_sha256'])
    segment=deepcopy(previous['alignment']);segment.update(definitions=['rqsw','rqsx','rqsy','hzmw'],remaining=[
        'public audience and open discourse','dissemination of reasoned self-assessment and attitudes',
        'source-appropriate collective extent','freedom condition, comparison baseline and author attribution'])
    paths=set(cat.source_sha256)|set(build())|set(previous['source_sha256'])|set(modal['source_sha256'])|{
        'reports/intragroup-change-v1.json','reports/graded-modality-v1.json','scripts/compose_collective_change.py',
        'scripts/check_collective_change.py','tests/test_collective_change.py','docs/collective-change-v1.md',
        'scripts/check_scoped_counts.py','scripts/check_described_explanations.py','noema/constructed.py',
        'noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py',
        'noema/script.py','noema/meaning_catalog.py'}
    return dict(status='same_process_collective_extent_partial_source_component',document=FULL,
        generic=generic_checks(),source_cases=source_checks(),structure=structure(),roundtrips=True,
        alignment=segment,new_source_assertions=0,active_review_index_unchanged='data/semantic-review-index-v22.json',
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Collective scope and same-process internal changes checked')


if __name__=='__main__':main()
