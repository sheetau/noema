"""Check actual readout channels, causal record sharing, and all-speed scope."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document,DescriptionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_deflection_response as prior
from scripts.check_clock_site_time import relation,perturb,value as described
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_deflection_speed_determination import *

DOC='docs/deflection-speed-determination-v1.md';SOURCE='data/einstein-deflection-speed-determination-reading-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/electron-deflection-response-v1.json','reports/electron-transformed-dynamics-v1.json','reports/coordinate-measurement-v1.json','reports/electron-force-measurement-v1.json')
CONSTANTS=prior.CONSTANTS|{n:n for n in REFERENCES}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),*[n for n,t in MEASUREMENT if t=='a'],'observer','accelerationunit']))
SCENES=prior.SCENES+('assessment',)
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk;fn=prior.fn;sort=prior.sort;scalarize=prior.scalarize
BOUNDS={'eqs':{'ek3q','ejwb'},'eqt':{'ejsn','ejsj'},'equ':{'ejsn','ejsj'},'eqz':{'eqh'},'eq2':{'eqz'},'eq4':{'eq2','eqs','eqt','equ','eq3'},'eq5':{'eq4'},'eq6':{'ek3n','ek3o','ek3u'},'eq7':{'eq6','eq5'},'era':{'eq6','eqh','setk'},'erb':{'eq6','eqz'},'erc':{'eq6','eq2'},'ere':{'era','elk','erb','erc','eq7','erf','erg'},'eri':{'erh'},'erj':{'erc'},'erl':{'erk'}}

BOUNDS['eq3']={'ejwb'}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in prior.prior.prior.physical.NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==root)
        def expose(x):
            if isinstance(x,list):return [expose(y) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind') in ('forall','exists'):
                d['parameters'].append(dict(name=x['variable'],sort=x['sort']));return expose(x['body'])
            return {k:expose(v) for k,v in x.items()}
        d['body']=expose(d['body'])
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jdsarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jdspoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jdspoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jdspoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=SCENES,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def key(a,x):
    if isinstance(x,DescriptionValue):return described(x)
    if isinstance(x,(list,tuple)):return tuple(key(a,y) for y in x)
    return a.key(x)
def keyed(a,rows):return {n:lambda *xs,row=row:key(a,xs)==key(a,row) for n,row in rows.items()}
def model(speed=3):
    a=prior.model(speed=speed,Y=2,N=5);c=a.c
    a.by.update(observer='observer',assessment='assessment',accelerationunit='accelerationunit',accelerationscale=Q(1),ratio=c(Q(speed,5)),recovered=c(speed))
    for pre,quantity in [('electricacc','electricay'),('magneticacc','magneticay'),('electricfield','electricstrength'),('magneticfield','magneticstrength')]:
        for n,t in DEVICE:a.by[pre+n]=pre+n if t=='a' else fn(sort(DOMAIN),lambda x:abs(a.r(x))<100) if n=='range' else fn(sort(F),lambda x:c(2*a.r(x))) if n=='calibration' else c(a.r(a.by[quantity])/2)
    for n,t in SHARED:
        if n in FIXED:a.m[FIXED[n]]=lambda value=a.by[n]:value
    a.m['eisxv']=lambda:'event';a.m['eis3k']=lambda:'view'
    return a

@lru_cache(None)
def scalar_checks():
    a=model();c=a.c;cases=0
    for x,y,z,want in [(-6,2,3,True),(6,2,3,True),(0,2,0,True),(-6,2,-3,False),(6,0,3,False),(6,-2,3,False),(6,2,2,False)]:assert run('eqw',list(map(c,(x,y,z))),a.m)==want;cases+=1
    for root,triples in [('eqx',[(3,5,Q(3,5),True),(3,0,0,False),(3,5,1,False)]),('eqy',[(5,Q(3,5),3,True),(5,Q(3,5),4,False)])]:
        for x,y,z,want in triples:assert run(root,list(map(c,(x,y,z))),a.m)==want;cases+=1
    for L,T,A in ((1,1,1),(3,2,Q(3,4)),(2,3,Q(2,9))):
        mm=a.m|{'ejwb':lambda unit,l,m,t,scale,ctx:(unit,l,m,t,scale,ctx)==('accelerationunit',1,0,-2,A,'case')}
        vs=[Q(L),Q(T),'accelerationunit',Q(A),'case'];assert run('eq3',vs,mm);bad=vs.copy();bad[0]+=1;assert not run('eq3',bad,mm);cases+=2
    return dict(cases=cases,signed_normalization_nonzero_divisor_and_order=True,coherent_acceleration_unit_rescaling=True)

@lru_cache(None)
def physical_checks():
    cases=0
    for speed in (0,3):
        a=model(speed);vs=a.values(PAIR)
        rs={key(a,prior.expected_case(a,pre,y,n)) for pre,y,n in [('electric',2,0),('magnetic',0,5)]}
        mm=a.m|{'eqh':lambda *xs:key(a,xs) in rs,'eisoe':lambda view,source,target:(view,source,target) in {('view','other','electriccase'),('view','other','magneticcase')}}
        assert run('eqz',vs,mm);cases+=1
        for name,typ in BACKGROUND+STRENGTHS:
            bad=vs.copy();pos=[n for n,t in PAIR].index(name);bad[pos]='case' if typ=='d' else 'a' if typ=='a' else bad[pos]+1 if typ=='b' else a.c(a.r(bad[pos])+1)
            assert not run('eqz',bad,mm);cases+=1
        for symbol in ('eqh','eisoe'):
            assert not run('eqz',vs,mm|{symbol:lambda *xs:False});reject(lambda:run('eqz',vs,mm|{symbol:forbidden}));cases+=2
        vs=a.values(RESPONSE);mm=a.m|{'eqz':lambda *xs:True};assert run('eq2',vs,mm);cases+=1
        for name in ('electricay','magneticay','electricresponse','magneticresponse'):
            bad=vs.copy();pos=[n for n,t in RESPONSE].index(name);bad[pos]=a.c(a.r(bad[pos])+1);assert not run('eq2',bad,mm);cases+=1
        by=a.by|dict(context='case',chargerecord='eis35')
        rows={n:[by[x] for x,t in fields] for n,fields in [('ek3n',UNITS),('ek3o',MASS),('ek3u',CHARGE)]}
        mm=a.m|keyed(a,rows);assert run('eq6',[Q(1),'case'],mm);cases+=1
        for n in rows:
            assert not run('eq6',[Q(1),'case'],mm|{n:lambda *xs:False});reject(lambda:run('eq6',[Q(1),'case'],mm|{n:forbidden}));cases+=2
        assert not run('eq6',[Q(2),'case'],mm);cases+=1
        # The closed display must feed the same physical response and ratio operands.
        bound=[('speed',R)]+WITNESSES+STRENGTHS+COEFFICIENTS
        values=[Q(1)]+[a.by[n] for n,t in bound]
        response=[by[n] for n,t in RESPONSE]
        mm=a.m|{'eq6':lambda scale,ctx:(scale,ctx)==(Q(1),'case'),'eiscv':lambda *xs:True,'eq2':lambda *xs:key(a,xs)==key(a,response)}
        assert run('erc',values,mm,'instance');cases+=1
        for name in ('electricresponse','magneticresponse'):
            bad=values.copy();pos=1+[n for n,t in bound].index(name);bad[pos]=a.c(0 if speed==0 and name=='electricresponse' else a.r(bad[pos])+1)
            assert not run('erc',bad,mm|{'eq2':lambda *xs:True},'instance');cases+=1
        reject(lambda:run('erc',[],mm));cases+=1
        expected=[by[n] for n,t in BACKGROUND]
        assert run('eq7',[Q(1),a.c(speed)],a.m|{'eq6':lambda *xs:True,'eiscv':lambda *xs:True,'eq5':lambda *xs:key(a,xs)==key(a,expected)},'instance');cases+=1
    a=model();by=a.by|dict(context='case');c=a.c
    bound=[('speed',R)]+TRACE+STRENGTHS
    values=[Q(1)]+[by[n] for n,t in bound]
    row=[by[n] for n,t in CASE]
    law=[by['light'],by['speed'],c(a.beta),by['mass'],by['charge'],by['electricstrength'],by['magneticstrength'],by['ay']]
    mm=a.m|{'eq6':lambda *xs:True,'eiscv':lambda *xs:True,'eqh':lambda *xs:key(a,xs)==key(a,row),'eisoe':lambda *xs:xs==('view','case','case'),'setk':lambda *xs:key(a,xs)==key(a,law)}
    assert run('era',values,mm,'instance');assert not run('era',values,mm|{'setk':lambda *xs:False},'instance');cases+=2
    reject(lambda:run('era',[],mm));cases+=1
    by['electricstrength']=c(3);by['electricay']=c(-a.r(by['magneticay']))
    bound=[('speed',R)]+WITNESSES+STRENGTHS;values=[Q(1)]+[by[n] for n,t in bound]
    row=[by[n] for n,t in PAIR]
    mm=a.m|{'eq6':lambda *xs:True,'eiscv':lambda *xs:True,'eqz':lambda *xs:key(a,xs)==key(a,row)}
    assert run('erb',values,mm,'instance');cases+=1
    bad=values.copy();pos=1+[n for n,t in bound].index('electricay');bad[pos]=c(1)
    assert not run('erb',bad,mm|{'eqz':lambda *xs:True},'instance');cases+=1
    reject(lambda:run('erb',[],mm));cases+=1
    return dict(cases=cases,physical_trials_without_law_premise=True,closed_source_contents_keep_same_background_and_operands=True,full_function_domains_refused=True)

@lru_cache(None)
def quantity_checks():
    a=model();by=a.by;cases=0
    for root,unit,value,pre in [('eqs','accelerationunit','electricay','electric'),('eqt','electricunit','electricstrength','electric'),('equ','magneticunit','magneticstrength','magnetic')]:
        d=next(x for x in core()['declarations'] if x['name']==root);witnesses=[];node=d['body']
        while node['kind']=='exists':witnesses.append((node['variable'],node['sort']));node=node['body']
        # Normalization renames binders; obtain the original public order from the generated source schema.
        if root=='eqs':names=[n for n,t in KINEMATIC if n not in ('matter','frame','event','context','ay','region')]+['lengthscale','timescale','accelerationscale']
        else:names=[n for n,t in FIELDS if n not in ('frame','context',unit)]+['location']
        supply=by|{n:by[pre+n] for n,t in TRACE}|dict(context=by[pre+'scene'],point=by[pre+'location'],target=by['matter'],unit=by[unit],value=by[value],electricconversion=a.c(1),magneticconversion=a.c(Q(1,5)))
        vs=[supply[n] for n,t in QUANTITY]+[supply[n] for n in names]
        mm=a.m|{'ek3q':lambda *xs:True,'ejwb':lambda *xs:True,'ejsn':lambda *xs:True,'ejsj':lambda *xs:True,'eisqd':lambda *xs:True}
        assert run(root,vs,mm,'instance');cases+=1
        if root!='eqs':
            bad=vs.copy();bad[4]=a.c(a.r(bad[4])+1);assert not run(root,bad,mm,'instance');cases+=1
            reject(lambda:run(root,vs,mm|{'ejsn':forbidden},'instance'));cases+=1
        else:
            bad=vs.copy();bad[len(QUANTITY)+names.index('accelerationscale')]+=1;assert not run(root,bad,mm,'instance');cases+=1
            reject(lambda:run(root,vs,mm|{'ek3q':forbidden},'instance'));cases+=1
        reject(lambda:run(root,vs[:len(QUANTITY)],mm));cases+=1
    return dict(cases=cases,canonical_quantities_keep_units_field_axis_and_history=True,full_function_witnesses_refused=True)

def measurement_rows(a):
    by=a.by;rows={n:[] for n in ('eqs','eqt','equ','eq3','eis3r','eis3s','eis3u','eis3t')}
    for pre in ('electric','magnetic'):rows['eq3'].append([by[n] for n in ('lengthscale','timescale','accelerationunit','accelerationscale')]+[by[pre+'scene']])
    for channel,quantity,val,unit in [('electricacc','eqs','electricay','accelerationunit'),('magneticacc','eqs','magneticay','accelerationunit'),('electricfield','eqt','electricstrength','electricunit'),('magneticfield','equ','magneticstrength','magneticunit')]:
        pre='electric' if channel.startswith('electric') else 'magnetic'
        values={n:by[channel+n] for n,t in DEVICE}|dict(observer=by['observer'],target=by['matter'],quantity=quantity,frame=by['frame'],event=by[pre+'event'],unit=by[unit],context=by[pre+'scene'],value=by[val])
        rows[quantity].append([values[n] for n,t in QUANTITY]);rows['eis3r'].append([values[n] for n,t in CAL]);rows['eis3s'].append([values[n] for n,t in ACQUIRE]);rows['eis3u'].append([by['observer'],by[channel+'record'],by[pre+'scene'],by['assessment']])
    for rule,x,y,z in [('eqw','electricay','electricstrength','electricresponse'),('eqw','magneticay','magneticstrength','magneticresponse'),('eqx','magneticresponse','electricresponse','ratio'),('eqy','light','ratio','recovered')]:rows['eis3t'].append([by['observer'],rule,by[x],by[y],by[z],by['assessment']])
    return {n:{key(a,row) for row in rs} for n,rs in rows.items()}

@lru_cache(None)
def measurement_checks():
    cases=0
    for speed in (0,3):
        a=model(speed);rows=measurement_rows(a);vs=a.values(MEASUREMENT)
        mm=a.m|{n:lambda *xs,rs=rs:key(a,xs) in rs for n,rs in rows.items()}|{'eq2':lambda *xs:key(a,xs)==key(a,a.values(RESPONSE)),'eisoe':lambda view,source,result:(view,source,result)==('view','other','assessment')}
        assert run('eq4',vs,mm);cases+=1
        for symbol,rs in rows.items():
            for row in rs:assert not run('eq4',vs,mm|{symbol:lambda *xs,kept=rs-{row}:key(a,xs) in kept});cases+=1
            reject(lambda:run('eq4',vs,mm|{symbol:forbidden}));cases+=1
        for channel in CHANNELS:
            bad=vs.copy();pos=[n for n,t in MEASUREMENT].index(channel+'signal');bad[pos]=a.c(a.r(bad[pos])+1)
            assert not run('eq4',bad,mm|{'eis3s':lambda *xs:True});cases+=1
            bad=vs.copy();bad[[n for n,t in MEASUREMENT].index(channel+'calibration')]=fn(sort(F),lambda x:a.c(2*a.r(x)+1));assert not run('eq4',bad,mm|{'eis3r':lambda *xs:True});cases+=1
            bad=vs.copy();bad[[n for n,t in MEASUREMENT].index(channel+'range')]=fn(sort(DOMAIN),lambda x:False);assert not run('eq4',bad,mm|{'eis3r':lambda *xs:True});cases+=1
        for name in ('observer','assessment','accelerationunit'):
            bad=vs.copy();bad[[n for n,t in MEASUREMENT].index(name)]='case' if name=='assessment' else 'a';assert not run('eq4',bad,mm);cases+=1
        # A recorded computation may disagree with the actual speed; equality belongs to success, not acquisition.
        if speed:
            bad=vs.copy()
            for name,factor in [('magneticresponse',Q(2)),('magneticay',Q(2)),('magneticaccsignal',Q(2)),('ratio',Q(2)),('recovered',Q(2))]:bad[[n for n,t in MEASUREMENT].index(name)]=a.c(a.r(bad[[n for n,t in MEASUREMENT].index(name)])*factor)
            assert run('eq4',bad,a.m|{n:lambda *xs:True for n in rows}|{'eq2':lambda *xs:True,'eisoe':lambda *xs:True});cases+=1
    assert not {'setk','sets','eqm','eqi'}&{d['name'] for d in boundary('eq4')['declarations']};cases+=1
    return dict(cases=cases,four_actual_channels_and_calibrations=True,causal_record_availability_not_independent_worlds=True,same_observer_rules_inputs_and_units=True,measurement_does_not_preassume_success=True)

@lru_cache(None)
def possibility_checks():
    a=model();vs=a.values(BACKGROUND+MEASURE_WITNESSES);row=key(a,a.values(MEASUREMENT));mm=a.m|{'eq4':lambda *xs:key(a,xs)==row}
    assert run('eq5',vs,mm,'instance');cases=1
    for name in ('speed','recovered','electricrecord','magneticrecord','assessment'):
        if name not in dict(BACKGROUND+MEASURE_WITNESSES):continue
        bad=vs.copy();pos=[n for n,t in BACKGROUND+MEASURE_WITNESSES].index(name);bad[pos]='case' if name=='assessment' else 'a' if isinstance(bad[pos],str) else a.c(a.r(bad[pos])+1)
        assert not run('eq5',bad,mm,'instance');cases+=1
    bad=vs.copy();bad[-1]=a.c(4);assert not run('eq5',bad,a.m|{'eq4':lambda *xs:True},'instance');cases+=1
    reject(lambda:run('eq5',a.values(BACKGROUND),mm));cases+=1
    for speed in (0,3,5,6):
        for possible in (False,True):
            mm=a.m|{'eq6':lambda *xs:True,'eiscv':lambda *xs:True,'eq5':lambda *xs:possible}
            assert run('eq7',[Q(1),a.c(speed)],mm,'instance')==(speed>=5 or possible);cases+=1
    reject(lambda:run('eq7',[],mm));cases+=1
    return dict(cases=cases,recovered_value_matches_same_speed_only_at_success=True,all_subluminal_speeds_including_zero_not_samples=True,full_quantification_refused=True)

@lru_cache(None)
def binding_checks():
    doc=boundary('eq5');d=next(d for d in doc['declarations'] if d['name']=='eq5');names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(BACKGROUND,d['parameters'])};node=d['body']
    for n,t in MEASURE_WITNESSES:assert node['kind']=='exists';names[n]=dict(kind='variable',name=node['variable']);node=node['body']
    call=next(x for x in walk(node) if x.get('kind')=='call' and x.get('symbol')=='eq4');assert call['arguments']==[names[n] for n,t in MEASUREMENT];cases=1
    compact=collapse(scalarize(doc))
    for pivot,(field,typ) in enumerate(MEASURE_WITNESSES):
        f,dd,slots,name,body=lifted(compact,'eq5',pivot,len(MEASURE_WITNESSES),'exists');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']};special='other' if typ=='d' else 'b';probe=next(x for x in walk(body) if x.get('kind')=='call' and x.get('symbol')=='eq4');row=tuple((env|{name:special})[x['name']] for x in probe['arguments'])
        for permitted in (False,True):
            mm={d['name']:lambda *xs:True for d in f['declarations'] if d['kind']=='primitive'}|{n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{'eq4':lambda *xs:permitted and xs==row}
            assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=30000)[0]['value']==permitted;cases+=1
    d=next(d for d in core()['declarations'] if d['name']=='eq7');quantifiers=[x for x in walk(d['body']) if x.get('kind') in ('exists','forall')];assert [x['kind'] for x in quantifiers]==['exists','forall'];cases+=1
    assert quantifiers[0]['sort']=='number' and quantifiers[1]['sort']==sort(R);cases+=1
    return dict(cases=cases,all_68_witness_slots_two_value_diagnostics=True,charge_scale_fixed_outside_all_speeds=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislk':{('eis3x','eis3w',Q(1),'paper','case')},'eis3v':{('era','elk',Q(2),'case')},'eiswm':{('eis3y','author','eisym','elk','paper','case')},'zc':{('eis3y','author','era','erb','tenth','case'),('eis3z','author','erb','eq7','tenth','case'),('eis3z','author','erc','eq7','tenth','case')},'uh':{('eis3y','author','erb','tenth','case'),('eis3z','author','eq7','tenth','case')},'eisnw':{('eis3z','author','eis33','erf','paper','case'),('eis3z','author','eis34','erg','paper','case')},'uf':{('author','eis3z','eis32','case')},'ue':{('eis3y','eis3z','case'),('eis3z','eis32','case')}}
    # Use the existing display's observed constant mapping.
    display=CONSTANTS.get('eisym','eisym');rows['eiswm']={('eis3y','author',display,'elk','paper','case')}
    cases=perturb(lambda m:run('ere',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['ere']},rows)
    for root,node,msg,prev in [('eri','eis3x','erh','eis3w'),('erl','eis32','erk','eis3x')]:
        rows={'eir3':{(node,'author','paper',msg,'case')},'ue':{(prev,node,'case')}};cases+=perturb(lambda m:run(root,[],m),{n:relation(rs) for n,rs in rows.items()}|{msg:forbidden},rows)
    rows={'eisox':{('eis32','erc','case')},'uh':{('eis32','author','erc','tenth','case')}};cases+=perturb(lambda m:run('erj',[],m),{n:relation(rs) for n,rs in rows.items()}|{'erc':forbidden},rows)
    return dict(cases=cases,second_equation_and_first_item_order=True,inference_and_formula_application_keep_different_roles=True,coefficient_names_and_forward_display=True,quoted_physics_not_executed=True)

@lru_cache(None)
def source_record():
    d=json.loads(read(INVENTORY));units=d['units'][265:267];math=[m for m in d['math'] if m['id'] in [f'M{i:04d}' for i in range(430,437)]]
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-deflection-speed-determination-reading-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[m for m in math if m['id'] in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))) for u in units],facsimile_pages=[920],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==434 and after.document['statements'][:432]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[430,431])==selection_binding(before,[430,431]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES),new_statements=2,all_432_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('scalar',scalar_checks),('quantities',quantity_checks),('physical',physical_checks),('measurement',measurement_checks),('possibility',possibility_checks),('bindings',binding_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_deflection_speed_determination.py','scripts/check_deflection_speed_determination.py','tests/test_deflection_speed_determination.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='deflection_measurements_all_speed_determination_and_display_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
