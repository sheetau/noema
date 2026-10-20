"""Check reproof, evaluative standing and the same currently required levy."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import function_sort
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,Message
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_levy_reproof import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_civic_levy_refusal import case_model as civic_model

REPORT='reports/levy-reproof-v1.json'
DOC='docs/levy-reproof-v1.md'
PRIOR='reports/civic-levy-refusal-v1.json'
EVIDENCE='data/vorwitzig-reading-v1.json'
DOMAIN=(*NAMES,'community','levy','criticism','audience','criterion','standing','reader','second','other')
SCENES=('reference','outcome','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
CRITERION_SORT=json.dumps(function_sort(['individual','individual'],'content'),sort_keys=True,separators=(',',':'))


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind):
    target=dict(message='r34a',reproof='r34b',standing='r34c',case='r34d')[kind]
    names=dict(message=('levy','criterion'),reproof=('person','criticism','audience','levy','criterion'),
        standing=('person','criticism','standing','levy'),
        case=('levy','community',*NAMES,'criticism','audience','criterion','standing'))[kind]
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,[target]),statements=[])
    call='k '+target+'['+' '.join('k z'+n+'[]' for n in names)+' k zref[]]'
    statement='l['+call+'].' if kind=='message' else 'q[t['+call+'][k zpoint[]]].'
    return parse(format_graph(doc,'compact')+EXTRA+statement)


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in DOMAIN:v['z'+n]=lambda n=n:n
    v.update(zref=lambda:'reference',zpoint=lambda:'outcome')
    return v


@lru_cache(None)
def message_checks():
    doc,rows=fixture('message'),{}
    for satisfied in (False,True):
        v=base(doc)
        v.update(h243v=lambda criterion,levy,ref:(criterion,levy,ref)==('criterion','levy','reference'),
            h243u=lambda criterion,levy,ref,point:satisfied)
        value=evaluate(doc,v,DOMAIN,SCENES,True)[0]
        assert isinstance(value,Message) and value.force=='assert'
        assert value.content==Content(SCENES,(not satisfied,)*len(SCENES))
        rows[str(satisfied)]=dict(force=value.force,content=list(value.content.values))
    return dict(cases=rows,native_message_construction=True,assertion_force_does_not_guarantee_truth=True)


def reproof_model(doc,variant='baseline'):
    v=base(doc)
    v.update(dg=lambda act,point:variant!='no_event' and (act,point)==('criticism','outcome'),
        f3=lambda p,act,point:(p,act,point)==('other' if variant=='other_speaker' else 'person','criticism','outcome'),
        h6t=lambda audience,recipient,ref:variant!='empty_audience' and (audience,ref)==('audience','reference')
            and recipient in ('reader','second'),
        h244n=lambda p,act,levy,point:variant!='no_disapproval' and (p,act,levy,point)==(
            'person','other' if variant=='other_disapproval_event' else 'criticism',
            'other' if variant=='other_disapproval_subject' else 'levy','outcome'))
    def conveys(act,recipient,levy,criterion,code,ref,point):
        return recipient in (('reader',) if variant=='missing_second_recipient' else ('reader','second')) and (
            act,levy,criterion,symbol(code),code.rank,ref,point)==(
                'other' if variant=='other_presentation' else 'criticism',
                'other' if variant=='other_presented_levy' else 'levy',
                'other' if variant=='other_criterion' else 'criterion','r34a',0,
                'other' if variant=='other_message_reference' else 'reference',
                'other' if variant=='other_presentation_point' else 'outcome')
    v['h244o']=conveys
    return v


@lru_cache(None)
def reproof_checks():
    doc,rows=fixture('reproof'),{}
    for variant in ('baseline','no_event','other_speaker','empty_audience','no_disapproval','other_disapproval_event',
        'other_disapproval_subject','missing_second_recipient','other_presentation','other_presented_levy',
        'other_criterion','other_message_reference','other_presentation_point'):
        v=reproof_model(doc,variant)
        assert v['h243u'] is unknown and v['h243v'] is unknown
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    assert not {'ce','cf','h7b'} & {d['name'] for d in doc['declarations']}
    return dict(contrasts=rows,native_same_reproof_and_all_fixed_recipients=True,
        reproof_content_truth_not_evaluated=True,no_publication_or_permission_requirement=True)


def standing_model(doc,variant='baseline'):
    v=base(doc)
    v['h244l']=lambda person,act,standing,point:variant!='no_self_taking' and (person,act,standing,point)==(
        'other' if variant=='other_self_actor' else 'person','other' if variant=='other_self_event' else 'criticism',
        'other' if variant=='other_self_standing' else 'standing','other' if variant=='other_self_point' else 'outcome')
    def conditions(standing,subject,ref):
        matched=(standing,subject,ref)==('standing','other' if variant=='other_criteria_subject' else 'levy',
            'other' if variant=='other_criteria_reference' else 'reference')
        def check(person,role):
            if variant=='unknown_criterion':return unknown()
            target=('other' if variant=='other_criterion_person' else 'person',
                    'other' if variant=='other_criterion_standing' else 'standing')
            return Content(SCENES,tuple(not (matched and (person,role)==target
                and point==('other' if variant=='other_criterion_point' else 'outcome')
                and variant!='all_satisfied') for point in SCENES))
        failure=FunctionValue(('individual','individual'),'content',check)
        satisfied=FunctionValue(('individual','individual'),'content',lambda p,r:Content(SCENES,(True,)*len(SCENES)))
        items=() if variant=='empty_criteria' else (satisfied,failure)
        if variant=='reordered':items=(failure,satisfied)
        if variant=='duplicate_failure':items=(failure,failure)
        return SequenceValue(items,CRITERION_SORT)
    v['h244m']=conditions
    return v


@lru_cache(None)
def standing_checks():
    doc,rows=fixture('standing'),{}
    for variant in ('baseline','all_satisfied','empty_criteria','no_self_taking','other_self_actor','other_self_event',
        'other_self_standing','other_self_point','other_criteria_subject','other_criteria_reference',
        'other_criterion_person','other_criterion_standing','other_criterion_point','reordered','duplicate_failure'):
        actual=evaluate(doc,standing_model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant in ('baseline','reordered','duplicate_failure')],(variant,actual);rows[variant]=actual[0]
    assert not {'cf','h7b','cb','cg'} & {d['name'] for d in doc['declarations']}
    return dict(contrasts=rows,native_rfq_and_rfp=True,no_permission_or_delegation_test=True,
        fixed_criteria_and_same_actor_standing_point=True)


def case_model(doc,variant='baseline'):
    v=base(doc)
    # Merge only implemented relations; an unknown default must not erase a component.
    for model in (civic_model(doc,variant),reproof_model(doc,variant),standing_model(doc,variant)):
        v.update({n:f for n,f in model.items() if f is not unknown})
    def requirement(issuer,person,role,code,bindings,sign,point):
        points=('reference',) if variant=='no_current_requirement' else (
            ('outcome',) if variant=='no_reference_requirement' else ('reference','outcome'))
        return point in points and (issuer,person,role,symbol(code),code.rank,tuple(bindings.items),sign)==(
            'issuer','person','role','r33u',0,('person',
            'other' if variant=='other_required_transfer' else 'transfer','receiver','medium'),True)
    v['h7k']=requirement
    return v


@lru_cache(None)
def case_checks():
    doc,rows=fixture('case'),{}
    for variant in ('baseline','other_levy','other_assessment_person','other_assessment_receiver','other_required_transfer',
        'no_current_requirement','no_reference_requirement','other_presented_levy','no_disapproval','no_self_taking',
        'empty_criteria','other_criteria_subject','other_criterion_point'):
        v=case_model(doc,variant)
        assert all(v[n] is unknown for n in ('ti','tj','h243u','h243v'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_civic_reproof_and_standing_composition=True,
        requirement_applies_at_reference_and_criticism_point=True,payment_and_reproof_truth_not_evaluated=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for kind,model,names in (('reproof',reproof_model,('h244n','h244o')),
        ('standing',standing_model,('h244l','h244m')),('case',case_model,('h7k',))):
        doc=fixture(kind)
        for name in names:
            v=model(doc);v[name]=unknown
            try:evaluate(doc,v,DOMAIN,SCENES,True)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError(name)
            rows.append(name)
    try:evaluate(fixture('standing'),standing_model(fixture('standing'),'unknown_criterion'),DOMAIN,SCENES,True)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('unknown criterion')
    return dict(unknown_inputs_refused=rows+['criterion_function'])


@lru_cache(None)
def structure_checks():
    new=catalog();assert not new.document['statements']
    source={n:e for parent in parents() for n,e in parent.entries.items()}
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==source[n]['declaration'] and e['meaning_ja']==source[n]['meaning_ja'],n
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    evidence=read(EVIDENCE)
    validate_hashes(ROOT,{s['raw_archive']:s['raw_sha256'] for s in evidence['sources']})
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_semantic_reviews=0,
        active_manuscript_unchanged=True,roundtrips=True,archived_lexical_sources_hashes_verified=True,
        lexical_candidate_not_certified_equivalence=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)


def build_report():
    results={}
    for name,fn in [('message',message_checks),('reproof',reproof_checks),('standing',standing_checks),
        ('case',case_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set().union(*(set(c.source_sha256) for c in parents()))|{
        DOC,PRIOR,EVIDENCE,'scripts/compose_levy_reproof.py','scripts/check_levy_reproof.py','tests/test_levy_reproof.py',
        'scripts/compose_civic_levy_refusal.py','scripts/check_civic_levy_refusal.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_levy_reproof_and_explicit_presumptuous_standing_candidate',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
