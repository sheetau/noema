"""Carry twelve unchanged unit judgments into an append-only content extension."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, load_reviews, validate_hashes
from scripts.compose_graded_change import ROOT, FULL, BASIS, ANNOTATIONS
from scripts.check_graded_change import INDEX as PREVIOUS, REPORT, AUDIT, DOC

INDEX = 'data/semantic-review-index-v90.json'
REVALIDATION = 'Five definitions compose uniquely assessed qualitative degrees, actual increase to a near-target region, and retained near states. The source schema keeps its comparison reference and assessment explicit; the nature comparison is not yet grounded. No new primitives or authored assertions are added. All 51 previous statements and inherited meanings are unchanged; twelve review bindings are identical. No new sentence or unit completion is counted.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def build():
    load_reviews(ROOT, PREVIOUS)
    index = read(PREVIOUS); active = index['works']['kant-1784']
    old, new = load_catalog(ROOT, active['meaning_basis']), load_catalog(ROOT, BASIS)
    report, reading = read(REPORT), read(AUDIT)
    for r in (report, reading):
        validate_hashes(ROOT, r['source_sha256'])
    assert report['structure']['preserved_review_selections'] == 12
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 51
    assert not report['whole_sentence_semantically_verified'] and report['new_verified_sentence_characters'] == 0
    paths = set(new.source_sha256) | set(report['source_sha256']) | set(reading['source_sha256']) | {
        FULL, BASIS, ANNOTATIONS, REPORT, AUDIT, DOC, 'scripts/register_graded_change.py'}
    pins = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    outputs = {}; migrated = []
    for path in active['reviews']:
        review = read(path); ids = [r['index'] for r in review['selection']['statements']]
        assert review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
        revised = deepcopy(review)
        revised.update(document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
                       revalidated_from=path, revalidation=REVALIDATION)
        revised['evidence']['formal_checks'].append(REPORT)
        revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins)
        revised['source_sha256'][path] = digest((ROOT / path).read_bytes())
        name = 'data/graded-change-inherited-' + review['unit'].split(':')[-1] + '-review-v1.json'
        outputs[name] = encoded(revised); migrated.append(name)
    index['works']['kant-1784'].update(document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS, reviews=migrated)
    index['source_sha256'].update({p: digest((ROOT / p).read_bytes()) for p in (PREVIOUS, FULL, BASIS, ANNOTATIONS)})
    index['source_sha256'].update({p: digest(s.encode('utf-8')) for p, s in outputs.items()})
    outputs[INDEX] = encoded(index)
    return outputs


def audit_registration():
    old, new = load_reviews(ROOT, PREVIOUS), load_reviews(ROOT, INDEX)
    before, after = old['works']['kant-1784'], new['works']['kant-1784']
    assert [r['unit'] for r in before] == [r['unit'] for r in after] and len(after) == 12
    assert sum(r['source_nonblank_characters'] for r in after) == 2212
    assert new['works']['einstein-1905'] == old['works']['einstein-1905'] == []
    for a, b in zip(before, after):
        first, last = read(a['review']), read(b['review'])
        assert all(first[k] == last[k] for k in ('source', 'selection', 'decision', 'reviewer', 'interpretation', 'limits', 'requirements', 'unresolved'))
        assert last['revalidated_from'] == a['review'] and last['revalidation'] == REVALIDATION
    return dict(previous_reviews_preserved=12, reviewed_nonblank_characters=2212,
                new_whole_unit_reviews=0, new_verified_sentence_characters=0, automatic_equivalence_proof=False)


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print(json.dumps(audit_registration(), ensure_ascii=False), flush=True)
