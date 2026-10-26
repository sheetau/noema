from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_differential_visible as check
from scripts import axial_expansion_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
VS=dict(kind='function',parameters=['individual'],result=RS)
MS=dict(kind='function',parameters=['individual','individual'],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
ROLES=('x','y','z','time')
POINTS=('context','discourse','other')
CONSTANTS={'ra':'frame','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdq':'trial','zd2':'expansion','zea':'differential','zeb':'rewrite'}
DOMAIN=('frame','time','author','paper','section','trial','expansion','differential','rewrite','depart','tuple','other')
POINTS=('context','discourse','other')

def forbidden(*args):raise ValueError('Unknown differential-visible input')
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
    boundaries|={'bj','sjd'}
    if name=='ei2v':boundaries|={'skc','sjv','sjw'}
    if name=='ei2w':boundaries|={'ei2p','ei2v'}
    if name=='ei2x':boundaries.add('ei2w')
    if name=='sjw' and mode!='native':boundaries.add('sjs')
    if name=='skc' and mode=='instance':boundaries.add('sjg')
    if name.startswith('differentialrole'):boundaries|={'skc','sjs'}
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
    if name=='skc' and mode=='instance':assert instantiate(target)==[RS]
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
        except ValueError as e:assert 'Unknown differential-visible' in str(e),str(e)
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

def instantiate(d):
    """Expose every quantifier in this definition's own body as a parameter."""
    added=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='forall':
            added.append(dict(name=node['variable'],sort=node['sort']))
            return walk(node['body'])
        return {k:walk(v) for k,v in node.items()}
    d['body']=walk(d['body']);d['parameters']+=added
    return [p['sort'] for p in added]


def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    m['bj']=lambda scale,val:c(scale*r(val))
    def inverse(x):
        if r(x)<=0:forbidden()
        return c(1/r(x))
    m['sjd']=inverse
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(-r(x)/4+3*r(y)+7*r(z)+2*r(t)))
    for n,value in {'tc':3,'zb7':1,'zd5':Q(1,2),'zd6':Q(-1,4),'zd7':2}.items():m[n]=lambda value=value:c(Q(value))
    m['zd4']=lambda:fn;m['qe']=lambda tr:'depart' if tr=='trial' else forbidden()
    m['zdz']=lambda e,f,ctx:'tuple' if (e,f,ctx)==('depart','frame','context') else forbidden()
    m['zc6']=lambda tup,role:c(Q(5)) if (tup,role)==('tuple','time') else forbidden()
    ordinary=norm_factory(cuts,())
    def norm(xs):return tuple(tuple(r(x(*(c(Q(a)) for a in point))) for point in ((0,0,0,5),(1,2,3,4))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else ordinary((x,))[0] for x in xs)
    return cuts,m,fn,norm

@lru_cache(None)
def premise_checks():
    cuts,m,fn,norm=model();c=cuts.make
    args=[fn,*map(c,map(Q,(3,1,5,Q(1,2),Q(-1,4),2)))];finger=norm((fn,))[0]
    point=(finger,Q(0),Q(0),Q(0),Q(5),Q(-1,4),Q(2))
    rows={'skc':{(finger,Q(3),Q(1),Q(5),Q(1,2))},'sjv':{point},'sjw':{point}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda mm:run('ei2v',args,mm);count=perturb(check,m,rows,norm)
    for slot in range(1,7):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei2v',bad,m);count+=1
    for speed in (0,-1,3,4):
        bad=args.copy();bad[2]=c(Q(speed));assert not run('ei2v',bad,m);count+=1
    unknowns(check,m,('ba','bg','bb'))
    whole={'ei2p':{()},'ei2v':{norm(args)}};mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in whole.items()}
    count+=perturb(lambda mm:run('ei2w',[],mm),mm,whole,norm)
    unknowns(lambda mm:run('ei2w',[],mm),mm,('zd4','tc','zb7','zd5','zd6','zd7','qe','zdz','zc6'))
    assert run('ei2w',[],mm|{'sjl':forbidden,'skd':forbidden});count+=1
    for truth in (False,True):assert run('ei2x',[],{'ei2w':lambda truth=truth:truth})==truth;count+=1
    return dict(cases=count,current_physical_premise_and_same_tau_time_radius_and_partials_bound=True,separate_partials_not_substituted_for_total_differentiability=True,old_sjl_and_skd_not_used=True)

@lru_cache(None)
def neighborhood_checks():
    cuts,m,fn,norm=model();c=cuts.make;count=0
    for h in (Q(-1),Q(0),Q(1,8),Q(1,4),Q(1,2),Q(3,4)):
        xs=[fn,c(Q(3)),c(Q(1)),c(Q(5)),c(Q(1,2)),c(h)]
        for truth in (False,True):
            seen=[]
            def midpoint(*args):seen.append(norm(args));return truth
            assert run('skc',xs,m|{'sjg':midpoint},'instance')==(truth or not 0<h<Q(1,2));count+=1
            assert seen==[(norm((fn,))[0],h,Q(3),Q(1),Q(5))]
    for radius in (0,-1):
        assert not run('skc',[fn,*map(c,map(Q,(3,1,5,radius,Q(1,4))))],m|{'sjg':lambda *xs:True},'instance');count+=1
    args=[fn,*map(c,map(Q,(3,1,5,Q(1,2),Q(1,4))))]
    row=norm([fn,*map(c,map(Q,(Q(1,4),3,1,5)))])
    mm=m|{'sjg':lambda *xs:norm(xs)==row}
    count+=perturb(lambda mm:run('skc',args,mm,'instance'),mm,{'sjg':{row}},norm)
    return dict(cases=count,strict_positive_radius_and_all_interior_positive_steps_preserved=True,instances_check_scope_not_the_full_neighborhood=True,same_midpoint_function_and_all_five_arguments_bound=True)

@lru_cache(None)
def slice_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;observed=[];count=0
    # Fingerprints distinguish the two native slice closures; they do not prove limits.
    def derivative(domain,f,point,result):
        p=r(point);d=r(result);samples=tuple(r(f(c(p+h))) for h in (Q(-1),Q(0),Q(2)))
        observed.append((p,d,samples))
        return domain(point) and (p,d,samples) in {(Q(0),Q(-1,4),(Q(41,4),Q(10),Q(19,2))),(Q(5),Q(2),(Q(8),Q(10),Q(14)))}
    args=[fn,*map(c,map(Q,(0,0,0,5,Q(-1,4),2)))];mm=m|{'sjs':derivative}
    assert run('sjw',args,mm);count+=1;assert len(observed)==2
    for slot in range(1,7):
        bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('sjw',bad,mm);count+=1
    wrong=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(r(x)/4+3*r(y)+7*r(z)+2*r(t)))
    assert not run('sjw',[wrong,*args[1:]],mm);count+=1
    unknowns(lambda m:run('sjw',args,m),mm,('sjs','ba'))
    return dict(cases=count,both_native_slices_fix_the_other_three_coordinates=True,both_values_belong_to_the_same_function_and_point=True,finite_affine_fingerprints_not_limit_proofs=True)

