"""Check principal role functions, source supply and unchanged reviewed meanings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts.compose_pastoral_roles import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,parent,build,closure
from scripts.check_written_carriers import source_values as written_values,PEOPLE,SOURCE_SCENES
from scripts.fetch_pastoral_role_evidence import PATH as EVIDENCE,validate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_designation_order import substantive

INDEX='data/semantic-review-index-v47.json'
REPORT='reports/pastoral-roles-v1.json'
AUDIT='data/pastoral-roles-reading-v1.json'
DOC='docs/pastoral-roles-v1.md'
DOMAIN=(*PEOPLE,'pastoral','otherRole')

def evaluate(doc,v,people,scenes,memo=False):
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=scenes,
        primitives={d['name']:v[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=memo,memoize_expressions=memo)]

def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r jp[] a.r js[] d.
r jh[a a d] c.r jf[a i[h[a] e] d] c.r jn[a i[h[a] e] d] c.r ju[a d] c.
d jteach[person a] e[b scene[k ju[v person v scene]]].
q[k rqxl[k jp[] r[p jteach] k js[] p jh p jf p jn]].''')
    rows=[]
    for bits in product((False,True),repeat=6):
        sets=[{r for r,b in zip(('roleA','roleB'),bits[i:i+2]) if b} for i in (0,2,4)]
        v=dict(jp=lambda:'teacher',js=lambda:'now',ju=unknown,
            jh=lambda p,r,s:p=='teacher' and r in sets[0] and s=='now',
            jf=lambda r,d,s:r in sets[1] and symbol(d)=='jteach' and s=='now',
            jn=lambda r,d,s:r in sets[2] and symbol(d)=='jteach' and s=='now')
        actual=evaluate(doc,v,('teacher','roleA','roleB'),('now',))[0]
        assert actual==bool(set.intersection(*sets))
        rows.append(dict(bits=list(bits),value=actual))
    return dict(role_combinations=rows,instruction_role_fixture=True,task_content_not_executed=True)

@lru_cache(None)
def source_doc(previous=False,integrated=False):
    c=parent() if previous else load_catalog(ROOT,BASIS);d=deepcopy(c.document)
    names=['sv','re','s2','sy','wh'] if integrated else ['sp','st']
    d.update(declarations=closure(d,names),statements=[])
    questions='''q[t[k sv[k jperson[]]][k jscene[]]].
q[k re[k jperson[] p sv i[scene d][k s2[k jperson[] k wh[] v scene]]]].
q[t[k sy[k jperson[]]][k wh[]]].''' if integrated else '''q[k sp[k jguide[] k jscene[]]].q[t[k st[k jperson[]]][k jscene[]]].'''
    return parse(format_graph(d,'compact')+'r jperson[] a.r jguide[] a.r jscene[] d.'+questions)

def source_values(variant):
    v=written_values(variant);v.update(jperson=lambda:'person',jguide=lambda:'guide',jscene=lambda:'case')
    old_holds,old_serves=v['hzwn'],v['hzwo']
    v['hzwn']=lambda p,r,s:old_holds(p,r,s) or variant!='no_role' and (p,r,s)==(
        'other' if variant=='other_holder' else 'guide','pastoral','case')
    v['hzwo']=lambda r,d,s:old_serves(r,d,s) or variant!='no_service' and r==(
        'otherRole' if variant=='split_role' else 'pastoral') and symbol(d) in (
        ('so','sq') if variant=='co_primary' else ('sq',) if variant=='other_function' else ('so',)) and s=='case'
    v['hzwu']=lambda r,d,s:variant!='incidental_function' and r=='pastoral' and symbol(d) in (
        ('so','sq') if variant=='co_primary' else ('sm',) if variant=='other_primary_content' else ('so',)) and s==(
        'text' if variant=='other_context' else 'case')
    if variant=='nonhuman':
        aa=v['aa'];v['aa']=lambda p:aa(p) and p!='guide'
    if variant=='no_access':
        access=v['sa'];v['sa']=lambda p,w,s:access(p,w,s) and w!='guide'
    if variant=='no_supply':
        supply=v['sb'];v['sb']=lambda w,p,t,s:supply(w,p,t,s) and w!='guide'
    return v

def source_checks():
    failures=('no_role','other_holder','split_role','no_service','other_function','incidental_function','other_primary_content','other_context')
    variants=('baseline',*failures,'nonhuman','no_access','no_supply','wrong_beneficiary','shared_human_provider','co_primary')
    rows={}
    for variant in variants:
        v=source_values(variant);new=evaluate(source_doc(),v,DOMAIN,SOURCE_SCENES)
        old=evaluate(source_doc(True),v,DOMAIN,SOURCE_SCENES)
        role=variant not in (*failures,'nonhuman')
        supplied=role and variant not in ('no_access','no_supply','wrong_beneficiary')
        assert new==[role,supplied],(variant,new)
        assert old==([True,True] if variant in failures else new),(variant,old)
        rows[variant]=dict(previous=old,current=new)
    for n in ('hzwn','hzwo','hzwu'):
        v=source_values('baseline');v[n]=unknown
        try:evaluate(source_doc(),v,DOMAIN,SOURCE_SCENES)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(contrasts=rows,unknown_inputs_refused=3,task_content_not_executed=True,ordinary_evaluation=True)

def integration_checks():
    rows={}
    for variant in ('baseline','no_role','incidental_function','shared_human_provider','failed_goal'):
        v=source_values(variant)
        actual=evaluate(source_doc(integrated=True),v,DOMAIN,SOURCE_SCENES,True)
        premise=variant not in ('no_role','incidental_function')
        assert actual==[premise,premise,not premise or variant!='failed_goal'],(variant,actual)
        rows[variant]=actual
    assert evaluate(source_doc(integrated=True),source_values('baseline'),DOMAIN,SOURCE_SCENES)==rows['baseline']
    return dict(cases=rows,definitions_replaced_by_primitives=False,pure_memoization=True,
        ordinary_baseline_agrees=True,vacuous_condition_not_counted_as_example=True)

def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_author','other_node','other_description','other_context','reverse_order','reverse_examples','closed_list'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(s3=lambda:'examples',mw=lambda:'cause',wa=lambda:'author',wh=lambda:'text',
            s4=lambda n,a,t,s:(n,a,symbol(t),s)==('other' if variant=='other_node' else 'examples',
                'other' if variant=='other_author' else 'author','sv' if variant=='other_description' else 'sy',
                'other' if variant=='other_context' else 'text'),
            s5=lambda n,a,ds,s:variant!='closed_list' and (n,a,s)==('examples','author','text') and
                [symbol(x) for x in ds.items]==(['su','st','ss'] if variant=='reverse_examples' else ['ss','st','su']),
            ue=lambda a,b,s:(a,b,s)==(('examples','cause','text') if variant=='reverse_order' else ('cause','examples','text')))
        rows[variant]=evaluate(doc,v,('examples','cause','author','other'),('text',))
        assert rows[variant]==[variant=='baseline']
    return dict(contrasts=rows,all_pastoral_and_task_facts_unknown=True)

def structure():
    old,new=parent(),load_catalog(ROOT,BASIS)
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==42
    assert set(new.entries)-set(old.entries)=={'rqxl','rqxm','hzwu'}
    assert [n for n in old.entries if old.entries[n]['declaration']!=new.entries[n]['declaration']]==['sp']
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in old.entries if n!='sp')
    affected=[i for i,s in enumerate(new.document['statements']) if 'sp' in {d['name'] for d in closure(new.document,_references(s))}]
    assert affected==[4]
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in r['selection']['statements']]
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a==r['selection'] and a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2,3],[5]):
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s
    for p in (FULL,CORE,LIBRARY):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            s=format_graph(d,style);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    assert validate(json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=42,changed_definitions=['sp'],affected_statements=affected,
        added_definitions=2,added_primitives=1,moved_unchanged_primitives=['hzwn','hzwo'],preserved_review_meanings=11,
        first_cause_sentence_meanings_unchanged=True,payment_meanings_unchanged=True,roundtrips=True,primary_evidence_valid=True)

def audit():
    inv='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in json.loads((ROOT/inv).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='einen Seelsorger, der für mich Gewissen hat';start=unit['text'].index(phrase)
    paths=(PARENT,PARENT_BASIS,INDEX,inv,EVIDENCE,'artifacts/first-cause-reading-v1/page-482.jpg','docs/substituted-judgment-v1.md')
    return dict(status='partial_principal_pastoral_role',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        reading='宗教的な配慮を主な務めとする役割を担う者が、本人に代わる道徳上の判断を供するという職務上の読み。',
        evidence=EVIDENCE,consulted='https://korpora.org/Kant/aa08/035.html',
        decisions=['役割の保持・機能・主要性を同じ役割と状況へ結ぶ。',
            '主要な務めを唯一の務めや数値的な時間割合へ変えない。',
            '教義の真理、本人の信仰・現在の成功、特定教派の叙任手続は追加しない。'],
        remaining=['宗教的な配慮を判断の援助で表す範囲、聖職者の制度上の全条件','良心の語義と談話上の働き',
            '書物・医師の残る語義、第二段落全体','二作品全文'],
        whole_unit_semantically_verified=False,full_noun_equivalence=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})

def build_report():
    results={}
    for n,f in [('generic',generic_checks),('source',source_checks),('integration',integration_checks),('attribution',attribution_checks),('structure',structure)]:
        results[n]=f();print(n+' checked',flush=True)
    reading=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==reading
    paths=set(build())|set(parent().source_sha256)|set(reading['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_pastoral_roles.py','scripts/check_pastoral_roles.py','scripts/register_pastoral_roles.py',
        'scripts/fetch_pastoral_role_evidence.py','tests/test_pastoral_roles.py','scripts/check_written_carriers.py',
        'scripts/check_role_qualifications.py','scripts/check_substituted_judgment.py','scripts/check_motive_causes.py',
        'scripts/check_designation_order.py','scripts/compose_falling_depiction.py','noema/constructed.py',
        'noema/constructed_semantics.py','noema/constructed_discourse.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_principal_pastoral_role_composition',document=FULL,**results,
        alignment=dict(**reading['source'],definitions=['rqxl','rqxm','sp','st'],status='explicit_interpretive_annotation'),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))

if __name__=='__main__':main()
