"""Check plan-specific commands without replacing their content by obedience bits."""
import argparse
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue,Content,FunctionValue
from noema.script import transcribe
from scripts.compose_commanded_protection import ROOT,LIBRARY,EXAMPLE,BASIS,PARENT,PARENT_EXAMPLE,OBEDIENCE,build,basis

REPORT=ROOT/'reports/commanded-protection-v1.json'
VARIABLES=('pf','tf','sf')
DOMAIN=('m1','m2','chief','group','people','plan','other','work','thing','role','order',*VARIABLES)
ROWS=tuple(product((False,True),repeat=3))
SCENES=('anchor',*['w'+''.join(str(int(b)) for b in row) for row in ROWS],'done','failed')


@lru_cache(maxsize=2)
def setup(restricted=True):
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))
    if restricted:
        alias=deepcopy(next(d for d in doc['declarations'] if d['name']=='jnact'));alias['name']='jnalias';doc['declarations'].append(alias)
        prefix=[d for d in doc['declarations'] if d['kind']=='primitive' or d['name'] in ('jnact','jnalias')]
        doc['declarations']=prefix+[d for d in doc['declarations'] if d not in prefix]
        node=next(d for d in doc['declarations'] if d['name']=='rtx')['body']['body']['body']
        assert node['kind']=='forall' and node['sort']['kind']=='description'
        instances=[dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],body=deepcopy(node['body'])),
            arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=name))]) for name in ('jnact','jnalias')]
        node.clear();node.update(kind='and',arguments=instances)
        doc=parse(format_graph(doc,'compact'))
    return doc


