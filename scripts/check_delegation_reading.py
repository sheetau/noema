"""Review the corrected delegation sentence under an explicit source reading."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_falling_depiction import ROOT, closure
from scripts.check_appointed_roles import source_values, attribution_checks, DOMAIN as PEOPLE, source_doc
from scripts.check_pastoral_roles import evaluate, SOURCE_SCENES
from scripts.check_motive_causes import unknown, symbol
from scripts.check_delegation_sentence import reading as previous_reading
from scripts.fetch_appointed_roles_evidence import PATH as EVIDENCE, validate

FULL = 'examples/v016/kant-appointed-roles.noema'
BASIS = 'data/appointed-roles-basis-v1.json'
INDEX = 'data/semantic-review-index-v57.json'
CORE = 'examples/v016/delegation-reading-core.noema'
AUDIT = 'data/delegation-reading-v1.json'
REPORT = 'reports/delegation-reading-v1.json'
DOC = 'docs/delegation-reading-v1.md'


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def core():
    d = deepcopy(catalog().document)
    d['statements'] = [d['statements'][i] for i in (4, 42)]
    d['declarations'] = closure(d, _references(d['statements']))
    return format_graph(d, 'compact') + '\n'


@lru_cache(None)
def questions():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['ss', 'st', 'su', 'sv', 'sx', 're', 's2', 'sy', 'wh']), statements=[])
    text = format_graph(d, 'compact') + 'r jp[] a.r js[] d.'
    for n in ('ss', 'st', 'su', 'sv', 'sx'):
        text += 'q[t[k ' + n + '[k jp[]]][k js[]]].'
    text += 'q[k re[k jp[] p sv i[scene d][k s2[k jp[] k wh[] v scene]]]].q[t[k sy[k jp[]]][k wh[]]].'
    return parse(text)


def supply_checks():
    base = {('book', 'person', 'bm', 'case'), ('guide', 'person', 'sm', 'case'), ('doctor', 'person', 'sn', 'case')}
    variants = ('baseline', 'wrong_book_task', 'wrong_guide_recipient', 'wrong_doctor_scene', 'swap_tasks', 'self_provider')
    expected = {
        'baseline': [True, True, True], 'wrong_book_task': [False, True, True],
        'wrong_guide_recipient': [True, False, True], 'wrong_doctor_scene': [True, True, False],
        'swap_tasks': [False, False, True], 'self_provider': [False, True, True],
    }
    rows = {}
    for variant in variants:
        facts = set(base)
        if variant == 'wrong_book_task':
            facts.remove(('book', 'person', 'bm', 'case')); facts.add(('book', 'person', 'sm', 'case'))
        if variant == 'wrong_guide_recipient':
            facts.remove(('guide', 'person', 'sm', 'case')); facts.add(('guide', 'other', 'sm', 'case'))
        if variant == 'wrong_doctor_scene':
            facts.remove(('doctor', 'person', 'sn', 'case')); facts.add(('doctor', 'person', 'sn', 'text'))
        if variant == 'swap_tasks':
            facts = {('book', 'person', 'sm', 'case'), ('guide', 'person', 'bm', 'case'), ('doctor', 'person', 'sn', 'case')}
        if variant == 'self_provider':
            facts.remove(('book', 'person', 'bm', 'case')); facts.add(('person', 'person', 'bm', 'case'))
        v = source_values(); v['sb'] = lambda w, p, task, s: (w, p, symbol(task), s) in facts
        if variant == 'self_provider':
            # Give the person every book/access predicate of the old provider,
            # so exclusion is not merely caused by a missing provider kind.
            fold = lambda x: 'book' if x == 'person' else x
            for n in ('sc',):
                fn = v[n]; v[n] = lambda p, s, fn=fn: fn(fold(p), s)
            fn = v['hzwr']; v['hzwr'] = lambda r, w, s, fn=fn: fn(r, fold(w), s)
            fn = v['sa']; v['sa'] = lambda p, w, s, fn=fn: fn(p, fold(w), s)
        actual = evaluate(questions(), v, PEOPLE, SOURCE_SCENES, True)
        assert actual[:3] == expected[variant], (variant, actual)
        assert actual[3:] == [all(expected[variant]), True, all(expected[variant]), True]
        rows[variant] = actual
    # Ordinary evaluation of the same composite premise, including all roles.
    d = deepcopy(questions()); d['statements'] = d['statements'][:4]
    d['declarations'] = closure(d, _references(d['statements']))
    assert evaluate(d, source_values(), PEOPLE, SOURCE_SCENES) == [True] * 4
    for name in ('sa', 'sb'):
        v = source_values(); v[name] = unknown
        try:
            evaluate(d, v, PEOPLE, SOURCE_SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, ordinary_full_premise_agrees=True, unknown_inputs_refused=2,
        substituted_tasks_not_performed_by_recipient=True)


def appointment_checks():
    rows = {}
    for variant in ('baseline', 'no_appointment', 'no_responsibility', 'other_responsible_community'):
        v = source_values(variant)
        old = evaluate(source_doc(True, True), v, PEOPLE, SOURCE_SCENES)
        current = evaluate(source_doc(compact=True), v, PEOPLE, SOURCE_SCENES)
        assert old == [True, True]
        assert current == [variant == 'baseline'] * 2
        rows[variant] = dict(previous=old, current=current)
    return dict(contrasts=rows, prior_nonappointed_countermodel_excluded=True,
        ordinary_evaluation=True, actual_religious_activity_unknown=True)


def reading():
    old = previous_reading(); r = deepcopy(old)
    for clause in r['clauses']:
        clause['status'] = 'reviewed_under_stated_reading'
        if clause['id'] == 'pastoral_provider':
            clause.update(definitions=['sp', 'rqxx', 'hzxi'],
                interpretation_ja='宗教上の援助を主要な務めとし、同じ共同体の公の宗教的奉仕を担う責務を持つ同じ役割に任じられた者。Geistlicherの広い歴史的用法を採り、特定教派の叙任儀礼を一律に要求しない。')
    r.update(status='corrected_delegation_sentence_reviewed_under_stated_reading',
        decision='equivalent_under_stated_reading_for_this_sentence',
        document=FULL, meaning_basis=BASIS, selection=selection_binding(catalog(), [4, 42]),
        supersedes_for_current_snapshot='data/delegation-sentence-reading-v1.json',
        findings=['原刊482頁の条件文全体を十一範囲に分け、同じ本人・供給元・仕事・状況・条件と否定の範囲を照合した。',
            '任用と公的責務を同じ役割・共同体へ結ぶ修正により、前版の非任用の援助役の反例を区別できる。',
            '書物・良心・医師・Diätは固定済みの機能上の読みを採る。目的・努力・仮定と結果の範囲も前の文脈指定を保持する。',
            'この一文は採用した読みの下で対応すると判断する。判断はテストの出力から自動生成したものではない。'],
        interpretation_limits=[
            'この一文と固定したv57の定義に対するアシスタントの読解判断であり、独立査読や自動的な意味一致の証明ではない。',
            '語の全用法ではなく、この箇所の採用読解を対象とする。書物の刊行慣習や全時代の医療・聖職制度を一括して定義したとはしない。',
            '任用・責務・公的な宗教行為などの基本関係は公開した意味規約で解釈する。儀礼や制度の全内部構造を定義展開したとはしない。',
            '努力は判断の取組みに関する目的相対的な必要性であり、全活動の不実行ではない。結果範囲を恣意的に除けば意味が変わる。',
            '仮定例の提示とjaを保持し、著者による推奨や後件の現実の偽を追加しない。前後を含む批判的な議論の全体確認は段落レビューに残す。',
            'この確認は別版や別の文脈設定へ自動的に継承しない。'],
        remaining=['便宜・支払い・後見人の働きかけを含む第二段落全体の意味確認', '二作品全文'],
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=157, new_whole_unit_reviews=0,
        semantic_equivalence_automatically_proved=False)
    paths = set(old['source_sha256']) | {FULL, BASIS, INDEX, EVIDENCE,
        'data/delegation-sentence-reading-v1.json', 'reports/delegation-sentence-v1.json',
        'data/appointed-roles-reading-v1.json', 'reports/appointed-roles-v1.json', 'docs/appointed-roles-v1.md'}
    r['source_sha256'] = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    return r


def integrity_checks():
    r = reading(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == r
    validate_hashes(ROOT, r['source_sha256'])
    assert r['source']['range'] == [326, 518] and r['source']['nonblank_characters'] == 157
    assert len(r['clauses']) == 11 and ''.join(c['text'] for c in r['clauses']) == r['source']['text']
    for clause in r['clauses']:
        a, b = clause['range']
        assert clause['text'] == r['source']['text'][a-326:b-326]
        assert clause['status'] == 'reviewed_under_stated_reading'
        assert all(n in catalog().entries for n in clause['definitions'])
    old = previous_reading()
    assert not old['whole_sentence_semantically_verified']
    assert old['context'] == r['context'] and old['source'] == r['source']
    assert old['selection']['statements'] == r['selection']['statements']
    assert old['selection']['dependency_sha256'] != r['selection']['dependency_sha256']
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document'] == FULL and index['works']['kant-1784']['meaning_basis'] == BASIS
    previous_report = json.loads((ROOT / 'reports/appointed-roles-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, previous_report['source_sha256'])
    assert previous_report['source']['previous_nonappointed_countermodel_rejected']
    assert len(previous_report['sentence']['combinations']) == 32
    assert previous_report['structure']['preserved_review_meanings'] == 11
    assert (ROOT / CORE).read_text(encoding='utf-8') == core()
    d = parse(core())
    for style in ('compact', 'full'):
        text = format_graph(d, style)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(clause_partition=11, current_selection_bound=True, historical_negative_review_preserved=True,
        prior_full_composition_report_matches_current_inputs=True, manuscripts_unchanged=True,
        reviewed_sentence_characters=157, roundtrips=True, semantic_equivalence_automatically_proved=False)


def build_report():
    results = {}
    for name, fn in [('supply', supply_checks), ('appointment', appointment_checks),
        ('attribution', attribution_checks), ('integrity', integrity_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading(); source = r['source']
    paths = set(r['source_sha256']) | set(catalog().source_sha256) | {CORE, AUDIT, DOC,
        'scripts/check_delegation_reading.py', 'scripts/register_delegation_reading.py',
        'tests/test_delegation_reading.py', 'scripts/check_delegation_sentence.py',
        'scripts/check_appointed_roles.py', 'scripts/fetch_appointed_roles_evidence.py',
        'scripts/fetch_pastoral_role_evidence.py', 'scripts/check_service_roles.py',
        'scripts/check_clinical_roles.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_recognizable_consequence.py', 'scripts/check_motive_causes.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='whole_sentence_reviewed_under_explicit_source_reading', document=CORE, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=['ss', 'st', 'su', 'sv', 'sx', 'sy', 'hzwy'], status='explicit_interpretive_annotation'),
        review_decision=r['decision'], reviewer='assistant_review', review_scope='this sentence in fixed v57 only',
        whole_sentence_semantically_verified=True, new_verified_sentence_characters=157,
        semantic_equivalence_automatically_proved=False, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / CORE, core()); write_exact(ROOT / AUDIT, encoded(reading()))


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
