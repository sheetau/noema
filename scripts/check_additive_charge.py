"""Check finite signed contents, then distinguish spatial contract checks."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_comoving_labels import values
from scripts.check_rod_setup import callbacks
from scripts.check_field_equations import AXES
from scripts.compose_limits import call as k,app,v
from scripts.compose_additive_charge import ROOT,PARENT,BUILDERS,ROOTS,ADAPTER,SOURCE,CUT,POINT,BALL,MEASURE,DOMAIN,TOTAL

REPORT=ROOT/'reports/additive-charge-v1.json'
ATOMS=('first','second','outside')
SUBSETS=tuple(frozenset(ATOMS[i] for i in range(3) if bits[i]) for bits in product((False,True),repeat=3))


def function(sort,callback):return FunctionValue(tuple(sort['parameters']),sort['result'],callback)


def used_model(doc,model):return {d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


def finite_checks(text):
    region='h[a] c';domain='h['+region+'] c';totaltype='h['+region+'] '+CUT
    doc=abstract(parse(text+'r ja[] '+region+'.r jb[] '+domain+'.r jc[] '+totaltype+'.q[k seoq[k ja[] k jb[]]].q[k seor[k ja[] k jb[] k jc[]]].'),OPS)
    rows={}
    cases={'signed':(True,True),'zero':(True,True),'negative':(True,True),'empty_universe':(True,True),'restricted_domain':(True,True),
        'missing_empty':(False,False),'not_union_closed':(False,False),'not_difference_closed':(False,False),
        'domain_depends_on_outside':(False,False),'nonzero_empty':(True,False),
        'wrong_union':(True,False),'total_depends_on_outside':(True,False)}
    for variant,want in cases.items():
        cuts,model=setup(doc)
        active=frozenset() if variant=='empty_universe' else frozenset(ATOMS[:2])
        def members(r):return frozenset(a for a in ATOMS if r(a))
        def selected(r):
            raw=members(r);s=raw&active
            if variant=='missing_empty':return bool(s)
            if variant=='not_union_closed':return len(s)<2
            if variant=='not_difference_closed':return s!=frozenset(('second',))
            if variant=='domain_depends_on_outside':return 'outside' not in raw
            if variant=='restricted_domain':return 'second' not in s
            return True
        def total(r):
            raw=members(r);s=raw&active
            # Noema functions are total; values outside the selected domain are
            # arbitrary and are not accepted as regional quantities.
            if variant=='restricted_domain' and 'second' in s:return cuts.make(999)
            weights=(0,0) if variant=='zero' else (-3,-1) if variant=='negative' else (3,-1)
            value=sum(weights[i] for i,a in enumerate(ATOMS[:2]) if a in s)
            if variant=='nonzero_empty' and not s:value=1
            if variant=='wrong_union' and len(s)==2:value+=1
            if variant=='total_depends_on_outside' and 'outside' in raw:value+=1
            return cuts.make(value)
        callbacks(doc,model,{'ja':lambda a:a in active,'jb':selected,'jc':total})
        actual=values(doc,used_model(doc,model),ATOMS)
        if actual!=list(want):raise ValueError('Finite content '+variant+': '+repr(actual))
        rows[variant]=actual
    # Query actual seos for every subset, with signed cancellation and with a
    # wrong value. This enumerates the whole finite universe, not spatial cuts.
    textdoc=parse(text+'r ja[] '+region+'.r jb[] '+domain+'.r jc[] '+totaltype+'.r jd[] '+region+'.r je[] '+CUT+'.q[k seos[k ja[] k jb[] k jc[] k jd[] k je[]]].')
    textdoc=abstract(textdoc,OPS);samples=[]
    for subset in SUBSETS:
        for wrong in (False,True):
            cuts,model=setup(textdoc)
            charge=lambda r:sum(w for a,w in zip(ATOMS,(3,-3,0)) if r(a))
            expected=sum(w for a,w in zip(ATOMS,(3,-3,0)) if a in subset)
            callbacks(textdoc,model,{'ja':lambda a:a!='outside','jb':lambda r:True,
                'jc':lambda r:cuts.make(charge(r)),'jd':lambda a:a in subset})
            model['je']=lambda:cuts.make(expected+int(wrong))
            actual=values(textdoc,used_model(textdoc,model),ATOMS)
            if actual!=[not wrong]:raise ValueError('Regional signed total differs')
            samples.append(dict(region=sorted(subset),total=expected,wrong_value=wrong,result=actual[0]))
    return dict(domain_and_content=rows,regional_values=samples,
        all_eight_regions_and_all_region_pairs_quantified=True,arithmetic_is_rational_cut_interpretation=True,
        arbitrary_values_outside_selected_domain_do_not_constrain_content=True,continuous_space_or_countable_additivity_proved=False)


LOCAL=[('flow','a'),('frame','a'),('event','a'),('region',BALL),('lengthunit','a'),('chargeunit','a'),('value',CUT),('context','d')]
SYMBOLS={n:'jm'+number_word(i) for i,(n,_) in enumerate(ADAPTER+LOCAL)}
PEOPLE=AXES+('flow','frame','event','length','time','charge','other')
CENTER=(F(1),F(2),F(3),F(4))


def bridge_doc(text):
    extra=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in ADAPTER+LOCAL)
    query=app(k('seou',*(k(SYMBOLS[n]) for n,_ in ADAPTER)),*(k(SYMBOLS[n]) for n,_ in LOCAL))
    return abstract(candidate(text,extra+'q['+query+'].'),OPS|{'seor','seow'})


def bridge_model(doc,variant='baseline',weights=(F(3),F(-1))):
    cuts,model=setup(doc);make,read=cuts.make,cuts.read
    declarations={d['name']:d for d in doc['declarations']}
    for name,value in dict(distribution='flow',timeunit='time',flow='flow',frame='frame',event='event',lengthunit='length',chargeunit='charge',context='text').items():
        model[SYMBOLS[name]]=lambda value=value:value
    if variant=='wrong_distribution':model[SYMBOLS['distribution']]=lambda:'other'
    model[SYMBOLS['value']]=lambda:make(sum(weights)+(1 if variant=='wrong_value' else 0))
    point_sort=parse('n:r ja[] '+POINT+'.')['declarations'][0]['result']
    def point(x,t=F(4)):
        coords=(x,CENTER[1],CENTER[2],t)
        return function(point_sort,lambda axis:make(coords[AXES.index(axis)] if axis in AXES else 0))
    points=[point(F(1)),point(F(2)),point(F(1),F(5))]
    def region(p):return read(p('t'))==4 and sum((read(p(a))-CENTER[i])**2 for i,a in enumerate(AXES[:3]))<4
    def expected(actual,baseline,prefix,labels):
        baseline=list(baseline)
        for i,label in enumerate(labels):
            if variant==prefix+'_'+label:baseline[i]='other'
        return list(actual)==baseline
    def clock(frame,event,time,context):
        if variant=='unknown_clock':raise ValueError('Clock interpretation missing')
        ok=expected((frame,event,time,context),('frame','event','time','text'),'clock',('frame','event','timeunit','context'))
        return make(4 if ok else 5)
    def key(args,category):
        return expected(args,('frame','event','length','time','charge','text'),category,
            ('frame','event','lengthunit','timeunit','chargeunit','context'))
    domain_sort=declarations[SYMBOLS['domains']]['result']['result']
    total_sort=declarations[SYMBOLS['totals']]['result']['result']
    def domains(*args):
        if variant=='unknown_domain':raise ValueError('Region domain missing')
        ok=key(args,'domain')
        return function(domain_sort,lambda r:ok and variant!='outside_domain')
    def totals(*args):
        if variant=='unknown_total':raise ValueError('Total interpretation missing')
        ok=key(args,'total')
        return function(total_sort,lambda r:make(sum(w for p,w in zip(points[:2],weights) if r(p))+(0 if ok else 1)))
    def original(flow,frame,event,r,length,charge,value,context):
        if variant=='unknown_original':raise ValueError('Original electric attribution missing')
        return expected((flow,frame,event,[r(p) for p in points],length,charge,read(value),context),
            ('flow','frame','event',[True,True,False],'length','charge',sum(weights),'text'),'original',
            ('flow','frame','event','region','lengthunit','chargeunit','value','context'))
    def content(universe,domain,total):
        if variant=='unknown_content':raise ValueError('Spatial content interpretation missing')
        # A contract oracle only: actual finite-region laws are checked above.
        if variant=='inconsistent_content':return False
        return [universe(p) for p in points]==[True,True,False] and domain(function(declarations[SYMBOLS['region']]['result'],region))
    def spatial(universe,domain):
        if variant=='unknown_spatial':raise ValueError('Spatial representation interpretation missing')
        return variant!='nonspatial_regions'
    callbacks(doc,model,{SYMBOLS['original']:original,SYMBOLS['clock']:clock,
        SYMBOLS['domains']:domains,SYMBOLS['totals']:totals,SYMBOLS['region']:region})
    model['seor']=content
    model['seow']=spatial
    return used_model(doc,model)


def bridge_checks(texts):
    docs=[bridge_doc(text) for text in texts]
    def run(**options):
        rows=[values(doc,bridge_model(doc,**options),PEOPLE) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Extracted spatial charge differs')
        return rows[0]
    baselines=[]
    for weights in ((F(3),F(-1)),(F(3),F(-3)),(F(-3),F(-1))):
        row=run(weights=weights)
        if row!=[True]:raise ValueError('Signed spatial total rejected')
        baselines.append(dict(weights=[str(x) for x in weights],result=row[0]))
    contrasts={}
    names=['wrong_distribution','wrong_value','outside_domain','inconsistent_content','nonspatial_regions']
    for category,labels in (('original',('flow','frame','event','region','lengthunit','chargeunit','value','context')),
        ('clock',('frame','event','timeunit','context')),
        ('domain',('frame','event','lengthunit','timeunit','chargeunit','context')),
        ('total',('frame','event','lengthunit','timeunit','chargeunit','context'))):
        names += [category+'_'+label for label in labels]
    for name in names:
        row=run(variant=name)
        if row!=[False]:raise ValueError('Charge adapter ignored '+name)
        contrasts[name]=row[0]
    for doc in docs:
        for variant in ('unknown_original','unknown_clock','unknown_domain','unknown_total','unknown_content','unknown_spatial'):
            try:values(doc,bridge_model(doc,variant=variant),PEOPLE)
            except ValueError as exc:
                if 'missing' not in str(exc):raise
            else:raise ValueError('Unknown interpretation invented')
    return dict(cases=baselines,contrasts=contrasts,standalone_agrees=True,unknown_interpretations_refused=True,
        spatial_content_and_representation_are_explicit_contract_oracles=True,actual_spatial_additivity_proved=False)


def representation_probe(text):
    doc=parse(text);decl=next(d for d in doc['declarations'] if d['name']=='seow');region=decl['body']
    first=region['body']['arguments'][1];second=first['body']
    parameters=deepcopy(decl['parameters'])+[dict(name=n['variable'],sort=n['sort']) for n in (region,first,second)]
    body=dict(kind='implies',arguments=[deepcopy(region['body']['arguments'][0]),deepcopy(second['body'])])
    doc['declarations'].append(dict(kind='definition',name='jzz',parameters=parameters,result='truth',body=body));doc['statements']=[]
    extra=''.join('r '+n+'[] '+s+'.' for n,s in zip(('ja','jb','jc','jd','je'),(BALL,DOMAIN,BALL,POINT,POINT)))
    return abstract(parse(format_graph(doc,'compact')+extra+'q[k jzz[k ja[] k jb[] k jc[] k jd[] k je[]]].'),OPS)


def representation_checks(texts):
    docs=[representation_probe(text) for text in texts];rows={}
    for variant,want in (('same_coordinates',True),('hidden_component',False),('different_x',True),('outside_time',True),('excluded_region',True)):
        results=[]
        for doc in docs:
            cuts,model=setup(doc);make,read=cuts.make,cuts.read
            def first(axis):return make(CENTER[AXES.index(axis)] if axis in AXES else 0)
            def second(axis):
                if axis=='x' and variant=='different_x':return make(2)
                if axis=='t' and variant=='outside_time':return make(5)
                return make(CENTER[AXES.index(axis)] if axis in AXES else 7)
            hidden=variant in ('hidden_component','outside_time','excluded_region')
            callbacks(doc,model,{'ja':lambda p:read(p('t'))==4,'jb':lambda r:variant!='excluded_region',
                'jc':lambda p:read(p('other' if hidden else 'x'))<(1 if hidden else 2),'jd':first,'je':second})
            results.append(values(doc,used_model(doc,model),PEOPLE))
        if results!=[[want],[want]]:raise ValueError('Coordinate representation differs: '+variant)
        rows[variant]=want
    return dict(cases=rows,actual_region_and_point_clause_instantiated=True,not_a_full_spatial_domain_proof=True)


def structural_checks(generic,source):
    gd={d['name']:d for d in generic['declarations']};sd={d['name']:d for d in source['declarations']}
    point=parse('n:r ja[] '+POINT+'.')['declarations'][0]['result']
    def lift_sort(sort):
        if sort=='individual':return deepcopy(point)
        if isinstance(sort,dict):return {key:[lift_sort(x) for x in val] if isinstance(val,list) else lift_sort(val) for key,val in sort.items()}
        return sort
    def lift(node):
        if isinstance(node,list):return [lift(n) for n in node]
        if not isinstance(node,dict):return node
        return {key:lift_sort(val) if key in ('sort','result') else lift(val) for key,val in node.items()}
    for name in ROOTS[:5]:
        if lift(gd[name])!=sd[name]:raise ValueError('Spatial set laws differ from generic laws: '+name)
    adapter=sd['seou'];body=adapter['body']
    if body['kind']!='lambda':raise ValueError('Charge relation is not constructed')
    refs={n:dict(kind='variable',name=p['name']) for (n,_),p in zip(ADAPTER,adapter['parameters'],strict=True)}
    refs.update({n:dict(kind='variable',name=p['name']) for (n,_),p in zip(LOCAL,body['parameters'],strict=True)})
    apply=lambda name,names:dict(kind='apply',function=refs[name],arguments=[refs[n] for n in names])
    clock=apply('clock',('frame','event','timeunit','context'))
    keys=('frame','event','lengthunit','timeunit','chargeunit','context')
    domain,total=apply('domains',keys),apply('totals',keys)
    def flatten(node):return flatten(node['arguments'][0])+flatten(node['arguments'][1]) if node.get('kind')=='and' else [node]
    parts=flatten(body['body'])
    if len(parts)!=5 or parts[3].get('symbol')!='seow':raise ValueError('Charge adapter lost representation or attribution conditions')
    def expected_universe(universe):
        if universe['kind']!='lambda' or len(universe['parameters'])!=1:raise ValueError('Missing simultaneous spatial domain')
        return dict(kind='lambda',parameters=deepcopy(universe['parameters']),body=dict(kind='call',symbol='seot',arguments=[
            dict(kind='variable',name=universe['parameters'][0]['name']),clock]))
    expectedparts=[dict(kind='equal',arguments=[refs['flow'],refs['distribution']]),dict(kind='call',symbol='ba',arguments=[clock]),
        apply('original',[n for n,_ in LOCAL]),dict(kind='call',symbol='seow',arguments=[expected_universe(parts[3]['arguments'][0]),domain]),
        dict(kind='call',symbol='seos',arguments=[expected_universe(parts[4]['arguments'][0]),domain,total,refs['region'],refs['value']])]
    if parts!=expectedparts:raise ValueError('Charge adapter conflated original attribution, clock, units or regional totals')
    wrapper=sd['seov'];refs={n:dict(kind='variable',name=p['name']) for (n,_),p in zip(SOURCE,wrapper['parameters'],strict=True)}
    adapted=dict(kind='call',symbol='seou',arguments=[refs[n] for n in ('distribution','timeunit','measured','clock','domains','totals')])
    from scripts.compose_local_density import FIXED
    expected=dict(kind='call',symbol='seon',arguments=[refs['light']]+[adapted if n=='measured' else refs[n] for n,_ in FIXED]+[refs['electricassigned'],refs['frames']])
    if wrapper['body']!=expected:raise ValueError('Density/velocity route lost charge interpretation or shared units')
    return dict(spatial_laws_are_same_typed_schema=True,adapter_preserves_attribution_time_and_units=True,adapter_reaches_density_and_velocity=True)


def unbounded_check(text):
    result={}
    for symbol in ('seor','seow'):
        doc=bridge_doc(text);original=next(d for d in parse(text)['declarations'] if d['name']==symbol)
        doc['declarations']=[deepcopy(original) if d['name']==symbol else d for d in doc['declarations']]
        try:values(doc,bridge_model(doc),PEOPLE)
        except ValueError as exc:
            if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
            result[symbol]=str(exc)
        else:raise ValueError('All spatial regions were finitely certified')
    return result


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored additive charge differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Additive charge roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    previous=json.loads((ROOT/'reports/local-density-v1.json').read_text(encoding='utf-8'));segment=deepcopy(previous['alignment']['segments'][0])
    segment.update(definitions=['seor','seos','seou','seov'],review_ja='同時刻の領域に対する符号付き総量の有限加法性と外延的一致を、既存の電荷帰属・密度・速度へ結ぶ部分構成。電気的作用と校正の基礎説明、原文単位全体の意味確認は未完。')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_additive_charge.py','scripts/check_additive_charge.py','scripts/check_plane_waveforms.py',
        'scripts/check_rod_setup.py','scripts/check_comoving_labels.py','scripts/check_coordinate_correspondence.py',
        'scripts/check_described_appraisals.py','noema/finite_semantics.py','noema/extraction.py','reports/local-density-v1.json']
    return dict(status='partial_additive_regional_charge',documents=documents,sizes=sizes,
        finite=finite_checks(texts[0]),bridge=bridge_checks(texts[1:]),representation=representation_checks(texts[1:]),structure=structural_checks(parse(texts[0]),doc),
        unbounded=unbounded_check(texts[2]),alignment=dict(segments=[segment],semantic_completion=False),
        new_definitions=9,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Additive charge report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Signed regional totals, domain closure, extensionality and density connections checked')


if __name__=='__main__':main()
