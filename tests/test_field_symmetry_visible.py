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
from scripts import check_einstein_field_symmetry_visible as check
from scripts import field_symmetry_visible_profile as profile
from scripts import check_field_symmetry_conclusion as source
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


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (field-symmetry fixture)')


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




def test_source_parent_and_composed_symmetry_note_are_preserved():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==207 and doc['statements'][:202]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert len(ds)==3111
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==880 and len(check.NEW_DEFINITIONS)==32
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    assert len(check.LOCAL_NAMES)==43 and len(set(check.names().values()))==len(check.names())
    b=check.bridge();assert b['source_statement_indices']==[26,27,28,29,30]
    assert set(b['source_units'])=={f'einstein-1905:u{i:04d}' for i in (167,168,169,170,171,172,282)}
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(0,0,1)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(5,169,38)
    assert check.FORMS=={} and check.PUBLIC_RELATIONS=={}


def reference_values():
    # This candidate raises if called: lookup must not execute it or its role.
    return dict(check.BASE)|dict(zn7=FunctionValue(('individual',),profile.CUT,forbidden))


def test_reference_positions_footnote_attachment_and_every_lookup_slot():
    b=reference_values();h=check.context_handlers(b);cases=[]
    for old,(paragraph,sentence) in check.SENTENCES.items():
        cases.append(('sentencereference',[b['ri'],Q(paragraph),Q(sentence)],b[old]))
    for old,(node,start,end) in check.SPANS.items():
        cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['zn7'])),check.canonical(profile.ROLE))
    args=[b['eirf'],b['zoa'],role,b['ri']];kind='describedindividualcutfunctionreference'
    cases.append((kind,args,b['zn7']))
    for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):h[kind](*args[:2],bad,args[3])
    cases.append(('footnoteattachmentreference',[b['eirf'],b['fieldsymmetrysentence'],Q(1),Q(1),b['ri']],b['fieldsymmetryattachment']))
    cases.append(('footnotereference',[b['eirf'],b['fieldsymmetryattachment'],Q(1),b['ri']],b['zoa']))
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    boundaries=check.text_boundaries()
    assert boundaries['sentences']['fieldsymmetrysentence']['position']==[75,1]
    assert len(boundaries['sentences']['fieldsymmetrysentence']['tokens'])==17
    assert boundaries['footnote']['after_token']==4 and len(boundaries['footnote']['tokens'])==33
    assert boundaries['footnote']['original_page']=='909' and boundaries['footnote']['inventory_page_at_end']=='921'


