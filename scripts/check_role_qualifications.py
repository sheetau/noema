"""Check role/qualification bindings without treating requirements as actual skills."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts.compose_role_qualifications import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,parent,build,closure
from scripts.check_substituted_judgment import source_model,SOURCE_PEOPLE,SOURCE_SCENES
from scripts.check_motive_causes import unknown,symbol
from scripts.check_designation_order import substantive

INDEX='data/semantic-review-index-v45.json'
REPORT='reports/role-qualifications-v1.json'
AUDIT='data/role-qualifications-reading-v1.json'
DOC='docs/role-qualifications-v1.md'

def evaluate(doc,v,people,scenes):
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=scenes,
        primitives={d['name']:v[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},max_steps=10000000)]

def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r jp[] a.r js[] d.
r jh[a a d] c.r jf[a i[h[a] e] d] c.r jn[a i[h[a] e] d] c.r ju[a d] c.
d jrepair[person a] e[b scene[k ju[v person v scene]]].
d jtraining[person a] e[b scene[k ju[v person v scene]]].
d jother[person a] e[b scene[k ju[v person v scene]]].
q[k rqxh[k jp[] r[p jrepair] r[p jtraining] k js[] p jh p jf p jn]].''')
    people=('worker','other','roleA','roleB');scenes=('now','elsewhere');rows=[]
    for bits in product((False,True),repeat=6):
        held={r for r,b in zip(('roleA','roleB'),bits[:2]) if b}
        functions={r for r,b in zip(('roleA','roleB'),bits[2:4]) if b}
        requirements={r for r,b in zip(('roleA','roleB'),bits[4:]) if b}
        v=dict(jp=lambda:'worker',js=lambda:'now',ju=unknown,
            jh=lambda p,r,s:p=='worker' and r in held and s=='now',
            jf=lambda r,d,s:r in functions and symbol(d)=='jrepair' and s=='now',
            jn=lambda r,d,s:r in requirements and symbol(d)=='jtraining' and s=='now')
        actual=evaluate(doc,v,people,scenes)[0]
        assert actual==bool(held&functions&requirements)
        rows.append(dict(bits=list(bits),value=actual))
    contrast={}
    for variant in ('baseline','other_holder','other_function','other_requirement','other_time','split_role'):
        v=dict(jp=lambda:'worker',js=lambda:'now',ju=unknown,
            jh=lambda p,r,s:(p,r,s)==('other' if variant=='other_holder' else 'worker','roleA','now'),
            jf=lambda r,d,s:(r,symbol(d),s)==('roleB' if variant=='split_role' else 'roleA',
                'jother' if variant=='other_function' else 'jrepair','now'),
            jn=lambda r,d,s:(r,symbol(d),s)==('roleA','jother' if variant=='other_requirement' else 'jtraining',
                'elsewhere' if variant=='other_time' else 'now'))
        contrast[variant]=evaluate(doc,v,people,scenes)[0]
        assert contrast[variant]==(variant=='baseline')
    return dict(role_combinations=rows,repair_practice_contrasts=contrast,qualification_content_not_executed=True)

@lru_cache(None)
def source_doc(previous=False):
    c=parent() if previous else load_catalog(ROOT,BASIS);d=deepcopy(c.document)
    d.update(declarations=closure(d,['sr','su','sv','re','s2','sy','wh']),statements=[])
    return parse(format_graph(d,'compact')+'''r jperson[] a.r jprovider[] a.r jscene[] d.
q[k sr[k jprovider[] k jscene[]]].q[t[k su[k jperson[]]][k jscene[]]].
q[t[k sv[k jperson[]]][k jscene[]]].
q[k re[k jperson[] p sv i[scene d][k s2[k jperson[] k wh[] v scene]]]].
q[t[k sy[k jperson[]]][k wh[]]].''')

def source_values(variant):
    v=source_model(source_doc(),variant)
    provider='guide' if variant=='shared_human_provider' else 'doctor'
    v.update(jperson=lambda:'person',jprovider=lambda:provider,jscene=lambda:'case',hzwq=unknown,
        hzwn=lambda p,r,s:variant!='family_helper' and (p,r,s)==(
            'other' if variant=='other_holder' else provider,'roleA','case'),
        hzwo=lambda r,d,s:(r,symbol(d),s)==('roleB' if variant=='split_role' else 'roleA',
            'sn' if variant=='other_role_function' else 'sq','case'),
        hzwp=lambda r,d,s:variant!='no_qualification_requirement' and (r,symbol(d),s)==(
            'roleB' if variant=='requirement_on_other_role' else 'roleA',
            'sn' if variant=='other_qualification' else 'rqxi','text' if variant=='other_role_context' else 'case'))
    return v

def source_checks():
    invalid_supply=('inaccessible_text','missing_access','wrong_task','split_provider','wrong_beneficiary','wrong_role')
    invalid_result=('failed_goal','unavailable_plan','empty_results','own_effort')
    invalid_role=('family_helper','other_holder','split_role','other_role_function','no_qualification_requirement',
        'requirement_on_other_role','other_qualification','other_role_context')
    variants=('baseline','shared_human_provider',*invalid_supply,*invalid_result,'empty_cases','wrong_perspective',*invalid_role)
    rows={};people=(*SOURCE_PEOPLE,'roleA','roleB')
    for variant in variants:
        v=source_values(variant)
        new=evaluate(source_doc(),v,people,SOURCE_SCENES)
        old=evaluate(source_doc(True),v,people,SOURCE_SCENES)
        role=variant not in (*invalid_role,'wrong_role')
        su=role and variant not in ('missing_access','split_provider','wrong_beneficiary')
        premise=variant not in (*invalid_supply,*invalid_role)
        applicable=premise and variant not in ('empty_cases','wrong_perspective')
        conditional=variant not in ('empty_cases','wrong_perspective') and (not premise or variant not in invalid_result)
        assert new==[role,su,premise,applicable,conditional],(variant,new)
        if variant in invalid_role:assert old==[True]*5,(variant,old)
        else:assert new==old,(variant,new,old)
        rows[variant]=dict(previous=old,current=new)
    for n in ('hzwn','hzwo','hzwp'):
        v=source_values('baseline');v[n]=unknown
        try:evaluate(source_doc(),v,people,SOURCE_SCENES)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(contrasts=rows,definitions_replaced_by_primitives=False,
        actual_qualification_unknown=True,unknown_role_relations_refused=3,ordinary_evaluation=True)

def competence_checks():
    c=load_catalog(ROOT,BASIS);d=deepcopy(c.document)
    d.update(declarations=closure(d,['sr','rqxi']),statements=[])
    doc=parse(format_graph(d,'compact')+'''r jp[] a.r js[] d.
q[k sr[k jp[] k js[]]].q[t[k rqxi[k jp[]]][k js[]]].''')
    rows=[]
    for role,skill in product((False,True),repeat=2):
        v=source_values('baseline');v.update(jp=lambda:'doctor',js=lambda:'case',
            hzwn=lambda p,r,s:role and (p,r,s)==('doctor','roleA','case'),
            hzwq=lambda p,t,s:skill and (p,symbol(t),s)==('doctor','sq','case'))
        actual=evaluate(doc,v,(*SOURCE_PEOPLE,'roleA'),SOURCE_SCENES)
        assert actual==[role,skill]
        rows.append(dict(role=role,actual_skill=skill,values=actual))
    for variant in ('other_person','other_task','other_scene'):
        v=source_values('baseline');v.update(jp=lambda:'doctor',js=lambda:'case',
            hzwq=lambda p,t,s:(p,symbol(t),s)==('other' if variant=='other_person' else 'doctor',
                'sn' if variant=='other_task' else 'sq','text' if variant=='other_scene' else 'case'))
        assert evaluate(doc,v,(*SOURCE_PEOPLE,'roleA'),SOURCE_SCENES)==[True,False]
    return dict(independent_role_and_skill=rows,skill_binding_contrasts=3)

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
    return dict(contrasts=rows,all_role_and_task_facts_unknown=True)

def structure():
    old,new=parent(),load_catalog(ROOT,BASIS)
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==42
    assert set(new.entries)-set(old.entries)==set(PRIMITIVES)|{'rqxh','rqxi','rqxj'}
    assert [n for n in old.entries if old.entries[n]['declaration']!=new.entries[n]['declaration']]==['sr']
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in old.entries if n!='sr')
    affected=[i for i,s in enumerate(new.document['statements']) if 'sr' in {d['name'] for d in closure(new.document,_references(s))}]
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
    return dict(preserved_statements=42,changed_definitions=['sr'],affected_statements=affected,
        new_definitions=3,new_primitives=4,preserved_review_meanings=11,
        first_cause_sentence_meanings_unchanged=True,payment_meanings_unchanged=True,roundtrips=True)

def audit():
    inv='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in json.loads((ROOT/inv).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='einen Arzt der für mich die Diät beurtheilt';start=unit['text'].index(phrase)
    paths=(PARENT,PARENT_BASIS,INDEX,inv,'artifacts/first-cause-reading-v1/page-482.jpg','docs/substituted-judgment-v1.md')
    return dict(status='partial_medical_role_qualification_explanation',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        consulted='https://korpora.org/Kant/aa08/035.html',
        reading='医師を、専門的な知識・技能を資格要件とする健康上の助言の役割として部分的に説明する。',
        findings=['旧srは継続的な健康助言者だけを要求し、専門的な役割を持たない家族なども許した。',
            '実際の能力を直接必須にすると、役割を持つが能力が不足する人や誤る人を記述できなくなる。'],
        decisions=['役割保持・機能・資格要求を同じ役割と状況へ結ぶ。専門性の対象を健康判断sqにそろえる。',
            '要求の内容は引用し、本人の実際の技能を実行評価しない。技能を述べたい場合は同じ記述を別に実行できる。',
            '現代の免許・学位・特定の法制度・診断の成功を原文へ補わない。'],
        remaining=['他の健康専門職との歴史的な役割境界','役割・知識・学習の基礎説明','書物・宗教上の助言者・良心の意味と第二段落全体','二作品全文'],
        whole_unit_semantically_verified=False,full_noun_equivalence=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})

def build_report():
    results={}
    for n,f in [('generic',generic_checks),('source',source_checks),('competence',competence_checks),('attribution',attribution_checks),('structure',structure)]:
        results[n]=f();print(n+' checked',flush=True)
    reading=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==reading
    paths=set(build())|set(parent().source_sha256)|set(reading['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_role_qualifications.py','scripts/check_role_qualifications.py','scripts/register_role_qualifications.py',
        'tests/test_role_qualifications.py','scripts/check_substituted_judgment.py','scripts/check_motive_causes.py',
        'scripts/check_designation_order.py','scripts/compose_falling_depiction.py','noema/constructed.py',
        'noema/constructed_semantics.py','noema/constructed_discourse.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_role_qualification_composition',document=FULL,**results,
        alignment=dict(**reading['source'],definitions=['rqxh','rqxi','rqxj','sr','su'],status='explicit_interpretive_annotation'),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))

if __name__=='__main__':main()
