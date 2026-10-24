"""Check machine operation, fixed contacts, polarity and shared witnesses."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json,re
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
from scripts.check_material_relative_frame import arithmetic,RS
from scripts.check_resting_charge_force import retag
from scripts.check_rod_methods import value
from scripts.compose_unipolar_machine import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,MODE,WITNESSES,COUPLING,CIRCUIT,CONTACT,TURN,build

DOC='docs/unipolar-machine-v1.md';SOURCE='data/einstein-unipolar-machine-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg';RESEARCH='data/unipolar-machine-research-v1.json'
DEPENDENCIES=('reports/moving-conductor-case-v1.json','reports/moving-field-definition-v1.json','reports/asymmetry-resolution-v1.json')
CONSTANTS={'ri':'case','eirf':'paper','eisrh':'expression','eisri':'node'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),*(n for n,t in MODE if t=='a'),'a','b','body','other')))
SITUATIONS=('case','other','first')

def finite_reals(node):
    if node==RS:return 'individual'
    if isinstance(node,list):return [finite_reals(x) for x in node]
    if isinstance(node,dict):return {k:finite_reals(v) for k,v in node.items()}
    return node

@lru_cache(None)
def base(name,mode):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds={'ba','bb','bc','bg','sca','lg'}
    if name=='ekai':bounds|={'ekah'}
    if name=='ekaj':bounds|={'ekai'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='finite':doc=finite_reals(doc)
    if mode=='slots':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
    return doc

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(base(name,'slots' if mode.startswith('slot:') else mode));d=next(d for d in doc['declarations'] if d['name']==name)
    if mode.startswith('slot:'):
        pivot=int(mode.split(':')[1]);retained=None
        for i in range(len(WITNESSES)):
            node=d['body'];assert node['kind']=='exists';d['body']=node['body']
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
        d['body']=retained|{'body':d['body']}
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jum'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots]))]
    return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN,situations=SITUATIONS):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    return evaluate_document(doc,individuals=domain,situations=situations,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def polarity_checks():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|={'bg':lambda x,y:r(x)<r(y),'lg':lambda lo,hi,t:r(lo)<=r(t)<=r(hi)};cases=0
    for slope,intercept in ((0,0),(0,1),(0,-1),(1,0),(1,-1),(-1,0)):
        curve=FunctionValue((RS,),RS,lambda t,a=slope,b=intercept:c(a*r(t)+b))
        for t in (-1,0,Q(1,2),1,2,3):
            for positive in (True,False):
                expected=not 0<=t<=2 or ((slope*t+intercept)>=0 if positive else (slope*t+intercept)<=0)
                assert run('ekag',[c(0),c(2),curve,positive,c(t)],m)==expected;cases+=1
    nums=tuple(str(i) for i in range(-2,4));n={s:Q(s) for s in nums}
    mm={'ba':lambda x:x in n,'bb':lambda x:str(int(x)),'bc':lambda x,y:n[x]<=n[y],'bg':lambda x,y:n[x]<n[y],'sca':lambda x,y:n[x]==n[y],'lg':lambda lo,hi,t:n[lo]<=n[t]<=n[hi]}
    examples=[(lambda t:'1',True),(lambda t:'-1',True),(lambda t:'0',False),(lambda t:t if t in ('0','1','2') else '-1',True),(lambda t:'-1' if t=='1' else '1',False),(lambda t:'0' if t in ('0','1','2') else '1',False)]
    for curve,expected in examples:
        assert run('ekah',['0','2',curve],mm,'finite',nums)==expected;cases+=1
    for lo,hi in [('0','0'),('2','0')]:assert not run('ekah',[lo,hi,lambda t:'1'],mm,'finite',nums);cases+=1
    unknowns(lambda model:run('ekah',['0','2',lambda t:'1'],model,'finite',nums),mm,mm)
    try:run('ekah',[c(0),c(2),FunctionValue((RS,),RS,lambda t:c(1))],m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full real time domain was silently sampled')
    return dict(cases=cases,both_polarities_nonconstant_and_zero_crossings_distinguished=True,finite_time_diagnostic_not_full_real_proof=True,whole_real_time_domain_refused=True)

def setup(turns=Q(1)):
    cuts,m=arithmetic();c=cuts.make;r=cuts.read;slots=fixture('ekai')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(MODE,slots))]
    pos={n:i for i,(n,_) in enumerate(MODE)}
    for n,x in [('lower',0),('upper',2),('turns',turns)]:values[pos[n]]=c(x)
    def gate(ns,xs):return len(ns)==len(xs) and all(same_value(x,values[pos[n]],slots[pos[n]][1],cuts) for n,x in zip(ns,xs))
    fields={
      'zjg':['rotor','device','operation'],'va':['frame'],'zjn':['rotor','axis','frame','operation'],
      'eisrg':[n for n,_ in TURN],'eisre':[n for n,_ in CIRCUIT],
      'eispn':['process','frame','electric','magnetic','region','operation'],'eirn':['frame','magnetic','magneticunit','operation'],'ekah':['lower','upper','output'],
    }
    m|={n:lambda *xs,ns=ns:gate(ns,xs) for n,ns in fields.items()}
    m['eisrf']=lambda contact,*xs:contact in ('first','second') and gate([n for n,_ in CONTACT],xs)
    m['eisrd']=lambda *xs:value(xs[-1])=='eidz' and gate([n for n,_ in COUPLING if n!='law'],xs[:-1])
    return cuts,m,slots,values,pos

@lru_cache(None)
def machine_checks():
    cuts,m,slots,values,pos=setup();cases=1;assert run('ekai',values,m)
    for i,(_,s) in enumerate(slots):
        bad=values[:];bad[i]='other' if s in ('individual','situation') else sentinel(s,100+i,cuts)
        assert not run('ekai',bad,m),MODE[i][0];cases+=1
    for turns in (Q(-2),Q(-1),Q(-1,2),Q(0),Q(1,2),Q(1),Q(2)):
        _,mm,_,vs,_=setup(turns);assert run('ekai',vs,mm)==(abs(turns)>=1);cases+=1
    for callee in ('zjg','va','zjn','eisrg','eisre','eisrf','eispn','eirn','eisrd','ekah'):
        assert not run('ekai',values,m|{callee:lambda *xs:False});cases+=1
    for missing in ('first','second'):
        assert not run('ekai',values,m|{'eisrf':lambda contact,*xs:contact!=missing and m['eisrf'](contact,*xs)});cases+=1
    for a,b in [('rotor','returnpath'),('first','second')]:
        bad=values[:];bad[pos[a]]=bad[pos[b]]
        # True relation boundaries isolate the explicit inequalities.
        mm=m|{n:lambda *xs:True for n in ('zjg','va','zjn','eisrg','eisre','eisrf','eispn','eirn','eisrd','ekah')}
        assert not run('ekai',bad,mm);cases+=1
    unknowns(lambda mm:run('ekai',values,mm),m,('eisre','eisrf','eisrd','eisrg','eispn','eirn','ekah'))
    return dict(cases=cases,complete_turn_fixed_circuit_two_contacts_and_induction_bound=True,field_units_process_output_and_operation_not_swapped=True,source_magnet_not_required_to_be_separate_object=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for pivot,(pn,pt) in enumerate(WITNESSES):
        choices=('case','other') if pt=='d' else ('a','b');mode='slot:'+str(pivot)
        for target in (*choices,'unavailable'):
            expected={n:('case' if t=='d' else 'a') for n,t in MODE};expected[pn]=target
            args=['a','case']+[expected[n] for i,(n,_) in enumerate(WITNESSES) if i!=pivot]
            row=tuple(expected[n] for n,_ in MODE)
            m={'ekai':lambda *xs,row=row:tuple(xs)==row,'eisrc':relation({('a','case',expected['operation'])})}
            assert run('ekaj',args,m,mode,('a','b'))==(target!='unavailable');cases+=1
            if target=='unavailable':continue
            for i,badval in [(0,'b'),(1,'other')]:
                bad=args[:];bad[i]=badval;assert not run('ekaj',bad,m,mode,('a','b'));cases+=1
            assert not run('ekaj',args,m|{'eisrc':lambda *xs:False},mode,('a','b'));cases+=1
        unknowns(lambda mm:run('ekaj',args,mm,mode,('a','b')),m,('ekai','eisrc'))
    try:run('ekaj',['a','case'],{'ekai':lambda *xs:True,'eisrc':lambda *xs:True},domain=('a','b'))
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full operation-function domain was sampled')
    return dict(cases=cases,witnesses=len(WITNESSES),one_configuration_with_shared_device_and_operation=True,binding_diagnostics_with_other_witnesses_instantiated=True,full_function_domain_refused=True)

@lru_cache(None)
def annotation_checks():
    rows={'eisrj':{('expression','ekaj','paper','node','case')}};m={n:relation(rs) for n,rs in rows.items()}
    cases=perturb(lambda mm:run('ekak',[],mm),m,rows)
    assert run('ekak',[],m|{'ekaj':forbidden});cases+=1
    return dict(cases=cases,source_expression_bound_to_composed_machine_rule=True,annotation_not_an_author_assertion_or_question_answer=True,quoted_classification_not_executed=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][176];assert u['id']=='einstein-1905:u0177' and digest(u['text'].encode())==u['text_sha256']
    term='(Unipolarmaschinen)';start=u['text'].index(term);end=start+len(term)
    research=json.loads(read(RESEARCH));validate_hashes(ROOT,research['source_sha256'])
    return dict(status='machine_term_composed_second_sentence_incomplete',unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=term,math=[],source_nonblank_characters=len(term),observations=['原刊910頁の括弧内の装置類を、運転可能な回転・滑り接触・閉回路・磁場との結合・非反転出力へ結ぶ。','Faradayの原報は装置の範囲の検討に使い、Sitzの意味や問いの判断をそこから確定しない。'],remaining=['Sitzの所在の問いとその前提、gegenstandslosという判断、Auchの提示','u0177第二文と全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC,RESEARCH,*research['source_sha256'])})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==INDEX+1 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eidz','eicn','eispn','eirn','zjn','zjg','eisrd','eisrf'}<=names
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=6,new_references=2,old_361_statements_preserved=True,whole_unit_review_not_added=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('polarity',polarity_checks),('machine',machine_checks),('witness',witness_checks),('annotation',annotation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_resting_charge_force','check_rod_methods','compose_vacuum_field_domain','compose_material_relative_frame','compose_field_equations','compose_moving_conductor_case','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_unipolar_machine.py','scripts/check_unipolar_machine.py','tests/test_unipolar_machine.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='unipolar_machine_operation_and_term_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
