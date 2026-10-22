"""Check causal identity and a prohibition whose scope does not depend on harm."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_compact_causal_denial import ROOT,LIBRARY,BASIS,MEANINGS,LIMITS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import base as period_base,SCENES,DOMAIN,EXTRA

REPORT='reports/compact-causal-denial-v1.json'
READING='data/compact-causal-denial-reading-v1.json'
DOC='docs/compact-causal-denial-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/persistent-compact-progress-v1.json','reports/fixed-religious-compact-v1.json','reports/cohort-covenant-purpose-v1.json','reports/guardian-irrationality-v1.json','reports/provisional-order-sentence-v1.json')
FIVE=' '.join('k zalpha[]' for _ in NAMES)
SIX='k zalpha[] '+FIVE
CONTEXT='k zreference[] k zcandidate[]'

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
def content(value):return Content(SCENES,tuple(value and s=='candidate' for s in SCENES))
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(('alpha',)*5,'"individual"')
    v['h254z']=lambda a:'start';v['h26ar']=lambda r:'assessment'
    return v

@lru_cache(None)
def causal_checks():
    d=fixture(('r5jp',),'q[k r5jp['+FIVE+' '+CONTEXT+']].',('r5jh','r5jg','r5jm'));rows={}
    for variant in ('baseline','no_formation','no_implementation','no_result','no_cause','other_agreement','other_result','other_bindings','other_reference','other_candidate','wrong_assessment','wrong_anchor'):
        v=base(d)
        v['r5jh']=lambda *a:a==(*('alpha',)*5,'reference','candidate','start') and variant!='no_formation'
        v['r5jg']=lambda b,r,c,s:content(normalized(b)==('alpha',)*4 and(r,c,s)==('reference','candidate','start') and variant!='no_implementation')
        v['r5jm']=lambda p,r,a,c:(p,r,a,c)==('alpha','reference','assessment','candidate') and variant!='no_result'
        expected=['alpha',('r5jo',0),('alpha',)*5,'reference','candidate']
        changes={'other_agreement':(0,'beta'),'other_result':(1,('r5jn',0)),'other_bindings':(2,('alpha',)*4+('beta',)),
            'other_reference':(3,'assessment'),'other_candidate':(4,'after')}
        if variant in changes:i,value=changes[variant];expected[i]=value
        v['h26as']=lambda *a:normalized(a)==tuple(expected) and variant!='no_cause'
        if variant=='wrong_assessment':v['h26ar']=lambda r:'reference'
        if variant=='wrong_anchor':v['h254z']=lambda a:'middle'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v=base(d);v['r5jh']=lambda *a:True;v['r5jg']=lambda *a:content(True);v['r5jm']=lambda *a:True;v['h26as']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Coexistence accepted without known cause')
    return dict(same_formation_implementation_result_and_actual_cause=rows,unknown_cause_rejected=True,
        boundaries=['r5jh','r5jg','r5jm; native constructions preserved in prior evidence'])

@lru_cache(None)
def adapter_checks():
    rows={}
    for root,boundary in (('r5jn','r5jh'),('r5jo','r5jm'),('r5jq','r5jp'),('r5jx','r5jh')):
        boundaries=(boundary,'r5jg') if root=='r5jx' else(boundary,)
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',boundaries);positions=[]
        for i in range(5):
            five=tuple('beta' if j==i else 'alpha' for j in range(5));v=base(d);v['zbindings']=lambda:SequenceValue(five,'"individual"')
            if root in ('r5jn','r5jx'):v['r5jh']=lambda *a:a==(*five,'reference','candidate','start')
            elif root=='r5jo':v['r5jm']=lambda *a:a==(five[4],'reference','assessment','candidate')
            else:v['r5jp']=lambda *a:a==(*five,'reference','candidate')
            if root=='r5jx':v['r5jg']=lambda b,r,c,s:content(normalized(b)==five[1:] and(r,c,s)==('reference','candidate','start'))
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*5,'"individual"')
            assert run(d,v)==[root=='r5jo' and i!=4],(root,i)
            positions.append(i)
        for n in (4,6):
            v['zbindings']=lambda n=n:SequenceValue(('alpha',)*n,'"individual"');assert run(d,v)==[False]
        rows[root]=positions
    return dict(exact_five_objects_and_fixed_context=rows,result_only_depends_on_period_but_preserves_full_binding=True,
        boundaries=['r5jh','r5jg','r5jm','r5jp; adapter tests only'])

@lru_cache(None)
def consequence_checks():
    d=fixture(('r5jr',),'q[k r5jr['+FIVE+' '+CONTEXT+']].');rows={}
    for variant in ('baseline','no_consequence','formation_only','different_result','different_cause_binding','different_result_binding','different_reference','different_point'):
        v=base(d);expected=[('r5jx',2),('alpha',)*5,('r5jo',2),('alpha',)*5,'reference','candidate']
        changes={'formation_only':(0,('r5jn',2)),'different_result':(2,('r5jq',2)),
            'different_cause_binding':(1,('beta',)*5),'different_result_binding':(3,('beta',)*5),'different_reference':(4,'assessment'),'different_point':(5,'start')}
        if variant in changes:i,value=changes[variant];expected[i]=value
        v['h253x']=lambda *a:normalized(a)==tuple(expected) and variant!='no_consequence'
        v['h254z']=unknown;v['h26ar']=unknown
        actual=run(d,v);assert actual==[variant=='baseline'];rows[variant]=actual[0]
        assert v['h26as'] is unknown if 'h26as' in v else True
    return dict(quoted_conditional_consequence=rows,formation_implementation_and_result_not_executed=True)

@lru_cache(None)
def scope_checks():
    d=fixture(('r5js',),'q[k r5js['+SIX+' '+CONTEXT+']].');rows={}
    for variant in ('baseline','one_party','nonhuman_party','missing_member','extra_member','no_agreement_kind','invalid_period','late_anchor','different_group','different_candidate'):
        v=period_base(d,'gap' if variant=='invalid_period' else 'baseline');v['h254z']=lambda a:'middle' if variant=='late_anchor' else 'start'
        v['h26aw']=lambda a,r:(a,r)==('alpha','reference') and variant!='no_agreement_kind'
        v['aa']=lambda p:p=='alpha' or variant!='nonhuman_party'
        members=('alpha',) if variant in ('one_party','extra_member') else DOMAIN
        v['h26dj']=lambda a,p,r,c,s:(a,r,c,s)==('alpha','reference','candidate','start') and p in members
        v['h246c']=lambda g,p,s:(g,s)==('beta' if variant=='different_group' else 'alpha','start') and(p=='alpha' or variant!='missing_member')
        if variant=='different_candidate':v['zcandidate']=lambda:'after'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v.get('dg',unknown) is unknown and v.get('h26as',unknown) is unknown
    return dict(unformed_candidate_complete_party_group_and_valid_period=rows,native_scope_and_period=True,no_success_selection=True)

@lru_cache(None)
def normative_checks():
    q='q[t[k r5jv[k zalpha[] k zbeta[] k zreference[]]][k zcandidate[]]].q[t[k r5jw[k zreference[]]][k zcandidate[]]].'
    d=fixture(('r5jv','r5jw'),q,('r5js',));rows={}
    first=('alpha',)*6;second=('beta',*('alpha',)*4,'beta')
    for variant in ('baseline','missing_second_ban','missing_consequence','no_bans','empty_scope','opposite_polarity','different_target','different_binding','different_source','different_role'):
        v=base(d)
        v['r5js']=lambda *a:a[:-2] in (() if variant=='empty_scope' else (first,second)) and a[-2:]==('reference','candidate')
        def ban(source,group,role,target,b,r,sign,point):
            six=normalized(b)
            return source==('beta' if variant=='different_source' else 'alpha') and role==('alpha' if variant=='different_role' else 'beta') and normalized(target)==('r5jq' if variant=='different_target' else 'r5jt',1) and six in(first,second) and group==six[0] and(r,point)==('reference','candidate') and sign==(variant=='opposite_polarity') and variant not in ('no_bans','different_binding') and not(variant=='missing_second_ban' and six==second)
        v['h237z']=ban
        v['h253x']=lambda cause,cb,result,rb,r,t:normalized((cause,result,r,t))==(('r5jx',2),('r5jo',2),'reference','candidate') and normalized(cb)==normalized(rb) and variant!='missing_consequence'
        v['h254z']=unknown;v['h26ar']=unknown
        actual=run(d,v);expected=[variant in ('baseline','missing_consequence','empty_scope'),variant!='missing_consequence']
        assert actual==expected,(variant,actual);rows[variant]=actual
    # Neither the world's formation nor its effect needs a truth interpretation here.
    return dict(universal_prohibition_and_causal_consequence_independent=rows,
        harmful_success_not_a_condition_of_prohibition=True,empty_scope_does_not_assert_agreement_existence=True,
        boundary='r5js only for universal six-object scope; native scope checked separately')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='partial_causal_and_normative_dependency',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[2310,2677],text=u['text'][2310:2677]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        unresolved=['後世への害の対象範囲・内容・様相と第二のdadurch','期間の消去への見立て','評価規範・立場の固定、全面性・auch nur・Aberの提示と全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();sources=parents();old={n:e for s in sources for n,e in s.entries.items()}
    for n in read(BASIS)['imported_symbols']:
        assert c.entries[n]['declaration']==old[n]['declaration'] and c.entries[n]['meaning_ja']==old[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record()
    assert len(sources[1].document['statements'])==103
    return dict(new_definitions=len(MEANINGS),new_primitives=0,roundtrips=True,preserved_main_statements=103,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('causal',causal_checks),('adapters',adapter_checks),('consequence',consequence_checks),('scope',scope_checks),('normative',normative_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,
        'scripts/compose_compact_causal_denial.py','scripts/check_compact_causal_denial.py','tests/test_compact_causal_denial.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='same_compact_causal_result_and_unconditional_formation_prohibition',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
