from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,Content,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_standard_configuration_visible as check
from scripts import standard_configuration_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
HISTORY_DOMAIN=('body','second','origin','otherorigin','guide','otherguide','point','hidden','frame','moving','lengthunit','timeunit','x','y','z','other')
POINTS=('context','other')
DOMAIN=HISTORY_DOMAIN+('author','paper','section','node','heading','designation')
POINTS=('context','discourse','other');SMALL=('a','b')

def forbidden(*args):raise ValueError('Unknown standard-configuration-visible input')
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
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','zbm':'moving','zb4':'context','zb5':'node','eismt':'heading','eiseb':'designation','eisms':'section','eirf':'paper','rd':'author','ri':'discourse'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    selected=NUM|set(constants())|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    if name in {'eiu5','eiu6','eiu7','eiva','eivb','eivc','eivd','eive','eivf','eivg'}:
        selected|={'eigy','eit2'}
        selected.add('eiad' if mode=='native_history' else 'eipw')
        if name in ('eivc','eivd','eive','eivf'):selected.add('eiva')
        if name=='eivf':selected.add('eivc')
        if name=='eivg':selected|={'eivf','eive','eivd'}
    else:
        selected|={'eipw','eigy','eivf','eivg'}
        if mode!='native_history':selected.add('eit2')
        if name=='eivl':selected|={'eivi','eild','eivj','eivk'}
        if name in ('eivq','initialsettingrole'):selected.add('eivl')
    selected.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in selected if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    target=ds[m[name]];slots=[]
    for i,p in enumerate(target['parameters']):
        slot='tripslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='tripcontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('tripcontext'))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,model,mode='boundary',domain=None):
    if domain is None:
        domain=HISTORY_DOMAIN if name in {'eiu5','eiu6','eiu7','eiva','eivb','eivc','eivd','eive','eivf','eivg'} else DOMAIN
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    m=constants()|{'tripcontext':lambda:'discourse'}|model|{n:(lambda x=x:x) for n,x in zip(slots,args)}
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

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown standard-configuration-visible' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                changed=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

def setup(positions=None,members=('guide','point','hidden')):
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

@lru_cache(None)
def numeric_checks():
    cuts,m=numbers();c=cuts.make;count=0
    vectors=((0,0,0),(1,0,0),(-2,0,0),(0,3,0),(1,2,3))
    for u,w in product(vectors,repeat=2):
        cross=(u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0])
        args=[c(Q(x)) for x in u+w]
        assert run('eiu5',args,m)==(cross==(0,0,0));count+=1
        assert run('eiu6',args,m)==(any(u) and any(w) and sum(a*b for a,b in zip(u,w))==0);count+=1
    for root in ('eiu5','eiu6'):
        args=[c(Q(x)) for x in (1,0,0,0,1,0)]
        assert not run(root,args,m|{'ba':lambda x:False});count+=1
        unknowns(lambda mm:run(root,args,mm),m,('ba','bb','shv','sca'))
    return dict(cases=count,zero_displacement_allowed_but_zero_direction_not_perpendicular=True,opposite_directions_and_nonunit_vectors_supported=True)

@lru_cache(None)
def line_checks():
    count=0
    cases=(('straight',{},('guide','point','hidden'),True),('hidden_bend',{'hidden':(-3,1,0)},('guide','point','hidden'),False),('zero_direction',{'guide':(0,0,0)},('guide','point','hidden'),False),('origin_unoccupied',{'point':(1,0,0)},('guide','point','hidden'),False),('guide_not_material',{},('point','hidden'),False),('empty',{},(),False),('opposite_side',{'guide':(-2,0,0)},('guide','point','hidden'),True))
    for label,pos,members,expected in cases:
        cuts,m,_,_=setup(pos,members);args=['body','origin','guide','frame','context',cuts.make(Q(0))]
        assert run('eiu7',args,m)==expected,label;count+=1
    cuts,m,_,_=setup();args=['body','origin','guide','frame','context',cuts.make(Q(0))]
    unknowns(lambda mm:run('eiu7',args,mm),m,('eislu','eirh','ba','sca'))
    assert not run('eiu7',args,m|{'eirh':lambda b,p,ctx:b=='body' and p in ('guide','point','hidden','other') and ctx=='context'});count+=1
    return dict(cases=count,all_members_not_only_two_markers_checked=True,origin_occupied_without_marker_identity=True,nondegenerate_material_direction_required=True)

