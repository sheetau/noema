import itertools

import pytest

torch = pytest.importorskip("torch")
from noema.mention_sequence import BIOChain, SequenceMentionHead, infer_sequence_mentions
from noema.semantics import SemanticError


def valid_paths(length):
    return [path for path in itertools.product(range(3), repeat=length) if path[0] != 2
            and all(current != 2 or previous in (1, 2) for previous, current in zip(path, path[1:]))]


def path_score(chain, emissions, path):
    return (chain.starts[path[0]] + chain.ends[path[-1]] + sum(emissions[i, label] for i, label in enumerate(path))
            + sum(chain.transitions[a, b] for a, b in zip(path, path[1:])))


def test_partition_decode_and_nll_match_all_valid_paths():
    torch.manual_seed(8)
    chain = BIOChain()
    with torch.no_grad():
        chain.starts.copy_(torch.randn(3))
        chain.ends.copy_(torch.randn(3))
        chain.transitions.copy_(torch.randn(3, 3))
    emissions = torch.randn(4, 3)
    paths = valid_paths(4)
    scores = torch.stack([path_score(chain, emissions, path) for path in paths])
    expected = torch.logsumexp(scores, dim=0)
    assert torch.allclose(chain.partition(emissions[None], torch.tensor([4]))[0], expected)
    best = int(scores.argmax())
    assert chain.decode(emissions) == list(paths[best])
    assert torch.allclose(chain.nll(emissions[None], torch.tensor([paths[best]]), torch.tensor([4]))[0], expected - scores[best])


def test_padding_and_batching_do_not_join_independent_sentences():
    torch.manual_seed(10)
    chain = BIOChain()
    first, second = torch.randn(2, 3), torch.randn(4, 3)
    padded = torch.stack((torch.cat((first, torch.full((2, 3), 1000.))), second))
    tags = torch.tensor([[1, 2, 0, 2], [0, 1, 2, 0]])
    batch = chain.nll(padded, tags, torch.tensor([2, 4]))
    individual = torch.cat((chain.nll(first[None], tags[:1, :2], torch.tensor([2])),
                            chain.nll(second[None], tags[1:], torch.tensor([4]))))
    assert torch.allclose(batch, individual)
    padded.requires_grad_()
    chain.nll(padded, tags, torch.tensor([2, 4])).sum().backward()
    assert torch.equal(padded.grad[0, 2:], torch.zeros(2, 3))
    assert torch.isfinite(padded.grad).all()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in chain.parameters())


def test_invalid_gold_is_rejected_without_repair():
    chain = BIOChain()
    for tags in ([[2, 0]], [[0, 2]]):
        with pytest.raises(SemanticError, match="Invalid gold BIO"):
            chain.nll(torch.zeros(1, 2, 3), torch.tensor(tags), torch.tensor([2]))
    with pytest.raises(SemanticError, match="Invalid sequence lengths"):
        chain.partition(torch.zeros(1, 2, 3), torch.tensor([0]))


def test_sequence_head_trains_with_finite_gradients():
    torch.manual_seed(17)
    head = SequenceMentionHead(4, 3)
    loss = head.loss(torch.randn(2, 4, 4), torch.tensor([[0, 1, 2, 0], [1, 2, 0, 0]]), torch.tensor([4, 3]))
    loss.backward()
    assert torch.isfinite(loss)
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters())


def test_decoding_preserves_source_offsets_and_empty_documents():
    head = SequenceMentionHead(2)
    with torch.no_grad():
        head.emitter.network.weight.zero_()
        head.emitter.network.bias.copy_(torch.tensor([0., 5., 0.]))
        head.chain.transitions[1, 2] = 10
    text = "AB"
    prediction = {"text": text, "tokens": [{"text": "A", "start": 0, "end": 1}, {"text": "B", "start": 1, "end": 2}]}
    assert infer_sequence_mentions(prediction, torch.eye(2), head) == [{"id": 0, "text": "AB", "start": 0, "end": 2}]
    assert infer_sequence_mentions({"text": "", "tokens": []}, torch.empty(0, 2), head) == []


def test_sequence_confirmation_is_new_and_voice_pairs_have_same_roles():
    import json
    from pathlib import Path
    from scripts.train_mention_learning import DATA
    from scripts.train_role_transfer import validate_rows
    old = [r for path in (*DATA, "data/role-context-v3.json") for r in json.loads(Path(path).read_text(encoding="utf-8"))]
    new = json.loads(Path("data/mention-sequence-v4.json").read_text(encoding="utf-8"))
    validate_rows(old + new)
    assert len(new) == 8 and sum(len(r["roles"]) for r in new) == 20
    assert not ({r["family"] for r in old} & {r["family"] for r in new})
    for family in {r["family"] for r in new}:
        pair = [r for r in new if r["family"] == family]
        assert len(pair) == 2 and sorted(pair[0]["roles"]) == sorted(pair[1]["roles"])
