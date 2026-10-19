"""Check episode/subject/time binding and independence of two quietness readings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_scoped_quiet import ROOT,FULL,CORE,BASIS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.fetch_scoped_quiet_evidence import PATH as EVIDENCE,validate

INDEX='data/semantic-review-index-v73.json'
REPORT='reports/scoped-quiet-v1.json'
READING='data/scoped-quiet-reading-v1.json'
DOC='docs/scoped-quiet-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','one','two')
TIMES=('start','middle','end','elsewhere')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture():
    return parse((ROOT/CORE).read_text(encoding='utf-8')+'''
r jp[] a.r jhistory[d] c.r jphase[d] c.r jbefore[d d] c.
r jsubject[a a d] c.r joccurs[a d] c.r jmarked[a d] c.
r jexperience[a a d] c.r jfelt[a d] c.r jinner[a d] c.
q[k rqz2[k jp[] p jhistory p jphase p jbefore p jsubject p joccurs p jmarked]].
q[k rqz3[k jp[] p jhistory p jphase p jbefore p jsubject p joccurs p jmarked]].
q[k rqz4[k jp[] p jhistory p jphase p jbefore p jmarked]].
q[k rqz2[k jp[] p jhistory p jphase p jbefore p jexperience p jfelt p jinner]].
''')


def values(bits=(True,False,True,False,True,False),variant='baseline'):
    subjects,occurrences,qualities=[{e for e,b in zip(('one','two'),bits[i:i+2]) if b} for i in (0,2,4)]
    v=dict(jp=lambda:'person',jhistory=lambda t:t in TIMES[:3],jphase=lambda t:t in TIMES[:3],
        jbefore=lambda a,b:a in TIMES[:3] and b in TIMES[:3] and TIMES.index(a)<TIMES.index(b),
        jsubject=lambda p,e,t:p=='person' and e in subjects and t=='middle',
        joccurs=lambda e,t:e in occurrences and t=='middle',jmarked=lambda e,t:e in qualities and t=='middle',
        jexperience=lambda *args:False,jfelt=lambda *args:False,jinner=lambda *args:False)
    if variant=='other_person':v['jsubject']=lambda p,e,t:(p,e,t)==('other','one','middle')
    if variant=='split_point':v['jsubject']=lambda p,e,t:(p,e,t)==('person','one','start')
    if variant=='split_episode':v['jmarked']=lambda e,t:(e,t)==('two','middle')
    if variant=='other_point':
        v.update(jsubject=lambda p,e,t:(p,e,t)==('person','one','elsewhere'),
            joccurs=lambda e,t:(e,t)==('one','elsewhere'),jmarked=lambda e,t:(e,t)==('one','elsewhere'))
    if variant=='gapped_phase':v['jphase']=lambda t:t in ('start','end')
    if variant=='empty_phase':v['jphase']=lambda t:False
    if variant=='outside_history':v['jphase']=lambda t:t=='elsewhere'
    if variant=='empty_history':v['jhistory']=lambda t:False
    if variant=='reflexive_order':v['jbefore']=lambda a,b:a in TIMES[:3] and b in TIMES[:3] and TIMES.index(a)<=TIMES.index(b)
    if variant=='shorter_phase':v['jphase']=lambda t:t=='start'
    if variant=='other_quality':v['jmarked']=lambda *args:False
    if variant=='not_occurred':v['joccurs']=lambda *args:False
    v.update(df=v['jsubject'],dg=v['joccurs'])
    return v


def binding_checks():
    doc=deepcopy(fixture());doc['statements']=doc['statements'][:2];rows=[]
    for bits in product((False,True),repeat=6):
        actual=evaluate(doc,values(bits),DOMAIN,TIMES)
        common=any(bits[i] and bits[i+2] and bits[i+4] for i in (0,1))
        assert actual==[not common,common],(bits,actual)
        rows.append(dict(subject_occurrence_quality=bits,absence_presence=actual))
    return dict(combinations=rows,same_episode_subject_and_point_required=True,ordinary_evaluation=True)


def scope_checks():
    doc=deepcopy(fixture());doc['statements']=doc['statements'][:2];rows={}
    malformed={'gapped_phase','empty_phase','outside_history','empty_history','reflexive_order'}
    names=('other_person','split_point','split_episode','other_point','gapped_phase','empty_phase',
        'outside_history','empty_history','reflexive_order','shorter_phase','other_quality','not_occurred')
    for name in names:
        actual=evaluate(doc,values(variant=name),DOMAIN,TIMES)
        assert actual==([False,False] if name in malformed else [True,False]),(name,actual)
        rows[name]=actual
    for name in ('jhistory','jphase','jbefore','jsubject','joccurs','jmarked'):
        v=values();v[name]=unknown
        try:evaluate(doc,v,DOMAIN,TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_inputs_refused=6,
        malformed_scope_is_neither_presence_nor_absence=True,shorter_valid_scope_not_equal_to_longer_scope=True,
        complete_interpretation_not_finite_observation_claim=True,ordinary_evaluation=True)


def independent_checks():
    rows=[]
    for active,agitated,experienced,burdensome in product((False,True),repeat=4):
        v=values((True,False,active,False,agitated,False))
        v.update(jexperience=lambda p,e,t:(p,e,t)==('person','two','middle'),
            jfelt=lambda e,t:experienced and (e,t)==('two','middle'),
            jinner=lambda e,t:burdensome and (e,t)==('two','middle'))
        actual=evaluate(fixture(),v,DOMAIN,TIMES)
        expected=[not(active and agitated),active and agitated,not(active and agitated),not(experienced and burdensome)]
        assert actual==expected,(active,agitated,experienced,burdensome,actual)
        rows.append(dict(active=active,marked_activity=agitated,experienced=experienced,
            marked_experience=burdensome,values=actual))
    # A calm outward reading remains evaluable when all experience inputs are
    # unknown. The separate inner reading must remain unknown in that case.
    d=deepcopy(fixture());d['statements']=d['statements'][2:3]
    v=values((True,False,True,False,False,False))
    for name in ('jexperience','jfelt','jinner'):v[name]=unknown
    assert evaluate(d,v,DOMAIN,TIMES)==[True]
    d['statements']=fixture()['statements'][3:]
    try:evaluate(d,v,DOMAIN,TIMES)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown experience became inner calm')
    # df and dg stay the actual Noema primitives used by the specialization.
    d=deepcopy(fixture());d['statements']=d['statements'][2:3]
    for name in ('df','dg'):
        v=values();v[name]=unknown
        try:evaluate(d,v,DOMAIN,TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,active_but_unmarked_activity_possible=True,
        outward_and_inner_readings_independent=True,unknown_inner_state_not_inferred=True,
        actor_occurrence_specialization_evaluated=True,unknown_specialization_inputs_refused=2,ordinary_evaluation=True)


def reading():
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));validate(evidence)
    old=json.loads((ROOT/'data/step-depiction-reading-v1.json').read_text(encoding='utf-8'))
    clause=next(c for c in old['clauses'] if c['id']=='quiet_creatures')
    paths=(INDEX,PARENT,PARENT_BASIS,INVENTORY,EVIDENCE,'data/step-depiction-reading-v1.json')
    return dict(status='scoped_absence_comparison_not_a_completed_quietness_definition',reviewer='assistant_review',
        document=FULL,source={**{k:old['source'][k] for k in ('unit','unit_sha256')},
            'range':clause['range'],'text':clause['text']},context=old['source'],source_adoption=False,
        lexical_evidence=dict(url=evidence['url'],entry='Ruhig',pages='1203–1204',
            interpretation_ja='歴史辞典は動き・他者への煩わしさ・内面の感覚など複数の用法を記す。本文でどの側面を採るかは文脈の判断を要する。非抵抗や服従をこの形容詞の一律の定義としない。'),
        findings=['本人に結び付いた同じ生起出来事と性質を、同じ時点で検査する。',
            '空または間が欠けた範囲から不在を主張しない。観測の欠落と意味上の範囲を区別する。',
            '乱れを持つ活動がないことは全ての活動がないことを含意せず、内面の経験についても独立である。'],
        interpretation_limits=LIMITS,whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        next_required=['ruhigenの文脈上の側面と顕著さの基準','同じ対象者と先行局面への描写の接続',
            'Geschöpfeの指示と描写','jaの強調','一文・第二段落・二作品全文'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-4]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==48
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    active=load_catalog(ROOT,idx['works']['kant-1784']['meaning_basis'])
    assert selection_binding(active,list(range(48)))==selection_binding(new,list(range(48)))
    for path in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'))
        assert r['selection']==selection_binding(new,[s['index'] for s in r['selection']['statements']])
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body
    for path in (FULL,CORE):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    r=reading();assert r==json.loads((ROOT/READING).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    assert [d['name'] for d in parse((ROOT/CORE).read_text(encoding='utf-8'))['declarations'] if d['kind']=='primitive']==['df','dg']
    return dict(active_manuscript_unchanged=True,preserved_statements=48,new_definitions=4,new_primitives=0,
        preserved_review_selections=11,roundtrips=True,source_adoption=False)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('binding',binding_checks),('scope',scope_checks),('independence',independent_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{READING,DOC,
        'scripts/compose_scoped_quiet.py','scripts/check_scoped_quiet.py','scripts/register_scoped_quiet.py',
        'scripts/fetch_scoped_quiet_evidence.py','scripts/fetch_pastoral_role_evidence.py','tests/test_scoped_quiet.py',
        'scripts/compose_grounded_step.py','scripts/compose_falling_depiction.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='scoped_episode_absence_and_independent_quietness_readings_comparison',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
