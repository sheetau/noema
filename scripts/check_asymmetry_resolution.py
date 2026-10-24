"""Check common mechanism classes and the complete physical comparison projection."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
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
from scripts.check_material_relative_frame import arithmetic
from scripts.check_resting_charge_force import retag
from scripts.compose_asymmetry_resolution import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,FIELDS,RULE,KEYS,WITNESSES,GENERATION,MOTION,COMPARISONS,history,build

DOC='docs/asymmetry-resolution-v1.md';SOURCE='data/einstein-asymmetry-resolution-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/observable-contrast-v1.json','reports/apparent-asymmetry-v1.json','reports/relative-history-match-v1.json','reports/auxiliary-role-v1.json')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','eisqw':'theory','eisq6':'view','eisq7':'node','eisaa':'magnet','eisab':'conductor','eisac':'process','eir7':'opening','eisaj':'contrast','zpw':'prior'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','body','other')))
SITUATIONS=('case','other','first')

@lru_cache(None)
def base(name,mode):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds={'eida','eia2','eiag','eiah'}
    if name=='ejz7':bounds={'ejz6'}
    if name=='ekaa':bounds={'ejz7','ejz5'}
    if name=='ekab':bounds={'ekaa'}
    if name=='ekac':bounds={'ekab'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
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
        n='jasr'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN,situations=SITUATIONS):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    return evaluate_document(doc,individuals=domain,situations=situations,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def classification_checks():
    subsets=[{x for x,yes in zip(('a','b'),bits) if yes} for bits in product((False,True),repeat=2)]
    args=['a','b','a','case','b','other','case'];cases=0
    for accounts,firsta,seconda,firstb,secondb in product(subsets,repeat=5):
        cats={'a':(firsta,seconda),'b':(firstb,secondb)}
        rows={'eisaf':{('a','b','a','case','b','other',a,'case') for a in accounts},'eisag':{('a','b',a,f,ctx,label,'case') for a,pair in cats.items() for f,ctx,labels in [('a','case',pair[0]),('b','other',pair[1])] for label in labels}}
        m={n:relation(rs) for n,rs in rows.items()}
        got=run('ejz5',args,m,domain=('a','b'))
        expected=bool(accounts) and all(cats[a][0]&cats[a][1] for a in accounts)
        assert got==expected,(accounts,cats)
        old=run('eidd',args,m,domain=('a','b'))
        assert old==(bool(accounts) and all(x and y and not x&y for a in accounts for x,y in [cats[a]]))
        assert not (got and old);cases+=2
    rows={'eisaf':{('a','b','a','case','b','other','a','case')},'eisag':{('a','b','a',f,ctx,'a','case') for f,ctx in [('a','case'),('b','other')]}}
    m={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda mm:run('ejz5',args,mm),m,rows)
    return dict(cases=cases,all_allowed_accounts_have_common_mechanism=True,empty_and_disjoint_explanations_rejected=True,not_merely_negation_of_old_distinction=True,classification_sets_need_not_be_identical=True)

@lru_cache(None)
def physical_binding_checks():
    cuts,m=arithmetic();slots=fixture('ejz6')[1];values=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];positions={n:i for i,(n,_) in enumerate(FIELDS)}
    def gate(names,xs):return len(names)==len(xs) and all(same_value(x,values[positions[n]],slots[positions[n]][1],cuts) for n,x in zip(names,xs))
    def names(xs):return [x.removeprefix('v ') for x in xs]
    motions={'eiag':[names(history('first','left')),names(history('second','right'))],'eiah':[names(history('first','right')),names(history('second','left'))]}
    m|={n:(lambda *xs,ns=[f for f,_ in fs]:gate(ns,xs)) for n,fs in [('eida',FIELDS),('eia2',MOTION),('eisq5',GENERATION)]}
    for n,alternatives in motions.items():m[n]=lambda *xs,aa=alternatives:any(gate(ns,xs) for ns in aa)
    assert run('ejz6',values,m);cases=1
    for i,(_,s) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(s,100+i,cuts);assert not run('ejz6',bad,m),FIELDS[i][0];cases+=1
    for n in ('eida','eia2','eiag','eiah','eisq5'):
        assert not run('ejz6',values,m|{n:lambda *xs:False});cases+=1
    unknowns(lambda mm:run('ejz6',values,mm),m,('eida','eia2','eiag','eiah','eisq5'))
    return dict(cases=cases,all_78_typed_arguments_and_physical_components_bound=True,generation_not_inferred_from_current_equality=True,lower_physical_bodies_are_prior_pinned_boundaries=True)

@lru_cache(None)
def projection_checks():
    cases=0
    for pivot,(pn,_) in enumerate(WITNESSES):
        mode='slot:'+str(pivot)
        for target in ('a','b','unavailable'):
            expected={n:('case' if t=='d' else 'a') for n,t in FIELDS};expected[pn]=target
            supplied=[expected[n] for n,_ in KEYS]+[expected[n] for i,(n,_) in enumerate(WITNESSES) if i!=pivot]
            row=tuple(expected[n] for n,_ in FIELDS);m={'ejz6':lambda *xs,row=row:tuple(xs)==row}
            assert run('ejz7',supplied,m,mode,('a','b'))==(target!='unavailable');cases+=1
            if target=='unavailable':continue
            # Every free key is kept with this same witness tuple.
            for i,(n,t) in enumerate(KEYS):
                bad=supplied[:];bad[i]='other' if t=='d' else 'b';assert not run('ejz7',bad,m,mode,('a','b'));cases+=1
                changed=dict(expected);changed[n]=bad[i];changed_row=tuple(changed[nn] for nn,_ in FIELDS)
                assert run('ejz7',bad,{'ejz6':lambda *xs,row=changed_row:tuple(xs)==row},mode,('a','b'));cases+=1
        unknowns(lambda mm:run('ejz7',supplied,mm,mode,('a','b')),m,('ejz6',))
    try:run('ejz7',['a','a','a','a','a','case','a','case','case'],{'ejz6':lambda *xs:True},domain=('a','b'))
    except ValueError as e:assert 'Finite function domain' in str(e) or 'rational number domain' in str(e),str(e)
    else:raise AssertionError('Full history/function witness domain was sampled')
    return dict(cases=cases,witnesses=len(WITNESSES),every_witness_and_all_nine_free_keys_distinguished=True,others_instantiated_one_binder_varied=True,full_function_domain_refused=True)

@lru_cache(None)
def scope_checks():
    keys=['magnet','conductor','process','scope','a','case','b','other','case'];args=keys+['view']
    rs={'ejz7':{tuple(keys)},'ejz5':{('view','scope','a','case','b','other','case')}};m={n:relation(rows) for n,rows in rs.items()}
    assert run('ekaa',args,m);cases=1
    assert not run('ekaa',args,m|{'ejz5':lambda *xs:False});cases+=1
    assert run('ekaa',args,{'ejz7':lambda *xs:False,'ejz5':lambda *xs:False});cases+=1
    unknowns(lambda mm:run('ekaa',args,mm),{'ejz7':lambda *xs:False,'ejz5':lambda *xs:False},('ejz5',))
    cases+=perturb(lambda mm:run('ekaa',args,mm),m,{'ejz5':rs['ejz5']})
    # Native universal quantifiers visit every scope/frame/context combination.
    supplied=['a','b','a','b','case'];combos=list(product(('a','b'),('a','b'),('case','other'),('a','b'),('case','other')))
    assert run('ekab',supplied,{'ekaa':lambda *xs:True},domain=('a','b'),situations=('case','other'));cases+=1
    for combo in combos:
        row=('a','b','a',*combo,'case','b')
        assert not run('ekab',supplied,{'ekaa':lambda *xs,row=row:tuple(xs)!=row},domain=('a','b'),situations=('case','other'));cases+=1
    unknowns(lambda mm:run('ekab',supplied,mm,domain=('a','b'),situations=('case','other')),{'ekaa':lambda *xs:True},('ekaa',))
    rows={'eisqy':{('theory','paper','eigj','scope','case')},'eisay':{('theory','view','paper','case')},'ekab':{('magnet','conductor','process','view','case')}}
    cases+=perturb(lambda mm:run('ekac',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,all_scopes_frames_and_contexts_preserved=True,same_introductory_objects_and_current_theory=True,ineligible_cases_not_forced_to_share_mechanism=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('node','author','ekac','scope','case')},'zdg':{('node','author','ekac','scope','case')},'eisra':{('node','author','paper',n,p,'ekac','process','case') for n,p in [('opening','eiez'),('contrast','eidh')]},'eisrb':{('prior','node','author','ejzw','ekac','scope','case')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ekad',[],mm),m,rows)
    assert run('ekad',[],m|{'ekac':forbidden,'eiez':forbidden,'eidh':forbidden,'ejzw':forbidden});cases+=1
    rows={'eir3':{('node','author','paper','ekae','case')},'ue':{('prior','node','case')}}
    cases+=perturb(lambda mm:run('ekaf',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    assert not run('ekaf',[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,'eisq7':lambda:'prior'});cases+=1
    return dict(cases=cases,introduction_reference_ferner_klar_and_author_preserved=True,quoted_prior_claims_not_reasserted=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][176];assert u['id']=='einstein-1905:u0177' and digest(u['text'].encode())==u['text_sha256']
    end=u['text'].index('verschwindet.')+len('verschwindet.');text=u['text'][:end]
    return dict(status='asymmetry_resolution_first_sentence_connected_unit_incomplete',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,end],text=text,math=[],source_nonblank_characters=len(re.sub(r'\s','',text)),observations=['保存済み原刊910頁の第一文を固定転記と照合した。序文の同じ磁石・導体の例と通常の理解での説明上の区別を受ける。','同じ相対運動に伴う電流を新理論で共通機構として説明する読みを採り、観測値の一致だけで解消を代用しない。','ferner、klar、in der Einleitungへの参照を同じ内容へ結ぶ。'],remaining=['単極機に関する電動力のSitzの問いが対象を失うという第二文','u0177全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==INDEX+1 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eidd','eisag','eisaf','eida','eia2','eisq5','eisra','eisrb','eisqy','eisay','zdg'}<=names
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=3,new_references=2,old_360_statements_preserved=True,whole_unit_review_not_added=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('classification',classification_checks),('physical_binding',physical_binding_checks),('projection',projection_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_resting_charge_force','compose_vacuum_field_domain','compose_material_relative_frame','compose_observable_contrast','compose_relative_history_match','compose_relativity_conjecture','compose_two_postulates','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_asymmetry_resolution.py','scripts/check_asymmetry_resolution.py','tests/test_asymmetry_resolution.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='introductory_asymmetry_resolution_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
