"""Check full physical schemas, all bindings, and both directions of completeness."""
from scripts.compose_complete_motion_expression import *
from itertools import product
from fractions import Fraction as Q
import json,re
from noema.finite_semantics import evaluate_document,Content,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_experimental_relation_tests as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse

DOC='docs/complete-motion-expression-v1.md';SOURCE='data/einstein-complete-motion-expression-reading-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/experimental-list-opening-v1.json','reports/experimental-relation-tests-v1.json','reports/deflection-speed-determination-v1.json','reports/local-magnetic-radius-v1.json','reports/traversed-potential-v1.json')
CONSTANTS=prior.CONSTANTS|{'rd':'author','eirf':'paper','ri':'case','eisxg':'section','eis6j':'summary','eis3x':'first','eis4q':'second','eis4u':'third','eis4x':'previous','eisxh':'matter','ra':'frame','eis3k':'view'}
SCENES=('case','other','assessment');PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values()]))
BOUNDS={'euu':{'er7','esa'},'euv':{'esu','esv','est'},'euw':{'eud','euu'},'eux':{'esp','euv'},'euy':{'eun','euw','eux'},'eu7':{'eu6'},'eva':{'eu7','eu6','euy'},'evc':{'eun','esd','euo','eup','eva'},'eve':{'evd'}}
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk;scalarize=prior.scalarize
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==root);b=d['body'];assert b['kind']=='content'
        d['parameters']=[dict(name=b['variable'],sort='situation')];d['result']='truth';b=b['body']
        while b['kind']=='forall':d['parameters'].append(dict(name=b['variable'],sort=b['sort']));b=b['body']
        d['body']=b
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jcmeslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].insert(0,dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,vs,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots),(root,len(vs),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=PEOPLE,situations=SCENES,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def predicate(f):return FunctionValue(('situation',),'truth',f)

@lru_cache(None)
def equivalence_checks():
    cases=0
    for allowed,described in product(range(4),repeat=2):
        scope=lambda s:s in SCENES[1:]
        a=lambda s: s in SCENES[1:] and bool(allowed&(1<<SCENES[1:].index(s)))
        d=lambda s: s in SCENES[1:] and bool(described&(1<<SCENES[1:].index(s)))
        args=[predicate(f) for f in (scope,a,d)]
        wanted=[not bool(allowed&~described),not bool(described&~allowed),allowed==described,bool(described&~allowed),bool(allowed&~described)]
        for root,value in zip(('euz','eu2','eu3','eu4','eu5'),wanted):assert run(root,args,{})==value;cases+=1
    false=predicate(lambda s:False);true=predicate(lambda s:True)
    assert not run('eu3',[false,true,true],{});cases+=1
    # An additional candidate reveals a missing law even after a narrower agreement.
    narrow=predicate(lambda s:s=='other');wide=predicate(lambda s:s in ('other','assessment'));one=predicate(lambda s:s=='other')
    assert run('eu3',[narrow,true,one],{});assert not run('eu3',[wide,true,one],{});cases+=2
    for i in range(3):
        args=[true,true,true];args[i]=predicate(forbidden);reject(lambda:run('eu3',args,{}));cases+=1
    return dict(cases=cases,both_directions_and_distinct_counterexamples=True,empty_scope_refused=True,larger_scope_can_reveal_failure=True,unknown_inputs_not_inferred=True)

@lru_cache(None)
def physical_content_checks():
    cases=0
    for root,a,fields,parts in [('euu',prior.pot.model(),PBASE,('er7','esa')),('euv',prior.rad.model(),radius.SETTING,('esu','esv','est'))]:
        for vals in product((False,True),repeat=len(parts)):
            m={n:lambda *xs,x=x:x for n,x in zip(parts,vals)};assert run(root,a.values(fields),m)==(vals[0] and vals[1]);cases+=1
        for n in parts:reject(lambda:run(root,a.values(fields),{p:lambda *xs:True for p in parts}|{n:forbidden}));cases+=1
    for vals in product((False,True),repeat=3):
        m={n:lambda x=x:Content(SCENES,(x,False,False)) for n,x in zip(('eun','euw','eux'),vals)};assert run('euy',[],m)==all(vals);cases+=1
    for root,pre,law,fields,ws,a in [('euw','eud','euu',PBASE,P_VARIABLE,prior.pot.model()),('eux','esp','euv',radius.SETTING,R_VARIABLE,prior.rad.model())]:
        row=prior.key(a,a.values(fields));m=a.m|{pre:lambda *xs:prior.key(a,xs)==row,law:lambda *xs:prior.key(a,xs)==row}
        values=['case']+[a.by[n] for n,t in ws]
        assert run(root,values,m,'instance');assert not run(root,values,m|{law:lambda *xs:False},'instance');assert run(root,values,m|{pre:lambda *xs:False,law:lambda *xs:False},'instance');cases+=3
        reject(lambda:run(root,[],m));cases+=1
    return dict(cases=cases,whole_second_and_third_contents_preserved=True,all_three_properties_required=True,inapplicable_cases_not_forced_to_obey=True,native_unbounded_domains_refused=True)

@lru_cache(None)
def binding_checks():
    cases=0;slots_checked=0
    for root,pre,law,fields,fixed,ws in [('euw','eud','euu',PBASE,P_FIXED,P_VARIABLE),('eux','esp','euv',radius.SETTING,R_FIXED,R_VARIABLE)]:
        doc=boundary(root);decl=next(d for d in doc['declarations'] if d['name']==root);b=decl['body'];point=b['variable'];b=b['body'];names={}
        for n,t in ws:assert b['kind']=='forall';names[n]=b['variable'];b=b['body']
        calls={x['symbol']:x for x in walk(b) if x.get('kind')=='call'}
        expected=[dict(kind='variable',name=point) if n=='context' else dict(kind='call',symbol=fixed[n],arguments=[]) if n in fixed else dict(kind='variable',name=names[n]) for n,t in fields]
        assert calls[pre]['arguments']==calls[law]['arguments']==expected;cases+=1
        compact=collapse(scalarize(doc))
        for pivot in range(len(ws)):
            f,d,slots,var,body=lifted(compact,root,pivot,len(ws),'forall');calls={x['symbol']:x for x in walk(body) if x.get('kind')=='call'};env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            def evaluate(selected,allowed):
                rows=lambda picks:{tuple((env|{var:pick})[x['name']] if x['kind']=='variable' else 'a' for x in calls[law]['arguments']) for pick in picks}
                hs,ls=rows(selected),rows(allowed)
                m={x['name']:lambda:'a' for x in f['declarations'] if x['kind']=='primitive'}|{n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{pre:lambda *xs:xs in hs,law:lambda *xs:xs in ls}
                return evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=m,max_steps=30000)[0]['value']
            for selected,allowed,wanted in [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]:assert evaluate(selected,allowed)==wanted,(root,pivot);cases+=1
            slots_checked+=1
    return dict(cases=cases,universal_slots_checked=slots_checked,every_parameter_shared_by_applicability_and_law=True,two_value_diagnostics_not_full_function_enumeration=True)

@lru_cache(None)
def specialization_checks():
    lookup={d['name']:d for d in core()['declarations']}
    expand={'euu','euv','esd','esb','esc','euo','esz','es2','es3','esy'}
    def unfold(x,env=None):
        env={} if env is None else env
        if isinstance(x,list):return [unfold(y,env) for y in x]
        if not isinstance(x,dict):return x
        if x.get('kind')=='quote':return x
        if x.get('kind')=='variable' and x['name'] in env:return deepcopy(env[x['name']])
        if x.get('kind')=='call' and x['symbol'] in expand:
            d=lookup[x['symbol']];vs=unfold(x['arguments'],env);return unfold(d['body'],{p['name']:v for p,v in zip(d['parameters'],vs)})
        if x.get('kind')=='evaluate':
            content=unfold(x['content'],env);point=unfold(x['situation'],env)
            if content['kind']=='content':return unfold(content['body'],{content['variable']:point})
            return dict(kind='evaluate',content=content,situation=point)
        return {k:unfold(v,env) for k,v in x.items()}
    point=dict(kind='call',symbol='ri',arguments=[]);cases=0
    for root,original,fields,fixed in [('euu','esd',PBASE,potential.FIXED),('euv','euo',radius.SETTING,radius.FIXED)]:
        vs=[point if n=='context' else dict(kind='call',symbol=fixed[n],arguments=[]) for n,t in fields]
        actual=unfold(dict(kind='call',symbol=root,arguments=vs));wanted=unfold(dict(kind='evaluate',content=dict(kind='call',symbol=original,arguments=[]),situation=point))
        assert actual==wanted,root;cases+=1
        # A different endpoint / event cannot be silently treated as the source case.
        slot=next(i for i,(n,t) in enumerate(fields) if n==('end' if root=='euu' else 'event'));bad=deepcopy(vs);bad[slot]=dict(kind='call',symbol='rd',arguments=[])
        assert unfold(dict(kind='call',symbol=root,arguments=bad))!=wanted;cases+=1
    for root in ('euw','eux'):
        d=next(d for d in boundary(root)['declarations'] if d['name']==root);assert not any(x.get('symbol') in {'sevy','sets','esa','esr'} for x in walk(d['body']));cases+=1
    return dict(cases=cases,exact_specialization_to_both_existing_full_contents=True,wrong_episode_or_event_distinguished=True,no_old_numeric_projection=True)

@lru_cache(None)
def theory_scope_checks():
    cases=0;vs=['view','matter','frame','case','other'];rows={'eis6w':{('view','matter','frame','eu6','case','other')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'eu6':lambda:Content(SCENES,(True,True,False))}
    cases+=perturb(lambda mm:run('eu7',vs,mm),m,rows)
    assert not run('eu7',vs,m|{'eu6':lambda:Content(SCENES,(True,False,False))});reject(lambda:run('eu7',vs,m|{'eu6':forbidden}));cases+=2
    for allowed,described in product(range(4),repeat=2):
        scope=lambda view,subject,frame,base,candidate:(view,subject,frame,base)==('view','matter','frame','case') and candidate in SCENES[1:]
        permit=lambda view,base,candidate:(view,base)==('view','case') and candidate in SCENES[1:] and bool(allowed&(1<<SCENES[1:].index(candidate)))
        m={'eu7':scope,'eisoe':permit,'eu6':lambda:Content(SCENES,(True,True,True)),'euy':lambda:Content(SCENES,(False,bool(described&1),bool(described&2))),'eiscv':relation({('view','paper','eigj','case')})}
        assert run('eva',[],m)==(allowed==described);cases+=1
    for patch in ({'eu7':lambda *xs:False},{'eiscv':lambda *xs:False},{'eu6':lambda:Content(SCENES,(False,True,True))}):assert not run('eva',[],m|patch);cases+=1
    for n in ('eu7','eisoe','eu6','euy','eiscv'):reject(lambda:run('eva',[],m|{n:forbidden}));cases+=1
    return dict(cases=cases,same_theory_subject_frame_and_background=True,scope_independent_of_theory_permission=True,necessity_is_theory_relative_not_actual_motion=True)

@lru_cache(None)
def presentation_checks():
    rows={'eiswm':{('summary','author',item,content,'paper','case') for item,content in zip(('first','second','third'),('eun','esd','euo'))},'eis3v':{(n,'eup',Q(i+1),'case') for i,n in enumerate(('eun','esd','euo'))},'uh':{('summary','author','eva','section','case')}}
    m={n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['evc']};cases=perturb(lambda mm:run('evc',[],mm),m,rows)
    for name,target in [('eis4q','first'),('eis4u','first'),('eis4u','second')]:assert not run('evc',[],{n:lambda *xs:True for n in rows}|{name:lambda target=target:target});cases+=1
    rows={'eir3':{('summary','author','paper','evd','case')},'ue':{('previous','summary','case')}}
    cases+=perturb(lambda mm:run('eve',[],mm),{n:relation(rs) for n,rs in rows.items()}|{'evd':forbidden},rows)
    return dict(cases=cases,three_distinct_prior_items_and_entire_contents=True,author_document_order_and_theory_claim_preserved=True,quotation_not_execution=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][274];assert u['id']=='einstein-1905:u0275' and not u['math_ids'];assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-complete-motion-expression-reading-v1',unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])),facsimile_pages=[921],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==446 and after.document['statements'][:445]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items());load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert selection_binding(after,[441,442,443,444])==selection_binding(before,[441,442,443,444])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_statements=1,all_445_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('equivalence',equivalence_checks),('physical_content',physical_content_checks),('binding',binding_checks),('specialization',specialization_checks),('theory_scope',theory_scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_complete_motion_expression.py','scripts/check_complete_motion_expression.py','tests/test_complete_motion_expression.py'}
    for p in DEPENDENCIES:paths.update(json.loads(read(p))['source_sha256'])
    return dict(status='three_full_relations_characterize_theory_permitted_motion',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
