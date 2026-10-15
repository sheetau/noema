"""Check readiness, current action, assignment and same-target physical means."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.script import transcribe
from scripts.compose_armed_readiness import ROOT,PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,RELATIONS,build,basis
from scripts.compose_qualified_utterance import closure
from scripts.check_assigned_formation import alignment as parent_alignment

REPORT=ROOT/'reports/armed-readiness-v1.json'
DOMAIN=('event','method','toolmethod','operator','target','tool','group','opponent','community','other','chief','institution','memberrole','commandrole')
SCENES=('anchor','operation','restricted','safe')
CONTRASTS=('other_command','same_group','same_person','other_operator_membership','other_target_membership','other_community',
    'no_instrument','other_tool_use','other_target_use','other_beneficiary','other_tool_result','other_tool_target',
    'other_tool_operator','other_tool_anchor','tool_outside_outcomes','mixed_tool_methods','multiple_tool_outcomes',
    'other_unit_community','other_unit_anchor','unit_outside_outcomes','mixed_unit_methods','multiple_unit_outcomes')


@lru_cache(maxsize=5)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def interpretation(flags=(True,)*7,current=False,current_harm=False,variant='baseline'):
    occurs,unitavailable,unitselected,toolavailable,toolselected,effective,used=flags
    target_person='operator' if variant=='same_person' else 'target'
    opponent='group' if variant=='same_group' else 'opponent'
    def member(group,person,point):
        expected=[('other' if variant=='other_operator_membership' else 'group','operator'),
                  ('other' if variant=='other_target_membership' else opponent,target_person)]
        return point in ('anchor','operation') and (group,person) in expected
    def instrument_use(event,actor,tool,point):
        return used and (event,actor,tool)==('event','operator','other' if variant=='other_tool_use' else 'tool') and point in ('anchor','operation')
    def restricted(tool,target,point):
        if variant=='unknown_effect':raise ValueError('Unknown physical restriction')
        if point=='anchor':return current_harm and (tool,target)==('tool',target_person)
        return effective and (tool,target,point)==('other' if variant=='other_tool_result' else 'tool',
            'other' if variant=='other_tool_target' else target_person,'restricted')
    def tool_method(operator,tool,target,method,start):
        if variant=='unknown_tool_methods':raise ValueError('Unknown tool methods')
        return toolavailable and (operator,tool,target,method)==('other' if variant=='other_tool_operator' else 'operator','tool',target_person,
            'other' if variant=='mixed_tool_methods' else 'toolmethod') and start in (('safe',) if variant=='other_tool_anchor' else ('anchor','operation'))
    def tool_selected(operator,tool,target,method,start,end):
        if variant=='unknown_tool_selection':raise ValueError('Unknown tool assessment')
        return toolselected and (operator,tool,target,method)==('operator','tool',target_person,'toolmethod') and start in ('anchor','operation') and end in (('restricted','safe') if variant=='multiple_tool_outcomes' else ('restricted',))
    def tool_outcomes(operator,tool,target,method,start,end):
        return (operator,tool,target,method)==('operator','tool',target_person,'toolmethod') and start in ('anchor','operation') and end in (('safe',) if variant=='tool_outside_outcomes' else ('restricted','safe'))
    def unit_method(group,community,method,start):
        if variant=='unknown_unit_methods':raise ValueError('Unknown unit methods')
        return unitavailable and (group,community,method,start)==('group','other' if variant=='other_unit_community' else 'community',
            'other' if variant=='mixed_unit_methods' else 'method','safe' if variant=='other_unit_anchor' else 'anchor')
    def unit_selected(group,community,method,start,end):
        if variant=='unknown_unit_selection':raise ValueError('Unknown unit assessment')
        return unitselected and (group,community,method,start)==('group','community','method','anchor') and end in (('operation','safe') if variant=='multiple_unit_outcomes' else ('operation',))
    def unit_outcomes(group,community,method,start,end):
        return (group,community,method,start)==('group','community','method','anchor') and end in (('safe',) if variant=='unit_outside_outcomes' else ('operation','safe'))
    return dict(
        jqgroup=lambda:'group',jqcommunity=lambda:'community',jqanchor=lambda:'anchor',jqevent=lambda:'event',
        jqoccurs=lambda e,t:e=='event' and (occurs and t=='operation' or current and t=='anchor'),
        jqcommanded=lambda e,g,t:(e,g)==('event','other' if variant=='other_command' else 'group') and t in ('anchor','operation'),
        jqopponentof=lambda e,t:opponent,jqactorof=lambda e,t:'operator',
        jqtargetof=lambda e,t:target_person,jqtoolof=lambda e,t:'tool',jqmembers=member,
        jqopposes=lambda g,o,c,t:(g,o,c)==('group',opponent,'other' if variant=='other_community' else 'community') and t in ('anchor','operation'),
        jqinstrument=lambda tool,t:variant!='no_instrument' and tool=='tool',jqused=instrument_use,
        jqagainst=lambda e,a,target,t:(e,a,target)==('event','operator','other' if variant=='other_target_use' else target_person) and t in ('anchor','operation'),
        jqonbehalf=lambda e,c,t:(e,c)==('event','other' if variant=='other_beneficiary' else 'community') and t in ('anchor','operation'),
        jqrestricted=restricted,jqtoolmethods=tool_method,jqtooloutcomes=tool_outcomes,jqtoolselected=tool_selected,
        jqunitmethods=unit_method,jqunitoutcomes=unit_outcomes,jqunitselected=unit_selected)


def values(flags=(True,)*7,*,current=False,current_harm=False,variant='baseline',indices=(0,1,2),memoize=True):
    doc=deepcopy(document(EXAMPLE));doc['statements']=[doc['statements'][i] for i in indices]
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=interpretation(flags,current,current_harm,variant),max_steps=10_000_000,
        memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(maxsize=1)
def source_setup():
    doc=deepcopy(document(EXAMPLE));doc['statements']=[];names={d['name'] for d in doc['declarations']}
    for decl in closure(document(SOURCE),['hzzqualified','hzyqualified']):
        if decl['name'] not in names:doc['declarations'].append(decl);names.add(decl['name'])
    text=format_graph(doc,'compact')+'r jqchief[] a.r jqremaining[a a a d] c.'
    refs='k jqchief[] k jqgroup[] k jqcommunity[] k jqanchor[]'
    residual='i[actor a group a community a point d][k hzzqualified[p jqremaining v actor v group v community v point]]'
    combined='k hzyqualified[r[p hzzmission] '+residual+' '+refs+']'
    queries=['t[k hzzmission[k jqgroup[] k jqcommunity[]]][k jqanchor[]]',
        'k hzyformation[r[p hzzmission] '+refs+']','k hzzagreement[k jqchief[] k jqgroup[] k jqanchor[]]',combined,
        'e[r['+combined+']][r['+combined+']]']
    return parse(text+''.join('q['+q+'].' for q in queries))


def source_values(*,ready=True,assigned=True,remaining=True,variant='baseline',indices=(0,1,2,3,4)):
    doc=deepcopy(source_setup());doc['statements']=[doc['statements'][i] for i in indices]
    model=interpretation((True,ready,True,True,True,True,True),variant=variant)
    for name,sort in RELATIONS:model['hzz'+name]=model['jq'+name]
    if variant=='new_scope_extra':
        old=model['hzzmembers'];model['hzzmembers']=lambda g,p,t:old(g,p,t) or (g,p,t)==('group','other','anchor')
    def members(actor,group,anchor):
        assert (actor,group,anchor)==('chief','group','anchor')
        def scope(g,p,t):
            if variant=='unknown_scope':raise ValueError('Unknown old membership scope')
            return model['jqmembers'](g,p,t) or (variant=='old_scope_extra' and (g,p,t)==('group','other','anchor')) or (
                variant=='old_future_extra' and (g,p,t)==('group','other','operation'))
        return FunctionValue(('individual','individual','situation'),'truth',scope)
    def mission(code):return json.loads(code.syntax)==dict(kind='function_ref',symbol='hzzmission')
    def remaining_condition(a,g,c,t):
        if variant=='unknown_remaining':raise ValueError('Unknown remaining qualification')
        return remaining and (a,g,c,t)==('chief','group','other' if variant=='other_remaining_community' else 'community','anchor')
    model.update(jqchief=lambda:'chief',jqremaining=remaining_condition,hzxmembersof=members,
        hzyinstitution=lambda a,g,t:'institution',hzyconstituted=lambda i,g,t:(i,g,t)==('institution','group','anchor'),
        hzyassigned=lambda i,g,c,code,t:assigned and (i,g,c,t)==('institution','group','community','anchor') and mission(code),
        hzyoffices=lambda role,i,g,t:role in ('memberrole','commandrole') and (i,g,t)==('institution','group','anchor'),
        hzyholders=lambda person,role,i,g,t:(person,role) in (('operator','memberrole'),('chief','commandrole')) and (i,g,t)==('institution','group','anchor'),
        hzyresponsibilities=lambda role,i,g,c,code,t:role in ('memberrole','commandrole') and (i,g,c,t)==('institution','group','community','anchor') and mission(code),
        hzydirects=lambda role,i,g,t:(role,i,g,t)==('commandrole','institution','group','anchor'))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=10_000_000,memoize_definitions=True,memoize_expressions=True)]


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Readiness or assignment evaluated during attribution')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def annotation(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='hzzonly')
    model.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',hzzannotation=annotation)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=model)]


def alignment():
    result=parent_alignment();result.update(definitions=['hzzmission','hzzagreement','hzzqualified','hzzonly','hzzattribution'],
        military_mission_open=False,military_mission_status='explicit_armed_readiness_candidate',residual_qualification_open=True)
    return result


def binding_structure():
    lookup={d['name']:d for d in document(SOURCE)['declarations']}
    d=lookup['hzzonly'];remaining,anchor=[p['name'] for p in d['parameters']];body=d['body']
    assert body['symbol']=='hzyonly'
    assert body['arguments'][0]==dict(kind='quote',body=dict(kind='function_ref',symbol='hzzmission'))
    fn=body['arguments'][1];bound=[p['name'] for p in fn['parameters']]
    assert fn['body']==dict(kind='call',symbol='hzzqualified',arguments=[dict(kind='variable',name=n) for n in [remaining,*bound]])
    assert body['arguments'][2]==dict(kind='variable',name=anchor)
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
    for flags in product((False,True),repeat=7):
        result=values(flags);assert result==[all(flags),False,True],(flags,result)
        matrix.append(dict(flags=flags,result=result))
    actual=[]
    for current,harm in product((False,True),repeat=2):
        result=values(current=current,current_harm=harm);assert result==[True,current,True]
        actual.append(dict(current=current,harm=harm,result=result))
    assert values((True,False,True,True,True,True,True),current=True)==[False,True,True]
    contrasts={v:values(variant=v) for v in CONTRASTS}
    assert all(r==[False,False,True] for r in contrasts.values()),contrasts
    for variant in ('unknown_effect','unknown_tool_methods','unknown_tool_selection','unknown_unit_methods','unknown_unit_selection'):
        assert values(variant=variant,indices=(2,))==[True]
        try:values(variant=variant,indices=(0,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown capability was filled')
    source=[]
    for ready,assigned,remaining in product((False,True),repeat=3):
        result=source_values(ready=ready,assigned=assigned,remaining=remaining)
        assert result==[ready,assigned,True,ready and assigned and remaining,True]
        source.append(dict(bits=[ready,assigned,remaining],result=result))
    assert source_values(variant='old_future_extra')==[True]*5
    assert source_values(variant='new_scope_extra')==[True,True,False,False,True]
    assert source_values(variant='old_scope_extra')==[True,False,False,False,True]
    assert source_values(variant='other_remaining_community')==[True,True,True,False,True]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    assert values(memoize=False)==[True,False,True]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,'scripts/compose_armed_readiness.py','scripts/check_armed_readiness.py',
        'tests/test_armed_readiness.py','noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='explicit_readiness_mission_and_actual_role_integration',documents=documents,matrix=matrix,actual=actual,
        contrasts=contrasts,source_matrix=source,binding_structure=binding_structure(),roundtrips=True,
        integrated_assignment_evaluated=True,integrated_protection_and_utterance_evaluated=False,source_alignment=alignment(),
        verified_full_units={'kant-1784':0,'einstein-1905':0},unresolved=basis()['unresolved'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Armed readiness, unasserted current fighting, assigned mission and source integration verified')


if __name__=='__main__':main()
