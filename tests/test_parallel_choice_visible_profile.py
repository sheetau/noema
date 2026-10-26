from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,Content,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_parallel_choice_visible as check
from scripts import parallel_choice_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
HISTORY_DOMAIN=('body','second','origin','otherorigin','guide','otherguide','point','hidden','frame','moving','lengthunit','timeunit','x','y','z','other')
POINTS=('context','initial','discourse','scope','scene','other')

def forbidden(*args):raise ValueError('Unknown parallel-choice-visible input')
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
    if family=='motion':
        selected|={'eipf','eigy','eioj'}
        if mode!='native_history':selected.add('se')
        if name=='eivw':selected.add('eivu')
        if name=='eivy':selected|={'eivx','eivv','eivw'}
        if name=='eivz':selected.add('eivy')
    elif family=='axes':
        selected|={'eigy','se'}
        if name=='eiv2':selected.add('eiu7')
        if name=='eiv6':selected|={'eiu7','eiv5'}
        if name=='eiv7':selected|={'eiv2','eiv6'}
        if name=='eiwa':selected|={'eiv6','eiv4'}
        if name=='eiwb':selected|={'eiv7','eiwa'}
    elif family=='states':
        if name=='eiwf':selected|={'eiwd','eiwe','eiwc'}
        if name=='eiwg':selected|={'eiwd','eiwc'}
        if name=='eiwh':selected|={'eiwf','eiwg'}
        if name=='eiwj':selected|={'eivz','eiv7','eiwh','eiwi'}
    elif family=='choice':
        selected|={'eiv7','eipw','eit2','eivz','eiwj','eiwb'}
        if name!='eiwk':selected.add('eiwk')
        if name in ('eiwo','eiwp','eiwq'):selected.add('eiwm')
        if name=='motionsettingrole':selected.add('eivx')
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
            if node.get('kind')=='forall' and node['sort']==RS:
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
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives=h,max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
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

def history_setup(positions=None,members=('guide','point','hidden')):
    cuts,m=numbers();c=cuts.make;r=cuts.read
    # Every member of this explicit finite carrier has a specified coordinate.
    # Inputs outside it are rejected, never assigned a default zero trajectory.
    pos={p:(Q(i+11),Q(5),Q(6)) for i,p in enumerate(HISTORY_DOMAIN)}
    pos.update(origin=(0,0,0),guide=(2,0,0),point=(0,0,0),hidden=(-3,0,0),otherorigin=(0,0,0),otherguide=(0,3,0))
    pos.update(positions or {})
    tracks={(a,p):FunctionValue((RS,),RS,lambda t,a=a,p=p:c(Q(pos[p][a]))) for a in range(3) for p in HISTORY_DOMAIN}
    families=[FunctionValue(('individual',),FS,lambda p,a=a:tracks[a,p] if (a,p) in tracks else forbidden()) for a in range(3)]
    def selector(body,frame,lu,tu,axis,ctx):
        if body not in HISTORY_DOMAIN or (frame,lu,tu,ctx)!=('frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return families[('x','y','z').index(axis)]
    m|={'eislu':selector,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eirh':lambda b,p,ctx:b=='body' and p in members and ctx=='context'}
    def one(x):
        if not isinstance(x,FunctionValue):return value(x)
        if x.parameters==('number',):return r(x)
        if x.parameters==(RS,):return tuple(r(x(c(Q(t)))) for t in (0,1,2))
        if x.parameters==('individual',) and x.result=='truth':return tuple(x(p) for p in HISTORY_DOMAIN)
        if x.parameters==('individual',) and x.result==FS:return tuple(one(x(p)) for p in HISTORY_DOMAIN)
        forbidden()
    return cuts,m,families,lambda xs:tuple(one(x) for x in xs)


motion_DOMAIN=HISTORY_DOMAIN + ('ruler', 'clocka', 'clockb', 'clockc')
def motion_run(name,args,m,mode='boundary',domain=None):return run('motion',name,args,m,mode,domain)

def motion_constants():
    return {n: lambda x=x: x for n, x in {'ra': 'frame', 'zbm': 'moving', 'zb4': 'initial', 'ta': 'lengthunit', 'rb': 'timeunit', 'yn': 'x', 'yo': 'y', 'yp': 'z'}.items()}

def motion_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown parallel-choice-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def motion_perturb(check, m, rows, norm=lambda xs: tuple((value(x) for x in xs))):
    count = 1
    assert check(m)
    for n, rs in rows.items():
        for row in rs:
            assert not check(m | {n: lambda *xs, rs=rs - {row}: norm(xs) in rs}), (n, row)
            count += 1
            for i in range(len(row)):
                changed = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
                assert not check(m | {n: lambda *xs, rs=rs - {row} | {changed}: norm(xs) in rs}), (n, i)
                count += 1
    motion_unknowns(check, m, rows)
    return count

@lru_cache(None)
def motion_representative_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    count = 0

    def norm(xs):

        def one(x):
            if not isinstance(x, FunctionValue):
                return value(x)
            if x.parameters == ('number',):
                return r(x)
            if x.parameters == (RS,):
                return tuple((r(x(c(Q(t)))) for t in (0, 1, 2)))
            forbidden()
        return tuple((one(x) for x in xs))
    fields = ['body', 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2))]
    metric = {('frame', 'lengthunit', 'timeunit', 'context')}
    for origin in ((3, -5, 7), (0, 0, 0), (Q(-1, 2), 4, Q(7, 3))):
        for speed in (Q(-2), Q(0), Q(1, 2), Q(5)):
            fs = [FunctionValue((RS,), RS, lambda t, a=a: c(origin[a] + (speed * r(t) if a == 0 else 0))) for a in range(3)]
            expected = norm(fields + fs)
            mm = m | {'eisdd': relation(metric), 'se': lambda *xs: norm(xs) == expected}
            args = fields + fs + [c(speed)]
            assert motion_run('eivu', args, mm) == (speed > 0)
            count += 1
            if speed <= 0:
                continue
            for axis in range(3):
                wrong = list(fs)
                wrong[axis] = FunctionValue((RS,), RS, lambda t, a=axis: c(r(fs[a](t)) + r(t) * (2 - r(t))))
                assert not motion_run('eivu', fields + wrong + [c(speed)], mm)
                count += 1
            assert not motion_run('eivu', fields + fs + [c(speed + 1)], mm)
            count += 1
            count += motion_perturb(lambda mm: motion_run('eivu', args, mm), mm, {'se': {expected}, 'eisdd': metric}, norm)
    for lo, hi in ((2, 2), (3, 2)):
        bad = list(args)
        bad[5:7] = [c(Q(lo)), c(Q(hi))]
        assert not motion_run('eivu', bad, mm | {'se': lambda *xs: True})
        count += 1
    motion_unknowns(lambda mx: motion_run('eivu', args, mx), mm, ('se', 'eisdd', 'ba', 'bf', 'bd', 'shv', 'bg'))
    bad = list(args)
    bad[-1] = FunctionValue(('number',), 'truth', lambda n: n < 1)
    try:
        motion_run('eivu', bad, mm)
    except ValueError:
        pass
    else:
        raise AssertionError('Unknown cut decoded by sampling')
    try:
        motion_run('eivu', args, mm | {'zzbg': lambda a, b: r(a) < r(b)}, 'native_history')
    except ValueError as e:
        assert 'rational number domain' in str(e) or 'Finite function domain' in str(e), str(e)
    else:
        raise AssertionError('Complete representative history silently sampled')
    return dict(cases=count, native_linear_paths_at_arbitrary_positions=True, positive_x_only_and_mid_interval_deviation_checked=True, complete_real_history_refused=True, finite_boundary_samples_not_global_proof=True)

