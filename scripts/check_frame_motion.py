"""Check complete translation bindings and exact carried-object populations."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_material_relative_frame import RS,FS
from scripts.check_material_axes import setup as history_setup,DOMAIN as HISTORY_DOMAIN
from scripts.check_rod_methods import value,relation
from scripts.compose_frame_motion import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/frame-motion-v1.md';SOURCE='data/einstein-frame-motion-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-frame-instruments-review-v1.json'
DEPENDENCIES=('reports/frame-instruments-v1.json','reports/material-axes-v1.json','reports/rod-geometry-v1.json','reports/moving-trip-geometry-v1.json','reports/first-principle-v1.json')
DOMAIN=HISTORY_DOMAIN+('ruler','clocka','clockb','clockc')
POINTS=('context','initial','other')

def forbidden(*xs):raise ValueError('Unknown frame-motion input')
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','zbm':'moving','zb4':'initial','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eipf','eigy','eioj'}
    if mode!='native_history':boundaries.add('se')
    if name=='eivw':boundaries.add('eivu')
    if name=='eivy':boundaries|={'eivx','eivv','eivw'}
    if name=='eivz':boundaries.add('eivy')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jfm'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown frame-motion' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                changed=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def representative_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.parameters==(RS,):return tuple(r(x(c(Q(t)))) for t in (0,1,2))
            forbidden()
        return tuple(one(x) for x in xs)
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2))]
    metric={('frame','lengthunit','timeunit','context')}
    for origin in ((3,-5,7),(0,0,0),(Q(-1,2),4,Q(7,3))):
        for speed in (Q(-2),Q(0),Q(1,2),Q(5)):
            fs=[FunctionValue((RS,),RS,lambda t,a=a:c(origin[a]+(speed*r(t) if a==0 else 0))) for a in range(3)]
            expected=norm(fields+fs)
            mm=m|{'eisdd':relation(metric),'se':lambda *xs:norm(xs)==expected}
            args=fields+fs+[c(speed)]
            assert run('eivu',args,mm)==(speed>0);count+=1
            if speed<=0:continue
            for axis in range(3):
                wrong=list(fs);wrong[axis]=FunctionValue((RS,),RS,lambda t,a=axis:c(r(fs[a](t))+r(t)*(2-r(t))))
                # Endpoints agree, but the intermediate coordinate disagrees.
                assert not run('eivu',fields+wrong+[c(speed)],mm);count+=1
            assert not run('eivu',fields+fs+[c(speed+1)],mm);count+=1
            count+=perturb(lambda mm:run('eivu',args,mm),mm,{'se':{expected},'eisdd':metric},norm)
    # Invalid intervals and unknown cuts are not quietly decoded or sampled.
    for lo,hi in ((2,2),(3,2)):
        bad=list(args);bad[5:7]=[c(Q(lo)),c(Q(hi))]
        assert not run('eivu',bad,mm|{'se':lambda *xs:True});count+=1
    unknowns(lambda mx:run('eivu',args,mx),mm,('se','eisdd','ba','bf','bd','shv','bg'))
    bad=list(args);bad[-1]=FunctionValue(('number',),'truth',lambda n:n<1)
    try:run('eivu',bad,mm)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded by sampling')
    try:run('eivu',args,mm|{'zzbg':lambda a,b:r(a)<r(b)},'native_history')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete representative history silently sampled')
    return dict(cases=count,native_linear_paths_at_arbitrary_positions=True,positive_x_only_and_mid_interval_deviation_checked=True,complete_real_history_refused=True,finite_boundary_samples_not_global_proof=True)

@lru_cache(None)
def history_checks():
    cuts,m,fs,norm=history_setup();c=cuts.make
    members=FunctionValue(('individual',),'truth',lambda p:p in ('guide','point','hidden'))
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*fs]
    rows={'eipf':{norm(fields+[c(Q(3))])},'eigy':{norm(fields)}}
    m|={'zb7':lambda:c(Q(3))}|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count=perturb(lambda mm:run('eivv',['body','context'],mm,domain=HISTORY_DOMAIN),m,rows,norm)
    unknowns(lambda mm:run('eivv',['body','context'],mm,domain=HISTORY_DOMAIN),m,('zb7','eislu','eirh','eisls','eislt'))
    traces=[f('body') for f in fs]
    representative=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*traces,c(Q(3))]
    rows={'eivu':{norm(representative)}}
    def select(obj,frame,lu,tu,axis,ctx):
        if (obj,frame,lu,tu,ctx)!=('body','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return traces[('x','y','z').index(axis)]
    m|={'eismh':select,'eivu':lambda *xs:norm(xs)==norm(representative)}
    count+=perturb(lambda mm:run('eivw',['body','context'],mm,domain=HISTORY_DOMAIN),m,rows,norm)
    unknowns(lambda mm:run('eivw',['body','context'],mm,domain=HISTORY_DOMAIN),m,('zb7','eismh','eisls','eislt'))
    return dict(cases=count,all_material_members_and_representative_positions_kept_separate=True,same_speed_units_context_and_interval_bound=True)

def frame_setup():
    lines={'x':'body','y':'second','z':'hidden'};clocks=('clocka','clockb');origin='origin'
    rows={'zca':{('moving','initial','context')},'zbv':{('moving',origin,'context')},'zcb':{(x,'initial','context') for x in (origin,*lines.values(),'ruler',*clocks)},'zbx':{('moving','ruler','context')},'zbw':{('moving',line,axis,'context') for axis,line in lines.items()},'zbr':{(line,origin,'context') for line in lines.values()}}
    given={('moving',clock,ctx) for clock in clocks for ctx in ('initial','context')}
    def selector(f,ctx):
        if f!='moving' or ctx not in ('initial','context'):forbidden()
        return origin
    def axis(f,a,ctx):
        if f!='moving' or a not in lines or ctx not in ('initial','context'):forbidden()
        return lines[a]
    m={n:relation(rs) for n,rs in rows.items()}|{'zbn':selector,'zbo':axis,'zby':lambda f,ctx:'ruler' if f=='moving' and ctx in ('initial','context') else forbidden(),'zbz':relation(given)}
    return m,rows,given,lines

@lru_cache(None)
def identity_checks():
    m,rows,given,lines=frame_setup();check=lambda mm:run('eivx',['context'],mm)
    count=perturb(check,m,rows)
    for removed in sorted(given):
        assert not check(m|{'zbz':relation(given-{removed})});count+=1
    for extra in (('moving','clockc','context'),('moving','clockc','initial')):
        assert not check(m|{'zbz':relation(given|{extra})});count+=1
    assert not check(m|{'zbz':lambda *xs:False});count+=1
    for n,extra in (('zbw',('moving','guide','x','context')),('zbw',('moving','body','other','context')),('zbv',('moving','otherorigin','context'))):
        assert not check(m|{n:relation(rows[n]|{extra})});count+=1
    for n in ('zbn','zby'):
        base=m[n];assert not check(m|{n:lambda f,ctx,base=base:'other' if ctx=='context' else base(f,ctx)});count+=1
    for a in lines:
        base=m['zbo'];assert not check(m|{'zbo':lambda f,r,ctx,a=a:'other' if r==a and ctx=='context' else base(f,r,ctx)});count+=1
    # More clocks are permitted when both populations and their identities agree.
    extra={('moving','clockc',ctx) for ctx in ('initial','context')}
    assert check(m|{'zbz':relation(given|extra),'zcb':relation(rows['zcb']|{('clockc','initial','context')})});count+=1
    assert not check(m|{'zbo':lambda *xs:'body','zbw':relation({('moving','body',a,'context') for a in lines})});count+=1
    unknowns(check,m,('zbn','zbo','zby','zbz'))
    return dict(cases=count,native_identity_transfer_and_exact_axis_roles=True,clock_additions_and_losses_detected=True,unique_origin_and_all_three_distinct_axes=True)

@lru_cache(None)
def population_checks():
    m,_,given,lines=frame_setup()
    rows={'eivx':{('context',)},'eivv':{(b,'context') for b in (*lines.values(),'ruler')},'eivw':{(x,'context') for x in ('origin','clocka','clockb')},'ca':{(x,) for x in ('clocka','clockb')},'xc':{('ruler',)},'eisdf':{(x,'context') for x in ('clocka','clockb')}}
    m|={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('eivy',['context'],mm)
    count=perturb(check,m,rows)
    more=given|{('moving','clockc','context')}
    assert not check(m|{'zbz':relation(more)});count+=1
    qualified=m|{'zbz':relation(more),'ca':relation(rows['ca']|{('clockc',)}),'eisdf':relation(rows['eisdf']|{('clockc','context')})}
    assert not check(qualified);count+=1
    assert check(qualified|{'eivw':relation(rows['eivw']|{('clockc','context')})});count+=1
    # A clock's whole material body need not satisfy the rigid translation test.
    assert check(m|{'eivv':relation(rows['eivv']),'eivw':relation(rows['eivw'])});count+=1
    unknowns(check,m,('zbn','zbo','zby','zbz'))
    return dict(cases=count,every_axis_ruler_origin_and_clock_connected=True,clock_internal_parts_not_sent_to_material_motion=True,extra_clock_requires_its_own_full_placement=True)

@lru_cache(None)
def frame_checks():
    cuts,m=numbers();c=cuts.make;rows={'eivy':{('context',)},'eioj':{('frame','moving','lengthunit','timeunit','context')}}
    def velocity(first,second,lu,tu,axis,ctx):
        if (first,second,lu,tu,ctx)!=('frame','moving','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return c(Q(2 if axis=='x' else 0))
    m|={n:relation(rs) for n,rs in rows.items()}
    m|={'zb7':lambda:c(Q(2)),'eislc':velocity,'zbi':lambda *xs:c(Q(2))}
    check=lambda mm:run('eivz',['context'],mm);count=perturb(check,m,rows)
    for a in ('x','y','z'):
        assert not check(m|{'eislc':lambda *xs,a=a:c(Q(7)) if xs[4]==a else velocity(*xs)});count+=1
    for speed in (-2,0,3):
        assert not check(m|{'zb7':lambda speed=speed:c(Q(speed))});count+=1
    assert not check(m|{'zbi':lambda *xs:c(Q(3))});count+=1
    unknowns(check,m,('zb7','eislc','zbi','ba','sca'))
    return dict(cases=count,same_complete_frame_motion_and_three_speed_components=True,old_rod_speed_not_used=True)

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][43];assert u['id']=='einstein-1905:u0044' and len(u['text'])==687
    first=u['text'].split(' Jeder Zeit ')[0];assert first.endswith('mitteilen möge.')
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};forms=dict(zip(('M0066','M0067','M0068','M0069'),('k','v','x','K')))
    for n,s in forms.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-frame-motion-source-reading-v1',reviewer='assistant_visual_and_text_review',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(first)],text=first,source_nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',first)),pages=['897'],math=[dict(id=n,sha256=math[n]['sha256'],printed=s) for n,s in forms.items()],observations=['原点に与える一定速度は静止系Kの増加するx方向である。','同じ速度を座標軸・該当する物差し・時計にも共有させる。時計の内部運動停止や同期を述べていない。','Es werde ... erteiltとmitteilen mögeは設定の指示であり、物理的な実行済みの報告へ替えない。'],semantic_completion=False,remaining=['設定指示、同じk/K/v/xの導入・参照と著者帰属','全静止系時刻における軸配置の存在・一意性と実座標の対応','一つの運動で全時刻に平行となるという仮定と対称性による許容','括弧内のtの呼称とu0044全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==268
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[267])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/frame-instruments-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=268,prior_meanings_and_reviews_preserved=True,no_new_author_assertion=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('representative',representative_checks),('history',history_checks),('identity',identity_checks),('populations',population_checks),('frame',frame_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,PRIOR,*DEPENDENCIES,'scripts/compose_frame_motion.py','scripts/check_frame_motion.py','tests/test_frame_motion.py','scripts/check_material_axes.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_frame_instruments.py','scripts/compose_rod_methods.py','scripts/compose_moving_trip_geometry.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='complete_frame_translation_dependency_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
