"""Check supplied evaluation/criteria and witnesses chosen inside each person."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_prince_merit_scope import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,ACHIEVEMENT,ASSESSMENT,STANDARD,parents,build,closure
from scripts import check_release_merit as prior
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/prince-merit-scope-v1.md';READING='data/prince-merit-scope-reading-v1.json'
INVENTORY=prior.INVENTORY;INDEX=prior.INDEX
PRIORS=('reports/release-merit-v1.json','reports/humanity-release-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','data/release-merit-reading-v1.json')
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES;z=prior.z;ns=prior.ns;identity=prior.identity
ACH='k r52q[r['+z('reference')+'] r['+z('candidate')+']]'
AS='k r52s[r['+z('reference')+'] r['+z('candidate')+']]'
G='k r52t['+' '.join('r['+z(n)+']' for n in prior.VALUES)+' '+AS+']'
B=prior.B
def response(side):return 'k r52j['+' '.join('r['+z(n)+']' for n in prior.scope_names(side))+' o r['+B+'] o r['+G+']]'
SAVE='q[k zsaveachievement['+ACH+']].q[k zsaveground['+G+']].q[k zsavebenefit['+B+']].'+''.join('q[k zsave'+s+'['+response(s)+']].' for s in ('current','post'))
COHORT=ns(('currentgroup','postgroup','currentepoch','postepoch','hearers'))
FRAME=ns(('office','community','topic','reference','candidate','now'))+' '+COHORT
SELECTED=ns(prior.VALUES)+' '+COHORT+' '+z('beneficiary')
QUERY='q[t[c[k r52v['+SELECTED+']]['+z('actor')+']]['+z('now')+']].'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,event_boundary=False,witness_boundary=False):
    # Reuse the earlier native naming and criterion fixtures without mutating
    # its cached document or its catalog. New declarations are appended below.
    d=deepcopy(prior.fixture(('r52p','r52b'),'',True,True,True,conclusion_boundary=True))
    extra='r zsaveachievement['+ACHIEVEMENT+'] c.'
    extra+='r zpickstandards[a a a a a d j['+STANDARD+'] j['+STANDARD+'] j['+STANDARD+']] j['+STANDARD+'].'
    extra+='d h26n6[actor a office a community a group a epoch a reference d] j['+STANDARD+'][k zpickstandards[v actor v office v community v group v epoch v reference l['+STANDARD+'][k zstandard[]] l['+STANDARD+'][k zpoststandard[]] l['+STANDARD+'][]]].'
    if witness_boundary:extra+='r zwitness[a a a a a a d d d d d d a a a a a a a d] c.'
    d['declarations']+=parse('p:r zstandard[] '+STANDARD+'.r zpoststandard[] '+STANDARD+'.'+extra)['declarations'][2:]
    d['declarations'] += [deepcopy(catalog().entries[n]['declaration']) for n in ('h26n5',*MEANINGS)]
    if event_boundary:
        x=next(x for x in d['declarations'] if x['name']=='r5z5');x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    if witness_boundary:
        from scripts.compose_prince_merit_scope import DETAILS,COHORT as CF,DARGS,COARGS
        stub='d zstub['+DETAILS+' '+CF+' beneficiary a] h[a] e[i[actor a][b point[k zwitness['+DARGS+' '+COARGS+' v beneficiary v actor v point]]]].'
        primitive=next(x for x in d['declarations'] if x['name']=='zwitness')
        head=deepcopy(d);head.update(declarations=[primitive],statements=[])
        body=parse(format_graph(head,'compact')+stub)['declarations'][-1]['body']
        next(x for x in d['declarations'] if x['name']=='r52v')['body']=body
    helpers=tuple(x['name'] for x in d['declarations'] if x['name'].startswith('z'))
    d.update(declarations=closure(d,(*roots,*helpers)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN):
    try:run(d,v,domain)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v,saved=prior.base(d)
    for x in d['declarations']:
        if x['kind']=='primitive' and x['name'] not in v:v[x['name']]=unknown
    v['zsaveachievement']=lambda c:saved.update(achievement=identity(c)) is None
    v['h26n5']=lambda p,c,r,t:p in DOMAIN and identity(c)==saved['achievement'] and r=='reference' and t in SCENES
    def criteria(a,o,c,g,e,r,first,last,empty):
        if (a,o,c,r)!=('actor','office','community','reference'):return empty
        return first if (g,e)==('currentgroup','currentepoch') else last if (g,e)==('postgroup','postepoch') else empty
    v['zpickstandards']=criteria
    return v,saved

@lru_cache(None)
def comparison_checks():
    q='q[k zsaveachievement['+ACH+']].q[k r52b['+ns(('actor','activity','reference','candidate','now','last'))+' k r52r['+ns(('reference','candidate'))+']]].'
    d=fixture(('r52b','r52r','r52q'),q,event_boundary=True)
    domain=('actor','other','activity','response','government','community');order=('before','acted','last','now','later');rows={}
    def model():
        v,saved=base(d)
        v.update(aa=lambda p:p in ('actor','other'),h257z=lambda r,c,t:(r,c)==('reference','candidate') and t in order,
            ic=lambda a,b,c:c=='candidate' and a in order and b in order and order.index(a)<order.index(b))
        return v,saved
    key=('actor','activity','government','community','reference','candidate','last')
    for case in ('baseline','earlier_other','earlier_self','unassessed_other','unassessed_actor','only_future_unassessed','no_achievement','wrong_criterion_name'):
        v,_=model();events={key}
        if case in ('earlier_other','earlier_self'):events.add(('other' if case=='earlier_other' else 'actor','response','government','community','reference','candidate','before'))
        if case=='no_achievement':events=set()
        if case in ('unassessed_other','unassessed_actor','only_future_unassessed'):
            old=v['h26n5'];missing=('other','before') if case=='unassessed_other' else ('actor','last')
            v['h26n5']=lambda p,c,r,t:old(p,c,r,t) and (t!='later' if case=='only_future_unassessed' else (p,t)!=missing)
        if case=='wrong_criterion_name':
            old=v['zrefpick'];v['zrefpick']=lambda p,*cs:old('later' if p=='reference' else p,*cs)
        v['r5z5']=lambda *a:a in events
        got=run(d,v,domain);assert got==[True,case in ('baseline','only_future_unassessed')],(case,got);rows[case]=got[-1]
    v,_=model();v['r5z5']=lambda *a:a==key;v['h26n5']=unknown;rejects(d,v,domain)
    # The supplied evaluation has the same code and arguments when dequoted.
    q='q[k zsaveachievement['+ACH+']].'+''.join('q[c['+f+']['+ns(('other','before'))+']].' for f in ('k r52r['+ns(('reference','candidate'))+']','s['+AS+']'))
    e=fixture(('r52q','r52r','r52s'),q);v,_=base(e);assert run(e,v)==[True]*3
    v['h26n5']=lambda *a:False;assert run(e,v)==[True,False,False]
    return dict(cases=rows,same_achievement_code_and_reference=True,assessment_not_success=True,native_and_dequoted_assessment_match=True,
        unknown_rejected=True,boundary='Native first comparison and supplied evaluation; the already checked dated release r5z5 is an exact event boundary. Earlier events and incomplete evaluation remain distinguishable.')

@lru_cache(None)
def supplied_checks():
    d=fixture(('r52v','r52q','r52j'),SAVE+QUERY);rows={}
    for case in ('baseline','missing_assessment','false_merit','missing_benefit','empty_current','empty_post','false_current','false_post'):
        v,_=base(d)
        if case=='missing_assessment':v['h26n5']=lambda *a:False
        if case=='false_merit':v['r52c']=lambda *a:False
        if case=='missing_benefit':v['r52d']=lambda *a:False
        if case in ('empty_current','empty_post'):
            old=v['zpickstandards'];side='currentgroup' if case=='empty_current' else 'postgroup'
            v['zpickstandards']=lambda *a:a[-1] if a[3]==side else old(*a)
        if case=='false_current':v['zcriterion']=lambda *a:False
        if case=='false_post':v['zpostcriterion']=lambda *a:False
        got=run(d,v);assert got==[True]*5+[case=='baseline'],(case,got);rows[case]=got[-1]
    for pos in range(6):
        v,_=base(d);old=v['zpickstandards']
        def wrong(*a):
            b=list(a);b[pos]='other' if pos<5 else 'later';return old(*b)
        v['zpickstandards']=wrong;assert run(d,v)==[True]*5+[False],pos
    for n in ('activity','government','office','community','beneficiary'):
        v,_=base(d);old=v['znamepick'];v['znamepick']=lambda p,*cs,n=n:old('other' if p==n else p,*cs)
        assert run(d,v)==[True]*5+[False],n
    for n in ('h26n5','zpickstandards','zcriterion','zpostcriterion','r52c','r52d'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,six_standard_provider_arguments_checked=True,same_supplied_assessment_in_ground_and_benefit=True,
        distinct_nonempty_complete_criteria_for_each_cohort=True,unknown_rejected=True,
        boundary='r52c/r52d and complete population frame retain prior exact tuple boundaries. Criterion provider selects native Noema function sequences; both merit folds, quotations and supplied evaluation execute natively.')

@lru_cache(None)
def scope_checks():
    # Two individuals and two situations suffice to distinguish per-person
    # witnesses without enumerating the much larger native event model again.
    prince=ns(('label','users','source','office','beforegroup','community','topic','audience','reference'))
    q='q[t[k r52x['+prince+' '+ns(('candidate','now'))+' '+COHORT+']]['+z('now')+']].'
    d=fixture(('r52x',),q,witness_boundary=True);rows={};seen=set()
    def model():
        v,_=base(d)
        v.update({'z'+n:lambda:'actor' for n in DOMAIN});v.update({'z'+n:lambda:'now' for n in SCENES})
        v.update(zability=lambda a,t:t=='now',zqualified=lambda a,t:t=='now')
        def witness(*a):
            # activity, government, two populations, beneficiary and all three
            # event times depend on the very person receiving the conclusion.
            person=a[18];when='now' if person=='actor' else 'later'
            ok=all(a[i]==person for i in (0,1,2,3,17)) and all(a[i]==when for i in (8,9,10))
            ok=ok and all(a[i]=='actor' for i in (4,5,12,13,14,15,16)) and all(a[i]=='now' for i in (6,7,11,19))
            if ok:seen.add((person,a[0],a[1],a[17],a[8],a[9],a[10]))
            return ok
        v['zwitness']=witness;return v
    for case in ('both_distinct','only_first_event','only_second_event','split_witness','second_incapable','no_qualified','one_qualified','wrong_fixed_context','wrong_anchor'):
        tested=d;v=model();old=v['zwitness']
        if case=='only_first_event':v['zwitness']=lambda *a:a[18]=='actor' and old(*a)
        if case=='only_second_event':v['zwitness']=lambda *a:a[18]=='other' and old(*a)
        if case=='split_witness':v['zwitness']=lambda *a:old(*a) and a[0]!=a[1]
        if case=='second_incapable':v['zability']=lambda a,t:a=='actor'
        if case=='no_qualified':v['zqualified']=lambda *a:False;v['zwitness']=lambda *a:False
        if case=='one_qualified':v['zqualified']=lambda a,t:a=='actor';v['zwitness']=lambda *a:a[18]=='actor' and old(*a)
        if case=='wrong_fixed_context':v['zoffice']=lambda:'other'
        if case=='wrong_anchor':
            changed=q.replace(ns(('candidate','now')),ns(('candidate','later')))
            tested=fixture(('r52x',),changed,witness_boundary=True);v['zlater']=lambda:'later'
        got=run(tested,v,('actor','other'),('now','later'));assert got==[case in ('both_distinct','no_qualified','one_qualified')],(case,got);rows[case]=got[0]
    assert ('actor','actor','actor','actor','now','now','now') in seen and ('other','other','other','other','later','later','later') in seen
    v=model();v['zwitness']=unknown
    try:run(d,v,('actor','other'),('now','later'))
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown witness accepted')
    return dict(cases=rows,two_qualified_people_with_distinct_complete_witnesses=True,one_person_cannot_supply_the_others_event=True,
        office_community_reference_and_cohorts_remain_shared=True,existence_not_inferred_from_generality=True,unknown_rejected=True,
        boundary='Only this quantifier test replaces r52v with an exact 20-argument native-function boundary, and prior ability/qualification profiles. Synthetic witness dates test binding, not event chronology; strict chronology and public release were checked in the pinned native event tests.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');end=u['text'].index('zu bedienen.')+len('zu bedienen.')
    return dict(status='per_prince_conclusion_scope_and_supplied_evaluation_criteria',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,end],text=u['text'][:end]),
        interpretation=LIMITS,evidence=list(SOURCES),
        unresolved=['名称・規範出所・聴衆・時代等の本文設定と著者帰属','wenigstens・sondern等の提示と名称評価の独立した帰属','一文全体と後続の通読判断'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==112
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for new,old in (('r52t','r52f'),('r52u','r52n')):
        d=deepcopy(c.entries[new]['declaration']);original=parents()[0].entries[old]['declaration'];var=d['parameters'][12]['name']
        d['name']=old;d['parameters'][12]['sort']=deepcopy(original['parameters'][12]['sort'])
        def lower(x):
            if isinstance(x,list):return [lower(y) for y in x]
            if isinstance(x,dict):
                y={k:('r52f' if k=='symbol' and v=='r52t' else lower(v)) for k,v in x.items()}
                if y.get('kind')=='disquote' and y.get('description')==dict(kind='variable',name=var):y.pop('rank',None)
                return y
            return x
        d['body']=lower(d['body']);assert d==original,(new,old)
    # All low-grade attempts use the actual unmodified dependencies.
    full=format_graph(c.document,'compact')
    for symbol,low,valid in (('r52r','r','r b'),('r52u','r b','r c')):
        code=low+'[p '+symbol+']'
        try:parse(full+'q[e['+code+']['+code+']].')
        except ValueError as e:assert 'Quoted evaluation' in str(e)
        else:raise AssertionError('Low grade accepted: '+symbol)
        code=valid+'[p '+symbol+']';parse(full+'q[e['+code+']['+code+']].')
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,parent_meanings_preserved=True,upgrades_change_only_assessment_grade=True,
        assessment_grade_one_and_bound_integration_grade_two_required=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('comparison',comparison_checks),('supplied',supplied_checks),('scope',scope_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_prince_merit_scope.py','scripts/check_prince_merit_scope.py','tests/test_prince_merit_scope.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_qualified_prince_frame.py',
        'scripts/compose_release_merit.py','scripts/check_release_merit.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='per_prince_witnesses_and_bound_evaluation_criteria_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
