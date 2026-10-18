"""Check one referenced public across permission and future qualification."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_audience_liberty as liberty
from scripts import check_existential_route_fields as prior
from scripts.compose_subject_bound_departure import closure
from scripts.compose_shared_public_scope import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,PROVIDERS,build
from scripts.compose_shared_future_period import CONDITION
from scripts.compose_existential_route_fields import SOURCE_PROVIDERS

REPORT=ROOT/'reports/shared-public-scope-v1.json'
UNKNOWN=prior.receipt.UNKNOWN


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=liberty.DOMAIN,situations=liberty.SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True,max_steps=5000000)]


def scope_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['rqu3'])
    doc=parse(format_graph(doc,'compact')+'r zaudience[] a.r zreference[] d.r zperson[] a.r zpoint[] d.'
        'q[c[k rqu3[k zaudience[] k zreference[]]][k zperson[] k zpoint[]]].')
    memberships={('group','anchor'):{'person','other'},('group','before'):{'person'},('plan','anchor'):{'part'}}
    count=0
    for group,reference,person,point in product(('group','plan'),('before','anchor'),('person','other','part'),liberty.SCENES):
        seen=[]
        def members(g,p,r):seen.append((g,p,r));return p in memberships.get((g,r),set())
        values=dict(zaudience=lambda:group,zreference=lambda:reference,zperson=lambda:person,zpoint=lambda:point,h6t=members)
        assert evaluate(doc,values)==[person in memberships.get((group,reference),set())]
        assert seen and set(seen)=={(group,person,reference)};count+=1
    return dict(public_reference_person_and_opportunity_combinations=count,
        evaluation_point_does_not_replace_reference=True,nonhuman_membership_not_silently_filtered=True)


@lru_cache(maxsize=1)
def document():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    text='''
r zaudience[] a.r zreference[] d.r zsource[] a.r zpoint[] d.r zbranch[] d.
r zorigins[d] d.r zcases[d] c.r zsubgroup[a d] c.r zqualified[a d] c.r zlegacy[a d] c.
d zforecast[branch d] e[b base[
 k rqtj[k rqtw[k zaudience[] v branch] k rqtx[v branch] v base
 i[point d][w[f person a[y[c[k rqu3[k zaudience[] k zreference[]]][v person v point]][k aa[v person]]]][
 k rqti[v point k rqu3[k zaudience[] k zreference[]] p zsubgroup p zqualified]]]]
]].
q[k hzna[k zaudience[] k zreference[] k zsource[] k zpoint[]]].
q[t[k zforecast[k zbranch[]]][k zorigins[k zbranch[]]]].
q[k hzp7[k zaudience[] k zreference[] k zsource[] k zaudience[] p zorigins p zcases p zforecast]].
'''
    return parse(format_graph(doc,'compact')+text)


def model(doc,members=('person','other'),qualified=('person','other'),permitted=('person','other'),seen=None):
    values=liberty.model(doc,'actual_permission',point='before')
    allowed=values['h7b'];original_scope=values['h6t']
    def scope(group,person,reference):
        if seen is not None:seen.append((group,person,reference))
        if (group,reference)==('group','anchor'):return person in members
        return original_scope(group,person,reference)
    values.update(h6t=scope,h7b=lambda source,person,*args:person in permitted and allowed(source,person,*args),
        zbranch=lambda:'anchor',zorigins=lambda b:'before',zcases=lambda b:b=='anchor',
        zsubgroup=lambda p,t:p=='person',zqualified=lambda p,t:p in qualified,
        zlegacy=lambda p,t:p in ('person','other'),
        h7q=lambda frame,branch,point:(frame,branch)==('group','anchor') and point in liberty.SCENES,
        ic=lambda first,last,branch:branch=='anchor' and first in liberty.SCENES and last in liberty.SCENES and liberty.SCENES.index(first)<liberty.SCENES.index(last))
    return values


def connection_checks():
    doc=document();count=0
    for bits in product((False,True),repeat=6):
        members={p for p,flag in zip(('person','other'),bits[:2]) if flag}
        qualified={p for p,flag in zip(('person','other'),bits[2:4]) if flag}
        permitted={p for p,flag in zip(('person','other'),bits[4:]) if flag}
        permission=bool(members) and members<=permitted
        forecast=len(members&qualified)>=2 and 'person' in members&qualified
        seen=[];actual=evaluate(doc,model(doc,members,qualified,permitted,seen))
        assert actual==[permission,forecast,permission and forecast],(bits,actual)
        assert seen and all((g,r)==('group','anchor') for g,p,r in seen);count+=1
    # Formerly a second, independently supplied population could supply the
    # missing second thinker. Keep it positive beside the corrected forecast.
    contrasted=parse(format_graph(doc,'compact')+'q[k rqti[k zpoint[] p zlegacy p zsubgroup p zqualified]].')
    result=evaluate(contrasted,model(contrasted,members=('person',)))
    assert result==[True,False,False,True],result
    invalid=evaluate(doc,model(doc,members=('person','other','process')))
    assert invalid==[False,False,False],invalid
    for name in ('h6t','zaudience','zreference','h7b','zqualified'):
        values=model(doc);values[name]=UNKNOWN
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    return dict(membership_qualification_permission_combinations=count,
        native_public_permission_and_future_quantifiers_executed=True,
        independent_population_cannot_supply_missing_thinker=result,nonhuman_public_refused=invalid,
        unknown_inputs_refused=5,qualification_is_test_predicate_not_full_dissemination=True,all_checks_eager=True)


def attribution_checks():
    thinkers=prior.receipt.thinkers
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));prior.merge(doc,thinkers.native_document())
    doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'r zresponsepreferred[a d d d] c.')
    values,_=thinkers.prior.conditional.closed.arguments()
    values.update(state=prior.receipt.STATE.replace('r[p zpreferred]','r[p zresponsepreferred]'),thinkpreferred='p zpreferred')
    supplied=' '.join('i[branch d]['+values[n]+']' for n,t in PROVIDERS)
    frame='r b[k rqu4['+thinkers.prior.attributed.previous.prior.CONDITION_ARGS+' '+supplied+']]'
    doc=parse(format_graph(doc,'compact')+'q[k hzpy['+frame+' r[k zgoverned[]] r[p zappointed] r[p zguardian]]].')
    rows={}
    for reported,backgrounded in product((False,True),repeat=2):
        seen=[];model=thinkers.prior.attributed.previous.unknown_values(doc)
        model.update(hzp5=lambda:'person',wa=lambda:'authority',hzpz=lambda:'person',hzq2=lambda:'authority',hzp3=lambda:'outside')
        model.update(thinkers.prior.attributed.relation_values(reported,backgrounded,seen))
        actual=thinkers.prior.attributed.evaluate(doc,model);assert actual==[reported and backgrounded]
        refs=_references(seen[0][3])
        assert {'rqu4','hzr2','hzhb','zpermissionaudience','zpermissionreference','zgoverned'}<=refs
        assert not {'zbranchmembers','zmembers'}&refs
        assert seen[0][3]==seen[1][3] and {'rqts','hzpt'}<=_references(seen[1][4]);rows[str((reported,backgrounded))]=actual
    return dict(native_closed_attribution=rows,guardian_governed_group_kept_separate=True,
        twelve_remaining_branch_providers=len(PROVIDERS),world_truth_not_executed=True,
        whole_group_existential_truth_not_inferred=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-2]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    defs={d['name']:d for d in new.document['declarations']};wrapper=defs['rqu4']
    assert wrapper['body']['symbol']=='rqu2' and len(wrapper['parameters'])==len(CONDITION)+12
    args=wrapper['body']['arguments'];names={n:p['name'] for (n,t),p in zip(CONDITION+PROVIDERS,wrapper['parameters'],strict=True)}
    assert args[:len(CONDITION)]==[dict(kind='variable',name=names[n]) for n,t in CONDITION]
    for (n,t),argument in zip(SOURCE_PROVIDERS,args[len(CONDITION):],strict=True):
        if n=='members':
            assert argument['kind']=='lambda' and argument['body']['symbol']=='rqu3'
            assert argument['body']['arguments']==[dict(kind='variable',name=names[n]) for n in ('permissionaudience','permissionreference')]
        else:assert argument==dict(kind='variable',name=names[n])
    assert _references(defs['rqu3'])=={'h6t'}
    return dict(new_compositions=2,new_primitives=0,existing_statements=34,seven_review_bindings_preserved=True,
        permission_and_membership_use_identical_public_and_reference=True,source_branch_providers_before=13,source_branch_providers_after=12,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/existential-route-fields-v1.json').read_text(encoding='utf-8'))
    for p,sha in previous['source_sha256'].items():assert digest((ROOT/p).read_bytes())==sha
    paths=set(outputs)|set(load_catalog(ROOT,BASIS).source_sha256)|set(previous['source_sha256'])|{
        'reports/existential-route-fields-v1.json','scripts/check_audience_liberty.py',
        'scripts/compose_shared_public_scope.py','scripts/check_shared_public_scope.py','tests/test_shared_public_scope.py','docs/shared-public-scope-v1.md'}
    results={}
    for name,fn in [('scope',scope_checks),('connection',connection_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0011')
    return dict(status='permission_and_future_population_share_reference_checked',document=FULL,**results,roundtrips=True,
        new_source_assertions=0,new_covered_characters=0,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=137,end=176,source=unit['text'][137:176],
            definitions=['rqu3','rqu4'],status='partial_same_public_prediction',full_semantic_equivalence=False),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Shared public scope checked',flush=True)


if __name__=='__main__':main()
