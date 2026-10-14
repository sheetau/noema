"""Check past appointment witnesses, exact terms and independent current duties."""
import argparse
import hashlib
from itertools import product
import json
import re

from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_closed_policies import quoted
from scripts.check_rod_setup import guarded,callbacks
from scripts.compose_appointment_terms import ROOT,PARENT,BUILDERS,APPOINTS,TERMS

REPORT=ROOT/'reports/appointment-terms-v1.json'
TRUE='e[n p a b][n p a b]'
EXTRA=('r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] d.r zg[] d.'
    'r zh[] '+APPOINTS+'.r zi[] '+TERMS+'.r zj[a a d] c.'
    'd zk[person a activity a] e[b scene[k zj[v person v activity v scene]]].'
    'd zl[person a activity a] e[b scene[k zj[v person v activity v scene]]].')
TARGET='r[p zk]'
OPEN='k zd[] k za[] k zc[] k zb[] '+TARGET+' '+TRUE+' k zg[]'
RECORD='k ze[] k zd[] k za[] k zc[] k zb[] '+TARGET+' '+TRUE+' k zf[] k zg[]'
QUERIES=('q[k hzbl['+RECORD+' k zh[] k zi[]]].'
    'q[k hzbm['+OPEN+' k zh[] k zi[]]].q[k hzbn['+OPEN+' k zh[] k zi[]]].'
    'q[k h7a['+OPEN+']].q[t[c[s['+TARGET+']][k za[] k zb[]]][k zg[]]].')
DOMAIN=('person','activity','role','issuer','event','other')
SCENES=('past','middle','now','future','elsewhere')


def setup(text):
    return candidate(text,EXTRA+QUERIES)


def model_for(doc,bits=(True,True,True,True,True,True,True),variant='baseline',rename=lambda x:x,target=None):
    occurred,delegated,appointed,term,required,current,performed=bits
    n=rename
    expected_target=syntax(target or quoted('function_ref','zk'))
    alternate_target=syntax(quoted('function_ref','zl'))
    # Reinterpret a closed Noema record; these strings name model individuals,
    # not words recognized in natural-language input.
    wanted_time='now' if variant=='present_only' else 'future' if variant=='future_only' else 'past'
    def matches(actual,expected,category,fields):
        expected=list(expected)
        for i,field in enumerate(fields):
            if variant==category+'_'+field:expected[i]='elsewhere' if field=='time' else 'other'
        return list(actual)==[n(x) for x in expected]
    def appointment(event,issuer,person,role,time):
        events=('event','other') if variant=='two_appointments' else ('event',)
        return appointed and any(matches((event,issuer,person,role,time),(e,'issuer','person','role',wanted_time),
            'appointment',('event','issuer','person','role','time')) for e in events)
    def terms(event,activity,target,positive,time):
        e='other' if variant=='split_event' else 'event'
        t='middle' if variant=='split_time' else wanted_time
        events=(e,'other') if variant=='two_appointments' else (e,)
        desc=alternate_target if variant=='terms_description' else expected_target
        return term and positive==(variant not in ('terms_polarity','negative')) and target.syntax==desc and any(
            matches((event,activity,time),(item,'activity',t),'terms',('event','activity','time')) for item in events)
    def norm(issuer,person,role,activity,target,positive,time):
        return required and positive==(variant not in ('norm_polarity','negative')) and target.syntax==(
            alternate_target if variant=='norm_description' else expected_target) and matches((issuer,person,role,activity,time),
            ('issuer','person','role','activity','now'),'norm',('issuer','person','role','activity','time'))
    def history(person,context,point):
        allowed=('now',) if variant=='foreign_history' else ('past','middle','now','future')
        return matches((person,context),('person','now'),'history',('person','time')) and point in tuple(map(n,allowed))
    def earlier(first,second,context):
        order=tuple(map(n,('past','middle','now','future')))
        if context!=n('now'):return False
        if variant=='cyclic_order' and (first,second)==(n('now'),n('past')):return True
        if variant=='reflexive_order' and first==second==n('past'):return True
        if variant=='incomparable_order' and {first,second}=={n('middle'),n('now')}:return False
        if variant=='nontransitive_order' and (first,second)==(n('past'),n('now')):return False
        return first in order and second in order and order.index(first)<order.index(second)
    def occurs(event,time):
        events=('event','other') if variant in ('split_event','two_appointments') else ('event',)
        times=(wanted_time,'middle') if variant=='split_time' else (wanted_time,)
        return occurred and event in tuple(map(n,events)) and time in tuple(map(n,times))
    def entrusted(person,role,time):
        if (person,role)!=(n('person'),n('role')):return False
        return current if time==n('now') else delegated and time in tuple(map(n,('past','middle','future')))
    model=guarded(doc)
    model.update({name:(lambda value=value:n(value)) for name,value in zip(
        ('za','zb','zc','zd','ze','zf','zg'),('person','activity','role','issuer','event','past','now'))})
    model.update(ia=history,ic=earlier,dg=occurs,cf=entrusted,h7a=norm,
        zj=lambda person,activity,time:performed and (person,activity,time)==tuple(map(n,('person','activity','now'))))
    callbacks(doc,model,{'zh':appointment,'zi':terms})
    primitive_names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {name:value for name,value in model.items() if name in primitive_names}


