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
from scripts import check_einstein_moving_field_visible as check
from scripts import moving_field_visible_profile as profile
from scripts import check_moving_field_definition as source
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


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (moving-field fixture)')


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
    assert boundaries['sentences']['movingfielddefinitionsentence']['position']==[72,1]
    assert boundaries['designations']=={'eispv':['eispy',1],'eispw':['eispy',2]}


def test_native_reference_lookup_never_executes_roles_or_candidates():
    b=reference_values()
    for old in (*check.SENTENCES,*check.SPANS,*check.DESIGNATIONS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='movingcapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('movingcapture',call(check.names()[old])))]
        handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
        # Function values can be wrapped by the evaluator; the capture checks the
        # declared type without executing the candidate or its quoted role.
        handlers['movingcapture']=lambda x,sort=sort,old=old: x==b[old] if sort=='individual' else isinstance(x,FunctionValue) and x.parameters==tuple(sort['parameters']) and x.result==sort['result']
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
        name='movingwitness'+chr(97+i)
        declarations.append(dict(kind='primitive',name=name,parameters=[],result=sort))
        if i!=active:inner=substitute(inner,variable,call(name))
    variable,sort=binders[active];first='movingwitness'+chr(97+active);second=first+'other'
    declarations.append(dict(kind='primitive',name=second,parameters=[],result=sort))
    return dict(kind='or',arguments=[substitute(inner,variable,call(n)) for n in (first,second)]),declarations,binders


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
        assert len(binders)==5;decls+=extra
    decls += [dict(kind='primitive',name='movingcandidate',parameters=[],result=check.REFERENCE_SORTS[old]),
              dict(kind='primitive',name='movingcontext',parameters=[],result='situation'),body]
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls,
        statements=[dict(kind='ask',body=call(symbol,call('movingcandidate'),call('movingcontext')))]))


