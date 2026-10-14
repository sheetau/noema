"""Check simultaneous material slices and density-volume cancellation."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode,decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_moving_light_trip import literal
from scripts.check_rod_setup import callbacks,guarded
from scripts.compose_limits import call as k,op,both,v
from scripts.compose_material_charge import ROOT,PARENT,BUILDERS,COORD,JAC,CELL,INPUTS,CUT,generic_composed

REPORT=ROOT/'reports/material-charge-v1.json'
FIELDS=INPUTS+[(n,CUT) for n in COORD.split() if n not in dict(INPUTS)]
SYMBOLS={name:'jr'+number_word(i) for i,(name,_) in enumerate(FIELDS)}
DOMAIN=('matter','oldframe','newframe','oldslice','newslice','other')


def numbers(speed=3,velocity=(1,-2,3),density=4,volume=11,tau=2):
    V=F(5);s=F(speed);beta=F(1) if s==0 else F(5,4)
    ux,uy,uz=map(F,velocity);rho=F(density);volume=F(volume);tau=F(tau)
    D=V*V-s*ux;stretch=V*V/(beta*D);sheary=s*uy/D;shearz=s*uz/D
    ax,ay,az=map(F,(1,2,3));time=(V*V*tau/beta+s*ax)/D
    x,y,z=ax+ux*time,ay+uy*time,az+uz*time
    vx,vy,vz=V*V*(ux-s)/D,V*V*uy/(beta*D),V*V*uz/(beta*D)
    newdensity=beta*D*rho/(V*V);newvolume=stretch*volume
    return dict(light=V,speed=s,beta=beta,ux=ux,uy=uy,uz=uz,density=rho,newdensity=newdensity,vx=vx,vy=vy,vz=vz,
        stretch=stretch,sheary=sheary,shearz=shearz,volume=volume,newvolume=newvolume,charge=rho*volume,newcharge=newdensity*newvolume,
        ax=ax,ay=ay,az=az,time=time,tau=tau,x=x,y=y,z=z,xi=beta*(x-s*time),eta=y,zeta=z)


def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b));eq=lambda a,b:op('e',a,b)
    cell=k('sene',*map(v,CELL.split()));jac=k('send',*map(v,JAC.split()));coord=k('senc',*map(v,COORD.split()))
    square=mul(v('light'),v('light'));D=sub(square,mul(v('speed'),v('ux')))
    fields=' '.join(dict.fromkeys((COORD+' '+CELL).split()))
    image=both(eq(v('xi'),add(mul(v('stretch'),v('ax')),mul(v('vx'),v('tau')))),
        eq(v('eta'),add(add(v('ay'),mul(v('sheary'),v('ax'))),mul(v('vy'),v('tau')))),
        eq(v('zeta'),add(add(v('az'),mul(v('shearz'),v('ax'))),mul(v('vz'),v('tau')))))
    fixed=numbers()
    concrete=k('sene',*(literal(fixed[n]) for n in CELL.split()))
    claims={
        'density_and_slice_volume_factors_cancel':assertion(CELL,op('y',cell,eq(mul(v('stretch'),v('newdensity')),v('density')))),
        'uniform_material_cell_preserves_charge':assertion(CELL,op('y',cell,eq(v('charge'),v('newcharge')))),
        'slice_stretch_is_positive':assertion(JAC,op('y',jac,k('aa',literal(0),v('stretch')))),
        'rest_volume_contracts_by_beta':assertion(JAC,op('y',both(jac,eq(v('ux'),literal(0))),eq(mul(v('beta'),v('stretch')),literal(1)))),
        'same_new_time_selects_label_dependent_old_time':assertion(COORD,op('y',coord,eq(mul(mul(v('beta'),D),v('time')),
            add(mul(square,v('tau')),mul(mul(v('beta'),v('speed')),v('ax')))))),
        'slice_affine_map_follows_from_worldline_and_boost':assertion(fields,op('y',both(coord,cell),image)),
        'density_alone_is_invariant':assertion('',op('y',concrete,eq(literal(fixed['density']),literal(fixed['newdensity'])))),
        'coordinate_volume_is_invariant':assertion('',op('y',concrete,eq(literal(fixed['volume']),literal(fixed['newvolume'])))),
    }
    rows={};text=generic_composed()[0]
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),MEANINGS,timeout_ms=25000,max_expansion=250000)[0]
        want='invalid' if name in ('density_alone_is_invariant','coordinate_volume_is_invariant') else 'valid'
        if result['status']!=want:raise ValueError('Material charge proof '+name+': '+result['status'])
        rows[name]=result
    return dict(claims=rows,rational_algebra_only=True,all_real_cut_laws_proved=False,
                general_volume_change_of_variables_proved=False,arbitrary_accelerated_body_conservation_proved=False)


def expression(name):return k(SYMBOLS[name])


def fixture():
    extra=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in FIELDS)
    fields=lambda names:[expression(n) for n in names.split()]
    mul=lambda a,b:k('shv',a,b);add=lambda a,b:k('bd',a,b);eq=lambda a,b:k('sca',a,b)
    square=mul(expression('light'),expression('light'))
    D=k('bf',square,mul(expression('speed'),expression('ux')))
    image=both(eq(expression('xi'),add(mul(expression('stretch'),expression('ax')),mul(expression('vx'),expression('tau')))),
        eq(expression('eta'),add(add(expression('ay'),mul(expression('sheary'),expression('ax'))),mul(expression('vy'),expression('tau')))),
        eq(expression('zeta'),add(add(expression('az'),mul(expression('shearz'),expression('ax'))),mul(expression('vz'),expression('tau')))))
    time=eq(mul(mul(expression('beta'),D),expression('time')),
        add(mul(square,expression('tau')),mul(mul(expression('beta'),expression('speed')),expression('ax'))))
    queries=[k('senf',*fields(COORD)),k('seng',*fields(JAC)),k('senh',*fields(CELL)),k('seni',*(expression(n) for n,_ in INPUTS)),
        eq(expression('charge'),expression('newcharge')),image,time]
    return extra+''.join('q['+q+'].' for q in queries)


def model_for(doc,*,config=None,changes=None,variant='baseline'):
    config=dict(config or numbers());config.update(changes or {})
    cuts,model=setup(doc);read,make=cuts.read,cuts.make
    for name,sort in FIELDS:
        if name in ('assigned','paired','frames'):continue
        if sort==CUT:model[SYMBOLS[name]]=lambda name=name:make(config[name])
        else:model[SYMBOLS[name]]=lambda name=name:'motion' if name=='context' else name
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:
                expected[i]=expected[i]+1 if isinstance(expected[i],F) else 'text' if label=='context' else 'other'
        return list(actual)==expected
    def assigned(matter,frame,slice,density,volume,charge,context):
        return any(match((matter,frame,slice,read(density),read(volume),read(charge),context),
            ('matter',prefix+'frame',prefix+'slice',config[d],config[w],config[q],'motion'),prefix,
            ('matter','frame','slice','density','volume','charge','context')) for prefix,d,w,q in (
                ('old','density','volume','charge'),('new','newdensity','newvolume','newcharge')))
    callbacks(doc,model,{
        SYMBOLS['assigned']:assigned,
        SYMBOLS['paired']:lambda *a:match(a,('matter','oldframe','newframe','oldslice','newslice','motion'),'pair',
            ('matter','oldframe','newframe','oldslice','newslice','context')),
        SYMBOLS['frames']:lambda old,new,speed,context:match((old,new,read(speed),context),
            ('oldframe','newframe',config['speed'],'motion'),'frame',('oldframe','newframe','speed','context'))})
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:f for n,f in model.items() if n in used}


def finite_checks(texts):
    docs=[abstract(candidate(text,fixture()),OPS) for text in texts]
    def run(**options):
        rows=[values(doc,model_for(doc,**options),DOMAIN) for doc in docs]
        if rows[0]!=rows[1]:raise ValueError('Extracted material cell differs')
        return rows[0]
    cases=[]
    for speed,velocity,density,tau in product((-3,0,3),((0,0,0),(1,-2,3),(5,0,0)),(-4,0,4),(-2,3)):
        config=numbers(speed,velocity,density,tau=tau);row=run(config=config)
        if row!=[True]*7:raise ValueError('Consistent material slice failed')
        cases.append(dict(speed=speed,velocity=list(velocity),density=density,tau=tau,
            oldtime=str(config['time']),newvolume=str(config['newvolume']),newdensity=str(config['newdensity']),charge=str(config['charge']),results=row))
    contrasts={}
    for name in ('time','tau','x','y','z','xi','eta','zeta','ax','ay','az'):
        config=numbers();row=run(changes={name:config[name]+1})
        if row[0] or row[1:5]!=[True]*4:raise ValueError('Point changed independent volume or charge condition')
        contrasts['coordinate_'+name]=row
    for name in ('stretch','sheary','shearz','newdensity','newvolume','charge','newcharge'):
        config=numbers();row=run(changes={name:config[name]+1})
        want_jac=name not in ('stretch','sheary','shearz')
        if row[:4]!=[True,want_jac,False,False]:raise ValueError('Material factor mutation accepted: '+name)
        contrasts['value_'+name]=row
    for category,labels in (
        ('old',('matter','frame','slice','density','volume','charge','context')),
        ('new',('matter','frame','slice','density','volume','charge','context')),
        ('pair',('matter','oldframe','newframe','oldslice','newslice','context')),
        ('frame',('oldframe','newframe','speed','context'))):
        for label in labels:
            variant=category+'_'+label;row=run(variant=variant)
            if row!=[True,True,True,False,True,True,True]:raise ValueError('Wrong material assignment accepted: '+variant)
            contrasts[variant]=row
    edges=[]
    for volume in (0,-1):
        row=run(config=numbers(volume=volume))
        if row!=[True,True,False,False,True,True,True]:raise ValueError('Nonpositive physical volume accepted')
        edges.append(dict(condition='volume='+str(volume),results=row))
    for ux in (F(25,3),F(10)):
        row=run(changes={'ux':ux})
        if row[:4]!=[False]*4:raise ValueError('Nonpositive simultaneity denominator accepted')
        edges.append(dict(condition='ux='+str(ux),results=row))
    for doc in docs:
        for name in ('assigned','paired','frames'):
            model=model_for(doc);model[SYMBOLS[name]]=guarded(doc)[SYMBOLS[name]]
            try:values(doc,model,DOMAIN)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Missing material correspondence supplied')
    # Different old times at one new simultaneous slice are a required feature.
    base=numbers();second=dict(base);second['ax']=F(2)
    D=base['light']**2-base['speed']*base['ux']
    second['time']=(base['light']**2*base['tau']/base['beta']+base['speed']*second['ax'])/D
    for label,axis,u in (('ax','x','ux'),('ay','y','uy'),('az','z','uz')):second[axis]=second[label]+second[u]*second['time']
    second.update(xi=second['beta']*(second['x']-second['speed']*second['time']),eta=second['y'],zeta=second['z'])
    if run(config=second)!=[True]*7 or second['time']==base['time']:raise ValueError('Relativity of simultaneity disappeared')
    return dict(cases=cases,contrasts=contrasts,edge_cases=edges,standalone_agrees=True,unknown_bindings_refused=True,
        simultaneous_new_slice=dict(tau=str(base['tau']),oldtimes=[str(base['time']),str(second['time'])]),
        rational_embeddings_only=True,uniform_affine_material_region_only=True)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0238')
    excerpt='so bleibt seine Ladung auch';start=unit['text'].index(excerpt)
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
        definitions=['senc','send','sene','senf','seng','senh','seni'],status='explicit_interpretive_annotation',
        review_ja='任意運動の電荷一定性そのものではなく、その前段として一様並進の同じ物質領域で密度と同時刻体積が相殺する条件を記述する。二系の時刻面を混同しない。加速・非一様密度・境界流束・時間を通じた一般の保存則は未完。')],semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored material charge differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Material charge roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_material_charge.py','scripts/check_material_charge.py','scripts/compose_density_boost.py',
        'scripts/check_comoving_labels.py','scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py',
        'scripts/check_plane_waveforms.py','scripts/check_real_products.py','scripts/check_rod_setup.py','scripts/check_moving_light_trip.py',
        'noema/finite_semantics.py','noema/polynomial_proofs.py','noema/extraction.py','artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_uniform_material_slice_and_charge_cancellation',documents=documents,sizes=sizes,
        polynomial=polynomial_checks(),finite=finite_checks(texts[1:]),alignment=alignment(),new_definitions=7,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args()
    report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Material charge report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Material slicing, density-volume cancellation and bound charge comparisons checked')


if __name__=='__main__':main()
