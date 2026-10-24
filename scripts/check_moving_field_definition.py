"""Check signed probe response, common theory, conditional claim and source."""
from functools import lru_cache
from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_moving_trip_geometry import NUM
from scripts.check_vacuum_field_domain import setup as base_setup,RS,PS,TAU,AXES,POINTS
from scripts.compose_moving_field_definition import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,PRIMITIVES,MEANINGS,WITNESSES,build

DOC='docs/moving-field-definition-v1.md';SOURCE='data/einstein-moving-field-definition-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p908-0.jpg')
PRIORS=tuple(f'data/einstein-field-transformation-application-u{n:04d}-review-v1.json' for n in range(156,161))
DEPENDENCIES=('reports/field-transformation-application-v1.json','reports/first-principle-v1.json','reports/vacuum-field-domain-v1.json','reports/vacuum-equation-assumption-v1.json','reports/electric-action-v1.json','reports/field-equations-v1.json')
CONSTANTS={'ra':'frame','zbm':'moving','ta':'length','rb':'duration','ri':'context','rd':'author','eirf':'paper','zno':'scope','zny':'application','eispr':'previous','eispx':'display','eispy':'explanation','eispv':'electricname','eispw':'magneticname','zor':'electric','eisps':'pole','eispp':'process','eisk3':'principlename','eispf':'lawname','znu':'law','znv':'history','znw':'left','znx':'right',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'charge','poleunit','force','electricunit','magneticunit','a','b','other')))
SITUATIONS=('context','other')
RESP=dict(kind='function',parameters=[PS,RS],result=PS)

def substitute(node,name,term):
    if isinstance(node,list):return [substitute(x,name,term) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==name:return deepcopy(term)
    return {k:substitute(x,name,term) for k,x in node.items()}

def diagnostic(node,mode):
    if isinstance(node,list):return [diagnostic(x,mode) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind') in ('exists','forall'):
        if mode=='witness':return {**node,'sort':'individual','body':diagnostic(node['body'],mode)}
        symbols=('jmfpointa','jmfpointb') if node.get('sort')==PS else ('jmfnegative','jmfzero','jmfpositive') if node.get('sort')==RS else ()
        if mode=='sample' and symbols:
            terms=[diagnostic(substitute(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[])),mode) for n in symbols]
            joined=terms[-1]
            for term in reversed(terms[:-1]):joined=dict(kind='or' if node['kind']=='exists' else 'and',arguments=[term,joined])
            return joined
    return {k:diagnostic(x,mode) for k,x in node.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'ejts':{'ejtr'},'ejtt':{'ejts'},'ejtu':{'ejtt'} if mode=='witness' else set(),'ejtv':{'ejtu','ejsm','s5y'},'ejtw':{'ejtv'},'ejtx':{'ejtu','ejs3'},'ejty':{'ejtu','ejs3'},'ejt2':{'eiok','eiom'},'eion':{'eiok','eiom'},'ejt3':{'eiok','ejs6','ejtw'},'ejt4':{'ejt2','ejt3'},'ejt5':{'ejs6','ejtw'}}.get(name,set())
    if name=='ejts':bounds.add('ejsl')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode in ('sample','witness'):
        doc=diagnostic(doc,mode)
        if mode=='witness':
            for d in doc['declarations']:
                if d['name']=='ejtt':d['parameters']=['individual']*len(WITNESSES)+['situation']
        else:doc['declarations'][:0]=[dict(kind='primitive',name=n,parameters=[],result=s) for n,s in [('jmfpointa',PS),('jmfpointb',PS),('jmfnegative',RS),('jmfzero',RS),('jmfpositive',RS)]]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmfa'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=900000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup():
    s=base_setup();c,r=s['c'],s['r'];point=lambda values:FunctionValue(('individual',),RS,lambda a:c(dict(zip(AXES,values)).get(a,0)))
    def field(offset):
        return FunctionValue(('individual',),TAU,lambda axis:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(offset+AXES.index(axis)+sum((i+1)*r(x) for i,x in enumerate(xs)) if axis in AXES[:3] else 0)))
    electric,magnetic=field(1),field(5)
    def response(f,conversion,axis=None,at=None,strength=None,shift=None):
        def atpoint(p,a):
            coords=[r(p(n)) for n in AXES];pos=tuple(coords)
            if shift is not None:coords[shift]+=1
            vals=[conversion*r(a)*r(f(n)(*[c(x) for x in coords]))+(n==axis and (at is None or pos==at) and (strength is None or r(a)==strength)) for n in AXES[:3]]
            return point(vals+[0])
        return FunctionValue((PS,RS),PS,atpoint)
    er,mr=response(electric,2),response(magnetic,3);base_norm=s['norm']
    def norm(xs):
        def one(x):
            if isinstance(x,FunctionValue) and x.parameters==(PS,RS):return ('response',tuple(r(x(p,c(a))(axis)) for p in s['points'] for a in (-1,0,1) for axis in AXES[:3]))
            return base_norm((x,))[0]
        return tuple(one(x) for x in xs)
    rel=lambda rows:lambda *xs:norm(xs) in rows
    m=s['m']|{'znr':lambda:electric,'zns':lambda:magnetic,'znt':lambda:s['fields'][4],'tc':lambda:c(2),'jmfpointa':lambda:s['points'][0],'jmfpointb':lambda:s['points'][1],**{n:lambda a=a:c(a) for n,a in [('jmfnegative',-1),('jmfzero',0),('jmfpositive',1)]}}
    s.update(m=m,electric=electric,magnetic=magnetic,er=er,mr=mr,response=response,point=point,norm=norm,rel=rel)
    return s

