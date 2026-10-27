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
from noema.constructed_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_vacuum_assumption_visible as check
from scripts import vacuum_assumption_visible_profile as profile
from scripts import check_vacuum_equation_assumption as source
from scripts import check_vacuum_field_domain as field
from scripts import check_material_relative_frame as material


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
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (vacuum-assumption fixture)')


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
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,ConstructedCuts=Cuts,
        relation=relation,perturb=perturb,unknowns=unknowns,forbidden=forbidden,
        extract_document=checked_extract,evaluate_document=native_evaluate)|(extra or {})
    for name in names:
        fn=getattr(module,name);fn=getattr(fn,'__wrapped__',fn)
        ns[name]=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
    return ns


@lru_cache(None)
def models():
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    fs=clone(field,('setup',),dict(arithmetic=arithmetic))['setup']
    return clone(source,('fixture','run','setup','physical_checks','equation_binding_checks','altered',
                         'vector_checks','curl_checks','presentation_checks'),dict(field_setup=fs))


@pytest.mark.parametrize('name',['physical_checks','equation_binding_checks','vector_checks','curl_checks','presentation_checks'])
def test_decoded_physical_vector_equation_and_presentation_bodies(name):
    assert models()[name]()


def test_source_parent_and_public_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    parent=check.previous.document();assert len(doc['statements'])==195 and doc['statements'][:192]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert len(ds)==2923
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==872 and len(check.NEW_DEFINITIONS)==13
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    b=check.bridge();assert b['source_statement_indices']==[21]
    assert set(b['source_units'])=={f'einstein-1905:u{i:04d}' for i in (153,154,155)}
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(2,0,1)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(1,159,36)
    assert check.FORMS=={'eispj':'(X,Y,Z)','eispk':'(L,M,N)'}
    assert all(s['body']['symbol']==check.vocabulary()._symbols['printedform'] for s in doc['statements'][-2:])
    for oldname,public in profile.SOURCE_RELATIONS.items():
        assert ds[mapping()[oldname]]==renamed(old[oldname],mapping())
        assert profile.CONTRACTS[public]['parameters']==old[oldname]['parameters']


def reference_values():
    b=dict(check.BASE)
    for old,sort in check.REFERENCE_SORTS.items():
        b[old]=FunctionValue(tuple(sort['parameters']),sort['result'],forbidden)
    return b


def test_reference_positions_types_and_every_lookup_slot():
    b=reference_values();h=check.context_handlers(b);cases=[]
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
    assert boundaries['sentences']['sixthopeningsentence']['position']==[70,1]
    assert boundaries['designations']=={'eispj':['eispm',1],'eispk':['eispm',2]}


