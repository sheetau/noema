"""Check actual decoded bodies before finite point/binder diagnostics.

Point substitution is explicit. Many-witness checks instantiate the other
binders and vary one binder over two values; they are not full-domain proofs.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,DescriptionValue,evaluate_document
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_field_application_visible as check
from scripts import field_application_visible_profile as profile
from scripts import check_field_transformation_application as source
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


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (field-application fixture)')


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


@lru_cache(None)
def models():
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    setup=clone(field,('setup',),dict(arithmetic=arithmetic))['setup']
    ns=clone(source,('fixture','run','provenance_checks','coverage_checks','numerical_model',
                     'inverse_checks','premise_checks','presentation_checks'),dict(field_setup=setup))
    ns['fixture']=lru_cache(None)(ns['fixture'])
    return ns


@pytest.mark.parametrize('name',['provenance_checks','coverage_checks','inverse_checks','premise_checks','presentation_checks'])
def test_decoded_process_records_inverse_and_author_presentation(name):
    assert models()[name]()


def test_source_parent_and_preserved_public_contracts():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==196 and doc['statements'][:195]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert len(ds)==2957
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==875 and len(check.NEW_DEFINITIONS)==25
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    b=check.bridge();assert b['source_statement_indices']==[22]
    assert set(b['source_units'])=={f'einstein-1905:u{i:04d}' for i in range(156,161)}
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(3,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(1,160,36)
    assert check.FORMS=={}
    for oldname,public in profile.SOURCE_RELATIONS.items():
        assert ds[mapping()[oldname]]==renamed(old[oldname],mapping())
        assert profile.CONTRACTS[public]['parameters']==old[oldname]['parameters']


def test_reference_positions_and_every_lookup_slot():
    b=dict(check.BASE);h=check.context_handlers(b);cases=[]
    for old,(paragraph,sentence) in check.SENTENCES.items():
        cases.append(('sentencereference',[b['ri'],Q(paragraph),Q(sentence)],b[old]))
    for old,(node,start,end) in check.SPANS.items():
        cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['eispp'])),
        check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
    args=[b['eirf'],b['znq'],role,b['ri']]
    cases.append(('describedreference',args,b['eispp']))
    for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    assert check.text_boundaries()['sentences']['fieldapplicationsentence']['position']==[71,1]


def test_native_lookup_does_not_execute_process_role():
    b=dict(check.BASE)
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='fieldcapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('fieldcapture',call(check.names()[old])))]
        handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
        handlers['fieldcapture']=lambda x,old=old:x==b[old]
        assert evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,
            primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def test_process_role_preserves_candidate_context_and_has_no_result_filter():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    name=check.reference_roles()['eispp'];role=ds[name]
    assert role==check.role_definitions()[0]
    assert role['body']==call(mapping()['ejte'],dict(kind='variable',name='va'),dict(kind='variable',name='vb'))
    seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for x in _references(ds[n].get('body')):visit(x)
    visit(name)
    assert not seen&{mapping()[n] for n in ('eispp','s6o','ejtj','ejtk','ejtl','ejtn','ejtp')}
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=mapping()['ejte'],parameters=['individual','situation'],result='truth'),
        dict(kind='primitive',name='fieldcandidate',parameters=[],result='individual'),
        dict(kind='primitive',name='fieldcontext',parameters=[],result='situation'),role],
        statements=[dict(kind='ask',body=call(name,call('fieldcandidate'),call('fieldcontext')))]))
    for candidate in ('a','b'):
        for context in ('context','other'):
            model={'fieldcandidate':lambda:candidate,'fieldcontext':lambda:context,mapping()['ejte']:lambda x,s:(x,s)==('a','context')}
            assert evaluate_document(doc,individuals=('a','b'),situations=('context','other'),primitives=model)[0]['value']==((candidate,context)==('a','context'))


def test_source_six_equations_beta_and_existing_counterexample():
    assert json.loads(json.dumps(source.source_record(),ensure_ascii=False))==check.author.read(source.SOURCE)
    record=check.author.read('reports/field-transform-v1.json')
    assert record['status']=='partial_field_transform_with_insufficient_premise_counterexample'
    assert record['finite_refusal']['refused']
    assert not set(check.mapping())&{'s6p','s5z','sae2','saf2'}


@lru_cache(None)
def transform_models():
    from scripts import check_field_transform as transform
    from scripts import check_rod_setup as rod
    def candidate(text,questions):
        doc=transform.candidate(text,questions)
        return checked_extract(doc,statement_indices=range(len(doc['statements']))).document
    callbacks=clone(rod,('callbacks',))['callbacks']
    def values(doc,model,domain):
        # The historical arithmetic model also supplies unused operations.
        # The extracted Native program requires exactly its declared inputs;
        # any missing interpretation still rejects when actually invoked.
        selected={d['name']:model.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
        return [r['value'] for r in native_evaluate(doc,individuals=domain,situations=('motion','text','other'),
            primitives=selected,max_steps=5_000_000,memoize_definitions=True,memoize_expressions=True)]
    return clone(transform,('setup','affine_callback','component_checks','region_checks','equation_checks','inverse_checks'),
        dict(candidate=candidate,callbacks=callbacks,values=values))


@pytest.mark.parametrize('name',['component_checks','region_checks','equation_checks','inverse_checks'])
def test_decoded_mixing_pullback_and_insufficient_curl_premise(name):
    assert transform_models()[name]()


