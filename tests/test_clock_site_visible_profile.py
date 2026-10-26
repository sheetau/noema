from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,Content,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_clock_site_visible as check
from scripts import clock_site_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
HISTORY_DOMAIN=('body','second','origin','otherorigin','guide','otherguide','point','hidden','frame','moving','lengthunit','timeunit','x','y','z','other')
POINTS=('context','initial','discourse','scope','scene','other')

def forbidden(*args):raise ValueError('Unknown clock-site-visible input')
def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
@lru_cache(None)
def mapping():return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

@lru_cache(None)
def fixture(family,name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    constants=globals()[family+'_constants']()
    selected=NUM|set(constants)|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    if family=='measurement':
        selected|={'eipw','eigy','eixb'}
        if name=='eixg':selected.add('eixf')
        if name=='eixh':selected.add('eixg')
    elif family=='projection':
        selected|={'eiv2','eipw','eit2'}
        if name=='eixb':selected.add('eixa')
    elif family=='spatial':
        selected|={'eit2','eiv2','eipw','eigy'}
        selected|={'eixl':{'eixj','eixk'},'eixm':{'eixl','eiv5'},'eixn':{'eixm','eixj','eixk'},'eixo':{'eixn','eixj','eixh'},'eixp':{'eixo'},'eixq':{'eixp'},'eixr':{'eixm','eixq'},'eixs':{'eixr'}}.get(name,set())
    elif family=='space':
        selected|={'eivf','eivg','eivl','eiwn','eixs','eipw','eigy','eivv','eixq'}
        if name=='eix3':selected.add('eixt')
    elif family=='clock':
        selected|={'eit2','qo'}
        if name in ('eiyf','eiyg'):selected.add('eiye')
        if name=='eiyh':selected.add('eiyg')
        if name=='eiyi':selected|={'eiuk','eiyh'}
        if name=='eiyk':selected|={'eiyf','eiyi','eiyj'}
        if name in ('eiyn','eiyo'):selected.add('eiyg')
        if name=='eiyp':selected.add('eiyk')
        if mode=='protocol':selected.discard('qo');selected.add('db')
        if mode=='native_history':selected.discard('eit2')
    else:raise ValueError('Unknown test family')
    selected.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in selected if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    target=ds[m[name]]
    if mode=='instance':
        added=[]
        def walk(node):
            if isinstance(node,list):return [walk(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('forall','exists') and node['sort']==RS:
                added.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
            return {k:walk(v) for k,v in node.items()}
        target['body']=walk(target['body']);target['parameters']+=added;assert len(added)==1
    slots=[]
    for i,p in enumerate(target['parameters']):
        slot='motionslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='motioncontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('motioncontext'))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(family,name,args,model,mode='boundary',domain=None):
    if domain is None:domain=globals()[family+'_DOMAIN']
    doc,slots=fixture(family,name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    m=globals()[family+'_constants']()|{'motioncontext':lambda:'discourse'}|model|{n:(lambda x=x:x) for n,x in zip(slots,args)}
    h=handlers(doc);h.update({mapping().get(n,n):f for n,f in m.items() if mapping().get(n,n) in h})
    return evaluate_document(doc,individuals=domain,situations=globals()[family+'_POINTS'],primitives=h,max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
class ConstructedCuts:
    """Only registered exact rational cuts are read; no probing unknown functions."""
    def __init__(self):self.table={}
    def make(self,value):
        value=Q(value);result=cut(value);self.table[result.implementation]=value;return result
    def read(self,value):
        while isinstance(value,FunctionValue):
            impl=value.implementation
            if impl in self.table:return self.table[impl]
            if isinstance(impl,FunctionValue):
                value=impl
                continue
            code=getattr(impl,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(impl,'__closure__',None) or ()))))
            value=free.get('raw')
        raise ValueError('Cut was not constructed by this finite fixture')
def arithmetic():
    cuts=ConstructedCuts();r=cuts.read;c=cuts.make
    return cuts,dict(ba=lambda x:isinstance(r(x),Q),bb=c,bc=lambda a,b:r(a)<=r(b),bd=lambda a,b:c(r(a)+r(b)),bf=lambda a,b:c(r(a)-r(b)),shv=lambda a,b:c(r(a)*r(b)),sca=lambda a,b:r(a)==r(b),zzba=lambda x:isinstance(r(x),Q),zzbc=lambda a,b:r(a)<=r(b))

def numbers():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b))}
    return cuts,m

def norm_factory(cuts,times):
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return cuts.read(x)
            if x.result==RS:return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            forbidden()
        return tuple(one(x) for x in xs)
    return norm


COORDINATES = (('eisne', 'x', 'eixv', 'ra', 'yn'), ('eisnf', 'y', 'eixw', 'ra', 'yo'), ('eisng', 'z', 'eixx', 'ra', 'yp'), ('eisnh', 'ξ', 'eixy', 'zbm', 'yn'), ('eisni', 'η', 'eixz', 'zbm', 'yo'), ('eisnj', 'ζ', 'eix2', 'zbm', 'yp'))

measurement_DOMAIN=('a', 'b')

measurement_POINTS=('context', 'initial')
def measurement_run(name,args,m,mode='boundary',domain=None):return run('measurement',name,args,m,mode,domain)

def measurement_constants():
    return {n: lambda x=x: x for n, x in {'ta': 'a', 'rb': 'b', 'yn': 'a', 'yo': 'b', 'yp': 'a', 'zb4': 'initial'}.items()}

def measurement_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown clock-site-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def measurement_perturb(check, m, rows, norm):
    count = 1
    assert check(m)
    for n, rs in rows.items():
        for row in rs:
            assert not check(m | {n: lambda *xs, rs=rs - {row}: norm(xs) in rs}), (n, row)
            count += 1
            for i in range(len(row)):
                wrong = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
                assert not check(m | {n: lambda *xs, rs=rs - {row} | {wrong}: norm(xs) in rs}), (n, i)
                count += 1
    measurement_unknowns(check, m, rows)
    return count

@lru_cache(None)
def measurement_magnitude_checks():
    cuts, m = numbers()
    c = cuts.make
    count = 0
    for length in (-3, -1, 0, 1, 3, Q(1, 2)):
        for signed in (-3, -1, 0, 1, 3, Q(-1, 2), Q(1, 2)):
            assert measurement_run('eixc', [c(Q(length)), c(Q(signed))], m) == (length >= 0 and length == abs(signed))
            count += 1
    assert not measurement_run('eixc', [c(Q(2)), c(Q(-2))], m | {'ba': lambda x: False})
    count += 1
    measurement_unknowns(lambda mm: measurement_run('eixc', [c(Q(2)), c(Q(-2))], mm), m, ('ba', 'bc', 'bb', 'shv', 'sca'))
    return dict(cases=count, zero_negative_signed_and_nonnegative_magnitude_distinguished=True)

def test_measurement_magnitude_checks():assert measurement_magnitude_checks()

