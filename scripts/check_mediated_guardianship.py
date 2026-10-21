"""Check all members, same mediated role, turnover, duration and quoted purpose."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_grounded_step import closure
from scripts.compose_mediated_guardianship import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build
from scripts.check_motive_causes import unknown,symbol
from scripts.check_pastoral_roles import evaluate
from scripts.check_irrevisable_confession import DOMAIN as FORM_DOMAIN,SCENES,formation_model
from scripts.check_promissory_oath import modifiers

REPORT='reports/mediated-guardianship-v1.json'
DOC='docs/mediated-guardianship-v1.md'
READING='data/mediated-guardianship-reading-v1.json'
PRIORS=('reports/promissory-oath-v1.json','reports/continuing-institutions-v1.json','reports/fifth-paragraph-v1.json')
DOMAIN=('body','person','second','ward','other','role','matter','subject','community')
NAMES=tuple(dict.fromkeys((*DOMAIN,*FORM_DOMAIN)))
EXTRA=''.join('r z'+n+'[] a.' for n in NAMES)+''.join('r zt'+n+'[] d.' for n in SCENES)
ARGS='k zbody[] k zcommunity[] k zsubject[] k ztreference[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in NAMES});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    return v


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


def point_model(doc,variant='baseline'):
    v=base(doc)
    def people(point):
        return ('second','other') if point=='future' and variant=='turnover' else ('person','ward')
    def members(body,person,point):
        allowed={people(point)[0]}
        if variant=='extra_member':allowed.add('second')
        if variant=='nonhuman_member':allowed.add('matter')
        if variant=='empty_members':allowed.clear()
        return body=='body' and person in allowed
    def citizens(person,community,point):
        allowed={people(point)[1]}
        if variant=='extra_ward':allowed.add('other')
        if variant=='empty_people':allowed.clear()
        return community=='community' and person in allowed
    v['h246c']=members;v['h237c']=citizens
    v['aa']=lambda p:p in ('person','second','ward','other')
    v['h246d']=lambda body,point:body=='body' and variant!='not_institution'
    v['h245z']=lambda subject,ref:(subject,ref)==('subject','reference') and variant!='not_religious'
    v['hzwn']=lambda actor,role,point:actor in ('body',people(point)[0]) and role=='role'
    def control(actor,ward,point):
        member,citizen=people(point)
        return (actor,ward)==('body',member) and variant!='missing_upper' or (actor,ward)==(member,citizen) and variant!='missing_lower'
    v['dc']=control
    v['sg']=lambda matter,person,point:matter=='matter' and person in people(point) and variant!='reversed_spiritual_args'
    def scope(actor,ward,role,matter,point):
        return role==('other' if variant=='different_role' else 'role') and matter=='matter' and control(actor,ward,point)
    v['h253r']=scope
    v['h255i']=lambda matter,subject,ref:(matter,subject,ref)==('matter','subject','reference') and variant!='different_subject'
    def mediation(body,member,role,ward,matter,point):
        if variant=='independent_lower':return False
        if variant=='middle_gap' and point=='middle':return False
        principal='other' if variant=='other_body' else 'body'
        expected_role='other' if variant=='other_mediating_role' else 'role'
        expected_matter='other' if variant=='other_mediating_matter' else 'matter'
        return (body,member,role,ward,matter)==(principal,people(point)[0],expected_role,people(point)[1],expected_matter)
    v['h255j']=mediation
    history=('reference','middle','future')
    v['h253w']=lambda community,candidate,point:(community,candidate)==('community','candidate') and point in history and not (variant=='missing_anchor' and point=='reference')
    def order(first,last,candidate):
        result=candidate=='candidate' and first in history and last in history and history.index(first)<history.index(last)
        if variant=='cycle' and (first,last)==('future','reference'):return True
        if variant=='missing_transitive' and (first,last)==('reference','future'):return False
        return result
    v['ic']=order
    return v


@lru_cache(None)
def point_checks():
    doc=fixture(('r464',),'q[k r464['+ARGS+' k ztreference[]]].q[k r464['+ARGS+' k ztfuture[]]].')
    rows={}
    variants=('baseline','turnover','extra_member','extra_ward','nonhuman_member','empty_members','empty_people',
              'not_institution','not_religious','missing_upper','missing_lower','reversed_spiritual_args','different_role',
              'different_subject','independent_lower','other_body','other_mediating_role','other_mediating_matter')
    for variant in variants:
        actual=run(doc,point_model(doc,variant));assert actual==[variant in ('baseline','turnover')]*2,(variant,actual);rows[variant]=actual
    for name in ('dc','sg','hzwn','h253r','h246c','h237c','h255i','h255j'):
        v=point_model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_all_members_and_all_people=rows,correct_matter_person_order=True,
        mediation_not_inferred_from_two_control_edges=True,unknown_not_false=True)


@lru_cache(None)
def temporal_checks():
    q=''.join('q[t[k '+n+'['+ARGS+']][k ztcandidate[]]].' for n in ('r466','r467'))
    native=fixture(('r466','r467'),q);rows={}
    for variant in ('turnover','middle_gap'):
        actual=run(native,point_model(native,variant));expected=[variant=='turnover',False]
        assert actual==expected,(variant,actual);rows[variant]=actual
    boundary=fixture(('r466','r467'),q,('r464',))
    for variant in ('baseline','missing_anchor','cycle','missing_transitive'):
        v=point_model(boundary,variant);v['r464']=lambda body,community,subject,ref,point:(body,community,subject,ref)==('body','community','subject','reference')
        actual=run(boundary,v);assert actual==[variant=='baseline',False],(variant,actual);rows[variant]=actual
    return dict(native_turnover_and_midcourse_mediation_gap=rows,
        malformed_order_tests_boundary='r464; native point and native temporal integration tested separately',
        no_finite_history_claimed_endless=True,no_numeric_infinity_claim=True)


@lru_cache(None)
def causal_checks():
    doc=fixture(('r47b',),'q[t[k r47b[k zbody[] k zagreement[] k zcommunity[] k zsubject[] k ztreference[]]][k ztcandidate[]]].',('r467',))
    rows={}
    for variant in ('baseline','no_result','no_cause','other_agreement','other_body','wrong_code','wrong_bindings','wrong_reference','wrong_candidate'):
        v=base(doc)
        v['r467']=lambda *args:Content(SCENES,tuple(variant!='no_result' and args==('body','community','subject','reference') and at=='candidate' for at in SCENES))
        def cause(agreement,body,code,bindings,ref,candidate):
            wanted=('other' if variant=='other_agreement' else 'agreement','other' if variant=='other_body' else 'body',
                    'r466' if variant=='wrong_code' else 'r47a',0,('body','subject','community') if variant=='wrong_bindings' else ('body','community','subject'),
                    'middle' if variant=='wrong_reference' else 'reference','future' if variant=='wrong_candidate' else 'candidate')
            return variant!='no_cause' and (agreement,body,symbol(code),code.rank,tuple(bindings.items),ref,candidate)==wanted
        v['h255k']=cause
        actual=run(doc,v,(*DOMAIN,'agreement'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v['h255k']=unknown
    try:run(doc,v,(*DOMAIN,'agreement'))
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown causal input accepted')
    return dict(same_causal_result_and_truth=rows,boundary='r467; no finite positive model is presented as endless',
        shared_closed_result_expanded_statically=True,unknown_causation_not_false=True)


@lru_cache(None)
def bindings_checks():
    rows={}
    for name,names,target in (('r47a',('body','community','subject'),'r467'),('r47c',('body','agreement','community','subject'),'r47b')):
        for seq in (names,names[:-1],(*names,'body'),tuple(reversed(names))):
            literal='l[a]['+' '.join('k z'+n+'[]' for n in seq)+']'
            doc=fixture((name,),'q[t[k '+name+'['+literal+' k ztreference[]]][k ztcandidate[]]].',('r466',target))
            v=base(doc)
            def content(expected):return lambda *args:Content(SCENES,tuple(args==expected and at=='candidate' for at in SCENES))
            v['r466']=content(('body','community','subject','reference'))
            v[target]=content((*names,'reference'))
            actual=run(doc,v,names);assert actual==[seq==names],(name,seq,actual);rows[name+str(seq)]=actual[0]
    return dict(exact_result_three_and_goal_four_bindings=rows,boundaries='r466/r467/r47b; native temporal and causal wrappers tested separately')


@lru_cache(None)
def formation_checks():
    args='k zbody[] k zagreement[] k zcreed[] k zsubject[]'
    query='q[k r46z['+args+' k ztreference[]]].q[k r47d['+args+' k zcommunity[] k ztreference[]]].'
    doc=fixture(('r46z','r47d'),query);rows={}
    variants=('baseline','no_goal','other_goal','other_goal_body','other_goal_agreement','other_community','other_subject','other_reference','no_collective_act','second_outside_collective',
              'separate_act','separate_person','separate_time','separate_body','separate_agreement')
    for variant in variants:
        v=modifiers(formation_model(doc));v.update({'z'+n:lambda n=n:n for n in NAMES});v.update({'zt'+n:lambda n=n:n for n in SCENES})
        def goal(body,agreement,code,bindings,ref):
            expected=('other' if variant=='other_goal_body' else 'body','other' if variant=='other_goal_agreement' else 'agreement','r466' if variant=='other_goal' else 'r47c',0,
                ('body','agreement','other' if variant=='other_community' else 'community','other' if variant=='other_subject' else 'subject'),
                'middle' if variant=='other_reference' else 'reference')
            return variant!='no_goal' and (body,agreement,symbol(code),code.rank,tuple(bindings.items),ref)==expected
        v['h255l']=goal
        def participant(person,act,body,agreement,point):
            if variant=='second_outside_collective' and person=='second':return False
            expected_body='other' if variant=='separate_body' else 'body';expected_agreement='other' if variant=='separate_agreement' else 'agreement'
            allowed={('person','acta','past'),('second','actb','reference')}
            if variant=='separate_act':allowed={('person','other','past'),('second','other','reference')}
            if variant=='separate_person':allowed={('other','acta','past'),('other','actb','reference')}
            if variant=='separate_time':allowed={('person','acta','middle'),('second','actb','middle')}
            return variant!='no_collective_act' and (body,agreement)==(expected_body,expected_agreement) and (person,act,point) in allowed
        v['h255m']=participant
        actual=run(doc,v,(*FORM_DOMAIN,'community'));assert actual==[True,variant=='baseline'],(variant,actual);rows[variant]=actual
        assert all(v[n] is unknown for n in ('h255e','dc','h255i','h255j','h255k','h253w'))
    for name in ('h255l','h255m'):
        # Reuse the final total model; an unknown required input must still be rejected.
        checked=dict(v);checked[name]=unknown
        try:run(doc,checked,(*FORM_DOMAIN,'community'))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_same_oath_and_collective_purpose=rows,purpose_not_executed=True,
        does_not_require_all_private_motives_to_match=True)


def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    phrase='um so eine unaufhörliche Obervormundschaft über jedes ihrer Glieder und vermittelst ihrer über das Volk zu führen, und diese so gar zu verewigen'
    start=unit['text'].index(phrase)
    return dict(status='mediated_guardianship_and_collective_perpetuation_purpose_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        primary_page=read('data/promissory-oath-reading-v1.json')['primary_page'],
        adopted_readings=[
            '同じ団体の各時点の全成員への宗教的な上位後見と、同じ成員の後見を介して政治的共同体の全人民へ及ぶ団体の指導。独立した二つの監督では代用しない。',
            '全将来の中断なしと、同じ合意の実施によって同じ後見を終点なしに成立・維持させる目的を分ける。後続のauf immerとも対応する強い読み。数値的な無限時間・成員個人の不死は加えない。',
            '合意を形成する団体の共同目的と、その目的を実施する同じ宣誓行為への参加。全員の私的な内心の目的の一致や目的の達成は外側で要求しない。'],
        remaining=['sogarの同じ二つの目的への強調','一般団体へのetwaの例示と会議体・自己呼称','権限の否定疑問と回答の統合'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)


@lru_cache(None)
def structure_checks():
    new=catalog();sources=parents()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            old=next(c.entries[n] for c in sources if n in c.entries)
            assert e['declaration']==old['declaration'] and e['meaning_ja']==old['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    assert read(READING)==reading_record()
    page=read(READING)['primary_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    assert not new.document['statements'] and len(sources[0].document['statements'])==96
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        source_range_and_primary_page_pinned=True,no_new_author_assertion=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    results={}
    for name,fn in [('point',point_checks),('temporal',temporal_checks),('causal',causal_checks),('bindings',bindings_checks),
                   ('formation',formation_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=read(READING)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,READING,reading['source_inventory'],reading['primary_page']['path'],
        'scripts/compose_mediated_guardianship.py','scripts/check_mediated_guardianship.py','tests/test_mediated_guardianship.py',
        'scripts/check_promissory_oath.py','scripts/check_irrevisable_confession.py','scripts/check_motive_causes.py','scripts/check_pastoral_roles.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_spiritual_guardians.py'}
    return dict(status='same_mediated_religious_guardianship_and_collective_perpetuation_purpose',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