def test_motion_representative_checks():assert motion_representative_checks()

@lru_cache(None)
def motion_history_checks():
    cuts, m, fs, norm = history_setup()
    c = cuts.make
    members = FunctionValue(('individual',), 'truth', lambda p: p in ('guide', 'point', 'hidden'))
    fields = ['body', 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2)), members, *fs]
    rows = {'eipf': {norm(fields + [c(Q(3))])}, 'eigy': {norm(fields)}}
    m |= {'zb7': lambda: c(Q(3))} | {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    count = motion_perturb(lambda mm: motion_run('eivv', ['body', 'context'], mm, domain=HISTORY_DOMAIN), m, rows, norm)
    motion_unknowns(lambda mm: motion_run('eivv', ['body', 'context'], mm, domain=HISTORY_DOMAIN), m, ('zb7', 'eislu', 'eirh', 'eisls', 'eislt'))
    traces = [f('body') for f in fs]
    representative = ['body', 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2)), *traces, c(Q(3))]
    rows = {'eivu': {norm(representative)}}

    def select(obj, frame, lu, tu, axis, ctx):
        if (obj, frame, lu, tu, ctx) != ('body', 'frame', 'lengthunit', 'timeunit', 'context') or axis not in ('x', 'y', 'z'):
            forbidden()
        return traces[('x', 'y', 'z').index(axis)]
    m |= {'eismh': select, 'eivu': lambda *xs: norm(xs) == norm(representative)}
    count += motion_perturb(lambda mm: motion_run('eivw', ['body', 'context'], mm, domain=HISTORY_DOMAIN), m, rows, norm)
    motion_unknowns(lambda mm: motion_run('eivw', ['body', 'context'], mm, domain=HISTORY_DOMAIN), m, ('zb7', 'eismh', 'eisls', 'eislt'))
    return dict(cases=count, all_material_members_and_representative_positions_kept_separate=True, same_speed_units_context_and_interval_bound=True)

def test_motion_history_checks():assert motion_history_checks()

def motion_frame_setup():
    lines = {'x': 'body', 'y': 'second', 'z': 'hidden'}
    clocks = ('clocka', 'clockb')
    origin = 'origin'
    rows = {'zca': {('moving', 'initial', 'context')}, 'zbv': {('moving', origin, 'context')}, 'zcb': {(x, 'initial', 'context') for x in (origin, *lines.values(), 'ruler', *clocks)}, 'zbx': {('moving', 'ruler', 'context')}, 'zbw': {('moving', line, axis, 'context') for axis, line in lines.items()}, 'zbr': {(line, origin, 'context') for line in lines.values()}}
    given = {('moving', clock, ctx) for clock in clocks for ctx in ('initial', 'context')}

    def selector(f, ctx):
        if f != 'moving' or ctx not in ('initial', 'context'):
            forbidden()
        return origin

    def axis(f, a, ctx):
        if f != 'moving' or a not in lines or ctx not in ('initial', 'context'):
            forbidden()
        return lines[a]
    m = {n: relation(rs) for n, rs in rows.items()} | {'zbn': selector, 'zbo': axis, 'zby': lambda f, ctx: 'ruler' if f == 'moving' and ctx in ('initial', 'context') else forbidden(), 'zbz': relation(given)}
    return (m, rows, given, lines)

@lru_cache(None)
def motion_identity_checks():
    m, rows, given, lines = motion_frame_setup()
    check = lambda mm: motion_run('eivx', ['context'], mm)
    count = motion_perturb(check, m, rows)
    for removed in sorted(given):
        assert not check(m | {'zbz': relation(given - {removed})})
        count += 1
    for extra in (('moving', 'clockc', 'context'), ('moving', 'clockc', 'initial')):
        assert not check(m | {'zbz': relation(given | {extra})})
        count += 1
    assert not check(m | {'zbz': lambda *xs: False})
    count += 1
    for n, extra in (('zbw', ('moving', 'guide', 'x', 'context')), ('zbw', ('moving', 'body', 'other', 'context')), ('zbv', ('moving', 'otherorigin', 'context'))):
        assert not check(m | {n: relation(rows[n] | {extra})})
        count += 1
    for n in ('zbn', 'zby'):
        base = m[n]
        assert not check(m | {n: lambda f, ctx, base=base: 'other' if ctx == 'context' else base(f, ctx)})
        count += 1
    for a in lines:
        base = m['zbo']
        assert not check(m | {'zbo': lambda f, r, ctx, a=a: 'other' if r == a and ctx == 'context' else base(f, r, ctx)})
        count += 1
    extra = {('moving', 'clockc', ctx) for ctx in ('initial', 'context')}
    assert check(m | {'zbz': relation(given | extra), 'zcb': relation(rows['zcb'] | {('clockc', 'initial', 'context')})})
    count += 1
    assert not check(m | {'zbo': lambda *xs: 'body', 'zbw': relation({('moving', 'body', a, 'context') for a in lines})})
    count += 1
    motion_unknowns(check, m, ('zbn', 'zbo', 'zby', 'zbz'))
    return dict(cases=count, native_identity_transfer_and_exact_axis_roles=True, clock_additions_and_losses_detected=True, unique_origin_and_all_three_distinct_axes=True)

def test_motion_identity_checks():assert motion_identity_checks()

@lru_cache(None)
def motion_population_checks():
    m, _, given, lines = motion_frame_setup()
    rows = {'eivx': {('context',)}, 'eivv': {(b, 'context') for b in (*lines.values(), 'ruler')}, 'eivw': {(x, 'context') for x in ('origin', 'clocka', 'clockb')}, 'ca': {(x,) for x in ('clocka', 'clockb')}, 'xc': {('ruler',)}, 'eisdf': {(x, 'context') for x in ('clocka', 'clockb')}}
    m |= {n: relation(rs) for n, rs in rows.items()}
    check = lambda mm: motion_run('eivy', ['context'], mm)
    count = motion_perturb(check, m, rows)
    more = given | {('moving', 'clockc', 'context')}
    assert not check(m | {'zbz': relation(more)})
    count += 1
    qualified = m | {'zbz': relation(more), 'ca': relation(rows['ca'] | {('clockc',)}), 'eisdf': relation(rows['eisdf'] | {('clockc', 'context')})}
    assert not check(qualified)
    count += 1
    assert check(qualified | {'eivw': relation(rows['eivw'] | {('clockc', 'context')})})
    count += 1
    assert check(m | {'eivv': relation(rows['eivv']), 'eivw': relation(rows['eivw'])})
    count += 1
    motion_unknowns(check, m, ('zbn', 'zbo', 'zby', 'zbz'))
    return dict(cases=count, every_axis_ruler_origin_and_clock_connected=True, clock_internal_parts_not_sent_to_material_motion=True, extra_clock_requires_its_own_full_placement=True)

def test_motion_population_checks():assert motion_population_checks()

