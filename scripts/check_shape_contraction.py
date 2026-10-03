"""Check shape-independent differences, finite charts and quantified width syntax."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.rational_proofs import verify
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.check_real_products import MEANINGS, call as k, op, assertion, conjunction as both
from scripts.check_moving_light_trip import literal
from scripts.compose_shape_contraction import ROOT, CUT, SHAPE, generic_composed, source_composed

REPORT=ROOT/'reports/shape-contraction-v1.json'


def polynomial_checks():
    V,s,f,g,L,eps,d,b,x,y,z,t,X,Y,Z,T,x2,y2,z2,X2,Y2,Z2,T2=map(lambda n:'v '+n,
        'light speed factor otherfactor length epsilon delta beta x y z time xx yy zz tt xtwo ytwo ztwo xxtwo yytwo zztwo tttwo'.split())
    zero=literal(0);one=literal(1);two=literal(2)
    mul=lambda a,b:k('ad',a,b);sq=lambda a:mul(a,a);add=lambda a,b:k('ab',a,b)
    sub=lambda a,b:add(a,k('ac',b));lt=lambda a,b:k('aa',a,b);eq=lambda a,b:op('e',a,b)
    factor=k('stt',V,s,f)
    pair=both(k('srb',V,s,b,one,x,y,z,t,X,Y,Z,T),k('srb',V,s,b,one,x2,y2,z2,t,X2,Y2,Z2,T2),factor)
    names='light speed beta factor x y z time xx yy zz tt xtwo ytwo ztwo xxtwo yytwo zztwo tttwo'
    claims={
        'same_observer_time_scales_only_longitudinal_differences':assertion(names,op('y',pair,both(eq(sub(x2,x),mul(f,sub(X2,X))),eq(sub(y2,y),sub(Y2,Y)),eq(sub(z2,z),sub(Z2,Z))))),
        'reciprocal_factor_has_positive_product_one':assertion('light speed beta factor',op('y',both(k('sra',V,s,b),factor),eq(mul(b,f),one))),
        'opposite_velocity_has_same_contraction':assertion('light speed factor',op('z',factor,k('stt',V,k('ac',s),f))),
        'zero_speed_has_factor_one':assertion('light factor',op('y',k('stt',V,zero,f),eq(f,one))),
        'nonzero_speed_strictly_shortens_positive_length':assertion('light speed factor length',op('y',both(factor,op('u',eq(s,zero)),lt(zero,L)),lt(mul(f,L),L))),
        'larger_speed_magnitude_has_smaller_factor':assertion('light speed factor other otherfactor',op('y',both(factor,k('stt',V,'v other',g),lt(sq(s),sq('v other'))),lt(g,f))),
        'delta_candidate_is_below_half_light_speed':assertion('light length epsilon delta',op('y',k('stu',V,L,eps,d),lt(mul(two,d),V))),
        'delta_candidate_certifies_small_contracted_length':assertion('light speed factor length epsilon delta',op('y',both(k('stu',V,L,eps,d),factor,op('u',lt(s,zero)),lt(sub(V,s),d)),lt(mul(L,f),eps))),
        'positive_scale_transports_upper_bound_and_width':assertion('factor lower upper value offset',op('y',both(lt(zero,f),op('u',lt('v value','v lower')),op('u',lt('v upper','v value'))),both(
            op('u',lt(add(mul(f,'v value'),'v offset'),add(mul(f,'v lower'),'v offset'))),op('u',lt(add(mul(f,'v upper'),'v offset'),add(mul(f,'v value'),'v offset'))),
            eq(sub(add(mul(f,'v upper'),'v offset'),add(mul(f,'v lower'),'v offset')),mul(f,sub('v upper','v lower')))))),
        'finite_beta_at_light_speed':assertion('',k('sra',literal(5),literal(5),one)),
        'finite_beta_above_light_speed':assertion('',k('sra',literal(5),literal(6),one)),
        'transverse_width_also_contracts':assertion('',eq(literal(3),mul(literal(Fraction(4,5)),literal(3)))),
        'constant_epsilon_independent_neighborhood_suffices':assertion('',op('y',both(k('stt',literal(5),literal(Fraction(24,5)),literal(Fraction(7,25))),lt(sub(literal(5),literal(Fraction(24,5))),one)),lt(mul(literal(5),literal(Fraction(7,25))),literal(Fraction(1,10))))),
    }
    invalid={'finite_beta_at_light_speed','finite_beta_above_light_speed','transverse_width_also_contracts','constant_epsilon_independent_neighborhood_suffices'}
    rows={}
    for name,claim in claims.items():
        row=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if row['status']!=('invalid' if name in invalid else 'valid'):raise ValueError('Contraction polynomial differs: '+name+repr(row))
        rows[name]=row
    return {'claims':rows,'rational_lemmas_only':True,'general_real_cut_completeness_proved':False}


def bounds_checks():
    # Reuse the actual bound definition after an explicit rational-domain
    # specialization. This does not assert equivalence of Q and real cuts.
    source=parse(source_composed()[0]);bound=deepcopy(next(d for d in source['declarations'] if d['name']=='suj'))
    cut=parse('n:r ja[] '+CUT+'.')['declarations'][0]['result']
    def rationalize(node):
        if node==cut:return 'number'
        if isinstance(node,list):return [rationalize(a) for a in node]
        if isinstance(node,dict):return {key:rationalize(value) for key,value in node.items()}
        return node
    base=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.d ba[x b] c[e[v x][v x]].d bc[x b y b] c[u[k aa[v y v x]]].')
    base['declarations'].append(rationalize(bound))
    text=format_graph(base,'compact')
    cases={
        'open_interval':('i[x b][w[k aa[n p a b v x]][k aa[v x n p d b]]]','0','3',True),
        'loose_upper':('i[x b][w[k aa[n p a b v x]][k aa[v x n p d b]]]','0','4',False),
        'loose_lower':('i[x b][w[k aa[n p a b v x]][k aa[v x n p d b]]]','-1','3',False),
        'empty':('i[x b][u[e[v x][v x]]]','0','0',False),
        'unbounded':('i[x b][k aa[n p a b v x]]','0','3',False),
        'singleton':('i[x b][e[v x][n p c b]]','2','2',True),
        'disconnected':('i[x b][x[w[k aa[n u f b v x]][k aa[v x n u c b]]][w[k aa[n p d b v x]][k aa[v x n p f b]]]]','-5','5',True),
        'translated_contracted_open_interval':('i[x b][w[k aa[n p c b v x]][k aa[v x '+literal(Fraction(22,5))+']]]','2',str(Fraction(22,5)),True),
    }
    rows={}
    for name,(domain,lower,upper,expected) in cases.items():
        query='s['+k('suj',domain,literal(Fraction(lower)),literal(Fraction(upper)))+'].'
        row=verify(parse(text+query),MEANINGS,timeout_ms=15000)[0]
        if row['status']!=('valid' if expected else 'invalid'):raise ValueError('Tight bounds differ: '+name+repr(row))
        rows[name]=row
    return {'cases':rows,'actual_bound_definition_specialized_to_rationals':True,'open_extrema_not_required':True,'real_suprema_not_machine_proved':True}


def shape_definition():
    # Two disjoint rectangular patches in the z=0 plane, written in Noema.
    n=lambda x:k('bb',literal(x));x,y,z='v x','v y','v z'
    interval=lambda a,b,c:both(k('bc',n(a),c),k('bc',c,n(b)))
    shape=both(op('x',interval(-5,-2,x),interval(3,5,x)),interval(0,2,y),k('sca',z,n(0)))
    return 'd ja[x '+CUT+' y '+CUT+' z '+CUT+'] c['+shape+'].'


DOMAIN=('left','right','interior','later','rL','rR','rO','rT','mL','mR','mO','mT','body','otherbody','orphan','rest','moving','x','y','z','t','length','time')


def physical_model(doc,label):
    fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
    reverse=label=='reverse';speed=-3 if reverse else 0 if label=='stationary' else 3
    observer,resting=('moving','rest') if reverse else ('rest','moving')
    beta=Fraction(1) if speed==0 else Fraction(5,4);axis=Fraction(5)/beta
    coords={'rL':[-axis,0,0,0],'rR':[axis,2,0,0],'rO':[0,1,0,0],'rT':[speed+axis,2,0,1]}
    for rr,mr in zip(('rL','rR','rO','rT'),('mL','mR','mO','mT')):
        x,y,z,t=coords[rr];coords[mr]=[beta*(x-speed*t),y,z,beta*(t-Fraction(speed,25)*x)]
    if label=='wrong_transform':coords['mR'][0]=4
    if label=='wrong_shape':coords['mR'][2]=1
    if label=='missing_zero_slice':
        for row in coords.values():row[3]+=2
    members={'left','right','later'}
    if label=='missing_surface':members.remove('left')
    if label=='interior_in_surface':members.add('interior')
    if label=='unmeasured_surface':members.add('orphan')
    events=('left','right','interior','later')
    charts={(event,frame):record for frame,records in ((observer,('rL','rR','rO','rT')),(resting,('mL','mR','mO','mT'))) for event,record in zip(events,records)}
    for symbol,value in {'ra':'rest','zbm':'moving','yn':'x','yo':'y','yp':'z','zc7':'t','ta':'length','rb':'time','zhw':'body','zb6':'motion','jb':observer,'jc':resting}.items():model[symbol]=lambda value=value:value
    model.update(tc=lambda:c(5),zb7=lambda:c(speed),sky=lambda x:square_root(fixture,x),
        zc5=lambda r:r in coords,zc6=lambda r,axis:c(coords.get(r,[0]*4)[('x','y','z','t').index(axis)] if axis in ('x','y','z','t') else 0),
        zc4=lambda event:event in events and label!='empty_scope',
        shd=lambda event,r,frame,setting:setting=='motion' and charts.get((event,frame))==r and not (label=='missing_chart' and event=='right' and frame==observer),
        zhu=lambda body,event,setting:(body,setting)==('otherbody' if label=='wrong_body' else 'body','motion') and event in members,
        zbq=lambda body,setting:(body,setting)==('body','motion') and label!='not_rigid',
        x4=lambda body,frame,setting:(body,frame,setting)==('body',resting,'motion') and label!='not_stationary',
        zbo=lambda frame,axis,setting:axis,
        zgj=lambda moving,rest,axis,value,lengthunit,timeunit,setting:(moving,rest,axis,n(value),lengthunit,timeunit,setting)==(resting,observer,'x',-speed if label=='wrong_motion' else speed,'length','time','motion'))
    return model,fixture,coords


def shape_checks():
    zero=k('bb',literal(0));params='k zhw[] p ja k jb[] k jc[] k tc[] k zb7[] '+zero+' k zb6[]'
    query=shape_definition()+'r jb[] a.r jc[] a.'
    query+='q[k sue['+params+']].q[k sub[k zhw[] p ja k jb[] k tc[] k zb7[] '+zero+' k zb6[]]].q[k suf['+params+']].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    expected={
        'baseline':[True,True,True],'reverse':[True,True,True],'stationary':[True,True,True],
        'wrong_transform':[False,True,True],'wrong_shape':[False,True,True],
        'wrong_motion':[False,True,True],'not_rigid':[False,True,True],'not_stationary':[False,True,True],
        'missing_surface':[False,False,True],'interior_in_surface':[False,False,True],
        'unmeasured_surface':[False,False,True],'wrong_body':[False,False,True],
        'empty_scope':[False,False,True],'missing_chart':[False,False,True],'missing_zero_slice':[False,False,True],
    }
    for label,wanted in expected.items():
        model,_,_=physical_model(doc,label);actual=values(doc,model,DOMAIN)
        if actual!=wanted:raise ValueError('Arbitrary shape chart differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'shape_predicate_defined_in_noema':True,'two_disconnected_rectangular_patches':True,
        'false_premise_does_not_certify_conclusion':True,'physical_boundary_and_charts_are_oracles':True}


def difference_checks():
    query=shape_definition()+'r jb[] a.r jc[] a.r jd[] a.r je[] a.r jf[] a.r jg[] a.'
    args='k jd[] k je[] k jf[] k jg[] k tc[] k zb7[]'
    query+='q[k suc['+args+']].q[k sud['+args+']].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    for label in ('baseline','reverse','stationary','non_simultaneous','wrong_transform'):
        model,fixture,coords=physical_model(doc,label)
        for symbol,value in zip(('jd','je','jf','jg'),('rL','rT' if label=='non_simultaneous' else 'rR','mL','mT' if label=='non_simultaneous' else 'mR')):model[symbol]=lambda value=value:value
        actual=values(doc,model,DOMAIN);expected=label not in ('non_simultaneous','wrong_transform')
        if actual!=[expected]*2:raise ValueError('Shape-independent difference differs: '+label)
        rows[label]={'accepted':actual,'proper_times':[str(coords['mL'][3]),str(coords['mR'][3])]}
    return rows


def limit_candidate_checks():
    query='r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.r jd[] '+CUT+'.q[k sbg[k sun[k ja[] k jb[] k jc[]]]].q[k sca[k sun[k ja[] k jb[] k jc[]] k jd[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC);rows={}
    for length,epsilon in ((5,1),(5,Fraction(1,10)),(10,Fraction(1,10)),(1,10)):
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('ja','jb','jc'),(5,length,epsilon)):model[symbol]=lambda value=value:fixture.make(value)
        # The old fixture validity guard is for bounded arithmetic examples;
        # these deliberately include intermediate values above 128.
        model['ba']=lambda value: isinstance(fixture.read(value),Fraction)
        expected=Fraction(5)*epsilon**2/(2*(length**2+epsilon**2))
        model['jd']=lambda:fixture.make(expected)
        if values(doc,model,('object',))!=[True,True]:raise ValueError('Positive neighborhood candidate differs')
        rows[f'{length}:{epsilon}']={'delta':str(expected)}
    # Full cut quantification must refuse finite evaluation, never substitute a grid.
    query='q[k sup[k bb[n p f b] k bb[n p f b]]].'
    full=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'})
    fixture=ConstructedCuts();model=guarded(full);fixture.arithmetic(model)
    try:values(full,model,('object',))
    except ValueError as error:
        if 'rational number domain' not in str(error):raise
    else:raise ValueError('Full real limit was finitely sampled')
    return {'candidates':rows,'full_cut_limit_refuses_finite_sampling':True}


def factor_checks():
    query='r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.q[k stx[k bb[n p f b] k ja[] k jc[]]].q[k sus[k bb[n p f b] k ja[] k jb[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    cases={'baseline':(3,Fraction(24,5),Fraction(4,5),True),
        'reverse':(-3,Fraction(-24,5),Fraction(4,5),True),
        'wrong_factor':(3,Fraction(24,5),Fraction(5,4),False),
        'light_boundary':(5,3,0,False),'superluminal':(6,3,0,False),
        'equal_magnitudes':(3,-3,Fraction(4,5),True),'stationary':(0,3,1,True)}
    for name,(speed,other,factor,expected) in cases.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model['sky']=lambda value:square_root(fixture,value)
        for symbol,value in zip(('ja','jb','jc'),(speed,other,factor)):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=[expected,True]:raise ValueError('Signed contraction factor differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'monotonicity_is_conditional_on_admissible_ordered_speeds':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-7:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_shape','wrong_width','wrong_monotonicity','wrong_limit','wrong_domain','wrong_reverse','wrong_clear'):
        model=guarded(doc);constants={'zh5':'shape','zh6':'width','zic':'monotonicity','zh7':'limit','zia':'domain','zib':'reverse','rd':'author','rh':'scope','ri':'text'}
        for name,value in constants.items():model[name]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        claims={('shape','sum' if label=='wrong_shape' else 'sug'),('width','sug' if label=='wrong_width' else 'sum'),('monotonicity','sum' if label=='wrong_monotonicity' else 'sut'),('domain','suq' if label=='wrong_domain' else 'sur'),('reverse','sug' if label=='wrong_reverse' else 'suu')}
        model.update(uh=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d)) in claims,
            zfl=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d))==('limit','sug','sur' if label=='wrong_limit' else 'suq'),
            zdg=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('reverse','sug' if label=='wrong_clear' else 'suu'))
        actual=values(doc,model,tuple(v for k,v in constants.items() if k!='ri'))
        expected=[label not in ('wrong_author','wrong_scope','wrong_context',wrong) for wrong in ('wrong_shape','wrong_width','wrong_monotonicity','wrong_limit','wrong_domain','wrong_reverse','wrong_clear')]
        if actual!=expected:raise ValueError('Shape attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned shape source differs')
    rows=[]
    for index,defs in ((116,['stv','sug','suk','sum','sup','sur','sut']),(117,['suh','suf','suu','suv'])):
        unit=next(u for u in artifact['units'] if u['id']==f'einstein-1905:u{index:04}')
        # Exclude the final forward-looking assertion about infinite velocities.
        end=unit['text'].index(';') if index==116 else len(unit['text'])
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Shape unit differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=0,end=end,source=unit['text'][:end],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False))
        for mid in unit['math_ids']:
            item=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Shape math differs')
            rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=item['sha256'],definitions=defs,status='partial',full_semantic_equivalence=False))
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'boundary_limit_is_explicit_interpretation':True,'infinite_velocity_forward_reference_unwritten':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored contraction differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored contraction basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Contraction roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/shape-contraction-basis-v1.json','data/einstein-shape-contraction-basis-v1.json',
        'examples/v014/sphere-slice.noema','examples/v014/einstein-sphere-slice.noema',
        'scripts/compose_shape_contraction.py','scripts/check_shape_contraction.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py','noema/rational_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-sphere-slice.noema').read_text(encoding='utf-8')
    return {'status':'partial_arbitrary_shape_contraction_and_boundary_limit','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'bounds':bounds_checks(),'shapes':shape_checks(),'differences':difference_checks(),
        'limit_candidates':limit_candidate_checks(),'factors':factor_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Shape contraction report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Arbitrary shapes, directional widths and boundary limit conditions checked')


if __name__=='__main__':main()
