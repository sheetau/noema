"""Check volume naming, same-setting quotient, calculation and presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from noema.polynomial_proofs import verify_universal
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import NUM
from scripts.check_light_region_slices import setup
from scripts.check_light_ellipsoid_surface import CONSTANTS as PRIOR_CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.check_resting_charge_force import retag
from scripts.check_wave_cycle_frequency import refused
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.check_calculation_discourse import sequence,pair,symbol
from scripts.compose_light_complex import generic_composed
from scripts.compose_light_volume_ratio import *
from scripts.read_light_volume_ratio import DOC,SOURCE,INVENTORY,READING,PRIOR,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'eistw':'volumeintro','eistx':'volumedisplay','eisty':'oldvolumename','eistz':'newvolumename'}
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,*CONSTANTS.values(),'method']))
DEPENDENCIES=('reports/light-ellipsoid-surface-v1.json','reports/geometric-volumes-v1.json','reports/distant-direction-geometry-v1.json','reports/calculation-discourse-v1.json')
BOUNDS={'ekoz':{'ekoy'},'ekpa':{'ekn7'},'ekpb':{'ekn7'},'ekpd':{'ekn7','sedp','sca'},'ekpe':{'ekn7','ekoz'},'ekpf':{'ekpd','ekpe'},'ekpg':{'ekos','ekpd','ekpe','ekpf','ekpa','ekpb'},'ekpi':{'ekph'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:') or mode=='binding':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        if mode.startswith('slot:'):
            d=next(d for d in doc['declarations'] if d['name']==name);isname=name in ('ekpa','ekpb');body=d['body'] if isname else d['body']['body'];variables=name_variables('volume' if name=='ekpa' else 'newvolume')[1] if isname else VARIABLES
            pivot=int(mode.split(':')[1]);retained=None
            for i,(n,t) in enumerate(variables):
                assert body['kind']==('exists' if isname else 'forall')
                if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
                else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
                body=body['body']
            if isname:d['body']=retained|{'body':body}
            else:d['body']['body']=retained|{'body':body}
    if name=='ekpf':
        pairs=json.loads(mode);prefix='n:r ekpd[] e.r ekpe[] e.r jlvrmid[] e.r jlvrprogram[a d '+STEPS+'] '+STEPS+'.'
        helper=parse(prefix)['declarations'][-1];replacement=parse(prefix+'d zlx[method a stage d] '+STEPS+'[k jlvrprogram[v method v stage '+sequence(pairs)+']].')['declarations'][-1]
        doc['declarations']=[d for d in doc['declarations'] if d['name']!='zlx'];missing={n for p in pairs for n in p}-{d['name'] for d in doc['declarations']};at=next(i for i,d in enumerate(doc['declarations']) if d['name']==name)
        doc['declarations'][at:at]=[dict(kind='primitive',name=n,parameters=[],result='content') for n in sorted(missing)]+[helper,replacement]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jlvr'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jlvrcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jlvrcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jlvrcapture']=capture;mm.setdefault('jlvrprogram',lambda method,stage,seq:seq if (method,stage)==('method','case') else SequenceValue((),seq.element_type))
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def numeric_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    # The native evaluator is eager. Supply an off-domain reciprocal so the
    # explicit positive-volume guard, rather than Python division, rejects zero.
    m=m|{'sjd':lambda x:c(1/r(x) if r(x) else 0)}
    for speed in (-3,0,3):
        for co in (-1,Q(-3,5),0,Q(1,3),Q(3,5),1):
            root=Q(4,5) if speed else Q(1);ratio=root/(1-Q(speed,5)*co)
            assert r(run('ekox',list(map(c,(5,speed,co))),m))==ratio;cases+=1
            values=(5,speed,co,8,8*ratio)
            assert run('ekoy',list(map(c,values)),m);cases+=1
            for bad in ((*values[:4],values[4]+1),(*values[:3],values[4],values[3]),(*values[:3],0,values[4]),(*values[:3],values[3],-values[4])):
                expected=bad[3]>0 and bad[4]>0 and Q(bad[4])/bad[3]==ratio
                assert run('ekoy',list(map(c,bad)),m)==expected;cases+=1
    good=(5,3,0,8,Q(32,5));values=list(map(c,good))
    unknowns(lambda mm:run('ekoy',values,mm),m,('ba','sky','sjd','sca'))
    for bad in ((5,5,0,8,8),(5,-5,0,8,8),(0,0,0,8,8),(5,3,2,8,8),(5,3,-2,8,8),(5,3,0,0,8)):
        for undefined in (0,17):
            mm=m|{'sjd':lambda x:c(1/r(x) if r(x) else undefined),'sky':lambda x:m['sky'](x) if r(x)>=0 else c(undefined)}
            assert not run('ekoy',list(map(c,bad)),mm);cases+=1
    # In the valid oblique direction cos(phi)=1/3, the volumes can coincide.
    assert run('ekoy',list(map(c,(5,3,Q(1,3),8,8))),m);cases+=1
    return dict(cases=cases,printed_quotient_direction_root_and_cosine_preserved=True,positive_volumes_and_denominator_required=True,exceptional_equal_volume_direction_kept=True)

@lru_cache(None)
def binding_checks():
    cases=0
    for name in ('ekpd','ekpe'):
        for pivot,(var,sort) in enumerate(VARIABLES):
            mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)};values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            for value in ('a','b'):
                assigned=base|{var:value,'frame':'a','light':'a','scope':'b','portion':'b','context':'case'};row=tuple(assigned[n] for n,t in SETTING)
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b','ekn7':lambda *xs,row=row:xs==row}
                targets={'ekoz':row} if name=='ekpe' else {'sedp':tuple(assigned[n] for n,t in VOLUMES),'sca':(assigned['anglecos'],assigned['ax'])}
                mm|={n:lambda *xs,row=row:xs==row for n,row in targets.items()}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                for target in targets:
                    assert not run(name,values,mm|{target:lambda *xs:False},mode,('a','b'));cases+=1
                bad=assigned|{var:'a' if value=='b' else 'b'}
                for target,names in ([('ekoz',SETTING)] if name=='ekpe' else [('sedp',VOLUMES),('sca',[('anglecos',R),('ax',R)])]):
                    wrong=tuple(bad[n] for n,t in names)
                    assert run(name,values,mm|{target:lambda *xs,row=wrong:xs==row},mode,('a','b'))==(var not in {n for n,t in names});cases+=1
            assert run(name,values,mm|{'ekn7':lambda *xs:False}|{n:lambda *xs:False for n in targets},mode,('a','b'));cases+=1
            unknowns(lambda mod:run(name,values,mod,mode,('a','b')),mm,('ekn7',*targets))
        refused(lambda:run(name,[],{}));cases+=1
    values=['a' if i%2==0 else 'b' for i in range(len(SETTING))];values[[n for n,t in SETTING].index('context')]='case';row=tuple(values[[n for n,t in SETTING].index(n)] for n,t in RATIO)
    assert run('ekoz',values,{'ekoy':lambda *xs:xs==row},'binding',('a','b'));cases+=1
    for n,t in RATIO:
        bad=values[:];i=[n0 for n0,t0 in SETTING].index(n);bad[i]='b' if bad[i]=='a' else 'a'
        assert not run('ekoz',bad,{'ekoy':lambda *xs:xs==row},'binding',('a','b'));cases+=1
    for name,which in [('ekpa','volume'),('ekpb','newvolume')]:
        variables=name_variables(which)[1]
        for pivot,(var,sort) in enumerate(variables):
            base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(variables)};values=['b','a','case']+[base[n] for i,(n,t) in enumerate(variables) if i!=pivot];mode=f'slot:{pivot}'
            for value in ('a','b'):
                assigned=base|{var:value,'frame':'a','light':'a','scope':'b','portion':'b','context':'case',which:'a'};row=tuple(assigned[n] for n,t in SETTING)
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekn7':lambda *xs,row=row:xs==row}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                assert not run(name,values,mm|{'ekn7':lambda *xs:False},mode,('a','b'));cases+=1
                for i in range(3):
                    bad=values[:];bad[i]='other' if i==2 else ('b' if bad[i]=='a' else 'a')
                    assert not run(name,bad,mm,mode,('a','b'));cases+=1
            unknowns(lambda mod:run(name,values,mod,mode,('a','b')),mm,('ekn7',))
        cuts,m=setup();refused(lambda:run(name,['body',cuts.make(8),'case'],m));cases+=1
    return dict(cases=cases,all_63_shared_context_roles_and_62_name_witnesses_checked=True,same_setting_both_volumes_and_angle=True,native_infinite_domains_refused=True)

@lru_cache(None)
def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);sub=lambda a,b:k('ab',a,k('ac',b));eq=lambda a,b:op('e',a,b);one='n p b b'
    root,beta,den,invden,S,T,invS=map(v,('root','beta','den','invden','old','new','invold'))
    premise=both(eq(mul(root,beta),one),eq(mul(den,invden),one),eq(mul(S,invS),one),eq(mul(mul(beta,den),T),S))
    claim=assertion('root beta den invden old new invold',op('y',premise,eq(mul(T,invS),mul(root,invden))))
    base=generic_composed()[0];result=verify_universal(parse(base+claim),POLYNOMIAL,timeout_ms=20000)[0];assert result['status']=='valid',result
    return dict(lemmas={'volume_identity_to_printed_ratio':result},rational_polynomial_only=True,prior_integral_endpoint_proofs_reused_not_fundamental_theorem_proved=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislo':{('oldvolumename','ekpa','paper','case'),('newvolumename','ekpb','paper','case')},'uh':{('volumeintro','author','ekpe','section8','case'),('volumeintro','author','ekpf','section8','case')},'eisox':{('volumedisplay','ekpe','case')},'uf':{('author','volumeintro','volumedisplay','case')},'ue':{('volumeintro','volumedisplay','case')},'eisra':{('volumeintro','author','paper','ellipsoidintro','ekos','ekpd','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mod:run('ekpg',[],mod),mm,rows)
    assert run('ekpg',[],mm|{n:forbidden for n in ('ekpa','ekpb','ekos','ekpd','ekpe','ekpf')});cases+=1
    rows={'eir3':{('volumeintro','author','paper','ekph','case')},'ue':{('ellipsoidintro','volumeintro','case')}};mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda mod:run('ekpi',[],mod),mm,rows)
    for n,val in [('eistw','ellipsoidintro'),('eistx','volumeintro'),('eistz','oldvolumename')]:assert not run('ekpi',[],{n:lambda *xs:True for n in rows}|{n:lambda:val});cases+=1
    return dict(cases=cases,names_claim_easy_calculation_colon_display_and_back_reference_preserved=True,quoted_contents_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==392 and new.document['statements'][:391]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[390])==selection_binding(old,[390]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    ann=json.loads(read(ANNOTATIONS));assert ann['entries'][:-2]==json.loads(read('data/light-ellipsoid-surface-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'sedp','ekl4','ekn7','ekdq','s2y','eislo'}<=names
    assert not {'sech','ekml'}&names
    # Preserve the actual inherited angle path; the ratio has not been inserted into its premise.
    declarations={d['name']:d for d in new.document['declarations']}
    setting_names={d['name'] for d in extract_document(new.document,roots=['ekn7'],statement_indices=[]).document['declarations']}
    assert {'eklp','eklf','eket','ekdq','ekdp','ekdn','sedp'}<=setting_names
    assert not (set(MEANINGS)|{'sech','ekml'})&setting_names
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(new,[INDEX]);assert reading['reviewed_math_elements']==3
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=4,all_391_statements_and_judgments_preserved=True,reviewed_prose_characters=reading['reviewed_prose_characters'],reviewed_math_elements=3)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('bindings',binding_checks),('calculation',chain_checks),('polynomial',polynomial_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_light_ellipsoid_surface','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_calculation_discourse','compose_limits','compose_light_complex','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_light_region_slices','check_light_ellipsoid_surface','check_resting_charge_force','check_wave_cycle_frequency','check_real_products','check_calculation_discourse','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_light_volume_ratio.py','scripts/check_light_volume_ratio.py','scripts/read_light_volume_ratio.py','tests/test_light_volume_ratio.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_light_volumes_named_ratio_and_calculation_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def chain_checks():
    good=[('ekpd','jlvrmid'),('jlvrmid','ekpe')];count=0
    cases=((good,2,{},True),([('ekpd','ekpe')],1,{},True),([],2,{},False),(list(reversed(good)),2,{},False),([good[1]],2,{},False),([good[0]],2,{},False),([good[0],('ekpd','ekpe')],2,{},False),(good,1,{},False),(good,2,{good[0]:-1},False),([good[0],('jlvrmid','jlvrmid'),good[1]],2,{},False),([good[0],('jlvrmid','jlvrmid'),good[1]],3,{},True),(good,0,{('ekpd','ekpe'):0},False))
    for pairs,budget,costs,expected in cases:
        m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','case'),'zla':lambda a,b,s:s=='case','zlb':lambda step,s:Q(costs.get(pair(step),1)),'zlc':lambda n,s:s=='case' and n<=budget}
        assert run('ekpf',[],m,json.dumps(pairs))==expected;count+=1
    m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','case'),'zla':lambda a,b,s:s=='case' and (symbol(a),symbol(b)) in good,'zlb':lambda step,s:Q(1 if s=='case' else 10),'zlc':lambda n,s:s=='case' and n<=2};mode=json.dumps(good)
    for patch in ({'zlw':lambda *xs:False},{'rd':lambda:'other'},{'zlw':lambda a,p,s:(a,p,s)==('author','other','case')},{'zlw':lambda a,p,s:(a,p,s)==('author','method','other')},{'zla':lambda a,b,s:(symbol(a),symbol(b))==good[0]},{'zlb':lambda step,s:Q(10)},{'zlc':lambda n,s:s=='other' and n<=2},{'jlvrprogram':lambda p,s,seq:seq if (p,s)==('other','case') else SequenceValue((),seq.element_type)}):
        assert not run('ekpf',[],m|patch,mode);count+=1
    unknowns(lambda mm:run('ekpf',[],mm,mode),m,('zlw','zla','zlb','zlc'))
    assert run('ekpf',[],m|{n:forbidden for n in ('ekpd','ekpe','ejpa','s2t','ejoi','ejoj','ejow')},mode);count+=1
    return dict(cases=count,native_connected_nonempty_chain_and_nonnegative_total=True,same_available_method_stage_premise_result_and_burden=True,no_fixed_step_count_or_cost_threshold=True,quoted_conclusion_not_executed_as_true=True)


