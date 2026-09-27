"""Extract frozen native reference scores and contextual node vectors."""
import torch
from torch.nn import functional as F

from .semantics import require


def extract_reference_features(parser, text):
    config = parser.configs["word"]
    tasks = list(config.cohesion_tasks)
    require("coreference_resolution" in tasks, "Native model has no reference head")
    relation_index = (len(config.pas_cases) if "pas_analysis" in tasks else 0) + (len(config.br_cases) if "bridging_reference_resolution" in tasks else 0)
    special = [token for token in config.special_tokens if token != " "]
    captured = []
    hook = parser.models["word"].register_forward_hook(
        lambda module, args, result: captured.append(result["cohesion_logits"][0, relation_index].detach().clone()))
    try:
        prediction, vectors = parser.analyze(text, return_features=True)
    finally:
        hook.remove()
    require(len(captured) == 1, "Expected one native reference forward")
    tokens, phrases = prediction["tokens"], prediction["phrases"]
    require([p["id"] for p in phrases] == list(range(len(phrases))), "Reference phrase order differs")
    require(len(vectors) == len(tokens), "Reference token vectors differ")
    lookup = {(t["start"], t["end"]): i for i, t in enumerate(tokens)}
    indices, nodes = [], []
    for phrase in phrases:
        key = phrase["head"]["start"], phrase["head"]["end"]
        require(key in lookup, "Reference head is not a source token")
        index = lookup[key]
        contained = [i for i, t in enumerate(tokens) if phrase["start"] <= t["start"] and t["end"] <= phrase["end"]]
        require(bool(contained), "Reference phrase has no tokens")
        indices.append(index)
        nodes.append(torch.cat((F.normalize(vectors[index], dim=0), F.normalize(vectors[contained].mean(0), dim=0))))
    logits = captured[0]
    nonlink = [len(tokens) + i for i, token in enumerate(special) if token != "[ROOT]"]
    require(bool(nonlink) and max(nonlink) < logits.shape[1], "Reference special positions differ")
    head_scores = logits[indices]
    native = torch.cat((head_scores[:, nonlink].max(-1, keepdim=True).values, head_scores[:, indices]), dim=1)
    return prediction, {"nodes": torch.stack(nodes).cpu() if nodes else vectors.new_empty((0, vectors.shape[1] * 2)).cpu(),
                        "native": native.cpu(), "word_indices": torch.tensor(indices, dtype=torch.long),
                        "word_count": torch.tensor(len(tokens), dtype=torch.long)}

