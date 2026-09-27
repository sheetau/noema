"""Convert the official legacy Unify-SRL checkpoint without arbitrary unpickling."""
import argparse
import json
from pathlib import Path


def main():
    import torch
    from safetensors.torch import save_file
    from noema.definition_probe import digest
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    destinations = [out / name for name in ("model.safetensors", "hparams.json", "conversion.json")]
    if any(p.exists() for p in destinations):
        raise ValueError("Refusing to overwrite converted model files")
    # This metadata type is only a dict in the training framework. Replace it
    # with a builtin rather than importing or executing the old framework.
    with torch.serialization.safe_globals([(dict, "pytorch_lightning.utilities.parsing.AttributeDict")]):
        checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    save_file({k: v.contiguous() for k, v in checkpoint["state_dict"].items()}, destinations[0])
    destinations[1].write_text(json.dumps(dict(checkpoint["hyper_parameters"]), indent=2) + "\n", encoding="utf-8", newline="\n")
    metadata = {"source_sha256": digest(args.checkpoint), "tensor_sha256": digest(destinations[0]),
                "hparams_sha256": digest(destinations[1]), "torch": str(torch.__version__), "weights_only": True}
    destinations[2].write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