def evaluate(doc,model,rename=lambda x:x):
    return values(doc,model,tuple(map(rename,DOMAIN)),tuple(map(rename,SCENES)))


def finite_checks(texts):
    docs=[setup(text) for text in texts]
    cases=[]
    for bits in product((False,True),repeat=7):
        occurred,delegated,appointed,term,required,current,performed=bits
        past=occurred and delegated and appointed and term
        expected=[past,past,past and required,required,performed]
        rows=[evaluate(doc,model_for(doc,bits)) for doc in docs]
        if rows!=[expected]*2:raise ValueError('Appointment/current duty collapsed: '+repr((bits,rows)))
        cases.append(dict(states=list(bits),results=expected))
    variants=(
        'appointment_event','appointment_issuer','appointment_person','appointment_role','appointment_time',
        'terms_event','terms_activity','terms_time','terms_description','terms_polarity',
        'norm_issuer','norm_person','norm_role','norm_activity','norm_time','norm_description','norm_polarity',
        'history_person','history_time','foreign_history','split_event','split_time','present_only','future_only',
        'cyclic_order','reflexive_order','incomparable_order','nontransitive_order','two_appointments')
    contrasts={}
    for variant in variants:
        expected=([True,True,False,False,True] if variant.startswith('norm_') else
            [True]*5 if variant=='two_appointments' else [False,False,False,True,True])
        rows=[evaluate(doc,model_for(doc,variant=variant)) for doc in docs]
        if rows!=[expected]*2:raise ValueError('Appointment witness differs: '+repr((variant,rows)))
        contrasts[variant]=expected
    refusals={}
    for doc in docs:
        normonly={**doc,'statements':doc['statements'][:4]}
        model=model_for(doc);model['zj']=guarded(doc)['zj']
        if evaluate(normonly,model)!=[True]*4:raise ValueError('Terms executed the target')
        try:evaluate(doc,model)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unknown target replaced')
        for name in ('zh','zi','ia','ic','dg','cf','h7a'):
            missing=model_for(doc);missing[name]=guarded(doc)[name]
            try:evaluate(normonly,missing)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown appointment relation replaced: '+name)
            refusals[name]=True
    rename=lambda value:{'person':'researcher','issuer':'laboratory','role':'post','activity':'procedure','event':'hiring'}.get(value,value)
    transfer=[evaluate(doc,model_for(doc,rename=rename),rename) for doc in docs]
    if transfer!=[[True]*5]*2:raise ValueError('Transferred appointment differs')
    # A bad named witness must not erase a different valid existential witness.
    alternate=[]
    for doc in docs:
        model=model_for(doc);model['ze']=lambda:'other'
        row=evaluate(doc,model)
        if row!=[False,True,True,True,True]:raise ValueError('Named witness replaced existential scope')
        alternate.append(row)
    negative=[]
    for text in texts:
        doc=candidate(text,EXTRA+QUERIES.replace(TRUE,'u['+TRUE+']'))
        row=evaluate(doc,model_for(doc,variant='negative'))
        if row!=[True]*5:raise ValueError('Negative appointment terms differ')
        negative.append(row)
    return dict(cases=cases,binding_and_history_contrasts=contrasts,unknown_relations_refused=refusals,
        named_and_existential_witnesses=alternate,target_not_executed_by_appointment_or_requirement=True,
        unknown_target_refused=True,laboratory_interpretation=transfer[0],standalone_agrees=True,
        negative_terms_with_target_actually_true=negative,current_delegation_and_performance_do_not_determine_past=True)