@lru_cache(None)
def history_checks():
    cuts,m,families,norm=setup();c=cuts.make
    members=FunctionValue(('individual',),'truth',lambda p:p in ('guide','point','hidden'))
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*families]
    origin=['origin','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*(f('origin') for f in families)]
    rows={'eismv':{('body','context')},'eipw':{('body','frame','context')},'eigy':{norm(fields)},'eit2':{norm(origin)},'eisdd':{('frame','lengthunit','timeunit','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda mm:run('eiva',['body','origin','guide','frame','context'],mm)
    count=perturb(check,m,rows,norm)
    unknowns(check,m,('eislu','eisls','eislt'))
    try:run('eiva',['body','origin','guide','frame','context'],m|{'eiad':lambda *xs:True},'native_history')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete static history silently sampled')
    return dict(cases=count,same_complete_material_history_and_geometric_origin=True,all_real_history_refused=True,finite_boundary_function_samples_not_extensional_or_history_proof=True)

@lru_cache(None)
def support_checks():
    count=0;args=['body','origin','guide','second','otherorigin','otherguide','frame','context']
    cases=(('perpendicular',(0,0,0),(0,3,0),(True,False,False)),('same_line_shift',(4,0,0),(1,0,0),(False,True,True)),('parallel_offset',(0,1,0),(2,1,0),(False,True,False)),('same_origin_opposite',(0,0,0),(-4,0,0),(False,True,True)),('oblique',(0,0,0),(1,1,0),(False,False,False)))
    rows={'eiva':{tuple(args[:3]+args[-2:]),tuple(args[3:6]+args[-2:])}}
    for label,o,g,expected in cases:
        _,m,_,_=setup({'otherorigin':o,'otherguide':g});m|={'eiva':relation(rows['eiva'])}
        actual=tuple(run(n,args,m) for n in ('eivc','eivd','eive'));assert actual==expected,(label,actual);count+=3
    _,m,_,_=setup({'otherorigin':(4,0,0),'otherguide':(1,0,0)});m|={'eiva':relation(rows['eiva'])}
    count+=perturb(lambda mm:run('eive',args,mm),m,rows)
    unknowns(lambda mm:run('eive',args,mm),m,('eislu','eisls'))
    return dict(cases=count,support_coincidence_distinct_from_parallelism_and_object_identity=True,shifted_origins_and_reversed_directions_allowed=True,actual_coordinate_directions_used=True)

@lru_cache(None)
def triad_checks():
    cuts,m,_,_=setup();count=0
    lines={'x':'body','y':'second','z':'hidden'}
    rows={'va':{('moving',)},'zbv':{('moving','origin','context')}}
    rows['zbw']={('moving',line,role,'context') for role,line in lines.items()}
    rows['zbr']={(line,'origin','context') for line in lines.values()}
    rows['eiva']={(line,'origin','guide','frame','context') for line in lines.values()}
    rows['eivc']={(lines[a],'origin','guide',lines[b],'origin','guide','frame','context') for a,b in (('x','y'),('x','z'),('y','z'))}
    m|={n:relation(rs) for n,rs in rows.items()}
    m|={'zbn':lambda f,c:'origin','zbo':lambda f,r,c:lines[r] if (f,c)==('moving','context') and r in lines else forbidden(),'eismu':lambda *xs:'guide','eigy':lambda *xs:xs[0] in lines.values() and xs[1:5]==('frame','context','lengthunit','timeunit')}
    count+=perturb(lambda mm:run('eivf',['moving','context'],mm),m,rows)
    for extra in (('moving','other','x','context'),('moving','body','other','context')):
        assert not run('eivf',['moving','context'],m|{'zbw':relation(rows['zbw']|{extra})});count+=1
    assert not run('eivf',['moving','context'],m|{'zbv':relation(rows['zbv']|{('moving','other','context')})});count+=1
    assert not run('eivf',['moving','context'],m|{'eigy':lambda *xs:False});count+=1
    unknowns(lambda mm:run('eivf',['moving','context'],mm),m,('eismu','zbn','zbo','eigy'))
    # Connect native sey with two different origins and three directed pairings.
    linepairs={('frame','x'):'body',('frame','y'):'second',('frame','z'):'hidden',('moving','x'):'point',('moving','y'):'other',('moving','z'):'otherguide'}
    expected=lambda a,b: (a,'origin','guide',b,'otherorigin','guide','frame','context')
    rows={'eivf':{('frame','context'),('moving','context')},'eive':{expected('body','point')},'eivd':{expected('second','other'),expected('hidden','otherguide')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'zbn':lambda f,c:'origin' if f=='frame' else 'otherorigin','zbo':lambda f,r,c:linepairs[f,r],'eismu':lambda *xs:'guide'}
    count+=perturb(lambda mm:run('eivg',['frame','moving','context'],mm),m,rows)
    assert not run('eivg',['frame','frame','context'],{n:lambda *xs:True for n in rows}|{k:v for k,v in m.items() if k not in rows});count+=1
    return dict(cases=count,native_sex_and_sey_connected_to_material_geometry=True,exact_three_axis_roles_and_unique_origin=True,all_three_pairs_and_frame_identity_checked=True)


history_setup=setup

@lru_cache(None)
def exact_checks():
    slots=list(product(SMALL,repeat=3));count=0
    base={'xc':lambda x:x in SMALL,'eismw':relation({('a','b','a','a','context')}),'eismx':relation({('a',f,'a','context') for f in SMALL})}
    for bits in product((False,True),repeat=8):
        rows={(r,f,'a',v,'a','context') for (r,f,v),on in zip(slots,bits) if on}
        sets=lambda r,f:{v for rr,ff,v in slots if rr==r and ff==f and (rr,ff,'a',v,'a','context') in rows}
        expected=all(bool(sets('a',f)) and sets('a',f)==sets('b',f) for f in SMALL)
        assert run('eivi',['a','b','a','context'],base|{'eismy':relation(rows)},domain=SMALL)==expected;count+=1
    rows={'xc':{('a',),('b',)},'eismw':{('a','b','a','a','context')},'eismx':{('a',f,'a','context') for f in SMALL},'eismy':{(r,f,'a','a','a','context') for r,f in product(SMALL,repeat=2)}}
    m={n:relation(rs) for n,rs in rows.items()}
    # A changed feature scope is a different specification, not by itself a
    # mismatch. Its completeness is required separately by eismw.
    count+=perturb(lambda mm:run('eivi',['a','b','a','context'],mm,domain=SMALL),m,{n:rows[n] for n in ('xc','eismw','eismy')})
    assert not run('eivi',['a','b','a','context'],m|{'eismx':lambda *xs:False},domain=SMALL);count+=1
    unknowns(lambda mm:run('eivi',['a','b','a','context'],mm,domain=SMALL),m,('eismx',))
    return dict(cases=count,nonempty_complete_features_and_bidirectional_description_match=True,extra_missing_and_unknown_characteristics_rejected=True)

@lru_cache(None)
def calibration_checks():
    cuts,m,fs,norm=history_setup();c=cuts.make;r=cuts.read
    origin=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*(f('body') for f in fs)]
    rows={'ca':{('body',)},'ci':{('timeunit',)},'eisdf':{('body','context')},'cc':{('body','frame')},'eit2':{norm(origin)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def position(body,frame,lu,tu,axis,ctx):
        if (body,frame,lu,tu,ctx)!=('body','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(axis)]('body')
    m['eismh']=position
    count=perturb(lambda mm:run('eivj',['body','context'],mm,domain=HISTORY_DOMAIN),m,rows,norm)
    unknowns(lambda mm:run('eivj',['body','context'],mm,domain=HISTORY_DOMAIN),m,('eismh','eisls','eislt'))
    try:run('eivj',['body','context'],m|{'eisdd':lambda *xs:True,'zzbg':lambda a,b:r(a)<r(b)},'native_history',HISTORY_DOMAIN)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Representative complete history silently sampled')
    members=FunctionValue(('individual',),'truth',lambda p:p in ('guide','point','hidden'))
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*fs]
    calibration=['body','point','frame','lengthunit','timeunit',c(Q(0)),c(Q(2)),'context']
    rows={'xc':{('body',)},'ti':{('lengthunit',)},'eipw':{('body','frame','context')},'eigy':{norm(fields)},'eisef':{norm(calibration)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eivk',['body','context'],mm,domain=HISTORY_DOMAIN),m,rows,norm)
    alternative=list(calibration);alternative[1]='hidden'
    assert run('eivk',['body','context'],m|{'eisef':lambda *xs:norm(xs)==norm(alternative)},domain=HISTORY_DOMAIN);count+=1
    unknowns(lambda mm:run('eivk',['body','context'],mm,domain=HISTORY_DOMAIN),m,('eislu','eisls','eislt'))
    return dict(cases=count,clock_representative_static_without_freezing_internal_parts=True,ruler_complete_static_rigidity_and_calibrated_scale=True,calibration_method_exists_without_measurement_execution=True,real_history_refused=True)

@lru_cache(None)
def population_checks():
    domain=('a','b','c');cuts,m=numbers();c=cuts.make
    track=FunctionValue((RS,),RS,lambda t:c(Q(0)))
    family=FunctionValue(('individual',),FS,lambda p:track if p in domain else forbidden())
    given={('a','a','context'),('a','b','context'),('b','c','context')}
    rows={'xc':{('a',),('b',)},'ca':{(x,) for x in domain},'zbx':{('a','a','context'),('b','b','context')},'eivi':{('a','b','a','context')},'eild':{(a,b,'a','context') for a,b in product(domain,repeat=2)},'eivk':{('a','context'),('b','context')},'eivj':{(a,'context') for a in domain}}
    m|={n:relation(rs) for n,rs in rows.items()}
    m|={'ra':lambda:'a','ta':lambda:'a','rb':lambda:'b','yn':lambda:'a','yo':lambda:'b','yp':lambda:'c','eirf':lambda:'a','zby':lambda f,ctx:f,'zbz':relation(given),'eirh':lambda *xs:True,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eislu':lambda *xs:family,'eigy':lambda *xs:xs[0] in ('a','b') and xs[1:5]==('a','context','a','b')}
    check=lambda mm:run('eivl',['a','b','context'],mm,domain=domain)
    count=perturb(check,m,rows)
    for empty in ('a','b'):
        assert not check(m|{'zbz':relation({row for row in given if row[0]!=empty})});count+=1
    assert not check(m|{'eigy':lambda *xs:False});count+=1
    assert not check(m|{'zby':lambda *xs:'a'});count+=1
    assert not run('eivl',['a','a','context'],m,domain=domain);count+=1
    # The shared same-specification relation checks every pair, including two
    # clocks in the same group; no reference-clock-only shortcut is used.
    assert not check(m|{'eild':relation(rows['eild']-{('a','b','a','context')})});count+=1
    unknowns(check,m,('zbz','zby','eigy'))
    return dict(cases=count,two_nonempty_groups_and_every_clock_pair=True,same_group_mismatch_not_hidden=True,both_rulers_and_all_clock_qualifications_bound=True)

@lru_cache(None)
def setting_checks():
    rows={'va':{('frame',),('moving',)},'eivf':{('frame','context'),('moving','context')},'eivg':{('frame','moving','context')},'eivl':{('frame','moving','context')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eivq',[],mm),m,rows)
    assert not run('eivq',[],{n:lambda *xs:True for n in rows}|{'zbm':lambda:'frame'});count+=1
    rows={'eisd3':{('node','moving','paper','discourse')},'eismz':{('node','designation','frame','paper','discourse')},'eism2':{('node','author','eivm','eivn','paper','discourse')},'ug':{('node','author','eivq','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eivr',[],mm),m,rows)
    assert run('eivr',[],m|{n:forbidden for n in ('eivq','eivf','eivg','eivl','eivi','eild','se')});count+=1
    rows={'eir3':{('node','author','paper','eivs','discourse')},'ue':{('heading','node','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eivt',[],mm),m,rows)
    assert run('eivt',[],m|{n:forbidden for n in ('ug','eismz','eism2','eisd3','eivq')});count+=1
    return dict(cases=count,three_sentence_conditions_same_initial_context=True,quoted_rest_frame_reference_and_explanatory_reformulation=True,assumption_adoption_and_author_attribution_do_not_execute_physics=True)


def test_profile_and_exact_source_projection():
    voc=check.vocabulary();old=check.previous.vocabulary().document();new=voc.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new[field].get(k)==v for k,v in old[field].items())
    assert len(voc._words)==719
    doc=check.restored()['document'];ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:-1]==check.previous.document()['statements']
    assert all(ds[d['name']]==d for d in check.previous.document()['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==122
    assert check.bridge()['source_statement_indices']==[103]

def test_numeric_directions():assert numeric_checks()['opposite_directions_and_nonunit_vectors_supported']
def test_all_material_points():assert line_checks()['all_members_not_only_two_markers_checked']
def test_complete_history_boundaries():assert history_checks()['all_real_history_refused']
def test_support_line_geometry():assert support_checks()['shifted_origins_and_reversed_directions_allowed']
def test_exact_three_axes_and_corresponding_supports():assert triad_checks()['all_three_pairs_and_frame_identity_checked']
def test_exact_ruler_specifications():assert exact_checks()['nonempty_complete_features_and_bidirectional_description_match']

def test_specification_witness_binding_on_two_values():
    # Binding diagnostics for the standard, feature and description value.
    # This finite carrier does not establish a complete physical specification.
    for standard,feature,description in product(SMALL,repeat=3):
        rows={'xc':{('a',),('b',)},'eismw':{('a','b',standard,'a','context')},
            'eismx':{(standard,feature,'a','context')},
            'eismy':{(r,feature,standard,description,'a','context') for r in SMALL}}
        model={n:relation(rs) for n,rs in rows.items()}
        args=['a','b','a','context']
        assert run('eivi',args,model,domain=SMALL)
        for name in ('eismw','eismx','eismy'):
            assert not run('eivi',args,model|{name:lambda *xs:False},domain=SMALL)
        different='b' if description=='a' else 'a'
        mismatch={(r,feature,standard,description if r=='a' else different,'a','context') for r in SMALL}
        assert not run('eivi',args,model|{'eismy':relation(mismatch)},domain=SMALL)

def test_calibration_and_clock_position():assert calibration_checks()['real_history_refused']
def test_all_clock_pairs():assert population_checks()['same_group_mismatch_not_hidden']
def test_setting_and_explanatory_directive():assert setting_checks()['assumption_adoption_and_author_attribution_do_not_execute_physics']

def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]
def context(doc):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}

def test_reference_acquisition_never_executes_physics_or_introduction():
    doc=deepcopy(check.restored()['document']);n=check.names()
    for old in (*check.SENTENCES,'zb5','zbm','zb4'):
        sort='situation' if old=='zb4' else 'individual'
        trial=deepcopy(doc);trial['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result=sort))
        trial['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        assert native_run(trial,context(trial)|dict(expected=lambda:check.BASE[old]))==[True]
        other=check.BASE['ri'] if sort=='situation' else 'other'
        assert native_run(trial,context(trial)|dict(expected=lambda:other))==[False]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())

def test_connected_native_attribution_and_order():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][63:64]
    b=check.BASE
    rows={'eir3':{(b['zb5'],b['rd'],b['eirf'],'eivs',b['ri'])},'ue':{(b['eismt'],b['zb5'],b['ri'])}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]
    for n in rows:assert native_run(doc,h|{mapping()[n]:lambda *xs:False})==[False]
    ds={d['name']:d for d in doc['declarations']}
    assert ds[mapping()['eivs']]['body']['force']=='direct'

def test_exact_three_sentence_span_and_unknown_references():
    b=check.BASE;h=check.context_handlers(b);span=h['sentencespanreference']
    key=[b['eirf'],b['configfirst'],b['configthird'],b['ri']]
    assert span(*key)==b['zb5']
    for i in range(4):
        bad=list(key);bad[i]='unknown'
        with pytest.raises(ValueError):span(*bad)
    for first,last in [('configthird','configfirst'),('configfirst','configsecond'),('configsecond','configthird')]:
        with pytest.raises(ValueError):span(b['eirf'],b[first],b[last],b['ri'])
    for name,(_,sentence) in check.SENTENCES.items():assert h['sentencereference'](b['ri'],28,sentence)==b[name]
    for bad in (0,-1,4,Q(1,2),True,1.0,'1'):
        with pytest.raises(ValueError):h['sentencereference'](b['ri'],28,bad)
    from scripts.temporal_discourse_profile import ROLE
    from scripts.rod_experiment_profile import SETTING_ROLE
    for name,typ,model,expected in [('secondframerole',ROLE,check.reference_model(b),b['zbm']),('initialsettingrole',SETTING_ROLE,check.setting_model(b),b['zb4'])]:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()[name])),json.dumps(typ,sort_keys=True,separators=(',',':')),0)
        key=[b['eirf'],b['zb5'],role,b['ri']]
        assert model.described(*key)==expected
        for i in (0,1,3):
            bad=list(key);bad[i]='unknown'
            with pytest.raises(ValueError):model.described(*bad)
        for bad in (True,DescriptionValue(role.syntax,role.result_type,1),DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.names()['eivt'])),role.result_type,0)):
            with pytest.raises(ValueError):model.described(key[0],key[1],bad,key[3])

def test_reference_role_conditions_are_independent_of_referents():
    rows={'va':{('moving',)},'eisd3':{('node','moving','paper','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()}
    perturb(lambda mm:run('secondframerole',['moving','discourse'],mm),m,rows)
    assert not run('secondframerole',['frame','discourse'],{n:lambda *xs:True for n in rows})
    rows={'eivf':{('frame','context'),('moving','context')},'eivg':{('frame','moving','context')},'eivl':{('frame','moving','context')}}
    m={n:relation(rs) for n,rs in rows.items()}
    perturb(lambda mm:run('initialsettingrole',['context','discourse'],mm),m,rows)
    assert not run('initialsettingrole',['other','discourse'],m)
    # Role depends on its candidate situation, never the reference zb4 itself.
    assert run('initialsettingrole',['context','discourse'],m|{'zb4':forbidden})

def test_source_scope_and_changed_evidence_rejected():
    b=check.bridge();unit=b['source_units']['einstein-1905:u0043']
    assert unit['range']==[0,441] and len(''.join(re.sub(r'\[M\d+\]','',unit['text']).split()))==361
    assert b['text_span']==['configfirst','configthird']
    assert b['sentence_coordinates']==dict(configfirst=[28,1],configsecond=[28,2],configthird=[28,3])
    assert check.author.read(check.BRIDGE)==b
    assert [row['binding'] for row in b['math']]==['yn','yo','yp']
    doc=deepcopy(check.restored()['document']);doc['statements'][63]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
