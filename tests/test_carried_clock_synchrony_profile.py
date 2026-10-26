from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
import pytest
from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts.name_presentation_profile import scalar_text
from noema.meaning_catalog import _references
from scripts import check_einstein_carried_clock_synchrony as check
from scripts import carried_clock_synchrony_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
OLD_DOMAIN=('rod','ruler','observer','frame','movingframe','lengthunit','timeunit','xaxis','yaxis','zaxis','firstend','lastend','p','q','r','eventa','eventb','displaya','displayb','clocka','clockb','reference','placea','placeb','author','paper','scope','methoda','methodb','questionnode','lengthname','section','other')
RECORDS=('recorda7','recorda8','recordb7','recordb8')
DOMAIN=OLD_DOMAIN+('carrieda','carriedb','namea','nameb','syncname','addition','naming','initial','kinematicsnode','timeconvention')+RECORDS+tuple(prefix+str(i) for prefix in ('event','place','localclock','owndisplay','localdisplay') for i in range(4))
SITUATIONS=('methodactx','methodbctx','context','other')
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
def forbidden(*args):raise ValueError('Unknown carried-clock-synchrony input')
def value(x):return x
def ask(body):return dict(kind='ask',body=body)
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def context(doc,**kwargs):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE,**kwargs).items()}
def native_run(doc,h):return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame'}),situations=check.SITUATIONS,primitives=h)]

def old_constants():
    return {n:lambda x=x:x for n,x in {'xi':'rod','xj':'ruler','xk':'observer','ra':'frame','xl':'movingframe','ta':'lengthunit','rb':'timeunit','yn':'xaxis','yo':'yaxis','yp':'zaxis','xn':'firstend','xo':'lastend','xp':'eventa','xq':'eventb','xr':'clocka','xs':'clockb','xt':'placea','xu':'placeb','rc':'reference','ye':'methodactx','yf':'methodbctx','xw':'methoda','xx':'methodb','y3':'questionnode','rd':'author','eirf':'paper','xy':'scope','ri':'context','eisl6':'lengthname','eisdy':'section'}.items()}


def constants():return old_constants()|{n:lambda x=x:x for n,x in {'yd':'methodbctx','zaj':'carrieda','zak':'carriedb','zal':'addition','zam':'naming','y2':'initial','zv':'kinematicsnode','eisjd':'timeconvention','eismd':'syncname','eismf':'namea','eismg':'nameb'}.items()}


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);mapping=check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()
    selected=NUM|set(constants())|{'qo','se','eipk'}
    selected|={d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    if mode=='coverage':selected|={'eiqz','eiq2','lg'}
    if mode=='pair':selected|={'eiq4'}
    if mode=='clockrole':selected|={'eiqz'}
    selected.discard(name)
    symbols={mapping[n] for n in selected if n in mapping}
    for d in doc['declarations']:
        if d['name'] in symbols:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(mapping[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    target=ds[mapping[name]];slots=[]
    for i,p in enumerate(target['parameters']):
        slot='candidateslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(mapping[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jccscontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('jccscontext'))
    doc['statements']=[ask(body)];return doc,slots

def evaluate(doc,m,domain=DOMAIN):
    mapping=check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()
    h=handlers(doc)
    h.update({mapping.get(old,old):f for old,f in m.items() if mapping.get(old,old) in h})
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives=h,max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jccscontext':lambda:'context'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)
def unknowns(checker,m,names):
    for n in names:
        with pytest.raises(ValueError,match='Unknown carried-clock-synchrony'):checker(m|{n:forbidden})

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

def replace_real_sort(node):
    if node==RS:return 'individual'
    if isinstance(node,dict):return {k:replace_real_sort(v) for k,v in node.items()}
    if isinstance(node,list):return [replace_real_sort(v) for v in node]
    return node

def old_setup(length_a=5,length_b=4,time_a=7,time_b=7,target=7):
    cuts,m=arithmetic();c=cuts.make;r=cuts.read;m|=constants()
    m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b)),'zzbg':lambda a,b:r(a)<r(b),'yb':lambda:c(Q(2)),'x2':lambda:c(Q(time_a)),'x3':lambda:c(Q(time_b)),'xv':lambda:c(Q(target))}
    contexts=('methodactx','methodbctx');frames=('frame','movingframe');bodies=('rod','ruler','observer');roles=('xaxis','yaxis','zaxis');probes=('firstend','lastend','p','q','r')
    members={'rod':{'p','q'},'ruler':{'q','r'},'observer':{'p','r'}}
    def span(f):
        if f not in frames:forbidden()
        return (6,8) if f=='frame' else (16,18)
    def position(b,f,a,p,t):
        if b not in bodies or f not in frames or a not in roles or p not in DOMAIN:forbidden()
        length=Q(length_b if f=='frame' else length_a)
        x=length if p in ('lastend','q') else Q(0)
        if f=='frame':x+=2*(t-7)
        return (x,Q(0),Q(0))[roles.index(a)]+100*bodies.index(b)
    families={(b,f,ctx,a):FunctionValue(('individual',),FS,lambda p,b=b,f=f,a=a:FunctionValue((RS,),RS,lambda t:c(position(b,f,a,p,r(t))))) for b in bodies for f in frames for ctx in contexts for a in roles}
    def family(b,f,l,tu,a,ctx):
        if (l,tu)!=('lengthunit','timeunit') or (b,f,ctx,a) not in families:forbidden()
        return families[b,f,ctx,a]
    def bounds(f,tu,ctx,i):
        if tu!='timeunit' or ctx not in contexts:forbidden()
        return c(Q(span(f)[i]))
    def endpoint(b,f,ctx,last=False):
        if b!='rod' or f not in frames or ctx not in contexts:forbidden()
        return 'lastend' if last else 'firstend'
    def velocity(f,g,l,tu,a,ctx):
        if (f,g,l,tu)!=('frame','movingframe','lengthunit','timeunit') or a not in roles or ctx not in contexts:forbidden()
        return c(Q(2 if a=='xaxis' else 0))
    m|={'eisls':lambda f,t,ctx:bounds(f,t,ctx,0),'eislt':lambda f,t,ctx:bounds(f,t,ctx,1),'eislu':family,'eislv':endpoint,'eislw':lambda b,f,ctx:endpoint(b,f,ctx,True),'eislc':velocity,'eirh':lambda b,p,ctx:b in members and p in members[b] and ctx in contexts}
    return cuts,m,None,None,None


