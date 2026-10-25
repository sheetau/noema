"""Check fraction displays, shared coefficient roles and conditional discourse."""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from math import isqrt
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_force_measurement as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_directional_masses import *

DOC='docs/electron-directional-masses-v1.md';SOURCE='data/einstein-electron-directional-masses-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf'
DEPENDENCIES=('reports/electron-force-measurement-v1.json','reports/electron-mass-rewrite-v1.json','reports/mass-coefficients-v1.json')
CONSTANTS=prior.CONSTANTS|{n:n for n in REFERENCES}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values()]))
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk
NUM=prior.prior.prior.prior.base.BOUNDS|{'cj'}
BOUNDS={'emj':{'emc'},'emm':{'eml','emj'},'emn':{'emm'},'emo':{'emc','emk','emj'},'emp':{'eml'},'emq':{'eml'},'emr':{'emc','sepi'},'ems':{'emc','emk'},'emy':{'elk','emc','eme','emd','emv','emw'},'em3':{'ema','emb','elu'},'em6':{'enc','emu','enb','elu','emr','emp','emq','emd','emv','emw'},'em2':{'emz'},'em5':{'em4'},'ena':{'em7'},'enc':{'emt','enb'},'emg':{'emc','emd','emf'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document
@lru_cache(None)
def fixture(root):
    doc=deepcopy(boundary(root));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jdmslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jdmpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jdmpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jdmcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jdmcapture',arguments=[expr])
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m):
    doc,slots=fixture(root);assert len(values)==len(slots);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jdmpoint':lambda:'case','jdmcapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    result=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def numeric_checks():
    cases=0
    for speed in (0,3):
        a=prior.Model(speed,1);c,r=a.c,a.r
        a.by.update(forcerecord='force_record',force=a.point([r(a.by['charge'])*r(a.by['newelectric'](axis)(*map(c,(0,0,0,0)))) for axis in ('x','y','z')]+[0]),accelerationunit='acceleration_unit',accelerationscale=Q(1))
        def sqrt(x):
            value=r(x);n,d=isqrt(value.numerator),isqrt(value.denominator)
            if Q(n*n,d*d)!=value:forbidden()
            return c(Q(n,d))
        mm=a.m|{'cj':sqrt,'emc':lambda *xs:a.key(xs)==a.key(a.values(CONVENTION))}
        L=r(a.by['mass'])*a.beta**3;T=r(a.by['mass'])*a.beta**2
        assert r(run('emh',[],mm))==1-Q(speed,5)**2
        assert r(run('emi',[],mm))==Q(1,a.beta);cases+=2
        assert run('emj',a.values(CONVENTION)+list(map(c,(L,T))),mm);cases+=1
        for wrong in ((L+1,T),(L,T+1),(T,L)):
            if wrong==(L,T):continue
            assert not run('emj',a.values(CONVENTION)+list(map(c,wrong)),mm);cases+=1
        for axis in range(3):
            force=list(a.pv(a.by['force']));force[axis]+=1;values=a.values(CONVENTION);values[[n for n,t in CONVENTION].index('force')]=a.point(force)
            assert not run('emj',values+list(map(c,(L,T))),mm|{'emc':lambda *xs:True});cases+=1
        # Negative square root must not silently preserve the longitudinal sign.
        assert not run('emj',a.values(CONVENTION)+list(map(c,(L,T))),mm|{'cj':lambda x:c(-r(sqrt(x)))});cases+=1
        for name in ('cj','emc'):reject(lambda:run('emj',a.values(CONVENTION)+list(map(c,(L,T))),mm|{name:forbidden}));cases+=1
    return dict(cases=cases,positive_square_root_and_both_printed_denominators=True,three_actual_components_retained=True,finite_exact_rational_diagnostics_only=True)

@lru_cache(None)
def conditional_checks():
    a=prior.force_model();a.by.update(accelerationunit='acceleration_unit',accelerationscale=Q(1));values=a.values(CONVENTION)+[a.c(7),a.c(8)];key=a.key;wanted=key(values);cases=0
    for premise in (False,True):
        for conclusion in (False,True):
            mm={'eml':lambda *xs:key(xs)==wanted and premise,'emj':lambda *xs:key(xs)==wanted and conclusion}
            assert run('emm',values,mm)==(not premise or conclusion);cases+=1
    for name in ('eml','emj'):reject(lambda:run('emm',values,{'eml':lambda *xs:True,'emj':lambda *xs:True}|{name:forbidden}));cases+=1
    for antecedent in (False,True):
        for consequent in (False,True):
            assert run('enc',[],{'emt':lambda:Content(('case','other'),(antecedent,antecedent)),'enb':lambda:Content(('case','other'),(consequent,consequent))})==(not antecedent or consequent);cases+=1
    # Public argument contracts are independent of the implementation body.
    contracts={'eml':{'emd':ALL,'emk':CONVENTION},'emm':{'eml':ALL,'emj':ALL},'emj':{'emf':ALL},'emd':{'emc':CONVENTION}}
    for root,targets in contracts.items():
        d=next(x for x in core()['declarations'] if x['name']==root);names=dict(zip((n for n,t in ALL),(p['name'] for p in d['parameters'])));seen=set()
        for call in walk(d['body']):
            if call.get('kind')=='call' and call.get('symbol') in targets:
                symbol=call['symbol'];assert call['arguments']==[dict(kind='variable',name=names[n]) for n,t in targets[symbol]];seen.add(symbol)
        assert seen==set(targets);cases+=1
    d=next(x for x in core()['declarations'] if x['name']=='emd');names=dict(zip((n for n,t in ALL),(p['name'] for p in d['parameters'])));var=lambda n:dict(kind='variable',name=names[n]);constant=lambda n:dict(kind='call',symbol=n,arguments=[])
    factor=next(x for x in walk(d['body']) if x.get('kind')=='call' and x.get('symbol')=='sepi')
    assert factor['arguments']==[constant('tc'),constant('eisxt'),dict(kind='call',symbol='soy',arguments=[constant('tc'),constant('eisxt')]),var('mass'),var('longitudinal'),var('transverse')];cases+=1
    return dict(cases=cases,conditional_truth_tables_and_same_48_roles=True,coefficient_identity_factor_order_checked=True)

@lru_cache(None)
def presentation_checks():
    names={('eisza',('x',),'emd','emv','paper','tenth','case'),('eiszb',('y','z'),'emd','emw','paper','tenth','case')}
    rows_by={
      'emy':{'eisyu':{('eisyy','author','Adisplay','elk','emc','eme','tenth','case')},'eisyv':{('eisyy','author','tenth','case')},'eisyx':names},
      'em3':{'uh':{('eisyz','author','ema','tenth','case'),('eisy2','author','emb','tenth','case')},'eiswm':{('eisyz','author','chaindisplay','elu','paper','case')},'eir5':{('eisy2','author','eisyz','emb','case')},'eisa5':{('eisy2','author','ema','emb','case')},'ue':{('eisyz','eisy2','case'),('eisy2','eisy3','case')}},
      'em6':{'uh':{('eisy3','author','enc','tenth','case')},'zc':{('eisy3','author','emu','enb','tenth','case')},'eiswm':{('eisy3','author','chaindisplay','elu','paper','case')},'eisd4':{('eisy3','author','Kname','frame','paper','case')},'eisox':{('eisy4','emr','case'),('eisy5','emp','case'),('eisy6','emq','case')},'eisyx':names,'uf':{('author','eisy3','eisy5','case'),('author','eisy3','eisy6','case')},'ue':{('eisy3','eisy4','case'),('eisy4','eisy5','case'),('eisy5','eisy6','case')}},
      'em2':{'eir3':{('eisyy','author','paper','emz','case')},'ue':{('Adisplay','eisyy','case'),('eisyy','rewrite','case')}},
      'em5':{'eir3':{('eisyz','author','paper','em4','case')},'ue':{('chaindisplay','eisyz','case')}},
      'ena':{'eir3':{('eisy3','author','paper','em7','case')},'ue':{('eisy2','eisy3','case')}},
    };cases=0
    for root,rows in rows_by.items():
        mm={n:relation(rs) for n,rs in rows.items()}
        cases+=perturb(lambda m:run(root,[],m),mm,rows)
        assert run(root,[],mm|{n:forbidden for n in BOUNDS[root]});cases+=1
    a=prior.force_model();a.by.update(accelerationunit='acceleration_unit',accelerationscale=Q(1))
    rows={'eisyw':{('eisy3','author','eisy7','force_record','paper','case')}}
    cases+=perturb(lambda m:run('emk',a.values(CONVENTION),m),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,question_custom_names_example_parenthesis_and_conditional_derivation=True,quoted_contents_not_executed=True)

@lru_cache(None)
def binding_checks():
    def transform(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jdmunit',arguments=[])
        return {k:transform(x) for k,x in node.items()}
    cases=0
    for root,fields in [('emn',BOUND+EXTRA_MASS+COEFFICIENTS),('emo',BOUND+EXTRA_MASS)]:
        doc=collapse(transform(boundary(root)));doc['declarations'].append(dict(kind='primitive',name='jdmunit',parameters=[],result='individual'));doc['declarations'].sort(key=lambda x:x['kind']!='primitive')
        d=next(x for x in doc['declarations'] if x['name']==root);body=d['body']['body'];bindings=[]
        for _ in fields:bindings.append(dict(name=body['variable'],sort=body['sort']));body=body['body']
        mapping=dict(zip((n for n,t in fields),(p['name'] for p in bindings)));var=lambda n:dict(kind='variable',name=n);constant=lambda n:dict(kind='call',symbol=n,arguments=[])
        fixed={'frame':constant('ra'),'event':constant('eisxv'),'electricconversion':constant('jdmunit'),'context':var(d['body']['variable'])}
        actual=[fixed[n] if n in fixed else var(mapping['oldpoint' if n=='point' else n]) for n,t in (ALL if root=='emn' else CONVENTION)]
        if root=='emn':assert body==dict(kind='call',symbol='emm',arguments=actual)
        else:
            assert body['kind']=='implies';calls=[x for x in walk(body['arguments'][0]) if x.get('kind')=='call' and x.get('symbol') in ('emc','emk')];assert [(x['symbol'],x['arguments']) for x in calls]==[('emc',actual),('emk',actual)]
            start=body['arguments'][1];w=start;wvars=[]
            for _ in COEFFICIENTS:assert w['kind']=='exists';wvars.append(var(w['variable']));w=w['body']
            assert w==dict(kind='call',symbol='emj',arguments=actual+wvars)
            sub=(start,[dict(name=d['body']['variable'],sort='situation')]+bindings)
            for pivot in range(2):
                f,dd,slots,varname,b=lifted(doc,root,pivot,2,'exists',sub);env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']}
                row=tuple((env|{varname:'b'})[x['name']] if x['kind']=='variable' else 'a' for x in b['arguments'])
                for succeeds in (False,True):
                    mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{n:lambda:'a' for n in ('ra','eisxv','jdmunit')}|{'emj':lambda *xs:xs==row and succeeds}
                    assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'},max_steps=25000)[0]['value']==succeeds;cases+=1
        cases+=1
        if root!='emn':continue
        for pivot in range(len(fields)):
            f,dd,slots,varname,b=lifted(doc,root,pivot,len(fields),'forall');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']}
            def row(value):return tuple((env|{varname:value})[x['name']] if x['kind']=='variable' else 'a' for x in b['arguments'])
            for allowed,want in [(('a','b'),True),(('a',),False)]:
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{n:lambda:'a' for n in ('ra','eisxv','jdmunit')}|{'emm':lambda *xs:xs in {row(x) for x in allowed}}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'},max_steps=25000)[0]['value']==want;cases+=1
    reject(lambda:run('emn',[],{'emm':lambda *xs:True}));cases+=1
    return dict(cases=cases,all_44_universal_slots_and_both_existential_candidates=True,independent_public_role_contract_before_small_domain_diagnostics=True,full_function_domain_refused=True)

@lru_cache(None)
def source_record():
    inventory=json.loads(read(INVENTORY));rows=[]
    for unit in inventory['units'][251:258]:
        assert digest(unit['text'].encode())==unit['text_sha256'];math=[m for m in inventory['math'] if m['id'] in unit['math_ids']]
        for m in math:assert digest(m['mathml'].encode())==m['sha256']
        rows.append(dict(unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],math=math,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',unit['text']))))
    return dict(version='einstein-electron-directional-masses-reading-v1',units=rows,facsimile_pages=[918,919],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==426 and after.document['statements'][:423]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[422])==selection_binding(before,[422]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES),new_statements=3,all_423_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('conditional',conditional_checks),('presentation',presentation_checks),('bindings',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_directional_masses.py','scripts/check_electron_directional_masses.py','tests/test_electron_directional_masses.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='directional_masses_question_force_example_and_conditional_display_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
