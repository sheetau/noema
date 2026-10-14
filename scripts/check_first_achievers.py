"""Check first and uniquely first agents with same-target causal transitions."""
import argparse
import hashlib
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_scoped_nonprescription import SOURCE_FIELD
from scripts.compose_deserved_responses import STANDARD,RESPONSE,BASIS
from scripts.compose_first_achievers import ROOT,PARENT,BUILDERS,CONFIG,FIRST,GOAL,ACHIEVES,MEANINGS

REPORT=ROOT/'reports/first-achievers-v1.json'
POINTS=('start','early','late')
SCENES=(*POINTS,'outside')
DOMAIN=('leader','other','act','otheract','group','alice','bob','role','faith','governor')
EXTRA='r joperson[] a.r joother[] a.r joactivity[] a.r jotarget[] a.r joanchor[] d.r jopoint[] d.r johistory[d] c.r jobefore[d d] c.r jopeople[a] c.r joassessed[a d] c.r jogoal[a] e.r joachieves[a a a '+GOAL+' d] c.'
SOURCE_EXTRA='r jogovernor[] a.r jotopic[] a.r joview[] d.r jomembers[a a] c.r joroles[a] a.r joactivities[a a a d] c.r joevaluated[a a d] c.r joexecution[a a] e.r joresponse[a a a] e.r joworthy[a '+RESPONSE+' '+BASIS+' d] c.'


def setup(text,source=False):
    base=parse(text);base['statements']=[];base=parse(format_graph(base,'compact')+EXTRA+(SOURCE_EXTRA if source else ''))
    goal='p jogoal';facts='p joachieves';removed=0
    if source:
        fields=dict(source='k jogovernor[]',people='i[person a][k jomembers[v group v person]]',roles='p joroles',topic='k jotopic[]',anchor='k joview[]',context='v point',
            activities='p joactivities',descriptions='i[person a activity a][r[p joexecution]]',assessed='p joevaluated')
        goal='i[group a][b point['+k('hzfo',*(fields[n] for n,_ in SOURCE_FIELD))+']]'
        spec=specialize_definition(base,'hzge','joknownfacts',{2:description(base,goal)});base=spec.document;removed+=spec.disquotations_removed
        facts=k('joknownfacts','p johistory','p jobefore')
    refs=dict(history='p johistory',before='p jobefore',people='p jopeople',target='k jotarget[]',goal='r['+goal+']',achieves=facts,assessed='p joassessed',
        anchor='k joanchor[]',person='k joperson[]',activity='k joactivity[]',point='k jopoint[]')
    first=k('rod',*(refs[n] for n,_ in CONFIG));sole=k('roe',*(refs[n] for n,_ in CONFIG));at=lambda expr:'t['+expr+'][k joanchor[]]'
    queries=[k(n,*(refs[name] for name,_ in FIRST)) for n in ('rob','roc')]
    queries += [at('c['+first+'][k joperson[]]'),at('c['+sole+'][k joperson[]]'),at('c['+first+'][k joother[]]')]
    if source:
        actual='c['+facts+'][k joperson[] k joactivity[] k jotarget[] r['+goal+'] k jopoint[]]'
        standard='i[subject a response '+RESPONSE+' basis '+BASIS+'][b point['+k('joworthy','v subject','v response','v basis','v point')+']]'
        spec=specialize_definition(base,'ro6','jomerit',{1:description(base,first)});base=spec.document;removed+=spec.disquotations_removed
        merit=k('jomerit','r[p joresponse]','l['+STANDARD+']['+standard+']')
        queries=[actual]+queries+[at('c['+merit+'][k joperson[]]'),'e[r['+first+']][r['+first+']]']
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,source=source,goal=goal,facts=facts,first=first,refs=refs,goal_syntax=syntax(description(base,goal)),
        first_syntax=syntax(description(base,first)),execution_syntax=syntax(description(base,'p joexecution')) if source else None,response_syntax=syntax(description(base,'p joresponse')) if source else None,disquotations_removed=removed)


def common_model(data,variant='baseline'):
    model=guarded(data['document'])
    def before(first,last):
        if variant=='cyclic' and (first,last)==('late','start'):return True
        if variant=='unordered' and (first,last)==('start','early'):return False
        return first in POINTS and last in POINTS and POINTS.index(first)<POINTS.index(last)
    model.update(joperson=lambda:'leader',joother=lambda:'other',joactivity=lambda:'act',jotarget=lambda:'group',joanchor=lambda:'outside' if variant=='foreign_anchor' else 'late',
        jopoint=lambda:'late',johistory=lambda p:p in POINTS,jobefore=before,jopeople=lambda p:p in ('leader','other') and not (variant=='excluded_actor' and p=='leader'),
        joassessed=lambda person,point:variant!='unassessed' or (person,point)!=('other','start'))
    return model


