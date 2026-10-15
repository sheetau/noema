"""Check constructed comparative statements, personal judgments and joint policies."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_comparative_speech import ROOT,PARENT,SOURCE,CORE,BASIS,DETAILS,DETAIL_SYMBOLS,CCODE,LINK,build,basis
from scripts.compose_public_permission_risk import ACTION
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,op
from scripts.check_policy_recognition import source_setup as parent_setup
from scripts.check_public_permission_risk import DOMAIN,SCENES

REPORT=ROOT/'reports/comparative-speech-v1.json'


@lru_cache(maxsize=1)
def setup():
    parent=parent_setup();doc=deepcopy(parent['document']);doc['statements']=[]
    names={d['name'] for d in doc['declarations']}
    doc['declarations'] += [d for d in parse((ROOT/CORE).read_text(encoding='utf-8'))['declarations'] if d['name'] not in names]
    text='r jdbetter[a a a d] c.r jdolder[] a.r jdnewer[] a.r jdforms[a a d] c.'
    text+='r jdlinked[a '+CCODE+' a a a d] c.r jdcandidates[a d d] c.'
    text+=definition('jdcompare','subject a older a newer a','b point[k jdbetter[v subject v older v newer v point]]','e')
    text+=definition('jdcomparealias','subject a older a newer a','b point[k jdbetter[v subject v older v newer v point]]','e')
    codes=dict(criterion='r[p jdcompare]',older='r[k jdolder[]]',newer='r[k jdnewer[]]',
        forms='r[p jdforms]',linked='r[p jdlinked]',candidates='r[p jdcandidates]')
    text+=''.join(definition(DETAIL_SYMBOLS[n],'person a activity a anchor d',codes[n],t) for n,t in DETAILS)
    fixture=parse('p:'+text);replacement={d['name']:d for d in fixture['declarations']}
    prefix=[d for d in fixture['declarations'] if d['name'].startswith('jd')]
    doc['declarations']=prefix+[replacement.get(d['name'],d) for d in doc['declarations']]
    lookup={d['name']:d for d in doc['declarations']}
    code_nodes={n:lookup[DETAIL_SYMBOLS[n]]['body'] for n,_ in DETAILS}
    message=dict(kind='apply',function=lookup['rru']['body']['function']['body'],
        arguments=[code_nodes[n]['body'] for n,_ in DETAILS[:3]])
    arguments=[code_nodes['criterion']['body'],code_nodes['criterion']]+[code_nodes[n]['body'] for n,_ in DETAILS[1:]]
    arguments += [dict(kind='quote',body=message) if n=='message' else parent['target_syntax']['arguments'][i] for i,(n,_) in enumerate(ACTION)]
    target=dict(kind='apply',function=dict(kind='function_ref',symbol='rrv'),arguments=arguments)
    policies=[]
    for name,template in (('hzopolicy','rrs'),('hzpcomparative','rrx')):
        policies.append(dict(kind='apply',function=dict(kind='function_ref',symbol=template),
            arguments=[a['body'] for a in lookup[name]['body']['arguments']]))
    joint=dict(kind='apply',function=lookup['rrz']['body']['function']['body'],arguments=policies)
    target_call=k('hzptarget',k('jdperson'),k('jdactivity'),k('wh'))
    message_call=k('rru',*(codes[n] for n,_ in DETAILS[:3]))
    queries=[op('t',app('s['+target_call+']',k('jdperson'),k('jdactivity')),k('wh')),
        op('t',k('jdcompare',k('jdsubject'),k('jdolder'),k('jdnewer')),k('wh'))]
    queries += [op('t','s['+k(symbol)+']',k('wh')) for symbol in ('hzpcomparative','hzopolicy','hzppolicy')]
    queries += ['t[s[r c[k hzpsafety[]]]][k wh[]]','t[s[r d[k hzpinsight[]]]][k wh[]]',
        op('t','o['+app('s['+message_call+']',k('jdsubject'))+']',k('wh'))]
    doc=parse(format_graph(doc,'compact')+''.join('q['+q+'].' for q in queries))
    doc['statements'].insert(0,dict(kind='ask',body=dict(kind='equal',arguments=[
        dict(kind='call',symbol='hzptarget',arguments=[dict(kind='call',symbol=s,arguments=[]) for s in ('jdperson','jdactivity','wh')]),
        dict(kind='quote',body=target)])))
    doc=parse(format_graph(doc,'compact'))
    # Use the canonical, independently quoted expression for model comparisons.
    target=doc['statements'][0]['body']['arguments'][1]['body']
    message=target['arguments'][7+[n for n,_ in ACTION].index('message')]['body']
    return dict(document=doc,target=target,message=message,joint=joint,policies=policies,
        general_target=parent['target_syntax'],criterion=code_nodes['criterion']['body'])


def values(performed=True,judgment=True,candidate_better=True,actual_better=False,
           general_permission=True,comparative_permission=True,general_selected=True,comparative_selected=True,
           aware=True,actual_safe=True,variant='baseline',indices=None,memoize=True):
    data=setup();doc=deepcopy(data['document'])
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args):raise AssertionError('Unexpected primitive during comparative speech evaluation')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def matches(code,expected):return json.loads(code.syntax)==expected
    def better(subject,older,newer,point):
        if variant=='unknown_comparison':raise ValueError('Unknown comparison')
        return (subject,older,newer)==('topic','older','newer') and (actual_better if point=='anchor' else candidate_better)
    def linked(item,code,subject,older,newer,point):
        criterion=dict(kind='function_ref',symbol='jdcomparealias') if variant=='other_criterion' else data['criterion']
        return (item,subject,older,newer,point)==('judgment','topic','newer' if variant=='reversed_forms' else 'older',
            'older' if variant=='reversed_forms' else 'newer','anchor') and matches(code,criterion)
    def allowed(ruler,person,role,act,code,sign,point):
        if (ruler,person,role,act,sign)!=('ruler','person','role','act',True):return False
        general=matches(code,data['general_target']);comparative=matches(code,data['target'])
        if variant=='split_outcomes' and point in ('safe','bad'):
            return (general and point=='safe') or (comparative and point=='bad')
        if variant=='wrong_target':comparative=False
        return (general and general_permission) or (comparative and comparative_permission)
    def prospects(code,context,outcome):
        expected=data['policies'][0] if variant=='old_policy_prospects' else data['joint']
        choices=('safe','bad') if variant=='split_outcomes' else (('bad',) if context=='bad' or (context=='anchor' and not actual_safe) else ('safe',))
        return matches(code,expected) and outcome in choices
    def awareness(person,code,context):
        expected=dict(kind='call',symbol='hzosafety' if variant=='old_safety_awareness' else 'hzpsafety',arguments=[])
        return aware and (person,context)==('ruler','anchor') and matches(code,expected)
    def conveys(act,reader,subject,code,point):
        expected=data['general_target']['arguments'][[n for n,_ in ACTION].index('message')]['body'] if variant=='wrong_message' else data['message']
        return performed and (act,reader,subject,point)==('act','reader','topic','anchor') and matches(code,expected)
    def own(person,item,point):
        if variant=='unknown_judgment':raise ValueError('Unknown personal judgment')
        return judgment and (person,item,point)==('other' if variant=='other_person' else 'person','judgment','anchor')
    model.update(jdperson=lambda:'person',jdactivity=lambda:'act',jdsubject=lambda:'topic',jdrole=lambda:'role',
        jdrecipient=lambda:'world',jdchannel=lambda:'channel',jdolder=lambda:'older',jdnewer=lambda:'older' if variant=='same_form' else 'newer',
        jdbetter=better,jdforms=lambda form,subject,point:form in ('older','newer') and (subject,point)==('channel' if variant=='other_subject' else 'topic','anchor'),
        jdlinked=linked,jdcandidates=lambda item,context,point:(item,context,point)==('judgment','anchor','safe') and variant!='empty_candidates',
        fa=own,fb=lambda item,subject,point:(item,subject,point)==('judgment','channel' if variant=='other_matter' else 'topic','anchor'),
        hzmruler=lambda:'ruler',wh=lambda:'anchor',hzmpeople=lambda person,point:(person,point)==('person','anchor'),
        hzmactivities=lambda person,act,point:general_selected and (act,point)==('act','anchor'),
        hzpactivities=lambda person,act,point:comparative_selected and (act,point)==('act','anchor'),
        hzodomains=lambda ruler,subject,point:(ruler,subject,point)==('ruler','topic','anchor'),
        h7a=lambda *args:False,h7b=allowed,hzmprospects=prospects,hzmadverse=lambda point:point=='bad',hznawareness=awareness,
        hznalternatives=lambda person,code,context,point:(person,context,point)==('ruler','anchor','safe')
            and matches(code,dict(kind='call',symbol='hzpsafety',arguments=[])),
        jdaudience=lambda reader:reader=='reader',
        jdvoices=lambda person,act,principal,role,subject,code,point:(person,act,principal,role,subject,point)==('person','act','person','role','topic','anchor') and matches(code,data['message']),
        ab=lambda faculty,person,point:(faculty,person)==('faculty','person'),
        ac=lambda person,faculty,act,point:performed and (person,faculty,act,point)==('person','faculty','act','anchor'),
        dg=lambda act,point:performed and (act,point)==('act','anchor'),f3=lambda person,act,point:(person,act,point)==('person','act','anchor'),f2=conveys,
        ca=lambda person,act,point:(person,act,point)==('person','act','anchor'),
        cb=lambda person,act,role,point:(person,act,role,point)==('person','act','role','anchor'),
        cc=lambda act,recipient,point:(act,recipient,point)==('act','world','anchor'),
        cd=lambda role,point:role=='role',ce=lambda recipient,point:recipient=='world',aa=lambda person:person in ('person','reader'),
        h6n=lambda reader,point:reader=='reader',h6t=lambda recipient,reader,point:(recipient,reader)==('world','reader'),
        h6u=lambda act,channel,subject,code,point:(act,channel,subject,point)==('act','channel','topic','anchor') and matches(code,data['message']))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN+('older','newer','judgment'),situations=SCENES,
        primitives=model,max_steps=100_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def attribution(doc):
    doc=deepcopy(doc);doc['statements']=doc['statements'][-1:];rows=[]
    for attributed in (False,True):
        def forbidden(*args):raise AssertionError('Attribution executed policy or comparative speech')
        def report(node,author,code,scope,point):
            assert (node,author,scope,point)==('node','author','scope','point')
            assert code.rank==3 and json.loads(code.syntax)==dict(kind='call',symbol='hzpinsight',arguments=[])
            return attributed
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(hznreport=report,hzpnode=lambda:'node',wa=lambda:'author',hzpscope=lambda:'scope',wh=lambda:'point')
        result=evaluate_document(doc,individuals=('node','author','scope'),situations=('point',),primitives=model)
        assert result==[dict(kind='assert',value=attributed)];rows.append(result)
    return rows


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text),attribution=attribution(doc))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    parent,source=[parse((ROOT/p).read_text(encoding='utf-8')) for p in (PARENT,SOURCE)]
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert source['statements'][:-1]==parent['statements'][:-1]
    judgments=[]
    for performed,judgment,candidate,actual in product((False,True),repeat=4):
        result=values(performed,judgment,candidate,actual)
        assert result==[True,performed and judgment and candidate,actual]+[True]*5+[actual]
        judgments.append(dict(performed=performed,judgment=judgment,candidate_better=candidate,actual_better=actual,result=result))
    permissions=[]
    for gs,cs,gp,cp in product((False,True),repeat=4):
        general=not gs or gp;comparative=not cs or cp;joint=general and comparative
        result=values(general_selected=gs,comparative_selected=cs,general_permission=gp,comparative_permission=cp)
        assert result==[True,True,False,comparative,general,joint,joint,joint,False]
        permissions.append(dict(selected=[gs,cs],granted=[gp,cp],result=result))
    contrasts={}
    for variant in ('other_person','other_matter','reversed_forms','other_criterion','other_subject','empty_candidates','same_form','wrong_message'):
        result=values(variant=variant);assert result==[True,False,False]+[True]*5+[False]
        contrasts[variant]=result
    for variant,expected in (
        ('wrong_target',[True,True,False,False,True,False,False,False,False]),
        ('old_policy_prospects',[True,True,False,True,True,True,False,False,False]),
        ('old_safety_awareness',[True,True,False,True,True,True,True,False,False]),
        ('split_outcomes',[True,True,False,True,True,True,False,False,False])):
        result=values(variant=variant);assert result==expected
        contrasts[variant]=result
    uncached=values(indices=(0,1,2,8),memoize=False)
    assert uncached==values(indices=(0,1,2,8))==[True,True,False,False]
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0016')
    phrases=('sieht ein','in Ansehung seiner Gesetzgebung',
        'es ohne Gefahr sei, seinen Unterthanen zu erlauben, von ihrer eigenen Vernunft öffentlichen Gebrauch zu machen',
        'und ihre Gedanken über eine bessere Abfassung derselben','der Welt öffentlich vorzulegen')
    segments=[]
    for phrase in phrases:
        start=unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase,
            status='explicit_interpretive_annotation',definitions=['rru','rrv','rrw','rrx','rry','rrz','hzptarget','hzpcomparative','hzppolicy','hzpsafety','hzpinsight','hzpattribution']))
    paths=[PARENT,SOURCE,CORE,BASIS,'scripts/compose_comparative_speech.py','scripts/check_comparative_speech.py','tests/test_comparative_speech.py',
        'scripts/check_policy_recognition.py','scripts/check_public_permission_risk.py','scripts/compose_public_permission_risk.py','scripts/compose_topic_scopes.py',
        'examples/v016/policy-recognition-core.noema','examples/v016/public-permission-risk-core.noema',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py',
        'artifacts/written-units-v1/kant-1784.json']
    result=dict(status='partial_comparative_public_speech_source_connection',documents=documents,
        parent_declarations_and_first_16_statements_preserved=True,revised_fragment_attributions=1,roundtrips=True,
        finite_interpretation=dict(judgments=judgments,permissions=permissions,contrasts=contrasts,uncached_action_comparison=uncached),
        alignment=dict(semantic_completion=False,segments=segments),limitations=basis()['unresolved'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Comparative judgment, constructed speech and joint permission verified')


if __name__=='__main__':main()
