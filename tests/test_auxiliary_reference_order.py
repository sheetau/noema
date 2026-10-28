"""Use real source spans to distinguish text order from dependency order."""
import pytest
from scripts import compose_auxiliary_reference_order as check


def test_old_reversed_order_fails_and_corrected_native_body_passes():
    assert check.run('ejzz') is False
    assert check.run('magauxmainclauseorder') is True
    assert check.run('magauxmainclauseorder', {'ue': lambda a, b, c: check.before(b, a, c)}) is False
    assert check.run('magauxmainclauseorder', {'zpv': lambda: 'zpt'}) is False


def test_whole_sentence_order_does_not_treat_contained_main_clause_as_prior():
    assert check.before('zps', check.WHOLE, 'ri')
    assert not check.before('zpv', check.WHOLE, 'ri')
    assert not check.before(check.WHOLE, 'zpt', 'ri')
    assert check.run('magauxwholepresentation') is True
    assert check.run('magauxwholepresentation', {'zps': lambda: 'zpv'}) is False
    assert check.run('magauxwholepresentation', {check.WHOLE: lambda: 'zpv'}) is False


def test_whole_content_assertion_and_man_sieht_share_node_and_content():
    assert check.run('magauxwholeassertion') is True
    for relation in ('uh', 'zdg'):
        assert check.run('magauxwholeassertion', {relation: lambda *args: False}) is False
        def wrong_content(node, author, content, scope, context):
            return check.quoted(content) == 'ejzv'
        assert check.run('magauxwholeassertion', {relation: wrong_content}) is False
    for node in ('zpv', 'zpt', 'zpw'):
        assert check.run('magauxwholeassertion', {check.WHOLE: lambda node=node: node}) is False


def test_source_location_model_rejects_unknown_inputs():
    for args in [('unknown', 'zpt', 'ri'), ('zpv', 'unknown', 'ri'), ('zpv', 'zpt', 'other')]:
        with pytest.raises(ValueError):
            check.before(*args)
    with pytest.raises(ValueError):
        check.run('magauxmainclauseorder', {'zpt': lambda: 'unknown'})


def test_old_declarations_and_every_other_statement_are_preserved():
    old, new = check.parent(), check.document()
    assert new['declarations'][:len(old['declarations'])] == old['declarations']
    assert [i for i, (a, b) in enumerate(zip(old['statements'], new['statements'], strict=True)) if a != b] == [40, 41]
    assert len(new['declarations']) == len(old['declarations']) + 5
