"""Evaluate the actual policy schema together with its causal and appraisal layers."""
from copy import deepcopy
from functools import lru_cache
import argparse
import hashlib
import json
import sys
from pathlib import Path
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from scripts.compose_policy_constraints import ROOT, CORE
from scripts.check_caused_choice import evaluate
from scripts.check_thinking_disposition import code_is, forbidden
from scripts import check_political_consequence as political
from scripts import check_self_benefit as benefit
from scripts import check_collective_conditional as collective
from scripts import check_public_reason_claim as permission

REPORT=ROOT/'reports/policy-integration-v1.json'
LABELS=('schema','premise_witness','appraisal','actual_benefit','beneficiaries','policy_inclusion','political_cause')


@lru_cache(maxsize=1)
def fixture():
    source=parse((ROOT/CORE).read_text(encoding='utf-8'))
    doc=deepcopy(source);doc['statements']=[]
    # Keep every source declaration byte-for-byte at the AST level. Only test
    # constants and policies from the previous concrete example are appended.
    names={d['name'] for d in doc['declarations']}
    for d in benefit.source_fixture()['declarations']+collective.source_fixture()['declarations']:
        if d['name'] not in names:
            doc['declarations'].append(deepcopy(d));names.add(d['name'])
    extra=parse(format_graph(doc,'compact')+'r jinormcases[d] c.d jipolicy[bindings j[a]] e[c[k iavtreatment[k jpsource[] k jpactor[] k jpoffice[] l[a][k jpperson[]] i[person a][e[v person][k jpperson[]]] p jinormcases]][v bindings]].')
    # jpnew is a fixture, never a source definition. Its content is the concrete
    # criterion, rather than a primitive boolean meaning "policy is realized".
    new=next(d for d in doc['declarations'] if d['name']=='jpnew')
    doc['declarations'].remove(new)
    doc['declarations'].extend(extra['declarations'][-2:-1])
    new['body']=extra['declarations'][-1]['body'];doc['declarations'].append(new)
    queries='''
q[k iayschema[r b[p iahinner] k jpsource[] k jpactor[] k jpoffice[] r[p jpold] r[p jpnew] p jpprobes p jpremaining]].
q[t[k iaqwitness[r b[p iahinner] k jpcommunity[]]][k wh[]]].
q[k iatappraisal[k jpactor[] r[p jpnew] k juanchor[]]].
q[k iatbenefit[k jpactor[] k jpactor[] r[p jpnew] k juanchor[] k juanchor[]]].
q[k iaxbeneficiaries[k jpactor[] r[p jpnew] k jpcommunity[] k wh[] k juanchor[]]].
q[k iaymeaning[k jpsource[] k jpactor[] k jpoffice[] r[p jpnew] k jpcommunity[] k wh[]]].
q[k iascausal[r b[p iahinner] k jpcommunity[] k jpstart[] k jpend[] k jpsource[] k jpactor[] k jpoffice[] r[p jpold] r[p jpnew] p jpprobes]].
'''
    doc=parse(format_graph(doc,'compact')+queries)
    actual={d['name']:d for d in doc['declarations']}
    assert all(actual[d['name']]==d for d in source['declarations'])
    return doc


