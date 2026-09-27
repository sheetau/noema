"""Frozen Unify-SRL dependency annotation probe, not a Noema translator.

Inference-compatible architecture for the authors' xlmr_ft_full_all checkpoint:
https://github.com/SapienzaNLP/unify-srl/tree/6d4fe9fadc90be22ed5eeaab12771c4fdc1939eb
No gold predicates, lexical candidate lookup, text generation, or repairs.
"""
import argparse
import json
from pathlib import Path
import platform
from types import SimpleNamespace

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from .encoder import MODELS, deterministic
from .definition_probe import digest
from .semantics import require

SOURCE_REVISION = "6d4fe9fadc90be22ed5eeaab12771c4fdc1939eb"


class StateEncoder(nn.Module):
    def __init__(self, size, hp, prefix):
        super().__init__()
        require(hp[prefix + "_encoder_activation"] == "swish", "Unsupported activation")
        width = hp[prefix + "_encoding_size"]
        self.linears = nn.ModuleList(nn.Linear(size if i == 0 else width, width)
                                    for i in range(hp[prefix + "_encoder_layers"]))

    def forward(self, states):
        for layer in self.linears:
            states = layer(states)
            states = states * states.sigmoid()
        return states


class ConnectedSequence(nn.Module):
    def __init__(self, size, hidden, layers):
        super().__init__()
        self.norms = nn.ModuleList(nn.LayerNorm(size + 2 * hidden * i) for i in range(layers))
        self.lstms = nn.ModuleList(nn.LSTM(size + 2 * hidden * i, hidden, batch_first=True,
                                        bidirectional=True) for i in range(layers))

    def forward(self, states, lengths):
        for norm, lstm in zip(self.norms, self.lstms):
            packed = pack_padded_sequence(norm(states), lengths.cpu(), batch_first=True, enforce_sorted=False)
            values, _ = lstm(packed)
            values, _ = pad_packed_sequence(values, batch_first=True, total_length=states.shape[1])
            states = torch.cat((states, values), dim=-1)
        return states


class SequenceEncoder(nn.Module):
    def __init__(self, size, hp, prefix=""):
        super().__init__()
        require(hp[prefix + "sequence_representation"] == "connected_lstm"
                and hp[prefix + "lstm_bidirectional"], "Unsupported sequence architecture")
        self.sequence_encoder = ConnectedSequence(size, hp[prefix + "lstm_hidden_size"], hp[prefix + "lstm_num_layers"])
        self.output_size = size + 2 * hp[prefix + "lstm_hidden_size"] * hp[prefix + "lstm_num_layers"]

    def forward(self, states, lengths):
        return self.sequence_encoder(states, lengths)


class WordEncoder(nn.Module):
    def __init__(self, hp, config):
        super().__init__()
        from transformers import AutoModel
        self.word_embedding = nn.Module()
        self.word_embedding.bert = AutoModel.from_config(config, attn_implementation="eager")
        self.batch_normalization = nn.BatchNorm1d(config.hidden_size * 4)
        self.projection = nn.Linear(config.hidden_size * 4, hp["word_projection_size"])

    def forward(self, word_ids, subword_indices, sequence_lengths):
        mask = torch.arange(word_ids.shape[1], device=word_ids.device)[None, :] < sequence_lengths[:, None]
        hidden = self.word_embedding.bert(word_ids, attention_mask=mask, output_hidden_states=True).hidden_states
        values = torch.cat(hidden[-4:], dim=-1)
        values = self.batch_normalization(values.transpose(1, 2)).transpose(1, 2)
        values = self.projection(values)
        values = values * values.sigmoid()
        # Native scatter-add mean replaces the obsolete torch-scatter dependency.
        n = int(subword_indices.max()) + 1
        sums = values.new_zeros(values.shape[0], n, values.shape[2])
        counts = values.new_zeros(values.shape[0], n, 1)
        sums.scatter_add_(1, subword_indices[:, :, None].expand_as(values), values)
        counts.scatter_add_(1, subword_indices[:, :, None], values.new_ones(*subword_indices.shape, 1))
        return sums / counts.clamp_min(1)