@lru_cache(None)
def response_checks():
    s=setup();c=s['c'];m=s['m'];field=s['electric'];response=s['er'];count=0
    for p,amount in product(s['points'][:2],(-2,0,3)):
        args=[field,response,c(2),p,c(amount)];assert run('ejtq',args,m);count+=1
        for axis in AXES[:3]:
            bad=args.copy();bad[1]=s['response'](field,2,axis=axis);assert not run('ejtq',bad,m);count+=1
    for slot in range(4):
        assert not run('ejtq',[field,s['response'](field,2,shift=slot),c(2),s['points'][0],c(1)],m);count+=1
    for factor in (0,-1,3):
        assert not run('ejtq',[field,response,c(factor),s['points'][0],c(1)],m);count+=1
    args=[field,response,c(2),s['fields'][4]];assert run('ejtr',args,m,'sample');count+=1
    for pos,axis,amount in product(POINTS[:2],AXES[:3],(-1,0,1)):
        bad=args.copy();bad[1]=s['response'](field,2,axis,pos,amount);assert not run('ejtr',bad,m,'sample');count+=1
    outside=args.copy();outside[1]=s['response'](field,2,'x',POINTS[2]);assert run('ejtr',outside,m,'sample');count+=1
    empty=args.copy();empty[3]=s['region'](set());assert not run('ejtr',empty,m,'sample');count+=1
    unknowns(lambda mm:run('ejtq',[field,response,c(2),s['points'][0],c(1)],mm),m,('sca','ba'))
    try:run('ejtr',args,m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All coordinates and real strengths silently sampled')
    return dict(cases=count,positive_negative_zero_and_all_components=True,all_four_coordinates_shared=True,whole_region_and_all_strengths_retained=True,native_full_domain_refused=True)

@lru_cache(None)
def calibration_checks():
    s=setup();m=s['m'];norm=s['norm'];rel=s['rel'];reg=s['fields'][4]
    args=['electric','moving','length','duration','charge','force',reg,'context',s['er'],'electricunit',s['c'](2),s['electric']]
    rows={'ejsl':{('moving','length','duration','context')},'eispt':{norm(args[:9])},'eispu':{norm(('electric','charge','electricunit','force',s['c'](2),'context'))},'eirn':{norm(('moving',s['electric'],'electricunit','context'))},'ejtr':{norm((s['electric'],s['er'],s['c'](2),reg))}}
    m|={n:rel(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('ejts',args,mm),m,rows,norm)
    pair=['charge','poleunit','electricunit','magneticunit','force',s['c'](2),s['c'](3),s['er'],s['mr'],'context']
    magnetic=['pole','moving','length','duration','poleunit','force',reg,'context',s['mr'],'magneticunit',s['c'](3),s['magnetic']]
    rows2={'ejts':{norm(args),norm(magnetic)},'znn':{norm(('moving',s['electric'],s['magnetic'],reg,'context'))},'eispn':{norm(('process','moving',s['electric'],s['magnetic'],reg,'context'))}}
    mm=s['m']|{n:rel(rs) for n,rs in rows2.items()};count+=perturb(lambda mm:run('ejtt',pair,mm),mm,rows2,norm)
    assert not run('ejtt',pair,mm|{'eisps':lambda:'electric'});count+=1
    # Only quantifier wiring is retagged here. Native typed body is checked above.
    targets=[('a',)*9,('b',)*9]+[tuple('b' if i==j else 'a' for i in range(9)) for j in range(9)]+[tuple('a' if i==j else 'b' for i in range(9)) for j in range(9)]
    for target in targets:
        model={'ejtt':lambda *xs,target=target:xs==(*target,'context')}
        assert run('ejtu',['context'],model,'witness',('a','b'));count+=1
        assert not run('ejtu',['other'],model,'witness',('a','b'));count+=1
    assert not run('ejtu',['context'],{'ejtt':lambda *xs:False},'witness',('a','b'));count+=1
    unknowns(lambda model:run('ejtu',['context'],model,'witness',('a','b')),{'ejtt':lambda *xs:True},('ejtt',))
    return dict(cases=count,two_distinct_probe_kinds_and_all_reference_slots=True,same_process_two_fields_and_common_force_unit=True,all_nine_witness_slots_distinguished=True,no_actual_probe_body_required=True)

@lru_cache(None)
def content_checks():
    s=setup();norm=s['norm'];rel=s['rel'];reg=s['fields'][4]
    rows={'ejtu':{('context',)},'ejsm':{norm(('moving','length','duration','context',reg))},'s5y':{norm((s['electric'],s['magnetic'],reg,s['c'](2)))}}
    count=perturb(lambda mm:run('ejtv',['context'],mm),s['m']|{n:rel(rs) for n,rs in rows.items()},rows,norm)
    for name,field in (('ejtx',s['electric']),('ejty',s['magnetic'])):
        rs={'ejtu':{('context',)},'ejs3':{norm((field,field,reg))}}
        count+=perturb(lambda mm:run(name,[field,'context'],mm),s['m']|{n:rel(rows) for n,rows in rs.items()},rs,norm)
    for old,new in product((False,True),repeat=2):
        m={'ejs6':lambda old=old:Content(SITUATIONS,(old,not old)),'ejtw':lambda new=new:Content(SITUATIONS,(new,not new))}
        assert run('ejt5',[],m)==(not old or new);count+=1
    return dict(cases=count,current_vacuum_fields_light_and_notation_bound=True,conditional_not_unconditional_truth=True)

@lru_cache(None)
def principle_checks():
    count=0;pairs=tuple(product(('a','b'),repeat=2))
    for selected,saved in product(product((False,True),repeat=4),repeat=2):
        eligible={(*pair,'context') for pair,on in zip(pairs,selected) if on}
        holds={(*pair,'a','context') for pair,on in zip(pairs,saved) if on}
        m={'eiok':relation(eligible),'eiom':relation(holds)}
        expected=any(selected) and all(not a or b for a,b in zip(selected,saved))
        assert run('ejt2',['a','context'],m,domain=('a','b'))==expected;count+=1
        assert run('eion',[],m,domain=('a','b'))==expected;count+=1
    for first,second in product(('a','b'),repeat=2):
        m={'ejt2':relation({(first,'context')}),'ejt3':relation({(second,'context')})}
        assert run('ejt4',[],m,domain=('a','b'))==(first==second);count+=1
    rows={'eiok':{('frame','moving','context')},'eisle':{('a','law','context')},'eislf':{('a','history','context')},'vh':{('history','frame','left','context'),('history','moving','right','context')},'vi':{('law','left','context'),('law','right','context')}}
    m={n:relation(rs) for n,rs in rows.items()}|{n:lambda:Content(SITUATIONS,(True,False)) for n in ('ejs6','ejtw')}
    count+=perturb(lambda mm:run('ejt3',['a','context'],mm),m,rows)
    for old,new,left,right in product((False,True),repeat=4):
        mm=m|{'ejs6':lambda old=old:Content(SITUATIONS,(old,False)),'ejtw':lambda new=new:Content(SITUATIONS,(new,False)),'vi':lambda law,rep,ctx,left=left,right=right:left if rep=='left' else right}
        assert run('ejt3',['a','context'],mm)==(old==left and new==right);count+=1
    unknowns(lambda mm:run('ejt4',[],mm,domain=('a','b')),{'ejt2':lambda *xs:True,'ejt3':lambda *xs:True},('ejt2','ejt3'))
    return dict(cases=count,full_current_principle_body_preserved=True,same_theory_not_two_separate_witnesses=True,same_law_history_representations_and_content_equivalence=True)

@lru_cache(None)
def presentation_checks():
    rows={'zc':{('application','author','ejt4','ejt5','scope','context')},'eisch':{('principlename','eion','scope','context'),('lawname','ejtw','scope','context')},'eispi':{('electricname','ejtx','paper','context'),('magneticname','ejty','paper','context')},'eisox':{('display','ejtw','context')},'uf':{('author','application','explanation','context'),('author','explanation','display','context')},'ue':{('application','explanation','context'),('explanation','display','context')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('ejt6',[],mm),m,rows)
    assert run('ejt6',[],m|{n:forbidden for n in ('ejt4','ejt5','ejtw','ejtx','ejty','eion')});count+=1
    for symbol,target in (('eispy','application'),('eispx','application'),('eispx','explanation')):
        assert not run('ejt6',[],{n:lambda *xs:True for n in rows}|{symbol:lambda target=target:target});count+=1
    outer={'eir3':{('application','author','paper','ejt7','context')},'ue':{('previous','application','context')}}
    count+=perturb(lambda mm:run('ejua',[],mm),{n:relation(rs) for n,rs in outer.items()},outer)
    return dict(cases=count,conditional_requirement_explanation_display_and_author=True,quoted_fields_and_principle_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][160:162]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[table[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    for mid,form in zip(('M0294','M0295','M0296','M0297','M0298','M0299'),('k','K','k','(X′,Y′,Z′)','(L′,M′,N′)','k')):assert ''.join(ET.fromstring(table[mid]['mathml']).itertext())==form
    tree=ET.fromstring(table['M0300']['mathml']);ns='{http://www.w3.org/1998/Math/MathML}'
    order=[tuple(''.join(x.itertext()) for x in f) for f in tree.iter(ns+'mfrac') if ''.join(f[0].itertext()).startswith('∂')]
    expected=[('∂X′','∂τ'),('∂N′','∂η'),('∂M′','∂ζ'),('∂L′','∂τ'),('∂Y′','∂ζ'),('∂Z′','∂η'),('∂Y′','∂τ'),('∂L′','∂ζ'),('∂N′','∂ξ'),('∂M′','∂τ'),('∂Z′','∂ξ'),('∂X′','∂ζ'),('∂Z′','∂τ'),('∂M′','∂ξ'),('∂L′','∂η'),('∂N′','∂τ'),('∂X′','∂η'),('∂Y′','∂ξ')]
    assert order==expected and sum(''.join(x.itertext())=='=' for x in tree.iter(ns+'mo'))==6
    assert sum(''.join(x.itertext())=='−' for x in tree.iter(ns+'mo'))==6
    return dict(version='einstein-moving-field-definition-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['908'],segments=segments,source_derivative_order=order,observations=['原刊908頁の一文を、原理が要求するwennの条件、d. h.の説明、ponderomotorische Wirkungenによる二場の定義、六式まで連続して照合した。','原刊は二列配置で電気側・磁気側の式が交互に並ぶ。固定MathMLの18偏微分の軸・プライム・差の符号を照合し、Noemaのs5yは同じ六条件を電気側三式・磁気側三式の順で結ぶ。','磁気的質量は符号付き試験磁極という明示した読みを採る。慣性質量や運動電荷への力だけに置換しない。後続の二組の式の比較と共通係数は別の主張として残す。'],reading_support=dict(url='https://en.wikisource.org/wiki/A_Treatise_on_Electricity_and_Magnetism/Part_III/Chapter_I',sections=['374','376','377'],use='符号付き磁極強度と局所的な極の理想化の語義。原文の追加法則として採用しない。'),source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,*FACSIMILES)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p in PRIORS:
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[153])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'ejs6','ejsm','ejs3','eiok','eiom','eion','eibr','eispn','eispi','s5y','zc'}<=names
    assert not names&{'s6k','s6l','sac2','sad2','sae2','saf2','saw'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=2,new_quantity_kind=1,new_reference_individuals=4,replaced_statement=INDEX,other_357_statements_and_prior_judgments_preserved=True,moving_fields_not_identified_with_calculated_mixtures=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('response',response_checks),('calibration',calibration_checks),('content',content_checks),('principle',principle_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_field_equations','compose_material_relative_frame','compose_solid_sphere_geometry','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_vacuum_field_domain','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_moving_field_definition.py','scripts/check_moving_field_definition.py','tests/test_moving_field_definition.py',*(f'scripts/{n}.py' for n in helpers)}
    segments=[]
    for s in source_record()['segments']:
        row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation');segments.append(row)
        for m in s['math']:segments.append(dict(row,math_id=m['id'],math_sha256=m['sha256']))
    return dict(status='moving_fields_probe_definition_and_relativity_requirement_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0161–u0162の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
