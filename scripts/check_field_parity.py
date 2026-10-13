"""Check a nonzero magnetic probe without equating symmetry with positive scale."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import xml.etree.ElementTree as ET
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_total_differential import setup, OPERATIONS
from scripts.check_field_transform import affine_callback
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_parity import ROOT, PARENT, CUT, composed, generic_composed

REPORT=ROOT/'reports/field-parity-v1.json'
DOMAIN=('x','y','z','t','rest','other')


def polynomial_checks():
    a,b,beta,r,N=('v '+n for n in ('first','second','beta','ratio','magnetic'))
    zero,one=literal(0),literal(1);neg=lambda x:k('ac',x);eq=lambda a,b:op('e',a,b);nz=lambda a:op('u',eq(a,zero));square=lambda a:k('ad',a,a)
    response=lambda scale,ratio:k('saw2',scale,beta,ratio,N)
    first,second=response(a,r),response(b,neg(r));nonzero=both(nz(beta),nz(r),nz(N))
    claims={
        'strict_flip_is_nonzero_additive_inverse':assertion('first second',op('z',k('saz2',a,b),both(nz(a),eq(b,neg(a))))),
        'nonzero_odd_response_forces_even_factor':assertion('first second beta ratio magnetic',op('y',both(nonzero,k('saz2',first,second)),eq(a,b))),
        'equal_nonzero_factors_give_strict_flip':assertion('first second beta ratio magnetic',op('y',both(nonzero,nz(a),eq(a,b)),k('saz2',first,second))),
        'equal_magnitude_alone_allows_same_sign':assertion('',both(eq(square(one),square(one)),op('u',k('saz2',one,one)))),
        'opposite_signs_alone_allow_unequal_magnitudes':assertion('',both(k('aa',literal(-1),zero),k('aa',zero,literal(2)),op('u',k('saz2',literal(-1),literal(2))))),
        'zero_response_does_not_establish_a_sign_change':assertion('',op('u',k('saz2',zero,zero))),
        'zero_ratio_hides_unequal_factors':assertion('beta magnetic',both(eq(k('saw2',one,beta,zero,N),neg(k('saw2',literal(2),beta,zero,N))),op('u',eq(one,literal(2))))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),{'aa':'less','ab':'add','ac':'negate','ad':'multiply'},timeout_ms=20000)[0]
        if result['status']!='valid':raise ValueError('Field parity algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_identities_only':True,'physical_symmetry_not_proved':True}


def signed_value_checks():
    doc=abstract(candidate(composed()[0],'r ja[] '+CUT+'.r jb[] '+CUT+'.q[k sba2[k ja[] k jb[]]].'),OPERATIONS);rows={}
    for a,b in ((1,-1),(-1,1),(2,-2),(-2,2),(0,0),(1,1),(-1,-1),(1,-2),(0,1)):
        fixture,model=setup(doc);model.update(ja=lambda:fixture.make(a),jb=lambda:fixture.make(b))
        actual=values(doc,model,DOMAIN)
        if actual!=[a!=0 and b==-a]:raise ValueError('Real sign/magnitude condition differs')
        rows[f'{a},{b}']=actual
    return {'cases':rows,'real_arithmetic_is_an_exact_rational_cut_fixture':True}


def source_checks():
    names=('sbe2','sbf2','saq2','sbg2','sbh2','sar2')
    doc=abstract(candidate(composed()[0],''.join('q[t[k '+name+'[]][k ri[]]].' for name in names)),OPERATIONS);rows={}
    labels=('baseline','negative_factor','unequal_reciprocal','opposite_factors','zero_factors',*(f'nonzero_component_{i}' for i in range(5)),
        'zero_magnetic','negative_magnetic','zero_speed','negative_speed','wrong_point','outside_region','wrong_context')
    for label in labels:
        fixture,model=setup(doc);c,n=fixture.make,fixture.read
        electric=[[1,0,0,0,-1],[0]*5,[0]*5];magnetic=[[0]*5,[0]*5,[0,2,0,0,1]]
        if label.startswith('nonzero_component_'):(electric+magnetic)[int(label[-1])][4]+=1
        if label=='zero_magnetic':magnetic[2]=[0]*5
        if label=='negative_magnetic':magnetic[2]=[0,2,0,0,-1]
        a,b={'negative_factor':(-1,-1),'unequal_reciprocal':(2,F(1,2)),'opposite_factors':(1,-1),'zero_factors':(0,0)}.get(label,(1,1))
        speed=-3 if label=='negative_speed' else 0 if label=='zero_speed' else 3
        point=(2 if label=='wrong_point' else 1,0,0,0)
        callbacks(doc,model,{'znl':affine_callback(doc,fixture,'znl',electric),'znm':affine_callback(doc,fixture,'znm',magnetic),
            'znk':lambda *xs:label!='outside_region','zn7':lambda role:c(point[DOMAIN.index(role)] if role in DOMAIN[:4] else 0),
            'znz':lambda value:c(a if n(value)==speed else b)})
        model.update(tc=lambda:c(5),zb7=lambda:c(speed),ra=lambda:'rest',ri=lambda:'text',
            znn=lambda frame,e,h,region,ctx:frame=='rest' and ctx==('other' if label=='wrong_context' else 'text'))
        actual=values(doc,model,DOMAIN)
        probe=not(label.startswith('nonzero_component_') or label in ('zero_magnetic','zero_speed','wrong_point','outside_region','wrong_context'))
        response=a==b and a!=0 and label not in ('zero_magnetic','zero_speed')
        inverse=a*b==1;expected=[probe,response,inverse,not(probe and inverse) or response,probe and inverse and response,a==b]
        if actual!=expected:raise ValueError('Footnote probe or response differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'fields_are_not_required_to_be_constant_away_from_the_probe':True,
        'negative_even_factor_not_excluded':True,'physical_symmetry_response_is_not_assumed_automatically':True}


def component_checks():
    point='k zn7[]';coords=[app(point,'k '+role+'[]') for role in ('yn','yo','yp','zc7')]
    N=app(app('k znm[]','k yp[]'),*coords);zero=k('bb',literal(0));V='k tc[]'
    queries=[]
    for speed in ('k zb7[]',k('bf',zero,'k zb7[]')):
        full=k('sal2',app('k znz[]',speed),k('s6i',V,speed,'k znl[]','k znm[]'))
        reduced=k('sbb2',app('k znz[]',speed),k('soy',V,speed),k('shv',speed,k('sjd',V)),N)
        queries.append('q['+k('sca',app(app(full,'k yo[]'),*coords),reduced)+'].')
    doc=abstract(candidate(composed()[0],''.join(queries)),OPERATIONS);rows={}
    for speed,magnetic,factor in ((3,1,1),(-3,1,1),(3,-1,1),(3,2,-1)):
        fixture,model=setup(doc);c=fixture.make
        callbacks(doc,model,{'znl':affine_callback(doc,fixture,'znl',[[1,0,0,0,-1],[0]*5,[0]*5]),
            'znm':affine_callback(doc,fixture,'znm',[[0]*5,[0]*5,[0,2,0,0,magnetic]]),
            'zn7':lambda role:c(1 if role=='x' else 0),'znz':lambda value:c(factor)})
        model.update(tc=lambda:c(5),zb7=lambda:c(speed));actual=values(doc,model,DOMAIN)
        if actual!=[True,True]:raise ValueError('Reduced response is not the original Y component')
        rows[str((speed,magnetic,factor))]=actual
    return {'cases':rows,'same_old_event_compared_at_both_speeds':True,'no_equal_numeric_new_coordinates_assumed':True}


def attribution_checks():
    source=parse(composed()[0]);rows={}
    for index,node,kind,contents in ((-2,'zoa','uh',('sbg2',)),(-1,'zob','zc',('sbh2','sar2'))):
        doc=dict(source,statements=[source['statements'][index]])
        for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_content'):
            model=guarded(doc)
            for name,value in {node:'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
            def relation(n,author,*args):
                descriptions,scope,ctx=args[:-2],args[-2],args[-1]
                return (n,author,scope,ctx)==('node','other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and tuple(json.loads(d.syntax)['symbol'] for d in descriptions)==(('other',)*len(contents) if label=='wrong_content' else contents)
            model[kind]=relation;actual=values(doc,model,('node','author','scope','other'))
            if actual!=[label=='baseline']:raise ValueError('Footnote attribution differs')
            rows[node+':'+label]=actual
    return {'cases':rows,'physical_claims_not_evaluated_during_attribution':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Parity source changed')
    meta=json.loads((ROOT/'data/field-scale-inverse-facsimile-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256((ROOT/meta['image']).read_bytes()).hexdigest()!=meta['image_sha256']:raise ValueError('Footnote scan changed')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0282')
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Footnote text changed')
    base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['sba2','sbb2','sbc2','sbd2','sbe2','sbf2','sbg2','sbh2'],status='partial_explicit_reading',full_semantic_equivalence=False)
    start=unit['text'].index('daß bei Zeichenwechsel');rows=[dict(base,start=start,end=len(unit['text']),source=unit['text'][start:])];maths={}
    for mid in unit['math_ids']:
        m=next(m for m in source['math'] if m['id']==mid)
        if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Footnote math changed')
        maths[mid]=''.join(ET.fromstring(m['mathml']).itertext());rows.append(dict(base,math_id=mid,math_sha256=m['sha256']))
    if maths!={'M0443':'X=Y=Z=L=M=0','M0444':'N≠0','M0445':'v','M0446':'Y′'}:raise ValueError('Footnote component order differs')
    ref=next(a for a in source['annotations'] if a['id']=='A0023')
    if ref['targets']!=['#cite_note-4'] or 'cite_note-4' not in unit['source_ids']:raise ValueError('Footnote backlink differs')
    return {'segments':rows,'source_math_text':maths,'body_reference':'einstein-1905:u0167','reference_target':ref['targets'][0],
        'facsimile_scope':'Author footnote at bottom of printed p909 inspected; inventory page_at_end=921 is the placement of collected notes, not its print page',
        'physical_symmetry_and_clarity_phrase_excluded_from_ranges':True,'nonzero_speed_interpretation_explicit':True,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'field-parity'),(composed,'einstein-field-parity')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored field parity differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Field parity roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-2]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Parent parity source changed')
    paths=list(documents)+['data/field-parity-basis-v1.json','data/einstein-field-parity-basis-v1.json',PARENT,
        'scripts/compose_field_parity.py','scripts/check_field_parity.py','scripts/check_field_transform.py','scripts/check_total_differential.py',
        'data/field-scale-inverse-facsimile-v1.json','artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    return {'status':'partial_nonzero_magnetic_probe_and_signed_response','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'signed_values':signed_value_checks(),'source':source_checks(),'components':component_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Field parity report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Signed response, nonzero probe, even coefficient and footnote alignment checked')


if __name__=='__main__':main()
