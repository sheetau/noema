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
from scripts import check_einstein_force_interpretation_visible as check
from scripts import force_interpretation_visible_profile as profile
from scripts import check_force_interpretation as source
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


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (force-interpretation fixture)')


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


def test_source_parent_and_six_sentence_connection_are_preserved():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==213 and doc['statements'][:207]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.vocabulary()._words)==887 and len(check.NEW_DEFINITIONS)==42
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    assert len(check.LOCAL_NAMES)==116 and len(set(check.names().values()))==len(check.names())
    b=check.bridge();assert b['source_statement_indices']==[194,32,33,34,35,195]
    assert set(b['source_units'])=={'einstein-1905:u0173'}
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(7,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(6,175,38)
    assert check.FORMS=={} and check.DESIGNATIONS=={}


def reference_values():
    # Lookup must never execute these candidates or their identifying roles.
    return dict(check.BASE)|{n:FunctionValue(('individual',),profile.CUT,forbidden)
        for n,s in check.REFERENCE_SORTS.items() if isinstance(s,dict)}


def test_every_reference_lookup_slot_and_full_source_phrases():
    b=reference_values();h=check.context_handlers(b);cases=[]
    for old,(paragraph,sentence) in check.SENTENCES.items():
        cases.append(('sentencereference',[b['ri'],Q(paragraph),Q(sentence)],b[old]))
    for old,(node,start,end) in check.SPANS.items():
        cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    for old in check.ROLE_ASSIGNMENTS:
        role_sort=dict(kind='function',parameters=[check.REFERENCE_SORTS[old],'situation'],result='truth')
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(role_sort))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']];kind=check.reference_kind(old)
        cases.append((kind,args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h[kind](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    bounds=check.text_boundaries();assert len(bounds['sentences'])==6
    assert check.SPANS[check.REFERENCE_ANCHORS['zpo']]==('zpi',8,12)
    assert check.SPANS[check.REFERENCE_ANCHORS['zpm']]==('zpi',15,24)
    assert bounds['sentences']['zoy']['tokens'][17:19]==['d.','h.']
    assert all(check.names()[n]==check.previous.names()[n] for n in ('eisk3','eispj','eispv','ra'))


def test_native_reference_lookup_does_not_execute_candidates_or_roles():
    b=reference_values();doc=deepcopy(check.restored()['document'])
    ds={d['name']:d for d in doc['declarations']};doc['statements']=[]
    # Exact dependency extraction avoids repeatedly typing unrelated manuscript
    # definitions. All retained bodies are copied unchanged from decoded Native.
    needed=set();pending=[check.names()[n] for n in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS)]
    while pending:
        name=pending.pop()
        if name in needed:continue
        needed.add(name);pending.extend(_references(ds[name].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate((*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS)):
        sort=ds[check.names()[old]]['result'];name='forcecapture'+chr(97+i//26)+chr(97+i%26)
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[sort],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(name,call(check.names()[old]))))
        handlers[name]=lambda x,sort=sort,old=old: x==b[old] if sort=='individual' else isinstance(x,FunctionValue) and x.parameters==('individual',) and x.result==profile.CUT
    results=evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
        situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)
    assert len(results)==len(doc['statements']) and all(r['value'] is True for r in results)


def test_all_roles_preserve_native_bodies_and_acyclic_reference_dependencies():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    seen=set();active=set()
    def visit(n):
        assert n not in active
        if n in seen:return
        seen.add(n);active.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
        active.remove(n)
    for old,role in zip(check.ROLE_ASSIGNMENTS,check.role_definitions(),strict=True):
        assert ds[role['name']]==role
        assert role['name'] in _references(ds[check.names()[old]]['body'])
        visit(role['name'])
    assert len(check.role_definitions())==28
    assert not seen&{mapping()[n] for n in (*check.NEW_DEFINITIONS,'x4','eibs','ejts')}


@lru_cache(None)
def models():
    from scripts import check_point_charge_calibration as calibration
    from scripts import check_moving_unit_charge as moving
    from scripts import check_resting_charge_force as resting
    from scripts import check_electric_action as electric
    from scripts import check_field_comparison_claim as comparison
    arithmetic=clone(material,('arithmetic',))['arithmetic']
    cal=clone(calibration,('fixture','run','setup','unit_checks','geometry_checks','calibration_checks','presentation_checks'),dict(arithmetic=arithmetic))
    mov=clone(moving,('fixture','run','setup','amount_checks','premise_checks','presentation_checks'),dict(calibration_setup=cal['setup']))
    electric_setup=clone(electric,('setup',),dict(arithmetic=arithmetic))['setup']
    rest=clone(resting,('fixture','run','force_setup','force_checks','rest_setup','rest_checks','conditional_checks','presentation_checks'),dict(electric_setup=electric_setup,arithmetic=arithmetic))
    base_setup=clone(field,('setup',),dict(arithmetic=arithmetic))['setup']
    final_setup=clone(comparison,('setup',),dict(base_setup=base_setup))['setup']
    interp=clone(source,('fixture','run','contents','electric_checks','premise_checks','wording_checks','presentation_checks'),dict(setup=final_setup))
    result=dict(calibration=cal,moving=mov,resting=rest,interpretation=interp)
    for ns in result.values():ns['fixture']=lru_cache(None)(ns['fixture'])
    return result


@pytest.mark.parametrize('group,name',[
    ('calibration','unit_checks'),('calibration','geometry_checks'),('calibration','calibration_checks'),('calibration','presentation_checks'),
    ('moving','amount_checks'),('moving','premise_checks'),('moving','presentation_checks'),
    ('resting','force_checks'),('resting','rest_checks'),('resting','conditional_checks'),('resting','presentation_checks'),
    ('interpretation','electric_checks'),('interpretation','premise_checks'),('interpretation','wording_checks'),('interpretation','presentation_checks')])
def test_decoded_units_direction_same_records_rest_conditions_and_wordings(group,name):
    assert models()[group][name]()






def replace_free(node,name,expression):
    if isinstance(node,list):return [replace_free(x,name,expression) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==name:return deepcopy(expression)
    if node.get('kind') in ('exists','forall','lambda') and node.get('variable')==name:return deepcopy(node)
    return {k:replace_free(x,name,expression) for k,x in node.items()}


@lru_cache(None)
def role_library(old):
    """Keep decoded roles and math; explicitly bound source references and cut validity."""
    original=check.restored()['document'];ds={d['name']:d for d in original['declarations']}
    boundary={mapping()[d['name']] for d in check.source_excerpt()['declarations']
        if d['kind']=='primitive' and not d['parameters']}|{mapping()['ba']}
    selected={};pending=[check.reference_roles()[old]]
    while pending:
        name=pending.pop()
        if name in selected:continue
        d=deepcopy(ds[name])
        if name in boundary and d['kind']=='definition':
            d=dict(kind='primitive',name=name,parameters=[p['sort'] for p in d['parameters']],result=d['result'])
        selected[name]=d;pending.extend(_references(d.get('body'))-selected.keys())
    return dict(original,declarations=[selected[d['name']] for d in original['declarations'] if d['name'] in selected],statements=[])


def role_case(old,bad_axis=None):
    cuts=Cuts();axes=('x','y','z','t')
    point=lambda offset:FunctionValue(('individual',),profile.CUT,lambda a:cuts.make(99 if a==bad_axis else offset+axes.index(a)))
    candidate=point(2) if isinstance(check.REFERENCE_SORTS[old],dict) else 'candidate'
    constants={d['name']:d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive' and not d['parameters']}
    constants.update(dict(zip(('yn','yo','yp','zc7'),axes)))
    def norm(xs):
        def one(x):
            if isinstance(x,FunctionValue):
                return cuts.read(x) if x.parameters==('number',) else tuple(cuts.read(x(a)) for a in axes)
            return x
        return tuple(one(x) for x in xs)
    doc=deepcopy(role_library(old));root=next(d for d in doc['declarations'] if d['name']==check.reference_roles()[old])
    witness_values={};witness_sorts=[]
    def sampled(node):
        if isinstance(node,list):return [sampled(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='exists':
            i=len(witness_sorts);sort=node['sort'];witness_sorts.append(sort)
            values=('witness-a','witness-b') if sort=='individual' else (cuts.make(2),cuts.make(3)) if sort==profile.CUT else (point(6),point(7))
            branches=[]
            # There are at most two witnesses per role. This explicit two-value
            # specialization is a binding diagnostic, never a full-domain proof.
            body=sampled(node['body'])
            for j,x in enumerate(values):
                name='forcewitness'+chr(97+i)+chr(97+j);witness_values[name]=x
                doc['declarations'].insert(0,dict(kind='primitive',name=name,parameters=[],result=sort))
                branches.append(replace_free(body,node['variable'],call(name)))
            return dict(kind='or',arguments=branches)
        return {k:sampled(x) for k,x in node.items()}
    root['body']=sampled(root['body'])
    w=['witness-b']*2
    if witness_sorts:
        w=[witness_values['forcewitness'+chr(97+i)+'b'] for i in range(len(witness_sorts))]+['witness-b']
    c=candidate;s='case'
    rows={
        'zol':{'eisqc':[(c,s)]},
        'zom':{'zoh':[(w[0],'zol',c,'ra',w[1],s)]},
        'zon':{'zoh':[(c,'zol','zom','ra',w[0],s)]},
        'zoo':{'zoh':[('zon','zol','zom','ra',c,s)]},
        'zos':{'eisqb':[(c,Q(1),Q(0),Q(0),Q(1,100),s)]},
        'zot':{'eisqb':[(c,Q(1),Q(1),Q(-2),Q(1,100000),s)]},
        'zou':{'zof':[(c,'zor',Q(1),s)]},
        'zop':{'zof':[('zos',c,Q(1),s)]},
        'zoq':{'zof':[('zot',c,Q(1),s)]},
        'zpo':{'eisqd':[('zol','ra',c,'ta','rb',w[0],s)]},
        'zpq':{'eislk':[(c,'eisqn',Q(1),'eirf',s)]},
        'zpr':{'eislk':[(c,'eisqn',Q(2),'eirf',s)]}}
    for n,target,kind,frame,event,unit in [
        ('zov','zon','zop','ra','zoo','zos'),('zow','zon','zoq','ra','zoo','zot'),
        ('zox','zol','zor','ra','zoo','zou'),('eisqf','zom','zor','ra','zoo','zou'),
        ('zpd','zol','zor','zbm','zoo','zou'),('zpp','zol','zor','ra','zpo','zou'),('eisqk','zol','zor','zbm','zpo','zou')]:
        rows[n]={'zog':[(c,target,kind,frame,event,unit,w[0],s)]}
    for n,frame in [('zpe','ra'),('zpf','zbm')]:
        rows[n]={'zpc':[(c,'zol','zpn',frame,'zpo','zot',w[0],s)],'eirl':[(c,'zol',frame,'zpo',s)]}
    for n,target,frame,event,length,duration in [
        ('eisqg','zol','ra','zoo','zos','zik'),('eisqh','zom','ra','zoo','zos','zik'),
        ('zpj','zol','ra','zpo','ta','rb'),('zpk','zol','zbm','zpo','ta','rb')]:
        rows[n]={'eisqd':[(target,frame,event,length,duration,c,s)]}
    for n,record,frame in [('zpl','zpe','ra'),('zpm','zpf','zbm')]:
        rows[n]={'zpc':[(record,'zol','zpn',frame,'zpo','zot',c,s)]}
    rows['eisqi']={'eisqe':[('zow','zon','zol','zom','ra','zoo','zot',c,s)]}
    table={n:{norm(row) for row in rs} for n,rs in rows[old].items()}
    model={mapping().get(n,n):lambda x=x:x for n,x in constants.items()}|{n:lambda x=x:x for n,x in witness_values.items()}
    model[mapping()['ba']]=lambda x:cuts.read(x)!=99
    model.update({mapping().get('aa','aa'):lambda a,b:a<b,mapping().get('ab','ab'):lambda a,b:a+b})
    doc['declarations']+= [dict(kind='primitive',name='rolecandidate',parameters=[],result=check.REFERENCE_SORTS[old]),dict(kind='primitive',name='rolecontext',parameters=[],result='situation')]
    model.update(rolecandidate=lambda:c,rolecontext=lambda:s)
    doc['statements']=[dict(kind='ask',body=call(check.reference_roles()[old],call('rolecandidate'),call('rolecontext')))]
    def run(changes=None):
        handlers=model|{mapping()[n]:lambda *xs,rs=rs:norm(xs) in rs for n,rs in table.items()}|{mapping().get(n,n):fn for n,fn in (changes or {}).items()}
        return evaluate_document(doc,individuals=tuple(set(constants.values())|{'candidate','witness-a','witness-b','other'}),situations=('case','other'),
            primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']
    return run,table,norm


@pytest.mark.parametrize('old',list(check.ROLE_ASSIGNMENTS))
def test_role_argument_binding_with_explicit_two_value_witness_specialization(old):
    run,table,norm=role_case(old);assert run()
    for name,rs in table.items():
        for row in rs:
            assert not run({name:lambda *xs:False})
            for slot in range(len(row)):
                wrong=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not run({name:lambda *xs,wrong=wrong:norm(xs)==wrong}),(old,name,slot)
        with pytest.raises(ValueError):run({name:forbidden})


@pytest.mark.parametrize('old',['eisqg','eisqh','zpj','zpk','zpl','zpm','eisqi'])
def test_coordinate_roles_need_four_values_and_force_roles_only_three(old):
    for axis in ('x','y','z','t'):
        run,_,_=role_case(old,axis)
        assert run()==(axis=='t' and old in ('zpl','zpm','eisqi'))


def test_rest_force_witness_slots_on_two_value_domain():
    from scripts import check_resting_charge_force as source_rest
    for name,callee,slots in [('ejwr','ejwq',(5,6)),('ejwu','ejwt',(6,16)),('ejwv','ejwt',(6,16)),('ejwy','ejts',(9,8))]:
        # checked_extract verifies the actual decoded definition before the
        # historical witness-only diagnostic retags function sorts.
        ns=clone(source_rest,('fixture',));doc,args=ns['fixture'](name,'witness')
        root=next(d for d in doc['declarations'] if d['name']==name)
        body=root['body'];body=body['body'] if body['kind']=='content' else body
        binders=[];cursor=body
        while cursor['kind']=='exists':binders.append(cursor['variable']);cursor=cursor['body']
        assert len(binders)==2
        base={d['name']:lambda:'a' for d in doc['declarations'] if d['kind']=='primitive' and not d['parameters'] and d['result']=='individual'}
        base|={'bb':lambda x:'a','ri':lambda:'case'}
        for n,sort in args:base[n]=(lambda:'case') if sort=='situation' else (lambda:'a')
        length=7 if name=='ejwr' else 12 if name=='ejwy' else 17
        ctx=4 if name=='ejwr' else 7 if name=='ejwy' else 15
        for binder,slot in zip(binders,slots,strict=True):
            specialized=deepcopy(doc);special=next(d for d in specialized['declarations'] if d['name']==name)
            def fix(node):
                if isinstance(node,list):return [fix(x) for x in node]
                if not isinstance(node,dict):return node
                if node.get('kind')=='exists' and node['variable']!=binder:
                    return fix(replace_free(node['body'],node['variable'],call('fixedwitness')))
                return {k:fix(x) for k,x in node.items()}
            special['body']=fix(special['body'])
            specialized['declarations'].insert(0,dict(kind='primitive',name='fixedwitness',parameters=[],result='individual'))
            for wanted in ('a','b'):
                target=['a']*length;target[ctx]='case';target[slot]=wanted
                def run(fn):
                    model=base|{'fixedwitness':lambda:'a',callee:fn}
                    return native_evaluate(specialized,individuals=('a','b'),situations=('case','other'),primitives={d['name']:model.get(d['name'],forbidden) for d in specialized['declarations'] if d['kind']=='primitive'})[0]['value']
                assert run(lambda *xs:xs==tuple(target))
                assert not run(lambda *xs:False)
                with pytest.raises(ValueError):run(forbidden)
