import pytest
import torch

from noema.glossreader import split_checkpoint, span_positions


def test_checkpoint_keeps_two_encoder_weights_distinct_and_rejects_missing_or_extra_components():
    a, b = torch.tensor([1.]), torch.tensor([2.])
    state = {'context_encoder.context_encoder.layer.weight': a, 'gloss_encoder.gloss_encoder.layer.weight': b}
    result = split_checkpoint(state)
    assert result['context']['layer.weight'] is a and result['gloss']['layer.weight'] is b
    with pytest.raises(ValueError, match='Both'):
        split_checkpoint({'context_encoder.context_encoder.layer.weight': a})
    with pytest.raises(ValueError, match='Unexpected'):
        split_checkpoint({**state, 'other.weight': a})
    with pytest.raises(ValueError, match='Non-tensor'):
        split_checkpoint({**state, 'ood_prob': 0.})


def test_span_uses_original_offsets_for_repeated_words_and_ignores_padding():
    text = 'key key'
    positions, spill = span_positions(text, 4, 7, [(0, 0), (0, 3), (3, 7), (0, 0), (4, 7)], [1, 1, 1, 1, 0])
    assert positions == [2] and spill == []
    with pytest.raises(ValueError, match='fully covered'):
        span_positions(text, 4, 7, [(0, 0), (4, 6)], [1, 1])


def test_partial_boundary_tokens_are_explicit_instead_of_silently_calling_them_exact():
    positions, spills = span_positions('門を開けた', 2, 5, [(0, 0), (0, 1), (1, 4), (4, 5), (0, 0)], [1] * 5)
    assert positions == [2, 3]
    assert spills == [{'token_index': 2, 'offset': [1, 4], 'outside_text': 'を'}]
    with pytest.raises(ValueError, match='Invalid token offsets'):
        span_positions('犬', 0, 1, [(0, 2)], [1])
    with pytest.raises(ValueError, match='fully covered'):
        span_positions(' ', 0, 1, [(0, 1)], [1])
