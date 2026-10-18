"""Exercise definition comparison through Noema's existing thought interface."""
from copy import deepcopy
from functools import lru_cache
import argparse
import json
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.definition_comparison import DefinitionComparator
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_falling_depiction import closure
from scripts import check_described_thoughts as previous

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = 'examples/v016/kant-periodical-profile.noema'
BASIS = 'data/periodical-profile-basis-v1.json'
EXAMPLE = 'examples/v016/defined-thought-comparison.noema'
REPORT = 'reports/defined-thoughts-v1.json'
READING = 'data/chance-reading-v1.json'
ALIAS = 'k jmessage[]'
DOC = 'docs/defined-thoughts-v1.md'


@lru_cache(None)
def document(right=ALIAS):
    doc = parse((ROOT / ACTIVE).read_text(encoding='utf-8'))
    doc['declarations'] = closure(doc, ['hzll', 'rqrz', 'rqsa'])
    doc['statements'] = []
    mapper = previous.mapper(right).replace(previous.CLAIMS,
        previous.CLAIMS + 'd jmessage[] f[' + previous.POS + '].')
    text = format_graph(doc, 'compact') + mapper + '''
r jcriterion[i[f] i[f] a d] c.r jextent[] a.r jscene[] d.
r jleft[] a.r jright[] a.r jtopic[] a.
q[k rqrz[r[''' + previous.POS + '] r[' + right + '''] k jtopic[] k jscene[]]].
q[k rqsa[k jleft[] k jright[] k jtopic[] k jscene[] p jdescribe p jcriterion]].
q[h[k hzll[p jdescribe p jcriterion]][k jextent[]]].
'''
    return parse(text)


def unknown(*args):
    raise ValueError('Thought comparison not established')


def values(doc, variant='baseline'):
    # The historical abstract source model specifies possible scenarios, not
    # actual claims made by either author. No natural language is classified.
    without_new = deepcopy(doc)
    without_new['declarations'] = [d for d in doc['declarations'] if d['name'] not in
        ('jcriterion', 'jleft', 'jright', 'jtopic', 'jscene')]
    model = previous.previous.source_model(without_new, variant)
    comparator = DefinitionComparator(doc)
    calls = []

    def criterion(left, right, topic, scene):
        if (topic, scene) != ('full', 'possible'):
            return unknown()
        if variant == 'unknown_criterion':
            return unknown()
        quotes = [dict(kind='quote', body=json.loads(value.syntax),
            **({'rank': value.rank} if value.rank else {})) for value in (left, right)]
        result = comparator.compare(*quotes)
        calls.append(result['status'])
        if result['status'] != 'same_definition_expansion':
            return unknown()
        return True

    def pick(item, topic, scene, left, right):
        if (topic, scene) != ('full', 'possible') or item not in ('author', 'other'):
            return unknown()
        return left if item == 'author' else right

    model.update(jscene=lambda: 'possible', jleft=lambda: 'author', jright=lambda: 'other',
        jtopic=lambda: 'full', jcriterion=criterion, jpick=pick,
        jclaim=unknown, jotherclaim=unknown, jwho=unknown, jother=unknown)
    return {d['name']: model[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'}, calls


def checks():
    rows = {}
    for variant in ('baseline', 'no_chance', 'no_cause', 'empty_possible'):
        doc = document()
        model, calls = values(doc, variant)
        # The old extent interface eagerly requests unused item descriptions.
        # Its established diagnostic lowering skips these guarded requests;
        # the new comparison itself performs no evaluation in either mode.
        result = previous.previous.evaluate(doc, model, True,
            previous.previous.previous.DOMAIN, previous.previous.previous.SCENES)
        assert result == [False, True, variant == 'baseline'], (variant, result)
        assert calls and set(calls) == {'same_definition_expansion'}
        rows[variant] = result
    # Check the two direct adapters with the ordinary, saved eager graph too.
    direct = deepcopy(document())
    direct['statements'] = direct['statements'][:2]
    model, _ = values(direct)
    assert previous.previous.evaluate(direct, model, False,
        previous.previous.previous.DOMAIN, previous.previous.previous.SCENES) == [False, True]
    rejected = []
    for name, doc, variant in (
        ('different_polarity', document(previous.NEG), 'baseline'),
        ('unknown_criterion', document(), 'unknown_criterion')):
        model, _ = values(doc, variant)
        try:
            previous.previous.evaluate(doc, model, True,
                previous.previous.previous.DOMAIN, previous.previous.previous.SCENES)
        except ValueError as error:
            assert 'Thought comparison not established' in str(error)
            rejected.append(name)
        else:
            raise AssertionError(name)
    return dict(cases=rows, unresolved_inputs=rejected, actual_thought_contents_never_evaluated=True,
        source_question_diagnostic_lowering=True, direct_adapter_ordinary_evaluation=True,
        syntactic_difference_not_automatically_semantic_difference=True,
        comparator_adopted_as_total_source_criterion=False)


def reading():
    inventory = 'artifacts/written-units-v1/kant-1784.json'
    units = json.loads((ROOT / inventory).read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id'] == 'kant-1784:u0020')
    return dict(status='contextual_chance_reading_still_open', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[394, 462], text=unit['text'][394:462]),
        consulted=[
            dict(url='https://korpora.org/Kant/aa08/042.html', role='著者注の全文と未受領・比較の文脈'),
            dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_9_1_1075',
                role='Zufallの当時に近い語義資料。予想外の出来事と原因の不明という説明を区別して確認。'),
            dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_9_1_1077',
                role='zufälligには日常用法と哲学的な必然・本質との対比があり、同じ定義に一括しない。')],
        decision='未読の別回答との一致を問う文脈は、意図的な調整を補わない読みに適合する。ただし非調整という否定だけでは、予想外の成立や偶発的な寄与の全てを表さない。一般語義としての置換は採用しない。',
        limitations=['辞書は語義の補助資料であり、カントがこの文で採った唯一の理論の証明ではない。',
            '後代の確率論的独立、無原因性、人格化された偶然、全ての出来事の物理的非決定性は追加しない。',
            '定義展開で確認できる内容対応は十分条件の一つであり、全同義関係の決定手続きにはしない。'],
        remaining=['文脈的な偶発性の採用定義', '定義展開で判定できない内容対応の規約', '著者注全体の意味確認'],
        whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (inventory, ACTIVE, BASIS,
            'data/footnote-audit-v2.json', 'data/periodical-profile-status-v1.json')} )


