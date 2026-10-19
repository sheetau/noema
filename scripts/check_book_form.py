"""Check actual and intended carrier forms without equating plans with artifacts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_book_form import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, parent, build, closure
from scripts.check_pastoral_roles import evaluate, source_values as pastoral_values, DOMAIN, SOURCE_SCENES
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_book_form_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v49.json'
REPORT = 'reports/book-form-v1.json'
AUDIT = 'data/book-form-reading-v1.json'
DOC = 'docs/book-form-v1.md'


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r jw[] a.r js[] d.r jr[a a d] c.r jc[a a d] c.r ja[a d] c.r jf[a d] c.
q[k rqxn[k jw[] p jf k js[] p jr p jc p ja]].''')
    people = ('work', 'recordA', 'recordB', 'mediumA', 'mediumB')
    rows = []
    for bits in product((False, True), repeat=8):
        sets = [{i for i, b in enumerate(bits[k:k+2]) if b} for k in (0, 2, 4, 6)]
        records, media = ('recordA', 'recordB'), ('mediumA', 'mediumB')
        values = dict(jw=lambda: 'work', js=lambda: 'now',
            jr=lambda r, w, s: (w, s) == ('work', 'now') and r in {records[i] for i in sets[0]},
            jc=lambda r, m, s: s == 'now' and (r, m) in {(records[i], media[i]) for i in sets[1]},
            ja=lambda r, s: s == 'now' and r in {records[i] for i in sets[2]},
            jf=lambda m, s: s == 'now' and m in {media[i] for i in sets[3]})
        actual = evaluate(doc, values, people, ('now',))[0]
        assert actual == bool(set.intersection(*sets))
        rows.append(dict(bits=list(bits), shaped_realization=actual))
    contrasts = {}
    for variant in ('baseline', 'other_work', 'split_record', 'other_readable_record',
                    'other_medium', 'other_record_scene', 'other_carry_scene', 'other_readable_scene', 'other_form_scene'):
        values = dict(jw=lambda: 'work', js=lambda: 'now',
            jr=lambda r, w, s: (r, w, s) == ('recordA', 'elsewhere' if variant == 'other_work' else 'work',
                'then' if variant == 'other_record_scene' else 'now'),
            jc=lambda r, m, s: (r, m, s) == ('recordB' if variant == 'split_record' else 'recordA', 'mediumA',
                'then' if variant == 'other_carry_scene' else 'now'),
            ja=lambda r, s: (r, s) == ('recordB' if variant == 'other_readable_record' else 'recordA',
                'then' if variant == 'other_readable_scene' else 'now'),
            jf=lambda m, s: (m, s) == ('mediumB' if variant == 'other_medium' else 'mediumA',
                'then' if variant == 'other_form_scene' else 'now'))
        contrasts[variant] = evaluate(doc, values, (*people, 'elsewhere'), ('now', 'then'))
        assert contrasts[variant] == [variant == 'baseline']
    return dict(relation_combinations=rows, binding_contrasts=contrasts,
        generic_form_argument=True, ordinary_evaluation=True)


@lru_cache(None)
def source_doc(previous=False, integrated=False):
    c = parent() if previous else load_catalog(ROOT, BASIS)
    doc = deepcopy(c.document)
    names = ['sv', 're', 's2', 'sy', 'wh'] if integrated else ['sl', 'ss'] + ([] if previous else ['rqxo'])
    doc.update(declarations=closure(doc, names), statements=[])
    questions = '''q[t[k sv[k jperson[]]][k jscene[]]].
q[k re[k jperson[] p sv i[scene d][k s2[k jperson[] k wh[] v scene]]]].
q[t[k sy[k jperson[]]][k wh[]]].''' if integrated else (
        ('' if previous else 'q[k rqxo[k jwork[] k jscene[]]].') +
        'q[k sl[k jwork[] k jscene[]]].q[t[k ss[k jperson[]]][k jscene[]]].')
    return parse(format_graph(doc, 'compact') + 'r jperson[] a.r jwork[] a.r jscene[] d.' + questions)


def source_values(variant):
    mapped = 'no_record' if variant == 'plan_without_record' else variant
    values = pastoral_values(mapped)
    values.update(jperson=lambda: 'person', jwork=lambda: 'book', jscene=lambda: 'case')
    planned = variant in ('planned', 'both', 'plan_without_record', 'plan_other_work', 'plan_other_form', 'plan_other_scene')
    actual = variant not in ('planned', 'neither', 'plan_without_record', 'plan_other_work', 'plan_other_form', 'plan_other_scene')
    values['hzwv'] = lambda m, s: actual and (m, s) == (
        'paperB' if variant == 'other_medium' else 'paperA', 'text' if variant == 'other_form_scene' else 'case')
    values['hzww'] = lambda w, f, s: planned and (w, symbol(f), s) == (
        'other' if variant == 'plan_other_work' else 'book', 'hzwt' if variant == 'plan_other_form' else 'hzwv',
        'text' if variant == 'plan_other_scene' else 'case')
    if variant == 'missing_access':
        access = values['sa']; values['sa'] = lambda p, w, s: access(p, w, s) and w != 'book'
    if variant == 'wrong_task':
        supply = values['sb']; values['sb'] = lambda w, p, t, s: supply(w, p, t, s) and w != 'book'
    return values


def source_checks():
    variants = ('baseline', 'planned', 'both', 'neither', 'no_record', 'wrong_work', 'unreadable',
        'other_medium', 'other_form_scene', 'plan_other_work', 'plan_other_form', 'plan_other_scene',
        'plan_without_record', 'missing_access', 'wrong_task', 'wrong_beneficiary')
    absent_form = ('neither', 'no_record', 'wrong_work', 'unreadable', 'other_medium', 'other_form_scene',
        'plan_other_work', 'plan_other_form', 'plan_other_scene')
    absent_record = ('no_record', 'wrong_work', 'unreadable', 'plan_without_record')
    absent_supply = ('missing_access', 'wrong_task', 'wrong_beneficiary')
    rows = {}
    for variant in variants:
        values = source_values(variant)
        actual = evaluate(source_doc(), values, DOMAIN, SOURCE_SCENES)
        old = evaluate(source_doc(True), values, DOMAIN, SOURCE_SCENES)
        shape = variant not in absent_form
        work = shape and variant not in absent_record
        assert actual == [shape, work, work and variant not in absent_supply], (variant, actual)
        old_work = variant not in absent_record
        assert old == [old_work, old_work and variant not in absent_supply], (variant, old)
        rows[variant] = dict(previous=old, current=actual)
    for name in ('hzwv', 'hzww'):
        values = source_values('neither'); values[name] = unknown
        try:
            evaluate(source_doc(), values, DOMAIN, SOURCE_SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=2, task_content_not_executed=True,
        definitions_replaced_by_primitives=False, ordinary_evaluation=True)


def integration_checks():
    rows = {}
    for variant in ('baseline', 'planned', 'neither', 'plan_without_record', 'wrong_beneficiary', 'failed_goal'):
        values = source_values(variant)
        actual = evaluate(source_doc(integrated=True), values, DOMAIN, SOURCE_SCENES, True)
        premise = variant not in ('neither', 'plan_without_record', 'wrong_beneficiary')
        assert actual == [premise, premise, not premise or variant != 'failed_goal'], (variant, actual)
        rows[variant] = actual
    assert evaluate(source_doc(integrated=True), source_values('baseline'), DOMAIN, SOURCE_SCENES) == rows['baseline']
    return dict(cases=rows, definitions_replaced_by_primitives=False, pure_memoization=True,
        ordinary_baseline_agrees=True, vacuous_condition_not_counted_as_example=True)


def attribution_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    for variant in ('baseline', 'other_author', 'other_node', 'other_description', 'other_context', 'reverse_order', 'reverse_examples', 'closed_list'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(s3=lambda: 'examples', mw=lambda: 'cause', wa=lambda: 'author', wh=lambda: 'text',
            s4=lambda n, a, t, s: (n, a, symbol(t), s) == ('other' if variant == 'other_node' else 'examples',
                'other' if variant == 'other_author' else 'author', 'sv' if variant == 'other_description' else 'sy',
                'other' if variant == 'other_context' else 'text'),
            s5=lambda n, a, ds, s: variant != 'closed_list' and (n, a, s) == ('examples', 'author', 'text') and
                [symbol(x) for x in ds.items] == (['su', 'st', 'ss'] if variant == 'reverse_examples' else ['ss', 'st', 'su']),
            ue=lambda a, b, s: (a, b, s) == (('examples', 'cause', 'text') if variant == 'reverse_order' else ('cause', 'examples', 'text')))
        rows[variant] = evaluate(doc, values, ('examples', 'cause', 'author', 'other'), ('text',))
        assert rows[variant] == [variant == 'baseline']
    return dict(contrasts=rows, all_carrier_form_and_plan_facts_unknown=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 42
    assert set(new.entries) - set(old.entries) == {'rqxn', 'rqxo', 'rqxp', 'hzwv', 'hzww'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['sl']
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'sl')
    affected = [i for i, s in enumerate(new.document['statements']) if 'sl' in {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [4]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        r = json.loads((ROOT / path).read_text(encoding='utf-8')); ids = [s['index'] for s in r['selection']['statements']]
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a == r['selection'] and a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2, 3], [5]):
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    conscience = closure(old.document, ['sm', 'st'])
    assert conscience == closure(new.document, ['sm', 'st'])
    assert all(substantive(old.entries[d['name']]) == substantive(new.entries[d['name']]) for d in conscience)
    for p, s in build().items():
        assert (ROOT / p).read_text(encoding='utf-8') == s
    for p in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / p).read_text(encoding='utf-8'))
        for style in ('full', 'compact'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=42, changed_definitions=['sl'], affected_statements=affected,
        added_definitions=3, added_primitives=2, preserved_review_meanings=11,
        first_cause_sentence_meanings_unchanged=True, payment_meanings_unchanged=True,
        conscience_components_unchanged=True, roundtrips=True, primary_evidence_valid=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    phrase = 'ein Buch, das für mich Verstand hat'; start = unit['text'].index(phrase)
    paths = (PARENT, PARENT_BASIS, INDEX, inv, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'docs/substituted-judgment-v1.md', 'data/conscience-reading-v1.json')
    return dict(status='partial_actual_or_intended_leaf_collection_form', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
        reading='参照できる記された作品を内容として利用する読みへ、実際または制作上予定された、葉を一つに集める媒体の形を接続する。',
        evidence=EVIDENCE, consulted='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009131_4_4_4406',
        decisions=['記録がある媒体と、形を持つ媒体を同一にする。別媒体の形を借りない。',
            '同じ作品・構成・状況の制作予定を使う。予定の内容を実際の形の存在として実行しない。',
            '内容としての書物は未製本や予定された形も含み得る。本人の利用可能性はsaで別に要求する。',
            '辞典には分量の慣習もあるが固定のページ数・現代の規格は追加しない。'],
        remaining=['分量と刊行単位の慣習、書物全語義の定義', '宗教上の職務・医師の残る条件',
            '便宜や反語を含む条件文と第二段落全体', '二作品全文'],
        whole_unit_semantically_verified=False, full_noun_equivalence=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for n, f in [('generic', generic_checks), ('source', source_checks), ('integration', integration_checks),
                 ('attribution', attribution_checks), ('structure', structure)]:
        results[n] = f(); print(n + ' checked', flush=True)
    reading = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_book_form.py', 'scripts/check_book_form.py', 'scripts/register_book_form.py',
        'scripts/fetch_book_form_evidence.py', 'tests/test_book_form.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_written_carriers.py', 'scripts/check_role_qualifications.py',
        'scripts/check_substituted_judgment.py', 'scripts/check_motive_causes.py', 'scripts/check_designation_order.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/constructed_discourse.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='partial_book_form_composition', document=FULL, **results,
        alignment=dict(**reading['source'], definitions=['rqxn', 'rqxo', 'rqxp', 'sl', 'ss'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit()))
    write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
