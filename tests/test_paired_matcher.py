import json
from pathlib import Path

import pytest
import torch
from types import SimpleNamespace

from noema.definition_probe import definitions, normalized, rows_from_fixture
from noema.paired_matcher import pooled_pair, PairCompatibilityHead, paired_features
from noema.semantics import SemanticError


def test_pair_pooling_separates_identical_offsets_in_different_sequences():
    hidden = torch.tensor([[99., 99.], [1., 0.], [0., 1.], [1., 1.], [0., 8.]])
    offsets = [(0, 0), (0, 2), (3, 4), (0, 2), (3, 4)]
    result = pooled_pair(hidden, offsets, [None, 0, 0, 1, 1], 0, 2)
    assert torch.equal(result[0], torch.tensor([1., 0.]))
    assert torch.allclose(result[1], normalized(torch.tensor([.5, 4.5])))
    with pytest.raises(SemanticError, match='Missing target'):
        pooled_pair(hidden, offsets, [None, 0, 0, 1, 1], 10, 12)


@pytest.mark.parametrize('hidden', [0, 64])
def test_head_never_depends_on_candidate_order_count_or_identity(hidden):
    torch.manual_seed(17)
    pairs = normalized(torch.randn(3, 7, 2, 12))
    head = PairCompatibilityHead(12, hidden)
    assert torch.allclose(head(pairs), (pairs[:, :, 0] * pairs[:, :, 1]).sum(-1))
    with torch.no_grad():
        for parameter in head.parameters():
            parameter.normal_(std=.1)
    original = head(pairs)
    permutation = [2, 1, 5, 3, 6, 0, 4]
    assert torch.allclose(head(pairs[:, permutation]), original[:, permutation], atol=1e-6)
    expanded = torch.cat([pairs, normalized(torch.randn(3, 5, 2, 12))], dim=1)
    assert torch.allclose(head(expanded)[:, :7], original, atol=1e-6)
    assert (original - (pairs[:, :, 0] * pairs[:, :, 1]).sum(-1)).abs().max() <= .250001


def test_feature_extractor_rejects_invalid_span_before_encoding():
    row = {'language': 'ja', 'text': 'abc', 'start': -1, 'end': 1, 'span': 'a'}
    with pytest.raises(SemanticError, match='Invalid target'):
        paired_features(None, [row], [{'id': 'c', 'ja': 'def', 'en': 'def'}])


def test_pair_truncation_is_rejected_before_model_forward():
    encoder = SimpleNamespace(dimension=2, spec={'max_length': 3},
                              tokenizer=lambda *a, **k: {'attention_mask': torch.ones(1, 4)})
    row = {'language': 'en', 'text': 'abc', 'start': 0, 'end': 1, 'span': 'a'}
    with pytest.raises(SemanticError, match='truncation is forbidden'):
        paired_features(encoder, [row], [{'id': 'c', 'en': 'def', 'ja': 'def'}])


def test_multiple_targets_share_forward_and_gold_is_not_an_encoder_input():
    calls = []
    class Encoded(dict):
        def sequence_ids(self, i):
            return [None, 0, 0, 1]
    def tokenizer(left, right, **kwargs):
        calls.append((left, right))
        return Encoded(attention_mask=torch.ones(1, 4), input_ids=torch.ones(1, 4, dtype=torch.long),
                       offset_mapping=torch.tensor([[[0, 0], [0, 1], [1, 2], [0, 3]]]))
    encoder = SimpleNamespace(dimension=2, spec={'max_length': 8}, device='cpu', tokenizer=tokenizer,
                              model=lambda **k: SimpleNamespace(last_hidden_state=torch.tensor([[[9., 9.], [1., 0.], [0., 1.], [1., 1.]]])))
    rows = [{'text': 'ab', 'language': 'en', 'start': i, 'end': i + 1, 'span': 'ab'[i], 'expected': 'ignored'} for i in range(2)]
    result = paired_features(encoder, rows, [{'id': 'opaque', 'en': 'def', 'ja': 'definition'}])
    assert calls == [(['ab'], ['def'])]
    assert torch.equal(result[:, 0, 0], torch.eye(2))


def test_confirmation_is_new_text_and_has_twenty_known_six_unknown_pairs():
    ids = {d['id'] for d in definitions()}
    rows = rows_from_fixture(json.loads(Path('data/definition-probe-v5.json').read_text(encoding='utf-8')), ids)
    assert len(rows) == 52 and sum(r['expected'] is None for r in rows) == 12
    old = [r for n in (1, 2, 3, 4) for r in rows_from_fixture(json.loads(
        Path(f'data/definition-probe-v{n}.json').read_text(encoding='utf-8')), ids)]
    selected = json.loads(Path('reports/shared-matcher-v1/selection.json').read_text(encoding='utf-8'))
    assert not {r['text'] for r in rows} & {r['text'] for r in [*old, *selected['train'], *selected['dev']]}
