"""Check practical ability without laundering prohibition, aims, or actuality."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.diagnostic_short_circuit import lower
from noema.script import transcribe
from scripts.compose_norm_bound_choice import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,READING,NORM,MODEL,PROVIDERS,MEANINGS,build
from scripts.compose_qualified_utterance import closure
from scripts.check_outcome_choice import model as outcome_model,DOMAIN as OLD_DOMAIN,SCENES,REFS as MODEL_REFS,structure as parent_structure

REPORT=ROOT/'reports/norm-bound-choice-v1.json'
DOMAIN=OLD_DOMAIN+('source','role','other_source','other_role')
NORM_REFS=' '.join('p jdn'+n if t.startswith('h[') else 'k jdn'+n+'[]' for n,t in NORM)
BASE_REFS=NORM_REFS+' '+MODEL_REFS
ITEM_REFS='k jdnmethod[] k jdnwanted[] '+BASE_REFS


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,values,indices=range(6),*,short=True,memoize=True):
    doc=deepcopy(doc);doc['statements']=[doc['statements'][i] for i in indices]
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'};values={n:values[n] for n in names}
    if short:doc,values=lower(doc,values)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=8_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def fixture(path=LIBRARY,alias=False):
    doc=parse(text(path));doc['statements']=[]
    extra=''.join('r jdom'+n+('[] '+t if t.startswith('j[') else t[1:])+'.' for n,t in MODEL)
    extra+=''.join('r jdn'+n+(t[1:] if t.startswith('h[') else '[] '+t)+'.' for n,t in NORM if n!='code')
    extra+='''r jdnmethod[] a.r jdnwanted[] a.r jdnaims[a a i[h[j[a]] e] j[a] d] c.r jdnactual[j[a] d] c.
d jdncontent[bindings j[a]] e[b point[k jdnactual[v bindings v point]]].
d jdnalias[bindings j[a]] e[b point[k jdnactual[v bindings v point]]].'''
    extra+='d jdncode[] i[h[j[a]] e][r[p '+('jdnalias' if alias else 'jdncontent')+']].'
    queries=['k rqqi['+BASE_REFS+']','k rqqj['+ITEM_REFS+']','k rqqk['+ITEM_REFS+']',
        'k rqql['+ITEM_REFS+' p jdnaims]','k rqqm['+BASE_REFS+' p jdnaims]','k rqqn['+BASE_REFS+']']
    queries+=['e[r['+queries[4]+']][r['+queries[4]+']]','t[c[s[k jdncode[]]][l[a][k jdnperson[] k jdntarget[] k jdnwanted[]]]][k jdnpoint[]]']
    return parse(format_graph(doc,'compact')+extra+''.join('q['+q+'].' for q in queries))


def model(doc,bits=(True,True,False,True,True),variant='baseline',actual=None):
    known,banned,permitted,aim,power=bits
    values=outcome_model(doc,((1,1),(2,2)) if power else ((1,2),(2,1)),variant='unchecked' if variant=='model_unchecked' else 'baseline')
    values.update(jdnsource=lambda:'source',jdnperson=lambda:'holder',jdntarget=lambda:'target',jdnrole=lambda:'role',
        jdnpoint=lambda:'before',jdnmethod=lambda:'method0',jdnwanted=lambda:'outcome0')
    def description(code,alias=False):
        return json.loads(code.syntax)==dict(kind='function_ref',symbol='jdnalias' if alias else 'jdncontent') and code.rank==0
    def checked(source,person,role,code,bindings,point):
        if variant=='unknown_norm':raise ValueError('unknown normative assessment')
        if variant=='unchecked_other_outcome' and bindings.items[-1]=='outcome1':return False
        return known and (source,person,role,point)==('source','holder','role','before') and (
            description(code) or description(code,True)) and bindings.items in (('holder','target','outcome0'),('holder','target','outcome1'))
    def match(source,person,role,code,bindings,point):
        expected=('other_source' if variant=='other_source' else 'source',
            'target' if variant=='other_addressee' else 'holder','other_role' if variant=='other_role' else 'role',
            'after' if variant=='other_point' else 'before')
        args={'other_target':('holder','outside','outcome0'),'other_outcome':('holder','target','outcome1'),
            'swapped_bindings':('target','holder','outcome0'),'extra_binding':('holder','target','outcome0','outside')}.get(variant,('holder','target','outcome0'))
        return (source,person,role,point)==expected and description(code,variant=='other_description') and bindings.items==args
    def required(source,person,role,code,bindings,sign,point):
        if variant=='unknown_required':raise ValueError('unknown requirement')
        return match(source,person,role,code,bindings,point) and (banned if not sign else variant=='contradictory_requirements')
    def allowed(source,person,role,code,bindings,sign,point):
        return permitted and sign and match(source,person,role,code,bindings,point)
    def aims(person,method,code,bindings,point):
        if variant=='unknown_aim':raise ValueError('unknown aim')
        return aim and (person,method,point)==('target' if variant=='other_goal_person' else 'holder',
            'method1' if variant=='other_goal_method' else 'method0','after' if variant=='other_goal_point' else 'before') and (
            description(code,variant=='other_goal_description')) and bindings.items==(
                'holder','outside' if variant=='other_goal_target' else 'target','outcome0')
    def content(bindings,point):
        if actual is None:raise AssertionError('Norm, goal or ability evaluation executed the actual content')
        return bool(actual)
    values.update(jdnnormchecked=checked,jdnrequired=required,jdnallowed=allowed,jdnaims=aims,jdnactual=content)
    return values


def expected(bits):
    known,banned,permitted,aim,power=bits
    prohibited=known and power and banned
    return [known,prohibited,known and power and permitted and not banned,prohibited and aim,prohibited and aim,known and not(power and banned)]


def contextual_checks(path):
    doc=fixture(path);doc=deepcopy(doc);doc['statements']=[]
    extra=''.join('r jdns'+n+t[1:]+'.' for n,t in PROVIDERS)
    query='k rqqo['+NORM_REFS+' '+' '.join('p jdns'+n for n,t in PROVIDERS)+' p jdnaims]'
    doc=parse(format_graph(doc,'compact')+extra+'q['+query+'].')
    results={}
    for variant in ('baseline','other_person_model','other_target_model','other_point_model'):
        values=model(doc);seen=[]
        expected_context={'other_person_model':('target','target','before'),'other_target_model':('holder','outside','before'),
            'other_point_model':('holder','target','after')}.get(variant,('holder','target','before'))
        for name,sort in MODEL:
            def provider(person,target,point,n=name,t=sort):
                seen.append((n,person,target,point));fn=values['jdom'+n]
                if t.startswith('j['):return fn()
                count=3 if n=='possible' else 2 if n=='checked' else 1
                if n=='checked' and (person,target,point)!=expected_context:fn=lambda *args:False
                return FunctionValue(tuple('individual' for _ in range(count)),'truth',fn)
            values['jdns'+name]=provider
        actual=evaluate(doc,values,indices=(0,));assert actual==[variant=='baseline'],(variant,actual)
        assert {n for n,p,t,s in seen}=={n for n,t in MODEL}
        assert {(p,t,s) for n,p,t,s in seen}=={('holder','target','before')}
        results[variant]=actual
    return results


@lru_cache(None)
def checks():
    doc=fixture();count=0
    for bits in product((False,True),repeat=5):
        actual=evaluate(doc,model(doc,bits));assert actual==expected(bits),(bits,actual,expected(bits));count+=1
    variants={n:[True,False,False,False,False,True] for n in ('other_source','other_addressee','other_role','other_point','other_target',
        'swapped_bindings','extra_binding','other_description')}
    variants.update({n:[True,True,False,False,False,False] for n in ('other_goal_person','other_goal_method','other_goal_point','other_goal_target','other_goal_description')})
    variants.update(baseline=expected((True,True,False,True,True)),contradictory_requirements=expected((True,True,False,True,True)),
        other_outcome=[True,False,False,False,False,False],unchecked_other_outcome=[False,True,False,True,True,False],model_unchecked=[False]*6)
    contrasts={}
    for path in (LIBRARY,FULL):
        doc=fixture(path);contrasts[path]={}
        for variant,wanted in variants.items():
            actual=evaluate(doc,model(doc,variant=variant));assert actual==wanted,(path,variant,actual,wanted)
            contrasts[path][variant]=actual
        aliasdoc=fixture(path,True)
        assert evaluate(aliasdoc,model(aliasdoc))==[True,False,False,False,False,True]
        def forbidden(*args):raise AssertionError('Quotation construction evaluated input')
        assert evaluate(doc,{n:forbidden for n in model(doc)},indices=(6,))==[True]
        for truth in (False,True):
            values=model(doc,actual=truth)
            assert evaluate(doc,values)==expected((True,True,False,True,True))
            assert evaluate(doc,values,indices=(7,))==[truth]
            assert evaluate(aliasdoc,model(aliasdoc,actual=truth),indices=(7,))==[truth]
    refused=[]
    for variant in ('unknown_norm','unknown_required','unknown_aim'):
        try:evaluate(doc,model(doc,variant=variant))
        except ValueError as exc:assert 'unknown' in str(exc);refused.append(variant)
        else:raise AssertionError(variant)
    doc=fixture()
    for bits in ((True,True,False,True,True),(True,False,True,True,False)):
        assert evaluate(doc,model(doc,bits),short=False,memoize=False)==expected(bits)
    context={path:contextual_checks(path) for path in (LIBRARY,FULL)}
    return dict(truth_combinations=count,contrasts=contrasts,contextual_models=context,same_truth_aliases_not_substituted=True,
        quote_construction_nonfactive=True,actual_content_truth_independent=True,unlowered_uncached_cases=2,
        unknown_inputs_refused=refused,actual_outcome_control_and_norm_definitions_executed=True)


def structure():
    inherited=parent_structure();old=parse(text(PARENT));doc=parse(text(FULL));basis=json.loads(text(BASIS))
    assert doc['declarations'][:len(old['declarations'])]==old['declarations'] and doc['statements']==old['statements']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)==set(basis['definitions'])
    assert {d['name']:{k:d[k] for k in ('parameters','result')} for d in added}==basis['new_signatures']
    assert parse(text(LIBRARY))['declarations']==closure(doc,['rqqk','rqqn','rqqo'])
    reading=json.loads(text(READING))
    for source in reading['sources']:
        assert hashlib.sha256((ROOT/source['artifact']).read_bytes()).hexdigest()==source['sha256']
    return dict(inherited_basis_checked=inherited['inherited_basis_checked'],previous_statements_preserved=len(old['statements']),
        previous_declarations_preserved=True,new_definitions=len(added),new_primitives=0,new_assertions=0,primary_sources_pinned=2)


def build_report():
    files=build()
    for name,body in files.items():assert text(name)==body,name
    for path in (FULL,LIBRARY):
        doc=parse(text(path))
        for notation in ('full','compact'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    paths=set(files)|{PARENT,PARENT_BASIS,READING,'reports/outcome-choice-v1.json',
        'docs/norm-bound-choice-v1.md','tests/test_norm_bound_choice.py'}
    paths.update(source['artifact'] for source in json.loads(text(READING))['sources'])
    paths.update('scripts/'+n+'.py' for n in ('compose_norm_bound_choice','check_norm_bound_choice','compose_outcome_choice',
        'check_outcome_choice','check_unilateral_decision','check_relational_departure','check_quoted_outcomes','compose_origin_clock',
        'compose_limits','compose_situated_criticism','compose_qualified_utterance','compose_policy_norms','compose_parameterized_goals','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','meaning_basis','script','constructed',
        'constructed_discourse','constructed_semantics','guarded_ranked_semantics','diagnostic_short_circuit'))
    return dict(status='normative_practical_purposive_diagnostics_without_new_source_claim',document=FULL,
        finite=checks(),structure=structure(),alignment={'segments':[]},roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Norms, purposes and practical choice checked independently',flush=True)


if __name__=='__main__':main()
