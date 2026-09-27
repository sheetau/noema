import math
import pytest
torch = pytest.importorskip("torch")
from noema.joint import assign_roles, decode
from noema.structured import LABELS, targets
from noema.semantics import SemanticError, make_graph
from noema.dataset import mark, unmark


def distribution(**values):
    return torch.tensor([values.get(role, 0.) for role in LABELS["role"]])


def test_global_assignment_resolves_duplicate_argmax_without_changing_frame():
    # Both independent argmax decisions say agent; the best *joint* mapping is unique.
    a = distribution(agent=.9, patient=.1)
    b = distribution(agent=.6, patient=.4)
    roles, confidence, evidence = assign_roles("ba", ["aa", "ab"], [a, b], 3)
    assert roles == ("agent", "patient")
    assert evidence["posterior"] == pytest.approx(.36 / (.36 + .06))
    assert confidence == pytest.approx(math.sqrt(.36))
    # Swapping input entity order must preserve the assignment to each entity.
    reverse, same_confidence, _ = assign_roles("ba", ["ab", "aa"], [b, a], 3)
    assert reverse == tuple(reversed(roles))
    assert same_confidence == pytest.approx(confidence)


def test_ties_missing_entities_and_incompatible_frames_remain_unresolved():
    p = distribution(agent=.5, patient=.5)
    with pytest.raises(SemanticError, match="Ambiguous"):
        assign_roles("ba", ["aa", "ab"], [p, p], 3)
    with pytest.raises(SemanticError, match="presence"):
        assign_roles("ba", ["aa"], [p], 3)
    with pytest.raises(SemanticError, match="presence"):
        assign_roles("be", ["aa", "ab"], [p, p], 3)
    with pytest.raises(SemanticError, match="typed"):
        assign_roles("ba", ["aa", "ah"], [p, p], 3)


def oracle():
    text, spans = unmark(mark("entity", "dog", "agent", "aa") + " " + mark("predicate", "sees", concept="bb") + " " + mark("quantity", "123", "patient", quantity=123) + " " + mark("entity", "cats", "patient", "ab", 123))
    graph = make_graph("bb", {"agent": {"concept": "aa"}, "patient": {"concept": "ab", "quantity": 123}})
    feature = {"offsets": [(i, i + 1) for i in range(len(text))], "truncated": False}
    row = {"supported": True, "graph": graph, "spans": spans}
    logits = {}
    for key, value in targets(row, feature).items():
        logits[key] = torch.full((*value.shape, len(text) if key == "attachment" else len(LABELS[key])), -20.)
        logits[key].scatter_(-1, value.clamp_min(0).unsqueeze(-1), 20.)
    return text, feature, graph, logits


def test_quantity_uses_jointly_assigned_entity_role_and_preserves_exact_literal():
    text, feature, graph, logits = oracle()
    assert decode(text, feature, logits, .9)["graph"] == graph
    logits["role"][text.index("cats"):] = distribution(agent=.6, patient=.4).clamp_min(1e-20).log()
    result = decode(text, feature, logits, .5)
    assert result["graph"] == graph
    assert result["diagnostics"]["confidence"] < .7
    assert decode(text, feature, logits, .9)["status"] == "unresolved"


def test_partial_decimal_literal_is_rejected_rather_than_silently_shortened():
    text, feature, _, logits = oracle()
    end = text.index("123") + 2
    logits["span"][end] = -20.
    logits["span"][end, LABELS["span"].index("O")] = 20.
    result = decode(text, feature, logits)
    assert result["status"] == "unresolved"
    assert "complete decimal literal" in result["diagnostics"]["reason"]


@pytest.mark.parametrize("value", [-1, True, 1.5, "1"])
def test_invalid_numeric_values_cannot_enter_base32_conversion(value):
    from noema.grammar import number_word
    with pytest.raises(SemanticError):
        number_word(value)
