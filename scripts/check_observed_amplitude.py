"""Check calibrated amplitude candidates and nonfactive source presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,QuestionValue
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
from scripts.check_aberration_specialization import CONSTANTS,DOMAIN
from scripts.check_wave_amplitudes import reviewed_formula
from scripts.compose_observed_amplitude import *
CONSTANTS=CONSTANTS|{'eiss5':'amplitudeintro','eiss6':'amplitudedisplay','eiss7':'oldname','eista':'newname','eissf':'inquiry'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values()]))
DOC='docs/observed-amplitude-v1.md';SOURCE='data/einstein-observed-amplitude-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
COLLATION='data/wave-amplitudes-facsimile-v1.json'
DEPENDENCIES=('reports/aberration-specialization-v1.json','reports/wave-amplitudes-v1.json','reports/wave-transform-application-v1.json','reports/doppler-specialization-v1.json')
BOUNDS={'ekib':{'eket','ekia'},'ekic':{'eket'},'ekid':{'eket'},'ekie':{'eket'},'ekif':{'ekie','ekhz'},'ekig':{'ekic'},'ekik':{'ekib','ekij'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sky','soy','szi','shu','ejor','sedi'}|BOUNDS.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);iscontent=d['result']=='content';body=d['body']['body'] if iscontent else d['body'];pivot=int(mode.split(':')[1]);retained=None
        fields=NAME_WITNESSES if name in ('ekif','ekig') else VARIABLES
        for i in range(len(fields)):
            assert body['kind']==('exists' if name in ('ekif','ekig') else 'forall')
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        if iscontent:d['body']['body']=retained|{'body':body}
        else:d['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='joam'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='joamcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='joamcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['joamcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def values_for(fields,cuts,root):
    slots=fixture(root)[1]
    return [n if t=='a' else 'case' if t=='d' else False if t=='c' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(fields,slots))]

@lru_cache(None)
def numeric_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for side,amp in product((False,True),(-5,0,5,12,13)):
        assert run('ekhz',[side,*map(c,(3,4,0,0,0,12,amp))],m)==(amp==(12 if side else 5));cases+=1
    # Exact rational transverse vectors: H=n cross E, both magnitudes are |scale|.
    for ratio,n,E,scale in product((Q(-3,5),Q(0),Q(3,5),Q(5,13)),((1,0,0),(0,1,0),(Q(3,5),Q(4,5),0)),((0,0,1),),(Q(-2),Q(0),Q(3))):
        V=Q(5);speed=V*ratio;H=(n[1],-n[0],0);old=[scale*x for x in (*E,*H)]
        beta=r(m['soy'](c(V),c(speed)));factor=beta*(1-ratio*n[0]);A=abs(scale);newA=A*factor
        vals=values_for(SETTING,cuts,'ekia');pos={n:i for i,(n,t) in enumerate(SETTING)}
        for name,x in dict(light=V,speed=speed,anglecos=n[0],amplitude=A,newamplitude=newA,**dict(zip(AMP_NAMES,old))).items():vals[pos[name]]=c(x)
        for side in (False,True):
            vals[pos['magneticside']]=side;assert run('ekia',vals,m);cases+=1
            assert run('ekij',vals,m);cases+=1
            assert r(run('ekii',list(map(c,(V,speed,n[0],A))),m))==newA*newA;cases+=1
        if A:
            vals[pos['newamplitude']]=c(-newA);assert not run('ekia',vals,m);cases+=1
    # Do not impose transverse equality as the meaning of choosing E or H.
    vals=values_for(SETTING,cuts,'ekia');pos={n:i for i,(n,t) in enumerate(SETTING)}
    for name,x in dict(light=5,speed=3,anglecos=1,amplitude=1,newamplitude=1,ex=1,ey=0,ez=0,hx=0,hy=0,hz=0).items():vals[pos[name]]=c(x)
    assert run('ekia',vals,m);assert not run('ekij',vals,m);cases+=2
    vals[pos['magneticside']]=True;assert not run('ekia',vals,m);cases+=1
    # Printed denominator is squared gamma, not gamma alone.
    assert r(run('ekii',list(map(c,(5,3,0,1))),m))==Q(25,16)!=Q(5,4);cases+=1
    unknowns(lambda mm:run('ekhz',[False,*map(c,(3,4,0,0,0,12,5))],mm),m,('sca','bc','shv'))
    unknowns(lambda mm:run('ekii',list(map(c,(5,3,0,1))),mm),m,('sjd','shv','bf'))
    return dict(cases=cases,same_side_nonnegative_magnitudes=True,transverse_cases_match_square_ratio=True,nontransverse_counterexample_not_hidden=True,facsimile_denominator_distinguished=True)

@lru_cache(None)
def binding_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    values=values_for(SETTING,cuts,'ekib');slots=fixture('ekib')[1]
    gate=lambda xs,ys,ss:len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,ss))
    mm=m|{'eket':lambda *xs:gate(xs,values[:60],slots[:60]),'ekia':lambda *xs:gate(xs,values,slots)}
    assert run('ekib',values,mm);cases+=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=not changed[i] if s=='truth' else sentinel(s,100+i,cuts)
        assert not run('ekib',changed,mm);cases+=1
    unknowns(lambda model:run('ekib',values,model),mm,('eket','ekia'))
    query=values_for(QUESTION,cuts,'ekid');qs=fixture('ekid')[1];pos={n:i for i,(n,t) in enumerate(QUESTION)}
    for name,x in dict(light=5,speed=3,ex=0,ey=3,ez=4,hx=0,hy=-4,hz=3).items():query[pos[name]]=c(x)
    qm=m|{'eket':lambda *xs:gate(xs,query[:60],qs[:60])}
    question=run('ekid',query,qm);assert isinstance(question,QuestionValue);assert question.function(c(Q(5,2)));cases+=1
    for value in (-5,Q(-5,2),0,5,10):assert not question.function(c(value));cases+=1
    for i,(n,s) in enumerate(qs[:60]):
        changed=query[:];changed[i]=sentinel(s,200+i,cuts)
        # Both the fixed condition and the question use exactly the same old setting.
        assert not run('ekie',changed,qm);cases+=1
    for side in (False,True):
        query[-1]=side;assert run('ekid',query,qm).function(c(Q(5,2)));cases+=1
    unknowns(lambda model:run('ekid',query,model).function(c(Q(5,2))),qm,('eket','soy','sjd','sca'))
    return dict(cases=cases,all_63_setting_roles_bound=True,question_keeps_61_fixed_inputs_outside_candidate=True,calibration_and_approximation_inherited_without_new_records=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for root,fields,premise,conclusion in [('ekik',VARIABLES,'ekib','ekij'),('ekif',NAME_WITNESSES,'ekie','ekhz'),('ekig',NAME_WITNESSES,'ekic',None)]:
        for pivot,(name,t) in enumerate(fields):
            for target in ((False,True) if t=='c' else ('a','b','unavailable')):
                expected={n:False if t=='c' else 'a' for n,t in SETTING};expected.update(context='case',scope='b',amplitude='b',newamplitude='b');expected[name]=target
                exp=lambda fs:tuple(expected[n] for n,t in fs)
                const={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b'}
                vals=[expected[n] for i,(n,t) in enumerate(fields) if i!=pivot]
                if root=='ekik':
                    row=exp(SETTING);mm=const|{premise:lambda *xs,row=row:tuple(xs)==row,conclusion:lambda *xs:False}
                    assert run(root,vals,mm,'slot:'+str(pivot),('a','b'))==(target=='unavailable');cases+=1
                    assert run(root,vals,mm|{conclusion:lambda *xs,row=row:tuple(xs)==row},'slot:'+str(pivot),('a','b'));cases+=1
                else:
                    vals=['a','b','case']+vals;row=exp(QUESTION)
                    if root=='ekif':
                        mag=(expected['magneticside'],*(expected[n] for n in AMP_NAMES),'b')
                        mm=const|{'ekie':lambda *xs,row=row:tuple(xs)==row,'ekhz':lambda *xs,mag=mag:tuple(xs)==mag}
                    else:
                        row=(*row,'b');mm=const|{'ekic':lambda *xs,row=row:tuple(xs)==row}
                    assert run(root,vals,mm,'slot:'+str(pivot),('a','b'))==(target!='unavailable');cases+=1
        unknowns(lambda model:run(root,vals,model,'slot:'+str(pivot),('a','b')),mm,(premise,))
    cuts,m=setup();refused(lambda:run('ekik',[],m|{'tc':lambda:cuts.make(5),'ekib':lambda *xs:True,'ekij':lambda *xs:True}))
    return dict(cases=cases,universal_roles=59,naming_witnesses_each=56,boolean_side_shared_at_every_position=True,no_finite_substitute_for_real_domain=True)

@lru_cache(None)
def presentation_checks():
    rows={
     'ekin':{'eiss4':{('amplitudeintro','author','inquiry','ekbn','ekie','ekid',True,'scope','case')}},
     'ekih':{'eislo':{('oldname','ekif','paper','case'),('newname','ekig','paper','case')}},
     'ekir':{'eisox':{('amplitudedisplay','ekik','case')}},
     'ekiq':{'eir3':{('amplitudeintro','author','paper','ekip','case')},'ue':{('specialdisplay','amplitudeintro','case')}},
     'ekit':{'eir3':{('amplitudedisplay','author','paper','ekis','case')},'ue':{('amplitudeintro','amplitudedisplay','case')}}}
    rows['ekio']=rows['ekin']|rows['ekih']|{'eissb':{('amplitudeintro','parameters','author','ekco','ekim','scope','case')},'zc':{('amplitudeintro','author','ekim','ekik','scope','case')},'uf':{('author','amplitudeintro','amplitudedisplay','case')},'ue':{('amplitudeintro','amplitudedisplay','case')}}
    cases=0
    for root,rs in rows.items():cases+=perturb(lambda mm:run(root,[],mm),{n:relation(vs) for n,vs in rs.items()},rs)
    return dict(cases=cases,remaining_task_names_consequence_colon_and_display_connected=True,closed_quotes_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={x['id']:x for x in inv['math']};meta=json.loads(read(COLLATION));segments=[]
    reviewed=reviewed_formula(math['M0345']['mathml'],meta['correction'])
    readings={'M0343':'A','M0344':'A′','M0345':'A′²=A²(1−(v/V)cosφ)²/(1−(v/V)²)'}
    for i in range(196,198):
        u=inv['units'][i];assert digest(u['text'].encode())==u['text_sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],statements=[379+i-196],math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert digest((ROOT/FACSIMILE).read_bytes())==meta['image_sha256']
    return dict(status='amplitude_task_names_measurement_roles_and_square_ratio_collated',segments=segments,observations=LIMITS,correction=dict(record=COLLATION,snapshot_mathml=math['M0345']['mathml'],reviewed_mathml=reviewed,reviewed_math_sha256=digest(reviewed.encode())),source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,COLLATION,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==381 and new.document['statements'][:379]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    ann=load_annotations(ROOT,BASIS,ANNOTATIONS);assert [x['forms'][0]['text'] for x in ann.annotations['entries'][-2:]]==['A','A′']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=4,old_379_statements_and_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('binding',binding_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_aberration_specialization','check_wave_amplitudes','check_wave_cycle_frequency','check_resting_charge_force','compose_doppler_specialization','compose_wave_transform_application','compose_aberration_presentation','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_observed_amplitude.py','scripts/check_observed_amplitude.py','tests/test_observed_amplitude.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='calibrated_amplitude_task_names_and_square_ratio_connected',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
