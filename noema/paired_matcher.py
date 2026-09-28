"""Label-independent compatibility of target spans and definitions in paired inputs."""
from collections import defaultdict

import torch
from torch import nn

from .definition_probe import normalized
from .semantics import require


def pooled_pair(hidden, offsets, sequences, start, end):
    require(type(start) is int and type(end) is int and 0 <= start < end, 'Invalid target span')
    target = [i for i, ((a, b), s) in enumerate(zip(offsets, sequences, strict=True))
              if s == 0 and a < b and a < end and b > start]
    definition = [i for i, ((a, b), s) in enumerate(zip(offsets, sequences, strict=True)) if s == 1 and a < b]
    require(target and definition, 'Missing target or definition tokens')
    return normalized(torch.stack([hidden[target].mean(0), hidden[definition].mean(0)]))


def paired_features(encoder, rows, bank, batch_size=16, progress=None):
    require(rows and bank, 'Empty paired input')
    require(len({d['id'] for d in bank}) == len(bank), 'Duplicate definition ID')
    requests = defaultdict(list)
    for i, row in enumerate(rows):
        a, b = row['start'], row['end']
        require(row['language'] in ('ja', 'en'), 'Unknown input language')
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(row['text']), 'Invalid target span')
        require(row['text'][a:b] == row['span'], 'Target text differs')
        for j, definition in enumerate(bank):
            text = definition[row['language']]
            require(isinstance(text, str) and text.strip(), 'Empty definition')
            requests[row['text'], text].append((i, j, a, b))
    keys = list(requests)
    output = torch.empty(len(rows), len(bank), 2, encoder.dimension)
    for offset in range(0, len(keys), batch_size):
        pairs = keys[offset:offset + batch_size]
        encoded = encoder.tokenizer([a for a, _ in pairs], [b for _, b in pairs], padding=True,
                                    truncation=False, return_tensors='pt', return_offsets_mapping=True)
        require(all(int(v) <= encoder.spec['max_length'] for v in encoded['attention_mask'].sum(1)),
                'Paired input exceeds maximum length; truncation is forbidden')
        positions = encoded.pop('offset_mapping').tolist()
        sequences = [encoded.sequence_ids(i) for i in range(len(pairs))]
        with torch.inference_mode():
            hidden = encoder.model(**{k: v.to(encoder.device) for k, v in encoded.items()}).last_hidden_state.cpu()
        for n, key in enumerate(pairs):
            for i, j, a, b in requests[key]:
                output[i, j] = pooled_pair(hidden[n], positions[n], sequences[n], a, b)
        if progress and (offset // batch_size % 100 == 0 or offset + batch_size >= len(keys)):
            progress(min(offset + batch_size, len(keys)), len(keys))
    return output


def independent_features(encoder, rows, bank):
    texts = list(dict.fromkeys([r['text'] for r in rows] + [d[l] for d in bank for l in ('ja', 'en')]))
    cache = dict(zip(texts, encoder.encode(texts), strict=True))
    require(all(not f['truncated'] for f in cache.values()), 'Truncated independent input')
    definitions = {}
    for d in bank:
        for language in ('ja', 'en'):
            f = cache[d[language]]
            positions = [i for i, (a, b) in enumerate(f['offsets']) if a < b]
            require(positions, 'Empty definition tokens')
            definitions[d['id'], language] = normalized(f['tokens'][positions].mean(0))
    output = torch.empty(len(rows), len(bank), 2, encoder.dimension)
    for i, row in enumerate(rows):
        f = cache[row['text']]
        positions = [j for j, (a, b) in enumerate(f['offsets']) if a < b and a < row['end'] and b > row['start']]
        require(positions and row['text'][row['start']:row['end']] == row['span'], 'Invalid independent target')
        q = normalized(f['tokens'][positions].mean(0))
        for j, d in enumerate(bank):
            output[i, j] = torch.stack([q, definitions[d['id'], row['language']]])
    return output


class PairCompatibilityHead(nn.Module):
    def __init__(self, dimension, hidden=0):
        super().__init__()
        require(type(dimension) is int and dimension > 0 and type(hidden) is int and hidden >= 0, 'Invalid head dimensions')
        self.dimension = dimension
        self.network = nn.Sequential(nn.Linear(4 * dimension, hidden), nn.Tanh(), nn.Linear(hidden, 1)) if hidden else nn.Linear(4 * dimension, 1)
        last = self.network[-1] if hidden else self.network
        nn.init.zeros_(last.weight)
        nn.init.zeros_(last.bias)

    def forward(self, pairs):
        require(pairs.ndim == 4 and pairs.shape[2:] == (2, self.dimension), 'Invalid paired feature shape')
        q, d = pairs[:, :, 0], pairs[:, :, 1]
        features = torch.cat([q, d, (q - d).abs(), q * d], dim=-1)
        return (q * d).sum(-1) + .25 * torch.tanh(self.network(features).squeeze(-1))
