"""Check the corrected interval, moving region and same-hypothesis question act."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_distant_wave_source import numbers
from scripts.check_wave_observer_question import binding_setup as old_binding_setup
from scripts.compose_wave_inquiry import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,FAMILY,SETTING,QUESTION,LOCATION,INVESTIGATION,ANSWERS,REGION_INPUT,build

DOC='docs/wave-inquiry-v1.md';SOURCE='data/einstein-wave-inquiry-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=tuple('artifacts/written-facsimiles-v1/einstein-1905-unlp-p'+str(p)+'-0.jpg' for p in (910,911))
DEPENDENCIES=('reports/wave-observer-question-v1.json','reports/wave-display-v1.json','reports/frame-motion-v1.json','reports/field-transform-v1.json')
CONSTANTS={'ra':'old','zbm':'moving','ta':'lengthunit','rb':'timeunit','eisrx':'scope','rd':'author','eirf':'paper','ri':'case','eissc':'explanation','eissf':'question','yn':'x','yo':'y','yp':'z','zc7':'t'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in FAMILY+QUESTION if t=='a'],'a','b','body','other']))

@lru_cache(None)
def fixture(name,mode='native'):
    # The erroneous historical root is loaded only for an explicit regression counterexample.
    doc=extract_document(parse(read(FULL if name=='ekbw' else CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sje','szi','soy'}
    if name in ('ekca','ekbw'):bounds.add('ekbu')
    if name=='ekcb':bounds.add('ekca')
    if name in ('ekcc','ekcd'):bounds|={'ekcb','ejsn'}
    if name in ('ekb3','ekb4'):bounds|={'ekbl','eivz','ekcb','ekcc','ekb2'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='pointwise':
        found=[]
        def instantiate(node):
            if isinstance(node,list):return [instantiate(x) for x in node]
            if isinstance(node,dict):
                if node.get('kind')=='forall' and node['sort']==RS:
                    found.append(dict(name=node['variable'],sort=node['sort']));return node['body']
                return {k:instantiate(x) for k,x in node.items()}
            return node
        d['body']=instantiate(d['body']);assert len(found)==1;d['parameters']+=found
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jwi'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jwicapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jwicapture',arguments=[expr])
    if d['result']=='content' and not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)};captured=[]
    def capture(value):captured.append(value);return True
    mm['jwicapture']=capture
    answer=evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else answer

@lru_cache(None)
def interval_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;cases=0;truth=lambda *xs:True
    positions=[FunctionValue((RS,),RS,lambda t,i=i:c(i+1)) for i in range(3)]
    base=['observer','moving','case','lengthunit','timeunit',c(0),c(2),*positions]
    for time,region_truth in product((-1,0,1,2,3),(False,True)):
        region=FunctionValue((RS,)*4,'truth',lambda *xs,yes=region_truth:yes)
        values=base+[region,c(time)];expected=not 0<=time<=2 or region_truth
        assert run('ekca',values,m|{'ekbu':truth},'pointwise')==expected;cases+=1
    # Native lg (not a callback with mirrored argument order) reveals the old false acceptance.
    bad_region=FunctionValue((RS,)*4,'truth',lambda *xs:False)
    values=base+[bad_region,c(1)]
    assert run('ekbw',values,m|{'ekbu':truth},'pointwise');cases+=1
    assert not run('ekca',values,m|{'ekbu':truth},'pointwise');cases+=1
    for lo,hi in ((0,2),(-2,0),(1,3)):
        for time in (-3,-2,-1,0,1,2,3,4):
            values=base[:];values[5:7]=[c(lo),c(hi)];values+=[bad_region,c(time)]
            assert run('ekca',values,m|{'ekbu':truth},'pointwise')==(not lo<=time<=hi);cases+=1
    unknowns(lambda mm:run('ekca',base+[bad_region,c(1)],mm,'pointwise'),m|{'ekbu':truth},('ba','zzba','zzbc','ekbu'))
    try:run('ekca',base+[bad_region],m|{'ekbu':truth})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full real interval enumerated')
    return dict(cases=cases,native_closed_interval_order_lower_upper_time=True,old_false_acceptance_reproduced_and_excluded=True,whole_real_time_quantifier_preserved=True)

def arithmetic_model():
    cuts,m=numbers();c,r=cuts.make,cuts.read
    m|={'sje':lambda a,b:c(r(a)/r(b)),'soy':lambda light,speed:c(Q(5,4)) if (r(light),abs(r(speed)))==(5,3) else forbidden()}
    return cuts,m

@lru_cache(None)
def region_checks():
    cuts,m=arithmetic_model();c,r=cuts.make,cuts.read;cases=0
    space=FunctionValue((RS,)*3,'truth',lambda *xs:all(abs(r(x))<=1 for x in xs))
    for speed in (-3,3):
        region=run('ekb2',[space,c(0),c(2),c(5)],m|{'zb7':lambda:c(speed)})
        for x,y,z,t in product((-1,0,1,2),(0,2),(0,-2),(-1,0,1,2,3)):
            gamma=Q(5,4);moving=(gamma*(x-speed*t),Q(y),Q(z),gamma*(Q(t)-Q(speed*x,25)))
            expected=all(abs(s)<=1 for s in (x,y,z)) and 0<=t<=2
            assert region(*map(c,moving))==expected;cases+=1
        # The same four numbers in the old rectangular region are a different test.
        assert not region(c(0),c(0),c(0),c(2));cases+=1
    return dict(cases=cases,same_inverse_map_and_all_four_coordinates=True,moving_region_not_old_rectangular_patch=True,rational_gamma_supplied_as_numeric_boundary=True)

def setup():
    cuts,m=numbers();c=cuts.make;slots=fixture('ekb3')[1];pos={n:i for i,(n,t) in enumerate(FAMILY)}
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(FAMILY,slots))]
    for n,x in {'frame':'old','lengthunit':'lengthunit','timeunit':'timeunit','scope':'scope','light':c(5)}.items():values[pos[n]]=x
    region=FunctionValue((RS,)*4,'truth',lambda *xs:True);wrong_region=FunctionValue((RS,)*4,'truth',lambda *xs:False)
    def same(x,y,sort):return same_value(x,y,sort,cuts)
    def prior(*xs):return len(xs)==len(SETTING) and all(same(x,y,s) for x,y,(_,s) in zip(xs,values,slots))
    def region_factory(*xs):
        names=[n for n,t in REGION_INPUT]
        return region if len(xs)==len(names) and all(same(x,values[pos[n]],slots[pos[n]][1]) for x,n in zip(xs,names)) else wrong_region
    selected={n:values[pos[n]] for n,t in FAMILY}
    selected.update(frame='moving',lower=selected['obslower'],upper=selected['obsupper'],x=selected['obsx'],y=selected['obsy'],z=selected['obsz'],region=region,electricconversion=c(1),magneticconversion=c(Q(1,5)))
    qslots=fixture('ekcc')[1]
    def gate(names):
        sorts={n:s for (n,t),(_,s) in zip(QUESTION+ANSWERS,qslots)}
        return lambda *xs:len(xs)==len(names) and all(same(x,selected[n],sorts[n]) for x,n in zip(xs,names))
    answers=[sentinel(s,70+i,cuts) for i,(slot,s) in enumerate(qslots[-2:])]
    selected.update(electricfield=answers[0],magneticfield=answers[1])
    m|={'tc':lambda:c(5),'zb7':lambda:c(3),'ekbl':prior,'eivz':lambda ctx:ctx=='case','ekb2':region_factory,'ekcb':gate([n for n,t in INVESTIGATION]),'ekcc':gate([n for n,t in QUESTION+ANSWERS])}
    return cuts,values,slots,m,answers

@lru_cache(None)
def family_checks():
    cuts,values,slots,m,answers=setup();c=cuts.make;cases=0
    assert run('ekb3',values,m);cases+=1
    question=run('ekb4',values,m);assert isinstance(question,QuestionValue) and question.function(*answers);cases+=1
    for i,(slot,sort) in enumerate(slots):
        altered=values[:];altered[i]=sentinel(sort,150+i,cuts)
        assert not run('ekb3',altered,m),FAMILY[i];cases+=1
    for n in ('ekbl','eivz','ekcb'):
        assert not run('ekb3',values,m|{n:lambda *xs:False});cases+=1
    for n in ('ra','zbm','ta','rb','eisrx'):
        assert not run('ekb3',values,m|{n:lambda:'other'});cases+=1
    for speed in (-5,5,6):assert not run('ekb3',values,m|{'zb7':lambda speed=speed:c(speed)});cases+=1
    assert not question.function(answers[1],answers[0]);cases+=1
    for n in ('wave','process','observer','context','lengthunit','timeunit','chargeunit','electricunit','magneticunit','forceunit','obslower','obsupper','obsx','obsy','obsz','space','lower','upper','light'):
        i=next(i for i,(name,t) in enumerate(FAMILY) if name==n);altered=values[:];altered[i]=sentinel(slots[i][1],150+i,cuts)
        assert not run('ekb4',altered,m).function(*answers),n;cases+=1
    unknowns(lambda mm:run('ekb3',values,mm),m,('ekbl','eivz','ekcb','ekb2','tc','zb7'))
    unknowns(lambda mm:run('ekb4',values,mm).function(*answers),m,('ekb2','ekcc','sjd'))
    return dict(cases=cases,all_41_roles_preserve_one_hypothesis_assignment=True,question_keeps_same_wave_observer_units_and_transformed_region=True,old_35_setting_roles_not_rebound_per_candidate=True)

@lru_cache(None)
def candidate_checks():
    cuts,values,slots,model,gate=old_binding_setup();model['ekcb']=model.pop('ekbx');cases=0
    assert run('ekcc',values,model);cases+=1
    question=run('ekcd',values[:-2],model);assert question.function(*values[-2:]);cases+=1
    for i,(slot,sort) in enumerate(slots):
        altered=values[:];altered[i]=sentinel(sort,100+i,cuts)
        assert not run('ekcd',altered[:-2],model).function(*altered[-2:]);cases+=1
    for n in ('ekcb','ejsn','eispn'):
        assert not run('ekcc',values,model|{n:lambda *xs:False});cases+=1
    inv=values[:len(INVESTIGATION)];mm={'ekca':gate([n for n,t in LOCATION]),'eissd':gate(['observer','wave','process','frame','region','context'])}
    assert run('ekcb',inv,mm);cases+=1
    for i,(slot,sort) in enumerate(slots[:len(INVESTIGATION)]):
        altered=inv[:];altered[i]=sentinel(sort,100+i,cuts)
        assert not run('ekcb',altered,mm);cases+=1
    unknowns(lambda changed:run('ekcb',inv,changed),mm,('ekca','eissd'))
    unknowns(lambda changed:run('ekcc',values,changed),model,('ekcb','ejsn','eispn'))
    return dict(cases=cases,corrected_interval_chain_reaches_physical_candidate_pair=True,all_question_parameters_and_both_answer_slots_checked=True)

@lru_cache(None)
def presentation_checks():
    fixtures={'ekb5':{'eisse':{('question','author','explanation','ekbn','ekb3','ekb4','scope','case')}},'ekb7':{'eir3':{('question','author','paper','ekb6','case')},'ue':{('explanation','question','case')}}};cases=0
    for name,rows in fixtures.items():cases+=perturb(lambda mm:run(name,[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    assert run('ekb5',[],{'eisse':relation(fixtures['ekb5']['eisse']),'ekbn':forbidden,'ekb3':forbidden,'ekb4':forbidden});cases+=1
    assert not run('ekb7',[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,'eissf':lambda:'explanation'});cases+=1
    return dict(cases=cases,actual_author_question_act_under_same_prior_hypothesis=True,closed_family_quotes_not_executed_or_asserted_as_actual_experiment=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][181];text=u['text'][:144];assert u['id']=='einstein-1905:u0182' and text.endswith('untersucht werden.') and digest(u['text'].encode())==u['text_sha256']
    math=next(m for m in inv['math'] if m['id']=='M0324')
    return dict(status='moving_observer_question_first_sentence_connected_unit_incomplete',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,144],text=text,math=[dict(id='M0324',sha256=math['sha256'],reading='k')],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),observations=['原刊910頁末のWir fragenから、911頁冒頭のBeobachter untersucht werden.までを続けて照合した。頁境界は文の条件へ含めない。','dieser Wellen/dieselbenを先行の同じ波の仮定へ、bewegten System kを同じ二系の相対運動へ、ruhendを全区間の代表位置の静止へ結ぶ。','同じ引数割当の条件と質問を閉じた規則として著者の質問提示へ帰属する。候補ごとの波の存在選択や現実の実験成立へ変えない。','旧ekbwの閉区間呼出順の誤りを新定義で修正し、今回の文から旧経路を除外した。'],remaining=['u0182後半の§6の場と§3の座標・時刻の変換を適用して直ちに得るという提示と後続表示への参照','近似的な表示を、同じ波の問いに対する近似的な答えとして接続すること','u0182全体の通読判断及びu0178の主題'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,*FACSIMILES,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==367 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'ekbl','ekbn','ekbu','ekbv','ejsn','eispn','eissd','eivz','s6m','lg'}<=names
    assert not names&{'ekbw','ekbx','ekby','ekbz','cf','seaj','znl','znm','eispp'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=1,old_366_statements_and_all_original_evidence_preserved=True,historical_interval_bug_not_in_new_statement_dependencies=True,whole_unit_review_not_added=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('interval',interval_checks),('region',region_checks),('family',family_checks),('candidate',candidate_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_rod_methods','check_conductor_cases','check_material_relative_frame','check_distant_wave_source','check_wave_observer_question','compose_wave_observer_question','compose_distant_wave_source','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_wave_inquiry.py','scripts/check_wave_inquiry.py','tests/test_wave_inquiry.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='same_wave_moving_observer_question_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