@lru_cache(None)
def motion_frame_checks():
    cuts, m = numbers()
    c = cuts.make
    rows = {'eivy': {('context',)}, 'eioj': {('frame', 'moving', 'lengthunit', 'timeunit', 'context')}}

    def velocity(first, second, lu, tu, axis, ctx):
        if (first, second, lu, tu, ctx) != ('frame', 'moving', 'lengthunit', 'timeunit', 'context') or axis not in ('x', 'y', 'z'):
            forbidden()
        return c(Q(2 if axis == 'x' else 0))
    m |= {n: relation(rs) for n, rs in rows.items()}
    m |= {'zb7': lambda: c(Q(2)), 'eislc': velocity, 'zbi': lambda *xs: c(Q(2))}
    check = lambda mm: motion_run('eivz', ['context'], mm)
    count = motion_perturb(check, m, rows)
    for a in ('x', 'y', 'z'):
        assert not check(m | {'eislc': lambda *xs, a=a: c(Q(7)) if xs[4] == a else velocity(*xs)})
        count += 1
    for speed in (-2, 0, 3):
        assert not check(m | {'zb7': lambda speed=speed: c(Q(speed))})
        count += 1
    assert not check(m | {'zbi': lambda *xs: c(Q(3))})
    count += 1
    motion_unknowns(check, m, ('zb7', 'eislc', 'zbi', 'ba', 'sca'))
    return dict(cases=count, same_complete_frame_motion_and_three_speed_components=True, old_rod_speed_not_used=True)

def test_motion_frame_checks():assert motion_frame_checks()

axes_DOMAIN=HISTORY_DOMAIN
def axes_run(name,args,m,mode='boundary',domain=None):return run('axes',name,args,m,mode,domain)

def axes_constants():
    return {n: lambda x=x: x for n, x in {'ra': 'frame', 'ta': 'lengthunit', 'rb': 'timeunit', 'yn': 'x', 'yo': 'y', 'yp': 'z'}.items()}

def axes_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown parallel-choice-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def axes_perturb(check, m, rows, norm=lambda xs: tuple((value(x) for x in xs))):
    count = 1
    assert check(m)
    for n, rs in rows.items():
        for row in rs:
            assert not check(m | {n: lambda *xs, rs=rs - {row}: norm(xs) in rs}), (n, row)
            count += 1
            for i in range(len(row)):
                changed = tuple(('wrong' if j == i else x for j, x in enumerate(row)))
                assert not check(m | {n: lambda *xs, rs=rs - {row} | {changed}: norm(xs) in rs}), (n, i)
                count += 1
    axes_unknowns(check, m, rows)
    return count

def axes_setup(positions=None, rotate=False):
    cuts, m, base, norm = history_setup(positions)
    c = cuts.make
    r = cuts.read

    def coordinate(a, p, t):
        if p not in axes_DOMAIN:
            forbidden()
        val = r(base[a](p)(t))
        time = r(t)
        if rotate and p == 'otherguide':
            delta = (2 * (time - 1) ** 2, 2 * (1 - (time - 1) ** 2), 0)[a]
            val = r(base[a]('otherorigin')(t)) + delta
        return c(val + (3 * time if a == 0 else -2 * time if a == 1 else 0))
    tracks = {(a, p): FunctionValue((RS,), RS, lambda t, a=a, p=p: coordinate(a, p, t)) for a in range(3) for p in axes_DOMAIN}
    families = [FunctionValue(('individual',), FS, lambda p, a=a: tracks[a, p] if (a, p) in tracks else forbidden()) for a in range(3)]

    def selector(body, frame, lu, tu, axis, ctx):
        if body not in axes_DOMAIN or (frame, lu, tu, ctx) != ('frame', 'lengthunit', 'timeunit', 'context') or axis not in ('x', 'y', 'z'):
            forbidden()
        return families[('x', 'y', 'z').index(axis)]
    m['eislu'] = selector
    m['eirh'] = lambda b, p, ctx: ctx == 'context' and (b == 'body' and p in ('guide', 'point', 'hidden') or (b == 'second' and p in ('otherorigin', 'otherguide')))
    return (cuts, m, families, norm)

@lru_cache(None)
def axes_geometry_checks():
    count = 0
    args = ['body', 'origin', 'guide', 'second', 'otherorigin', 'otherguide', 'frame', 'context']
    cases = (('same', (0, 1, 0), (3, 1, 0), (True, False)), ('opposite', (0, 1, 0), (-2, 1, 0), (True, False)), ('perpendicular', (4, 3, 0), (4, 5, 0), (False, True)), ('oblique', (4, 3, 0), (5, 4, 0), (False, False)), ('collapsed', (4, 3, 0), (4, 3, 0), (False, False)))
    for label, o, g, expected in cases:
        cuts, m, _, _ = axes_setup({'otherorigin': o, 'otherguide': g})
        for time in (0, 1, 2):
            actual = tuple((axes_run(n, args + [cuts.make(Q(time))], m) for n in ('eiv4', 'eiv5')))
            assert actual == expected, (label, time, actual)
            count += 2
    cuts, m, _, _ = axes_setup({'otherorigin': (0, 1, 0)}, rotate=True)
    for time, expected in ((0, (True, False)), (1, (False, True)), (2, (True, False))):
        actual = tuple((axes_run(n, args + [cuts.make(Q(time))], m) for n in ('eiv4', 'eiv5')))
        assert actual == expected, (time, actual)
        count += 2
    cuts, m, _, _ = axes_setup({'otherorigin': (0, 1, 0), 'otherguide': (2, 1, 0), 'hidden': (-3, 1, 0)})
    assert not axes_run('eiv4', args + [cuts.make(Q(1))], m)
    count += 1
    cuts, m, _, _ = axes_setup({'otherorigin': (0, 1, 0), 'otherguide': (2, 1, 0)})
    axes_unknowns(lambda mm: axes_run('eiv4', args + [cuts.make(Q(1))], mm), m, ('eislu', 'eirh', 'ba', 'bf', 'sca'))
    return dict(cases=count, actual_time_dependent_directions_not_initial_directions=True, opposite_and_transversely_separated_parallel_axes_allowed=True, intermediate_rotation_and_bent_hidden_member_detected=True)

def test_axes_geometry_checks():assert axes_geometry_checks()

@lru_cache(None)
def axes_history_checks():
    cuts, m, fs, norm = axes_setup()
    c = cuts.make
    members = FunctionValue(('individual',), 'truth', lambda p: p in ('guide', 'point', 'hidden'))
    fields = ['body', 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2)), members, *fs]
    origin = ['origin', 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2)), *(f('origin') for f in fs)]
    line = ['body', 'origin', 'guide', 'frame', 'context']
    rows = {'eismv': {('body', 'context')}, 'eigy': {norm(fields)}, 'se': {norm(origin)}, 'eiu7': {norm(line + [c(Q(1))])}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}

    def representative(o, f, lu, tu, axis, ctx):
        if (o, f, lu, tu, ctx) != ('origin', 'frame', 'lengthunit', 'timeunit', 'context') or axis not in ('x', 'y', 'z'):
            forbidden()
        return fs[('x', 'y', 'z').index(axis)]('origin')
    m['eismh'] = representative
    check = lambda mm: axes_run('eiv2', line + [c(Q(1))], mm, 'instance')
    count = axes_perturb(check, m, rows, norm)
    for axis in ('x', 'y', 'z'):

        def bad(*xs, axis=axis):
            fn = representative(*xs)
            return FunctionValue((RS,), RS, lambda t: c(cuts.read(fn(t)) + 1)) if xs[4] == axis else fn
        assert not check(m | {'eismh': bad})
        count += 1
    for time in (-1, 0, 1, 2, 3):
        args = line + [c(Q(time))]
        expected = time not in (0, 1, 2)
        assert axes_run('eiv2', args, m | {'eiu7': lambda *xs: False}, 'instance') == expected
        count += 1
    axes_unknowns(check, m, ('eislu', 'eismh', 'eisls', 'eislt', 'eirh'))
    try:
        axes_run('eiv2', line, m)
    except ValueError as e:
        assert 'rational number domain' in str(e) or 'Finite function domain' in str(e), str(e)
    else:
        raise AssertionError('All real times silently sampled')
    return dict(cases=count, material_and_representative_origins_share_complete_worldline=True, all_time_body_and_interval_guard_checked=True, complete_real_time_quantification_refused=True, finite_function_fingerprints_only_for_boundary_binding=True)

