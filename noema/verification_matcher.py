"""Shared binary sense verification; only raw context, target span and definition are inputs."""
from collections import defaultdict

import torch
from torch import nn

from .paired_matcher import pooled_pair
from .semantics import require


def verification_features(encoder, rows, batch_size=16, max_length=256):
    require(rows and 0 < max_length <= encoder.model.config.max_position_embeddings, 'Invalid verification sequence limit')
    requests = defaultdict(list)
    for i, row in enumerate(rows):
        a, b = row['start'], row['end']
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(row['text']), 'Invalid verification span')
        require(row['text'][a:b] == row['span'] and row['definition'].strip(), 'Invalid verification text')
        requests[row['text'], row['definition']].append((i, a, b))
    keys = list(requests)
    output = torch.empty(len(rows), 2, encoder.dimension)
    for offset in range(0, len(keys), batch_size):
        pairs = keys[offset:offset + batch_size]
        encoded = encoder.tokenizer([p[0] for p in pairs], [p[1] for p in pairs], padding=True,
                                    truncation=False, return_tensors='pt', return_offsets_mapping=True)
        require(bool((encoded['attention_mask'].sum(1) <= max_length).all()), 'Verification input too long; truncation is forbidden')
        positions = encoded.pop('offset_mapping').tolist()
        sequences = [encoded.sequence_ids(i) for i in range(len(pairs))]
        with torch.inference_mode():
            hidden = encoder.model(**{k: v.to(encoder.device) for k, v in encoded.items()}).last_hidden_state.cpu()
        for j, pair in enumerate(pairs):
            for i, a, b in requests[pair]:
                output[i] = pooled_pair(hidden[j], positions[j], sequences[j], a, b)
    return output


class VerificationHead(nn.Module):
    def __init__(self, dimension, hidden=0):
        super().__init__()
        require(type(dimension) is int and dimension > 0 and type(hidden) is int and hidden >= 0, 'Invalid verifier dimensions')
        self.dimension = dimension
        self.network = nn.Sequential(nn.Linear(4 * dimension, hidden), nn.Tanh(), nn.Linear(hidden, 1)) if hidden else nn.Linear(4 * dimension, 1)
        final = self.network[-1] if hidden else self.network
        nn.init.zeros_(final.weight)
        nn.init.zeros_(final.bias)

    def forward(self, pairs):
        require(pairs.ndim >= 3 and pairs.shape[-2:] == (2, self.dimension), 'Invalid verification feature shape')
        q, d = pairs[..., 0, :], pairs[..., 1, :]
        return self.network(torch.cat([q, d, (q - d).abs(), q * d], dim=-1)).squeeze(-1)


def binary_metrics(logits, labels):
    require(len(logits) == len(labels) > 0, 'Invalid binary evaluation lengths')
    require(all(type(label) is bool for label in labels), 'Expected boolean binary labels')
    require(all(torch.isfinite(torch.tensor(v)).item() for v in logits), 'Non-finite binary prediction')
    tp = sum(v >= 0 and y for v, y in zip(logits, labels, strict=True))
    fp = sum(v >= 0 and not y for v, y in zip(logits, labels, strict=True))
    tn = sum(v < 0 and not y for v, y in zip(logits, labels, strict=True))
    fn = sum(v < 0 and y for v, y in zip(logits, labels, strict=True))
    require(tp + fn > 0 and tn + fp > 0, 'Both binary classes required')
    return {'count': len(labels), 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
            'accuracy': (tp + tn) / len(labels), 'balanced_accuracy': (tp / (tp + fn) + tn / (tn + fp)) / 2,
            'precision': tp / (tp + fp) if tp + fp else None, 'recall': tp / (tp + fn),
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}
