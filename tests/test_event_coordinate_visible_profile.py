from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import FunctionValue,SequenceValue,DescriptionValue,Content,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_event_coordinate_visible as check
from scripts import event_coordinate_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
HISTORY_DOMAIN=('body','second','origin','otherorigin','guide','otherguide','point','hidden','frame','moving','lengthunit','timeunit','x','y','z','other')
POINTS=('context','initial','discourse','scope','scene','other')

def forbidden(*args):raise ValueError('Unknown event-coordinate-visible input')
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

CONSTANTS={'ra':'frame','zbm':'moving','rb':'unit','ta':'lengthunit','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','ri':'discourse','eisms':'section','zc3':'clocks','zda':'claim','zdb':'task','zcg':'motion','eisna':'kname','eism5':'tname','eisnl':'tauname'}
CONSTANTS.update({sign:printed+'name' for sign,printed,*_ in COORDINATES})
DOMAIN=tuple(dict.fromkeys(['event','tuple','place','otherplace','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')


@lru_cache(None)
def fixture(name):
    doc=deepcopy(check.restored()['document']);m=mapping()
    selected=NUM|set(CONSTANTS)|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}|{'eixq'}
    if name=='eiyw':selected|={'eiyv','eiyi','eiyj'}
    if name=='eiyx':selected.add('eiyw')
    if name in ('eiyy','eiyz','eiy2','eiy3'):selected|={'eiyx','shh'}
    if name=='eiy5':selected|={'eiyz','eiy2','eiyy','shh'}
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
    if name=='eiy5':
        sort=target['result']['parameters'][0];assert sort['kind']=='sequence'
        doc['declarations'].append(dict(kind='primitive',name='jectseq',parameters=[],result=sort))
        doc['statements']=[dict(kind='ask',body=dict(kind='answer_matches',question=call(m[name]),arguments=[call('jectseq')]))]
        return doc,['jectseq']
    for i,p in enumerate(target['parameters']):
        slot='eventslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='eventcontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('eventcontext'))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,model,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    m={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'eventcontext':lambda:'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    h=handlers(doc);h.update({mapping().get(n,n):f for n,f in m.items() if mapping().get(n,n) in h})
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives=h,max_steps=1500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown event-coordinate-visible' in str(e),str(e)
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

def measurement_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,());roles=('x','y','z','time');vals=(-2,0,3,7)
    positions={p:(100+i,200+i,300+i) for i,p in enumerate(DOMAIN)};positions['place']=vals[:3]
    rows={'zc5':{('tuple',)},'zcu':{('place','frame','context')},'eixq':{('place','frame',r,'context') for r in roles[:3]}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'zc6':lambda t,r:c(Q(vals[roles.index(r)])),'zcy':lambda p,f,r,u,ctx:c(Q(positions[p][roles.index(r)]))}
    args=['tuple','place','frame','context'];count=perturb(lambda mm:run('eiyu',args,mm),m,rows)
    for i,r in enumerate(roles[:3]):
        assert not run('eiyu',args,m|{'zc6':lambda t,a,i=i:c(Q(vals[roles.index(a)]+(1 if roles.index(a)==i else 0)))});count+=1
    assert run('eiyu',args,m|{'zc6':lambda t,r:c(Q(99 if r=='time' else vals[roles.index(r)]))});count+=1
    assert not run('eiyu',args,m|{'ba':lambda val:cuts.read(val)!=7});count+=1
    assert not run('eiyu',args,m|{'zc7':lambda:'x'});count+=1
    unknowns(lambda mm:run('eiyu',args,mm),m,('zc6','zcy','ba','sca'))
    assert run('eiyv',args,m);count+=1
    extended=m|{'zcu':relation(rows['zcu']|{('otherplace','frame','context')}),'eixq':relation(rows['eixq']|{('otherplace','frame',r,'context') for r in roles[:3]})}
    assert run('eiyv',args,extended);count+=1
    ambiguous=extended|{'zcy':lambda p,f,r,u,ctx:c(Q(vals[roles.index(r)] if p in ('place','otherplace') else positions[p][roles.index(r)]))}
    assert not run('eiyv',args,ambiguous);count+=1
    assert not run('eiyv',args,m|{'zcu':lambda *xs:False});count+=1
    # Four-component equality is value equality, including separate records.
    # The evaluator is eager. Non-role members of this explicit finite domain
    # get an irrelevant numeric cell; sgt's role predicate excludes that cell.
    vectors={'tuple':vals,'other':vals};mm={n:m[n] for n in NUM if n in m}|{'zc6':lambda t,r:c(Q(vectors[t][roles.index(r)] if r in roles else -31))}
    assert run('shh',['tuple','other'],mm);count+=1
    for i in range(4):
        changed=list(vals);changed[i]+=1
        assert not run('shh',['tuple','other'],mm|{'zc6':lambda t,r,changed=changed:c(Q((changed if t=='other' else vals)[roles.index(r)] if r in roles else -31))});count+=1
    return dict(cases=count,native_sha_eixu_and_all_location_candidates_checked=True,four_component_value_identity_not_record_identity=True,time_component_not_assigned_by_spatial_measurement_alone=True)