def test_axes_history_checks():assert axes_history_checks()

def axes_triad_setup():
    cuts, m, _, norm = axes_setup()
    lines = {'x': 'body', 'y': 'second', 'z': 'hidden'}
    rows = {'va': {('moving',)}, 'zbv': {('moving', 'origin', 'context')}, 'zbw': {('moving', line, a, 'context') for a, line in lines.items()}, 'zbr': {(line, 'origin', 'context') for line in lines.values()}}
    rows['eiu7'] = {(line, 'origin', 'guide', 'frame', 'context', Q(1)) for line in lines.values()}
    rows['eiv5'] = {(lines[a], 'origin', 'guide', lines[b], 'origin', 'guide', 'frame', 'context', Q(1)) for a, b in (('x', 'y'), ('x', 'z'), ('y', 'z'))}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m |= {'zbn': lambda f, c: 'origin', 'zbo': lambda f, a, c: lines[a] if (f, c) == ('moving', 'context') and a in lines else forbidden(), 'eismu': lambda *xs: 'guide', 'eigy': lambda *xs: xs[0] in lines.values() and xs[1:5] == ('frame', 'context', 'lengthunit', 'timeunit')}
    return (cuts, m, rows, lines, norm)

@lru_cache(None)
def axes_triad_checks():
    cuts, m, rows, lines, norm = axes_triad_setup()
    c = cuts.make
    check = lambda mm: axes_run('eiv6', ['moving', 'context', c(Q(1))], mm)
    count = axes_perturb(check, m, rows, norm)
    for n, extra in (('zbw', ('moving', 'other', 'x', 'context')), ('zbw', ('moving', 'body', 'other', 'context')), ('zbv', ('moving', 'otherorigin', 'context'))):
        assert not check(m | {n: relation(rows[n] | {extra})})
        count += 1
    assert not check(m | {'eigy': lambda *xs: False})
    count += 1
    axes_unknowns(check, m, ('eismu', 'zbn', 'zbo', 'eigy'))
    rows = {'eiv2': {(line, 'origin', 'guide', 'frame', 'context') for line in lines.values()}, 'eiv6': {('moving', 'context', Q(1))}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    check = lambda mm: axes_run('eiv7', ['moving', 'context', c(Q(1))], mm, 'instance')
    count += axes_perturb(check, m, rows, norm)
    for time in (-1, 0, 1, 2, 3):
        assert axes_run('eiv7', ['moving', 'context', c(Q(time))], m | {'eiv6': lambda *xs: False}, 'instance') == (time not in (0, 1, 2))
        count += 1
    try:
        axes_run('eiv7', ['moving', 'context'], m)
    except ValueError as e:
        assert 'rational number domain' in str(e) or 'Finite function domain' in str(e), str(e)
    else:
        raise AssertionError('All-time triad silently sampled')
    return dict(cases=count, native_three_axes_and_exact_roles_connected=True, all_three_complete_lines_and_every_time_bound=True)

def test_axes_triad_checks():assert axes_triad_checks()

@lru_cache(None)
def axes_parallel_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    norm = lambda xs: tuple((r(x) if isinstance(x, FunctionValue) else value(x) for x in xs))
    lines = {('frame', 'x'): 'body', ('frame', 'y'): 'second', ('frame', 'z'): 'hidden', ('moving', 'x'): 'point', ('moving', 'y'): 'other', ('moving', 'z'): 'otherguide'}
    expected = lambda a, b: (a, 'origin', 'guide', b, 'otherorigin', 'guide', 'frame', 'context', Q(1))
    rows = {'eiv6': {('frame', 'context', Q(1)), ('moving', 'context', Q(1))}, 'eiv4': {expected(lines['frame', a], lines['moving', a]) for a in ('x', 'y', 'z')}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m |= {'zbn': lambda f, c: 'origin' if f == 'frame' else 'otherorigin', 'zbo': lambda f, a, c: lines[f, a], 'eismu': lambda *xs: 'guide', 'eisls': lambda *xs: c(Q(0)), 'eislt': lambda *xs: c(Q(2))}
    check = lambda mm: axes_run('eiwa', ['frame', 'moving', 'context', c(Q(1))], mm)
    count = axes_perturb(check, m, rows, norm)
    assert not axes_run('eiwa', ['frame', 'frame', 'context', c(Q(1))], m | {'eiv6': lambda *xs: True, 'eiv4': lambda *xs: True})
    count += 1
    rows = {'eiv7': {('frame', 'context'), ('moving', 'context')}, 'eiwa': {('frame', 'moving', 'context', Q(1))}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    check = lambda mm: axes_run('eiwb', ['frame', 'moving', 'context', c(Q(1))], mm, 'instance')
    count += axes_perturb(check, m, rows, norm)
    for time in (-1, 0, 1, 2, 3):
        assert axes_run('eiwb', ['frame', 'moving', 'context', c(Q(time))], m | {'eiwa': lambda *xs: False}, 'instance') == (time not in (0, 1, 2))
        count += 1
    try:
        axes_run('eiwb', ['frame', 'moving', 'context'], m)
    except ValueError as e:
        assert 'rational number domain' in str(e) or 'Finite function domain' in str(e), str(e)
    else:
        raise AssertionError('Whole interval alignment silently sampled')
    return dict(cases=count, all_three_corresponding_pairs_and_distinct_frames=True, same_two_histories_across_all_times=True, no_origin_coincidence_or_positive_orientation_required=True)

def test_axes_parallel_checks():assert axes_parallel_checks()

states_DOMAIN=HISTORY_DOMAIN
def states_run(name,args,m,mode='boundary',domain=None):return run('states',name,args,m,mode,domain)

def states_constants():
    return {n: lambda x=x: x for n, x in {'ra': 'frame', 'zbm': 'moving', 'zb6': 'scope', 'ta': 'lengthunit', 'rb': 'timeunit', 'yn': 'x', 'yo': 'y', 'yp': 'z'}.items()}

def states_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown parallel-choice-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def states_perturb(check, m, rows, norm=lambda xs: tuple((value(x) for x in xs))):
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
    states_unknowns(check, m, rows)
    return count

@lru_cache(None)
def states_coordinate_checks():
    cuts, m, fs, _ = axes_setup()
    c = cuts.make
    r = cuts.read
    coords = {a: r(fs[i]('guide')(c(Q(1)))) for i, a in enumerate(('x', 'y', 'z'))}

    def record(p, moment, f, lu, a, ctx):
        if (p, moment, f, lu) != ('guide', 'point', 'frame', 'lengthunit') or a not in coords or ctx not in ('context', 'scene'):
            forbidden()
        return c(coords[a])
    rows = {'zce': {('guide', 'point', 'frame', 'lengthunit', ctx) for ctx in ('context', 'scene')}, 'zcf': {('point', 'frame', 'timeunit', ctx) for ctx in ('context', 'scene')}}
    m |= {n: relation(rs) for n, rs in rows.items()}
    m |= {'ym': record, 'yl': lambda *xs: c(Q(1))}
    check = lambda mm: states_run('eiwc', ['guide', 'point', 'context', 'scene'], mm)
    count = states_perturb(check, m, rows)
    for a in coords:
        assert not check(m | {'ym': lambda *xs, a=a: c(coords[a] + 1) if xs[4] == a and xs[5] == 'scene' else record(*xs)})
        count += 1
    assert not check(m | {'yl': lambda *xs: c(Q(2 if xs[-1] == 'scene' else 1))})
    count += 1
    states_unknowns(check, m, ('ym', 'yl', 'ba', 'sca'))
    rows = {n: {row for row in rs if row[-1] == 'context'} for n, rs in rows.items()}
    check = lambda mm: states_run('eiwe', ['body', 'guide', 'point', 'context'], mm)
    count += states_perturb(check, m, rows)
    for a in coords:
        assert not check(m | {'ym': lambda *xs, a=a: c(coords[a] + 1) if xs[4] == a else record(*xs)})
        count += 1
    for time in (-1, 3):
        assert not check(m | {'yl': lambda *xs, time=time: c(Q(time))})
        count += 1
    states_unknowns(check, m, ('ym', 'yl', 'eislu', 'eisls', 'eislt'))
    return dict(cases=count, all_three_coordinates_and_same_rest_time_checked=True, record_values_bound_to_physical_history=True)

def test_states_coordinate_checks():assert states_coordinate_checks()

def states_objects():
    return ({'x': 'body', 'y': 'second', 'z': 'other'}, {'body': ('guide', 'hidden'), 'second': ('otherguide',), 'other': ('point',)})

@lru_cache(None)
def states_metadata_checks():
    lines, _ = states_objects()
    rows = {'zcn': {('point',)}, 'zbv': {('moving', 'origin', 'scene')}, 'zbw': {('moving', line, a, 'scene') for a, line in lines.items()}}
    m = {n: relation(rs) for n, rs in rows.items()} | {'zcl': lambda p: 'scene', 'zbn': lambda *xs: 'origin', 'zbo': lambda f, a, ctx: lines[a]}
    check = lambda mm: states_run('eiwd', ['point', 'context'], mm)
    count = states_perturb(check, m, rows)
    for n, extra in (('zbv', ('moving', 'otherorigin', 'scene')), ('zbw', ('moving', 'guide', 'x', 'scene')), ('zbw', ('moving', 'body', 'other', 'scene'))):
        assert not check(m | {n: relation(rows[n] | {extra})})
        count += 1
    assert not check(m | {'zbn': lambda f, ctx: 'otherorigin' if ctx == 'scene' else 'origin'})
    count += 1
    for axis in lines:
        assert not check(m | {'zbo': lambda f, a, ctx, axis=axis: 'hidden' if a == axis and ctx == 'scene' else lines[a]})
        count += 1
    states_unknowns(check, m, ('zcl', 'zbn', 'zbo'))
    return dict(cases=count, same_origin_and_exact_three_roles_in_snapshot=True, no_whole_history_imposed_on_snapshot=True)

def test_states_metadata_checks():assert states_metadata_checks()

def states_population_setup():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    lines, members = states_objects()
    norm = lambda xs: tuple((r(x) if isinstance(x, FunctionValue) else value(x) for x in xs))
    selected = {(body, p) for body, ps in members.items() for p in (*ps, 'origin')}
    m |= {'zci': lambda hist: 'context', 'zcl': lambda pose: 'scene', 'zbn': lambda *xs: 'origin', 'zbo': lambda f, a, ctx: lines[a], 'eirh': lambda body, p, ctx: ctx == 'context' and p in members.get(body, ()), 'yl': lambda *xs: c(Q(1))}
    return (cuts, m, norm, selected)

@lru_cache(None)
def states_assignment_checks():
    cuts, m, norm, selected = states_population_setup()
    rows = {'zcn': {('point',)}, 'zcf': {('guide', 'frame', 'timeunit', ctx) for ctx in ('scope', 'context')}, 'zck': {('body', 'guide', 'point', 'frame', 'timeunit', Q(1), 'context')}, 'eiwd': {('point', 'context')}, 'eiwe': {(b, p, 'guide', 'context') for b, p in selected}, 'eiwc': {(p, 'guide', 'context', 'scene') for b, p in selected}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    check = lambda mm: states_run('eiwf', ['body', 'guide', 'point'], mm)
    count = states_perturb(check, m, rows, norm)
    assert not check(m | {'eirh': lambda b, p, ctx: (b, p) in {('body', 'otherorigin')} or m['eirh'](b, p, ctx)})
    count += 1
    states_unknowns(check, m, ('zci', 'zcl', 'zbn', 'zbo', 'eirh', 'yl'))
    rows = {'eiwd': {('point', 'context'), ('otherguide', 'context')}, 'eiwc': {(p, 'guide', 'scene', 'other') for b, p in selected}}
    m |= {n: relation(rs) for n, rs in rows.items()}
    m['zcl'] = lambda p: 'scene' if p == 'point' else 'other'
    count += states_perturb(lambda mm: states_run('eiwg', ['point', 'otherguide', 'guide', 'context'], mm), m, rows)
    return dict(cases=count, all_axis_members_and_origin_bound_to_same_history_and_snapshot=True, extra_hidden_member_cannot_be_omitted=True, distinct_state_identifiers_can_describe_equal_configuration=True)

def test_states_assignment_checks():assert states_assignment_checks()

@lru_cache(None)
def states_uniqueness_checks():
    domain = ('a', 'b')
    pairs = list(product(domain, repeat=2))
    count = 0
    for assigned_bits in product((False, True), repeat=2):
        assigned = {p for p, on in zip(domain, assigned_bits) if on}
        for equal_bits in product((False, True), repeat=4):
            same = {pair for pair, on in zip(pairs, equal_bits) if on}
            m = {'zci': lambda h: 'context', 'eiwf': lambda h, t, p: p in assigned, 'eiwg': lambda a, b, t, ctx: (a, b) in same}
            expected = bool(assigned) and all(((a, b) in same for a, b in product(assigned, repeat=2)))
            assert states_run('eiwh', ['a', 'b'], m, domain=domain) == expected
            count += 1
    return dict(cases=count, existence_and_all_corresponding_states_checked=True, duplicate_equal_descriptions_allowed_but_conflicting_state_rejected=True)

def test_states_uniqueness_checks():assert states_uniqueness_checks()

@lru_cache(None)
def states_coverage_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    values = {p: Q(10) for p in states_DOMAIN}
    values.update(guide=Q(0), point=Q(2), hidden=Q(1), second=Q(1))
    rows = {'ys': {('guide', 'context'), ('point', 'context')}, 'zcf': {(p, 'frame', 'timeunit', 'context') for p in states_DOMAIN}}
    m |= {n: relation(rs) for n, rs in rows.items()}
    m |= {'yl': lambda p, *xs: c(values[p]), 'eisls': lambda *xs: c(Q(0)), 'eislt': lambda *xs: c(Q(2))}
    count = 0
    for time, expected in ((-1, False), (0, True), (1, False), (2, True), (3, False)):
        assert states_run('eiwi', [c(Q(time)), 'context'], m) == expected
        count += 1
    for witness in ('hidden', 'second'):
        check = lambda mm: states_run('eiwi', [c(Q(1)), 'context'], mm)
        amended = m | {'ys': relation(rows['ys'] | {(witness, 'context')})}
        assert check(amended)
        count += 1
        assert not check(amended | {'zcf': relation(rows['zcf'] - {(witness, 'frame', 'timeunit', 'context')})})
        count += 1
    states_unknowns(lambda mm: states_run('eiwi', [c(Q(0)), 'context'], mm), m, ('ys', 'zcf', 'yl', 'eisls', 'eislt'))
    return dict(cases=count, missing_intermediate_real_time_detected=True, alternative_and_duplicate_time_records_allowed=True)

def test_states_coverage_checks():assert states_coverage_checks()

@lru_cache(None)
def states_candidate_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    norm = lambda xs: tuple((r(x) if isinstance(x, FunctionValue) else value(x) for x in xs))
    rows = {'zch': {('body', 'scope')}, 'eivz': {('context',)}, 'eiv7': {('moving', 'context')}, 'eiwh': {('body', p) for p in ('guide', 'point')}, 'eiwi': {(Q(1), 'context')}}
    ys = {(p, ctx) for p in ('guide', 'point') for ctx in ('scope', 'context')}
    alltime = {('frame', 'moving', p, 'context') for p in ('guide', 'point')}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m |= {'zci': lambda h: 'context', 'ys': relation(ys), 'eisla': relation(alltime), 'eisls': lambda *xs: c(Q(0)), 'eislt': lambda *xs: c(Q(2))}
    check = lambda mm: states_run('eiwj', ['body', c(Q(1))], mm, 'instance')
    count = states_perturb(check, m, rows, norm)
    for row in ys:
        assert not check(m | {'ys': relation(ys - {row})})
        count += 1
    for row in alltime:
        assert not check(m | {'eisla': relation(alltime - {row})})
        count += 1
    assert not check(m | {'ys': lambda *xs: False, 'eisla': lambda *xs: False})
    count += 1
    for t in (-1, 0, 1, 2, 3):
        assert states_run('eiwj', ['body', c(Q(t))], m | {'eiwi': lambda *xs: False}, 'instance') == (t not in (0, 1, 2))
        count += 1
    states_unknowns(check, m, ('zci', 'ys', 'eisla', 'eisls', 'eislt'))
    try:
        states_run('eiwj', ['body'], m)
    except ValueError as e:
        assert 'rational number domain' in str(e) or 'Finite function domain' in str(e), str(e)
    else:
        raise AssertionError('All real-time coverage silently sampled')
    return dict(cases=count, same_motion_geometry_and_complete_time_population=True, full_interval_coverage_not_finitely_sampled=True)

def test_states_candidate_checks():assert states_candidate_checks()

choice_DOMAIN=HISTORY_DOMAIN + ('author', 'paper', 'section', 'initialnode', 'firstnode', 'definitenode', 'adoptionnode', 'reasonnode', 'tdesignation', 'kdesignation', 'Kdesignation', 'usea', 'useb', 'usec')
def choice_run(name,args,m,domain=None):return run('choice',name,args,m,domain=domain)

def choice_constants():
    return {n: lambda x=x: x for n, x in {'ra': 'frame', 'zbm': 'moving', 'zb4': 'initial', 'zb6': 'context', 'zcj': 'body', 'ta': 'lengthunit', 'rb': 'timeunit', 'yn': 'x', 'yo': 'y', 'yp': 'z', 'rd': 'author', 'eirf': 'paper', 'eisms': 'section', 'ri': 'discourse', 'zb5': 'initialnode', 'zcg': 'firstnode', 'zco': 'definitenode', 'zcp': 'adoptionnode', 'zcq': 'reasonnode', 'eism5': 'tdesignation', 'eisna': 'kdesignation', 'eisnb': 'Kdesignation'}.items()}

def choice_unknowns(check, m, names):
    for n in names:
        try:
            check(m | {n: forbidden})
        except ValueError as e:
            assert 'Unknown parallel-choice-visible' in str(e), str(e)
        else:
            raise AssertionError(('Unknown input accepted', n))

def choice_perturb(check, m, rows, norm=lambda xs: tuple((value(x) for x in xs))):
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
    choice_unknowns(check, m, rows)
    return count

@lru_cache(None)
def choice_reference_checks():
    cuts, m, fs, norm = history_setup()
    c = cuts.make
    lines = {'x': 'body', 'y': 'second', 'z': 'hidden'}
    origin = ['origin', 'frame', 'context', 'lengthunit', 'timeunit', c(Q(0)), c(Q(2)), *(f('origin') for f in fs)]
    rows = {'eiv7': {('frame', 'context')}, 'eipw': {(line, 'frame', 'context') for line in lines.values()}, 'eit2': {norm(origin)}}
    m |= {n: lambda *xs, rs=rs: norm(xs) in rs for n, rs in rows.items()}
    m |= {'zbn': lambda *xs: 'origin', 'zbo': lambda f, a, ctx: lines[a], 'eismh': lambda o, f, lu, tu, a, ctx: fs[('x', 'y', 'z').index(a)](o)}
    check = lambda mm: choice_run('eiwk', ['context'], mm, domain=HISTORY_DOMAIN)
    count = choice_perturb(check, m, rows, norm)
    assert not check(m | {'zbn': lambda f, ctx: 'otherorigin' if ctx == 'initial' else 'origin'})
    count += 1
    for a in lines:
        assert not check(m | {'zbo': lambda f, role, ctx, a=a: 'other' if role == a and ctx == 'initial' else lines[role]})
        count += 1
    choice_unknowns(check, m, ('zbn', 'zbo', 'eismh', 'eisls', 'eislt'))
    rows = {'eivz': {('context',)}, 'eiv7': {('moving', 'context')}, 'eiwk': {('context',)}}
    count += choice_perturb(lambda mm: choice_run('eiwl', ['context'], mm), {n: relation(rs) for n, rs in rows.items()}, rows)
    return dict(cases=count, same_initial_reference_origin_and_all_axes_remain_static=True, moving_frame_not_given_static_condition=True)

def test_choice_reference_checks():assert choice_reference_checks()

@lru_cache(None)
def choice_candidate_checks():
    rows = {'eiwj': {('body',)}, 'eiwk': {('context',)}, 'eiwb': {('frame', 'moving', 'context')}}
    m = {n: relation(rs) for n, rs in rows.items()} | {'zci': lambda h: 'context'}
    count = choice_perturb(lambda mm: choice_run('eiwn', ['body'], mm), m, rows)
    domain = ('a', 'b')
    for valid_bits in product((False, True), repeat=2):
        valid = {h for h, on in zip(domain, valid_bits) if on}
        for parallel_bits in product((False, True), repeat=2):
            parallel = {h for h, on in zip(domain, parallel_bits) if on}
            ctx = {'a': 'context', 'b': 'other'}
            m = {'ra': lambda: 'a', 'zbm': lambda: 'b', 'zci': lambda h: ctx[h], 'eiwm': lambda h: h in valid, 'eiwb': lambda a, b, c: any((ctx[h] == c for h in parallel))}
            assert choice_run('eiwo', [], m, domain) == bool(valid & parallel)
            count += 1
    m = {'zci': lambda h: 'context', 'eiwm': relation({('body',)})}
    assert choice_run('eiwp', [], m)
    assert not choice_run('eiwp', [], m | {'zci': lambda h: 'other'})
    count += 2
    return dict(cases=count, one_candidate_meets_admissibility_and_whole_interval_alignment=True, definite_selected_history_kept_separate_from_parallel_possibility=True)

def test_choice_candidate_checks():assert choice_candidate_checks()

@lru_cache(None)
def choice_symmetry_checks():
    domain = ('a', 'b')
    count = 0
    for forward in (dict(a='a', b='b'), dict(a='b', b='a'), dict(a='a', b='a')):
        for inverse in (dict(a='a', b='b'), dict(a='b', b='a')):
            for flags in product((False, True), repeat=2):
                valid = {h for h, on in zip(domain, flags) if on}

                def physical(d, f, i, ref, axis, ctx):
                    return tuple((d(p) for p in domain)) == (True, True) and tuple((f(p) for p in domain)) == tuple((forward[p] for p in domain)) and (tuple((i(p) for p in domain)) == tuple((inverse[p] for p in domain))) and ((ref, axis, ctx) == ('a', 'b', 'context'))
                m = {'ra': lambda: 'a', 'yn': lambda: 'b', 'zch': lambda h, c: h in domain and c == 'context', 'zcr': lambda h: forward[h], 'zcs': lambda h: inverse[h], 'eiwm': lambda h: h in valid, 'eism3': physical}
                expected = all((inverse[forward[h]] == h and forward[inverse[h]] == h and ((h in valid) == (forward[h] in valid)) for h in domain))
                assert choice_run('eiwq', [], m, domain) == expected
                count += 1
    m = {'ra': lambda: 'a', 'yn': lambda: 'b', 'zbm': lambda: 'b', 'zch': lambda *xs: True, 'zcr': lambda h: h, 'zcs': lambda h: h, 'eiwm': lambda h: True, 'eism3': lambda *xs: True, 'zci': lambda h: 'context', 'eiwb': lambda *xs: False}
    assert choice_run('eiwq', [], m, domain) and (not choice_run('eiwo', [], m, domain))
    count += 1
    assert not choice_run('eiwq', [], m | {'eism3': lambda *xs: False}, domain)
    count += 1
    choice_unknowns(lambda mm: choice_run('eiwq', [], mm, domain), m, ('eism3', 'zch', 'zcr', 'zcs', 'eiwm'))
    return dict(cases=count, native_bijection_and_condition_preservation_checked=True, physical_symmetry_classification_required_beyond_arbitrary_permutation=True, symmetry_does_not_imply_parallel_candidate_existence=True)

def test_choice_symmetry_checks():assert choice_symmetry_checks()

@lru_cache(None)
def choice_notation_checks():
    cuts, m = numbers()
    c = cuts.make
    r = cuts.read
    rows = {'zcf': {('point', 'frame', 'timeunit', 'context')}}
    m |= {'zcf': relation(rows['zcf']), 'yl': lambda *xs: c(Q(3))}
    count = choice_perturb(lambda mm: choice_run('eiwt', ['point', c(Q(3)), 'context'], mm), m, rows)
    assert not choice_run('eiwt', ['point', c(Q(4)), 'context'], m)
    count += 1
    choice_unknowns(lambda mm: choice_run('eiwt', ['point', c(Q(3)), 'context'], mm), m, ('yl', 'ba', 'sca'))
    uses = {('usea', 'tdesignation', 'paper', 'paper', 'discourse'), ('useb', 'tdesignation', 'paper', 'paper', 'discourse'), ('usec', 'tdesignation', 'paper', 'paper', 'discourse')}
    rows = {'eislo': {('tdesignation', 'eiwt', 'paper', 'discourse')}, 'eism7': {(u, 'eiwt', 'paper', 'discourse') for u in ('usea', 'useb', 'usec')}}
    m = {n: relation(rs) for n, rs in rows.items()} | {'eism6': relation(uses)}
    count += choice_perturb(lambda mm: choice_run('eiwu', [], mm), m, rows)
    assert not choice_run('eiwu', [], m | {'eism6': lambda *xs: False})
    count += 1
    assert not choice_run('eiwu', [], m | {'eism6': relation(uses | {('other', 'tdesignation', 'paper', 'paper', 'discourse')})})
    count += 1
    assert choice_run('eiwu', [], m | {'yl': forbidden, 'zcf': forbidden})
    count += 1
    choice_unknowns(lambda mm: choice_run('eiwu', [], mm), m, ('eism6',))
    return dict(cases=count, rest_time_rule_and_every_occurrence_bound=True, notation_does_not_execute_measurement=True)

def test_choice_notation_checks():assert choice_notation_checks()

@lru_cache(None)
def choice_presentation_checks():
    rows = {'eism4': {('author', 'eiwr', 'section', 'paper', 'discourse')}, 'zct': {('reasonnode', 'author', 'eiwq', 'adoptionnode', 'section', 'discourse')}}
    m = {n: relation(rs) for n, rs in rows.items()}
    count = choice_perturb(lambda mm: choice_run('eiws', [], mm), m, rows)
    assert choice_run('eiws', [], m | {n: forbidden for n in ('ug', 'eiwo', 'eiwn', 'eiwq', 'sfs', 'eism3')})
    count += 1
    rows = {'ug': {('adoptionnode', 'author', 'eiwo', 'section', 'discourse')}}
    count += choice_perturb(lambda mm: choice_run('eiwr', [], mm), {n: relation(rs) for n, rs in rows.items()}, rows)
    rows = {'ug': {('firstnode', 'author', 'eiwv', 'section', 'discourse')}, 'zao': {('initialnode', 'firstnode', 'section', 'discourse')}, 'eisd4': {('firstnode', 'author', 'kdesignation', 'moving', 'paper', 'discourse'), ('firstnode', 'author', 'Kdesignation', 'frame', 'paper', 'discourse')}}
    m = {n: relation(rs) for n, rs in rows.items()}
    count += choice_perturb(lambda mm: choice_run('eiww', [], mm), m, rows)
    assert choice_run('eiww', [], m | {n: forbidden for n in ('eiwv', 'eiwl', 'eivz', 'eiv7', 'eit2')})
    count += 1
    rows = {'uh': {('definitenode', 'author', 'eiwp', 'section', 'discourse')}, 'ue': {('firstnode', 'definitenode', 'discourse')}, 'eisa5': {('adoptionnode', 'author', 'eiwo', 'eiwu', 'discourse')}, 'eism4': {('author', 'eiwr', 'section', 'paper', 'discourse')}, 'zct': {('reasonnode', 'author', 'eiwq', 'adoptionnode', 'section', 'discourse')}, 'eislo': {('tdesignation', 'eiwt', 'paper', 'discourse')}, 'eism7': {('usea', 'eiwt', 'paper', 'discourse')}}

    def inference(author, premise, result, ctx):
        return (author, result, ctx) == ('author', 'definitenode', 'discourse') and {p for p in choice_DOMAIN if premise(p)} == {'firstnode'}
    m = {n: relation(rs) for n, rs in rows.items()} | {'ud': inference, 'eism6': relation({('usea', 'tdesignation', 'paper', 'paper', 'discourse')})}
    count += choice_perturb(lambda mm: choice_run('eiwz', [], mm), m, rows)
    assert not choice_run('eiwz', [], m | {'ud': lambda *xs: False})
    count += 1
    assert choice_run('eiwz', [], m | {n: forbidden for n in ('eiwp', 'eiwo', 'eiwm', 'ug')})
    count += 1
    for name, node, message, prior in (('eiwy', 'firstnode', 'eiwx', 'initialnode'), ('eiw3', 'definitenode', 'eiw2', 'firstnode')):
        rows = {'eir3': {(node, 'author', 'paper', message, 'discourse')}, 'ue': {(prior, node, 'discourse')}}
        m = {n: relation(rs) for n, rs in rows.items()}
        count += choice_perturb(lambda mm: choice_run(name, [], mm), m, rows)
        assert choice_run(name, [], m | {n: forbidden for n in ('ug', 'uh', 'eism4', 'eism7', 'zct', 'eivz', 'eiwo')})
        count += 1
    return dict(cases=count, permission_not_assumption_execution_or_physical_truth=True, two_sentence_forces_names_consequence_and_parenthesis_connected=True, author_attribution_does_not_execute_quoted_contents=True)

def test_choice_presentation_checks():assert choice_presentation_checks()

def test_profile_source_and_annotation_boundaries():
    doc=check.restored()['document'];old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:64]==old['statements']
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert len(doc['declarations'])==1223 and len(doc['statements'])==69
    assert len(check.vocabulary()._words)==736
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[104,105] and len(b['source_declarations'])==175
    assert check.author.read(check.BRIDGE)==b
    unit=b['source_units']['einstein-1905:u0044'];assert unit['range']==[0,687]
    assert len(''.join(re.sub(r'\[M\d+\]','',unit['text']).split()))==526
    assert [r['binding'] for r in b['math']]==['zbm','zb7','yn','ra','eiwt','ra','zbm','eiwt','eism5']
    assert check.annotations()['entries'].keys()==check.FORMS.keys()
    assert ds[mapping()['eiwx']]['body']['force']=='direct' and ds[mapping()['eiw2']]['body']['force']=='assert'
    doc=deepcopy(doc);doc['statements'][64]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)

def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]
def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}

