"""Frozen context/gloss encoders with explicit character-span alignment."""
from collections import defaultdict
import json
from pathlib import Path
import platform

import torch

from .definition_probe import digest
from .encoder import deterministic
from .semantics import require

BASE_MODEL = 'FacebookAI/xlm-roberta-large'
BASE_REVISION = 'c23d21b0620b635a76227c604d44e43a9f0ee389'
SOURCE = Path('artifacts/glossreader-source-v1')
MANIFEST = Path('reports/glossreader-source-v1/manifest.json')
MAX_LENGTH = 512


def split_checkpoint(state):
    require(isinstance(state, dict) and state, 'Expected a tensor state dictionary')
    prefixes = {name: f'{name}_encoder.{name}_encoder.' for name in ('context', 'gloss')}
    result = {name: {} for name in prefixes}
    for key, value in state.items():
        require(isinstance(key, str) and isinstance(value, torch.Tensor), 'Non-tensor checkpoint component')
        matches = [name for name, prefix in prefixes.items() if key.startswith(prefix)]
        require(len(matches) == 1, 'Unexpected GlossReader checkpoint component')
        name = matches[0]
        result[name][key[len(prefixes[name]):]] = value
    require(all(result.values()), 'Both independently trained encoders are required')
    return result


def span_positions(text, start, end, offsets, attention):
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'Invalid character span')
    require(len(offsets) == len(attention), 'Offset and attention lengths differ')
    require(all(type(a) is int and type(b) is int and 0 <= a <= b <= len(text) for a, b in offsets), 'Invalid token offsets')
    positions = [i for i, ((a, b), active) in enumerate(zip(offsets, attention, strict=True))
                 if active and a < b and a < end and b > start]
    needed = {i for i in range(start, end) if not text[i].isspace()}
    covered = {i for p in positions for i in range(max(start, offsets[p][0]), min(end, offsets[p][1]))}
    require(needed and needed <= covered, 'Target characters are not fully covered by active tokens')
    spills = [{'token_index': p, 'offset': list(offsets[p]),
               'outside_text': text[offsets[p][0]:min(start, offsets[p][1])] + text[max(end, offsets[p][0]):offsets[p][1]]}
              for p in positions if text[offsets[p][0]:min(start, offsets[p][1])].strip()
              or text[max(end, offsets[p][0]):offsets[p][1]].strip()]
    return positions, spills


