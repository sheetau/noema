"""Check event correspondence, transformed waves, error bounds and attribution."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_resting_charge_force import retag
from scripts.check_wave_inquiry import arithmetic_model,CONSTANTS as PREVIOUS
from scripts.compose_wave_transform_application import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,MEANINGS,FAMILY,SETTING,WAVE,RESULT,COORDS,build

DOC='docs/wave-transform-application-v1.md';SOURCE='data/einstein-wave-transform-application-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p911-0.jpg'
DEPENDENCIES=('reports/wave-inquiry-v1.json','reports/plane-waveforms-v1.json','reports/wave-directions-v1.json','reports/wave-approximation-v1.json','reports/field-transformation-application-v1.json','reports/field-symmetry-conclusion-v1.json')
WITNESSES=[(n,t) for n,t in FAMILY if n not in ('frame','scope','context','light')]
CONSTANTS=PREVIOUS|{'eissh':'application','eissi':'display','eissj':'parameters','zno':'sixth','eisms':'third'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in FAMILY if t=='a'],'eventa','eventb','lab','own','otherlab','otherown','a','b','body','other']))

@lru_cache(None)
def base(name,mode):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sje','szi','soy','shu'}
    if name in ('ekcf','ejtg'):bounds.add('eiyx')
    if name in ('ekcg','ekch'):bounds|={'ekcf','ejtg','ekce','ejsj','s6m'}
    if name=='ekch':bounds.add('ekcg')
    if name=='ekci':bounds|={'ekb3','ekch','ekcc','ekau','ekb2','s6k','s6l'}
    if name=='ekck':bounds|={'ekci','ekbh','seat','ekb2','s6k','s6l','sdx2','ekbf','s6f','sdn2','sdo2','sdp2','seau','seav'}
    if name=='ekcl':bounds|={'ekck','sdq2','sdz2','sdn2','sdo2','sdp2'}
    if name in ('ekcm','ekcn','ekco'):bounds|={'ekci','ekck','ekcl'}
    if mode=='full_domain':bounds-={'ekbh','seat'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='slots':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(t,dict) else t for t in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
    return doc

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(base(name,'slots' if mode.startswith('slot:') else mode));d=next(d for d in doc['declarations'] if d['name']==name)
    if mode.startswith('slot:'):
        pivot=int(mode.split(':')[1]);node=d['body']['body'];retained=None
        for i in range(len(WITNESSES)):
            assert node['kind']=='exists'
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
            node=node['body']
        d['body']['body']=retained|{'body':node}
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jwta'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jwtacapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jwtacapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(value):captured.append(value);return True
    mm['jwtacapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def numbers():
    cuts,m=arithmetic_model();m['shu']=lambda x:cuts.make(abs(cuts.read(x)))
    return cuts,m

def point(c,values):return FunctionValue(('individual',),RS,lambda axis:c(values[('x','y','z','t').index(axis)]) if axis in ('x','y','z','t') else c(0))

@lru_cache(None)
def coordinate_checks():
    cuts,m=numbers();c=cuts.make;cases=0
    for speed,old in product((-3,3),((0,0,0,0),(1,2,-1,1),(-2,3,1,2))):
        x,y,z,t=map(Q,old);new=(Q(5,4)*(x-speed*t),y,z,Q(5,4)*(t-speed*x/25))
        values=[c(5),c(speed),point(c,old),point(c,new)];assert run('ekce',values,m);cases+=1
        for side in (2,3):
            for i in range(4):
                coords=old if side==2 else new;bad=tuple(x+1 if j==i else x for j,x in enumerate(coords));altered=values[:];altered[side]=point(c,bad)
                assert not run('ekce',altered,m);cases+=1
    unknowns(lambda mm:run('ekce',values,mm),m,('sca','sje','soy'))
    return dict(cases=cases,both_directions_and_all_four_coordinates=True,same_event_not_same_numeric_tuple=True)

@lru_cache(None)
def event_checks():
    cuts,m=numbers();c=cuts.make;cases=0
    members={('eventa','process','case'),('eventb','process','case')}
    rows={('eventa','lab','old','case'),('eventa','own','moving','case'),('eventb','otherlab','old','case'),('eventb','otherown','moving','case')}
    mm={'eispo':relation(members),'eiyx':relation(rows)}
    assert run('ekcf',['process','case'],mm);cases+=1
    for row in rows:
        assert not run('ekcf',['process','case'],mm|{'eiyx':relation(rows-{row})});cases+=1
    assert not run('ekcf',['process','case'],mm|{'eispo':lambda *xs:False});cases+=1
    assert run('ejtg',['process','lab','own','case'],mm);cases+=1
    assert not run('ejtg',['process','lab','otherown','case'],mm);cases+=1
    unknowns(lambda model:run('ekcf',['process','case'],model),mm,('eispo','eiyx'))
    # Two-value records diagnose every pair without enumerating large domains.
    for chosen in product(('a','b'),repeat=2):
        pair=lambda proc,lab,own,ctx,chosen=chosen:(proc,lab,own,ctx)==('a',*chosen,'case')
        coords=lambda record,role:c(0 if record=='a' else 1)
        gate=lambda *xs:True
        mm=m|{'ra':lambda:'a','zbm':lambda:'b','ekcf':gate,'ejtg':pair,'zc6':coords,'ekce':gate}
        assert run('ekcg',['a','case',c(5),c(3)],mm,domain=('a','b'));cases+=1
        assert not run('ekcg',['a','case',c(5),c(3)],mm|{'ekce':lambda *xs:False},domain=('a','b'));cases+=1
    oldregion=FunctionValue((RS,)*4,'truth',lambda *xs:True);newregion=FunctionValue((RS,)*4,'truth',lambda *xs:False)
    mm=m|{'ekcg':lambda *xs:True,'ejtg':lambda proc,lab,own,ctx:(lab,own) in (('a','a'),('b','b')),'zc6':lambda record,role:c(0 if record=='a' else 1),'s6m':lambda *xs:newregion}
    for oldset,newset,expected in (({0},{0},True),({0,1},{0,1},True),({0},{1},False),(set(),set(),False)):
        mm['ejsj']=lambda p,reg,oldset=oldset,newset=newset:cuts.read(p('a')) in (oldset if reg(c(0),c(0),c(0),c(0)) else newset)
        assert run('ekch',['a','case',c(5),c(3),oldregion],mm,domain=('a','b'))==expected;cases+=1
    return dict(cases=cases,nonempty_all_events_have_both_records=True,cross_event_pair_rejected=True,local_membership_equivalence_does_not_force_entire_process_inside=True)

def transformed_fixture(direction):
    cuts,m=numbers();c,r=cuts.make,cuts.read;V,s,w=5,3,2;amps=(3,-4,5,-6,7,-8)
    profile=FunctionValue((RS,),RS,lambda phi:c(2*r(phi)+1))
    old=[run('sdx2',[profile,*map(c,(V,w,*direction)),*map(c,part)],m) for part in (amps[:3],amps[3:])]
    fields=[run(n,[c(V),c(s),*old],m) for n in ('s6k','s6l')]
    oldphase=run('ekbf',list(map(c,(V,w,*direction))),m)
    ps=dict(kind='function',parameters=['individual'],result=RS)
    inverse=FunctionValue((ps,),ps,lambda p:run('s46',[c(V),c(-s),p],m))
    phase=run('s6f',[oldphase,inverse],m)
    values=[profile,*map(c,(V,s,w,*direction,*amps)),*fields,phase]
    return cuts,m,values,old,fields

@lru_cache(None)
def wave_checks():
    cases=0
    for direction in ((1,0,0),(0,1,0),(Q(3,5),Q(4,5),0)):
        cuts,m,values,old,fields=transformed_fixture(direction);c,r=cuts.make,cuts.read
        for coords in ((0,0,0,0),(1,2,-1,1),(-2,1,0,3)):
            args=values+list(map(c,coords));assert run('ekcj',args,m);cases+=1
            for side,field in enumerate(fields):
                for axis in ('x','y','z'):
                    broken=FunctionValue(field.parameters,field.result,lambda role,field=field,axis=axis:FunctionValue((RS,)*4,RS,lambda *xs:c(r(field(role)(*xs))+(1 if role==axis else 0))))
                    altered=args[:];altered[len(WAVE)+side]=broken
                    assert not run('ekcj',altered,m);cases+=1
            phase=values[-1];wrong=FunctionValue((RS,)*4,RS,lambda *xs:c(r(phase(*xs))+1));altered=args[:];altered[len(WAVE)+2]=wrong
            assert not run('ekcj',altered,m);cases+=1
    unknowns(lambda mm:run('ekcj',args,mm),m,('soy','sjd','sca'))
    return dict(cases=cases,six_components_and_independent_pulled_back_phase=True,three_directions_nonzero_signed_amplitudes=True,diagnostic_profile_not_claimed_to_be_sine=True)

@lru_cache(None)
def error_checks():
    cuts,m,values,old,fields=transformed_fixture((Q(3,5),Q(4,5),0));c,r=cuts.make,cuts.read;cases=0
    bounds=[run(n,[c(5),c(3),c(1),c(2)],m) for n in ('seau','seav')]
    assert [r(x) for x in bounds]==[Q(11,4),Q(13,4)];cases+=1
    signs=((1,1,1,1,1,1),(-1,-1,-1,-1,-1,-1),(1,1,1,-1,-1,-1),(-1,-1,-1,1,1,1),(1,-1,1,-1,1,-1),(-1,1,-1,1,-1,1))
    xyz=list(map(c,(1,2,-1,1)))
    for sign in signs:
        actual=[]
        for side,f in enumerate(old):
            actual.append(FunctionValue(f.parameters,f.result,lambda axis,f=f,side=side:FunctionValue((RS,)*4,RS,lambda *xs:c(r(f(axis)(*xs))+(1+side)*sign[3*side+('x','y','z').index(axis)]) if axis in ('x','y','z') else c(0))))
        new=[run(n,[c(5),c(3),*actual],m) for n in ('s6k','s6l')]
        for side,axis in product((0,1),('x','y','z')):
            actualvalue=new[side](axis)(*xyz);approx=fields[side](axis)(*xyz)
            assert run('sear',[actualvalue,approx,bounds[side]],m);cases+=1
            if r(actualvalue)!=r(approx):assert not run('sear',[actualvalue,approx,c(0)],m);cases+=1
    return dict(cases=cases,nonzero_errors_and_cross_field_contributions_preserved=True,transformed_bounds_not_zero_or_swapped=True)

@lru_cache(None)
def binding_checks():
    cuts,m=numbers();c=cuts.make;slots=fixture('ekci')[1];pos={n:i for i,(n,t) in enumerate(FAMILY)}
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(FAMILY,slots))];values[pos['light']]=c(5)
    gate=lambda *xs:len(xs)==len(values) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,values,slots))
    region=FunctionValue((RS,)*4,'truth',lambda *xs:True)
    fs=fixture('s6k')[0];field_sort=next(d['result'] for d in fs['declarations'] if d['name']=='s6k')
    transformed=[sentinel(field_sort,70+i,cuts) for i in range(2)]
    mm=m|{'ekb3':gate,'zb7':lambda:c(3),'ekau':lambda *xs:region,'ekb2':lambda *xs:region,'s6k':lambda *xs:transformed[0],'s6l':lambda *xs:transformed[1],'ekch':lambda *xs:True,'ekcc':lambda *xs:True}
    assert run('ekci',values,mm);cases=1
    for i,(name,sort) in enumerate(slots):
        altered=values[:];altered[i]=sentinel(sort,120+i,cuts)
        assert not run('ekci',altered,mm);cases+=1
    expected=(values[pos['process']],'case',c(5),c(3),region)
    region_sort=dict(kind='function',parameters=[RS]*4,result='truth')
    def localgate(*xs):return len(xs)==5 and xs[0:2]==expected[0:2] and cuts.read(xs[2])==5 and cuts.read(xs[3])==3 and same_value(xs[4],region,region_sort,cuts)
    assert run('ekci',values,mm|{'ekch':localgate});cases+=1
    for name in ('ekb3','ekch','ekcc'):
        assert not run('ekci',values,mm|{name:lambda *xs:False});cases+=1
    for root,checks in (('ekck',('ekci','ekbh','seat')),('ekcl',('ekck','sdq2','sdz2'))):
        local=m|{'zb7':lambda:c(3),**{n:lambda *xs:True for n in checks}}
        # Numeric/function boundaries are only for the composition gate; native bodies are checked above.
        for d in fixture(root)[0]['declarations']:
            if d['kind']=='primitive' and d['name'] not in local and d['name'] not in CONSTANTS and not d['name'].startswith('jwta'):
                result=sentinel(d['result'],2,cuts);local[d['name']]=lambda *xs,result=result:result
        assert run(root,values,local);cases+=1
        for n in checks:assert not run(root,values,local|{n:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekci',values,model),mm,('ekb3','ekch','ekcc','s6k','s6l'))
    return dict(cases=cases,all_41_setting_roles_shared=True,physical_coordinate_and_field_application_and_error_gates_required=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for root,rule in (('ekcm','ekci'),('ekcn','ekck'),('ekco','ekcl')):
        for pivot,(name,sort) in enumerate(WITNESSES):
            for target in ('a','b','unavailable'):
                expected={n:'a' for n,t in FAMILY};expected.update(frame='a',scope='b',context='case',light='a');expected[name]=target
                values=[expected[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot];row=tuple(expected[n] for n,t in FAMILY)
                m={'ra':lambda:'a','eisrx':lambda:'b','tc':lambda:'a',rule:lambda *xs,row=row:tuple(xs)==row}
                assert run(root,values,m,'slot:'+str(pivot),('a','b'))==(target!='unavailable');cases+=1
                if target!='unavailable':assert not run(root,values,m|{rule:lambda *xs:False},'slot:'+str(pivot),('a','b'));cases+=1
    cuts,m=numbers()
    try:run('ekcn',[],m|{'tc':lambda:cuts.make(5),'ekck':lambda *xs:True})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full setting function domain finitely enumerated')
    return dict(cases=cases,witnesses_per_content=len(WITNESSES),same_37_witnesses_for_application_display_and_parameter_explanation=True,whole_function_domain_refused=True)

@lru_cache(None)
def presentation_checks():
    fixtures={
      'ekcp':{'eissg':{('application','author','question','ekbn','ekci','ekcl',True,'scope','case')},'eisov':{('application','author','sixth','ejvm','paper','case'),('application','author','third','ejeh','paper','case')},'uf':{('author','application','display','case')},'ue':{('application','display','case')}},
      'ekcs':{'eisox':{('display','ekcn','case')}},
      'ekcv':{'eissb':{('parameters','display','author','ekcn','ekco','scope','case')},'eisox':{('parameters','ekco','case')},'uf':{('author','display','parameters','case')}}}
    for n,msg,node,prior in (('ekcr','ekcq','application','question'),('ekcu','ekct','display','application'),('ekcx','ekcw','parameters','display')):
        fixtures[n]={'eir3':{(node,'author','paper',msg,'case')},'ue':{(prior,node,'case')}}
    cases=0
    for root,rows in fixtures.items():cases+=perturb(lambda mm:run(root,[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    m={n:relation(rs) for n,rs in fixtures['ekcp'].items()}
    assert run('ekcp',[],m|{n:forbidden for n in ('ekbn','ekci','ekcl','ejvm','ejeh')});cases+=1
    wrong=('application','author','question','ekbn','ekci','ekcl',False,'scope','case')
    assert not run('ekcp',[],m|{'eissg':relation({wrong})});cases+=1
    return dict(cases=cases,both_correct_sections_and_final_laws_used=True,immediate_application_forward_display_and_wobei_preserved=True,quoted_laws_not_automatically_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings={'M0324':'k','M0325':'X′=X0 sin Φ′; Y′=β(Y0−v N0/V) sin Φ′; Z′=β(Z0+v M0/V) sin Φ′; L′=L0 sin Φ′; M′=β(M0+v Z0/V) sin Φ′; N′=β(N0−v Y0/V) sin Φ′.','M0326':'Φ′=ω′(τ−(a′ξ+b′η+c′ζ)/V).','M0327':'ω′=ωβ(1−av/V); a′=(a−v/V)/(1−av/V); b′=b/(β(1−av/V)); c′=c/(β(1−av/V)).'}
    for n,equals in (('M0325',6),('M0326',1),('M0327',4)):
        tokens=[x.text for x in ET.fromstring(math[n]['mathml']).iter() if x.text];assert tokens.count('=')==equals
    for i in range(181,187):
        u=inv['units'][i];assert digest(u['text'].encode())==u['text_sha256'];text=u['text'];indices=[366,367] if i==181 else [368] if i in (182,183) else [369]
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(text)],text=text,statements=indices,math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text))))
    return dict(status='both_transformations_seven_equations_and_four_parameters_collated',segments=segments,observations=['原刊911頁の両変換の適用、七表示式、wobeiと四つのパラメータ式、gesetzt ist.を一続きに照合した。','固定在庫のM0325は六成分、M0326は位相、M0327が角周波数と三方向の四式である。以前の再開情報の番号説明を訂正し、原資料は保持する。','前後の波の仮定と同じ対象・近似・単位を共有する。全過程の出来事を局所領域の内部へ限定しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==370 and new.document['statements'][:367]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,INDICES)['dependencies']);assert set(MEANINGS)-{'ekcj','ekcm'}<=names
    assert {'ekca','ekcc','ekb3','ekbl','eispo','eiyx','s6k','s6l','s6m','s6f','seat','seau','seav','sdq2','sdz2'}<=names
    # Historical field references occur in the quoted laws, but never in the new physical rule itself.
    physical={d['name'] for d in extract_document(new.document,roots=['ekci','ekck','ekcl'],statement_indices=[]).document['declarations']}
    assert not physical&{'znl','znm','eispp','seaj','ekbw','ekbx','ekby','ekbz'}
    # cf occurs in the inherited light-signal coordinate protocol eiyx, not as a new classification of this wave.
    def calls(node):
        if isinstance(node,list):return set().union(*(calls(x) for x in node))
        if isinstance(node,dict):return ({node['symbol']} if node.get('kind')=='call' else set())|set().union(*(calls(x) for x in node.values()))
        return set()
    assert all('cf' not in calls(d) for d in new.document['declarations'][len(old.document['declarations']):])
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=3,old_367_statements_and_judgments_preserved=True,physical_rules_use_current_wave_not_prior_section_fields=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('coordinates',coordinate_checks),('events',event_checks),('waves',wave_checks),('errors',error_checks),('binding',binding_checks),('witness',witness_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_resting_charge_force','check_wave_inquiry','compose_wave_inquiry','compose_wave_display','compose_distant_wave_source','compose_field_equations','compose_field_transformation_application','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_wave_transform_application.py','scripts/check_wave_transform_application.py','tests/test_wave_transform_application.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='same_wave_both_transformations_display_and_parameter_explanation_connected',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
