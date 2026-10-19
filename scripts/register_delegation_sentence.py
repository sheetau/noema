"""Pin the sentence audit while preserving its unresolved semantic gate."""
from copy import deepcopy
import json
from noema.semantic_reviews import digest, load_reviews, validate_hashes
from scripts.check_delegation_sentence import ROOT, INDEX as PREVIOUS, REPORT, AUDIT, DOC, CORE, reading

INDEX = 'data/semantic-review-index-v56.json'


def build():
    before = load_reviews(ROOT, PREVIOUS)
    index = json.loads((ROOT / PREVIOUS).read_text(encoding='utf-8'))
    review = json.loads((ROOT / AUDIT).read_text(encoding='utf-8'))
    assert review == reading() and not review['whole_unit_semantically_verified']
    assert not review['whole_sentence_semantically_verified']
    report = json.loads((ROOT / REPORT).read_text(encoding='utf-8'))
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert report['integrity']['current_selection_bound']
    assert not report['whole_sentence_semantically_verified']
    assert report['lexical_gap']['current_sp_does_not_distinguish_status']
    assert report['new_verified_sentence_characters'] == 0
    for record in (review, report):
        validate_hashes(ROOT, record['source_sha256'])
    paths = set(review['source_sha256']) | set(report['source_sha256']) | {
        PREVIOUS, REPORT, AUDIT, DOC, CORE, 'scripts/register_delegation_sentence.py'}
    updated = deepcopy(index)
    for path in sorted(paths):
        value = digest((ROOT / path).read_bytes())
        if path in updated['source_sha256']:
            assert updated['source_sha256'][path] == value, path
        updated['source_sha256'][path] = value
    assert updated['works'] == index['works']
    assert len(before['works']['kant-1784']) == 11 and before['works']['einstein-1905'] == []
    return json.dumps(updated, ensure_ascii=False, indent=2) + '\n'


def audit_registration():
    old, new = load_reviews(ROOT, PREVIOUS), load_reviews(ROOT, INDEX)
    assert old['works'] == new['works']
    assert all(new['source_sha256'][p] == h for p, h in old['source_sha256'].items())
    assert sum(r['source_nonblank_characters'] for r in new['works']['kant-1784']) == 1001
    assert not new['semantic_equivalence_automatically_proved']
    return dict(manuscripts_unchanged=True, whole_unit_judgments_unchanged=11,
        reviewed_whole_unit_characters=1001, sentence_audit_does_not_add_a_whole_unit=True,
        unresolved_clerical_status_retained=True, all_new_evidence_inputs_pinned=True)


def main():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT / INDEX, build())
    print(json.dumps(audit_registration(), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
