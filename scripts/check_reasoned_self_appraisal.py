"""Verify self-valuation and assent to an explicitly described universal task."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_described_explanations import symbol
from scripts.compose_reasoned_self_appraisal import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,READING,MEANINGS,build

REPORT=ROOT/'reports/reasoned-self-appraisal-v1.json'
DOMAIN=('person','other','selfjudge','normjudge','reason','criterion','grade','topic','source','role')
SCENES=('before','now')
REFS='r[k zcriterion[]] r[k zsubject[]] r[k zsource[]] r[k zrole[]]'
CLAIM='k hzns[r[k zsource[]] r[k zrole[]]]'
PROFILE='k hznv['+REFS+']'
FIXTURE='''
r zperson[] a.r zother[] a.r zcriterion[] a.r zsubject[] a.r zsource[] a.r zrole[] a.r zpoint[] d.
r zprocess[] a.r zpart[] a.r zstart[] d.r zhistory[d] c.r zbefore[d d] c.r zothersource[] a.r zothercriterion[] a.
'''


def unknown(*args):raise ValueError('Unknown interpretation is required')


def evaluate(doc,model,people=DOMAIN,memoize=True):
    values={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=SCENES,primitives=values,
        max_steps=8000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zp[] a.r zj[] a.r zs[] a.r zt[] d.r za[a a d] c.r zb[a a d] c.r zc[a a d] c.r zd[a a d] c.
q[k rqtf[k zp[] k zj[] k zs[] k zt[] p za p zb p zc p zd]].
''')
    for flags in product((False,True),repeat=4):
        judge,about,used,support=flags
        values=dict(zp=lambda:'person',zj=lambda:'selfjudge',zs=lambda:'topic',zt=lambda:'now',
            za=lambda p,j,t:judge and (p,j,t)==('person','selfjudge','now'),
            zb=lambda j,s,t:about and (j,s,t)==('selfjudge','topic','now'),
            zc=lambda j,r,t:used and (j,r,t)==('selfjudge','reason','now'),
            zd=lambda r,j,t:support and (r,j,t)==('reason','selfjudge','now'))
        assert evaluate(doc,values,memoize=False)==[all(flags)]
    values['zd']=lambda r,j,t:(r,j,t)==('other','selfjudge','now')
    assert evaluate(doc,values,memoize=False)==[False]
    return dict(four_relation_combinations=16,different_supporting_reason_refused=True,uncached=True)


@lru_cache(maxsize=12)
def document(kind='profile',arguments='l[a][k zperson[]]'):
    queries={
        'self':'t[k hznr[k zperson[] k zcriterion[]]][k zpoint[]]',
        'assent':'t[k hznt[k zperson[] k zsubject[] '+CLAIM+']][k zpoint[]]',
        'profile':'t[c[s['+PROFILE+']][k zperson[]]][k zpoint[]]',
        'norm':'t[c[k hznq[k zsource[] k zrole[]]][k zsubject[]]][k zpoint[]]',
        'goal':'t[k hznp['+arguments+']][k zpoint[]]',
        'change':'k rqte[p zhistory p zbefore k zperson[] k zprocess[] k zpart[] k zstart[] k zpoint[] '+PROFILE+' p ag p la p dg p h6a p g3]',
    }
    return parse((ROOT/CORE).read_text(encoding='utf-8')+FIXTURE+'q['+queries[kind]+'].')


def reference(name):return dict(kind='call',symbol=name,arguments=[])


def claim_syntax(source='zsource'):
    return dict(kind='apply',function=dict(kind='function_ref',symbol='hznq'),arguments=[reference(source),reference('zrole')])


def profile_syntax(criterion='zcriterion'):
    return dict(kind='apply',function=dict(kind='function_ref',symbol='hznu'),arguments=[reference(criterion),reference('zsubject'),
        dict(kind='quote',body=reference('zsource')),dict(kind='quote',body=reference('zrole'))])


def model(doc,variant='baseline',norm_flags=(False,False),seen=None):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    active=lambda point:point=='now' or variant=='already_acquired'
    def judge(person,judgment,point):
        expected='other' if (variant=='different_self_judge' and judgment=='selfjudge' or variant=='different_norm_judge' and judgment=='normjudge') else 'person'
        return active(point) and person==expected and judgment in ('selfjudge','normjudge')
    def about(judgment,subject,point):
        expected='person' if judgment=='selfjudge' else 'topic'
        if variant=='different_self_subject' and judgment=='selfjudge' or variant=='different_norm_subject' and judgment=='normjudge':expected='other'
        return active(point) and judgment in ('selfjudge','normjudge') and subject==expected
    def uses(judgment,reason,point):
        return active(point) and reason=='reason' and judgment in ('selfjudge','normjudge') and not (
            variant=='no_self_reason' and judgment=='selfjudge' or variant=='no_norm_reason' and judgment=='normjudge')
    def supports(reason,judgment,point):
        expected='other' if variant=='different_support' and judgment=='selfjudge' else 'reason'
        return active(point) and reason==expected and judgment in ('selfjudge','normjudge') and not (
            variant=='no_self_support' and judgment=='selfjudge' or variant=='no_norm_support' and judgment=='normjudge')
    def appraisal(judgment,target,criterion,assessment,point):
        return active(point) and variant!='no_appraisal' and (judgment,target,criterion,assessment)==(
            'normjudge' if variant=='other_appraisal_act' else 'selfjudge',
            'other' if variant=='other_appraised_person' else 'person',
            'other' if variant=='other_criterion' else 'criterion',
            'role' if variant=='different_grade' else 'grade')
    def assent(judgment,subject,description,sign,point):
        if seen is not None:seen.add(('assent',description.syntax))
        expected=claim_syntax('zothersource' if variant=='different_claim' else 'zsource')
        return active(point) and variant!='no_assent' and (judgment,subject,sign)==(
            'selfjudge' if variant=='other_assent_act' else 'normjudge','topic',variant!='negative_assent') and json.loads(description.syntax)==expected
    def required(source,person,role,description,bindings,sign,point):
        if seen is not None:seen.add(('norm',person,tuple(bindings.items),symbol(description)))
        return person in ('person','other') and norm_flags[('person','other').index(person)] and (
            source,role,symbol(description),tuple(bindings.items),sign,point)==('source','role','hznp',(person,),True,'now')
    def produces(part,target,description,point):
        expected=profile_syntax('zothercriterion' if variant=='different_causal_target' else 'zcriterion')
        return variant!='no_cause' and (part,target,point)==('role','person','now') and json.loads(description.syntax)==expected
    values.update(zperson=lambda:'person',zother=lambda:'other',zcriterion=lambda:'criterion',zsubject=lambda:'topic',
        zsource=lambda:'source',zrole=lambda:'role',zpoint=lambda:'now',zprocess=lambda:'source',zpart=lambda:'role',
        zstart=lambda:'before',zhistory=lambda point:True,zbefore=lambda a,b:a=='before' and b=='now',
        zothersource=lambda:'source',zothercriterion=lambda:'criterion',
        aa=lambda person:person in ('person','other'),fa=judge,fb=about,fc=uses,fd=supports,hznm=appraisal,hznn=assent,h7k=required,
        ag=lambda p,s,e:(p,s,e)==('source','before','now'),la=lambda t,p,s,e:(t,p,s,e)==('person','source','before','now'),
        dg=lambda part,point:part in ('source','role') and point=='now',h6a=lambda a,p,t:(a,p,t)==('role','source','now'),g3=produces)
    return values


def source_checks():
    rows={}
    variants=('baseline','different_self_judge','different_norm_judge','different_self_subject','different_norm_subject',
        'no_self_reason','no_norm_reason','different_support','no_self_support','no_norm_support','no_appraisal',
        'other_appraisal_act','other_appraised_person','other_criterion','different_grade','different_claim','no_assent',
        'negative_assent','other_assent_act')
    doc=document()
    for variant in variants:
        actual=evaluate(doc,model(doc,variant))
        assert actual==[variant in ('baseline','different_grade')],(variant,actual)
        rows[variant]=actual
    assert evaluate(doc,model(doc),memoize=False)==[True]
    assert evaluate(doc,model(doc,'different_claim'),memoize=False)==[False]
    joint=deepcopy(doc);joint['statements']+=document('norm')['statements']
    comparisons={}
    for flags in product((False,True),repeat=2):
        seen=set();actual=evaluate(joint,model(joint,norm_flags=flags,seen=seen))
        assert actual==[True,all(flags)],(flags,actual)
        assert ('norm','person',('person',),'hznp') in seen
        if flags[0]:assert ('norm','other',('other',),'hznp') in seen
        assert all(row[2]==(row[1],) and row[3]=='hznp' for row in seen if row[0]=='norm')
        assert all(json.loads(row[1])==claim_syntax() for row in seen if row[0]=='assent')
        comparisons[str(flags)]=actual
    return dict(contrasts=rows,assent_and_actual_universal_requirement=comparisons,
        task_not_executed=True,each_person_bound_to_own_task=True,qualitative_grade_not_fixed=True,
        same_truth_or_referent_does_not_erase_description_identity=True,uncached_positive_and_negative_agree=True)


def goal_checks():
    people=('person','other','selfjudge','reason','criterion');rows={}
    for label,args,variant in (('own_task','l[a][k zperson[]]','baseline'),('other_person','l[a][k zother[]]','baseline'),
        ('empty','l[a][]','baseline'),('extra_person','l[a][k zperson[] k zother[]]','baseline'),
        ('no_support','l[a][k zperson[]]','no_self_support'),('guided','l[a][k zperson[]]','guided')):
        doc=document('goal',args);values=model(doc,variant)
        values.update(ab=lambda faculty,person,point:(faculty,person,point)==('criterion','person','now'),
            ac=lambda person,faculty,judgment,point:(person,faculty,judgment,point)==('person','criterion','selfjudge','now'),
            ad=lambda other,person,judgment,point:variant=='guided' and (other,person,judgment,point)==('other','person','selfjudge','now'))
        actual=evaluate(doc,values,people)
        assert actual==[label=='own_task'],(label,actual);rows[label]=actual
    return dict(native_task_contrasts=rows,source_thinking_definition_executed=True)


def change_checks():
    doc=document('change');rows={}
    for variant in ('baseline','already_acquired','no_cause','different_causal_target','no_appraisal','no_assent'):
        actual=evaluate(doc,model(doc,variant))
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,same_constructed_state_used_for_acquisition_and_causation=True,
        self_approval_wrapper_not_used=True)


def unknown_checks():
    cases=[('profile',name) for name in ('fa','fb','fc','fd','hznm','hznn')]+[('norm','h7k'),('change','g3'),('goal','ab')]
    for kind,name in cases:
        doc=document(kind);values=model(doc);values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error),(kind,name,error)
        else:raise AssertionError((kind,name))
    return dict(unknown_inputs_refused=len(cases))


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-11]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    earlier=parse((ROOT/'examples/v016/kant-thinking-disposition.noema').read_text(encoding='utf-8'))
    thinking=next(d for d in earlier['declarations'] if d['name']=='iahthinking')
    current=new.entries['hzno']['declaration']
    assert all(thinking[key]==current[key] for key in ('parameters','result','body'))
    return dict(new_definitions=9,new_primitives=2,existing_statements=32,seven_review_bindings_preserved=True,
        independent_thinking_body_reused_exactly=True,generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def alignment():
    path=ROOT/'artifacts/written-units-v1/kant-1784.json'
    record=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    assert digest(path.read_bytes())==record['works']['kant-1784']['units_sha256']
    unit=next(u for u in json.loads(path.read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0011')
    text=unit['text'];assert digest(text.encode('utf-8'))==unit['text_sha256']
    start=text.index('vernünftigen Schätzung');end=text.index('selbst zu denken',start)+len('selbst zu denken')
    return dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=start,end=end,source=text[start:end],
        definitions=list(MEANINGS),status='partial_explicit_reading',full_semantic_equivalence=False,
        remaining=['source-appropriate valuation criterion and normative reading','spirit/disposition beyond individual judgments',
            'full dissemination, future modality and author attribution'])


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            form=format_graph(doc,notation);assert parse(form)==parse(transcribe(form,alphabet='v2'))==doc
    reading=json.loads((ROOT/READING).read_text(encoding='utf-8'))
    for row in reading['sources']:assert digest((ROOT/row['artifact']).read_bytes())==row['artifact_sha256']
    catalog=load_catalog(ROOT,BASIS)
    paths=set(catalog.source_sha256)|set(outputs)|{READING,
        'scripts/compose_reasoned_self_appraisal.py','scripts/check_reasoned_self_appraisal.py',
        'tests/test_reasoned_self_appraisal.py','docs/reasoned-self-appraisal-v1.md',
        'scripts/compose_subject_bound_departure.py','scripts/check_described_explanations.py',
        'examples/v016/kant-thinking-disposition.noema','data/thinking-disposition-reading-review-v1.json',
        'artifacts/written-units-v1/kant-1784.json','reports/written-units-v1.json',
        'noema/constructed_semantics.py','noema/constructed_discourse.py','noema/constructed.py','noema/meaning_catalog.py'}
    paths.update(row['artifact'] for row in reading['sources'])
    return dict(status='reasoned_self_appraisal_and_normative_calling_partial_reading',document=FULL,
        generic=generic_checks(),source=source_checks(),goal=goal_checks(),change=change_checks(),unknowns=unknown_checks(),
        structure=structure(),roundtrips=True,alignment=alignment(),new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Self-appraisal, reasoned assent, universal own-task binding and acquisition checked')


if __name__=='__main__':main()
