"""Diagnose decoded heading subjects, local driving and anchored references.

Full closed-description quantifiers remain in Native. Two-description role
substitution is a binding diagnostic applied only after actual-body equality.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_sixth_heading_visible as check
from scripts import sixth_heading_visible_profile as profile
from scripts import check_sixth_section_heading as source
from scripts import check_material_relative_frame as material
from scripts import check_electric_action as electric
from scripts import check_magnetic_action as magnetic
from scripts import check_vacuum_field_domain as field


@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (sixth-heading-visible fixture)')


def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x


def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


def unknowns(test,model,names):
    for name in names:
        with pytest.raises(ValueError,match='Unknown clock-site-time'):test(model|{name:forbidden})


def perturb(test,model,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert test(model)
    for name,rs in rows.items():
        for row in rs:
            assert not test(model|{name:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not test(model|{name:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    unknowns(test,model,rows);return count


class Cuts:
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
def native_blueprint(serialized):
    old=json.loads(serialized);doc=normalize_document(renamed(old,mapping()))
    recovered={d['name']:d for d in check.restored()['document']['declarations']}
    for i,(original,d) in enumerate(zip(old['declarations'],doc['declarations'],strict=True)):
        if d['kind']!='definition':continue
        assert d['name'] in recovered,original['name']
        actual=deepcopy(recovered[d['name']]);assert actual==d,('Source/Native definition differs',original['name'])
        doc['declarations'][i]=actual
    return normalize_document(doc)


def native_evaluate(document,*,primitives,**options):
    doc=native_blueprint(json.dumps(document,sort_keys=True))
    return evaluate_document(doc,primitives={mapping().get(n,n):fn for n,fn in primitives.items()},**options)


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,ConstructedCuts=Cuts,
        relation=relation,perturb=perturb,unknowns=unknowns,forbidden=forbidden,evaluate_document=native_evaluate)|(extra or {})
    for name in names:
        fn=getattr(module,name);fn=getattr(fn,'__wrapped__',fn)
        ns[name]=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
    return ns


@lru_cache(None)
def models():
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    es=clone(electric,('setup',),dict(arithmetic=arithmetic))['setup']
    ms=clone(magnetic,('setup',),dict(arithmetic=arithmetic,electric_setup=es))['setup']
    fs=clone(field,('setup',),dict(arithmetic=arithmetic))['setup']
    return clone(source,('run','driving_fixture','norm_factory','equation_checks','driving_checks','heading_checks'),
        dict(magnetic_setup=ms,field_setup=fs))


@pytest.mark.parametrize('name',['equation_checks','driving_checks','heading_checks'])
def test_decoded_field_driving_and_heading_models(name):assert models()[name]()


def test_whole_source_parent_and_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    parent=check.previous.document();assert len(doc['statements'])==192 and doc['statements'][:190]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert len(ds)==2896
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==869 and len(check.NEW_DEFINITIONS)==21 and not check.REUSED_DEFINITIONS
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    b=check.bridge();assert b['source_statement_indices']==[193] and list(b['source_units'])==['einstein-1905:u0152']
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(4,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(1,158,34)
    assert len(b['annotations']['entries'])==1 and check.FORMS=={'eispf':'Maxwell-Hertzschen Gleichungen'}
    assert doc['statements'][-1]['body']['symbol']==check.vocabulary()._symbols['printedform']
    previous=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field].get(n)==d for n,d in previous[field].items())
    for oldname,public in profile.SOURCE_RELATIONS.items():
        assert ds[mapping()[oldname]]==renamed(old[oldname],mapping())
        assert profile.CONTRACTS[public]['parameters']==old[oldname]['parameters']


def test_reference_positions_types_and_unknown_arguments():
    b=dict(check.BASE);h=check.context_handlers(b);cases=[]
    for old,i in check.HEADINGS.items():cases.append(('headingreference',[b['ri'],Q(i)],b[old]))
    for old,pos in check.SENTENCES.items():cases.append(('sentencereference',[b['ri'],*map(Q,pos)],b[old]))
    for old,(node,i) in check.DESIGNATIONS.items():cases.append(('designationreference',[b['eirf'],b[node],Q(i),b['ri']],b[old]))
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        cases.append(('describedreference',args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    boundaries=check.text_boundaries();sentence=boundaries['sentences']['sixthopeningsentence']
    assert sentence['position']==[70,1] and [r['unit'] for r in sentence['segments']]==[f'einstein-1905:u{i:04d}' for i in (153,154,155)]
    assert boundaries['designations']=={'eispf':['eisph',1]}
    assert boundaries['headings']['eisph']['parent']=='eispb'


def test_native_reference_lookup_does_not_execute_role_or_quoted_content():
    b=dict(check.BASE)
    for old in (*check.HEADINGS,*check.SENTENCES,*check.DESIGNATIONS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='sixthcapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('sixthcapture',call(check.names()[old])))]
        handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
        handlers['sixthcapture']=lambda x:x==b[old]
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def finite_descriptions(body):
    """Replace only the scope role's one content binder with two diagnostic quotes."""
    body=deepcopy(body);quant=body['arguments'][0]
    assert quant['kind']=='exists' and quant['sort']==dict(kind='description',result='content')
    def substitute(node,term):
        if isinstance(node,list):return [substitute(x,term) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='variable' and node['name']==quant['variable']:return deepcopy(term)
        return {k:substitute(x,term) for k,x in node.items()}
    body['arguments'][0]=dict(kind='or',arguments=[substitute(quant['body'],dict(kind='quote',body=call(mapping()[n]))) for n in ('eion','eiot')])
    return body


@lru_cache(None)
def body_fixture(old,finite=False):
    ds={d['name']:d for d in check.restored()['document']['declarations']};symbol=check.reference_roles()[old]
    body=deepcopy(ds[symbol]);expected={d['name']:d for d in check.role_definitions()}[symbol]
    assert body==expected,'Actual Native role differs before finite substitution'
    if finite:body['body']=finite_descriptions(body['body'])
    decls=[]
    for name in sorted(_references(body['body'])):
        d=ds[name];parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=name,parameters=parameters,result=d['result']))
    slots=[]
    for i,p in enumerate(body['parameters']):
        name='sixtharg'+chr(97+i);slots.append(name);decls.append(dict(kind='primitive',name=name,parameters=[],result=p['sort']))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls+[body],
        statements=[dict(kind='ask',body=call(symbol,*(call(n) for n in slots)))])),slots


