"""Check signed formula, current quantities, calculation chain and attribution."""
from functools import lru_cache
from fractions import Fraction as Q
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_material_relative_frame import RS
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_calculation_discourse import sequence,pair,symbol
from scripts.check_angle_composition import CASES
from scripts.check_transverse_time import square_root
from scripts.check_written_math_corrections import reviewed_math
from scripts.compose_velocity_composition_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,STEPS,build

DOC='docs/velocity-composition-claim-v1.md';SOURCE='data/einstein-velocity-composition-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-velocity-angle-claim-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-velocity-angle-u{n:04d}-review-v1.json' for n in (135,137,138))+('data/einstein-velocity-magnitude-u0136-review-v1.json',)
DEPENDENCIES=('reports/angle-composition-v1.json','reports/velocity-angle-measure-v1.json','reports/velocity-angle-claim-v1.json','reports/velocity-magnitude-claim-v1.json','reports/calculation-discourse-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','ri':'discourse','eisoq':'fifth','zb6':'context','zkv':'anglemeaning','zkx':'calculation','zkw':'formula'}
DOMAIN=tuple(CONSTANTS.values())+('method','other');POINTS=('context','discourse','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sjd','sjt','sky'}
    if name=='ejpa':bounds|={'ejoi','ejoj','ejow'}
    if name in ('ejpb','ejpc'):bounds|={'ejpa'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if name=='ejpd':
        pairs=json.loads(mode)
        helper=parse('n:r jvccprogram[a d '+STEPS+'] '+STEPS+'.')['declarations'][0]
        prefix='n:r ejpb[] e.r ejpc[] e.r jvccmid[] e.r jvccprogram[a d '+STEPS+'] '+STEPS+'.'
        replacement=parse(prefix+'d zlx[method a stage d] '+STEPS+'[k jvccprogram[v method v stage '+sequence(pairs)+']].')['declarations'][-1]
        doc['declarations']=[d for d in doc['declarations'] if d['name']!='zlx'];missing={n for p in pairs for n in p}-{d['name'] for d in doc['declarations']}
        at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='ejpd')
        doc['declarations'][at:at]=[dict(kind='primitive',name=n,parameters=[],result='content') for n in sorted(missing)]+[helper,replacement]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvcc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvccpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvccpoint',arguments=[]))
    elif d['result']==RS:
        doc['declarations'].append(dict(kind='primitive',name='jvccresult',parameters=[RS],result='truth'));expr=dict(kind='call',symbol='jvccresult',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots);values=[]
    def capture(value):values.append(value);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvccpoint':lambda:'discourse','jvccresult':capture}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jvccprogram',lambda method,stage,seq:seq if (method,stage)==('method','discourse') else SequenceValue((),seq.element_type))
    result=evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return values[0] if values else result


def arithmetic(undefined=0):
    cuts,m=numbers();c=lambda x:cuts.make(Q(x));r=cuts.read
    reciprocal=lambda x:c(1/r(x) if r(x) else undefined)
    root=lambda x:square_root(cuts,x) if r(x)>=0 else c(undefined)
    return cuts,m|{'sjd':reciprocal,'sjt':reciprocal,'sky':root}


@lru_cache(None)
def numeric_checks():
    count=0;out={}
    for undefined in (0,17):
        cuts,m=arithmetic(undefined);c=lambda x:cuts.make(Q(x))
        for label,(values,expected) in CASES.items():
            if label=='invalid_cut':continue
            result=run('s2t',list(map(c,values)),m);assert result==expected,label;count+=1;out[label]=result
        assert not run('s2t',list(map(c,(5,3,1,1,0,Q(25,7)))),m|{'ba':lambda *xs:False});count+=1
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read
    values=(5,3,25,Q(-3,5),Q(4,5),25);args=list(map(c,values))
    assert r(run('s2r',args[:5],m))==400 and r(run('s2s',args[:4],m))==Q(-4,5);count+=2
    assert not run('s2t',args,m) and run('s2t',args[:-1]+[c(-25)],m);count+=2
    unknowns(lambda mm:run('s2t',list(map(c,(5,3,1,1,0,Q(25,7)))),mm),m,('sjd','sjt','sky','ba','sca'))
    return dict(cases=count,examples=out,original_signed_quotient_not_absolute_or_squared=True,domain_rejection_under_two_off_guard_oracle_values=True,negative_denominator_counterexample=dict(radicand='400',denominator='-4/5',printed_value='-25',nonnegative_magnitude='25'))