def eval_role(doc,model):
    handlers={mapping().get(n,n):fn for n,fn in model.items()}
    return evaluate_document(doc,individuals=source.DOMAIN,situations=('context','other'),
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


@lru_cache(None)
def models():
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    setup=clone(field,('setup',),dict(arithmetic=arithmetic))['setup']
    ns=clone(source,('fixture','run','setup','response_checks','content_checks','principle_checks','presentation_checks'),dict(base_setup=setup))
    ns['fixture']=lru_cache(None)(ns['fixture'])
    return ns


@pytest.mark.parametrize('name',['response_checks','content_checks','principle_checks','presentation_checks'])
def test_decoded_signed_response_full_principle_conditional_and_quoted_presentation(name):
    assert models()[name]()


def test_source_parent_and_preserved_public_contracts():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==199 and doc['statements'][:196]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert len(ds)==2997
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==878 and len(check.NEW_DEFINITIONS)==17
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    b=check.bridge();assert b['source_statement_indices']==[23]
    assert set(b['source_units'])=={f'einstein-1905:u{i:04d}' for i in (161,162)}
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(3,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(1,161,38)
    assert check.FORMS=={'eispv':'(X′,Y′,Z′)','eispw':'(L′,M′,N′)'}
    for oldname,public in profile.SOURCE_RELATIONS.items():
        assert ds[mapping()[oldname]]==renamed(old[oldname],mapping())
        assert profile.CONTRACTS[public]['parameters']==old[oldname]['parameters']


def test_decoded_physical_calibration_every_slot_and_common_force_unit():
    s=models()['setup']();m=s['m'];norm=s['norm'];rel=s['rel'];reg=s['fields'][4];run=models()['run']
    args=['electric','moving','length','duration','charge','force',reg,'context',s['er'],'electricunit',s['c'](2),s['electric']]
    rows={'ejsl':{('moving','length','duration','context')},'eispt':{norm(args[:9])},
          'eispu':{norm(('electric','charge','electricunit','force',s['c'](2),'context'))},
          'eirn':{norm(('moving',s['electric'],'electricunit','context'))},
          'ejtr':{norm((s['electric'],s['er'],s['c'](2),reg))}}
    assert perturb(lambda mm:run('ejts',args,mm),m|{n:rel(rs) for n,rs in rows.items()},rows,norm)
    pair=['charge','poleunit','electricunit','magneticunit','force',s['c'](2),s['c'](3),s['er'],s['mr'],'context']
    magnetic=['pole','moving','length','duration','poleunit','force',reg,'context',s['mr'],'magneticunit',s['c'](3),s['magnetic']]
    rows2={'ejts':{norm(args),norm(magnetic)},'znn':{norm(('moving',s['electric'],s['magnetic'],reg,'context'))},
           'eispn':{norm(('process','moving',s['electric'],s['magnetic'],reg,'context'))}}
    mm=s['m']|{n:rel(rs) for n,rs in rows2.items()}
    assert perturb(lambda model:run('ejtt',pair,model),mm,rows2,norm)
    assert not run('ejtt',pair,mm|{'eisps':lambda:'electric'})


def test_each_of_nine_typed_witness_binders_with_others_instantiated():
    fixture,slots=models()['fixture']('ejtu')
    source.abstract(fixture,{'ejtt'})
    target=next(d for d in fixture['declarations'] if d['name']=='ejtu')
    s=models()['setup']();norm=s['norm']
    values=['charge','poleunit','electricunit','magneticunit','force',s['c'](2),s['c'](3),s['er'],s['mr']]
    for active in range(9):
        doc=deepcopy(fixture);d=next(d for d in doc['declarations'] if d['name']=='ejtu')
        d['body'],extra,binders=bind_one_at_a_time(target['body'],active)
        assert [sort for _,sort in binders]==['individual']*5+[profile.CUT]*2+[source.RESP]*2
        doc['declarations'][:0]=extra
        alternate='other' if active<5 else s['c'](7) if active<7 else s['mr'] if active==7 else s['er']
        handlers={n:lambda x=x:x for n,x in source.CONSTANTS.items()}
        handlers.update({'movingwitness'+chr(97+i):lambda x=x:x for i,x in enumerate(values)})
        handlers['movingwitness'+chr(97+active)+'other']=lambda:alternate
        for chosen in (values[active],alternate):
            expected=values[:];expected[active]=chosen;row=norm([*expected,'context'])
            for context,want in (('context',True),('other',False)):
                model=handlers|{slots[0][0]:lambda:context,'ejtt':lambda *xs:norm(xs)==row}
                assert native_evaluate(doc,individuals=source.DOMAIN,situations=source.SITUATIONS,
                    primitives={x['name']:model.get(x['name'],forbidden) for x in doc['declarations'] if x['kind']=='primitive'})[0]['value']==want
        model=handlers|{slots[0][0]:lambda:'context','ejtt':lambda *xs:False}
        assert not native_evaluate(doc,individuals=source.DOMAIN,situations=source.SITUATIONS,
            primitives={x['name']:model.get(x['name'],forbidden) for x in doc['declarations'] if x['kind']=='primitive'})[0]['value']
    # Keep native higher-order quantifiers, with a small individual domain.
    with pytest.raises(ValueError,match='rational number domain|Finite function domain'):
        models()['run']('ejtu',['context'],{},domain=('a','b'))


def test_role_dependencies_preserve_types_and_avoid_circular_or_result_filters():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    expected={d['name']:d for d in check.role_definitions()}
    for old,name in check.reference_roles().items():
        assert ds[name]==expected[name]
        seen=set();active=set()
        def visit(n):
            assert n not in active,('Cyclic role dependency',old,n)
            if n in seen:return
            seen.add(n);active.add(n)
            for ref in _references(ds[n].get('body')):visit(ref)
            active.remove(n)
        visit(name)
        assert not seen&{mapping()[n] for n in ('ejt4','ejt5','ejt6','ejt7','ejua','ejtw','s6k','s6l')}
        assert check.names()[old] not in seen
        if old in ('znr','zns'):
            assert not seen&{check.names()[n] for n in ('znr','zns')}
            body=ds[name]['body'];sorts=[]
            while body.get('kind')=='exists':sorts.append(body['sort']);body=body['body']
            assert sorts==['individual']*3+[profile.CUT,source.RESP]
            assert body['symbol']==mapping()['ejts'] and body['arguments'][11]==dict(kind='variable',name='va')


def test_region_history_and_theory_reference_roles_bind_every_slot():
    s=models()['setup']();region=s['fields'][4]
    rows={'ejsm':{s['norm'](('moving','length','duration','context',region))}}
    base={'zbm':lambda:'moving','ta':lambda:'length','rb':lambda:'duration','movingcandidate':lambda:region,'movingcontext':lambda:'context'}
    assert perturb(lambda m:eval_role(role_fixture('znt'),m),base|{'ejsm':s['rel'](rows['ejsm'])},rows,s['norm'])
    for old,frame in (('znw','frame'),('znx','moving')):
        rows={'vh':{('history',frame,'left','context')}}
        base={'znv':lambda:'history','ra':lambda:'frame','zbm':lambda:'moving',
              'movingcandidate':lambda:'left','movingcontext':lambda:'context','vh':relation(rows['vh'])}
        assert perturb(lambda m:eval_role(role_fixture(old),m),base,rows)
    for old,relation_name in (('znu','eisle'),('znv','eislf')):
        doc=role_fixture(old)
        for candidate in ('a','b'):
            for context in ('context','other'):
                base={'movingcandidate':lambda:candidate,'movingcontext':lambda:context,relation_name:relation({('a','b','context')})}
                assert eval_role(doc,base)==(candidate=='b' and context=='context')
        assert not eval_role(doc,base|{relation_name:lambda *xs:False})
        with pytest.raises(ValueError):eval_role(doc,base|{relation_name:forbidden})


@pytest.mark.parametrize('old',['znr','zns'])
def test_each_field_role_witness_binder_without_cartesian_enumeration(old):
    s=models()['setup']();electric=old=='znr';candidate=s['electric' if electric else 'magnetic'];response=s['er' if electric else 'mr']
    values=['charge' if electric else 'poleunit','force','electricunit' if electric else 'magneticunit',s['c'](2 if electric else 3),response]
    for active in range(5):
        doc=role_fixture(old,active)
        alternate='other' if active<3 else s['c'](7) if active==3 else s['mr' if electric else 'er']
        model={'zbm':lambda:'moving','ta':lambda:'length','rb':lambda:'duration','znt':lambda:s['fields'][4],
               'zor':lambda:'electric','eisps':lambda:'pole','movingcandidate':lambda:candidate,'movingcontext':lambda:'context'}
        model.update({'movingwitness'+chr(97+i):lambda x=x:x for i,x in enumerate(values)})
        model['movingwitness'+chr(97+active)+'other']=lambda:alternate
        for chosen in (values[active],alternate):
            witnesses=values[:];witnesses[active]=chosen
            row=s['norm'](['electric' if electric else 'pole','moving','length','duration',witnesses[0],witnesses[1],s['fields'][4],
                          'context',witnesses[4],witnesses[2],witnesses[3],candidate])
            good=model|{'ejts':s['rel']({row})}
            assert eval_role(doc,good)
            assert not eval_role(doc,good|{'movingcontext':lambda:'other'})
            if active==0 and chosen==values[0]:assert perturb(lambda m:eval_role(doc,m),good,{'ejts':{row}},s['norm'])
        assert not eval_role(doc,model|{'ejts':lambda *xs:False})


def test_source_prime_designations_six_equations_and_no_calculated_mixture():
    assert json.loads(json.dumps(source.source_record(),ensure_ascii=False))==check.author.read(source.SOURCE)
    assert not set(check.mapping())&{'s6k','s6l','sac2','sad2','sae2','saf2','saw'}
