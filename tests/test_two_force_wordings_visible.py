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
from scripts import check_einstein_two_force_wordings_visible as check
from scripts import two_force_wordings_visible_profile as profile
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


def test_source_parent_items_and_quoted_form_are_preserved():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==216 and doc['statements'][:213]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==891 and len(check.NEW_DEFINITIONS)==38
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    assert len(check.LOCAL_NAMES)==39 and check.REUSED_DEFINITIONS==['sexb'] and not check.ROLE_ASSIGNMENTS
    assert all(check.names()[n]==check.previous.names()[n] for n in ('zpq','zpr','eisqn','zol','zpo'))
    b=check.bridge();assert b['source_statement_indices']==[36,37]
    assert set(b['source_units'])=={'einstein-1905:u0174','einstein-1905:u0175'}
    assert (b['new_public_relations'],b['new_reference_primitives'],b['new_core_words'])==(4,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(2,177,39)
    assert check.FORMS=={'eisqs':'„elektromotorische Kraft“'}
    assert check.annotations()['entries']['eisqs']['forms'][0]['text']==check.FORMS['eisqs']
    bounds=check.text_boundaries()['items']
    assert bounds['zpq']['parenthetical_range']==[53,54] and bounds['zpr']['parenthetical_range']==[44,45]


def test_new_designation_on_inherited_item_dispatches_and_rejects_unknowns():
    b=dict(check.BASE);h=check.context_handlers(b)
    args=[b['eirf'],b['zpq'],Q(1),b['ri']]
    assert h['designationreference'](*args)==b['eisqs']
    for slot in range(4):
        bad=args[:];bad[slot]=Q(999) if slot==2 else 'unknown'
        with pytest.raises(ValueError):h['designationreference'](*bad)
    ancestor=check.previous;count=0
    while ancestor is not None:
        for old,anchor in getattr(ancestor,'DESIGNATIONS',{}).items():
            if isinstance(anchor,int):
                # The original synchrony connector stores the common node
                # in document()/context_handlers(), and only ordinals here.
                assert ancestor.__name__=='scripts.check_einstein_synchrony'
                node,index='eisiz',anchor
            else:
                node,index=anchor
            if node=='zpq':continue
            assert h['designationreference'](b['eirf'],b[node],Q(index),b['ri'])==b[old]
            with pytest.raises(ValueError):h['designationreference']('unknown',b[node],Q(index),b['ri'])
            with pytest.raises(ValueError):h['designationreference'](b['eirf'],b[node],Q(index),'unknown')
            count+=1
        ancestor=getattr(ancestor,'previous',None)
    assert count>0


def test_native_designation_and_inherited_items_do_not_execute_roles():
    b=dict(check.BASE);doc=deepcopy(check.restored()['document']);ds={d['name']:d for d in doc['declarations']}
    targets=('eisqs','zpq','zpr','eisi2','eisi3');needed=set();pending=[check.names()[n] for n in targets]
    while pending:
        n=pending.pop()
        if n in needed:continue
        needed.add(n);pending.extend(_references(ds[n].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate(targets):
        capture='wordingcapture'+chr(97+i)
        doc['declarations'].append(dict(kind='primitive',name=capture,parameters=['individual'],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(capture,call(check.names()[old]))))
        handlers[capture]=lambda x,old=old:x==b[old]
    results=evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
        situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)
    assert len(results)==5 and all(r['value'] is True for r in results)


@lru_cache(None)
def models():
    from scripts import check_comoving_wording as comoving
    from scripts import check_field_transform as transform
    from scripts import check_total_differential as differential
    from scripts import check_force_motion_binding as motion
    from scripts import check_resting_charge_force as resting
    numeric=clone(transform,('setup',))['setup']
    total=clone(differential,('setup',),dict(base_setup=numeric))['setup']
    vector=clone(motion,('vector',))['vector']
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    rest=clone(resting,('rest_setup',),dict(arithmetic=arithmetic))['rest_setup']
    moving=clone(motion,('fixture','run','motion_setup','motion_checks','field_setup'),dict(numeric_setup=total,vector=vector,rest_setup=rest))
    first=clone(source,('fixture','run','setup','numeric_checks','physical_checks','approximation_checks','presentation_checks'),dict(numeric_setup=total,vector=vector))
    second=clone(comoving,('fixture','run','setup','memo_field','boost_checks','field_checks','physical_checks','presentation_checks'),dict(numeric_setup=numeric,vector=vector))
    for ns in (first,second,moving):ns['fixture']=lru_cache(None)(ns['fixture'])
    return dict(first=first,second=second,motion=moving)


@pytest.mark.parametrize('group,name',[
    ('first','numeric_checks'),('first','physical_checks'),('first','approximation_checks'),('first','presentation_checks'),
    ('motion','motion_checks'),
    ('second','boost_checks'),('second','field_checks'),('second','physical_checks'),('second','presentation_checks')])
def test_decoded_force_approximation_chart_transform_and_presentation(group,name):
    assert models()[group][name]()


def replace_free(node,name,expression):
    if isinstance(node,list):return [replace_free(x,name,expression) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==name:return deepcopy(expression)
    if node.get('kind') in ('exists','forall','lambda') and node.get('variable')==name:return deepcopy(node)
    return {k:replace_free(x,name,expression) for k,x in node.items()}


def one_binder_run(ns,name,args,model,selected):
    # fixture() first checks the actual recovered definitions, then explicitly
    # retags function witnesses for binding diagnostics. Fix all but one binder
    # to supplied a-values; only the selected binder ranges over {a,b}.
    doc,slots=deepcopy(ns['fixture'](name,'witness'))
    target=next(d for d in doc['declarations'] if d['name']==name)
    fixed={};count=0
    def specialize(node):
        nonlocal count
        if isinstance(node,list):return [specialize(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='exists':
            index=count;count+=1;body=specialize(node['body'])
            if index==selected:return dict(node,body=body)
            n='wordingfixed'+chr(97+index);fixed[n]='a'
            doc['declarations'].insert(0,dict(kind='primitive',name=n,parameters=[],result='individual'))
            return replace_free(body,node['variable'],call(n))
        return {k:specialize(v) for k,v in node.items()}
    target['body']=specialize(target['body'])
    assert 0<=selected<count
    mm={n:lambda x=x:x for n,x in ns['CONSTANTS'].items()}|model
    mm.update({n:lambda x=x:x for n,x in fixed.items()})
    mm.update({n:lambda x=x:x for (n,sort),x in zip(slots,args,strict=True)})
    return native_evaluate(doc,individuals=('a','b'),situations=('case','other'),
        primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)[0]['value']


@pytest.mark.parametrize('group,name,slots',[('first','ejyc',4),('first','ejyg',5),('second','ejyv',6),('motion','ejxl',2)])
def test_each_witness_shares_all_dependent_slots_with_others_instantiated(group,name,slots):
    ns=models()[group]
    for selected in range(slots):
        ws=tuple('b' if i==selected else 'a' for i in range(slots))
        if name=='ejxl':
            args=['a']*9+['case'];target=(*args,*ws);callee='ejxk'
            m={'ejxk':lambda *xs:xs==target}
        elif name=='ejyc':
            target=('a',*ws,'case');args=['a','case'];callee='ejx7'
            m={'ejx7':lambda *xs:xs==target,'ejya':lambda u,response,ctx:(u,response,ctx)==('a',ws[0],'case')}
        elif name=='ejyg':
            target=(*ws,'case','a');args=['a','case'];callee='ejye'
            m={'ejyb':lambda u,ctx:(u,ctx)==(ws[0],'case'),'ejye':lambda *xs:xs==target}
        else:
            target=('a',*ws,'case');args=['a','case'];callee='ejyu'
            m={'ejys':lambda *xs:xs==('a',ws[0],ws[1],'case'),'ejyu':lambda *xs:xs==target}
        run=lambda mm:one_binder_run(ns,name,args,mm,selected)
        assert run(m)
        for i in range(len(target)):
            bad=target[:i]+('unavailable',)+target[i+1:]
            assert not run(m|{callee:lambda *xs,bad=bad:xs==bad})
        for relation_name in m:
            assert not run(m|{relation_name:lambda *xs:False})
        unknowns(run,m,m.keys())


@pytest.mark.parametrize('group,name,result_relation',[('first','ejyd','ejyc'),('second','ejyw','ejyv')])
def test_all_velocity_candidates_are_conditional_on_the_same_motion(group,name,result_relation):
    from itertools import product
    ns=models()[group]
    for selected,result in product(product((False,True),repeat=2),repeat=2):
        m={'ejyb':lambda u,ctx:selected[('a','b').index(u)] and ctx=='case',
           result_relation:lambda u,ctx:result[('a','b').index(u)] and ctx=='case'}
        assert ns['run'](name,[],m,'witness',('a','b'))==all(not a or b for a,b in zip(selected,result))


def test_unsampled_full_domains_are_rejected():
    first=models()['first'];s=first['setup']('ejx6')
    with pytest.raises(ValueError,match='rational number domain|Finite function domain'):
        first['run']('ejx6',s['approx'],s['m'],'full')
    second=models()['second'];s=second['setup']('ejyv')
    with pytest.raises(ValueError,match='rational number domain|Finite function domain'):
        second['run']('ejyv',[s['uv'],'case'],s['m'])


def test_motion_premise_and_quoted_vector_role_keep_physical_bindings():
    first=models()['first'];s=first['setup']('ejyb')
    m=s['m']|{'ejxm':lambda u,ctx:s['readvec'](u)==(1,-2,2) and ctx=='case'}
    assert first['run']('ejyb',[s['u'],'case'],m)
    assert not first['run']('ejyb',[s['u'],'case'],m|{'ejxm':lambda *xs:False})
    s=first['setup']('ejye')
    assert first['run']('ejye',s['args']+[s['extra']],s['m'])
    assert not first['run']('ejye',s['args']+[s['base']],s['m'])
    moving=models()['motion'];s=moving['field_setup']('ejxm')
    velocity=moving['vector'](s['c'],(1,-2,3))
    def local(*xs):
        return xs[:7]==('carrier','frame','event','chargerecord','chargeunit','length','duration') and s['point'](xs[7])==s['old'] and s['point'](xs[8])==(1,-2,3,0) and xs[9]=='case'
    m=s['m']|{'ejxl':local,'ejsy':lambda ctx:ctx=='case'}
    assert moving['run']('ejxm',[velocity,'case'],m)
    for name in ('ejxl','ejsy'):
        assert not moving['run']('ejxm',[velocity,'case'],m|{name:lambda *xs:False})
    assert not moving['run']('ejxm',[velocity,'case'],m|{'znk':lambda:FunctionValue(tuple([moving['RS']]*4),'truth',lambda *xs:False)})
    unknowns(lambda mm:moving['run']('ejxm',[velocity,'case'],mm),m,('ejxl','ejsy','znk'))


