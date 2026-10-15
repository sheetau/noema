"""Test joint outcomes against separately achievable member goals."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_joint_readiness import ROOT,LIBRARY,EXAMPLE,BASIS,COUNTS,OBEDIENCE,build,basis

REPORT=ROOT/'reports/joint-readiness-v1.json'
DOMAIN=('p','q','chief','group','role','order','work','one','two')
SCENES=('anchor','left','right')

@lru_cache(maxsize=2)
def setup(restricted=True):
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))
    available='k jsavailable[k jsplanner[] k jsgroup[] v plan k jsanchor[]]'
    selected='k jsselected[k jsplanner[] k jsgroup[] v plan k jsanchor[] v point]'
    outcome='k jsoutcomes[k jsplanner[] k jsgroup[] v plan k jsanchor[] v point]'
    goal='t[k jsgoals[k jsplanner[] k jsgroup[] v person v plan k jsanchor[]]][v point]'
    diagnostic='q[k jsmembers[]][e[n p a b][n p a b]][i[valid c person a][w[v valid][g plan a[w['+available+'][w[g point d['+selected+']][w[f point d[y['+selected+']['+outcome+']]][f point d[y['+selected+']['+goal+']]]]]]]]]'
    doc=parse(format_graph(doc,'compact')+'q['+diagnostic+'].')
    if restricted:
        alias=deepcopy(next(d for d in doc['declarations'] if d['name']=='jsaction'));alias['name']='jsalias';doc['declarations'].append(alias)
        prefix=[d for d in doc['declarations'] if d['kind']=='primitive' or d['name'] in ('jsaction','jsalias')]
        doc['declarations']=prefix+[d for d in doc['declarations'] if d not in prefix]
        node=next(d for d in doc['declarations'] if d['name']=='rtx')['body']['body']['body']
        assert node['kind']=='forall' and node['sort']['kind']=='description'
        instances=[dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],body=deepcopy(node['body'])),
            arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=name))]) for name in ('jsaction','jsalias')]
        node.clear();node.update(kind='and',arguments=instances);doc=parse(format_graph(doc,'compact'))
    return doc

def values(bits=(True,True,True,True),variant='baseline',*,threshold=1,restricted=True,indices=None,memoize=True):
    available_flag,p_success,q_success,goal_success=bits
    doc=deepcopy(setup(restricted))
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    members={'missing_member':('p',),'extra_member':('p','q','chief'),'duplicate_member':('p','p','q'),'empty_group':()}.get(variant,('p','q'))
    plans=('one','two') if variant in ('separate_plans','good_and_bad_plans','empty_other_plan','goal_not_all_plans','incoherent_other_plan') else ('one',)
    def forbidden(*args):raise AssertionError('Unexpected primitive interpretation')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def available(planner,group,plan,anchor):
        if variant=='unknown_availability':raise ValueError('Unknown availability')
        expected=('p' if variant=='wrong_planner' else 'chief','work' if variant=='wrong_group' else 'group','right' if variant=='wrong_anchor' else 'anchor')
        return available_flag and (planner,group,anchor)==expected and plan in plans
    def selected(planner,group,plan,anchor,point):
        if (planner,group,anchor)!=('chief','group','anchor') or plan not in plans:return False
        if variant=='empty_selected' or (variant=='empty_other_plan' and plan=='two'):return False
        if variant=='one_bad_realization':return point in ('left','right')
        return point==('left' if plan=='one' else 'right')
    def outcome(planner,group,plan,anchor,point):
        if variant=='incoherent_other_plan' and plan=='two':return (planner,group,anchor,point)==('chief','group','anchor','left')
        if variant=='outside_outcome':return (planner,group,plan,anchor,point)==('chief','group','one','anchor','right')
        return (planner,group,anchor)==('chief','group','anchor') and plan in plans and point in ('left','right')
    def required(source,person,role,activity,code,sign,anchor):
        if variant=='unknown_requirements':raise ValueError('Unknown requirements')
        names=('jsaction','jsalias') if variant=='unlisted_requirement' else ('jsaction',)
        return source==('p' if variant=='wrong_norm_source' else 'chief') and person in (('p',) if variant=='wrong_norm_person' else ('p','q')) and \
            (role,activity,sign,anchor)==('role','work',True,'anchor') and json.loads(code.syntax).get('symbol') in names
    def execution(person,activity,point):
        if variant=='unknown_execution':raise ValueError('Unknown execution')
        if activity!='work' or person not in ('p','q'):return False
        if variant=='separate_plans':return (person,point) in (('p','left'),('q','right'))
        if variant in ('good_and_bad_plans','one_bad_realization'):return point=='left' or (person=='p' and point=='right')
        return point in ('left','right') and (p_success if person=='p' else q_success)
    def target(point):
        if variant=='goal_elsewhere':return point=='right'
        if variant=='goal_not_all_plans':return point=='left'
        return goal_success and point in ('left','right')
    model.update(ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda condition:Fraction((2 if variant=='bad_indicator' else 1) if condition else 0),
        jsplanner=lambda:'chief',jsgroup=lambda:'group',jsmembers=lambda:SequenceValue(members,json.dumps('individual')),jsanchor=lambda:'anchor',jsplan=lambda:'one',
        jsmembersof=lambda group,person,anchor:variant!='empty_group' and (group,anchor)==('group','anchor') and person in ('p','q'),
        jscriterion=lambda count:count>Fraction(threshold),jsavailable=available,jsoutcomes=outcome,jsselected=selected,jstarget=target,
        jsscope=lambda group,person,role,plan,anchor:(group,role,anchor)==('group','role','anchor') and person in ('p','q'),
        jsitems=lambda group,person,item,plan,anchor:(group,item,anchor)==('group','order','anchor') and person in ('p','q'),
        jsroles=lambda group,person,item,plan,anchor:'role',jsactions=lambda group,person,item,plan,anchor:'work',
        jssigns=lambda group,person,item,plan,anchor:True,jsrequired=required,jsexecution=execution)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=50_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]

def full_domain_refused():
    try:values(restricted=False,indices=(1,))
    except ValueError as error:assert 'description domain' in str(error)
    else:raise AssertionError('All action descriptions were silently replaced by the diagnostic list')
    return True

def build_report():
    documents={}
    for name,text in build().items():
        assert (ROOT/name).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[name]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for bits in product((False,True),repeat=4):
        a,p,q,g=bits;ready=a and p and q;result=values(bits)
        assert result==[True,ready,ready and g,ready,ready and g,True,ready],(bits,result)
        matrix.append(dict(bits=bits,result=result))
    contrasts={}
    for name,expected in [
        ('separate_plans',[True,False,False,False,False,True,True]),
        ('good_and_bad_plans',[True,True,True,False,False,True,True]),
        ('empty_other_plan',[True,True,True,False,False,True,True]),
        ('goal_elsewhere',[True,True,False,True,False,True,True]),
        ('goal_not_all_plans',[True,True,True,True,True,True,True]),
        ('one_bad_realization',[True,False,False,False,False,True,False]),
        ('incoherent_other_plan',[True,True,True,False,False,True,True])]:
        result=values(variant=name);assert result==expected,(name,result);contrasts[name]=result
    for name in ('empty_selected','outside_outcome','wrong_planner','wrong_group','wrong_anchor','wrong_norm_source','wrong_norm_person','unlisted_requirement'):
        result=values(variant=name);assert result[:5]==[True,False,False,False,False],(name,result);contrasts[name]=result
    for name in ('missing_member','extra_member','duplicate_member','empty_group','bad_indicator'):
        result=values(variant=name,indices=(0,1,2,3,4,5));assert result==[False]*5+[True],(name,result);contrasts[name]=result
    assert values(threshold=2,indices=(0,2,3,4))==[False,True,True,False]
    for name in ('unknown_availability','unknown_requirements','unknown_execution'):
        assert values(variant=name,restricted=False,indices=(5,))==[True]
    assert values(memoize=False,indices=(0,1,5))==[True,True,True]
    paths=[LIBRARY,EXAMPLE,BASIS,COUNTS,OBEDIENCE,'scripts/compose_joint_readiness.py','scripts/check_joint_readiness.py','tests/test_joint_readiness.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    result=dict(status='same_plan_same_outcomes_not_full_group_discipline_or_army_meaning',documents=documents,new_definitions=6,
        inherited_arithmetic_primitives=['ha','hc','hd'],roundtrips=True,matrix=matrix,contrasts=contrasts,
        diagnostic_descriptions=['jsaction','jsalias'],full_description_domain_refused=full_domain_refused(),full_description_domain_verified=False,
        limitations=basis()['limitations'],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Exact members, joint plans, all-plan compliance and common outcomes verified')

if __name__=='__main__':main()
