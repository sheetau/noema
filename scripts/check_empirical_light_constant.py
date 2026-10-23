"""Check native rate bindings, complete trial scope and empirical adoption."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM
from scripts.check_synchrony_laws import native_model,DOMAIN as PRIOR_DOMAIN
from scripts.compose_empirical_light_constant import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_empirical_light_constant import SOURCE,INVENTORY,DOC,READING,PRIORS,source_record

POINTS=('now','other');DOMAIN=PRIOR_DOMAIN+('length','speedunit','law','experience','definition')


def forbidden(*args):raise ValueError('Unknown empirical-light-constant input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple('other' if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode!='full_real':abstract(doc,NUM|{'bg','sah'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jelc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jelccontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jelccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)


def run(name,args,m,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jelccontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})[0]['value']


def reject_unknown(name,args,m,symbols):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden})
        except ValueError as e:assert 'Unknown empirical-light-constant' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


def setup(second_end=14,first_middle=2):
    cuts,m,rows=native_model();r=cuts.read;c=cuts.make
    names={'ta':'length','tb':'speedunit','tm':'law','tn':'experience','rj':'definition'}
    m|={n:(lambda x=x:x) for n,x in names.items()}|{'tc':lambda:c(Q(3)),'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b))}
    rows|={'td':{(t,'frame','unit','length','now') for t in ('trial','trial2')},'eiskr':{(t,'frame','unit','length','paper','now') for t in ('trial','trial2')},'tl':{('frame','unit','length','now')},'ti':{('length',)},'tj':{('length','unit','speedunit')},'tk':set(rows['cg'])}
    m|={n:relation(rs) for n,rs in rows.items()}
    m|={'te':lambda t:'clockb' if t=='trial2' else 'clocka','tf':lambda t:'clocka' if t=='trial2' else 'clockb','tg':lambda t:c(Q(6)),'th':lambda a,b,f,u,d:(a,b) in {('placea','placeb'),('placeb','placea')} and (f,u)==('frame','length') and r(d)==6}
    oldqj,oldqk,oldce=m['qj'],m['qk'],m['ce']
    m['qj']=lambda t:c(Q(first_middle)) if t=='trial' else oldqj(t)
    m['qk']=lambda t:c(Q(second_end)) if t=='trial2' else oldqk(t)
    def reading(clock,event,frame,unit,x):
        if (clock,event)==('clockb','a2'):return (frame,unit)==('frame','unit') and r(x)==second_end
        if (clock,event)==('clockb','reflect'):return (frame,unit)==('frame','unit') and r(x)==first_middle
        return oldce(clock,event,frame,unit,x)
    m['ce']=reading
    return cuts,m,rows


@lru_cache(None)
def numeric_checks():
    cuts,m,_=setup();count=0
    for d,a,b,s in product((Q(0),Q(3),Q(6)),(Q(-2),Q(0)),(Q(0),Q(2),Q(4)),(Q(0),Q(3,2),Q(3))):
        expected=d>0 and b>a and s>0 and s*(b-a)==2*d
        assert run('sai',[cuts.make(x) for x in (d,a,b,s)],m)==expected
        if d>0 and b>a and s>0:assert expected==(s==2*d/(b-a))
        count+=1
    for a,b in ((0,4),(10,14),(-10,-6)):
        assert run('sai',[cuts.make(Q(x)) for x in (6,a,b,3)],m);count+=1
    # A fixed positive distance and duration have one rate in the tested candidates.
    hits=[s for s in (Q(3,2),Q(2),Q(3),Q(4)) if run('sai',[cuts.make(x) for x in (Q(6),Q(0),Q(4),s)],m)]
    assert hits==[Q(3)];count+=4
    reject_unknown('sai',[cuts.make(Q(x)) for x in (6,0,4,3)],m,('ba','bg','bf','bd','sah','bc'))
    try:run('sai',[cuts.make(Q(x)) for x in (6,0,4,3)],m,'full_real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real domain silently sampled')
    return dict(cases=count,positive_product_equation_matches_displayed_quotient=True,common_origin_shifts_preserve_rate=True,constructed_rational_cuts_not_sampled_predicates=True,full_real_domain_not_sampled=True)


@lru_cache(None)
def physical_checks():
    cuts,m,rows=setup();count=0
    for name in ('eins','einr','einv'):
        assert run(name,[],m);count+=1
    for symbol in ('ca','cb','cc','cd','ci','cf','cg','ch','ce','th','ti','tj','tk'):
        assert not run('eins',[],m|{symbol:lambda *xs:False});count+=1
    for row in (('ray','depart','reflect','frame'),('ray','reflect','arrive','frame')):
        assert not run('eins',[],m|{'tk':relation(rows['tk']-{row})});count+=1
    # Return time must be read on A, not on the reflection-side B clock.
    original=m['ce']
    assert not run('eins',[],m|{'ce':lambda clock,event,f,u,x:False if (clock,event)==('clocka','arrive') else original(clock,event,f,u,x)});count+=1
    _,offset,_=setup(first_middle=99)
    assert run('eins',[],offset|{'bi':forbidden,'db':forbidden,'qo':forbidden});count+=1
    assert run('einr',[],offset|{'bi':forbidden,'db':forbidden,'qo':forbidden});count+=1
    for symbol in ('ra','rb','ta','tb'):
        assert not run('eins',[],m|{symbol:lambda:'other'});count+=1
    reject_unknown('eins',[],m,('ca','cb','cc','cd','ce','cg','ch','th','ti','tj','tk','tg'))
    return dict(cases=count,native_sal_da_and_sai_bound_to_same_trial=True,both_vacuum_legs_and_compatible_units_required=True,reflection_clock_offset_does_not_change_roundtrip_rate=True,synchrony_equality_not_added=True)


@lru_cache(None)
def printed_binding_checks():
    cuts,m,rows=setup();count=0
    for symbol in ('te','tf','qc','qd','qe','qf','qg','qh'):
        original=m[symbol]
        assert not run('eins',[],m|{symbol:lambda t:'other'});count+=1
    for symbol in ('qi','qk','tg'):
        assert not run('eins',[],m|{symbol:lambda t:cuts.make(Q(99))});count+=1
    for symbol in ('eisjo','eisjq','tc'):
        assert not run('eins',[],m|{symbol:lambda:cuts.make(Q(99))});count+=1
    for symbol in ('eisib','eisik','ziq','zir','eisjk','eisjl','eisjm','eisjn','eisjj'):
        assert not run('eins',[],m|{symbol:lambda:'other'});count+=1
    assert not run('eins',[],m|{'td':relation(set())});count+=1
    reject_unknown('eins',[],m,('te','tf','qc','qd','qe','qf','qg','qh','qi','qk','eisjo','eisjq','tc'))
    return dict(cases=count,named_A_B_departure_return_and_same_V_checked=True,distance_is_one_way_and_denominator_is_A_return_minus_departure=True)


@lru_cache(None)
def scope_checks():
    cuts,m,rows=setup();count=0
    for selected,eligible in product(product((False,True),repeat=2),repeat=2):
        td={r for r in rows['td'] if selected[0 if r[0]=='trial' else 1]};scope={r for r in rows['eiskr'] if eligible[0 if r[0]=='trial' else 1]}
        assert run('einr',[],m|{'td':relation(td),'eiskr':relation(scope)})==(selected==eligible and any(selected));count+=1
    assert not run('einr',[],m|{'tl':relation(set())});count+=1
    for row in rows['eiskr']:
        for i in range(len(row)):
            assert not run('einr',[],m|{'eiskr':relation((rows['eiskr']-{row})|{changed(row,i)})});count+=1
    cuts,bad,badrows=setup(second_end=15)
    assert not run('einr',[],bad);count+=1
    assert run('einv',[],bad);count+=1
    # Each trial has a rate; neither candidate is the one common rate for both.
    for speed in (Q(3),Q(12,5)):
        assert not run('einr',[],bad|{'tc':lambda s=speed:cuts.make(s)});count+=1
    only={r for r in badrows['td'] if r[0]=='trial'}
    assert run('san',[cuts.make(Q(3)),'now'],bad|{'td':relation(only)});count+=1
    assert not run('einr',[],bad|{'td':relation(only)});count+=1
    # Evaluate both individual trial bodies with their own valid rates.
    doc=extract_document(parse(read(CORE)),roots=['sal','sai','ra','rb','ta','tb','ri'],statement_indices=[]).document;abstract(doc,NUM|{'bg','sah'})
    for trial,speed in (('trial',Q(3)),('trial2',Q(12,5))):
        query='r jelctrial[] a.r jelcrate[] h[b] c.q[k sal[k jelctrial[] k ra[] k rb[] k ta[] k tb[] k jelcrate[] k ri[] p sai]].'
        test=parse(format_graph(doc,'compact')+query)
        assert evaluate(test,bad|{'jelctrial':lambda t=trial:t,'jelcrate':lambda s=speed:cuts.make(s)})[0]['value'];count+=1
    reject_unknown('einr',[],m,('eiskr','td','tl','tg','qk'))
    return dict(cases=count,complete_nonempty_applicable_scope_not_observed_successes=True,per_trial_rates_do_not_make_one_universal_constant=True,physical_kind_does_not_by_itself_assert_constancy=True)


def presentation_model():
    _,m,_=setup();rows={'ug':{('law','author','einr','paper','now')},'to':{('law','author','experience','paper','now')},'eir3':{('law','author','paper','einu','now')},'eisjt':{('law','author','einr','eins','paper','now')},'eisa5':{('law','author','einr','einv','now')},'eisb2':{('law','author','eini','eint','paper','now')},'ue':{('definition','law','now')}}
    return m|{n:relation(rs) for n,rs in rows.items()},rows


@lru_cache(None)
def presentation_checks():
    m,rows=presentation_model();count=0
    assert run('eint',[],m);count+=1
    for symbol in ('ug','to'):
        row=next(iter(rows[symbol]))
        for i in range(len(row)):
            assert not run('eint',[],m|{symbol:relation({changed(row,i)})});count+=1
    physics={n:forbidden for n in ('tc','td','tl','eiskr','th','tk','ce','ba')}
    assert run('eint',[],m|physics);count+=1
    reject_unknown('eint',[],m,('ug','to'))
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        assert evaluate(doc,m)[0]['value'];count+=1
        for symbol in ('eir3','eisjt','eisa5','eisb2','ue'):
            row=next(iter(rows[symbol]))
            for i in range(len(row)):
                assert not evaluate(doc,m|{symbol:relation({changed(row,i)})})[0]['value'];count+=1
        assert evaluate(doc,m|physics|{'ug':forbidden,'to':forbidden})[0]['value'];count+=1
    return dict(cases=count,empirical_adoption_not_execution_of_law=True,one_sentence_formula_parenthesis_addition_and_order_preserved=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==246
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in zip(PRIORS,([243,244],list(range(234,240)))):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,indices)
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert [s['nonblank_characters'] for s in source['segments']]==[46,0,66]
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=245,previous_clock_and_event_time_judgments_preserved=True,three_units_one_112_character_sentence_and_formula_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_empirical_light_constant import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('numeric',numeric_checks),('physical',physical_checks),('printed_bindings',printed_binding_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]};segments=[]
    for s in source_record()['segments']:
        segments.append(dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
        segments.extend(dict(unit=s['unit'],unit_sha256=s['unit_sha256'],math_id=m['id'],math_sha256=m['sha256'],definitions=['sai','sal','eins'],status='explicit_interpretive_annotation') for m in s['math'])
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS,'scripts/compose_empirical_light_constant.py','scripts/check_empirical_light_constant.py','scripts/review_empirical_light_constant.py','tests/test_empirical_light_constant.py','scripts/check_synchrony_laws.py','scripts/check_light_roundtrip_definition.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='empirical_universal_vacuum_light_constant_and_printed_roundtrip_rate_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['一文を構成する三原文単位の判断登録、u0022以降'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
