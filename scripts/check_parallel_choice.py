"""Check one parallel candidate, scoped permission and universal t notation."""
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
from scripts.check_material_axes import setup,DOMAIN as HISTORY_DOMAIN
from scripts.check_rod_methods import value,relation
from scripts.compose_parallel_choice import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build
from scripts.review_parallel_choice import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

DOMAIN=HISTORY_DOMAIN+('author','paper','section','initialnode','firstnode','definitenode','adoptionnode','reasonnode','tdesignation','kdesignation','Kdesignation','usea','useb','usec')
POINTS=('context','other','initial','discourse')
def forbidden(*xs):raise ValueError('Unknown parallel-choice input')
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','zbm':'moving','zb4':'initial','zb6':'context','zcj':'body','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zb5':'initialnode','zcg':'firstnode','zco':'definitenode','zcp':'adoptionnode','zcq':'reasonnode','eism5':'tdesignation','eisna':'kdesignation','eisnb':'Kdesignation'}.items()}

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eiv7','eipw','eit2','eivz','eiwj','eiwb'}
    if name!='eiwk':boundaries.add('eiwk')
    if name in ('eiwo','eiwp','eiwq'):boundaries.add('eiwm')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jpc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpccontent',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpccontent',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jpccontent',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown parallel-choice' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('wrong' if i==j else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def reference_checks():
    cuts,m,fs,norm=setup();c=cuts.make;lines={'x':'body','y':'second','z':'hidden'}
    origin=['origin','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*(f('origin') for f in fs)]
    rows={'eiv7':{('frame','context')},'eipw':{(line,'frame','context') for line in lines.values()},'eit2':{norm(origin)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'zbn':lambda *xs:'origin','zbo':lambda f,a,ctx:lines[a],'eismh':lambda o,f,lu,tu,a,ctx:fs[('x','y','z').index(a)](o)}
    check=lambda mm:run('eiwk',['context'],mm,domain=HISTORY_DOMAIN);count=perturb(check,m,rows,norm)
    assert not check(m|{'zbn':lambda f,ctx:'otherorigin' if ctx=='initial' else 'origin'});count+=1
    for a in lines:
        assert not check(m|{'zbo':lambda f,role,ctx,a=a:'other' if role==a and ctx=='initial' else lines[role]});count+=1
    unknowns(check,m,('zbn','zbo','eismh','eisls','eislt'))
    rows={'eivz':{('context',)},'eiv7':{('moving','context')},'eiwk':{('context',)}}
    count+=perturb(lambda mm:run('eiwl',['context'],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=count,same_initial_reference_origin_and_all_axes_remain_static=True,moving_frame_not_given_static_condition=True)

@lru_cache(None)
def candidate_checks():
    rows={'eiwj':{('body',)},'eiwk':{('context',)},'eiwb':{('frame','moving','context')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'zci':lambda h:'context'}
    count=perturb(lambda mm:run('eiwn',['body'],mm),m,rows)
    domain=('a','b')
    for valid_bits in product((False,True),repeat=2):
        valid={h for h,on in zip(domain,valid_bits) if on}
        for parallel_bits in product((False,True),repeat=2):
            parallel={h for h,on in zip(domain,parallel_bits) if on}
            ctx={'a':'context','b':'other'}
            m={'ra':lambda:'a','zbm':lambda:'b','zci':lambda h:ctx[h],'eiwm':lambda h:h in valid,'eiwb':lambda a,b,c:any(ctx[h]==c for h in parallel)}
            assert run('eiwo',[],m,domain)==bool(valid&parallel);count+=1
    m={'zci':lambda h:'context','eiwm':relation({('body',)})}
    assert run('eiwp',[],m);assert not run('eiwp',[],m|{'zci':lambda h:'other'});count+=2
    return dict(cases=count,one_candidate_meets_admissibility_and_whole_interval_alignment=True,definite_selected_history_kept_separate_from_parallel_possibility=True)

@lru_cache(None)
def symmetry_checks():
    domain=('a','b');count=0
    for forward in (dict(a='a',b='b'),dict(a='b',b='a'),dict(a='a',b='a')):
        for inverse in (dict(a='a',b='b'),dict(a='b',b='a')):
            for flags in product((False,True),repeat=2):
                valid={h for h,on in zip(domain,flags) if on}
                def physical(d,f,i,ref,axis,ctx):
                    return tuple(d(p) for p in domain)==(True,True) and tuple(f(p) for p in domain)==tuple(forward[p] for p in domain) and tuple(i(p) for p in domain)==tuple(inverse[p] for p in domain) and (ref,axis,ctx)==('a','b','context')
                m={'ra':lambda:'a','yn':lambda:'b','zch':lambda h,c:h in domain and c=='context','zcr':lambda h:forward[h],'zcs':lambda h:inverse[h],'eiwm':lambda h:h in valid,'eism3':physical}
                expected=all(inverse[forward[h]]==h and forward[inverse[h]]==h and ((h in valid)==(forward[h] in valid)) for h in domain)
                assert run('eiwq',[],m,domain)==expected;count+=1
    m={'ra':lambda:'a','yn':lambda:'b','zbm':lambda:'b','zch':lambda *xs:True,'zcr':lambda h:h,'zcs':lambda h:h,'eiwm':lambda h:True,'eism3':lambda *xs:True,'zci':lambda h:'context','eiwb':lambda *xs:False}
    assert run('eiwq',[],m,domain) and not run('eiwo',[],m,domain);count+=1
    assert not run('eiwq',[],m|{'eism3':lambda *xs:False},domain);count+=1
    unknowns(lambda mm:run('eiwq',[],mm,domain),m,('eism3','zch','zcr','zcs','eiwm'))
    return dict(cases=count,native_bijection_and_condition_preservation_checked=True,physical_symmetry_classification_required_beyond_arbitrary_permutation=True,symmetry_does_not_imply_parallel_candidate_existence=True)

@lru_cache(None)
def notation_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    rows={'zcf':{('point','frame','timeunit','context')}};m|={'zcf':relation(rows['zcf']),'yl':lambda *xs:c(Q(3))}
    count=perturb(lambda mm:run('eiwt',['point',c(Q(3)),'context'],mm),m,rows)
    assert not run('eiwt',['point',c(Q(4)),'context'],m);count+=1
    unknowns(lambda mm:run('eiwt',['point',c(Q(3)),'context'],mm),m,('yl','ba','sca'))
    uses={('usea','tdesignation','paper','paper','discourse'),('useb','tdesignation','paper','paper','discourse'),('usec','tdesignation','paper','paper','discourse')}
    rows={'eislo':{('tdesignation','eiwt','paper','discourse')},'eism7':{(u,'eiwt','paper','discourse') for u in ('usea','useb','usec')}}
    m={n:relation(rs) for n,rs in rows.items()}|{'eism6':relation(uses)}
    count+=perturb(lambda mm:run('eiwu',[],mm),m,rows)
    assert not run('eiwu',[],m|{'eism6':lambda *xs:False});count+=1
    assert not run('eiwu',[],m|{'eism6':relation(uses|{('other','tdesignation','paper','paper','discourse')})});count+=1
    assert run('eiwu',[],m|{'yl':forbidden,'zcf':forbidden});count+=1
    unknowns(lambda mm:run('eiwu',[],mm),m,('eism6',))
    return dict(cases=count,rest_time_rule_and_every_occurrence_bound=True,notation_does_not_execute_measurement=True)

@lru_cache(None)
def presentation_checks():
    rows={'eism4':{('author','eiwr','section','paper','discourse')},'zct':{('reasonnode','author','eiwq','adoptionnode','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiws',[],mm),m,rows)
    assert run('eiws',[],m|{n:forbidden for n in ('ug','eiwo','eiwn','eiwq','sfs','eism3')});count+=1
    rows={'ug':{('adoptionnode','author','eiwo','section','discourse')}}
    count+=perturb(lambda mm:run('eiwr',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    rows={'ug':{('firstnode','author','eiwv','section','discourse')},'zao':{('initialnode','firstnode','section','discourse')},'eisd4':{('firstnode','author','kdesignation','moving','paper','discourse'),('firstnode','author','Kdesignation','frame','paper','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiww',[],mm),m,rows)
    assert run('eiww',[],m|{n:forbidden for n in ('eiwv','eiwl','eivz','eiv7','eit2')});count+=1
    rows={'uh':{('definitenode','author','eiwp','section','discourse')},'ue':{('firstnode','definitenode','discourse')},'eisa5':{('adoptionnode','author','eiwo','eiwu','discourse')},'eism4':{('author','eiwr','section','paper','discourse')},'zct':{('reasonnode','author','eiwq','adoptionnode','section','discourse')},'eislo':{('tdesignation','eiwt','paper','discourse')},'eism7':{('usea','eiwt','paper','discourse')}}
    def inference(author,premise,result,ctx):return (author,result,ctx)==('author','definitenode','discourse') and {p for p in DOMAIN if premise(p)}=={'firstnode'}
    m={n:relation(rs) for n,rs in rows.items()}|{'ud':inference,'eism6':relation({('usea','tdesignation','paper','paper','discourse')})}
    count+=perturb(lambda mm:run('eiwz',[],mm),m,rows)
    assert not run('eiwz',[],m|{'ud':lambda *xs:False});count+=1
    assert run('eiwz',[],m|{n:forbidden for n in ('eiwp','eiwo','eiwm','ug')});count+=1
    for name,node,message,prior in (('eiwy','firstnode','eiwx','initialnode'),('eiw3','definitenode','eiw2','firstnode')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(prior,node,'discourse')}}
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ug','uh','eism4','eism7','zct','eivz','eiwo')});count+=1
    return dict(cases=count,permission_not_assumption_execution_or_physical_truth=True,two_sentence_forces_names_consequence_and_parenthesis_connected=True,author_attribution_does_not_execute_quoted_contents=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==270
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIORS[0]));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[267])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);oldann=json.loads(read('data/axis-states-identifiers-v1.json'))['entries'];assert json.loads(read(ANNOTATIONS))['entries'][:len(oldann)]==oldann
    from scripts.compose_kant_discourse import discourse_basis
    canonical=next(p for p in discourse_basis()['primitives'] if p['symbol']=='ud')
    assert new.entries['ud']['meaning_ja']==canonical['meaning_ja']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert len(doc['statements'])==2
    assert ds['eiwx']['body']['force']=='direct' and ds['eiw2']['body']['force']=='assert'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=268,prior_meanings_and_reviews_preserved=True,setting_directive_and_permission_claim_distinguished=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('reference',reference_checks),('candidate',candidate_checks),('symmetry',symmetry_checks),('notation',notation_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_parallel_choice.py','scripts/check_parallel_choice.py','scripts/review_parallel_choice.py','tests/test_parallel_choice.py','scripts/check_material_axes.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_axis_states.py','scripts/compose_material_axes.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py','scripts/compose_kant_discourse.py'}
    return dict(status='whole_motion_setting_and_symmetry_permission_connected',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0044の全単位意味判断登録','u0045以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