def test_measurement_checks():assert measurement_checks()

def binding_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,())
    rows={'zc4':{('event',)},'zcz':{('event','moving','context')},'zbd':{('event',)},'va':{('moving',)},'ti':{('lengthunit',)},'ci':{('unit',)},'eiyv':{('tuple','place','moving','context')},'cb':{('event','place','moving')},'eiyi':{('event','place','moving','context')},'eiyj':{('event','moving','context')}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'zc6':lambda t,r:c(Q(7)) if (t,r)==('tuple','time') else forbidden(),'zbe':lambda *xs:c(Q(7)) if xs==('event','moving','unit','context') else forbidden()}
    args=['event','tuple','place','moving','context'];check=lambda mm:run('eiyw',args,mm)
    count=perturb(check,m,rows);assert not check(m|{'zbe':lambda *xs:c(Q(8))});count+=1
    unknowns(check,m,('zc6','zbe','sca'))
    small=('a','b')
    for e,t,p,f in product(small,repeat=4):
        row=(e,t,p,f,'context');args=[e,t,f,'context'];mm={'eiyw':relation({row})}
        assert run('eiyx',args,mm,small);count+=1
        for i in range(5):
            bad=list(row);bad[i]='wrong'
            assert not run('eiyx',args,{'eiyw':relation({tuple(bad)})},small);count+=1
    unknowns(lambda mm:run('eiyx',['a','b','a','context'],mm,small),{'eiyw':lambda *xs:True},('eiyw',))
    return dict(cases=count,same_event_place_frame_tuple_time_and_context_bound=True,existential_place_checked_with_two_individuals=True)

def test_binding_checks():assert binding_checks()