def test_native_reference_lookup_never_executes_roles_or_candidates():
    b=reference_values()
    for old in (*check.SPANS,*check.DESIGNATIONS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='vacuumcapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('vacuumcapture',call(check.names()[old])))]
        handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
        # Function values can be wrapped by the evaluator; the capture checks the
        # declared type without executing the candidate or its quoted role.
        handlers['vacuumcapture']=lambda x,sort=sort,old=old: x==b[old] if sort=='individual' else isinstance(x,FunctionValue) and x.parameters==tuple(sort['parameters']) and x.result==sort['result']
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def substitute(node,variable,term):
    if isinstance(node,list):return [substitute(x,variable,term) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==variable:return deepcopy(term)
    return {k:substitute(x,variable,term) for k,x in node.items()}


def bind_one_at_a_time(body,active):
    binders=[];inner=deepcopy(body)
    while inner.get('kind')=='exists':
        binders.append((inner['variable'],inner['sort']));inner=inner['body']
    declarations=[]
    for i,(variable,sort) in enumerate(binders):
        name='vacuumwitness'+chr(97+i)
        declarations.append(dict(kind='primitive',name=name,parameters=[],result=sort))
        if i!=active:inner=substitute(inner,variable,call(name))
    variable,sort=binders[active];first='vacuumwitness'+chr(97+active);second=first+'other'
    declarations.append(dict(kind='primitive',name=second,parameters=[],result=sort))
    return dict(kind='or',arguments=[substitute(inner,variable,call(n)) for n in (first,second)]),declarations,binders


def test_each_of_six_physical_witness_binders_with_other_witnesses_instantiated():
    # Start from the full typed body and abstract only the physical predicate
    # after checking its identity against the actual Native document.
    fixture,slots=models()['fixture']('ejsy','unbounded')
    source.abstract(fixture,{'ejsx'})
    target=next(d for d in fixture['declarations'] if d['name']=='ejsy')
    s=models()['setup']();values=['charge','electricunit','magneticunit','force',s['c'](2),s['c'](Q(1,2))]
    norm=lambda xs:tuple(s['r'](x) if isinstance(x,FunctionValue) else x for x in xs)
    for active in range(6):
        doc=deepcopy(fixture);d=next(d for d in doc['declarations'] if d['name']=='ejsy')
        d['body'],extra,binders=bind_one_at_a_time(target['body'],active)
        assert len(binders)==6 and [sort for _,sort in binders]==['individual']*4+[profile.CUT]*2
        doc['declarations'][:0]=extra
        alternate='other' if active<4 else s['c'](7)
        handlers={n:lambda x=x:x for n,x in source.CONSTANTS.items()}
        handlers.update({'vacuumwitness'+chr(97+i):lambda x=x:x for i,x in enumerate(values)})
        handlers['vacuumwitness'+chr(97+active)+'other']=lambda:alternate
        for chosen in (values[active],alternate):
            expected=values[:];expected[active]=chosen;row=norm([*expected,'context'])
            for context,want in (('context',True),('other',False)):
                model=handlers|{slots[0][0]:lambda:context,'ejsx':lambda *xs: norm(xs)==row}
                assert native_evaluate(doc,individuals=('other','charge','electricunit','magneticunit','force'),situations=('context','other'),
                    primitives={x['name']:model.get(x['name'],forbidden) for x in doc['declarations'] if x['kind']=='primitive'})[0]['value']==want
        model=handlers|{slots[0][0]:lambda:'context','ejsx':lambda *xs:False}
        assert not native_evaluate(doc,individuals=('other','charge','electricunit','magneticunit','force'),situations=('context','other'),
            primitives={x['name']:model.get(x['name'],forbidden) for x in doc['declarations'] if x['kind']=='primitive'})[0]['value']
    with pytest.raises(ValueError,match='rational number domain|Finite function domain'):
        models()['run']('ejsy',['context'],{},'unbounded',('a','b'))


def test_region_and_field_roles_keep_typed_binders_and_acyclic_dependencies():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    expected={d['name']:d for d in check.role_definitions()}
    for old,name in check.reference_roles().items():
        assert ds[name]==expected[name]
        refs=_references(ds[name]['body'])
        assert name not in refs and not refs&{mapping()[n] for n in ('s5y','ejsz','ejs4','ejs5')}
        if old=='znk':
            assert refs=={mapping()[n] for n in ('ejsm','ra','ta','rb')}
        else:
            body=ds[name]['body'];sorts=[]
            while body.get('kind')=='exists':sorts.append(body['sort']);body=body['body']
            assert sorts==['individual']*4+[profile.CUT]*2+[check.REFERENCE_SORTS[old]]
            assert body['symbol']==mapping()['ejsn']
            assert body['arguments'][11 if old=='znl' else 12]==dict(kind='variable',name='va')
            assert not refs&{mapping()['znl'],mapping()['znm']}


def role_fixture(old,active=None):
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    symbol=check.reference_roles()[old];body=deepcopy(ds[symbol])
    assert body==next(d for d in check.role_definitions() if d['name']==symbol)
    decls=[]
    for name in sorted(_references(body['body'])):
        d=ds[name];params=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=name,parameters=params,result=d['result']))
    if active is not None:
        body['body'],extra,binders=bind_one_at_a_time(body['body'],active)
        assert len(binders)==7;decls+=extra
    decls += [dict(kind='primitive',name='vacuumcandidate',parameters=[],result=check.REFERENCE_SORTS[old]),
              dict(kind='primitive',name='vacuumcontext',parameters=[],result='situation'),body]
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls,
        statements=[dict(kind='ask',body=call(symbol,call('vacuumcandidate'),call('vacuumcontext')))]))


def eval_role(doc,model):
    handlers={mapping().get(n,n):fn for n,fn in model.items()}
    return evaluate_document(doc,individuals=source.DOMAIN,situations=('context','other'),
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def test_region_role_binds_every_context_and_region_slot():
    s=models()['setup']();region=s['fields'][4];row=s['norm'](('frame','length','duration','context',region))
    model={'ra':lambda:'frame','ta':lambda:'length','rb':lambda:'duration',
        'vacuumcandidate':lambda:region,'vacuumcontext':lambda:'context','ejsm':s['relation']({row})}
    assert perturb(lambda m:eval_role(role_fixture('znk'),m),model,{'ejsm':{row}},s['norm'])


@pytest.mark.parametrize('old',['znl','znm'])
def test_each_field_role_witness_binder_without_cartesian_enumeration(old):
    s=models()['setup']();fs=s['fields'];candidate=fs[-2 if old=='znl' else -1]
    other=fs[-1 if old=='znl' else -2];values=[*fs[5:11],other]
    for active in range(7):
        doc=role_fixture(old,active)
        alternate='other' if active<4 else s['c'](7) if active<6 else candidate
        model={'ra':lambda:'frame','ta':lambda:'length','rb':lambda:'duration','znk':lambda:fs[4],
            'vacuumcandidate':lambda:candidate,'vacuumcontext':lambda:'context'}
        model.update({'vacuumwitness'+chr(97+i):lambda x=x:x for i,x in enumerate(values)})
        model['vacuumwitness'+chr(97+active)+'other']=lambda:alternate
        for chosen in (values[active],alternate):
            witnesses=values[:];witnesses[active]=chosen
            fields=[candidate,witnesses[-1]] if old=='znl' else [witnesses[-1],candidate]
            row=s['norm'](['frame','length','duration','context',fs[4],*witnesses[:6],*fields])
            good=model|{'ejsn':s['relation']({row})}
            assert eval_role(doc,good)
            assert not eval_role(doc,good|{'vacuumcontext':lambda:'other'})
            if active==0 and chosen==values[0]:
                assert perturb(lambda m:eval_role(doc,m),good,{'ejsn':{row}},s['norm'])
        assert not eval_role(doc,model|{'ejsn':lambda *xs:False})
