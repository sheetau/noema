"""Adopt the periodical description without adding a whole-unit judgment."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, load_reviews, validate_hashes
from scripts.compose_periodical_profile import ROOT, FULL, BASIS, ANNOTATIONS
from scripts.check_periodical_profile import REPORT, READING

PREVIOUS = 'data/semantic-review-index-v35.json'
INDEX = 'data/semantic-review-index-v36.json'
STATUS = 'data/periodical-profile-status-v1.json'
DOC = 'docs/periodical-profile-v1.md'


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def build():
    old_index = json.loads((ROOT / PREVIOUS).read_text(encoding='utf-8'))
    load_reviews(ROOT, PREVIOUS)
    active = old_index['works']['kant-1784']
    old_cat = load_catalog(ROOT, active['meaning_basis'])
    cat = load_catalog(ROOT, BASIS)
    formal = json.loads((ROOT / REPORT).read_text(encoding='utf-8'))
    reading = json.loads((ROOT / READING).read_text(encoding='utf-8'))
    validate_hashes(ROOT, formal['source_sha256'])
    validate_hashes(ROOT, reading['source_sha256'])
    assert formal['structure']['preserved_statements'] == 41
    assert formal['structure']['appended_statement'] == 41
    assert formal['structure']['preserved_review_selections'] == 10
    paths = set(cat.source_sha256) | set(formal['source_sha256']) | set(reading['source_sha256']) | {
        FULL, BASIS, ANNOTATIONS, REPORT, READING, DOC, 'scripts/register_periodical_profile.py'}
    pins = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    outputs, migrated = {}, []
    for path in active['reviews']:
        old = json.loads((ROOT / path).read_text(encoding='utf-8'))
        indices = [row['index'] for row in old['selection']['statements']]
        assert selection_binding(old_cat, indices) == old['selection'] == selection_binding(cat, indices)
        new = deepcopy(old)
        new.update(document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
            revalidated_from=path,
            revalidation='Selected statements, definitions and meaning conventions are unchanged. The appended periodical description is outside these whole-unit judgments. Unused comparison definitions do not acquire a source interpretation through this migration.')
        new['evidence']['formal_checks'].append(REPORT)
        new['evidence']['semantic_reading'].append(DOC)
        new['source_sha256'].update(pins)
        new['source_sha256'][path] = digest((ROOT / path).read_bytes())
        name = 'data/periodical-profile-inherited-' + old['unit'].split(':')[-1] + '-review-v1.json'
        outputs[name] = encoded(new)
        migrated.append((old['unit'], name))
    outputs[STATUS] = encoded(dict(status='periodical_description_adopted_under_stated_reading',
        document=FULL, source_reading=READING, appended_statement=41,
        resolved=['著者注の刊行系列とBüschingの編集上の帰属', '呼称内の週刊周期と実際の発行履歴の区別'],
        remaining=['偶発性と思想の一致の基準', '著者注全体の意味確認', '後続本文とアインシュタイン全文'],
        inherited_review_count=10, new_whole_unit_reviews=0, new_covered_characters=0,
        comparison_definitions_adopted_as_source_meanings=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (REPORT, READING, DOC)}))
    index = deepcopy(old_index)
    index['works']['kant-1784'].update(document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
        reviews=[p for _, p in sorted(migrated)])
    index['source_sha256'].update({p: digest((ROOT / p).read_bytes()) for p in (PREVIOUS, FULL, BASIS, ANNOTATIONS)})
    index['source_sha256'].update({p: digest(body.encode('utf-8')) for p, body in outputs.items()})
    outputs[INDEX] = encoded(index)
    return outputs


def audit_registration():
    old, new = load_reviews(ROOT, PREVIOUS), load_reviews(ROOT, INDEX)
    before = {r['unit']: r for r in old['works']['kant-1784']}
    after = {r['unit']: r for r in new['works']['kant-1784']}
    assert set(after) == set(before) and len(after) == 10
    assert sum(r['source_nonblank_characters'] for r in after.values()) == 604
    assert new['works']['einstein-1905'] == old['works']['einstein-1905'] == []
    for unit, row in before.items():
        a = json.loads((ROOT / row['review']).read_text(encoding='utf-8'))
        b = json.loads((ROOT / after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k] == b[k] for k in ('selection', 'source', 'decision', 'reviewer', 'interpretation', 'requirements', 'unresolved'))
        assert b['revalidated_from'] == row['review']
    status = json.loads((ROOT / STATUS).read_text(encoding='utf-8'))
    validate_hashes(ROOT, status['source_sha256'])
    assert status['new_whole_unit_reviews'] == 0 and not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=10, new_whole_unit_reviews=0, reviewed_nonblank_characters=604,
        appended_statement=41, automatic_equivalence_proof=False)


def main():
    for name, body in build().items():
        p = ROOT / name
        if p.exists():
            assert p.read_text(encoding='utf-8') == body, name
        else:
            with p.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print(json.dumps(audit_registration(), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
