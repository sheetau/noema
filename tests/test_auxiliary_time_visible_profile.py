from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_auxiliary_time_visible as check
from scripts import auxiliary_time_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
VS=dict(kind='function',parameters=['individual'],result=RS)
MS=dict(kind='function',parameters=['individual','individual'],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
ROLES=('x','y','z','time')
POINTS=('context','discourse','other')
CONSTANTS={'ra':'frame','zbm':'moving','ta':'lengthunit','rb':'unit','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdf':'previous','zdb':'task','zdj':'introduction','zdk':'invariance','zdl':'tautask','zdp':'purpose','eisdy':'firstsection'}
DOMAIN=tuple(dict.fromkeys(['point','moment','othermoment','event','place','clock','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')

def forbidden(*args):raise ValueError('Unknown auxiliary-time-visible input')
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

def project(node,sorts):
    if any(node==s for s in sorts):return 'individual'
    if isinstance(node,dict):return {k:project(v,sorts) for k,v in node.items()}
    if isinstance(node,list):return [project(v,sorts) for v in node]
    return node

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    boundaries=NUM|set(CONSTANTS)|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    if name=='eizm':boundaries|={'eit2','eivw'}
    if name=='eizn':boundaries|={'sb','eixu','lg'}
    if name=='eizo':boundaries.add('eizn')
    if name=='eizp':boundaries|={'eivz','eizm','eizo','eiwi','sil','lg'}
    if name=='eizq':boundaries.add('eizp')
    if name in ('eizu','eizv'):boundaries|={'eiy3','eiyz','eiy2','eiyy'}
    if name=='eizz':boundaries|={'eizu','eiyf','eiyx','eiyg','sin'}
    boundaries.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in boundaries if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    if mode=='projection':doc=project(doc,[RS])
    target=next(d for d in doc['declarations'] if d['name']==m[name]);slots=[]
    if name=='eizv':
        sort=target['result']['parameters'][0]
        doc['declarations'].append(dict(kind='primitive',name='jatcandidate',parameters=[],result=sort))
        doc['statements']=[dict(kind='ask',body=dict(kind='answer_matches',question=call(m[name]),arguments=[call('jatcandidate')]))]
        return doc,['jatcandidate']
    for i,p in enumerate(target['parameters']):
        slot='auxiliaryslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='auxiliarycontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('auxiliarycontext'))
    elif target['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jatcapture',parameters=[target['result']],result='truth'))
        body=call('jatcapture',body)
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,model,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    m={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'auxiliarycontext':lambda:'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    h=handlers(doc);h.update({mapping().get(n,n):f for n,f in m.items() if mapping().get(n,n) in h})
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives=h,max_steps=1500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown auxiliary-time-visible' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('wrong' if i==j else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

def wrap(sort,fn):return FunctionValue(tuple(sort['parameters']),sort['result'],fn)
def vector(c,values):return FunctionValue(('individual',),RS,lambda a:c(Q(values[ROLES.index(a)])))
def typed_arguments(name,implementations,mode='boundary'):
    doc,slots=fixture(name,mode);decls={d['name']:d for d in doc['declarations']}
    return [wrap(decls[n]['result'],fn) if callable(fn) else fn for n,fn in zip(slots,implementations,strict=True)]
def reject_full(check):
    try:check()
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Full function quantification silently sampled')

def norm_factory(cuts,times):
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return cuts.read(x)
            if x.result==RS:return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            forbidden()
        return tuple(one(x) for x in xs)
    return norm



def history_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,2));axes=('x','y','z')
    tracks={a:FunctionValue((RS,),RS,lambda t,i=i:c(Q(7+i))) for i,a in enumerate(axes)}
    def raw(p,f,lu,tu,a,ctx):
        if (p,f,lu,tu,ctx)!=('point','moving','lengthunit','unit','context') or a not in tracks:forbidden()
        return tracks[a]
    rows={'eit2':{norm(['point','moving','context','lengthunit','unit',c(Q(4)),c(Q(6)),*tracks.values()])},'eivw':{('point','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};m|={'eismh':raw,'eisls':lambda *xs:c(Q(4)),'eislt':lambda *xs:c(Q(6))}
    check=lambda mm:run('eizm',['point','context'],mm);count=perturb(check,m,rows,norm)
    unknowns(check,m,('eismh','eisls','eislt'));assert check(m|{'eipw':forbidden});count+=1
    return dict(cases=count,own_frame_static_and_same_K_translation_both_required=True,complete_representative_not_material_internals=True)

def test_history_checks():assert history_checks()

def event_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,());axes=('x','y','z')
    times={'frame':Q(1),'moving':Q(5)};values={'frame':(4,5,6),'moving':(7,8,9)}
    bounds={'frame':(0,2),'moving':(4,6)}
    def raw(p,f,lu,tu,a,ctx):
        if (p,lu,tu,ctx)!=('point','lengthunit','unit','context') or f not in times or a not in axes:forbidden()
        val=values[f][axes.index(a)]
        return FunctionValue((RS,),RS,lambda t:c(Q(val)+(2*(r(t)-1) if f=='frame' and a=='x' else 0)))
    rows={'zce':{('point','moment','frame','lengthunit','context')},'zcf':{('moment','frame','unit','context'),('othermoment','moving','unit','context')},'zbd':{('event',)},'cb':{('event','place','frame')},'eisnk':{('event','moment','frame','context'),('event','othermoment','moving','context')},'sb':{('point','event',f,'context','lengthunit','unit',t,*map(Q,values[f])) for f,t in times.items()},'eixu':{('place','frame',a,Q(values['frame'][i]),'context') for i,a in enumerate(axes)},'lg':{(*map(Q,bounds[f]),t) for f,t in times.items()}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'eismh':raw,'eisls':lambda f,*xs:c(Q(bounds[f][0])),'eislt':lambda f,*xs:c(Q(bounds[f][1])),'yl':lambda mo,f,u,ctx:c(times[f]),'ym':lambda p,mo,f,u,a,ctx:c(Q(values[f][axes.index(a)]))}
    args=['point','moment','event','place','othermoment','context'];check=lambda mm:run('eizn',args,mm)
    count=perturb(check,m,rows,norm);unknowns(check,m,('eismh','ym','yl','eisls','eislt','ba','sca'))
    for axis in axes:
        assert not check(m|{'ym':lambda p,mo,f,u,a,ctx,axis=axis:c(Q(values[f][axes.index(a)]+(1 if a==axis else 0)))});count+=1
    assert check(m|{'eiyi':forbidden,'eiyg':forbidden});count+=1
    return dict(cases=count,same_point_event_and_frame_specific_moments_bound=True,all_three_actual_spatial_measurements_and_tracks_required=True,unequal_t_and_tau_allowed_without_K_clock_at_every_point=True)

def test_event_checks():assert event_checks()

def quantifier_checks():
    small=('a','b');count=0
    for row in product(small,repeat=5):
        check=lambda mm:run('eizo',[*row[:2],'context'],mm,domain=small)
        m={'eizn':relation({(*row,'context')})};assert check(m);count+=1
        assert not check({'eizn':lambda *xs:False});count+=1
        for i in (0,1):
            wrong=list(row[:2]);wrong[i]='a' if wrong[i]=='b' else 'b'
            assert not run('eizo',[*wrong,'context'],m,domain=small);count+=1
        assert not run('eizo',[*row[:2],'other'],m,domain=small);count+=1
    rows={'eivz':{('context',)},'eizm':{(p,'context') for p in small},'eizo':{(p,t,'context') for p,t in product(small,repeat=2)},'eiwi':{(t,'context') for t in small},'sil':{('context',)}}
    m={n:relation(rs) for n,rs in rows.items()}|{'ra':lambda:'a','zbm':lambda:'b','rb':lambda:'b','zdi':lambda p,ctx:ctx=='context','x4':lambda p,f,ctx:(f,ctx)==('b','context'),'eisk7':lambda f,p,ctx:(f,ctx)==('b','context'),'ys':lambda t,ctx:ctx=='context','eisla':lambda f,g,t,ctx:(f,g,ctx)==('a','b','context'),'eisls':lambda *xs:'a','eislt':lambda *xs:'b','lg':lambda lo,hi,t:(lo,hi)==('a','b')}
    check=lambda mm:run('eizp',['context'],mm,'projection',small);count+=perturb(check,m,rows)
    for p in small:
        for name,fn in [('zdi',lambda x,ctx,p=p:x!=p),('x4',lambda x,f,ctx,p=p:x!=p),('eisk7',lambda f,x,ctx,p=p:x!=p),('ys',lambda x,ctx,p=p:x!=p),('eisla',lambda f,g,x,ctx,p=p:x!=p)]:
            assert not check(m|{name:fn});count+=1
    unknowns(check,m,('zdi','x4','eisk7','ys','eisla','lg','eisls','eislt'))
    cuts,n=numbers();native=m|n|{'eisls':lambda *xs:cuts.make(Q(0)),'eislt':lambda *xs:cuts.make(Q(2)),'lg':lambda *xs:True}
    reject_full(lambda:run('eizp',['context'],native,domain=small));count+=1
    return dict(cases=count,existential_every_slot_checked_on_two_individuals=True,all_points_times_and_real_time_coverage_preserved=True,native_infinite_time_domain_refused=True)

def test_quantifier_checks():assert quantifier_checks()

def candidate_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;axes=('x','y','z','time');domain=('a','b','c','d','frame','moving','lengthunit','unit',*axes)
    # Nonmember tuples have explicitly known irrelevant values because logical
    # implication is eager; this is not a fallback for unknown external input.
    values={t:(0,0,0,0) for t in domain}|{'a':(7,2,3,1),'b':(11,-2,4,3),'c':(80,90,100,17),'d':(110,120,130,10)}
    graph={('a','c'),('b','d')};speed=Q(2)
    m|={'eiy3':lambda:Content(POINTS,(True,True,True)),'eiyz':lambda t:t in ('a','b'),'eiy2':lambda t:t in ('c','d'),'eiyy':lambda a,b:(a,b) in graph,'zc6':lambda t,a:c(Q(values[t][axes.index(a)])),'zb7':lambda:c(speed),'zbi':lambda *xs:c(speed)}
    # Both tuples have x'=5, but different y,z,t. All four arguments matter.
    formula=lambda xp,y,z,t:xp+2*y+3*z-t
    good=FunctionValue((RS,)*4,RS,lambda *xs:c(formula(*map(r,xs))))
    count=0
    for name in ('eizu','eizv'):
        check=lambda mm:run(name,[good],mm,domain=domain)
        assert check(m);count+=1
        for patch in ({'eiy3':lambda:Content(POINTS,(False,True,True))},{'zbi':lambda *xs:c(Q(3))},{'ba':lambda x:r(x)!=10}):assert not check(m|patch);count+=1
        for role in axes:
            changed=dict(values);changed['d']=tuple(x+(1 if a==role else 0) for x,a in zip(changed['d'],axes))
            actual=check(m|{'zc6':lambda t,a,vs=changed:c(Q(vs[t][axes.index(a)]))})
            assert actual==(role!='time');count+=1
        for slot in range(4):
            wrong=FunctionValue((RS,)*4,RS,lambda *xs,slot=slot:c(formula(*(r(x)+(1 if i==slot else 0) for i,x in enumerate(xs)))))
            assert not run(name,[wrong],m,domain=domain);count+=1
        # Swapping source x with the moving measured xi cannot satisfy this example.
        assert not check(m|{'zc6':lambda t,a:c(Q(80 if t=='a' and a=='x' else values[t][axes.index(a)]))});count+=1
        unknowns(check,m,('eiy3','eiyz','eiy2','eiyy','zc6','zb7','zbi','ba','sca','bf','shv'))
    return dict(cases=count,native_x_minus_vt_and_all_four_arguments_checked=True,current_same_event_coordinate_graph_and_both_tuples_required=True,moving_xi_not_substituted_for_auxiliary_x=True,question_has_same_candidate_condition=True)

def test_candidate_checks():assert candidate_checks()

def clock_totality_checks():
    small=('a','b');candidate=FunctionValue(('individual',)*4,'individual',lambda xp,y,z,t:xp)
    # Explicit sort projection for the quantifier skeleton only. Numeric inputs
    # and the native clock body are checked separately and pinned dependencies.
    m={'ra':lambda:'a','zbm':lambda:'b','yn':lambda:'a','yo':lambda:'b','yp':lambda:'b','zc7':lambda:'a','zb7':lambda:'b','sin':lambda speed,x,t:x,'zc6':lambda first,role:first,'eizu':lambda f:all(f(x,'b','b','a')==x for x in small),'eiyf':lambda f,ctx:(f,ctx)==('b','context'),'zc4':lambda e:e in small,'eiyx':lambda e,t,f,ctx:e==t and (f,ctx)==('a','context'),'zcz':lambda e,f,ctx:(f,ctx)==('b','context'),'zbz':lambda f,cl,ctx:(f,ctx)==('b','context'),'cb':lambda obj,p,f:p=='a' and f=='b','ba':lambda x:x in small,'sca':lambda a,b:a==b,'eiyg':lambda e,cl,p,f,val,ctx:val==e and (p,f,ctx)==('a','b','context')}
    check=lambda mm:run('eizz',[candidate],mm,'projection',small);assert check(m);count=1
    for e,cl in product(small,repeat=2):
        base=m['eiyg']
        assert not check(m|{'eiyg':lambda ev,clock,p,f,val,ctx,e=e,cl=cl:base(ev,clock,p,f,val,ctx) and (ev,clock)!=(e,cl)});count+=1
        assert not check(m|{'eiyg':lambda ev,clock,p,f,val,ctx,e=e,cl=cl:base(ev,clock,p,f,val,ctx) or ((ev,clock)==(e,cl) and val!=e)});count+=1
    for name in ('eizu','eiyf'):
        assert not check(m|{name:lambda *xs:False});count+=1
    # Include both places: failure at the added place must now count.
    assert not check(m|{'cb':lambda obj,p,f:f=='b'});count+=1
    # No claim at a place with no deployed local clock; nonmembers are excluded.
    assert check(m|{'zbz':lambda f,cl,ctx:cl=='a' and (f,ctx)==('b','context'),'eiyg':lambda e,cl,p,f,val,ctx:cl=='a' and m['eiyg'](e,cl,p,f,val,ctx)});count+=1
    unknowns(check,m,('eizu','eiyf','zc4','eiyx','zcz','zbz','cb','eiyg','zc6','sin','ba','sca'))
    cuts,n=numbers();c=cuts.make
    native=m|n|{'zb7':lambda:c(Q(1)),'zc6':lambda *xs:c(Q(1)),'sin':lambda *xs:c(Q(1)),'eizu':lambda f:True,'eiyg':lambda *xs:True}
    fn=FunctionValue((RS,)*4,RS,lambda *xs:c(Q(1)))
    reject_full(lambda:run('eizz',[fn],native,domain=small));count+=1
    return dict(cases=count,all_events_local_clocks_and_values_required=True,extra_readings_rejected_not_only_candidate_existence=True,unclocked_places_and_nonmembers_not_added=True,projection_not_a_finite_semantic_judgment_of_all_reals=True)

def test_clock_totality_checks():assert clock_totality_checks()

def presentation_checks():
    rows={'zdm':{('introduction','author','sin','section','discourse')},'uh':{('invariance','author','eizq','section','discourse')},'zdg':{('invariance','author','eizq','section','discourse')},'ue':{('introduction','invariance','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eizr',[],mm),m,rows)
    assert run('eizr',[],m|{n:forbidden for n in ('sin','eizq','eizp','sil')});count+=1
    rows={'zdn':{('tautask','author','task','eizv','section','discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eizw',[],mm),m,rows)
    rows={'zdo':{('purpose','author','eizz','tautask','section','discourse')},'eislp':{('purpose','author','firstsection','eiyo','paper','discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiz2',[],mm),m,rows)
    assert run('eiz2',[],m|{n:forbidden for n in ('eizz','eiyg','eiyf','eiyo')});count+=1
    for name,node,message,previous in (('eizt','introduction','eizs','previous'),('eizy','tautask','eizx','invariance'),('eiz4','purpose','eiz3','tautask')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
    return dict(cases=count,adoption_obviousness_first_subtask_purpose_and_section_one_bound=True,quoted_physical_content_and_questions_not_executed=True,three_sentence_author_order_preserved=True)

def test_presentation_checks():assert presentation_checks()

def test_source_profile_and_saved_bridge():
    doc=check.restored()['document'];prior=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:80]==prior['statements']
    assert all(ds[d['name']]==d for d in prior['declarations'])
    assert len(doc['declarations'])==1379 and len(doc['statements'])==83 and len(check.vocabulary()._words)==753
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[110,111,112] and len(b['source_declarations'])==257
    unit=b['source_units']['einstein-1905:u0048'];assert unit['range']==[0,437]
    assert len(''.join(re.sub(r'\[M\d+\]','',unit['text']).split()))==314
    assert len(b['math'])==8 and b['text_boundaries']['spans']=={'zdk':['zdj',4,22]}
    assert [len(r['tokens']) for r in b['text_boundaries']['sentences'].values()]==[22,10,36]
    for name in ('eizs','eizx','eiz3'):assert ds[mapping()[name]]['body']['force']=='assert'
    assert ds[mapping()['eizv']]['result']['kind']=='question'
    assert set(profile.SOURCE_RELATIONS)=={'zdi','zdm','zdn','zdo'}
    changed=deepcopy(doc);changed['statements'][80]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(changed)

def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]
def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}

def test_reference_scopes_and_inherited_names():
    doc=deepcopy(check.restored()['document']);n=check.names();b=check.BASE|{'zb7':cut(Q(3))}
    for old in (*check.SENTENCES,*check.SPANS):
        trial=deepcopy(doc);trial['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
        trial['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:b[old]))==[True]
        assert native_run(trial,context(trial,b)|dict(expected=lambda:'other'))==[False]
    h=check.context_handlers(b)
    assert h['sentencetokenspanreference'](b['eirf'],b['zdf'],12,b['zdf'],18,b['ri'])==b['zde']
    assert h['designationreference'](b['eirf'],b['zc3'],1,b['ri'])==b['eisnl']
    assert h['sentencetokenspanreference'](b['eirf'],b['zco'],24,b['zco'],60,b['ri'])==b['zcp']
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())


def test_invariance_span_rejects_changed_endpoints_and_unknown_inputs():
    b=check.BASE|{'zb7':cut(Q(3))};h=check.context_handlers(b)
    key=[b['eirf'],b['zdj'],4,b['zdj'],22,b['ri']]
    assert h['sentencetokenspanreference'](*key)==b['zdk']
    for slot in range(6):
        bad=key.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    for bad in (0,-1,1,3,5,23,Q(1,2),True,4.0,'4'):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['zdj'],bad,b['zdj'],22,b['ri'])
    for end in (3,21,23):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['zdj'],4,b['zdj'],end,b['ri'])

def test_whole_attribution_preserves_three_sentences_without_execution():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][80:83];b=check.BASE|{'zb7':cut(Q(3))}
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('zdj','eizs'),('zdl','eizx'),('zdp','eiz3'))},
        'ue':{(b[first],b[last],b['ri']) for first,last in (('zdf','zdj'),('zdk','zdl'),('zdl','zdp'))}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]*3
    for n,rs in rows.items():
        for row in rs:
            result=native_run(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==2

def test_actual_auxiliary_numeric_kernel_and_selected_component():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    for speed,x,t in ((2,7,3),(-2,7,3),(Q(1,2),Q(-3,2),Q(1,3))):
        expected=Q(x)-Q(speed)*Q(t)
        model=m|{'jatcapture':lambda result:r(result)==expected}
        args=[c(Q(v)) for v in (speed,x,t)]
        assert run('sin',args,model)
        unknowns(lambda mm:run('sin',args,mm),model,('bf','shv'))
    # Evaluate the actual composed cut at fixed rational probes. This is a
    # distinguishing diagnostic, not recovery of an arbitrary cut's value.
    probes=tuple(Q(v) for v in (-1,0,1,2,4,5,6,7,10))
    coords={'x':7,'y':5,'z':6}
    def measured(p,mo,f,u,a,ctx):
        if (p,mo,f,u,ctx)!=('point','moment','frame','lengthunit','context'):forbidden()
        return c(Q(coords[a]))
    def time(mo,f,u,ctx):
        if (mo,f,u,ctx)!=('moment','frame','unit','context'):forbidden()
        return c(Q(3))
    for role,want in (('x',1),('y',5),('z',6)):
        args=typed_arguments('sij',['point','moment',role,'context',m['bf'],m['shv']])
        model=m|{'ym':measured,'yl':time,'zb7':lambda:c(Q(2)),
            'jatcapture':lambda result,want=want:all(result(q)==(q<want) for q in probes)}
        assert run('sij',args,model)
        unknowns(lambda mm:run('sij',args,mm),model,('ym','yl','zb7'))

def test_actual_invariance_kernel_checks_all_points_times_and_components():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    domain=('p','q','first','middle','last','x','y','z');times={'first':0,'middle':1,'last':2}
    scenarios=['baseline','different_point_values','empty_points','empty_times','no_width','missing_middle','duplicate_axes']
    scenarios += [f'change_{p}_{axis}' for p in ('p','q') for axis in ('x','y','z')]
    for scenario in scenarios:
        def coordinate(p,mo,axis):
            # Complete explicit finite fixture; nonmembers have irrelevant zero.
            value=(3 if p=='p' else 9 if p=='q' else 0)+(2 if axis=='y' else 4 if axis=='z' else 0)
            if scenario==f'change_{p}_{axis}' and mo=='middle':value+=1
            return c(Q(value))
        implementations=[lambda p:p in ('p','q') and scenario!='empty_points',
            lambda mo:mo in times and scenario!='empty_times',
            SequenceValue(('x','x','z') if scenario=='duplicate_axes' else ('x','y','z'),'"individual"'),
            lambda p,mo:not(scenario=='missing_middle' and (p,mo)==('q','middle')),
            lambda first,last:scenario!='no_width' and first in times and last in times and times[first]<times[last],
            coordinate,lambda a,b:r(a)==r(b)]
        args=typed_arguments('sih',implementations)
        assert run('sih',args,m,domain=domain)==(scenario in ('baseline','different_point_values'))
