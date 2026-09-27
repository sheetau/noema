"""Optional PyTorch/Transformers integration; no generation, remote code or encoder training."""
import json
import os
import platform
from importlib.resources import files

MODELS = json.loads(files("noema").joinpath("resources/models.json").read_text(encoding="utf-8"))


def deterministic(seed=17):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False


class FrozenEncoder:
    def __init__(self, model="xlmr", device="cpu", offline=False):
        import torch
        import transformers
        from transformers import AutoModel, AutoTokenizer
        deterministic()
        self.spec = MODELS[model]
        self.key, self.device = model, device
        kwargs = {"revision": self.spec["revision"], "local_files_only": offline, "trust_remote_code": False}
        self.tokenizer = AutoTokenizer.from_pretrained(self.spec["id"], use_fast=True, **kwargs)
        if not self.tokenizer.is_fast:
            raise ValueError("A fast tokenizer with character offsets is required")
        self.model = AutoModel.from_pretrained(self.spec["id"], use_safetensors=True, attn_implementation="eager", **kwargs).to(device=device, dtype=torch.float32)
        self.model.eval()
        self.model.requires_grad_(False)
        self.dimension = self.model.config.hidden_size
        self.metadata = {**self.spec, "key": model, "torch": str(torch.__version__), "transformers": transformers.__version__,
                         "python": platform.python_version(), "platform": platform.platform(), "device": device,
                         "processor": platform.processor(), "dtype": "float32", "attention": "eager", "threads": torch.get_num_threads(),
                         "pooling": "attention-mask mean including special tokens", "seed": 17,
                         "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(device) if device.startswith("cuda") else None}

    def encode(self, texts, batch_size=16):
        import torch
        output = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            encoded = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True,
                                     max_length=self.spec["max_length"], return_offsets_mapping=True)
            offsets = encoded.pop("offset_mapping")
            # Determine truncation explicitly: no silently incomplete semantic output.
            lengths = [len(self.tokenizer(t, truncation=False)["input_ids"]) for t in batch]
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            with torch.inference_mode():
                hidden = self.model(**encoded).last_hidden_state
            for i in range(len(batch)):
                n = int(encoded["attention_mask"][i].sum())
                features = hidden[i, :n].cpu().clone()
                output.append({"tokens": features, "pooled": features.mean(0), "offsets": offsets[i, :n].tolist(),
                               "truncated": lengths[i] > self.spec["max_length"]})
        return output
