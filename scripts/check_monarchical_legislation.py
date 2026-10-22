"""Check shared prohibitions, complete public will and normative authority grounds."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_monarchical_legislation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import SCENES,DOMAIN,EXTRA

REPORT='reports/monarchical-legislation-v1.json'
READING='data/monarchical-legislation-reading-v1.json'
DOC='docs/monarchical-legislation-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/personal-renunciation-sentence-v1.json','reports/rational-self-imposition-v1.json','reports/law-enactment-v1.json','reports/single-ruler-v1.json','reports/legislative-touchstone-v1.json')
FOUR=' '.join('k zalpha[]' for _ in range(4))
CTX='k zreference[] k zcandidate[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def base(d,bindings=('alpha',)*4):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26b7=lambda:'reference',
        h26cg=lambda:'alpha',h26ch=lambda:'beta',h26cj=lambda:'beta',h26go=lambda:'alpha')
    return v

@lru_cache(None)
def enactment_checks():
    query='q[k r5mb['+FOUR+' '+CTX+']].q[t[k r5mc[k zbindings[] k zreference[]]][k zcandidate[]]].'
    d=fixture(('r5mb','r5mc'),query,('r5ep','r2uj','r5ek'));rows={}
    for variant in ('baseline','not_monarch','different_community','different_actor','split_points','no_adoption','no_candidate','cycle','outside_history','wrong_reference'):
        v=base(d);history=('start','end')
        v['r5ep']=lambda p,c,l,h:(p,c,l,h)==('alpha','alpha','alpha','candidate') and variant!='no_candidate'
        v['r2uj']=lambda a,c,t:(a,c,t)==('beta' if variant=='different_actor' else 'alpha','beta' if variant=='different_community' else 'alpha','start' if variant=='split_points' else 'end') and variant!='not_monarch'
        v['r5ek']=lambda a,p,c,l,act,r,h,t:(a,p,c,l,r,h,t)==('alpha','alpha','alpha','alpha','reference','candidate','end') and variant!='no_adoption'
        v['h257z']=lambda r,h,t:(r,h)==('reference','candidate') and t in history and not(variant=='outside_history' and t=='end')
        v['ic']=lambda a,b,h:h=='candidate' and a in history and b in history and (a!=b if variant=='cycle' else (a,b)==('start','end'))
        if variant=='wrong_reference':v['zreference']=lambda:'assessment'
        actual=run(d,v)
        want=[variant in('baseline','split_points','no_adoption','cycle'),variant in('baseline','no_candidate')]
        # The frame uses the pinned r5ep boundary; its native history check is
        # covered by the parent report. The new enactment checks ta natively.
        assert actual==want,(variant,actual);rows[variant]=actual
    d=fixture(('r5mc',),'q[t[k r5mc[k zbindings[] k zreference[]]][k zcandidate[]]].',('r2uj','r5ek'))
    for i in range(4):
        b=tuple('beta' if i==j else 'alpha' for j in range(4));v=base(d,b)
        v['h257z']=lambda r,c,t:(r,c,t)==('reference','candidate','end');v['ic']=lambda *a:False
        v['r2uj']=lambda a,c,t:(a,c,t)==(b[0],b[2],'end')
        v['r5ek']=lambda a,p,c,l,act,r,h,t:(a,p,c,l,r,h,t)==(*b,'reference','candidate','end')
        assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*4,'"individual"');assert run(d,v)==[False]
    return dict(monarch_and_enactment_same_point=rows,all_four_positions=True,
        boundaries=['r5ep; native frame pinned','r2uj; native institutional monarchy pinned','r5ek; native enactment and full clauses pinned'])

@lru_cache(None)
def prohibition_checks():
    rows={}
    for root,length,target,source,role in (('r5md',3,'r5en','alpha','beta'),('r5me',4,'r5mc','beta','alpha')):
        d=fixture((root,),'q[k '+root+'['+' '.join('k zalpha[]' for _ in range(length))+' '+CTX+']].')
        expected=(source,'alpha',role,(target,1),('alpha',)*length,'reference',False,'candidate');cases={}
        for variant in ('baseline','absent','positive','other_source','other_bearer','other_role','other_conduct','other_bindings','other_reference','other_candidate'):
            v=base(d);wanted=list(expected)
            changes={'positive':(6,True),'other_source':(0,'beta' if source=='alpha' else 'alpha'),'other_bearer':(1,'beta'),
                'other_role':(2,'alpha' if role=='beta' else 'beta'),'other_conduct':(3,('r5ev',1)),
                'other_bindings':(4,('beta',)*length),'other_reference':(5,'assessment'),'other_candidate':(7,'end')}
            if variant in changes:i,value=changes[variant];wanted[i]=value
            v['h237z']=lambda *a:normalized(a)==tuple(wanted) and variant!='absent'
            actual=run(d,v);assert actual==[variant=='baseline'],(root,variant,actual);cases[variant]=actual[0]
        v=base(d);v['h237z']=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError('Unknown prohibition accepted')
        rows[root]=cases
    return dict(explicit_negative_requirements=rows,quoted_adoption_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def limit_checks():
    d=fixture(('r5mg',),'q[t[k r5mg[k zreference[]]][k zouter[]]].',('r5mb',));rows={}
    cases={('alpha','alpha','alpha','alpha','candidate'),('beta','alpha','alpha','alpha','candidate')}
    for variant in ('baseline','missing_second_monarch_ban','no_self_ban','no_bans','empty_scope','different_candidate','different_law'):
        v=base(d);v['r5mb']=lambda a,p,c,l,r,h:r=='reference' and(a,p,c,l,h) in cases and variant!='empty_scope'
        def norm(s,bearer,role,target,b,r,sign,h):
            code=normalized(target);items=normalized(b)
            if(r,sign)!=('reference',False):return False
            if code==('r5en',1):return(s,bearer,role,items,h)==('alpha','alpha','beta',('alpha',)*3,'candidate') and variant not in('no_self_ban','no_bans')
            if code!=('r5mc',1) or(s,role)!=('beta','alpha') or len(items)!=4 or items[0]!=bearer:return False
            wanted=('end' if variant=='different_candidate' else 'candidate')
            return items[1:]==('alpha','alpha','beta' if variant=='different_law' else 'alpha') and h==wanted and variant!='no_bans' and not(variant=='missing_second_monarch_ban' and bearer=='beta')
        v['h237z']=norm
        actual=run(d,v);assert actual==[variant in('baseline','no_self_ban','no_bans','empty_scope')],(variant,actual);rows[variant]=actual[0]
    return dict(all_monarchs_same_people_law_and_candidate=rows,absence_of_ban_not_used_as_ban=True,boundary='r5mb only')

@lru_cache(None)
def will_checks():
    query='q[k r5mi[k zalpha[] k zbeta[] k zalpha[] k zalpha[] k zbeta[] k zreference[]]].'
    d=fixture(('r5mi',),query,('r45d','r5ei','r5es'));rows={}
    for variant in ('baseline','incomplete_people','empty_laws','wrong_public_owner','wrong_own_owner','no_incorporation','reverse_incorporation','public_extra_law','public_missing_law','own_extra_law','own_missing_law','wrong_reference','no_acceptable_law'):
        v=base(d);v['r45d']=lambda p,c,r:(p,c,r)==('beta','alpha','reference') and variant!='incomplete_people'
        v['r5ei']=lambda p,c,l,r:(p,c,r)==('beta','alpha','reference') and l in DOMAIN and variant!='empty_laws'
        v['r5es']=lambda p,c,l:(p,c,l)==('beta','alpha','alpha') and variant!='no_acceptable_law'
        def owner(w,bearer,c,r):
            if(c,r)!=('alpha','reference'):return False
            return(w,bearer)==('beta','alpha' if variant=='wrong_public_owner' else 'beta') or (w,bearer)==('alpha','beta' if variant=='wrong_own_owner' else 'alpha')
        v['h26gp']=owner
        v['h26gr']=lambda own,public,r:(own,public,r)==(('beta','alpha','reference') if variant=='reverse_incorporation' else ('alpha','beta','reference')) and variant!='no_incorporation'
        def accepts(w,l,r):
            if r!='reference' or w not in DOMAIN or l not in DOMAIN:return False
            if variant=='no_acceptable_law':return False
            if(w,l)==('beta','beta') and variant=='public_extra_law':return True
            if(w,l)==('beta','alpha') and variant=='public_missing_law':return False
            if(w,l)==('alpha','beta') and variant=='own_extra_law':return True
            if(w,l)==('alpha','alpha') and variant=='own_missing_law':return False
            return l=='alpha'
        v['h26gq']=accepts
        if variant=='wrong_reference':v['zreference']=lambda:'assessment'
        actual=run(d,v);assert actual==[variant in('baseline','no_acceptable_law')],(variant,actual);rows[variant]=actual[0]
    v['zreference']=lambda:'reference';v['h26gq']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown will content accepted')
    return dict(native_complete_public_range_and_structural_incorporation=rows,unknown_rejected=True,
        boundaries=['r45d complete people; pinned','r5ei complete law scope; pinned','r5es rational possibility; pinned'],
        no_unanimous_vote_or_simultaneous_enactment_required=True)

@lru_cache(None)
def ground_checks():
    d=fixture(('r5ml',),'q[t[k r5ml[k zbindings[] k zreference[]]][k zcandidate[]]].');rows={}
    expected=(('r5mj',1),('alpha',)*3,('r5mk',1),('alpha',)*3,'reference','candidate')
    for variant in ('baseline','absent','other_ground','other_ground_bindings','other_standing','other_standing_bindings','other_reference','other_candidate'):
        v=base(d,('alpha',)*3);wanted=list(expected)
        changes={'other_ground':(0,('r5mk',1)),'other_ground_bindings':(1,('beta',)*3),'other_standing':(2,('r5mj',1)),
            'other_standing_bindings':(3,('beta',)*3),'other_reference':(4,'assessment'),'other_candidate':(5,'end')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26gt']=lambda *a:normalized(a)==tuple(wanted) and variant!='absent'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['h26gp'] is unknown and v['h26gs'] is unknown
    # The will content evaluates rank-zero clause descriptions through r5es;
    # grounding therefore needs rank-one quotations, not rank zero.
    malformed=format_graph(d,'compact').replace('r b[p r5mj]','r[p r5mj]')
    try:parse(malformed)
    except ValueError:pass
    else:raise AssertionError('Lower-rank grounding accepted')
    return dict(same_ground_and_standing_quoted_at_required_rank=rows,ground_and_authority_not_executed=True,lower_rank_rejected=True)

@lru_cache(None)
def standing_checks():
    query='q[k r5mm[k zalpha[] k zbeta[] k zalpha[] '+CTX+']].q[t[k r5mk[k zbindings[] k zreference[]]][k zcandidate[]]].'
    d=fixture(('r5mm','r5mk'),query,('r45d','r2uj'));rows={}
    for variant in ('baseline','incomplete_people','not_monarch','other_community','outside_history','cycle','no_authority','other_authority_actor','other_authority_role','other_authority_candidate','wrong_reference'):
        v=base(d,('alpha','beta','alpha'));history=('start','end')
        v['r45d']=lambda p,c,r:(p,c,r)==('beta','alpha','reference') and variant!='incomplete_people'
        v['r2uj']=lambda a,c,t:(a,c,t)==('alpha','beta' if variant=='other_community' else 'alpha','end') and variant!='not_monarch'
        v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in history and not(variant=='outside_history' and t=='end')
        v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and (a!=b if variant=='cycle' else (a,b)==('start','end'))
        expected=('beta' if variant=='other_authority_actor' else 'alpha','alpha','beta' if variant=='other_authority_role' else 'alpha','reference','end' if variant=='other_authority_candidate' else 'candidate')
        v['h26gs']=lambda *a:a==expected and variant!='no_authority'
        if variant=='wrong_reference':v['zreference']=lambda:'assessment'
        actual=run(d,v)
        want=[variant not in('incomplete_people','not_monarch','other_community','outside_history','cycle','wrong_reference'),
            variant not in('incomplete_people','no_authority','other_authority_actor','other_authority_role','other_authority_candidate','wrong_reference')]
        assert actual==want,(variant,actual);rows[variant]=actual
    d=fixture(('r5mj',),'q[t[k r5mj[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5mi',))
    for i in range(3):
        b=tuple('beta' if i==j else 'alpha' for j in range(3));v=base(d,b)
        v['r5mi']=lambda a,p,c,own,public,r:(a,p,c,own,public,r)==(*b,'alpha','beta','reference')
        assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*3,'"individual"');assert run(d,v)==[False]
    for length in (2,4):
        v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
    return dict(native_scope_and_separate_authority_content=rows,existential_incorporation_keeps_all_three_bindings=True,
        boundaries=['r45d complete people','r2uj institutional monarchy','r5mi only for existential adapter'])

@lru_cache(None)
def foundation_checks():
    d=fixture(('r5mn',),'q[t[k r5mn[k zreference[]]][k zouter[]]].',('r5mm','r5mj','r5mk'));rows={}
    for variant in ('baseline','authority_without_incorporation','incorporation_without_authority','neither_actual','missing_ground','wrong_ground_candidate'):
        v=base(d);v['r5mm']=lambda a,p,c,r,h:(a,p,c,r,h)==('alpha','beta','alpha','reference','candidate')
        v['r5mj']=lambda b,r:content({'candidate'}) if(normalized(b),r)==(('alpha','beta','alpha'),'reference') and variant not in('authority_without_incorporation','neither_actual') else content(set())
        v['r5mk']=lambda b,r:content({'candidate'}) if(normalized(b),r)==(('alpha','beta','alpha'),'reference') and variant not in('incorporation_without_authority','neither_actual') else content(set())
        expected=(('r5mj',1),('alpha','beta','alpha'),('r5mk',1),('alpha','beta','alpha'),'reference','end' if variant=='wrong_ground_candidate' else 'candidate')
        v['h26gt']=lambda *a:normalized(a)==expected and variant!='missing_ground'
        actual=run(d,v);assert actual==[variant in('baseline','incorporation_without_authority','neither_actual')],(variant,actual);rows[variant]=actual[0]
    d=fixture(('r5mo',),'q[t[k r5mo[]][k zcandidate[]]].',('r5mg','r5mn'));combined={}
    for limits,grounds in product((False,True),repeat=2):
        v=base(d);v['r5mg']=lambda r:content({'candidate'}) if r=='reference' and limits else content(set())
        v['r5mn']=lambda r:content({'candidate'}) if r=='reference' and grounds else content(set())
        actual=run(d,v);assert actual==[limits and grounds];combined[str((limits,grounds))]=actual[0]
    return dict(grounding_and_necessary_but_not_sufficient_incorporation=rows,both_halves=combined,
        boundaries=['r5mm scope','r5mj incorporation','r5mk authority','r5mg/r5mn only in conjunction test'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if 'page-490' in p['path']]
    return dict(status='partial_monarchical_legislative_limits_and_authority_ground',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[2986,3225],text=u['text'][2986:3225]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,primary_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/039.html',lines='37',observation='人民自身の決定への否認を確認。'),dict(url='https://korpora.org/kant/aa08/040.html',lines='1–3',observation='同じ人民への君主の決定、立法上の権威、全人民意志を自身の意志に統合する説明を確認。')],
        unresolved=['nicht einmal/noch wenigerの比較','aber、denn、ebenの提示','全文への帰属と通読'],
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
    assert read(READING)==reading_record() and len(old.document['statements'])==105
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=105,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('enactment',enactment_checks),('prohibition',prohibition_checks),('limits',limit_checks),('will',will_checks),('ground',ground_checks),('standing',standing_checks),('foundation',foundation_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_monarchical_legislation.py','scripts/check_monarchical_legislation.py','tests/test_monarchical_legislation.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='same_legislative_limits_and_complete_public_will_as_authority_ground',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