def measurement_setup(length=Q(3)):
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    families = {a: FunctionValue(('individual',), FS, lambda p, a=a: FunctionValue((RS,), RS, lambda t: c(Q((1 if p == 'a' else 2) * (1 if a == 'a' else 4))))) for a in measurement_DOMAIN}

    def family(b, f, lu, tu, a, ctx):
        if (b, f, lu, tu, ctx) != ('b', 'a', 'a', 'b', 'context') or a not in measurement_DOMAIN:
            forbidden()
        return families[a]

    def norm(xs):

        def one(x):
            if not isinstance(x, FunctionValue):
                return value(x)
            if x.parameters == ('number',):
                return r(x)
            if x.result == 'truth':
                return tuple((p for p in measurement_DOMAIN if x(p)))
            if x.result == FS:
                return tuple((r(x(p)(c(Q(t)))) for p in measurement_DOMAIN for t in (0, 1, 2)))
            forbidden()
        return tuple((one(x) for x in xs))
    members = FunctionValue(('individual',), 'truth', lambda p: p == 'b')
    h = ['b', 'a', 'context', 'a', 'b', c(Q(0)), c(Q(2)), members, families['a'], families['b'], families['a']]
    rows = {'xc': {('b',)}, 'va': {('a',)}, 'ti': {('a',)}, 'ci': {('b',)}, 'eisej': {('b', 'b', 'context')}, 'eipw': {('b', 'a', 'context')}, 'eigy': {norm(h)}, 'eisef': {('b', 'b', 'a', 'a', 'b', Q(0), Q(2), 'context')}, 'xb': {('a',)}, 'eisnc': {('a', 'b', 'a', 'b', 'a', 'a', length, 'context')}, 'xh': {('a', 'b', 'a', 'b', 'a', 'a', length, 'context')}, 'th': {('a', 'b', 'a', 'a', length)}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m |= {'eisls': lambda *xs: c(Q(0)), 'eislt': lambda *xs: c(Q(2)), 'eislu': family, 'eirh': lambda b, p, ctx: (b, p, ctx) == ('b', 'b', 'context')}
    args = ['a', 'b', 'b', 'a', 'b', 'a', c(length), 'context']
    return (cuts, m, rows, norm, args)

@lru_cache(None)
def measurement_instrument_checks():
    cuts, m, rows, norm, _ = measurement_setup()
    args = ['b', 'b', 'a', 'context']
    selected = {n: rows[n] for n in ('xc', 'va', 'ti', 'ci', 'eisej', 'eipw', 'eigy', 'eisef')}
    check = lambda mm: measurement_run('eixd', args, mm)
    count = measurement_perturb(check, m, selected, norm)
    assert not check(m | {'eisej': lambda *xs: xs in rows['eisej'] | {('a', 'b', 'context')}})
    count += 1
    assert not check(m | {'eirh': lambda *xs: True})
    count += 1
    original = m['eislu']

    def wrong(*xs):
        fn = original(*xs)
        return FunctionValue(('individual',), FS, lambda p: FunctionValue((RS,), RS, lambda t: cuts.make(cuts.read(fn(p)(t)) + 1)))
    assert not check(m | {'eislu': wrong})
    count += 1
    measurement_unknowns(check, m, ('eislu', 'eirh', 'eisls', 'eislt'))
    return dict(cases=count, single_given_ruler_is_entire_tool_range=True, same_calibrated_method_interval_and_complete_rigid_history=True)

def test_measurement_instrument_checks():assert measurement_instrument_checks()

@lru_cache(None)
def measurement_procedure_checks():
    cuts, m, rows, norm, args = measurement_setup()
    check = lambda mm: measurement_run('eixe', args, mm)
    count = measurement_perturb(check, m, {n: rows[n] for n in ('xb', 'eisnc', 'xh', 'th')}, norm)
    for length in (Q(-3), Q(0), Q(3)):
        _, mm, _, _, aa = measurement_setup(length)
        assert measurement_run('eixe', aa, mm) == (length >= 0)
        count += 1
    changed = {('b', 'a', 'a', 'a', 'b', Q(0), Q(2), 'context')}
    assert not check(m | {'eisef': lambda *xs: norm(xs) in changed})
    count += 1
    return dict(cases=count, actual_procedure_reading_and_distance_all_required=True, calibration_of_different_method_rejected=True, zero_distance_included=True)

def test_measurement_procedure_checks():assert measurement_procedure_checks()

@lru_cache(None)
def measurement_projection_checks():
    count = 0
    for signed in (Q(-3), Q(0), Q(3)):
        cuts, m, rows, norm, _ = measurement_setup(abs(signed))
        c = cuts.make
        physical = ['b', 'a', 'b', 'a', 'b', 'a', 'b', 'context']
        geom = norm(physical + [c(signed)])
        m['eixb'] = lambda *xs: norm(xs) == geom
        args = physical + ['a', 'b', 'b', c(signed), c(abs(signed))]
        check = lambda mm: measurement_run('eixf', args, mm)
        count += measurement_perturb(check, m, {'eixb': {geom}}, norm)
        assert not measurement_run('eixf', args[:-1] + [c(abs(signed) + 1)], m)
        count += 1
        measurement_unknowns(check, m, ('eisnc', 'xh', 'th', 'eisef'))
    return dict(cases=count, same_origin_projection_axis_role_value_and_distance=True, negative_and_zero_coordinates_use_nonnegative_measurements=True)

def test_measurement_projection_checks():assert measurement_projection_checks()

@lru_cache(None)
def measurement_identity_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    norm = lambda xs: tuple((r(x) if isinstance(x, FunctionValue) else value(x) for x in xs))
    physical = ['b', 'a', 'b', 'a', 'b', 'a', 'b', 'context']
    args = physical + ['a', 'b', c(Q(-3)), c(Q(3))]
    expected = norm(physical + ['a', 'b', 'b', c(Q(-3)), c(Q(3))])
    rows = {'eixf': {expected}, 'zbx': {('a', 'b', 'context')}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m |= {'zby': lambda f, ctx: 'b', 'zbn': lambda f, ctx: 'a', 'zbo': lambda f, role, ctx: 'b', 'eismu': lambda axis, f, ctx: 'b'}
    check = lambda mm: measurement_run('eixg', args, mm)
    count = measurement_perturb(check, m, rows, norm)
    for n in ('zby', 'zbn', 'zbo'):
        old = m[n]

        def wrong(*xs, old=old):
            return ('b' if old(*xs) == 'a' else 'a') if xs[-1] == 'initial' else old(*xs)
        assert not check(m | {n: wrong})
        count += 1
    assert not check(m | {'eismu': lambda *xs: 'a'})
    count += 1
    measurement_unknowns(check, m, ('zby', 'zbn', 'zbo', 'eismu'))
    return dict(cases=count, initial_given_ruler_origin_and_role_axis_preserved=True, current_guide_and_distribution_bound=True)

def test_measurement_identity_checks():assert measurement_identity_checks()

@lru_cache(None)
def measurement_candidate_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    count = 0
    norm = lambda xs: tuple((r(x) if isinstance(x, FunctionValue) else value(x) for x in xs))
    m |= {'zbo': lambda f, role, ctx: 'b' if role == 'b' else 'a', 'zbn': lambda f, ctx: 'a', 'eismu': lambda axis, f, ctx: 'b'}
    args = ['a', 'a', 'b', c(Q(-3)), 'context', c(Q(3))]
    expected = ('b', 'a', 'b', 'a', 'b', 'a', 'b', 'context', 'a', 'b', Q(-3), Q(3))
    check = lambda mm: measurement_run('eixh', args, mm, 'instance')
    mm = m | {'eixg': lambda *xs: norm(xs) == expected}
    assert check(mm)
    count += 1
    assert not check(m | {'eixg': lambda *xs: False})
    count += 1
    for i in range(len(expected)):
        wrong = tuple(('wrong' if j == i else x for j, x in enumerate(expected)))
        assert not check(m | {'eixg': lambda *xs: norm(xs) == wrong})
        count += 1
    for i in (4, 8, 9):
        changed = tuple((('a' if x == 'b' else 'b') if j == i else x for j, x in enumerate(expected)))
        assert check(m | {'eixg': lambda *xs: norm(xs) == changed})
        count += 1
    try:
        measurement_run('eixh', args[:-1], mm)
    except ValueError as e:
        assert 'Finite function domain' in str(e) or 'rational number domain' in str(e), str(e)
    else:
        raise AssertionError('Real length witness silently enumerated')
    measurement_unknowns(check, mm, ('eixg', 'zbo', 'zbn', 'eismu'))
    return dict(cases=count, two_value_domain_distinguishes_all_existential_slots=True, alternative_projection_observer_method_allowed=True, native_real_witness_not_finitely_enumerated=True)

def test_measurement_candidate_checks():assert measurement_candidate_checks()

projection_DOMAIN=('axis', 'origin', 'guide', 'place', 'projection', 'frame', 'lengthunit', 'timeunit', 'x', 'y', 'z', 'recorda', 'recordb', 'other')

projection_POINTS=('context', 'other')
def projection_run(name,args,m,mode='boundary',domain=None):return run('projection',name,args,m,mode,domain)

def projection_constants():
    return {n: lambda x=x: x for n, x in {'ta': 'lengthunit', 'rb': 'timeunit', 'yn': 'x', 'yo': 'y', 'yp': 'z'}.items()}

def projection_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown clock-site-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

@lru_cache(None)
def projection_geometry_checks():
    cuts, m = numbers()
    c = cuts.make
    count = 0

    def check(name, args, expected):
        nonlocal count
        actual = projection_run(name, [c(Q(x)) for x in args], m)
        assert actual == expected, (name, args, actual)
        count += 1
    for axis in range(3):
        for signed in (-3, 0, 2):
            foot = [0, 0, 0]
            foot[axis] = signed
            point = foot.copy()
            point[(axis + 1) % 3] = 4
            for scale in (-5, 2):
                direction = [0, 0, 0]
                direction[axis] = scale
                for p in (point, foot):
                    check('eiw4', p + foot + direction, True)
                    expected = signed * (1 if scale > 0 else -1)
                    check('eiw6', p + foot + direction + [expected], True)
                    check('eiw6', p + foot + direction + [expected + 1], False)
                broken = foot.copy()
                broken[(axis + 1) % 3] = 1
                check('eiw4', point + broken + direction, False)
                broken = foot.copy()
                broken[axis] += 1
                check('eiw4', point + broken + direction, False)
    for scale in (Q(1, 2), 2, -3):
        d = [3 * scale, 4 * scale, 0]
        s = 5 if scale > 0 else -5
        check('eiw6', [7, 1, 2, 3, 4, 0] + d + [s], True)
        check('eiw6', [7, 1, 2, 3, 4, 0] + d + [50], False)
    for name, args in (('eiw4', [1, 2, 3, 0, 0, 0, 0, 0, 0]), ('eiw5', [0, 0, 0, 0, 0, 0, 0]), ('eiw6', [0] * 10)):
        check(name, args, False)
    args = [c(Q(x)) for x in [2, 1, 3, 2, 0, 0, 4, 0, 0, 2]]
    assert not projection_run('eiw6', args, m | {'ba': lambda x: False})
    count += 1
    projection_unknowns(lambda mm: projection_run('eiw6', args, mm), m, ('ba', 'bf', 'bd', 'shv', 'bg', 'sca'))
    return dict(cases=count, zero_and_negative_coordinates_and_each_axis=True, oblique_direction_scale_and_sign_distinguished=True, zero_direction_and_nonorthogonal_foot_rejected=True)

def test_projection_geometry_checks():assert projection_geometry_checks()

def projection_setup(positions=None, directions=None):
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    pos = {'origin': (10, 20, 30), 'guide': (8, 20, 30), 'place': (12, 21, 33), 'projection': (12, 20, 30)} | (positions or {})
    fs = {(p, a): FunctionValue((RS,), RS, lambda t, p=p, a=a: c(Q(pos[p][a]))) for p in pos for a in range(3)}

    def representative(p, f, lu, tu, a, ctx):
        if p not in pos or (f, lu, tu, ctx) != ('frame', 'lengthunit', 'timeunit', 'context') or a not in ('x', 'y', 'z'):
            forbidden()
        return fs[p, ('x', 'y', 'z').index(a)]

    def family(body, f, lu, tu, a, ctx):
        if body != 'axis' or (f, lu, tu, ctx) != ('frame', 'lengthunit', 'timeunit', 'context') or a not in ('x', 'y', 'z'):
            forbidden()
        return FunctionValue(('individual',), FS, lambda p: representative(p, f, lu, tu, a, ctx))

    def norm(xs):

        def one(x):
            if not isinstance(x, FunctionValue):
                return value(x)
            if x.parameters == ('number',):
                return r(x)
            if x.parameters == (RS,) and x.result == RS:
                return tuple((r(x(c(Q(t)))) for t in (0, 1, 2)))
            forbidden()
        return tuple((one(x) for x in xs))
    rows = {'va': {('frame',)}, 'ti': {('lengthunit',)}, 'ci': {('timeunit',)}, 'zbv': {('frame', 'origin', 'context')}, 'zbw': {('frame', 'axis', 'x', 'context')}, 'zcu': {(p, 'frame', 'context') for p in ('place', 'projection')}, 'eisdd': {('frame', 'lengthunit', 'timeunit', 'context')}, 'eiv2': {('axis', 'origin', 'guide', 'frame', 'context')}, 'eipw': {('axis', 'frame', 'context')}}
    rows['eit2'] = {norm([p, 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2)), *(fs[p, a] for a in range(3))]) for p in ('origin', 'place', 'projection')}
    rows['zsa'] = {(p, 'axis', 'frame', 'lengthunit', 'context') for p in ('recorda', 'recordb')}
    vectors = {'recorda': (4, 0, 0), 'recordb': (7, 0, 0)} | (directions or {})

    def component(rec, a):
        if rec not in projection_DOMAIN or a not in ('x', 'y', 'z'):
            forbidden()
        return c(Q(vectors.get(rec, (1, 0, 0))[('x', 'y', 'z').index(a)]))
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m |= {'eismh': representative, 'eislu': family, 'eisls': lambda *xs: c(Q(0)), 'eislt': lambda *xs: c(Q(2)), 'zsb': component}
    args = ['axis', 'origin', 'guide', 'place', 'projection', 'frame', 'x', 'context', c(Q(1)), c(Q(2))]
    return (cuts, m, rows, norm, args)

