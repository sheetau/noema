"""Check actual praise separately from two nonperformed deserved responses."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Message
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_merit_praise import ROOT,LIBRARY,BASIS,GROUND,GROUND_NAME,MESSAGE,RESPONSE,STANDARD,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/merit-praise-v1.md';READING='data/merit-praise-reading-v1.json';REPORT='reports/merit-praise-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v196.json'
PRIORS=('reports/prince-conclusion-v1.json','reports/qualified-prince-frame-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/merit-praise-v1/dwb-preisen.html','artifacts/merit-praise-v1/dwb-dankbar.html')
DOMAIN=('speaker','subject','act','hearer','groupone','grouptwo','eraone','eratwo','audience','other')
SCENES=('reference','candidate','now','future')
def z(n):return 'k z'+n+'[]'
G='r[p zgrounded]';GN='r['+G+']'
def scope(side):return ' '.join(z(n) for n in ('group'+side,'era'+side,'audience','reference','candidate'))+' '+G
def code(side):return 'k r5x7['+' '.join('r['+z(n)+']' for n in ('group'+side,'era'+side,'audience','reference','candidate'))+' '+GN+']'
CODES={'first':code('one'),'last':code('two'),'message':'k r5x4['+G+']'}
SAVE=''.join('q[k zsave'+n+'['+c+']].' for n,c in CODES.items())
FIRST_LIST='l['+STANDARD+'][k zstandard[]]';LAST_LIST='l['+STANDARD+'][k zlaststandard[]]'
MERIT=' '.join(z(n) for n in ('groupone','grouptwo','eraone','eratwo','audience','candidate'))+' '+G+' '+FIRST_LIST+' '+LAST_LIST

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def identity(c):return c.rank,json.loads(c.syntax)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=False):
    d=deepcopy(catalog().document)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zground[a d] c.d zgrounded[person a] e[b point[k zground[v person v point]]].d zothergrounded[person a] e[b point[k zground[v person v point]]].'
    extra+='r zsavefirst['+RESPONSE+'] c.r zsavelast['+RESPONSE+'] c.r zsavemessage['+MESSAGE+'] c.'
    for n,primitive in (('zstandard','zcriterion'),('zlaststandard','zlastcriterion')):
        extra+='r '+primitive+'[a '+RESPONSE+' '+GROUND+' d] c.d '+n+'[] '+STANDARD+'[i[subject a response '+RESPONSE+' ground '+GROUND+'][b point[k '+primitive+'[v subject v response v ground v point]]]].'
    if boundaries:
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
        zground=lambda p,s:(p,s)==('subject','now'),zability=lambda p,s:(p,s)==('subject','now'),zqualified=lambda p,s:(p,s)==('subject','now'))
    for n in CODES:v['zsave'+n]=lambda c,n=n:saved.update({n:identity(c)}) is None
    return v,saved

def actual_model(d):
    v,saved=base(d);ground=(0,{'kind':'function_ref','symbol':'zgrounded'})
    v.update(aa=lambda p:p in ('speaker','subject','hearer'),dg=lambda a,s:(a,s)==('act','now'),
        f3=lambda p,a,s:(p,a,s)==('speaker','act','now'),
        h246c=lambda g,p,r:r=='reference' and (g,p) in (('audience','hearer'),('groupone','speaker'),('grouptwo','other')),
        h26ab=lambda e,r,c,s:(r,c)==('reference','candidate') and (e,s) in (('eraone','now'),('eratwo','future')),
        f2=lambda a,h,p,m,s:(a,h,p,identity(m),s)==('act','hearer','subject',saved['message'],'now'),
        h26nr=lambda p,a,t,g,s:(p,a,t,identity(g),s)==('speaker','act','subject',ground,'now'),
        h26ns=lambda p,a,t,g,r,s:(p,a,t,identity(g),r,s)==('speaker','act','subject',ground,'reference','now'))
    return v,saved

@lru_cache(None)
def praise_checks():
    direct='k r5x6['+scope('one')+']';quoted='s['+code('one')+']'
    q=SAVE+''.join('q[t[c['+f+']['+z('speaker')+' '+z('act')+' '+z('subject')+']]['+z('now')+']].' for f in (direct,quoted))
    d=fixture(('r5x4','r5x6','r5x7'),q);v,_=actual_model(d);assert run(d,v)==[True]*5
    rows={}
    for n in ('aa','dg','f3','f2','h26nr','h26ns','h26ab'):
        v,_=actual_model(d);v[n]=lambda *a:False;assert run(d,v)==[True]*3+[False]*2;rows[n]=False
    for missing in ('audience','groupone'):
        v,_=actual_model(d);old=v['h246c'];v['h246c']=lambda g,*a:g!=missing and old(g,*a)
        assert run(d,v)==[True]*3+[False]*2;rows['empty_'+missing]=False
    for name,count in (('h26nr',5),('h26ns',6)):
        for pos in range(count):
            v,_=actual_model(d);old=v[name]
            def wrong(*a):
                if pos==3:return False # A different aspect, even if coextensive.
                changed=list(a);changed[pos]='other' if pos<3 else 'future';return old(*changed)
            v[name]=wrong;assert run(d,v)==[True]*3+[False]*2,(name,pos)
    for name in ('dg','f3','f2','h26nr','h26ns','h246c','h26ab'):
        v,_=actual_model(d);v[name]=unknown;rejects(d,v)
    # Neither expressed praise nor quotation executes the merit as a fact.
    v,_=actual_model(d);v['zground']=unknown;assert run(d,v)==[True]*5
    message=fixture(('r5x4',),'l[c[s[k r5x4['+G+']]]['+z('subject')+']].')
    v,_=base(message);v['zground']=lambda *a:False;m=run(message,v)[0]
    assert isinstance(m,Message) and m.force=='assert' and not any(m.content.values)
    return dict(direct_and_dequoted_actual_responses_match=True,missing_components=rows,
        all_eleven_appraisal_arguments_bound=True,false_merit_can_be_asserted_or_praised=True,
        neutral_report_without_positive_expression_rejected=True,weak_expression_rejected=True,unknown_rejected=True)

def merit_model(d,ground=True,first=True,last=True):
    v,saved=base(d);v['zground']=lambda p,s:ground and (p,s)==('subject','now')
    def criterion(p,r,g,s,side,flag):
        return flag and (p,s)==('subject','now') and identity(r)==saved[side] and identity(g)==(0,{'kind':'function_ref','symbol':'zgrounded'})
    v.update(zcriterion=lambda *a:criterion(*a,'first',first),zlastcriterion=lambda *a:criterion(*a,'last',last))
    return v,saved

@lru_cache(None)
def merit_checks():
    q=SAVE+'q[t[c[k r5yc['+z('reference')+' '+MERIT+']]['+z('subject')+']]['+z('now')+']].'
    d=fixture(('r5x4','r5x7','r5yc'),q);rows=[]
    for bits in product((False,True),repeat=3):
        v,_=merit_model(d,*bits);got=run(d,v);assert got==[True]*3+[all(bits)],(bits,got)
        for n in ('dg','f2','h26nr','h26ns','h246c','h26ab'):assert v[n] is unknown
        rows.append(dict(ground=bits[0],first=bits[1],last=bits[2],both=got[-1]))
    for source,replacement in ((FIRST_LIST,'l['+STANDARD+'][]'),(LAST_LIST,'l['+STANDARD+'][]'),
        (' '+z('grouptwo')+' ', ' '+z('groupone')+' '),(' '+z('eratwo')+' ',' '+z('eraone')+' '),(G,'r[p zothergrounded]')):
        changed=fixture(('r5x4','r5x7','r5yc'),SAVE+q[len(SAVE):].replace(source,replacement));v,_=merit_model(changed)
        assert run(changed,v)==[True]*3+[False],(source,replacement)
    for name in ('zground','zcriterion','zlastcriterion'):
        v,_=merit_model(d);v[name]=unknown;rejects(d,v)
    for name in ('zground','zcriterion','zlastcriterion'):
        v,_=merit_model(d);old=v[name];v[name]=lambda p,*a:old('other',*a);assert run(d,v)==[True]*3+[False]
    for name in ('groupone','grouptwo','eraone','eratwo','audience','reference','candidate'):
        v,_=merit_model(d)
        if name in SCENES:v['zrefpick']=lambda p,*codes:codes[SCENES.index('future' if p==name else p)]
        else:v['znamepick']=lambda p,*codes:codes[DOMAIN.index('other' if p==name else p)]
        assert run(d,v)==[True]*3+[False],name
    return dict(eight_ground_and_two_scope_cases=rows,both_scopes_required=True,empty_criteria_and_same_scope_rejected=True,
        same_ground_description_not_just_same_truth=True,all_seven_scope_names_checked=True,
        no_actual_praise_future_event_or_world_content_execution=True,unknown_rejected=True,
        boundary='Criteria in this fixture check exact response/ground bindings. Their substantive normative adequacy and gratitude are still unresolved source inputs.')

@lru_cache(None)
def integration_checks():
    # Only this quantifier test replaces already separately checked profiles.
    prince=' '.join([z('subject')]*8+[z('reference')])
    q=SAVE+'q[t[k r5ye['+prince+' '+MERIT+']]['+z('now')+']].'
    d=fixture(('r5x4','r5x7','r5ye'),q,True);rows=[]
    for qualified,ability,first,last in product((False,True),repeat=4):
        v,_=merit_model(d,True,first,last)
        v.update(zqualified=lambda p,s:qualified and (p,s)==('subject','now'),zability=lambda p,s:ability and (p,s)==('subject','now'))
        got=run(d,v);assert got==[True]*3+[not qualified or (ability and first and last)]
        rows.append(dict(qualified=qualified,ability=ability,first=first,last=last,result=got[-1]))
    return dict(sixteen_shared_conclusion_cases=rows,qualification_existence_not_required=True,
        boundary='The unchanged qualification r5xj and ability r5xv use native function bodies with primitive truth boundaries only here. Their native evidence is pinned in the prior reports.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('von der dankbaren');end=u['text'].index(', der zuerst')
    return dict(status='praise_and_both_scoped_deserving_dependency',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,evidence=[dict(path=SOURCES[1],url='https://www.dwds.de/wb/dwb/preisen',retrieved='2026-10-23',observation='第一のpreisen、語義2の高い評価と称揚、2bのals等による対象の性質・資格の提示。実際の受け手の評価上昇を必要条件には採らない。'),
            dict(path=SOURCES[2],url='https://www.dwds.de/wb/dwb/dankbar',retrieved='2026-10-23',observation='人格的態度と表出の用法。感謝の詳細は未構成であり、心情を発話の実演だけにしないための補助。')],
        unresolved=['感謝の恩恵認識・相手への好意的承認、現在と後代の全人物範囲と時代順序','最初の政府側の解放と良心の全事項の自由という具体的功績','功績に対する称揚適合の全基準、本文束縛・著者帰属・一文全体・後続'],
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
    assert c.entries['r5x7']['declaration']['result'].get('rank',0)==0
    assert c.entries['ro5']['declaration']==parents()[0].entries['ro5']['declaration']
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,rank_zero_response_reuses_ro5=True,parent_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('praise',praise_checks),('merit',merit_checks),('integration',integration_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_merit_praise.py','scripts/check_merit_praise.py','tests/test_merit_praise.py',
        'scripts/compose_qualified_prince_frame.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='emphatic_praise_and_two_scoped_deserving_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
