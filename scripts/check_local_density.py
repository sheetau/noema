"""Check local density without treating sampled ball profiles as real limits."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json

from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.rational_proofs import verify
from noema.polynomial_proofs import verify_universal
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_field_equations import AXES
from scripts.check_moving_light_trip import literal
from scripts.check_real_products import assertion,MEANINGS
from scripts.compose_limits import call as k,app,op,both,v
from scripts.compose_local_density import ROOT,PARENT,BUILDERS,CUT,POINT,BOUND,NORMAL,FIXED,LIMIT

REPORT=ROOT/'reports/local-density-v1.json'
CENTER=tuple(map(F,(1,2,3,4)))
PEOPLE=AXES+('marker','flow','frame','event','length','time','charge','other')
SYMBOLS={n:'jm'+number_word(i) for i,(n,_) in enumerate(NORMAL)}


def rational_checks():
    base=format_graph(extract_document(parse((ROOT/'examples/v011/limits.noema').read_text(encoding='utf-8')),roots=['kc'],statement_indices=[]).document,'compact')
    base+='r ad[b b] b.'
    domain='i[x b]['+both(k('aa',literal(0),v('x')),k('aa',v('x'),literal(3)))+']'
    rows={}
    cases=[('affine_right_limit',4,2,4,'valid'),('wrong_limit',4,2,5,'invalid'),
        ('negative_constant',-4,0,-4,'valid'),('zero_constant',0,0,0,'valid')]
    for name,rho,slope,result,want in cases:
        fn='i[x b]['+k('ab',literal(rho),k('ad',literal(slope),v('x')))+']'
        row=verify(parse(base+'s['+k('kc',domain,fn,literal(0),literal(result))+'].'),MEANINGS,timeout_ms=15000)[0]
        if row['status']!=want:raise ValueError('Rational local limit '+name+': '+row['status'])
        rows[name]=row
    empty='i[x b]['+op('u',op('e',v('x'),v('x')))+']'
    row=verify(parse(base+'s['+k('kc',empty,'i[x b][v x]',literal(0),literal(0))+'].'),MEANINGS,timeout_ms=15000)[0]
    if row['status']!='invalid':raise ValueError('Empty radii became a limit')
    rows['empty_approach']=row
    mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b)
    q,V,rho,L,C,Q,W,d=map(v,('charge','volume','density','lengthscale','chargescale','newcharge','newvolume','newdensity'))
    cube=mul(L,mul(L,L))
    premise=both(k('aa',literal(0),V),k('aa',literal(0),L),k('aa',literal(0),C),eq(q,mul(rho,V)),eq(Q,mul(C,q)),eq(W,mul(cube,V)),eq(mul(d,cube),mul(C,rho)))
    algebra='n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
    claim=assertion('charge volume density lengthscale chargescale newcharge newvolume newdensity',op('y',premise,eq(Q,mul(d,W))))
    valid=verify_universal(parse(algebra+claim),MEANINGS,timeout_ms=25000)[0]
    if valid['status']!='valid':raise ValueError('Charge/volume unit scaling differs')
    # Q=12, V=3, rho=4. Rescaling coordinates by 2 and charge values by
    # 3 gives Q'=36, V'=24 and rho'=3/2, while all scaling premises hold.
    concrete=both(*[k('aa',literal(0),literal(x)) for x in (3,2,3)],
        eq(literal(12),mul(literal(4),literal(3))),
        eq(literal(36),mul(literal(3),literal(12))),
        eq(literal(24),mul(literal(8),literal(3))),
        eq(mul(literal(F(3,2)),literal(8)),mul(literal(3),literal(4))))
    invalid=verify_universal(parse(algebra+assertion('',op('y',concrete,eq(literal(F(3,2)),literal(4))))),MEANINGS,timeout_ms=25000)[0]
    if invalid['status']!='invalid':raise ValueError('Changed density unit was ignored')
    return dict(limits=rows,unit_scaling=valid,density_value_invariant_under_changed_units=invalid,
        rational_comparison_only=True,all_real_ball_density_or_pi_proved=False)


def ball_checks(text):
    doc=abstract(candidate(text,'r ja[] '+POINT+'.r jb[] '+CUT+'.r jc[] '+POINT+'.q[k seog[k ja[] k jb[] k jc[]]].'),OPS)
    points=[('center',(0,0,0,0),2,True),('inside',(1,1,1,0),2,True),('boundary',(2,0,0,0),2,False),
        ('outside',(2,1,0,0),2,False),('other_time',(0,0,0,1),2,False),('zero_radius',(0,0,0,0),0,False),('negative_radius',(0,0,0,0),-2,False)]
    rows={}
    for label,offset,radius,want in points:
        cuts,model=setup(doc);make=cuts.make;model['jb']=lambda:make(radius)
        callbacks(doc,model,{'ja':lambda a:make(CENTER[AXES.index(a)] if a in AXES else 0),
            'jc':lambda a:make(CENTER[AXES.index(a)]+offset[AXES.index(a)] if a in AXES else 0)})
        used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        row=values(doc,{n:f for n,f in model.items() if n in used},PEOPLE)
        if row!=[want]:raise ValueError('Simultaneous spatial ball '+label)
        rows[label]=row
    return rows


def average_checks(text):
    doc=abstract(candidate(text,''.join('r '+n+'[] '+CUT+'.' for n in ('ja','jb','jc'))+'q[k seoh[k ja[] k jb[] k jc[]]].'),OPS)
    rows=[]
    cases=[(rho*volume,volume,rho,True) for rho in (-4,0,3) for volume in (F(1,2),F(1),F(4))]
    cases += [(F(0),F(0),F(0),False),(F(-4),F(-1),F(4),False),(F(4),F(1),F(5),False)]
    for charge,volume,average,want in cases:
        cuts,model=setup(doc)
        for name,value in zip(('ja','jb','jc'),(charge,volume,average)):model[name]=lambda value=value:cuts.make(value)
        used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'};actual=values(doc,{n:f for n,f in model.items() if n in used},PEOPLE)
        if actual!=[want]:raise ValueError('Signed average or positive volume guard differs')
        rows.append(dict(charge=str(charge),volume=str(volume),average=str(average),result=actual[0]))
    return rows


def flatten(node):
    if node.get('kind')=='and':return flatten(node['arguments'][0])+flatten(node['arguments'][1])
    return [node]


def conjunction(nodes):
    return nodes[0] if len(nodes)==1 else dict(kind='and',arguments=[nodes[0],conjunction(nodes[1:])])


def bound_probe(text):
    doc=parse(text);ds={d['name']:d for d in doc['declarations']};parts=flatten(ds['seok']['body']);radius=parts[-1]
    if radius['kind']!='forall':raise ValueError('Expected every-radius source condition')
    helper=dict(kind='definition',name='jzz',parameters=deepcopy(ds['seok']['parameters'])+[dict(name=radius['variable'],sort=radius['sort'])],
        result='truth',body=conjunction(parts[:-1]+[radius['body']]))
    doc['declarations'].append(helper);doc['statements']=[]
    fixture=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in NORMAL)+'r jzy[] '+CUT+'.'
    local=k('jzz',*(k(SYMBOLS[n]) for n,_ in BOUND),k('jzy'))
    normal=k('seml',*(k(SYMBOLS[n]) for n in ('pi','normalized','density')))
    return abstract(parse(format_graph(doc,'compact')+fixture+''.join('q['+x+'].' for x in (local,normal,both(local,normal)))),OPS|{'seoi','sjr','sedm','sedi'})


def bound_model(doc,rho=F(4),slope=F(2),radius=F(1),variant='baseline'):
    cuts,model=setup(doc);make,read=cuts.make,cuts.read;upper=F(0) if variant=='empty_approach' else F(3)
    for n,value in dict(matter='marker',distribution='flow',frame='frame',event='event',context='text',lengthunit='length',timeunit='time',chargeunit='charge').items():model[SYMBOLS[n]]=lambda value=value:value
    for n,value in dict(upper=upper,pi=F(3),density=rho+(1 if variant=='wrong_limit' else 0),normalized=12*rho+(1 if variant=='wrong_normalized' else 0)).items():model[SYMBOLS[n]]=lambda value=value:make(value)
    model['jzy']=lambda:make(radius)
    def volume(r):return 4*r*r*r
    def average(r):
        if r==0:raise ValueError('Zero-radius average must not be evaluated')
        return rho+slope*r
    def qfn(r):return make(average(read(r))*volume(read(r)))
    def vfn(r):return make((0 if variant=='zero_volume' else -1 if variant=='negative_volume' else 1)*volume(read(r)))
    def afn(r):return make(average(read(r))+(1 if variant=='wrong_average' else 0))
    callbacks(doc,model,{SYMBOLS['point']:lambda a:make(CENTER[AXES.index(a)] if a in AXES else 0),
        SYMBOLS['charge']:qfn,SYMBOLS['volume']:vfn,SYMBOLS['average']:afn})
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='other'
        return list(actual)==expected
    def measured(flow,frame,event,region,lengthunit,chargeunit,value,context):
        if variant=='unknown_measure':raise ValueError('Charge assignment missing')
        pointsort=next(d['result'] for d in doc['declarations'] if d['name']==SYMBOLS['point'])
        shape=True
        for offset,want in (((0,0,0,0),True),((radius,0,0,0),False),((radius/2,0,0,0),True),((0,0,0,1),False)):
            point=FunctionValue(tuple(pointsort['parameters']),pointsort['result'],lambda a,offset=offset:make(CENTER[AXES.index(a)]+offset[AXES.index(a)] if a in AXES else 0))
            shape=shape and region(point)==want
        return match((flow,frame,event,lengthunit,chargeunit,read(value),context,shape),
            ('flow','frame','event','length','charge',average(radius)*volume(radius),'text',True),'measure',
            ('distribution','frame','event','lengthunit','chargeunit','value','context','region'))
    def units(frame,length,time,context):
        if variant=='unknown_units':raise ValueError('Coordinate unit convention missing')
        return match((frame,length,time,context),('frame','length','time','text'),'units',('frame','lengthunit','timeunit','context'))
    def member(marker,flow,context):
        if variant=='unknown_member':raise ValueError('Distribution membership missing')
        return match((marker,flow,context),('marker','flow','text'),'member',('matter','distribution','context'))
    callbacks(doc,model,{SYMBOLS['measured']:measured,SYMBOLS['chartunits']:units,SYMBOLS['member']:member})
    def location(matter,frame,event,point,context):
        if variant=='unknown_location':raise ValueError('Point location missing')
        return match((matter,frame,event,tuple(read(point(a)) for a in AXES),context),('marker','frame','event',CENTER,'text'),
            'location',('matter','frame','event','point','context'))
    def profile(cap,charge,vol,avg):
        if variant=='unknown_profile':raise ValueError('Full profile consistency missing')
        cap=read(cap)
        return cap>0 and all(read(vol(make(r)))>0 and read(charge(make(r)))==read(vol(make(r)))*read(avg(make(r))) for r in (cap/4,cap/2,3*cap/4))
    def limit(domain,fn,point,value):
        if variant=='unknown_limit':raise ValueError('Real limit interpretation missing')
        if upper<=0:return False
        return read(point)==0 and not domain(make(0)) and not domain(make(-1)) and not domain(make(upper)) and all(
            domain(make(r)) and read(fn(make(r)))==average(r) for r in (upper/4,upper/2,3*upper/4)) and read(value)==rho
    model.update(va=lambda frame:frame=='frame',zpb=location,seoi=profile,sjr=limit,
        sedi=lambda pi:variant!='missing_pi' and read(pi)==3,
        sedm=lambda r,pi,vol:read(pi)==3 and read(r)>0 and read(vol)==volume(read(r)))
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:f for n,f in model.items() if n in used}


def binding_checks(texts):
    docs=[bound_probe(text) for text in texts]
    def run(**options):
        rows=[values(doc,bound_model(doc,**options),PEOPLE) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Extracted density binding differs')
        return rows[0]
    cases=[]
    for rho,slope in ((F(-4),F(0)),(F(0),F(0)),(F(4),F(0)),(F(-4),F(2)),(F(4),F(-1))):
        for radius in (F(1,2),F(1),F(2)):
            row=run(rho=rho,slope=slope,radius=radius)
            if row!=[True]*3:raise ValueError('Signed local density or profile rejected')
            cases.append(dict(density=str(rho),slope=str(slope),radius=str(radius),results=row))
    contrasts={}
    for category,labels in (('location',('matter','frame','event','point','context')),('member',('matter','distribution','context')),
        ('measure',('distribution','frame','event','lengthunit','chargeunit','value','context','region')),('units',('frame','lengthunit','timeunit','context'))):
        for label in labels:
            name=category+'_'+label;row=run(variant=name)
            if row!=[False,True,False]:raise ValueError('Local density referents ignored: '+name)
            contrasts[name]=row
    numeric={}
    for name in ('zero_volume','negative_volume','wrong_average','wrong_limit','wrong_normalized','empty_approach','missing_pi'):
        row=run(variant=name);expected=[False,False,False] if name in ('wrong_limit','missing_pi') else [True,False,False] if name=='wrong_normalized' else [False,True,False]
        if row!=expected:raise ValueError('Density/normalization condition differs: '+name+repr(row))
        numeric[name]=row
    for doc in docs:
        for variant in ('unknown_measure','unknown_units','unknown_member','unknown_location','unknown_profile','unknown_limit'):
            try:values(doc,bound_model(doc,variant=variant),PEOPLE)
            except ValueError as exc:
                if 'missing' not in str(exc):raise
            else:raise ValueError('Missing density interpretation invented')
    return dict(cases=cases,contrasts=contrasts,numeric=numeric,standalone_agrees=True,
        zero_radius_average_not_evaluated=True,profile_limit_and_volume_are_explicit_oracles=True,
        pi_oracle_is_synthetic=True,actual_pi_or_all_real_density_proved=False,unknown_interpretations_refused=True)


def structural_checks(doc):
    ds={d['name']:d for d in doc['declarations']};factory=ds['seom'];body=factory['body']
    if body['kind']!='lambda':raise ValueError('Density assignment is not constructed')
    fixed={n:p['name'] for (n,_),p in zip(FIXED,factory['parameters'],strict=True)}
    local={n:p['name'] for n,p in zip(('matter','frame','event','normalized','context'),body['parameters'],strict=True)}
    body=body['body'];witnesses={}
    for name,_ in [('point',POINT)]+LIMIT:
        if body['kind']!='exists':raise ValueError('Local density profiles must exist')
        witnesses[name]=body['variable'];body=body['body']
    names=fixed|local|witnesses
    expected=dict(kind='call',symbol='seol',arguments=[dict(kind='variable',name=names[n]) for n,_ in NORMAL])
    if body!=expected:raise ValueError('Density factory conflated distribution, marker, units or normalized value')
    scalar=flatten(ds['seoi']['body'])[-1];binding=flatten(ds['seok']['body'])[-1]
    if scalar['kind']!='forall' or binding['kind']!='forall':raise ValueError('Every-radius condition replaced by a selected sample')
    limit=flatten(ds['seoj']['body'])[-1]
    expectedzero=parse('n:r bb[b] c.q[k bb[n p a b]].')['statements'][0]['body']
    if limit.get('symbol')!='sjr' or limit['arguments'][2]!=expectedzero:raise ValueError('Local limit point is not zero')
    wrapper=ds['seon'];content=wrapper['body']
    if content['kind']!='content':raise ValueError('Density/velocity content was removed')
    refs=[dict(kind='variable',name=p['name']) for p in wrapper['parameters']]
    constructed=dict(kind='call',symbol='seom',arguments=refs[1:9])
    expectedcontent=dict(kind='and',arguments=[dict(kind='call',symbol='sedi',arguments=[refs[2]]),
        dict(kind='evaluate',content=dict(kind='call',symbol='seof',arguments=[refs[0],constructed,refs[9],refs[10]]),
            situation=dict(kind='variable',name=content['variable']))])
    if content['body']!=expectedcontent:raise ValueError('Source content bypassed density construction or shared pi')
    return dict(existential_profiles=True,distribution_fixed_and_marker_bound=True,units_shared=True,
        every_positive_radius_required=True,limit_is_at_zero=True,content_uses_constructed_density_and_velocity=True)


def unbounded_check(text):
    # Restore each infinite condition separately to verify it is not silently
    # interpreted by the fixture's selected radii.
    result={}
    for symbol in ('seoi','sjr'):
        doc=bound_probe(text);original=next(d for d in parse(text)['declarations'] if d['name']==symbol)
        doc['declarations']=[deepcopy(original) if d['name']==symbol else d for d in doc['declarations']]
        try:values(doc,bound_model(doc),PEOPLE)
        except ValueError as exc:
            if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
            result[symbol]=str(exc)
        else:raise ValueError('Full density limit was finitely certified')
    return result


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored density differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Density roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    previous=json.loads((ROOT/'reports/material-velocity-v1.json').read_text(encoding='utf-8'));segment=deepcopy(previous['alignment']['segments'][0])
    segment.update(definitions=['seok','seol','seom','seon'],review_ja='球内の総電荷・体積・比の局所極限と4pi規格化を、追跡点が属する分布と単位へ結ぶ部分構成。電気量の測定の実現と全文の意味確認は未完。')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_local_density.py','scripts/check_local_density.py','examples/v011/limits.noema',
        'scripts/check_plane_waveforms.py','scripts/check_rod_setup.py','scripts/check_comoving_labels.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_real_products.py',
        'scripts/check_moving_light_trip.py','noema/finite_semantics.py','noema/rational_proofs.py','noema/polynomial_proofs.py','noema/extraction.py',
        'reports/material-velocity-v1.json']
    return dict(status='partial_local_ball_charge_density',documents=documents,sizes=sizes,
        rational=rational_checks(),balls=ball_checks(texts[0]),averages=average_checks(texts[0]),finite=binding_checks(texts[1:]),
        structure=structural_checks(doc),unbounded=unbounded_check(texts[2]),alignment=dict(segments=[segment],semantic_completion=False),
        new_definitions=8,new_primitives=0,new_author_statements=0,parent_preserved=True,roundtrips=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Density report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Local ball density, signed averages, units, distribution membership and limit refusals checked')


if __name__=='__main__':main()