@lru_cache(None)
def projection_physical_checks():
    cuts, m, rows, norm, args = projection_setup()
    count = 1
    check = lambda mm: projection_run('eixa', args, mm)
    assert check(m)
    for n, rs in rows.items():
        if n == 'zsa':
            continue
        for row in rs:
            assert not check(m | {n: lambda *xs, rs=rs - {row}: norm(xs) in rs}), (n, row)
            count += 1
            for i in range(len(row)):
                changed = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
                assert not check(m | {n: lambda *xs, rs=rs - {row} | {changed}: norm(xs) in rs}), (n, i)
                count += 1
    for positions, expected in (({'projection': (12, 21, 30)}, False), ({'projection': (13, 20, 30)}, False), ({'guide': (10, 20, 30)}, False), ({'guide': (10, 18, 30)}, False), ({'guide': (17, 20, 30)}, True), ({'origin': (0, 0, 0), 'guide': (-2, 0, 0), 'place': (2, 1, 3), 'projection': (2, 0, 0)}, True)):
        _, mm, _, _, aa = projection_setup(positions)
        assert projection_run('eixa', aa, mm) == expected, (positions, expected)
        count += 1
    for a in ('eismh', 'eislu'):
        original = m[a]

        def changed(*xs, original=original, a=a):
            fn = original(*xs)
            if xs[4] != 'y':
                return fn
            if a == 'eismh':
                return FunctionValue((RS,), RS, lambda t: cuts.make(cuts.read(fn(t)) + 1))
            return FunctionValue(('individual',), FS, lambda p: FunctionValue((RS,), RS, lambda t: cuts.make(cuts.read(fn(p)(t)) + (1 if p == 'guide' else 0))))
        assert not check(m | {a: changed})
        count += 1
    projection_unknowns(check, m, tuple(rows) + ('eismh', 'eislu', 'eisls', 'eislt', 'zsb'))
    return dict(cases=count, native_coordinates_and_material_direction_connected=True, origin_and_both_places_share_complete_static_histories=True, every_physical_boundary_argument_checked=True)

def test_projection_physical_checks():assert projection_physical_checks()

@lru_cache(None)
def projection_orientation_checks():
    cuts, m, rows, norm, args = projection_setup()
    count = 0
    for directions, expected in (({'recordb': (-7, 0, 0)}, False), ({'recordb': (0, 0, 0)}, False), ({'recordb': (7, 1, 0)}, False), ({'recorda': (Q(1, 7), 0, 0)}, True)):
        _, mm, _, _, aa = projection_setup(directions=directions)
        assert projection_run('eixa', aa, mm) == expected
        count += 1
    renamed = {('other',) + row[1:] for row in rows['zsa']}
    assert projection_run('eixa', args, m | {'zsa': lambda *xs: tuple(xs) in renamed})
    count += 1
    for i in range(1, 5):
        changed = {tuple(('other' if j == i else x for j, x in enumerate(row))) for row in rows['zsa']}
        assert not projection_run('eixa', args, m | {'zsa': lambda *xs: tuple(xs) in changed})
        count += 1
    assert not projection_run('eixa', args, m | {'zsa': lambda *xs: False})
    count += 1
    assert not projection_run('eixa', args[:-1] + [cuts.make(Q(-2))], m)
    count += 1
    for positive in (-1, 1):
        localcuts, mm, _, _, aa = projection_setup({'place': (10, 21, 33), 'projection': (10, 20, 30)}, dict(recorda=(positive, 0, 0), recordb=(positive * 2, 0, 0)))
        aa[-1] = localcuts.make(Q(0))
        assert projection_run('eixa', aa, mm)
        count += 1
    return dict(cases=count, arbitrary_material_guide_not_assumed_positive=True, all_positive_direction_records_checked=True, zero_coordinate_valid_with_either_consistent_orientation=True)

def test_projection_orientation_checks():assert projection_orientation_checks()

@lru_cache(None)
def projection_interval_checks():
    cuts, m, _, norm, args = projection_setup()
    c = cuts.make
    count = 0
    base = args[:8] + args[-1:]
    row = norm(args)
    mm = m | {'eixa': lambda *xs: norm(xs) == row}
    assert projection_run('eixb', base + [c(Q(1))], mm, 'instance')
    count += 1
    for i in range(len(row)):
        altered = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
        assert not projection_run('eixb', base + [c(Q(1))], m | {'eixa': lambda *xs: norm(xs) == altered}, 'instance')
        count += 1
    for t in (-1, 0, 1, 2, 3):
        assert projection_run('eixb', base + [c(Q(t))], m | {'eixa': lambda *xs: False}, 'instance') == (t not in (0, 1, 2))
        count += 1
    try:
        projection_run('eixb', base, mm)
    except ValueError as e:
        assert 'rational number domain' in str(e) or 'Finite function domain' in str(e), str(e)
    else:
        raise AssertionError('Whole real interval silently sampled')
    projection_unknowns(lambda model: projection_run('eixb', base + [c(Q(1))], model, 'instance'), mm, ('eixa', 'eisls', 'eislt'))
    return dict(cases=count, same_points_role_and_value_bound_at_every_time=True, native_all_real_time_evaluation_rejected=True)

def test_projection_interval_checks():assert projection_interval_checks()

spatial_DOMAIN=('a', 'b', 'origin', 'guide', 'point', 'hidden', 'linea', 'lineb', 'linec', 'ruler', 'frame', 'moving', 'x', 'y', 'z')

spatial_POINTS=('reference', 'setting', 'initial')
def spatial_run(name,args,m,mode='boundary',domain=None):return run('spatial',name,args,m,mode,domain)

def spatial_constants():
    return {n: lambda x=x: x for n, x in {'ta': 'a', 'rb': 'b', 'yn': 'x', 'yo': 'y', 'yp': 'z', 'zb4': 'initial', 'ra': 'frame', 'zbm': 'moving'}.items()}