def setup():
    cuts,m,_,_,_=old_setup();c=cuts.make;r=cuts.read;m|=constants()
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result==RS:return tuple(r(x(c(Q(t)))) for t in (7,8))
            forbidden()
        return tuple(one(x) for x in xs)
    rows={n:set() for n in ('zaa','xf','xm','xg','zab','ce','cb','cc','qo','eisgm','zzbv','zzbu','se')}
    events=set();clocks={'reference','carrieda','carriedb'};record_data={}
    for i,record in enumerate(RECORDS):
        clock,end=('carrieda','firstend') if i<2 else ('carriedb','lastend');time=Q(7+i%2)
        event,place,local,own_display,local_display=(prefix+str(i) for prefix in ('event','place','localclock','owndisplay','localdisplay'))
        clocks.add(local);events.update((event,own_display,local_display));ctx='methodbctx'
        record_data[record]=(clock,end,event,place,local,time,time,ctx)
        rows['zaa'].add((clock,end,'rod',ctx));rows['xf'].add((end,'rod','frame',ctx));rows['xm'].add((clock,'frame',ctx))
        rows['xg'].add((end,event,place,'frame',ctx));rows['zab'].add((clock,event,place,'frame',ctx))
        for ck,display in ((clock,own_display),(local,local_display)):
            for ev in (event,display):rows['ce'].add((ck,ev,'frame','timeunit',time))
            rows['eisgm'].add((event,display,ck,'frame',ctx));rows['cb'].add((display,place,'frame'))
        rows['cb'].update(((local,place,'frame'),(event,place,'frame')));rows['cc'].add((local,'frame'));rows['qo'].add((local,'reference','frame','timeunit',ctx))
        x=2*(time-7)+(0 if end=='firstend' else 4)
        rows['zzbu'].add((event,'frame',ctx,'lengthunit','timeunit',time,x,Q(0),Q(0)))
        for obj in (clock,end):rows['zzbv'].add((obj,event,ctx))
    rows['cc'].add(('reference','frame'))
    for clock,end in (('carrieda','firstend'),('carriedb','lastend')):
        for obj in (clock,end):rows['se'].add((obj,'frame','methodbctx','lengthunit','timeunit',Q(6),Q(8),(Q(0 if end=='firstend' else 4),Q(2 if end=='firstend' else 6)),(Q(0),Q(0)),(Q(0),Q(0))))
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'ca':lambda ck:ck in clocks,'zbd':lambda e:e in events,'ci':lambda u:u=='timeunit'}
    return cuts,m,rows,norm,record_data


