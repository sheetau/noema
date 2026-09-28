import pytest
import torch

from noema.target_ablation import masked_pairs, target_effect, target_switch_metrics


def test_masking_uses_one_annotated_occurrence_without_modifying_definition_or_other_text():
    rows = [{'text': 'key, key!', 'span': 'key', 'start': 5, 'end': 8, 'language': 'en', 'expected': 'unused'}]
    bank = [{'id': 'a', 'en': 'a physical key', 'ja': '鍵'}]
    pairs, ids = masked_pairs(rows, bank, '<mask>')
    assert pairs == [('key, <mask>!', 'a physical key')] and ids == ['a']
    rows[0]['expected'] = None
    assert masked_pairs(rows, bank, '<mask>')[0] == pairs
    rows = [{'text': '青い鳥が飛ぶ。', 'span': '青い鳥', 'start': 0, 'end': 3, 'language': 'ja'}]
    assert masked_pairs(rows, bank, '<mask>')[0] == [('<mask>が飛ぶ。', '鍵')]


def test_masking_rejects_ambiguous_literal_mask_and_bad_span():
    row = {'text': 'a key', 'span': 'key', 'start': 2, 'end': 5, 'language': 'en'}
    with pytest.raises(ValueError, match='Literal mask'):
        masked_pairs([row], [{'id': 'a', 'en': '<mask>', 'ja': '鍵'}], '<mask>')
    with pytest.raises(ValueError, match='span'):
        masked_pairs([{**row, 'start': 1}], [{'id': 'a', 'en': 'a key', 'ja': '鍵'}], '<mask>')


def test_effect_uses_context_difference_and_cancels_shared_candidate_bias():
    full = torch.tensor([[4., 5., 1.], [2., 5., 1.]])
    masked = torch.tensor([[1., 5., 2.], [1., 1., 1.]])
    assert target_effect(full, masked).argmax(-1).tolist() == [0, 1]
    bias = torch.tensor([[20., -10., 2.]])
    assert torch.equal(target_effect(full + bias, masked + bias), target_effect(full, masked))
    with pytest.raises(ValueError, match='Mismatched'):
        target_effect(full, masked[:1])
    with pytest.raises(ValueError, match='Non-finite'):
        target_effect(full, masked * float('nan'))


def test_target_switch_counts_correctness_separately_from_merely_different_answers():
    rows = [{'text': 'same', 'language': 'en', 'expected': e, 'top': [{'concept': p}]}
            for e, p in [('a', 'a'), ('b', 'wrong'), (None, 'other')]]
    result = target_switch_metrics(rows)['en']
    assert result == {'sentences': 1, 'known_targets': 2, 'all_known_targets_correct': 0,
                      'distinct_gold_pairs': 1, 'different_top_candidates': 1, 'both_targets_correct': 0}
    rows[1]['top'][0]['concept'] = 'b'
    assert target_switch_metrics(rows)['en']['all_known_targets_correct'] == 1
