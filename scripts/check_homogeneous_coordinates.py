"""Check affine rows, origin offsets and limits of the homogeneity inference."""
import argparse
import hashlib
import json
from fractions import Fraction

from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_measurements import ARITHMETIC, cut
from scripts.check_rod_setup import callbacks, embedding, guarded
from scripts.check_real_products import MEANINGS, ZERO, call, op, assertion
from scripts.compose_homogeneous_coordinates import ROOT, CUT, VECTOR, MATRIX, MAP, OP, VALID, SAME, generic_composed, source_composed

REPORT=ROOT/'reports/homogeneous-coordinates-v1.json'
ROLES=('x','y','z','t')
CUT_SORT={'kind':'function','parameters':['number'],'result':'truth'}
VECTOR_SORT={'kind':'function','parameters':['individual'],'result':CUT_SORT}


def vector(values):
    return FunctionValue(('individual',),CUT_SORT,lambda role:cut(values.get(role,0)))


def evaluate(doc,model,domain=ROLES):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('motion','text','other'),
        primitives=model,max_steps=3_000_000,memoize_definitions=True,memoize_expressions=True)]


def matrix_checks():
    doc=parse(generic_composed()[0]+'r ja[] j[a].r jb[] '+MATRIX+'.r jc[] '+VECTOR+'.r jd[] '+VECTOR+'.r je[] '+VECTOR+'.r jf[] '+OP+'.r jg[] '+OP+'.r jh[] '+SAME+'.r ji[] '+VALID+'.'+
        'q[k shn[k ja[] k jd[] k ji[]]].q[k sho[k ja[] k shq[k ja[] k jb[] k jc[] k jd[] k jf[] k jg[]] k je[] k jh[]]].')
    rows={}
    names=('baseline','zero_offset','constant_map','wrong_x','wrong_y','wrong_z','wrong_t','duplicate_axis','empty_axes','invalid_input')
    for name in names:
        matrix=((2,1,0,-1),(0,1,0,0),(0,0,-2,0),(1,0,0,1)) if name!='constant_map' else ((0,0,0,0),)*4
        offset=(0,)*4 if name=='zero_offset' else (3,-1,2,5)
        inputs=(1,2,-1,3) if name!='invalid_input' else (30,2,-1,3)
        expected=[offset[i]+sum(matrix[i][j]*inputs[j] for j in range(4)) for i in range(4)]
        if name.startswith('wrong_'):expected[ROLES.index(name[-1])]+=1
        axes=() if name=='empty_axes' else ROLES+('x',) if name=='duplicate_axis' else ROLES
        model={**ARITHMETIC,'ja':lambda:SequenceValue(axes,'"individual"')}
        callbacks(doc,model,{'jb':lambda a,b:cut(matrix[ROLES.index(a)][ROLES.index(b)]),
            'jc':lambda r:cut(offset[ROLES.index(r)]),'jd':lambda r:cut(inputs[ROLES.index(r)]),
            'je':lambda r:cut(expected[ROLES.index(r)]),
            'jf':lambda a,b:cut(embedding(a)+embedding(b)),'jg':lambda a,b:cut(embedding(a)*embedding(b)),
            'jh':lambda a,b:embedding(a)==embedding(b),'ji':lambda value:abs(embedding(value))<25})
        actual=evaluate(doc,model)
        expected_truth=[name not in ('duplicate_axis','empty_axes','invalid_input'),name in ('baseline','zero_offset','constant_map','invalid_input')]
        if actual!=expected_truth:raise ValueError('Affine matrix row differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'integer_embedding_oracles':True,'all_real_inputs_proved':False}


def increment_checks():
    doc=parse(generic_composed()[0]+'r ja[] j[a].r jb[] '+VECTOR+'.r jc[] '+VECTOR+'.r jd[] '+VECTOR+'.r je[] '+MAP+'.r jf[] '+VALID+'.r jg[] '+SAME+'.r jh[] '+OP+'.r ji[] '+OP+'.'+
        'q[k shr[k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jg[] k jh[] k ji[]]].')
    rows={}
    for name in ('affine_with_offset','affine_without_offset','quadratic','quadratic_zero_shift','quadratic_same_base','invalid_output','duplicate_axis','empty_axes'):
        first=dict(zip(ROLES,(0,1,-1,2)));second=dict(zip(ROLES,(1,-1,2,0)))
        if name=='quadratic_same_base':second=first
        shift=dict(zip(ROLES,(0,0,0,0) if name=='quadratic_zero_shift' else (1,2,-1,1)))
        axes=() if name=='empty_axes' else ROLES+('x',) if name=='duplicate_axis' else ROLES
        def transform(v):
            x,y,z,t=(embedding(v(r)) for r in ROLES)
            result=(x*x,y,z,t) if name.startswith('quadratic') else (2*x+y-t,y,-2*z,x+t)
            if name=='affine_with_offset':result=tuple(a+b for a,b in zip(result,(3,-1,2,5)))
            if name=='invalid_output':result=(30,*result[1:])
            return vector(dict(zip(ROLES,result)))
        model={**ARITHMETIC,'ja':lambda:SequenceValue(axes,'"individual"')}
        callbacks(doc,model,{'jb':lambda r:cut(first[r]),'jc':lambda r:cut(second[r]),'jd':lambda r:cut(shift[r]),
            'je':transform,'jf':lambda v:abs(embedding(v))<25,'jg':lambda a,b:embedding(a)==embedding(b),
            'jh':lambda a,b:cut(embedding(a)+embedding(b)),'ji':lambda a,b:cut(embedding(a)-embedding(b))})
        actual=evaluate(doc,model)[0]
        if actual!=(name in ('affine_with_offset','affine_without_offset','quadratic_zero_shift','quadratic_same_base')):raise ValueError('Homogeneous increment differs: '+name)
        rows[name]=actual
    return {'cases':rows,'local_pairs_only':True,'global_homogeneity_proved':False}


def polynomial_checks():
    add=lambda a,b:call('ab',a,b)
    sub=lambda a,b:add(a,call('ac',b))
    row=lambda point,offset='v offset':call('shw',*(('v '+r) for r in ('a','b','c','d')),offset,*point)
    first=['v '+r for r in ('x','y','z','t')];second=['v '+r for r in ('u','v','w','s')];delta=['v '+r for r in ('dx','dy','dz','dt')]
    inc=lambda p,offset='v offset':sub(row([add(a,b) for a,b in zip(p,delta)],offset),row(p,offset))
    quadratic=lambda p:call('ad',p,p)
    claims={
        'affine_increment_is_base_independent':assertion('a b c d offset x y z t u v w s dx dy dz dt',op('e',inc(first),inc(second))),
        'offset_does_not_change_increments':assertion('a b c d offset other x y z t dx dy dz dt',op('e',inc(first),inc(first,'v other'))),
        'origin_maps_to_offset':assertion('a b c d offset',op('e',row([ZERO]*4),'v offset')),
        'affine_form_always_preserves_origin':assertion('a b c d offset',op('e',row([ZERO]*4),ZERO)),
        'quadratic_increment_is_base_independent':assertion('x u dx',op('e',sub(quadratic(add('v x','v dx')),quadratic('v x')),sub(quadratic(add('v u','v dx')),quadratic('v u')))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name in ('affine_form_always_preserves_origin','quadratic_increment_is_base_independent') else 'valid'
        if result['status']!=expected:raise ValueError('Affine rational lemma differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'homogeneity_implies_real_affinity_proved':False}


def signed_product_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.r jd[] '+SAME+'.q[c[k jd[]][k shv[k ja[] k jb[]] k jc[]]].'),{'bc','be','sah'})
    rows={}
    for a,b in ((2,3),(-2,3),(2,-3),(-2,-3),(0,3),(3,0),(0,-3),(-3,0),(0,0)):
        model=guarded(doc)
        model.update(aa=lambda x,y:x<y,ja=lambda:cut(a),jb=lambda:cut(b),jc=lambda:cut(a*b),
            bc=lambda x,y:embedding(x)<=embedding(y),be=lambda x:cut(-embedding(x)),sah=lambda x,y:cut(embedding(x)*embedding(y)))
        callbacks(doc,model,{'jd':lambda x,y:embedding(x)==embedding(y)})
        actual=evaluate(doc,model,('object',))[0]
        if not actual:raise ValueError('Signed product composition differs')
        rows[str((a,b))]=actual
    return {'cases':rows,'existing_cut_operations_replaced_with_integer_oracles':True,'full_real_field_laws_proved':False}


def canonical_map_checks():
    doc=candidate(source_composed()[0],'r ja[] '+VECTOR+'.r jb[] '+VECTOR+'.r jc[] '+SAME+'.q[k sho[k shx[] c[k sia[]][k ja[]] k jb[] k jc[]]].')
    domain=(*ROLES,'hidden','rest','moving','length','time');rows={}
    for name in ('baseline','changed_hidden_input','map_reads_hidden_input','wrong_source','wrong_target','wrong_length_unit','wrong_time_unit','wrong_context'):
        model=guarded(doc)
        constants={'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'moving' if name=='wrong_source' else 'rest',
            'zbm':'rest' if name=='wrong_target' else 'moving','ta':'time' if name=='wrong_length_unit' else 'length',
            'rb':'length' if name=='wrong_time_unit' else 'time','zb6':'other' if name=='wrong_context' else 'motion'}
        for k,v in constants.items():model[k]=lambda v=v:v
        model['aa']=lambda a,b:a<b
        def selected(f,g,l,t,ctx):
            def transform(v):
                right=(f,g,l,t,ctx)==('rest','moving','length','time','motion')
                return vector({r:embedding(v(r))+2+(embedding(v('hidden')) if name=='map_reads_hidden_input' else 0) if right else 20 for r in ROLES})
            return FunctionValue((VECTOR_SORT,),VECTOR_SORT,transform)
        model['zdd']=selected
        callbacks(doc,model,{'ja':lambda r:cut(17 if name=='changed_hidden_input' else 9) if r=='hidden' else cut(1),
            'jb':lambda r:cut(3),'jc':lambda a,b:embedding(a)==embedding(b)})
        actual=evaluate(doc,model,domain)[0]
        if actual!=(name in ('baseline','changed_hidden_input','map_reads_hidden_input')):raise ValueError('Four-coordinate map binding differs: '+name)
        rows[name]=actual
    return rows


def graph_binding_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] '+MAP+'.q[k sib[k ja[]]].'),{'shf','shg','she','shh','ba','sca'})
    domain=('a','b','c','d',*ROLES);coords={'a':0,'b':1,'c':2,'d':3};rows={}
    for name in ('baseline','wrong_output','missing_pair','extra_pair','invalid_output','empty_source'):
        pairs={('a','c'),('b','d')}
        if name=='missing_pair':pairs.remove(('b','d'))
        if name=='extra_pair':pairs.add(('a','d'))
        model=guarded(doc)
        model.update(shf=lambda t:t in ('a','b') and name!='empty_source',shg=lambda t:t in ('c','d'),she=lambda a,b:(a,b) in pairs,
            shh=lambda a,b:coords.get(a)==coords.get(b),ba=lambda v:abs(embedding(v))<25,sca=lambda a,b:embedding(a)==embedding(b),
            yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zc7=lambda:'t',zc6=lambda t,r:cut(coords.get(t,0) if r=='x' else 0))
        callbacks(doc,model,{'ja':lambda v:vector({r:(30 if name=='invalid_output' else embedding(v(r))+(1 if name=='wrong_output' else 2)) if r=='x' else embedding(v(r)) for r in ROLES})})
        actual=evaluate(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('Prior coordinate graph binding differs: '+name)
        rows[name]=actual
    return {'cases':rows,'coordinate_assignments_and_cut_conditions_are_oracles':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_premise','wrong_conclusion','wrong_obviousness','wrong_task'):
        model=guarded(doc)
        for key,value in {'zde':'homogeneity','zdf':'inference','zdb':'task','rd':'author','rh':'scope','ri':'text'}.items():model[key]=lambda value=value:value
        symbol=lambda desc:json.loads(desc.syntax)['symbol']
        def common(author,scope,ctx):return (author,scope,ctx)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model.update(ug=lambda n,a,d,s,c:n=='homogeneity' and common(a,s,c) and symbol(d)==('sid' if name=='wrong_premise' else 'sic'),
            zc=lambda n,a,p,q,s,c:n=='inference' and common(a,s,c) and (symbol(p),symbol(q))==('sid' if name=='wrong_premise' else 'sic','sic' if name=='wrong_conclusion' else 'sid'),
            zdg=lambda n,a,d,s,c:n=='inference' and common(a,s,c) and symbol(d)==('sic' if name=='wrong_obviousness' else 'sid'),
            zdh=lambda n,t,d,s,c:(n,t,s,c)==('inference','other' if name=='wrong_task' else 'task','scope','text') and symbol(d)=='sid')
        actual=evaluate(doc,model,('homogeneity','inference','task','author','scope'))
        bad={'wrong_author','wrong_scope','wrong_context'}
        expected=[name not in bad|{'wrong_premise'},name not in bad|{'wrong_premise','wrong_conclusion','wrong_obviousness','wrong_task'}]
        if actual!=expected:raise ValueError('Homogeneity inference attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0047')
    digest='310fcb8ac513c187ebaf29ec06e0f7c72cb46b12b8b9be78fd0e1a5cf88d69be'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Homogeneity source changed')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['shs','sht','sic','sid'],'status':'partial_explicit_interpretation','full_semantic_equivalence':False}],
        'affine_reading_with_unfixed_origins':True,'homogeneity_is_operational_interpretation':True,'facsimile_checked':False,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored homogeneity differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Homogeneity roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/homogeneous-coordinates-basis-v1.json','data/einstein-homogeneous-coordinates-basis-v1.json',
        'examples/v014/einstein-coordinate-correspondence.noema','scripts/compose_homogeneous_coordinates.py','scripts/check_homogeneous_coordinates.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-coordinate-correspondence.noema').read_text(encoding='utf-8')
    return {'status':'partial_homogeneous_increments_affine_form_and_attribution','documents':documents,
        'matrix_rows':matrix_checks(),'increments':increment_checks(),'polynomial_lemmas':polynomial_checks(),
        'signed_product':signed_product_checks(),'four_role_map':canonical_map_checks(),'graph_binding':graph_binding_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Homogeneity report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Affine rows, homogeneous increments, origins and attributed inference checked')


if __name__=='__main__':main()