@lru_cache(None)
def local_checks():
    cuts,m,rows,norm,data=setup();c=cuts.make;count=0
    def args(record):
        ck,end,event,place,local,own,t,ctx=data[record];return [ck,end,event,place,local,c(own),c(t),ctx]
    for rec in RECORDS:assert run('eiq2',args(rec),m);count+=1
    selected='recorda7';check=lambda mm:run('eiq2',args(selected),mm)
    # Only remove rows actually consumed by this comparison; later records must
    # remain usable with their own distinct places and stationary local clocks.
    relevant={
      'zaa':{('carrieda','firstend','rod','methodbctx')},'xf':{('firstend','rod','frame','methodbctx')},'xm':{('carrieda','frame','methodbctx')},
      'xg':{('firstend','event0','place0','frame','methodbctx')},'zab':{('carrieda','event0','place0','frame','methodbctx')},
      'eisgm':{row for row in rows['eisgm'] if row[0]=='event0'},'ce':{row for row in rows['ce'] if row[1] in ('event0','owndisplay0','localdisplay0')},
      'cb':{row for row in rows['cb'] if row[1]=='place0'},'cc':{('localclock0','frame'),('reference','frame')},'qo':{('localclock0','reference','frame','timeunit','methodbctx')},
      'zzbv':{row for row in rows['zzbv'] if row[1]=='event0'},'zzbu':{row for row in rows['zzbu'] if row[0]=='event0'}}
    for n,rs in relevant.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rows[n]-{row}:norm(xs) in rs}),n;count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rows[n]-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    wrong=args(selected);wrong[5]=c(Q(8));assert not run('eiq2',wrong,m);count+=1
    wrong=args(selected);wrong[4]='carrieda';assert not run('eiq2',wrong,m);count+=1
    assert not check(m|{'rc':lambda:'carriedb'});count+=1
    # The successful model has no carried-clock cc row and no carried-clock qo row.
    assert all(row[0] not in ('carrieda','carriedb') for row in rows['cc']|rows['qo'])
    assert check(m|{'xv':forbidden,'ya':forbidden});count+=1
    unknowns(check,m,('ce','eisgm','qo','cc','zab','eislu','zzbv','zzbu'))
    unknown=FunctionValue(('number',),'truth',lambda x:x<7);wrong=args(selected);wrong[5]=unknown
    try:run('eiq2',wrong,m)
    except ValueError:pass
    else:raise AssertionError('Unknown displayed value decoded by sampling')
    return dict(cases=count,native_scv_sct_scu_eing_saf_and_sb_connected=True,same_event_position_and_both_local_displays=True,local_stationary_clock_can_change_with_position=True,no_carried_clock_stationarity_or_direct_reference_synchrony=True)


@lru_cache(None)
def attachment_checks():
    cuts,m,rows,norm,data=setup();count=0
    for clock,end in (('carrieda','firstend'),('carriedb','lastend')):
        check=lambda mm:run('eiqz',[clock,end,'methodbctx'],mm);assert check(m);count+=1
        for obj in (clock,end):
            row=next(row for row in rows['se'] if row[0]==obj)
            assert not check(m|{'se':lambda *xs,rs=rows['se']-{row}:norm(xs) in rs});count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{'se':lambda *xs,rs=(rows['se']-{row})|{changed}:norm(xs) in rs});count+=1
        assert not check(m|{'zaa':lambda *xs:False});count+=1
        unknowns(check,m,('se','zaa','eislu','eisls','eislt'))
    return dict(cases=count,clock_position_and_endpoint_share_complete_worldline=True,physical_attachment_not_coordinate_coincidence_alone=True,clock_internal_motion_not_frozen=True)


