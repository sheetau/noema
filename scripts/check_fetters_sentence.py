"""Correct gloss references and bind a contextual review of Kant's third sentence.

Mechanical checks establish provenance and correspondence, not German equivalence.
The sentence decision below is an explicit interpretive judgment by the assistant.
"""
from copy import deepcopy
from functools import lru_cache
import json
import re

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_occasional_continuation import ROOT, FULL, ANNOTATIONS

PREVIOUS = 'data/semantic-review-index-v104.json'
OLD_BASIS = 'data/occasional-continuation-basis-v1.json'
BASIS = 'data/occasional-continuation-basis-v2.json'
AUDIT = 'data/fetters-sentence-reading-v1.json'
REPORT = 'reports/fetters-sentence-v1.json'
DOC = 'docs/fetters-sentence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/future-dissemination-reading-v1/page-483.jpg'
FIRST = 'data/nature-sentence-reading-v1.json'
SECOND = 'data/confirmed-incapacity-reading-v1.json'
PRIOR = 'reports/occasional-continuation-v1.json'
CORRECTIONS = {'r2gb': ('r2g8', 'r2ga'), 'r2gc': ('r2g9', 'r2gb'),
               'r2gd': ('r2g8', 'r2ga'), 'r2ge': ('r2gb', 'r2gd')}


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def references(text):
    # Japanese letters next to ASCII identifiers must not suppress a match.
    return set(re.findall(r'(?<![A-Za-z0-9_])r2g[a-z0-9]*(?![A-Za-z0-9_])', text))


def corrected_basis():
    old = read(OLD_BASIS)
    new = deepcopy(old)
    edits = []
    for name, (before, after) in CORRECTIONS.items():
        assert before in references(old['definitions'][name])
        new['definitions'][name] = re.sub(
            r'(?<![A-Za-z0-9_])' + before + r'(?![A-Za-z0-9_])',
            after, old['definitions'][name])
        edits.append(dict(definition=name, old_reference=before, corrected_reference=after,
                          before=old['definitions'][name], after=new['definitions'][name]))
    new['correction'] = dict(previous_basis=OLD_BASIS,
        previous_sha256=digest((ROOT / OLD_BASIS).read_bytes()), edits=edits,
        reason='未公開時の参照名変更で、日本語に隣接する四つの説明内参照が更新されなかった。Noema式は既に正しい。',
        executable_document_unchanged=True,
        historical_limitations='limitationsは候補作成時の記録として保持する。第三文の通し判断は別のfetters-sentence-reading-v1.jsonに記録する。')
    return new


@lru_cache(None)
def catalogs():
    return load_catalog(ROOT, OLD_BASIS), load_catalog(ROOT, BASIS)


def correction_checks():
    old, new = catalogs()
    assert read(BASIS) == corrected_basis()
    assert old.document == new.document
    assert len(new.document['statements']) == 54
    changed_meanings = {n for n in old.entries if old.entries[n]['meaning_ja'] != new.entries[n]['meaning_ja']}
    assert changed_meanings == set(CORRECTIONS)
    rebound = set(read(OLD_BASIS)['definitions']) | set(read(OLD_BASIS)['primitives'])
    assert len(rebound) == 10
    for name, entry in old.entries.items():
        expected = deepcopy(entry)
        if name in rebound:
            expected['meaning_basis'] = BASIS
        if name in CORRECTIONS:
            expected['meaning_ja'] = read(BASIS)['definitions'][name]
            before, after = CORRECTIONS[name]
            assert after in _references(entry['declaration'])
            assert before not in _references(entry['declaration'])
        assert new.entries[name] == expected, name
    for name, gloss in read(BASIS)['definitions'].items():
        assert references(gloss) <= set(new.entries), name
    assert references('結果r2g8へ、内容r2g9を、対象r2gbへ') == {'r2g8', 'r2g9', 'r2gb'}
    assert references('prefixr2g8 r2ga_suffix') == set()
    return dict(corrected_glosses=4, provenance_reissued_entries=10,
        declarations_and_all_54_statements_unchanged=True,
        corrected_references_match_executable_calls=True,
        japanese_adjacent_reference_regression_checked=True)


