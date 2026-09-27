import itertools
import pytest
torch = pytest.importorskip("torch")
from noema.structured import LABELS, TOKEN_HEADS, SequenceHeads, bio_path, character_features, targets, decode
from noema.dataset import mark, unmark
from noema.semantics import make_graph


def test_viterbi_path_has_the_best_legal_bio_score():
    torch.manual_seed(1)
    scores = torch.randn(3, len(LABELS["span"]))
    legal = []
    for seq in itertools.product(range(len(LABELS["span"])), repeat=3):
        words = [LABELS["span"][i] for i in seq]
        if any(w.startswith("I-") and (i == 0 or words[i-1] not in ("B-"+w[2:], w)) for i, w in enumerate(words)):
            continue
        legal.append((sum(float(scores[i, x]) for i, x in enumerate(seq)), seq))
    assert tuple(bio_path(scores)) == max(legal)[1]


def test_exact_quantity_and_name_are_copied_from_character_spans():
    text, spans = unmark(mark("entity", "Hana", "agent", "ag") + " sees " + mark("quantity", "12345", "patient", quantity=12345) + " " + mark("entity", "cats", "patient", "ab", 12345))
    # Add the predicate annotation, which the surface helper above kept plain.
    spans.append({"start": 5, "end": 9, "kind": "predicate", "concept": "bb", "role": "none", "quantity": "unspecified"})
    spans.sort(key=lambda s: s["start"])
    graph = make_graph("bb", {"agent": {"concept": "ag", "name": "Hana"}, "patient": {"concept": "ab", "quantity": 12345}})
    row = {"id": "copy", "text": text, "spans": spans, "graph": graph, "supported": True}
    feature = {"offsets": [(i, i+1) for i in range(len(text))], "truncated": False}
    gold = targets(row, feature)
    logits = {}
    for key, value in gold.items():
        logits[key] = torch.full((*value.shape, len(text) if key == "attachment" else len(LABELS[key])), -20.)
        logits[key].scatter_(-1, value.clamp_min(0).unsqueeze(-1), 20.)
    result = decode(text, feature, logits, .9)
    assert result["status"] == "confirmed" and result["graph"] == graph
    # The learned link, rather than the number token's role label, decides its target.
    for i in range(10, 15):
        logits["role"][i] = -20.
        logits["role"][i, LABELS["role"].index("agent")] = 20.
    assert decode(text, feature, logits, .9)["graph"] == graph


def test_decimal_type_constraints_do_not_split_a_number_or_capture_a_suffix():
    values = torch.full((3, len(LABELS["span"])), -10.)
    values[:, LABELS["span"].index("B-quantity")] = 10.
    values[:, LABELS["span"].index("I-quantity")] = 9.
    values[:, LABELS["span"].index("O")] = 8.
    assert [LABELS["span"][i] for i in bio_path(values, "12匹")] == ["B-quantity", "I-quantity", "O"]


def test_character_projection_retains_each_original_position():
    text = "12匹"
    frozen = {"tokens": torch.arange(8.).reshape(2, 4), "offsets": [(0, 3), (0, 0)], "truncated": False}
    projected = character_features(text, frozen)
    assert projected["offsets"] == [(0, 1), (1, 2), (2, 3)]
    assert projected["tokens"].shape == (3, 13)
    assert torch.equal(projected["tokens"][0, :4], projected["tokens"][2, :4])
    assert projected["tokens"][0, -4] == 1 and projected["tokens"][2, -4] == 0


def test_sequence_heads_ignore_padding_and_receive_gradients():
    torch.manual_seed(2)
    model = SequenceHeads(13, hidden=8).eval()
    tokens = torch.randn(2, 6, 13)
    tokens[:, :, -1] = torch.randint(0, 4096, (2, 6)).float()
    batched = model(tokens, torch.tensor([3, 6]))
    single = model(tokens[:1, :3], torch.tensor([3]))
    for key in LABELS:
        assert torch.allclose(batched[key][0, :3] if key in TOKEN_HEADS else batched[key][0], single[key][0], atol=1e-6)
    assert torch.allclose(batched["attachment"][0, :3, :3], single["attachment"][0], atol=1e-6)
    assert torch.isneginf(batched["attachment"][0, :, 3:]).all()
    batched["span"].sum().backward()
    assert model.sequence.weight_ih_l0.grad is not None
