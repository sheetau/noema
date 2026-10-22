"""Check personal non-direction separately from institutional competence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_personal_religious_remit import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build
from scripts.check_civic_compatibility import PROVIDERS,base,run,content,DOMAIN,EXTRA
from scripts.check_personal_salvation_judgment import personal
from scripts.check_covenant_nullity import normalized
from scripts.check_motive_causes import unknown

DOC='docs/personal-religious-remit-v1.md'
READING='data/personal-religious-remit-reading-v1.json'
REPORT='reports/personal-religious-remit-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/personal-salvation-judgment-v1.json','reports/monarchical-sentence-v1.json','reports/single-ruler-v1.json')
A='k zalpha[]';B='k zbeta[]';R='k zreference[]';P='k zcandidate[]'
ARGS=' '.join((A,B,A,B,A,R))

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    prefix=parse('p:'+EXTRA+PROVIDERS)
    providers={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in providers]+[providers.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)

def settings(d):
    v=personal(base(d),person='beta')
    v['h26hn']=lambda p,c,r:'alpha' if (p,c,r)==('beta','alpha','reference') else 'beta'
    return v

@lru_cache(None)
def norm_checks():
    d=fixture('q[k r5ns['+ARGS+' '+P+']].');rows={}
    for positive,negative in product((False,True),repeat=2):
        v=settings(d)
        v['h237z']=lambda s,p,role,code,b,r,sign,at:normalized((s,p,role,code,b,r,at))==('alpha','beta','alpha',('r5np',1),('beta','beta','alpha'),'reference','candidate') and (positive if sign else negative)
        actual=run(d,v);assert actual==[not(positive or negative)];rows[str((positive,negative))]=actual[0]
        assert v['ztruth'] is unknown and v['h26hl'] is unknown
    distinct={}
    for variant in ('other_source','other_person','other_standing','other_content','other_bindings','other_reference','other_point'):
        v=settings(d);wanted=['alpha','beta','alpha',('r5np',1),('beta','beta','alpha'),'reference','candidate']
        pos,val={'other_source':(0,'beta'),'other_person':(1,'alpha'),'other_standing':(2,'beta'),'other_content':(3,('r5nr',1)),
            'other_bindings':(4,('beta','alpha','alpha')),'other_reference':(5,'assessment'),'other_point':(6,'end')}[variant]
        wanted[pos]=val
        v['h237z']=lambda s,p,role,code,b,r,sign,at:normalized((s,p,role,code,b,r,at))==tuple(wanted)
        assert run(d,v)==[True];distinct[variant]=True
    v=settings(d);v['h237z']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown norms treated as absent')
    return dict(both_polarities_absent=rows,other_normative_targets_not_erased=distinct,positive_permission_not_required=True,quoted_conduct_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def intervention_checks():
    d=fixture('q[k r5nu['+ARGS+' '+B+' '+P+']].');rows={}
    for variant in ('baseline','no_activity','no_participation','no_intervention','other_actor','other_activity','other_person','other_content','other_community','other_undertaking','other_goal','other_role','other_reference','other_point','unknown'):
        v=settings(d);v['dg']=lambda *a:a==('beta','candidate') and variant!='no_activity'
        v['df']=lambda *a:a==('beta' if variant=='other_actor' else 'alpha','beta','candidate') and variant!='no_participation'
        wanted=['beta','beta',('r5nt',1),('beta','alpha','beta','alpha','alpha'),'reference','candidate']
        changes={'other_activity':(0,'alpha'),'other_person':(1,'alpha'),'other_content':(2,('r5nr',1)),
            'other_community':(3,('beta','beta','beta','alpha','alpha')),'other_undertaking':(3,('beta','alpha','alpha','alpha','alpha')),
            'other_goal':(3,('beta','alpha','beta','beta','alpha')),'other_role':(3,('beta','alpha','beta','alpha','beta')),
            'other_reference':(4,'assessment'),'other_point':(5,'end')}
        if variant in changes:i,val=changes[variant];wanted[i]=val
        v['h26ho']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_intervention'
        if variant=='unknown':
            v['h26ho']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown intervention')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['ztruth'] is unknown and v['h26hm'] is unknown
    return dict(same_activity_actor_person_standing_and_content=rows,contents_and_belief_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def leaving_checks():
    d=fixture('q[k r5nv['+ARGS+' '+P+']].');rows={}
    for prescription,intervention in product((False,True),repeat=2):
        v=settings(d);v['h237z']=lambda *a:prescription
        v['dg']=lambda *a:a==('beta','candidate');v['df']=lambda *a:a==('alpha','beta','candidate')
        v['h26ho']=lambda *a:intervention and normalized(a)==('beta','beta',('r5nt',1),('beta','alpha','beta','alpha','alpha'),'reference','candidate')
        actual=run(d,v);assert actual==[not(prescription or intervention)];rows[str((prescription,intervention))]=actual[0]
    v['h237z']=lambda *a:False;v['h26ho']=lambda *a:False;v['h26hk']=lambda *a:False
    assert run(d,v)==[False]
    return dict(native_nonprescription_and_nonintervention=rows,personal_content_required=True,actual_performance_or_salvation_not_required=True,boundaries=[])

@lru_cache(None)
def remit_checks():
    d=fixture('q[k r5nw['+ARGS+' '+P+']].',('r2uj','r2ui'));rows={}
    for variant in ('outside','inside','not_monarch','other_office','other_community','other_content','other_person','other_undertaking','other_goal','other_reference','other_point','unknown'):
        v=settings(d);v['r2uj']=lambda *a:a==('alpha','alpha','candidate') and variant!='not_monarch'
        v['h234f']=lambda *a:a==('beta','alpha','candidate')
        v['r2ui']=lambda *a:a==('alpha','beta','alpha','candidate')
        wanted=['beta','alpha',('r5nr',1),('beta','beta','alpha'),'reference','candidate']
        changes={'other_office':(0,'alpha'),'other_community':(1,'beta'),'other_content':(2,('r5nt',1)),
            'other_person':(3,('alpha','beta','alpha')),'other_undertaking':(3,('beta','alpha','alpha')),'other_goal':(3,('beta','beta','beta')),
            'other_reference':(4,'assessment'),'other_point':(5,'end')}
        if variant in changes:i,val=changes[variant];wanted[i]=val
        v['h26hp']=lambda *a:variant!='outside' and normalized(a)==tuple(wanted)
        if variant=='unknown':
            v['h26hp']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown competence')
            continue
        actual=run(d,v);assert actual==[variant not in ('inside','not_monarch')],(variant,actual);rows[variant]=actual[0]
        assert v['ztruth'] is unknown and v['h237z'] is unknown and v['h26ho'] is unknown
    return dict(same_monarchical_office_and_necessary_means_matter=rows,independent_of_prescription_intervention_or_actual_necessity=True,boundaries=['r2uj','r2ui'],unknown_rejected=True)

@lru_cache(None)
def universal_checks():
    query=''.join('q[t[k '+n+'['+A+' '+B+' '+R+']]['+P+']].' for n in ('r5nx','r5ny'))
    boundaries=('r5ni','r5nk','r5nn','r5nq','r5nv','r5nw');d=fixture(query,boundaries);rows={}
    for variant in ('baseline','second_person_controlled','second_person_inside_remit','belief_withdrawn_later','not_believed','empty_person_scope','invalid_names','invalid_names_without_belief','wrong_target_reference','wrong_target_point','unknown'):
        v=base(d)
        v['r5ni']=lambda actor,p,c,at:(actor,c,at)==('alpha','beta','reference') and variant!='empty_person_scope'
        v['r5nk']=lambda p,u,g,r:(u,g,r)==('alpha','beta','reference')
        v['r5nn']=lambda *a:variant not in ('invalid_names','invalid_names_without_belief')
        calls=[]
        def selected(actor,p,c,u,g,r,at):
            calls.append(at)
            return (actor,c,u,g,r,at)==('alpha','beta','alpha','beta','reference','reference') and variant not in ('not_believed','invalid_names_without_belief')
        v['r5nq']=selected
        def target(actor,p,c,u,g,r,at,kind):
            fixed=(actor,c,u,g,r,at)==('alpha','beta','alpha','beta','assessment' if variant=='wrong_target_reference' else 'reference','end' if variant=='wrong_target_point' else 'candidate')
            missing=kind=='leave' and variant in ('second_person_controlled','belief_withdrawn_later') or kind=='remit' and variant=='second_person_inside_remit'
            return fixed and not(missing and p=='beta')
        v['r5nv']=lambda *a:target(*a,'leave');v['r5nw']=lambda *a:target(*a,'remit')
        if variant=='unknown':
            v['r5nn']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown names accepted')
            continue
        actual=run(d,v)
        expected=[True,True]
        if variant in ('second_person_controlled','belief_withdrawn_later'):expected=[False,True]
        if variant=='second_person_inside_remit':expected=[True,False]
        if variant in ('invalid_names','invalid_names_without_belief','wrong_target_reference','wrong_target_point'):expected=[False,False]
        assert actual==expected,(variant,actual);assert set(calls)<={'reference'};rows[variant]=actual
    return dict(all_candidates_at_fixed_reference=rows,call_boundaries=list(boundaries),later_belief_change_does_not_remove_target=True,names_validated_before_belief_filter=True,unknown_rejected=True)

@lru_cache(None)
def adapter_checks():
    rows={}
    for root,target,length in (('r5nr','r5nl',3),('r5nt','r5np',5),('r5nz','r5nx',2),('r5n2','r5ny',2)):
        d=fixture('q[t[k '+root+'[k zbindings[] '+R+']]['+P+']].',(target,));positions=[]
        for i in range(length):
            b=tuple('beta' if i==j else 'alpha' for j in range(length));v=base(d,b)
            if root=='r5nt':
                v['h26hn']=lambda p,c,r:b[4] if (p,c,r)==(b[0],b[1],'reference') else ('beta' if b[4]=='alpha' else 'alpha')
                v[target]=lambda bindings,r:content({'candidate'}) if normalized((bindings,r))==((b[0],b[2],b[3]),'reference') else content(set())
            else:v[target]=lambda *a:content({'candidate'}) if a==(*b,'reference') else content(set())
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False],(root,i);positions.append(i)
        for size in (length-1,length+1):v['zbindings']=lambda:SequenceValue(('alpha',)*size,'"individual"');assert run(d,v)==[False]
        rows[root]=positions
    source=(ROOT/LIBRARY).read_text(encoding='utf-8')
    for target in ('r5np','r5nt','r5nr'):
        try:parse(source.replace('r b[p '+target+']','r[p '+target+']'))
        except (ValueError,TypeError):pass
        else:raise AssertionError('Rank-zero accepted: '+target)
    return dict(exact_adapters=rows,rank_zero_targets_rejected=True,boundaries=['r5nl','r5np','r5nx','r5ny'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if 'page-490' in p['path']]
    return dict(status='partial_personal_religious_choices_and_monarchical_remit',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3353,3488],text=u['text'][3353:3488]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,primary_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='5–9',observation='本人に委ねる節と君主には関わりがないという節を、その直前の市民的秩序への監督と直後の暴力的妨害防止から分けて構成。個人的な救済判断の所管と公的な秩序の職責を混同しない。')],
        unresolved=['kann/nur/übrigensと監督のWenn条件','暴力的妨害防止を積極的な職責にするwohl aber','同じ救済の決定と全能力での促進','全文の照応・提示・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();sources=parents()
    for n in read(BASIS)['imported_symbols']:
        old=next(s.entries[n] for s in sources if n in s.entries)
        assert c.entries[n]['declaration']==old['declaration'] and c.entries[n]['meaning_ja']==old['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record() and len(sources[1].document['statements'])==106
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=106,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('norms',norm_checks),('intervention',intervention_checks),('leaving',leaving_checks),('remit',remit_checks),('universal',universal_checks),('adapters',adapter_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_personal_religious_remit.py','scripts/check_personal_religious_remit.py','tests/test_personal_religious_remit.py',
        'scripts/check_personal_salvation_judgment.py','scripts/check_civic_compatibility.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/check_persistent_compact_progress.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='personal_religious_nonprescription_nonintervention_and_public_remit',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