@lru_cache(None)
def equation_checks():
    cuts,m,fn,norm=model();c=cuts.make;count=0
    for V,s,px,pt,expected in ((3,1,Q(-1,4),2,True),(3,1,-1,8,True),(5,2,Q(-2,21),1,True),(3,0,0,8,True),(3,1,1,8,False),(3,1,-1,4,False),(3,1,8,-1,False),(3,-1,-1,8,False)):
        args=list(map(c,map(Q,(V,s,px,pt))))
        for name in ('sjx','sjy'):assert run(name,args,m)==expected;count+=1
    for name in ('skf','skg'):
        assert run(name,[],m);assert not run(name,[],m|{'zd6':lambda:c(Q(1,4))});count+=2
    assert not run('skf',[],m|{'bj':lambda scale,val:val});count+=1
    for name in ('sjx','sjy'):
        for speed in (3,4):
            try:run(name,list(map(c,map(Q,(3,speed,-1,8)))),m)
            except ValueError as e:assert 'Unknown differential-visible' in str(e)
            else:raise AssertionError('Invalid reciprocal silently fabricated')
            count+=1
    unknowns(lambda mm:run('skf',[],mm),m,('tc','zb7','zd6','zd7','sjd','bj','bd','bf','shv','sca','ba','bc','bg'))
    unknowns(lambda mm:run('skg',[],mm),m,('sjd','bf','shv','sca'))
    return dict(cases=count,native_both_equations_and_same_partials_preserved=True,denominator_signs_half_and_speed_factor_checked=True,invalid_reciprocal_rejected=True)

@lru_cache(None)
def finite_refusals():
    cuts,m,fn,norm=model();c=cuts.make;results={}
    for name,args in (('skc',[fn,*map(c,map(Q,(3,1,5,Q(1,2))))]),('sjv',[fn,*map(c,map(Q,(0,0,0,5,Q(-1,4),2)))]),('sjw',[fn,*map(c,map(Q,(0,0,0,5,Q(-1,4),2)))])):
        try:run(name,args,m,'native')
        except ValueError as e:assert 'Cannot finitely quantify' in str(e);results[name]=str(e)
        else:raise AssertionError('Finite evaluator accepted a full real limit')
    return dict(full_real_neighborhood_and_derivatives_refused=True,reasons=results)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
      ('ei2y',{'zc':{('differential','author','ei2x','skf','section','discourse')}}),
      ('ei23',{'zd3':{('rewrite','author','ei2x','skf','skg','section','discourse')}}),
      ('ei22',{'eir3':{('differential','author','paper','ei2z','discourse')},'ue':{('expansion','differential','discourse')}}),
      ('ei25',{'eir3':{('rewrite','author','paper','ei24','discourse')},'ue':{('differential','rewrite','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei2x','skf','skg','ei2w','ei2p')});count+=1
    return dict(cases=count,same_premise_and_two_equations_in_inference_and_reexpression=True,author_section_and_order_preserved=True,quoted_inference_not_executed_as_truth=True)


def test_premise_checks():
    assert premise_checks()['cases']>0


def test_neighborhood_checks():
    assert neighborhood_checks()['cases']>0


def test_slice_checks():
    assert slice_checks()['cases']>0


def test_equation_checks():
    assert equation_checks()['cases']>0


def test_presentation_checks():
    assert presentation_checks()['cases']>0


def test_full_real_neighborhood_and_derivatives_are_not_finite_proofs():
    assert finite_refusals()['full_real_neighborhood_and_derivatives_refused']

def test_source_closure_backprojection_and_unchanged_vocabulary():
    assert check.backprojection(check.restored()['document'])==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[116,117]
    assert len(b['source_units'])==4 and len(b['math'])==3
    assert len(b['text_boundaries']['sentences']['zea']['tokens'])==11
    assert b['text_boundaries']['spans']=={'zeb':['zea',10,11]}
    assert check.document()['statements'][:86]==check.previous.document()['statements']
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(check.vocabulary()._words)==757

def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]