def test_reference_acquisition_preserves_inherited_spans_and_does_not_execute_roles():
    doc=deepcopy(check.restored()['document']);n=check.names();speed=cut(Q(3));b=check.BASE|{'zb7':speed}
    for old in (*check.SENTENCES,*check.SPANS,*check.DESIGNATIONS,'zb6','zcj'):
        trial=deepcopy(doc);sort='situation' if old=='zb6' else 'individual'
        trial['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result=sort))
        trial['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:b[old]))==[True]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:b['ri'] if sort=='situation' else 'other'))==[False]
    trial=deepcopy(doc);trial['statements']=[dict(kind='ask',body=dict(kind='apply',function=call(n['zb7']),arguments=[check.author.num(2)]))]
    assert native_run(trial,context(trial,b))==[True]
    trial['statements'][0]['body']['arguments']=[check.author.num(3)]
    assert native_run(trial,context(trial,b))==[False]
    h=check.context_handlers(b)
    assert h['sentencetokenspanreference'](b['eirf'],b['za3'],15,b['contrastsecond'],28,b['ri'])==b['zbb']
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())

def test_scoped_spans_and_unknown_roles_are_rejected():
    from scripts.temporal_discourse_profile import ROLE
    from scripts.rod_experiment_profile import SETTING_ROLE
    from scripts.light_speed_time_profile import ROLE as CUT_ROLE
    b=check.BASE|{'zb7':cut(Q(3))};h=check.context_handlers(b)
    for old,(node,start,end) in check.SPANS.items():
        key=[b['eirf'],b[node],start,b[node],end,b['ri']]
        assert h['sentencetokenspanreference'](*key)==b[old]
        for i in range(6):
            bad=list(key);bad[i]='unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    for bad in (0,-1,61,Q(1,2),True,1.0,'24'):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['zco'],bad,b['zco'],60,b['ri'])
    for role,node,typ,model,expected in [('motionsettingrole','zcg',SETTING_ROLE,check.setting_model(b),b['zb6']),('motionspeedrole','zcg',CUT_ROLE,check.cut_model(b),b['zb7']),('motionhistoryrole','zco',ROLE,check.reference_model(b),b['zcj'])]:
        desc=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()[role])),json.dumps(typ,sort_keys=True,separators=(',',':')),0)
        key=[b['eirf'],b[node],desc,b['ri']];assert model.described(*key)==expected
        for i in (0,1,3):
            bad=list(key);bad[i]='unknown'
            with pytest.raises(ValueError):model.described(*bad)
        for bad in (True,DescriptionValue(desc.syntax,desc.result_type,1),DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()['eiw3'])),desc.result_type,0)):
            with pytest.raises(ValueError):model.described(key[0],key[1],bad,key[3])

