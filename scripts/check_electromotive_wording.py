"""Check physical force residuals and the any-direction first-order wording."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_resting_charge_force import retag,RS,PS,TAU
from scripts.check_total_differential import OPERATIONS,setup as numeric_setup
from scripts.check_force_motion_binding import vector
from scripts.compose_electromotive_wording import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,APPROX,CURRENT,PHYSICAL,build

DOC='docs/electromotive-wording-v1.md';SOURCE='data/einstein-electromotive-wording-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=tuple('artifacts/written-facsimiles-v1/einstein-1905-unlp-p'+p+'-0.jpg' for p in ('909','910'))
DEPENDENCIES=('reports/force-motion-binding-v1.json','reports/resting-charge-force-v1.json','reports/force-wordings-v1.json','reports/moving-field-definition-v1.json')
AXES=('x','y','z','t');SITUATIONS=('case','other')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','ra':'frame','zbm':'moving','zol':'carrier','zpo':'event','zpe':'baserecord','zou':'chargeunit','zot':'forceunit','zor':'chargekind','zpn':'forcekind','ta':'length','rb':'duration','zpq':'first','zpr':'second','eisqn':'intro','eisqs':'quotedterm',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'magneticunit','totalrecord','extrarecord','a','b','other')))
DS=dict(kind='function',parameters=[PS,RS,PS],result=PS)

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=OPERATIONS|{'ejwu','ejxm'}
    if mode!='full':bounds.add('svy')
    if mode=='witness':bounds|={'ejyc':{'ejx7','ejya'},'ejyg':{'ejyb','ejye'},'ejyd':{'ejyb','ejyc'}}[name]
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='witness':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jemw'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jemwcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jemwcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    captured=[]
    def capture(x):captured.append(x);return True
    mm['jemwcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def setup(name,velocity=(1,-2,2),magnetic=(2,1,3),quadratic=(2,-3,4),cubic=(0,0,0),wrong_linear=(0,0,0),offset=(0,0,0)):
    cuts,m=numeric_setup(fixture(name)[0]);c,r=cuts.make,cuts.read;m|={n:lambda x=x:x for n,x in CONSTANTS.items()}
    u=tuple(map(Q,velocity));h=tuple(map(Q,magnetic));base=(Q(2),Q(3),Q(1));point=(Q(1),Q(2),Q(-1),Q(1));light=Q(5);normu=sum(x*x for x in u)
    vec=lambda xs:vector(c,tuple(map(Q,xs)));readvec=lambda x:tuple(r(x(a)) for a in AXES[:3])
    def force(p,amount,vel):
        vs=readvec(vel);square=sum(x*x for x in vs)/(light*light);parameter=sum(x*y for x,y in zip(vs,u))/normu
        cross=(vs[1]*h[2]-vs[2]*h[1],vs[2]*h[0]-vs[0]*h[2],vs[0]*h[1]-vs[1]*h[0])
        # This fixture is an explicitly constructed polynomial of degree <=3.
        return vec([r(amount)*(base[i]+cross[i]/light+Q(quadratic[i])*square+Q(cubic[i])*parameter**3+Q(wrong_linear[i])*parameter+Q(offset[i])) for i in range(3)])
    response=FunctionValue((PS,RS,PS),PS,force);p=vec(point);uv=vec(u);b=vec(base);hv=vec(h)
    field=lambda values:FunctionValue(('individual',),TAU,lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:c(values[AXES.index(a)] if a in AXES[:3] else 0)))
    E,H=field(base),field(h);reg=FunctionValue(tuple([RS]*4),'truth',lambda *xs:True)
    m|={'tc':lambda:c(light),'zpj':lambda:p,'zpl':lambda:b,'znl':lambda:E,'znm':lambda:H,'znk':lambda:reg}
    def one(x):
        if isinstance(x,DescriptionValue):return json.loads(x.syntax).get('symbol')
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==RS:return tuple(r(x(a)) for a in AXES)
        if x.parameters==('individual',):return tuple(r(x(a)(*[c(t) for t in row])) for a in AXES[:3] for row in (point,(0,1,2,3)))
        if x.parameters==tuple([RS]*4):return tuple(x(*[c(t) for t in row]) for row in (point,(0,1,2,3)))
        if x.parameters==(PS,RS,PS):return tuple(r(x(p,c(q),vec(vs))(a)) for q in (0,1,-1) for vs in ((0,0,0),u,(2,1,-1)) for a in AXES[:3])
        raise ValueError('Unknown electromotive fixture function')
    norm=lambda xs:tuple(one(x) for x in xs);rel=lambda rows:lambda *xs:norm(xs) in rows
    total=response(p,c(1),uv);extra=vec([a-bb for a,bb in zip(readvec(total),base)])
    fields=('chargekind','frame','length','duration','chargeunit','forceunit',E,H,reg,'case',response)
    rows={'eisqp':{norm(fields)},'ejwu':{('case',)},'eirn':{norm(('frame',H,'magneticunit','case'))},'eispu':{norm(('chargekind','chargeunit','magneticunit','forceunit',c(1),'case'))},'zpc':{norm((record,'carrier','forcekind','frame','event','forceunit',value,'case')) for record,value in (('totalrecord',total),('extrarecord',extra))}}
    m|={n:rel(rs) for n,rs in rows.items()}
    observations=[]
    def order(domain,actual,linear,comparison,center):
        a=Q(1,4);ts=(-2*a,-a,Q(0),a,2*a);errors={t:r(actual(c(t)))-r(linear(c(t))) for t in ts}
        # Symmetric derivative is exact for these explicitly chosen cubic
        # fixtures. It is an oracle, not a test for arbitrary real functions.
        derivative=(8*(errors[a]-errors[-a])-(errors[2*a]-errors[-2*a]))/(12*a)
        valid=r(center)==0 and all(domain(c(t)) for t in ts) and all(r(comparison(c(t)))==t*t*normu/light**2 for t in ts)
        observations.append((errors[0],derivative,valid));return valid and errors[0]==0 and derivative==0
    m['svy']=order
    return dict(c=c,r=r,m=m,vec=vec,readvec=readvec,p=p,u=uv,h=hv,base=b,response=response,total=total,extra=extra,fields=fields,rows=rows,norm=norm,rel=rel,observations=observations,args=[uv,response,'magneticunit','totalrecord','extrarecord','case'],approx=[c(light),uv,hv,b,p,response])

@lru_cache(None)
def numeric_checks():
    s=setup('ejxy');c=s['c'];cases=0
    for u in ((1,0,0),(0,-2,0),(0,0,3),(1,-2,2)):
        for scale in (-2,0,Q(1,3),1):
            out=run('ejxy',[s['vec'](u),c(scale)],s['m']);assert s['readvec'](out)==tuple(scale*x for x in u);cases+=1
    s=setup('ejxz');out=run('ejxz',[s['vec']((1,-2,3)),s['vec']((4,5,-6))],s['m']);assert s['readvec'](out)==(-3,-7,9);cases+=1
    s=setup('ejx2');assert s['r'](run('ejx2',[s['u']],s['m']))==9;cases+=1
    s=setup('ejx3')
    for light,u,want in [(5,(1,-2,2),True),(5,(0,0,0),True),(0,(0,0,0),False),(-5,(1,0,0),False),(5,(3,4,0),False),(5,(4,4,0),False)]:
        assert run('ejx3',[s['c'](light),s['vec'](u)],s['m'])==want;cases+=1
    s=setup('ejx4');out=run('ejx4',[s['response'],s['p'],s['base'],s['u']],s['m']);assert s['readvec'](out)==s['readvec'](s['extra']);cases+=1
    s=setup('ejx5')
    for parameter in (-2,0,Q(1,4),1):
        assert s['r'](run('ejx5',[s['c'](5),s['u'],s['c'](parameter)],s['m']))==parameter**2*Q(9,25);cases+=1
    return dict(cases=cases,ordered_three_component_scale_and_residual=True,speed_ratio_squared_not_signed_cross_product=True)

@lru_cache(None)
def physical_checks():
    s=setup('ejx7');m=s['m'];cases=perturb(lambda mm:run('ejx7',s['args'],mm),m,s['rows'],s['norm'])
    # A numerical decomposition cannot replace the physical response or units.
    for i in range(len(CURRENT)):
        args=list(s['args']);args[i]=s['vec']((3,2,1)) if i==0 else FunctionValue((PS,RS,PS),PS,lambda *xs:s['vec']((99,99,99))) if i==1 else 'other'
        assert not run('ejx7',args,m),i;cases+=1
    assert not run('ejx7',s['args'],m|{'zpl':lambda:s['vec']((9,9,9))});cases+=1
    for constant in ('zol','ra','zpo','zou','zot','ta','rb'):
        assert not run('ejx7',s['args'],m|{constant:lambda:'other'}),constant;cases+=1
    for i in (3,4):
        args=list(s['args']);args[i]='baserecord';assert not run('ejx7',args,m|{'zpc':lambda *xs:True});cases+=1
    args=list(s['args']);args[4]='totalrecord';assert not run('ejx7',args,m|{'zpc':lambda *xs:True});cases+=1
    for axis in range(3):
        changed=list(s['readvec'](s['extra']));changed[axis]+=1
        wanted=s['norm'](('extrarecord','carrier','forcekind','frame','event','forceunit',s['vec'](changed),'case'))
        original=s['norm'](('extrarecord','carrier','forcekind','frame','event','forceunit',s['extra'],'case'))
        assert not run('ejx7',s['args'],m|{'zpc':s['rel'](s['rows']['zpc']-{original}|{wanted})});cases+=1
    # Zero additional force is allowed even with nonzero motion.
    z=setup('ejx7',velocity=(1,2,2),magnetic=(2,4,4),quadratic=(0,0,0));assert run('ejx7',z['args'],z['m']) and z['readvec'](z['extra'])==(0,0,0);cases+=1
    assert run('ejx7',s['args'],m|{n:forbidden for n in ('ejwv','zpm','scm2','xm','zpa')});cases+=1
    return dict(cases=cases,physical_response_and_force_records_bound=True,same_fields_units_event_and_frame=True,three_residual_components_checked=True,zero_extra_force_allowed=True,static_physical_force_is_prior_checked_boundary=True)

@lru_cache(None)
def approximation_checks():
    cases=0
    for velocity,magnetic in [((1,0,0),(2,1,3)),((0,-2,0),(2,1,3)),((0,0,3),(2,1,3)),((1,-2,2),(2,1,3)),((-1,2,-2),(0,0,0)),((1,2,2),(2,4,4))]:
        for quadratic,cubic in [((0,0,0),(0,0,0)),((2,-3,4),(0,0,0)),((2,-3,4),(1,0,-2))]:
            s=setup('ejx6',velocity,magnetic,quadratic,cubic);assert run('ejx6',s['approx'],s['m']);assert len(s['observations'])==3;cases+=1
    for axis in range(3):
        bad=[0,0,0];bad[axis]=1
        for kw in ({'wrong_linear':bad},{'offset':bad}):
            s=setup('ejx6',**kw);assert not run('ejx6',s['approx'],s['m']);cases+=1
    s=setup('ejx6');unknowns(lambda mm:run('ejx6',s['approx'],mm),s['m'],('svy',))
    for i in (0,1,2,3,4):
        args=list(s['approx']);args[i]=s['c'](6) if i==0 else s['vec']((3,2,1,9))
        # Point alone is irrelevant in this constant-field fixture; its
        # physical identity is checked in the separate response binding.
        if i==4:continue
        assert not run('ejx6',args,s['m']),i;cases+=1
    try:run('ejx6',s['approx'],s['m'],'full')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All-real asymptotic quantification silently sampled')
    # Actual current residual need not equal its first-order vector.
    assert s['readvec'](s['extra'])!=tuple(Q(x,5) for x in (-8,1,5));cases+=1
    s=setup('ejya');assert run('ejya',[s['u'],s['response'],'case'],s['m']);cases+=1
    return dict(cases=cases,all_directions_and_cross_product_order=True,zero_second_and_third_order_errors_allowed=True,constant_and_linear_errors_rejected=True,finite_speed_exact_equality_not_required=True,low_degree_polynomial_response_and_asymptotic_oracle_only=True,full_real_asymptotic_domain_refused=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for selected,result in product(product((False,True),repeat=2),repeat=2):
        m={'ejyb':lambda u,ctx:selected[('a','b').index(u)] and ctx=='case','ejyc':lambda u,ctx:result[('a','b').index(u)] and ctx=='case'}
        assert run('ejyd',[],m,'witness',('a','b'))==all(not a or b for a,b in zip(selected,result));cases+=1
    for name,slots in [('ejyc',4),('ejyg',5)]:
        patterns=[('a',)*slots,('b',)*slots]+[tuple('b' if i==j else 'a' for i in range(slots)) for j in range(slots)]
        for ws in patterns:
            if name=='ejyc':
                target=('a',*ws,'case');args=['a','case'];m={'ejx7':lambda *xs,target=target:xs==target,'ejya':lambda u,response,ctx,ws=ws:(u,response,ctx)==('a',ws[0],'case')};callee='ejx7'
            else:
                target=(*ws,'case','a');args=['a','case'];m={'ejyb':lambda u,ctx,ws=ws:(u,ctx)==(ws[0],'case'),'ejye':lambda *xs,target=target:xs==target};callee='ejye'
            assert run(name,args,m,'witness',('a','b'));cases+=1
            for i in range(len(target)):
                bad=target[:i]+('unavailable',)+target[i+1:]
                assert not run(name,args,m|{callee:lambda *xs,bad=bad:xs==bad},'witness',('a','b'));cases+=1
        unknowns(lambda mm:run(name,args,mm,'witness',('a','b')),m,m.keys())
    s=setup('ejyb');m=s['m']|{'ejxm':lambda velocity,ctx:s['readvec'](velocity)==(1,-2,2) and ctx=='case'}
    assert run('ejyb',[s['u'],'case'],m);assert not run('ejyb',[s['u'],'case'],m|{'ejxm':lambda *xs:False});cases+=2
    s=setup('ejye');assert run('ejye',s['args']+[s['extra']],s['m']);cases+=1
    assert not run('ejye',s['args']+[s['base']],s['m']);cases+=1
    return dict(cases=cases,all_velocity_candidates_conditional=True,every_witness_and_free_slot_distinguished=True,quoted_role_does_not_require_approximation_law=True,two_value_diagnostic_only=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('first','author','ejyd','scope','case')},'eisqq':{('quotedterm','ejyg','first','paper','case')},'eisqr':{('first','second','scope','case')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ejyh',[],mm),m,rows)
    assert run('ejyh',[],m|{n:forbidden for n in ('ejyd','ejyg','ejxr')});cases+=1
    rows={'eir3':{('first','author','paper','ejyi','case')},'ue':{('intro','first','case')}}
    cases+=perturb(lambda mm:run('ejyj',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,author_scope_order_old_new_contrast=True,quoted_term_role_not_execution=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][173];assert u['id']=='einstein-1905:u0174' and digest(u['text'].encode())==u['text_sha256']
    m=next(m for m in inv['math'] if m['id']=='M0318');assert digest(m['mathml'].encode())==m['sha256'] and ''.join(ET.fromstring(m['mathml']).itertext())=='v/V'
    page=next(x for x in inv['annotations'] if x['id']=='A0024');assert page['kind']=='page' and page['source_id']=='910'
    starts=[0]+[u['text'].index(t) for t in ('so wirkt','welche unter','gleich ist','(Alte')];ends=starts[1:]+[len(u['text'])]
    clauses=[dict(range=[a,b],text=u['text'][a:b]) for a,b in zip(starts,ends)];assert ''.join(c['text'] for c in clauses)==u['text']
    return dict(status='complete_first_wording_source_collation_not_automatic_equivalence',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=m,page_boundary=page,clauses=clauses,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),observations=['原刊909末尾–910頁の第一項全体を読む。動く点状単位電気量、電気力に加わる寄与、引用用語、近似の留保、外積の順序と除数、旧来の位置付けを保持する。','速度方向は三成分で直接扱い、x方向に限定しない。両項は先行する最終変換の適用域での言い表しとして読む。','追加寄与を同じ機械力応答と電気基準の差へ結ぶ。原文のv/V二次以上の留保は固定した場・方向での一次部分と読む。'],remaining=['全単位判断は別の記録で行う','第二項の任意方向の共動系変換と全文、u0176以降は未完'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,*FACSIMILES)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==360 and [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[163,164,165,166,168,358,359])==selection_binding(old,[163,164,165,166,168,358,359])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'eisqp','eisqq','eisqr','eisqs','ejxm','ejwu','svy','sci2'}<=names
    assert not names&{'ejxo','ejxp','ejxr','scm2','sco2','scp2','xm','zpa','zpm'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=3,new_references=1,replaced_statement=INDEX,other_359_statements_and_judgments_preserved=True,semantic_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('physical',physical_checks),('approximation',approximation_checks),('quantifier',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_field_equations','compose_force_wordings','compose_rest_force','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_total_differential','check_force_motion_binding','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_electromotive_wording.py','scripts/check_electromotive_wording.py','tests/test_electromotive_wording.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='old_wording_physical_additional_force_any_direction_and_first_order_checked',document=FULL,**results,alignment=dict(segments=[row,dict(row,math_id=s['math']['id'],math_sha256=s['math']['sha256'])]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
