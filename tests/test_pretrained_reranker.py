from types import SimpleNamespace

import pytest
import torch

from noema.pretrained_reranker import FrozenReranker, concept_scores, raw_pairs


def fixture():
    rows = [{'text': 'A cold response.', 'span': 'cold', 'start': 2, 'end': 6, 'language': 'en', 'expected': 'secret'},
            {'text': 'A cold room.', 'span': 'cold', 'start': 2, 'end': 6, 'language': 'en', 'expected': None}]
    bank = [{'id': 'z', 'en': 'low temperature', 'ja': '低い温度'},
            {'id': 'a', 'en': 'emotionally distant', 'ja': 'よそよそしい'}]
    return rows, bank


def test_raw_pairs_do_not_include_labels_or_invent_target_instructions():
    rows, bank = fixture()
    pairs, ids = raw_pairs(rows, bank, 'isolated')
    assert ids == ['a', 'z'] and pairs == [('cold', 'emotionally distant'), ('cold', 'low temperature')] * 2
    assert raw_pairs(rows, bank, 'sentence')[0][0] == ('A cold response.', 'emotionally distant')
    rows[0]['expected'] = 'changed'
    assert raw_pairs(rows, bank, 'isolated')[0] == pairs
    rows[0]['start'] = 0
    with pytest.raises(ValueError, match='span'):
        raw_pairs(rows, bank, 'sentence')


def test_deduplication_retains_all_rows_and_column_identity():
    class Scorer:
        def score(self, pairs, progress=None):
            assert len(pairs) == 2
            return torch.tensor([3., -2.])
    rows, bank = fixture()
    matrix, audit = concept_scores(Scorer(), rows, bank, 'isolated')
    assert matrix.tolist() == [[3., -2.], [3., -2.]]
    assert audit == {'rows': 2, 'candidates': 2, 'pairs': 4, 'unique_pairs': 2}
    assert torch.equal(matrix, concept_scores(Scorer(), rows, list(reversed(bank)), 'isolated')[0])


def test_model_forward_rejects_long_and_nonfinite_inputs_without_truncation():
    reranker = FrozenReranker.__new__(FrozenReranker)
    calls = []
    def tokenizer(a, b, **kwargs):
        assert kwargs['truncation'] is False and a == ['raw'] and b == ['definition']
        return {'input_ids': torch.ones(1, 257, dtype=torch.long)}
    reranker.tokenizer = tokenizer
    reranker.model = lambda **kwargs: calls.append(kwargs)
    with pytest.raises(ValueError, match='too long'):
        reranker.score([('raw', 'definition')])
    assert not calls
    reranker.tokenizer = lambda *args, **kwargs: {'input_ids': torch.ones(1, 3, dtype=torch.long)}
    reranker.model = lambda **kwargs: SimpleNamespace(logits=torch.tensor([[float('nan')]]))
    with pytest.raises(ValueError, match='Invalid reranker scores'):
        reranker.score([('raw', 'definition')])
