"""Check physical flow roles, cycle averages and shared hypothetical settings."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden,relation,perturb
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_aberration_line import setup
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_observed_amplitude import CONSTANTS,DOMAIN
from scripts.check_radiative_intensity import source_record as prior_source
from scripts.compose_observed_intensity import *

CONSTANTS=CONSTANTS|{'eistg':'intensityclaim','eistd':'amplitudespecial'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values(),'view','body',*(n for n,t in SETTING+MODEL if t=='a')]))
DOC='docs/observed-intensity-v1.md';SOURCE='data/einstein-observed-intensity-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
DEPENDENCIES=('reports/radiative-intensity-v1.json','reports/observed-amplitude-v1.json','reports/wave-cycle-frequency-v1.json','reports/observed-doppler-v1.json','reports/speed-boundary-forecast-v1.json')
BOUNDS={'ekjz':{'ekc7','sede'},'ekkc':{'ekjz','ekjh'},'ekkd':{'eket','ekkb','ekkc'},'ekke':{'ekkd'},'ekkf':{'ekke'},'ekkg':{'ekkf'},'ekkh':{'ekkg'},'ekki':{'ekkg'},'ekkj':{'ekki','ekkh','ekjt','eigj'},'ekkk':{'ekkd','ekij'},'ekkl':{'ekco','ekik'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','sjd','sky','soy','szi','shu','ejor','sedi'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);inside=d['result']=='content';body=d['body']['body'] if inside else d['body'];pivot=int(mode.split(':')[1]);retained=None
        fields=WITNESSES if name=='ekkg' else VARIABLES if name=='ekkk' else BACKGROUND_VARIABLES
        for i in range(len(fields)):
            assert body['kind']==('exists' if name=='ekkg' else 'forall')
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        if inside:d['body']['body']=retained|{'body':body}
        else:d['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='joif'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='joifcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='joifcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['joifcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def values_for(fields,cuts,root):
    return [n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(fields,fixture(root)[1]))]

def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))

@lru_cache(None)
def cycle_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    # Piecewise periodic diagnostics are not the normalized analytic sine.
    sine=FunctionValue((RS,),RS,lambda x:c(1 if r(x)%2<1 else 0));cosine=FunctionValue((RS,),RS,lambda x:c(1 if (r(x)+Q(1,2))%2<1 else 0))
    for rate,offset in product((Q(1),Q(3),Q(2,3)),(Q(-2),Q(0),Q(1,3))):
        period=2/rate;values=[sine,cosine,*map(c,(1,2,rate,offset,period,1/period))];slots=fixture('ekjz')[1]
        def integral(lo,hi,fn,value):
            return r(lo)==0 and r(hi)==period and r(value)==period/2 and all(r(fn(c(t)))==r(sine(c(rate*t+offset)))**2 for t in (Q(0),Q(1,7),Q(2,3),Q(4,3)))
        mm=m|{'ekc7':lambda *xs:gate(xs,values,slots,cuts),'sede':integral}
        assert run('ekjz',values,mm);cases+=1
        for i,(_,s) in enumerate(slots):
            bad=values[:];bad[i]=sentinel(s,100+i,cuts);assert not run('ekjz',bad,mm);cases+=1
        unknowns(lambda model:run('ekjz',values,model),mm,('ekc7','sede'))
    profile=FunctionValue((RS,),RS,lambda t:c(2*r(t)-3));squared=run('ekjy',[profile],m)
    for t in (-2,0,1,3):assert r(squared(c(t)))==(2*t-3)**2;cases+=1
    values=values_for(AVERAGE,cuts,'ekkc');pos={n:i for i,(n,t) in enumerate(AVERAGE)}
    for n,value in dict(coefficient=2,nx=-1,ny=0,nz=0,ex=0,ey=3,ez=4,hx=0,hy=4,hz=-3,pi=1,cycle=2,rate=3,offset=Q(1,3),period=Q(2,3),frequency=Q(3,2),intensity=25).items():values[pos[n]]=c(value)
    values[pos['sine']]=sine;values[pos['cosine']]=cosine
    tw=[values[pos[n]] for n,t in TIMEWAVE];twslots=fixture('ekjz')[1]
    def mean(*xs):
        expected=[values[pos[n]] for n,t in FLUX]
        if not gate(xs[:10],expected,fixture('ekjf')[1],cuts):return False
        fn,lo,hi,integrated,I=xs[10:]
        return tuple(map(r,(lo,hi,integrated,I)))==(0,Q(2,3),Q(50,3),25) and all(r(fn(c(t)))==r(sine(c(3*t+Q(1,3)))) for t in (Q(0),Q(1,7),Q(2,3)))
    mm=m|{'ekjz':lambda *xs:gate(xs,tw,twslots,cuts),'ekjh':mean}
    assert run('ekkc',values,mm);cases+=1
    for i,(_,s) in enumerate(fixture('ekkc')[1]):
        bad=values[:];bad[i]=sentinel(s,100+i,cuts);assert not run('ekkc',bad,mm);cases+=1
    return dict(cases=cases,same_cycle_profile_offset_integral_and_intensity=True,periodic_diagnostics_not_a_sine_integral_theorem=True)

@lru_cache(None)
def physical_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    sine=FunctionValue((RS,),RS,lambda x:c(r(x)+1));phase=FunctionValue((RS,RS,RS,RS),RS,lambda x,y,z,t:c(r(x)+2*r(y)+3*r(z)+5*r(t)))
    values=values_for(MODEL,cuts,'ekkb');pos={n:i for i,(n,t) in enumerate(MODEL)}
    for n,value in dict(coefficient=2,ex=1,ey=2,ez=3,hx=4,hy=5,hz=6).items():values[pos[n]]=c(value)
    values[pos['sine']]=sine;values[pos['phase']]=phase
    vector=[values[pos[n]] for n,t in VECTOR];field=run('ekka',vector,m)
    for xyztime in ((0,0,0,0),(1,2,-1,3),(-2,1,4,-1)):
        p=sum(a*b for a,b in zip(xyztime,(1,2,3,5)))+1
        for axis,component in (('x',-6),('y',12),('z',-6),('body',0)):
            assert r(field(axis)(*map(c,xyztime)))==component*p*p;cases+=1
    def calibration(*xs):
        return gate(xs,[values[pos[n]] for n,t in COEFFICIENT],[(n,fixture('ekkb')[1][pos[n]][1]) for n,t in COEFFICIENT],cuts)
    def flow(wave,process,frame,lu,tu,eu,region,flux,scope,ctx):
        if (wave,process,frame,lu,tu,eu,scope,ctx)!=('wave','process','frame','lengthunit','timeunit','energyunit','scope','case'):return False
        if not same_value(region,values[pos['region']],fixture('ekkb')[1][pos['region']][1],cuts):return False
        return all(r(flux(axis)(*map(c,point)))==r(field(axis)(*map(c,point))) for axis,point in product(('x','y','z','body'),((0,0,0,0),(1,2,-1,3))))
    mm=m|{'eiste':calibration,'eistf':flow};assert run('ekkb',values,mm);cases+=1
    for i,(_,s) in enumerate(fixture('ekkb')[1]):
        bad=values[:];bad[i]=sentinel(s,100+i,cuts);assert not run('ekkb',bad,mm),(i,MODEL[i]);cases+=1
    unknowns(lambda model:run('ekkb',values,model),mm,('eiste','eistf','shv'))
    return dict(cases=cases,all_three_flux_components_and_same_physical_units=True,physical_role_not_inferred_from_numeric_values=True)

@lru_cache(None)
def condition_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;values=values_for(SETTING,cuts,'ekkd');slots=fixture('ekkd')[1];pos={n:i for i,(n,t) in enumerate(SETTING)}
    for n,value in dict(light=5,speed=3,rate=1,ax=-1,ay=0,az=0,ex=0,ey=3,ez=4,hx=0,hy=4,hz=-3,amplitude=5,newamplitude=10,coefficient=2,incident=25,received=100,pi=4,cycle=8,angle=4,anglecos=-1,anglesin=0,ratio=0,principal=0,oldperiod=8,newperiod=4,frequency=Q(1,8),newfrequency=Q(1,4),newoffset=2).items():values[pos[n]]=c(value)
    seenmodels=[];seenaverages=[]
    def collect(target):
        def f(*xs):target.append(xs);return True
        return f
    mm=m|{'eket':lambda *xs:gate(xs,values[:60],slots[:60],cuts),'ekkb':collect(seenmodels),'ekkc':collect(seenaverages)}
    assert run('ekkd',values,mm);cases+=1
    assert len(seenmodels)==len(seenaverages)==2
    modelpos={n:i for i,(n,t) in enumerate(MODEL)};avgpos={n:i for i,(n,t) in enumerate(AVERAGE)}
    for i in range(2):
        model=seenmodels[i];average=seenaverages[i]
        assert model[modelpos['frame']]==('frame' if i==0 else CONSTANTS['zbm']);cases+=1
        assert tuple(r(model[modelpos[n]]) for n in ('coefficient','ex','ey','ez','hx','hy','hz'))==((2,0,3,4,0,4,-3) if i==0 else (2,0,6,8,0,8,-6));cases+=1
        assert r(model[modelpos['phase']](*map(c,(1,2,3,4))))==Q(21,5)*(i+1);cases+=1
        assert tuple(r(average[avgpos[n]]) for n in ('nx','ny','nz','rate','offset','period','frequency','intensity'))==((-1,0,0,1,0,8,Q(1,8),25) if i==0 else (-1,0,0,2,2,4,Q(1,4),100));cases+=1
    modelslots=fixture('ekkb')[1];avgslots=fixture('ekkc')[1]
    mm=m|{'eket':lambda *xs:gate(xs,values[:60],slots[:60],cuts),'ekkb':lambda *xs:any(gate(xs,row,modelslots,cuts) for row in seenmodels),'ekkc':lambda *xs:any(gate(xs,row,avgslots,cuts) for row in seenaverages)}
    assert run('ekkd',values,mm);cases+=1
    for i,(_,s) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(s,100+i,cuts)
        try:actual=run('ekkd',bad,mm)
        except (ValueError,ZeroDivisionError):pass
        else:assert not actual,(i,SETTING[i])
        cases+=1
    for name in ('angle','ax','incident','received'):
        bad=values[:];bad[pos[name]]=c(0);assert not run('ekkd',bad,mm);cases+=1
    assert run('ekke',values,m|{'ekkd':lambda *xs:gate(xs,values,slots,cuts)});cases+=1
    bad=values[:];bad[pos['newamplitude']]=c(5);assert not run('ekke',bad,m|{'ekkd':lambda *xs:True});cases+=1
    unknowns(lambda model:run('ekkd',values,model),mm,('eket','ekkb','ekkc'))
    return dict(cases=cases,all_66_roles_bound_to_same_models=True,head_on_real_angle_and_positive_incident_required=True,old_and_new_periods_and_observer_offset_distinct=True,prior_square_ratio_separate_from_physical_premise=True)

@lru_cache(None)
def alternative_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;fields=BACKGROUND+[('speed',R),('received',R)]+WITNESSES;values=values_for(fields,cuts,'ekkf');slots=fixture('ekkf')[1];pos={n:i for i,(n,t) in enumerate(fields)};cases=0
    values[pos['alternative']]='other'
    expected=[values[pos['alternative' if n=='context' else n]] for n,t in SETTING];actualslots=fixture('ekkd')[1]
    mm={'eisoe':lambda view,base,alt:(view,base,alt)==('view','case','other'),'ekke':lambda *xs:gate(xs,expected,actualslots,cuts)}
    assert run('ekkf',values,mm);cases+=1
    for i,(_,s) in enumerate(slots):
        bad=values[:];bad[i]='case' if fields[i][0]=='alternative' else sentinel(s,100+i,cuts)
        assert not run('ekkf',bad,mm),(i,fields[i]);cases+=1
    unknowns(lambda model:run('ekkf',values,model),mm,('eisoe','ekke'))
    for pivot,(name,t) in enumerate(WITNESSES):
        targets=('case','other','unavailable') if t=='d' else ('a','b','unavailable')
        for target in targets:
            expected={n:'case' if s=='d' else 'a' for n,s in fields};expected[name]=target;row=tuple(expected[n] for n,s in fields)
            supplied=[expected[n] for n,s in BACKGROUND+[('speed',R),('received',R)]]+[expected[n] for i,(n,s) in enumerate(WITNESSES) if i!=pivot]
            base={'ekkf':lambda *xs,row=row:tuple(xs)==row}
            assert run('ekkg',supplied,base,'slot:'+str(pivot),('a','b'))==(target!='unavailable');cases+=1
            assert not run('ekkg',supplied,{'ekkf':lambda *xs:False},'slot:'+str(pivot),('a','b'));cases+=1
    background=values_for(BACKGROUND,cuts,'ekkh');bgslots=fixture('ekkh')[1]
    def point(*xs):return gate(xs[:-2],background,bgslots,cuts) and tuple(map(r,xs[-2:]))==(3,100)
    fn=run('ekkh',background,{'ekkg':point});assert fn(c(3),c(100)) and not fn(c(100),c(3));cases+=2
    for i,(_,s) in enumerate(bgslots):
        bad=background[:];bad[i]=sentinel(s,100+i,cuts);assert not run('ekkh',bad,{'ekkg':point})(c(3),c(100));cases+=1
    return dict(cases=cases,alternative_context_used_throughout_physical_setting=True,base_context_and_alternative_not_identified=True,all_existential_slots=16,all_fixed_background_slots=50)

@lru_cache(None)
def universal_checks():
    cases=0
    for root,fields,universal in (('ekkk',SETTING,VARIABLES),('ekkj',BACKGROUND,BACKGROUND_VARIABLES)):
        for pivot,(name,t) in enumerate(universal):
            for target in ('a','b','unavailable'):
                expected={n:'a' for n,t in fields};expected.update(context='case',scope='b');expected[name]=target;row=tuple(expected[n] for n,t in fields)
                values=[expected[n] for i,(n,t) in enumerate(universal) if i!=pivot]
                base={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b'}
                if root=='ekkk':
                    base|={'ekkd':lambda *xs,row=row:tuple(xs)==row,'ekij':lambda *xs:False}
                    good={'ekij':lambda *xs:xs[60] is False and len(xs)==63}
                else:
                    base|={'eirf':lambda:'a','eiscv':relation({(expected['view'],'a','eigj','case')}),'ekki':lambda *xs,row=row:tuple(xs)==row,'ekkh':lambda *xs,row=row:'a' if tuple(xs)==row else 'b','ekjt':lambda G,B:False}
                    good={'ekjt':lambda G,B:G=='a' and B=='a'}
                assert run(root,values,base,'slot:'+str(pivot),('a','b'))==(target=='unavailable');cases+=1
                assert run(root,values,base|good,'slot:'+str(pivot),('a','b'));cases+=1
    cuts,m=setup();c=cuts.make
    for root in ('ekkk','ekkj'):
        refused(lambda root=root:run(root,[],m|{'tc':lambda:c(5),'ekkd':lambda *xs:True,'ekij':lambda *xs:True,'eiscv':lambda *xs:True,'ekki':lambda *xs:True,'ekkh':lambda *xs:None,'ekjt':lambda *xs:True}));cases+=1
    return dict(cases=cases,all_setting_universal_slots=62,all_background_universal_slots=46,no_sampled_real_or_function_quantification=True)

@lru_cache(None)
def presentation_checks():
    rows={
      'ekkm':{'eissb':{('intensityclaim','amplitudedisplay','author','ekik','ekkk','scope','case')},'zc':{('intensityclaim','author','ekkl','ekkj','scope','case')},'uh':{('intensityclaim','author','ekkj','scope','case')}},
      'ekko':{'eir3':{('intensityclaim','author','paper','ekkn','case')},'ue':{('amplitudespecial','intensityclaim','case')}}}
    cases=0
    for root,rs in rows.items():cases+=perturb(lambda model:run(root,[],model),{n:relation(vs) for n,vs in rs.items()},rs)
    for a,b in product((False,True),repeat=2):
        # Evaluating the conjunction is separate from quoting it in ekkm.
        from noema.finite_semantics import Content
        mm={'ekco':lambda a=a:Content(('case','other'),(a,a)),'ekik':lambda b=b:Content(('case','other'),(b,b))}
        assert run('ekkl',[],mm)==(a and b);cases+=1
    return dict(cases=cases,same_developed_equations_and_conditional_conclusion=True,quoted_boundary_not_evaluated_during_attribution=True)

@lru_cache(None)
def source_record():
    prior=prior_source();u=prior['units'][0];inv=json.loads(read(INVENTORY));original=inv['units'][200]
    return dict(status='same_radiation_intensity_and_hypothetical_boundary_connected',segments=[dict(u,range=[0,len(u['text'])],statements=[INDEX],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',original['text'])))],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC,'data/einstein-radiative-intensity-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==384 and new.document['statements'][:-1]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    doc=core()
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),general_relations=2,source_references=1,old_383_statements_and_judgments_preserved=True,whole_unit_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('cycle',cycle_checks),('physical',physical_checks),('condition',condition_checks),('alternative',alternative_checks),('universal',universal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_wave_cycle_frequency','check_resting_charge_force','check_observed_amplitude','check_radiative_intensity','compose_radiative_intensity','compose_doppler_specialization','compose_observed_amplitude','compose_wave_cycle_frequency','compose_wave_transform_application','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_observed_intensity.py','scripts/check_observed_intensity.py','tests/test_observed_intensity.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_radiation_cycle_intensity_and_hypothetical_boundary_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
