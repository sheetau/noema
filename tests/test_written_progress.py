"""Progress must not promote a partial association to semantic completion."""
import pytest

from scripts.audit_written_progress import collect_alignment, digest, merge_ranges, summarize


def unit(work='kant-1784', text='ab cd', kind='body', math_ids=None):
    return {'id': work + ':u0001', 'kind': kind, 'text': text,
            'text_sha256': digest(text.encode('utf-8')), 'math_ids': math_ids or []}


def collect(item, **changes):
    source = unit(**changes)
    report = {'source_unit': source['id'], 'source_alignment': item}
    return collect_alignment(report, {source['id']: source}, {'aa'}, 'example.json')


def test_ranges_union_without_double_counting():
    assert merge_ranges([[2, 5], [0, 3], [0, 3], [7, 9], [9, 10]]) == [[0, 5], [7, 10]]


def test_unbounded_association_does_not_count_as_full_text():
    source, other = unit(), unit('einstein-1905')
    records = collect({'status': 'partial', 'definitions': ['aa']})
    row = summarize({s['id']: s for s in (source, other)}, {}, records)['kant-1784']
    assert row['units_with_partial_drafts'] == 1
    assert row['text_characters_in_explicit_partial_ranges'] == 0
    assert row['verified_semantic_units'] == 0


def test_math_is_separate_and_editorial_is_excluded():
    source = unit(text='ab [M0001] cd', math_ids=['M0001'])
    other = unit('einstein-1905')
    editorial = dict(unit(kind='editorial'), id='kant-1784:u0002')
    records = collect({'status': 'partial', 'range': [0, 10]},
                      text=source['text'], math_ids=source['math_ids'])
    row = summarize({s['id']: s for s in (source, other, editorial)},
                    {('kant-1784', 'M0001'): {}}, records)['kant-1784']
    assert row['author_unit_count'] == 1
    assert row['nonblank_text_characters'] == 4
    assert row['text_characters_in_explicit_partial_ranges'] == 2
    assert row['math_objects_with_partial_associations'] == 1


def test_pending_and_unstructured_mentions_are_not_evidence():
    assert collect({'status': 'pending', 'range': [0, 5]}) == []
    assert collect({'context_units_still_partial': ['kant-1784:u0001']}) == []


@pytest.mark.parametrize('item', [
    {'status': 'partial', 'range': [0, 6]},
    {'status': 'partial', 'range': [False, 5]},
    {'status': 'partial', 'range': [0, 2], 'text': 'wrong'},
    {'status': 'partial', 'range': [0, 2], 'text_sha256': 'wrong'},
    {'status': 'partial', 'definitions': ['unknown']},
    {'status': 'partial', 'math_id': 'M9999'},
    {'status': 'complete', 'range': [0, 5]},
])
def test_invalid_or_unreviewed_evidence_is_rejected(item):
    with pytest.raises(ValueError):
        collect(item)


def test_editorial_cannot_be_promoted_to_author_progress():
    with pytest.raises(ValueError, match='Editorial'):
        collect({'status': 'partial', 'range': [0, 2]}, kind='editorial')
