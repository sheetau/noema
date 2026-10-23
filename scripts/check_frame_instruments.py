"""Check exact specifications, all instruments and non-factive setting directives."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
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
from scripts.compose_frame_instruments import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build
from scripts.review_frame_instruments import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

DOMAIN=HISTORY_DOMAIN+('author','paper','section','node','heading','designation')
POINTS=('context','discourse','other');SMALL=('a','b')
def forbidden(*xs):raise ValueError('Unknown frame-instruments input')
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','zbm':'moving','zb4':'context','zb5':'node','eismt':'heading','eiseb':'designation','eisms':'section','eirf':'paper','rd':'author','ri':'discourse'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eipw','eigy','eivf','eivg'}
    if mode!='native_history':boundaries.add('eit2')
    if name=='eivl':boundaries|={'eivi','eild','eivj','eivk'}
    if name=='eivq':boundaries.add('eivl')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jfi'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jficontent',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jficontent',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jficontent',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown frame-instruments' in str(e),str(e)
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
def exact_checks():
    slots=list(product(SMALL,repeat=3));count=0
    base={'xc':lambda x:x in SMALL,'eismw':relation({('a','b','a','a','context')}),'eismx':relation({('a',f,'a','context') for f in SMALL})}
    for bits in product((False,True),repeat=8):
        rows={(r,f,'a',v,'a','context') for (r,f,v),on in zip(slots,bits) if on}
        sets=lambda r,f:{v for rr,ff,v in slots if rr==r and ff==f and (rr,ff,'a',v,'a','context') in rows}
        expected=all(bool(sets('a',f)) and sets('a',f)==sets('b',f) for f in SMALL)
        assert run('eivi',['a','b','a','context'],base|{'eismy':relation(rows)},domain=SMALL)==expected;count+=1
    rows={'xc':{('a',),('b',)},'eismw':{('a','b','a','a','context')},'eismx':{('a',f,'a','context') for f in SMALL},'eismy':{(r,f,'a','a','a','context') for r,f in product(SMALL,repeat=2)}}
    m={n:relation(rs) for n,rs in rows.items()}
    # A changed feature scope is a different specification, not by itself a
    # mismatch. Its completeness is required separately by eismw.
    count+=perturb(lambda mm:run('eivi',['a','b','a','context'],mm,domain=SMALL),m,{n:rows[n] for n in ('xc','eismw','eismy')})
    assert not run('eivi',['a','b','a','context'],m|{'eismx':lambda *xs:False},domain=SMALL);count+=1
    unknowns(lambda mm:run('eivi',['a','b','a','context'],mm,domain=SMALL),m,('eismx',))
    return dict(cases=count,nonempty_complete_features_and_bidirectional_description_match=True,extra_missing_and_unknown_characteristics_rejected=True)

@lru_cache(None)
def calibration_checks():
    cuts,m,fs,norm=history_setup();c=cuts.make;r=cuts.read
    origin=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*(f('body') for f in fs)]
    rows={'ca':{('body',)},'ci':{('timeunit',)},'eisdf':{('body','context')},'cc':{('body','frame')},'eit2':{norm(origin)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def position(body,frame,lu,tu,axis,ctx):
        if (body,frame,lu,tu,ctx)!=('body','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(axis)]('body')
    m['eismh']=position
    count=perturb(lambda mm:run('eivj',['body','context'],mm,domain=HISTORY_DOMAIN),m,rows,norm)
    unknowns(lambda mm:run('eivj',['body','context'],mm,domain=HISTORY_DOMAIN),m,('eismh','eisls','eislt'))
    try:run('eivj',['body','context'],m|{'eisdd':lambda *xs:True,'zzbg':lambda a,b:r(a)<r(b)},'native_history',HISTORY_DOMAIN)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Representative complete history silently sampled')
    members=FunctionValue(('individual',),'truth',lambda p:p in ('guide','point','hidden'))
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*fs]
    calibration=['body','point','frame','lengthunit','timeunit',c(Q(0)),c(Q(2)),'context']
    rows={'xc':{('body',)},'ti':{('lengthunit',)},'eipw':{('body','frame','context')},'eigy':{norm(fields)},'eisef':{norm(calibration)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eivk',['body','context'],mm,domain=HISTORY_DOMAIN),m,rows,norm)
    alternative=list(calibration);alternative[1]='hidden'
    assert run('eivk',['body','context'],m|{'eisef':lambda *xs:norm(xs)==norm(alternative)},domain=HISTORY_DOMAIN);count+=1
    unknowns(lambda mm:run('eivk',['body','context'],mm,domain=HISTORY_DOMAIN),m,('eislu','eisls','eislt'))
    return dict(cases=count,clock_representative_static_without_freezing_internal_parts=True,ruler_complete_static_rigidity_and_calibrated_scale=True,calibration_method_exists_without_measurement_execution=True,real_history_refused=True)

@lru_cache(None)
def population_checks():
    domain=('a','b','c');cuts,m=numbers();c=cuts.make
    track=FunctionValue((RS,),RS,lambda t:c(Q(0)))
    family=FunctionValue(('individual',),FS,lambda p:track if p in domain else forbidden())
    given={('a','a','context'),('a','b','context'),('b','c','context')}
    rows={'xc':{('a',),('b',)},'ca':{(x,) for x in domain},'zbx':{('a','a','context'),('b','b','context')},'eivi':{('a','b','a','context')},'eild':{(a,b,'a','context') for a,b in product(domain,repeat=2)},'eivk':{('a','context'),('b','context')},'eivj':{(a,'context') for a in domain}}
    m|={n:relation(rs) for n,rs in rows.items()}
    m|={'ra':lambda:'a','ta':lambda:'a','rb':lambda:'b','yn':lambda:'a','yo':lambda:'b','yp':lambda:'c','eirf':lambda:'a','zby':lambda f,ctx:f,'zbz':relation(given),'eirh':lambda *xs:True,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eislu':lambda *xs:family,'eigy':lambda *xs:xs[0] in ('a','b') and xs[1:5]==('a','context','a','b')}
    check=lambda mm:run('eivl',['a','b','context'],mm,domain=domain)
    count=perturb(check,m,rows)
    for empty in ('a','b'):
        assert not check(m|{'zbz':relation({row for row in given if row[0]!=empty})});count+=1
    assert not check(m|{'eigy':lambda *xs:False});count+=1
    assert not check(m|{'zby':lambda *xs:'a'});count+=1
    assert not run('eivl',['a','a','context'],m,domain=domain);count+=1
    # The shared same-specification relation checks every pair, including two
    # clocks in the same group; no reference-clock-only shortcut is used.
    assert not check(m|{'eild':relation(rows['eild']-{('a','b','a','context')})});count+=1
    unknowns(check,m,('zbz','zby','eigy'))
    return dict(cases=count,two_nonempty_groups_and_every_clock_pair=True,same_group_mismatch_not_hidden=True,both_rulers_and_all_clock_qualifications_bound=True)

@lru_cache(None)
def setting_checks():
    rows={'va':{('frame',),('moving',)},'eivf':{('frame','context'),('moving','context')},'eivg':{('frame','moving','context')},'eivl':{('frame','moving','context')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eivq',[],mm),m,rows)
    assert not run('eivq',[],{n:lambda *xs:True for n in rows}|{'zbm':lambda:'frame'});count+=1
    rows={'eisd3':{('node','moving','paper','discourse')},'eismz':{('node','designation','frame','paper','discourse')},'eism2':{('node','author','eivm','eivn','paper','discourse')},'ug':{('node','author','eivq','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eivr',[],mm),m,rows)
    assert run('eivr',[],m|{n:forbidden for n in ('eivq','eivf','eivg','eivl','eivi','eild','se')});count+=1
    rows={'eir3':{('node','author','paper','eivs','discourse')},'ue':{('heading','node','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eivt',[],mm),m,rows)
    assert run('eivt',[],m|{n:forbidden for n in ('ug','eismz','eism2','eisd3','eivq')});count+=1
    return dict(cases=count,three_sentence_conditions_same_initial_context=True,quoted_rest_frame_reference_and_explanatory_reformulation=True,assumption_adoption_and_author_attribution_do_not_execute_physics=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==268
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIORS[0]));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[266])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/material-axes-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert len(doc['statements'])==1
    assert ds['eivs']['body']['force']=='direct' and ds['eivs']['body']['content']['symbol']=='eivr'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=267,prior_meanings_and_reviews_preserved=True,setting_directive_not_truth_assertion=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('exact_specifications',exact_checks),('calibration',calibration_checks),('populations',population_checks),('setting',setting_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_frame_instruments.py','scripts/check_frame_instruments.py','scripts/review_frame_instruments.py','tests/test_frame_instruments.py','scripts/check_material_axes.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_axes.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='initial_frames_and_exact_instruments_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0043の全単位判断登録','u0044以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
