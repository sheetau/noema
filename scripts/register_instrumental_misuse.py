"""Preserve unit and sentence judgments while connecting a third-sentence candidate."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, load_reviews, validate_hashes
from scripts.compose_instrumental_misuse import ROOT, FULL, BASIS, ANNOTATIONS
from scripts.check_instrumental_misuse import INDEX as PREVIOUS, REPORT, AUDIT, DOC

INDEX = 'data/semantic-review-index-v99.json'
REVALIDATION = 'Five definitions connect unexamined expression use, natural faculty misuse, occurrence and causal persistence through the same activity. Only statement 52 changes; the other 53 statements, the third-sentence reformulation at 10, fourth-sentence conditional at 53, twelve unit reviews and the first two sentence judgments are preserved. No new whole sentence, unit or covered source characters are claimed.'


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
    assert len(old.document['statements']) == 54 and len(new.document['statements']) == 54
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b] == [52]
    assert new.document['statements'][10] == old.document['statements'][10]
    assert new.document['statements'][53] == old.document['statements'][53]
    assert not report['whole_sentence_semantically_verified'] and report['new_verified_sentence_characters'] == 0
    assert not report['whole_unit_semantically_verified'] and report['new_covered_characters'] == 0
    assert report['reused']['first_sentence_review_preserved'] and report['reused']['second_sentence_review_preserved']
    paths = set(new.source_sha256) | set(report['source_sha256']) | set(reading['source_sha256']) | {
        FULL, BASIS, ANNOTATIONS, REPORT, AUDIT, DOC, 'scripts/register_instrumental_misuse.py'}
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
        name = 'data/instrumental-misuse-inherited-' + review['unit'].split(':')[-1] + '-review-v1.json'
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
                new_whole_unit_reviews=0, new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=247, automatic_equivalence_proof=False)


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print(json.dumps(audit_registration(), ensure_ascii=False), flush=True)
