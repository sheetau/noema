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
from noema.constructed_semantics import Content,FunctionValue,DescriptionValue,SequenceValue,QuestionValue,evaluate_document
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_seat_questions_visible as check
from scripts import seat_questions_visible_profile as profile
from scripts import check_electromotive_wording as source
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


def forbidden(*xs):raise ValueError('Unknown seat-questions diagnostic input')


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
    ns=dict(vars(module))|dict(Content=Content,FunctionValue=FunctionValue,QuestionValue=QuestionValue,ConstructedCuts=Cuts,value=value,
        relation=relation,perturb=perturb,unknowns=unknowns,forbidden=forbidden,
        extract_document=checked_extract,evaluate_document=native_evaluate)|(extra or {})
    for name in names:
        fn=getattr(module,name);fn=getattr(fn,'__wrapped__',fn)
        ns[name]=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
    return ns


def test_recovered_selection_preserves_parent_and_reviewed_meanings():
    doc=check.restored()['document'];check.document();parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==224 and doc['statements'][:221]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==935 and len(check.NEW_DEFINITIONS)==59
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    bridge=check.bridge()
    assert bridge['source_statement_indices']==[196,197,198]
    assert set(bridge['source_units'])=={'einstein-1905:u0177'}
    assert (bridge['new_public_relations'],bridge['new_reference_primitives'],bridge['new_core_words'])==(36,0,0)
    assert (bridge['new_source_assertions'],bridge['total_source_assertions'],bridge['total_annotations'])==(3,184,40)


def test_reference_positions_preserve_inherited_spans_and_reject_unknown_inputs():
    bounds=check.text_boundaries();b=dict(check.BASE);h=check.context_handlers(b)
    assert bounds['coordinates']['eisq7']==[80,1] and bounds['coordinates']['eisrs']==[80,2]
    assert check.SPANS['zpw']==['magauxsecondsentence',17,37]
    # New uses of the inherited sentence must not shadow its old clause spans.
    for old,(node,start,end) in (check.previous.SPANS|check.SPANS).items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args[:];bad[slot]=Q(999) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    for old,(paragraph,sentence) in check.SENTENCES.items():
        assert h['sentencereference'](b['ri'],Q(paragraph),Q(sentence))==b[old]
    for old,(node,index) in (check.previous.DESIGNATIONS|check.DESIGNATIONS).items():
        args=[b['eirf'],b[node],Q(index),b['ri']]
        assert h['designationreference'](*args)==b[old]
        for slot in range(4):
            bad=args[:];bad[slot]=Q(999) if slot==2 else 'unknown'
            with pytest.raises(ValueError):h['designationreference'](*bad)


def test_native_reference_lookup_does_not_execute_physical_or_theoretical_roles():
    b=dict(check.BASE);doc=deepcopy(check.restored()['document']);ds={d['name']:d for d in doc['declarations']}
    targets=tuple(check.SENTENCES)+tuple(check.SPANS)+tuple(check.DESIGNATIONS)+tuple(check.ROLE_ASSIGNMENTS)
    needed=set();pending=[check.names()[n] for n in targets]
    while pending:
        n=pending.pop()
        if n in needed:continue
        needed.add(n);pending.extend(_references(ds[n].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate(targets):
        capture='seatcapture'+chr(97+i)
        doc['declarations'].append(dict(kind='primitive',name=capture,parameters=['individual'],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(capture,call(check.names()[old]))))
        handlers[capture]=lambda x,old=old:x==b[old]
    results=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),
        situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)
    assert len(results)==len(targets) and all(r['value'] is True for r in results)
    # Same anchor, different role or context must not retrieve a reference.
    from scripts.temporal_discourse_profile import ROLE
    model=check.reference_model(b)
    for old in check.ROLE_ASSIGNMENTS:
        desc=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(ROLE))
        assert model.described(b['eirf'],b[check.reference_anchor(old)],desc,b['ri'])==b[old]
        with pytest.raises(ValueError):model.described(b['eirf'],b[check.reference_anchor(old)],desc,'unknown')
        wrong=DescriptionValue(check.canonical(dict(kind='function_ref',symbol='unknown')),check.canonical(ROLE))
        with pytest.raises(ValueError):model.described(b['eirf'],b[check.reference_anchor(old)],wrong,b['ri'])


@lru_cache(None)
def models():
    from scripts import check_material_relative_frame as material
    from scripts import check_conductor_cases as cases
    from scripts import check_asymmetry_resolution as asymmetry
    from scripts import check_unipolar_machine as machine
    from scripts import check_seat_questions as questions
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    probes=clone(cases,('sentinel','same_value'))
    extra=dict(arithmetic=arithmetic,sentinel=probes['sentinel'],same_value=probes['same_value'])
    first=clone(asymmetry,('base','fixture','run','classification_checks','physical_binding_checks','projection_checks','scope_checks','presentation_checks'),extra)
    second=clone(machine,('finite_reals','base','fixture','run','setup','polarity_checks','machine_checks','witness_checks','annotation_checks'),extra)
    third=clone(questions,('fixture','run','model','signature','question_checks','premise_checks','transition_checks','presentation_checks'))
    for ns in (first,second,third):
        ns['fixture']=lru_cache(None)(ns['fixture'])
        if 'base' in ns:ns['base']=lru_cache(None)(ns['base'])
    return dict(asymmetry=first,machine=second,questions=third)


@pytest.mark.parametrize('group,name',[
    ('asymmetry','classification_checks'),('asymmetry','physical_binding_checks'),
    ('asymmetry','projection_checks'),('asymmetry','scope_checks'),('asymmetry','presentation_checks'),
    ('machine','polarity_checks'),('machine','machine_checks'),('machine','witness_checks'),('machine','annotation_checks'),
    ('questions','question_checks'),('questions','premise_checks'),('questions','transition_checks'),('questions','presentation_checks')])
def test_decoded_native_bodies_and_binding_diagnostics(group,name):
    assert models()[group][name]()


def conductor_fixture(symbol,native=False):
    from scripts import check_conductor_reading as source
    doc=checked_extract(source.parse(source.read(source.CORE)),roots=[symbol],statement_indices=[]).document
    source.abstract(doc,source.NUM|{'eibf'}|({'eicg'} if symbol in ('eich','eici') and not native else set()))
    target=next(d for d in doc['declarations'] if d['name']==symbol);slots=[]
    for i,p in enumerate(target['parameters']):
        n='seatconductorslot'+source.number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=call(symbol,*(call(n) for n,_ in slots)))]
    return doc,slots


@lru_cache(None)
def conductor_model():
    from scripts import check_material_relative_frame as material
    from scripts import check_conductor_reading as source
    class ConductorCuts(Cuts):
        def read(self,value):
            try:return super().read(value)
            except ValueError as error:raise ValueError('Cut not constructed in this finite diagnostic') from error
    arithmetic=clone(material,('arithmetic',),dict(ConstructedCuts=ConductorCuts))['arithmetic']
    result=clone(source,('run','values','equal','sorts','setup','mutate','window_checks','trial_checks','capacity_checks'),
        dict(arithmetic=arithmetic,fixture=lru_cache(None)(conductor_fixture),forbidden=source.forbidden))
    result['sorts']=lru_cache(None)(result['sorts'])
    return result


@pytest.mark.parametrize('name',['window_checks','trial_checks','capacity_checks'])
def test_decoded_conductor_criteria_possible_result_and_capacity(name):
    assert conductor_model()[name]()
