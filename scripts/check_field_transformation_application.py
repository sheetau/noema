"""Check same-process records, inverse arguments and the author's rewrite claim."""
from functools import lru_cache
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
from scripts.check_vacuum_field_domain import setup as field_setup,RS,TAU
from scripts.check_field_transform import OPS
from scripts.check_angle_composition import model_arithmetic
from scripts.check_parallel_composition import transform
from scripts.check_tau_differential import ConstructedCuts
from scripts.compose_field_transformation_application import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/field-transformation-application-v1.md';SOURCE='data/einstein-field-transformation-application-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=tuple('artifacts/written-facsimiles-v1/'+n for n in ('einstein-1905-unlp.pdf','einstein-1905-unlp-p907-0.jpg','einstein-1905-unlp-p908-0.jpg'))
PRIORS=tuple(f'data/einstein-vacuum-equation-assumption-u{n:04d}-review-v1.json' for n in range(153,156))
DEPENDENCIES=('reports/vacuum-equation-assumption-v1.json','reports/field-transform-v1.json','reports/final-transform-claim-v1.json','reports/event-coordinate-task-v1.json','reports/frame-motion-v1.json','reports/kinematic-foundation-v1.json')
CONSTANTS={'ra':'frame','zbm':'moving','zb6':'context','ri':'discourse','rd':'author','eirf':'paper','eisms':'section','zno':'scope','znq':'application','eispm':'previous','eispp':'process','eispq':'display','eispr':'beta','yn':'x','yo':'y','yp':'z','zc7':'t'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','lab','own','event','other')))
SITUATIONS=('context','discourse','other')


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=set(OPS)
    bounds|={'ejte':{'eig3','ejsy'},'ejtf':{'eiyx'},'ejtg':{'ejtf'},'ejth':{'ejte','eivz','ejtf'},'ejtj':{'ejth','ejtg','eiyz','eiy2','eiyy','ejti'},'ejtk':{'ejs6','ejeh','ejtj'}}.get(name,set())
    if name=='ejti' and mode=='isolated':bounds.add('ssn')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jfta'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots


def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    def missing(symbol):
        def reject(*xs):raise ValueError('Unknown field-transformation input: '+symbol)
        return reject
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],missing(d['name'])) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=800000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def provenance_checks():
    s=field_setup();f=s['fields'];norm=s['norm'];rel=s['relation']
    rows={'eig3':{('process','context')},'ejsy':{('context',)},'eispn':{norm(('process','frame',f[-2],f[-1],f[4],'context'))}}
    m={n:rel(rs) for n,rs in rows.items()}|{'znl':lambda:f[-2],'znm':lambda:f[-1],'znk':lambda:f[4]}
    count=perturb(lambda mm:run('ejte',['process','context'],mm),m,rows,norm)
    count+=perturb(lambda mm:run('ejtf',['process','event','lab','frame','context'],mm),{'eispo':relation({('event','process','context')}),'eiyx':relation({('event','lab','frame','context')})},{'eispo':{('event','process','context')},'eiyx':{('event','lab','frame','context')}})
    for left,right in product(('a','b'),repeat=2):
        rows2={('a',left,'a','a','context'),('a',right,'b','b','context')}
        assert run('ejtg',['a','a','b','context'],{'ejtf':relation(rows2),'ra':lambda:'a','zbm':lambda:'b'},domain=('a','b'))==(left==right);count+=1
    unknowns(lambda mm:run('ejtg',['a','a','b','context'],mm,domain=('a','b')),{'ejtf':lambda *xs:True,'ra':lambda:'a','zbm':lambda:'b'},('ejtf',))
    return dict(cases=count,same_process_fields_region_and_context=True,same_event_for_both_records=True)


