"""Frozen relevance scoring of raw text pairs, without instructions or generation."""
import platform

import torch

from .definition_probe import digest
from .encoder import deterministic
from .semantics import require

MODEL = 'BAAI/bge-reranker-v2-m3'
REVISION = '953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e'
MAX_LENGTH = 256


class FrozenReranker:
    def __init__(self, offline=True):
        import transformers
        from huggingface_hub import hf_hub_download
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        deterministic()
        kwargs = {'revision': REVISION, 'local_files_only': offline, 'trust_remote_code': False}
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True, **kwargs)
        self.model, info = AutoModelForSequenceClassification.from_pretrained(
            MODEL, use_safetensors=True, weights_only=True, attn_implementation='eager',
            output_loading_info=True, **kwargs)
        require(not any(info.get(k) for k in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')),
                'Reranker checkpoint did not load exactly')
        require(self.model.config.model_type == 'xlm-roberta' and self.model.config.num_labels == 1
                and not self.model.can_generate(), 'Expected non-generative scalar reranker')
        self.model.to(device='cpu', dtype=torch.float32).eval().requires_grad_(False)
        paths = {name: hf_hub_download(MODEL, name, revision=REVISION, local_files_only=True)
                 for name in ('config.json', 'model.safetensors', 'tokenizer.json', 'tokenizer_config.json',
                              'special_tokens_map.json', 'sentencepiece.bpe.model', 'README.md')}
        self.metadata = {'id': MODEL, 'revision': REVISION, 'license': 'Apache-2.0',
                         'class': type(self.model).__name__, 'device': 'cpu', 'dtype': 'float32',
                         'attention': 'eager', 'seed': 17, 'max_length': MAX_LENGTH,
                         'threads': torch.get_num_threads(), 'python': platform.python_version(),
                         'torch': str(torch.__version__), 'transformers': transformers.__version__,
                         'platform': platform.platform(), 'parameters': sum(p.numel() for p in self.model.parameters()),
                         'files_sha256': {name: digest(path) for name, path in paths.items()}}

    def score(self, pairs, batch_size=16, progress=None):
        require(pairs and type(batch_size) is int and batch_size > 0, 'Empty pairs or invalid batch size')
        require(all(len(p) == 2 and all(isinstance(s, str) and s.strip() for s in p) for p in pairs),
                'Expected nonempty raw text pairs')
        output = []
        for offset in range(0, len(pairs), batch_size):
            batch = pairs[offset:offset + batch_size]
            encoded = self.tokenizer([p[0] for p in batch], [p[1] for p in batch], padding=True,
                                     truncation=False, return_tensors='pt')
            require(encoded['input_ids'].shape[1] <= MAX_LENGTH, 'Reranker input too long; truncation is forbidden')
            with torch.inference_mode():
                logits = self.model(**encoded).logits
            require(logits.shape == (len(batch), 1) and bool(torch.isfinite(logits).all()), 'Invalid reranker scores')
            output.append(logits[:, 0].cpu())
            if progress:
                progress(min(offset + batch_size, len(pairs)), len(pairs))
        return torch.cat(output)


def raw_pairs(rows, bank, mode):
    """No labels, IDs, instructions, type hints, or handcrafted target marking in model input."""
    require(mode in ('isolated', 'sentence'), 'Unknown reranker input mode')
    require(rows and bank and len({d['id'] for d in bank}) == len(bank), 'Invalid reranker inventory')
    ids = [d['id'] for d in sorted(bank, key=lambda d: d['id'])]
    by_id = {d['id']: d for d in bank}
    pairs = []
    for row in rows:
        a, b = row['start'], row['end']
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(row['text'])
                and row['span'] == row['text'][a:b], 'Invalid target span')
        require(row['language'] in ('ja', 'en'), 'Unsupported definition language')
        query = row['span'] if mode == 'isolated' else row['text']
        for key in ids:
            definition = by_id[key][row['language']]
            require(isinstance(definition, str) and definition.strip(), 'Empty concept definition')
            pairs.append((query, definition))
    return pairs, ids


def concept_scores(reranker, rows, bank, mode, progress=None):
    pairs, ids = raw_pairs(rows, bank, mode)
    # Identical strings have identical model inputs; no labels are used to collapse them.
    unique = list(dict.fromkeys(pairs))
    lookup = {pair: i for i, pair in enumerate(unique)}
    values = reranker.score(unique, progress=progress)
    require(values.shape == (len(unique),) and bool(torch.isfinite(values).all()), 'Invalid deduplicated scores')
    matrix = values[[lookup[p] for p in pairs]].reshape(len(rows), len(ids))
    return matrix, {'rows': len(rows), 'candidates': len(ids), 'pairs': len(pairs), 'unique_pairs': len(unique)}
