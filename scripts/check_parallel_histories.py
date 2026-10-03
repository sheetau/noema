"""Check quantifier order, unique configurations and the limits of symmetry."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, embedding, guarded
from scripts.check_rod_measurements import cut
from scripts.compose_parallel_histories import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/parallel-histories-v1.json'
SCENES=('initial','motion','alternative','snapshot','text','other')


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=SCENES,
        primitives=model,max_steps=3_000_000,memoize_definitions=True,memoize_expressions=True)]


def history_document(source=False):
    text=source_composed()[0] if source else generic_composed()[0]
    common='''
r ja[a] c.r jb[a] c.r jc[a a a] c.r jd[a a] c.r je[a a] c.r jf[a] c.r jg[] a.
'''
    queries=('q[k sfy[p jb p jc p jd p jf]].' if source else 'q[k sfq[p ja p jb p jc p jd p je]].')
    queries+='q[k sfr[p ja p jb p jc p jd p je]].'
    queries+=('q[k sfx[k jg[] p jb p jc p jd p jf]].' if source else 'q[k sfp[k jg[] p ja p jc p jd p je]].')
    return candidate(text,common+queries)


def history_checks(source=False):
    doc=history_document(source);rows=[]
    states={('ha','first'):'aa',('ha','last'):'ab',('hb','first'):'ba',('hb','last'):'bb'}
    domain=('ha','hb','first','last','aa','ab','ba','bb','alias')
    for bits in product((False,True),repeat=4):
        properties=dict(zip(states.values(),bits));model=guarded(doc)
        model.update(ja=lambda m:m in ('first','last'),jb=lambda h:h in ('ha','hb'),
            jc=lambda h,m,s:states.get((h,m))==s,jd=lambda a,b:a==b,
            je=lambda m,s:properties.get(s,False),jf=lambda s:properties.get(s,False),jg=lambda:'ha')
        if source:model.update(ys=lambda m,ctx:ctx=='motion' and m in ('first','last'),zb6=lambda:'motion')
        actual=values(doc,model,domain)
        expected=[all(bits[:2]) or all(bits[2:]),(bits[0] or bits[2]) and (bits[1] or bits[3]),all(bits[:2])]
        if actual!=expected:raise ValueError('One-history quantifier order differs')
        rows.append({'parallel_at_history_times':list(bits),'results':actual})
    return rows


def uniqueness_checks():
    doc=history_document();rows={}
    domain=('ha','hb','first','last','aa','ab','ba','bb','alias')
    for name in ('baseline','missing_last','duplicate_same_pose','conflicting_pose','equivalent_pose_with_bad_property','empty_times'):
        states={('ha','first','aa'),('ha','last','ab')}
        if name=='missing_last':states.remove(('ha','last','ab'))
        if name in ('duplicate_same_pose','equivalent_pose_with_bad_property'):states.add(('ha','last','alias'))
        if name=='conflicting_pose':states.add(('ha','last','bb'))
        model=guarded(doc)
        model.update(ja=lambda m:name!='empty_times' and m in ('first','last'),jb=lambda h:h=='ha',
            jc=lambda *args:args in states,jd=lambda a,b:('ab' if a=='alias' else a)==('ab' if b=='alias' else b),
            je=lambda m,s:name!='equivalent_pose_with_bad_property' or s!='alias',
            jf=lambda s:name!='equivalent_pose_with_bad_property' or s!='alias',jg=lambda:'ha')
        actual=values(doc,model,domain)
        good=name in ('baseline','duplicate_same_pose')
        # Pointwise selection can ignore one bad equivalent representation;
        # the all-representations condition deliberately cannot.
        expected=[good,good or name=='equivalent_pose_with_bad_property',good]
        if actual!=expected:raise ValueError('Configuration uniqueness differs: '+name+' '+repr(actual))
        rows[name]=actual
    return rows


def symmetry_checks():
    doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a] a.r jc[a] a.r jd[a] c.
q[k sfs[p ja p jb p jc p jd]].''')
    rows={}
    for name in ('swap_preserves','identity_preserves','empty_domain','forward_leaves_domain','inverse_leaves_domain',
        'not_inverse','not_invariant'):
        forward={'ha':'hb','hb':'ha','outside':'outside'};inverse=dict(forward)
        if name=='identity_preserves':forward=inverse={x:x for x in forward}
        if name=='forward_leaves_domain':forward['ha']='outside'
        if name=='inverse_leaves_domain':inverse['ha']='outside'
        if name=='not_inverse':inverse['ha']='ha'
        model={'ja':lambda h:name!='empty_domain' and h in ('ha','hb'),'jb':lambda h:forward[h],
            'jc':lambda h:inverse[h],'jd':lambda h:name!='not_invariant' or h=='ha'}
        actual=values(doc,model,('ha','hb','outside'))[0]
        if actual!=(name in ('swap_preserves','identity_preserves')):raise ValueError('Symmetry model differs: '+name)
        rows[name]=actual
    # Both histories may be admissible and swapped by a symmetry while every
    # configuration is nonparallel; invariance is no existence proof.
    no_parallel=history_checks()[0]['results'][0]
    if no_parallel or not rows['swap_preserves']:raise ValueError('Symmetry countermodel differs')
    return {'cases':rows,'symmetry_without_parallel_history':{'symmetry':True,'parallel_history_exists':no_parallel}}


def time_binding_checks():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] h[h[b] c] c.r je[] h[h[b] c h[b] c] c.
q[k sfu[k ja[] k jb[] k jc[] k jd[] k je[]]].''')
    names=('baseline','wrong_history','wrong_moment','wrong_pose','wrong_frame','wrong_unit','wrong_history_context',
        'missing_common_time','missing_candidate_time','different_time_value','invalid_time','wrong_assignment_value','untyped_pose')
    rows={}
    for name in names:
        model=guarded(doc)
        const={'ja':'other' if name=='wrong_history' else 'history','jb':'other' if name=='wrong_moment' else 'moment',
            'jc':'other' if name=='wrong_pose' else 'pose','ra':'other' if name=='wrong_frame' else 'frame',
            'rb':'other' if name=='wrong_unit' else 'unit','zb6':'motion'}
        for key,val in const.items():model[key]=lambda val=val:val
        model.update(zci=lambda h:'other' if name=='wrong_history_context' or h!='history' else 'alternative',
            zcn=lambda p:name!='untyped_pose' and p=='pose',
            zcf=lambda m,f,u,ctx:(m,f,u)==('moment','frame','unit') and ctx in ('motion','alternative') and not(
                name=='missing_common_time' and ctx=='motion' or name=='missing_candidate_time' and ctx=='alternative'),
            yl=lambda m,f,u,ctx:cut(2 if name=='different_time_value' and ctx=='alternative' else 1),
            zck=lambda h,m,p,f,u,t,ctx:(h,m,p,f,u,ctx)==('history','moment','pose','frame','unit','alternative') and embedding(t)==(2 if name=='wrong_assignment_value' else 1))
        callbacks(doc,model,{'jd':lambda value:name!='invalid_time','je':lambda a,b:embedding(a)==embedding(b)})
        actual=values(doc,model,('history','moment','pose','frame','unit','other'))[0]
        if actual!=(name=='baseline'):raise ValueError('Rest-time configuration binding differs: '+name)
        rows[name]=actual
    return {'cases':rows,'full_real_equality_evaluated':False}


def configuration_checks():
    doc=candidate(source_composed()[0],'r ja[] a.q[k sfw[k ja[]]].')
    axes={(f,r):f+r for f in ('a','b') for r in ('x','y','z')}
    domain=('a','b','x','y','z','oa','ob','pose',*axes.values(),'other');rows={}
    for name in ('baseline','untyped_pose','unknown_snapshot','wrong_origin','replaced_axis','missing_assignment',
        'not_material','not_rigid','not_perpendicular','x_not_parallel','y_not_parallel','z_not_parallel'):
        model=guarded(doc)
        for key,val in {'ja':'pose','ra':'a','zbm':'b','yn':'x','yo':'y','yp':'z','zb4':'initial'}.items():model[key]=lambda val=val:val
        def axis(f,r,ctx):return 'other' if name=='replaced_axis' and (f,r,ctx)==('b','z','snapshot') else axes.get((f,r),'other')
        model.update(zcn=lambda p:p=='pose' and name!='untyped_pose',zcl=lambda p:'other' if name=='unknown_snapshot' else 'snapshot',
            va=lambda f:f in ('a','b'),zbn=lambda f,ctx:'oa' if name=='wrong_origin' and (f,ctx)==('b','snapshot') else 'o'+f,zbo=axis,
            zbv=lambda f,o,ctx:ctx=='snapshot' and o=='o'+f,
            zbw=lambda f,line,role,ctx:ctx=='snapshot' and axes.get((f,role))==line and name!='missing_assignment',
            zbp=lambda line:line in axes.values() and not(name=='not_material' and line=='bz'),
            zbq=lambda line,ctx:ctx=='snapshot' and line in axes.values() and name!='not_rigid',
            zbr=lambda line,o,ctx:ctx=='snapshot' and line in axes.values() and o=='o'+line[0],
            zbs=lambda a,b,ctx:ctx=='snapshot' and a in axes.values() and b in axes.values() and a[0]==b[0] and a[1]!=b[1] and name!='not_perpendicular',
            zbt=lambda a,b,ctx:ctx=='snapshot' and (a,b) in (('ax','bx'),('ay','by'),('az','bz')) and name!=a[1]+'_not_parallel')
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('Parallel configuration differs: '+name)
        rows[name]=actual
    return rows


def snapshot_coordinate_checks():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] h[h[b] c] c.r je[] h[h[b] c h[b] c] c.
q[k sfv[k ja[] k jb[] k jc[] k jd[] k je[]]].''')
    axes={'xrole':'xaxis','yrole':'yaxis','zrole':'zaxis'}
    points={'origin':0,'px':3,'py':6,'pz':9,'clockpoint':12}
    placed={('px','xaxis'),('py','yaxis'),('pz','zaxis'),('clockpoint','clock')}
    names=('baseline','missing_history_coordinate','missing_snapshot_coordinate','changed_origin_x',
        'changed_x_axis_y','changed_y_axis_z','changed_z_axis_x','invalid_snapshot_value',
        'wrong_reference_frame','wrong_length_unit','wrong_moment','clock_only_difference')
    rows={}
    for name in names:
        model=guarded(doc)
        const={'ja':'history','jb':'other' if name=='wrong_moment' else 'moment','jc':'pose',
            'zbm':'moving','ra':'other' if name=='wrong_reference_frame' else 'rest',
            'ta':'other' if name=='wrong_length_unit' else 'unit','zb4':'initial','yn':'xrole','yo':'yrole','yp':'zrole'}
        for key,val in const.items():model[key]=lambda val=val:val
        def coordinate(p,m,f,u,axis,ctx):
            value=points.get(p,0)+{'xrole':0,'yrole':1,'zrole':2}.get(axis,0)
            changed={'changed_origin_x':('origin','xrole'),'changed_x_axis_y':('px','yrole'),
                'changed_y_axis_z':('py','zrole'),'changed_z_axis_x':('pz','xrole'),
                'clock_only_difference':('clockpoint','xrole')}
            if ctx=='snapshot' and (p,axis)==changed.get(name):value+=1
            if ctx=='snapshot' and name=='invalid_snapshot_value' and (p,axis)==('origin','xrole'):value=33
            return cut(value)
        model.update(zci=lambda h:'motion',zcl=lambda p:'snapshot',zcn=lambda p:p=='pose',
            zbn=lambda f,ctx:'origin',zbo=lambda f,role,ctx:axes.get(role,'other'),
            zcc=lambda p,obj,ctx:ctx=='motion' and (p,obj) in placed,
            zce=lambda p,m,f,u,ctx:p in points and (m,f,u)==('moment','rest','unit') and ctx in ('motion','snapshot') and not(
                name=='missing_history_coordinate' and ctx=='motion' and p=='pz' or
                name=='missing_snapshot_coordinate' and ctx=='snapshot' and p=='pz'),ym=coordinate)
        callbacks(doc,model,{'jd':lambda value:embedding(value)!=33,'je':lambda a,b:embedding(a)==embedding(b)})
        domain=('history','moment','pose','moving','rest','unit',*axes,*axes.values(),*points,'clock','other')
        actual=values(doc,model,domain)[0]
        if actual!=(name in ('baseline','clock_only_difference')):raise ValueError('Snapshot coordinates differ: '+name)
        rows[name]=actual
    return {'cases':rows,'full_real_coordinate_equality_evaluated':False,'integer_embedding_oracles':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-3:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_definite_content','wrong_choice',
        'wrong_existence','wrong_prior_motion','wrong_symmetry','wrong_assumption_target'):
        model=guarded(doc)
        const={'zco':'positionnode','zcp':'choicenode','zcq':'reasonnode','zcg':'motionnode','rd':'author','rh':'scope','ri':'text'}
        for key,val in const.items():model[key]=lambda val=val:val
        symbol=lambda desc:json.loads(desc.syntax)['symbol']
        def common(author,scope,ctx):return (author,scope,ctx)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model['uh']=lambda node,author,desc,scope,ctx:common(author,scope,ctx) and (node,symbol(desc)) in (
            ('positionnode','sgc' if name=='wrong_definite_content' else 'sgb'),('choicenode','sgd' if name=='wrong_existence' else 'sgc'))
        model['ug']=lambda node,author,desc,scope,ctx:common(author,scope,ctx) and (node,symbol(desc))==('choicenode','sgc' if name=='wrong_choice' else 'sgd')
        model['zao']=lambda a,b,scope,ctx:(a,b,scope,ctx)==('other' if name=='wrong_prior_motion' else 'motionnode','choicenode','scope','text')
        model['zct']=lambda node,author,desc,target,scope,ctx:common(author,scope,ctx) and (node,symbol(desc),target)==('reasonnode','sgc' if name=='wrong_symmetry' else 'sge','other' if name=='wrong_assumption_target' else 'choicenode')
        actual=values(doc,model,tuple(const.values())+('other',))
        common_bad={'wrong_author','wrong_scope','wrong_context'}
        expected=[name not in common_bad|{'wrong_definite_content'},name not in common_bad|{'wrong_choice','wrong_existence','wrong_prior_motion'},name not in common_bad|{'wrong_symmetry','wrong_assumption_target'}]
        if actual!=expected:raise ValueError('Symmetry rationale attribution differs: '+name)
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0044')
    digest='ac47cdbc668ed13b37de8f87f8e35303185a24899f06aa94af78d1768b8a5ae5'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Parallel history source changed')
    start=unit['text'].index('Jeder Zeit')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':start,'end':len(unit['text']),'source':unit['text'][start:],
        'definitions':['sft','sfu','sfw','sgb','sgc','sgd','sge'],'status':'partial_explicit_reading','full_semantic_equivalence':False}],
        'verified_full_units':0,'facsimile_checked':False,'specific_source_symmetry_transformation_not_identified':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored parallel history differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Parallel history roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/parallel-histories-basis-v1.json','data/einstein-parallel-histories-basis-v1.json',
        'examples/v014/einstein-frame-translation.noema','scripts/compose_parallel_histories.py','scripts/check_parallel_histories.py',
        'noema/discourse.py','noema/finite_semantics.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-frame-translation.noema').read_text(encoding='utf-8')
    return {'status':'partial_parallel_history_choice_and_symmetry_rationale','documents':documents,
        'histories':history_checks(),'source_histories':history_checks(True),'uniqueness':uniqueness_checks(),
        'symmetry':symmetry_checks(),'time_binding':time_binding_checks(),'configurations':configuration_checks(),
        'snapshot_coordinates':snapshot_coordinate_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Parallel history report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Global history choice, unique poses, time bindings and symmetry limits checked')


if __name__=='__main__':main()
