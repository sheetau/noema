"""Verify velocity bindings while refusing finite certification of real histories."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json

from noema.finite_semantics import FunctionValue
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_field_equations import AXES
from scripts.check_material_charge import numbers
from scripts.check_parallel_composition import transform
from scripts.compose_limits import call as k,app
from scripts.compose_material_velocity import ROOT,PARENT,BUILDERS,TRACK,AT,SOURCE,INPUTS,CUT,POINT,DOMAIN,CURVE,DENSITY

REPORT=ROOT/'reports/material-velocity-v1.json'
PEOPLE=AXES+('matter','frame','event','later','old','new','other')
CENTER=tuple(map(F,(1,2,3,4)))
SYMBOLS={n:'jm'+number_word(i) for i,(n,_) in enumerate(AT)}
SOURCE_SYMBOLS={n:'jn'+number_word(i) for i,(n,_) in enumerate(SOURCE)}


def fv(sort,callback):return FunctionValue(tuple(sort['parameters']),sort['result'],callback)


def generic_fixture():
    text=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in AT)+'r jmo[] a.r jmp[] '+CUT+'.'
    args=lambda items:[k(SYMBOLS[n]) for n,_ in items]
    time=app(k(SYMBOLS['point']),k('zc7'))
    text+='q['+k('seoa',*args(TRACK),k(SYMBOLS['event']),time)+'].'
    text+='q['+k('seoa',*args(TRACK),k('jmo'),k('jmp'))+'].'
    text+='q['+k('seoc',*args(AT))+'].'
    text+='q['+k('senz',k(SYMBOLS['domain']),time)+'].'
    return text


def generic_model(doc,velocity=(1,-2,3),quadratic=(0,0,0),variant='baseline'):
    cuts,model=setup(doc);make,read=cuts.make,cuts.read
    decls={d['name']:d for d in doc['declarations']};u=tuple(map(F,velocity));q=tuple(map(F,quadratic))
    scale=2 if variant=='proper_parameter' else 1
    def curve_at(t):
        dt=scale*(t-CENTER[3]);offset=1 if variant=='wrong_curve_position' else 0
        return tuple(CENTER[i]+u[i]*dt+q[i]*dt*dt+offset for i in range(3))+(CENTER[3]+dt,)
    def domain(t):
        t=read(t)
        if variant=='isolated':return t==CENTER[3]
        if variant=='one_sided':return t>=CENTER[3]
        if variant=='empty_domain':return False
        return True
    def curve(t):
        row=curve_at(read(t));return fv(decls[SYMBOLS['curve']]['result']['result'],lambda axis:make(row[AXES.index(axis)] if axis in AXES else 0))
    model.update({SYMBOLS['matter']:lambda:'matter',SYMBOLS['frame']:lambda:'frame',SYMBOLS['context']:lambda:'text',
        SYMBOLS['event']:lambda:'event','jmo':lambda:'later','jmp':lambda:make(CENTER[3]+1)})
    for i,name in enumerate(('ux','uy','uz')):
        value=u[i]*scale+(1 if variant=='wrong_'+name else 0);model[SYMBOLS[name]]=lambda value=value:make(value)
    callbacks(doc,model,{SYMBOLS['curve']:curve,SYMBOLS['domain']:domain,
        SYMBOLS['point']:lambda axis:make(CENTER[AXES.index(axis)] if axis in AXES else 0)})
    def location(matter,frame,event,point,context):
        if variant=='unknown_location':raise ValueError('Location interpretation missing')
        expected=['matter','frame',event,'text']
        for i,name in enumerate(('matter','frame','event','context')):
            if variant=='wrong_'+name:expected[i]='other'
        if [matter,frame,event,context]!=expected or event not in ('event','later'):return False
        row=CENTER if event=='event' else curve_at(CENTER[3]+1)
        return tuple(read(point(a)) for a in AXES)==row
    observed=[]
    def derivative(domain,fn,time,value):
        if variant=='unknown_derivative':raise ValueError('Derivative interpretation missing')
        t=read(time);center=read(fn(make(t)));left=read(fn(make(t-1)));right=read(fn(make(t+1)))
        slope=(right-left)/2;curvature=(right+left-2*center)/2
        if any(read(fn(make(t+d)))!=center+slope*d+curvature*d*d for d in (-2,2)):raise ValueError('Fixture is not its stated quadratic')
        observed.append((slope,read(value)))
        return variant!='missing_derivative' and domain(time) and slope==read(value)
    def history(matter,frame,context,domain,curve):
        if variant=='unknown_history':raise ValueError('Whole-history interpretation missing')
        # This is an explicit premise oracle, never a finite proof of seob.
        return variant not in ('missing_history','proper_parameter','empty_domain','conflicting_record')
    def interior(domain,time):
        if variant=='unknown_interior':raise ValueError('Interior interpretation missing')
        return variant not in ('isolated','one_sided','empty_domain') and domain(time)
    model.update(zpb=location,sjs=derivative,seob=history,senz=interior)
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:f for n,f in model.items() if n in used},observed


def generic_checks(texts):
    docs=[abstract(candidate(text,generic_fixture()),OPS|{'sjs','seob','senz'}) for text in texts]
    def run(**options):
        rows=[]
        for doc in docs:
            model,observed=generic_model(doc,**options);rows.append(values(doc,model,PEOPLE))
            if len(observed)!=3:raise ValueError('Three coordinate derivatives were not kept')
        if rows[0]!=rows[1] or rows[0]!=rows[2]:raise ValueError('Extracted material velocity differs')
        return rows[0]
    cases=[]
    for velocity,quadratic in (((0,0,0),(0,0,0)),((1,-2,3),(0,0,0)),((-2,4,-3),(0,0,0)),((1,-2,3),(1,-1,2)),((0,0,0),(2,3,-1))):
        row=run(velocity=velocity,quadratic=quadratic)
        if row!=[True]*4:raise ValueError('Known affine or quadratic derivative rejected')
        cases.append(dict(velocity=list(velocity),quadratic=list(quadratic),results=row))
    contrasts={}
    variants=['wrong_'+n for n in ('ux','uy','uz','matter','frame','event','context')]+[
        'wrong_curve_position','missing_derivative','missing_history','conflicting_record','proper_parameter','isolated','one_sided','empty_domain']
    for variant in variants:
        row=run(variant=variant)
        expected=[True,True,False,True]
        if variant in ('wrong_matter','wrong_frame','wrong_event','wrong_context'):expected=[False,False,False,True]
        if variant in ('wrong_curve_position','proper_parameter'):expected=[variant=='proper_parameter',variant=='wrong_curve_position',False,True]
        if variant=='isolated':expected=[True,False,False,False]
        if variant=='one_sided':expected=[True,True,False,False]
        if variant=='empty_domain':expected=[False]*4
        if row!=expected:raise ValueError('Coordinate velocity contrast '+variant+': '+repr(row))
        contrasts[variant]=row
    for doc in docs:
        for variant in ('unknown_location','unknown_derivative','unknown_history','unknown_interior'):
            model,_=generic_model(doc,variant=variant)
            try:values(doc,model,PEOPLE)
            except ValueError as exc:
                if 'missing' not in str(exc):raise
            else:raise ValueError('Missing trajectory interpretation invented')
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,unknown_interpretations_refused=True,
        history_and_interior_are_explicit_oracles=True,all_real_history_or_derivative_proved=False)



def reverse_probe_checks(text):
    doc=candidate(text,generic_fixture());ds={d['name']:d for d in doc['declarations']}
    reverse=ds['seob']['body']['arguments'][1]['arguments'][1]
    event,observed=reverse,reverse['body']
    helper=dict(kind='definition',name='jmr',parameters=deepcopy(ds['seob']['parameters'])+[
        dict(name=event['variable'],sort=event['sort']),dict(name=observed['variable'],sort=observed['sort'])],
        result='truth',body=deepcopy(observed['body']))
    pointsort=ds[SYMBOLS['point']]['result']
    doc['declarations'] += [helper,dict(kind='primitive',name='jms',parameters=[],result=pointsort)]
    doc['statements']=[]
    shared=[k(SYMBOLS[n]) for n,_ in TRACK]+[k(SYMBOLS['event'])]
    doc=parse(format_graph(doc,'compact')+''.join('q['+k('jmr',*shared,k(point))+'].' for point in (SYMBOLS['point'],'jms')))
    doc=abstract(doc,OPS|{'sjs','seob','senz'});model,_=generic_model(doc)
    make=model['bb'];equal=model['sca'];conflict=(CENTER[0]+1,*CENTER[1:])
    model['jms']=lambda:fv(pointsort,lambda axis:make(conflict[AXES.index(axis)] if axis in AXES else 0))
    def location(matter,frame,event,point,context):
        return (matter,frame,event,context)==('matter','frame','event','text') and any(
            all(equal(point(axis),make(value)) for axis,value in zip(AXES,row)) for row in (CENTER,conflict))
    model['zpb']=location
    actual=values(doc,model,PEOPLE)
    if actual!=[True,False]:raise ValueError('Reverse history clause accepted conflicting same-time coordinates')
    return dict(results=actual,actual_reverse_clause_instantiated=True,not_a_full_history_proof=True)



def interior_probe_checks(text):
    doc=candidate(text,generic_fixture());ds={d['name']:d for d in doc['declarations']}
    radius=ds['senz']['body']['arguments'][1]['arguments'][1]
    moment=radius['body']['arguments'][1]['arguments'][1]
    helper=dict(kind='definition',name='jmv',parameters=deepcopy(ds['senz']['parameters'])+[
        dict(name=radius['variable'],sort=radius['sort']),dict(name=moment['variable'],sort=moment['sort'])],
        result='truth',body=deepcopy(moment['body']))
    sort=ds['jmp']['result'];doc['declarations'] += [helper,*[dict(kind='primitive',name=n,parameters=[],result=sort) for n in ('jmt','jmu')]]
    doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'q['+k('jmv',k(SYMBOLS['domain']),app(k(SYMBOLS['point']),k('zc7')),k('jmt'),k('jmu'))+'].')
    doc=abstract(doc,OPS|{'sjs','seob','senz'});rows=[]
    for variant in ('baseline','one_sided','isolated'):
        for radius in (F(1),F(1,3),F(10)):
            for sign in (-1,1):
                model,_=generic_model(doc,variant=variant);make=model['bb']
                model.update(jmt=lambda:make(radius),jmu=lambda:make(CENTER[3]+sign*radius/2))
                actual=values(doc,model,PEOPLE);expected=variant=='baseline' or variant=='one_sided' and sign==1
                if actual!=[expected]:raise ValueError('Interior clause missed an excluded nearby time')
                rows.append(dict(domain=variant,radius=str(radius),side=sign,result=actual[0]))
    return dict(cases=rows,actual_neighborhood_clause_instantiated=True,not_a_full_interior_proof=True)


def structural_checks(doc):
    ds={d['name']:d for d in doc['declarations']}
    def walk(node):
        if isinstance(node,dict):
            yield node
            for child in node.values():yield from walk(child)
        elif isinstance(node,list):
            for child in node:yield from walk(child)
    kinds=lambda name:[n['kind'] for n in walk(ds[name]['body']) if 'kind' in n]
    interior=kinds('senz');history=kinds('seob')
    if interior.count('exists')!=1 or interior.count('forall')!=1:raise ValueError('Two-sided interior lost full real quantification')
    if history.count('exists')!=3 or history.count('forall')!=3:raise ValueError('History needs nonempty, forward and reverse coverage')
    calls=[n for n in walk(ds['seoc']['body']) if n.get('kind')=='call']
    if [n['symbol'] for n in calls].count('sjs')!=3 or not {'seob','senz','zpb'}<={n['symbol'] for n in calls}:raise ValueError('Velocity lost its history or coordinate derivatives')
    factory=ds['seoe'];body=factory['body'];names=[p['name'] for p in body['parameters']]
    expected=dict(kind='apply',function=dict(kind='variable',name=factory['parameters'][0]['name']),
        arguments=[dict(kind='variable',name=names[i]) for i in (0,1,2,3,7)])
    if body['kind']!='lambda' or body['body']['kind']!='and' or body['body']['arguments'][0]!=expected:raise ValueError('Density and velocity were conflated')
    witness=body['body']['arguments'][1]
    witnesses=[]
    for _ in range(3):
        if witness['kind']!='exists':raise ValueError('Velocity witnesses must exist')
        witnesses.append(witness['variable']);witness=witness['body']
    expected=[names[0],names[1],names[7],witnesses[0],witnesses[1],names[2],witnesses[2],names[4],names[5],names[6]]
    if witness!=dict(kind='call',symbol='seoc',arguments=[dict(kind='variable',name=n) for n in expected]):raise ValueError('Velocity factory lost its shared witnesses or derivatives')
    integration=ds['seof'];p=[dict(kind='variable',name=p['name']) for p in integration['parameters']]
    if integration['body']!=dict(kind='call',symbol='senx',arguments=[p[0],dict(kind='call',symbol='seoe',arguments=[p[1]]),p[2],p[3]]):raise ValueError('Source content lost its explained velocity assignment')
    return dict(full_history_in_both_directions=True,two_sided_interior=True,three_time_derivatives=True,
        density_kept_separate=True,velocity_assignment_constructed=True,source_content_uses_constructed_assignment=True)


def unbounded_checks(text):
    rows={}
    base=candidate(text,generic_fixture());base['statements']=base['statements'][:3]
    for symbol,index in (('seob',2),('senz',2),('sjs',2)):
        doc=abstract(deepcopy(base),OPS|({'sjs','seob','senz'}-{symbol}));doc['statements']=[doc['statements'][index]]
        model,_=generic_model(doc)
        try:values(doc,model,PEOPLE)
        except ValueError as exc:
            if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
            rows[symbol]=str(exc)
        else:raise ValueError('Full real trajectory condition was finitely certified')
    return rows


def source_checks(text):
    decl=''.join('r '+SOURCE_SYMBOLS[n]+'[] '+sort+'.' for n,sort in SOURCE)
    doc=abstract(candidate(text,decl+'q['+k('seod',*(k(SOURCE_SYMBOLS[n]) for n,_ in SOURCE))+'].'),{'senv','seoc'})
    ds={d['name']:d for d in doc['declarations']};config=numbers();oldpoint=tuple(transform(CENTER,-config['speed']));rows={}
    for variant in ('baseline','formula_false','old_velocity_false','new_velocity_false','old_curve_wrong','new_curve_wrong'):
        cuts,model=setup(doc);make,read=cuts.make,cuts.read
        for n,value in config.items():
            if n in SOURCE_SYMBOLS:model[SOURCE_SYMBOLS[n]]=lambda value=value:make(value)
        for n,value in dict(matter='matter',event='event',oldframe='old',newframe='new',context='text').items():model[SOURCE_SYMBOLS[n]]=lambda value=value:value
        def dummy(sort):
            if isinstance(sort,dict):return fv(sort,lambda *a:dummy(sort['result']))
            return False if sort=='truth' else F(0) if sort=='number' else 'other'
        for n,_ in SOURCE:
            name=SOURCE_SYMBOLS[n]
            if name not in model or name in {p['name'] for p in doc['declarations'] if p['kind']=='primitive'} and n not in config and n not in ('matter','event','oldframe','newframe','context'):
                sort=ds[name]['result'];model[name]=lambda sort=sort:dummy(sort)
        for prefix,point,vel in (('old',oldpoint,('ux','uy','uz')),('new',CENTER,('vx','vy','vz'))):
            def curve(t,prefix=prefix,point=point,vel=vel):
                dt=read(t)-point[3];row=tuple(point[i]+config[vel[i]]*dt+(1 if variant==prefix+'_curve_wrong' else 0) for i in range(3))+(read(t),)
                return fv(ds[SOURCE_SYMBOLS[prefix+'curve']]['result']['result'],lambda axis:make(row[AXES.index(axis)] if axis in AXES else 0))
            callbacks(doc,model,{SOURCE_SYMBOLS[prefix+'curve']:curve,SOURCE_SYMBOLS[prefix+'domain']:lambda t:True,
                SOURCE_SYMBOLS['oldpoint' if prefix=='old' else 'point']:lambda axis,point=point:make(point[AXES.index(axis)] if axis in AXES else 0)})
        def velocity(matter,frame,context,domain,curve,event,point,ux,uy,uz):
            if frame not in ('old','new'):return False
            expected=oldpoint if frame=='old' else CENTER;vel=tuple(config[n] for n in (('ux','uy','uz') if frame=='old' else ('vx','vy','vz')))
            if (matter,event,context)!=('matter','event','text') or variant==frame+'_velocity_false':return False
            if tuple(read(point(a)) for a in AXES)!=expected or tuple(map(read,(ux,uy,uz)))!=vel:return False
            return all(domain(make(t)) and tuple(read(curve(make(t))(a)) for a in AXES)==tuple(expected[i]+vel[i]*(t-expected[3]) for i in range(3))+(t,) for t in (expected[3],expected[3]+1))
        model.update(senv=lambda *a:variant!='formula_false',seoc=velocity)
        used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        actual=values(doc,{n:f for n,f in model.items() if n in used},PEOPLE)
        if actual!=[variant=='baseline']:raise ValueError('Old/new velocity bridge differs: '+variant+repr(actual))
        rows[variant]=actual
    return dict(cases=rows,formula_and_complete_history_are_contract_oracles=True)


def build_report():
    documents={};texts=[];sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored velocity differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Velocity roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    previous=json.loads((ROOT/'reports/equation-presentation-v1.json').read_text(encoding='utf-8'))
    segment=deepcopy(previous['alignment']['segments'][1]);segment.update(definitions=['seoc','seod','seoe','seof'],review_ja='速度を同じ物質点の座標時刻による履歴の微分へ部分接続する。密度の意味と測定の実現、原文全体の意味確認は未完。')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_material_velocity.py','scripts/check_material_velocity.py','scripts/check_tau_differential.py',
        'scripts/check_plane_waveforms.py','scripts/check_rod_setup.py','scripts/check_comoving_labels.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py',
        'scripts/check_material_charge.py','scripts/check_parallel_composition.py','noema/finite_semantics.py','noema/extraction.py',
        'reports/equation-presentation-v1.json']
    return dict(status='partial_coordinate_time_velocity_grounding',documents=documents,sizes=sizes,
        structure=structural_checks(doc),finite=generic_checks(texts),reverse_probes=reverse_probe_checks(texts[0]),interior_probes=interior_probe_checks(texts[0]),source_bridge=source_checks(texts[1]),unbounded=unbounded_checks(texts[0]),
        alignment=dict(segments=[segment],semantic_completion=False),new_definitions=7,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Velocity report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Coordinate-time velocity, explicit history premises and real-domain refusals checked')


if __name__=='__main__':main()
