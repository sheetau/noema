from functools import lru_cache
from scripts.check_kant_reference_anchor_spellings import build_report
from scripts.kant_reference_anchor_context import anchor_context, previous_context


report = lru_cache(maxsize=1)(build_report)


def test_names_definitions_referents_and_old_aliases_are_preserved():
    old, new = previous_context(), anchor_context()
    assert old.document == new.document
    assert old.declarations == new.declarations
    assert all(new.spellings.get(parts)==name for parts,name in old.spellings.items())
    assert len(new.declared_spellings)-len(old.declared_spellings) == 7


def test_density_explains_every_saved_svg_and_limits_redraw_scope():
    result = report()
    assert len(result['density']) == 40
    assert result['saved_circles'] == 2825
    assert result['saved_root_circles'] == 2342
    assert result['saved_grammar_circles'] == 483
    assert result['predicted_circles'] < result['saved_circles']
    assert len(result['changed_statements']) == 18
    assert all(r['saved_circles']==r['before']['circles'] for r in result['density'])


def test_all_seven_actual_word_diagnostics_shrink_without_changing_the_symbol():
    words = report()['words']
    assert len(words) == 7
    assert all(r['exact'] and r['after_circles'] < r['before_circles'] for r in words)


def test_actual_body_is_recovered_and_shrinks_with_multiple_branches():
    body = report()['actual_body']
    assert body['exact']
    assert body['circles'] < body['before_circles']
    assert body['branches'] > 0
