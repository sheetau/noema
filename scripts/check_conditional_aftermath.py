"""Check conditional scope, reading identity, history and separate antecedent witnesses."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_conditional_aftermath import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,TAIL,build,basis
from scripts.check_faculty_opportunities import evaluate
from scripts.check_apparent_liberty import UNITS
from scripts.compose_qualified_utterance import closure
from scripts import check_thinking_disposition as previous

REPORT=ROOT/'reports/conditional-aftermath-v1.json'
SCENES=('now','one','two','laterone','latertwo','outside')
DOMAIN=('person','other')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jcperson[] a.r jcfirst[a d] c.r jcsecond[a d] c.r jccases[d] c.r jcnow[] d.
r jchistory[d d] c.r jcbefore[d d d] c.
'''+f'r jctail[{HIGH} a d d] c.'+'''
d jcfirstreading[person a] e[b scene[k jcfirst[v person v scene]]].
d jcsecondreading[person a] e[b scene[k jcsecond[v person v scene]]].
q[k rxa[r b[p jcfirstreading] k jcperson[] p jccases p jchistory p jcbefore p jctail]].
q[k rxb[r b[p jcfirstreading] k jcperson[] p jccases]].
q[k rxa[r b[p jcsecondreading] k jcperson[] p jccases p jchistory p jcbefore p jctail]].
q[t[k jcfirstreading[k jcperson[]]][k jcnow[]]].
''')


def model(premises=3,results=3,*,second=0,variant='baseline',calls=None):
    starts=('one','two');ends=('laterone','latertwo')
    def truth(person,scene,mask):
        if variant=='unknown_premise' and scene in starts:raise ValueError('Unknown antecedent')
        return person=='person' and scene in starts and bool(mask&(1<<starts.index(scene)))
    def cases(scene):
        if variant=='unknown_cases':raise ValueError('Unknown case scope')
        return variant!='empty_cases' and scene in starts
    def history(scene,point):
        if variant=='unknown_history':raise ValueError('Unknown history')
        if scene not in starts:return False
        end=ends[starts.index(scene)]
        if variant=='missing_start':return point==end
        if variant=='missing_end':return point==scene
        return point in (scene,end)
    def before(scene,left,right):
        if variant=='unknown_order':raise ValueError('Unknown order')
        if scene not in starts:return False
        end=ends[starts.index(scene)]
        if variant=='reflexive' and left==right==scene:return True
        if variant=='cycle' and (left,right)==(end,scene):return True
        if variant=='reversed':return (left,right)==(end,scene)
        return (left,right)==(scene,end)
    def tail(reading,person,start,end):
        if calls is not None:calls.append((reading,person,start,end))
        if variant=='unknown_result' or variant=='unknown_unused_result' and start=='two':raise ValueError('Unknown consequence')
        if variant=='forbidden_result':raise AssertionError('False antecedent executed consequence')
        if start not in starts:return False
        expected='jcsecondreading' if variant=='wrong_reading' or variant=='split_readings' and start=='two' else 'jcfirstreading'
        owner='other' if variant=='wrong_person' else 'person'
        index=starts.index(start)
        endpoint=ends[1-index] if variant=='other_history' else start if variant=='simultaneous' else 'now' if variant=='past' else ends[index]
        return previous.code_is(reading,expected,1) and person==owner and end==endpoint and bool(results&(1<<index))
    return dict(jcperson=lambda:'person',jcnow=lambda:'now',jcfirst=lambda p,s:truth(p,s,premises),
        jcsecond=lambda p,s:truth(p,s,second),jccases=cases,jchistory=history,jcbefore=before,jctail=tail)


def values(*,indices=(0,1,3),memoize=True,**options):
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    return evaluate(doc,model(**options),DOMAIN,SCENES,memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(SOURCE));doc['statements']=[]
    doc['declarations']=closure(doc,['iaiframe','iaiwitness'])
    return parse(format_graph(doc,'compact')+f'r jctail[{HIGH} a d d] c.r jcperson[] a.'+'''
q[k iaiframe[r b[p iahinner] p jctail]].
q[k iaiframe[r b[p iahvocation] p jctail]].
q[t[k iaiwitness[r b[p iahinner] k jcperson[]]][k wh[]]].
q[t[k iaiwitness[r b[p iahvocation] k jcperson[]]][k wh[]]].
q[k iaiframe[r b[p iahthinking] p jctail]].
''')


def source_values(*,urge=True,assigned=True,result=True,variant='baseline',memoize=True,indices=(0,1,2,3,4),calls=None):
    scenes=previous.SCENES+('after','otherafter')
    people=lambda p,a:variant!='empty_people' and (p,a)==('person','end')
    def cases(person,anchor,scene):
        if variant=='unknown_source_cases':raise ValueError('Unknown source cases')
        return variant!='empty_cases' and (person,anchor)==('person','outside' if variant=='other_anchor' else 'end') and scene in ('end','outside')
    def history(person,anchor,scene,point):
        return (person,anchor)==('person','end') and (scene,point) in (('end','end'),('end','after'),('outside','outside'),('outside','otherafter'))
    def order(person,anchor,scene,left,right):
        return (person,anchor)==('person','end') and (scene,left,right) in (('end','end','after'),('outside','outside','otherafter'))
    def tail(reading,person,start,end):
        if calls is not None:calls.append((reading,person,start,end))
        if variant=='unknown_source_result' or variant=='unknown_unused_result' and start=='outside':raise ValueError('Unknown source consequence')
        accepted=('iahvocation',) if variant=='vocation_only' else ('iahinner','iahvocation')
        return result and any(previous.code_is(reading,n,1) for n in accepted) and (person,start,end)==('other' if variant=='other_person' else 'person','end','otherafter' if variant=='other_history' else 'after')
    p=previous.model(urge=urge,assigned=assigned)
    p.update(iaipeople=people,iaicases=cases,iaihistory=history,iaibefore=order,jctail=tail,jcperson=lambda:'person')
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],previous.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,previous.DOMAIN,scenes,memoize=memoize)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:previous.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iaireport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and previous.code_is(code,'iaiframe',2))
    return [r['value'] for r in evaluate_document(doc,individuals=previous.DOMAIN,situations=previous.SCENES,primitives=p)]


CONTRASTS=('empty_cases','missing_start','missing_end','reflexive','cycle','reversed','wrong_reading','wrong_person','other_history','simultaneous','past')
UNKNOWNS=('unknown_cases','unknown_history','unknown_order','unknown_premise','unknown_result')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iaiconditional','iaiwitness','iaiframe','iaiattribution'],
        adds_new_text_coverage=False,semantic_completion=False,consequent_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for premises,results in product(range(4),repeat=2):
        assert values(premises=premises,results=results)==[premises&~results==0,premises!=0,False]
    for name in CONTRASTS:assert values(variant=name,indices=(0,))==[False],name
    for name in UNKNOWNS:
        try:values(variant=name,indices=(0,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    assert values(premises=0,variant='forbidden_result')==[True,False,False]
    assert values(memoize=False)==values()
    for urge,assigned in product((False,True),repeat=2):
        assert source_values(urge=urge,assigned=assigned,result=False)==[not urge,not assigned,urge,assigned,False]
    assert source_values()==[True,True,True,True,False]
    assert source_values(variant='vocation_only',indices=(0,1))==[False,True]
    assert source_values(memoize=False,indices=(0,))==source_values(indices=(0,))
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_conditional_aftermath.py','scripts/check_conditional_aftermath.py',
        'tests/test_conditional_aftermath.py','noema/constructed.py','noema/constructed_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='conditional_scope_checked_consequent_still_unfilled',documents=documents,truth_table_combinations=16,
        source_alignment=alignment(),roundtrips=True,uncached_generic_and_source_baseline_checked=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Conditional scope, fixed reading and separate witness verified; consequent remains unfilled')


if __name__=='__main__':main()
