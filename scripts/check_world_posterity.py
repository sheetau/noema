"""Check exact population scopes and two nonperformed grateful responses."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_world_posterity import ROOT,LIBRARY,BASIS,GOAL,RESPONSE,STANDARD,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/world-posterity-v1.md';READING='data/world-posterity-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v196.json'
PRIORS=('reports/grateful-regard-v1.json','reports/merit-praise-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/world-posterity-v1/dwb-nachwelt.html')
DOMAIN=('actor','holder','survivor','laterperson','farperson','dead','benefaction','beneficiary','response','hearer','firstgroup','lastgroup','firstepoch','lastepoch','hearers','other')
SCENES=('reference','candidate','past','now','edge','later','far','outside')
ORDER=('past','now','edge','later','far')
PEOPLE=('holder','survivor','laterperson','farperson','dead')
LIVES={('holder','now'),('survivor','now'),('survivor','later'),('laterperson','later'),('farperson','far'),('dead','past')}
MEMBERS={('firstgroup','holder'),('firstgroup','survivor'),('lastgroup','survivor'),('lastgroup','laterperson'),('lastgroup','farperson'),('hearers','hearer')}
PERIODS={('firstepoch',p) for p in ('past','now','edge')}|{('lastepoch',p) for p in ('later','far')}
def z(n):return 'k z'+n+'[]'
G='r[p zgrounded]';B='r[p zbenefit]'
def names(side):return (side+'group',side+'epoch','hearers','benefaction','beneficiary','reference','candidate','now')
def scope(side):return ' '.join(z(n) for n in names(side))+' '+B+' '+G
def code(side):return 'k r5yu['+' '.join('r['+z(n)+']' for n in names(side))+' r['+B+'] r['+G+']]'
SAVE=''.join('q[k zsave'+side+'['+code(side)+']].' for side in ('first','last'))
FIRST='l['+STANDARD+'][k zstandard[]]';LAST='l['+STANDARD+'][k zlaststandard[]]'
MERIT=' '.join(z(n) for n in ('firstgroup','lastgroup','firstepoch','lastepoch','hearers','benefaction','beneficiary','candidate','now'))+' '+B+' '+G+' '+FIRST+' '+LAST
FRAME=' '.join(z(n) for n in ('firstgroup','lastgroup','firstepoch','lastepoch','reference','candidate','now'))
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def identity(c):return c.rank,json.loads(c.syntax)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,response_boundary=False,integration_boundary=False):
    d=deepcopy(catalog().document)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zground[a d] c.r zbenefitstate[a d] c.d zgrounded[person a] e[b point[k zground[v person v point]]].d zbenefit[person a] e[b point[k zbenefitstate[v person v point]]].'
    extra+='r zsavefirst['+RESPONSE+'] c.r zsavelast['+RESPONSE+'] c.'
    for n,primitive in (('zstandard','zcriterion'),('zlaststandard','zlastcriterion')):
        extra+='r '+primitive+'[a '+RESPONSE+' '+GOAL+' d] c.d '+n+'[] '+STANDARD+'[i[actor a response '+RESPONSE+' ground '+GOAL+'][b point[k '+primitive+'[v actor v response v ground v point]]]].'
    if response_boundary:
        # Only the already checked gratitude/praise interior is replaced.
        extra+='r zgrateful[a a '+GOAL+' d d '+GOAL+' a a a d] c.'
        stub='d zstub[activity a beneficiary a goal '+GOAL+' reference d candidate d audience h[a] c ground '+GOAL+'] h[a a a] e[i[holder a response a actor a][b point[w[c[v audience]['+z('hearer')+']][k zgrateful[v activity v beneficiary v goal v reference v candidate v ground v holder v response v actor v point]]]]].'
        stubdoc=parse('p:'+extra+stub)
        next(x for x in d['declarations'] if x['name']=='r5yp')['body']=stubdoc['declarations'][-1]['body']
    if integration_boundary:
        for n,primitive in (('r5xv','zability'),('r5xj','zqualified')):
            extra+='r '+primitive+'[a d] c.'
            body=parse('p:r '+primitive+'[a d] c.d zstub[] h[a] e[i[person a][b point[k '+primitive+'[v person v point]]]].')['declarations'][1]['body']
            next(x for x in d['declarations'] if x['name']==n)['body']=body
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
    v.update(znamepick=lambda item,*codes:codes[DOMAIN.index(item)],zrefpick=lambda point,*codes:codes[SCENES.index(point)],
        aa=lambda p:p in PEOPLE,
        h26aa=lambda e,r:r=='reference' and e in ('firstepoch','lastepoch'),
        h257z=lambda r,c,p:(r,c)==('reference','candidate') and p in ORDER,
        ic=lambda a,b,c:c=='candidate' and a in ORDER and b in ORDER and ORDER.index(a)<ORDER.index(b),
        h26ab=lambda e,r,c,p:(r,c)==('reference','candidate') and (e,p) in PERIODS,
        h256o=lambda p,c,s:c=='candidate' and (p,s) in LIVES,
        h246c=lambda g,p,r:r=='reference' and (g,p) in MEMBERS)
    for side in ('first','last'):v['zsave'+side]=lambda c,side=side:saved.update({side:identity(c)}) is None
    return v,saved

@lru_cache(None)
def population_checks():
    d=fixture(('r5ys',),'q[k r5ys['+FRAME+']].');rows={}
    for case in ('baseline','missing_current','dead_in_current','missing_far_person','extra_future_person','only_next_generation','overlap','outside_history','empty_future','cyclic_order','bad_epoch','wrong_anchor','wrong_reference','wrong_candidate'):
        v,_=base(d)
        if case in ('missing_current','dead_in_current','missing_far_person','extra_future_person'):
            members=set(MEMBERS)
            if case=='missing_current':members.remove(('firstgroup','survivor'))
            if case=='dead_in_current':members.add(('firstgroup','dead'))
            if case=='missing_far_person':members.remove(('lastgroup','farperson'))
            if case=='extra_future_person':members.add(('lastgroup','dead'))
            v['h246c']=lambda g,p,r:r=='reference' and (g,p) in members
        if case in ('only_next_generation','overlap','outside_history','empty_future'):
            periods=set(PERIODS)
            if case=='only_next_generation':periods.remove(('lastepoch','far'))
            if case=='overlap':periods.add(('lastepoch','edge'))
            if case=='outside_history':periods.add(('lastepoch','outside'))
            if case=='empty_future':periods={pair for pair in periods if pair[0]!='lastepoch'}
            v['h26ab']=lambda e,r,c,p:(r,c)==('reference','candidate') and (e,p) in periods
        if case=='cyclic_order':v['ic']=lambda a,b,c:c=='candidate' and a!=b and a in ORDER and b in ORDER
        if case=='bad_epoch':v['h26aa']=lambda *a:False
        if case=='wrong_anchor':v['znow']=lambda:'later'
        if case=='wrong_reference':v['zreference']=lambda:'outside'
        if case=='wrong_candidate':v['zcandidate']=lambda:'outside'
        got=run(d,v);assert got==[case=='baseline'],(case,got);rows[case]=got[0]
    for n in ('aa','h26aa','h257z','ic','h26ab','h256o','h246c'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,shared_survivor_allowed=True,current_population_not_whole_epoch_population=True,
        entire_future_tail_required=True,unknown_rejected=True,
        boundary='Finite native models check the definitions, not an empirical enumeration of future humanity.')

def response_model(d,holder,point):
    v,saved=base(d)
    v['zgrateful']=lambda a,b,g,r,c,gr,h,s,t,p:(a,b,identity(g),r,c,identity(gr),h,s,t,p)==(
        'benefaction','beneficiary',(0,dict(kind='function_ref',symbol='zbenefit')),'reference','candidate',
        (0,dict(kind='function_ref',symbol='zgrounded')),holder,'response','actor',point)
    return v,saved
@lru_cache(None)
def response_checks():
    rows={}
    for side,holder,point,expected in (('first','holder','now',True),('last','farperson','far',True),('last','survivor','later',True),
            ('first','dead','past',False),('first','holder','edge',False),('first','holder','later',False),('last','holder','later',False)):
        q=''.join('q[t[c['+f+']['+' '.join(z(n) for n in (holder,'response','actor'))+']]['+z(point)+']].' for f in ('k r5yt['+scope(side)+']','s['+code(side)+']'))
        d=fixture(('r5yt','r5yu'),q,True);v,_=response_model(d,holder,point);got=run(d,v)
        assert got==[expected]*2,(side,holder,point,got);rows['/'.join((side,holder,point))]=got
        if side=='first' and holder=='holder' and point=='now':
            for n in ('h246c','h256o','h26ab','zgrateful'):
                v,_=response_model(d,holder,point);v[n]=lambda *a:False;assert run(d,v)==[False]*2
                v[n]=unknown;rejects(d,v)
            for target,replacement in (('benefaction','other'),('beneficiary','other'),('reference','outside'),('candidate','outside'),('hearers','other'),('response','other'),('actor','other')):
                changed=fixture(('r5yt','r5yu'),q.replace(z(target),z(replacement)),True)
                v,_=response_model(changed,holder,point);assert run(changed,v)==[False]*2,target
            # Benefit and merit are distinct descriptions even when coextensive.
            changed=fixture(('r5yt','r5yu'),q.replace(B,G),True);v,_=response_model(changed,holder,point);assert run(changed,v)==[False]*2
    # A current member's earlier response is ruled out independently of membership.
    q='q[t[c[k r5yt['+scope('first')+']]['+z('holder')+' '+z('response')+' '+z('actor')+']]['+z('past')+']].'
    d=fixture(('r5yt',),q,True);v,_=response_model(d,'holder','past');v['h256o']=lambda *a:True;assert run(d,v)==[False]
    return dict(cases=rows,direct_and_dequoted_scopes_match=True,all_response_settings_kept=True,
        before_anchor_and_dead_speaker_rejected=True,unknown_rejected=True,
        boundary='Only r5yp interior uses a native function with an exact-argument truth boundary here. Its actual gratitude/praise composition is pinned by reports/grateful-regard-v1.json; population, time and quotation execute natively.')

def merit_model(d,ground=True,first=True,last=True):
    v,saved=base(d);v['zground']=lambda a,p:ground and (a,p)==('actor','now')
    def criterion(a,r,g,p,side,flag):return flag and (a,p)==('actor','now') and identity(r)==saved[side] and identity(g)==(0,dict(kind='function_ref',symbol='zgrounded'))
    v.update(zcriterion=lambda *a:criterion(*a,'first',first),zlastcriterion=lambda *a:criterion(*a,'last',last))
    return v,saved
@lru_cache(None)
def merit_checks():
    tail='q[t[c[k r5yy['+z('reference')+' '+MERIT+']]['+z('actor')+']]['+z('now')+']].'
    d=fixture(('r5yu','r5yy'),SAVE+tail);rows=[]
    for bits in product((False,True),repeat=3):
        v,_=merit_model(d,*bits);got=run(d,v);assert got==[True]*2+[all(bits)],(bits,got)
        for n in ('dg','g3','h26nf','h26nt','h26nu','h26nv','h26nr','h26ns','zbenefitstate'):assert v[n] is unknown
        rows.append(dict(ground=bits[0],first=bits[1],last=bits[2],result=got[-1]))
    for old,new in ((FIRST,'l['+STANDARD+'][]'),(LAST,'l['+STANDARD+'][]'),(B,G),(G,B),
            (z('lastgroup'),z('firstgroup')),(z('lastepoch'),z('firstepoch'))):
        changed=fixture(('r5yu','r5yy'),SAVE+tail.replace(old,new));v,_=merit_model(changed)
        v['zbenefitstate']=v['zground'] # Coextensive descriptions still have different content identities.
        assert run(changed,v)==[True]*2+[False],(old,new)
    changed=fixture(('r5yu','r5yy'),SAVE+tail.replace(']['+z('now')+']].',']['+z('later')+']].'))
    v,_=merit_model(changed);assert run(changed,v)==[True]*2+[False]
    for name in (*names('first'),*names('last')):
        v,_=merit_model(d)
        if name in SCENES:v['zrefpick']=lambda p,*codes:codes[SCENES.index('outside' if p==name else p)]
        else:v['znamepick']=lambda p,*codes:codes[DOMAIN.index('other' if p==name else p)]
        assert run(d,v)==[True]*2+[False],name
    for n in ('zground','zcriterion','zlastcriterion'):
        v,_=merit_model(d);v[n]=unknown;rejects(d,v)
        v,_=merit_model(d);old=v[n];v[n]=lambda a,*rest:old('other',*rest);assert run(d,v)==[True]*2+[False]
    return dict(eight_cases=rows,both_nonempty_criteria_required=True,all_closed_names_checked=True,
        distinct_benefit_and_merit_codes_kept=True,actual_gratitude_and_praise_not_executed=True,
        boundary='Criteria check exact same target, response, merit and present point. Substantive merit and the source choice of normative criteria remain open.')

@lru_cache(None)
def integration_checks():
    prince=' '.join([z('actor')]*8+[z('reference')])
    q=SAVE+'q[t[c[k r5yz['+z('actor')+' '+z('reference')+' '+MERIT+']]['+z('actor')+']]['+z('now')+']].'
    q+='q[t[k r5y2['+prince+' '+MERIT+']]['+z('now')+']].'
    d=fixture(('r5yu','r5yz','r5y2'),q,integration_boundary=True);rows=[]
    for qualified,ability,first,last in product((False,True),repeat=4):
        v,_=merit_model(d,True,first,last)
        v.update(zqualified=lambda p,s:qualified and (p,s)==('actor','now'),zability=lambda p,s:ability and (p,s)==('actor','now'))
        got=run(d,v);assert got==[True]*2+[ability and first and last,not qualified or (ability and first and last)]
        rows.append(dict(qualified=qualified,ability=ability,first=first,last=last,result=got[-2:]))
    return dict(sixteen_cases=rows,same_actor_and_present_point=True,qualification_existence_not_inferred=True,
        boundary='Only the unchanged r5xj qualification and r5xv ability have native truth-boundary bodies here. Their native evidence is preserved in the parent report chain; scopes, norms and quantification execute natively.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('von der dankbaren');end=u['text'].index(' als derjenige')
    return dict(status='complete_population_scopes_and_nonfactive_grateful_response_dependency',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,evidence=[dict(path=SOURCES[1],url='https://www.dwds.de/wb/dwb/nachwelt',retrieved='2026-10-23',
            observation='第一義の未来の人類・来たる世代とWelt/Mitweltとの対照を補助に使う。第二義の血縁の子孫へ狭めない。')],
        unresolved=['最初の政府側の解放と良心の全事項の自由という具体的功績・恩恵の同じ出来事への束縛',
            '本文の全設定・称揚適合の全基準・名称評価の独立した著者帰属・sondern・一文全体と後続'],
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
    # Same merit body/parameter roles; the response code and criterion type alone gain rank 1.
    original=deepcopy(c.entries['r5yw']['declaration']);original['name']='ro5'
    def lower(x):
        if isinstance(x,list):return [lower(v) for v in x]
        if isinstance(x,dict):return {k:(0 if k=='rank' and v==1 else lower(v)) for k,v in x.items()}
        return x
    old=deepcopy(c.entries['ro5']['declaration'])
    # Normalizing absent rank 0 avoids relying on how the parser spells that default.
    def explicit_zero(x):
        if isinstance(x,list):return [explicit_zero(v) for v in x]
        if isinstance(x,dict):
            result={k:explicit_zero(v) for k,v in x.items()}
            if 'rank' in result and result['rank']==0:result.pop('rank')
            return result
        return x
    assert explicit_zero(lower(original))==explicit_zero(old)
    assert c.entries['ro5']['declaration']['parameters'][1]['sort'].get('rank',0)==0
    source=(ROOT/LIBRARY).read_text(encoding='utf-8')
    try:parse(source.replace('r b[p r5yt]','r[p r5yt]'))
    except (ValueError,TypeError):pass
    else:raise AssertionError('Grateful response quotation lost required rank')
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=0,new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,parent_meanings_preserved=True,
        rank_one_response_required=True,old_rank_zero_merit_unchanged=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('population',population_checks),('response',response_checks),('merit',merit_checks),('integration',integration_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_world_posterity.py','scripts/check_world_posterity.py','tests/test_world_posterity.py',
        'scripts/compose_qualified_prince_frame.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='complete_population_scopes_and_two_grateful_deserved_responses_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
