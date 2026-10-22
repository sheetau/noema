"""Check subject identity and belief without treating necessary means as true."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_personal_salvation_judgment import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build
from scripts.check_civic_compatibility import PROVIDERS,base,run,content,SCENES,DOMAIN,EXTRA
from scripts.check_motive_causes import unknown

DOC='docs/personal-salvation-judgment-v1.md'
READING='data/personal-salvation-judgment-reading-v1.json'
REPORT='reports/personal-salvation-judgment-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/monarchical-sentence-v1.json','reports/single-ruler-v1.json','reports/civic-compatibility-v1.json')
A='k zalpha[]';B='k zbeta[]';R='k zreference[]';P='k zcandidate[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    prefix=parse('p:'+EXTRA+PROVIDERS+'r zsaveone[i b[e]] c.')
    providers={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in providers]+[providers.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)

def personal(v,person='alpha',undertaking='beta',goal='alpha',reference='reference'):
    v['h26hj']=lambda *a:a==(goal,person,reference)
    v['h26hk']=lambda *a:a==(undertaking,person,reference)
    return v

@lru_cache(None)
def subject_checks():
    d=fixture('q[k r5ni['+' '.join((A,B,A,P))+']].',('r2uj','r2ui'));rows={}
    for variant in ('baseline','no_person','no_monarch','no_office','no_holder','no_subjection','other_person','other_role','other_community','other_point','unknown'):
        v=base(d)
        if variant=='no_person':v['aa']=lambda *a:False
        v['r2uj']=lambda *a:a==('alpha','alpha','candidate') and variant!='no_monarch'
        v['h234f']=lambda *a:a==('beta','alpha','candidate') and variant!='no_office'
        v['r2ui']=lambda *a:a==('alpha','beta','alpha','candidate') and variant!='no_holder'
        wanted=['beta','beta','alpha','candidate']
        changes={'other_person':(0,'alpha'),'other_role':(1,'alpha'),'other_community':(2,'beta'),'other_point':(3,'end')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26hi']=lambda *a:a==tuple(wanted) and variant!='no_subjection'
        if variant=='unknown':
            v['h26hi']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown subjection')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(same_person_monarch_office_community_and_point=rows,boundaries=['r2uj','r2ui'],actual_obedience_not_required=True,unknown_rejected=True)

@lru_cache(None)
def necessity_checks():
    d=fixture('q[t[k r5nl['+' '.join((A,B,A,R))+']]['+P+']].');rows={}
    for variant in ('baseline','not_sufficient','counterexample','no_success','empty_scope','only_outside_scope_success','no_person','not_own_goal','not_own_action','other_reference','other_assessment','other_person','other_undertaking','other_goal','unknown'):
        v=personal(base(d));wanted=['alpha','beta','alpha','reference','candidate']
        changes={'other_person':(0,'beta'),'other_undertaking':(1,'alpha'),'other_goal':(2,'beta'),'other_reference':(3,'assessment'),'other_assessment':(4,'end')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26hl']=lambda *a:a[:-1]==tuple(wanted) and a[-1] in ('start','end') and variant!='empty_scope'
        truth={('alpha','start'),('beta','start')}
        if variant=='not_sufficient':truth.add(('beta','end'))
        if variant=='counterexample':truth.add(('alpha','end'))
        if variant=='no_success':truth={('beta','start')}
        if variant=='only_outside_scope_success':truth={('alpha','candidate'),('beta','candidate')}
        if variant=='no_person':v['aa']=lambda *a:False
        if variant=='not_own_goal':v['h26hj']=lambda *a:a==('alpha','beta','reference')
        if variant=='not_own_action':v['h26hk']=lambda *a:a==('beta','beta','reference')
        v['ztruth']=lambda obj,p:(obj,p) in truth
        if variant=='unknown':
            v['ztruth']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown means')
            continue
        actual=run(d,v);assert actual==[variant in ('baseline','not_sufficient')],(variant,actual);rows[variant]=actual[0]
        assert v['h26hm'] is unknown
    return dict(native_necessary_means=rows,success_nonempty=True,necessity_does_not_imply_sufficiency=True,unknown_rejected=True,boundaries=[])

@lru_cache(None)
def belief_checks():
    # Construct the expected specialization independently of r5nm, so a shared
    # argument-order or target error in that helper cannot make both sides agree.
    literal='o a[r b[p r5nl]][r[k zalpha[]] r[k zbeta[]] r[k zalpha[]] r[k zreference[]]]'
    query='q[k zsaveone['+literal+']].q[k r5no['+' '.join((A,B,A,R,P))+']].'
    rows={}
    for variant in ('baseline','false_necessity','impossible_goal','unexecuted_contents','no_belief','other_person','other_point','wrong_name','wrong_reference_name','wrong_order','not_own_goal','not_own_action','unknown'):
        selected=query
        if variant=='wrong_order':selected=query.replace(literal,'o a[r b[p r5nl]][r[k zbeta[]] r[k zalpha[]] r[k zalpha[]] r[k zreference[]]]',1)
        if variant in ('false_necessity','impossible_goal'):selected+='q[t[k r5nl['+' '.join((A,B,A,R))+']]['+P+']].'
        d=fixture(selected);v=personal(base(d));saved=[];v['zsaveone']=lambda code:saved.append(code) is None
        v['h26hm']=lambda p,code,at:variant!='no_belief' and (p,at)==('beta' if variant=='other_person' else 'alpha','end' if variant=='other_point' else 'candidate') and code.rank==1 and code.syntax==saved[0].syntax
        v['h26hl']=unknown;v['ztruth']=unknown
        if variant in ('false_necessity','impossible_goal'):
            v['h26hl']=lambda *a:a==('alpha','beta','alpha','reference','candidate','start')
            v['ztruth']=lambda obj,p:variant=='false_necessity' and (obj,p)==('alpha','start')
        if variant=='wrong_name':v['znamepick']=lambda obj,a,b,c:a
        if variant=='wrong_reference_name':v['zrefpick']=lambda p,r,a:a
        if variant=='not_own_goal':v['h26hj']=lambda *a:False
        if variant=='not_own_action':v['h26hk']=lambda *a:False
        if variant=='unknown':
            v['h26hm']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown belief')
            continue
        actual=run(d,v);expected=[True,variant in ('baseline','false_necessity','impossible_goal','unexecuted_contents')]
        if variant in ('false_necessity','impossible_goal'):expected.append(False)
        assert actual==expected,(variant,actual);rows[variant]=actual
    positions=[]
    for i in range(3):
        b=['alpha']*3;b[i]='beta';args=' '.join('k z'+x+'[]' for x in b)
        literal='o a[r b[p r5nl]]['+' '.join('r[k z'+x+'[]]' for x in b)+' r[k zreference[]]]'
        d=fixture('q[k zsaveone['+literal+']].q[k r5no['+args+' '+R+' '+P+']].');v=personal(base(d),*b);saved=[]
        v['zsaveone']=lambda code:saved.append(code) is None
        v['h26hm']=lambda p,code,at:(p,at)==(b[0],'candidate') and code.rank==1 and code.syntax==saved[0].syntax
        assert run(d,v)==[True,True];v['znamepick']=lambda obj,a,b,c:a;assert run(d,v)==[True,False];positions.append(i)
    malformed=(ROOT/LIBRARY).read_text(encoding='utf-8').replace('r b[p r5nl]','r[p r5nl]')
    try:parse(malformed)
    except (ValueError,TypeError):pass
    else:raise AssertionError('Rank-zero necessity accepted')
    return dict(fallible_judgment=rows,all_three_name_positions=positions,rank_zero_rejected=True,unknown_rejected=True)

@lru_cache(None)
def connection_checks():
    # Exercise actual conduct natively; belief and salvation achievement remain unknown/false.
    d=fixture('q[t[k r5np[k zbindings[] '+R+']]['+P+']].');v=personal(base(d,('alpha','beta','alpha')))
    v['ztruth']=lambda obj,p:(obj,p)==('beta','candidate')
    assert run(d,v)==[True] and v['h26hm'] is unknown
    v['ztruth']=lambda obj,p:(obj,p)==('alpha','candidate');assert run(d,v)==[False]
    positions=[]
    for i in range(3):
        b=tuple('beta' if i==j else 'alpha' for j in range(3));v=personal(base(d,b),*b)
        v['ztruth']=lambda obj,p:(obj,p)==(b[1],'candidate')
        assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*3,'"individual"');assert run(d,v)==[False];positions.append(i)
    for size in (2,4):v['zbindings']=lambda:SequenceValue(('alpha',)*size,'"individual"');assert run(d,v)==[False]
    connected=[]
    for i in range(5):
        b=tuple('beta' if i==j else 'alpha' for j in range(5));args=' '.join('k z'+x+'[]' for x in b)
        d=fixture('q[k r5nq['+args+' '+R+' '+P+']].',('r5ni','r5no'));v=base(d)
        actor,person,community,undertaking,goal=b
        v['r5ni']=lambda *a:a==(actor,person,community,'candidate')
        v['r5no']=lambda *a:a==(person,undertaking,goal,'reference','candidate')
        assert run(d,v)==[True];v['zbeta']=lambda:'alpha';assert run(d,v)==[False];connected.append(i)
    for relation in ('r5ni','r5no'):
        v=base(d);v['r5ni']=lambda *a:True;v['r5no']=lambda *a:True;v[relation]=lambda *a:False;assert run(d,v)==[False]
    return dict(native_conduct_without_goal_achievement_or_belief=True,exact_three_conduct_bindings=positions,all_five_subject_judgment_bindings=connected,boundaries_for_connection_only=['r5ni','r5no'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if 'page-490' in p['path']]
    return dict(status='partial_subject_scope_and_personal_salvation_judgment',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3353,3464],text=u['text'][3353:3464]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,primary_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='5–10',observation='同じ君主の臣民と、本人が救済のため必要と考える営み。後続の委ね方と職責・妨害防止は別に残す。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_4_1_1277',entry='Der Unterthan, 第二義, 1119–1120頁',observation='国家・領邦の最高権力に服する共同体成員の義を採用。私的領主の農奴的身分という別義へ狭めない。')],
        unresolved=['同じ臣民全員へ本人に委ねる範囲とkann/nur/übrigens','Wennの監督条件との接続','君主の職責と暴力的妨害防止','同じ救済の決定と全能力での促進','全文の照応・提示・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent()
    for n in read(BASIS)['imported_symbols']:
        assert c.entries[n]['declaration']==old.entries[n]['declaration'] and c.entries[n]['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record() and len(old.document['statements'])==106
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=106,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('subjects',subject_checks),('necessity',necessity_checks),('belief',belief_checks),('connections',connection_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_personal_salvation_judgment.py','scripts/check_personal_salvation_judgment.py','tests/test_personal_salvation_judgment.py',
        'scripts/check_civic_compatibility.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='same_political_subject_and_fallible_necessary_means_to_own_salvation',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
