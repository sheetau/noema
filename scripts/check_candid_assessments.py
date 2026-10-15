"""Check explicit scope coverage, personal evaluations and signed disclosure."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_candid_assessments import ROOT,PARENT,LIBRARY,EXAMPLE,BASIS,DISCLOSURE,build,basis

REPORT=ROOT/'reports/candid-assessments-v1.json'
PEOPLE=('person','other','act','otheract','topic','othertopic','role','world','reader','channel','first','second','outside')
POINTS=('anchor','candidate','elsewhere')
RECORDS=('first','second')


@lru_cache(maxsize=1)
def setup():
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+'r jdoutside[] a.')
    doc['declarations'].insert(0,doc['declarations'].pop())
    original=next(d for d in doc['declarations'] if d['name']=='jdstandardone')
    alias=deepcopy(original);alias['name']='jdstandardalias';doc['declarations'].append(alias)
    doc['statements']=statements;doc=parse(format_graph(doc,'compact'))
    lookup={d['name']:d for d in doc['declarations']}
    polarity_codes=lookup['jdpolarities']['body']['arguments'][1:]
    return dict(document=doc,signs=[code['body'] for code in polarity_codes])


def values(records=RECORDS,scope=RECORDS,signs=(True,False),candidate=(True,False),actual=(True,True),
           delivered=(True,True),judgments=(True,True),candidates=(True,True),variant='baseline',memoize=True):
    data=setup();doc=deepcopy(data['document'])
    for decl in doc['declarations']:
        if decl['name'] in ('jdcomplete','jdcritical'):
            sequence=decl['body']['arguments'][[n for n,_ in DISCLOSURE].index('records')]
            sequence['items']=[dict(kind='call',symbol='jd'+name,arguments=[]) for name in records]
    doc=parse(format_graph(doc,'compact'))
    record_index={'first':0,'second':1,'outside':0}
    def forbidden(*args):raise AssertionError('Unexpected primitive in assessment disclosure')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def truth(index,subject,point):
        if variant=='unknown_truth':raise ValueError('Unknown criterion evaluation')
        return subject=='topic' and (actual[index] if point=='anchor' else candidate[index])
    def choose_criterion(record,left,right):return (left,right)[record_index[record]]
    def choose_polarity(record,positive,negative):return positive if signs[record_index[record]] else negative
    def selected(record,point):
        if variant=='unknown_scope':raise ValueError('Unknown disclosure scope')
        return record in scope and point=='anchor'
    def owner(person,record,point):
        if record not in record_index:return False
        index=record_index[record]
        return judgments[index] and (person,point)==('other' if variant=='other_person' and index==1 else 'person','anchor')
    def matters(record,subject,point):
        return record in record_index and (subject,point)==('othertopic' if variant=='other_subject' and record_index[record]==1 else 'topic','anchor')
    def linked(record,code,polarity,point):
        if record not in record_index:return False
        index=record_index[record]
        symbol='jdstandardalias' if variant=='other_criterion' and index==0 else ('jdstandardone','jdstandardtwo')[index]
        expected=not signs[index] if variant=='wrong_polarity' and index==1 else signs[index]
        return point=='anchor' and polarity==expected and json.loads(code.syntax)==dict(kind='function_ref',symbol=symbol)
    def chosen(record,context,point):
        if variant=='unknown_candidates':raise ValueError('Unknown judgment candidates')
        return record in record_index and candidates[record_index[record]] and (context,point)==('anchor','candidate')
    messages=[]
    for index in (0,1):
        sign=not signs[index] if variant=='wrong_message' and index==1 else signs[index]
        messages.append(dict(kind='apply',function=dict(kind='function_ref',symbol='rsa'),arguments=[
            dict(kind='function_ref',symbol=('jdstandardone','jdstandardtwo')[index]),data['signs'][0 if sign else 1]]))
    def message_index(code):
        syntax=json.loads(code.syntax)
        return next((i for i,message in enumerate(messages) if syntax==message),None)
    def conveys(act,reader,subject,code,point):
        index=message_index(code)
        return index is not None and delivered[index] and (act,reader,subject,point)==(
            'otheract' if variant=='other_activity' and index==1 else 'act','reader','topic','anchor')
    def voices(person,act,principal,role,subject,code,point):
        index=message_index(code)
        return index is not None and (person,act,principal,role,subject,point)==('person','act',
            'other' if variant=='other_principal' and index==1 else 'person','role','topic','anchor')
    model.update(jdfirst=lambda:'first',jdsecond=lambda:'second',jdoutside=lambda:'outside',jdperson=lambda:'person',
        jdact=lambda:'act',jdsubject=lambda:'topic',jdrole=lambda:'role',jdrecipient=lambda:'world',jdchannel=lambda:'channel',jdcontext=lambda:'anchor',
        jdmetone=lambda subject,point:truth(0,subject,point),jdmettwo=lambda subject,point:truth(1,subject,point),
        jdscope=selected,jdchoosecriterion=choose_criterion,jdchoosepolarity=choose_polarity,
        jdjudgments=owner,jdmatters=matters,jdlinked=linked,jdcandidates=chosen,
        jdaudience=lambda reader:reader=='reader',jdvoices=voices,
        dg=lambda act,point:(act,point)==('act','anchor'),f3=lambda person,act,point:(person,act,point)==('person','act','anchor'),f2=conveys,
        ca=lambda person,act,point:(person,act,point)==('person','act','anchor'),
        cb=lambda person,act,role,point:(person,act,role,point)==('person','act','role','anchor'),
        cc=lambda act,recipient,point:(act,recipient,point)==('act','world','anchor'),cd=lambda role,point:role=='role',
        ce=lambda recipient,point:recipient=='world',aa=lambda person:person in ('person','reader'),
        h6n=lambda reader,point:reader=='reader',h6t=lambda recipient,reader,point:(recipient,reader)==('world','reader'),
        h6u=lambda act,channel,subject,code,point:message_index(code) is not None and (act,channel,subject,point)==('act','channel','topic','anchor'))
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=POINTS,primitives=model,
        max_steps=5_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def quotation_case():
    doc=deepcopy(setup()['document']);doc['statements']=[]
    text='r jdinspect[i[h[a] f]] c.q[k jdinspect[k rsb[r[p jdstandardtwo] r[u[e[n p a b][n p a b]]]]]].'
    doc=parse(format_graph(doc,'compact')+text)
    expected=dict(kind='apply',function=dict(kind='function_ref',symbol='rsa'),arguments=[
        dict(kind='function_ref',symbol='jdstandardtwo'),setup()['signs'][1]])
    def forbidden(*args):raise AssertionError('Quoted assessment executed an unknown criterion')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    model['jdinspect']=lambda code:code.rank==0 and json.loads(code.syntax)==expected
    result=evaluate_document(doc,individuals=('dummy',),situations=('point',),primitives=model)
    assert result==[dict(kind='ask',value=True)]
    return result


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    parent={d['name']:d for d in parse((ROOT/PARENT).read_text(encoding='utf-8'))['declarations']}
    library=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    inherited=[d for d in library['declarations'] if d['name'] in parent]
    assert inherited and all(d==parent[d['name']] for d in inherited)
    additions=[d for d in library['declarations'] if d['name'] not in parent]
    assert len(additions)==7 and all(d['kind']=='definition' for d in additions)
    matrix=[]
    for first,second,current1,current2,delivered1,delivered2 in product((False,True),repeat=6):
        complete=first and not second and delivered1 and delivered2
        result=values(candidate=(first,second),actual=(current1,current2),delivered=(delivered1,delivered2))
        assert result==[complete,complete,current2]
        matrix.append(dict(candidate=[first,second],actual=[current1,current2],delivered=[delivered1,delivered2],result=result))
    scopes=[]
    for records,scope,expected in (
        ((),(),[False,False,True]),(('first',),RECORDS,[False,False,True]),
        (RECORDS,('first',),[False,False,True]),(('first',),('first',),[True,False,True]),
        (('second',),('second',),[True,True,True]),(('second','first'),RECORDS,[True,True,True]),
        (('first','second','first'),RECORDS,[True,True,True]),(('first','second','outside'),RECORDS,[False,False,True])):
        result=values(records=records,scope=scope);assert result==expected
        scopes.append(dict(records=records,scope=scope,result=result))
    contrasts={}
    for variant in ('other_person','other_subject','other_criterion','wrong_polarity','wrong_message','other_activity','other_principal'):
        result=values(variant=variant);assert result==[False,False,True];contrasts[variant]=result
    uncached=values(memoize=False);assert uncached==values()==[True,True,True]
    paths=[PARENT,LIBRARY,EXAMPLE,BASIS,'scripts/compose_candid_assessments.py','scripts/check_candid_assessments.py',
        'tests/test_candid_assessments.py','scripts/compose_speech_principals.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    result=dict(status='experimental_scope_relative_disclosure_not_complete_candor',documents=documents,
        inherited_public_presentation_unchanged=True,new_library_primitives=0,roundtrips=True,
        finite_interpretation=dict(matrix=matrix,scopes=scopes,contrasts=contrasts,uncached=uncached,quotation=quotation_case()),
        motivation='Kant u0016: a candidate condition for candid criticism; not integrated into the source permission or counted as new source coverage.',
        limitations=basis()['unresolved'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Declared assessment scope, signed public presentation and non-factivity verified')


if __name__=='__main__':main()