def test_role_candidates_and_positive_speed_are_bound_without_circularity():
    assert choice_run('motionsettingrole',['context','discourse'],{'eivx':relation({('context',)}),'zb6':forbidden,'zb7':forbidden})
    assert not choice_run('motionsettingrole',['other','discourse'],{'eivx':relation({('context',)})})
    rows={'zch':{('body','context')}};m={'zch':relation(rows['zch']),'zci':lambda h:'context'}
    choice_perturb(lambda mm:choice_run('motionhistoryrole',['body','discourse'],mm),m,rows)
    assert not choice_run('motionhistoryrole',['body','discourse'],m|{'zci':lambda h:'other'})
    cuts,m=numbers();c=cuts.make
    for speed in (-2,0,3):
        args=[c(Q(speed)),'discourse'];expected=('frame','moving','lengthunit','timeunit','context')
        def velocity(*xs):
            if xs!=expected:forbidden()
            return c(Q(speed))
        assert choice_run('motionspeedrole',args,m|{'zbi':velocity})==(speed>0)
    assert not choice_run('motionspeedrole',[c(Q(4)),'discourse'],m|{'zbi':lambda *xs:c(Q(3))})

def test_whole_native_attribution_and_three_printed_designations():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][64:66];b=check.BASE|{'zb7':cut(Q(3))}
    rows={'eir3':{(b['zcg'],b['rd'],b['eirf'],'eiwx',b['ri']),(b['zco'],b['rd'],b['eirf'],'eiw2',b['ri'])},'ue':{(b['zb5'],b['zcg'],b['ri']),(b['zcg'],b['zco'],b['ri'])}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True,True]
    for n in rows:assert native_run(doc,h|{mapping()[n]:lambda *xs:False})==[False,False]
    trial=deepcopy(check.restored()['document']);trial['statements']=trial['statements'][66:69]
    seen=[]
    h=context(trial,b)|{check.vocabulary()._symbols['printedform']:lambda *xs:seen.append(xs) or True}
    assert native_run(trial,h)==[True,True,True]
    assert {r[0] for r in seen}=={b[n] for n in check.FORMS}