def values(flags=(True,True,True),variant='baseline',*,indices=(10,11,12),restricted=True,threshold=1,memoize=True):
    present,first,second=flags
    doc=deepcopy(setup(restricted));doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args):raise AssertionError('Unexpected primitive')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def bits(point):return tuple(ch=='1' for ch in point[1:]) if point.startswith('w') else (False,False,True)
    def known(planner,group,person,plan,anchor):
        return (planner,group,anchor)==('chief','group','anchor') and plan in (('plan','other') if variant=='other_plan_failed' else ('plan',)) and person in ('m1','m2')
    def scope(planner,group,person,plan,role,anchor):
        return variant!='empty_commands' and known(planner,group,person,plan,anchor) and role=='role'
    def items(planner,group,person,plan,item,anchor):
        return variant not in ('empty_commands','omit_record') and known(planner,group,person,plan,anchor) and item=='order'
    def orders(source,group,plan,person,role,activity,code,sign,anchor):
        if variant=='unknown_orders':raise ValueError('Unknown orders')
        if variant=='empty_commands':return False
        codes=('jnact','jnalias') if variant=='unlisted_description' else ('jnalias',) if variant=='wrong_description' else ('jnact',)
        expected=('m1' if variant=='wrong_source' else 'chief','people' if variant=='wrong_group' else 'group',
            plan if variant=='other_plan_failed' and plan in ('plan','other') else 'other' if variant=='wrong_plan' else 'plan',
            'w111' if variant=='wrong_anchor' else 'anchor')
        target='thing' if variant=='other_plan_failed' and plan=='other' else 'work'
        return present and (source,group,plan,anchor)==expected and person in (('m2',) if variant=='wrong_person' else ('m1','m2')) and \
            (role,activity,sign)==('role',target,variant not in ('negative','wrong_polarity')) and json.loads(code.syntax).get('symbol') in codes
    def execution(person,activity,point):
        if variant=='unknown_execution':raise ValueError('Unknown execution')
        if person not in ('m1','m2') or activity!='work':return False
        success=bits(point)[0] and (first if person=='m1' else second)
        return not success if variant=='negative' else success
    def selected(planner,group,plan,anchor,point):
        return known(planner,group,'m1',plan,anchor) and point=='w111'
    def record(point):
        row=bits(point)
        return FunctionValue(('individual',),'truth',lambda item:row[VARIABLES.index(item)] if item in VARIABLES else False)
    def methods(person,activity,method,start):return person in ('m1','m2') and (activity,method)==('work','plan')
    def taskselected(person,activity,method,start,end):
        return methods(person,activity,method,start) and end==('done' if bits(start)[2] else 'failed')
    model.update(ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)),
        jgplanner=lambda:'chief',jggroup=lambda:'group',jgmembers=lambda:SequenceValue(('m1','m2'),'"individual"'),jganchor=lambda:'anchor',jgplan=lambda:'plan',
        jgmembersof=lambda group,person,anchor:(group,anchor)==('group','anchor') and person in ('m1','m2'),
        jgavailable=lambda planner,group,plan,anchor:known(planner,group,'m1',plan,anchor),
        jgoutcomes=selected,jgselected=selected,jgvariables=lambda:SequenceValue(VARIABLES,'"individual"'),
        jgequations=lambda item,state:(state('pf') or not state('tf')) if item=='sf' else item in VARIABLES,
        jgfactor=lambda:'pf',jgthreatfactor=lambda:'tf',jgmodelgoal=lambda state:state('sf'),
        jgworlds=lambda state:'w'+''.join(str(int(state(item))) for item in VARIABLES),
        jgthreat=lambda:Content(SCENES,tuple(bits(point)[1] for point in SCENES)),jgrecords=record,
        jccommunity=lambda:'people',jccitizens=lambda community,person,anchor:community=='people' and person in ('m1','m2'),
        jcactivities=lambda community,person,activity,anchor:(community,activity)==('people','work') and person in ('m1','m2'),
        jcpossessions=lambda community,person,thing,anchor:(community,thing)==('people','thing') and person in ('m1','m2'),
        jcholds=lambda person,thing,point:person in ('m1','m2') and thing=='thing' and bits(point)[2],
        jcmethods=methods,jctaskoutcomes=lambda person,activity,method,start,end:methods(person,activity,method,start) and end in ('done','failed'),
        jctaskselected=taskselected,jcachieved=lambda person,activity,point:person in ('m1','m2') and (activity,point)==('work','done'),
        jcsubject=lambda:'m1',jctask=lambda:'work',jcpoint=lambda:'w111',
        jncommandrolescope=scope,jncommanditems=items,jncommandroles=lambda *args:'role',
        jncommandactions=lambda planner,group,person,plan,item,anchor:'thing' if variant=='other_plan_failed' and plan=='other' else 'work',
        jncommandsigns=lambda *args:variant!='negative',jnorders=orders,jnexecuted=execution,jncriterion=lambda count:count>threshold)
    return [row['value'] for row in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=150_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def full_domain_refused():
    try:values(restricted=False,indices=(10,))
    except ValueError as error:assert 'description domain' in str(error)
    else:raise AssertionError('Description quantification silently restricted')
    return True


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for flags in product((False,True),repeat=3):
        present,first,second=flags;result=values(flags)
        assert result==[present and first,False,present and first and second],(flags,result)
        matrix.append(dict(flags=flags,result=result))
    contrasts={}
    for name in ('wrong_source','wrong_group','wrong_plan','wrong_anchor','wrong_person','omit_record','unlisted_description','wrong_description','wrong_polarity'):
        result=values(variant=name);assert result==[False]*3,(name,result);contrasts[name]=result
    contrasts['negative']=values(variant='negative');assert contrasts['negative']==[True,False,True]
    contrasts['empty_commands']=values(variant='empty_commands');assert contrasts['empty_commands']==[True]*3
    integration={}
    for name,threshold,expected in [('baseline',1,[True,True]),('baseline',2,[True,False]),('empty_commands',1,[False,False]),
                                  ('other_plan_failed',1,[True,False])]:
        result=values(variant=name,threshold=threshold,indices=(4,5));assert result==expected,(name,threshold,result)
        integration[name+'_'+str(threshold)]=result
    for name in ('unknown_orders','unknown_execution'):assert values(variant=name,restricted=False,indices=(6,))==[True]
    assert values(indices=(10,),memoize=False)==[True]
    paths=[LIBRARY,EXAMPLE,BASIS,PARENT,PARENT_EXAMPLE,OBEDIENCE,'scripts/compose_commanded_protection.py',
        'scripts/check_commanded_protection.py','tests/test_commanded_protection.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='command_bound_community_protection_not_full_military_concept',documents=documents,
        matrix=matrix,contrasts=contrasts,integration=integration,roundtrips=True,diagnostic_descriptions=['jnact','jnalias'],
        full_description_domain_refused=full_domain_refused(),full_description_domain_verified=False,limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Same-source, same-group and same-plan commands connected to community protection')


if __name__=='__main__':main()
