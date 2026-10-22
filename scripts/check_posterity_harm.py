"""Check complete future membership, strict disadvantage and quoted conjecture."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_posterity_harm import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

REPORT='reports/posterity-harm-v1.json'
READING='data/posterity-harm-reading-v1.json'
DOC='docs/posterity-harm-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/compact-causal-denial-v1.json','reports/posterity-repudiation-v1.json','reports/epoch-undertakings-v1.json','reports/provisional-order-sentence-v1.json')
SCENES=('reference','candidate','baseline','anchor','later','farther','outside')
DOMAIN=('alpha','beta')
EXTRA=''.join('r z'+n+'[] a.' for n in (*DOMAIN,'gamma'))+''.join('r z'+n+'[] d.' for n in SCENES)+'r zbindings[] j[a].'
EIGHT=' '.join('k zalpha[]' for _ in NAMES)
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
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def base(d,bindings=('alpha',)*8):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,'gamma',*SCENES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    v['h254z']=lambda a:'anchor';v['h26e7']=lambda:'alpha'
    return v

def epoch_model(d,variant='baseline'):
    v=base(d);history=('anchor','later','farther')
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in history
    v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and history.index(a)<history.index(b)
    v['h26aa']=lambda e,r:r=='reference' and e in ('alpha','beta','gamma')
    spans={'alpha':{'anchor'},'beta':{'later'},'gamma':{'farther'}}
    if variant=='uncovered':spans['beta']=set()
    if variant=='overlap':spans['alpha'].add('later')
    v['h26ab']=lambda e,r,c,t:(r,c)==('reference','candidate') and t in spans.get(e,set())
    v['aa']=lambda p:p in ('alpha','beta')
    alive={('alpha','anchor'),('alpha','farther'),('beta','later')}
    if variant=='no_posterity':alive={('alpha','anchor')}
    v['h256o']=lambda p,c,t:c=='candidate' and (p,t) in alive
    members={'alpha','beta'}
    if variant=='missing_farther_member':members={'beta'}
    if variant=='missing_later_member':members={'alpha'}
    if variant=='nonhuman_member':members.add('gamma')
    if variant=='empty_group':members=set()
    v['h246c']=lambda g,p,r:g=='alpha' and r=='reference' and p in members
    if variant=='wrong_anchor':v['h254z']=lambda a:'later'
    if variant=='wrong_reference':v['zreference']=lambda:'outside'
    return v

@lru_cache(None)
def scope_checks():
    rows={};domain=(*DOMAIN,'gamma')
    for person in DOMAIN:
        for point in ('anchor','later','farther','outside'):
            d=fixture(('r5jy',),'q[k r5jy[k z'+person+'[] k zalpha[] '+CONTEXT+' k z'+point+'[]]].')
            actual=run(d,epoch_model(d),domain)
            expected=(person,point) in (('alpha','farther'),('beta','later'))
            assert actual==[expected],(person,point,actual);rows[person+':'+point]=actual[0]
    d=fixture(('r5j2',),'q[k r5j2[k zalpha[] k zalpha[] k zalpha[] '+CONTEXT+']].')
    groups={}
    for variant in ('baseline','missing_farther_member','missing_later_member','nonhuman_member','empty_group','no_posterity','uncovered','overlap','wrong_anchor','wrong_reference'):
        actual=run(d,epoch_model(d,variant),domain);assert actual==[variant=='baseline'],(variant,actual);groups[variant]=actual[0]
    for n in ('h26aa','h26ab','h257z','h256o','h246c','ic'):
        v=epoch_model(d);v[n]=unknown
        try:run(d,v,domain)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(native_posterity_points=rows,native_complete_group_and_agreement_epoch=groups,
        earlier_survivor_and_nonimmediate_future_included=True,unknown_membership_rejected=True,boundaries=[])

def harm_model(d,variant='baseline',bindings=('alpha',)*8):
    v=base(d,bindings);a,_,_,_,_,ep,g,standard=bindings
    v['r5j2']=lambda ag,e,p,r,c:(ag,e,p,r)==(a,ep,g,'reference') and c in ('candidate','baseline') and not(variant=='different_population' and c=='baseline')
    v['r5jo']=lambda b,r:content({'candidate','baseline'} if variant=='barren_baseline' else ({'candidate'} if variant!='no_candidate_barrenness' else set())) if normalized(b)==bindings[:5] and r=='reference' else content({'baseline'})
    expected=[('r5jo',0),bindings[:5],'reference','candidate','baseline']
    changes={'other_condition':(0,('r5j4',0)),'other_bindings':(1,('beta',)*5),'other_reference':(2,'outside'),'other_candidate':(3,'outside')}
    if variant in changes:i,value=changes[variant];expected[i]=value
    v['h26e6']=lambda *args:normalized(args)==tuple(expected) and variant!='no_comparator'
    v['h26e4']=lambda group,s,r,c:(group,s,r)==(g,standard,'reference') and c in ('candidate','baseline') and not(variant=='unevaluated_candidate' and c=='candidate') and not(variant=='unevaluated_baseline' and c=='baseline')
    pairs={('candidate','candidate'),('baseline','baseline'),('baseline','candidate')}
    if variant=='equal':pairs.add(('candidate','baseline'))
    if variant=='incomparable':pairs.remove(('baseline','candidate'))
    if variant=='better':pairs.remove(('baseline','candidate'));pairs.add(('candidate','baseline'))
    if variant=='nonreflexive':pairs.remove(('baseline','baseline'))
    v['h26e5']=lambda group,s,r,f,t:(group,s,r)==(g,standard,'reference') and (f,t) in pairs
    return v

@lru_cache(None)
def harm_checks():
    d=fixture(('r5j3',),'q[t[k r5j3[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5j2','r5jo'));rows={}
    for variant in ('baseline','no_candidate_barrenness','barren_baseline','different_population','no_comparator','other_condition','other_bindings','other_reference','other_candidate','unevaluated_candidate','unevaluated_baseline','equal','incomparable','better','nonreflexive'):
        actual=run(d,harm_model(d,variant));assert actual==[variant in ('baseline','no_candidate_barrenness')],(variant,actual);rows[variant]=actual[0]
    for n in ('h26e4','h26e5','h26e6'):
        v=harm_model(d);v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    positions=[]
    for i in range(8):
        b=tuple('beta' if j==i else 'alpha' for j in range(8));v=harm_model(d,bindings=b)
        assert run(d,v)==[True],i
        v['zbindings']=lambda:SequenceValue(('alpha',)*8,'"individual"');assert run(d,v)==[False],i
        positions.append(i)
    for length in (7,9):
        v=harm_model(d);v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
    return dict(strict_collective_comparison=rows,all_eight_positions_distinguished=positions,unknown_evaluation_rejected=True,
        boundaries=['r5j2 complete population tested natively above','r5jo prior all-pairs barrenness evidence preserved'],
        harm_not_identified_with_barrenness=True)

@lru_cache(None)
def cause_checks():
    d=fixture(('r5j6',),'q[t[k r5j6[k zbindings[] k zreference[]]][k zcandidate[]]].');rows={}
    for variant in ('baseline','no_cause','formation_source','other_period_source','other_result','source_binding','result_binding','reference','point'):
        v=base(d);expected=[('r5j4',2),('alpha',)*8,('r5j3',2),('alpha',)*8,'reference','candidate']
        changes={'formation_source':(0,('r5jn',2)),'other_period_source':(0,('r5jo',2)),'other_result':(2,('r5j4',2)),
            'source_binding':(1,('beta',)*8),'result_binding':(3,('beta',)*8),'reference':(4,'outside'),'point':(5,'baseline')}
        if variant in changes:i,value=changes[variant];expected[i]=value
        v['h253x']=lambda *a:normalized(a)==tuple(expected) and variant!='no_cause'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    for i in range(8):
        b=tuple('beta' if j==i else 'alpha' for j in range(8));v=base(d,b)
        v['h253x']=lambda *a:normalized(a)==(('r5j4',2),b,('r5j3',2),b,'reference','candidate')
        assert run(d,v)==[True],i
        v['zbindings']=lambda:SequenceValue(('alpha',)*8,'"individual"');assert run(d,v)==[False]
    v=base(d)
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown causal consequence accepted')
    return dict(quoted_second_causal_link=rows,all_eight_bindings_shared=True,world_content_not_executed=True,boundaries=[])

@lru_cache(None)
def adapter_checks():
    d=fixture(('r5j4','r5j7'),'q[t[k r5j4[k zbindings[] k zreference[]]][k zcandidate[]]].q[t[k r5j7[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5j2','r5jo','r5js'))
    rows={}
    for variant in ('baseline','no_barrenness','no_posterity','no_compact_scope','wrong_standard'):
        v=base(d)
        v['r5j2']=lambda *a:a==('alpha','alpha','alpha','reference','candidate') and variant!='no_posterity'
        v['r5jo']=lambda b,r:content({'candidate'} if normalized(b)==('alpha',)*5 and r=='reference' and variant!='no_barrenness' else set())
        v['r5js']=lambda *a:a==(*('alpha',)*6,'reference','candidate') and variant!='no_compact_scope'
        if variant=='wrong_standard':v['h26e7']=lambda:'beta'
        actual=run(d,v);expected=[variant not in ('no_barrenness','no_posterity'),variant not in ('no_posterity','no_compact_scope','wrong_standard')]
        assert actual==expected,(variant,actual);rows[variant]=actual
    for length in (7,9):
        v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False,False]
    return dict(source_and_candidate_scope=rows,candidate_scope_does_not_require_harm_or_formation=True,
        boundaries=['r5j2','r5jo','r5js; each native dependency verified separately'])

@lru_cache(None)
def presentation_checks():
    whole='r d[k r5j6[l[a]['+EIGHT+'] k zreference[]]]'
    d=fixture(('r5ka',),'q[k r5ka[k zalpha[] k zbeta[] '+whole+' k zreference[] k zoutside[]]].');rows={}
    for variant in ('baseline','node','author','whole','scope','focus','reference','context','no_conjecture'):
        v=base(d);expected=['alpha','beta',('r5j6',3),('r5j7',2),('r5j6',2),'reference','outside']
        changes={'node':(0,'beta'),'author':(1,'alpha'),'whole':(2,('r5j4',3)),'scope':(3,('r5j4',2)),
            'focus':(4,('r5j3',2)),'reference':(5,'candidate'),'context':(6,'reference')}
        if variant in changes:i,value=changes[variant];expected[i]=value
        v['h26fa']=lambda *a:normalized(a)==tuple(expected) and variant!='no_conjecture'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v=base(d)
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown conjectural presentation accepted')
    return dict(same_whole_scope_focus_reference_and_context=rows,quoted_world_and_consequence_not_asserted=True,boundaries=[])

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013')
    start=u['text'].index('dadurch aber wohl gar',2310);end=u['text'].index(', zu machen',start)
    return dict(status='partial_posterity_harm_and_tentative_consequence',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_comparison=dict(url='https://korpora.org/kant/aa08/039.html',lines='30–32',kind='source_text_comparison_not_unique_interpretation_proof'),
        unresolved=['期間の消去への見立て','gar・内側aber、規範出所と立場、schlechterdings・auch nur・冒頭Aber','具体的全体と箇所への接続、著者帰属・全文通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();sources=parents();old={n:e for s in sources for n,e in s.entries.items()}
    for n in read(BASIS)['imported_symbols']:
        assert c.entries[n]['declaration']==old[n]['declaration'] and c.entries[n]['meaning_ja']==old[n]['meaning_ja']
    # The parser canonicalizes bound names; inserting reference shifts the
    # candidate, point and both local quantifier names by one position.
    renaming=dict(zip(('vc','vd','ve','vf'),('vd','ve','vf','vg')))
    def generalize(x):
        if isinstance(x,dict):
            if x.get('kind')=='call' and x.get('symbol')=='h26av':return {'kind':'variable','name':'vc'}
            return {k:renaming.get(v,v) if k in ('name','variable') and isinstance(v,str) else generalize(v) for k,v in x.items()}
        if isinstance(x,list):return [generalize(v) for v in x]
        return x
    assert generalize(sources[1].entries['r5ds']['declaration']['body'])==c.entries['r5jy']['declaration']['body']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record()
    assert len(sources[1].document['statements'])==103
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),old_posterity_formula_generalized_exactly=True,
        roundtrips=True,preserved_main_statements=103,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('scope',scope_checks),('harm',harm_checks),('cause',cause_checks),('adapters',adapter_checks),('presentation',presentation_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,
        'scripts/compose_posterity_harm.py','scripts/check_posterity_harm.py','tests/test_posterity_harm.py',
        'scripts/compose_compact_causal_denial.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='posterity_collective_comparative_harm_and_tentative_causal_consequence',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
