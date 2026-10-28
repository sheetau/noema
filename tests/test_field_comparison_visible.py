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
from scripts import check_einstein_field_comparison_visible as check
from scripts import field_comparison_visible_profile as profile
from scripts import check_field_comparison_claim as source
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




def test_source_parent_and_preserved_public_contract():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    parent=check.previous.document()
    assert len(doc['statements'])==200 and doc['statements'][:199]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert len(ds)==3027
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==879 and len(check.NEW_DEFINITIONS)==21
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    b=check.bridge();assert b['source_statement_indices']==[24]
    assert set(b['source_units'])=={f'einstein-1905:u{i:04d}' for i in (163,164)}
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(1,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(1,162,38)
    assert check.FORMS=={}
    assert ds[mapping()['eispz']]==renamed(old['eispz'],mapping())
    assert profile.CONTRACTS['twofielddisplayform']['parameters']==old['eispz']['parameters']



def reference_values():
    b=dict(check.BASE)
    for old,sort in check.REFERENCE_SORTS.items():
        if isinstance(sort,dict):b[old]=FunctionValue(tuple(sort['parameters']),sort['result'],forbidden)
    return b


def test_reference_positions_types_and_every_lookup_slot():
    b=reference_values();h=check.context_handlers(b);cases=[]
    for old,(paragraph,sentence) in check.SENTENCES.items():
        cases.append(('sentencereference',[b['ri'],Q(paragraph),Q(sentence)],b[old]))
    for old,(node,start,end) in check.SPANS.items():
        cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    for old,(node,i) in check.DESIGNATIONS.items():
        cases.append(('designationreference',[b['eirf'],b[node],Q(i),b['ri']],b[old]))
    for old,sort in check.REFERENCE_SORTS.items():
        kind=check.reference_kind(old)
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=[sort,'situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        cases.append((kind,args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h[kind](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    boundaries=check.text_boundaries()
    assert {n:r['position'] for n,r in boundaries['sentences'].items()}=={'eisp2':[73,1],'eisp3':[73,2],'fieldresultssentence':[73,3]}
    assert boundaries['designations']=={}


def test_native_reference_lookup_never_executes_roles_or_candidates():
    b=reference_values()
    for old in (*check.SENTENCES,*check.SPANS,*check.DESIGNATIONS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='comparisoncapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('comparisoncapture',call(check.names()[old])))]
        handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
        # Function values can be wrapped by the evaluator; the capture checks the
        # declared type without executing the candidate or its quoted role.
        handlers['comparisoncapture']=lambda x,sort=sort,old=old: x==b[old] if sort=='individual' else isinstance(x,FunctionValue) and x.parameters==tuple(sort['parameters']) and x.result==sort['result']
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def substitute(node,variable,term):
    if isinstance(node,list):return [substitute(x,variable,term) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==variable:return deepcopy(term)
    return {k:substitute(x,variable,term) for k,x in node.items()}


@lru_cache(None)
def models():
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    base_setup=clone(field,('setup',),dict(arithmetic=arithmetic))['setup']
    ns=clone(source,('fixture','run','setup','setting_checks','equivalence_checks','form_checks','scale_checks','presentation_checks'),dict(base_setup=base_setup))
    ns['fixture']=lru_cache(None)(ns['fixture'])
    original=ns['setup']
    def setup(*args,**kwargs):
        s=original(*args,**kwargs);oldnorm=s['norm']
        # A quoted closed form contains its actual visible spelling. Compare
        # its checked inverse name at the legacy diagnostic boundary only.
        norm=lambda xs:oldnorm(tuple(value(x) if isinstance(x,DescriptionValue) else x for x in xs))
        s['norm']=norm;s['rel']=lambda rows:lambda *xs:norm(xs) in rows
        return s
    ns['setup']=setup
    return ns


@pytest.mark.parametrize('name',['setting_checks','equivalence_checks','form_checks','scale_checks','presentation_checks'])
def test_decoded_full_comparison_scope_equivalence_form_scale_and_presentation(name):
    assert models()[name]()




def test_decoded_vector_scale_zero_negative_nonunique_and_axis_membership():
    s=models()['setup']();c=s['c'];run=models()['run']
    cases=[
        (2,(1,2,3),(2,4,6),('x','y','z'),True),
        (-2,(1,2,3),(-2,-4,-6),('x','y','z'),True),
        (0,(1,2,3),(0,0,0),('x','y','z'),True),
        (1,(0,0,0),(0,0,0),('x','y','z'),True),
        (2,(0,0,0),(0,0,0),('x','y','z'),True),
        (2,(1,2,3),(2,6,6),('x','y','z'),False),
        (2,(1,0,0),(0,1,0),('x','y','z'),False),
        (2,(1,2,3),(2,4,6),(),False),
        (2,(1,2,3),(2,4,6),('x','x'),False),
        (2,(1,2,3),(2,4,6),('z','x','y'),True)]
    def vector(values):return FunctionValue(('individual',),profile.CUT,lambda axis:c(dict(zip(('x','y','z'),values)).get(axis,0)))
    for scale,left,right,axes,want in cases:
        assert run('sag2',[SequenceValue(axes,'"individual"'),c(scale),vector(left),vector(right)],s['m'])==want


def test_coefficient_role_is_typed_acyclic_and_has_no_proportionality_filter():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    name=check.reference_roles()['znz'];role=ds[name]
    assert role==check.role_definitions()[0]
    assert role['parameters'][0]['sort']==check.REFERENCE_SORTS['znz']
    assert role['body']['kind']=='forall' and role['body']['sort']==profile.CUT
    assert _references(role['body'])=={mapping()[n] for n in ('s45','tc','ba')}
    seen=set();active=set()
    def visit(n):
        assert n not in active
        if n in seen:return
        seen.add(n);active.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
        active.remove(n)
    visit(name)
    assert not seen&{mapping()[n] for n in ('znz','zeq','sak2','sai2','ejub','ejuh','ejuj','ejuq')}
    assert check.REFERENCE_ANCHORS=={'znz':'fieldscaleanchor'}


def coefficient_role_fixture(sample=False):
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    name=check.reference_roles()['znz'];role=deepcopy(ds[name]);assert role==check.role_definitions()[0]
    decls=[]
    for ref in sorted(_references(role['body'])):
        d=ds[ref];parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=ref,parameters=parameters,result=d['result']))
    if sample:
        quantified=role['body'];terms=[]
        for i in range(7):
            n='comparisonspeed'+chr(97+i)
            decls.append(dict(kind='primitive',name=n,parameters=[],result=profile.CUT))
            terms.append(substitute(quantified['body'],quantified['variable'],call(n)))
        body=terms[-1]
        for term in reversed(terms[:-1]):body=dict(kind='and',arguments=[term,body])
        role['body']=body
    decls += [dict(kind='primitive',name='comparisoncandidate',parameters=[],result=check.REFERENCE_SORTS['znz']),
              dict(kind='primitive',name='comparisoncontext',parameters=[],result='situation'),role]
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls,
        statements=[dict(kind='ask',body=call(name,call('comparisoncandidate'),call('comparisoncontext')))]))