def teaching_checks(text):
    from scripts.check_adopted_standards import source_setup
    from scripts.check_assessed_payments import description
    from scripts.compose_prescribed_teaching import CRITERION
    from noema.specialization import specialize_definition
    original=source_setup(text)
    # Both definitions live in one document: a name from another document is
    # not a substitute for a separately bound definition in this scope.
    standard=description(original[0],'l['+CRITERION+'][p zu p zt]')
    extended=specialize_definition(original[0],'hzbi','hzbo',{7:standard}).document
    names={name:'zs'+name[1:] for name in ('za','zb','zc','zd','ze','zf','zg','zh','zi','zj','zk','zl')}
    if set(names.values()) & {d['name'] for d in extended['declarations']}:
        raise ValueError('Teaching fixture namespace collision')
    extra=re.sub(r'\b(?:'+ '|'.join(names)+r')\b',lambda match:names[match.group()],EXTRA+QUERIES)
    doc=candidate(format_graph(extended,'compact'),extra)
    reference=setup(text)
    teaching=original[1]
    def replace(node):
        if isinstance(node,dict):
            if node==quoted('function_ref',names['zk']):return teaching
            return {name:replace(value) for name,value in node.items()}
        if isinstance(node,list):return [replace(value) for value in node]
        return node
    doc['statements']=replace(doc['statements'][:4])
    doc=parse(format_graph(doc,'compact'))
    def alternate(node):
        if isinstance(node,dict):
            if node=={'kind':'function_ref','symbol':'hzbj'}:
                return {'kind':'function_ref','symbol':'hzbo'}
            return {name:alternate(value) for name,value in node.items()}
        if isinstance(node,list):return [alternate(value) for value in node]
        return node
    other=alternate(teaching)
    if syntax(other)==syntax(teaching):raise ValueError('Teaching alternative was not distinct in the same scope')
    def fixture(target):
        result=guarded(doc)
        result.update({names.get(name,name):value for name,value in model_for(reference,target=target).items()})
        return result
    model=fixture(teaching)
    accepted=evaluate(doc,model)
    if accepted!=[True]*4:raise ValueError('Concrete teaching terms differ')
    rejected=evaluate(doc,fixture(other))
    if rejected!=[False]*4:raise ValueError('Other adopted standard replaced teaching target')
    # All presentation, criteria and message-truth callbacks remain guarded.
    return dict(same_closed_teaching_description=accepted,reordered_standard_description=rejected,
        target_not_evaluated=True,alternatives_share_one_definition_scope=True,static_specialization=original[-1])


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpt='er ist auf diese Bedingung angenommen worden'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous appointment passage')
    start=unit['text'].index(excerpt)
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
        definitions=['hzbl','hzbm','hzbn'],status='partial',review_ja='同じ過去の任用行為・職務・条件の記述を結び、現在の要求と区別する。任用と条件の関係は明示的な入力であり、制度の全説明、dennの正当化、全教示への範囲は未完。')],
        semantic_completion=False,new_source_ranges=True)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored appointment differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Appointment roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
        sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_appointment_terms.py','scripts/check_appointment_terms.py',
        'scripts/check_conditional_release.py','scripts/check_described_appraisals.py',
        'scripts/check_described_explanations.py','scripts/check_rod_setup.py',
        'scripts/check_public_assessment.py','scripts/check_closed_policies.py',
        'scripts/check_adopted_standards.py','scripts/check_prescribed_teaching.py',
        'scripts/check_assessed_payments.py','scripts/compose_prescribed_teaching.py',
        'scripts/compose_adopted_standards.py','noema/specialization.py','noema/description_templates.py',
        'noema/finite_semantics.py','noema/extraction.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_past_appointment_with_exact_terms',documents=documents,sizes=sizes,
        finite=finite_checks(texts[1:]),teaching=teaching_checks(texts[1]),alignment=alignment(),new_definitions=6,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Appointment report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Past appointment, shared terms and independent present obligations checked')


if __name__=='__main__':main()