LIMITS = [
    'この第三文について、文脈上の種類一般化と継続使用時の性向を採る。あらゆる規定・表現の全使用について、全員が必ず生涯未成熟になるとの全称命題にはしない。',
    '規定は採用された条件付き要求、定型表現は固定して再利用する表現の構成として読む。社会的慣習の成立史、特定の法制度、正確なドイツ語の綴りはこの文が述べる内容に補わない。任意の機器がコードを格納するだけでは保持関係hzzzaを満たさない。',
    '機械的という語は、同じ対象を活動に適用することを本人が吟味しない使用として読む。無意識、思考能力の全般的欠如、あらゆる過去の判断不在という強い条件を加えない。',
    '持続は、使うかどうかが問題になる局面で使用を続ける比較履歴の残りの生涯全体に及ぶ。使用のない時間も結果を要求する。永遠の生命、無限時間、離脱不可能を補わない。途中で使用をやめた候補の停止前だけを保証する命題や、停止すれば成熟するという逆命題は含めない。',
    '比較事例、通常性、適用局面、完全な履歴、誤用評価、因果関係は意味規約に従う解釈入力である。都合のよい反例除外を許さないが、現実の入力の妥当性を有限テストが証明するわけではない。',
    '足枷は対象と本人の位置を保つ非字義的提示である。物理的な足枷の実在は主張しない。第四文の跳躍への比喩継続と第五文、段落全体の意味判断は未完である。',
    'アシスタントによる明示した読みの下での判断であり、独立査読や原文同義性の自動証明ではない。既存の有限検査は入力ハッシュと実行式の同一性を確認して再利用する。',
]


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    pieces = [
        (293, 303, ['hd2', 'rbe'], '採用された条件付き要求という規定の種類。'),
        (303, 316, ['r2fg', 'hzzza', 'r2gb'], '固定して再利用する表現の構成という別の種類を併記し、二種類の通常事例を別々に一般化する。'),
        (316, 322, ['r2fw', 'r2fh'], '同格の指示は主語と同じ種類記述を受ける。'),
        (322, 345, ['r2ep', 'hx2', 'r2ev'], '対象を同じ活動の手段に使い、その適用を本人が吟味しない。'),
        (345, 374, ['hm2', 'ho2'], '合理的な使用という先の記述を、後続の言い直しの出発点として提示する。'),
        (374, 399, ['ho2', 'hn2'], '同じ使用を誤用へ言い直す。二内容の同時断定や単なる論理否定にはしない。'),
        (399, 418, ['hm2', 'hn2', 'r2fy', 'r2ev'], '先行二文と同じ人物範囲の本人に自然に備わる能力と、その同じ使用活動を保つ。'),
        (418, 445, ['r2ge', 'r2gd', 'rbu', 'h2b'], '規定または定型表現と本人の二位置を、身体運動を妨げる足枷と被拘束者へ対応させた比喩を帰属する。'),
        (445, 473, ['r2ga', 'r2g5', 'r2g7', 'bf'], '使用が続く比較履歴では、以前の同じ使用からの因果的関与と同じ本人の未成熟が全将来に続く。'),
    ]
    paths = {PREVIOUS, OLD_BASIS, BASIS, FULL, ANNOTATIONS, INVENTORY, IMAGE, FIRST, SECOND, PRIOR}
    return dict(status='third_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[293, 473], text=unit['text'][293:473]),
        clauses=[dict(range=[a, b], text=unit['text'][a:b], definitions=roots, reading=meaning)
                 for a, b, roots, meaning in pieces],
        selection=selection_binding(catalogs()[1], [10, 52]),
        decision='equivalent_under_stated_reading_for_this_sentence',
        references=[
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
                 use='第三文全文と、続く足枷を捨てる仮定・少数者の離脱を照合。条件付き持続は文脈から採る解釈である。'),
            dict(url='https://www.duden.de/rechtschreibung/Formel', title='Duden Formel', accessed='2026-10-20',
                 use='固定した表現という語義と数学的公式の区別を比較。現代辞典だけから1784年の唯一の語義を決めない。'),
            dict(url='https://www.duden.de/rechtschreibung/immerwaehrend', title='Duden immerwährend', accessed='2026-10-20',
                 use='持続の用法を比較。数理的な無限時間を必須条件にはしないが、文脈解釈の証明とはしない。'),
        ], original_page=dict(path=IMAGE, visually_inspected=True, page=483),
        interpretation_limits=LIMITS, revised_statement_indices=[],
        supersedes_pending_sentence_judgment='data/occasional-continuation-reading-v1.json',
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=161, preserved_reviewed_sentence_characters=247,
        paragraph_reviewed_sentence_characters=408, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def preservation_checks():
    old, new = catalogs()
    report = read(PRIOR)
    validate_hashes(ROOT, report['source_sha256'])
    assert parse((ROOT / report['document']).read_text(encoding='utf-8')) == new.document
    assert all(report['source_sha256'][p] == h for p, h in old.source_sha256.items())
    rows = read(PREVIOUS)['works']['kant-1784']['reviews']
    assert len(rows) == 12
    for path in rows + [FIRST, SECOND]:
        row = read(path)
        validate_hashes(ROOT, row['source_sha256'])
        ids = [s['index'] for s in row['selection']['statements']]
        assert row['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    for style in ('compact', 'full'):
        text = format_graph(new.document, style)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=247, roundtrips=True,
        prior_finite_checks_reused_without_new_execution=True,
        prior_report=PRIOR, all_executable_declarations_unchanged=True,
        historical_meaning_differences_limited_to_four_corrected_references=True)