@lru_cache(None)
def coverage_checks():
    count=0;domain=('a','b')
    for membership in product((False,True),repeat=2):
        members={e for e,yes in zip(domain,membership) if yes}
        for records in product((False,True),repeat=4):
            available={(e,fr) for (e,fr),yes in zip(product(domain,domain),records) if yes}
            m={'ra':lambda:'a','zbm':lambda:'b','ejte':relation({('a','context')}),'eivz':relation({('context',)}),'eispo':lambda e,p,c,members=members:(p,c)==('a','context') and e in members,'ejtf':lambda p,e,r,fr,c,available=available:(p,c)==('a','context') and r=='a' and (e,fr) in available}
            expected=bool(members) and all((e,fr) in available for e in members for fr in domain)
            assert run('ejth',['a','context'],m,domain=domain)==expected;count+=1
    rows={'ejte':{('a','context')},'eivz':{('context',)},'eispo':{('a','a','context')},'ejtf':{('a','a','a','a','context'),('a','a','b','b','context')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'ra':lambda:'a','zbm':lambda:'b'};count+=perturb(lambda mm:run('ejth',['a','context'],mm,domain=domain),m,rows)
    assert not run('ejth',['a','other'],{n:lambda *xs:True for n in rows}|{'ra':lambda:'a','zbm':lambda:'b'},domain=domain);count+=1
    pairs={('a','b'),('b','a')};rows={'ejth':{('a','context')},'ejtg':{('a',a,b,'context') for a,b in pairs},'eiyz':{('a',),('b',)},'eiy2':{('a',),('b',)},'eiyy':pairs,'ejti':pairs}
    m={n:relation(rs) for n,rs in rows.items()}
    # Removing a selected pair narrows the diagnostic range, so test range selection separately.
    constrained={n:rs for n,rs in rows.items() if n!='ejtg'}
    count+=perturb(lambda mm:run('ejtj',['a','context'],mm,domain=domain),m,constrained)
    for pair in pairs:
        assert not run('ejtj',['a','context'],m|{'ejti':relation(pairs-{pair})},domain=domain);count+=1
    assert run('ejtj',['a','context'],m|{'ejti':relation(pairs|{('a','a')})},domain=domain);count+=1
    unknowns(lambda mm:run('ejtj',['a','context'],mm,domain=domain),m,('ejtg',))
    return dict(cases=count,all_members_have_both_frames=True,all_same_event_pairs_not_only_successful_pairs=True,two_value_binding_domain=True)


def numerical_model(old=(2,1,-1,1),speed=3):
    cuts=ConstructedCuts();m={};model_arithmetic(cuts,m);c=cuts.make;r=cuts.read
    m['szi']=lambda condition,left,right:left if condition else right
    new=transform(tuple(map(Q,old)),Q(speed),Q(5));table={'lab':tuple(map(Q,old)),'own':new}
    m|={'tc':lambda:c(5),'zb7':lambda:c(speed),'zc5':lambda rec:rec in table,'zc6':lambda rec,axis:c(table[rec][('x','y','z','t').index(axis)]),'znk':lambda:FunctionValue(tuple([dict(kind='function',parameters=['number'],result='truth')]*4),'truth',lambda x,y,z,t:r(x)>0 and r(t)<4)}
    return cuts,m,table


@lru_cache(None)
def inverse_checks():
    count=0
    for old in ((2,1,-1,1),(1,-2,3,0),(3,2,1,-1)):
        cuts,m,table=numerical_model(old);assert run('ejti',['lab','own'],m);count+=1
        for slot in range(4):
            altered=list(table['own']);altered[slot]+=1
            bad=m|{'zc6':lambda rec,axis,altered=altered:cuts.make((table['lab'] if rec=='lab' else altered)[('x','y','z','t').index(axis)]),'ssn':lambda *xs:True}
            assert not run('ejti',['lab','own'],bad,'isolated');count+=1
    _,m,_=numerical_model((0,1,-1,1));assert not run('ejti',['lab','own'],m);count+=1
    _,m,_=numerical_model((2,1,-1,4));assert not run('ejti',['lab','own'],m);count+=1
    cuts,m,table=numerical_model();unknowns(lambda mm:run('ejti',['lab','own'],mm),m,('zc6',))
    # The new point is generally outside the original numerical region: use its inverse image.
    assert table['own'][0]<0<table['lab'][0]
    field=FunctionValue(('individual',),TAU,lambda role:FunctionValue(tuple([RS]*4),RS,lambda *xs:cuts.make(0)))
    try:run('s6o',[],m|{'znl':lambda:field,'znm':lambda:field})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole transformed field equations silently sampled')
    return dict(cases=count,native_final_equations_and_inverse_four_arguments=True,same_inverse_region_not_unchanged_numerical_region=True,all_four_inverse_slots_distinguished=True,native_full_transformed_domain_refused=True)


@lru_cache(None)
def premise_checks():
    count=0
    for a,b,c in product((False,True),repeat=3):
        m={'ejs6':lambda a=a:Content(SITUATIONS,(a,not a,not a)),'ejeh':lambda b=b:Content(SITUATIONS,(not b,b,not b)),'ejtj':lambda p,s,c=c:c and (p,s)==('process','context')}
        assert run('ejtk',[],m)==(a and b and c);count+=1
    m={'ejs6':lambda:Content(SITUATIONS,(True,False,False)),'ejeh':lambda:Content(SITUATIONS,(False,True,False)),'ejtj':relation({('process','context')})}
    unknowns(lambda mm:run('ejtk',[],mm),m,('ejs6','ejeh','ejtj'))
    return dict(cases=count,prior_assumption_applied_to_same_current_setting=True,final_transformation_and_same_process_required=True)


@lru_cache(None)
def presentation_checks():
    rows={'zd3':{('application','author','ejtk','ejs6','s6o','scope','discourse')},'eisov':{('application','author','section',n,'paper','discourse') for n in ('ejeh','eiy6')},'uh':{('beta','author','spq','scope','discourse')},'eisox':{('display','s6o','discourse')},'uf':{('author','application','display','discourse'),('author','display','beta','discourse')},'ue':{('application','display','discourse'),('display','beta','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('ejtn',[],mm),m,rows)
    assert run('ejtn',[],m|{n:forbidden for n in ('ejs6','ejeh','ejtj','s6o','spq','znl','znm')});count+=1
    for n,x in (('eispq','application'),('eispr','application'),('eispr','display')):
        assert not run('ejtn',[],{n:lambda *xs:True for n in rows}|{n:lambda x=x:x});count+=1
    outer={'eir3':{('application','author','paper','ejto','discourse')},'ue':{('previous','application','discourse')}}
    count+=perturb(lambda mm:run('ejtp',[],mm),{n:relation(rs) for n,rs in outer.items()},outer)
    return dict(cases=count,same_section_three_transform_and_introduced_frame=True,display_six_equations_and_same_beta_supplement=True,rewrite_claim_does_not_execute_or_certify_conclusion=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][155:160]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[table[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    ns='{http://www.w3.org/1998/Math/MathML}';order=[];counts=[]
    for mid in ('M0291','M0292'):
        tree=ET.fromstring(table[mid]['mathml']);counts.append(sum(''.join(x.itertext())=='=' for x in tree.iter(ns+'mo')))
        for f in tree.iter(ns+'mfrac'):
            pair=tuple(''.join(n.itertext()) for n in f)
            if pair[0].startswith('∂'):order.append(pair)
    expected=[('∂X','∂τ'),('∂β(N−vVY)','∂η'),('∂β(M+vVZ)','∂ζ'),('∂β(Y−vVN)','∂τ'),('∂L','∂ζ'),('∂β(N−vVY)','∂ξ'),('∂β(Z+vVM)','∂τ'),('∂β(M+vVZ)','∂ξ'),('∂L','∂η'),('∂L','∂τ'),('∂β(Y−vVN)','∂ζ'),('∂β(Z+vVM)','∂η'),('∂β(M+vVZ)','∂τ'),('∂β(Z+vVM)','∂ξ'),('∂X','∂ζ'),('∂β(N−vVY)','∂τ'),('∂X','∂η'),('∂β(Y−vVN)','∂ξ')]
    assert order==expected and counts==[4,2]
    assert ''.join(ET.fromstring(table['M0290']['mathml']).itertext())=='v'
    beta=ET.fromstring(table['M0293']['mathml']);flat=re.sub(r'\s','',''.join(beta.itertext()))
    assert flat=='β=11−(vV)2.' and len(list(beta.iter(ns+'msqrt')))==1
    return dict(version='einstein-field-transformation-application-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['907','908'],segments=segments,source_derivative_order=order,observations=['原刊907頁で第三節の変換を同じ電磁過程へ適用する導入と四式、908頁冒頭で残る二式とwobei・βまでを一つの文として照合した。','六式の18偏微分の成分・変数・符号、同じv/Vとβの正の平方根を固定MathMLへ照合した。原刊の改頁を内容の分断にしない。','移動系の独立した物理的な場の定義は次のu0161で導入される。この六式の混合成分を先にその測定場と同一視しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,*FACSIMILES)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p in PRIORS:
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[152])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'ejs6','ejeh','eiy6','eivz','eiyx','eig3','eisc3','eibf','eibs','eico','s46','ssn','s6k','s6l','s6m','s5y','spq','zd3','eisov','uh'}<=names
    assert not names&{'s6p','s5z','sae2','saf2'}
    oldreport=json.loads(read('reports/field-transform-v1.json'))
    assert oldreport['status']=='partial_field_transform_with_insufficient_premise_counterexample'
    assert oldreport['finite_refusal']['refused']
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=2,new_reference_individuals=3,replaced_statement=INDEX,other_357_statements_and_prior_judgments_preserved=True,existing_insufficient_premise_counterexample_preserved=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('provenance',provenance_checks),('coverage',coverage_checks),('inverse',inverse_checks),('premise',premise_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_field_equations','compose_material_relative_frame','compose_solid_sphere_geometry','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_vacuum_field_domain','check_field_transform','check_angle_composition','check_parallel_composition','check_tau_differential','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_field_transformation_application.py','scripts/check_field_transformation_application.py','tests/test_field_transformation_application.py',*(f'scripts/{n}.py' for n in helpers)}
    segments=[]
    for s in source_record()['segments']:
        row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation');segments.append(row)
        for m in s['math']:segments.append(dict(row,math_id=m['id'],math_sha256=m['sha256']))
    return dict(status='same_process_coordinate_application_six_equations_and_beta_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0156–u0160の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
