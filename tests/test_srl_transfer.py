import json
from pathlib import Path
from types import SimpleNamespace
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
from transformers import XLMRobertaConfig
from noema.srl_transfer import TransferNetwork, SRLTransfer
from noema.semantics import SemanticError
from scripts.probe_srl_transfer import assess, overlaps, frame_agreement


def tiny_model():
    hp = {"word_projection_size": 8, "language_sequence_encoders": False, "language_state_encoders": False,
          "languages": ["EN"], "num_senses": {"EN": 5}, "num_roles": {"EN": 3}}
    for prefix in ("", "argument_"):
        hp.update({prefix + "sequence_representation": "connected_lstm", prefix + "lstm_hidden_size": 4,
                   prefix + "lstm_num_layers": 2, prefix + "lstm_bidirectional": True})
    for prefix in ("predicate", "sense", "predicate_timestep", "argument_timestep", "argument"):
        hp.update({prefix + "_encoding_size": 4, prefix + "_encoder_layers": 1, prefix + "_encoder_activation": "swish"})
    return TransferNetwork(hp, XLMRobertaConfig(vocab_size=32, hidden_size=8, num_hidden_layers=4,
                                              num_attention_heads=2, intermediate_size=16, max_position_embeddings=32)).eval()


def test_predicates_are_predicted_and_empty_sentence_analysis_is_well_formed():
    model = tiny_model()
    payload = {"word_ids": torch.tensor([[0, 4, 5, 6, 2]]), "subword_indices": torch.tensor([[0, 1, 1, 2, 3]]),
               "sequence_lengths": torch.tensor([4]), "tokenized_sequence_lengths": torch.tensor([4])}
    with torch.inference_mode():
        states = model.states(payload)
        model.predicate_scorer["EN"].weight.zero_()
        model.predicate_scorer["EN"].bias.copy_(torch.tensor([1., 0.]))
        absent = model.classify(states, "EN")
        assert absent["indices"].tolist() == [] and absent["roles"].shape == (0, 2, 3)
        model.predicate_scorer["EN"].bias.copy_(torch.tensor([0., 1.]))
        detected = model.classify(states, "EN")
        assert detected["indices"].tolist() == [0, 1] and detected["roles"].shape == (2, 2, 3)
        # Explicit positions are only for compatibility diagnostics. Reordering
        # them must reorder predicate/argument scores without reassigning roles.
        reverse = model.classify(states, "EN", [1, 0])
        torch.testing.assert_close(detected["roles"].flip(0), reverse["roles"])


def test_pooling_and_attention_keep_the_trained_encoder_convention():
    model = tiny_model()
    seen = {}
    class Fixed(torch.nn.Module):
        def forward(self, ids, attention_mask, output_hidden_states):
            seen["mask"] = attention_mask.tolist()
            values = torch.arange(40, dtype=torch.float32).reshape(1, 5, 8)
            return SimpleNamespace(hidden_states=[values] * 4)
    model.word_encoder.word_embedding.bert = Fixed()
    args = (torch.tensor([[0, 4, 5, 6, 2]]), torch.tensor([[0, 1, 1, 2, 3]]), torch.tensor([4]))
    with torch.inference_mode():
        pooled = model.word_encoder(*args)
        individual = model.word_encoder(args[0], torch.arange(5)[None, :], args[2])
    assert seen["mask"] == [[True, True, True, True, False]]
    torch.testing.assert_close(pooled[:, 1], individual[:, 1:3].mean(1))
    torch.testing.assert_close(pooled[:, [0, 2, 3]], individual[:, [0, 3, 4]])


def test_input_length_is_rejected_without_silent_truncation():
    probe = object.__new__(SRLTransfer)
    class Tokenizer:
        cls_token_id, sep_token_id = 0, 2
        def tokenize(self, word): return list(word)
        def convert_tokens_to_ids(self, pieces): return [3] * len(pieces)
    probe.tokenizer = Tokenizer()
    assert probe.payload(["x" * 500])["word_ids"].shape == (1, 502)
    with pytest.raises(SemanticError, match="no silent truncation"):
        probe.payload(["x" * 501])


def test_evaluation_keeps_wrong_role_and_wrong_target_distinct():
    row = {"id": "test", "en": "Dog sees cat", "predicates": [{"en": "sees", "roles": [["A0", "", "Dog"], ["A1", "", "cat"]]}]}
    tokens = [{"start": 0, "end": 3}, {"start": 4, "end": 8}, {"start": 9, "end": 12}]
    result = {"language": "en", "text": row["en"], "sentences": [{"tokens": tokens, "inventories": {"EN": [
        {"token": 1, "roles": [{"token": 0, "label": "A0"}, {"token": 0, "label": "A1"}]}]}}]}
    scored = assess(row, result)
    assert scored["checks"][0]["detected"] and not scored["all_specified_checks"]
    assert [r["correct"] for r in scored["checks"][0]["roles"]] == [True, False]
    assert not overlaps(tokens[0], (3, 4))


def test_committed_predictions_reproduce_partial_assessment():
    root = Path("reports/srl-transfer-v1")
    rows = {r["id"]: r for r in json.loads(Path("data/srl-transfer-v1.json").read_text(encoding="utf-8"))}
    predictions = json.loads((root / "predictions.json").read_text(encoding="utf-8"))
    actual = json.loads(json.dumps([assess(rows[p["id"]], p) for p in predictions]))
    assert actual == json.loads((root / "assessment.json").read_text(encoding="utf-8"))
    assert frame_agreement(list(rows.values()), predictions) == json.loads((root / "frame-agreement.json").read_text(encoding="utf-8"))
