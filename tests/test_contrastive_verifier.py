import pytest
import torch

from noema.contrastive_verifier import comparison_groups, partition, group_objective, ranking_metrics


def rows():
    result = []
    for i in range(40):
        for label in (False, True):
            result.append({'text': f'target {i}', 'start': 0, 'end': 6, 'matches': label,
                           'annotation': {'lemma': f'lemma{i}'}})
    # Same context with a different target must not leak across split boundaries.
    result.append({'text': 'target 0', 'start': 7, 'end': 8, 'matches': True, 'annotation': {'lemma': 'lemma1'}})
    return result


def test_split_connects_shared_lemmas_and_contexts_and_covers_every_row():
    data = rows()
    split = partition(data)['splits']
    a, b = split['train']['indices'], split['dev']['indices']
    assert set(a).isdisjoint(b) and sorted(a + b) == list(range(len(data)))
    assert not {data[i]['text'] for i in a} & {data[i]['text'] for i in b}
    assert not {data[i]['annotation']['lemma'] for i in a} & {data[i]['annotation']['lemma'] for i in b}
    original = {tuple(sorted(data[i]['annotation'].items())): k for k, v in split.items() for i in v['indices']}
    shuffled = list(reversed(data))
    repeated = partition(shuffled)['splits']
    assert original == {tuple(sorted(shuffled[i]['annotation'].items())): k for k, v in repeated.items() for i in v['indices']}


def test_pair_loss_is_group_balanced_and_only_uses_annotated_pairs():
    groups = [{'indices': [0, 1], 'positive': [0], 'negative': [1]},
              {'indices': [2, 3, 4], 'positive': [2], 'negative': [3, 4]},
              {'indices': [5], 'positive': [5], 'negative': []}]
    logits = torch.tensor([2., 0., 1., 0., -1., 3.], requires_grad=True)
    labels = torch.tensor([1., 0., 1., 0., 0., 1.])
    loss, bce, rank = group_objective(logits, labels, groups, 1., 3, 2)
    expected = (torch.nn.functional.softplus(torch.tensor(-2.)) +
                torch.nn.functional.softplus(torch.tensor([-1., -2.])).mean()) / 2
    assert rank.item() == pytest.approx(expected.item())
    assert loss.item() == pytest.approx((bce + expected).item())
    rank.backward()
    assert logits.grad[0] < 0 and logits.grad[1] > 0 and logits.grad[5] == 0


def test_ranking_ties_and_global_bias_are_explicit():
    data = rows()[:4]
    groups = comparison_groups(data, range(4))
    result = ranking_metrics([0., 0., 1., 2.], groups)
    assert result['group_mean_pair_accuracy'] == .75 and result['tied_pairs'] == 1
    assert result == ranking_metrics([9., 9., 10., 11.], groups)
