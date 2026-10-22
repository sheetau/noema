"""Check shared-person qualifications and nonfactive rank-seven discourse."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_qualified_prince_frame import ROOT,LIBRARY,BASIS,PROFILE,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts import check_self_report_dignity as self_report
from scripts import check_designation_rejection as rejection

INDEX=rejection.INDEX;INVENTORY=rejection.INVENTORY;REPORT='reports/qualified-prince-frame-v1.json'
READING='data/qualified-prince-frame-reading-v1.json';DOC='docs/qualified-prince-frame-v1.md'
GRAMMAR='artifacts/qualified-prince-frame-v1/ids-focus-reading.json'
COLLATION='data/eighth-paragraph-source-reading-v1.json'
SOURCES=(*rejection.prior.SOURCES,'artifacts/eighth-paragraph-source-v1/page-492.jpg',GRAMMAR)
PRIORS=('reports/self-report-dignity-v1.json','reports/designation-rejection-v1.json','reports/haughty-designation-v1.json','reports/single-ruler-v1.json')
DOMAIN=rejection.DOMAIN;SCENES=rejection.SCENES;z=rejection.z;identity=rejection.identity
NAMES=('work','otherwork',*self_report.SNAMES);ARGS=' '.join(z(n) for n in NAMES)
REF=z('reference');NOW=z('now');ACTOR=z('actor')
PCODES=dict(head='k r5xn[r['+z('role')+'] r['+z('community')+']]',
    premise='k r5xo['+' '.join('r['+z(n)+']' for n in self_report.SNAMES)+']',
    refusal='k r5xp['+' '.join('r['+z(n)+']' for n in ('work','otherwork',*rejection.FNAMES))+']',
    qualified='k r5xq['+' '.join('r['+z(n)+']' for n in NAMES)+']')
SAVE=''.join('q[k zsave'+key+'['+value+']].' for key,value in PCODES.items())
LOW_SAVE='q[k zsaveappraisal['+self_report.CODE6+']].q[k zsaveuse['+rejection.USE+']].q[k zsavepattern['+rejection.CODE+']].'
DISC=' '.join(z(n) for n in ('person','otherperson','event','actor','group'))+' '+ARGS+' '+z('otherpoint')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);boundary_declarations=[]
    for x in d['declarations']:
        if x['name'] in boundaries:
            # Keep a native Noema function. Python callables are not values of
            # a returned Noema function sort; only the truth boundary is native.
            symbol='zbound'+x['name']
            patch=parse('p:r '+symbol+'[a d] c.d zprofile[] h[a] e[i[actor a][b point[k '+symbol+'[v actor v point]]]].')
            boundary_declarations.append(patch['declarations'][0]);x['body']=patch['declarations'][1]['body']
    d['declarations']=boundary_declarations+d['declarations']
    d.update(declarations=closure(d,roots),statements=[])
    extra=self_report.prior.EXTRA+self_report.prior.PROVIDERS+self_report.PROVIDERS
    extra+='r zsaveuse['+rejection.USE_CODE+'] c.r zsavepattern['+rejection.PATTERN+'] c.'
    extra+=''.join('r zsave'+n+'['+PROFILE+'] c.' for n in PCODES)
    extra+='r zconclusion[a d] c.d zresult[] h[a] e[i[actor a][b point[k zconclusion[v actor v point]]]].'
    prefix=parse('p:'+extra);replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e','h26nh')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in replacements]+[replacements.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v,saved=self_report.base(d)
    for key in PCODES:v['zsave'+key]=lambda code,key=key:saved.update({key:identity(code)}) is None
    v.update(zsaveuse=lambda code:saved.update(use=identity(code)) is None,zsavepattern=lambda code:saved.update(pattern=identity(code)) is None,
        h246c=lambda g,p,r:g in ('group','other','otherwork') and p in ('person','otherperson') and r=='reference',
        h26ni=lambda actor,code,point:(actor,identity(code),point)==('actor',saved['appraisal'],'now'),
        h26nk=lambda label,code,c,r:(label,identity(code),c,r)==('work',saved['pattern'],'community','reference'),
        h244j=lambda actor,event,code,b,sign,point:(actor,event,identity(code),normalized(b),sign,point)==('actor','event',saved['use'],('actor','work','otherwork'),False,'now'),
        cf=lambda p,role,point:(p,role,point)==('actor','role','now'),
        hzwn=lambda p,role,point:(p,role,point)==('actor','role','now'),
        hzxf=lambda p,role,c,point:(p,role,c,point)==('actor','role','community','now'),
        h234d=lambda role,c,point:(role,c,point)==('role','community','now'),
        h234e=lambda *a:False,h234f=lambda role,c,point:(role,c,point)==('role','community','now'),
        zconclusion=lambda p,point:(p,point)==('actor','now'))
    return v,saved

@lru_cache(None)
def qualification_checks():
    q=LOW_SAVE+SAVE+'q[t[c[k r5xj['+ARGS+']]['+ACTOR+']]['+NOW+']].q[t[c[s['+PCODES['qualified']+']]['+ACTOR+']]['+NOW+']].'
    d=fixture(('r5wn','r5wz','r5wu','r5xn','r5xo','r5xp','r5xq','r5xj'),q);rows=[]
    for ruler,appraised,refused in product((False,True),repeat=3):
        v,_=base(d);v['cf']=lambda *a:ruler and a==('actor','role','now')
        judgment=v['h26ni'];stance=v['h244j'];v['h26ni']=lambda *a:appraised and judgment(*a);v['h244j']=lambda *a:refused and stance(*a)
        got=run(d,v);want=ruler and appraised and refused;assert got==[True]*7+[want,want],(ruler,appraised,refused,got)
        assert v['h26nf'] is unknown and v['h26ne'] is unknown and v['h26ng'] is unknown
        rows.append(dict(ruler=ruler,appraised=appraised,refused=refused,result=got[-2:]))
    for name,fn in (('hzwn',lambda *a:a==('person','role','now')),('hzxf',lambda *a:a==('actor','role','other','now')),
        ('h234f',lambda *a:a==('other','community','now')),('h26ni',lambda *a:a[0]=='person'),('h244j',lambda *a:a[0]=='person')):
        v,_=base(d);v[name]=fn;assert run(d,v)[-2:]==[False,False],name
    for n in ('cf','hzwn','hzxf','h26ni','h244j'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(eight_qualification_combinations=rows,native_composed_and_dequoted_profiles_match=True,
        same_actor_office_community=True,inner_judgment_duty_policy_and_self_report_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def generality_checks():
    # All fixed individual arguments must also belong to the small model's
    # domain. Their identity is tested by the separate native/frame checks.
    small_args=' '.join([ACTOR]*(len(NAMES)-1)+[REF])
    q=''.join('q[t[k '+n+'['+small_args+(' k zresult[]' if n!='r5xl' else '')+']]['+NOW+']].' for n in ('r5xk','r5xl','r5xm'))
    d=fixture(('r5xk','r5xl','r5xm'),q,('r5xi','r5wq','r5w5'));people=('actor','person','otherperson');rows={}
    cases={'none':(set(),set(),set(),set()),'satisfied':({'actor'},)*4,
        'counterexample':({'actor'},{'actor'},{'actor'},set()),'split_subjects':({'actor'},{'person'},{'otherperson'},set()),
        'unqualified_failure':({'actor'}, {'actor'}, {'actor'}, {'actor','person'}),
        'two_qualified_one_failure':({'actor','person'},)*3+({'actor'},)}
    for name,(heads,appraised,refused,conclusions) in cases.items():
        v,_=base(d)
        v.update(zboundr5xi=lambda p,s:p in heads and s=='now',zboundr5wq=lambda p,s:p in appraised and s=='now',
            zboundr5w5=lambda p,s:p in refused and s=='now',zconclusion=lambda p,s:p in conclusions and s=='now')
        qualified=heads&appraised&refused;got=run(d,v,people);assert got==[qualified<=conclusions,bool(qualified),bool(qualified-conclusions)],(name,got);rows[name]=got
    return dict(cases=rows,common_person_for_all_qualifiers=True,universal_existence_counterexample_distinct=True,
        validation_boundary='Only this quantifier test replaces three separately evaluated profiles; native composition is checked in qualification_checks.')

def discourse_model(d):
    v,saved=base(d)
    for n in ('cf','hzwn','hzxf','h234d','h234e','h234f','h26ni','h26nf','h26ne','h26ng','h26nk','h244j'):v[n]=unknown
    v.update(h26nn=lambda node,author,scope,b,p,c:(node,author,scope,identity(b),identity(p),c)==('person','actor','group',saved['head'],saved['premise'],'otherpoint'),
        h26no=lambda node,author,scope,b,p,c:(node,author,scope,identity(b),identity(p),c)==('otherperson','actor','group',saved['head'],saved['refusal'],'otherpoint'),
        h26np=lambda node,author,scope,clause,b,f,item,c:(node,author,scope,clause,identity(b),identity(f),item,c)==('event','actor','group','otherperson',saved['head'],saved['refusal'],'work','otherpoint'),
        ud=lambda author,premises,result,c:(author,result,c)==('actor','otherperson','otherpoint') and tuple(p for p in DOMAIN if premises(p))==('person',),
        ue=lambda first,second,c:(first,second,c)==('person','otherperson','otherpoint'))
    return v,saved

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5xn','r5xo','r5xp','r5xq','r5xu'),SAVE+'q[k r5xu['+DISC+']].');rows={}
    v,_=discourse_model(d);assert run(d,v)==[True]*5
    for n in ('h26nn','h26no','h26np','ud','ue'):
        v,_=discourse_model(d);v[n]=lambda *a:False;assert run(d,v)==[True]*4+[False];rows[n]=False
    for name in ('h26nn','h26no','h26np'):
        size=8 if name=='h26np' else 6
        for pos in range(size):
            v,saved=discourse_model(d)
            def changed(*a):
                key=[identity(x) if hasattr(x,'syntax') else x for x in a]
                want=['person' if name=='h26nn' else 'otherperson','actor','group',saved['head'],saved['premise' if name=='h26nn' else 'refusal'],'otherpoint']
                if name=='h26np':want=['event','actor','group','otherperson',saved['head'],saved['refusal'],'work','otherpoint']
                want[pos]='wrong';return key==want
            v[name]=changed;assert run(d,v)==[True]*4+[False],(name,pos)
    for n in ('h26nn','h26no','h26np','ud','ue'):
        v,_=discourse_model(d);v[n]=unknown;rejects(d,v)
    return dict(missing_components_rejected=rows,all_twenty_scoped_presentation_arguments_checked=True,
        same_author_scope_bound_person_profiles_and_clause=True,no_world_content_execution=True,unknown_rejected=True)

@lru_cache(None)
def reference_checks():
    d=fixture(('r5xn','r5xo','r5xp','r5xq','r5xu'),SAVE+'q[k r5xu['+DISC+']].');rows={}
    for name in NAMES:
        v,_=discourse_model(d)
        if name=='reference':v['zrefpick']=lambda point,*codes:codes[2] if point=='reference' else codes[SCENES.index(point)]
        else:v['znamepick']=lambda item,*codes:codes[DOMAIN.index('person' if item==name else item)]
        got=run(d,v);assert got==[True]*4+[False],(name,got);rows[name]=False
    for n in ('znamepick','zrefpick'):
        v,_=discourse_model(d);v[n]=unknown;rejects(d,v)
    return dict(all_nine_references_checked=rows,wrong_closed_name_not_silently_adopted=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');end=u['text'].index(': ist selbst');last=u['text'].index('. ')+1
    return dict(status='qualified_prince_and_scoped_consequence_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,end],text=u['text'][:end]),
        sentence_context=dict(range=[0,last],text=u['text'][:last]),interpretation=LIMITS,
        evidence=[dict(path=SOURCES[0],url='https://korpora.org/kant/aa08/040.html',observation='同一人物の二つの関係節とalso/selbstの位置。'),
            dict(path=COLLATION,observation='原刊491–492頁の第一文照合。原刊と固定本文のコロン、後続第四文のist/sei差を保持。'),
            dict(path=GRAMMAR,url='https://grammis.ids-mannheim.de/systematische-grammatik/408',observation='検索で取得したIDS本文ではselbstを焦点助詞に含める。直接ページ取得は失敗したため、保存記録は検索取得の範囲と明記する。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['全設定と談話箇所の本文束縛・名称評価の独立した著者帰属','sondernとist selbst aufgeklärt、具体的な啓蒙と称賛内容','最初の政府側の解放・良心事項の理性使用と一文全体・後続'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,COLLATION,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[2].document['statements'])==112
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for r in reviews:assert r['selection']==selection_binding(parents()[2],[s['index'] for s in r['selection']['statements']])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    source=(ROOT/LIBRARY).read_text(encoding='utf-8')
    for target in ('r5wq','r5xj'):
        try:parse(source.replace('r h[p '+target+']','r g[p '+target+']'))
        except (ValueError,TypeError):pass
        else:raise AssertionError('Rank-seven quotation lowered: '+target)
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        preserved_whole_unit_reviews=17,new_verified_characters=0,compact_full_v2_roundtrips=True,rank_seven_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('qualifications',qualification_checks),('generality',generality_checks),('discourse',discourse_checks),('references',reference_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,COLLATION,*SOURCES,*PRIORS,
        'scripts/compose_qualified_prince_frame.py','scripts/check_qualified_prince_frame.py','tests/test_qualified_prince_frame.py',
        'scripts/compose_self_report_dignity.py','scripts/check_self_report_dignity.py','scripts/check_designation_rejection.py',
        'scripts/check_religious_freedom_policy.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='qualified_prince_scoped_consequence_and_object_focus_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
