"""Check nonfactive construction/attribution and explicit evaluation of causal quotations."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from itertools import product
from noema.grammar import parse as legacy_parse
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,evaluate_document
from noema.finite_semantics import Content as LegacyContent
from noema.diagnostic_short_circuit import lower
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_quoted_outcomes import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,MEANINGS,FIELDS,build
from scripts.compose_qualified_utterance import closure
from scripts import check_causal_outcome_contrast as previous

REPORT=ROOT/'reports/quoted-outcomes-v1.json'
DOMAIN=previous.DOMAIN+('node','author','scope','other')
SCENES=previous.SCENES
REFS={'target':'k jcotarget[]','kind':'p jcokind','first':'r[p jcoleft]','second':'r[p jcoright]',
    'anchor':'k jcoanchor[]','prospects':'p jcoprospects'}


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


@lru_cache(None)
def fixture(path=LIBRARY,variant='normal'):
    doc=parse(text(path));doc['statements']=[]
    extra=[d for d in previous.fixture(previous.CORE)['declarations'] if d['name'].startswith('jco')]
    names={d['name'] for d in doc['declarations']};assert not names&{d['name'] for d in extra}
    doc['declarations']+=deepcopy(extra)
    declarations='''r jqrnode[] a.r jqrauthor[] a.r jqrscope[] a.r jqrcontext[] d.r jqrtargetalias[] a.
r jqrrecords[a a i b[c] a d] c.'''
    refs=REFS.copy()
    if variant=='alias_target':refs['target']='k jqrtargetalias[]'
    if variant=='swapped_results':refs['first'],refs['second']=refs['second'],refs['first']
    if variant=='other_result_description':refs['first']='r[p jcoalias]'
    codes=' '.join('r b['+refs[n]+']' for n,t in FIELDS)
    assembled='k hzhl['+codes+']'
    literal='r b[c[p hzhk]['+' '.join(REFS[n] for n,t in FIELDS)+']]'
    direct='k hzhk['+' '.join(REFS[n] for n,t in FIELDS)+']'
    report='k hzhm[k jqrnode[] k jqrauthor[] '+codes+' k jqrscope[] k jqrcontext[] p jqrrecords]'
    return parse(format_graph(doc,'compact')+declarations+'q[e['+assembled+']['+literal+']].q[s['+assembled+']].q['+direct+'].q['+report+'].')


def adapt(callback):
    def call(*args):
        value=callback(*args)
        return Content(value.situations,value.values) if isinstance(value,LegacyContent) else value
    return call


def model(doc,bits=(True,True,True,False,False,False),variant='baseline',reported=True):
    result={n:adapt(f) for n,f in previous.model(doc,bits,variant).items()}
    expected=doc['statements'][0]['body']['arguments'][1]['body']
    def records(node,author,code,scope,context):
        if variant=='unknown_record':raise ValueError('unknown attribution record')
        return reported and (node,author,scope,context)==('node','author','scope','outside') and code.rank==1 and json.loads(code.syntax)==expected
    result.update(jqrnode=lambda:'other' if variant=='wrong_node' else 'node',
        jqrauthor=lambda:'other' if variant=='wrong_author' else 'author',
        jqrscope=lambda:'other' if variant=='wrong_scope' else 'scope',
        jqrcontext=lambda:'now' if variant=='wrong_report_context' else 'outside',jqrtargetalias=lambda:'target',jqrrecords=records)
    return result


def evaluate(doc,primitives,*,indices=None,short=True,memoize=True):
    if indices is not None:
        doc=deepcopy(doc);doc['statements']=[doc['statements'][i] for i in indices]
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    primitives={n:primitives[n] for n in names}
    if short:doc,primitives=lower(doc,primitives)
    return [x['value'] for x in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives,
        max_steps=5_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def checks():
    count=0;rows={}
    for path in (LIBRARY,FULL):
        doc=fixture(path)
        selected=list(product((False,True),repeat=6)) if path==LIBRARY else [
            (True,True,True,False,False,False),(True,True,True,True,True,True),
            (False,False,False,False,False,False),(True,False,True,True,False,True)]
        for bits in selected:
            actual=all(bits[:3]) and not all(bits[3:])
            for reported in (False,True):
                result=evaluate(doc,model(doc,bits,reported=reported));assert result==[True,actual,actual,reported],(path,bits,result)
                count+=1
        contrasts={n:[True,True,True,False] for n in ('wrong_node','wrong_author','wrong_scope','wrong_report_context')}
        contrasts.update(second_activity=[True,False,False,True],right_true_only=[True,True,True,True])
        rows[path]={}
        for variant,wanted in contrasts.items():
            result=evaluate(doc,model(doc,variant=variant));assert result==wanted,(path,variant,result);rows[path][variant]=result
        for variant,wanted in (('alias_target',[False,True,True,False]),('swapped_results',[False,False,True,False]),
            ('other_result_description',[False,False,True,False])):
            other=fixture(path,variant);result=evaluate(other,model(other));assert result==wanted,(path,variant,result);rows[path][variant]=result
        def forbidden(*args):raise AssertionError('Quotation construction or attribution executed content')
        values=model(doc)
        # Only the attribution coordinates and the relation may be evaluated.
        for name in values:
            if name not in ('jqrnode','jqrauthor','jqrscope','jqrcontext','jqrrecords'):values[name]=forbidden
        assert evaluate(doc,values,indices=(0,3))==[True,True]
        assert evaluate(doc,values,indices=(0,3),short=False,memoize=False)==[True,True]
    doc=fixture();refused=[]
    for variant,indices in (('unknown_effect',(1,)),('unknown_cause',(1,)),('unknown_record',(3,))):
        try:evaluate(doc,model(doc,variant=variant),indices=indices)
        except ValueError as exc:assert 'unknown' in str(exc);refused.append(variant)
        else:raise AssertionError(variant)
    for variant in ('baseline','second_activity'):
        expected=evaluate(doc,model(doc,variant=variant))
        assert evaluate(doc,model(doc,variant=variant),short=False,memoize=False)==expected
    return dict(truth_and_attribution_cases=count,contrasts=rows,construction_and_attribution_do_not_execute_content=True,
        quoted_and_direct_evaluation_agree=True,unknown_inputs_refused=refused,unlowered_uncached_examples=4,
        report_context_distinct_from_modal_anchor=True)


def rejection_checks():
    doc=fixture();body=format_graph(doc,'compact');rejected=[]
    tests={
        'rank_zero_function':body.replace('r b[p hzhk]','r[p hzhk]'),
        'wrong_target_type':body.replace('r b[k jcotarget[]]','r b[k jcoanchor[]]'),
        'missing_nested_result_quote':body.replace('r b[r[p jcoleft]]','r b[p jcoleft]'),
        'implicit_rank_promotion':body.replace('r b[k jcotarget[]]','r[k jcotarget[]]'),
    }
    # Formatting normalizes variable names but leaves these closed expressions.
    for name,bad in tests.items():
        assert bad!=body,name
        try:parse(bad)
        except ValueError:rejected.append(name)
        else:raise AssertionError(name)
    try:legacy_parse(text(FULL))
    except ValueError:rejected.append('legacy_parser_does_not_silently_adopt_016')
    else:raise AssertionError('Legacy parser accepted an opt-in edition')
    return rejected


def structure():
    old=legacy_parse(text(PARENT));new=parse(text(FULL));basis=json.loads(text(BASIS))
    inherited=audit_basis(old,json.loads(text(PARENT_BASIS)))
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements']==old['statements']
    added=new['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)==set(basis['definitions'])
    assert {d['name']:{k:d[k] for k in ('parameters','result')} for d in added}==basis['new_signatures']
    assert parse(text(LIBRARY))['declarations']==closure(new,['hzhl','hzhm'])
    return dict(inherited_basis_signature_coverage=inherited['signature_and_documentation_coverage'],
        inherited_declarations_and_15_statements_unchanged=True,new_definitions=2,new_primitives=0,new_assertions=0,
        explicit_edition='0.16',new_definition_signatures_documented=True)


def build_report():
    files=build()
    for name,body in files.items():assert text(name)==body,name
    for path in (FULL,LIBRARY):
        doc=parse(text(path))
        for notation in ('full','compact'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    alignment=deepcopy(json.loads(text('reports/causal-outcome-contrast-v1.json'))['alignment'])
    for row in alignment['segments']:
        row['definitions']=['hzhk','hzhl','hzhm'];row['status']='partial_quoted_causal_contrast_bridge'
        row['remaining'].append('concrete source concept descriptions and an actual author attribution')
    paths=set(files)|{PARENT,PARENT_BASIS,'reports/causal-outcome-contrast-v1.json',previous.CORE,previous.LIBRARY,
        'docs/quoted-outcomes-v1.md','tests/test_quoted_outcomes.py','artifacts/written-units-v1/kant-1784.json'}
    paths.update('scripts/'+n+'.py' for n in ('compose_quoted_outcomes','check_quoted_outcomes','compose_causal_outcome_contrast',
        'check_causal_outcome_contrast','compose_origin_clock','compose_limits','compose_situated_criticism',
        'compose_qualified_utterance','check_described_appraisals','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','meaning_basis','script',
        'constructed','constructed_discourse','constructed_semantics','guarded_ranked_semantics','diagnostic_short_circuit'))
    return dict(status='explicit_016_quote_bridge_not_completed_source_attribution',document=FULL,finite=checks(),
        rejected_inputs=rejection_checks(),structure=structure(),alignment=alignment,roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Causal quotation construction, attribution and explicit evaluation checked',flush=True)


if __name__=='__main__':main()
