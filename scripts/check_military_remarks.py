"""Check notes, goals, public roles, and execution without truth export."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_military_remarks import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_officer_command_binding import model as officer_model

REPORT='reports/military-remarks-v1.json'
DOC='docs/military-remarks-v1.md'
PRIOR='reports/officer-example-v1.json'
SCENES=('reference','other')
DOMAIN=(*NAMES,'office','institution','remark','remarkother','criterion','reader','judgment','record','carrier','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind,bindings=('audience','notes')):
    target={'defect':'r326','goal':'r327','notes':'r33a','candidate':'r33b','officer':'r33c',
            'making':'r33d','presenting':'r33e','joint':'r33f'}[kind]
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,[target]),statements=[])
    args={
        'defect':'k zfield[] k zcriterion[] k zref[]',
        'goal':'l[a]['+' '.join('k z'+n+'[]' for n in bindings)+']',
        'notes':'k znotes[] k zfield[] k zref[]',
        'candidate':' '.join('k z'+n+'[]' for n in NAMES)+' k zref[]',
        'officer':'k zoffice[] k zinstitution[] '+' '.join('k z'+n+'[]' for n in NAMES)+' k zref[]',
        'making':'k zperson[] k zmaking[] k znotes[]',
        'presenting':'k zperson[] k zpresenting[] k znotes[] k zaudience[]',
        'joint':'k zperson[] k zmaking[] k zpresenting[] k znotes[] k zaudience[]',
    }[kind]
    call='k '+target+'['+args+']'
    if kind in ('defect','goal','making','presenting','joint'):call='t['+call+'][k zref[]]'
    return parse(format_graph(doc,'compact')+EXTRA+'q['+call+'].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in DOMAIN:v['z'+n]=lambda n=n:n
    v['zref']=lambda:'reference'
    return v


@lru_cache(None)
def defect_checks():
    doc,rows=fixture('defect'),{}
    for variant in ('baseline','satisfied','inapplicable','wrong_target','wrong_criterion','wrong_reference','wrong_evaluation'):
        v=base(doc)
        v['h243v']=lambda criterion,target,ref:variant!='inapplicable' and (criterion,target,ref)==(
            'other' if variant=='wrong_criterion' else 'criterion','other' if variant=='wrong_target' else 'field',
            'other' if variant=='wrong_reference' else 'reference')
        v['h243u']=lambda criterion,target,ref,point:variant=='satisfied' or point==('reference' if variant=='wrong_evaluation' else 'other')
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows, applicable_criterion_and_failure_distinguished=True)


def notes_model(doc,variant='baseline'):
    v=base(doc)
    v.update(h243w=lambda notes,remark,ref:variant!='empty' and (notes,ref)==('notes','reference') and remark in ('remark','remarkother'),
        h243x=lambda remark,target,criterion,code,ref:remark in ('remark',) if variant=='one_unrelated_remark' else (
            remark in ('remark','remarkother') and (target,criterion,symbol(code),code.rank,ref)==(
                'other' if variant=='other_field' else 'field','criterion','r326',0,
                'other' if variant=='other_reference' else 'reference')))
    return v


@lru_cache(None)
def notes_checks():
    doc,rows=fixture('notes'),{}
    for variant in ('baseline','empty','one_unrelated_remark','other_field','other_reference'):
        v=notes_model(doc,variant)
        assert v['h243u'] is unknown and v['h243v'] is unknown
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows, nonempty_all_remarks_same_field=True, defects_not_asserted_true=True)


def goal_model(doc,variant='baseline'):
    v=base(doc)
    v.update(aa=lambda reader:reader=='reader',
        h6t=lambda audience,reader,point:variant!='no_reader' and (audience,reader)==('other' if variant=='other_audience' else 'audience','reader'),
        fa=lambda reader,judgment,point:variant!='no_judgment' and (reader,judgment)==('other' if variant=='other_judge' else 'reader','judgment'),
        fb=lambda judgment,notes,point:(judgment,notes)==('judgment','other' if variant=='other_notes' else 'notes'))
    return v


@lru_cache(None)
def goal_checks():
    rows={}
    small=('audience','notes','reader','judgment','other')
    doc=fixture('goal')
    for variant in ('baseline','no_reader','no_judgment','other_audience','other_judge','other_notes'):
        actual=evaluate(doc,goal_model(doc,variant),small,('reference',),True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    for bindings in ((),('audience',),('audience','notes'),('notes','audience'),('audience','notes','other')):
        doc=fixture('goal',bindings)
        actual=evaluate(doc,goal_model(doc),small,('reference',),True)
        assert actual==[bindings==('audience','notes')],(bindings,actual);rows[str(bindings)]=actual[0]
    return dict(contrasts=rows, exact_two_bindings=True, some_public_judgment_not_universal_agreement=True)


def candidate_model(doc,variant='baseline'):
    v=notes_model(doc,variant)
    v.update(aa=lambda p:p=='person',
        ca=lambda p,act,ref:(p,ref)==('person','reference') and act in ('making','presenting'),
        cb=lambda p,act,role,ref:(p,role,ref)==('person','other' if variant=='other_scholar' else 'scholar','reference') and act in ('making','presenting'),
        cd=lambda role,ref:(role,ref)==('scholar','reference'),
        cc=lambda act,audience,ref:act in ('making','presenting') and (audience,ref)==('other' if variant=='other_audience' else 'audience','reference'),
        ce=lambda audience,ref:(audience,ref)==('audience','reference'),
        h243y=lambda p,act,notes,ref:(p,act,notes,ref)==('person','making','other' if variant=='other_created_notes' else 'notes','reference'),
        h242g=lambda act,notes,audience,ref:(act,notes,audience,ref)==('presenting','other' if variant=='other_routed_notes' else 'notes','audience','reference'),
        h243z=lambda act,notes,audience,ref:variant!='not_submitted_for_inspection' and (act,notes,audience,ref)==('presenting','notes','audience','reference'))
    def aims(p,act,code,bindings,ref):
        return (p,act,symbol(code),code.rank,tuple(bindings.items),ref)==(
            'other' if variant=='other_goal_actor' else 'person','making' if variant=='goal_on_wrong_activity' else 'presenting',
            'r327',0,('audience','other' if variant=='other_goal_notes' else 'notes'),'reference')
    v['hztl']=aims
    return v


@lru_cache(None)
def candidate_checks():
    doc,rows=fixture('candidate'),{}
    for variant in ('baseline','empty','one_unrelated_remark','other_field','other_scholar','other_audience',
                    'other_created_notes','other_routed_notes','not_submitted_for_inspection','other_goal_actor','goal_on_wrong_activity','other_goal_notes'):
        v=candidate_model(doc,variant)
        assert all(v[n] is unknown for n in ('h243u','h243v','h6t','fa','fb'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows, native_public_use_and_note_structure=True,
        defect_truth_and_public_judgment_not_evaluated=True, no_existing_records_required=True)


@lru_cache(None)
def officer_checks():
    doc,rows=fixture('officer'),{}
    for variant in ('baseline','not_military','not_officer_rank','other_military_field','other_institution'):
        v=officer_model(doc,variant);v.update(candidate_model(doc))
        # Keep the officer relations from the independent native fixture.
        original=officer_model(doc,variant)
        for n in ('hzwn','hzxf','cf','h233d','h233e'):v[n]=original[n]
        v['h244a']=lambda field,institution,ref:(field,institution,ref)==(
            'other' if variant=='other_military_field' else 'field','other' if variant=='other_institution' else 'institution','reference')
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows, native_same_officer_institution_and_remarks=True)


def execution_model(doc,variant='baseline'):
    v=base(doc)
    v.update(cg=lambda p,act,point:(p,point)==('person','reference') and act in (
            () if variant=='no_execution' else ('making',) if variant=='only_making' else ('presenting',) if variant=='only_presenting' else ('making','presenting')),
        sc=lambda notes,point:(notes,point)==('notes','reference'),
        hzwr=lambda record,notes,point:(record,notes,point)==('record','other' if variant=='other_recorded_work' else 'notes','reference'),
        hzws=lambda record,carrier,point:(record,carrier,point)==('record','carrier','reference'),
        hzwt=lambda record,point:variant!='no_readable_record' and (record,point)==('record','reference'),
        h244b=lambda p,act,notes,point:(p,act,notes,point)==('other' if variant=='other_creator' else 'person',
            'presenting' if variant=='other_creation_activity' else 'making','notes','reference'),
        h244c=lambda act,notes,audience,point:(act,notes,audience,point)==('presenting',
            'other' if variant=='other_provided_work' else 'notes','other' if variant=='other_receiving_public' else 'audience','reference'))
    return v


@lru_cache(None)
def execution_checks():
    rows={}
    for variant,wanted in (
        ('baseline',(True,True,True)),('no_execution',(False,False,False)),
        ('only_making',(True,False,False)),('only_presenting',(False,True,False)),
        ('other_recorded_work',(False,False,False)),('no_readable_record',(False,False,False)),
        ('other_creator',(False,True,False)),('other_creation_activity',(False,True,False)),
        ('other_provided_work',(True,False,False)),('other_receiving_public',(True,False,False))):
        values=[]
        for kind,expected in zip(('making','presenting','joint'),wanted):
            doc=fixture(kind);v=execution_model(doc,variant)
            actual=evaluate(doc,v,DOMAIN,SCENES,True)
            assert actual==[expected],(kind,variant,actual);values.append(actual[0])
        rows[variant]=values
    return dict(contrasts=rows, native_external_record=True, creation_and_submission_separate=True,
                judgment_and_agreement_not_execution_conditions=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for kind,names,model in (
        ('defect',('h243u','h243v'),lambda doc:dict(base(doc),h243u=lambda *a:False,h243v=lambda *a:True)),
        ('candidate',('h243w','h243x','h243y','h243z','hztl'),candidate_model),
        ('joint',('h244b','h244c'),execution_model)):
        doc=fixture(kind)
        for name in names:
            v=model(doc);v[name]=unknown
            try:evaluate(doc,v,DOMAIN,SCENES,True)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError(name)
            rows.append(name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert not new.document['statements']
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_semantic_reviews=0,
                active_manuscript_unchanged=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)


def build_report():
    results={}
    for name,fn in [('defect',defect_checks),('notes',notes_checks),('goal',goal_checks),('candidate',candidate_checks),
                    ('officer',officer_checks),('execution',execution_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{
        DOC,PRIOR,'scripts/compose_military_remarks.py','scripts/check_military_remarks.py','tests/test_military_remarks.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_officer_command_binding.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='remarks_on_military_shortcomings_and_submission_for_public_judgment',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