def model(variant='baseline',calls=None):
    p,domain,scenes=political.source_model(
        variant='old_retained' if variant=='old_retained' else 'baseline',
        remaining=variant!='remaining_false')
    domain+=tuple(x for x in permission.DOMAIN if x not in domain)
    scenes+=('left','right')
    old=dict(p)
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    goals=('topicone','topictwo')
    def signature(assessor,actor,beneficiary,policy,recipe,context):
        log('appraisal',assessor,actor,beneficiary,policy,recipe,context)
        return (assessor,actor,beneficiary,context)==('government','government','government','political') and code_is(policy,'jpnew') and code_is(recipe,'iatbenefit',1)
    def outcomes(actor,policy,sign,context,outcome):
        return actor=='government' and code_is(policy,'jpnew') and context in ('outside','political') and outcome==(
            'normbase' if context=='outside' and sign else 'normchanged' if sign else 'normkept')
    p.update(juanchor=lambda:'political',
        iatgoals=lambda who,anchor:SequenceValue(goals if (who,anchor)==('government','political') else (), '"individual"'),
        iatscope=lambda who,anchor,goal:(who,anchor)==('government','political') and goal in goals,
        iatholds=lambda who,goal,point:who=='government' and (goal=='topicone' or goal=='topictwo' and point=='normbase' and variant!='no_benefit'),
        iatclassified=lambda who,goal,point:who=='government' and goal in goals,
        iatoutcomes=outcomes,
        iatviews=lambda *args:signature(*args[:-1]) and args[-1]=='outside',
        iatawareness=lambda *args:variant!='unrecognized' and signature(*args))
    permissions=permission.permission_model(allowed=1 if variant=='missing_permission' else 3)
    permissions.pop('aa');allow=permissions['h7b']
    permissions['h7b']=lambda *args:args[-1] in ('normbase','normchanged') and allow(*args)
    p.update(permissions)
    def required(source,actor,office,code,bindings,polarity,point):
        if code_is(code,'iavclaim'):
            log('criterion',source,actor,office,bindings.items,point)
            return variant!='missing_requirement' and (source,actor,office)==('norm','government','office') and bindings.items==('government','person') and polarity
        return old['h7k'](source,actor,office,code,bindings,polarity,point)
    def targets(actor,policy,community,anchor):
        log('targets',actor,policy,community,anchor)
        return (actor,community,anchor)==('government','community','end') and code_is(policy,'jpold' if variant=='wrong_target_policy' else 'jpnew')
    p.update(h7k=required,jinormcases=lambda point:point in ('normbase','normchanged'),
        iaxpeople=lambda *args:SequenceValue(('person',),'"individual"'),
        iaxscope=lambda actor,policy,community,anchor,person:targets(actor,policy,community,anchor) and person=='person',
        iaynormcases=lambda source,actor,office,policy,community,anchor,point:variant!='empty_normcases' and (source,office)==('norm','office') and targets(actor,policy,community,anchor) and point in ('normbase','normchanged'))
    # Independent judgments are evaluated in two separate comparison situations.
    # Existing reasoning relations in every other situation are preserved.
    def judge(point):return 'judgmentone' if point=='left' else 'judgmenttwo'
    def reason(point):return 'reason' if point=='left' else 'matter'
    new_relations=dict(
        ab=lambda faculty,actor,point:(faculty,actor)==('faculty','person'),
        ac=lambda actor,faculty,judgment,point:(actor,faculty,judgment)==('person','faculty',judge(point)),
        fa=lambda actor,judgment,point:(actor,judgment)==('person',judge(point)),
        fb=lambda judgment,topic,point:(judgment,topic)==(judge(point),'topicone'),
        fc=lambda judgment,r,point:(judgment,r)==(judge(point),reason(point)),
        fd=lambda r,judgment,point:(judgment,r)==(judge(point),reason(point)),
        ad=lambda guide,actor,judgment,point:variant=='guided' and (guide,actor,judgment)==('other','person',judge(point)))
    for name,relation in new_relations.items():
        previous=old.get(name,forbidden)
        p[name]=lambda *args,_new=relation,_old=previous:_new(*args) if args[-1] in ('left','right') else _old(*args)
    def cases(actor,topic,anchor,point):
        return (actor,topic,anchor)==('person','topicone','political') and point in ('left','right')
    def presents(node,author,target,depiction,point):
        log('depiction',node,author,target,depiction,point)
        return (node,author,point)==('node','author','end') and code_is(target,'iahinner',1) and code_is(depiction,'iagdepiction' if variant=='old_depiction' else 'iawdepiction',1)
    p.update(iaxcases=cases,iaxassessed=cases,
        iaxdirective=lambda actor,topic,point:'office',
        iaxchoice=lambda actor,topic,point:'topicone' if point=='left' else 'topictwo',
        iaxjudgment=lambda actor,topic,point:judge(point),
        iaxchooses=lambda actor,topic,judgment,choice,point:(actor,topic,judgment,choice)==('person','topicone',judge(point),'topicone' if point=='left' else 'topictwo'),
        iahpresents=presents)
    def remaining(*args):
        log('remaining',*args)
        return old['jpremaining'](*args)
    p['jpremaining']=remaining
    return p,domain,scenes


def values(variant='baseline',indices=(0,),calls=None):
    p,domain,scenes=model(variant,calls)
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,budget=90_000_000)


CONTRASTS=('missing_permission','missing_requirement','guided','old_retained',
    'unrecognized','no_benefit','wrong_target_policy','empty_normcases','old_depiction','remaining_false')


@lru_cache(maxsize=1)
def checks():
    calls=[]
    baseline=values(indices=tuple(range(len(LABELS))),calls=calls)
    assert baseline==[True,True,True,False,True,True,True],baseline
    reached={call[0] for call in calls}
    assert {'appraisal','criterion','targets','depiction','remaining'}<=reached
    print('Integrated baseline and nonvacuous premise: passed',flush=True)
    results={}
    for variant in CONTRASTS:
        results[variant]=values(variant)
        assert results[variant]==[False],(variant,results[variant])
        print(variant+': rejected',flush=True)
    return dict(baseline=dict(zip(LABELS,baseline)),contrasts=results,
        reached_primitive_families=sorted(reached))


def input_paths():
    paths={CORE,'scripts/check_policy_integration.py','tests/test_policy_integration.py',
        'docs/policy-integration-v1.md'}
    # Pin all repository modules loaded by this executable: the inherited model
    # is deliberately reused, and its implementation is part of the evidence.
    for module in tuple(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(ROOT) and path.suffix=='.py':
                paths.add(path.relative_to(ROOT).as_posix())
                # Model fixtures read historical Noema documents through these
                # modules. Pin their declared document inputs as well as code.
                for name,value in vars(module).copy().items():
                    if name.isupper() and isinstance(value,(str,Path)) and str(value).endswith('.noema'):
                        candidate=(ROOT/value).resolve()
                        if candidate.is_relative_to(ROOT) and candidate.is_file():
                            paths.add(candidate.relative_to(ROOT).as_posix())
    return paths


def build_report(result=None):
    result=checks() if result is None else result
    return dict(status='actual_policy_schema_evaluated_in_shared_finite_model',
        document=CORE,results=result,source_definitions_replaced=[],
        scope='Actual iayschema and its causal/appraisal parents; care depiction remains attributed, not asserted as fact.',
        semantic_completion=False,counts_as_translated_coverage=False,
        input_sha256={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sorted(input_paths())})


def write_report():
    report=build_report()
    with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return report


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--variant',default='baseline');cli.add_argument('--indices',default='0')
    cli.add_argument('--report',action='store_true')
    args=cli.parse_args()
    if args.report:write_report()
    else:print(values(args.variant,tuple(map(int,args.indices.split(',')))),flush=True)
