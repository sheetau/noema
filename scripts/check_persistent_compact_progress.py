"""Check whole interval scopes, unexecuted general compacts and all-pairs progress."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_persistent_compact_progress import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

REPORT='reports/persistent-compact-progress-v1.json'
READING='data/persistent-compact-progress-reading-v1.json'
DOC='docs/persistent-compact-progress-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/fixed-religious-compact-v1.json','reports/provisional-order-sentence-v1.json','reports/cognitive-acquisition-v1.json','reports/human-enlightenment-block-v1.json','reports/cohort-covenant-denial-v1.json')
SCENES=('reference','assessment','candidate','before','start','middle','end','after','outer')
POINTS=('before','start','middle','end','after')
DOMAIN=('alpha','beta')
EXTRA='r zalpha[] a.r zbeta[] a.r zbindings[] j[a].'+''.join('r z'+n+'[] d.' for n in SCENES)
CONTEXT='k zreference[] k zcandidate[] k zstart[]'
PERIOD='k zalpha[] k zreference[] k zcandidate[]'

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
def base(d,variant='baseline',bindings=('alpha',)*4):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    community,regime,audience,period=bindings
    v['aa']=lambda p:p=='beta'
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in POINTS
    v['ic']=lambda a,b,c:c=='candidate' and a in POINTS and b in POINTS and(POINTS.index(a)<POINTS.index(b) or(variant=='cycle' and(a,b)==('middle','start')))
    v['h26ex']=lambda p,r,c,s,e:(p,r,c,s,e)==(period,'reference','candidate','start','end') and variant!='no_end_specification'
    selected=() if variant=='empty' else ('start','end') if variant=='gap' else ('start','middle','end') if variant=='closed_period' else ('before','start','middle') if variant=='earlier' else ('start',) if variant=='cut_short' else ('start','middle','end','after') if variant=='tail' else ('start','middle')
    v['h26e3']=lambda p,r,c,t:(p,r,c)==(period,'reference','candidate') and t in selected
    v['ib']=lambda p,c,t:(p,c)==('beta','candidate') and t in POINTS and not(variant=='short_life' and t in ('end','after'))
    v['h26cs']=lambda g,c,r:(g,c,r)==(regime,community,'reference')
    v['ce']=lambda a,r:(a,r)==(audience,'reference')
    v['h26cv']=lambda g,c,r,h,t:(g,c,r,h)==(regime,community,'reference','candidate') and t in ('start','middle') and not(variant=='missing_state' and t=='middle')
    v['cc']=lambda a,u,r:(u,r)==(audience,'reference')
    v['h26ey']=lambda a,g,c,r:(g,c,r)==(regime,community,'reference')
    v['h26ez']=lambda *args:'alpha';v['h26e2']=lambda:'alpha'
    v['h7k']=lambda source,p,role,target,b,polarity,t:normalized((source,p,role,target))==('alpha','beta','alpha',('r5h4',0)) and normalized(b) in tuple(('beta',a,regime,community,audience) for a in DOMAIN) and polarity is False and t in ('start','middle') and not(variant=='missing_prohibition' and t=='middle')
    return v

@lru_cache(None)
def scope_checks():
    q='q[k r5jd['+PERIOD+' k zstart[] k zend[]]].q[k r5je['+PERIOD+' k zstart[]]].q[k r5jf['+PERIOD+' k zstart[]]].q[k r5ji[k zbeta[] '+PERIOD+' k zstart[] k zend[]]].'
    d=fixture(('r5jd','r5je','r5jf','r5ji'),q);rows={}
    for variant in ('baseline','empty','gap','closed_period','earlier','cut_short','tail','cycle','no_end_specification','short_life'):
        actual=run(d,base(d,variant));ok=variant in ('baseline','short_life');expected=[ok,False,ok,variant=='baseline']
        assert actual==expected,(variant,actual);rows[variant]=actual
    v=base(d);v['h26e3']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown interval accepted')
    return dict(exact_bounded_scope_and_lifetime=rows,native_ta_tb_rbz_and_old_period=True,finite_tail_never_proves_unending=True,unknown_rejected=True)

@lru_cache(None)
def unending_wiring_checks():
    # This boundary checks the connection, not an infinite model in the finite evaluator.
    d=fixture(('r5je',),'q[k r5je['+PERIOD+' k zstart[]]].',('rbz',));rows={}
    for variant in ('baseline','missing_tail_point','bounded_end','no_unending','wrong_start'):
        v=base(d,'tail');v['h26ex']=lambda *args:variant=='bounded_end' and args==('alpha','reference','candidate','start','end')
        v['rbz']=lambda history,order,start:variant!='no_unending' and start=='start'
        if variant=='missing_tail_point':v['h26e3']=lambda p,r,c,t:(p,r,c)==('alpha','reference','candidate') and t in ('start','middle','end')
        if variant=='wrong_start':v['zstart']=lambda:'middle'
        actual=run(d,v);assert actual==[variant=='baseline'];rows[variant]=actual[0]
    return dict(unending_boundary_connection=rows,boundary='rbz only; finite native rejection checked separately',
        infinite_satisfiability_argument='Natural-number history, usual strict order, period n >= start, no finite endpoint: each n has n+1. This is a mathematical model argument, not finite execution or automatic translation proof.')

@lru_cache(None)
def terms_checks():
    q='q[t[k r5jg[k zbindings[] '+CONTEXT+']][k zouter[]]].q[e[k r5jg[k zbindings[] '+CONTEXT+']][k r5h6[k zbindings[] '+CONTEXT+']]].'
    d=fixture(('r5jg','r5h6'),q);rows={}
    for variant in ('baseline','missing_state','missing_prohibition','closed_period','cut_short','late_anchor'):
        v=base(d,variant)
        if variant=='late_anchor':v['zstart']=lambda:'middle'
        expected=[variant=='baseline',variant not in ('closed_period','cut_short')]
        actual=run(d,v);assert actual==expected,(variant,actual);rows[variant]=actual
    for pos in range(4):
        b=tuple('beta' if j==pos else 'alpha' for j in range(4));v=base(d,bindings=b)
        assert run(d,v)==[True,True]
        v['zbindings']=lambda:SequenceValue(('alpha',)*4,'"individual"');assert run(d,v)[0] is False
    return dict(native_general_terms_and_bounded_content_equality=rows,all_four_binding_positions=True,
        equality_requires_explicit_period_correspondence=True,quoted_descriptions_not_identified=True)

@lru_cache(None)
def agreement_checks():
    q='q[k r5jh[k zalpha[] k zalpha[] k zalpha[] k zalpha[] k zalpha[] '+CONTEXT+']].'
    d=fixture(('r5jh',),q);rows={}
    for variant in ('baseline','one_party','missing_assent','old_content','wrong_bindings','wrong_candidate','late_assent'):
        v=base(d);v['aa']=lambda p:True
        expected_target=('r5h6' if variant=='old_content' else 'r5jg',0)
        binding=('alpha','alpha','alpha','beta') if variant=='wrong_bindings' else ('alpha',)*4
        c='reference' if variant=='wrong_candidate' else 'candidate'
        v['h26dk']=lambda a,t,b,r,h,s:normalized((a,t,b,r,h,s))==('alpha',expected_target,binding,'reference',c,'start')
        v['h26dj']=lambda a,p,r,h,s:(a,r,h,s)==('alpha','reference','candidate','start') and(p=='alpha' or variant!='one_party')
        v['dg']=lambda a,t:t in ('before','start','middle')
        v['f3']=lambda p,a,t:p==a
        v['h26dl']=lambda p,a,g,t,b,r,h,s,at:normalized((g,t,b,r,h,s))==('alpha',expected_target,binding,'reference',c,'start') and p==a and at==('middle' if variant=='late_assent' else 'before') and not(variant=='missing_assent' and p=='beta')
        for n in ('h26e3','h26ex','h26cv','h7k'):v[n]=unknown
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(general_compact_same_parties_content_and_context=rows,quoted_finite_or_infinite_world_not_executed=True,native_agreement=True)

@lru_cache(None)
def progress_checks():
    q='q[k r5jl[k zalpha[] k zreference[] k zassessment[] k zcandidate[] k zstart[] k zend[]]].q[k r5jm[k zalpha[] k zreference[] k zassessment[] k zcandidate[]]].'
    d=fixture(('r5jl','r5jm'),q,('r5cs','r5cq'));rows={}
    for variant in ('baseline','endpoint_gain','middle_gain_then_loss','outside_gain','missing_evaluation','extinction','partial_humanity','nonhuman_member','wrong_assessment','wrong_reference','wrong_candidate','broken_period'):
        v=base(d,'gap' if variant=='broken_period' else 'baseline');v['h256m']=lambda:'alpha'
        v['aa']=lambda p:p=='beta'
        v['h246c']=lambda g,p,c:(g,c)==('alpha','candidate') and (p=='beta' and variant!='partial_humanity' or p=='alpha' and variant=='nonhuman_member')
        v['r5cq']=lambda g,r,c,t:(g,r,c)==('alpha','reference','candidate') and not(variant in ('missing_evaluation','extinction') and t=='middle')
        pair=('start','end') if variant in ('endpoint_gain','wrong_assessment','wrong_reference','wrong_candidate') else ('start','middle') if variant=='middle_gain_then_loss' else ('end','after') if variant=='outside_gain' else None
        v['r5cs']=lambda g,r,a,c,f,l:(g,r,a,c)==('alpha','assessment' if variant=='wrong_reference' else 'reference','reference' if variant=='wrong_assessment' else 'assessment','reference' if variant=='wrong_candidate' else 'candidate') and(f,l)==pair
        actual=run(d,v);expected=[variant=='endpoint_gain',variant in ('baseline','outside_gain','wrong_assessment','wrong_reference','wrong_candidate')]
        assert actual==expected,(variant,actual);rows[variant]=actual
    # Positive assessment remains fixed while gains at any pair inside the closure defeat barrenness.
    v=base(d);v['h256m']=lambda:'alpha';v['h246c']=lambda g,p,c:(g,p,c)==('alpha','beta','candidate');v['r5cq']=lambda *a:True;v['r5cs']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown progress accepted as absent')
    return dict(all_humanity_all_pairs_including_end=rows,unknown_rejected=True,
        boundaries=['r5cs: existing three kinds of progress, native evidence retained','r5cq: nonempty living humanity with valid individual evaluation, native evidence retained'],
        extinction_and_unassessed_points_not_success=True,causal_attribution_not_yet_supplied=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013')
    start=u['text'].index('beharrliche,',2310);end=u['text'].index('fruchtlos,',start)+len('fruchtlos,')
    return dict(status='partial_interval_and_progress_dependency',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        unresolved=['同じ合意による不毛化の原因性','消去への見立てと後世への害の様相','一般的な全面的不許可、auch nurの限定提示、前文との対照、全文帰属と通読'],
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
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=103,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('scope',scope_checks),('unending',unending_wiring_checks),('terms',terms_checks),('agreement',agreement_checks),('progress',progress_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,
        'scripts/compose_persistent_compact_progress.py','scripts/check_persistent_compact_progress.py','tests/test_persistent_compact_progress.py',
        'scripts/compose_fixed_religious_compact.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='bounded_or_unending_compact_and_complete_human_progress_interval',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
