import pytest

from noema.semantics import SemanticError
from noema.wic_tsv_data import parse_split, audit


def test_word_index_resolves_repeated_target_and_preserves_whitespace():
    rows = parse_split('bank\t2\t  bank   beside bank .\n', 'a financial institution\n', 'F\n', 'train')
    row = rows[0]
    assert row['text'] == '  bank   beside bank .'
    assert row['start'] == 16 and row['end'] == 20 and row['span'] == 'bank'
    assert row['matches'] is False and 'concept' not in row


@pytest.mark.parametrize('example,definition,label', [
    ('x\t0\tx\ny\t0\ty', 'one', 'T'), ('x\t4\tx', 'one', 'T'),
    ('y\t0\tx', 'one', 'T'), ('x\t-1\tx', 'one', 'T'),
    ('x\t0\tx', '', 'T'), ('x\t0\tx', 'one', '1')])
def test_bad_alignment_is_not_silently_repaired(example, definition, label):
    with pytest.raises(SemanticError):
        parse_split(example, definition, label, 'train')


def test_audit_reports_leakage_and_duplicate_inputs_without_hiding_them():
    train = parse_split('bank\t0\tbank\nbank\t0\tbank', 'a shore\na shore', 'T\nT', 'train')
    dev = parse_split('bank\t0\tbank', 'a shore', 'T', 'dev')
    result = audit({'train': train, 'dev': dev})
    assert result['splits']['train']['duplicate_input_rows'] == 1
    assert result['train_dev_overlap'] == {'pairs': 1, 'contexts': 1, 'lemmas': 1}
    train[1]['matches'] = False
    with pytest.raises(SemanticError, match='Conflicting'):
        audit({'train': train, 'dev': dev})
