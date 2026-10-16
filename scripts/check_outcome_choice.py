"""Check quantifier order, nondeterministic results and fixed comparison scope."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,FunctionValue,SequenceValue,Content
from noema.diagnostic_short_circuit import lower
from noema.script import transcribe
from scripts.compose_outcome_choice import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,MODEL,PROVIDERS,FIELDS,MEANINGS,build
from scripts.compose_qualified_utterance import closure
from scripts.check_unilateral_decision import arithmetic,structure as parent_structure,oracle as binary_oracle
from scripts.check_rod_setup import guarded

REPORT=ROOT/'reports/outcome-choice-v1.json'
METHODS=('method0','method1','method2','method3')
RESPONSES=('response0','response1')
OUTCOMES=('outcome0','outcome1','outcome2')
DOMAIN=('holder','target','process','cause')+METHODS+RESPONSES+OUTCOMES+('outside',)
SCENES=('before','after','outside')
REFS=' '.join(('k jdom'+n+'[]' if t.startswith('j[') else 'p jdom'+n) for n,t in MODEL)
SOURCE_REFS=' '.join('k jdosreference[]' if n=='reference' else 'p jdos'+n for n,t in FIELDS)
SOURCE_CODES=' '.join('r[k jdosreference[]]' if n=='reference' else 'r[p jdos'+n+']' for n,t in FIELDS)


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def sequence(items):return SequenceValue(tuple(items),json.dumps('individual'))


def evaluate(doc,values,indices=None,*,short=True,memoize=True):
    if indices is not None:
        doc=deepcopy(doc);doc['statements']=[doc['statements'][i] for i in indices]
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    values={n:values[n] for n in names}
    if short:doc,values=lower(doc,values)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=12_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def generic_fixture(path=LIBRARY):
    doc=parse(text(path));doc['statements']=[]
    extra=''.join('r jdom'+n+('[] '+t if t.startswith('j[') else t[1:])+'.' for n,t in MODEL)
    extra+='r jdomwanted[] a.'
    queries=['k '+n+'['+REFS+']' for n in ('rqqa','rqqd','rqqe')]
    queries+=['k rqqc[k jdomwanted[] '+REFS+']']
    return parse(format_graph(doc,'compact')+extra+''.join('q['+q+'].' for q in queries))


def model(doc,cells,*,count=2,variant='baseline'):
    methods=METHODS[:len(cells)];responses=RESPONSES;outcomes=OUTCOMES[:count]
    def listed(name):
        items=dict(methods=methods,responses=responses,outcomes=outcomes)[name]
        if variant=='empty_'+name:items=()
        if variant=='duplicate_'+name:items=items+items[:1]
        if variant=='missing_'+name:items=items[:-1]
        if variant=='reverse_lists':items=tuple(reversed(items))
        return sequence(items)
    def possible(method,response,outcome):
        if variant=='unknown_possible':raise ValueError('unknown possible')
        if method not in methods or response not in responses:return False
        if variant=='outside_result' and (method,response,outcome)==(methods[0],responses[0],'outside'):return True
        return outcome in outcomes and bool(cells[methods.index(method)][responses.index(response)]&(1<<outcomes.index(outcome)))
    def checked(method,response):
        if variant=='unknown_checked':raise ValueError('unknown checked')
        return variant!='unchecked' or (method,response)!=(methods[-1],responses[-1])
    values=guarded(doc);values.update(arithmetic())
    values.update(jdommethods=lambda:listed('methods'),jdomresponses=lambda:listed('responses'),jdomoutcomes=lambda:listed('outcomes'),
        jdommethodscope=lambda x:x in methods,jdomresponsescope=lambda x:x in responses,jdomoutcomescope=lambda x:x in outcomes,
        jdompossible=possible,jdomchecked=checked,jdomwanted=lambda:outcomes[0])
    return values


def oracle(cells,count):
    valid=all(mask>0 and mask<(1<<count) for row in cells for mask in row)
    uniform=[any(all(mask==(1<<wanted) for mask in row) for row in cells) for wanted in range(count)]
    hindsight=all(all(any(row[response]==(1<<wanted) for row in cells) for response in range(2)) for wanted in range(count))
    return [valid,valid and count>=2 and all(uniform),valid and count>=2 and hindsight,valid and uniform[0]]


@lru_cache(None)
def source_fixture(path=LIBRARY):
    doc=parse(text(path));doc['statements']=[]
    extra=''.join('r jdos'+n+('[] d' if n=='reference' else t[1:])+'.' for n,t in FIELDS)
    extra+='r jdostarget[] a.r jdosssecond[a] e.r jdosskind[a] c.r jdossprospects[a d d] c.r jdossanchor[] d.r jdossend[] d.'
    content='t[c[k hzhu['+SOURCE_REFS+']][k jdostarget[]]][k jdossend[]]'
    quote='k hzhw[r b[k jdostarget[]] r b[p jdosskind] r b[r[p jdosssecond]] r b[k jdossanchor[]] r b[p jdossprospects] '+SOURCE_CODES+']'
    literal='r b[c[p hzhk][k jdostarget[] p jdosskind r[c[p hzhu]['+SOURCE_REFS+']] r[p jdosssecond] k jdossanchor[] p jdossprospects]]'
    return parse(format_graph(doc,'compact')+extra+'q['+content+'].q[e['+quote+']['+literal+']].q[s['+quote+']].')


def source_model(doc,variant='baseline'):
    values=guarded(doc);values.update(arithmetic())
    base=((1,1),(2,2),(4,4));after=((1,2),(2,4),(4,1))
    def component(name,holder,target,point):
        selected=base if point=='before' or variant in ('continues','expanded_goals_after') else after
        if variant=='already_free':selected=after
        mode={'invalid_after':'missing_responses','unchecked_after':'unchecked','outside_after':'outside_result',
            'unknown_possible_after':'unknown_possible'}.get(variant,'baseline') if point=='after' else 'baseline'
        interpretation=model(doc,selected,count=3,variant=mode)
        fn=interpretation['jdom'+name]
        if name in ('methods','responses','outcomes'):
            if name=='outcomes' and point=='after' and variant=='changed_goals_after':return sequence(OUTCOMES[:2])
            if name=='outcomes' and point=='after' and variant=='expanded_goals_after':return sequence(OUTCOMES+('outside',))
            return fn()
        parameter_count={'methodscope':1,'responsescope':1,'outcomescope':1,'possible':3,'checked':2}[name]
        if name=='checked' and (holder,target)!=('holder','target'):fn=lambda *args:False
        if name=='outcomescope' and point=='after' and variant=='changed_goals_after':fn=lambda x:x in OUTCOMES[:2]
        if name=='outcomescope' and point=='after' and variant=='expanded_goals_after':fn=lambda x:x in OUTCOMES+('outside',)
        return FunctionValue(tuple('individual' for _ in range(parameter_count)),'truth',fn)
    for name,sort in MODEL:
        values['jdos'+name]=lambda holder,target,point,n=name:component(n,holder,target,point)
    values.update(jdosreference=lambda:'before',jdostarget=lambda:'outside' if variant=='wrong_target' else 'target',
        jdossanchor=lambda:'before',jdossend=lambda:'after',jdosholders=lambda x:x=='holder',
        jdoshistory=lambda s:s in ('before','after'),jdosbefore=lambda a,b:(a,b)==('before','after'),
        jdosassessed=lambda h,t,s:(h,t)==('holder','target') and s in ('before','after'),
        jdostransitions=lambda p,a,b:(p,a,b)==('cause' if variant=='wrong_transition' else 'process','before','after'),
        jdosaffected=lambda t,p,a,b:(t,p,a,b)==('target','process','before','after'),
        jdosskind=lambda x:x=='cause',jdossprospects=lambda p,a,b:(p,a,b)==('cause','before','after'),
        jdosssecond=lambda t:Content(SCENES,(False,False,False)),
        dg=lambda p,s:variant!='cause_absent' and (p,s)==('cause','after'))
    expected=dict(kind='apply',function=dict(kind='function_ref',symbol='hzhu'),arguments=[
        dict(kind='call',symbol='jdosreference',arguments=[]) if n=='reference' else dict(kind='function_ref',symbol='jdos'+n) for n,t in FIELDS])
    values['g3']=lambda p,t,description,s:variant!='other_description' and (p,t,s)==('cause','target','after') and json.loads(description.syntax)==expected
    return values


@lru_cache(None)
def checks():
    doc=generic_fixture();count=0
    for flat in product(range(4),repeat=4):
        cells=(flat[:2],flat[2:]);actual=evaluate(doc,model(doc,cells));wanted=oracle(cells,2)
        assert actual==wanted,(cells,actual,wanted);count+=1
    examples=dict(three_outcomes=((1,1),(2,2),(4,4)),respond_after_observation=((1,2),(2,4),(4,1)),
        nondeterministic_failure=((3,1),(2,2),(4,4)),extra_uncertain_method=((1,1),(2,2),(4,4),(7,7)),
        constant=((1,1),(1,1),(1,1)),impossible_combination=((0,1),(2,2),(4,4)))
    rows={}
    for path in (LIBRARY,FULL):
        doc=generic_fixture(path);rows[path]={}
        for name,cells in examples.items():
            actual=evaluate(doc,model(doc,cells,count=3));assert actual==oracle(cells,3),(name,actual)
            rows[path][name]=actual
    doc=generic_fixture();cells=examples['three_outcomes'];invalid={}
    for variant in tuple(prefix+name for prefix in ('empty_','duplicate_','missing_') for name in ('methods','responses','outcomes'))+('unchecked','outside_result'):
        actual=evaluate(doc,model(doc,cells,count=3,variant=variant));assert actual==[False]*4,(variant,actual)
        invalid[variant]=actual
    assert evaluate(doc,model(doc,cells,count=3,variant='reverse_lists'))==[True]*4
    assert evaluate(doc,model(doc,((1,1),(1,1)),count=1))==[True,False,False,True]
    binary=0
    for table in range(16):
        cells=tuple(tuple(1<<int(bool(table&(1<<(own+2*other)))) for other in range(2)) for own in range(2))
        actual=evaluate(doc,model(doc,cells),indices=(1,))[0]
        assert actual==binary_oracle(2,table,0)[1];binary+=1
    for cells in (((1,1),(2,2)),((1,2),(2,1))):
        assert evaluate(doc,model(doc,cells),short=False,memoize=False)==oracle(cells,2)
    source={}
    expected={n:[False,True,False] for n in ('already_free','continues','invalid_after','unchecked_after','outside_after','wrong_target','wrong_transition','expanded_goals_after')}
    expected.update(baseline=[True,True,True],changed_goals_after=[True,True,True],cause_absent=[True,True,False],other_description=[True,True,False])
    for path in (LIBRARY,FULL):
        doc=source_fixture(path);source[path]={}
        for variant,wanted in expected.items():
            actual=evaluate(doc,source_model(doc,variant));assert actual==wanted,(path,variant,actual)
            source[path][variant]=actual
        def forbidden(*args):raise AssertionError('Quote construction evaluated its content')
        assert evaluate(doc,{n:forbidden for n in source_model(doc)},indices=(1,))==[True]
    refused=[]
    try:evaluate(doc,source_model(doc,'unknown_possible_after'),indices=(0,))
    except ValueError as exc:assert 'unknown possible' in str(exc);refused.append('unknown_possible_after')
    else:raise AssertionError('Unknown postcondition was accepted')
    doc=generic_fixture()
    for variant in ('unknown_possible','unknown_checked'):
        try:evaluate(doc,model(doc,examples['three_outcomes'],count=3,variant=variant))
        except ValueError as exc:assert 'unknown' in str(exc);refused.append(variant)
        else:raise AssertionError(variant)
    return dict(exhaustive_two_outcome_relations=count,multivalued_cases=rows,invalid_configurations=invalid,
        deterministic_binary_compatibility_cases=binary,source_contrasts=source,unknown_inputs_refused=refused,
        list_permutation_checked=True,singleton_not_choice=True,unlowered_uncached_cases=2,
        quotation_nonfactive=True,actual_model_transition_and_causality_executed=True)


def structure():
    inherited=parent_structure();old=parse(text(PARENT));doc=parse(text(FULL));basis=json.loads(text(BASIS))
    assert doc['declarations'][:len(old['declarations'])]==old['declarations'] and doc['statements']==old['statements']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)==set(basis['definitions'])
    assert {d['name']:{k:d[k] for k in ('parameters','result')} for d in added}==basis['new_signatures']
    assert parse(text(LIBRARY))['declarations']==closure(doc,['rqqe','hzhw'])
    return dict(inherited_basis_checked=inherited['inherited_basis_checked'],previous_statements_preserved=len(old['statements']),
        previous_declarations_preserved=True,new_definitions=len(added),new_primitives=0,new_assertions=0)


def build_report():
    files=build()
    for name,body in files.items():assert text(name)==body,name
    for path in (FULL,LIBRARY):
        doc=parse(text(path))
        for notation in ('full','compact'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    alignment=deepcopy(json.loads(text('reports/unilateral-decision-v1.json'))['alignment'])
    for row in alignment['segments']:
        row['definitions']=list(MEANINGS);row['status']='partial_finite_multivalued_outcome_control'
        row['remaining'].append('available methods and others response mechanism grounded in the same political relation')
    paths=set(files)|{PARENT,PARENT_BASIS,'reports/unilateral-decision-v1.json',
        'docs/outcome-choice-v1.md','tests/test_outcome_choice.py','artifacts/written-units-v1/kant-1784.json'}
    paths.update('scripts/'+n+'.py' for n in ('compose_outcome_choice','check_outcome_choice','compose_relational_departure',
        'check_unilateral_decision','check_relational_departure','check_quoted_outcomes','compose_origin_clock','compose_limits',
        'compose_situated_criticism','compose_qualified_utterance','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','meaning_basis','script','constructed',
        'constructed_discourse','constructed_semantics','guarded_ranked_semantics','diagnostic_short_circuit'))
    return dict(status='partial_multivalued_control_with_fixed_outcome_scope',document=FULL,
        finite=checks(),structure=structure(),alignment=alignment,roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Multivalued choice, quantifier order and causal composition checked',flush=True)


if __name__=='__main__':main()