def reading_checks():
    record = reading()
    assert read(AUDIT) == record
    validate_hashes(ROOT, record['source_sha256'])
    parts = record['clauses']
    assert parts[0]['range'][0] == 293 and parts[-1]['range'][1] == 473
    assert all(a['range'][1] == b['range'][0] for a, b in zip(parts, parts[1:]))
    assert ''.join(c['text'] for c in parts) == record['source']['text']
    assert all(set(c['definitions']) <= set(record['selection']['dependencies']) for c in parts)
    assert sum(not c.isspace() for c in record['source']['text']) == 161
    assert record['paragraph_reviewed_sentence_characters'] == 108 + 139 + 161
    assert record['selection'] != read('data/occasional-continuation-reading-v1.json')['selection']
    return dict(source_partition_parts=9, reviewed_third_sentence_characters=161,
        paragraph_reviewed_sentence_characters=408, corrected_basis_bound=True,
        source_equivalence_is_reviewer_judgment_not_test_result=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / BASIS, encoded(corrected_basis()))
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('correction', correction_checks), ('preservation', preservation_checks), ('reading', reading_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    record = reading()
    paths = set(catalogs()[1].source_sha256) | set(read(PRIOR)['source_sha256']) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/check_fetters_sentence.py', 'scripts/register_fetters_sentence.py',
        'tests/test_fetters_sentence.py', 'data/occasional-continuation-reading-v1.json'}
    paths.update(read(PREVIOUS)['works']['kant-1784']['reviews'])
    return dict(status='whole_third_sentence_reviewed_under_explicit_reading', document=FULL, **results,
        alignment=dict(**record['source'], definitions=['r2ge', 'r2gc', 'r2gd', 'r2ga', 'ho2'],
                       status='explicit_interpretive_annotation'),
        review_decision=record['decision'], reviewer='assistant_review',
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=161, preserved_reviewed_sentence_characters=247,
        paragraph_reviewed_sentence_characters=408, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
