"""Check the scope of a presented consequence independently of its truth."""
from copy import deepcopy
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_recognizable_consequence import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, parent, build, closure
from scripts.check_pastoral_roles import evaluate, DOMAIN, SOURCE_SCENES
from scripts.check_book_form import source_values
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_recognizable_consequence_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v50.json'
REPORT = 'reports/recognizable-consequence-v1.json'
AUDIT = 'data/recognizable-consequence-reading-v1.json'
DOC = 'docs/recognizable-consequence-v1.md'


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r jnode[] a.r jauthor[] a.r jscene[] d.r jfact[] c.r jresult[] c.
r jpresented[a a i[h[a] e] d] c.r jrecognizable[a a i[h[a] e] i[h[a] e] d] c.
d jpremise[person a] e[b scene[k jfact[]]].
d jconclusion[person a] e[b scene[k jresult[]]].
d jconditional[person a] e[b scene[y[k jfact[]][k jresult[]]]].
q[k rqxq[k jnode[] k jauthor[] r[p jconditional] r[p jpremise] r[p jconclusion] k jscene[] p jpresented p jrecognizable]].
q[k jfact[]].q[k jresult[]].''')
    rows = []
    for presented, recognizable, premise, conclusion in product((False, True), repeat=4):
        values = dict(jnode=lambda: 'node', jauthor=lambda: 'speaker', jscene=lambda: 'context',
            jfact=lambda: premise, jresult=lambda: conclusion,
            jpresented=lambda n, a, d, s: presented and (n, a, symbol(d), s) == ('node', 'speaker', 'jconditional', 'context'),
            jrecognizable=lambda n, a, p, c, s: recognizable and (n, a, symbol(p), symbol(c), s) ==
                ('node', 'speaker', 'jpremise', 'jconclusion', 'context'))
        actual = evaluate(doc, values, ('node', 'speaker'), ('context',))
        assert actual == [presented and recognizable, premise, conclusion]
        rows.append(dict(presented=presented, recognizable=recognizable, premise=premise, conclusion=conclusion, actual=actual))
    return dict(independent_truth_combinations=rows, asserted_truth_not_required_for_presentation=True)


def presentation_values(variant='baseline'):
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(s3=lambda: 'examples', mw=lambda: 'cause', wa=lambda: 'author', wh=lambda: 'text',
        s4=lambda n, a, d, s: variant != 'no_presentation' and (n, a, symbol(d), s) == (
            'examples', 'author', 'sv' if variant == 'wrong_conditional' else 'sy', 'text'),
        s5=lambda n, a, ds, s: variant != 'closed_list' and (n, a, s) == ('examples', 'author', 'text') and
            [symbol(x) for x in ds.items] == ['ss', 'st', 'su'],
        ue=lambda a, b, s: (a, b, s) == (('examples', 'cause', 'text') if variant == 'reverse_order' else ('cause', 'examples', 'text')),
        hzwx=lambda n, a, p, c, s: variant != 'no_marker' and (n, a, symbol(p), symbol(c), s) == (
            'payment' if variant == 'other_node' else 'examples', 'other' if variant == 'other_author' else 'author',
            'sx' if variant == 'reversed_scope' else 'tp' if variant == 'other_premise' else 'sv',
            'sv' if variant == 'reversed_scope' else 'tq' if variant == 'other_conclusion' else 'sx',
            'case' if variant == 'other_context' else 'text'))
    return values


def scope_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    variants = ('baseline', 'no_presentation', 'no_marker', 'wrong_conditional', 'other_node',
        'other_author', 'other_premise', 'other_conclusion', 'reversed_scope', 'other_context', 'closed_list', 'reverse_order')
    for variant in variants:
        actual = evaluate(doc, presentation_values(variant), ('examples', 'cause', 'author', 'other', 'payment'), ('text', 'case'))
        old = variant not in ('no_presentation', 'wrong_conditional', 'closed_list', 'reverse_order')
        new = variant in ('baseline', 'closed_list', 'reverse_order')
        assert actual == [old, new], (variant, actual)
        rows[variant] = actual
    for name in ('s4', 'hzwx'):
        values = presentation_values(); values[name] = unknown
        try:
            evaluate(doc, values, ('examples', 'cause', 'author'), ('text',))
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=2, all_world_facts_unknown=True,
        no_fact_or_reader_agreement_inferred=True)


def source_truth_checks():
    c = load_catalog(ROOT, BASIS); doc = deepcopy(c.document)
    doc.update(declarations=closure(doc, ['sy', 'wh']), statements=[])
    doc = parse(format_graph(doc, 'compact') + 'r jperson[] a.q[t[k sy[k jperson[]]][k wh[]]].')
    presentation = parse((ROOT / CORE).read_text(encoding='utf-8'))
    rows = []
    for world_variant, marker in product(('baseline', 'failed_goal'), (False, True)):
        truth = evaluate(doc, source_values(world_variant), DOMAIN, SOURCE_SCENES, True)
        values = presentation_values('baseline' if marker else 'no_marker')
        presented = evaluate(presentation, values, ('examples', 'cause', 'author'), ('text',))
        assert truth == [world_variant == 'baseline'] and presented == [True, marker]
        rows.append(dict(world_variant=world_variant, recognizable_presentation=marker,
            actual_conditional=truth[0], presentation_claims=presented))
    assert evaluate(doc, source_values('failed_goal'), DOMAIN, SOURCE_SCENES) == [False]
    return dict(cases=rows, actual_conditional_definitions_executed=True, pure_memoization=True,
        ordinary_countermodel_agrees=True, presentation_does_not_prove_conditional=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert new.document['statements'][:42] == old.document['statements'] and len(new.document['statements']) == 43
    assert set(new.entries) - set(old.entries) == {'hzwx', 'rqxq', 'hzwy'}
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries)
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        r = json.loads((ROOT / path).read_text(encoding='utf-8')); ids = [s['index'] for s in r['selection']['statements']]
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a == r['selection'] and a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
    # The generic presentation combinator cannot discover this correspondence.
    # Inspect the actual source definition to bind sy's condition and consequence.
    sy = new.entries['sy']['declaration']['body']['body']
    assert sy['kind'] == 'call' and sy['symbol'] == 'rc'
    assert sy['arguments'][1:3] == [{'kind': 'function_ref', 'symbol': 'sv'}, {'kind': 'function_ref', 'symbol': 'sx'}]
    assert _references(new.entries['hzwy']['declaration']['body']) == {'rqxq', 's3', 'wa', 'sy', 'sv', 'sx', 'wh', 's4', 'hzwx'}
    for p, s in build().items():
        assert (ROOT / p).read_text(encoding='utf-8') == s
    for p in (FULL, CORE, LIBRARY):
        d = parse((ROOT / p).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=42, added_statement_indices=[42], changed_definitions=[], changed_meanings=[],
        added_definitions=2, added_primitives=1, preserved_review_meanings=11,
        source_condition_consequence_correspondence_checked=True, all_old_meanings_unchanged=True,
        roundtrips=True, primary_evidence_valid=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    phrase = 'so brauche ich mich ja nicht selbst zu bemühen.'; start = unit['text'].index(phrase)
    paths = (PARENT, PARENT_BASIS, INDEX, inv, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/delegation-reading-review-v1.json', 'docs/substituted-judgment-v1.md')
    return dict(status='scoped_ja_presentation_reading_not_complete_conditional_review', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
        interpretation='三つの代行例を仮定すれば本人の対象となる努力は不要になる、という帰結を受け手にも認めやすいものとして提示する読み。',
        evidence=EVIDENCE,
        decisions=['jaはこの後件の提示の扱いに結ぶ。前件や後件を現実の事実に昇格しない。',
            '同じ仮定例の人物位置・著者・箇所・提示文脈を保持し、前件svと後件sxを区別する。',
            '歴史辞典の条件文の並行例と、IDSの一般的な語用説明を参照する。現代の説明だけから1784年の唯一の意図を断定しない。',
            '解答としての肯定、命令の強調、程度の強調など、jaの他の用法をこの定義へ統一しない。'],
        remaining=['三名詞と仕事の文脈上の語義の最終選択', '目的・努力の範囲、selbstの焦点、反語と提示態度の相互関係',
            '条件文と第二段落全体の意味確認', '二作品全文'],
        whole_unit_semantically_verified=False, full_source_equivalence=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('scope', scope_checks), ('source_truth', source_truth_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    reading = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_recognizable_consequence.py', 'scripts/check_recognizable_consequence.py',
        'scripts/register_recognizable_consequence.py', 'scripts/fetch_recognizable_consequence_evidence.py',
        'tests/test_recognizable_consequence.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_book_form.py', 'scripts/check_pastoral_roles.py', 'scripts/check_written_carriers.py',
        'scripts/check_role_qualifications.py', 'scripts/check_substituted_judgment.py',
        'scripts/check_motive_causes.py', 'scripts/check_designation_order.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='scoped_recognizability_presentation_not_truth_proof', document=FULL, **results,
        alignment=dict(**reading['source'], definitions=['rqxq', 'hzwy', 'sy', 'sv', 'sx'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