@lru_cache(None)
def coverage_checks():
    doc,slots=fixture('eiq4','coverage');projected=replace_real_sort(deepcopy(doc));count=0
    first,second='event0','event1';rec0,rec1='recorda7','recorda8'
    # Every individual in this declared finite carrier has an explicit selector
    # entry; non-records are known inactive inputs, never unknown-data defaults.
    def model(selected=(rec0,rec1),times=None,bad=None,complete=True):
        assigned={x:first for x in DOMAIN};assigned[rec1]=second
        if times:assigned.update(times)
        m=constants()|{'jccscontext':lambda:'context','eiqz':lambda *xs:True,'zai':lambda *xs:complete,
          'zac':lambda rec,ck,ctx:rec in selected and ck=='carrieda' and ctx=='methodbctx',
          'eisls':lambda *xs:first,'eislt':lambda *xs:second,'lg':lambda lo,hi,t:(lo,hi)==(first,second) and t in (first,second),
          'sca':lambda a,b:a==b,'zah':lambda rec:assigned[rec],
          'zad':lambda rec:rec,'zae':lambda rec:'place0','zaf':lambda rec:'localclock0','zag':lambda rec:assigned[rec],
          'eiq2':lambda ck,end,event,place,local,own,t,ctx:ck=='carrieda' and end=='firstend' and event!=bad and own==t and ctx=='methodbctx'}
        m|={n:lambda x=x:x for n,x in zip(slots,('carrieda','firstend','methodbctx'))}
        return m
    for selected,times,bad,complete,expected in (
       ((rec0,rec1),None,None,True,True),((rec0,),None,None,True,False),((rec1,),None,None,True,False),((),None,None,True,False),
       ((rec0,rec1),{rec1:first},None,True,False),((rec0,rec1),None,rec1,True,False),((rec0,rec1),None,None,False,False),
       ((rec0,rec1,'recordb7'),None,'recordb7',True,False)):
        assert evaluate(projected,model(selected,times,bad,complete))==expected;count+=1
    unknowns(lambda m:evaluate(projected,m),model(),('zac','zai','zah','eiq2','eiqz'))
    # Bind the actual projected body of the time witness, including the local
    # comparison. The two-time experiment above is not used in production Noema.
    assert all(d['result']!='individual' for d in doc['declarations'] if d['name'] in {check.mapping()[n] for n in ('eisls','eislt','zah')})
    # Real-cut quantification is refused after explicitly abstracting histories
    # and local comparisons, so refusal cannot be attributed only to se.
    cuts,m,_,_,_=setup();c=cuts.make
    assignments={x:Q(7) for x in DOMAIN};assignments[rec1]=Q(8)
    mm=constants()|{'eiqz':lambda *xs:True,'eiq2':lambda *xs:True,'zai':lambda *xs:True,'zac':lambda rec,ck,ctx:rec in (rec0,rec1),
       'eisls':lambda *xs:c(Q(6)),'eislt':lambda *xs:c(Q(8)),'lg':lambda lo,hi,t:cuts.read(lo)<=cuts.read(t)<=cuts.read(hi),'sca':lambda a,b:cuts.read(a)==cuts.read(b),
       'zad':lambda rec:rec,'zae':lambda rec:'place0','zaf':lambda rec:'localclock0','zag':lambda rec:c(assignments[rec]),'zah':lambda rec:c(assignments[rec])}
    try:run('eiq4',['carrieda','firstend','methodbctx'],mm,mode='coverage')
    except ValueError as e:assert 'Cannot finitely quantify the rational number domain' in str(e),str(e)
    else:raise AssertionError('Real time silently replaced by selected records')
    return dict(cases=count,every_time_requires_its_own_matching_record=True,all_selected_records_valid_and_nonempty=True,complete_record_metadata_not_sufficient_by_itself=True,finite_time_projection_only_and_full_real_domain_refused=True)


def test_profile_preserves_words_and_exposes_thirteen_existing_contracts():
    old=check.previous.vocabulary();new=check.vocabulary()
    assert len(old._words)==674 and len(new._words)==687
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert set(profile.SOURCE_RELATIONS)==set('zaa zab zac zad zae zaf zag zah zai zan zao eismc eisme'.split())

def test_visible_document_preserves_parent_and_selected_source():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:51]==old['statements']
    assert (len(doc['declarations']),len(doc['statements']),len(check.source_excerpt()['declarations']))==(978,55,147)
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[96] and b['sentence_positions']==dict(zal=[25,1])
    assert b['sentence_ranges']=={'einstein-1905:u0035':[[0,321]]}
    assert b['designation_positions']==dict(eismf=['zal',1],eismg=['zal',2],eismd=['zal',3])
    assert [row['binding'] for row in b['math']]==['eismf designates xn','eismg designates xo']

