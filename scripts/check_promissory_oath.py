"""Check oath modifiers, same-act reciprocity and non-execution of invocations."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_grounded_step import closure
from scripts.compose_promissory_oath import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parent,build
from scripts.check_irrevisable_confession import EXTRA,DOMAIN,SCENES,base,run,formation_model
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_promissory_oath_evidence import RECORD as EVIDENCE,validate as validate_evidence

REPORT='reports/promissory-oath-v1.json'
DOC='docs/promissory-oath-v1.md'
READING='data/promissory-oath-reading-v1.json'
PRIOR='reports/irrevisable-confession-v1.json'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,query):
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)


def modifiers(v,variant='baseline',flags=(True,True,True)):
    rows={('person','acta','past'),('second','actb','reference')}
    def solemn(person,activity,point):
        if variant=='second_without_oath' and person=='second':return False
        return flags[0] and (person,activity,point) in rows
    def matching(person,activity,authority,terms,bindings,point):
        if variant=='separate_act':return activity=='other'
        if variant=='separate_time':return point=='middle'
        if variant=='separate_person':return person=='other'
        expected_authority='r46u' if variant=='wrong_authority' else 'r46w'
        expected_terms='r46t' if variant=='wrong_terms' else 'r46u'
        expected=(person,'agreement','body','alternative' if variant=='wrong_creed' else 'creed','subject')
        return (person,activity,point) in rows and (symbol(authority),authority.rank,symbol(terms),terms.rank,tuple(bindings.items))==(
            expected_authority,0,expected_terms,0,expected)
    v['h255f']=solemn
    v['h255g']=lambda *args:flags[1] and matching(*args)
    v['h255h']=lambda *args:flags[2] and matching(*args) and not (variant=='one_missing_judgment' and args[0]=='second')
    return v


@lru_cache(None)
def act_checks():
    query='q[k r46x[k zsecond[] k zactb[] r[p r46u] l[a][k zsecond[] k zagreement[] k zbody[] k zcreed[] k zsubject[]] k zref[]]].'
    doc=fixture(('r46x','r46u'),query);rows={}
    for flags in product((False,True),repeat=3):
        v=modifiers(base(doc),flags=flags);actual=run(doc,v)
        assert actual==[all(flags)],(flags,actual);rows[str(flags)]=actual[0]
        assert v['h255e'] is unknown and v['h246e'] is unknown
    for variant in ('separate_act','separate_time','separate_person','wrong_authority','wrong_terms','wrong_creed','one_missing_judgment'):
        actual=run(doc,modifiers(base(doc),variant));assert actual==[False],(variant,actual);rows[variant]=actual[0]
    for name in ('h255f','h255g','h255h'):
        v=modifiers(base(doc));v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_independent_modifiers_and_same_arguments=rows,authority_property_and_terms_not_evaluated=True,
        unknown_act_records_not_inferred=True)


@lru_cache(None)
def formation_checks():
    args='k zbody[] k zagreement[] k zcreed[] k zsubject[] k zref[]'
    doc=fixture(('r46v','r46z'),'q[k r46v['+args+']].q[k r46z['+args+']].')
    rows={}
    for variant in ('baseline','second_without_oath','separate_act','separate_time','separate_person','wrong_authority','wrong_terms','wrong_creed','one_missing_judgment'):
        v=modifiers(formation_model(doc),variant);actual=run(doc,v)
        assert actual==[True,variant=='baseline'],(variant,actual);rows[variant]=actual
        assert all(v[n] is unknown for n in ('h255e','h246e','h246g','h254w','h254y','h253w'))
    for variant in ('extra_member','singleton','wrong_anchor','future_declaration','no_assignment','no_declaration','wrong_person',
                    'different_creed','self_only','missing_reverse','separate_act','separate_time','other_counterparty','other_terms'):
        v=modifiers(formation_model(doc,variant));actual=run(doc,v)
        assert actual==[False,False],(variant,actual);rows['formation_'+variant]=actual
    for name in ('h255f','h255g','h255h','h255d'):
        v=modifiers(formation_model(doc));v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_old_and_strengthened_same_party_formation=rows,
        each_party_same_act_not_separate_ceremony=True,ritual_does_not_replace_reciprocal_undertaking=True,
        no_deity_existence_or_fulfillment_evaluation=True)


def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    phrase='sich eidlich unter einander auf ein gewisses unveränderliches Symbol zu verpflichten';start=unit['text'].index(phrase)
    return dict(status='religious_promissory_oath_on_same_irrevisable_confession_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        evidence=EVIDENCE,primary_page=read('data/irrevisable-confession-reading-v1.json')['primary_page'],
        adopted_reading='同じ引受けを慣習上の厳粛な表明として行い、神的な権威へ自分の誠実さの証人と故意の裏切りへの裁き手として呼びかけるという宗教的な宣誓の読み。具体的な宣誓文・罰・本人の信仰や誠実さ・神の実在を追加しない。',
        composition=['r46wで呼びかけ先の性質を引用','r46xで厳粛さ・証人・自己への裁きの同じ行為を接続',
                     'r46yで同じ引受けと全相手当事者を接続','r46zで基準時の全所属者と同じ五引数条項r46uを接続'],
        remaining=['一般団体と会議体の例示・自己呼称','上位後見・全成員を介する人民への媒介・持続の目的','権限の否定疑問と直後の回答'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)


@lru_cache(None)
def structure_checks():
    new=catalog();old=parent()
    for n,e in old.entries.items():
        assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    validate_hashes(ROOT,read(PRIOR)['source_sha256']);validate_evidence(read(EVIDENCE))
    assert read(READING)==reading_record()
    page=read(READING)['primary_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    assert not new.document['statements']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        same_source_and_historical_evidence_pinned=True,no_new_author_assertion=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    results={}
    for name,fn in [('act',act_checks),('formation',formation_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=read(READING)
    paths=set(build())|set(catalog().source_sha256)|{PRIOR,DOC,READING,EVIDENCE,read(EVIDENCE)['path'],
        reading['source_inventory'],reading['primary_page']['path'],'scripts/fetch_promissory_oath_evidence.py',
        'scripts/compose_promissory_oath.py','scripts/check_promissory_oath.py','tests/test_promissory_oath.py',
        'scripts/check_irrevisable_confession.py','scripts/check_motive_causes.py','scripts/check_pastoral_roles.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='same_reciprocal_undertaking_with_religious_promissory_oath',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
