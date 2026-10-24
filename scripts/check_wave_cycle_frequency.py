"""Diagnose least cycles, frequency units and the same wave's two frames."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_wave_inquiry import arithmetic_model
from scripts.check_wave_transform_application import DOMAIN,CONSTANTS
from scripts.check_resting_charge_force import retag
from scripts.compose_wave_cycle_frequency import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,MEANINGS,FAMILY,SETTING,WITNESSES,build

DOC='docs/wave-cycle-frequency-v1.md';SOURCE='data/einstein-wave-cycle-frequency-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p911-0.jpg'
DEPENDENCIES=('reports/wave-transform-application-v1.json','reports/plane-waveforms-v1.json','reports/wave-directions-v1.json','reports/velocity-angle-measure-v1.json')
BOUNDS={'ekc2':{'ekcz'},'ekc3':{'sdv2','sedi','ekc2'},'ekc7':{'ekc3','ekc2'},'ekde':{'ekcl','ekc7','ekdd'},'ekdf':{'ekde'}}

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sje','szi','soy'}
    if mode!='full':bounds|=BOUNDS.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='pointwise':
        found=[]
        def expose(node):
            if isinstance(node,list):return [expose(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and node['sort']==RS:
                found.append(dict(name=node['variable'],sort=RS));return expose(node['body'])
            return {k:expose(x) for k,x in node.items()}
        d['body']=expose(d['body']);assert len(found)==1,(name,len(found));d['parameters']+=found
    if mode.startswith('slot:'):
        doc=retag(doc)
        for dec in doc['declarations']:
            if dec['kind']=='primitive':
                dec['parameters']=['individual' if isinstance(t,dict) else t for t in dec['parameters']]
                if isinstance(dec['result'],dict):dec['result']='individual'
            else:
                for p in dec['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name)
        pivot=int(mode.split(':')[1]);node=d['body']['body'];retained=None
        for i in range(len(WITNESSES)):
            assert node['kind']=='exists'
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
            node=node['body']
        d['body']['body']=retained|{'body':node}
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jwcf'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jwcfcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jwcfcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(value):captured.append(value);return True
    mm['jwcfcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def refused(call):
    try:call()
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full real/function domain was enumerated')

@lru_cache(None)
def period_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;cases=0
    # Exact diagnostic periodic profiles, explicitly not sine/cosine.
    first=FunctionValue((RS,),RS,lambda t:c(r(t)%4));second=FunctionValue((RS,),RS,lambda t:c((r(t)+1)%2))
    for period,point in product((0,1,2,4,8),(-5,-1,0,Q(1,2),1,3,7)):
        args=[first,second,c(period),c(point)]
        assert run('ekcy',args,m)==(period%4==0);cases+=1
        assert run('ekcz',args,m,'pointwise')==(period>0 and period%4==0);cases+=1
    # Both profiles matter independently: one may have the proposed shorter period.
    constant=FunctionValue((RS,),RS,lambda t:c(0))
    assert not run('ekcy',[constant,first,c(2),c(0)],m);cases+=1
    assert not run('ekcy',[first,constant,c(2),c(0)],m);cases+=1
    oracle=lambda a,b,p:r(p)>0 and r(p)%4==0
    for period,candidate in product((0,1,2,4,8),(-1,0,1,2,3,4,8)):
        expected=period>0 and period%4==0 and not(0<candidate<period and candidate%4==0)
        assert run('ekc2',[first,second,c(period),c(candidate)],m|{'ekcz':oracle},'pointwise')==expected;cases+=1
    assert not run('ekc2',[constant,constant,c(4),c(1)],m|{'ekcz':lambda *xs:True},'pointwise');cases+=1
    unknowns(lambda mm:run('ekcy',[first,second,c(4),c(1)],mm),m,('ba','bd','sca'))
    unknowns(lambda mm:run('ekc2',[first,second,c(4),c(1)],mm,'pointwise'),m|{'ekcz':oracle},('ekcz',))
    refused(lambda:run('ekcz',[first,second,c(4)],m))
    refused(lambda:run('ekc2',[first,second,c(4)],m|{'ekcz':oracle}))
    return dict(cases=cases,common_period_for_both_profiles=True,least_positive_period_excludes_multiples_and_constant_profiles=True,full_real_quantifiers_preserved=True,diagnostic_profiles_not_sine=True)

@lru_cache(None)
def normalization_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;cases=0
    pair=[FunctionValue((RS,),RS,lambda t,i=i:c(r(t)+i)) for i in (1,2)]
    # A rational surrogate tests binding only; pi is not asserted to equal 2.
    mm=m|{'sdv2':lambda *xs:True,'sedi':lambda x:r(x)==2,'ekc2':lambda a,b,p:r(p)==4}
    values=[*pair,c(2),c(4)];assert run('ekc3',values,mm);cases+=1
    for pi,cycle in ((2,2),(2,8),(4,8),(2,-4),(0,0)):
        assert not run('ekc3',pair+[c(pi),c(cycle)],mm);cases+=1
    for n in ('sdv2','sedi','ekc2'):
        assert not run('ekc3',values,mm|{n:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekc3',values,model),mm,('sdv2','sedi','ekc2'))
    refused(lambda:run('ekc3',values,m,'full'))
    return dict(cases=cases,shared_normalized_profiles_integral_pi_and_twice_pi_required=True,supplied_rational_boundary_not_an_exact_pi_claim=True)

@lru_cache(None)
def frequency_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;cases=0
    for cycle,rate in product((Q(4),Q(8)),(Q(1,2),Q(2),Q(8))):
        period=cycle/rate;freq=1/period;values=[cycle,rate,period,freq]
        assert run('ekc6',list(map(c,values)),m);cases+=1
        for i in range(4):
            for bad in (Q(0),Q(-1),values[i]+1):
                changed=values[:];changed[i]=bad;assert not run('ekc6',list(map(c,changed)),m);cases+=1
        if freq!=rate:assert not run('ekc6',list(map(c,(cycle,rate,period,rate))),m);cases+=1
        # Same cycle with a changed time unit: rates divide and the period multiplies.
        for scale in (Q(2),Q(3,2)):
            assert run('ekc6',list(map(c,(cycle,rate/scale,period*scale,freq/scale))),m);cases+=1
    profile=FunctionValue((RS,),RS,lambda t:c(r(t)%4))
    for rate,offset,time in product((Q(1,2),Q(2)),(-3,0,5),(-2,0,1)):
        actual=run('ekc4',list(map(c,(rate,offset,time))),m);assert r(actual)==rate*time+offset;cases+=1
        lifted=run('ekc5',[profile,c(rate),c(offset)],m);assert r(lifted(c(time)))==(rate*time+offset)%4;cases+=1
    unknowns(lambda mm:run('ekc6',list(map(c,(4,8,Q(1,2),2))),mm),m,('shv','sca','bg'))
    return dict(cases=cases,angular_rate_cycle_period_and_frequency_distinct=True,positive_units_and_time_rescaling_checked=True,arbitrary_phase_offset_preserved=True)

@lru_cache(None)
def temporal_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;cases=0
    sine=FunctionValue((RS,),RS,lambda t:c(r(t)%4));cosine=FunctionValue((RS,),RS,lambda t:c((r(t)+1)%4))
    for rate,offset in product((Q(1,2),Q(2)),(-3,0,5)):
        period=4/rate;freq=1/period
        # Check the two function arguments actually supplied to the least-period boundary.
        def least(a,b,p):
            return r(p)==period and all(r(a(c(t)))==(rate*t+offset)%4 and r(b(c(t)))==(rate*t+offset+1)%4 for t in (-1,0,1,2))
        mm=m|{'ekc3':lambda *xs:True,'ekc2':least}
        args=[sine,cosine,*map(c,(2,4,rate,offset,period,freq))]
        assert run('ekc7',args,mm);cases+=1
        for n in ('ekc3','ekc2'):
            assert not run('ekc7',args,mm|{n:lambda *xs:False});cases+=1
        for i in (4,5,6,7):
            wrong=args[:];wrong[i]=c(r(args[i])+1);assert not run('ekc7',wrong,mm);cases+=1
    unknowns(lambda model:run('ekc7',args,model),mm,('ekc3','ekc2'))
    refused(lambda:run('ekc7',args,m,'full'))
    return dict(cases=cases,both_time_profiles_share_rate_offset_and_least_period=True,analytic_boundaries_remain_explicit=True)

@lru_cache(None)
def trace_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;cases=0
    # Native phase sds2, not a callback duplicating the coordinate order.
    phase=run('ekbf',list(map(c,(5,2,Q(3,5),Q(4,5),0))),m)
    for velocity,origins in product(((0,0,0),(3,0,0),(0,2,0)),((0,0,0),(1,-2,3))):
        positions=[FunctionValue((RS,),RS,lambda t,a=a,u=u:c(a+u*r(t))) for a,u in zip(origins,velocity)]
        rate=2*(1-(Q(3,5)*velocity[0]+Q(4,5)*velocity[1])/5)
        offset=-Q(2,5)*(Q(3,5)*origins[0]+Q(4,5)*origins[1])
        traced=run('ekda',[phase,*positions],m)
        for time in (-2,0,1,3):
            assert r(traced(c(time)))==rate*time+offset;cases+=1
            args=[phase,*positions,*map(c,(time,rate,offset))]
            assert run('ekdb',args,m);cases+=1
            for i in (5,6):
                changed=args[:];changed[i]=c(r(args[i])+1)
                # At t=0, a rate perturbation cannot be distinguished at one point.
                assert run('ekdb',changed,m)==(i==5 and time==0);cases+=1
        for lo,hi,time in product((0,),(2,),(-1,0,1,2,3)):
            args=[phase,*positions,*map(c,(lo,hi,rate,offset+1,time))]
            assert run('ekdc',args,m,'pointwise')==(not lo<=time<=hi);cases+=1
    refused(lambda:run('ekdc',[phase,*positions,*map(c,(0,2,rate,offset))],m))
    unknowns(lambda model:run('ekdc',[phase,*positions,*map(c,(0,2,rate,offset,1))],model,'pointwise'),m,('zzba','zzbc','sca'))
    return dict(cases=cases,native_four_coordinate_phase_pulled_along_same_time_path=True,phase_offset_and_motion_rate_checked=True,closed_interval_uses_lower_upper_time=True,one_point_does_not_fix_rate=True)

@lru_cache(None)
def doppler_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;cases=0
    for speed,direction,cycle,rate in product((-3,3),((1,0,0),(-1,0,0),(0,1,0),(Q(3,5),Q(4,5),0)),(Q(4),Q(8)),(Q(2),Q(8))):
        factor=Q(5,4)*(1-Q(direction[0])*speed/5);newrate=rate*factor
        values=[cycle,5,speed,*direction,rate,newrate,cycle/rate,cycle/newrate,rate/cycle,newrate/cycle]
        assert run('ekdd',list(map(c,values)),m);cases+=1
        for i in (0,3,6,7,8,9,10,11):
            changed=values[:];changed[i]+=1;assert not run('ekdd',list(map(c,changed)),m);cases+=1
        changed=values[:];changed[10],changed[11]=changed[6],changed[7]
        assert not run('ekdd',list(map(c,changed)),m);cases+=1
    unknowns(lambda model:run('ekdd',list(map(c,values)),model),m,('soy','shv','sca'))
    return dict(cases=cases,same_cycle_in_both_frames=True,frequencies_share_factor_periods_use_inverse=True,opposite_transverse_and_oblique_directions_checked=True)

@lru_cache(None)
def binding_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;slots=fixture('ekde')[1];pos={n:i for i,(n,t) in enumerate(SETTING)}
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    for n,x in dict(light=5,rate=8,ax=Q(3,5),ay=Q(4,5),az=0,pi=2,cycle=4,oldperiod=Q(1,2),newperiod=Q(5,8),frequency=2,newfrequency=Q(8,5)).items():values[pos[n]]=c(x)
    def matches(xs,expected,sorts):return len(xs)==len(expected) and all(same_value(x,y,s,cuts) for x,y,s in zip(xs,expected,sorts))
    parent=lambda *xs:matches(xs,values[:len(FAMILY)],[s for n,s in slots[:len(FAMILY)]])
    pair_sort=slots[pos['sine']][1]
    harmonic=[values[pos[n]] for n in ('sine','cosine','pi','cycle')]
    old=harmonic+[c(8),c(0),c(Q(1,2)),c(2)];new=harmonic+[c(Q(32,5)),c(0),c(Q(5,8)),c(Q(8,5))]
    temporal=lambda *xs:any(matches(xs,row,[pair_sort,pair_sort]+[RS]*6) for row in (old,new))
    expected=list(map(Q,(4,5,3,Q(3,5),Q(4,5),0,8,Q(32,5),Q(1,2),Q(5,8),2,Q(8,5))))
    numeric=lambda *xs:tuple(map(r,xs))==tuple(expected)
    # Wiring-only gamma boundary: perturbed light values are rejected by parent,
    # while eager evaluation still visits the consequent's numerical expressions.
    mm=m|{'soy':lambda *xs:c(Q(5,4)),'zb7':lambda:c(3),'ekcl':parent,'ekc7':temporal,'ekdd':numeric}
    assert run('ekde',values,mm);cases=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts);assert not run('ekde',changed,mm);cases+=1
    for n in ('ekcl','ekc7','ekdd'):
        assert not run('ekde',values,mm|{n:lambda *xs:False});cases+=1
    # Neither old nor new temporal branch may be dropped.
    for only in (old,new):
        assert not run('ekde',values,mm|{'ekc7':lambda *xs,only=only:matches(xs,only,[pair_sort,pair_sort]+[RS]*6)});cases+=1
    unknowns(lambda model:run('ekde',values,model),mm,('ekcl','ekc7','ekdd'))
    return dict(cases=cases,all_47_roles_and_both_temporal_branches_required=True,prior_actual_fields_and_nonzero_error_setting_preserved=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for pivot,(name,sort) in enumerate(WITNESSES):
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in SETTING};expected.update(frame='a',scope='b',context='case',light='a');expected[name]=target
            values=[expected[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot];row=tuple(expected[n] for n,t in SETTING)
            m={'ra':lambda:'a','eisrx':lambda:'b','tc':lambda:'a','ekde':lambda *xs,row=row:tuple(xs)==row}
            assert run('ekdf',values,m,'slot:'+str(pivot),('a','b'))==(target!='unavailable');cases+=1
            if target!='unavailable':assert not run('ekdf',values,m|{'ekde':lambda *xs:False},'slot:'+str(pivot),('a','b'));cases+=1
    cuts,m=arithmetic_model();refused(lambda:run('ekdf',[],m|{'tc':lambda:cuts.make(5),'ekde':lambda *xs:True}))
    return dict(cases=cases,witnesses=len(WITNESSES),every_witness_slot_and_absent_witness_checked=True,full_function_domain_refused=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};units=inv['units'][187:189]
    readings={'M0328':'ω′','M0329':'ν','M0330':'v','M0331':'φ','M0332':'ν′','M0333':'ν′=ν(1−cosφ*v/V)/sqrt(1−(v/V)^2)'}
    return dict(status='cycle_frequency_dependencies_collated_not_whole_source_translation',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']]) for u in units],observations=['原刊911頁ではω′の式から光源の周期数νと観測されるν′へ移る。角周波数と周期数は同一数値ではなく一周期2*piによって結ぶ。','今回の接続は同じ数学的な波の設定と周期の依存群である。光源の静止・無限遠・視線角・知覚・帰結の著者提示は未完なので原文文字範囲や全単位判断を追加しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==370
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert all(d['kind']=='definition' for d in new.document['declarations'][len(old.document['declarations']):])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    dependencies={d['name'] for d in extract_document(new.document,roots=['ekde'],statement_indices=[]).document['declarations']}
    assert {'ekcl','sdv2','sedi','s6k','s6l','seat','seau','seav','sdn2','ekc2','ekc3','ekc6','ekc7','ekdd'}<=dependencies
    assert not dependencies&{'ekbw','ekbx','ekby','ekbz'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,old_370_statements_and_judgments_preserved=True,no_new_source_completion_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('period',period_checks),('normalization',normalization_checks),('frequency',frequency_checks),('temporal',temporal_checks),('trace',trace_checks),('doppler',doppler_checks),('binding',binding_checks),('witness',witness_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_wave_inquiry','check_wave_transform_application','check_resting_charge_force','compose_wave_transform_application','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_wave_cycle_frequency.py','scripts/check_wave_cycle_frequency.py','tests/test_wave_cycle_frequency.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_wave_common_cycle_period_and_frequency_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