def spatial_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown clock-site-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def spatial_perturb(check, m, rows, norm=lambda xs: tuple((value(x) for x in xs))):
    count = 1
    assert check(m)
    for n, rs in rows.items():
        for row in rs:
            assert not check(m | {n: lambda *xs, rs=rs - {row}: norm(xs) in rs}), (n, row)
            count += 1
            for i in range(len(row)):
                wrong = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
                assert not check(m | {n: lambda *xs, rs=rs - {row} | {wrong}: norm(xs) in rs}), (n, i)
                count += 1
    spatial_unknowns(check, m, rows)
    return count

def spatial_numeric():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read

    def norm(xs):

        def one(x):
            if not isinstance(x, FunctionValue):
                return value(x)
            if x.parameters == ('number',):
                return r(x)
            if x.parameters == (RS,) and x.result == RS:
                return tuple((r(x(c(Q(t)))) for t in (0, 1, 2, 3, 5)))
            forbidden()
        return tuple((one(x) for x in xs))
    return (cuts, m, norm)

@lru_cache(None)
def spatial_point_checks():
    cuts, m, norm = spatial_numeric()
    c = cuts.make
    count = 0

    def setup(offset=(0, 0, 0)):
        fs = {(ctx, a): FunctionValue((RS,), RS, lambda t, ctx=ctx, i=i: c(Q(i + 1 + (offset[i] if ctx == 'setting' else 0)))) for ctx in ('reference', 'setting') for i, a in enumerate(('x', 'y', 'z'))}

        def raw(p, f, lu, tu, a, ctx):
            if (p, f, lu, tu) != ('point', 'frame', 'a', 'b') or (ctx, a) not in fs:
                forbidden()
            return fs[ctx, a]
        spans = {'reference': (0, 2), 'setting': (3, 5)}
        rows = {'eit2': {norm(['point', 'frame', ctx, 'a', 'b', *(c(Q(x)) for x in spans[ctx]), *(fs[ctx, a] for a in ('x', 'y', 'z'))]) for ctx in spans}, 'eisdd': {('frame', 'a', 'b', ctx) for ctx in spans}}
        mm = m | {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
        mm |= {'eismh': raw, 'eisls': lambda f, tu, ctx: c(Q(spans[ctx][0])), 'eislt': lambda f, tu, ctx: c(Q(spans[ctx][1]))}
        return (mm, rows)
    args = ['point', 'frame', 'reference', 'setting']
    mm, rows = setup()
    check = lambda model: spatial_run('eixj', args, model)
    count += spatial_perturb(check, mm, rows, norm)
    for i in range(3):
        offset = tuple((1 if a == i else 0 for a in range(3)))
        bad, _ = setup(offset)
        assert not check(bad)
        count += 1
    spatial_unknowns(check, mm, ('eismh', 'eisls', 'eislt', 'sca', 'ba'))
    return dict(cases=count, every_position_component_and_complete_static_history_bound=True, different_measurement_periods_allowed=True)

def test_spatial_point_checks():assert spatial_point_checks()

def spatial_direction_model(vectors=None):
    cuts, m, norm = spatial_numeric()
    c = cuts.make
    vec = {'a': (2, 0, 0), 'b': (7, 0, 0)} | (vectors or {})

    def component(rec, role):
        if rec not in ('a', 'b', 'x', 'y', 'z') or role not in ('x', 'y', 'z'):
            forbidden()
        return c(Q(vec.get(rec, (1, 0, 0))[('x', 'y', 'z').index(role)]))
    rows = {('a', 'a', 'a', 'a', 'reference'), ('b', 'a', 'a', 'a', 'setting')}
    m |= {'zsa': lambda *xs: xs in rows, 'zsb': component}
    return (cuts, m, norm, rows)

@lru_cache(None)
def spatial_orientation_checks():
    count = 0
    args = ['a', 'a', 'reference', 'setting']
    domain = ('a', 'b', 'x', 'y', 'z')
    for vec, expected in (({'b': (Q(1, 3), 0, 0)}, True), ({'b': (-7, 0, 0)}, False), ({'b': (0, 0, 0)}, False), ({'b': (7, 1, 0)}, False)):
        _, m, _, _ = spatial_direction_model(vec)
        assert spatial_run('eixk', args, m, domain=domain) == expected
        count += 1
    _, m, _, rows = spatial_direction_model()
    check = lambda mm: spatial_run('eixk', args, mm, domain=domain)
    for row in rows:
        assert not check(m | {'zsa': lambda *xs, rs=rows - {row}: xs in rs})
        count += 1
        for i in range(1, 5):
            wrong = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
            assert not check(m | {'zsa': lambda *xs, rs=rows - {row} | {wrong}: xs in rs})
            count += 1
    for ctx in ('reference', 'setting'):
        _, mm, _, rs = spatial_direction_model({'b': (-7, 0, 0)})
        rs = {(p, 'a', 'a', 'a', cc) for p, cc in (('a', 'reference'), ('a', 'setting'), ('b', ctx))}
        assert not check(mm | {'zsa': lambda *xs: xs in rs})
        count += 1
    spatial_unknowns(check, m, ('zsa', 'zsb', 'ba', 'shv', 'sca'))
    return dict(cases=count, all_cross_setting_positive_directions_checked=True, opposite_record_rejected_independently_of_zero_coordinate=True)

def test_spatial_orientation_checks():assert spatial_orientation_checks()

@lru_cache(None)
def spatial_axis_checks():
    cuts, m, norm = spatial_numeric()
    c = cuts.make
    count = 0
    args = ['linea', 'origin', 'frame', 'reference']
    rows = {'eiv2': {('linea', 'origin', 'guide', 'frame', 'reference')}, 'eipw': {('linea', 'frame', 'reference')}, 'eixj': {('origin', 'frame', 'reference', 'reference')}, 'eixk': {('linea', 'frame', 'reference', 'reference')}}
    m |= {n: lambda *xs, rs=rs: tuple(xs) in rs for n, rs in rows.items()}

    def family(body, f, lu, tu, role, ctx):
        if (body, f, lu, tu, ctx) != ('linea', 'frame', 'a', 'b', 'reference') or role not in ('x', 'y', 'z'):
            forbidden()
        return FunctionValue(('individual',), FS, lambda p: FunctionValue((RS,), RS, lambda t: c(Q(-2 if p == 'guide' and role == 'x' else 0))))

    def component(rec, role):
        if rec not in spatial_DOMAIN or role not in ('x', 'y', 'z'):
            forbidden()
        return c(Q(3 if role == 'x' else 0))
    m |= {'eismu': lambda *xs: 'guide', 'eisls': lambda *xs: c(Q(0)), 'eislu': family, 'zsa': lambda *xs: xs == ('a', 'linea', 'frame', 'a', 'reference'), 'zsb': component}
    check = lambda mm: spatial_run('eixl', args, mm)
    count += spatial_perturb(check, m, rows)
    assert not check(m | {'zsb': lambda rec, role: c(Q(1 if role == 'y' else 0))})
    count += 1
    spatial_unknowns(check, m, ('eismu', 'eislu', 'eisls', 'zsb'))
    return dict(cases=count, own_frame_static_axis_and_actual_material_direction_connected=True, negative_material_guide_allowed=True)

def test_spatial_axis_checks():assert spatial_axis_checks()

def spatial_triad_setup():
    cuts, m, norm = spatial_numeric()
    c = cuts.make
    lines = {'x': 'linea', 'y': 'lineb', 'z': 'linec'}
    m |= {'zbn': lambda f, ctx: 'origin', 'zbo': lambda f, role, ctx: lines[role] if role in lines else forbidden(), 'zby': lambda f, ctx: 'ruler', 'eismu': lambda *xs: 'guide', 'eisls': lambda *xs: c(Q(0))}
    rows = {'va': {('frame',)}, 'xc': {('ruler',)}, 'zbx': {('frame', 'ruler', 'reference')}, 'zbv': {('frame', 'origin', 'reference')}, 'zbw': {('frame', line, a, 'reference') for a, line in lines.items()}, 'zbr': {(line, 'origin', 'reference') for line in lines.values()}, 'eixl': {(line, 'origin', 'frame', 'reference') for line in lines.values()}, 'eiv5': {(lines[a], 'origin', 'guide', lines[b], 'origin', 'guide', 'frame', 'reference', Q(0)) for a, b in (('x', 'y'), ('x', 'z'), ('y', 'z'))}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m['eigy'] = lambda *xs: xs[0] in lines.values() and xs[1:5] == ('frame', 'reference', 'a', 'b')
    m['eislt'] = lambda *xs: c(Q(2))
    m['eirh'] = lambda *xs: False
    m['eislu'] = lambda *xs: FunctionValue(('individual',), FS, lambda p: FunctionValue((RS,), RS, lambda t: c(Q(0))))
    return (cuts, m, norm, rows)

@lru_cache(None)
def spatial_triad_checks():
    cuts, m, norm, rows = spatial_triad_setup()
    check = lambda mm: spatial_run('eixm', ['frame', 'reference'], mm)
    count = spatial_perturb(check, m, rows, norm)
    for n, row in (('zbw', ('frame', 'hidden', 'x', 'reference')), ('zbw', ('frame', 'linea', 'a', 'reference')), ('zbv', ('frame', 'hidden', 'reference'))):
        assert not check(m | {n: lambda *xs, rs=rows[n] | {row}: xs in rs})
        count += 1
    for n in ('zbn', 'zbo', 'zby'):
        old = m[n]
        assert not check(m | {n: lambda *xs, old=old: 'hidden' if xs[-1] == 'initial' else old(*xs)})
        count += 1
    spatial_unknowns(check, m, ('zbn', 'zbo', 'zby', 'eigy'))
    return dict(cases=count, all_three_own_frame_axes_exact_roles_and_unique_origin=True, initial_objects_preserved_without_freezing_ruler_position=True)

def test_spatial_triad_checks():assert spatial_triad_checks()

def spatial_transfer_setup():
    cuts, m, norm = spatial_numeric()
    lines = {'x': 'linea', 'y': 'lineb', 'z': 'linec'}
    members = {'linea': {'a', 'hidden'}, 'lineb': {'b'}, 'linec': {'point'}}
    m |= {'zbn': lambda f, ctx: 'origin', 'zbo': lambda f, role, ctx: lines[role], 'zby': lambda f, ctx: 'ruler', 'eirh': lambda body, p, ctx: body in members and p in members[body] and (ctx in ('reference', 'setting')), 'zcu': lambda p, f, ctx: p in ('point', 'a') and f == 'frame' and (ctx in ('reference', 'setting'))}
    rows = {'eisnd': {('frame', 'reference', 'setting')}, 'eixm': {('frame', ctx) for ctx in ('reference', 'setting')}, 'eixj': {(p, 'frame', 'reference', 'setting') for p in ('origin', 'a', 'hidden', 'b', 'point')}, 'eixk': {(line, 'frame', 'reference', 'setting') for line in lines.values()}}
    m |= {n: lambda *xs, rs=rs: xs in rs for n, rs in rows.items()}
    return (cuts, m, norm, rows)

@lru_cache(None)
def spatial_transfer_checks():
    _, m, _, rows = spatial_transfer_setup()
    check = lambda mm: spatial_run('eixn', ['frame', 'reference', 'setting'], mm)
    count = spatial_perturb(check, m, rows)
    original = m['eirh']
    for ctx in ('reference', 'setting'):
        assert not check(m | {'eirh': lambda body, p, cc, ctx=ctx: False if (body, p, cc) == ('linea', 'hidden', ctx) else original(body, p, cc)})
        count += 1
    originalspace = m['zcu']
    assert not check(m | {'zcu': lambda p, f, ctx: False if (p, ctx) == ('a', 'setting') else originalspace(p, f, ctx)})
    count += 1
    for n in ('zbn', 'zby', 'zbo'):
        original = m[n]
        assert not check(m | {n: lambda *xs, original=original: 'hidden' if xs[-1] == 'setting' else original(*xs)})
        count += 1
    base = m['eixj']
    assert check(m | {'eixj': lambda p, *xs: False if p == 'ruler' else base(p, *xs)})
    count += 1
    spatial_unknowns(check, m, ('eirh', 'zcu', 'zbn', 'zbo', 'zby'))
    return dict(cases=count, all_axis_members_positions_and_space_domain_preserved=True, measurement_affiliation_required=True, ruler_relocation_not_forbidden_by_axis_preservation=True)

def test_spatial_transfer_checks():assert spatial_transfer_checks()

@lru_cache(None)
def spatial_candidate_checks():
    cuts, m, norm = spatial_numeric()
    c = cuts.make
    rows = {'eixn': {('frame', 'reference', 'setting')}, 'zcu': {('point', 'frame', ctx) for ctx in ('reference', 'setting')}, 'eixj': {('point', 'frame', 'reference', 'setting')}, 'eixh': {('point', 'frame', 'x', Q(-3), 'setting')}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    args = ['point', 'frame', 'x', c(Q(-3)), 'reference', 'setting']
    check = lambda mm: spatial_run('eixo', args, mm)
    count = spatial_perturb(check, m, rows, norm)
    expected = norm(args)
    mm = m | {'eixo': lambda *xs: norm(xs) == expected}
    assert spatial_run('eixp', args[:-1], mm)
    count += 1
    assert not spatial_run('eixp', args[:-1], m | {'eixo': lambda *xs: False})
    count += 1
    for i in range(len(expected)):
        wrong = tuple(('wrong' if j == i else x for j, x in enumerate(expected)))
        assert not spatial_run('eixp', args[:-1], m | {'eixo': lambda *xs: norm(xs) == wrong})
        count += 1
    selected = ('point', 'frame', 'x', Q(-3), 'reference')
    base = args[:3] + ['reference']
    mm = m | {'zcy': lambda *xs: c(Q(-3)), 'eixp': lambda *xs: norm(xs) == selected}
    assert spatial_run('eixq', base + [c(Q(2))], mm, 'instance')
    count += 1
    assert not spatial_run('eixq', base + [c(Q(2))], mm | {'eixp': lambda *xs: norm(xs) in {selected, ('point', 'frame', 'x', Q(2), 'reference')}}, 'instance')
    count += 1
    assert not spatial_run('eixq', base + [c(Q(-3))], mm | {'eixp': lambda *xs: False}, 'instance')
    count += 1
    try:
        spatial_run('eixq', base, mm)
    except ValueError as e:
        assert 'Finite function domain' in str(e) or 'rational number domain' in str(e), str(e)
    else:
        raise AssertionError('Global real uniqueness silently sampled')
    spatial_unknowns(lambda model: spatial_run('eixq', base + [c(Q(-3))], model, 'instance'), mm, ('zcy', 'eixp', 'sca'))
    return dict(cases=count, same_point_and_geometry_before_actual_measurement=True, global_uniqueness_covers_all_measurement_settings=True, full_real_value_domain_not_sampled=True)

def test_spatial_candidate_checks():assert spatial_candidate_checks()

@lru_cache(None)
def spatial_coverage_checks():
    count = 0
    space = {'a', 'point'}
    roles = {'x', 'y', 'z'}
    rows = {'eixm': {('frame', 'reference')}, 'eixq': {(p, 'frame', a, 'reference') for p in space for a in roles}}
    m = {n: lambda *xs, rs=rs: xs in rs for n, rs in rows.items()}
    m['zcu'] = lambda p, f, ctx: p in space and (f, ctx) == ('frame', 'reference')
    check = lambda mm: spatial_run('eixr', ['frame', 'reference'], mm)
    count += spatial_perturb(check, m, rows)
    assert not check(m | {'zcu': lambda *xs: False})
    count += 1
    assert not check(m | {'zcu': lambda p, f, ctx: p in space | {'hidden'} and (f, ctx) == ('frame', 'reference')})
    count += 1
    rows = {'eixr': {('frame', 'reference'), ('moving', 'reference')}}
    m = {n: lambda *xs, rs=rs: xs in rs for n, rs in rows.items()}
    check = lambda mm: spatial_run('eixs', ['reference'], mm)
    count += spatial_perturb(check, m, rows)
    assert not check(m | {'zbm': lambda: 'frame'})
    count += 1
    return dict(cases=count, every_place_and_all_three_components_required=True, empty_or_extended_unmeasured_space_rejected=True, both_distinct_frames_required_without_value_equality=True)

def test_spatial_coverage_checks():assert spatial_coverage_checks()

space_DOMAIN=('frame', 'moving', 'restrod', 'movingrod', 'history', 'place', 'point', 'x', 'y', 'z', 'lengthunit', 'timeunit', 'author', 'paper', 'section', 'motionnode', 'previousnode', 'node', 'Kname', 'kname', 'xname', 'yname', 'zname', 'xiname', 'etaname', 'zetaname')

space_POINTS=('context', 'initial', 'discourse', 'other')
def space_run(name,args,m,mode='boundary',domain=None):return run('space',name,args,m,mode,domain)

def space_constants():
    mapping = {'ra': 'frame', 'zbm': 'moving', 'zcj': 'history', 'ta': 'lengthunit', 'rb': 'timeunit', 'yn': 'x', 'yo': 'y', 'yp': 'z', 'zb4': 'initial', 'zb6': 'context', 'ri': 'discourse', 'rd': 'author', 'eirf': 'paper', 'eisms': 'section', 'zcg': 'motionnode', 'zco': 'previousnode', 'zc2': 'node', 'eisnb': 'Kname', 'eisna': 'kname'}
    mapping.update(dict(zip((r[0] for r in COORDINATES), ('xname', 'yname', 'zname', 'xiname', 'etaname', 'zetaname'))))
    return {n: lambda x=x: x for n, x in mapping.items()}

def space_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown clock-site-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def space_relation(rows):
    return lambda *xs: tuple((value(x) for x in xs)) in rows

def space_perturb(check, m, rows, norm=lambda xs: tuple((value(x) for x in xs))):
    count = 1
    assert check(m)
    for n, rs in rows.items():
        for row in rs:
            assert not check(m | {n: lambda *xs, rs=rs - {row}: norm(xs) in rs}), (n, row)
            count += 1
            for i in range(len(row)):
                wrong = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
                assert not check(m | {n: lambda *xs, rs=rs - {row} | {wrong}: norm(xs) in rs}), (n, i)
                count += 1
    space_unknowns(check, m, rows)
    return count

@lru_cache(None)
def space_setting_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    families = {a: FunctionValue(('individual',), FS, lambda p, i=i: FunctionValue((RS,), RS, lambda t: c(Q(i + (1 if p == 'point' else 0))))) for i, a in enumerate(('x', 'y', 'z'))}
    members = FunctionValue(('individual',), 'truth', lambda p: p == 'point')

    def norm(xs):

        def one(x):
            if not isinstance(x, FunctionValue):
                return value(x)
            if x.parameters == ('number',):
                return r(x)
            if x.result == 'truth':
                return tuple((p for p in space_DOMAIN if x(p)))
            if x.result == FS:
                return tuple((r(x(p)(c(Q(t)))) for p in ('point', 'place') for t in (0, 1, 2)))
            forbidden()
        return tuple((one(x) for x in xs))
    hist = norm(['restrod', 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2)), members, *families.values()])
    rows = {'eivf': {('frame', 'initial'), ('moving', 'initial')}, 'eivg': {('frame', 'moving', 'initial')}, 'eivl': {('frame', 'moving', 'initial')}, 'eiwn': {('history',)}, 'eixs': {('context',)}, 'eipw': {('restrod', 'frame', 'context'), ('movingrod', 'moving', 'context')}, 'eigy': {hist}, 'eivv': {('movingrod', 'context')}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}

    def family(body, frame, lu, tu, axis, ctx):
        if (body, frame, lu, tu, ctx) != ('restrod', 'frame', 'lengthunit', 'timeunit', 'context') or axis not in families:
            forbidden()
        return families[axis]
    m |= {'zci': lambda h: 'context', 'zby': lambda frame, ctx: 'restrod' if frame == 'frame' else 'movingrod', 'eirh': lambda b, p, ctx: (b, p, ctx) == ('restrod', 'point', 'context'), 'eislu': family, 'eisls': lambda *xs: c(Q(0)), 'eislt': lambda *xs: c(Q(2))}
    check = lambda mm: space_run('eixt', ['context'], mm)
    count = space_perturb(check, m, rows, norm)
    assert not check(m | {'zci': lambda h: 'other'})
    count += 1
    assert not check(m | {'eipw': space_relation({('restrod', 'frame', 'context'), ('movingrod', 'frame', 'context')})})
    count += 1
    space_unknowns(check, m, ('zby', 'zci', 'eirh', 'eislu', 'eisls', 'eislt'))
    count += space_perturb(lambda mm: space_run('eix3', [], mm), {'eixt': space_relation({('context',)})}, {'eixt': {('context',)}})
    return dict(cases=count, initial_configuration_same_selected_parallel_history_and_all_measurements=True, rest_ruler_and_comoving_ruler_have_distinct_frame_conditions=True, physical_construction_is_closed_quoted_content=True)

def test_space_setting_checks():assert space_setting_checks()

@lru_cache(None)
def space_coordinate_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    count = 0
    values = {('frame', 'x'): Q(2), ('frame', 'y'): Q(3), ('frame', 'z'): Q(4), ('moving', 'x'): Q(-5), ('moving', 'y'): Q(6), ('moving', 'z'): Q(7)}

    def selected(place, frame, role, unit, ctx):
        if (place, unit, ctx) != ('place', 'lengthunit', 'context') or (frame, role) not in values:
            forbidden()
        return c(values[frame, role])
    rows = {'eixq': {('place', f, a, 'context') for f, a in values}}
    m |= {'zcy': selected, 'eixq': space_relation(rows['eixq'])}
    frames = {'ra': 'frame', 'zbm': 'moving'}
    roles = {'yn': 'x', 'yo': 'y', 'yp': 'z'}
    for sign, printed, rule, f, a in COORDINATES:
        frame, axis = (frames[f], roles[a])
        number = values[frame, axis]
        assert space_run(rule, ['place', c(number), 'context'], m)
        count += 1
        assert not space_run(rule, ['place', c(number + 1), 'context'], m)
        count += 1
        row = ('place', frame, axis, 'context')
        assert not space_run(rule, ['place', c(number), 'context'], m | {'eixq': space_relation(rows['eixq'] - {row})})
        count += 1
        space_unknowns(lambda mm: space_run(rule, ['place', c(number), 'context'], mm), m, ('zcy', 'eixq', 'ba', 'sca'))
    args = ['place', 'moving', 'y', c(Q(6)), 'context']
    norm = lambda xs: tuple((r(x) if isinstance(x, FunctionValue) else value(x) for x in xs))
    count += space_perturb(lambda mm: space_run('eixu', args, mm), m, {'eixq': {('place', 'moving', 'y', 'context')}}, norm)
    return dict(cases=count, all_six_symbols_bound_to_exact_frame_and_axis=True, negative_and_unequal_cross_frame_coordinates_allowed=True, measured_unique_value_required_not_candidate_label_alone=True)

def test_space_coordinate_checks():assert space_coordinate_checks()

def space_notation_rows():
    names = ('xname', 'yname', 'zname', 'xiname', 'etaname', 'zetaname')
    return {'eislo': {(name, rule, 'paper', 'discourse') for name, (_, _, rule, _, _) in zip(names, COORDINATES)}, 'eisd4': {('node', 'author', 'Kname', 'frame', 'paper', 'discourse'), ('node', 'author', 'kname', 'moving', 'paper', 'discourse')}}

clock_DOMAIN=('event', 'display', 'clock', 'reference', 'place', 'frame', 'moving', 'moment', 'othermoment', 'unit', 'lengthunit', 'x', 'y', 'z', 'author', 'paper', 'section', 'firstsection', 'space', 'time', 'tname', 'tauname', 'other')

clock_POINTS=('context', 'initial', 'discourse', 'other')
def clock_run(name,args,m,mode='boundary',domain=None):return run('clock',name,args,m,mode,domain)

def clock_relation(rows):
    return lambda *xs: tuple((value(x) for x in xs)) in rows

def clock_constants():
    return {n: lambda x=x: x for n, x in {'ra': 'frame', 'zbm': 'moving', 'rb': 'unit', 'ta': 'lengthunit', 'yn': 'x', 'yo': 'y', 'yp': 'z', 'zb4': 'initial', 'zb6': 'context', 'rd': 'author', 'eirf': 'paper', 'ri': 'discourse', 'eisms': 'section', 'eisdy': 'firstsection', 'zc2': 'space', 'zc3': 'time', 'eism5': 'tname', 'eisnl': 'tauname'}.items()}

def clock_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown clock-site-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def clock_perturb(check, m, rows, norm=lambda xs: tuple((value(x) for x in xs))):
    count = 1
    assert check(m)
    for n, rs in rows.items():
        for row in rs:
            assert not check(m | {n: lambda *xs, rs=rs - {row}: norm(xs) in rs}), (n, row)
            count += 1
            for i in range(len(row)):
                bad = tuple(('wrong' if i == j else x for j, x in enumerate(row)))
                assert not check(m | {n: lambda *xs, rs=rs - {row} | {bad}: norm(xs) in rs}), (n, i)
                count += 1
    clock_unknowns(check, m, rows)
    return count

@lru_cache(None)
def clock_clock_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    norm = norm_factory(cuts, (0, 2))
    fs = {a: FunctionValue((RS,), RS, lambda t, i=i: c(Q(i))) for i, a in enumerate(('x', 'y', 'z'))}
    history = ['clock', 'moving', 'context', 'lengthunit', 'unit', c(Q(0)), c(Q(2)), *fs.values()]
    rows = {'ca': {('clock',)}, 'va': {('moving',)}, 'ci': {('unit',)}, 'cc': {('clock', 'moving')}, 'eisdf': {('clock', 'context')}, 'eit2': {norm(history)}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}

    def tracks(cl, f, lu, tu, a, ctx):
        if (cl, f, lu, tu, ctx) != ('clock', 'moving', 'lengthunit', 'unit', 'context') or a not in fs:
            forbidden()
        return fs[a]
    m |= {'eismh': tracks, 'eisls': lambda *xs: c(Q(0)), 'eislt': lambda *xs: c(Q(2))}
    check = lambda mm: clock_run('eiye', ['clock', 'moving', 'context'], mm)
    count = clock_perturb(check, m, rows, norm)
    clock_unknowns(check, m, ('eismh', 'eisls', 'eislt'))
    assert check(m | {'eipw': forbidden})
    count += 1
    try:
        clock_run('eiye', ['clock', 'moving', 'context'], m | {'eisdd': lambda *xs: True, 'zzbg': lambda a, b: r(a) < r(b)}, 'native_history')
    except ValueError as e:
        assert 'rational number domain' in str(e) or 'Finite function domain' in str(e), str(e)
    else:
        raise AssertionError('Complete representative history silently sampled')
    return dict(cases=count, own_frame_complete_representative_rest_not_clock_internals=True, native_full_real_history_refused=True)

def test_clock_clock_checks():assert clock_clock_checks()

@lru_cache(None)
def clock_network_checks():
    domain = ('a', 'b', 'c')
    pop = {'a', 'b'}
    f = 'a'
    ctx = 'context'
    rows = {'va': {(f,)}, 'ci': {('b',)}, 'eisb7': {(f, 'a', 'b', ctx)}, 'eiye': {(cl, f, ctx) for cl in pop}, 'qo': {(a, b, f, 'b', ctx) for a, b in product(pop, repeat=2)}}
    base = {n: clock_relation(rs) for n, rs in rows.items()} | {'rb': lambda: 'b', 'zbh': lambda *xs: 'a', 'zbz': lambda frame, cl, c: frame == f and cl in pop and (c in (ctx, 'initial')), 'qa': lambda cl, frame, c: cl in pop and frame == f and (c == ctx), 'zcu': lambda place, frame, c: place in domain and frame == f and (c == ctx), 'cb': lambda cl, p, frame: cl in pop and cl == p and (frame == f)}
    check = lambda m: clock_run('eiyf', [f, ctx], m, domain=domain)
    count = clock_perturb(check, base, rows)
    for patch in ({'zbh': lambda *xs: 'c'}, {'zbz': lambda frame, cl, c: frame == f and cl in (pop if c == 'initial' else {'a'})}, {'qa': lambda cl, frame, c: cl in domain}, {'cb': lambda cl, p, frame: cl == 'a' and p == 'a'}, {'zcu': lambda place, frame, c: place == 'a'}):
        assert not check(base | patch)
        count += 1
    assert check(base | {'zcu': lambda place, frame, c: place in pop and frame == f and (c == ctx)})
    count += 1
    clock_unknowns(check, base, ('zbh', 'zbz', 'qa', 'zcu', 'cb'))
    return dict(cases=count, all_initial_clocks_and_all_pairs_required=True, unclocked_space_allowed=True, reference_in_same_population_and_all_locations_bound=True)

def test_clock_network_checks():assert clock_network_checks()

@lru_cache(None)
def clock_protocol_checks():
    cuts, m = numbers()
    c = cuts.make
    norm = norm_factory(cuts, ())
    domain = ('a', 'b')
    m |= {'qa': lambda cl, f, ctx: cl in domain and f == 'a' and (ctx == 'context'), 'ca': lambda cl: cl in domain, 'cc': lambda cl, f: cl in domain and f == 'a', 'cb': lambda cl, p, f: cl == p and f == 'a', 'ci': lambda u: u == 'b', 'ql': lambda a, b, f, u, ctx: (a, b, f, u, ctx) == ('a', 'b', 'a', 'b', 'context'), 'qb': lambda a, b, f, u, ctx, t: (a, b, f, u, ctx) == ('a', 'b', 'a', 'b', 'context') and t in domain}
    m |= {n: lambda t: t for n in ('qc', 'qd', 'qe', 'qf', 'qg', 'qh')}
    m |= {'qi': lambda t: c(Q(0)), 'qj': lambda t: c(Q(1)), 'qk': lambda t: c(Q(2))}
    trials = {('a', 'b', *(t for _ in range(6)), 'a', 'b', Q(0), Q(1), Q(2)) for t in domain}
    m['db'] = lambda *xs: norm(xs) in trials
    check = lambda mm: clock_run('qo', ['a', 'b', 'a', 'b', 'context'], mm, 'protocol', domain)
    count = clock_perturb(check, m, {'db': trials}, norm)
    for patch in ({'ql': lambda *xs: False}, {'qb': lambda *xs: False}):
        assert not check(m | patch)
        count += 1
    clock_unknowns(check, m, ('ql', 'qb', 'qi', 'qj', 'qk', 'qc', 'qd', 'qe', 'qf', 'qg', 'qh'))
    return dict(cases=count, nonempty_all_trials_and_completeness_not_single_success=True, all_protocol_arguments_bound=True)

def test_clock_protocol_checks():assert clock_protocol_checks()

@lru_cache(None)
def clock_local_checks():
    cuts, m = numbers()
    c = cuts.make
    norm = norm_factory(cuts, ())
    rows = {'zbz': {('moving', 'clock', 'context')}, 'zcu': {('place', 'moving', 'context')}, 'eiye': {('clock', 'moving', 'context')}, 'zbd': {('event',), ('display',)}, 'va': {('moving',)}, 'eisb7': {('moving', 'reference', 'unit', 'context')}, 'ca': {('clock',), ('reference',)}, 'cc': {('clock', 'moving'), ('reference', 'moving')}, 'ci': {('unit',)}, 'cb': {(o, 'place', 'moving') for o in ('clock', 'event', 'display')}, 'ce': {('clock', e, 'moving', 'unit', Q(7)) for e in ('event', 'display')}, 'qo': {('clock', 'reference', 'moving', 'unit', 'context')}, 'eisgm': {('event', 'display', 'clock', 'moving', 'context')}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m['zbh'] = lambda *xs: 'reference'
    args = ['event', 'clock', 'place', 'moving', c(Q(7)), 'context']
    check = lambda mm: clock_run('eiyg', args, mm)
    count = clock_perturb(check, m, rows, norm)
    clock_unknowns(check, m, ('zbh', 'ba'))
    assert not clock_run('eiyg', args[:4] + [c(Q(8)), 'context'], m)
    count += 1
    for bits in product(('a', 'b'), repeat=4):
        e, cl, p, f = bits
        row = (e, cl, p, f, Q(7), 'context')
        mm = {'eiyg': lambda *xs, row=row: norm(xs) == row}
        args = [e, p, f, c(Q(7)), 'context']
        assert clock_run('eiyh', args, mm, domain=('a', 'b'))
        count += 1
        for i in (0, 2, 3, 4, 5):
            bad = list(row)
            bad[i] = 'wrong'
            assert not clock_run('eiyh', args, {'eiyg': lambda *xs, bad=tuple(bad): norm(xs) == bad}, domain=('a', 'b'))
            count += 1
    rows = {'eiuk': {('event', 'moving', 'unit', 'context')}, 'eiyh': {('event', 'place', 'moving', Q(7), 'context')}}
    mm = {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()} | {'zbe': lambda *xs: c(Q(7))}
    count += clock_perturb(lambda mm: clock_run('eiyi', ['event', 'place', 'moving', 'context'], mm), mm, rows, norm)
    clock_unknowns(lambda mm: clock_run('eiyi', ['event', 'place', 'moving', 'context'], mm), mm, ('zbe',))
    for name, f in (('eiyn', 'frame'), ('eiyo', 'moving')):
        rows = {'eiyg': {('event', 'clock', 'place', f, Q(7), 'context')}}
        mm = {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
        count += clock_perturb(lambda mm: clock_run(name, ['event', 'clock', 'place', c(Q(7)), 'context'], mm), mm, rows, norm)
    return dict(cases=count, native_local_readout_saf_and_same_display_checked=True, population_place_clock_frame_value_and_unit_bound=True, existential_clock_selection_uses_two_individuals=True)

def test_clock_local_checks():assert clock_local_checks()

@lru_cache(None)
def clock_moment_checks():
    cuts, m = numbers()
    c = cuts.make
    norm = norm_factory(cuts, ())
    moments = {'moment', 'othermoment'}
    rows = {'zbd': {('event',)}, 'zcf': {(t, 'moving', 'unit', 'context') for t in moments}}
    m |= {n: clock_relation(rs) for n, rs in rows.items()}
    m |= {'eisnk': clock_relation({('event', t, 'moving', 'context') for t in moments}), 'zbe': lambda *xs: c(Q(7)), 'yl': lambda *xs: c(Q(7))}
    check = lambda mm: clock_run('eiyj', ['event', 'moving', 'context'], mm)
    count = clock_perturb(check, m, rows)
    assert check(m | {'eisnk': clock_relation({('event', 'moment', 'moving', 'context')})})
    count += 1
    for patch in ({'eisnk': lambda *xs: False}, {'eisnk': clock_relation({('event', 'moment', 'frame', 'context')})}, {'yl': lambda t, *xs: c(Q(8 if t == 'othermoment' else 7))}, {'zbe': lambda *xs: c(Q(8))}):
        assert not check(m | patch)
        count += 1
    clock_unknowns(check, m, ('eisnk', 'zbe', 'yl', 'ba', 'sca'))
    rows = {'zcf': {('moment', 'moving', 'unit', 'context')}}
    mm = {n: clock_relation(rs) for n, rs in rows.items()}
    mm |= {n: m[n] for n in NUM if n in m}
    mm['yl'] = lambda *xs: c(Q(9))
    count += clock_perturb(lambda mm: clock_run('eiym', ['moment', c(Q(9)), 'context'], mm), mm, rows)
    assert not clock_run('eiym', ['moment', c(Q(7)), 'context'], mm)
    count += 1
    return dict(cases=count, nonempty_and_all_moment_correspondences_match_local_value=True, multiple_descriptions_of_same_time_allowed=True, existing_t_rule_unchanged_and_tau_frame_distinguished=True)

def test_clock_moment_checks():assert clock_moment_checks()

@lru_cache(None)
def clock_coverage_checks():
    domain = ('a', 'b', 'c')
    f = 'a'
    ctx = 'context'
    pop = {'a', 'b'}
    base = {'eiyf': clock_relation({(f, ctx)}), 'zbz': lambda frame, cl, c: frame == f and cl in pop and (c == ctx), 'zcu': lambda p, frame, c: p in domain and frame == f and (c == ctx), 'cb': lambda o, p, frame: o == p and frame == f, 'zcz': lambda e, frame, c: e in domain and frame == f and (c == ctx), 'eiyi': clock_relation({(e, e, f, ctx) for e in pop}), 'eiyj': clock_relation({(e, f, ctx) for e in pop})}
    check = lambda m: clock_run('eiyk', [f, ctx], m, domain=domain)
    rows = {n: {(f, ctx)} if n == 'eiyf' else {(e, e, f, ctx) for e in pop} if n == 'eiyi' else {(e, f, ctx) for e in pop} for n in ('eiyf', 'eiyi', 'eiyj')}
    count = clock_perturb(check, base, rows)
    assert check(base | {'zcz': lambda *xs: False})
    count += 1
    assert not check(base | {'zbz': lambda frame, cl, c: frame == f and cl in domain and (c == ctx)})
    count += 1
    assert not check(base | {'cb': lambda o, p, frame: frame == f and (o == p or (o, p) == ('c', 'a'))})
    count += 1
    clock_unknowns(check, base, ('zbz', 'zcu', 'cb', 'zcz'))
    rows = {'eiyk': {('frame', 'context'), ('moving', 'context')}}
    count += clock_perturb(lambda mm: clock_run('eiyp', [], mm), {'eiyk': clock_relation(rows['eiyk'])}, rows)
    return dict(cases=count, all_events_at_all_clock_sites_not_all_space=True, no_event_existence_added_to_empty_site=True, both_frames_required=True)

def test_clock_coverage_checks():assert clock_coverage_checks()

@lru_cache(None)
def clock_presentation_checks():
    rows = {'eislo': {('tname', 'eiwt', 'paper', 'discourse'), ('tauname', 'eiym', 'paper', 'discourse')}, 'eislp': {('time', 'author', 'firstsection', r, 'paper', 'discourse') for r in ('eiyn', 'eiyo')}}
    m = {n: clock_relation(rs) for n, rs in rows.items()}
    count = clock_perturb(lambda mm: clock_run('eiyq', [], mm), m, rows)
    rows |= {'ug': {('time', 'author', 'eiyp', 'section', 'discourse')}, 'zao': {('space', 'time', 'section', 'discourse')}}
    m = {n: clock_relation(rs) for n, rs in rows.items()}
    count += clock_perturb(lambda mm: clock_run('eiyr', [], mm), m, rows)
    assert clock_run('eiyr', [], m | {n: forbidden for n in ('eiyp', 'eiyk', 'qo', 'eiyn', 'eiyo', 'eiym', 'yl')})
    count += 1
    rows = {'eir3': {('time', 'author', 'paper', 'eiys', 'discourse')}, 'ue': {('space', 'time', 'discourse')}}
    m = {n: clock_relation(rs) for n, rs in rows.items()}
    count += clock_perturb(lambda mm: clock_run('eiyt', [], mm), m, rows)
    assert clock_run('eiyt', [], m | {n: forbidden for n in ('ug', 'eiyr', 'eiyp', 'eiyk')})
    count += 1
    return dict(cases=count, two_first_section_references_and_both_time_symbols_bound=True, addition_direction_and_author_order_preserved=True, quoted_physical_content_not_executed=True)

def test_clock_presentation_checks():assert clock_presentation_checks()

def spacev2_run(name,m):return space_run(name,[],m)
@lru_cache(None)
def space_presentation_checks():
    rows = space_notation_rows()
    rows['eisd4'] = {('motionnode',) + row[1:] for row in rows['eisd4']}
    m = {n: space_relation(rs) for n, rs in rows.items()}
    count = space_perturb(lambda mm: spacev2_run('eiya', mm), m, rows)
    assert not spacev2_run('eiya', m | {'eisd4': space_relation(space_notation_rows()['eisd4'])})
    count += 1
    assert spacev2_run('eiya', m | {n: forbidden for n in ('eixu', 'eixq', 'zcy', 'eixt')})
    count += 1
    rows |= {'eislz': {('node', 'author', 'eix3', 'section', 'discourse')}, 'ug': {('node', 'author', 'eix3', 'section', 'discourse')}, 'zao': {('motionnode', 'node', 'section', 'discourse')}}
    m = {n: space_relation(rs) for n, rs in rows.items()}
    count += space_perturb(lambda mm: spacev2_run('eiyb', mm), m, rows)
    assert spacev2_run('eiyb', m | {n: forbidden for n in ('eixt', 'eix3', 'eiwn', 'eixs', 'eisnc', 'eism4')})
    count += 1
    rows = {'eir3': {('node', 'author', 'paper', 'eiyc', 'discourse')}, 'ue': {('previousnode', 'node', 'discourse')}}
    m = {n: space_relation(rs) for n, rs in rows.items()}
    count += space_perturb(lambda mm: spacev2_run('eiyd', mm), m, rows)
    assert spacev2_run('eiyd', m | {n: forbidden for n in ('eisd4', 'eislz', 'ug', 'eixt', 'eix3', 'eiyb')})
    count += 1
    return dict(cases=count, previous_naming_location_required_current_renaming_rejected=True, thought_setting_and_nonexecuting_quotation_preserved=True)
def test_corrected_prior_names():assert space_presentation_checks()

def test_source_profile_and_saved_bridge():
    doc=check.restored()['document'];old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:69]==old['statements']
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert len(doc['declarations'])==1296 and len(doc['statements'])==78
    assert len(check.vocabulary()._words)==744
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[106,107] and len(b['source_declarations'])==289
    unit=b['source_units']['einstein-1905:u0045'];assert unit['range']==[0,761]
    assert len(''.join(re.sub(r'\[M\d+\]','',unit['text']).split()))==602
    assert [r['binding'] for r in b['math']]==['ra','zbm','eixv/eixw/eixx','eixy/eixz/eix2','eiwt','eiym']
    assert b['text_boundaries']['first_section_reference_occurrences']==2
    assert b['text_boundaries']['designation_order']=={'zc2':['x','y','z','ξ','η','ζ'],'zc3':['τ']}
    assert ds[mapping()['eiyc']]['body']['force']=='assert' and ds[mapping()['eiys']]['body']['force']=='direct'
    changed=deepcopy(doc);changed['statements'][69]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(changed)

def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]
def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}