@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));norm=norm_factory(cuts,());count=0
    # The rational alpha below is only a boundary witness, not a value of atan.
    rows={'ejoi':{(Q(25),'context')},'ejoj':{(Q(25),'context')},'ejow':{(Q(3),'context')}}
    mm=m|{'zkp':lambda:c(25),'zkq':lambda:c(25),'eiso4':lambda:c(3)}|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejpa',['context'],mm),mm,rows,norm)
    for n in ('zkp','zkq','eiso4'):
        assert not run('ejpa',['context'],mm|{n:lambda:c(0)});count+=1
    assert not run('ejpa',['other'],mm);count+=1
    unknowns(lambda mm:run('ejpa',['context'],mm),mm,('zkp','zkq','eiso4'))
    rows={'ejpa':{('context',)}};base=m|{'ejpa':lambda ctx:ctx=='context'}
    count+=perturb(lambda mm:run('ejpb',[],mm),base,rows)
    for vals in ((5,3,1,1,0,Q(25,7)),(5,3,5,Q(3,5),Q(-4,5),5),(5,3,25,Q(-3,5),Q(4,5),25)):
        V,s,W,co,si,U=vals;angle=FunctionValue(('truth',),RS,lambda b:c(co if b else si))
        mm=base|{'tc':lambda:c(V),'zb7':lambda:c(s),'zkq':lambda:c(W),'zkp':lambda:c(U),'zkt':lambda:angle}
        assert run('ejpb',[],mm);count+=1
        assert run('ejpc',[],mm)==(W!=25);count+=1
        if W!=25:
            count+=perturb(lambda mm:run('ejpc',[],mm),mm,rows)
            assert not run('ejpc',[],mm|{'zkp':lambda:c(U+1)});count+=1
            assert not run('ejpc',[],mm|{'zb6':lambda:'other'});count+=1
            unknowns(lambda mm:run('ejpc',[],mm),mm,('tc','zb7','zkq','zkp','zkt','ejpa'))
    return dict(cases=count,current_derivative_norm_own_norm_and_same_alpha_bound=True,same_context_and_quantities_in_printed_formula=True,premise_not_filtered_to_positive_denominator=True,negative_denominator_premise_fixture_with_false_conclusion=True,angle_boundary_witness_not_exact_radian_value=True)


@lru_cache(None)
def chain_checks():
    good=[('ejpb','jvccmid'),('jvccmid','ejpc')];count=0
    cases=((good,2,{},True),([('ejpb','ejpc')],1,{},True),([],2,{},False),(list(reversed(good)),2,{},False),([good[1]],2,{},False),([good[0]],2,{},False),([good[0],('ejpb','ejpc')],2,{},False),(good,1,{},False),(good,2,{good[0]:-1},False),([good[0],('jvccmid','jvccmid'),good[1]],2,{},False),([good[0],('jvccmid','jvccmid'),good[1]],3,{},True),(good,0,{('ejpb','ejpc'):0},False))
    for pairs,budget,costs,expected in cases:
        m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','discourse'),'zla':lambda a,b,s:s=='discourse','zlb':lambda step,s:Q(costs.get(pair(step),1)),'zlc':lambda n,s:s=='discourse' and n<=budget}
        assert run('ejpd',[],m,json.dumps(pairs))==expected;count+=1
    m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','discourse'),'zla':lambda a,b,s:s=='discourse' and (symbol(a),symbol(b)) in good,'zlb':lambda step,s:Q(1 if s=='discourse' else 10),'zlc':lambda n,s:s=='discourse' and n<=2};mode=json.dumps(good)
    for patch in ({'zlw':lambda *xs:False},{'rd':lambda:'other'},{'zlw':lambda a,p,s:(a,p,s)==('author','other','discourse')},{'zlw':lambda a,p,s:(a,p,s)==('author','method','other')},{'zla':lambda a,b,s:(symbol(a),symbol(b))==good[0]},{'zlb':lambda step,s:Q(10)},{'zlc':lambda n,s:s=='other' and n<=2},{'jvccprogram':lambda p,s,seq:seq if (p,s)==('other','discourse') else SequenceValue((),seq.element_type)}):
        assert not run('ejpd',[],m|patch,mode);count+=1
    unknowns(lambda mm:run('ejpd',[],mm,mode),m,('zlw','zla','zlb','zlc'))
    assert run('ejpd',[],m|{n:forbidden for n in ('ejpb','ejpc','ejpa','s2t','ejoi','ejoj','ejow')},mode);count+=1
    return dict(cases=count,native_connected_nonempty_chain_and_nonnegative_total=True,same_available_method_stage_premise_result_and_burden=True,no_fixed_step_count_or_cost_threshold=True,quoted_conclusion_not_executed_as_true=True)


