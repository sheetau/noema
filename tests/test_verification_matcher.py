from types import SimpleNamespace
import pytest
import torch

from noema.definition_probe import normalized
from noema.verification_matcher import VerificationHead, binary_metrics, verification_features


def test_binary_metrics_include_both_classes_and_fixed_zero_threshold():
    result = binary_metrics([0., -1., 2., -2.], [True, True, False, False])
    assert [result[k] for k in ('tp', 'fp', 'tn', 'fn')] == [1, 1, 1, 1]
    assert result['balanced_accuracy'] == .5 and result['precision'] == .5


@pytest.mark.parametrize('hidden', [0, 64])
def test_verifier_has_one_shared_output_for_any_candidate_count(hidden):
    head = VerificationHead(4, hidden)
    pairs = normalized(torch.randn(2, 5, 2, 4))
    assert torch.equal(head(pairs), torch.zeros(2, 5))
    with torch.no_grad():
        for p in head.parameters():
            p.normal_()
    order = [4, 1, 0, 2, 3]
    assert torch.allclose(head(pairs[:, order]), head(pairs)[:, order], atol=1e-6)
    assert torch.allclose(head(pairs[:, :3]), head(pairs)[:, :3], atol=1e-6)


def test_annotations_and_lemma_do_not_change_verification_features():
    calls = []
    class Encoded(dict):
        def sequence_ids(self, index):
            return [None, 0, 1]
    def tokenize(a, b, **kwargs):
        calls.append((a, b))
        return Encoded(input_ids=torch.ones(1, 3, dtype=torch.long), attention_mask=torch.ones(1, 3),
                       offset_mapping=torch.tensor([[[0, 0], [0, 1], [0, 3]]]))
    encoder = SimpleNamespace(tokenizer=tokenize, dimension=2, device='cpu')
    class Model:
        config = SimpleNamespace(max_position_embeddings=512)
        def __call__(self, **kwargs):
            return SimpleNamespace(last_hidden_state=torch.tensor([[[9., 9.], [1., 0.], [0., 1.]]]))
    encoder.model = Model()
    row = {'text': 'x', 'span': 'x', 'start': 0, 'end': 1, 'definition': 'def', 'matches': True, 'annotation': {'lemma': 'secret'}}
    result = verification_features(encoder, [row, {**row, 'matches': False, 'annotation': {'lemma': 'different'}}])
    assert calls == [(['x'], ['def'])]
    assert torch.equal(result[0], result[1]) and torch.equal(result[0], torch.eye(2))
