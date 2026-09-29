from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.compose_kant_interventions import composed
from scripts.check_binary_interventions import STATE


def test_comparison_reading_defines_effects_without_circularity():
    text, basis = composed()
    audit = audit_basis(parse(text), basis)
    assert audit['primitive_count'] == 18
    assert audit['definition_count'] == 27
    dependencies = audit['definition_dependencies']
    assert not {'mb', 'mc'} & set(dependencies['primitive_symbols'])
    assert dependencies['definition_primitive_dependencies']['mb'] == ['mp', 'mq']
    assert dependencies['definition_primitive_dependencies']['mc'] == ['mp', 'mq']
    assert {'ag', 'mp', 'mq'} <= set(dependencies['statement_primitive_dependencies'][1])
    assert not audit['semantic_equivalence_to_source_proven']


def test_kant_questions_reflect_the_explicit_model_and_comparison_direction():
    text, _ = composed()
    doc = parse(text)
    # Exercise the two questions. The preserved motto is tested in its original
    # draft; this check does not claim a real model of Kant's social processes.
    doc['statements'] = doc['statements'][1:]
    for sign, expected in [('positive', [[], [['x']]]), ('negative', [[['x']], []]), ('neutral', [[], []])]:
        seen = []
        def model(context):
            assert context == 'now'
            return FunctionValue(('individual', STATE), 'truth',
                                 lambda x, s: False if x == 'x' else s('x') if sign == 'positive' else not s('x') if sign == 'negative' else True)
        def comparison(property_, context):
            seen.append((property_.parameters, property_.result, context))
            return FunctionValue((STATE, STATE), 'truth', lambda left, right: not left('y') and right('y'))
        primitives = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        primitives.update(ma=lambda x, s: x == 'x', md=lambda: 'now', mp=model, mq=comparison, ao=lambda: 'x')
        actual = evaluate_document(doc, individuals=('x', 'y'), situations=('now',), primitives=primitives, max_steps=2000000)
        assert [r['answers'] for r in actual] == expected
        assert seen and all(item == (('individual',), 'content', 'now') for item in seen)