def test_attribution_and_presentation_preserve_quotes_and_directions():
    for rows,size in ((check.diagnostics(),8),(check.presentation_diagnostics(),26)):
        assert len(rows)==size and rows[0]['values']==[True]
        assert all(r['values']==[False] for r in rows[1:])
    calls=check.presentation_diagnostics()[0]['calls']
    assert next(r['arguments'][2:4] for r in calls if r['relation']=='eisme')==[['call','eiq7'],['call','eiq6']]
    assert next(r['arguments'][1:3] for r in calls if r['relation']=='eisdk')==[['call','eiq6'],['call','eiq7']]

def test_native_reference_lookups_do_not_execute_physical_roles_and_are_acyclic():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    for old in (*check.SENTENCES,*check.DESIGNATIONS,*check.ROLE_ASSIGNMENTS):
        doc['statements']=[ask(op('equal',call(n[old]),call('expected')))]
        assert native_run(doc,context(doc)|dict(expected=lambda:check.BASE[old]))==[True]
        assert native_run(doc,context(doc)|dict(expected=lambda:'other'))==[False]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.ROLE_ASSIGNMENTS:visit(n[old],set())

@pytest.mark.parametrize('field',range(4))
def test_each_role_reference_key_rejects_unknown_input(field):
    doc=deepcopy(check.restored()['document']);n=check.names()
    for old,(anchor,_) in check.ROLE_ASSIGNMENTS.items():
        roles=check.role_model(check.BASE)
        key=(check.BASE['eirf'],check.BASE[anchor],check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.BASE['ri'])
        found=roles.pop(key);bad=list(key);bad[field]='unknown';roles[tuple(bad)]=found
        doc['statements']=[ask(op('equal',call(n[old]),call(n[old])))]
        with pytest.raises(ValueError,match='Unknown temporal reference'):native_run(doc,context(doc,roles=roles))

def test_exact_printed_forms_and_designation_positions():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][-3:]
    expected={(old,'de',text,'body') for old,text in check.FORMS.items()};seen=[]
    def form(name,language,text,ctx):
        row=(name,scalar_text(language),scalar_text(text),ctx);seen.append(row);return row in expected
    h=context(doc);h[check.vocabulary()._symbols['printedform']]=form
    assert native_run(doc,h)==[True]*3 and set(seen)==expected
    refs=check.context_handlers(check.BASE)
    assert refs['designationreference'](check.BASE['eirf'],check.BASE['zal'],Q(3),check.BASE['ri'])=='eismd'
    for old,(node,item) in check.DESIGNATIONS.items():
        key=[check.BASE['eirf'],check.BASE[node],Q(item),check.BASE['ri']]
        for field in range(4):
            bad=list(key);bad[field]=Q(4) if field==2 else 'unknown'
            with pytest.raises(ValueError):refs['designationreference'](*bad)

def test_native_clock_role_body_binds_candidate_endpoint_and_moving_context():
    for role,endpoint in [('carriedroleclocka','firstend'),('carriedroleclockb','lastend')]:
        row=('carrieda',endpoint,'methodbctx')
        base=constants()|{'eiqz':lambda *xs:xs==row}
        assert run(role,['carrieda','context'],base,mode='clockrole')
        assert not run(role,['carriedb','context'],base,mode='clockrole')
        for slot in range(3):
            bad=tuple('other' if i==slot else x for i,x in enumerate(row))
            assert not run(role,['carrieda','context'],base|{'eiqz':lambda *xs:xs==bad},mode='clockrole')

def test_native_naming_role_preserves_every_argument_and_two_clock_order():
    doc=deepcopy(check.restored()['document']);n=check.names();m=check.mapping();inverse={v:k for k,v in m.items()}
    doc['declarations'].append(dict(kind='primitive',name='candidate',parameters=[],result='individual'))
    doc['statements']=[ask(call(n['carriedrolenaming'],call('candidate'),call(n['ri'])))]
    facts={name:check.presentation_facts()[name] for name in ('zan','eismc')}
    def relation(name,rows):
        def accept(*args):
            args=list(args);slot=2 if name=='zan' else 3
            node=renamed(json.loads(args[slot].syntax),inverse);args[slot]=(node['kind'],node['symbol'])
            if name=='eismc':args[4]=tuple(args[4].items)
            return tuple(args) in rows
        return accept
    h=context(doc)|dict(candidate=lambda:'zam')|{m[k]:relation(k,rs) for k,rs in facts.items()}
    assert native_run(doc,h)==[True]
    assert native_run(doc,h|dict(candidate=lambda:'other'))==[False]
    for name,rows in facts.items():
        row=rows[0]
        for i in range(len(row)):
            bad=list(row);bad[i]=('zak','zaj') if name=='eismc' and i==4 else 'other'
            assert native_run(doc,h|{m[name]:relation(name,[tuple(bad)])})==[False]

