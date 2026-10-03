"""Check curve bindings and scoped assumptions without sampling continua."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import Content, FunctionValue
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.rational_proofs import verify
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_polygon_clock import bind_parameters, model_for as polygon_model
from scripts.check_rod_setup import guarded
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_real_products import MEANINGS, call as k
from scripts.check_moving_light_trip import literal
from scripts.compose_curved_clock import ROOT, CUT, CURVE, COMPARE, composed

REPORT=ROOT/'reports/curved-clock-v1.json'


def query_document(queries,parameters=COMPARE):
    names={n:'zz'+number_word(i) for i,(n,_) in enumerate(parameters)}
    text=''.join('r '+names[n]+'[] '+sort+'.' for n,sort in parameters)
    for symbol,items in queries:text+='q['+k(symbol,*(k(names[n]) for n,_ in items))+'].'
    return abstract(candidate(composed()[0],text),ARITHMETIC|{'sky','shd','qo'}),names


def curve_model(doc,names,label):
    axes=('x','y','z','vx','vy','vz');base_names={n:s for n,s in names.items() if n not in axes}
    oldlabel={'open_straight':'open_bend','changed_reading':'reset_corner'}.get(label,label)
    model,fixture,domain,times,_=polygon_model(doc,base_names,oldlabel)
    c=fixture.make;n=fixture.read;lo=times[0];hi=times[-1];span=hi-lo
    def components(time):
        t=time-lo
        if label=='open_straight':return (3*t,0,0,3,0,0)
        # A smooth closed polynomial is used only to test observed bindings.
        # Its speed is NOT constant; these samples do not certify sxv or sya.
        return (Fraction(3,5)*t*(span-t),Fraction(1,25)*t*(span-t)*(t-span*Fraction(1,2)),0,
            Fraction(3,5)*(span-2*t),Fraction(1,25)*(-3*t*t+3*span*t-span*span*Fraction(1,2)),0)
    oldcoord=model['zc6'];validrecord=model['zc5']
    def coordinate(record,axis):
        if axis=='t':return c(hi+1) if label=='outside_interval' and record=='mr0' else oldcoord(record,axis)
        if axis not in ('x','y','z') or not validrecord(record):return c(0)
        time=hi if record=='initialrecord' else n(oldcoord(record,'t'))
        value=components(time)[('x','y','z').index(axis)]
        if label=='wrong_curve_point' and record=='mr0' and axis=='y':value+=1
        return c(value)
    model['zc6']=coordinate
    previous_read=model[names['reading']]();previous_ce=model['ce']
    def dial(event):
        if event in ('mid0','mid1'):
            return c(n(previous_read('e0'))+Fraction(4,5)*(n(oldcoord('mr'+event[-1],'t'))-lo))
        return previous_read(event)
    model[names['reading']]=lambda:FunctionValue(('individual',),previous_read.result,dial)
    model['ce']=lambda clock,event,frame,unit,value:previous_ce(clock,event,frame,unit,value) or (
        (clock,frame,unit)==('clock','rest','time') and event in ('mid0','mid1') and n(value)==n(dial(event)))
    axis_inputs={axis:(lambda time,index=i:c(components(n(time))[index])) for i,axis in enumerate(axes)}
    bind_parameters(doc,model,{n:s for n,s in names.items() if n in axes},axis_inputs)
    if label=='candidate_record_mismatch':
        previous=model[names['record']]()
        model[names['record']]=lambda:FunctionValue(('individual',),'individual',lambda e:'r2' if e=='e1' else previous(e))
    if label=='wrong_time_unit':model['rb']=lambda:'second'
    if label=='extra_inconsistent_chart':
        previous=model['shd']
        model['shd']=lambda e,r,f,s:previous(e,r,f,s) or (e,r,f,s)==('e1','initialrecord','rest','motion')
    return model,fixture,domain


def binding_checks():
    doc,names=query_document([('sxx',CURVE),('sxz',CURVE),('syc',CURVE)])
    labels=('baseline','open_straight','negative_times','common_dial_offset','changed_reading','wrong_curve_point',
        'candidate_record_mismatch','wrong_time_unit','extra_inconsistent_chart','missing_midpoint','outside_interval',
        'missing_corner_record','wrong_clock_at_corner','same_endpoint_event')
    rows={}
    for label in labels:
        model,_,domain=curve_model(doc,names,label);actual=values(doc,model,domain)
        measured=label not in ('wrong_curve_point','candidate_record_mismatch','wrong_time_unit','extra_inconsistent_chart','wrong_clock_at_corner','same_endpoint_event')
        endpoints=label not in ('wrong_time_unit','same_endpoint_event')
        closed=label not in ('open_straight','same_endpoint_event')
        if actual!=[measured,endpoints,closed]:raise ValueError('Curved binding differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'closed_polynomial_samples_do_not_have_constant_speed':True,
        'binding_checks_do_not_certify_kinematics_or_clock_law':True,'changed_readings_are_allowed_before_extension_assumption':True}


def speed_checks():
    parameters=[(n,CUT) for n in ('speed','vx','vy','vz')]
    doc,names=query_document([('syh',parameters)],parameters);rows={}
    examples={'x_direction':(3,3,0,0),'y_direction':(3,0,3,0),'reverse':(3,-3,0,0),
        'diagonal':(3,Fraction(9,5),Fraction(12,5),0),'changed_magnitude':(3,4,0,0),
        'two_full_components':(3,3,3,0),'zero_speed':(0,0,0,0),'negative_speed':(-3,3,0,0)}
    for label,numbers in examples.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        bind_parameters(doc,model,names,{name:fixture.make(value) for (name,_),value in zip(parameters,numbers)})
        actual=values(doc,model,('point',))[0];expected=label in ('x_direction','y_direction','reverse','diagonal')
        if actual!=expected:raise ValueError('Curved speed differs: '+label)
        rows[label]={'values':[str(x) for x in numbers],'accepted':actual}
    return rows


def continuity_checks():
    source=parse(composed()[0]);cut=parse('n:r ja[] '+CUT+'.')['declarations'][0]['result']
    def rationalize(node):
        if node==cut:return 'number'
        if isinstance(node,list):return [rationalize(x) for x in node]
        if isinstance(node,dict):return {key:rationalize(value) for key,value in node.items()}
        return node
    base=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.d ba[x b] c[e[v x][v x]].d bb[x b] b[v x].d bg[x b y b] c[k aa[v x v y]].d bc[x b y b] c[u[k aa[v y v x]]].d bd[x b y b] b[k ab[v x v y]].d bf[x b y b] b[k ab[v x k ac[v y]]].')
    base['declarations'] += [rationalize(d) for d in source['declarations'] if d['name'] in ('sjo','sjp','sxs','sxt','sxu')]
    text=format_graph(base,'compact');domain='i[x b][k sxs[n p a b n p b b v x]]';identity='i[x b][v x]'
    empty='i[x b][u[e[v x][v x]]]';isolated='i[x b][e[v x][n p a b]]'
    examples={
        'identity_on_closed_interval':('sxu',[domain,identity],True),
        'affine_on_closed_interval':('sxu',[domain,'i[x b][k ab[k ad[n p d b v x] n p c b]]'],True),
        'one_sided_endpoint_continuity':('sxt',[domain,identity,literal(0)],True),
        'point_outside_domain':('sxt',[domain,identity,literal(2)],False),
        'isolated_point_can_be_continuous':('sxt',[isolated,identity,literal(0)],True),
        'empty_domain_has_no_continuity_point':('sxt',[empty,identity,literal(0)],False),
        'whole_empty_domain_is_vacuous':('sxu',[empty,identity],True),
    }
    rows={}
    for label,(symbol,arguments,expected) in examples.items():
        row=verify(parse(text+'s['+k(symbol,*arguments)+'].'),MEANINGS,timeout_ms=15000)[0]
        if row['status']!=('valid' if expected else 'invalid'):raise ValueError('Curve continuity differs: '+label+repr(row))
        rows[label]=row
    return {'cases':rows,'actual_definitions_specialized_to_rationals':True,'not_a_full_real_curve_verification':True}


def infinite_checks():
    rows={}
    for label,symbol,parameters in (('kinematics','sxv',CURVE),('worldline','sxy',CURVE),('complete_setting','sya',COMPARE),('approximation','syf',COMPARE)):
        doc,names=query_document([(symbol,parameters)]);model,_,domain=curve_model(doc,names,'baseline')
        try:values(doc,model,domain)
        except ValueError as error:
            if 'rational number domain' not in str(error):raise
            rows[label]=str(error)
        else:raise ValueError('Full curve condition was sampled: '+label)
    return rows


def truth_checks():
    text=composed()[0]
    query='q[t[k syb[]][k ri[]]].q[t[k sye[]][k ri[]]].q[k ug[k zje[] k rd[] r[k syb[]] k zjd[] k ri[]]].'
    doc=abstract(candidate(text,query),{'sxq','syg'});rows={}
    for polygon in (False,True):
        for curve in (False,True):
            model=guarded(doc)
            for name,value in {'ri':'text','zje':'assumption','rd':'author','zjd':'scope'}.items():model[name]=lambda value=value:value
            model['sxq']=lambda:Content(('motion','text','other'),(polygon,)*3)
            model['syg']=lambda:Content(('motion','text','other'),(curve,)*3)
            model['ug']=lambda node,author,description,scope,context:(node,author,scope,context)==('assumption','author','scope','text')
            actual=values(doc,model,('assumption','author','scope'))
            expected=[not polygon or curve,polygon and curve,True]
            if actual!=expected:raise ValueError('Curve assumption truth differs')
            rows[str((polygon,curve))]=actual
    return {'cases':rows,'false_extension_can_be_attributed_without_endorsement':True,'polygon_result_alone_does_not_establish_curve_law':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-4:];rows={}
    labels=('baseline','wrong_author','wrong_context','wrong_proved_node','wrong_assumption_scope','wrong_claim_scope',
        'wrong_inference_scope','wrong_extension','wrong_closed_result','wrong_inference_premise','missing_proved_status')
    for label in labels:
        model=guarded(doc)
        constants={'rd':'author','zjb':'polygon','ri':'text','zjd':'scope','zje':'assumption','zjf':'conclusion'}
        for name,value in constants.items():model[name]=lambda value=value:value
        common=lambda a,c:(a,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_context' else 'text')
        symbol=lambda description:json.loads(description.syntax)['symbol']
        model['ui']=lambda a,node,c:common(a,c) and node==('assumption' if label=='wrong_proved_node' else 'polygon') and label!='missing_proved_status'
        model['ug']=lambda node,a,d,s,c:common(a,c) and (node,s,symbol(d))==('assumption','other' if label=='wrong_assumption_scope' else 'scope','syg' if label=='wrong_extension' else 'syb')
        model['uh']=lambda node,a,d,s,c:common(a,c) and (node,s,symbol(d))==('conclusion','other' if label=='wrong_claim_scope' else 'scope','syg' if label=='wrong_closed_result' else 'syd')
        model['zc']=lambda node,a,p,d,s,c:common(a,c) and (node,s,symbol(p),symbol(d))==('conclusion','other' if label=='wrong_inference_scope' else 'scope','sxq' if label=='wrong_inference_premise' else 'sye','syd')
        actual=values(doc,model,('author','polygon','scope','assumption','conclusion','other'))
        common_ok=label not in ('wrong_author','wrong_context')
        expected=[common_ok and label not in bad for bad in (('wrong_proved_node','missing_proved_status'),('wrong_assumption_scope','wrong_extension'),('wrong_claim_scope','wrong_closed_result'),('wrong_inference_scope','wrong_inference_premise'))]
        if actual!=expected:raise ValueError('Curved attribution differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'quoted_physics_never_evaluated':True,'prior_polygon_content_is_named_and_reused':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned curve source differs')
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0128');end=unit['text'].index('Man schließt daraus')
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Curve text differs')
    definitions=['sxv','sxx','sxy','sya','syb','syc','syd','sye','syf']
    rows=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=0,end=end,source=unit['text'][:end],definitions=definitions,status='partial_explicit_reading',full_semantic_equivalence=False)]
    for mid in unit['math_ids']:
        item=next(m for m in artifact['math'] if m['id']==mid)
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Curve math differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=item['sha256'],definitions=definitions,status='partial',full_semantic_equivalence=False))
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'earth_clock_comparison_not_yet_connected':True,
        'c1_relative_endpoint_model_is_explicit_interpretation':True,'expression_and_physical_proof_are_distinct':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored curved clock differs')
    if json.loads((ROOT/'data/curved-clock-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Curved clock basis differs')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Curved clock roundtrip differs')
    paths=[basis['document'],'data/curved-clock-basis-v1.json','examples/v014/einstein-polygon-clock.noema','examples/v011/limits.noema',
        'data/conditional-discourse-basis-v1.json','scripts/compose_curved_clock.py','scripts/check_curved_clock.py',
        'scripts/check_polygon_clock.py','scripts/check_tau_differential.py','reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/rational_proofs.py']
    previous=(ROOT/'examples/v014/einstein-polygon-clock.noema').read_text(encoding='utf-8')
    return {'status':'partial_scoped_curve_extension_from_polygon_result','documents':{basis['document']:audit_basis(doc,basis)},
        'observed_bindings':binding_checks(),'speed_magnitude':speed_checks(),'continuity':continuity_checks(),
        'infinite_conditions':infinite_checks(),'truth_separation':truth_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Curved clock report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Curved clock bindings and scoped extension checked')


if __name__=='__main__':main()