class TransferNetwork(nn.Module):
    def __init__(self, hp, config):
        super().__init__()
        require(not hp["language_sequence_encoders"] and not hp["language_state_encoders"],
                "Language-specific encoders are not supported by this adapter")
        self.hparams = SimpleNamespace(**hp)
        self.word_encoder = WordEncoder(hp, config)
        self.sequence_encoder = SequenceEncoder(hp["word_projection_size"], hp)
        size = self.sequence_encoder.output_size
        for prefix in ("predicate", "sense", "predicate_timestep", "argument_timestep"):
            setattr(self, prefix + "_encoder", StateEncoder(size, hp, prefix))
        self.argument_sequence_encoder = SequenceEncoder(hp["predicate_timestep_encoding_size"] + hp["argument_timestep_encoding_size"], hp, "argument_")
        self.argument_encoder = StateEncoder(self.argument_sequence_encoder.output_size, hp, "argument")
        for name, width, labels in (("predicate", hp["predicate_encoding_size"], {k: 2 for k in hp["languages"]}),
                                    ("sense", hp["sense_encoding_size"], hp["num_senses"]),
                                    ("role", hp["argument_encoding_size"], hp["num_roles"])):
            setattr(self, name + "_scorer", nn.ModuleDict({k: nn.Linear(width, n) for k, n in labels.items()}))

    def states(self, payload):
        words = self.word_encoder(payload["word_ids"], payload["subword_indices"], payload["tokenized_sequence_lengths"])
        return self.sequence_encoder(words, payload["sequence_lengths"])[:, 1:-1]

    def classify(self, states, inventory, predicate_indices=None):
        require(states.shape[0] == 1, "Probe uses one unpadded sentence at a time")
        predicates = self.predicate_scorer[inventory](self.predicate_encoder(states))[0]
        if predicate_indices is None:
            predicate_indices = predicates.argmax(-1).nonzero().flatten()
        else:
            predicate_indices = torch.as_tensor(predicate_indices, dtype=torch.long)
        chosen = states[0, predicate_indices]
        senses = self.sense_scorer[inventory](self.sense_encoder(chosen))
        if not len(predicate_indices):
            return {"indices": predicate_indices, "predicates": predicates, "senses": senses,
                    "roles": states.new_empty(0, states.shape[1], self.role_scorer[inventory].out_features)}
        pred = self.predicate_timestep_encoder(chosen)[:, None, :].expand(-1, states.shape[1], -1)
        args = self.argument_timestep_encoder(states).expand(len(predicate_indices), -1, -1)
        paired = torch.cat((pred, args), dim=-1)
        lengths = torch.full((len(predicate_indices),), states.shape[1], dtype=torch.long)
        encoded = self.argument_sequence_encoder(paired, lengths)
        roles = self.role_scorer[inventory](self.argument_encoder(encoded))
        return {"indices": predicate_indices, "predicates": predicates, "senses": senses, "roles": roles}