class FrozenGlossReader:
    def __init__(self):
        import transformers
        from huggingface_hub import hf_hub_download
        from transformers import AutoConfig, AutoModel, AutoTokenizer
        deterministic()
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        checkpoint = SOURCE / 'best_model.ckpt'
        require(digest(checkpoint) == manifest['files_sha256']['best_model.ckpt'], 'GlossReader checkpoint changed')
        kwargs = {'revision': BASE_REVISION, 'local_files_only': True, 'trust_remote_code': False}
        config = AutoConfig.from_pretrained(BASE_MODEL, **kwargs)
        require(config.model_type == 'xlm-roberta' and config.hidden_size == 1024 and config.num_hidden_layers == 24,
                'Unexpected GlossReader architecture')
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True, **kwargs)
        require(self.tokenizer.is_fast, 'Fast tokenizer required for character alignment')
        state = torch.load(checkpoint, map_location='cpu', weights_only=True, mmap=True)
        split = split_checkpoint(state)
        self.encoders = {}
        for name in ('context', 'gloss'):
            model = AutoModel.from_config(config, trust_remote_code=False, attn_implementation='eager')
            model.load_state_dict(split[name], strict=True)
            require(not model.can_generate(), 'Generation model is not supported')
            self.encoders[name] = model.to(device='cpu', dtype=torch.float32).eval().requires_grad_(False)
        paths = {name: hf_hub_download(BASE_MODEL, name, revision=BASE_REVISION, local_files_only=True)
                 for name in ('config.json', 'tokenizer.json', 'tokenizer_config.json', 'sentencepiece.bpe.model')}
        self.metadata = {'model': 'GlossReader large retrained October 2023', 'record': 10530146,
                         'license': 'CC BY 4.0', 'source_manifest_sha256': digest(MANIFEST),
                         'checkpoint_sha256': manifest['files_sha256']['best_model.ckpt'],
                         'base_model': BASE_MODEL, 'base_revision': BASE_REVISION,
                         'base_files_sha256': {name: digest(path) for name, path in paths.items()},
                         'parameters': {name: sum(p.numel() for p in model.parameters()) for name, model in self.encoders.items()},
                         'python': platform.python_version(), 'torch': str(torch.__version__), 'transformers': transformers.__version__,
                         'platform': platform.platform(), 'dtype': 'float32', 'device': 'cpu', 'attention': 'eager',
                         'threads': torch.get_num_threads(), 'seed': 17, 'max_length': MAX_LENGTH,
                         'context_pooling': 'mean of active tokens overlapping the annotated character span',
                         'gloss_pooling': 'CLS', 'truncation': False}

    def encode_contexts(self, rows, batch_size=8):
        require(rows and type(batch_size) is int and batch_size > 0, 'Invalid context batch')
        groups = defaultdict(list)
        for i, row in enumerate(rows):
            require(isinstance(row['text'], str) and type(row['start']) is int and type(row['end']) is int
                    and 0 <= row['start'] < row['end'] <= len(row['text'])
                    and row['text'][row['start']:row['end']] == row['span'], 'Target text differs from its span')
            groups[row['text']].append((i, row))
        texts = list(groups)
        vectors, audit = [None] * len(rows), [None] * len(rows)
        for offset in range(0, len(texts), batch_size):
            batch = texts[offset:offset + batch_size]
            encoded = self.tokenizer(batch, padding=True, truncation=False, return_tensors='pt', return_offsets_mapping=True)
            require(encoded['input_ids'].shape[1] <= MAX_LENGTH, 'Context too long; truncation is forbidden')
            offsets = encoded.pop('offset_mapping').tolist()
            attention = encoded['attention_mask'].tolist()
            with torch.inference_mode():
                hidden = self.encoders['context'](**encoded).last_hidden_state
            for j, text in enumerate(batch):
                for i, row in groups[text]:
                    positions, spills = span_positions(text, row['start'], row['end'], offsets[j], attention[j])
                    vectors[i] = hidden[j, positions].mean(0)
                    # Audit the published prefix-count heuristic; never use it to select the requested span.
                    left = 1 + len(self.tokenizer(text[:row['start']], add_special_tokens=False)['input_ids'])
                    size = len(self.tokenizer(row['span'], add_special_tokens=False)['input_ids'])
                    legacy = list(range(left, left + size))
                    audit[i] = {'positions': positions, 'legacy_prefix_positions': legacy, 'different': positions != legacy,
                                'boundary_spills': spills}
        result = torch.stack(vectors)
        require(bool(torch.isfinite(result).all()), 'Non-finite context features')
        return result, audit

    def encode_glosses(self, glosses, batch_size=8):
        require(glosses and all(isinstance(g, str) and g.strip() for g in glosses), 'Empty gloss')
        require(type(batch_size) is int and batch_size > 0, 'Invalid gloss batch size')
        vectors = []
        for offset in range(0, len(glosses), batch_size):
            encoded = self.tokenizer(glosses[offset:offset + batch_size], padding=True, truncation=False, return_tensors='pt')
            require(encoded['input_ids'].shape[1] <= MAX_LENGTH, 'Gloss too long; truncation is forbidden')
            with torch.inference_mode():
                vectors.append(self.encoders['gloss'](**encoded).last_hidden_state[:, 0])
        result = torch.cat(vectors)
        require(bool(torch.isfinite(result).all()), 'Non-finite gloss features')
        return result
