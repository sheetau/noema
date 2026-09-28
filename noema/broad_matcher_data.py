"""Repartition historical annotations by target concept; never used during inference."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from .definition_probe import definitions, rows_from_fixture
from .semantics import require


def hash_key(value):
    return hashlib.sha256(json.dumps([17, value], ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def concept_partition(bank, annotated):
    splits = {'train': [], 'dev': [], 'test': []}
    for kind in ('entity', 'place', 'event', 'state'):
        group = sorted((d['id'] for d in bank if d['kind'] == kind and d['id'] in annotated), key=hash_key)
        count = math.ceil(len(group) / 5)
        require(len(group) > 2 * count, 'Insufficient concepts for stratification')
        splits['dev'].extend(group[:count])
        splits['test'].extend(group[count:2 * count])
        splits['train'].extend(group[2 * count:])
    return {k: sorted(v) for k, v in splits.items()}


def prepare():
    bank = definitions()
    inventory = {d['id'] for d in bank}
    historical = []
    for number in range(1, 6):
        path = Path(f'data/definition-probe-v{number}.json')
        for row in rows_from_fixture(json.loads(path.read_text(encoding='utf-8')), inventory):
            historical.append({**row, 'id': f'v{number}:{row["id"]}', 'pair': f'v{number}:{row["pair"]}',
                               'origin': str(path).replace('\\', '/')})
    split_ids = concept_partition(bank, {r['expected'] for r in historical if r['expected']})
    rows = {split: [r for r in historical if r['expected'] in concepts] for split, concepts in split_ids.items()}
    old = json.loads(Path('reports/shared-matcher-v1/selection.json').read_text(encoding='utf-8'))['train']
    heldout = set(split_ids['dev']) | set(split_ids['test'])
    for row in old:
        if row['expected'] in split_ids['train'] and not set(row['sentence_concepts']) & heldout:
            rows['train'].append({**row, 'id': 'old:' + row['id'], 'pair': 'old:' + row['id'],
                                  'origin': 'reports/shared-matcher-v1/selection.json', 'group': 'historical_training'})
    # Protect entire source texts, not just annotated spans. Test has priority over dev over train.
    protected, removed = set(), {}
    for split in ('test', 'dev', 'train'):
        original = rows[split]
        deduplicated = {}
        for row in original:
            if row['text'] in protected:
                continue
            key = row['language'], row['text'], row['start'], row['end']
            require(key not in deduplicated or deduplicated[key]['expected'] == row['expected'], 'Conflicting historical annotation')
            if key not in deduplicated:
                deduplicated[key] = row
        selected = list(deduplicated.values())
        if split == 'train':
            capped = []
            for concept in split_ids[split]:
                for language in ('ja', 'en'):
                    group = [r for r in selected if r['expected'] == concept and r['language'] == language]
                    # Keep authored natural-context annotations before repeated historical templates.
                    group.sort(key=lambda r: (r['origin'].startswith('reports/'), hash_key([r['text'], r['start'], r['end']])))
                    capped.extend(group[:8])
            selected = capped
        rows[split] = sorted(selected, key=lambda r: r['id'])
        protected.update(r['text'] for r in selected)
        removed[split] = len(original) - len(selected)
        require({r['expected'] for r in selected} == set(split_ids[split]), 'Split lost an annotated concept')
    unknown = [r for r in historical if r['expected'] is None]
    return {'concepts': split_ids, 'rows': rows, 'unknown_observed_diagnostic': unknown,
            'removed_or_capped': removed, 'counts': {s: dict(Counter(r['language'] + ':' + r['expected'] for r in rs)) for s, rs in rows.items()},
            'scope': 'target-concept heldout; unannotated context concepts may occur in other splits; historical tests are no longer independent'}
