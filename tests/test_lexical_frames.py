import copy
import json
from pathlib import Path

import pytest

from noema.lexical_frames import frame_queries, assemble_lexical_frames, LexicalFrameAnalyzer
from noema.lexical_frame_metrics import oracle_queries, assess_lexical_frames, summarize_lexical_frames
from noema.semantics import SemanticError


def fixture():
    row = {'id': 'sample', 'text': 'DOG SEES CAT', 'frames': [
        {'predicate': 'SEES', 'concept': 'bb', 'roles': [('agent', 'DOG', 'aa'), ('patient', 'CAT', 'ab')]}]}
    output = {'analysis': {'text': row['text']}, 'frames': [
        {'source': 1, 'predicate': {'start': 4, 'end': 8}, 'mentions': [
            {'id': 'dog', 'start': 0, 'end': 3}, {'id': 'cat', 'start': 9, 'end': 12}],
         'roles': [{'target': 'dog', 'role': 'agent'}, {'target': 'cat', 'role': 'patient'}]}]}
    matches = [{'start': a, 'end': b, 'span': row['text'][a:b], 'top': [{'concept': c, 'score': .3}]}
               for a, b, c in ((0, 3, 'aa'), (4, 8, 'bb'), (9, 12, 'ab'))]
    return row, output, matches


def test_predicted_spans_are_deduplicated_but_extra_roles_are_preserved():
    row, output, matches = fixture()
    output['frames'][0]['roles'].append({'target': 'dog', 'role': 'agent'})
    assert frame_queries(output) == [{'start': 0, 'end': 3}, {'start': 4, 'end': 8}, {'start': 9, 'end': 12}]
    result = assemble_lexical_frames(output, matches)
    assert len(result['frames'][0]['roles']) == 3
    assert result['frames'][0]['structural_errors'] == ['multiple_arguments_for_one_role']
    case = assess_lexical_frames(row, result)
    assert case['extra_role_span_concepts'] == 1 and not case['core_frames_exact']


def test_valid_core_is_never_reported_as_confirmed_whole_meaning():
    row, output, matches = fixture()
    before = copy.deepcopy(output)
    result = assemble_lexical_frames(output, matches)
    assert result['document'] is None and result['confirmed'] is False
    assert 'polarity_and_scope' in result['missing_components'] and 'quantity' in result['missing_components']
    assert output == before
    case = assess_lexical_frames(row, result)
    assert case['core_frames_exact'] and not case['confirmed']
    summary = summarize_lexical_frames([case])
    assert summary['accepted_coverage'] == 0 and summary['accepted_full_meaning_exact_accuracy'] is None
    assert not summary['acceptance_gate_passed']


def test_type_incompatibility_does_not_pick_a_more_convenient_candidate():
    _, output, matches = fixture()
    matches[1]['top'] = [{'concept': 'af', 'score': .6}, {'concept': 'bb', 'score': .5}]
    result = assemble_lexical_frames(output, matches)
    assert result['frames'][0]['predicate']['concept'] == 'af'
    assert 'predicate_is_not_event_or_state' in result['frames'][0]['structural_errors']
    matches[1]['top'][0]['concept'] = 'bb'
    matches[0]['top'][0]['concept'] = 'ah'
    assert 'argument_type_incompatible_with_role' in assemble_lexical_frames(output, matches)['frames'][0]['structural_errors']


def test_exact_role_spans_unknowns_and_missing_events_remain_errors():
    row, output, matches = fixture()
    result = assemble_lexical_frames(output, matches)
    result['frames'][0]['roles'][0]['end'] = 2
    case = assess_lexical_frames(row, result)
    assert case['correct_role_spans'] == 1 and not case['core_frames_exact']
    result = assemble_lexical_frames(output, matches)
    row['frames'][0]['concept'] = None
    assert not assess_lexical_frames(row, result)['core_frames_exact']
    result['frames'] = []
    case = assess_lexical_frames(row, result)
    assert case['gold_frames'] == 1 and case['missing_role_span_concepts'] == 2


def test_invalid_matches_and_targets_are_not_silently_ignored():
    _, output, matches = fixture()
    with pytest.raises(SemanticError, match='predicted spans'):
        assemble_lexical_frames(output, matches[1:])
    matches[0]['span'] = 'OTHER'
    with pytest.raises(SemanticError, match='source span'):
        assemble_lexical_frames(output, matches)
    output['frames'][0]['roles'][0]['target'] = 'absent'
    with pytest.raises(SemanticError, match='predicted mention'):
        frame_queries(output)


def test_inference_path_only_passes_raw_text_and_predicted_queries():
    _, output, matches = fixture()
    calls = []
    class Structure:
        def analyze(self, text):
            calls.append(('structure', text))
            return output
    class Matcher:
        def match(self, text, spans):
            calls.append(('match', text, spans))
            return matches
    analyzer = LexicalFrameAnalyzer.__new__(LexicalFrameAnalyzer)
    analyzer.structure, analyzer.matcher = Structure(), Matcher()
    result = analyzer.analyze('DOG SEES CAT')
    assert calls == [('structure', 'DOG SEES CAT'), ('match', 'DOG SEES CAT', frame_queries(output))]
    assert result['status'] == 'research_lexical_frames'


def test_fixed_annotations_have_unambiguous_source_positions_and_valid_concepts():
    rows = json.loads(Path('data/lexical-frames-v1.json').read_text(encoding='utf-8'))
    assert len(rows) == len({r['id'] for r in rows}) == 18
    queries = [q for row in rows for q in oracle_queries(row)]
    assert sum(q['expected'] is None for q in queries) == 2