def generic_model(data,bits=(False,False,True,False,False,False),variant='baseline'):
    model=common_model(data,variant)
    def achieves(person,activity,target,goal,point):
        if target!='group' or goal.syntax!=data['goal_syntax'] or point not in POINTS:return False
        if (person,activity) not in (('leader','act'),('other','otheract')):return False
        return bits[POINTS.index(point)+(0 if person=='leader' else 3)]
    model['joachieves']=achieves
    return model


def source_model(data,variant='baseline'):
    model=common_model(data,variant)
    def end(activity):
        if activity=='act':return 'late'
        if activity=='otheract' and variant in ('tie','earlier'):return 'late' if variant=='tie' else 'early'
        return None
    def reaches(point):return variant!='no_goal' and (variant=='already_true' or point=='late' or variant=='earlier' and point=='early')
    def rule(source,person,role,activity,desc,sign,point):
        return (source,role,activity)==('governor','role','act') and person in ('alice','bob') and desc.syntax==data['execution_syntax'] and reaches(point)
    model.update(jogovernor=lambda:'governor',jotopic=lambda:'faith',joview=lambda:'start',jomembers=lambda group,person:group=='group' and person in ('alice','bob'),
        joroles=lambda p:'role',joactivities=lambda person,act,topic,anchor:person in ('alice','bob') and (act,topic,anchor)==('act','faith','start'),
        joevaluated=lambda *args:True,aa=lambda p:p in ('leader','other','alice','bob'),h7a=lambda *args:False,h7b=rule,
        ag=lambda activity,earlier,later:earlier=='start' and end(activity)==later,
        la=lambda target,activity,earlier,later:variant!='no_affected' and target=='group' and earlier=='start' and end(activity)==later,
        dg=lambda activity,point:variant!='no_occurrence' and end(activity)==point,
        df=lambda person,activity,point:variant!='no_agent' and (person,activity) in (('leader','act'),('other','otheract')) and end(activity)==point,
        g3=lambda activity,target,desc,point:variant not in ('no_production','wrong_goal','wrong_target') and target=='group' and desc.syntax==data['goal_syntax'] and end(activity)==point,
        joworthy=lambda subject,response,basis,point:variant!='unworthy' and subject=='leader' and response.syntax==data['response_syntax'] and basis.syntax==data['first_syntax'])
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=DOMAIN,situations=SCENES,max_steps=48_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=6):
        earliest=next((i for i in range(3) if bits[i] or bits[3+i]),None)
        leader=earliest is not None and bits[earliest];other=earliest is not None and bits[3+earliest]
        candidate=leader and earliest==2
        expected=[candidate,candidate and not other,leader,leader and not other,other]
        result=values(data,generic_model(data,bits))
        if result!=expected:raise ValueError('First achiever differs from temporal table: '+repr((bits,result)))
        grid.append(dict(bits=list(bits),result=result))
    print('64 two-agent event histories passed',flush=True);rows=[]
    for text in texts[1:]:
        data=setup(text,True);cases={}
        for variant in ('baseline','tie','earlier','no_goal','already_true','no_affected','no_occurrence','no_agent','no_production','wrong_goal','wrong_target','unassessed','excluded_actor','foreign_anchor','cyclic','unordered','unworthy'):
            if variant=='tie':expected=[True,True,False,True,False,True,True,True]
            elif variant=='earlier':expected=[True,False,False,False,False,True,False,True]
            elif variant in ('unassessed','excluded_actor','foreign_anchor'):expected=[True,False,False,False,False,False,False,True]
            elif variant=='unworthy':expected=[True,True,True,True,True,False,False,True]
            elif variant=='baseline':expected=[True,True,True,True,True,False,True,True]
            else:expected=[False]*7+[True]
            result=values(data,source_model(data,variant))
            if result!=expected:raise ValueError('Source first achievement failed: '+repr((variant,result,expected)))
            cases[variant]=result
        rows.append(dict(cases=cases,disquotations_removed=data['disquotations_removed']));print('Source first-achievement contrasts passed',flush=True)
    return dict(grid=grid,source=rows,independent_temporal_table_oracle=True)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('First-achiever artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('First-achiever roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    phrase='der zuerst';start=unit['text'].index(phrase)
    paths={*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_first_achievers.py','scripts/check_first_achievers.py','scripts/compose_scoped_nonprescription.py','scripts/compose_deserved_responses.py',
        'scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py','noema/finite_semantics.py','noema/extraction.py','noema/specialization.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_first_achievement_with_same_target_and_causal_link',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=8,new_primitives=0,new_author_statements=0,alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('First-achiever record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('First achievement, unique priority, actual change and response worthiness remain distinct')


if __name__=='__main__':main()
