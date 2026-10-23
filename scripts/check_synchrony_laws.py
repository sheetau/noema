"""Check directed clock roles, conditional laws and numbered presentations."""
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
from scripts.check_light_roundtrip_definition import setup as prior_setup,DOMAIN as PRIOR_DOMAIN
from scripts.compose_synchrony_laws import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_synchrony_laws import SOURCE,INVENTORY,DOC,READING,PRIOR,source_record

POINTS=('now','other');DOMAIN=PRIOR_DOMAIN+('clockc','placec','intro','firstlaw','secondlaw')


def forbidden(*args):raise ValueError('Unknown synchrony-laws input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple('other' if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode=='boundary':abstract(doc,{'qo'})
    elif mode=='native':abstract(doc,NUM|{'bi'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsl'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jslcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jslcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jslcontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})[0]['value']


def reject_unknown(name,args,m,symbols,mode='boundary'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown synchrony-laws' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


def references():
    names={'eisib':'clocka','eisik':'clockb','eiskg':'clockc','ziq':'placea','zir':'placeb','eiskh':'placec','ra':'frame','rb':'unit','rd':'author','eirf':'paper','eiskc':'intro','eiskd':'firstlaw','eiske':'secondlaw','ri':'now'}
    return {n:(lambda x=x:x) for n,x in names.items()}


def base():return references()|{'cb':relation({(c,p,'frame') for c,p in (('clocka','placea'),('clockb','placeb'),('clockc','placec'))})}


@lru_cache(None)
def role_checks():
    args=['clockb','placeb','clocka','placea','frame','unit','now'];row=('clockb','clocka','frame','unit','now');m=base()|{'qo':relation({row})};count=0
    assert run('eim7',args,m);count+=1
    for i in range(len(args)):
        a=args.copy();a[i]='other';assert not run('eim7',a,m);count+=1
    for rowcb in (('clockb','placeb','frame'),('clocka','placea','frame')):
        assert not run('eim7',args,m|{'cb':relation({rowcb})});count+=1
    reject_unknown('eim7',args,m,('cb','qo'))
    expected={'eina':{('clockb','clocka'),('clocka','clockb')},'einb':{('clocka','clockb'),('clocka','clockc'),('clockb','clockc'),('clockc','clockb')}}
    for name,pairs in expected.items():
        seen=[];places=[]
        mm=base();located=mm['cb'];mm|={'qo':lambda *xs:seen.append(xs) or True,'cb':lambda *xs:places.append(xs) or located(*xs)}
        assert run(name,[],mm);count+=1
        assert set(seen)=={(a,b,'frame','unit',s) for a,b in pairs for s in POINTS}
        assert set(places)=={(c,'place'+c[-1],'frame') for pair in pairs for c in pair}
    return dict(cases=count,every_clock_place_frame_unit_and_context_slot_checked=True,same_A_in_both_premises_and_same_B_C_in_conclusion=True)


@lru_cache(None)
def conditional_checks():
    count=0
    for name,pairs in (('eina',[('clockb','clocka'),('clocka','clockb')]),('einb',[('clocka','clockb'),('clocka','clockc'),('clockb','clockc'),('clockc','clockb')])):
        for bits in product((False,True),repeat=len(pairs)):
            rows={(a,b,'frame','unit',s) for (a,b),yes in zip(pairs,bits) if yes for s in POINTS}
            expected=(not bits[0] or bits[1]) if name=='eina' else (not(bits[0] and bits[1]) or (bits[2] and bits[3]))
            assert run(name,[],base()|{'qo':relation(rows)})==expected;count+=1
        reject_unknown(name,[],base(),('qo',))
    return dict(cases=count,all_4_symmetry_and_16_fork_truth_assignments=True,both_premises_required_and_mutual_conclusion_preserved=True,unknown_not_hidden_by_false_antecedent=True)


@lru_cache(None)
def generality_checks():
    # Universal B/C exchange proves the mutual form without assuming symmetry.
    # Enumerating finite relations is a regression, not a proof for all cardinalities.
    domain=('a','b','c');pairs=list(product(domain,repeat=2));count=0;valid=0
    doc=extract_document(parse(read(CORE)),roots=['saa','sab'],statement_indices=[]).document
    doc=parse(format_graph(doc,'compact')+'r jsls[a] c.r jslr[a a] c.q[k saa[p jsls p jslr]].q[k sab[p jsls p jslr]].')
    for bits in product((False,True),repeat=9):
        rel=dict(zip(pairs,bits))
        fork=all(not(rel[a,b] and rel[a,c]) or rel[b,c] for a,b,c in product(domain,repeat=3))
        mutual=all(not(rel[a,b] and rel[a,c]) or (rel[b,c] and rel[c,b]) for a,b,c in product(domain,repeat=3))
        symmetric=all(rel[a,b]==rel[b,a] for a,b in pairs)
        actual=evaluate_document(doc,individuals=domain,situations=('now',),primitives={'jsls':lambda a:True,'jslr':lambda a,b:rel[a,b]},max_steps=100000,memoize_definitions=True)
        assert [r['value'] for r in actual]==[symmetric,fork]
        assert fork==mutual;count+=1;valid+=fork
    return dict(relations=count,fork_models=valid,universal_fork_equivalent_to_mutual_form_in_all_three_object_relations=True,native_generic_laws_checked_with_current_evaluator=True,argument_for_arbitrary_domains='Exchange the universally bound second and third variables; their conjunctive antecedent is unchanged.')


def native_model(forward_end=4):
    cuts,m,rows,readings,records,values=prior_setup();r=cuts.read
    rows['cd'].add(('clockb','clocka'))
    rows['cb']={row for row in rows['cb'] if row[0] not in ('d2','r2','a2')}|{(e,p,'frame') for e,p in (('d2','placeb'),('r2','placea'),('a2','placeb'))}
    rows['ql'].add(('clockb','clocka','frame','unit','now'))
    rows['qb']={('clocka','clockb','frame','unit','now','trial'),('clockb','clocka','frame','unit','now','trial2')}
    records['trial2']=('placeb','placea','d2','r2','a2','ray2');values['trial']=(0,2,forward_end)
    readings={(c,e,'frame','unit',Q(x)) for c,e,x in (('clocka','depart',0),('clockb','reflect',2),('clocka','arrive',forward_end),('clockb','d2',10),('clocka','r2',12),('clockb','a2',14))}
    m|=references()|{n:relation(rs) for n,rs in rows.items()}|{'ce':lambda c,e,f,u,x:(c,e,f,u,r(x)) in readings,'bi':lambda a,b,c:r(b)-r(a)==r(c)-r(b)}
    return cuts,m,rows


@lru_cache(None)
def native_checks():
    _,m,rows=native_model();forward=['clocka','placea','clockb','placeb','frame','unit','now'];reverse=['clockb','placeb','clocka','placea','frame','unit','now'];count=0
    for args in (forward,reverse):assert run('eim7',args,m,'native');count+=1
    assert run('eina',[],m,'native');count+=1
    _,bad,_=native_model(5)
    assert not run('eim7',forward,bad,'native');count+=1
    assert run('eim7',reverse,bad,'native');count+=1
    assert not run('eina',[],bad,'native');count+=1
    for symbol in ('ql','qb','qa','ca','cc','cd','cb','ci','cf','cg','ch','ce','bi'):
        assert not run('eim7',forward,m|{symbol:lambda *xs:False},'native');count+=1
    reject_unknown('eim7',forward,m,('ql','qb','qa','cb','ce','qi','qj','qk','bi'),'native')
    try:run('eim7',forward,m,'full_real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Unbounded rational/function domain silently sampled')
    return dict(cases=count,native_qo_qn_db_with_two_opposite_light_trials=True,reverse_synchrony_does_not_silently_force_forward=True,physical_roles_completeness_nonempty_trials_required=True,bi_and_numeric_cuts_are_explicit_boundaries=True,full_real_domain_not_sampled=True)


@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('firstlaw','author','paper','einc','now'),('secondlaw','author','paper','eind','now')},'eiski':{('firstlaw','author','qp','eina','paper','now'),('secondlaw','author','qq','einb','paper','now')},'eiskj':{('firstlaw','intro',Q(1),'paper','now'),('secondlaw','intro',Q(2),'paper','now')},'ue':{('intro','firstlaw','now'),('firstlaw','secondlaw','now')}};m=references()|{n:relation(rs) for n,rs in rows.items()};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-2:]
        def go(extra=None):return [r['value'] for r in evaluate(doc,m|(extra or {}))]
        assert go()==[True,True];count+=1
        for symbol,rs in rows.items():
            for row in rs:
                target=1 if row[0]=='secondlaw' or row==('firstlaw','secondlaw','now') else 0;expected=[True,True];expected[target]=False
                for i in range(len(row)):
                    assert go({symbol:relation((rs-{row})|{changed(row,i)})})==expected;count+=1
        assert go({n:forbidden for n in ('qo','cb','qa','ce','bi')})==[True,True];count+=1
    return dict(cases=count,same_intro_numbered_order_and_general_law_references=True,native_core_and_full_presentations_checked=True,attribution_does_not_execute_quoted_physics=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==243
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in ((PRIOR,[240]),('data/einstein-local-synchrony-paragraph-review-v1.json',list(range(234,240)))):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,indices)
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    assert [s['nonblank_characters'] for s in source['segments']]==[74,114] and sum(len(s['math']) for s in source['segments'])==9
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX,INDEX+1])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=241,previous_whole_paragraph_and_assumption_preserved=True,whole_188_character_and_nine_math_occurrence_source_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_synchrony_laws import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('roles',role_checks),('conditionals',conditional_checks),('generality',generality_checks),('native_synchrony',native_checks),('presentation',presentation_checks),('structure',structure_checks)]};segments=[]
    for s in source_record()['segments']:
        segments.append(dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
        segments.extend(dict(unit=s['unit'],unit_sha256=s['unit_sha256'],math_id=m['id'],math_sha256=m['sha256'],definitions=['eim7','eina','einb'],status='explicit_interpretive_annotation') for m in s['math'])
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,PRIOR,'data/einstein-local-synchrony-paragraph-review-v1.json','scripts/compose_synchrony_laws.py','scripts/check_synchrony_laws.py','scripts/review_synchrony_laws.py','tests/test_synchrony_laws.py','scripts/check_light_roundtrip_definition.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='numbered_synchrony_symmetry_and_three_clock_conditions_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['二単位の全体判断の登録、u0018の定義のまとめ'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
