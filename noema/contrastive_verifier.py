"""Compare only explicitly annotated positive and negative definitions for one target."""
from collections import defaultdict
import hashlib
import json

import torch

from .semantics import require


def stable_hash(value):
    return hashlib.sha256(json.dumps([17, value], ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def comparison_groups(rows, indices):
    grouped = defaultdict(list)
    for i in indices:
        row = rows[i]
        grouped[row['text'], row['start'], row['end']].append(i)
    result = []
    for key, values in sorted(grouped.items(), key=lambda item: stable_hash(item[0])):
        result.append({'id': stable_hash(key), 'indices': sorted(values),
                       'positive': sorted(i for i in values if rows[i]['matches']),
                       'negative': sorted(i for i in values if not rows[i]['matches'])})
    return result


def partition(rows):
    """Connected components prevent both lemma and source-text leakage."""
    parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(a, b):
        a, b = root(a), root(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    seen = {}
    for i, row in enumerate(rows):
        for key in (('lemma', row['annotation']['lemma'].casefold()), ('text', row['text'])):
            if key in seen:
                union(i, seen[key])
            else:
                seen[key] = i
    components = defaultdict(list)
    for i in range(len(rows)):
        components[root(i)].append(i)
    splits = {'train': [], 'dev': []}
    for values in components.values():
        lemmas = sorted({rows[i]['annotation']['lemma'].casefold() for i in values})
        split = 'dev' if int(stable_hash(lemmas), 16) % 5 == 0 else 'train'
        splits[split].extend(values)
    result = {}
    for split, values in splits.items():
        indices = sorted(values)
        groups = comparison_groups(rows, indices)
        eligible = [g for g in groups if g['positive'] and g['negative']]
        require(indices and eligible and {rows[i]['matches'] for i in indices} == {True, False}, 'Insufficient contrast split')
        result[split] = {'indices': indices, 'groups': groups, 'rows': len(indices), 'contexts': len({rows[i]['text'] for i in indices}),
                         'lemmas': len({rows[i]['annotation']['lemma'].casefold() for i in indices}),
                         'positive_rows': sum(rows[i]['matches'] for i in indices), 'comparison_groups': len(eligible),
                         'comparison_pairs': sum(len(g['positive']) * len(g['negative']) for g in eligible)}
    return {'component_count': len(components), 'splits': result}


def group_objective(logits, labels, groups, rank_weight, population_groups, population_comparison_groups):
    """Unbiased group-balanced binary loss plus mean annotated pairwise ranking loss."""
    require(groups and population_groups >= population_comparison_groups > 0 and rank_weight >= 0, 'Invalid contrast objective')
    binary, ranking = [], []
    for group in groups:
        indices = group['indices']
        binary.append(torch.nn.functional.binary_cross_entropy_with_logits(logits[indices], labels[indices]))
        if group['positive'] and group['negative']:
            differences = logits[group['positive']][:, None] - logits[group['negative']][None, :]
            ranking.append(torch.nn.functional.softplus(-differences).mean())
        else:
            ranking.append(logits[indices].sum() * 0)
    binary_mean, rank_mean = torch.stack(binary).mean(), torch.stack(ranking).mean()
    corrected_rank = rank_mean * population_groups / population_comparison_groups
    return binary_mean + rank_weight * corrected_rank, binary_mean, corrected_rank


def ranking_metrics(logits, groups):
    require(all(torch.isfinite(torch.tensor(v)).item() for v in logits), 'Non-finite contrast scores')
    valid = [g for g in groups if g['positive'] and g['negative']]
    require(valid, 'No annotated comparison groups')
    group_accuracies, strict, ties, pairs = [], 0, 0, 0
    for group in valid:
        differences = [logits[p] - logits[n] for p in group['positive'] for n in group['negative']]
        group_accuracies.append(sum(1 if d > 0 else .5 if d == 0 else 0 for d in differences) / len(differences))
        strict += min(logits[p] for p in group['positive']) > max(logits[n] for n in group['negative'])
        ties += sum(d == 0 for d in differences)
        pairs += len(differences)
    return {'groups': len(valid), 'pairs': pairs, 'group_mean_pair_accuracy': sum(group_accuracies) / len(valid),
            'strictly_ordered_groups': strict, 'tied_pairs': ties}
