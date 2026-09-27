"""Prepare only KWJA's frozen discriminative char/word checkpoints."""
import json
import argparse
import typing
from pathlib import Path

from noema.definition_probe import digest

REVISION = "4c5db234089ca9e524fc5d32d383bc45e6fe27a2"
SOURCE_REVISION = "821df300630b4d05c38406945536eaac848619da"
MODELS = {"char": ("char_deberta-v2-base-wwm.ckpt", "ku-nlp/deberta-v2-base-japanese-char-wwm", "29498bbcaa6e3220d9e74345cd6d963e7c00fee4"),
          "word": ("word_deberta-v2-base.ckpt", "ku-nlp/deberta-v2-base-japanese", "833680905d7c57dbc7914dd33707a9fe1b20c60d")}


def metadata_cache(factory=None):
    # The legacy OmegaConf metadata cache needs a plain mapping for conversion.
    return {}


def main():
    import torch
    from omegaconf import DictConfig, ListConfig, OmegaConf
    from omegaconf.nodes import AnyNode
    from omegaconf.base import ContainerMetadata, Metadata
    from safetensors.torch import save_file
    from huggingface_hub import hf_hub_download, snapshot_download
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/japanese-pas-model")
    root = Path(parser.parse_args().output)
    root.mkdir(parents=True, exist_ok=False)
    info = {"checkpoint_revision": REVISION, "source_revision": SOURCE_REVISION, "models": {}}
    for task, (filename, repo, revision) in MODELS.items():
        path = hf_hub_download("ku-nlp/kwja-checkpoints", filename, revision=REVISION, local_dir="artifacts/kwja-checkpoints")
        with torch.serialization.safe_globals([DictConfig, ListConfig, AnyNode, ContainerMetadata, Metadata,
                                              dict, int, list, typing.Any, (metadata_cache, "collections.defaultdict")]):
            checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        folder = root / task
        folder.mkdir()
        save_file({k: v.contiguous().clone() for k, v in checkpoint["state_dict"].items()}, str(folder / "model.safetensors"))
        config = OmegaConf.to_container(checkpoint["hyper_parameters"], resolve=True)
        (folder / "hparams.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        snapshot_download(repo, revision=revision, allow_patterns=["*.json", "*.txt", "*.model"], local_dir=folder / "encoder")
        info["models"][task] = {"repo": repo, "revision": revision, "checkpoint_sha256": digest(path),
                                 "weights_sha256": digest(folder / "model.safetensors"),
                                 "hparams_sha256": digest(folder / "hparams.json")}
        print(task, revision, flush=True)
    (root / "provenance.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
