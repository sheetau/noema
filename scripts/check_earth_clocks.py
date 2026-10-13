"""Check mechanism, geographical placement, controls and relative clock rates."""
import argparse
from fractions import Fraction
import hashlib
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.compose_earth_clocks import ROOT, composed

REPORT=ROOT/'reports/earth-clocks-v1.json'
DOMAIN=('eq','pole','r1','r2','s1','s2','axis','eqplace','poleplace','earth','length','time','scope','period','temperature','magnetism','frame','source','author')


def checks():
    query='''r ja[] a.r jb[] a.r jc[] a.r jd[] a.
q[k syi[k ja[] k zjt[]]].
q[k syj[k ja[] k jb[] k zjw[] k zjt[]]].
q[k syk[k jc[] k zjr[] k zjs[] k ta[] k zjt[]]].
q[k syl[k jd[] k zjr[] k zjs[] k ta[] k zjt[]]].
q[k sym[k ja[] k jb[] k jc[] k jd[] k zjr[] k zjs[] k ra[] k ta[] k zjw[] k zjt[]]].
q[k syn[k ja[] k jb[] k zjx[] k ra[] k rb[] k zjw[] k zjt[]]].'''
    doc=abstract(candidate(composed()[0],query),ARITHMETIC);rows={}
    labels=('baseline','south_pole','missing_spring','not_regulating_clock','pendulum_instead','different_structure','different_conditions',
        'empty_condition_scope','incomplete_conditions','both_absent_condition','same_clock','not_surface','off_equator','off_pole',
        'at_center','negative_radius','not_fixed_to_body','wrong_rotation_axis','equal_rates','reversed_rates','large_gap','zero_rate',
        'degree_standard_rejects','wrong_rate_unit','wrong_rate_interval')
    for label in labels:
        fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
        constants={'ja':'eq','jb':'eq' if label=='same_clock' else 'pole','jc':'eqplace','jd':'poleplace','zjr':'earth','zjs':'axis',
            'zjt':'motion','ta':'length','ra':'frame','rb':'time','zjw':'scope','zjx':'period'}
        for symbol,value in constants.items():model[symbol]=lambda value=value:value
        parts={('r1','eq'),('r2','pole'),('s1','r1'),('s2','r2')}
        if label=='missing_spring':parts.remove(('s1','r1'))
        axial={'eqplace':1 if label=='off_equator' else 0,'poleplace':0 if label=='at_center' else -10 if label=='south_pole' else 10}
        radial={'eqplace':-10 if label=='negative_radius' else 10,'poleplace':2 if label=='off_pole' else 0}
        eqrate={'equal_rates':1,'reversed_rates':Fraction(1001,1000),'large_gap':Fraction(4,5),'zero_rate':0}.get(label,Fraction(999,1000))
        model.update(
            ca=lambda clock:clock in ('eq','pole'),ci=lambda unit:unit=='time',
            cd=lambda a,b:(a,b)==('eq','pole') and label!='different_structure',
            zjg=lambda part,whole,ctx:ctx=='motion' and (part,whole) in parts,
            zjh=lambda rotor,axis,spring,ctx:axis=='axis' and ctx=='motion' and (rotor,spring) in {('r1','s1'),('r2','s2')} and label!='pendulum_instead',
            zji=lambda clock,rotor,ctx:ctx=='motion' and (clock,rotor) in {('eq','r1'),('pole','r2')} and label!='not_regulating_clock',
            zjk=lambda condition,scope,ctx:(condition,scope,ctx)==('temperature','scope','motion') and label!='empty_condition_scope',
            zjl=lambda scope,ctx:(scope,ctx)==('scope','motion') and label!='incomplete_conditions',
            zjj=lambda condition,clock,ctx:ctx=='motion' and condition=='temperature' and clock in ('eq','pole') and label!='both_absent_condition' and not(label=='different_conditions' and clock=='eq'),
            zjm=lambda clock,place,body,ctx:body=='earth' and ctx=='motion' and (clock,place) in {('eq','eqplace'),('pole','poleplace')} and label!='not_fixed_to_body',
            zjn=lambda body,axis,frame,ctx:(body,axis,frame,ctx)==('earth','axis','frame','motion') and label!='wrong_rotation_axis',
            zjo=lambda place,body,axis,unit,ctx:c(axial.get(place,0)),
            zjp=lambda place,body,axis,unit,ctx:c(radial.get(place,0)),
            zjq=lambda place,body,ctx:(body,ctx)==('earth','motion') and place in ('eqplace','poleplace') and not(label=='not_surface' and place=='eqplace'),
            zju=lambda clock,interval,frame,unit,ctx:c((eqrate if clock=='eq' else 1) if (interval,frame,unit,ctx)==('scope' if label=='wrong_rate_interval' else 'period','frame','length' if label=='wrong_rate_unit' else 'time','motion') else 0),
            zjv=lambda difference,reference,scope,ctx:(scope,ctx)==('scope','motion') and n(reference)==1 and 0<n(difference)<Fraction(1,100) and label!='degree_standard_rejects')
        actual=values(doc,model,DOMAIN)
        mechanism=label not in ('missing_spring','not_regulating_clock','pendulum_instead')
        controls=label not in ('different_conditions','empty_condition_scope','incomplete_conditions')
        equator=label not in ('not_surface','off_equator','negative_radius')
        pole=label not in ('off_pole','at_center')
        setup=mechanism and controls and equator and pole and label not in ('same_clock','different_structure','not_fixed_to_body','wrong_rotation_axis')
        slower=label not in ('same_clock','equal_rates','reversed_rates','large_gap','zero_rate','degree_standard_rejects','wrong_rate_unit','wrong_rate_interval')
        if actual!=[mechanism,controls,equator,pole,setup,slower]:raise ValueError('Earth comparison differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'test_threshold_only':'1/100 of reference rate','source_has_no_numeric_threshold':True,
        'mean_rates_not_absolute_dial_values':True,'structure_and_other_conditions_are_distinct':True,
        'condition_scope_completeness_is_an_explicit_oracle':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_premise','wrong_result'):
        model=guarded(doc)
        for symbol,value in {'zjy':'source','rd':'author','zjd':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        sym=lambda description:json.loads(description.syntax)['symbol']
        model['zc']=lambda node,author,premise,result,scope,ctx:(node,author,scope,ctx,sym(premise),sym(result))==(
            'source','earth' if label=='wrong_author' else 'author','earth' if label=='wrong_scope' else 'scope',
            'other' if label=='wrong_context' else 'text','syg' if label=='wrong_premise' else 'syd','syg' if label=='wrong_result' else 'syo')
        actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Earth source attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'quoted_physical_claim_is_not_executed_or_endorsed':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned earth source differs')
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0128');start=unit['text'].index('Man schließt daraus')
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Earth clock text differs')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=start,end=len(unit['text']),source=unit['text'][start:],
        definitions=['syi','syj','syk','syl','sym','syn','syo'],status='partial_explicit_reading',full_semantic_equivalence=False)],
        'facsimile_checked':False,'verified_full_units':0,'transition_from_colocated_return_to_separated_rates_is_attributed_not_proved':True}


def build_report():
    text,basis=composed();doc=parse(text)
    if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored earth clocks differ')
    if json.loads((ROOT/'data/earth-clocks-basis-v1.json').read_text(encoding='utf-8'))!=basis:raise ValueError('Earth basis differs')
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Earth clocks roundtrip differs')
    paths=[basis['document'],'data/earth-clocks-basis-v1.json','examples/v014/einstein-curved-clock.noema',
        'scripts/compose_earth_clocks.py','scripts/check_earth_clocks.py','scripts/check_tau_differential.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json','noema/discourse.py','noema/finite_semantics.py']
    return {'status':'partial_earth_equator_pole_controlled_rate_comparison','documents':{basis['document']:audit_basis(doc,basis)},
        'comparisons':checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},'lexical_reference':{'url':'https://www.patek.com/en/glossary',
            'checked_on':'2026-10-13','use':'balance and spring assembly regulates mechanical watch running; no proprietary design assumed'},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-curved-clock.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Earth clocks report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Earth clock mechanisms, controls, placement and rate comparison checked')


if __name__=='__main__':main()
