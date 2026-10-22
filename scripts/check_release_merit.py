"""Check same release/benefit bindings across rank-one merit and both cohorts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_release_merit import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,NAMES,DATES,GROUND,BENEFIT,RESPONSE,MESSAGE,STANDARD,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/release-merit-v1.md';READING='data/release-merit-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v196.json'
PRIORS=('reports/humanity-release-v1.json','reports/world-posterity-v1.json','reports/grateful-regard-v1.json','reports/merit-praise-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','data/humanity-release-reading-v1.json')
DOMAIN=('actor','holder','beneficiary','activity','response','government','beforegroup','aftergroup','office','community','currentgroup','postgroup','currentepoch','postepoch','hearers','hearer','topic','source','label','users','audience','other')
SCENES=('reference','candidate','before','acted','last','now','later')
VALUES=tuple({'first':'before','anchor':'now'}.get(n,n) for n in NAMES)
EVENT=('actor','activity','government','beforegroup','aftergroup','community','reference','candidate','before','acted','last','office','now')
def z(n):return 'k z'+n+'[]'
def ns(values):return ' '.join(z(n) for n in values)
ASSESS='r[p zassessed]'
G='k r52f['+' '.join('r['+z(n)+']' for n in VALUES)+' '+ASSESS+']'
B='k r5zp['+' '.join('r['+z(n)+']' for n in ('government','community','reference'))+']'
M='o a[r[p ro7]]['+G+']'
def scope_names(side):return (side+'group',side+'epoch','hearers','activity','beneficiary','reference','candidate','now')
def response(side):return 'k r52j['+' '.join('r['+z(n)+']' for n in scope_names(side))+' o r['+B+'] o r['+G+']]'
SAVE='q[k zsaveground['+G+']].q[k zsavebenefit['+B+']].q[k zsavemessage['+M+']].'+''.join('q[k zsave'+side+'['+response(side)+']].' for side in ('current','post'))
FIRST='l['+STANDARD+'][k zstandard[]]';LAST='l['+STANDARD+'][k zpoststandard[]]'
WORLD=ns(('currentgroup','postgroup','currentepoch','postepoch','hearers','beneficiary'))+' '+FIRST+' '+LAST
CONCRETE=ns(VALUES)+' '+ASSESS+' '+WORLD
QUERY='q[t[c[k r52n['+CONCRETE+']]['+z('actor')+']]['+z('now')+']].'
def identity(c):return c.rank,json.loads(c.syntax)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,ground_boundary=False,benefit_boundary=False,frame_boundary=False,gratitude_boundary=False,conclusion_boundary=False):
    d=deepcopy(catalog().document)
    boundaries=tuple(n for n,on in (('r52c',ground_boundary),('r52d',benefit_boundary),('r5ys',frame_boundary)) if on)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zassessed[a d] c.d zotherground[person a] e[b point[e[v person][v person]]].'
    for n,s in (('ground',GROUND),('benefit',BENEFIT),('message',MESSAGE),('current',RESPONSE),('post',RESPONSE)):
        extra+='r zsave'+n+'['+s+'] c.'
    for n,prim in (('zstandard','zcriterion'),('zpoststandard','zpostcriterion')):
        extra+='r '+prim+'[a '+RESPONSE+' '+GROUND+' d] c.d '+n+'[] '+STANDARD+'[i[actor a response '+RESPONSE+' ground '+GROUND+'][b point[k '+prim+'[v actor v response v ground v point]]]].'
    if gratitude_boundary:
        extra+='r zgratitude[a a '+BENEFIT+' d d a a d] c.'
        stub='d zstub[activity a beneficiary a benefit '+BENEFIT+' reference d candidate d] h[a a] e[i[holder a actor a][b point[k zgratitude[v activity v beneficiary v benefit v reference v candidate v holder v actor v point]]]].'
        next(x for x in d['declarations'] if x['name']=='r5yo')['body']=parse('p:'+extra+stub)['declarations'][-1]['body']
    if conclusion_boundary:
        for n,prim in (('r5xv','zability'),('r5xj','zqualified')):
            extra+='r '+prim+'[a d] c.'
            stub='d zstub[] h[a] e[i[actor a][b point[k '+prim+'[v actor v point]]]].'
            next(x for x in d['declarations'] if x['name']==n)['body']=parse('p:'+extra+stub)['declarations'][-1]['body']
    prefix=parse('p:'+extra);replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h')}
    additions=[x for x in prefix['declarations'] if x['name'] not in replacements]
    d['declarations']=additions+[replacements.get(x['name'],x) for x in d['declarations']]
    d.update(declarations=closure(d,(*roots,*(x['name'] for x in additions))),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    for n in ('ground','benefit','message','current','post'):v['zsave'+n]=lambda c,n=n:saved.update({n:identity(c)}) is None
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],zassessed=lambda *a:True,
        aa=lambda p:p in ('actor','holder','beneficiary','hearer','other'),
        r52c=lambda *a:a[:-1]==EVENT and a[-1]('other','before') is True,
        r52d=lambda *a:a[:-2]==EVENT and a[-2]('other','before') is True and a[-1]=='beneficiary',
        r5ys=lambda *a:a==('currentgroup','postgroup','currentepoch','postepoch','reference','candidate','now'),
        h246c=lambda g,p,r:r=='reference' and (g,p) in (('currentgroup','holder'),('postgroup','holder'),('hearers','hearer')),
        h256o=lambda p,c,t:p=='holder' and c=='candidate' and t in ('now','later'),
        h26ab=lambda e,r,c,t:(r,c)==('reference','candidate') and (e,t) in (('currentepoch','now'),('postepoch','later')),
        ic=lambda a,b,c:(a,b,c)==('now','later','candidate'),
        zcriterion=lambda a,r,g,t:(a,identity(r),identity(g),t)==('actor',saved['current'],saved['ground'],'now'),
        zpostcriterion=lambda a,r,g,t:(a,identity(r),identity(g),t)==('actor',saved['post'],saved['ground'],'now'),
        zability=lambda a,t:(a,t)==('actor','now'),zqualified=lambda a,t:(a,t)==('actor','now'))
    return v,saved

@lru_cache(None)
def ground_checks():
    profile='k r52e['+ns(VALUES)+' p zassessed]'
    q=''.join('q[t[c['+f+']['+z('actor')+']]['+z(p)+']].' for f in (profile,'s['+G+']') for p in ('now','later'))
    d=fixture(('r52e','r52f'),q,ground_boundary=True);v,_=base(d);assert run(d,v)==[True]*4
    for n in VALUES:
        v,_=base(d);v['z'+n]=lambda n=n:'later' if n in SCENES else 'other';assert run(d,v)==[False]*4,n
    v,_=base(d);v['zassessed']=lambda *a:False;assert run(d,v)==[False]*4
    v,_=base(d);v['r52c']=unknown;rejects(d,v)
    only=fixture(('r52f',),'q[k zsaveground['+G+']].')
    v,saved=base(only);assert run(only,v)==[True] and saved['ground'][0]==1
    v['r52c']=unknown;assert run(only,v)==[True]
    # Try the lower rank against the real dependency graph, not a stub.
    full=format_graph(catalog().document,'compact')
    try:parse(full+'d zbad[] i[h[a a a a a a d d d d d d h[a d] c] h[a] e][r[p r52e]].')
    except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
    else:raise AssertionError('Rank-zero concrete merit accepted')
    return dict(native_and_dequoted_profile_match=True,twelve_settings_and_assessment_bound=True,outer_time_does_not_move_episode=True,
        rank_one_required=True,construction_does_not_execute_release=True,unknown_rejected=True,
        boundary='Previously checked r52c is an exact tuple boundary for profile execution; quotation rank rejection uses the unmodified dependency graph.')

def praise_model(d,point):
    v,saved=base(d)
    v.update(dg=lambda a,t:(a,t)==('response',point),f3=lambda p,a,t:(p,a,t)==('holder','response',point),
        h234g=lambda a,p,s,m,t:(a,p,s,identity(m),t)==('response','hearer','actor',saved['message'],point),
        h26n3=lambda p,a,s,g,t:(p,a,s,identity(g),t)==('holder','response','actor',saved['ground'],point),
        h26n4=lambda p,a,s,g,r,t:(p,a,s,identity(g),r,t)==('holder','response','actor',saved['ground'],'reference',point),
        zgratitude=lambda a,b,g,r,c,h,s,t:(a,b,identity(g),r,c,h,s,t)==('activity','beneficiary',saved['benefit'],'reference','candidate','holder','actor',point))
    return v,saved
@lru_cache(None)
def praise_checks():
    rows={}
    for side,point in (('current','now'),('post','later')):
        scope=ns(scope_names(side))+' '+B+' '+G
        q=SAVE+''.join('q[t[c['+f+']['+ns(('holder','response','actor'))+']]['+z(point)+']].' for f in ('k r52i['+scope+']','s['+response(side)+']'))
        d=fixture(('r52i','r52j','r52f','r5zp'),q,gratitude_boundary=True)
        v,_=praise_model(d,point);v['r52c']=unknown;assert run(d,v)==[True]*7
        for n in ('dg','f3','h234g','h26n3','h26n4','zgratitude','h256o','h26ab'):
            v,_=praise_model(d,point);v[n]=lambda *a:False;assert run(d,v)==[True]*5+[False]*2,(side,n)
            v[n]=unknown;rejects(d,v)
        v,_=praise_model(d,point);v['h246c']=lambda *a:False;assert run(d,v)==[True]*5+[False]*2
        # The same truth value of another property cannot replace its syntax.
        wrong=fixture(('r52i','r52j','r52f','r5zp'),SAVE+q[len(SAVE):].replace(G,'r b[p zotherground]'),gratitude_boundary=True)
        v,_=praise_model(wrong,point);assert run(wrong,v)==[True]*5+[False]*2
        rows[side]=dict(native_and_dequoted=True,unperformed_ground_not_evaluated=True,empty_audience_rejected=True)
    return dict(cases=rows,rank_one_message_uses_existing_h234g=True,strong_own_positive_appraisal_required=True,
        same_benefit_and_ground_distinct=True,unknown_rejected=True,
        boundary='Only previously checked r5yo gratitude uses a native function with an eight-argument boundary. Native speech, scope and code identities are evaluated. No ground truth or actual release is executed by praise.')

@lru_cache(None)
def merit_checks():
    d=fixture(('r52k','r52f','r52j','r5zp'),SAVE+'q[t[k r52k['+z('actor')+' '+response('current')+' '+G+' '+FIRST+']]['+z('now')+']].',ground_boundary=True)
    rows={}
    for case in ('baseline','false_ground','false_standard','empty_standards','one_of_two_fails','different_ground','different_response'):
        tested=d;v,_=base(tested)
        if case=='false_ground':v['r52c']=lambda *a:False
        if case=='false_standard':v['zcriterion']=lambda *a:False
        if case in ('empty_standards','one_of_two_fails','different_ground','different_response'):
            # Build the alternate query without changing the captured descriptions.
            standard='l['+STANDARD+'][]' if case=='empty_standards' else 'l['+STANDARD+'][k zstandard[] k zpoststandard[]]'
            goal='r b[p zotherground]' if case=='different_ground' else G
            resp=response('post') if case=='different_response' else response('current')
            if case in ('different_ground','different_response'):standard=FIRST
            tested=fixture(('r52k','r52f','r52j','r5zp'),SAVE+'q[t[k r52k['+z('actor')+' '+resp+' '+goal+' '+standard+']]['+z('now')+']].',ground_boundary=True);v,_=base(tested)
        got=run(tested,v);assert got==[True]*5+[case=='baseline'],(case,got);rows[case]=got[-1]
        for n in ('h234g','h26n3','h26n4','h26nf','h26nu'):assert v.get(n,unknown) is unknown
    for n in ('r52c','zcriterion'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,true_same_merit_and_all_nonempty_standards=True,response_and_gratitude_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def binding_checks():
    q=SAVE+QUERY+'q[t[c[k r52o['+z('topic')+' '+CONCRETE+']]['+z('actor')+']]['+z('now')+']].'
    d=fixture(('r52n','r52o','r52j','r5zp'),q,True,True,True,conclusion_boundary=True);rows=[]
    for bits in product((False,True),repeat=5):
        v,_=base(d)
        for n,on in zip(('r52d','r52c','zcriterion','zpostcriterion','r5ys'),bits):
            old=v[n];v[n]=lambda *a,old=old,on=on:on and old(*a)
        got=run(d,v);assert got==[True]*5+[all(bits)]*2,(bits,got);rows.append(dict(conditions=bits,result=got[-2:]))
    v,_=base(d);v['zability']=lambda *a:False;assert run(d,v)==[True]*6+[False]
    for n in ('activity','government','beforegroup','aftergroup','office','community','beneficiary'):
        v,_=base(d);old=v['znamepick'];v['znamepick']=lambda p,*cs,n=n:old('other' if p==n else p,*cs)
        assert run(d,v)==[True]*5+[False]*2,n
    v,_=base(d);v['zassessed']=lambda *a:False;assert run(d,v)==[True]*5+[False]*2
    for n in ('r52c','r52d','zcriterion','zpostcriterion','r5ys','zability'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    # Native generality retains the common actor; no qualified person is invented.
    prince=ns(('label','users','source','office','beforegroup','community','topic','audience','reference'))
    tail=ns(tuple(v for n,v in zip(NAMES,VALUES) if n not in ('office','community','reference')))
    g=fixture(('r52p','r52j','r5zp'),SAVE+'q[t[k r52p['+prince+' '+tail+' '+ASSESS+' '+WORLD+']]['+z('now')+']].',True,True,True,conclusion_boundary=True)
    general={}
    for case in ('baseline','no_qualified','qualified_failure','different_person_qualified'):
        v,_=base(g)
        if case=='no_qualified':v['zqualified']=lambda *a:False;v['zability']=lambda *a:False
        if case=='qualified_failure':v['zability']=lambda *a:False
        if case=='different_person_qualified':v['zqualified']=lambda a,t:(a,t)==('other','now')
        got=run(g,v);assert got==[True]*5+[case in ('baseline','no_qualified')],(case,got);general[case]=got[-1]
    return dict(thirty_two_combinations=rows,generality=general,same_concrete_event_benefit_ground_and_both_cohorts=True,
        seven_names_and_assessment_checked=True,ability_is_independent_conjunct=True,unknown_rejected=True,
        boundary='Prior r52c/r52d and complete population frame r5ys are exact tuple boundaries. Ability and qualified-prince profiles use native function bodies with scalar boundaries. Concrete binding, quotation, both merit folds and universal conditional execute natively.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('und verdient');end=u['text'].index('zu bedienen.')+len('zu bedienen.')
    return dict(status='concrete_first_release_bound_to_both_grateful_deserved_responses',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,evidence=list(SOURCES),
        unresolved=['一般条件の設定・比較評価・全称揚適合基準の供給と本文束縛','wenigstens・sondern等の提示と名称評価の独立した著者帰属','一文全体と後続の意味判断'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[2].document['statements'])==112
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    # Compare the complete merit body after reverting only the ground grade.
    newer=deepcopy(c.entries['r52k']['declaration']);old=parents()[1].entries['r5yw']['declaration']
    from scripts.compose_release_merit import sortof
    def lower(x):
        if x==sortof(GROUND):return sortof(BENEFIT)
        if isinstance(x,list):return [lower(y) for y in x]
        if isinstance(x,dict):
            y={k:lower(v) for k,v in x.items()}
            if y.get('kind')=='disquote':y.pop('rank',None)
            return y
        return x
    newer=lower(newer);newer['name']='r5yw';assert newer==old
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,parent_meanings_preserved=True,merit_structure_unchanged_apart_from_ground_grade=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('ground',ground_checks),('praise',praise_checks),('merit',merit_checks),('binding',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_release_merit.py','scripts/check_release_merit.py','tests/test_release_merit.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_qualified_prince_frame.py',
        'scripts/compose_world_posterity.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_concrete_release_benefit_and_both_deserved_responses_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