def correspondence_checks():
    domain=('a','b','c','d','alias');count=0;out={}
    names=('baseline','empty_events','missing_source','missing_target','two_source_values','two_target_values','equivalent_target_alias','same_input_different_output','coincident_events','swapped_event_targets','equivalent_source_different_output','equivalent_source_same_output')
    for name in names:
        events=set() if name=='empty_events' else {'a','b'};left={('a','a'),('b','b')};right={('a','c'),('b','d')}
        if name=='missing_source':left.remove(('b','b'))
        if name=='missing_target':right.remove(('b','d'))
        if name=='two_source_values':left.add(('a','b'))
        if name=='two_target_values':right.add(('a','d'))
        if name=='equivalent_target_alias':right.add(('a','alias'))
        if name in ('same_input_different_output','coincident_events'):left={('a','a'),('b','a')}
        if name in ('coincident_events','equivalent_source_same_output'):right={('a','c'),('b','c')}
        if name=='swapped_event_targets':right={('a','d'),('b','c')}
        def key(t):return 'c' if t=='alias' else 'a' if t=='b' and name.startswith('equivalent_source_') else t
        same=lambda a,b:key(a)==key(b)
        relation=lambda a,b:any((e,a) in left and (e,b) in right for e in events)
        m={'ra':lambda:'a','zbm':lambda:'b','zc4':lambda e:e in events,'shh':same,'eiyx':lambda e,t,f,ctx:ctx=='context' and (e,t) in (left if f=='a' else right if f=='b' else set())}
        complete=bool(events) and all(all(vals and all(same(a,b) for a in vals for b in vals) for vals in ({t for e,t in left if e==event},{t for e,t in right if e==event})) for event in events)
        source={t for e,t in left if e in events};target={t for e,t in right if e in events}
        functional=bool(source) and all(any(relation(a,b) for b in target) for a in source) and all(same(b,d) for a,c,b,d in product(source,source,target,target) if same(a,c) and relation(a,b) and relation(c,d))
        actual=run('eiy3',[],m,domain);assert actual==(complete and functional),(name,actual);count+=1;out[name]=actual
        for a,b in (('a','c'),('a','d')):assert run('eiyy',[a,b],m,domain)==relation(a,b);count+=1
    return dict(cases=count,outcomes=out,native_sgu_sgv_sgw_and_modern_side_bindings_checked=True,coincident_events_and_equivalent_records_allowed=True,no_cross_event_pairing=True)

def test_correspondence_checks():assert correspondence_checks()

def equation_checks():
    domain=('a','b','c','d','extra');vectors={'a':(0,0,0,0),'b':(1,0,0,0),'c':(2,0,0,0),'d':(3,0,0,0),'extra':(2,1,0,0)}
    doc,slots=fixture('eiy5');element=next(d['result']['element'] for d in doc['declarations'] if d['name']=='jectseq');count=0;out={}
    for name in ('exact','reordered','duplicate_equation','empty','missing_x','missing_y','too_restrictive','invalid_side','no_source_domain','missing_correspondence','nonfunctional_correspondence'):
        cuts,m=numbers();c=cuts.make;r=cuts.read;indices=[0,1,2,3]
        if name=='reordered':indices.reverse()
        if name=='duplicate_equation':indices.append(0)
        if name=='empty':indices=[]
        if name=='missing_x':indices.remove(0)
        if name=='missing_y':indices.remove(1)
        def term(i,a,b,left):
            if name=='invalid_side' and i==3 and not left:return c(Q(99))
            n=vectors[a][i]+(2 if i==0 else 0) if left else vectors[b][i]
            if name=='too_restrictive' and i==1 and left:n+=1
            return c(Q(n))
        terms=tuple(FunctionValue(tuple(element['parameters']),element['result'],lambda a,b,left,i=i:term(i,a,b,left)) for i in indices)
        seq=SequenceValue(terms,json.dumps(element,sort_keys=True,separators=(',',':')))
        pairs={('a','c'),('b','d')}
        if name=='missing_correspondence':pairs.remove(('b','d'))
        if name=='nonfunctional_correspondence':pairs.add(('a','d'))
        m|={'eiyz':lambda t:t in ('a','b') and name!='no_source_domain','eiy2':lambda t:t in ('c','d','extra'),'eiyy':lambda a,b:(a,b) in pairs,'shh':lambda a,b:vectors[a]==vectors[b],'ba':lambda x:r(x)!=99}
        actual=run('eiy5',[seq],m,domain);expected=name in ('exact','reordered','duplicate_equation');assert actual==expected,(name,actual);count+=1;out[name]=actual
        if name=='exact':unknowns(lambda mm:run('eiy5',[seq],mm,domain),m,('eiyz','eiy2','eiyy','shh','ba','sca'))
    return dict(cases=count,outcomes=out,native_sgx_sgy_sgz_question_requires_exact_solution_set=True,empty_missing_extra_and_inconsistent_solutions_rejected=True,finite_example_not_a_physical_transformation_derivation=True)

