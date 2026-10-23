"""Check quantity bindings, quantified value comparison and non-factive discourse."""
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
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,RS
from scripts.check_rod_methods import setup,constants as old_constants,value,relation,DOMAIN as OLD_DOMAIN,POINTS,NUM,BOUNDARIES
from scripts.compose_rod_length_claims import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build
from scripts.review_rod_length_claims import SOURCE,DOC,INVENTORY,PRIORS,DEPENDENCIES,source_record

DOMAIN=OLD_DOMAIN+('namea','nameb','claim','forecast','later','movingname','restname')
BOUND=NUM|BOUNDARIES|{'eip2','eip6'}
def forbidden(*xs):raise ValueError('Unknown rod-length-claims input')
def constants():return old_constants()|{n:lambda x=x:x for n,x in {'ze':'namea','zf':'nameb','zg':'claim','zh':'forecast','zi':'later','eisma':'movingname','eismb':'restname'}.items()}


@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,BOUND|({'sbg'} if name in ('eiqh','eiqi') else set()))
    # Strip unused dependencies of the explicitly declared boundary interpretations.
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrlc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrlccontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrlccontext',arguments=[]))
    if isinstance(d['result'],dict) and d['result'].get('kind')=='question':
        doc['declarations'].append(dict(kind='primitive',name='jrlccapture',parameters=[d['result']],result='truth'))
        body=dict(kind='call',symbol='jrlccapture',arguments=[body])
    doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots


def evaluate(doc,m,domain=DOMAIN):return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots)
    captured=[]
    def capture(x):captured.append(x);return True
    result=evaluate(doc,m|{'jrlccontext':lambda:'context','jrlccapture':capture}|{n:(lambda x=x:x) for n,x in zip(slots,args)})
    return captured[0] if captured else result
def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown rod-length-claims' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))
def perturb(check,m,rows):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:relation(rs-{row})});count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:relation((rs-{row})|{bad})});count+=1
    unknowns(check,m,rows);return count


@lru_cache(None)
def quantity_checks():
    cuts,m,rows,expected,norm=setup();m|=constants();m['va']=lambda f:f in ('frame','movingframe');c=cuts.make;count=0
    # eiqf uses exactly the same geometrical axis-length boundary as method a.
    check=lambda mm:run('eiqf',[c(Q(5)),'methodactx'],mm)
    assert check(m);count+=1
    row=next(row for row in expected['eipe'] if row[2]=='methodactx')
    assert not check(m|{'eipe':lambda *xs:False});count+=1
    for i in range(len(row)):
        bad=tuple('other' if j==i else x for j,x in enumerate(row))
        assert not check(m|{'eipe':lambda *xs,rs=(expected['eipe']-{row})|{bad}:norm(xs) in rs});count+=1
    for n in ('xa','va','ti'):
        assert not check(m|{n:lambda *xs:False});count+=1
    unknowns(check,m,('eipe','eislu','eisls','eislt','eislv','eislw'))
    assert check(m|{'za':forbidden,'xe':forbidden,'ya':forbidden});count+=1
    # Method b's label is the native simultaneous endpoint distance, not a rest length.
    check=lambda mm:run('eiqg',[c(Q(4)),'methodbctx'],mm)
    assert check(m);count+=1
    assert not check(m|{'eipk':lambda *xs:False});count+=1
    assert not run('eiqg',[c(Q(5)),'methodbctx'],m);count+=1
    for n in ('xa','va','ti'):
        assert not check(m|{n:lambda *xs:False});count+=1
    for n in ('xn','xo','ra','ta'):
        # The exact coordinate oracle rejects an unconfigured point/frame/unit.
        try:accepted=check(m|{n:lambda:'other'})
        except ValueError:accepted=False
        assert not accepted;count+=1
    assert not check(m|{'xv':lambda:c(Q(9))});count+=1
    unknowns(check,m,('eislu','eipk','xv','eislv','eislw','eisls','eislt'))
    assert check(m|{'za':forbidden,'xh':forbidden,'ya':forbidden});count+=1
    return dict(cases=count,native_same_time_axis_distance_and_rest_axis_length=True,same_rod_frame_unit_context_and_value=True,labels_do_not_execute_measurement_or_assume_initial_equality=True)


def replace_real_sort(node):
    if node==RS:return 'individual'
    if isinstance(node,dict):return {k:replace_real_sort(v) for k,v in node.items()}
    if isinstance(node,list):return [replace_real_sort(v) for v in node]
    return node


@lru_cache(None)
def uniqueness_checks():
    # Only the value carrier is projected. Keep the actual composed quantifiers,
    # comparison, selected method and setting, including same-value distinct aliases.
    domain=('baseline','alias','shorter','longer');numbers=dict(zip(domain,(5,5,4,6)));count=0
    for name,method,setting,equal in (('eiqh','eip2','methodactx',True),('eiqi','eip6','methodbctx',False)):
        doc=replace_real_sort(deepcopy(fixture(name)[0]))
        for bits in product((False,True),repeat=4):
            selected={x for x,b in zip(domain,bits) if b};selected_values={numbers[x] for x in selected}
            for baseline_valid,correct_setting in product((False,True),repeat=2):
                m=constants()|{'jrlccontext':lambda:'context','ya':lambda:'baseline','sbg':lambda x:baseline_valid or numbers[x]!=5,'sca':lambda a,b:numbers[a]==numbers[b],method:lambda val,ctx:correct_setting and ctx==setting and val in selected}
                actual=evaluate(doc,m,domain)
                expected=correct_setting and baseline_valid and len(selected_values)==1 and ((next(iter(selected_values))==5)==equal)
                assert actual==expected,(name,selected,baseline_valid,correct_setting);count+=1
        # The production document retains the real-cut domain; the finite engine
        # must refuse quantifying it rather than silently use these four candidates.
        cuts,m=arithmetic();m|=constants();m|={'ya':lambda:cuts.make(Q(5)),method:lambda *xs:True}
        try:run(name,[],m)
        except ValueError as e:assert 'Cannot finitely quantify the rational number domain' in str(e),str(e)
        else:raise AssertionError('Full real-cut quantification was silently sampled')
    return dict(cases=count,empty_and_multiple_distinct_values_rejected=True,same_value_distinct_representatives_accepted=True,method_and_setting_kept_in_native_composition=True,finite_carrier_projection_only=True,full_real_domain_not_enumerated_or_proved=True)


