import pytest
torch = pytest.importorskip("torch")
from noema.model import Heads, LABELS, targets, decode
from noema.dataset import unmark, mark
from noema.semantics import make_graph


def fixture():
    text, spans = unmark(mark("entity", "犬", "agent", "aa") + "が" + mark("entity", "猫", "patient", "ab") + "を" + mark("predicate", "追う", concept="ba"))
    graph = make_graph("ba", {"agent": {"concept": "aa"}, "patient": {"concept": "ab"}})
    feature = {"offsets": [(0, 0)] + [(i, i + 1) for i in range(len(text))] + [(0, 0)], "truncated": False}
    return {"id": "unit", "text": text, "spans": spans, "supported": True, "graph": graph}, feature


def oracle_logits(row, feature):
    gold = targets(row, feature)
    logits = {}
    for k, target in gold.items():
        value = torch.full((*target.shape, len(LABELS[k])), -20.)
        value.scatter_(-1, target.clamp_min(0).unsqueeze(-1), 20.)
        logits[k] = value
    return logits


def test_decode_roles_and_low_confidence():
    row, feature = fixture()
    logits = oracle_logits(row, feature)
    result = decode(row["text"], feature, logits)
    assert result["status"] == "confirmed" and result["graph"] == row["graph"]
    logits["polarity"][:] = 0
    assert decode(row["text"], feature, logits)["status"] == "unresolved"


def test_bad_bio_truncation_and_unknown():
    row, feature = fixture()
    logits = oracle_logits(row, feature)
    logits["span"][1] = -20
    logits["span"][1, LABELS["span"].index("I-entity")] = 20
    assert decode(row["text"], feature, logits)["status"] == "unresolved"
    feature["truncated"] = True
    assert decode(row["text"], feature, oracle_logits(row, feature))["diagnostics"]["reason"] == "input_too_long"
    feature["truncated"] = False
    logits = oracle_logits(row, feature)
    logits["support"] = torch.tensor([20., -20.])
    assert decode(row["text"], feature, logits)["status"] == "unsupported"


@pytest.mark.parametrize("architecture", ["linear", "mlp"])
def test_heads_train_without_encoder(architecture):
    torch.manual_seed(5)
    h = Heads(8, architecture)
    token, pooled = torch.randn(5, 8), torch.randn(8)
    optimizer = torch.optim.Adam(h.parameters(), lr=.03)
    before = float(torch.nn.functional.cross_entropy(h(token, pooled)["role"], torch.ones(5, dtype=torch.long)).detach())
    for _ in range(10):
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(h(token, pooled)["role"], torch.ones(5, dtype=torch.long))
        loss.backward()
        optimizer.step()
    assert float(loss.detach()) < before
