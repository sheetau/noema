"""Register the explicit whole-note judgment; tests alone never award it."""
from copy import deepcopy
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, load_reviews, validate_hashes, REQUIREMENTS
from scripts.compose_footnote_reading import ROOT, FULL, BASIS, ANNOTATIONS, SELECTION
from scripts.check_footnote_reading import REPORT, AUDIT, DOC, INDEX as PREVIOUS, substantive

INDEX = 'data/semantic-review-index-v39.json'
REVIEW = 'data/footnote-whole-review-v1.json'
STATUS = 'data/footnote-reading-status-v1.json'
REASONS = [
    '固定転記u0020の全462文字とハッシュ、原刊494頁の標識と著者注全体、AA VIII 42頁の本文を照合した。九範囲は隙間なく全原文を覆う。原文の数式はない。',
    '読書・二刊行物の系列と号・案内と回答・未受領・反事実的な差し控え・試みの提示・可能な一致範囲の問いを別々に構成し、同じ文脈へ結ぶ。週刊は暦上の周期、偶発性は非目的性と比較条件上の非必然性、思想の一致は双方向の内容保持と範囲の網羅で説明する。',
    '著者wa、現在の論説hzik、先の回答hzjnとその著者hzjo、表題の問いhziaを共有する。二つの回答・案内・掲載号・対象号・本文の回答箇所を混同しない。現在の回答への指示はhzltとhzvbで同じ問いへ結び、日付の同月・今日・基準時を保持する。',
    '読書と未受領の主張、呼称内の描写、現実と区別した反事実、magの容認、nurの位置付けの種類への限定、試みの対象となる引用された問いを区別する。問いの提示から実際の思想の一致、成功、唯一の答えを導かない。',
    '原文にない刊行実績の完全な周期性、版元・全記事の単独著作、敬称使用者の内心の敬意、差し控えの具体的段階、数値確率や最大値を追加しない。片側の非対応内容や作用域を消さず、未知の比較を偽へ補完しない。前付の文脈二文は著者注の語句として再加算しない。',
    '共通の比較粒度、内容帰属、両方向の内容保持、文脈的な可能性と比較条件、目的の対象、因果的寄与、名称使用の規約を採用した読みとして明示した。構文同一性や有限例の真偽一致を全同義関係の定義にしない。実際の答えの取得は表現の条件にしない。',
    '原刊画像の再読と九範囲の読解を、有限モデルの検査から分ける。現行の12文の同時解釈、問いへの内容比較の接続、歴史的検査の固定入力を確認した。アシスタントの意味判断であり、独立査読・自動証明・著者の内心や読書履歴の事実認定ではない。',
    '標識から末尾の問いまで一続きに再読し、二つの回答をめぐる時点・照応・反事実・試みと問いの関係を照合した。記録した文脈的な読みの下で、この著者注内に未処理の意味要素はないと判断する。後続本文や二作品全体には判断を拡張しない。',
]


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def build():
    load_reviews(ROOT, PREVIOUS)
    index = json.loads((ROOT / PREVIOUS).read_text(encoding='utf-8'))
    active = index['works']['kant-1784']
    old, new = load_catalog(ROOT, active['meaning_basis']), load_catalog(ROOT, BASIS)
    formal = json.loads((ROOT / REPORT).read_text(encoding='utf-8'))
    reading = json.loads((ROOT / AUDIT).read_text(encoding='utf-8'))
    for obj in (formal, reading):
        validate_hashes(ROOT, obj['source_sha256'])
    assert formal['structure']['changed_declarations'] == []
    assert formal['structure']['preserved_review_meanings'] == 10
    assert reading['decision'] == 'equivalent_under_stated_reading' and reading['unresolved'] == []
    paths = set(new.source_sha256) | set(formal['source_sha256']) | set(reading['source_sha256']) | {
        FULL, BASIS, ANNOTATIONS, REPORT, AUDIT, DOC, 'scripts/register_footnote_reading.py'}
    pins = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    outputs, migrated = {}, []
    for path in active['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8'))
        indices = [r['index'] for r in review['selection']['statements']]
        before, after = selection_binding(old, indices), selection_binding(new, indices)
        assert before == review['selection'] and before['statements'] == after['statements']
        assert before['dependencies'] == after['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in before['dependencies'])
        revised = deepcopy(review)
        revised.update(document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS, selection=after,
            revalidated_from=path,
            revalidation='All selected statements, transitive declarations and meaning conventions are unchanged, excluding only meaning_basis and declaration_document provenance. The four refined content conventions are outside these ten judgments. Selection hashes are rebound to the current snapshot.')
        revised['evidence']['formal_checks'].append(REPORT)
        revised['evidence']['semantic_reading'].append(DOC)
        revised['source_sha256'].update(pins)
        revised['source_sha256'][path] = digest((ROOT / path).read_bytes())
        name = 'data/footnote-reading-inherited-' + review['unit'].split(':')[-1] + '-review-v1.json'
        outputs[name] = encoded(revised)
        migrated.append((review['unit'], name))
    source = reading['source']
    assert source['unit'] == 'kant-1784:u0020' and source['range'] == [0, 462]
    review = dict(schema_version='noema-semantic-review-1', work='kant-1784', unit=source['unit'],
        document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
        source=dict(inventory=active['source_inventory'], unit_sha256=source['unit_sha256'], text=source['text'],
            range=source['range'], math=[]), selection=selection_binding(new, SELECTION),
        decision='equivalent_under_stated_reading', reviewer='assistant_review',
        interpretation=reading['interpretation'], limits=reading['limits'], unresolved=[],
        requirements=[dict(id=k, decision='satisfied', reason=v) for k, v in zip(REQUIREMENTS, REASONS, strict=True)],
        evidence=dict(source_reading=[AUDIT], formal_checks=[REPORT], semantic_reading=[DOC]), source_sha256=pins)
    outputs[REVIEW] = encoded(review)
    outputs[STATUS] = encoded(dict(status='author_note_reviewed_under_stated_reading', document=FULL, meaning_basis=BASIS,
        review=REVIEW, reading_record=AUDIT, binding=review['selection'],
        resolved=['内容比較の粒度と対応規約', '著者注の全九範囲の意味と提示の再読'],
        remaining=['残るカント本文の意味確認', 'アインシュタイン全文', '文語体系全体の完成と任意の内容に対する表現能力の検証'],
        inherited_review_count=10, new_whole_unit_reviews=1, new_reviewed_nonblank_characters=397,
        new_partial_covered_nonblank_characters=0,
        source_sha256={REVIEW: digest(outputs[REVIEW].encode('utf-8')), AUDIT: digest((ROOT / AUDIT).read_bytes())}))
    index['works']['kant-1784'].update(document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
        reviews=[p for _, p in sorted(migrated + [(source['unit'], REVIEW)])])
    index['source_sha256'].update({p: digest((ROOT / p).read_bytes()) for p in (PREVIOUS, FULL, BASIS, ANNOTATIONS)})
    index['source_sha256'].update({p: digest(body.encode('utf-8')) for p, body in outputs.items()})
    outputs[INDEX] = encoded(index)
    return outputs


def audit_registration():
    old, new = load_reviews(ROOT, PREVIOUS), load_reviews(ROOT, INDEX)
    before = {r['unit']: r for r in old['works']['kant-1784']}
    after = {r['unit']: r for r in new['works']['kant-1784']}
    assert set(after) - set(before) == {'kant-1784:u0020'} and len(after) == 11
    assert after['kant-1784:u0020']['source_nonblank_characters'] == 397
    assert sum(r['source_nonblank_characters'] for r in after.values()) == 1001
    assert old['works']['einstein-1905'] == new['works']['einstein-1905'] == []
    for unit, row in before.items():
        a = json.loads((ROOT / row['review']).read_text(encoding='utf-8'))
        b = json.loads((ROOT / after[unit]['review']).read_text(encoding='utf-8'))
        assert all(a[k] == b[k] for k in ('source', 'decision', 'reviewer', 'interpretation', 'requirements', 'unresolved'))
        assert a['selection']['statements'] == b['selection']['statements']
        assert a['selection']['dependencies'] == b['selection']['dependencies']
        assert b['revalidated_from'] == row['review']
    status = json.loads((ROOT / STATUS).read_text(encoding='utf-8'))
    validate_hashes(ROOT, status['source_sha256'])
    assert status['review'] == after['kant-1784:u0020']['review']
    assert not new['semantic_equivalence_automatically_proved']
    return dict(previous_reviews_preserved=10, new_unit='kant-1784:u0020', total_units=11,
        reviewed_nonblank_characters=1001, new_reviewed_nonblank_characters=397, automatic_equivalence_proof=False)


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
