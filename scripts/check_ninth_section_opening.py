"""Check the complete ninth-section opening and preserve earlier judgments."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_convective_foundation_reading as prior
from scripts.check_problem_series_reduction import collapse
from scripts.check_clock_site_time import relation,perturb
from scripts.compose_ninth_section_opening import *

old=prior.old;forbidden=old.forbidden
DOC='docs/ninth-section-opening-v1.md';SOURCE='data/einstein-ninth-section-opening-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p916-0.jpg'
DEPENDENCIES=('reports/convective-foundation-reading-v1.json','reports/carrier-field-correspondence-v1.json','reports/convective-charge-setting-v1.json')
CONSTANTS={'ra':'frame','ta':'lengthunit','rb':'timeunit','tb':'speedunit','eiswb':'densityname','eiswc':'velocityname','eiswf':'intro','eiswg':'curls','eiswh':'where','eiswi':'divergence','eiswj':'explanation','eiswk':'foundation','eiswl':'heading','eisv6':'section','rd':'author','eirf':'paper','ri':'case','eispb':'part','eisvu':'previous','eispf':'designation'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),'inquiry','a','b','other','wrong']))
BOUNDS={'ekzq':{'ekxg'},'ekyy':{'ejsn','ejsj','ekzq','ekxk','ekxl'},'ekyz':{'ekyy'},'ekza':{'ejsj','s5u','seme'},'ekzb':{'ejsj','s5t','semd'},'ekzc':{'ekyz','ekyq'},'ekzd':{'ekyz','ekza'},'ekze':{'ekyz','ekzb'},'ekzf':set(),'ekzg':set(),'ekzk':{'ekyz','ekzf','ekzg','ekzc','ekzd','ekze','ekyx'},'ekzm':{'ekzl'},'ekzn':{'ekyy','ekyq'},'ekzo':{'ekzn','eiu2'},'ekzp':{'ekzo'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','bj','szi','sjd'}|BOUNDS[root]:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root);extras={}
    if root=='ekyy' and mode=='sample':
        start,bs,call=prior.chain(d['body'],'ekzq',7);target=next(x for x in doc['declarations'] if x['name']=='ekzq')
        start.clear();start.update(kind='call',symbol='jnowitness',arguments=call['arguments'][:len(SETTING)+1])
        doc['declarations'].append(dict(kind='primitive',name='jnowitness',parameters=target['parameters'][:len(SETTING)+1],result='truth'))
    if mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('forall','exists'):
                names=('jnopa','jnopb') if node['sort']==old.PS else ('jnoja','jnojb') if node['sort']==old.sort(JET) else None
                if names:
                    extras.update({n:node['sort'] for n in names})
                    return dict(kind='and' if node['kind']=='forall' else 'or',arguments=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in names])
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in extras.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jnoarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jnocontext',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jnocontext',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jnocapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jnocapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,values,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(slots)==len(values);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in (old.CONSTANTS|CONSTANTS).items()}|{'jnocontext':lambda:'case','jnocapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    out=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else out

def setup():
    by,m,c,r,parts,points,oldkey,mask=prior.setup()
    axis=lambda a:('x','y','z','t').index(a)+1 if a in ('x','y','z','t') else 0
    by['electricfield']=old.fn(old.sort(FIELD),lambda a:old.fn(old.sort(TAU),lambda x,y,z,t:c(axis(a)*(1+r(x)+2*r(y)+3*r(z)+4*r(t)))))
    by['electricjet']=old.fn(old.sort(JET),lambda a,b:c(100*axis(a)+axis(b)))
    by['magneticjet']=old.fn(old.sort(JET),lambda a,b:c(1000+100*axis(a)+axis(b)))
    def key(x):
        if isinstance(x,(list,tuple)):return tuple(key(y) for y in x)
        if isinstance(x,FunctionValue) and x.parameters==tuple(old.sort(TAU)['parameters']) and x.result==old.RS:
            return tuple(r(x(*(p(a) for a in ('x','y','z','t')))) for p in points)
        return oldkey(x)
    m|={'jnopa':lambda:points[0],'jnopb':lambda:points[1],'jnoja':lambda:by['electricjet'],'jnojb':lambda:by['magneticjet']}
    return by,m,c,r,parts,points,key,mask

def contrasts(root,values,m,rows,key):
    good=m|{n:old.rel(rs,key) for n,rs in rows.items()};assert run(root,values,good),root;cases=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,values,good|{n:old.rel(rs-{row},key)}),(root,n,'missing');cases+=1
            for i in range(len(row)):
                bad=list(row);bad[i]='wrong'
                assert not run(root,values,good|{n:old.rel((rs-{row})|{tuple(bad)},key)}),(root,n,i);cases+=1
        prior.prior.prior.reject(lambda:run(root,values,good|{n:forbidden}),True);cases+=1
    return cases

@lru_cache(None)
def physical_checks():
    by,m,c,r,parts,points,key,mask=setup();cases=0
    coords=lambda p:[p(a) for a in ('x','y','z','t')]
    loc=by|dict(density=by['chargefield'](*coords(by['point'])),normalized=by['densityfield'](*coords(by['point'])))
    cases+=contrasts('ekzq',[by[n] for n,t in PHYSICAL_LOCAL],m,{'ekxg':{key([loc[n] for n,t in NORMAL])}},key)
    rows={n:{key([by[x] for x,t in fs])} for n,fs in [('ejsn',FIELD_SETTING),('ekxl',FLOW)]};rows|={'jnowitness':set(),'ekxk':set()}
    for p in points:
        loc=by|dict(point=p,normalized=by['densityfield'](*coords(p)))
        rows['jnowitness'].add(key([*(by[n] for n,t in SETTING),p]));rows['ekxk'].add(key([loc[n] for n,t in SUPPORT]))
    cases+=contrasts('ekyy',[by[n] for n,t in SETTING],m|{'ejsj':lambda *xs:True},rows,key)
    good=m|{n:old.rel(rs,key) for n,rs in rows.items()}|{'ejsj':lambda *xs:True}
    assert not run('ekyy',[by[n] for n,t in SETTING],good|{'ejsj':lambda *xs:False});cases+=1
    rows={'ekyy':{key([by[n] for n,t in SETTING])},'eiscc':{key([by['frame'],by['lengthunit'],by['timeunit'],'speedunit','case'])}}
    cases+=contrasts('ekyz',[by[n] for n,t in GLOBAL],m,rows,key)
    good=m|{n:lambda *xs:True for n in rows}
    for n,x in [('frame','other'),('lengthunit','other'),('timeunit','other'),('light',c(7)),('electricconversion',c(2)),('magneticconversion',c(1))]:
        loc=by|{n:x};assert not run('ekyz',[loc[n] for n,t in GLOBAL],good);cases+=1
    for root,field in [('ekzf','densityfield'),('ekzg','velocityfield')]:
        assert key(run(root,[by[n] for n,t in GLOBAL],m))==key(by[field]);cases+=1
    return dict(cases=cases,physical_density_and_velocity_share_setting=True,source_calibration_and_field_selectors_bound=True,attachment_not_required_by_first_sentence=True)

@lru_cache(None)
def equation_checks():
    by,m,c,r,parts,points,key,mask=setup();cases=0;curl={'s5u':set(),'seme':set()};div={'s5t':set(),'semd':set()}
    for p in points:
        coords=[p(a) for a in ('x','y','z','t')];rho=by['densityfield'](*coords)
        vel=old.fn(old.PS,lambda axis,coords=coords:by['velocityfield'](axis)(*coords))
        curl['s5u'].add(key([by['electricfield'],by['magneticfield'],by['region'],p,by['electricjet'],by['magneticjet']]))
        curl['seme'].add(key([by['light'],rho,vel,by['electricjet'],by['magneticjet']]))
        for a in ('x','y','z'):div['s5t'].add(key([by['electricfield'](a),by['region'],p,a,by['electricjet'](a,a)]))
        div['semd'].add(key([by['electricjet'],rho]))
    for root,rows in [('ekza',curl),('ekzb',div)]:
        cases+=contrasts(root,[by[n] for n,t in GLOBAL],m|{'ejsj':lambda *xs:True},rows,key)
        good=m|{n:old.rel(rs,key) for n,rs in rows.items()}|{'ejsj':lambda *xs:True}
        assert not run(root,[by[n] for n,t in GLOBAL],good|{'ejsj':lambda *xs:False});cases+=1
        prior.prior.prior.reject(lambda:run(root,[by[n] for n,t in GLOBAL],good,'native'));cases+=1
    return dict(cases=cases,six_curls_and_electric_divergence_have_separate_displays=True,same_fields_points_axes_density_velocity_and_jets=True,all_point_domain_not_silently_enumerated=True)

def lifted(doc,root,pivot,count,kind,subtree=None,context=None):
    """Keep one actual binder and expose the others; no exponential tuples."""
    doc=deepcopy(doc);d=next(d for d in doc['declarations'] if d['name']==root)
    if subtree is not None:d['body']=deepcopy(subtree[0]);d['parameters']=deepcopy(subtree[1]);d['result']='truth'
    elif d['result']=='content':
        bind=d['body'];d['parameters']=[dict(name=bind['variable'],sort='situation')];d['body']=bind['body'];d['result']='truth'
    body=d['body'];kept=None;names=[]
    for i in range(count):
        assert body['kind']==kind
        names.append(body['variable'])
        if i==pivot:kept={k:body[k] for k in ('kind','variable','sort')}
        else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
        body=body['body']
    d['body']=kept|dict(body=body);doc=collapse(doc);d=next(d for d in doc['declarations'] if d['name']==root)
    slots=['jnoslot'+number_word(i) for i in range(len(d['parameters']))]
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=p['sort']) for n,p in zip(slots,d['parameters'])]
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive')
    return doc,d,slots,names[pivot],collapse(body)

@lru_cache(None)
def binder_checks():
    cases=0
    # The seven local material witnesses and the nineteen projected heading inputs.
    for root,target,count in [('ekyy','ekzq',7),('ekzn','ekyq',len(PROJECTED))]:
        doc=boundary(root);src=next(d for d in doc['declarations'] if d['name']==root);sub=None
        if root=='ekyy':
            start,bs,call=prior.chain(src['body'],target,count);td=next(d for d in doc['declarations'] if d['name']==target);width=len(call['arguments'])-count
            sub=(start,[dict(name=x['name'],sort=t) for x,t in zip(call['arguments'][:width],td['parameters'][:width])])
        for pivot in range(count):
            f,d,slots,var,body=lifted(doc,root,pivot,count,'exists',sub)
            call=next(x for x in prior.walk(body) if x.get('kind')=='call' and x.get('symbol')==target)
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}|{var:'b'}
            def evaluate(e,want):
                row=tuple(want[x['name']] for x in call['arguments'])
                m={x['name']:(lambda *xs:True) if x['result']=='truth' else (lambda:'a') for x in f['declarations'] if x['kind']=='primitive'}
                m|={n:lambda x=e[p['name']]:x for n,p in zip(slots,d['parameters'])};m[target]=lambda *xs:xs==row
                return evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=m,max_steps=20000)[0]['value']
            assert evaluate(env,env);assert not evaluate(env,env|{var:'unavailable'});cases+=2
            for p in d['parameters']:
                changed=env|{p['name']:'other' if p['sort']=='situation' else 'b'}
                assert evaluate(changed,changed);assert not evaluate(changed,env);cases+=2
    # Every source-law universal binds exactly the same hypothesis/conclusion tuple.
    for root,law in [('ekzc','ekyq'),('ekzd','ekza'),('ekze','ekzb')]:
        for pivot in range(len(CASES)):
            f,d,slots,var,body=lifted(boundary(root),root,pivot,len(CASES),'forall')
            calls={x['symbol']:x for x in prior.walk(body) if x.get('kind')=='call'}
            assert calls['ekyz']['arguments']==calls[law]['arguments']
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            def evaluate(selected,allowed):
                rows=lambda picks:{tuple((env|{var:pick})[x['name']] for x in calls[law]['arguments']) for pick in picks}
                hs,ls=rows(selected),rows(allowed)
                m={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ekyz':lambda *xs:xs in hs,law:lambda *xs:xs in ls}
                return evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=m,max_steps=20000)[0]['value']
            for selected,allowed,want in [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]:assert evaluate(selected,allowed)==want;cases+=1
    return dict(cases=cases,all_seven_local_and_nineteen_projection_slots_checked=True,all_31_universal_slots_in_three_contents_checked=True,same_tuple_under_hypothesis_and_law=True)

@lru_cache(None)
def presentation_checks():
    rows={'ug':{('intro','author','ekzc','section','case')},'eisox':{('curls','ekzd','case'),('divergence','ekze','case')},'eiswd':{('densityname','ekyz','ekzf','paper','section','case')},'eiswe':{('velocityname','ekyz','ekzg','paper','section','case')},'uh':{('foundation','author','ekyx','section','case')},'eiswm':{('foundation','author','intro','ekzc','paper','case')},'uf':{('author',a,b,'case') for a,b in [('intro','curls'),('curls','where'),('where','divergence'),('divergence','explanation')]},'ue':{(a,b,'case') for a,b in [('intro','curls'),('curls','where'),('where','divergence'),('divergence','explanation'),('explanation','foundation')]}}
    good={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda m:run('ekzk',[],m),good,rows)
    nodes=['eiswf','eiswg','eiswh','eiswi','eiswj','eiswk']
    for i,a in enumerate(nodes):
        for b in nodes[i+1:]:assert not run('ekzk',[],{n:lambda *xs:True for n in rows}|{a:lambda b=b:CONSTANTS[b]});cases+=1
    assert run('ekzk',[],good|{n:forbidden for n in ('ekyz','ekyq','ekza','ekzb','ekyx')});cases+=1
    outer={'eir3':{('intro','author','paper','ekzl','case')},'ue':{('heading','intro','case')}}
    cases+=perturb(lambda m:run('ekzm',[],m),{n:relation(rs) for n,rs in outer.items()},outer)
    topic={'eispd':{('inquiry','designation','ekzn','eiu2','case')}}
    cases+=perturb(lambda m:run('ekzo',['inquiry','case'],m),{n:relation(rs) for n,rs in topic.items()},topic)
    heading={'eisdv':{('heading','section','part','paper',Fraction(2),Fraction(9),'case')},'eisdw':{('heading','section','ekzo','case')},'ue':{('previous','heading','case'),('heading','intro','case')}}
    cases+=perturb(lambda m:run('ekzp',[],m),{n:relation(rs) for n,rs in heading.items()},heading)
    return dict(cases=cases,starting_premise_notation_displays_and_conditional_foundation_connected=True,same_prior_equations_in_anaphora=True,all_six_nodes_ordered_and_distinct=True,ninth_heading_scope_and_topic_retained=True,quoted_physics_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][226:232]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[math[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    ns='{http://www.w3.org/1998/Math/MathML}';tree=ET.fromstring(math['M0383']['mathml'])
    fracs=[tuple(''.join(n.itertext()) for n in f) for f in tree.iter(ns+'mfrac')]
    expected=[('∂X','∂t'),('∂N','∂y'),('∂M','∂z'),('∂L','∂t'),('∂Y','∂z'),('∂Z','∂y'),('∂Y','∂t'),('∂L','∂z'),('∂N','∂x'),('∂M','∂t'),('∂Z','∂x'),('∂X','∂z'),('∂Z','∂t'),('∂M','∂x'),('∂L','∂y'),('∂N','∂t'),('∂X','∂y'),('∂Y','∂x')]
    assert fracs.count(('1','V'))==6 and [f for f in fracs if f!=('1','V')]==expected
    ops=[''.join(n.itertext()) for n in tree.iter(ns+'mo')];assert ops.count('=')==ops.count('−')==6
    assert [''.join(x.itertext()) for x in tree.iter(ns+'msub')]==['ux','uy','uz']
    for mid,want in [('M0384','ϱ=∂X∂x+∂Y∂y+∂Z∂z'),('M0385','4π'),('M0386','ux,uy,uz')]:assert ''.join(ET.fromstring(math[mid]['mathml']).itertext())==want
    assert inv['units'][238]['text'].startswith('§ 10.')
    return dict(version='einstein-ninth-section-opening-reading-v1',reviewer='assistant_visual_and_text_review',pages=['916'],segments=segments,derivative_order=[list(x) for x in expected],division=dict(level=2,ordinal=9,parent='eispb',first='einstein-1905:u0227',last='einstein-1905:u0238',next_boundary='einstein-1905:u0239'),observations=['原刊916頁上部で第九節見出し、出発点の導入、三行二列の六式、wobei、ρの発散式、4π密度と三速度成分の意味説明、条件付き基礎の第二文を連続して視認した。','六式には両側とも1/Vがあり、電気側には各ux/uy/uzと同じρの積が加わる。三対角微分の和をρとする別表示に続き、ρが電荷密度の4π倍であると説明する。','Denkt man sichの条件、unveränderlich、kleine/starre、括弧内の二名称、diese Gleichungen、elektromagnetische Grundlage、Lorentzschenと二主題を保持する。後続の変換後表示は今回の原系と区別する。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC,'data/historical-carrier-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==410 and after.document['statements'][:INDEX]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[407])==selection_binding(before,[407]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries'][:-2]==json.loads(read('data/convective-foundation-reading-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    hypothesis={d['name'] for d in extract_document(core(),roots=['ekyz'],statement_indices=[]).document['declarations']}
    assert not hypothesis&{'semh','semf','seme','semd','ekx3','ekyc','ekyl','eiah'}
    assert not set(selection_binding(after,[INDEX,INDEX+1])['dependencies'])&{'semf','semi','ekbw','ekbx','ekby','ekbz'}
    assert len(PROJECTED)==19 and len(CASES)==31
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=3,new_reference_constants=9,added_statements=[408,409],all_408_prior_statements_and_meanings_preserved=True,first_sentence_has_no_attachment_or_law_in_antecedent=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('physical',physical_checks),('equation',equation_checks),('binder',binder_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_ninth_section_opening.py','scripts/check_ninth_section_opening.py','tests/test_ninth_section_opening.py','scripts/check_convective_foundation_reading.py','scripts/check_problem_series_reduction.py','scripts/check_clock_site_time.py'}
    return dict(status='ninth_section_opening_connected_for_whole_unit_review',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