def test_native_local_comparison_keeps_event_place_both_displays_and_stationary_reference():
    result=local_checks();assert result['cases']>100 and result['no_carried_clock_stationarity_or_direct_reference_synchrony']

def test_native_attachment_binds_complete_worldlines_and_physical_connection():
    result=attachment_checks();assert result['cases']>40 and result['physical_attachment_not_coordinate_coincidence_alone']

def test_native_coverage_requires_every_time_and_every_selected_record():
    result=coverage_checks();assert result['cases']==8 and result['finite_time_projection_only_and_full_real_domain_refused']

def test_native_record_witness_binds_every_selected_record_field():
    doc,slots=fixture('eiq3','coverage');doc=replace_real_sort(doc)
    expected=('left','right','left','right','left','left','left','methodbctx')
    m=constants()|{'ra':lambda:'left','rb':lambda:'right',
        'eisls':lambda *xs:'left','eislt':lambda *xs:'right',
        'lg':lambda lo,hi,t:(lo,hi,t)==('left','right','left'),'sca':lambda a,b:a==b,
        'zac':lambda rec,ck,ctx:(rec,ck,ctx)==('left','left','methodbctx'),
        'zad':lambda rec:'left','zae':lambda rec:'right','zaf':lambda rec:'left',
        'zag':lambda rec:'left','zah':lambda rec:'left','eiq2':lambda *xs:xs==expected}
    m|={n:lambda x=x:x for n,x in zip(slots,('left','right','left','methodbctx'))}
    test=lambda mm:evaluate(doc,mm,domain=('left','right'))
    assert test(m)
    for i in range(len(expected)):
        bad=tuple(('right' if x=='left' else 'left') if j==i else x for j,x in enumerate(expected))
        assert not test(m|{'eiq2':lambda *xs:xs==bad})
    for field in ('zad','zae','zaf','zag','zah'):
        replacement='left' if field=='zae' else 'right'
        assert not test(m|{field:lambda rec:replacement})
    for field in ('zac','lg'):
        assert not test(m|{field:lambda *xs:False})
    unknowns(test,m,('zac','zad','zae','zaf','zag','zah','eiq2'))

def test_native_qualification_accepts_either_witness_endpoint():
    for endpoint in ('firstend','lastend'):
        m=constants()|{'eiq4':lambda ck,end,ctx:(ck,end,ctx)==('carrieda',endpoint,'methodbctx')}
        assert run('eiq5',['carrieda','methodbctx'],m,'pair')
        assert not run('eiq5',['carriedb','methodbctx'],m,'pair')
    assert not run('eiq5',['carrieda','methodbctx'],constants()|{'eiq4':lambda *xs:False},'pair')

def test_native_pair_uses_distinct_clocks_and_the_same_rod_endpoints():
    rows={'eipk':{('methodbctx',)},'eiq4':{('carrieda','firstend','methodbctx'),('carriedb','lastend','methodbctx')}}
    m=constants()|{'eislv':lambda *xs:'firstend','eislw':lambda *xs:'lastend'}|{n:lambda *xs,rs=rs:xs in rs for n,rs in rows.items()}
    assert run('eiq6',[],m,'pair')
    for name,rs in rows.items():
        for row in rs:
            for slot in range(len(row)):
                bad=tuple('other' if i==slot else x for i,x in enumerate(row))
                assert not run('eiq6',[],m|{name:lambda *xs,rs=rs-{row}|{bad}:xs in rs},'pair')
    for name in ('eislv','eislw'):
        assert not run('eiq6',[],m|{name:lambda *xs:'other'},'pair')
    assert not run('eiq6',[],m|{'zak':lambda:'carrieda','eiq4':lambda *xs:True},'pair')
    assert not run('eiq6',[],m|{'xo':lambda:'firstend','eislw':lambda *xs:'firstend','eiq4':lambda *xs:True},'pair')

def test_changed_composition_or_reference_cannot_reuse_old_evidence():
    for old in (*check.NEW_DEFINITIONS,*check.ROLE_HELPERS,*check.ROLE_ASSIGNMENTS,*check.DESIGNATIONS):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
