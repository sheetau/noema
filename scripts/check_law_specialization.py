"""Check conditional law transfer without identifying distinct field values."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
import xml.etree.ElementTree as ET

from noema.finite_semantics import Content, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_law_invariance import source_model, base_facts
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded, callbacks
from scripts.check_field_transform import setup, affine_callback, OPS
from scripts.compose_law_specialization import ROOT, PARENT, composed, generic_composed

REPORT=ROOT/'reports/law-specialization-v1.json'
DOMAIN=('first','second','system','historyone','leftone','rightone','lawone','extra')


def values(doc,model,domain):
    return [row['value'] for row in evaluate_document(doc,individuals=domain,situations=('text',),
        primitives=model,max_steps=15_000_000,memoize_definitions=True,memoize_expressions=True)]


def generic_checks():
    args='k ja[] k jb[] k jc[] k jd[] k je[] k jf[] p jg p jh'
    doc=parse(generic_composed()[0]+'''
r ja[] a.r jb[] a.r jc[] a.r jd[] a.r je[] a.r jf[] a.
r jg[a a a] c.r jh[a a] c.r ji[] e.r jj[] e.r jk[] d.
'''+f'q[k s77[{args}]].q[k saa2[{args} k ji[] k jj[] k jk[]]].q[k sab2[{args} k ji[] k jj[] k jk[]]].')
    rows=[]
    for lf,rf,source,target in product((False,True),repeat=4):
        for variant in ('baseline','missing_left','wrong_history','wrong_law','extra_disagrees','wrong_context'):
            reps={('historyone','first','leftone'),('historyone','second','rightone')}
            if variant=='missing_left':reps.remove(('historyone','first','leftone'))
            if variant=='wrong_history':reps={('extra',f,r) for h,f,r in reps}
            if variant=='extra_disagrees':reps.add(('historyone','second','extra'))
            def fit(law,rep):
                return law==('extra' if variant=='wrong_law' else 'lawone') and {'leftone':lf,'rightone':rf,'extra':not lf}.get(rep,False)
            model={name:(lambda value=value:value) for name,value in zip(('ja','jb','jc','jd','je','jf'),('historyone','first','second','lawone','leftone','rightone'))}
            model.update(jg=lambda *args:args in reps,jh=fit,ji=lambda:Content(('text','other'),(source,not source)),
                jj=lambda:Content(('text','other'),(target,not target)),jk=lambda:'other' if variant=='wrong_context' else 'text')
            actual=[r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('text','other'),primitives=model,max_steps=1_000_000)]
            left=[r for h,f,r in reps if h=='historyone' and f=='first'];right=[r for h,f,r in reps if h=='historyone' and f=='second']
            shared=bool(left and right) and 'leftone' in left and 'rightone' in right and all(fit('lawone',a)==fit('lawone',b) for a in left for b in right)
            s,t=(not source,not target) if variant=='wrong_context' else (source,target)
            bridge=shared and fit('lawone','leftone')==s and fit('lawone','rightone')==t
            expected=[shared,bridge,not(bridge and s) or t]
            if actual!=expected or not actual[2]:raise ValueError('Generic conditional transfer differs: '+variant)
            rows.append(dict(left_fit=lf,right_fit=rf,source=source,target=target,variant=variant,result=actual))
    return {'cases':rows,'same_fitness_does_not_imply_same_representation':True}


def source_checks():
    query=''.join('q[t[k '+name+'[]][k ri[]]].' for name in ('saw','sad2','sae2','saf2'))
    doc=abstract(candidate(composed()[0],query),{'s5z','sac2'});rows={}
    for source,target in product((False,True),repeat=2):
        facts=base_facts();facts['laws']={'lawone'};facts['histories']={'historyone'}
        facts['systems']={('historyone','system','text')}
        facts['representations']={('historyone','first','leftone','text'),('historyone','second','rightone','text')}
        facts['allowed']={('lawone',rep,'text') for rep,truth in (('leftone',source),('rightone',target)) if truth}
        for variant in ('baseline','wrong_selected_history','wrong_selected_law','missing_representation','extra_disagrees','incomplete_scope','mismatched_source_content','wrong_selected_representation'):
            f=deepcopy(facts);model=source_model(doc,f)
            if variant=='missing_representation':f['representations'].remove(('historyone','second','rightone','text'))
            if variant=='extra_disagrees':
                f['representations'].add(('historyone','second','extra','text'))
                if not source:f['allowed'].add(('lawone','extra','text'))
            if variant=='incomplete_scope':f['complete']=set()
            model.update(zbm=lambda:'second',znu=lambda:'extra' if variant=='wrong_selected_law' else 'lawone',
                znv=lambda:'extra' if variant=='wrong_selected_history' else 'historyone',znw=lambda:'leftone',
                znx=lambda:'extra' if variant=='wrong_selected_representation' else 'rightone',
                s5z=lambda:Content(('text',),(not source if variant=='mismatched_source_content' else source,)),
                sac2=lambda:Content(('text',),(target,)))
            actual=values(doc,model,DOMAIN)
            principle=source==target and variant not in ('missing_representation','extra_disagrees','incomplete_scope')
            bridge=variant not in ('wrong_selected_history','wrong_selected_law','missing_representation','mismatched_source_content','wrong_selected_representation')
            s=not source if variant=='mismatched_source_content' else source
            expected=[principle,bridge,principle and bridge,not s or target]
            if actual!=expected or (actual[2] and not actual[3]):raise ValueError('Source specialization differs: '+str((source,target,variant,actual,expected)))
            rows[f'{int(source)}{int(target)}:{variant}']=actual
    return {'cases':rows,'full_principle_evaluated_on_supplied_finite_relations':True,
        'only_equation_contents_replaced_by_truth_oracles':True,'arbitrary_physical_systems_verified':False}


def field_binding_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sac2[]][k ri[]]].'),OPS|{'s5y'});rows={}
    for variant in ('baseline','wrong_frame','wrong_electric','wrong_magnetic','wrong_region','wrong_context','equations_false','wrong_light_speed'):
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        callbacks(doc,model,{'znr':affine_callback(doc,fixture,'znr',[(0,0,0,0,a) for a in (2,3,5)]),
            'zns':affine_callback(doc,fixture,'zns',[(0,0,0,0,a) for a in (7,11,13)]),'znt':lambda *xs:True})
        def components(field):return tuple(n(field(a)(c(0),c(0),c(0),c(0))) for a in ('x','y','z'))
        def bound(frame,e,h,region,context):
            return frame==('first' if variant=='wrong_frame' else 'second') and context==('other' if variant=='wrong_context' else 'text') and components(e)==((99,3,5) if variant=='wrong_electric' else (2,3,5)) and components(h)==((99,11,13) if variant=='wrong_magnetic' else (7,11,13)) and region(c(0),c(0),c(0),c(0))==(variant!='wrong_region')
        model.update(zbm=lambda:'second',ri=lambda:'text',tc=lambda:c(7 if variant=='wrong_light_speed' else 5),znn=bound,
            s5y=lambda e,h,region,light:variant!='equations_false' and components(e)==(2,3,5) and components(h)==(7,11,13) and region(c(0),c(0),c(0),c(0)) and n(light)==5)
        actual=values(doc,model,(*DOMAIN,'x','y','z','t'))
        if actual!=[variant=='baseline']:raise ValueError('Primed field binding differs: '+variant)
        rows[variant]=actual
    return {'cases':rows,'six_equation_predicate_is_an_explicit_fixture_oracle':True,
        'computed_mixed_fields_not_invoked':True,'field_samples_check_argument_binding_only':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    expected=('node','author','sae2','saf2','scope','text')
    for index in range(-1,6):
        model=guarded(doc)
        for name,value in {'zny':'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        target=list(expected)
        if index>=0:target[index]='other'
        model['zc']=lambda node,author,premise,conclusion,scope,context:[node,author,json.loads(premise.syntax)['symbol'],json.loads(conclusion.syntax)['symbol'],scope,context]==target
        actual=values(doc,model,('node','author','scope','other'))
        if actual!=[index==-1]:raise ValueError('Conditional attribution differs')
        rows['baseline' if index==-1 else 'wrong_'+str(index)]=actual
    return {'cases':rows,'quoted_contents_not_executed_as_truth':True,'attributed_inference_is_not_a_proof':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Law source inventory differs')
    rows=[]
    for index in (161,162):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Law source text differs')
        base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['sac2','sad2','sae2','saf2'],status='partial_explicit_reading',full_semantic_equivalence=False)
        if index==161:
            for phrase in ('Das Relativitätsprinzip fordert nun, daß die ','auch im System [M0294] gelten, wenn sie im System [M0295] gelten'):
                start=unit['text'].index(phrase);rows.append(dict(base,start=start,end=start+len(phrase),source=phrase))
        for mid in unit['math_ids']:
            m=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Law source math differs')
            rows.append(dict(base,math_id=mid,math_sha256=m['sha256']))
    m=next(m for m in source['math'] if m['id']=='M0300');ns='{http://www.w3.org/1998/Math/MathML}'
    fractions=[(''.join(f[0].itertext()),''.join(f[1].itertext())) for f in ET.fromstring(m['mathml']).iter(ns+'mfrac')]
    expected=[]
    for left,pos,neg in (('Xτ','Nη','Mζ'),('Lτ','Yζ','Zη'),('Yτ','Lζ','Nξ'),('Mτ','Zξ','Xζ'),('Zτ','Mξ','Lη'),('Nτ','Xη','Yξ')):
        expected.append(('1','V'));expected.extend(('∂'+term[0]+'′','∂'+term[1]) for term in (left,pos,neg))
    if fractions!=expected:raise ValueError('Primed equation derivative order differs')
    return {'segments':rows,'source_fraction_order':[list(p) for p in fractions],
        'operational_force_definitions_excluded_from_prose_ranges':True,'facsimile_review':False,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'law-specialization'),(composed,'einstein-law-specialization')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored law specialization differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Law specialization roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-1]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Prior source changed')
    paths=list(documents)+['data/law-specialization-basis-v1.json','data/einstein-law-specialization-basis-v1.json',PARENT,
        'scripts/compose_law_specialization.py','scripts/check_law_specialization.py','scripts/check_law_invariance.py',
        'scripts/check_field_transform.py','noema/discourse.py','noema/finite_semantics.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_conditional_law_specialization_with_independent_primed_fields','documents':documents,
        'generic':generic_checks(),'source':source_checks(),'field_binding':field_binding_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Law specialization report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Conditional law transfer, independent field binding and attribution checked')


if __name__=='__main__':main()