class SRLTransfer:
    def __init__(self, model_dir="artifacts/unify-srl-model", segmenter_dir="artifacts/stanza-srl"):
        import stanza
        import transformers
        from transformers import AutoConfig, AutoTokenizer
        from safetensors.torch import load_file
        deterministic()
        path = Path(model_dir)
        hp = json.loads((path / "hparams.json").read_text(encoding="utf-8"))
        self.labels = json.loads((path / "processor_config.json").read_text(encoding="utf-8"))
        require(hp["language_model"] == self.labels["model_name"] == "xlm-roberta-base", "Unexpected encoder")
        spec = MODELS["xlmr"]
        options = {"revision": spec["revision"], "local_files_only": True, "trust_remote_code": False}
        config = AutoConfig.from_pretrained(spec["id"], **options)
        self.tokenizer = AutoTokenizer.from_pretrained(spec["id"], use_fast=False, **options)
        self.model = TransferNetwork(hp, config)
        state = load_file(path / "model.safetensors")
        # Transformers 2.10 stored this deterministic buffer; newer versions do not.
        positions = state.pop("word_encoder.word_embedding.bert.embeddings.position_ids", None)
        if positions is not None:
            require(torch.equal(positions, torch.arange(config.max_position_embeddings)[None, :]), "Unexpected position buffer")
        self.model.load_state_dict(state, strict=True)
        self.model.eval().requires_grad_(False)
        self.segmenters = {}
        for lang, package in (("ja", "gsd"), ("en", "ewt")):
            segmenter = stanza.Pipeline(lang, dir=segmenter_dir, package=None,
                                       processors={"tokenize": package, "mwt": []},
                                       download_method=None, use_gpu=False, verbose=False)
            require(set(segmenter.processors) == {"tokenize"}, "Only non-generative tokenization is permitted")
            self.segmenters[lang] = segmenter
        self.metadata = {"source_revision": SOURCE_REVISION, "tokenizer": spec,
                         "torch": str(torch.__version__), "transformers": transformers.__version__, "stanza": stanza.__version__,
                         "python": platform.python_version(), "platform": platform.platform(), "device": "cpu", "dtype": "float32",
                         "seed": 17, "threads": torch.get_num_threads(), "gold_predicates": False,
                         "legacy_attention": "final SEP is masked, matching upstream training processor",
                         "files": {str(p): digest(p) for p in [path / "model.safetensors", path / "hparams.json", path / "processor_config.json",
                                  Path(segmenter_dir) / "resources.json", Path(segmenter_dir) / "ja/tokenize/gsd.pt", Path(segmenter_dir) / "en/tokenize/ewt.pt"]}}

    def payload(self, words):
        ids, groups = [self.tokenizer.cls_token_id], [0]
        for i, word in enumerate(words, 1):
            pieces = self.tokenizer.tokenize(word)
            require(bool(pieces), "A token produced no subwords")
            ids.extend(self.tokenizer.convert_tokens_to_ids(pieces))
            groups.extend([i] * len(pieces))
        ids.append(self.tokenizer.sep_token_id)
        groups.append(len(words) + 1)
        require(len(ids) <= 502, "Sentence exceeds model context; no silent truncation")
        return {"word_ids": torch.tensor([ids]), "subword_indices": torch.tensor([groups]),
                "sequence_lengths": torch.tensor([len(words) + 2]), "tokenized_sequence_lengths": torch.tensor([len(ids) - 1])}

    def label(self, inventory, kind, index):
        raw = self.labels["id2" + kind][inventory][str(index)]
        return raw.removeprefix(inventory + "_")

    def analyze(self, text, language):
        require(language in self.segmenters and isinstance(text, str) and text.strip(), "Expected nonempty ja/en text")
        sentences = []
        with torch.inference_mode():
            for sentence in self.segmenters[language](text).sentences:
                tokens = [{"text": t.text, "start": t.start_char, "end": t.end_char} for t in sentence.tokens]
                require(all(text[t["start"]:t["end"]] == t["text"] for t in tokens), "Token offsets do not reproduce source")
                states = self.model.states(self.payload([t["text"] for t in tokens]))
                predictions = {}
                for inv in ("EN", "VA"):
                    result = self.model.classify(states, inv)
                    annotations = []
                    for i, index in enumerate(result["indices"].tolist()):
                        annotations.append({"token": index, "sense": self.label(inv, "predicate", int(result["senses"][i].argmax())),
                                            "roles": [{"token": j, "label": self.label(inv, "role", role)}
                                                      for j, role in enumerate(result["roles"][i].argmax(-1).tolist()) if role != 0]})
                    predictions[inv] = annotations
                sentences.append({"tokens": tokens, "inventories": predictions})
        return {"status": "research_annotation", "language": language, "text": text, "sentences": sentences}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True)
    parser.add_argument("--language", choices=("ja", "en"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = SRLTransfer().analyze(args.text, args.language)
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
