import json
from pathlib import Path
from unittest.mock import patch

import torch

from noema.bge_encoder import FrozenBGE, SPEC
from noema.definition_probe import definitions, rows_from_fixture
from noema.encoder import FrozenEncoder


def test_bge_cls_preserves_offsets_and_truncation_from_encoder():
    tokens = torch.tensor([[1., 2.], [3., 4.]])
    features = [{'tokens': tokens, 'pooled': tokens.mean(0), 'offsets': [[0, 0], [0, 1]], 'truncated': True}]
    encoder = FrozenBGE.__new__(FrozenBGE)
    with patch.object(FrozenEncoder, 'encode', return_value=features) as encode:
        result = encoder.encode(['x'], batch_size=2)
    encode.assert_called_once_with(['x'], 2)
    assert torch.equal(result[0]['pooled'], tokens[0])
    assert result[0]['truncated'] and result[0]['offsets'] == [[0, 0], [0, 1]]
    result[0]['pooled'][0] = -1
    assert tokens[0, 0] == 1  # pooled representation does not alias the token matrix


def test_new_confirmation_has_no_exact_text_overlap_with_prior_probes_or_training():
    ids = {d['id'] for d in definitions()}
    rows = rows_from_fixture(json.loads(Path('data/definition-probe-v4.json').read_text(encoding='utf-8')), ids)
    assert len(rows) == 60 and sum(r['expected'] is None for r in rows) == 12
    old = [r for n in (1, 2, 3) for r in rows_from_fixture(
        json.loads(Path(f'data/definition-probe-v{n}.json').read_text(encoding='utf-8')), ids)]
    selected = json.loads(Path('reports/shared-matcher-v1/selection.json').read_text(encoding='utf-8'))
    assert not {r['text'] for r in rows} & {r['text'] for r in [*old, *selected['train'], *selected['dev']]}
    assert len(SPEC['revision']) == 40 and SPEC['max_length'] == 128