def test_new_references_and_inherited_scopes_without_physical_execution():
    doc=deepcopy(check.restored()['document']);n=check.names();b=check.BASE|{'zb7':cut(Q(3))}
    for old in (*check.SENTENCES,*check.DESIGNATIONS):
        trial=deepcopy(doc);trial['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
        trial['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:b[old]))==[True]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:'other'))==[False]
    h=check.context_handlers(b)
    assert h['designationreference'](b['eirf'],b['zcg'],1,b['ri'])==b['eisna']
    assert h['designationreference'](b['eirf'],b['zco'],1,b['ri'])==b['eism5']
    assert h['sentencetokenspanreference'](b['eirf'],b['zco'],24,b['zco'],60,b['ri'])==b['zcp']
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())

def test_reference_keys_and_unknown_designations():
    b=check.BASE|{'zb7':cut(Q(3))};h=check.context_handlers(b)
    for old,(node,i) in check.DESIGNATIONS.items():
        key=[b['eirf'],b[node],i,b['ri']];assert h['designationreference'](*key)==b[old]
        for slot in (0,1,3):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['designationreference'](*bad)
    for bad in (0,-1,7,Q(1,2),True,1.0,'1'):
        with pytest.raises(ValueError):h['designationreference'](b['eirf'],b['zc2'],bad,b['ri'])
    with pytest.raises(ValueError):h['designationreference'](b['eirf'],b['zc3'],2,b['ri'])
    for bad in (0,-1,3,Q(1,2),True,1.0,'1'):
        with pytest.raises(ValueError):h['sentencereference'](b['ri'],30,bad)

def test_whole_attribution_order_and_exact_printed_forms():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][69:71];b=check.BASE|{'zb7':cut(Q(3))}
    rows={'eir3':{(b['zc2'],b['rd'],b['eirf'],'eiyc',b['ri']),(b['zc3'],b['rd'],b['eirf'],'eiys',b['ri'])},'ue':{(b['zco'],b['zc2'],b['ri']),(b['zc2'],b['zc3'],b['ri'])}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True,True]
    for n in rows:
        for removed in rows[n]:
            assert native_run(doc,h|{mapping()[n]:relation(rows[n]-{removed})}).count(False)==1
    trial=deepcopy(check.restored()['document']);trial['statements']=trial['statements'][71:78]
    seen=[];h=context(trial,b)|{check.vocabulary()._symbols['printedform']:lambda *xs:seen.append(xs) or True}
    assert native_run(trial,h)==[True]*7
    assert {r[0] for r in seen}=={b[n] for n in check.FORMS}
    for statement,(old,text) in zip(trial['statements'],check.FORMS.items(),strict=True):
        args=statement['body']['arguments']
        assert args[1]==check.author.text_expression('de') and args[2]==check.author.text_expression(text)
        assert args[0]==call(check.names()[old])