def eval_coefficient_role(doc,model):
    handlers={mapping().get(n,n):fn for n,fn in model.items()}
    return evaluate_document(doc,individuals=source.DOMAIN,situations=source.SITUATIONS,
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


@pytest.mark.parametrize('factor',[-2,0,2])
def test_coefficient_role_signed_speed_boundaries_and_value_validity(factor):
    # The original quantified role was checked before this explicit finite
    # interface diagnostic. The ba callback's rejected sentinel tests wiring;
    # it is not a replacement definition of the real-number predicate.
    s=models()['setup']();c,r=s['c'],s['r'];doc=coefficient_role_fixture(sample=True)
    speeds=(-7,-5,-3,0,3,5,7);sort=check.REFERENCE_SORTS['znz']
    def candidate(fn):return FunctionValue(tuple(sort['parameters']),sort['result'],lambda x:c(fn(r(x))))
    model={'tc':lambda:c(5),'comparisoncontext':lambda:'context',
           's45':lambda light,speed:r(light)>0 and r(speed)**2<r(light)**2,
           'ba':lambda x:r(x)!=999}
    model.update({'comparisonspeed'+chr(97+i):lambda n=n:c(n) for i,n in enumerate(speeds)})
    for fn in (lambda speed:factor,lambda speed:factor+speed):
        assert eval_coefficient_role(doc,model|{'comparisoncandidate':lambda:candidate(fn)})
    for rejected in speeds:
        function=candidate(lambda speed:999 if speed==rejected else factor)
        assert eval_coefficient_role(doc,model|{'comparisoncandidate':lambda:function})==(abs(rejected)>=5)
    good=model|{'comparisoncandidate':lambda:candidate(lambda speed:factor)}
    for name in ('tc','s45','ba','comparisoncandidate'):
        with pytest.raises(ValueError):eval_coefficient_role(doc,good|{name:forbidden})


def test_native_coefficient_role_refuses_full_function_domain_enumeration():
    s=models()['setup']();sort=check.REFERENCE_SORTS['znz']
    model={'tc':lambda:s['c'](5),'comparisoncontext':lambda:'context','ba':lambda x:True,'s45':lambda *xs:True,
           'comparisoncandidate':lambda:FunctionValue(tuple(sort['parameters']),sort['result'],lambda x:s['c'](0))}
    with pytest.raises(ValueError,match='rational number domain|Finite function domain'):
        eval_coefficient_role(coefficient_role_fixture(),model)


def test_source_local_correction_and_preserved_nonproportional_counterexample():
    assert json.loads(json.dumps(source.source_record(),ensure_ascii=False))==check.author.read(source.SOURCE)
    record=check.author.read('reports/field-common-scale-v1.json')
    assert record['status']=='partial_common_field_factor_and_insufficient_premise_counterexample'
    assert record['counterexample']['eight_algebraic_balances']==[True]
    assert record['counterexample']['no_common_rational_scalar']['status']=='valid'
    assert record['counterexample']['first_electric']==[1,0,0] and record['counterexample']['second_electric']==[0,1,0]
    assert record['finite_refusal']['refused']
    corrected=source.source_record()['facsimile_corrected_math_cells'];raw=source.source_record()['raw_math_cells']
    assert raw[7].replace('z','Z')==corrected[7] and raw[7]!=corrected[7]
