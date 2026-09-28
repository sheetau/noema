"""Target-specific relevance differences; experimental scores, not semantic probabilities."""
from collections import defaultdict

import torch

from .pretrained_reranker import raw_pairs
from .semantics import require


def masked_pairs(rows, bank, mask_token):
    require(isinstance(mask_token, str) and mask_token.strip(), 'Missing model mask token')
    pairs, ids = raw_pairs(rows, bank, 'sentence')
    require(all(mask_token not in text for pair in pairs for text in pair), 'Literal mask token in source input')
    queries = [r['text'][:r['start']] + mask_token + r['text'][r['end']:] for r in rows]
    return [(queries[i // len(ids)], definition) for i, (_, definition) in enumerate(pairs)], ids


def masked_scores(reranker, rows, bank, progress=None):
    pairs, ids = masked_pairs(rows, bank, reranker.tokenizer.mask_token)
    unique = list(dict.fromkeys(pairs))
    index = {p: i for i, p in enumerate(unique)}
    values = reranker.score(unique, progress=progress)
    require(values.shape == (len(unique),) and bool(torch.isfinite(values).all()), 'Invalid masked scores')
    matrix = values[[index[p] for p in pairs]].reshape(len(rows), len(ids))
    return matrix, {'rows': len(rows), 'candidates': len(ids), 'pairs': len(pairs), 'unique_pairs': len(unique)}


def target_effect(full, masked):
    require(full.ndim == 2 and full.shape == masked.shape and full.numel() > 0, 'Mismatched ablation matrices')
    require(bool(torch.isfinite(full).all()) and bool(torch.isfinite(masked).all()), 'Non-finite ablation input')
    difference = full - masked
    require(bool(torch.isfinite(difference).all()), 'Non-finite ablation effect')
    return difference


def target_switch_metrics(predictions):
    """Only groups with multiple distinct known targets measure correct target switching."""
    grouped = defaultdict(list)
    for row in predictions:
        if row['expected'] is not None:
            grouped[row['language'], row['text']].append(row)
    result = {}
    for language in ('ja', 'en'):
        groups = [rows for (lang, _), rows in grouped.items()
                  if lang == language and len({r['expected'] for r in rows}) >= 2]
        pairs = [(a, b) for rows in groups for i, a in enumerate(rows) for b in rows[i + 1:]
                 if a['expected'] != b['expected']]
        result[language] = {'sentences': len(groups), 'known_targets': sum(map(len, groups)),
                            'all_known_targets_correct': sum(all(r['top'][0]['concept'] == r['expected'] for r in rows)
                                                             for rows in groups),
                            'distinct_gold_pairs': len(pairs),
                            'different_top_candidates': sum(a['top'][0]['concept'] != b['top'][0]['concept'] for a, b in pairs),
                            'both_targets_correct': sum(a['top'][0]['concept'] == a['expected']
                                                        and b['top'][0]['concept'] == b['expected'] for a, b in pairs)}
    return result
