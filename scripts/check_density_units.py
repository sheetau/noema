"""Verify the two-unit reconnection without certifying the density law."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from itertools import product
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.integration_audit import dependency_path
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_density_units import ROOT,PARENT,FULL,CORE,REVIEW,INDEX,FIELDS,BINDINGS,PREVIOUS_BINDINGS,build
from scripts.compose_local_density import FIXED
from scripts.compose_additive_charge import ADAPTER
from scripts.compose_limits import call as k,app,op,v,both
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_moving_light_trip import literal

REPORT=ROOT/'reports/density-units-v1.json'
SCENES=('text','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def source_quote(doc):return doc['statements'][INDEX]['body']['arguments'][-1]


def structural_checks():
    old=parse(text(PARENT));doc=parse(text(FULL))
    assert doc['declarations']==old['declarations']
    assert len(doc['statements'])==len(old['statements'])==206
    restored=deepcopy(doc);restored['statements'][INDEX]['body']['arguments'][-1]=source_quote(old)
    assert restored==old
    before,after=source_quote(old)['body'],source_quote(doc)['body']
    assert before['symbol']==after['symbol']=='seoz'
    changes=[]
    for (name,_),left,right in zip(FIELDS,before['arguments'],after['arguments'],strict=True):
        assert left==dict(kind='call',symbol=PREVIOUS_BINDINGS[name],arguments=[])
        assert right==dict(kind='call',symbol=BINDINGS[name],arguments=[])
        if left!=right:changes.append(name)
    assert changes==['lengthunit','timeunit']
    for name in ('seoz','seoy','seou','seoc','sens','ta','rb'):
        assert dependency_path(doc,INDEX,name),name
    for name in ('zqi','zqj'):assert dependency_path(doc,INDEX,name) is None,name
    # The same light-speed reading already uses these two units in the earlier
    # light propagation content; inspect those actual argument references.
    lookup={d['name']:d for d in doc['declarations']}
    assert lookup['sbd']['body']['body']['arguments'][0]==dict(kind='call',symbol='tc',arguments=[])
    from noema.extraction import _references
    assert {'ta','rb','tb'}<=_references(lookup['sba'])
    assert {'ta','rb'}<=_references(lookup['sbb'])
    # senu's actual antecedent starts with srd(light, speed, beta).
    guard=lookup['senu']['body']['arguments'][0]
    assert guard['symbol']=='srd' and guard['arguments']==[
        dict(kind='variable',name=lookup['senu']['parameters'][i]['name']) for i in (0,1,2)]
    return dict(changed_arguments=changes,all_206_statements_retained=True,other_205_statements_identical=True,
        declarations_identical=True,old_unit_references_unreachable_from_revised_statement=True,
        source_guard_is_actual_srd=True,frame_placement_still_external=True)


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=('item','other','author','earlier','node','scope','ta','rb','zqg','zqk','zqi','zqj'),situations=SCENES,
        primitives={n:model[n] for n in names},max_steps=2_000_000,memoize_definitions=True)]


def routing_probe(path,aliases=False):
    original=parse(text(path));quote=source_quote(original)['body']
    selected=extract_document(original,statement_indices=[INDEX]).document;selected['statements']=[]
    # Parse ordinary surface syntax rather than relying on an internal node name.
    direct='k seoz['+' '.join(k(a['symbol']) for a in quote['arguments'])+']'
    doc=abstract(candidate(format_graph(selected,'compact'),'q[t['+direct+'][k ri[]]].'),{'sedi','seou','seoy','seof'})
    lookup={d['name']:d for d in doc['declarations']};model=guarded(doc);seen=[]
    for name in model:
        decl=lookup[name]
        if not decl['parameters']:
            result=decl['result']
            if isinstance(result,dict) and result.get('kind')=='function':
                def forbidden(*xs,name=name):raise ValueError('Boundary input executed: '+name)
                value=FunctionValue(tuple(result['parameters']),result['result'],forbidden)
            else:value='text' if name=='ri' else name
            model[name]=lambda value=value:value
    if aliases:
        if 'zqi' in model:model['zqi']=lambda:'ta'
        if 'zqj' in model:model['zqj']=lambda:'rb'
    def returned(name):
        result=lookup[name]['result']
        return FunctionValue(tuple(result['parameters']),result['result'],lambda *xs:(_ for _ in ()).throw(ValueError('Physical predicate executed')))
    def totals(*xs):
        row=dict(zip((n for n,_ in ADAPTER),xs,strict=True))
        seen.append(dict(boundary='seou',timeunit=row['timeunit']))
        return returned('seou')
    def density(*xs):
        row=dict(zip([n for n,_ in FIXED]+['clock'],xs,strict=True))
        seen.append(dict(boundary='seoy',lengthunit=row['lengthunit'],timeunit=row['timeunit'],chargeunit=row['chargeunit']))
        return returned('seoy')
    model.update(sedi=lambda pi:True,seou=totals,seoy=density,seof=lambda *xs:Content(SCENES,(True,True)))
    assert evaluate(doc,model)==[True]
    return seen


def routing_checks():
    old=routing_probe(PARENT);new=routing_probe(FULL);same=routing_probe(PARENT,True)
    assert old and new and same==new
    assert all(row['timeunit']=='zqj' for row in old)
    assert all(row['timeunit']=='rb' for row in new)
    assert [row['lengthunit'] for row in new if row['boundary']=='seoy']==['ta']*len(SCENES)
    assert [row['chargeunit'] for row in new if row['boundary']=='seoy']==['zqk']*len(SCENES)
    return dict(previous=old,revised=new,previous_with_explicit_aliases=same,
        abstracted_boundaries=['sedi','seou','seoy','seof'],physical_density_law_evaluated=False)


def arithmetic_checks():
    library=extract_document(parse(text(FULL)),roots=['sra'],statement_indices=[]).document
    mul=lambda a,b:k('ad',a,b)
    old=k('sra',v('light'),v('speed'),v('beta'))
    common=k('sra',mul(v('scale'),v('light')),mul(v('scale'),v('speed')),v('beta'))
    mixed=k('sra',v('light'),mul(v('scale'),v('speed')),v('beta'))
    positive=k('aa',literal(0),v('scale'))
    # Fix a rational witness explicitly. An unconstrained real solver witness
    # can be irrational and is not, by itself, a counterexample over Q.
    witness=both(*(op('e',v(name),literal(value)) for name,value in
        zip(('light','speed','beta','scale'),(F(5),F(3),F(5,4),F(4,3)),strict=True)))
    proofs={}
    for name,body,wanted in (
        ('common_positive_speed_scale',op('y',positive,op('z',old,common)),'valid'),
        ('only_relative_speed_scaled',op('y',both(positive,old,witness),mixed),'invalid')):
        doc=parse(format_graph(library,'compact')+assertion('light speed beta scale',body))
        proof=verify_universal(doc,MEANINGS,timeout_ms=30000)[0]
        assert proof['status']==wanted,(name,proof);proofs[name]=proof
    # Actual real-cut guard from senu, using only rational-embedding arithmetic.
    base=extract_document(parse(text(FULL)),roots=['srd'],statement_indices=[]).document
    cases={'original':(F(5),F(3),F(5,4)),
        'consistent_new_units':(F(20,3),F(4),F(5,4)),
        'mixed_units':(F(5),F(4),F(5,4)),
        'mixed_units_negative_velocity':(F(5),F(-4),F(5,4)),
        'zero_velocity':(F(5),F(0),F(1))}
    rows={}
    for name,values in cases.items():
        query='q['+k('srd',*[k('bb',literal(x)) for x in values])+'].'
        doc=abstract(candidate(format_graph(base,'compact'),query),OPS);cuts,model=setup(doc)
        row=evaluate(doc,model);assert row==[name not in ('mixed_units','mixed_units_negative_velocity')],(name,row)
        rows[name]=dict(values=[str(x) for x in values],guard=row[0])
    return dict(rational_proofs=proofs,real_cut_guard_probes=rows,all_real_scaling_proved=False,
        conditional_case_disappearance_is_possible=True,full_source_content_truth_inferred=False)


def attribution_checks():
    source=parse(text(FULL));doc=extract_document(source,statement_indices=[INDEX]).document
    expected=deepcopy(doc['statements'][0]['body']['arguments'][-1]['body']);rows=[]
    for present,explain,order in product((False,True),repeat=3):
        model=guarded(doc)
        for name,value in dict(rd='author',zqa='earlier',zqb='node',zqc='scope',ri='text').items():model[name]=lambda value=value:value
        model.update(uh=lambda node,author,content,scope,context:present and json.loads(content.syntax)==expected,
            uf=lambda *args:explain,ue=lambda *args:order)
        actual=evaluate(doc,model);assert actual==[present and explain and order]
        rows.append(dict(present=present,explain=explain,order=order,value=actual[0]))
    # The old quote has distinct syntax even if the old unit values are aliases.
    old=parse(text(PARENT));probe=deepcopy(old);probe['statements']=[old['statements'][INDEX]]
    oldmodel=guarded(probe);oldmodel.update(model)
    oldmodel.update(zqi=lambda:'ta',zqj=lambda:'rb')
    assert evaluate(probe,oldmodel)==[False]
    return dict(cases=rows,old_quote_not_automatically_substituted=True,physical_content_evaluated=False)


def alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(x for x in source['units'] if x['id']=='einstein-1905:u0236')
    math=next(x for x in source['math'] if x['id']=='M0390')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0390',math_sha256=math['sha256'],
        status='partial_density_formula_with_shared_coordinate_units',definitions=['seoz','seoy','seou','sens'])])


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    for p in (FULL,CORE):
        doc=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('-basis-v1.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            formatted=format_graph(doc,notation);assert parse(formatted)==parse(transcribe(formatted,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    paths=set(files)|{PARENT,'data/einstein-sustained-assistance-basis-v1.json','data/density-formula-review-v5.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','tests/test_density_units.py','docs/density-units-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_density_units','check_density_units','compose_density_interpretation','compose_local_density',
        'compose_additive_charge','compose_origin_clock','compose_limits','compose_roundtrip_speed','compose_emitted_light',
        'check_coordinate_correspondence','check_described_appraisals','check_rod_setup','check_plane_waveforms','check_real_products','check_moving_light_trip',
        'check_field_equations','check_tau_differential','check_angle_composition'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','integration_audit','polynomial_proofs'))
    return dict(status='partial_density_formula_with_shared_coordinate_units',document=FULL,basis_audits=audits,
        structure=structural_checks(),routing=routing_checks(),arithmetic=arithmetic_checks(),attribution=attribution_checks(),
        roundtrips=True,cli_parse=True,alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Density units reconnected and routing, scaling and quotation checked',flush=True)


if __name__=='__main__':main()