@lru_cache(None)
def presentation_checks():
    count=0
    groups=(('ejpe',{'zc':{('calculation','author','ejpb','ejpc','fifth','discourse')}}),('ejpf',{'uh':{('calculation','author','ejpd','fifth','discourse')}}),('ejpi',{'eir3':{('calculation','author','paper','ejpg','discourse')},'ue':{('anglemeaning','calculation','discourse')}}),('ejpj',{'eir3':{('calculation','author','paper','ejph','discourse')}}),('ejpk',{'uh':{('formula','author','ejpc','fifth','discourse')},'ue':{('calculation','formula','discourse')}}))
    for name,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejpb','ejpc','ejpd','s2t','eismh')});count+=1
    for name,patch in (('ejpi',{'zkv':lambda:'calculation'}),('ejpk',{'zkw':lambda:'calculation'})):
        assert not run(name,[],{n:lambda *xs:True for n in ('eir3','uh','ue')}|patch);count+=1
    return dict(cases=count,source_result_easy_appraisal_same_author_node_scope=True,colon_connects_displayed_formula_and_prior_angle_explanation=True,attribution_does_not_certify_conclusion_or_method=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256'])
    reviewed=reviewed_math()['M0257'];flat=lambda xml:re.sub(r'\s','',''.join(ET.fromstring(xml).itertext()))
    assert flat(reviewed['reviewed_mathml'])=='U=(v2+w2+2vwcos⁡α)−(vwsin⁡αV)21+vwcos⁡αV2.'
    ns='{http://www.w3.org/1998/Math/MathML}';root=ET.fromstring(reviewed['reviewed_mathml']);fraction=next(root.iter(ns+'mfrac'))
    assert len(list(root.iter(ns+'msqrt')))==1 and 'cos' in flat(ET.tostring(fraction[1],encoding='unicode')) and 'sin' not in flat(ET.tostring(fraction[1],encoding='unicode'))
    segments=[]
    for u in inv['units'][138:140]:
        assert digest(u['text'].encode())==u['text_sha256']
        entries=[]
        for n in u['math_ids']:
            e=math[n];assert digest(e['mathml'].encode())==e['sha256'];item=dict(id=n,sha256=e['sha256'],mathml_flat=flat(e['mathml']))
            if n=='M0257':item.update(correction_id=reviewed['correction_id'],reviewed_math_sha256=reviewed['reviewed_math_sha256'],reviewed_mathml=reviewed['reviewed_mathml'],reviewed_mathml_flat=flat(reviewed['reviewed_mathml']))
            entries.append(item)
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=entries))
    assert segments[0]['text'][94:]=='Nach einfacher Rechnung ergibt sich:' and segments[1]['text']=='[M0257]'
    paths={INVENTORY,DOC,READING,*old['source_sha256'],'data/written-math-corrections-v1.json','reports/written-units-v1.json','scripts/check_written_math_corrections.py'}
    return dict(version='einstein-velocity-composition-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['906'],segments=segments,observations=['原刊906頁のαの意味の説明、Nach einfacher Rechnung ergibt sichのコロン、平方根・分数・二つのcosと分子のsin及び二乗、句点を照合した。','M0257は既存の原刊訂正層を使う。電子転記のMathMLとハッシュを保存し、分母のsinのみをcosへ訂正した別の式を明示する。','同じ点の二つの非負速さと角を現在の取得規則へ結ぶ。分母負で不一致となる条件を前提から削らず、印刷式の著者帰属と普遍的な真理を区別する。','計算の容易さは同じ前提から同じ結論までの許容された有限手順の低負担評価として読む。具体的な省略計算や実行済み履歴を補わない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([131,354,355],[131],[131,132],[355])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    legacy=parse(read('examples/v014/einstein-angle-composition.noema'));lb=json.loads(read('data/angle-composition-basis-v1.json'))
    for n in ('s2r','s2s','s2t'):
        assert next(d for d in new.document['declarations'] if d['name']==n)==next(d for d in legacy['declarations'] if d['name']==n)
        assert new.entries[n]['meaning_ja'].removeprefix('[current の記号名] ')==lb['definitions'][n]
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/velocity-angle-claim-identifiers-v1.json'))['entries']
    doc=core();names={d['name'] for d in doc['declarations']};assert {'s2r','s2s','s2t','s2w','s2x','s2y','ejoi','ejoj','ejow','ejny','ejm2','sede','sedi'}<=names
    assert not {'s2v','s3c','s3d','zke','syw','szs','szt'}&names
    active=extract_document(new.document,roots=[],statement_indices=list(range(356))).document
    # The unreviewed later alternative derivation (u0147, s5m) still quotes
    # s3c. Do not claim that this separate future task was repaired here.
    assert {'s2v','s3c','s3d'}&{d['name'] for d in active['declarations']}=={'s3c'}
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_partial_statements=list(INDICES),other_statements_preserved=353,prior_judgments_preserved=True,legacy_signed_formula_body_and_meaning_preserved=True,no_active_assertion_depends_on_old_formula_or_calculation=True,later_unreviewed_s5m_still_uses_old_premise_s3c=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('physical',physical_checks),('chain',chain_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_angle_claim','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','compose_calculation_discourse','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_coordinate_correspondence','check_calculation_discourse','check_angle_composition','check_transverse_time','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'examples/v014/einstein-angle-composition.noema','data/angle-composition-basis-v1.json','scripts/compose_velocity_composition_claim.py','scripts/check_velocity_composition_claim.py','tests/test_velocity_composition_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selection,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s,selection in zip(source_record()['segments'],([132,133,134,135],[133,134,135]))])
    return dict(status='printed_velocity_quotient_and_easy_calculation_connected',document=FULL,**results,alignment=alignment,reviewed_math_layer=reviewed_math()['M0257'],verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0139–u0140の全単位意味判断','u0141以降の対称性と軸方向合成'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
