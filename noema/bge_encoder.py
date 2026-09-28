"""Pinned dense BGE encoder; no instruction prefix, generation, or sparse matching."""
import json
import platform
from pathlib import Path

import torch
import transformers
from huggingface_hub import hf_hub_download
from transformers import AutoModel, AutoTokenizer

from .encoder import FrozenEncoder, deterministic
from .definition_probe import digest
from .semantics import require

SPEC = {'id': 'BAAI/bge-m3', 'revision': '5617a9f61b028005a4858fdac845db406aefb181', 'max_length': 128}


class FrozenBGE(FrozenEncoder):
    def __init__(self):
        deterministic()
        self.spec, self.key, self.device = dict(SPEC), 'bge-m3', 'cpu'
        kwargs = {'revision': SPEC['revision'], 'local_files_only': True, 'trust_remote_code': False}
        self.tokenizer = AutoTokenizer.from_pretrained(SPEC['id'], use_fast=True, **kwargs)
        require(self.tokenizer.is_fast, 'BGE needs character offsets')
        self.model, loading = AutoModel.from_pretrained(SPEC['id'], use_safetensors=False, weights_only=True,
                                                       attn_implementation='eager', output_loading_info=True, **kwargs)
        require(not any(loading.get(k) for k in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')),
                'BGE checkpoint has unmatched parameters')
        self.model.to(device='cpu', dtype=torch.float32).eval().requires_grad_(False)
        self.dimension = self.model.config.hidden_size
        paths = {name: hf_hub_download(SPEC['id'], name, revision=SPEC['revision'], local_files_only=True)
                 for name in ('pytorch_model.bin', 'config.json', 'tokenizer.json', 'tokenizer_config.json',
                              'special_tokens_map.json', 'sentencepiece.bpe.model', '1_Pooling/config.json')}
        pooling = json.loads(Path(paths['1_Pooling/config.json']).read_text(encoding='utf-8'))
        require(pooling['pooling_mode_cls_token'] and not pooling['pooling_mode_mean_tokens'], 'Unexpected BGE pooling')
        self.metadata = {**SPEC, 'key': self.key, 'python': platform.python_version(), 'torch': str(torch.__version__),
                         'transformers': transformers.__version__, 'platform': platform.platform(),
                         'device': 'cpu', 'dtype': 'float32', 'attention': 'eager', 'threads': torch.get_num_threads(),
                         'pooling': 'CLS token', 'seed': 17, 'batch_size': 16, 'instruction_prefix': None,
                         'parameters': sum(p.numel() for p in self.model.parameters()),
                         'checkpoint_sha256': {name: digest(path) for name, path in paths.items()}}

    def encode(self, texts, batch_size=16):
        features = super().encode(texts, batch_size)
        for feature in features:
            feature['pooled'] = feature['tokens'][0].clone()
        return features
