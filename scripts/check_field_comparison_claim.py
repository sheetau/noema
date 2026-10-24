"""Check scoped equivalence, equation form, six-component scale and discourse."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,DescriptionValue,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_moving_trip_geometry import NUM
from scripts.check_vacuum_field_domain import setup as base_setup,sample_points,RS,PS,TAU,AXES,POINTS
from scripts.compose_field_comparison_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,PRIMITIVES,MEANINGS,build

DOC='docs/field-comparison-claim-v1.md';SOURCE='data/einstein-field-comparison-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';CORRECTION='data/field-common-scale-facsimile-v1.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p908-0.jpg')
PRIORS=tuple(f'data/einstein-moving-field-definition-u{n:04d}-review-v1.json' for n in (161,162))
DEPENDENCIES=('reports/moving-field-definition-v1.json','reports/field-transformation-application-v1.json','reports/field-common-scale-v1.json','reports/field-transform-v1.json','reports/parallel-group-claim-v1.json')
CONSTANTS={'ra':'frame','zbm':'moving','ta':'length','rb':'duration','ri':'context','rd':'author','eirf':'paper','zno':'scope','zn2':'result','eispx':'movingdisplay','eispq':'calculateddisplay','eisp2':'first','eisp3':'second','eisp4':'display','eispf':'lawname','eispp':'process',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','other')));SITUATIONS=('context','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'s6k','s6l','s6m','s45'}|{'ejub':{'ejsy','ejtu','ejsm','saj2'},'ejuc':{'ejs6','s6o','ejtw'},'ejue':{'s6o','ejtw'},'ejud':{'ejub','ejuc'},'ejuf':{'ejub','ejue'},'ejuj':{'ejui','ejuh'},'ejug':{'saj2'},'ejuh':{'ejub'},'ejui':{'ejub','ejuc','ejug'},'ejuk':{'ejuf','ejug'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='sample':
        doc=sample_points(doc);doc['declarations'][:0]=[dict(kind='primitive',name=n,parameters=[],result=PS) for n in ('jvfdone','jvfdtwo')]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jfcca'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    return evaluate_document(doc,individuals=DOMAIN,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup(scale=2):
    s=base_setup();c,r=s['c'],s['r'];e,h=s['fields'][-2:];reg=s['fields'][4];oldnorm=s['norm']
    def scaled(f,factor,axis=None,at=None):return FunctionValue(('individual',),TAU,lambda role:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(factor*r(f(role)(*xs))+(role==axis and (at is None or tuple(map(r,xs))==at)))))
    olde,oldh=scaled(e,4),scaled(h,5);newe,newh=scaled(e,scale),scaled(h,scale)
    def norm(xs):return tuple(json.loads(x.syntax).get('symbol') if isinstance(x,DescriptionValue) else oldnorm((x,))[0] for x in xs)
    rel=lambda rows:lambda *xs:norm(xs) in rows
    wanted=norm((c(5),c(3),olde,oldh))
    def transform(result):
        def f(*xs):
            if norm(xs)!=wanted:raise ValueError('Wrong transformation arguments')
            return result
        return f
    def region(*xs):
        if norm(xs)!=norm((c(5),c(3),reg)):raise ValueError('Wrong inverse-region arguments')
        return reg
    m=s['m']|{'tc':lambda:c(5),'zb7':lambda:c(3),'znl':lambda:olde,'znm':lambda:oldh,'znr':lambda:newe,'zns':lambda:newh,'znk':lambda:reg,'znt':lambda:reg,'s6k':transform(e),'s6l':transform(h),'s6m':region,'s45':rel({norm((c(5),c(3)))}),'znz':lambda:FunctionValue((RS,),RS,lambda speed:c(scale) if r(speed)==3 else c(scale+1))}
    s.update(m=m,e=e,h=h,olde=olde,oldh=oldh,newe=newe,newh=newh,norm=norm,rel=rel,scaled=scaled,reg=reg);return s

@lru_cache(None)
def setting_checks():
    s=setup();norm=s['norm'];rel=s['rel'];reg=s['reg'];c=s['c']
    rows={'ejsy':{('context',)},'ejtu':{('context',)},'eispn':{norm(('process','frame',s['olde'],s['oldh'],reg,'context'))},'ejsm':{norm((f,'length','duration','context',reg)) for f in ('frame','moving')},'s45':{norm((c(5),c(3)))},'saj2':{norm((reg,reg))}}
    m=s['m']|{n:rel(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('ejub',[],mm),m,rows,norm)
    assert run('ejub',[],m|{n:forbidden for n in ('s5y','ejs6','s6o','ejtw','sai2','sak2')});count+=1
    return dict(cases=count,same_physical_process_both_fields_and_full_domain=True,no_success_condition_in_comparison_scope=True)

@lru_cache(None)
def equivalence_checks():
    count=0
    for a,b,c in product((False,True),repeat=3):
        m={n:lambda x=x:Content(SITUATIONS,(x,not x)) for n,x in [('ejs6',a),('s6o',b),('ejtw',c)]}
        assert run('ejuc',[],m)==(a==b and a==c);assert run('ejue',[],m)==(b==c);count+=2
    for name,pre,post in [('ejud','ejub','ejuc'),('ejuf','ejub','ejue'),('ejuj','ejui','ejuh')]:
        for selected,truth in product(product((False,True),repeat=2),repeat=2):
            m={pre:lambda selected=selected:Content(SITUATIONS,selected),post:lambda truth=truth:Content(SITUATIONS,truth)}
            assert run(name,[],m)==(any(selected) and all(not a or b for a,b in zip(selected,truth)));count+=1
        unknowns(lambda mm:run(name,[],mm),{pre:lambda:Content(SITUATIONS,(True,True)),post:lambda:Content(SITUATIONS,(True,True))},(pre,post))
    for name,names in [('ejui',('ejub','ejuc','ejug')),('ejuk',('ejuf','ejug'))]:
        for bits in product((False,True),repeat=len(names)):
            m={n:lambda b=b:Content(SITUATIONS,(b,not b)) for n,b in zip(names,bits)};assert run(name,[],m)==all(bits);count+=1
    return dict(cases=count,both_directions_not_one_way=True,nonempty_all_candidate_situations=True,necessity_not_current_truth=True)

@lru_cache(None)
def form_checks():
    s=setup();c=s['c'];norm=s['norm'];rel=s['rel'];reg=s['reg']
    rows={'s45':{norm((c(5),c(3)))},'saj2':{norm((reg,reg))},'eispz':{norm(('calculateddisplay','s5y',s['e'],s['h'],reg,c(5),'context')),norm(('movingdisplay','s5y',s['newe'],s['newh'],reg,c(5),'context'))}}
    m=s['m']|{n:rel(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('ejug',[],mm),m,rows,norm)
    assert run('ejug',[],m|{'s5y':forbidden,'sai2':forbidden});count+=1
    unknowns(lambda mm:run('ejug',[],mm),m,('s6k','s6l','s6m'))
    return dict(cases=count,same_closed_form_all_argument_roles=True,form_does_not_assert_truth_or_proportionality=True)

@lru_cache(None)
def scale_checks():
    count=0
    for scale in (-2,0,2):
        s=setup(scale);m=s['m']|{'ejub':lambda:Content(SITUATIONS,(True,False)),'znn':lambda *xs:True};reg=s['reg']
        assert run('ejuh',[],m,'sample');count+=1
        for which,axis,pos in product(('znr','zns'),AXES[:3],POINTS[:2]):
            f=s['e'] if which=='znr' else s['h'];changed=s['scaled'](f,scale,axis,pos)
            assert not run('ejuh',[],m|{which:lambda changed=changed:changed},'sample');count+=1
        assert not run('ejuh',[],m|{'ejub':lambda:Content(SITUATIONS,(False,True))},'sample');count+=1
        different=s['region']({POINTS[0]});assert not run('ejuh',[],m|{'znt':lambda:different},'sample');count+=1
        outside=s['scaled'](s['e'],scale,'x',POINTS[2]);assert run('ejuh',[],m|{'znr':lambda:outside},'sample');count+=1
        const=m|{'znz':lambda:FunctionValue((RS,),RS,lambda speed:s['c'](scale))};assert run('ejuh',[],const,'sample');count+=1
    try:run('ejuh',[],m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full field-function domain silently sampled')
    return dict(cases=count,same_scale_all_six_components_and_entire_region=True,negative_zero_and_constant_factors_allowed=True,speed_only_argument_and_no_coordinate_factor=True,native_full_domain_refused=True)

@lru_cache(None)
def presentation_checks():
    rows={'zc':{('first','author','ejud','ejuf','scope','context'),('second','author','ejuk','ejuj','scope','context'),('result','author','ejuj','ejuh','scope','context')},'zdg':{('first','author','ejuf','scope','context')},'eisox':{('display','ejuh','context')},'uf':{('author','result','display','context')},'eisch':{('lawname','ejs6','scope','context')},'ue':{(a,b,'context') for a,b in [('first','second'),('second','result'),('result','display')]}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('ejuo',[],mm),m,rows)
    assert run('ejuo',[],m|{n:forbidden for n in ('ejud','ejuf','ejuk','ejuj','ejuh','s5y')});count+=1
    for n,target in [('eisp3','first'),('zn2','second'),('eisp4','result')]:
        assert not run('ejuo',[],{n:lambda *xs:True for n in rows}|{n:lambda target=target:target});count+=1
    outer={'eir3':{('first','author','paper','ejup','context')},'ue':{('movingdisplay','first','context')}}
    count+=perturb(lambda mm:run('ejuq',[],mm),{n:relation(rs) for n,rs in outer.items()},outer)
    return dict(cases=count,three_inferences_obviousness_display_order_and_author=True,claims_and_necessity_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][162:164]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[table[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    flat=lambda mid:''.join(ET.fromstring(table[mid]['mathml']).itertext())
    assert [flat(n) for n in ('M0301','M0302','M0303','M0304','M0305','M0306')]==['k','K','ξ,η,ζ','τ','v','ψ(v)']
    calculated=flat('M0291')+flat('M0292')
    for old,new in [('β(Y−vVN)','Y′'),('β(Z+vVM)','Z′'),('β(M+vVZ)','M′'),('β(N−vVY)','N′'),('∂X','∂X′'),('∂L','∂L′')]:calculated=calculated.replace(old,new)
    equations=lambda s:sorted(x.strip().rstrip('.') for x in s.split(',') if x.strip())
    assert equations(calculated)==equations(flat('M0300')) and len(equations(calculated))==6
    correction=json.loads(read(CORRECTION));assert table['M0307']['sha256']==correction['correction']['snapshot_math_sha256']
    assert digest((ROOT/correction['image']).read_bytes())==correction['image_sha256']
    ns='{http://www.w3.org/1998/Math/MathML}';raw=[''.join(x.itertext()) for x in ET.fromstring(table['M0307']['mathml']).iter(ns+'mtd')]
    assert raw==['X′','=ψ(v)X,','L′','=ψ(v)L,','Y′','=ψ(v)β(Y−vVN),','M′','=ψ(v)β(M+vVz),','Z′','=ψ(v)β(Z+vVM),','N′','=ψ(v)β(N−vVY).']
    corrected=raw.copy();corrected[7]=corrected[7].replace('z','Z')
    return dict(version='einstein-field-comparison-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['908'],segments=segments,raw_math_cells=raw,facsimile_corrected_math_cells=corrected,normalized_prior_equations=equations(calculated),observations=['原刊908頁のu0163三文とu0164六式を通読した。Offenbar、müssen、二つのda、ferner、alsoをそれぞれ明白さ・必要性・理由・追加・帰結の提示へ接続する。','二つの先行式群はベクトル成分の表現を対応させると、同じ六偏微分式に正規化できる。数値場の等値や比例はこの構造一致から認定しない。','ξ,η,ζとτからの独立、vに依存してよいψ(v)、全六成分の同じ係数を確認した。M′右辺のz/Zは旧訂正記録の局所訂正を保持し、生資料を上書きしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,CORRECTION,*FACSIMILES)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p in PRIORS:
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[154])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'ejs6','ejtw','s6o','ejtu','ejsy','s6k','s6l','s6m','sai2','saj2','sak2','ejrj','s5k','zc','zdg'}<=names
    assert not names&{'sae2','saf2','saw','sau2'}
    prior=json.loads(read('reports/field-common-scale-v1.json'));assert prior['counterexample']['eight_algebraic_balances']==[True] and prior['counterexample']['no_common_rational_scalar']['status']=='valid' and prior['finite_refusal']['refused']
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_reference_individuals=3,replaced_statement=INDEX,other_357_statements_and_prior_judgments_preserved=True,nonproportional_solution_counterexample_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('setting',setting_checks),('equivalence',equivalence_checks),('form',form_checks),('scale',scale_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_vacuum_field_domain','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_field_comparison_claim.py','scripts/check_field_comparison_claim.py','tests/test_field_comparison_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    segments=[]
    for s in source_record()['segments']:
        row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation');segments.append(row)
        for m in s['math']:segments.append(dict(row,math_id=m['id'],math_sha256=m['sha256']))
    return dict(status='field_equivalence_form_common_factor_paragraph_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0163–u0164の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
