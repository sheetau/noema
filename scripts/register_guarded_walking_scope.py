"""Register a compound diagnostic without changing the manuscript or judgments."""
from copy import deepcopy
import json
from noema.semantic_reviews import digest, load_reviews, validate_hashes
from scripts.check_guarded_walking_scope import ROOT, INDEX as PREVIOUS, REPORT, AUDIT, CORE, DOC, reading

INDEX = 'data/semantic-review-index-v77.json'


def build():
    before = load_reviews(ROOT, PREVIOUS)
    index = json.loads((ROOT/PREVIOUS).read_text(encoding='utf-8'))
    report = json.loads((ROOT/REPORT).read_text(encoding='utf-8'))
    assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8')) == reading()
    validate_hashes(ROOT, report['source_sha256'])
    assert report['structure']['current_selection_bound']
    assert report['confinement']['contrasts']['confinement_after_prevention'] == [True, True, True, False, True]
    assert not report['whole_sentence_semantically_verified']
    assert report['new_verified_sentence_characters'] == report['new_covered_characters'] == 0
    updated = deepcopy(index)
    paths = set(report['source_sha256']) | {PREVIOUS, REPORT, AUDIT, CORE, DOC, 'scripts/register_guarded_walking_scope.py'}
    for path in sorted(paths):
        value = digest((ROOT/path).read_bytes())
        if path in updated['source_sha256']:
            assert updated['source_sha256'][path] == value, path
        updated['source_sha256'][path] = value
    assert updated['works'] == index['works']
    assert len(before['works']['kant-1784']) == 11 and before['works']['einstein-1905'] == []
    return json.dumps(updated, ensure_ascii=False, indent=2)+'\n'


def audit_registration():
    old, new = load_reviews(ROOT, PREVIOUS), load_reviews(ROOT, INDEX)
    assert old['works'] == new['works']
    assert all(new['source_sha256'][p] == h for p, h in old['source_sha256'].items())
    assert sum(r['source_nonblank_characters'] for r in new['works']['kant-1784']) == 1001
    return dict(manuscripts_unchanged=True, whole_unit_judgments_unchanged=11,
        reviewed_whole_unit_characters=1001, new_verified_sentence_characters=0,
        countermodel_registered=True)


def main():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/INDEX, build())
    print(json.dumps(audit_registration(), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
