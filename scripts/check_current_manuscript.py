"""Evaluate the current manuscript schema and expose its still-open bindings."""
from copy import deepcopy
from functools import lru_cache
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_dispositional_resistance import ROOT,CORE,SOURCE,REVIEW
from scripts.check_caused_choice import evaluate
from scripts.check_thinking_disposition import code_is,forbidden
from scripts import check_policy_integration as policy
from scripts import check_property_apposition as apposition
from scripts import check_cover_reference as cover

REPORT=ROOT/'reports/current-manuscript-v1.json'
LABELS=policy.LABELS+('current_family','apposition')
CONTRASTS=('wrong_regime','missing_mention','crossed','no_clarification','old_depiction',
           'missing_permission','remaining_false')
RESPONSE_PRIMITIVES=('ibaassessed','ibaload','ibadeformation','ibcprospects')


@lru_cache(maxsize=1)
def schema():
    return json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))['templates'][0]['symbol']


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(policy.fixture());names={d['name']:d for d in doc['declarations']}
    source=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for declaration in source['declarations']:
        name=declaration['name']
        if name not in names:doc['declarations'].append(deepcopy(declaration));names[name]=declaration
        else:assert names[name]==declaration,name
    doc['statements'][0]['body']['symbol']=schema()
    doc=parse(format_graph(doc,'compact')+'''
q[k ibcfamily[r b[p iahinner]]].
q[k ibbapposition[r b[p iahinner]]].
''')
    actual={d['name']:d for d in doc['declarations']}
    assert all(actual[d['name']]==d for d in source['declarations'])
    return doc


def model(variant='baseline',calls=None):
    p,domain,scenes=policy.model(variant,calls)
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    p.update(cover.reference_model('wrong_regime' if variant=='wrong_regime' else 'baseline',context='end'))
    nominal=apposition.source_model(variant=variant)
    for name in ('ibbgermnode','ibbdetailnode','ibbdenotes','ibbclarifies','ue'):
        p[name]=nominal[name]
    # Preserve the requested reference-model contrast: the nominal helper's
    # reference model supplies only its order relation, not its cover mapping.
    def presents(node,author,target,depiction,point):
        log('current_depiction',node,author,target,depiction,point)
        return (node,author,point)==('node','author','end') and code_is(target,'iahinner',1) and code_is(
            depiction,'ibadepiction' if variant=='old_depiction' else 'ibcdepiction',1)
    p['iahpresents']=presents
    for name in ('ibbdenotes','ibbclarifies','iazmapping'):
        previous=p[name]
        def traced(*args,_name=name,_previous=previous):
            log(_name,*args)
            return _previous(*args)
        p[name]=traced
    # A description is attributed. Its response conditions must never become
    # truth requirements of that attribution, even in the whole conditional.
    for name in RESPONSE_PRIMITIVES:
        def prohibited(*args,_name=name):
            log('unexpected_response_execution',_name,*args)
            raise AssertionError('Attributed response executed: '+_name)
        p[name]=prohibited
    domain+=tuple(x for x in ('cover','prior','prior_scope','germ','detail') if x not in domain)
    scenes+=tuple(x for x in ('low','high') if x not in scenes)
    return p,domain,scenes


def values(variant='baseline',indices=(0,),calls=None):
    p,domain,scenes=model(variant,calls)
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,budget=100_000_000)


def binding_audit():
    """Record executable diagnostic arguments without promoting them to text."""
    source=parse((ROOT/CORE).read_text(encoding='utf-8'))
    definition=next(d for d in source['declarations'] if d['name']==schema())
    current=fixture();query=current['statements'][0]['body']
    lookup={d['name']:d for d in current['declarations']}
    roles=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))['templates'][0]['parameter_roles']
    rows=[]
    for role,parameter,argument in zip(roles,definition['parameters'],query['arguments'],strict=True):
        referenced=sorted(_references(argument))
        rows.append(dict(role=role,variable=parameter['name'],sort=parameter['sort'],diagnostic_argument=argument,
            referenced_declarations={n:lookup[n]['kind'] for n in referenced},
            binding_status='diagnostic_interpretation_only'))
    root=next(d for d in source['declarations'] if d['name']==source['statements'][-1]['body']['symbol'])
    attribution=root['body']
    quoted_template=(attribution['kind']=='call' and attribution['symbol']=='iatreport' and
        attribution['arguments'][2]==dict(kind='quote',rank=2,body=dict(kind='function_ref',symbol=schema())))
    remaining=next(row for row in rows if row['role']=='remaining')['referenced_declarations']
    return dict(schema=schema(),parameters=rows,source_statement=source['statements'][-1],
        source_attribution_body=attribution,source_claim_is_still_template_attribution=quoted_template,
        remaining_is_still_external_relation=bool(remaining) and all(kind=='primitive' for kind in remaining.values()),
        limitation='Concrete test arguments instantiate the schema in a finite model; they do not supply the missing source meaning or bind the published attribution.')


@lru_cache(maxsize=1)
def checks():
    calls=[];baseline=values(indices=tuple(range(len(LABELS))),calls=calls)
    assert baseline==[True,True,True,False,True,True,True,True,True],baseline
    reached={call[0] for call in calls}
    assert {'current_depiction','ibbdenotes','ibbclarifies','iazmapping','appraisal','criterion','targets','remaining'}<=reached
    assert 'unexpected_response_execution' not in reached
    print('Current whole schema, premise witness and nonfactive appraisal: passed',flush=True)
    contrasts={}
    for variant in CONTRASTS:
        contrasts[variant]=values(variant)
        assert contrasts[variant]==[False],(variant,contrasts[variant])
        print(variant+': rejected',flush=True)
    try:values('unknown_reference')
    except ValueError as exc:
        assert 'Unknown nominal reference' in str(exc)
    else:raise AssertionError('Unknown reference was guessed')
    return dict(baseline=dict(zip(LABELS,baseline)),contrasts=contrasts,
        unknown_reference='raises_instead_of_guessing',reached_primitive_families=sorted(reached),
        response_conditions_executed=False)


def input_paths():
    return policy.input_paths()|{CORE,SOURCE,REVIEW,
        'scripts/check_current_manuscript.py','tests/test_current_manuscript.py','docs/current-manuscript-v1.md'}


def build_report(result=None):
    result=checks() if result is None else result
    return dict(status='current_manuscript_schema_evaluated_with_explicit_open_bindings',document=CORE,
        results=result,bindings=binding_audit(),source_definitions_replaced=[],
        scope='Whole current conditional including reference and apposition; cover growth and mechanical response remain attributed descriptions. No source-equivalence claim.',
        semantic_completion=False,counts_as_translated_coverage=False,
        input_sha256={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sorted(input_paths())})


def write_report():
    report=build_report()
    with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return report


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--report',action='store_true')
    cli.add_argument('--variant',default='baseline');args=cli.parse_args()
    if args.report:write_report()
    else:print(values(args.variant),flush=True)
