"""Adopt the contextual chance construction without adding a whole-unit claim."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, load_reviews, validate_hashes
from scripts.compose_incidental_agreement import ROOT, FULL, BASIS, ANNOTATIONS
from scripts.check_incidental_agreement import REPORT, AUDIT, DOC, INDEX as PREVIOUS, substantive

INDEX = 'data/semantic-review-index-v38.json'
STATUS = 'data/incidental-agreement-status-v1.json'


def encoded(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + '\n'


def build():
    load_reviews(ROOT, PREVIOUS)
    index = json.loads((ROOT / PREVIOUS).read_text(encoding='utf-8'))
    active = index['works']['kant-1784']
    old, new = load_catalog(ROOT, active['meaning_basis']), load_catalog(ROOT, BASIS)
    report = json.loads((ROOT / REPORT).read_text(encoding='utf-8'))
    reading = json.loads((ROOT / AUDIT).read_text(encoding='utf-8'))
    for value in (report, reading):
        validate_hashes(ROOT, value['source_sha256'])
    assert report['structure']['preserved_review_meanings'] == 10
    assert report['structure']['affected_statements'] == [22]
    paths = set(new.source_sha256) | set(report['source_sha256']) | set(reading['source_sha256']) | {
        FULL, BASIS, ANNOTATIONS, REPORT, AUDIT, DOC, 'scripts/register_incidental_agreement.py'}
    pins = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    outputs, migrated = {}, []
    for path in active['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8'))
        indices = [r['index'] for r in review['selection']['statements']]
        before, after = selection_binding(old, indices), selection_binding(new, indices)
        assert before == review['selection'] and before['statements'] == after['statements']
        assert before['dependencies'] == after['dependencies'] and 22 not in indices
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in before['dependencies'])
        revised = deepcopy(review)
        revised.update(document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS, selection=after,
            revalidated_from=path,
            revalidation='Selected statements and all transitive declarations and meaning conventions are unchanged, excluding only meaning_basis and declaration_document provenance. The revised hzlc is outside these ten whole-unit judgments. Selection hashes are rebound to the current full snapshot.')
        revised['evidence']['formal_checks'].append(REPORT)
        revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins)
        revised['source_sha256'][path] = digest((ROOT / path).read_bytes())
        name = 'data/incidental-agreement-inherited-' + review['unit'].split(':')[-1] + '-review-v1.json'
        outputs[name] = encoded(revised)
        migrated.append((review['unit'], name))
    outputs[STATUS] = encoded(dict(status='contextual_incidental_agreement_adopted', document=FULL, source_reading=AUDIT,
        changed_definition='hzlc', affected_statement=22,
        resolved=['偶発性を単独の未分解述語へ渡していた接続', '同じ結果・過程・比較条件・目的の結合'],
        remaining=['内容対応規約の採用範囲の確認', '著者注全体の意味確認', '後続本文とアインシュタイン全文'],
        inherited_review_count=10, new_whole_unit_reviews=0, new_covered_characters=0,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (REPORT, AUDIT, DOC)}))
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
    assert set(before) == set(after) and len(after) == 10
    assert sum(r['source_nonblank_characters'] for r in after.values()) == 604
    assert new['works']['einstein-1905'] == old['works']['einstein-1905'] == []
    for unit, row in before.items():
        a = json.loads((ROOT / row['review']).read_text(encoding='utf-8'))
        b = json.loads((ROOT / after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k] == b[k] for k in ('source', 'decision', 'reviewer', 'interpretation', 'requirements', 'unresolved'))
        assert a['selection']['statements'] == b['selection']['statements']
        assert a['selection']['dependencies'] == b['selection']['dependencies']
        assert a['selection'] != b['selection'] and b['revalidated_from'] == row['review']
    assert not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=10, new_whole_unit_reviews=0, reviewed_nonblank_characters=604,
        changed_definition='hzlc', affected_statement=22, automatic_equivalence_proof=False)


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
