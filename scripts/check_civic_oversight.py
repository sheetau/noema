"""Check realized change, all-case civil conditions and effective oversight."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_oversight import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build
from scripts.check_civic_compatibility import PROVIDERS,base,run,content,SCENES,DOMAIN,EXTRA
from scripts.check_covenant_nullity import normalized
from scripts.check_motive_causes import unknown

DOC='docs/civic-oversight-v1.md'
READING='data/civic-oversight-reading-v1.json'
REPORT='reports/civic-oversight-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/civic-compatibility-v1.json','reports/monarchical-sentence-v1.json','reports/single-ruler-v1.json')
A='k zalpha[]';B='k zbeta[]';R='k zreference[]';P='k zcandidate[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[];seen={x['name'] for x in d['declarations']}
    # Retain the previous universal compatibility claim only for the explicit
    # counterexample. It is not a dependency of the new oversight definition.
    d['declarations'] += [deepcopy(x) for x in parents()[0].document['declarations'] if x['name'] not in seen]
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    prefix=parse('p:'+EXTRA+PROVIDERS)
    providers={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in providers]+[providers.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)

@lru_cache(None)
def realization_checks():
    args=' '.join((A,A,A,A,B,A,R,P));d=fixture('q[k r5nc['+args+']].',('r5mw',));rows={}
    for variant in ('baseline','no_frame','no_activity','no_effect','no_realization','other_activity','other_change','other_community','other_reference','other_point','other_content','unknown'):
        v=base(d);v['r5mw']=lambda *a:a==('alpha','alpha','alpha','alpha','beta','alpha','reference') and variant!='no_frame'
        v['dg']=lambda act,p:(act,p)==('alpha' if variant=='other_activity' else 'beta','candidate') and variant!='no_activity'
        wanted=['beta','alpha','alpha','reference','candidate']
        changes={'other_change':(1,'beta'),'other_community':(2,'beta'),'other_reference':(3,'assessment'),'other_point':(4,'end')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26he']=lambda *a:a==tuple(wanted) and variant!='no_effect'
        v['ztruth']=lambda obj,p:(obj,p)==('alpha' if variant=='other_content' else 'beta','candidate') and variant!='no_realization'
        if variant=='unknown':
            v['h26he']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown implementation')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(same_change_activity_community_content_and_point=rows,boundary='r5mw: pinned complete candidate frame',unknown_rejected=True)

@lru_cache(None)
def universal_checks():
    query='q[t[k r5nd['+A+' '+B+' '+R+']][k zcandidate[]]].'
    boundaries=('r5mw','r5m2','r5m4','r5nc','r5m5','r5m6','r5m7')
    d=fixture(query,boundaries);rows={}
    def model(doc,qualifies=True,implemented=True,order=True,invalid=False):
        v=base(doc)
        v['r5mw']=lambda ch,f,c,o,n,s,r:(f,c,o,n,s,r)==('alpha','alpha','alpha','beta','alpha','reference')
        v['r5m2']=lambda *a:a==('alpha','beta','alpha','alpha','reference') and not invalid
        v['r5m4']=lambda ch,f,c,o,n,s,r,p:qualifies and (f,c,o,n,s,r,p)==('alpha','alpha','alpha','beta','alpha','reference','candidate')
        v['r5nc']=lambda ch,f,c,o,n,s,r,p:implemented and (f,c,o,n,s,r,p)==('alpha','alpha','alpha','beta','alpha','reference','candidate')
        v['r5m5']=lambda *a:a==('beta','alpha','reference')
        v['r5m6']=lambda *a:order and a==('beta','alpha','reference','candidate')
        return v
    for q,i,o in product((False,True),repeat=3):
        v=model(d,q,i,o);actual=run(d,v);assert actual==[not(q and i) or o];rows[str((q,i,o))]=actual[0]
    for variant in ('additional_implemented_change','invalid_names_even_unimplemented','wrong_order','wrong_community','wrong_reference','wrong_point'):
        v=model(d,True,False,False)
        if variant=='additional_implemented_change':v['r5nc']=lambda ch,*a:ch=='beta' and a==('alpha','alpha','alpha','beta','alpha','reference','candidate')
        elif variant=='invalid_names_even_unimplemented':v['r5m2']=lambda *a:False
        else:
            v=model(d,True,True,True);wanted=['beta','alpha','reference','candidate']
            position={'wrong_order':0,'wrong_community':1,'wrong_reference':2,'wrong_point':3}[variant]
            wanted[position]=('alpha','beta','assessment','end')[position]
            v['r5m6']=lambda *a:a==tuple(wanted)
        assert run(d,v)==[False],variant;rows[variant]=False
    # An incompatible proposed improvement may remain unimplemented: the old
    # universal possibility requirement fails, but actual implementation safety holds.
    d=fixture(query+'q[t[k r5nb['+A+' '+B+' '+R+']][k zcandidate[]]].',boundaries)
    v=model(d,True,False,True);v['r5m7']=lambda *a:False
    actual=run(d,v);assert actual==[True,False]
    return dict(all_qualified_implemented_changes_preserve_order=rows,unimplemented_incompatible_proposal_new_then_old=actual,
        boundaries=list(boundaries),all_proposals_need_not_be_implementable=True)

@lru_cache(None)
def oversight_checks():
    args=' '.join((A,B,A,B,R,P))
    d=fixture('q[k r5nf['+args+']].q[k r5ng['+args+']].',('r2uj','r5nd'));rows={}
    for variant in ('baseline','no_monarch','no_activity','no_participation','no_goal','no_attention','no_effect','no_result',
                    'other_actor','other_activity','other_community','other_order','other_reference','other_point','other_aspect','other_goal','unknown'):
        v=base(d);v['r2uj']=lambda *a:a==('alpha','alpha','candidate') and variant!='no_monarch'
        v['dg']=lambda *a:a==('beta','candidate') and variant!='no_activity'
        v['df']=lambda *a:a==('alpha','beta','candidate') and variant!='no_participation'
        code=('r5ne',1);bindings=('alpha','beta')
        goal=['alpha','beta',code,bindings,'reference','candidate']
        changes={'other_actor':(0,'beta'),'other_activity':(1,'alpha'),'other_community':(3,('beta','beta')),
            'other_order':(3,('alpha','alpha')),'other_reference':(4,'assessment'),'other_point':(5,'end'),'other_goal':(2,('r5my',1))}
        if variant in changes:i,value=changes[variant];goal[i]=value
        v['h26hf']=lambda *a:normalized(a)==tuple(goal) and variant!='no_goal'
        attention=('alpha','beta',code,bindings,'alpha' if variant=='other_aspect' else 'beta','reference','candidate')
        v['h26hg']=lambda *a:normalized(a)==attention and variant!='no_attention'
        v['h26hh']=lambda *a:normalized(a)==('beta',code,bindings,'reference','candidate') and variant!='no_effect'
        v['r5nd']=lambda c,o,r:content({'candidate'}) if (c,o,r)==('alpha','beta','reference') and variant!='no_result' else content(set())
        if variant=='unknown':
            v['h26hg']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown attention')
            continue
        actual=run(d,v);expected=[variant in ('baseline','no_effect','no_result'),variant=='baseline']
        assert actual==expected,(variant,actual);rows[variant]=actual
        assert v['h26he'] is unknown and v['h26ha'] is unknown and v['h233c'] is unknown
    malformed=(ROOT/LIBRARY).read_text(encoding='utf-8').replace('r b[p r5ne]','r[p r5ne]')
    try:parse(malformed)
    except (ValueError,TypeError):pass
    else:raise AssertionError('Rank-zero target accepted')
    return dict(same_monarch_action_goal_attention_causal_contribution_and_result=rows,boundaries=['r2uj native office pinned','r5nd target separately checked'],
        quoted_goal_not_executed_by_goal_or_attention=True,rank_zero_target_rejected=True)

@lru_cache(None)
def adapter_checks():
    rows={}
    for root,target,length in (('r5ne','r5nd',2),('r5nh','r5ng',3)):
        d=fixture('q[t[k '+root+'[k zbindings[] '+R+']][k zcandidate[]]].',(target,));positions=[]
        for i in range(length):
            b=tuple('beta' if j==i else 'alpha' for j in range(length));v=base(d,b)
            if root=='r5ne':v[target]=lambda *a:content({'candidate'}) if a==(*b,'reference') else content(set())
            else:v[target]=lambda actor,activity,c,o,r,p:(actor,c,o,r,p)==(*b,'reference','candidate') and activity=='beta'
            assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False];positions.append(i)
        for size in (length-1,length+1):v['zbindings']=lambda:SequenceValue(('alpha',)*size,'"individual"');assert run(d,v)==[False]
        rows[root]=positions
    return dict(exact_goal_and_actor_bindings=rows,boundaries=['r5nd','r5ng'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if 'page-490' in p['path']]
    return dict(status='partial_active_oversight_of_implemented_improvement',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3226,3341],text=u['text'][3226:3341]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,primary_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='3–5',observation='同じ君主が改善と市民的秩序の両立に配慮する節。前回の全案の可能性と、実施における秩序の確保を区別して接続。')],
        unresolved=['Wenn/nurの限定と後半への条件接続','同じ臣民の救済目的・必要性の自己判断','委ねる範囲と職責・暴力的妨害防止','全文の照応・提示・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();sources=parents()
    for n in read(BASIS)['imported_symbols']:
        e=next(s.entries[n] for s in sources if n in s.entries)
        assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record() and len(sources[1].document['statements'])==106
    assert 'r5nb' not in c.entries
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=106,semantic_review_characters_added=0,
        previous_all_proposals_possible_claim_not_used=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('realization',realization_checks),('universal',universal_checks),('oversight',oversight_checks),('adapters',adapter_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_civic_oversight.py','scripts/check_civic_oversight.py','tests/test_civic_oversight.py','scripts/check_civic_compatibility.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='same_monarch_active_oversight_and_civil_order_of_implemented_improvements',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
