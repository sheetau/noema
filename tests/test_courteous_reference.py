import pytest
from scripts import check_courteous_reference as check


@pytest.fixture(scope='module')
def result():return check.checks()


def test_same_use_name_target_and_context_are_required(result):
    assert result['generic_combinations']==8
    assert len(result['source_contrasts'])==12
    assert result['source_contrasts']['baseline']==[True]
    assert all(v==[False] for n,v in result['source_contrasts'].items() if n!='baseline')


def test_courtesy_is_not_sincere_regard_or_a_default_for_unknown_input(result):
    assert result['unknown_courtesy_refused'] and result['sincere_regard_not_entailed']


def test_notice_only_courtesy_cannot_satisfy_source_mention():
    rows=check.combined_checks()
    assert rows['citation_courtesy_only/baseline/baseline']==[True,True,True,False]
    assert rows['baseline/baseline/received_past']==[True,False,True,True]


def test_prior_statements_meanings_and_reviewed_bindings_are_unchanged():
    r=check.structure()
    assert r['previous_statements_preserved']==23
    assert r['signature_and_dateline_bindings_identical'] and r['previous_meaning_entries_identical']