def role(old,candidate,model,context='reference',finite=False):
    doc,slots=body_fixture(old,finite);handlers={mapping().get(n,n):fn for n,fn in model.items()}
    handlers.update({n:lambda x=x:x for n,x in zip(slots,[candidate,context],strict=True)})
    return evaluate_document(doc,individuals=('scope','other','section','part','paper','first','author','node'),situations=('reference','other'),
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def test_section_role_binds_heading_parent_depth_and_ordinal():
    rows={'eisdv':{('node','section','part','paper',Q(2),Q(6),'reference')}}
    model={'eisph':lambda:'node','eispb':lambda:'part','eirf':lambda:'paper','eisdv':relation(rows['eisdv'])}
    assert perturb(lambda m:role('eispg','section',m),model,rows)
    assert not role('eispg','part',model|{'eisdv':lambda *xs:True})
    assert not role('eispg','section',model,context='other')


def test_scope_role_binds_node_author_description_scope_and_context():
    rows={'ug':{('node','author','eion','scope','reference')}}
    model={'sixthopeningsentence':lambda:'node','rd':lambda:'author','eispg':lambda:'section','eisdx':lambda:'first','ug':relation(rows['ug'])}
    assert perturb(lambda m:role('zno','scope',m,finite=True),model,rows)
    for content in ('eion','eiot'):
        assert role('zno','scope',model|{'ug':relation({('node','author',content,'scope','reference')})},finite=True)
    for candidate in ('section','first'):
        assert not role('zno',candidate,model|{'ug':lambda *xs:True},finite=True)
    assert not role('zno','scope',model,context='other',finite=True)


def test_native_scope_retains_unrestricted_closed_description_binder():
    native,_=body_fixture('zno');finite,_=body_fixture('zno',True);name=check.reference_roles()['zno']
    original=next(d for d in native['declarations'] if d['name']==name)
    modified=next(d for d in finite['declarations'] if d['name']==name)
    assert original['body']['arguments'][0]['kind']=='exists'
    assert original['body']['arguments'][0]['sort']==dict(kind='description',result='content')
    assert modified['body']['arguments'][0]['kind']=='or' and original!=modified
