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
from scripts import check_einstein_magnetic_auxiliary_visible as check
from scripts import magnetic_auxiliary_visible_profile as profile
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


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (two-force-wordings fixture)')


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


def test_recovered_selection_preserves_parent_and_reviewed_meanings():
    doc=check.restored()['document']
    # document() opens the session which validates both the archived parent
    # state and the new active selection before calling historical constructors.
    check.document();parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==221 and doc['statements'][:216]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==899 and len(check.NEW_DEFINITIONS)==37
    assert len(check.LOCAL_NAMES)==45
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    bridge=check.bridge()
    assert bridge['source_statement_indices']==[38,39,40,41]
    assert set(bridge['source_units'])=={'einstein-1905:u0176'}
    assert (bridge['new_public_relations'],bridge['new_reference_primitives'],bridge['new_core_words'])==(8,0,0)
    assert (bridge['new_source_assertions'],bridge['total_source_assertions'],bridge['total_annotations'])==(4,181,40)


def test_reference_positions_quoted_designation_and_unknown_inputs():
    bounds=check.text_boundaries();b=dict(check.BASE);h=check.context_handlers(b)
    assert bounds['coordinates']=={'zps':[79,1],'magauxsecondsentence':[79,2]}
    assert check.SPANS=={'zpv':['magauxsecondsentence',1,16],
        'zpt':['magauxsecondsentence',23,37],'magauxtheoryanchor':['magauxsecondsentence',6,7]}
    for old,(paragraph,sentence) in check.SENTENCES.items():
        assert h['sentencereference'](b['ri'],Q(paragraph),Q(sentence))==b[old]
    for old,(node,start,end) in check.SPANS.items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args[:];bad[slot]=Q(999) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    args=[b['eirf'],b['zps'],Q(1),b['ri']]
    assert h['designationreference'](*args)==b['eisqv']
    for slot in range(4):
        bad=args[:];bad[slot]=Q(999) if slot==2 else 'unknown'
        with pytest.raises(ValueError):h['designationreference'](*bad)


def test_native_reference_lookup_does_not_execute_quoted_theory_role():
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
        capture='magneticcapture'+chr(97+i)
        doc['declarations'].append(dict(kind='primitive',name=capture,parameters=['individual'],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(capture,call(check.names()[old]))))
        handlers[capture]=lambda x,old=old:x==b[old]
    results=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),
        situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)
    assert len(results)==len(targets) and all(r['value'] is True for r in results)


@lru_cache(None)
def models():
    from scripts import check_comoving_wording as comoving
    from scripts import check_field_transform as transform
    from scripts import check_total_differential as differential
    from scripts import check_force_motion_binding as motion
    from scripts import check_magnetomotive_wording as magnetic
    from scripts import check_physical_field_dependence as dependence
    from scripts import check_auxiliary_role as auxiliary
    numeric=clone(transform,('setup',))['setup']
    total=clone(differential,('setup',),dict(base_setup=numeric))['setup']
    vector=clone(motion,('vector',))['vector']
    electric=clone(source,('fixture','run','setup'),dict(numeric_setup=total,vector=vector))
    moving=clone(comoving,('fixture','run','setup','memo_field'),dict(numeric_setup=numeric,vector=vector))
    first=clone(magnetic,('fixture','run','setup','motion_checks','approximation_checks','force_checks','comoving_checks','presentation_checks'),
        dict(base_setup=moving['setup'],electric_setup=electric['setup']))
    second=clone(dependence,('fixture','run','setup','realization_checks','geometry_checks','pair_checks','presence_checks','binding_checks','presentation_checks'),dict(base_setup=moving['setup']))
    third=clone(auxiliary,('fixture','run','model','full_rows','designation_checks','role_checks','explanation_checks'))
    for ns in (electric,moving,first,second,third):ns['fixture']=lru_cache(None)(ns['fixture'])
    return dict(magnetic=first,dependence=second,auxiliary=third)


@pytest.mark.parametrize('group,name',[
    ('magnetic','motion_checks'),('magnetic','approximation_checks'),('magnetic','force_checks'),
    ('magnetic','comoving_checks'),('magnetic','presentation_checks'),
    ('dependence','realization_checks'),('dependence','geometry_checks'),('dependence','pair_checks'),
    ('dependence','presence_checks'),('dependence','binding_checks'),('dependence','presentation_checks'),
    ('auxiliary','designation_checks'),('auxiliary','role_checks'),('auxiliary','explanation_checks')])
def test_decoded_physical_bodies_and_auxiliary_concept_bindings(group,name):
    assert models()[group][name]()


