"""Preserve attribution and the explicit specialization of convenience cases."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_convenience_visible as check
from scripts.shared_modality import call,renamed
import test_kant_first_cause_visible as parent

# Population and nature occur only inside opaque quotations in these assertions.
# Their binding is covered by the prior connector. Avoid expanding the finite
# attribution domain with unused content-world referents and token-span objects.
DOMAIN=tuple(n for n in parent.DOMAIN if n not in ('population-span','nature-span','population','nature'))+('convenience','illustration')


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=False,memoize_expressions=False)]


def model(doc,variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();inverse={value:key for key,value in check.mapping().items()}
    oldsentence=values[voc._symbols['sentencereference']]
    oldclaim=values[voc._symbols['assertsdescribedcontent']]
    oldbefore=values[voc._symbols['textbefore']]
    def sentence(context,paragraph,index):
        if (context,paragraph)==('closing',2) and index in (2,3):return 'convenience' if index==2 else 'illustration'
        return oldsentence(context,paragraph,index)
    def claim(node,author,description,context):
        if node=='convenience':
            expected=('other' if variant=='wrong_author' else 'author','other' if variant=='wrong_context' else 'body')
            return (author,context)==expected and renamed(json.loads(description.syntax),inverse)==call('mx' if variant=='wrong_content' else 'un')
        return oldclaim(node,author,description,context)
    def before(first,second,context):
        if (first,second)==('causal','convenience'):return context=='body' and variant!='reverse_before'
        if (first,second)==('convenience','illustration'):return context=='body' and variant!='reverse_after'
        return oldbefore(first,second,context)
    values.update({voc._symbols[n]:fn for n,fn in dict(sentencereference=sentence,assertsdescribedcontent=claim,textbefore=before).items()})
    return values


def test_source_bodies_and_state_specialization_are_preserved():
    actual=check.restored()['document']
    assert check.backprojection(actual)==check.source_excerpt()
    assert check.specialized_backprojection(actual)==check.specialized_source()
    assert len(check.source_excerpt()['declarations'])==191 and len(actual['statements'])==7
    assert actual['statements'][:6]==check.previous.document()['statements']
    ds={d['name']:d for d in actual['declarations']}
    for name in ('uo','s3','uj'):assert ds[check.names()[name]]['kind']=='definition'


def test_whole_document_preserves_convenience_attribution_and_order():
    doc=check.restored()['document']
    for variant in ('baseline','wrong_author','wrong_context','wrong_content','reverse_before','reverse_after'):
        assert evaluate(doc,model(doc,variant))==[True]*6+[variant=='baseline'],variant


def test_recovered_case_definition_uses_the_original_state_description():
    doc=deepcopy(check.restored()['document']);n=check.names();voc=check.vocabulary()
    doc['statements'].append(dict(kind='ask',body=call(n['uj'],call(n['wa']),call(n['wh']),call(n['wh']))))
    inverse={value:key for key,value in check.mapping().items()};seen=[]
    def candidates(person,description,context,case):
        syntax=renamed(json.loads(description.syntax),inverse);seen.append((person,syntax,context,case))
        if (person,syntax,context,case)!=('author',dict(kind='function_ref',symbol='bf'),'body','body'):
            raise ValueError('Unknown convenience case')
        return True
    values=model(doc)|{voc._symbols['stateconveniencecandidate']:candidates}
    assert evaluate(doc,values)==[True]*8 and len(seen)==1
    with pytest.raises(ValueError,match='Unspecified'):evaluate(doc,model(doc))
    changed=deepcopy(doc)
    definition=next(d for d in changed['declarations'] if d['name']==n['uj'])
    definition['body']['arguments'][1]['body']['symbol']=check.mapping()['kf']
    with pytest.raises(ValueError,match='Unknown convenience case'):evaluate(changed,values)


def test_unknown_attribution_inputs_are_rejected():
    doc=check.restored()['document'];voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified convenience input')
    for name in ('sentencereference','assertsdescribedcontent','textbefore'):
        with pytest.raises(ValueError,match='Unspecified'):evaluate(doc,model(doc)|{voc._symbols[name]:unknown})
