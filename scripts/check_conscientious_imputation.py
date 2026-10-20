"""Check moral self-imputation, warranted possibilities and all scoped matters."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_conscientious_imputation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parent,build
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.fetch_imputation_evidence import PATH as EVIDENCE,validate as validate_idiom
from scripts.fetch_conscience_evidence import PATH as CONSCIENCE,validate as validate_conscience

REPORT='reports/conscientious-imputation-v1.json'
DOC='docs/conscientious-imputation-v1.md'
DOMAIN=('person','judgment','judgmentb','matter','matterb','other')
TIMES=('reference','evaluation','candidate','otherpoint')
RELATIONS=('fa','se','fb','h247h','h247i','h247j')
EXPECTED={
    'fa':('person','judgment','candidate'),
    'se':('judgment','person','candidate'),
    'fb':('judgment','matter','candidate'),
    'h247h':('judgment','person','matter','reference','candidate'),
    'h247i':('judgment','reference','candidate'),
    'h247j':('person','matter','reference','evaluation','candidate'),
}


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture():
    text=format_graph(catalog().document,'compact')
    text+='r zperson[] a.r zjudgment[] a.r zmatter[] a.r zref[] d.r zcandidate[] d.r zevaluation[] d.r zscope[a] c.'
    args='k zperson[] k zjudgment[] k zmatter[] k zref[]'
    for n in ('r37r','r37s'):text+='q[t[k '+n+'['+args+']][k zcandidate[]]].'
    text+='q[t[k r37t[k zperson[] k zmatter[] k zref[]]][k zevaluation[]]].'
    text+='q[t[k r37u[k zperson[] p zscope k zref[]]][k zevaluation[]]].'
    text+='q[t[k r37r['+args+']][k zevaluation[]]].'
    return parse(text)


def model(bits=(True,)*6,changes=None,scope=('matter','matterb'),matter='matter'):
    changes=changes or {};expected=deepcopy(EXPECTED)
    # A second item has the same evaluation possibilities. Its own judgments
    # are linked to that item; scope selection never selects only blamed items.
    for n in ('fb','h247h','h247j'):
        expected[n]=tuple(matter if v=='matter' else v for v in expected[n])
    expected.update(changes)
    v=dict(zperson=lambda:'person',zjudgment=lambda:'judgment',zmatter=lambda:'matter',
        zref=lambda:'reference',zcandidate=lambda:'candidate',zevaluation=lambda:'evaluation',zscope=lambda x:x in scope)
    for n,bit in zip(RELATIONS,bits):v[n]=lambda *args,n=n,bit=bit:bit and args==expected[n]
    return v


@lru_cache(None)
def component_checks():
    rows=[]
    for bits in product((False,True),repeat=6):
        judgment=all(bits[:4]);warranted=all(bits[:5]);possible=all(bits)
        actual=evaluate(fixture(),model(bits),DOMAIN,TIMES,True)
        assert actual==[judgment,warranted,possible,not possible,False],(bits,actual)
        rows.append(dict(conditions=list(bits),results=actual))
    return dict(truth_table=rows,actual_self_blame_does_not_establish_warrant=True,
        possible_warranted_judgment_does_not_imply_current_judgment=True,definitions_replaced_by_primitives=False)


@lru_cache(None)
def identity_checks():
    rows={}
    for n,expected in EXPECTED.items():
        for i,value in enumerate(expected):
            changed=tuple(('otherpoint' if value in TIMES else 'other') if j==i else x for j,x in enumerate(expected))
            actual=evaluate(fixture(),model(changes={n:changed}),DOMAIN,TIMES,True)
            assert actual[2:4]==[False,True],(n,i,actual)
            rows[n+'_'+str(i)]=actual
    split={
        'different_moral_judgment':{'se':('judgmentb','person','candidate')},
        'different_warranted_judgment':{'h247i':('judgmentb','reference','candidate')},
        'inaccessible_success':{'h247j':('person','matter','reference','evaluation','otherpoint')},
    }
    for name,changes in split.items():
        actual=evaluate(fixture(),model(changes=changes),DOMAIN,TIMES,True)
        assert actual[2:4]==[False,True],(name,actual);rows[name]=actual
    return dict(contrasts=rows,same_person_judgment_matter_reference_and_candidate_required=True)


@lru_cache(None)
def scope_checks():
    rows={}
    for name,kwargs,expected in [
        ('both_items',{},[True,True,True,False,False]),
        ('second_item_only_blameworthy',dict(matter='matterb'),[False,False,False,False,False]),
        ('blameworthy_item_outside_scope',dict(matter='matterb',scope=('matter',)),[False,False,False,True,False]),
        ('no_scoped_items',dict(scope=()),[True,True,True,True,False]),
        ('no_evaluation_candidates',dict(bits=(True,True,True,True,True,False)),[True,True,False,True,False]),
    ]:
        actual=evaluate(fixture(),model(**kwargs),DOMAIN,TIMES,True)
        assert actual==expected,(name,actual);rows[name]=actual
    # Candidate assessments may disagree: one warranted candidate is enough.
    v=model();old=v['h247j'];v['h247j']=lambda p,m,r,e,c:old(p,m,r,e,c) or (p,m,r,e,c)==('person','matter','reference','evaluation','otherpoint')
    assert evaluate(fixture(),v,DOMAIN,TIMES,True)==[True,True,True,False,False]
    return dict(contrasts=rows,one_success_among_other_candidates_suffices=True,
        no_global_faultlessness_inferred=True,empty_scope_and_empty_candidate_set_distinct=True)


@lru_cache(None)
def structure_checks():
    old=parent();new=catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    validate_idiom(read(EVIDENCE));validate_conscience(read(CONSCIENCE))
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    rejected=[]
    for n in (*RELATIONS,'zscope'):
        v=model();v[n]=unknown
        try:evaluate(fixture(),v,DOMAIN,TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
        rejected.append(n)
    return dict(new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),inherited_meanings_preserved=True,
        roundtrips=True,unknown_relations_rejected=rejected,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('components',component_checks),('identity',identity_checks),('scope',scope_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{DOC,EVIDENCE,CONSCIENCE,
        'scripts/compose_conscientious_imputation.py','scripts/check_conscientious_imputation.py','tests/test_conscientious_imputation.py',
        'scripts/fetch_imputation_evidence.py','scripts/fetch_conscience_evidence.py','scripts/fetch_pastoral_role_evidence.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='conscientious_imputation_and_warranted_possibility_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
