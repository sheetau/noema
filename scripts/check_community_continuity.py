"""Test concrete community continuity inside the collective protection mechanism."""
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
from scripts.compose_community_continuity import ROOT,LIBRARY,EXAMPLE,BASIS,PARENT,PARENT_EXAMPLE,ABILITY,build,basis

REPORT=ROOT/'reports/community-continuity-v1.json'
VARIABLES=('pf','tf','sf')
DOMAIN=('m1','m2','chief','group','people','plan','other','work','thing','tool',*VARIABLES)
ROWS=tuple(product((False,True),repeat=3))
SCENES=('anchor',*['w'+''.join(str(int(b)) for b in row) for row in ROWS],'done','failed')


@lru_cache(maxsize=1)
def setup(): return parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))


def values(flags=(True,True,True,True),variant='baseline',*,indices=(4,5,7,8,9),memoize=True):
    doc=deepcopy(setup());doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args): raise AssertionError('Unexpected primitive')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def bits(point): return tuple(ch=='1' for ch in point[1:]) if point.startswith('w') else (False,False,True)
    def execution(planner,group,person,plan,anchor,point):
        return (planner,group,plan,anchor)==('chief','group','plan','anchor') and person in ('m1','m2') and bits(point)[0]
    def selected(planner,group,plan,anchor,point):
        return (planner,group,plan,anchor,point)==('chief','group','plan','anchor','w111')
    def record(point):
        row=bits(point)
        return FunctionValue(('individual',),'truth',lambda item: row[VARIABLES.index(item)] if item in VARIABLES else False)
    def citizens(community,person,anchor):
        if variant=='unknown_scope': raise ValueError('Unknown community scope')
        if variant=='empty_community': return False
        return community=='people' and person in (('m1',) if variant=='late_scope_removal' and anchor!='anchor' else ('m1','m2'))
    def activities(community,person,activity,anchor):
        return (community,activity)==('people','work') and person in ('m1','m2') and not (
            variant=='empty_person_activities' and person=='m2' or variant=='late_activity_removal' and anchor!='anchor')
    def possessions(community,person,thing,anchor):
        if variant=='no_possessions' or variant=='late_item_removal' and anchor!='anchor': return False
        return community=='people' and (person,thing) in (('m1','thing'),('m2','tool'))
    def holds(person,thing,point):
        if variant=='unknown_holding': raise ValueError('Unknown holding')
        if variant=='new_owner' and (person,thing)==('m1','tool') and point!='anchor': return True
        if (person,thing) not in (('m1','thing'),('m2','tool')): return False
        if point=='anchor': return not (variant=='not_held_at_anchor' and person=='m2')
        if variant in ('late_item_removal','new_owner') and person=='m2': return False
        return bits(point)[2] and flags[1 if person=='m1' else 3]
    def capable(person,activity,start):
        if person not in ('m1','m2') or activity!='work': return False
        if start=='anchor': return variant!='not_capable_at_anchor' or person!='m2'
        if variant in ('late_scope_removal','late_activity_removal') and person=='m2': return False
        return bits(start)[2] and flags[0 if person=='m1' else 2]
    def methods(person,activity,method,start):
        if variant=='unknown_method': raise ValueError('Unknown method')
        if variant=='wrong_activity_method': return activity=='tool' and method=='plan'
        if variant=='wrong_scene_method' and start!='anchor': return False
        return person in ('m1','m2') and activity=='work' and method==('plan' if person=='m1' else 'other')
    def taskselected(person,activity,method,start,end):
        if variant=='missing_assessment': return False
        return methods(person,activity,method,start) and (end in ('done','failed') if variant=='multiple_task_outcomes'
            else end==('done' if capable(person,activity,start) else 'failed'))
    def taskoutcomes(person,activity,method,start,end):
        if variant=='outside_taskoutcomes': return end=='failed'
        return methods(person,activity,method,start) and end in ('done','failed')
    def achieved(person,activity,point):
        if variant=='unknown_task': raise ValueError('Unknown task')
        return person in (('m2',) if variant=='wrong_goal_subject' else ('m1','m2')) and activity=='work' and point=='done'
    model.update(ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)),
        jgplanner=lambda:'chief',jggroup=lambda:'group',jgmembers=lambda:SequenceValue(('m1','m2'),'"individual"'),
        jganchor=lambda:'anchor',jgplan=lambda:'plan',
        jgmembersof=lambda group,person,anchor:(group,anchor)==('group','anchor') and person in ('m1','m2'),
        jgavailable=lambda planner,group,plan,anchor:(planner,group,plan,anchor)==('chief','group','plan','anchor'),
        jgoutcomes=selected,jgselected=selected,jgexecuted=execution,
        jgvariables=lambda:SequenceValue(VARIABLES,'"individual"'),
        jgequations=lambda item,state: (state('pf') or not state('tf')) if item=='sf' else item in VARIABLES,
        jgfactor=lambda:'pf',jgthreatfactor=lambda:'tf',jgmodelgoal=lambda state:state('sf'),
        jgworlds=lambda state:'w'+''.join(str(int(state(item))) for item in VARIABLES),
        jgthreat=lambda:Content(SCENES,tuple(bits(point)[1] for point in SCENES)),jgrecords=record,
        jccommunity=lambda:'group' if variant=='wrong_community' else 'people',jccitizens=citizens,jcactivities=activities,
        jcpossessions=possessions,jcholds=holds,jcmethods=methods,jctaskoutcomes=taskoutcomes,jctaskselected=taskselected,
        jcachieved=achieved,jcsubject=lambda:'m1',jctask=lambda:'work',jcpoint=lambda:'w111')
    return [row['value'] for row in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=100_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for flags in product((False,True),repeat=4):
        result=values(flags);expected=[all(flags),all(flags),True,all(flags),flags[0]]
        assert result==expected,(flags,result);matrix.append(dict(flags=flags,result=result))
    contrasts={}
    for name in ('late_scope_removal','late_activity_removal','late_item_removal','new_owner','wrong_scene_method'):
        result=values(variant=name)
        expected=[False,False,True,False,name!='wrong_scene_method']
        assert result==expected,(name,result);contrasts[name]=result
    for name in ('wrong_community','empty_community','empty_person_activities','not_held_at_anchor','not_capable_at_anchor'):
        result=values(variant=name);assert result==[False,False,False,False,True],(name,result);contrasts[name]=result
    for name in ('wrong_activity_method','missing_assessment','multiple_task_outcomes','outside_taskoutcomes','wrong_goal_subject'):
        result=values(variant=name);assert result==[False]*5,(name,result);contrasts[name]=result
    contrasts['no_possessions']=values(variant='no_possessions');assert contrasts['no_possessions']==[True]*5
    for name in ('unknown_scope','unknown_holding','unknown_method','unknown_task'):
        assert values(variant=name,indices=(6,))==[True]
    paths=[LIBRARY,EXAMPLE,BASIS,PARENT,PARENT_EXAMPLE,ABILITY,'scripts/compose_community_continuity.py',
        'scripts/check_community_continuity.py','tests/test_community_continuity.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='concrete_continuity_target_not_full_public_peace',documents=documents,
        roundtrips=True,matrix=matrix,contrasts=contrasts,limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream: json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Community capabilities, fixed holdings and collective protection verified')


if __name__=='__main__': main()