def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}

def reference_values():
    return check.BASE|{'zb7':cut(Q(3)),'zd5':cut(Q(1,2)),'zd6':cut(Q(-1,4)),'zd7':cut(Q(2))}

def test_references_do_not_execute_infinite_limit_roles():
    doc=deepcopy(check.restored()['document']);b=reference_values();n=check.names()
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        trial=deepcopy(doc);sort=RS if old in check.ROLE_ASSIGNMENTS else 'individual'
        trial['declarations'].append(dict(kind='primitive',name='differentialcapture',parameters=[sort],result='truth'))
        trial['statements']=[dict(kind='ask',body=call('differentialcapture',call(n[old])))]
        def capture(value):
            return all(value(Q(q))==b[old](Q(q)) for q in (-2,-1,Q(-1,4),0,Q(1,2),1,2,3)) if old in check.ROLE_ASSIGNMENTS else value==b[old]
        assert native_run(trial,context(trial,b)|dict(differentialcapture=capture))==[True]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())

def test_reference_scopes_reject_unknown_roles_and_boundaries():
    b=reference_values();h=check.context_handlers(b)
    for old,role in check.reference_roles().items():
        description=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=role)),check.canonical(dict(kind='function',parameters=[RS,'situation'],result='truth')))
        key=[b['eirf'],b['zea'],description,b['ri']]
        assert h['describedcutreference'](*key) is b[old]
        for slot in range(4):
            changed=key.copy();changed[slot]='unknown'
            with pytest.raises(ValueError):h['describedcutreference'](*changed)
        for bad in (DescriptionValue('{}',description.result_type),DescriptionValue(description.syntax,'"individual"'),DescriptionValue(description.syntax,description.result_type,1)):
            with pytest.raises(ValueError):h['describedcutreference'](*key[:2],bad,key[3])
    key=[b['eirf'],b['zea'],10,b['zea'],11,b['ri']]
    assert h['sentencetokenspanreference'](*key)==b['zeb']
    for slot in range(6):
        changed=key.copy();changed[slot]='unknown'
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*changed)
    assert h['sentencetokenspanreference'](b['eirf'],b['zdu'],39,b['zdu'],60,b['ri'])==b['zd2']

def test_reference_roles_bind_same_radius_function_time_and_slices():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read
    row=(norm((fn,))[0],Q(3),Q(1),Q(5),Q(1,2))
    rows={'skc':{row}};mm=m|{'skc':lambda *xs:norm(xs)==row}
    assert perturb(lambda mm:run('differentialroleradius',[c(Q(1,2)),'discourse'],mm),mm,rows,norm)>1
    for name,point,coefficient,expected in (('spacepartial',0,Q(-1,4),(Q(41,4),Q(10),Q(19,2))),('timepartial',5,2,(Q(8),Q(10),Q(14)))):
        observed=[]
        def derivative(domain,f,p,result):
            values=tuple(r(f(c(r(p)+h))) for h in (-1,0,2));observed.append((r(p),r(result),values))
            return domain(p) and (r(p),r(result),values)==(Q(point),Q(coefficient),expected)
        mm=m|{'sjs':derivative}
        assert run('differentialrole'+name,[c(coefficient),'discourse'],mm)
        assert len(observed)==1
        assert not run('differentialrole'+name,[c(coefficient+1),'discourse'],mm)
        assert not run('differentialrole'+name,[c(coefficient),'discourse'],mm|{'sjs':lambda *xs:False})
        for changed in ('zd4','qe','zdz','zc6'):
            with pytest.raises(ValueError):run('differentialrole'+name,[c(coefficient),'discourse'],mm|{changed:forbidden})

def test_whole_attribution_keeps_inference_and_reexpression_separate():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][86:88];b=reference_values()
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('zea','ei2z'),('zeb','ei24'))},
        'ue':{(b[first],b[last],b['ri']) for first,last in (('zd2','zea'),('zea','zeb'))}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]*2
    for n,rs in rows.items():
        for row in rs:
            result=native_run(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==1
