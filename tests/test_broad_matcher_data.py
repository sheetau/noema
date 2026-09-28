from collections import Counter
import json
from pathlib import Path

import pytest

from noema.broad_matcher_data import prepare, concept_partition
from noema.definition_probe import definitions, rows_from_fixture
from scripts.probe_broad_matcher import balanced_weights, macro_accuracy


def test_partition_covers_kinds_and_keeps_targets_and_texts_separate():
    selected = prepare()
    bank = definitions()
    by_id = {d['id']: d for d in bank}
    ids = selected['concepts']
    assert [len(ids[k]) for k in ('train', 'dev', 'test')] == [52, 19, 19]
    assert concept_partition(bank[::-1], set().union(*map(set, ids.values()))) == ids
    seen_ids, seen_texts = set(), set()
    for split in ('train', 'dev', 'test'):
        assert not seen_ids & set(ids[split])
        seen_ids.update(ids[split])
        assert {by_id[c]['kind'] for c in ids[split]} == {'entity', 'place', 'event', 'state'}
        rows = selected['rows'][split]
        assert not seen_texts & {r['text'] for r in rows}
        seen_texts.update(r['text'] for r in rows)
        assert {r['language'] for r in rows} == {'ja', 'en'}
        assert len(rows) == len({(r['language'], r['text'], r['start'], r['end']) for r in rows})
    counts = Counter((r['language'], r['expected']) for r in selected['rows']['train'])
    assert max(counts.values()) <= 8 and len(counts) == 104
    for r in selected['rows']['train']:
        if 'sentence_concepts' in r:
            assert not set(r['sentence_concepts']) & (set(ids['dev']) | set(ids['test']))


def test_unequal_example_counts_have_equal_group_loss_weight():
    rows = [{'language': language, 'expected': concept} for language in ('ja', 'en')
            for concept, count in (('a', 1), ('b', 7)) for _ in range(count)]
    weights = balanced_weights(rows)
    assert weights.sum().item() == pytest.approx(len(rows))
    totals = Counter()
    for row, weight in zip(rows, weights.tolist(), strict=True):
        totals[row['language'], row['expected']] += weight
    assert list(totals.values()) == pytest.approx([4.] * 4)
    predictions = [0] * len(rows)
    assert macro_accuracy(predictions, rows, ['a', 'b']) == {'ja': .5, 'en': .5, 'macro': .5}


def test_new_confirmation_covers_only_heldout_targets_and_new_texts():
    selected = prepare()
    rows = rows_from_fixture(json.loads(Path('data/definition-probe-v6.json').read_text(encoding='utf-8')),
                             {d['id'] for d in definitions()})
    assert len(rows) == 50 and sum(r['expected'] is None for r in rows) == 12
    assert {r['expected'] for r in rows if r['expected']} == set(selected['concepts']['test'])
    old = [r for n in range(1, 6) for r in rows_from_fixture(json.loads(
        Path(f'data/definition-probe-v{n}.json').read_text(encoding='utf-8')), {d['id'] for d in definitions()})]
    assert not {r['text'] for r in rows} & {r['text'] for r in old}
