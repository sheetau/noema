"""Keep the opening's attribution, qualifications and text order after decoding.

These are the retained discourse-model checks separated from historical file
generation and font checks. Every evaluated statement must occur in the actual
recovered Native document, and the shared adapter checks its definition bodies.
"""
from itertools import product
import pytest
from scripts.shared_modality import renamed
import test_early_semantics_visible as diagnostics

RESULTS={}
MODEL_GROUPS={
    'apparent_asymmetry':('discourse_model',3,[('eir3',5),('eisa5',5),('ue',3)]),
    'moving_magnet_case':('discourse_model',3,[('eir3',5),('uf',4),('ue',3)]),
    'moving_conductor_case':('discourse_model',5,list(enumerate((5,6,7,7,3)))),
    'relativity_conjecture':('presentation_model',5,[('eir3',5),('eisb2',6),('eisb3',6),('eisa5',5),('ue',3)]),
    'two_postulates':('presentation',5,list(enumerate((5,6,5,5,3)))),
}
TWO_ROW_GROUPS={
    'sufficient_postulates':('eigk','eiscu'),
    'ether_dispensability':('eigu','eisdc'),
    'kinematic_foundation':('eihd','eisdl'),
    'kinematic_difficulties':('eihk','eisds'),
}


def source_statements(ns):
    actual=diagnostics.check.restored()['document']['statements']
    for path in (ns['CORE'],ns['FULL']):
        doc=ns['parse'](ns['read'](path))
        doc['statements']=doc['statements'][-1:]
        assert len(doc['statements'])==1
        assert renamed(doc['statements'][0],diagnostics.mapping()) in actual,('Unrecovered statement',path)
        yield doc


def value(result):
    if isinstance(result,list):
        assert len(result)==1
        result=result[0]['value']
    assert type(result) is bool
    return result


@pytest.mark.parametrize('stem',MODEL_GROUPS)
def test_original_multiclause_presentation_bindings(stem):
    ns=diagnostics.namespace(stem);model_name,width,arities=MODEL_GROUPS[stem]
    model=ns[model_name];evaluate=ns['evaluate'];cases=0
    for doc in source_statements(ns):
        for bits in product((False,True),repeat=width):
            assert value(evaluate(doc,model(bits)))==all(bits)
            cases+=1
        for row,arity in arities:
            for slot in range(arity):
                assert not value(evaluate(doc,model(bad=(row,slot))))
                cases+=1
        if stem in ('relativity_conjecture','two_postulates'):
            assert not value(evaluate(doc,model(collision=True)))
            cases+=1
    RESULTS[stem]=dict(cases=cases,all_attribution_slots_checked=True,quoted_content_not_executed=True)


@pytest.mark.parametrize('stem',TWO_ROW_GROUPS)
def test_original_message_attribution_and_preceding_sentence(stem):
    ns=diagnostics.namespace(stem);message,node=TWO_ROW_GROUPS[stem]
    rows={'eir3':{('b','b','a',message,'a')},'ue':{('a','b','a')}}
    cases=0
    for doc in source_statements(ns):
        for bits in product((False,True),repeat=2):
            model=ns['base']()|{name:ns['relation'](rs if on else set()) for (name,rs),on in zip(rows.items(),bits)}
            assert value(ns['evaluate'](doc,model))==all(bits)
            cases+=1
        model=ns['base']()|{name:ns['relation'](rs) for name,rs in rows.items()}
        for name,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not value(ns['evaluate'](doc,model|{name:ns['relation']({bad})}))
                cases+=1
        assert not value(ns['evaluate'](doc,ns['base']()|{node:lambda:'a','eir3':lambda *xs:True,'ue':lambda *xs:True}))
        cases+=1
    RESULTS[stem]=dict(cases=cases,message_and_order_required=True,distinct_text_nodes=True,quoted_content_not_executed=True)