def test_equation_checks():assert equation_checks()

def notation_rows():
    rows={'eislo':{(printed+'name',rule,'paper','discourse') for _,printed,rule,_,_ in COORDINATES}|{('tname','eiwt','paper','discourse'),('tauname','eiym','paper','discourse')},'eisd4':{('motion','author','kname','moving','paper','discourse')}}
    return rows

def presentation_checks():
    rows=notation_rows();m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiy6',[],mm),m,rows)
    rows|={'uh':{('claim','author','eiy3','section','discourse')},'zao':{('clocks','claim','section','discourse')},'zdc':{('task','author','eiy5','section','discourse')},'ue':{('claim','task','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiy7',[],mm),m,rows)
    assert run('eiy7',[],m|{n:forbidden for n in ('eiy3','eiy4','eiy5','eiyx','eixq','eiyi')});count+=1
    rows={'eir3':{('claim','author','paper','eiza','discourse')},'ue':{('clocks','claim','discourse')}};m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eizb',[],mm),m,rows)
    assert run('eizb',[],m|{n:forbidden for n in ('uh','zdc','eiy7','eiy3','eiy5')});count+=1
    return dict(cases=count,eight_quantities_and_preceding_k_name_bound=True,claim_and_equation_task_order_and_scope_distinguished=True,quoted_question_and_physical_content_not_executed=True)

def test_presentation_checks():assert presentation_checks()

def test_source_profile_and_saved_bridge():
    doc=check.restored()['document'];old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:78]==old['statements']
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert len(doc['declarations'])==1322 and len(doc['statements'])==79
    assert len(check.vocabulary()._words)==746
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[108] and len(b['source_declarations'])==221
    unit=b['source_units']['einstein-1905:u0046'];assert unit['range']==[0,289]
    assert len(''.join(re.sub(r'\[M\d+\]','',unit['text']).split()))==227
    assert [r['binding'] for r in b['math']]==['eiyx/ra','zbm','eiyx/zbm']
    assert b['text_boundaries']['spans']=={'zdb':['zda',28,42]}
    assert ds[mapping()['eiza']]['body']['force']=='assert'
    assert ds[mapping()['eiy5']]['result']['kind']=='question'
    assert 'eiy4' not in check.NEW_DEFINITIONS
    changed=deepcopy(doc);changed['statements'][78]['body']=dict(kind='truth',value=True)
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
    assert h['designationreference'](b['eirf'],b['zc2'],4,b['ri'])==b['eisnh']
    assert h['designationreference'](b['eirf'],b['zc3'],1,b['ri'])==b['eisnl']
    assert h['sentencetokenspanreference'](b['eirf'],b['zco'],24,b['zco'],60,b['ri'])==b['zcp']
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())

def test_task_span_rejects_changed_endpoints_and_unknown_inputs():
    b=check.BASE|{'zb7':cut(Q(3))};h=check.context_handlers(b)
    key=[b['eirf'],b['zda'],28,b['zda'],42,b['ri']]
    assert h['sentencetokenspanreference'](*key)==b['zdb']
    for slot in range(6):
        bad=key.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    for bad in (0,-1,1,27,29,43,Q(1,2),True,28.0,'28'):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['zda'],bad,b['zda'],42,b['ri'])
    for end in (27,41,43):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['zda'],28,b['zda'],end,b['ri'])

def test_whole_attribution_preserves_order_without_executing_the_question():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][78:79];b=check.BASE|{'zb7':cut(Q(3))}
    rows={'eir3':{(b['zda'],b['rd'],b['eirf'],'eiza',b['ri'])},'ue':{(b['zc3'],b['zda'],b['ri'])}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]
    for n in rows:assert native_run(doc,h|{mapping()[n]:lambda *xs:False})==[False]