def test_native_reference_lookup_does_not_execute_point_or_role():
    b=reference_values();ds={d['name']:d for d in check.restored()['document']['declarations']}
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS,'fieldsymmetryattachment','zoa'):
        doc=deepcopy(check.restored()['document']);sort=ds[check.names()[old]]['result']
        doc['declarations'].append(dict(kind='primitive',name='symmetrycapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('symmetrycapture',call(check.names()[old])))]
        handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
        handlers['symmetrycapture']=lambda x,sort=sort,old=old: x==b[old] if sort=='individual' else isinstance(x,FunctionValue) and x.parameters==('individual',) and x.result==profile.CUT
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


@lru_cache(None)
def models():
    from scripts import check_field_transform as transform
    from scripts import check_total_differential as differential
    from scripts import check_field_comparison_claim as comparison
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    base_setup=clone(field,('setup',),dict(arithmetic=arithmetic))['setup']
    final_setup=clone(comparison,('setup',),dict(base_setup=base_setup))['setup']
    transform_setup=clone(transform,('setup',))['setup']
    numeric_setup=clone(differential,('setup',),dict(base_setup=transform_setup))['setup']
    ns=clone(source,('fixture','run','contents','premise_checks','probe_setup','probe_checks','coefficient_checks','final_field_checks','presentation_checks'),dict(numeric_setup=numeric_setup,final_setup=final_setup))
    ns['fixture']=lru_cache(None)(ns['fixture'])
    return ns


@pytest.mark.parametrize('name',['premise_checks','probe_checks','coefficient_checks','final_field_checks','presentation_checks'])
def test_decoded_probe_evenness_claimed_unit_final_fields_and_attribution(name):
    assert models()[name]()


def test_point_role_is_acyclic_and_does_not_select_successful_probes():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    role=check.role_definitions()[0];assert ds[role['name']]==role
    assert role['parameters'][0]['sort']==profile.MAP
    seen=set();active=set()
    def visit(n):
        assert n not in active
        if n in seen:return
        seen.add(n);active.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
        active.remove(n)
    visit(role['name'])
    assert check.names()['symmetryproberole'] in _references(ds[check.names()['zn7']]['body'])
    assert not seen&{mapping()[n] for n in ('zn7','sbe2','sbf2','znz','zb7','ejvf','ejvg','ejvh','ejvi','ejvk')}


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


def test_native_point_role_checks_each_coordinate_and_same_region():
    name=check.reference_roles()['zn7'];doc=native_library([name])
    # Keep the original native role, using explicit fixture inputs for its
    # axes, region and real-value predicate. This diagnoses the role bindings;
    # the reference lookup path is exercised separately above.
    assert next(d for d in doc['declarations'] if d['name']==name)==check.role_definitions()[0]
    for d in doc['declarations']:
        if d['name'] in {mapping()[n] for n in ('ba','znk','yn','yo','yp','zc7')}:
            if d['kind']=='definition':
                d['parameters']=[p['sort'] for p in d['parameters']]
            d['kind']='primitive';d.pop('body',None)
    doc['declarations'] += [dict(kind='primitive',name='symmetrycandidate',parameters=[],result=profile.MAP),
                            dict(kind='primitive',name='symmetrycontext',parameters=[],result='situation')]
    doc['statements']=[dict(kind='ask',body=call(name,call('symmetrycandidate'),call('symmetrycontext')))]
    cuts=Cuts();c,r=cuts.make,cuts.read;axes=('x','y','z','t');point=(1,-2,0,3)
    def run(values=point,inside=True,changed=None):
        model={n:lambda axis=axis:axis for n,axis in zip(('yn','yo','yp','zc7'),axes)}
        model|={'symmetrycandidate':lambda:FunctionValue(('individual',),profile.CUT,lambda axis:c(values[axes.index(axis)] if axis in axes else 999)),
                'symmetrycontext':lambda:'context','aa':lambda a,b:a<b,'ab':lambda a,b:a+b,
                'ba':lambda cut:r(cut)!=999,'znk':lambda:FunctionValue(tuple([profile.CUT]*4),'truth',lambda *xs:inside and tuple(map(r,xs))==point)}
        if changed:model.update(changed)
        handlers={mapping().get(n,n):fn for n,fn in model.items()}
        return evaluate_document(doc,individuals=(*axes,'other'),situations=('context','other'),
            primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']
    assert run() and not run(inside=False)
    for slot in range(4):
        for replacement in (999,point[slot]+1):
            changed=list(point);changed[slot]=replacement;assert not run(changed)
    for boundary in ('symmetrycandidate','ba','znk','yn','yo','yp','zc7'):
        with pytest.raises(ValueError):run(changed={boundary:forbidden})


def test_source_negative_branch_and_same_old_event_evidence_are_preserved():
    assert json.loads(json.dumps(source.source_record(),ensure_ascii=False))==check.author.read(source.SOURCE)
    report=check.author.read('reports/field-scale-inverse-v1.json')
    assert report['polynomial_lemmas']['claims']['negative_branch_is_a_counterexample_to_unit_conclusion']['status']=='valid'
    parity=check.author.read('reports/field-parity-v1.json')
    assert parity['components']['same_old_event_compared_at_both_speeds']
    assert parity['components']['no_equal_numeric_new_coordinates_assumed']
    branches=models()['coefficient_checks']()['branches']
    assert branches['negative']==dict(even=True,unit=False,premise=True)
    assert branches['zero_speed']['even']
