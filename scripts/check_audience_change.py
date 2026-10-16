"""Check audience scope, reference context, and compatibility with valid lists."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_collective_change as prior
from scripts.compose_subject_bound_departure import closure
from scripts.compose_audience_change import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,build

REPORT=ROOT/'reports/audience-change-v1.json'
DOMAIN,SCENES=prior.DOMAIN,prior.SCENES
EXTRA={
 'other_audience':(0,False,False),'other_context':(0,False,False),
 'end_success_only':(2,True,False),'unreached_reader':(3,True,False),
 'nonhuman_scope':(0,False,False),'wrong_audience_argument':(0,False,False),
}


@lru_cache(maxsize=2)
def document(joined=False):
    doc=parse((ROOT/(FULL if joined else CORE)).read_text(encoding='utf-8'))
    doc['statements']=[]
    if joined:doc['declarations']=closure(doc,['hzmz','hzmw','rqsx','rqsy'])
    text=format_graph(doc,'compact')+'''
r zgroup[] a.r zprocess[] a.r zstart[] d.r zend[] d.r zanchor[] d.
r zextent[h[a] c h[a] c] c.r zactor[] a.r ztarget[] a.r zpart[] a.
'''
    for root in (('hzmz','hzmw') if joined else ('hzmz',)):
        for extent in ('zextent','rqsy','rqsx'):
            text+='q[k '+root+'[k zgroup[] k zprocess[] k zstart[] k zend[] k zanchor[] p '+extent+']].'
    return parse(text)


def model(doc,variant='two',seen=None,scope_calls=None,legacy=False):
    base='all' if variant=='unreached_reader' else 'two' if variant in EXTRA or variant in ('unknown_scope','unknown_human') else variant
    values=prior.source_model(doc,base,seen)
    members={'person','other'} if base=='outside_second' else {'person'} if base=='single_member' else set(prior.PEOPLE)
    if variant=='unreached_reader':
        members.add('outsider');values['aa']=lambda p:p in (*prior.PEOPLE,'outsider')
    if variant=='nonhuman_scope':members.add('process')
    if variant=='wrong_audience_argument':values['zgroup']=lambda:'other_process'
    if variant=='unknown_human':
        known=values['aa']
        values['aa']=lambda p:prior.unknown() if p=='third' else known(p)
    def scope(group,person,context):
        if variant=='unknown_scope':return prior.unknown()
        if scope_calls is not None:scope_calls.append((group,context))
        wanted_group='other_process' if variant=='other_audience' else 'group'
        wanted_context='end' if variant=='other_context' else 'anchor'
        if variant=='end_success_only' and (group,context)==('group','end'):return person in ('person','third')
        return (group,context)==(wanted_group,wanted_context) and person in members
    values['h6t']=scope
    # These facts are deliberately unavailable. They are not dependencies of
    # the audience construction; an accidental evaluation must fail.
    if not legacy:values['mp']=prior.unknown
    for name in ('h6e','h6g','h6n'):values[name]=prior.unknown
    return values


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zgroup[] a.r zcontext[] d.r zscope[a a d] c.r zeligible[a] c.
q[k rqsz[k zgroup[] k zcontext[] p zscope p zeligible]].
''')
    count=0;domain=('a','b','group')
    for membership,eligibility in product(product((False,True),repeat=2),repeat=2):
        members={p for p,yes in zip(domain,membership) if yes};eligible={p for p,yes in zip(domain,eligibility) if yes}
        calls=[]
        def scope(group,person,context):
            calls.append((group,context));return (group,context)==('group','anchor') and person in members
        values=dict(zgroup=lambda:'group',zcontext=lambda:'anchor',zscope=scope,zeligible=lambda p:p in eligible)
        assert prior.evaluate(doc,values,domain,('anchor','other'))==[members<=eligible]
        assert calls and set(calls)=={('group','anchor')};count+=1
    return dict(scope_eligibility_combinations=count,reference_object_and_context_fixed=True,empty_scope_not_claimed_nonempty=True)


def source_checks():
    doc=document();rows={};expected={**prior.EXPECTED,**EXTRA}
    expected['duplicate_member']=(2,True,False)
    for variant,(count,plural,all_members) in expected.items():
        seen=[];calls=[];actual=prior.evaluate(doc,model(doc,variant,seen,calls),memoize=True)
        assert actual==[count>0,plural,all_members],(variant,actual)
        wanted=set(prior.PEOPLE) if count==3 else {'person','third'} if count==2 else {'person'} if count==1 else set()
        assert seen and all(changed==wanted for _,changed in seen),(variant,seen)
        assert all(context=='anchor' for _,context in calls),(variant,calls)
        assert {g for g,_ in calls}=={'other_process' if variant=='wrong_audience_argument' else 'group'}
        rows[variant]=dict(values=actual,audience=sorted(seen[0][0]),changed=sorted(seen[0][1]))
    assert rows['unreached_reader']['audience']==sorted((*prior.PEOPLE,'outsider'))
    assert rows['end_success_only']==rows['two']
    for variant in ('unknown_scope','unknown_human','unknown_second_capacity','unknown_extent'):
        try:prior.evaluate(doc,model(doc,variant),memoize=True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    joined=document(True);compatibility={}
    for variant in ('one','two','all','guided_second','duplicate_member'):
        actual=prior.evaluate(joined,model(joined,variant,legacy=True),memoize=True)
        assert actual[:3]==rows[variant]['values']
        if variant=='duplicate_member':assert actual[3:]==[False]*3
        else:assert actual[:3]==actual[3:]
        compatibility[variant]=actual
    witness=deepcopy(doc);witness['statements']=[]
    witness=parse(format_graph(witness,'compact')+
        'q[k hzmx[k zgroup[] k zactor[] k ztarget[] k zprocess[] k zpart[] k zstart[] k zend[] k zanchor[] p h6t]].')
    values=model(witness,'one')
    assert prior.evaluate(witness,values)==prior.evaluate(witness,values,memoize=True)==[True]
    return dict(audience_contrasts=rows,legacy_list_comparisons=compatibility,unknown_inputs_refused=4,
        primitive_receipt_understanding_access_and_list_not_evaluated=True,source_evaluation_memoized=True,
        native_witness_agrees_without_memoization=True,source_definitions_not_lowered_or_replaced=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-4]==old.document['declarations']
    for n,e in old.entries.items():assert new.entries[n]==e,n
    for i in (16,17,27,28,29,30,31):assert selection_binding(old,[i])==selection_binding(new,[i])
    core=load_catalog(ROOT,BASIS,document_path=CORE)
    assert not {'mp','h6b','hzmw','h6e','h6g','h6n','ce'}&set(core.entries)
    assert {'h6t','aa','rda','fo','bf','h4l','la','h6a','g3'}<=set(core.entries)
    # The new rda application is exactly the old application with only the
    # population predicate replaced; ability and causation are not weakened.
    def calls(node,symbol):
        if isinstance(node,dict):
            return ([node] if node.get('kind')=='call' and node.get('symbol')==symbol else [])+sum((calls(v,symbol) for v in node.values()),[])
        if isinstance(node,list):return sum((calls(v,symbol) for v in node),[])
        return []
    before=calls(new.entries['h6b']['declaration']['body'],'rda')[0]['arguments']
    after=calls(new.entries['hzmx']['declaration']['body'],'rda')[0]['arguments']
    assert len(before)==len(after)==19
    # Remove only the two intended population changes, then alpha-normalize
    # complete declarations. All other guards and rda arguments must agree.
    predecessor=new.entries['h6b']['declaration']
    def normalize_remainder(name):
        decl=deepcopy(new.entries[name]['declaration']);decl['name']='zcompare'
        decl['parameters']=deepcopy(predecessor['parameters'])
        decl['body']['arguments'][0]=deepcopy(predecessor['body']['arguments'][0])
        calls(decl['body'],'rda')[0]['arguments'][2]=deepcopy(before[2])
        wrapper=deepcopy(new.document);wrapper['statements']=[];wrapper['declarations'].append(decl)
        return parse(format_graph(wrapper,'compact'))['declarations'][-1]
    assert normalize_remainder('h6b')==normalize_remainder('hzmx')
    return dict(existing_statements=32,existing_meanings_and_seven_review_bindings_preserved=True,new_primitives=0,new_definitions=4,
        list_and_receipt_dependencies_absent=True,existing_native_ability_and_causation_reused=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    for name,body in build().items():assert (ROOT/name).read_text(encoding='utf-8')==body
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    cat=load_catalog(ROOT,BASIS)
    previous=json.loads((ROOT/'reports/collective-change-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,previous['source_sha256'])
    segment=deepcopy(previous['alignment']);segment.update(definitions=['rqsz','hzmx','hzmy','hzmz'],remaining=[
        'social basis of the intended public audience','dissemination of reasoned self-assessment and attitudes',
        'source-appropriate collective extent','freedom condition, comparison baseline and author attribution'])
    paths=set(cat.source_sha256)|set(build())|set(previous['source_sha256'])|{
        'reports/collective-change-v1.json','scripts/compose_audience_change.py','scripts/check_audience_change.py',
        'tests/test_audience_change.py','docs/audience-change-v1.md','docs/public-use-link-v1.md'}
    return dict(status='predicate_audience_change_partial_source_component',document=FULL,generic=generic_checks(),
        source_cases=source_checks(),structure=structure(),roundtrips=True,alignment=segment,new_source_assertions=0,
        active_review_index_unchanged='data/semantic-review-index-v22.json',verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Intended audience scope and native capacity changes checked without population lists')


if __name__=='__main__':main()