def replace_free(node,name,expression):
    if isinstance(node,list):return [replace_free(x,name,expression) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==name:return deepcopy(expression)
    if node.get('kind') in ('exists','forall','lambda') and node.get('variable')==name:return deepcopy(node)
    return {k:replace_free(x,name,expression) for k,x in node.items()}


def one_binder_run(ns,name,args,model,selected):
    doc,slots=deepcopy(ns['fixture'](name,'witness'))
    target=next(d for d in doc['declarations'] if d['name']==name);fixed={};count=0
    def specialize(node):
        nonlocal count
        if isinstance(node,list):return [specialize(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='exists':
            index=count;count+=1;body=specialize(node['body'])
            if index==selected:return dict(node,body=body)
            n='magneticfixed'+chr(97+index);fixed[n]='a'
            doc['declarations'].insert(0,dict(kind='primitive',name=n,parameters=[],result='individual'))
            return replace_free(body,node['variable'],call(n))
        return {k:specialize(v) for k,v in node.items()}
    target['body']=specialize(target['body']);assert 0<=selected<count
    mm={n:lambda x=x:x for n,x in ns['CONSTANTS'].items()}|model
    mm.update({n:lambda x=x:x for n,x in fixed.items()})
    mm.update({n:lambda x=x:x for (n,sort),x in zip(slots,args,strict=True)})
    return native_evaluate(doc,individuals=('a','b'),situations=('case','other'),
        primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)[0]['value']


@pytest.mark.parametrize('name,callee,slots',[('ejy4','ejy3',2),('ejy7','ejy6',7),('ejzb','ejza',6)])
def test_each_magnetic_witness_with_other_witnesses_instantiated(name,callee,slots):
    ns=models()['magnetic'];args=['a']*6+['case']
    for selected in range(slots):
        witnesses=tuple('b' if i==selected else 'a' for i in range(slots));target=tuple(args)+witnesses
        m={callee:lambda *xs:xs==target}
        if name=='ejy4':m.update(ejsj=lambda *xs:xs==('a','a'),ejsy=lambda ctx:ctx=='case',znk=lambda:'a')
        if name=='ejy7':m['ejzi']=lambda *xs:xs==tuple(args)+(witnesses[0],)
        run=lambda mm:one_binder_run(ns,name,args,mm,selected)
        assert run(m)
        for slot in range(len(target)):
            bad=target[:slot]+('unavailable',)+target[slot+1:]
            assert not run(m|{callee:lambda *xs,bad=bad:xs==bad})
        for relation_name in set(m)-{'znk'}:assert not run(m|{relation_name:lambda *xs:False})
        unknowns(run,m,m.keys())


def test_both_magnetic_wordings_for_each_motion_and_unsampled_domain_rejection():
    from itertools import product
    ns=models()['magnetic']
    for slot in range(6):
        target=tuple('b' if i==slot else 'a' for i in range(6))+('case',)
        for old,new in product((False,True),repeat=2):
            m={'ejy4':lambda *xs:xs==target,'ejy7':lambda *xs:old,'ejzb':lambda *xs:new}
            assert ns['run']('ejzc',[],m,'witness',('a','b'))==(old and new)
    setup=ns['setup']()
    for name in ('ejy4','ejy7','ejzb'):
        with pytest.raises(ValueError,match='rational number domain|Finite function domain'):
            ns['run'](name,setup['local'],setup['m'])


def test_corrected_presentation_uses_source_positions_and_whole_sentence():
    from scripts import compose_auxiliary_reference_order as corrected
    ns=clone(corrected,('fixture','run'),dict(quoted=value))
    # A message is quoted by the presentation; it is not a truth-valued ask.
    # Its complete decoded definition is checked by checked_extract() below.
    for name in ('magauxmainclauseorder','magauxwholeassertion','magauxwholepresentation'):
        assert ns['run'](name)
    assert corrected.before('zpv','zpt','ri')
    assert not corrected.before('zpt','zpv','ri')
    assert not corrected.before('zpv',corrected.WHOLE,'ri')
    assert not corrected.before(corrected.WHOLE,'zpv','ri')
    assert not ns['run']('magauxmainclauseorder',{'ue':lambda *xs:False})
    assert not ns['run']('magauxwholepresentation',{'ue':lambda *xs:False})
    for relation_name in ('uh','zdg'):
        assert not ns['run']('magauxwholeassertion',{relation_name:lambda *xs:False})
    assert not ns['run']('magauxwholepresentation',{'magauxsecondsentence':lambda:'zpv','ue':lambda *xs:True,'eir3':lambda *xs:True})
    assert ns['run']('magauxwholeassertion',{'ejzw':forbidden})
    for args in [('unknown','zpt','ri'),('zpv','unknown','ri'),('zpv','zpt','other')]:
        with pytest.raises(ValueError):corrected.before(*args)


