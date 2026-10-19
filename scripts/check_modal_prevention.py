"""Contrast caused permission absence with actual nonperformance."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_modal_prevention import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_guarded_walking_scope import model as previous_model,PEOPLE
from scripts.check_prevented_attempt import SCENES,ref
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v78.json'
REPORT='reports/modal-prevention-v1.json'
AUDIT='data/modal-prevention-reading-v1.json'
DOC='docs/modal-prevention-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
SELECTION=[9,35,36,46,47,48,49]
CHANGED=[35,36,47,48,49]


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def comparison():
    return fixture(['hztr','r2am'],'r za[] d.q[t[k hztr[k db[]]][k za[]]].q[t[k r2am[k db[]]][k za[]]].')


def values(d,allowed=False,attempt=False,norm_cause=True,variant='baseline'):
    v=previous_model(d,variant if variant in ('no_conditioning_result','no_warning') else 'baseline')
    original=v['g3']
    def produces(act,p,g,s):
        if ref(g,'r2ah'):
            return norm_cause and p in (('other',) if variant=='other_norm_person' else ('person','other')) \
                and (act,s)==('blocking_act','actual' if variant=='other_norm_time' else 'prior')
        return original(act,p,g,s) and not(variant=='no_nontrial_cause' and ref(g,'hzsm'))
    def goal(g,b):return symbol(g) in ('hztm','r2ai') and b.items in (('person',),('other',))
    v.update(g3=produces,h7l=lambda *args:allowed,
        ei=lambda p,g,s:attempt and (p,s)==('person','prior') and ref(g,'bb'),
        hztk=lambda group,act,g,b,aspect,s:(group,act,s)==('guards','blocking_act','prior')
            and goal(g,b) and aspect in ('detailone','detailtwo'),
        hztj=lambda actor,act,g,b,aspect,s:
            (actor,act,s)==('guardone' if aspect=='detailone' else 'guardtwo','blocking_act','prior')
            and (b.items==('person','other') if ref(g,'r2ai') and variant=='other_norm_bindings' else goal(g,b))
            and aspect in ('detailone','detailtwo') and not(ref(g,'r2ai') and (
                variant=='missing_norm_attention' and aspect=='detailtwo')),
        hztl=lambda actor,act,g,b,s:actor in ('guardone','guardtwo') and (act,s)==('blocking_act','prior')
            and goal(g,b) and not(ref(g,'r2ai') and variant=='no_norm_purpose'))
    return v


def scope_checks():
    rows=[]
    for allowed,attempt,cause in product((False,True),repeat=3):
        actual=evaluate(comparison(),values(comparison(),allowed,attempt,cause),PEOPLE,SCENES,True)
        assert actual==[not allowed and not attempt,not allowed and cause],(allowed,attempt,cause,actual)
        rows.append(dict(allowed=allowed,actual_attempt=attempt,norm_cause=cause,old_and_new=actual))
        print('scope '+str((allowed,attempt,cause))+' checked',flush=True)
    return dict(combinations=rows,unpermitted_but_attempted_countermodel=True,
        nonattempt_and_accidental_permission_absence_not_sufficient=True,
        actual_current_old_and_new_claims_executed=True,definitions_replaced_by_primitives=False)


def binding_checks():
    expected={'baseline':[True,True],'missing_norm_attention':[True,False],'other_norm_bindings':[True,False],
        'no_norm_purpose':[True,False],'no_nontrial_cause':[False,True],'other_norm_person':[True,False],
        'other_norm_time':[True,False],'no_conditioning_result':[False,False],'no_warning':[False,False]}
    rows={}
    for name,wanted in expected.items():
        actual=evaluate(comparison(),values(comparison(),variant=name),PEOPLE,SCENES,True)
        assert actual==wanted,(name,actual,wanted);rows[name]=actual
        print('binding '+name+' checked',flush=True)
    return dict(contrasts=rows,result_attention_and_purpose_share_the_normative_goal=True,
        participants_and_recipients_bound=True,pure_memoization=True)


def unknown_checks():
    d=fixture(['r2am'],'r za[] d.q[t[k r2am[k db[]]][k za[]]].')
    v=values(d)
    # uq/ur also participate in selecting the audience's existing risk
    # appraisals. Keep those facts; f4 leaves the conditional warning unknown.
    for name in ('ei','hzio','f5','ac','f4'):
        v[name]=unknown
    assert evaluate(d,v,PEOPLE,SCENES,True)==[True]
    for name in ('h7l','g3','hztj','hztl'):
        v=values(d)
        if name=='g3':
            old=v[name]
            v[name]=lambda act,p,g,s:unknown() if ref(g,'r2ah') else old(act,p,g,s)
        else:v[name]=unknown
        try:evaluate(d,v,PEOPLE,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(actual_trial_courage_success_and_warning_truth_left_unknown=True,
        unknown_primitives=['ei','hzio','f5','ac','f4'],audience_risk_appraisal_facts_retained=True,
        required_unknown_inputs_refused=4)


def presentation(d,variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    def claim(c):
        return json.loads(c.syntax)==dict(kind='call',symbol='hztr' if variant=='old_claim' else 'r2am',
            arguments=[dict(kind='call',symbol='db',arguments=[])])
    def aligns(n,a,c,t,b,s):
        omitted={'missing_confinement':'r2af','missing_step':'rqzx','missing_quiet':'rqz7'}.get(variant)
        return (n,a,s)==('clause','author','context') and claim(c) \
            and symbol(t)==('rqzw' if variant=='old_target' else 'r2an') \
            and symbol(b) in ('r2af','rqzx','rqz7') and symbol(b)!=omitted
    v.update(db=lambda:'guards',hzsq=lambda:'clause',wa=lambda:'author',wh=lambda:'context',
        qp=lambda:'livestock',dq=lambda:'previous',
        qa=lambda n,a,t,b,s:(n,a,symbol(t),symbol(b),s) in (
            ('livestock','author','qj','qk','context'),('clause','author','eu','rqy4','context')),
        uc=lambda n,a,c,s:(n,a,s)==('clause','author','context') and claim(c),
        ue=lambda a,b,s:(a,b,s)==('previous','clause','context'),hzyb=aligns,
        hzye=lambda n,a,c,p,f,s:variant!='missing_insistence' and claim(c) and
            (n,a,p,symbol(f),s)==('clause','author','author' if variant=='wrong_viewpoint' else 'guards','rqzx','context'))
    return v


def attribution_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));people=('guards','clause','author','livestock','previous','other');times=('context',)
    missing={'baseline':[],'old_claim':[1,2,4,5,6],'old_target':[2,4,5,6],
        'missing_confinement':[2],'missing_step':[4,6],'missing_quiet':[5],'missing_insistence':[6],'wrong_viewpoint':[6]}
    rows={}
    for name,indices in missing.items():
        actual=evaluate(d,presentation(d,name),people,times)
        assert actual==[i not in indices for i in range(7)],(name,actual);rows[name]=actual
    for name in ('uc','hzyb','hzye'):
        v=presentation(d);v[name]=unknown
        try:evaluate(d,v,people,times)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,current_seven_statements_executed=True,world_contents_unknown=True,
        old_claim_and_old_target_not_silently_reused=True,unknown_inputs_refused=3)


def reading():
    old=json.loads((ROOT/'data/prior-confinement-reading-v1.json').read_text(encoding='utf-8'))
    clauses=deepcopy(old['clauses'])
    replacements={
        'prior_stages':(['r2al'],'先行する理解不足の原因行為と、許容欠如を対象にする原因行為を後の提示へ結ぶ。'),
        'caused_deficiency':(['g4','r2al'],'同じ人の理解不足を生じさせる先行行為を保持し、後の危険提示へ結ぶ。'),
        'careful_prevention':(['r2ah','r2ai','r2aj','r2ak'],'原因行為と同じ行為の注意・目的を、本人への許容欠如へ向ける。実際の非試行を別に要求しない。'),
        'quiet_creatures':(['r2an','rqz7','r2aq'],'許容欠如への慎重な働きかけの同じ局面を、落ち着いた家畜像として描く。'),
        'emphasis':(['r2ar','rqzx'],'更新した同じ主張・対象側の局面について、身体側の不許容への後見人の強い姿勢を示す。'),
        'minimal_step':(['rqzx','r2ap'],'同じ本人・先行局面を、既存の四形の身体目標への試みの不許容へ結ぶ。'),
        'confinement':(['r2af','r2as'],'更新した対象側の同じ先行局面を、既存の局面上の閉じ込めへ結ぶ。'),
        'daring_permission':(['hztc','r2ah','r2ak','r2an'],'取り組みへの許容がない状態と、その状態への慎重な原因行為を結ぶ。許されずに試みた場合を排除しない。'),
        'later_presentation':(['ew','r2al','r2am','r2ao'],'同じ対象者への後の危険提示へ、更新した先行段階を接続する。'),
    }
    for c in clauses:
        if c['id'] in replacements:
            c['definitions'],c['interpretation_ja']=replacements[c['id']];c['status']='partial'
    paths=(INDEX,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,INVENTORY,
        'data/prior-confinement-reading-v1.json','reports/guarded-walking-scope-v1.json',
        'reports/prior-confinement-v1.json','reports/unpermitted-undertaking-v1.json',
        'docs/unpermitted-undertaking-v1.md','artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='causal_scope_moved_to_permission_absence',reviewer='assistant_review',
        decision='partial_source_modal_scope_revised_whole_sentence_not_verified',document=FULL,meaning_basis=BASIS,
        source=old['source'],clauses=clauses,selection=selection_binding(catalog(),SELECTION),source_review=old['source_review'],
        correction=dict(old_result='actual_nonattempt_plus_separate_permission_absence',
            new_result='caused_permission_absence_without_asserting_nonattempt',
            rationale_ja='否定された許容を含む従属節をverhütetenの対象とする、既存の許容読解に沿って結合する。許容欠如と非試行を区別する以前の規約を、本文の原因・注意・提示にも一貫して適用する。'),
        interpretation_limits=LIMITS,remaining=old['remaining'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-12]==old.document['declarations']
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if a!=b]==CHANGED
    assert len(new.document['statements'])==50 and all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)
    # The outcome and attention goal execute the SAME permission definition.
    for root in ('r2ah','r2ai','r2aj','r2ak','r2al','r2am','r2an'):
        assert 'hzsm' not in {x['name'] for x in closure(new.document,[root])},root
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in r['selection']['statements']]
        assert not set(ids)&set(CHANGED) and r['selection']==selection_binding(new,ids)
    for path,text in build().items():assert (ROOT/path).read_text(encoding='utf-8')==text,path
    for path in (FULL,CORE):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            t=format_graph(d,style);assert parse(t)==parse(transcribe(t,alphabet='v2'))==d
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert all(n in new.entries for c in r['clauses'] for n in c['definitions'])
    return dict(revised_statements=CHANGED,preserved_statements=45,total_statements=50,new_definitions=12,new_primitives=0,
        preserved_review_selections=11,nonattempt_removed_from_current_causal_dependencies=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('scope',scope_checks),('binding',binding_checks),('unknowns',unknown_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']==r['source']['unit'])
    span=[981,1114]
    paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_modal_prevention.py','scripts/check_modal_prevention.py','scripts/register_modal_prevention.py',
        'tests/test_modal_prevention.py','scripts/compose_courageous_undertaking.py',
        'scripts/check_guarded_walking_scope.py','scripts/check_prevented_attempt.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='caused_normative_absence_separated_from_nonperformance',document=FULL,**results,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=span,text=unit['text'][span[0]:span[1]],
            definitions=list(MEANINGS),status='partial_modal_prevention_scope'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