@lru_cache(None)
def candidate_question_checks():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read;m|=constants();count=0
    for valid_candidate,valid_base,measured,comparison in product((False,True),repeat=4):
        measured_fn=FunctionValue((RS,),'truth',lambda x:measured and r(x)==4)
        valid_fn=FunctionValue((RS,),'truth',lambda x:valid_candidate if r(x)==4 else valid_base if r(x)==5 else False)
        compare_fn=FunctionValue((RS,RS),'truth',lambda x,y:comparison and (r(x),r(y))==(4,5))
        assert run('sbx',[c(Q(4)),c(Q(5)),measured_fn,valid_fn,compare_fn],m)==all((valid_candidate,valid_base,measured,comparison));count+=1
    for selected in (set(),{Q(4)},{Q(4),Q(5)}):
        mm=m|{'eip6':lambda val,ctx:ctx=='methodbctx' and r(val) in selected}
        question=run('eiqj',[],mm)
        for n in (4,5,6):assert question.function(c(Q(n)))==(Q(n) in selected);count+=1
        # A different context does not answer the very same question.
        question=run('eiqj',[],mm|{'yf':lambda:'methodactx'})
        assert not question.function(c(Q(4)));count+=1
    unknown=FunctionValue(('number',),'truth',lambda x:x<4)
    question=run('eiqj',[],m|{'eip6':lambda val,ctx:r(val)==4})
    try:question.function(unknown)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded by finite probing')
    return dict(cases=count,native_real_cut_candidate_and_baseline_roles=True,question_does_not_require_existence_or_uniqueness=True,unknown_cut_rejected=True)


@lru_cache(None)
def presentation_checks():
    count=0;base=constants()
    for name,node,designation,method,label,extra in (
      ('eiqk','namea','movingname','eip2','eiqf',{'zc':{('claim','author','eion','eiqh','scope','context')}}),
      ('eiqn','nameb','restname','eip6','eiqg',{'zd':{('forecast','author','eiqj','eiqi',('eion','eiot'),'later','scope','context')},'eisci':{('later','paper','forecast','context')}})):
        rows={'zb':{(node,'author',method,label,'scope','context')},'eisl7':{(node,'author',designation,method,label,'scope','paper','context')},**extra}
        m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('eip2','eip6','eipe','eipk','ya','sbz','eion','eiot')});count+=1
        if name=='eiqn':
            original=next(iter(rows['zd']))
            for premises in (('eion',),('eiot',),('eion','eion'),('saw','sbd')):
                wrong=original[:4]+(premises,)+original[5:]
                assert not run(name,[],m|{'zd':relation({wrong})});count+=1
            # Premise order has no argumentative force: accept either order in
            # the physical interpretation, while preserving the written pair.
            assert run(name,[],m|{'zd':lambda *xs:tuple(value(x) for x in xs[:4])==original[:4] and set(value(xs[4]))=={'eion','eiot'} and tuple(value(x) for x in xs[5:])==original[5:]});count+=1
    for path in (CORE,FULL):
        original=parse(read(path))
        for i,(node,previous,msg) in enumerate((('claim','methodb','eiql'),('forecast','claim','eiqo'))):
            doc=dict(original,statements=[original['statements'][-2+i]])
            rows={'eir3':{(node,'author','paper',msg,'context')},'ue':{(previous,node,'context')}}
            m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:evaluate(doc,mm),m,rows)
            assert evaluate(doc,m|{n:forbidden for n in ('zb','zc','zd','eisl7','eisci','eip2','eip6','ya')});count+=1
    return dict(cases=count,prospective_names_and_frame_labels_distinct=True,first_principle_necessity_and_two_principle_forecast=True,same_initial_length_comparison_not_two_method_equality=True,quotes_do_not_execute_measurements_principles_or_derivations=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==259
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,index in zip(PRIORS,(255,256)):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    for path in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(path))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);ann=json.loads(read(ANNOTATIONS))['entries'];assert ann[:-2]==json.loads(read('data/rod-methods-identifiers-v1.json'))['entries']
    assert [a['forms'][0]['text'] for a in ann[-2:]]==['die Länge des Stabes im bewegten System','die Länge des (bewegten) Stabes im ruhenden System']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'sbx','sby','sbz','sca','scb','sce','eipe','eipa','eipk','eip2','eip6','eion','eiot'}<=set(ds)
    for n in ('eiqf','eiqg'):assert 'za' not in json.dumps(ds[n]['body'])
    for n,msg in (('eiql','eiqk'),('eiqo','eiqn')):
        assert ds[n]['body']['force']=='assert' and ds[n]['body']['content']['symbol']==msg
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=257,prior_methods_and_meanings_preserved=True,original_names_parentheses_and_both_l_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('quantity',quantity_checks),('uniqueness',uniqueness_checks),('candidate_question',candidate_question_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_rod_length_claims.py','scripts/check_rod_length_claims.py','scripts/review_rod_length_claims.py','tests/test_rod_length_claims.py','scripts/check_rod_methods.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='length_names_necessity_and_future_determination_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['二文の全単位判断登録','u0034以降と予告された後続論証'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