def build_report():
    result = checks()
    doc = document()
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert (ROOT / EXAMPLE).read_text(encoding='utf-8') == format_graph(doc, 'compact') + '\n'
    note = reading()
    assert json.loads((ROOT / READING).read_text(encoding='utf-8')) == note
    validate_hashes(ROOT, note['source_sha256'])
    old = parse((ROOT / ACTIVE).read_text(encoding='utf-8'))
    assert len(old['statements']) == 42
    paths = set(note['source_sha256']) | {EXAMPLE, READING, DOC, 'scripts/check_defined_thoughts.py',
        'noema/definition_comparison.py', 'tests/test_definition_comparison.py', 'tests/test_defined_thoughts.py',
        'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/constructed.py',
        'noema/grammar.py', 'noema/semantics.py', 'noema/script.py',
        'noema/diagnostic_short_circuit.py', 'scripts/check_described_thoughts.py',
        'scripts/check_thought_correspondence.py', 'scripts/check_exploratory_question.py',
        'scripts/compose_falling_depiction.py', 'reports/periodical-profile-v1.json'}
    source = note['source']
    return dict(status='partial_definition_expansion_evidence_for_thought_comparison', document=EXAMPLE,
        checks=result, roundtrips=True, active_manuscript_unchanged=ACTIVE, active_statement_count=42,
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'],
            source=source['text'], definitions=['rqsa', 'rqrz', 'hzll'],
            status='explicit_interpretive_annotation', full_semantic_equivalence=False),
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / EXAMPLE, format_graph(document(), 'compact') + '\n')
    write_exact(ROOT / READING, encoded(reading()))
    report = build_report()
    if args.verify_only:
        assert json.loads((ROOT / REPORT).read_text(encoding='utf-8')) == report
    else:
        write_exact(ROOT / REPORT, encoded(report))
    print('Definitional thought comparison checked without claiming universal equivalence', flush=True)


if __name__ == '__main__':
    main()
