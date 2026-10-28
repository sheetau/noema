"""Small distinguishing domains for current transition and concession binding."""
from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts import check_kant_first_cause_content_visible as content
from scripts.shared_modality import call,v

DIAGNOSTICS={}
PEOPLE=('first','second')
SCENES=('first','second')


def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)


def fixture(roots,replacements,extra,statements):
    source={d['name']:deepcopy(d) for d in content.check.backprojection(content.check.restored()['document'])['declarations']}
    source.update(replacements);source.update({d['name']:d for d in extra})
    needed=set();pending=set(roots)|_references(statements)
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.update(_references(source[name].get('body')))
    selected=[d for n,d in source.items() if n in needed]
    # New fixture primitives must precede definitions that use them.
    selected.sort(key=lambda d:d['kind']!='primitive')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=selected,statements=statements))


def run(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives=values,max_steps=200000,memoize_definitions=False,memoize_expressions=False)]


def question(name):return dict(kind='ask',body=dict(kind='evaluate',content=call(name,call('jperson')),situation=call('jcontext')))


def test_prior_transition_witnesses_keep_every_slot_and_outer_subject_context():
    actual=content.recovered()['km'];replacement=deepcopy(actual)
    replacement['body']=call('jtransition',*(v(p['name']) for p in replacement['parameters']))
    doc=fixture(['kf'],{'km':replacement},[
        primitive('jtransition',[p['sort'] for p in actual['parameters']],'truth'),
        primitive('jperson',[],'individual'),primitive('jcontext',[],'situation')],[question('kf')])
    count=0
    # Only two values of each sort. Every possible event/before/after witness
    # gets its own distinguishing interpretation; this is a binding diagnostic.
    for person,context,event,before,after in product(PEOPLE,SCENES,PEOPLE,SCENES,SCENES):
        expected=(person,event,before,after,context)
        model=dict(jperson=lambda:person,jcontext=lambda:context,jtransition=lambda *args:args==expected)
        assert run(doc,model)==[True];count+=1
        for slot in (0,4):
            wrong=list(expected);wrong[slot]='second' if expected[slot]=='first' else 'first'
            model['jtransition']=lambda *args:args==tuple(wrong)
            assert run(doc,model)==[False]
    model['jtransition']=lambda *args:False;assert run(doc,model)==[False]
    DIAGNOSTICS['prior_binding']=dict(cases=count,domain_per_sort=2,recovered_roots=['kf'],
        abstracted_lower_relation='km via jtransition; current km separately exercised by relative_past diagnostics',
        every_witness_slot=True,outer_subject_and_context=True,full_domain_proof=False)


def test_current_concession_connects_prior_state_and_lifetime_attitude():
    source=content.recovered();replacements={}
    extra=[primitive('jperson',[],'individual'),primitive('jcontext',[],'situation')]
    for name,relation in [('kf','jprior'),('ie','jcontinuation')]:
        d=deepcopy(source[name]);person=d['parameters'][0]['name'];scene=d['body']['variable']
        d['body']=dict(kind='content',variable=scene,body=call(relation,v(person),v(scene)))
        replacements[name]=d;extra.append(primitive(relation,['individual','situation'],'truth'))
    doc=fixture(['kg'],replacements,extra,[question('kg')]);count=0
    def values(prior,continued,selected,variant='baseline'):
        expected=('second' if variant=='perspective' else 'first',
            'second' if variant=='person' else 'first',
            dict(kind='function_ref',symbol='ie' if variant=='description' else 'kf'),
            'second' if variant=='context' else 'first','second')
        def candidates(perspective,person,description,context,alternative):
            return selected and (perspective,person,json.loads(description.syntax),context,alternative)==expected
        return dict(jperson=lambda:'first',jcontext=lambda:'first',wa=lambda:'first',ke=candidates,
            jprior=lambda person,scene:person=='first' and prior[SCENES.index(scene)],
            jcontinuation=lambda person,scene:person=='first' and continued[SCENES.index(scene)])
    for bits in product((False,True),repeat=5):
        prior=bits[:2];continued=bits[2:4];selected=bits[4]
        assert run(doc,values(prior,continued,selected))==[prior[0] and continued[0] and selected and prior[1] and not continued[1]]
        count+=1
    for variant in ('perspective','person','description','context'):
        assert run(doc,values((True,True),(True,False),True,variant))==[False]
    model=values((True,True),(True,False),True)
    def unknown(*args):raise ValueError('Unspecified concession input')
    for name in ('jprior','jcontinuation','ke'):
        with pytest.raises(ValueError,match='Unspecified'):run(doc,model|{name:unknown})
    DIAGNOSTICS['concession_binding']=dict(cases=count,domain_per_sort=2,recovered_roots=['ja','jb','kg'],
        abstracted_lower_contents=['kf','ie'],
        lower_content_evidence=['relative_past source_checks and prior witness binding','scoped_attitude scope_checks'],
        perspective_person_description_context_distinguished=True,full_domain_proof=False)
