"""Preserve hypothetical first person, ordered examples and ja presentation."""
from copy import deepcopy
import json
import pytest
from scripts import check_kant_three_examples_visible as check
from scripts.shared_modality import renamed
import test_kant_convenience_visible as parent

evaluate=parent.evaluate


def model(doc,variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();inverse={value:key for key,value in check.mapping().items()}
    def name(description):return renamed(json.loads(description.syntax),inverse)['symbol']
    def presentation(node,author,description,context):
        return (node,author,name(description),context)==('illustration','author',
            'sv' if variant=='wrong_conditional' else 'sy','body') and variant!='no_presentation'
    def examples(node,author,sequence,context):
        expected=['st','ss','su'] if variant=='swapped_examples' else ['ss','st'] if variant=='missing_example' else ['ss','st','su']
        return variant!='closed_list' and (node,author,context)==('illustration','author','body') and [name(d) for d in sequence.items]==expected
    def recognizable(node,author,premise,conclusion,context):
        return variant!='no_marker' and (node,author,name(premise),name(conclusion),context)==(
            'convenience' if variant=='wrong_node' else 'illustration',
            'other' if variant=='wrong_author' else 'author',
            'sx' if variant=='reversed_scope' else 'sy' if variant=='wrong_premise' else 'sv',
            'sv' if variant=='reversed_scope' else 'sy' if variant=='wrong_conclusion' else 'sx',
            'closing' if variant=='wrong_context' else 'body')
    before=values[voc._symbols['textbefore']]
    def ordered(first,second,context):
        if (first,second)==('causal','illustration'):return context=='body' and variant!='reverse_order'
        return before(first,second,context)
    values.update({voc._symbols[n]:fn for n,fn in dict(hypotheticalfirstpersonpresentation=presentation,
        nonexhaustiveexamplepresentation=examples,recognizableconditionalpresentation=recognizable,textbefore=ordered).items()})
    return values


def test_whole_source_and_prior_specialization_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:7]==check.previous.document()['statements']
    assert len(doc['declarations'])==278 and len(doc['statements'])==9
    assert len(check.source_excerpt()['declarations'])==260


def test_hypothetical_presentation_order_and_recognizable_scope():
    doc=check.restored()['document']
    variants=('baseline','no_presentation','wrong_conditional','swapped_examples','missing_example','closed_list',
        'no_marker','wrong_node','wrong_author','wrong_premise','wrong_conclusion','reversed_scope','wrong_context','reverse_order')
    for variant in variants:
        old=variant not in ('no_presentation','wrong_conditional','swapped_examples','missing_example','closed_list','reverse_order')
        new=variant in ('baseline','swapped_examples','missing_example','closed_list','reverse_order')
        assert evaluate(doc,model(doc,variant))==[True]*7+[old,new],variant


def test_unknown_presentation_inputs_are_rejected():
    doc=check.restored()['document'];voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified example presentation')
    for name in ('hypotheticalfirstpersonpresentation','nonexhaustiveexamplepresentation','recognizableconditionalpresentation'):
        with pytest.raises(ValueError,match='Unspecified'):evaluate(doc,model(doc)|{voc._symbols[name]:unknown})


def test_example_order_is_recovered_from_the_document():
    doc=deepcopy(check.restored()['document']);ds={d['name']:d for d in doc['declarations']}
    sequence=ds[check.names()['sz']]['body'];assert sequence['kind']=='sequence'
    sequence['items'][0],sequence['items'][1]=sequence['items'][1],sequence['items'][0]
    assert evaluate(doc,model(doc))==[True]*7+[False,True]
