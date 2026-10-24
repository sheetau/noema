"""Check local phase rays, angle naming and nonfactive equation presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re,xml.etree.ElementTree as ET
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
from scripts.check_aberration_line import setup,DIRECTIONS
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_doppler_specialization import CONSTANTS,DOMAIN
from scripts.compose_aberration_presentation import *

CONSTANTS=CONSTANTS|{'eisst':'infinity','eissv':'angleintro','eissw':'angledisplay','eissx':'phiname','eissy':'prioraxial'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values(),'body',*(n for n,t in SETTING if t=='a')]))
DOC='docs/aberration-presentation-v1.md';SOURCE='data/einstein-aberration-presentation-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
DEPENDENCIES=('reports/aberration-line-v1.json','reports/wave-transform-application-v1.json','reports/doppler-specialization-v1.json')
BOUNDS={'ekgv':{'ekgu'},'ekgw':{'ekbk'},'ekgx':{'ekgv','ekgw'},'ekgy':{'ekgn','ekhl'},'ekgz':{'ekgy'},'ekhl':{'ekgx'},'ekhb':{'ekgy','ekha'},'ekhc':{'ekgy','ekgo'},'ekhd':{'ekgn','ekhl'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','soy','sky','szi','shu'}|BOUNDS.get(name,set())
    if mode.startswith('scope:'):bounds.add('ekgt')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('scope:'):
        def replace(node):
            if node==RS:return 'individual'
            if isinstance(node,list):return [replace(x) for x in node]
            if isinstance(node,dict):return {k:replace(x) for k,x in node.items()}
            return node
        doc=replace(doc)
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='expose' or mode.startswith(('slot:','scope:')):
        content_result=d['result']=='content';body=d['body']['body'] if content_result else d['body']
        fields=NAME_WITNESSES if name=='ekgz' else RAY_VARS if name=='ekgv' else NORMAL_VARS if name=='ekgw' else VARIABLES
        pivot=None if mode=='expose' else int(mode.split(':')[1]);retained=None
        for i in range(len(fields)):
            assert body['kind']==('exists' if name=='ekgz' else 'forall')
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        final=retained|{'body':body} if retained else body
        if content_result:d['body']['body']=final
        else:d['body']=final
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jabp'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jabpcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jabpcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jabpcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def phase(cuts,V,rate,n,sign=-1):
    c,r=cuts.make,cuts.read
    return FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(rate*(r(t)+sign*sum(a*r(p) for a,p in zip(n,(x,y,z)))/V)))

@lru_cache(None)
def motion_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for V,w,n,p,dt in product((Q(1),Q(5)),(Q(2,3),Q(3)),DIRECTIONS,((0,0,0,0),(2,-1,3,4)),(-1,0,1,2)):
        end=run('ekgt',list(map(c,(V,*n,*p,dt))),m)
        assert tuple(r(end(a)) for a in ('x','y','z','t'))==(*(x+V*a*dt for x,a in zip(p[:3],n)),p[3]+dt);cases+=1
        args=list(map(c,(V,w,*n)))+[phase(cuts,V,w,n)]+list(map(c,(*p,dt)))
        assert run('ekgu',args,m)==(dt>0);cases+=1
        if dt>0:
            args[5]=phase(cuts,V,w,n,1);assert not run('ekgu',args,m);cases+=1
    args=list(map(c,(5,2,1,0,0)))+[phase(cuts,5,2,(1,0,0))]+list(map(c,(0,0,0,0,1)))
    unknowns(lambda mm:run('ekgu',args,mm),m,('ba','bg','sca','shv'))
    return dict(cases=cases,forward_phase_motion_uses_light_speed_not_phase_rate=True,opposite_direction_rejected=True,positive_elapsed_and_same_four_coordinates=True)

@lru_cache(None)
def scope_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    region=FunctionValue((RS,)*4,'truth',lambda x,y,z,t:0<=r(x)<=10 and 0<=r(t)<=2)
    optical=list(map(c,(5,2,1,0,0)))+[phase(cuts,5,2,(1,0,0)),region]
    for x,t,dt in product((-1,0,5,10),(0,1,2),(-1,0,1,2)):
        inside=0<=x<=10 and 0<=t<=2 and dt>0 and 0<=x+5*dt<=10 and 0<=t+dt<=2
        assert run('ekgv',optical+list(map(c,(x,0,0,t,dt))),m|{'ekgu':lambda *xs:False},'expose')==(not inside);cases+=1
    for x,otherx,t in product((-1,0,10),(-1,0,10),(0,2,3)):
        inside=0<=x<=10 and 0<=otherx<=10 and 0<=t<=2
        assert run('ekgw',optical+list(map(c,(x,0,0,otherx,2,3,t))),m|{'ekbk':lambda *xs:False},'expose')==(not inside);cases+=1
    # Real numeric checks of the normal, independently of the quantified wrapper.
    for n,p,z in product(DIRECTIONS,((0,0,0),(1,2,3)),((0,0,0),(2,3,-1))):
        vals=list(map(c,(5,2,*n)))+[phase(cuts,5,2,n)]+list(map(c,(*p,*z,1)))
        assert run('ekbk',vals,m);cases+=1
    # Retain every quantifier once over a small symbolic domain; its body and
    # arithmetic are checked separately above, not interpreted as real cuts here.
    domain=('a','b','x','y','z','t');fakephase=FunctionValue(('individual',)*4,'individual',lambda *xs:'a');allregion=FunctionValue(('individual',)*4,'truth',lambda *xs:True)
    for root,fields,probe in [('ekgv',RAY_VARS,'ekgu'),('ekgw',NORMAL_VARS,'ekbk')]:
        for pivot,(n,t) in enumerate(fields):
            for target in ('a','b','unavailable'):
                row=['a']*len(fields);row[pivot]=target
                vals=['a']*5+[fakephase,allregion]+[x for i,x in enumerate(row) if i!=pivot]
                expected=tuple(row);mm={'bb':lambda x:'a','ba':lambda x:True,'bg':lambda *xs:True,probe:lambda *xs,expected=expected:tuple(xs[6:])!=expected,'ekgt':lambda *xs:FunctionValue(('individual',),'individual',lambda a:'a')}
                assert run(root,vals,mm,'scope:'+str(pivot),domain)==(target=='unavailable');cases+=1
        refused(lambda root=root:run(root,optical,m|{probe:lambda *xs:True}))
    return dict(cases=cases,all_local_ray_and_same_time_normal_points_bound=True,both_endpoints_must_be_in_same_region=True,quantified_positions_checked=12,no_finite_real_domain_substitution=True)

@lru_cache(None)
def binding_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;slots=fixture('ekgy')[1];cases=0
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    gate=lambda *xs:all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,values,slots))
    model=m|{'ekgn':gate,'ekhl':gate};assert run('ekgy',values,model);cases+=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts);assert not run('ekgy',changed,model);cases+=1
    unknowns(lambda mm:run('ekgy',values,mm),model,('ekgn','ekhl'))
    pos={n:i for i,(n,t) in enumerate(SETTING)}
    for n,x in dict(light=5,speed=3,rate=4,ax=Q(3,5),ay=Q(4,5),az=0,lower=0,upper=4).items():values[pos[n]]=c(x)
    values[pos['space']]=FunctionValue((RS,)*3,'truth',lambda x,y,z:r(x)>=0)
    samples=((0,0,0,0),(2,1,0,1),(-4,3,0,2),(0,0,0,2),(3,2,1,4))
    def optical(V,rate,ax,ay,az,ph,region):
        if tuple(map(r,(V,rate,ax,ay,az)))!=(5,Q(16,5),0,1,0):return False
        for x,y,z,t in samples:
            if r(ph(*map(c,(x,y,z,t))))!=Q(16,5)*(t-Q(y,5)):return False
            oldx=Q(5,4)*(x+3*t);oldt=Q(5,4)*(t+Q(3*x,25))
            if region(*map(c,(x,y,z,t)))!=(oldx>=0 and 0<=oldt<=4):return False
        return True
    assert run('ekhl',values,m|{'ekgx':optical});cases+=1
    for name,x in [('rate',8),('lower',1),('upper',2)]:
        changed=values[:];changed[pos[name]]=c(x);assert not run('ekhl',changed,m|{'ekgx':optical});cases+=1
    unknowns(lambda mm:run('ekhl',values,mm),m|{'ekgx':optical},('ekgx','soy','sjd'))
    # Naming preserves the wave, candidate angle and all 59 remaining witnesses.
    for pivot,(name,t) in enumerate(NAME_WITNESSES):
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in SETTING};expected.update(context='case',scope='b',newangle='b');expected[name]=target
            row=tuple(expected[n] for n,t in SETTING);vals=['a','b','case']+[expected[n] for i,(n,t) in enumerate(NAME_WITNESSES) if i!=pivot]
            mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekgy':lambda *xs,row=row:tuple(xs)==row}
            assert run('ekgz',vals,mm,'slot:'+str(pivot),('a','b'))==(target!='unavailable');cases+=1
    expected={n:'a' for n,t in SETTING};expected.update(context='case',scope='b',newangle='b')
    row=tuple(expected[n] for n,t in SETTING);vals=['a','b','case']+[expected[n] for n,t in NAME_WITNESSES[1:]]
    mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekgy':lambda *xs:tuple(xs)==row}
    assert run('ekgz',vals,mm,'slot:0',('a','b'));cases+=1
    for i,bad in enumerate(('b','a','other')):
        changed=vals[:];changed[i]=bad;assert not run('ekgz',changed,mm,'slot:0',('a','b'));cases+=1
    unknowns(lambda model:run('ekgz',vals,model,'slot:0',('a','b')),mm,('ekgy',))
    return dict(cases=cases,shared_setting_roles=65,naming_witnesses=59,new_phase_rate_and_region_share_the_same_speed=True,printed_conclusion_not_in_naming_rule=True)

@lru_cache(None)
def universal_checks():
    cases=0
    for root,premise,conclusion in [('ekhb','ekgy','ekha'),('ekhc','ekgy','ekgo'),('ekhd','ekgn','ekhl')]:
        for pivot,(name,t) in enumerate(VARIABLES):
            for target in ('a','b','unavailable'):
                expected={n:'a' for n,t in SETTING};expected.update(context='case',scope='b');expected[name]=target
                row=tuple(expected[n] for n,t in SETTING);vals=[expected[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b',premise:lambda *xs,row=row:tuple(xs)==row,conclusion:lambda *xs:False}
                assert run(root,vals,mm,'slot:'+str(pivot),('a','b'))==(target=='unavailable');cases+=1
                assert run(root,vals,mm|{conclusion:lambda *xs,row=row:tuple(xs)==row},'slot:'+str(pivot),('a','b'));cases+=1
        unknowns(lambda model:run(root,vals,model,'slot:'+str(pivot),('a','b')),mm,(premise,conclusion))
        cuts,m=setup();refused(lambda root=root:run(root,[],m|{'tc':lambda:cuts.make(5),premise:lambda *xs:True,conclusion:lambda *xs:True}))
    # The real inherited literal angle and the earlier a' equation stay distinct.
    cuts,m=setup();c,r=cuts.make,cuts.read;slots=fixture('ekha')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    for n,x in dict(light=5,speed=3,ax=0,ay=1,az=0,anglecos=0,newanglecos=Q(4,5)).items():values[[n for n,t in SETTING].index(n)]=c(x)
    assert run('ekha',values,m);assert not run('ekgo',values,m);cases+=2
    return dict(cases=cases,three_contents_each_have_61_universal_slots=True,prior_a_prime_not_replaced_by_literal_line_angle=True,unknown_consequents_rejected=True)

@lru_cache(None)
def presentation_checks():
    rows={
     'ekhe':{'eislo':{('phiname','ekgz','paper','case')}},
     'ekhf':{'eislo':{('phiname','ekgz','paper','case')},'uh':{('angleintro','author','ekhd','scope','case')},'eisa5':{('angleintro','author','ekhe','ekhd','case')},'eisox':{('prioraxial','ekhb','case')},'eissb':{('angleintro','prioraxial','author','ekhb','ekhc','scope','case')},'ue':{('parameters','angleintro','case'),('angleintro','angledisplay','case')},'uf':{('author','angleintro','angledisplay','case')}},
     'ekhi':{'eisox':{('angledisplay','ekhc','case')}},
     'ekhh':{'eir3':{('angleintro','author','paper','ekhg','case')},'ue':{('infinity','angleintro','case')}},
     'ekhk':{'eir3':{('angledisplay','author','paper','ekhj','case')},'ue':{('angleintro','angledisplay','case')}}}
    cases=0
    for root,rs in rows.items():cases+=perturb(lambda mm:run(root,[],mm),{n:relation(vs) for n,vs in rs.items()},rs)
    return dict(cases=cases,naming_parenthetical_identity_rewrite_colon_and_display_preserved=True,quoted_physics_and_false_printed_claim_not_evaluated=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={x['id']:x for x in inv['math']};segments=[]
    readings={'M0338':'φ′','M0339':'a′','M0340':'cosφ′=(cosφ−v/V)/(1−(v/V)cosφ)'}
    for i in range(192,194):
        u=inv['units'][i];assert digest(u['text'].encode())==u['text_sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],statements=[375+i-192],math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert 'Wellennormale (Strahlrichtung)' in segments[0]['text'] and 'Verbindungslinie' in segments[0]['text']
    tokens=[x.text for x in ET.fromstring(math['M0340']['mathml']).iter() if x.text]
    assert tokens.count('=')==1 and tokens.count('−')==2
    return dict(status='literal_line_angle_naming_and_printed_aberration_display_collated',segments=segments,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==377 and new.document['statements'][:375]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    ann=load_annotations(ROOT,BASIS,ANNOTATIONS);assert ann.annotations['entries'][-1]['forms'][0]['text']=='φ′'
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_references=4,old_375_statements_and_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('motion',motion_checks),('scope',scope_checks),('binding',binding_checks),('universal',universal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_wave_cycle_frequency','check_resting_charge_force','check_doppler_specialization','compose_aberration_line','compose_wave_display','compose_wave_transform_application','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_aberration_presentation.py','scripts/check_aberration_presentation.py','tests/test_aberration_presentation.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='literal_line_angle_named_and_aberration_display_attributed',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
