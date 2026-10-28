"""Check actual decoded bodies before finite point/binder diagnostics.

Point and coefficient-domain substitution is explicit. Finite diagnostics
do not constitute proofs over all real numbers or function spaces.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,DescriptionValue,SequenceValue,evaluate_document
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_inverse_field_visible as check
from scripts import field_comparison_visible_profile as profile
from scripts import check_inverse_field_claim as source
from scripts import check_vacuum_field_domain as field
from scripts import check_material_relative_frame as material


from scripts.check_tau_differential import ConstructedCuts as HistoricalCuts

class Cuts:
    arithmetic=HistoricalCuts.arithmetic
    def __init__(self):self.table={}
    def make(self,n):
        n=Q(n);f=FunctionValue(('number',),'truth',lambda q:q<n);self.table[f.implementation]=n;return f
    def read(self,f):
        while isinstance(f,FunctionValue):
            impl=f.implementation
            if impl in self.table:return self.table[impl]
            if isinstance(impl,FunctionValue):f=impl;continue
            code=getattr(impl,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(impl,'__closure__',None) or ()))))
            f=free.get('raw')
        raise ValueError('Unregistered finite cut')


@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (field-comparison fixture)')


def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x


def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


def unknowns(test,model,names):
    for name in names:
        with pytest.raises(ValueError):test(model|{name:forbidden})


def perturb(test,model,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert test(model)
    for name,rs in rows.items():
        for row in rs:
            assert not test(model|{name:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not test(model|{name:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    unknowns(test,model,rows);return count


@lru_cache(None)
def checked_extract_json(serialized,roots,indices):
    extracted=extract_document(json.loads(serialized),roots=roots,statement_indices=list(indices))
    original=extracted.document
    mapped=normalize_document(renamed(original,mapping()))
    recovered={d['name']:d for d in check.restored()['document']['declarations']}
    inverse={v:k for k,v in mapping().items()}
    for i,(old,d) in enumerate(zip(original['declarations'],mapped['declarations'],strict=True)):
        if d['kind']!='definition':continue
        actual=deepcopy(recovered[d['name']])
        assert actual==d,('Native definition differs before diagnostic transformation',old['name'])
        original['declarations'][i]=renamed(actual,inverse)
    return extracted


def checked_extract(document,*,roots=(),statement_indices=()):
    return deepcopy(checked_extract_json(json.dumps(document,sort_keys=True),tuple(roots),tuple(statement_indices)))


def native_evaluate(document,*,primitives,**options):
    doc=normalize_document(renamed(document,mapping()))
    return evaluate_document(doc,primitives={mapping().get(n,n):fn for n,fn in primitives.items()},**options)


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(Content=Content,FunctionValue=FunctionValue,ConstructedCuts=Cuts,
        relation=relation,perturb=perturb,unknowns=unknowns,forbidden=forbidden,
        extract_document=checked_extract,evaluate_document=native_evaluate)|(extra or {})
    for name in names:
        fn=getattr(module,name);fn=getattr(fn,'__wrapped__',fn)
        ns[name]=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
    return ns




def test_source_parent_and_composed_methods_are_preserved():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==202 and doc['statements'][:200]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert len(ds)==3067
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==879 and len(check.NEW_DEFINITIONS)==28
    assert all(n in check.previous.names() for n in ('ra','rd','ri','eirf'))
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    assert len(check.LOCAL_NAMES)==40 and len(set(check.names().values()))==len(check.names())
    b=check.bridge();assert b['source_statement_indices']==[31,25]
    assert set(b['source_units'])=={f'einstein-1905:u{i:04d}' for i in (165,166)}
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(0,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(2,164,38)
    assert check.FORMS=={} and check.PUBLIC_RELATIONS=={}
    for old,ref in check.DERIVED_REFERENCES.items():
        assert ds[mapping()[old]]['body']==call(mapping()[ref['relation']],*(call(check.names()[n]) for n in ref['arguments']))


def steps(pairs):
    element=next(d['result']['element'] for d in check.source_excerpt()['declarations'] if d['name']=='zoc')
    description=element['result'];selector=element['parameters'][0]
    def quoted(n):return DescriptionValue(check.canonical(call(mapping()[n])),check.canonical('content'))
    return SequenceValue(tuple(FunctionValue((selector,),description,
        lambda choose,a=a,b=b:choose(quoted(a),quoted(b))) for a,b in pairs),check.canonical(element))


def reference_values():
    # An empty first sequence deliberately proves that lookup does not execute
    # the nonempty-path role. Its validity is checked separately below.
    return dict(check.BASE)|dict(zoc=steps([]),zod=steps([('ejuh','ejut')]))


def test_reference_positions_and_every_lookup_slot():
    b=reference_values();h=check.context_handlers(b);cases=[]
    for old,(paragraph,sentence) in check.SENTENCES.items():
        cases.append(('sentencereference',[b['ri'],Q(paragraph),Q(sentence)],b[old]))
    for old,(node,start,end) in check.SPANS.items():
        cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        cases.append(('describedreference',args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
    for old,ref in check.DERIVED_REFERENCES.items():
        cases.append(('methodsteps',[b[ref['arguments'][0]],b['ri']],b[old]))
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    boundaries=check.text_boundaries()
    assert boundaries['sentences']['inversefieldsentence']['position']==[74,1]
    assert len(boundaries['sentences']['inversefieldsentence']['tokens'])==49
    assert boundaries['designations']=={}


def test_native_reference_lookup_does_not_execute_method_roles_or_sequences():
    b=reference_values();ds={d['name']:d for d in check.restored()['document']['declarations']}
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS,*check.DERIVED_REFERENCES):
        doc=deepcopy(check.restored()['document']);sort=ds[check.names()[old]]['result']
        doc['declarations'].append(dict(kind='primitive',name='inversecapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('inversecapture',call(check.names()[old])))]
        handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
        handlers['inversecapture']=lambda x,sort=sort,old=old: x==b[old] if sort=='individual' else isinstance(x,SequenceValue) and x.element_type==b[old].element_type and len(x.items)==len(b[old].items)
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


@lru_cache(None)
def models():
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    ns=clone(source,('fixture','run','contents','binding_checks','path_checks','necessity_checks','conclusion_checks','presentation_checks'),
        dict(arithmetic=arithmetic,symbol=value))
    ns['fixture']=lru_cache(None)(ns['fixture'])
    return ns


@pytest.mark.parametrize('name',['binding_checks','path_checks','necessity_checks','conclusion_checks','presentation_checks'])
def test_decoded_inverse_methods_necessity_coefficient_product_and_attribution(name):
    assert models()[name]()


def test_method_role_dependencies_and_nonexecution_boundaries():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for role in check.role_definitions():assert ds[role['name']]==role
    graph={n:set(_references(d.get('body'))) for n,d in ds.items()}
    # Include the normally quoted role edge from each method reference.
    for old,name in check.reference_roles().items():assert name in graph[check.names()[old]]
    for name in check.reference_roles().values():
        seen=set();active=set()
        def visit(n):
            assert n not in active
            if n in seen:return
            seen.add(n);active.add(n)
            for ref in graph[n]:visit(ref)
            active.remove(n)
        visit(name)
        assert not seen&{mapping()[n] for n in ('zoc','zod','ejuu','ejux','ejuy','ejuz','ejva','ejvb','ejvc','ejvd','ejve')}
        assert not seen&{check.names()[n] for n in check.ROLE_ASSIGNMENTS}


def native_library(roots):
    """Extract unchanged 0.16 definitions; the historical extractor is 0.14."""
    source=check.restored()['document'];ds={d['name']:d for d in source['declarations']}
    assert set(roots)<=set(ds)
    selected=set();pending=set(roots)
    while pending:
        name=pending.pop()
        if name in selected:continue
        selected.add(name);pending.update(_references(ds[name].get('body'))-selected)
    declarations=[deepcopy(d) for d in source['declarations'] if d['name'] in selected]
    doc=normalize_document(dict(source,declarations=declarations,statements=[]))
    assert doc['declarations']==declarations and not doc['statements']
    return doc


def method_role_fixture(old):
    name=check.reference_roles()[old]
    doc=native_library([name,mapping()['ejus'],mapping()['ejut']])
    doc['declarations'] += [dict(kind='primitive',name='inversemethodcandidate',parameters=[],result='individual'),
                            dict(kind='primitive',name='inversemethodcontext',parameters=[],result='situation')]
    doc['statements']=[dict(kind='ask',body=call(name,call('inversemethodcandidate'),call('inversemethodcontext')))]
    return normalize_document(doc)


@pytest.mark.parametrize('old,target',[('inversefirstmethod','ejus'),('inversesecondmethod','ejut')])
def test_native_method_role_paths_and_each_method_context_slot(old,target):
    doc=method_role_fixture(old)
    def run(pairs,*,candidate='candidate',context='context',step_method='candidate',step_context='context',allow_context='context',allowed=True,changed=None):
        fixture=deepcopy(doc);name=check.reference_roles()[old]
        role=next(d for d in fixture['declarations'] if d['name']==name)
        method=next(d for d in fixture['declarations'] if d['name']==mapping()['zlx'])
        sequence=method['result'];element=sequence['element'];selector=element['parameters'][0]
        # Descriptions must be issued by this evaluation. Python-created
        # DescriptionValue objects are intentionally rejected by the language.
        items=[dict(kind='lambda',parameters=[dict(name='vc',sort=selector)],body=dict(kind='apply',
            function=dict(kind='variable',name='vc'),arguments=[dict(kind='quote',body=call(mapping()[n])) for n in pair])) for pair in pairs]
        fixture['declarations']=[d for d in fixture['declarations'] if d['name'] not in (name,mapping()['zlx'])]
        fixture['declarations'] += [dict(kind='primitive',name='inversestepsdispatch',parameters=['individual','situation',sequence],result=sequence),
            dict(kind='definition',name=mapping()['zlx'],parameters=[dict(name='va',sort='individual'),dict(name='vb',sort='situation')],result=sequence,
                 body=call('inversestepsdispatch',dict(kind='variable',name='va'),dict(kind='variable',name='vb'),dict(kind='sequence',element=element,items=items))),role]
        model={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,
               'inversemethodcandidate':lambda:candidate,'inversemethodcontext':lambda:context,
               'inversestepsdispatch':lambda method,ctx,issued:issued if (method,ctx)==(step_method,step_context) else SequenceValue((),check.canonical(element)),
               'zla':lambda a,b,ctx:allowed and ctx==allow_context and (value(a),value(b)) in {('ejuh',target),('ejuh','ejuh')}}
        if changed:
            model.update(changed)
            for d in fixture['declarations']:
                if d['name'] in {mapping().get(n,n) for n in changed} and d['kind']=='definition':
                    d['kind']='primitive';d['parameters']=[p['sort'] for p in d['parameters']];d.pop('body')
        handlers={mapping().get(n,n):fn for n,fn in model.items()}
        return evaluate_document(fixture,individuals=('candidate','other'),situations=('context','other'),
            primitives={d['name']:handlers.get(d['name'],forbidden) for d in fixture['declarations'] if d['kind']=='primitive'},max_steps=500000)[0]['value']
    assert run([('ejuh',target)])
    assert run([('ejuh','ejuh'),('ejuh',target)])
    assert not run([])
    assert not run([(target,target)])
    assert not run([('ejuh','ejut' if target=='ejus' else 'ejus')])
    assert not run([(target,'ejuh')])
    assert not run([('ejuh',target),('ejuh',target)])
    for options in (dict(candidate='other'),dict(context='other'),dict(step_method='other'),dict(step_context='other'),dict(allow_context='other'),dict(allowed=False)):
        assert not run([('ejuh',target)],**options)
    for boundary in ('inversestepsdispatch','zla','inversemethodcandidate','inversemethodcontext'):
        with pytest.raises(ValueError):run([('ejuh',target)],changed={boundary:forbidden})
    # Quoted contents remain unevaluated even on a successful path.
    assert run([('ejuh',target)],changed={n:forbidden for n in ('ejuh','ejus','ejut','ejur','ejuz')})


def test_full_coefficient_input_domain_is_not_replaced_by_finite_examples():
    doc=native_library([mapping()['sbo2']])
    cuts,model=clone(material,('arithmetic',))['arithmetic']()
    result=profile.CUT
    for n in ('inversecoefficienta','inversecoefficientb'):
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=result))
    doc['statements']=[dict(kind='ask',body=call(mapping()['sbo2'],call('inversecoefficienta'),call('inversecoefficientb')))]
    model|={'inversecoefficienta':lambda:cuts.make(2),'inversecoefficientb':lambda:cuts.make(Q(1,2))}
    handlers={mapping().get(n,n):fn for n,fn in model.items()}
    with pytest.raises(ValueError,match='rational number domain|Finite function domain'):
        evaluate_document(doc,individuals=source.DOMAIN,situations=source.SITUATIONS,
            primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000)


def test_source_glyph_distinction_and_preserved_inverse_algebra_counterexample():
    assert json.loads(json.dumps(source.source_record(),ensure_ascii=False))==check.author.read(source.SOURCE)
    record=source.source_record()
    assert record['raw_math']=={'M0308':'k','M0309':'K','M0310':'−v','M0311':'φ(v).φ(−v)=1'}
    inverse=check.author.read('reports/inverse-methods-v1.json')
    assert inverse['finite_refusal']['refused']
    assert inverse['scalars']['nonzero_witness_algebra']['status']=='valid'
    assert inverse['fields']['zero_field_agreement_not_general_operator_agreement']
    assert inverse['source_binding']['global_field_equality_and_domain_equality_are_explicit_fixture_oracles']
