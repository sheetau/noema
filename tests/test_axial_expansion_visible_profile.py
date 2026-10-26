from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_axial_expansion_visible as check
from scripts import axial_expansion_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
VS=dict(kind='function',parameters=['individual'],result=RS)
MS=dict(kind='function',parameters=['individual','individual'],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
ROLES=('x','y','z','time')
POINTS=('context','discourse','other')
CONSTANTS={'ra':'frame','zbm':'moving','ta':'lengthunit','rb':'unit','rc':'reference','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdq':'trial','zdr':'firstclock','zds':'secondclock','zdu':'setup','zdv':'inference','zdp':'purpose','zdx':'outward','zdy':'returning','zd2':'expansion'}
EVENTS=('depart','reflection','arrival');TUPLES=('tuplea','tupleb','tuplec');CLOCKS=('locala','localb','localc');PLACES=('placea','placeb','placec')
DOMAIN=tuple(dict.fromkeys([*EVENTS,*TUPLES,*CLOCKS,*PLACES,'tuple','origin','mirror','ray','axis','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')

def forbidden(*args):raise ValueError('Unknown axial-expansion-visible input')
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
    boundaries|={'bj','sje'}
    if name in ('eiz5','ei2k','ei2l'):boundaries.add('eiyx')
    if name=='eiz6':boundaries.add('eiz5')
    if name=='eiz7':boundaries|={'eiyg','eiyi','eiyj'}
    if name=='ei2a':boundaries|={'eiz7','qo'}
    if name=='ei2b':boundaries|={'eixt','eiyf','eiy3','ei2a','eizm','eiz6'}
    if name=='ei2c':boundaries.add('ei2b')
    if name=='qo':boundaries|={'da','bi'}
    if name=='ei2m':boundaries|={'eifw','eior','eiyg','eiyi','eiyj'}
    if name=='ei2n':boundaries|={'ei2m','se'} if mode=='paths' else {'ei2m','eiti'}
    if name=='ei2o':boundaries.add('eizz')
    if name=='ei2p':boundaries|={'ei2b','ei2l','eios','eiyf','ei2n','ei2o'}
    if name=='ei2q':boundaries.add('ei2p')
    if name.startswith('axialrole'):boundaries|={'ei2a','eiz6','ei2m','eizv'}
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
        except ValueError as e:assert 'Unknown axial-expansion-visible' in str(e),str(e)
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


def norm_factory(cuts,times):
    # Exact registered cuts only. History fingerprints are finite binding
    # diagnostics, not a proof of equality on all real inputs.
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return cuts.read(x)
            if list(x.parameters)==[RS] and x.result==RS:
                return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            forbidden()
        return tuple(one(x) for x in xs)
    return norm

def axial_run(name,args,m,domain=DOMAIN):return run(name,args,m,domain=domain)

def exact_numbers():
    cuts,m=numbers();m['bj']=lambda scale,val:cuts.make(scale*cuts.read(val));return cuts,m

@lru_cache(None)
def label_checks():
    cuts,m=exact_numbers();c=cuts.make;r=cuts.read;rows={'eiyx':{('reflection','tuple','frame','context')}}
    m|={n:relation(rs) for n,rs in rows.items()};m['zb7']=lambda:c(Q(2));coords={'x':Q(7),'y':Q(5),'z':Q(-4),'time':Q(3)}
    def coordinate(t,a):
        if t!='tuple' or a not in coords:forbidden()
        return c(coords[a])
    m['zc6']=coordinate;args=['reflection','tuple',c(Q(1)),'context'];check=lambda mm:axial_run('eiz5',args,mm)
    count=perturb(check,m,rows);unknowns(check,m,('zc6','zb7','ba','sca','bf','shv'))
    for label in (-3,0,1,4):
        expected=Q(label);mm=m|{'zc6':lambda t,a,label=label:c(Q(label+6) if a=='x' else coords[a])}
        assert axial_run('eiz5',['reflection','tuple',c(expected),'context'],mm);count+=1
    for patch in ({'zb7':lambda:c(Q(3))},{'zc6':lambda t,a:c(coords[a]+(1 if a=='time' else 0))},{'zc6':lambda t,a:c(Q(80) if a=='x' else coords[a])},{'ba':lambda x:False}):assert not check(m|patch);count+=1
    # y,z are not zeroed merely because the trial is longitudinal.
    assert check(m|{'zc6':lambda t,a:c(Q(100) if a in ('y','z') else coords[a])});count+=1
    small=('a','b')
    for event,tup,label in product(small,small,(0,1)):
        norm=norm_factory(cuts,());target=(event,tup,Q(label),'context')
        mm={'eiz5':lambda *xs,target=target:norm(xs)==target}
        assert axial_run('eiz6',[event,c(Q(label)),'context'],mm,small);count+=1
        assert not axial_run('eiz6',[event,c(Q(1-label)),'context'],mm,small);count+=1
        assert not axial_run('eiz6',['a' if event=='b' else 'b',c(Q(label)),'context'],mm,small);count+=1
        assert not axial_run('eiz6',[event,c(Q(label)),'other'],mm,small);count+=1
        assert not axial_run('eiz6',[event,c(Q(label)),'context'],{'eiz5':lambda *xs:False},small);count+=1
    return dict(cases=count,same_event_K_tuple_and_x_minus_vt_required=True,negative_zero_and_nonzero_labels_allowed_without_origin_choice=True,existential_all_slots_distinguished_on_two_individuals=True)

@lru_cache(None)
def local_checks():
    cuts,m=exact_numbers();c=cuts.make;norm=norm_factory(cuts,())
    rows={'zc4':{('reflection',)},'zcz':{('reflection','moving','context')},'eiyg':{('reflection','secondclock','mirror','moving',Q(4),'context')},'eiyi':{('reflection','mirror','moving','context')},'eiyj':{('reflection','moving','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def stamp(e,f,u,ctx):
        if (e,f,u,ctx)!=('reflection','moving','unit','context'):forbidden()
        return c(Q(4))
    m['zbe']=stamp;args=['reflection','secondclock','mirror',c(Q(4)),'context'];check=lambda mm:axial_run('eiz7',args,mm)
    count=perturb(check,m,rows,norm);unknowns(check,m,('zbe','sca'))
    assert not axial_run('eiz7',args[:3]+[c(Q(3)),'context'],m);count+=1
    assert not check(m|{'zbe':lambda *xs:c(Q(3))});count+=1
    return dict(cases=count,same_local_display_unique_time_and_frame_moment_required=True,stationary_time_cannot_replace_tau=True)

def trial_model():
    cuts,m=exact_numbers();c=cuts.make;norm=norm_factory(cuts,());events=('depart','reflection','arrival');readings=(Q(2),Q(4),Q(6))
    locations={('firstclock','origin','moving'),('secondclock','mirror','moving'),('depart','origin','moving'),('reflection','mirror','moving'),('arrival','origin','moving')}
    legs={('ray','depart','reflection','moving'),('ray','reflection','arrival','moving')}
    rows={'qb':{('firstclock','secondclock','moving','unit','context','trial')},'zbv':{('moving','origin','context')},'zbw':{('moving','axis','x','context')},'zbz':{('moving',cl,'context') for cl in ('firstclock','secondclock')},'zcu':{(p,'moving','context') for p in ('origin','mirror')},'ca':{('firstclock',),('secondclock',)},'cd':{('firstclock','secondclock')},'cc':{(cl,'moving') for cl in ('firstclock','secondclock')},'cb':locations,'ci':{('unit',)},'cf':{('ray',)},'cg':legs,'ch':{('ray','reflection','moving')},'ce':{(cl,e,'moving','unit',val) for e,cl,val in zip(events,('firstclock','secondclock','firstclock'),readings)},'qo':{('firstclock','secondclock','moving','unit','context')},'zdw':{(ray,a,b,'axis',f,'context') for ray,a,b,f in legs},'eiz7':{(e,cl,p,val,'context') for e,cl,p,val in zip(events,('firstclock','secondclock','firstclock'),('origin','mirror','origin'),readings)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    values={'qc':'origin','qd':'mirror','qe':'depart','qf':'reflection','qg':'arrival','qh':'ray','qi':c(Q(2)),'qj':c(Q(4)),'qk':c(Q(6))}
    def getter(name):
        def get(trial):
            if trial!='trial':forbidden()
            return values[name]
        return get
    m|={n:getter(n) for n in values}
    def origin(f,ctx):
        if (f,ctx)!=('moving','context'):forbidden()
        return 'origin'
    def axis(f,a,ctx):
        if (f,a,ctx)!=('moving','x','context'):forbidden()
        return 'axis'
    m|={'zbn':origin,'zbo':axis}
    return cuts,m,rows,norm

@lru_cache(None)
def trip_checks():
    cuts,m,rows,norm=trial_model();c=cuts.make;args=['trial','firstclock','secondclock','context'];check=lambda mm:axial_run('ei2a',args,mm)
    count=perturb(check,m,rows,norm)
    unknowns(check,m,('qc','qd','qe','qf','qg','qh','qi','qj','qk','zbn','zbo','bg'))
    for patch in ({'qg':lambda tr:'depart'},{'qd':lambda tr:'origin'},{'zbn':lambda *xs:'mirror'},{'qk':lambda tr:c(Q(1))},{'qj':lambda tr:c(Q(2))}):assert not check(m|patch);count+=1
    assert check(m|{'sgp':forbidden,'shc':forbidden,'siw':forbidden});count+=1
    return dict(cases=count,native_da_sde_same_ray_three_events_and_A_B_A_clock_roles=True,both_complete_axial_paths_required=True,selected_trial_sync_scope_and_strict_reading_order_preserved=True,legacy_local_time_and_origin_zero_rules_not_used=True)

@lru_cache(None)
def connection_checks():
    cuts,m=exact_numbers();c=cuts.make;norm=norm_factory(cuts,())
    rows={'eixt':{('context',)},'eiyf':{('moving','context')},'ei2a':{('trial','firstclock','secondclock','context')},'eizm':{('origin','context'),('mirror','context')},'eiz6':{('reflection',Q(-2),'context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def selected(value):
        return lambda tr:value if tr=='trial' else forbidden()
    m|={'eiy3':lambda:Content(POINTS,(True,True,True)),'qc':selected('origin'),'qd':selected('mirror'),'qf':selected('reflection'),'zdt':lambda:c(Q(-2))}
    check=lambda mm:axial_run('ei2b',[],mm);count=perturb(check,m,rows,norm)
    assert not check(m|{'eiy3':lambda:Content(POINTS,(False,True,True))});count+=1
    unknowns(check,m,('eiy3','qc','qd','qf','zdt'))
    for truth in (False,True):assert axial_run('ei2c',[],{'ei2b':lambda truth=truth:truth})==truth;count+=1
    return dict(cases=count,current_geometry_all_clocks_and_same_event_coordinate_graph_required=True,both_endpoints_own_rest_and_same_K_translation_required=True,assumed_content_and_setup_agree=True)

@lru_cache(None)
def midpoint_checks():
    cuts,m=exact_numbers();c=cuts.make;r=cuts.read;count=0;out={}
    for name,vals,want in [('ordinary',(2,4,6),True),('shifted',(-4,-2,0),True),('fractional',(Q(1,3),Q(2,3),1),True),('wrong_middle',(2,3,6),False),('wrong_return',(2,4,7),False),('reversed',(6,4,2),True),('coincident',(4,4,4),True)]:
        args=[c(Q(v)) for v in vals];assert axial_run('sit',args,m)==want;count+=1
        mm=m|{n:lambda tr,val=Q(val):c(val) if tr=='trial' else forbidden() for n,val in zip(('qi','qj','qk'),vals)}
        assert axial_run('ei2d',[],mm)==want;count+=1;out[name]=want
    args=[c(Q(v)) for v in (2,4,6)];assert not axial_run('sit',args,m|{'ba':lambda x:r(x)!=4});count+=1
    unknowns(lambda mm:axial_run('sit',args,mm),m,('ba','sca','bd','bj'))
    # Both occurrences of the reflection value in the doubled form remain the
    # same value. The displayed form has a literal 1/2, not an inferred order.
    assert not axial_run('sit',args,m|{'bj':lambda scale,val:c(r(val))});count+=1
    return dict(cases=count,outcomes=out,native_displayed_half_sum_checked_on_exact_rationals=True,formula_reuses_selected_trial_readings=True,midpoint_alone_does_not_imply_chronology=True)

@lru_cache(None)
def synchrony_checks():
    small=('a','b');out={};count=0
    for name in ('baseline','selected_fails','other_fails','selected_outside','incomplete_scope','empty_scope','invalid_other'):
        cuts,m=exact_numbers();c=cuts.make;r=cuts.read
        reads={'a':(0,3 if name in ('selected_fails','selected_outside') else 2,4),'b':(7,10 if name=='other_fails' else 99 if name=='invalid_other' else 9,11)}
        selected=set() if name=='empty_scope' else {'b'} if name=='selected_outside' else set(small)
        m|={'qa':lambda cl,f,ctx:cl in small and (f,ctx)==('a','context'),'ca':lambda cl:cl in small,'cc':lambda cl,f:cl in small and f=='a','cb':lambda cl,p,f:cl==p and f=='a','ci':lambda u:u=='b','ql':lambda a,b,f,u,ctx:name!='incomplete_scope' and (a,b,f,u,ctx)==('a','b','a','b','context'),'qb':lambda a,b,f,u,ctx,tr:(a,b,f,u,ctx)==('a','b','a','b','context') and tr in selected,'da':lambda *xs:True,'bi':lambda a,b,last:r(b)-r(a)==r(last)-r(b),'ba':lambda x:r(x)!=99}
        m|={n:lambda tr:tr for n in ('qc','qd','qe','qf','qg','qh')}
        m|={n:lambda tr,i=i:c(Q(reads[tr][i])) for i,n in enumerate(('qi','qj','qk'))}
        actual=axial_run('qo',['a','b','a','b','context'],m,small);equation=axial_run('sit',[c(Q(x)) for x in reads['a']],m,small)
        assert actual==(name in ('baseline','selected_outside'));assert equation==(name not in ('selected_fails','selected_outside'));count+=2
        out[name]=dict(all_trials_synchronized=actual,selected_trial_in_scope='a' in selected,selected_equation=equation)
    return dict(cases=count,outcomes=out,native_complete_nonempty_all_trial_quantifier_evaluated=True,a_single_passing_trial_is_not_synchrony=True,trial_membership_needed_to_apply_sync_to_selected_equation=True,physical_protocol_and_real_extensional_equality_boundaries_explicit=True)

@lru_cache(None)
def presentation_checks():
    count=0
    cases=[('ei2e',{'ug':{('setup','author','ei2c','section','discourse')},'zao':{('purpose','setup','section','discourse')}}),('ei2h',{'zc':{('inference','author','ei2c','ei2d','section','discourse')},'ue':{('setup','inference','discourse')}})]
    for name,rows in cases:
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:axial_run(name,[],mm),m,rows)
        assert axial_run(name,[],m|{n:forbidden for n in ('ei2b','ei2c','ei2d','sit')});count+=1
    for name,node,message,previous in (('ei2g','setup','ei2f','purpose'),('ei2j','inference','ei2i','setup')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:axial_run(name,[],mm),m,rows)
    return dict(cases=count,hypothetical_setup_and_conditional_necessity_not_actual_experiment=True,same_premise_conclusion_author_scope_and_order=True,quoted_physical_content_not_executed=True)

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;coords=dict(zip(TUPLES,((5,0,0,5),(23,0,0,11),(14,0,0,14))))
    def tupleof(e,f,ctx):
        if e not in EVENTS or (f,ctx)!=('frame','context'):forbidden()
        return TUPLES[EVENTS.index(e)]
    def coordinate(t,a):
        if t not in coords or a not in ROLES:forbidden()
        return c(Q(coords[t][ROLES.index(a)]))
    def selected(value):return lambda tr:value if tr=='trial' else forbidden()
    m|={'zb7':lambda:c(Q(1)),'tc':lambda:c(Q(3)),'zdt':lambda:c(Q(12)),'zdz':tupleof,'zc6':coordinate,'bj':lambda scale,val:c(scale*r(val))}
    def divide(a,b):
        if r(b)<=0:forbidden()
        return c(r(a)/r(b))
    m['sje']=divide
    m|={n:selected(value) for n,value in zip(('qc','qd','qh','qe','qf','qg'),('origin','mirror','ray',*EVENTS))}
    m|={n:selected(c(Q(value))) for n,value in zip(('qi','qj','qk'),(10,19,28))}
    fn=FunctionValue((RS,)*4,RS,lambda xp,y,z,t:c(2*r(t)-r(xp)/4));m['zd4']=lambda:fn
    return cuts,m,coords,fn

@lru_cache(None)
def coordinate_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read
    rows={'eiyx':{(e,t,'frame','context') for e,t in zip(EVENTS,TUPLES)}};m|={n:relation(rs) for n,rs in rows.items()}
    check=lambda mm:run('ei2l',['context'],mm);count=perturb(check,m,rows)
    for t in TUPLES:
        for axis in ROLES:
            old=m['zc6'];assert not check(m|{'zc6':lambda rec,a,t=t,axis=axis:c(r(old(rec,a))+(1 if (rec,a)==(t,axis) else 0))});count+=1
    for symbol,val in (('zdt',0),('zdt',-12),('zdt',13),('zb7',0),('zb7',-1),('tc',1),('tc',0)):
        assert not check(m|{symbol:lambda val=val:c(Q(val))});count+=1
    unknowns(check,m,('zdz','zc6','zb7','zdt','tc','ba','bg','sca','bf','shv'))
    return dict(cases=count,all_three_current_K_tuples_and_zero_auxiliary_origin_bound=True,both_transverse_zero_components_required=True,positive_direction_and_strict_subluminal_conditions_preserved=True,nonzero_departure_K_position_and_time_allowed=True)

def segments(cuts,m):
    c=cuts.make;norm=norm_factory(cuts,());data={'outward':(0,1,Q(18)),'returning':(1,2,Q(9))}
    values={}
    for seg,(a,b,path) in data.items():values[seg]={'wf':'ray','wi':EVENTS[a],'wj':EVENTS[b],'wk':CLOCKS[a],'wl':CLOCKS[b],'wm':PLACES[a],'wn':PLACES[b],'wo':c(Q((5,11,14)[a])),'wp':c(Q((5,11,14)[b])),'wq':c(path)}
    def getter(n):
        def get(seg):
            if seg not in values:forbidden()
            return values[seg][n]
        return get
    m=m|{n:getter(n) for n in values['outward']}
    def axis(f,a,ctx):
        if (f,a,ctx)!=('frame','x','context'):forbidden()
        return 'axis'
    def stamp(e,f,u,ctx):
        if e not in EVENTS or (f,u,ctx)!=('frame','unit','context'):forbidden()
        return c(Q((5,11,14)[EVENTS.index(e)]))
    m|={'zbo':axis,'zbe':stamp}
    rows={'eiscd':{(s,'frame','lengthunit','unit','context') for s in data},'eifw':{(s,'frame','reference',Q(3),'context') for s in data},'eior':{(s,'context') for s in data},'zbw':{('frame','axis','x','context')},'zdw':{('ray',EVENTS[a],EVENTS[b],'axis','frame','context') for a,b,_ in data.values()},'eiyg':{(e,cl,p,'frame',Q(t),'context') for e,cl,p,t in zip(EVENTS,CLOCKS,PLACES,(5,11,14))},'eiyi':{(e,p,'frame','context') for e,p in zip(EVENTS,PLACES)},'eiyj':{(e,'frame','context') for e in EVENTS}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return m,rows,norm

@lru_cache(None)
def segment_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read;m,rows,norm=segments(cuts,m)
    args=[['outward','ray','depart','reflection',c(Q(18)),'context'],['returning','ray','reflection','arrival',c(Q(9)),'context']]
    check=lambda mm:all(run('ei2m',xs,mm) for xs in args);count=perturb(check,m,rows,norm)
    unknowns(check,m,('wf','wi','wj','wk','wl','wm','wn','wo','wp','wq','zbo','zbe','zdz','zc6','tc','sca'))
    for name in ('wo','wp','wq'):
        for seg in ('outward','returning'):
            old=m[name];assert not check(m|{name:lambda s,old=old,seg=seg:c(r(old(s))+(1 if s==seg else 0))});count+=1
    assert check(m|{'sba':forbidden,'sbc':forbidden,'shd':forbidden});count+=1
    return dict(cases=count,both_segments_same_ray_events_law_scope_and_geometric_length_bound=True,current_K_local_readings_unique_times_and_coordinate_times_agree=True,old_segment_and_coordinate_rules_not_used=True)

@lru_cache(None)
def geometry_checks():
    cuts,m,coords,fn=model();c=cuts.make;norm=norm_factory(cuts,())
    row=('origin','mirror','ray',*EVENTS,'frame','context','lengthunit','unit',*map(Q,(5,12,3,1,5,11,14)))
    rows={'eiti':{row},'ei2m':{('outward','ray','depart','reflection',Q(18),'context'),('returning','ray','reflection','arrival',Q(9),'context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};check=lambda mm:run('ei2n',['context'],mm)
    count=perturb(check,m,rows,norm);unknowns(check,m,('qc','qd','qh','qe','qf','qg','zdz','zc6','zb7','tc','zdt','bf'))
    # Evaluate the native complete-path wrapper, with se as the explicit infinite
    # history boundary. Probe fingerprints only distinguish argument functions.
    times=(5,8,11,14);norm=norm_factory(cuts,times)
    def linear(start,x,speed):return FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(speed)*(cuts.read(t)-start)))
    zero=linear(0,0,0)
    histories=[['origin','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,5,1),zero,zero],['mirror','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,17,1),zero,zero],['ray','frame','context','lengthunit','unit',c(Q(5)),c(Q(11)),linear(5,5,3),zero,zero],['ray','frame','context','lengthunit','unit',c(Q(11)),c(Q(14)),linear(11,23,-3),zero,zero]]
    native={'se':{norm(xs) for xs in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set(),'ei2m':rows['ei2m']}
    for point,event,t,x in (('origin','depart',5,5),('mirror','reflection',11,23),('origin','arrival',14,14)):
        native['zzbu'].add((event,'frame','context','lengthunit','unit',Q(t),Q(x),Q(0),Q(0)))
        for obj in (point,'ray'):native['zzbv'].add((obj,event,'context'))
    mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in native.items()}
    count+=perturb(lambda model:run('ei2n',['context'],model,'paths'),mm,native,norm)
    return dict(cases=count,native_two_endpoint_and_two_light_histories_and_same_event_meetings=True,nonzero_K_origin_is_actual_v_times_departure_time=True,both_signed_path_lengths_and_all_parameters_bound=True,finite_function_fingerprints_are_not_whole_real_history_proofs=True)

@lru_cache(None)
def candidate_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read;probe=(Q(1),Q(2),Q(3),Q(4))
    m['eizz']=lambda f:r(f(*(c(x) for x in probe)))==Q(31,4)
    check=lambda mm:run('ei2o',[fn],mm);assert check(m);count=1
    for n in ('qi','qj','qk'):
        old=m[n];assert not check(m|{n:lambda tr,old=old:c(r(old(tr))+1)});count+=1
    assert not check(m|{'eizz':lambda f:False});count+=1
    wrong=FunctionValue((RS,)*4,RS,lambda xp,y,z,t:c(2*r(t)+r(xp)/4))
    assert not run('ei2o',[wrong],m);count+=1
    unknowns(check,m,('eizz','qe','qf','qg','qi','qj','qk','zdq','zdt','zdz','zc6','ba','sca'))
    # Tie the same function and all physical conditions into the closed premise.
    norm0=norm_factory(cuts,())
    def norm(xs):return tuple((r(x(c(Q(0)),c(Q(0)),c(Q(0)),c(Q(5)))),r(x(c(Q(12)),c(Q(0)),c(Q(0)),c(Q(11))))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else norm0((x,))[0] for x in xs)
    rows={'ei2b':{()},'ei2l':{('context',)},'eios':{(Q(3),'context')},'eiyf':{('frame','context')},'ei2n':{('context',)},'ei2o':{((Q(10),Q(19)),)}}
    mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};count+=perturb(lambda model:run('ei2p',[],model),mm,rows,norm)
    unknowns(lambda model:run('ei2p',[],model),mm,('zd4','tc'))
    for truth in (False,True):assert run('ei2q',[],{'ei2p':lambda truth=truth:truth})==truth;count+=1
    return dict(cases=count,same_candidate_function_used_for_global_clock_condition_and_three_actual_readings=True,current_prior_trip_K_clocks_light_principle_geometry_and_candidate_all_required=True,quoted_premise_does_not_find_a_tau_solution=True)

@lru_cache(None)
def expression_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read;count=0;out={}
    for name,label,start,wrong in [('baseline',12,5,False),('shifted_time_origin',12,-3,False),('negative_label_algebra_only',-12,5,False),('zero_label_algebra_only',0,5,False),('wrong_space_sign',12,5,True)]:
        calls=[]
        def function(x,y,z,t):
            vals=tuple(map(r,(x,y,z,t)));calls.append(vals)
            return c(2*vals[3]+(1 if wrong else -1)*vals[0]/4)
        f=FunctionValue((RS,)*4,RS,function);args=[f,c(Q(label)),c(Q(3)),c(Q(1)),c(Q(start))]
        actual=run('sjg',args,m);assert actual==(not wrong);count+=1
        expected={(Q(0),Q(0),Q(0),Q(start)),(Q(label),Q(0),Q(0),Q(start)+Q(label,2)),(Q(0),Q(0),Q(0),Q(start)+Q(3*label,4))}
        assert set(calls)==expected;count+=1;out[name]=actual
    assert run('ei2r',[],m);count+=1
    assert not run('ei2r',[],m|{'sje':lambda a,b:c(r(a)/(4 if r(b)==2 else 2))});count+=1
    assert not run('ei2r',[],m|{'bj':lambda scale,val:c(r(val))});count+=1
    assert not run('ei2r',[],m|{'ba':lambda value:r(value)!=12});count+=1
    unknowns(lambda mm:run('ei2r',[],mm),m,('zd4','zdt','tc','zb7','zdz','zc6','ba','bg','bd','bf','sje','bj','sca'))
    # Invalid denominator is rejected, even when the Boolean guard is false.
    for speed in (3,4):
        try:run('sjg',[fn,c(Q(12)),c(Q(3)),c(Q(speed)),c(Q(5))],m)
        except ValueError as e:assert 'Unknown axial-expansion-visible' in str(e)
        else:raise AssertionError('Invalid reciprocal input silently fabricated')
        count+=1
    return dict(cases=count,outcomes=out,native_sjf_sjg_all_four_argument_tuples_and_half_sum_checked=True,denominator_signs_and_reflection_return_order_preserved=True,invalid_division_rejected=True,negative_or_zero_label_algebra_not_claimed_as_physical_trip=True)

@lru_cache(None)
def expansion_presentation_checks():
    rows={'zd3':{('expansion','author','ei2q','ei2d','ei2r','section','discourse')}};m={n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ei2s',[],mm),m,rows)
    assert run('ei2s',[],m|{n:forbidden for n in ('ei2q','ei2d','ei2r','ei2p','sjg')});count+=1
    rows={'eir3':{('expansion','author','paper','ei2t','discourse')},'ue':{('inference','expansion','discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('ei2u',[],mm),m,rows)
    return dict(cases=count,same_current_midpoint_premise_and_expanded_formula_bound=True,conditional_reexpression_not_an_automatic_equivalence_proof=True,author_scope_and_source_order_preserved=True)


def test_label_checks():
    assert label_checks()['cases']>0


def test_local_checks():
    assert local_checks()['cases']>0


def test_trip_checks():
    assert trip_checks()['cases']>0


def test_connection_checks():
    assert connection_checks()['cases']>0


def test_midpoint_checks():
    assert midpoint_checks()['cases']>0


def test_synchrony_checks():
    assert synchrony_checks()['cases']>0


def test_presentation_checks():
    assert presentation_checks()['cases']>0


def test_coordinate_checks():
    assert coordinate_checks()['cases']>0


def test_segment_checks():
    assert segment_checks()['cases']>0


def test_geometry_checks():
    assert geometry_checks()['cases']>0


def test_candidate_checks():
    assert candidate_checks()['cases']>0


def test_expression_checks():
    assert expression_checks()['cases']>0


def test_expansion_presentation_checks():
    assert expansion_presentation_checks()['cases']>0


def test_source_closure_and_backprojection():
    assert check.backprojection(check.restored()['document'])==check.source_excerpt()
    b=check.bridge()
    assert b['source_statement_indices']==[113,114,115]
    assert len(b['source_units'])==5 and len(b['math'])==10
    assert check.document()['statements'][:83]==check.previous.document()['statements']
    assert len(profile.SOURCE_RELATIONS)==3 and len(profile.EXTRA)==1
    assert len(check.vocabulary()._words)==757
    for field in ('entries','compounds','definitions','primitives'):
        assert all(check.vocabulary().document()[field].get(n)==d for n,d in check.previous.vocabulary().document()[field].items())

def test_unknown_cut_cannot_be_inferred_from_samples():
    cuts,m=numbers()
    with pytest.raises(ValueError,match='not constructed'):
        cuts.read(FunctionValue(('number',),'truth',lambda x:x<1))


def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]


def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}


def reference_values():
    return check.BASE|{'zb7':cut(Q(3)),'zdt':cut(Q(12)),
        'zd4':FunctionValue((RS,)*4,RS,forbidden)}


def test_references_select_without_executing_physical_roles_or_candidate():
    doc=deepcopy(check.restored()['document']);n=check.names();b=reference_values()
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        trial=deepcopy(doc);sort=profile.CUT if old=='zdt' else profile.TAU if old=='zd4' else 'individual'
        trial['declarations'].append(dict(kind='primitive',name='axialcapture',parameters=[sort],result='truth'))
        trial['statements']=[dict(kind='ask',body=call('axialcapture',call(n[old])))]
        def capture(value):
            if old=='zd4':return isinstance(value,FunctionValue) and list(value.parameters)==profile.TAU['parameters'] and value.result==RS
            if old=='zdt':return all(value(Q(q))==(q<12) for q in (0,11,12,13))
            return value==b[old]
        assert native_run(trial,context(trial,b)|dict(axialcapture=capture))==[True]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())


def test_reference_type_scope_and_unknown_inputs_are_rejected():
    b=reference_values();h=check.context_handlers(b)
    for old,role in check.reference_roles().items():
        sort=profile.CUT if old=='zdt' else profile.TAU if old=='zd4' else 'individual'
        description=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=role)),check.canonical(dict(kind='function',parameters=[sort,'situation'],result='truth')))
        relation='describedcutreference' if old=='zdt' else 'describedfourcutfunctionreference' if old=='zd4' else 'describedreference'
        key=[b['eirf'],b[check.reference_anchor(old)],description,b['ri']]
        assert h[relation](*key) is b[old]
        for slot in range(4):
            changed=key.copy();changed[slot]='unknown'
            with pytest.raises(ValueError):h[relation](*changed)
        for bad in (DescriptionValue('{}',description.result_type),DescriptionValue(description.syntax,'"individual"'),DescriptionValue(description.syntax,description.result_type,1)):
            with pytest.raises(ValueError):h[relation](*key[:2],bad,key[3])
    for bad in (cut(3),FunctionValue((RS,)*3,RS,forbidden),FunctionValue((RS,)*4,'truth',forbidden),FunctionValue((RS,)*4,RS,None)):
        with pytest.raises(ValueError):profile.FourCutFunctionReferences({('paper','node','role','context'):bad})
    for old,(node,start,end) in check.SPANS.items():
        key=[b['eirf'],b[node],start,b[node],end,b['ri']]
        assert h['sentencetokenspanreference'](*key)==b[old]
        for slot in range(6):
            changed=key.copy();changed[slot]='unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*changed)
    assert h['sentencetokenspanreference'](b['eirf'],b['zdj'],4,b['zdj'],22,b['ri'])==b['zdk']


def test_reference_roles_bind_the_same_trial_clocks_and_cut():
    small=('a','b');cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,())
    # Each existential slot is distinguished on two individuals. This is a
    # binding diagnostic; it does not establish existence in a physical model.
    for trial,first,second in product(small,repeat=3):
        row=(trial,first,second,'context')
        model=m|{'zdq':lambda trial=trial:trial,'ei2a':lambda *xs:xs==row}
        assert run('axialroletrial',[trial,'discourse'],model,domain=small)
        assert not run('axialroletrial',['b' if trial=='a' else 'a','discourse'],model,domain=small)
        assert run('axialrolefirstclock',[first,'discourse'],model,domain=small)
        assert not run('axialrolefirstclock',['b' if first=='a' else 'a','discourse'],model,domain=small)
        assert run('axialrolesecondclock',[second,'discourse'],model,domain=small)
        assert not run('axialrolesecondclock',['b' if second=='a' else 'a','discourse'],model,domain=small)
        for target,args in (('axialroletrial',[trial,'discourse']),('axialrolefirstclock',[first,'discourse']),('axialrolesecondclock',[second,'discourse'])):
            assert not run(target,args,model|{'ei2a':lambda *xs:False},domain=small)
    rows={'eiz6':{('reflection',Q(12),'context')}}
    mm=m|{'qf':lambda tr:'reflection' if tr=='trial' else forbidden(),'eiz6':lambda *xs:norm(xs) in rows['eiz6']}
    assert perturb(lambda mm:run('axialrolereflectioncut',[c(12),'discourse'],mm),mm,rows,norm)>1
    assert not run('axialrolereflectioncut',[c(13),'discourse'],mm)


def test_segment_and_function_reference_roles_use_existing_conditions():
    cuts,m,coords,fn=model();c=cuts.make;norm=norm_factory(cuts,())
    for name,segment,first,last,length in (('outsegment','outward','depart','reflection',18),('backsegment','returning','reflection','arrival',9)):
        rows={'ei2m':{(segment,'ray',first,last,Q(length),'context')}}
        mm=m|{'ei2m':lambda *xs:norm(xs) in rows['ei2m']}
        assert perturb(lambda mm:run('axialrole'+name,[segment,'discourse'],mm),mm,rows,norm)>1
    trace=[]
    def accepted(candidate):
        trace.append(tuple(candidate.parameters))
        return cuts.read(candidate(c(12),c(0),c(0),c(11)))==19
    q=QuestionValue(FunctionValue((profile.TAU,),'truth',accepted))
    assert run('axialroletimefunction',[fn,'discourse'],m|{'eizv':lambda:q})
    assert len(trace)==1
    assert not run('axialroletimefunction',[fn,'discourse'],m|{'eizv':lambda:QuestionValue(FunctionValue((profile.TAU,),'truth',lambda f:False))})


def test_whole_attribution_keeps_order_without_executing_physical_claims():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][83:86];b=reference_values()
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('zdu','ei2f'),('zdv','ei2i'),('zd2','ei2t'))},
        'ue':{(b[first],b[last],b['ri']) for first,last in (('zdp','zdu'),('zdu','zdv'),('zdv','zd2'))}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]*3
    for n,rs in rows.items():
        for row in rs:
            result=native_run(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==2
