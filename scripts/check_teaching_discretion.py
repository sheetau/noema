"""Check scoped decision authority, unrestricted criterion and appointment."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from html.parser import HTMLParser
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_teaching_discretion import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_representative_policy import appointment_values,EXTRA_LOCAL,SMALL,PAST_SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_pastoral_role_evidence import entry

DOC='docs/teaching-discretion-v1.md'
REPORT='reports/teaching-discretion-v1.json'
EVIDENCE='data/teaching-discretion-lexical-v1.json'
PRIOR='reports/representative-policy-v1.json'
FIELDS=('source','person','role','subject','message','rank','reference','point')


class Text(HTMLParser):
    def __init__(self):super().__init__();self.items=[]
    def handle_data(self,data):self.items.append(data)


def extract(html):
    parser=Text();parser.feed(html)
    return ' '.join(' '.join(parser.items).split())


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(alias=False):
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r4d','r4e','r4f']),statements=[])
    prefix=EXTRA_LOCAL+'d zalias[subject a] f[k zmessage[v subject]].'
    code='r[p '+('zalias' if alias else 'zmessage')+']'
    args='k zchurch[] k zperson[] k zrole[] k zsubject[] '+code+' k zref[]'
    query=''.join('q[t[k '+n+'['+args+']][k zpoint[]]].' for n in ('r4d','r4e'))
    query+='q[t[k r4f['+' '.join('k z'+n+'[]' for n in NAMES)+' k zref[] '+code+']][k zpoint[]]].'
    return parse(format_graph(doc,'compact')+prefix+query)


def model(doc,variant='baseline',bits=(True,True,True)):
    competence,criterion,appointed=bits
    v=appointment_values(doc,'absent_terms' if not appointed else variant)
    def status(name,enabled):
        def result(source,person,role,subject,code,ref,point):
            expected=['church','person','role','subject','zmessage',0,'reference','now']
            for i,f in enumerate(FIELDS):
                if variant==name+'_'+f:expected[i]=1 if f=='rank' else 'other'
            return enabled and (source,person,role,subject,symbol(code),code.rank,ref,point)==tuple(expected)
        return result
    v.update(h247p=status('competence',competence),h247q=status('criterion',criterion))
    return v


@lru_cache(None)
def independence_checks():
    doc=fixture();rows=[]
    for bits in product((False,True),repeat=3):
        v=model(doc,bits=bits);free=bits[0] and bits[1]
        assert v['h247o'] is unknown and v['f2'] is unknown and v['zmeaning'] is unknown
        actual=evaluate(doc,v,SMALL,PAST_SCENES,True)
        assert actual==[free,not free,not free and bits[2]],(bits,actual)
        rows.append(dict(competence=bits[0],own_judgment_decisive=bits[1],appointed=bits[2],results=actual))
    return dict(truth_table=rows,restricted_competence_not_complete_absence_of_authority=True,
        appointment_and_denial_not_inferred_from_each_other=True,teaching_execution_and_message_truth_remain_unknown=True,
        definitions_replaced_by_primitives=False)


@lru_cache(None)
def identity_checks():
    doc=fixture();rows={}
    for prefix in ('competence','criterion'):
        for field in FIELDS:
            variant=prefix+'_'+field
            actual=evaluate(doc,model(doc,variant),SMALL,PAST_SCENES,True)
            assert actual==[False,True,True],(variant,actual);rows[variant]=actual
    alias=fixture(True);actual=evaluate(alias,model(alias),SMALL,PAST_SCENES,True)
    assert actual==[False,True,True]
    return dict(contrasts=rows,closed_message_alias_not_substituted=True,
        same_source_person_role_subject_message_reference_and_point=True)


@lru_cache(None)
def appointment_checks():
    doc=fixture();rows={}
    for variant in ('baseline','split_event','split_time','other_target','wrong_rank','other_reference','opposite_sign',
        'missing_current_delegation','missing_current_service','missing_current_business'):
        actual=evaluate(doc,model(doc,variant,bits=(True,False,True)),SMALL,PAST_SCENES,True)
        assert actual==[False,True,variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,same_native_current_appointment_and_policy=True,denial_survives_missing_appointment_but_conjunction_does_not=True)


@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    for source in read(EVIDENCE)['sources']:
        raw=(ROOT/source['raw_archive']).read_bytes();assert digest(raw)==source['raw_sha256']
        html=raw.decode(source['encoding']);text=entry(html) if source['kind']=='adelung' else extract(html)
        assert text==source['extracted_text']
        for snippet in source['locators']:assert snippet in text
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    rejected=[];doc=fixture()
    for n in ('h247p','h247q','h246m','cf','h246k','h247n'):
        v=model(doc,bits=(True,False,True));v[n]=unknown
        try:evaluate(doc,v,SMALL,PAST_SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
        rejected.append(n)
    doc=parse(format_graph(new.document,'compact')+'q[e[r c[p r4f]][r c[p r4f]]].')
    assert evaluate(doc,{d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'},SMALL,PAST_SCENES,True)==[True]
    return dict(new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),inherited_meanings_preserved=True,roundtrips=True,
        unknown_relations_rejected=rejected,quoted_compound_not_executed=True,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('independence',independence_checks),('identity',identity_checks),('appointment',appointment_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{DOC,EVIDENCE,PRIOR,
        *[r['raw_archive'] for r in read(EVIDENCE)['sources']],
        'scripts/compose_teaching_discretion.py','scripts/check_teaching_discretion.py','tests/test_teaching_discretion.py',
        'scripts/check_representative_policy.py','scripts/check_teaching_policy.py','scripts/check_ranked_appointment.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/fetch_pastoral_role_evidence.py'}
    return dict(status='free_teaching_discretion_and_same_representative_appointment',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
