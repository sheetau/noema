"""Distinguish no family member permitted from an unpermitted aggregate goal."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_unpermitted_families import ROOT,FULL,CORE,LIBRARY,BASIS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_unpermitted_undertaking import undertaking_code

INDEX='data/semantic-review-index-v68.json'
REPORT='reports/unpermitted-families-v1.json'
READING='data/unpermitted-families-reading-v1.json'
DOC='docs/unpermitted-families-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('one','two','outside','source','person','role','other')
SCENES=('now','elsewhere')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def generic():
    suffix='''
r js[] a.r jp[] a.r jr[] a.r jc[] d.r jm[a] c.r jb[a] j[a].r jvalid[j[a]] c.
r jselect[a i[h[j[a]] e] i[h[j[a]] e]] i[h[j[a]] e].
r jdemands[a a a i[h[j[a]] e] j[a] c d] c.r jpermits[a a a i[h[j[a]] e] j[a] c d] c.
r jworld[j[a] d] c.
d jone[bindings j[a]] e[b scene[k jworld[v bindings v scene]]].
d jtwo[bindings j[a]] e[b scene[k jworld[v bindings v scene]]].
'''
    args='k js[] k jp[] k jr[] p jm i[item a][k jselect[v item r[p jone] r[p jtwo]]] p jb e[n p a b][n p a b] k jc[] p jvalid p jdemands p jpermits'
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+suffix+'q[k rqy6['+args+']].q[k rqy7['+args+']].')


def generic_values(members=(True,True),allowed=(False,False),valid=(True,True),variant='baseline'):
    def permits(source,person,role,description,bindings,polarity,scene):
        candidate='one' if symbol(description)=='jone' else 'two'
        idx=('one','two').index(candidate)
        return allowed[idx] and (source,person,role,bindings.items,polarity,scene)==(
            'other' if variant=='other_source' else 'source','other' if variant=='other_person' else 'person',
            'other' if variant=='other_role' else 'role',
            ('other',candidate) if variant=='other_binding_person' else ('person','outside') if variant=='other_binding_item' else ('person',candidate),
            variant!='other_polarity','elsewhere' if variant=='other_scene' else 'now')
    return dict(js=lambda:'source',jp=lambda:'person',jr=lambda:'role',jc=lambda:'now',
        jm=lambda item:item in ('one','two') and members[('one','two').index(item)],
        jselect=lambda item,one,two:two if (item=='one')==(variant=='swapped_descriptions') else one,
        jb=lambda item:SequenceValue(('person',item),'"individual"'),
        jvalid=lambda b:len(b.items)==2 and b.items[1] in ('one','two') and valid[('one','two').index(b.items[1])],
        jdemands=unknown,jpermits=permits,jworld=unknown)


def generic_checks():
    rows=[]
    for bits in product((False,True),repeat=6):
        members,allowed,valid=bits[:2],bits[2:4],bits[4:]
        actual=evaluate(generic(),generic_values(members,allowed,valid),DOMAIN,SCENES)
        expected=[all(not m or v and not p for m,p,v in zip(members,allowed,valid)),
            any(m and v and p for m,p,v in zip(members,allowed,valid))]
        assert actual==expected,(bits,actual,expected)
        rows.append(dict(members=members,allowed=allowed,valid=valid,values=actual))
    return dict(combinations=rows,empty_family_has_no_existence_claim=True,
        malformed_selected_binding_not_denied=True,world_contents_and_demands_unknown=True,ordinary_evaluation=True)


def scope_checks():
    rows={}
    for variant in ('baseline','other_source','other_person','other_role','other_binding_person',
            'other_binding_item','other_polarity','other_scene','swapped_descriptions'):
        actual=evaluate(generic(),generic_values(allowed=(True,True),variant=variant),DOMAIN,SCENES)
        assert actual==([False,True] if variant=='baseline' else [True,False]),(variant,actual)
        rows[variant]=actual
    # A permission outside the selected family must not invalidate its denial.
    actual=evaluate(generic(),generic_values(members=(True,False),allowed=(False,True)),DOMAIN,SCENES)
    assert actual==[True,False];rows['permission_outside_family']=actual
    for name in ('jm','jselect','jb','jvalid','jpermits'):
        v=generic_values();v[name]=unknown
        try:evaluate(generic(),v,DOMAIN,SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    v=generic_values(members=(False,False))
    for name in ('jselect','jb','jvalid','jpermits'):v[name]=unknown
    # The existing interpreter evaluates both operands of implication eagerly.
    # Total interpretations establish empty-family truth; partial callbacks may
    # still fail outside the selected family. Do not claim lazy evaluation.
    try:evaluate(generic(),v,DOMAIN,SCENES)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Expected the current eager runtime to require total callbacks')
    return dict(contrasts=rows,unknown_inputs_refused=5,unknown_outside_empty_family_refused=True,
        runtime_requires_total_callbacks_even_outside_selected_family=True,
        ordinary_evaluation=True)


@lru_cache(None)
def undertaking_fixture():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,['rqza','rqy6']),statements=[])
    suffix='''
r js[] a.r jp[] a.r jr[] a.r jc[] d.r jm[a] c.r jfirst[a d] c.r jsecond[a d] c.
r jselect[a i[h[a] e] i[h[a] e]] i[h[a] e].
d jone[person a] e[b scene[k jfirst[v person v scene]]].
d jtwo[person a] e[b scene[k jsecond[v person v scene]]].
d jbroad[person a] e[b scene[x[t[k jone[v person]][v scene]][t[k jtwo[v person]][v scene]]]].
q[t[k hztc[k js[] k jp[] k jr[] r[p jbroad]]][k jc[]]].
q[t[k rqza[k js[] k jp[] k jr[] p jm i[item a][k jselect[v item r[p jone] r[p jtwo]]]]][k jc[]]].
q[k rqy6[k js[] k jp[] k jr[] p jm
 i[item a][o a[r[p hzta]][o r[k jselect[v item r[p jone] r[p jtwo]]]]]
 i[item a][l[a][k jp[]]] e[n p a b][n p a b] k jc[] p hztb p h7k p h7l]].
'''
    return parse(format_graph(d,'compact')+suffix)


def source_checks():
    d=undertaking_fixture();rows=[]
    for broad,one,two in product((False,True),repeat=3):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(js=lambda:'source',jp=lambda:'person',jr=lambda:'role',jc=lambda:'now',
            jm=lambda item:item in ('one','two'),jselect=lambda item,a,b:a if item=='one' else b,
            h7l=lambda source,person,role,desc,args,polarity,scene:
                (source,person,role,args.items,polarity,scene)==('source','person','role',('person',),True,'now') and
                any(flag and undertaking_code(desc,name) for flag,name in ((broad,'jbroad'),(one,'jone'),(two,'jtwo'))))
        actual=evaluate(d,v,DOMAIN,SCENES)
        assert actual==[not broad,not(one or two),not(one or two)],(broad,one,two,actual)
        rows.append(dict(broad_allowed=broad,first_allowed=one,second_allowed=two,values=actual))
    counter=next(r for r in rows if not r['broad_allowed'] and r['first_allowed'] and not r['second_allowed'])
    assert counter['values']==[True,False,False]
    # The broad goal actually contains both individual goals. The distinction
    # is not just three uninterpreted labels for unrelated activities.
    goals=deepcopy(d);goals.update(declarations=closure(d,['jone','jtwo','jbroad','jp','jc']),statements=[])
    suffix=''.join('q[t[k '+n+'[k jp[]]][k jc[]]].' for n in ('jone','jtwo','jbroad'))
    goals=parse(format_graph(goals,'compact')+suffix);goal_rows=[]
    for first,second in product((False,True),repeat=2):
        values=evaluate(goals,dict(jp=lambda:'person',jc=lambda:'now',
            jfirst=lambda p,s:first,jsecond=lambda p,s:second),DOMAIN,SCENES)
        assert values==[first,second,first or second]
        goal_rows.append(dict(first=first,second=second,values=values))
    return dict(combinations=rows,counterexample=counter,goal_combinations=goal_rows,
        broad_goal_is_explicit_disjunction=True,adapter_matches_generic_family=True,
        broad_missing_permission_does_not_imply_none_of_members_permitted=True,
        actual_undertaking_courage_and_success_unknown=True,source_adoption=False,ordinary_evaluation=True)


def reading():
    prior=json.loads((ROOT/'data/walking-warning-reading-v1.json').read_text(encoding='utf-8'))
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    clause=next(c for c in prior['clauses'] if c['id']=='minimal_step');a,b=clause['range']
    assert unit['text'][a:b]==clause['text']
    paths=(PARENT,PARENT_BASIS,INDEX,INVENTORY,'data/walking-warning-reading-v1.json',
        'data/unpermitted-undertaking-reading-v1.json','artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='scope_counterexample_and_generic_family_construction',reviewer='assistant_review',document=FULL,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[a,b],text=clause['text']),
        decision='single_broad_permission_query_insufficient_for_no_individual_step_reading',source_adoption=False,
        findings=['現行hztcは指定した一つの目標記述の許容欠如を表す。別の個別目標への許容とは独立に解釈できる。',
            '包括的目標には許容がなく、一つの個別目標には許容がある解釈で、旧単一条件と全候補の無許容を区別した。',
            '許容を否定する範囲を候補集合と各候補の内容・引数で明示する構成を追加した。新しい意味の基本関係は追加しない。',
            '候補範囲を一歩の物理的構成と装置外へ正しく結んでいない段階では、有限の例を原文の全候補と認定しない。'],
        interpretation_limits=LIMITS,whole_sentence_semantically_verified=False,
        new_verified_sentence_characters=0,semantic_equivalence_automatically_proved=False,
        next_required=['身体的な一歩の構成と候補の記述','装置外という目標範囲の完全性','同じ先行時点の阻止・許容との結合',
            'ruhigenとjaの描写、一文全体の意味確認'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['statements']==old.document['statements'] and len(old.document['statements'])==47
    assert new.document['declarations'][:-3]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    assert idx['works']['kant-1784']['document']==PARENT
    for p in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/p).read_text(encoding='utf-8'));ids=[x['index'] for x in r['selection']['statements']]
        assert selection_binding(old,ids)==r['selection']==selection_binding(new,ids)
    assert selection_binding(old,list(range(47)))==selection_binding(new,list(range(47)))
    for path,text in build().items():assert (ROOT/path).read_text(encoding='utf-8')==text
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(x['kind']=='definition' for x in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    r=reading();assert r==json.loads((ROOT/READING).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    return dict(active_manuscript_unchanged=True,preserved_statements=47,new_definitions=3,new_primitives=0,
        preserved_review_selections=11,general_library_has_no_primitives=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('scope',scope_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{READING,DOC,
        'scripts/compose_unpermitted_families.py','scripts/check_unpermitted_families.py','scripts/register_unpermitted_families.py',
        'tests/test_unpermitted_families.py','scripts/check_unpermitted_undertaking.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','noema/constructed.py','noema/constructed_semantics.py','noema/meaning_catalog.py',
        'noema/semantic_reviews.py','noema/script.py'}
    return dict(status='quantified_permission_comparison_not_source_adoption',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
