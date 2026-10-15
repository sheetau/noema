"""Check normative replacement without conflating adoption and fulfillment."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.script import transcribe
from scripts.compose_governing_principles import ROOT, PARENT, LIBRARY, SOURCE, CORE, BASIS, RULE, build, basis
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_thinking_disposition import code_is, forbidden
from scripts.check_apparent_liberty import UNITS

REPORT = ROOT / 'reports/governing-principles-v1.json'
PEOPLE = ('person', 'other')
DOMAIN = PEOPLE + ('government', 'source', 'office', 'outsider')
SCENES = ('start', 'end', 'probe', 'outside')


@lru_cache(maxsize=4)
def document(path):
    return parse((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(maxsize=4)
def fixture(path=LIBRARY):
    doc = deepcopy(document(path))
    doc['statements'] = []
    text = format_graph(doc, 'compact') + '''
r jgactor[] a.r jgsource[] a.r jgoffice[] a.r jgpeople[] j[a].r jgscope[a] c.
r jgcondition[a d] c.r jgfirsttreatment[a a d] c.r jgsecondtreatment[a a d] c.
r jgstart[] d.r jgend[] d.r jgprobes[d] c.
d jgfirst[bindings j[a]] e[c[k rxv[k jgactor[] k jgpeople[] p jgscope p jgcondition p jgfirsttreatment]][v bindings]].
d jgsecond[bindings j[a]] e[c[k rxv[k jgactor[] k jgpeople[] p jgscope p jgcondition p jgsecondtreatment]][v bindings]].
d jgalias[bindings j[a]] e[k jgfirst[v bindings]].
'''
    source = path != LIBRARY
    if not source:
        text += 'r jgrequired[' + RULE[2:-3] + '] c.'
    relation = '' if source else ' p jgrequired'
    common = 'k jgsource[] k jgactor[] k jgoffice[] '
    adoption = ('iaradoption' if source else 'rxx')
    fulfillment = ('iarfulfillment' if source else 'rxy')
    replacement = ('iarreplacement' if source else 'rx3')
    actual = lambda name, bindings='l[a][]', point='jgend': 't[k ' + name + '[' + bindings + ']][k ' + point + '[]]'
    queries = [actual('jgfirst'), actual('jgsecond'),
        'k rxw[k jgactor[] k jgpeople[] p jgscope p jgcondition k jgend[]]',
        'k ' + adoption + '[' + common + 'r[p jgfirst] k jgend[]' + relation + ']',
        'k ' + fulfillment + '[' + common + 'r[p jgfirst] k jgend[]' + relation + ']']
    normref = 'p h7k' if source else 'p jgrequired'
    for name, sign in (('jgfirst', 'u[e[n p a b][n p a b]]'), ('jgsecond', 'e[n p a b][n p a b]')):
        queries.append('k rxz[' + common + 'r[p ' + name + '] k jgstart[] k jgend[] ' + sign + ' ' + normref + ']')
    queries += [
        'k rx2[r[p jgfirst] r[p jgsecond] p jgprobes]',
        'k ' + replacement + '[' + common + 'r[p jgfirst] r[p jgsecond] p jgprobes k jgstart[] k jgend[]' + relation + ']',
        'k rx2[r[p jgfirst] r[p jgalias] p jgprobes]',
        actual('jgfirst', 'l[a][k jgactor[]]'),
        'u[e[r[p jgfirst]][r[p jgalias]]]', actual('jgfirst', point='jgstart')]
    return parse(text + ''.join('q[' + q + '].' for q in queries))


def values(condition=3, first=0, second=3, old=1, new=2, *, variant='baseline', path=LIBRARY,
        indices=tuple(range(13)), memoize=True, calls=None):
    def treatment(which, actor, person, point):
        if calls is not None:
            calls.append(('treatment', which, actor, person, point))
        if variant == 'unknown_treatment':
            raise ValueError('Unknown treatment')
        if variant == 'cross_context':
            return actor == 'government' and person in PEOPLE and point == 'end'
        return actor == 'government' and person in PEOPLE and bool((first if which == 'first' else second) & (1 << PEOPLE.index(person)))
    def prerequisite(person, point):
        if variant == 'unknown_condition':
            raise ValueError('Unknown condition')
        if variant == 'changing_application':
            return person in PEOPLE and point == 'end'
        return person in PEOPLE and bool(condition & (1 << PEOPLE.index(person)))
    def required(source, actor, office, description, bindings, polarity, point):
        if calls is not None:
            calls.append(('norm', source, actor, office, description, bindings.items, polarity, point))
        if variant == 'unknown_norm':
            raise ValueError('Unknown norm')
        # Move the available normative fact to another identity, binding or
        # polarity.  The queried relation must not borrow that other fact.
        expected = ('outsider' if variant == 'other_source' else 'source',
            'outsider' if variant == 'other_actor' else 'government',
            'outsider' if variant == 'other_office' else 'office')
        expected_bindings = ('person',) if variant == 'wrong_bindings' else ()
        identity = (source, actor, office) == expected and bindings.items == expected_bindings and polarity == (variant != 'negative_polarity')
        if not identity or point not in ('start', 'end'):
            return False
        mask = old if code_is(description, 'jgfirst') else new if code_is(description, 'jgsecond') else 0
        return bool(mask & (1 << ('start', 'end').index(point)))
    def probes(point):
        if variant == 'unknown_probes':
            raise ValueError('Unknown comparison scope')
        return variant != 'empty_probes' and point == 'probe'
    catalogue = () if variant == 'empty_people' else PEOPLE + ('person',) if variant == 'duplicate_people' else PEOPLE[:1] if variant == 'omitted_person' else PEOPLE
    p = dict(arithmetic(), jgactor=lambda: 'government', jgsource=lambda: 'source', jgoffice=lambda: 'office',
        jgpeople=lambda: SequenceValue(catalogue, '"individual"'),
        jgscope=lambda person: variant != 'empty_people' and person in PEOPLE,
        jgcondition=prerequisite,
        jgfirsttreatment=lambda *args: treatment('first', *args), jgsecondtreatment=lambda *args: treatment('second', *args),
        jgstart=lambda: 'start', jgend=lambda: 'start' if variant == 'same_context' else 'end', jgprobes=probes,
        jgrequired=required, h7k=required)
    doc = deepcopy(fixture(path))
    doc['statements'] = [doc['statements'][i] for i in indices]
    p = {d['name']: p.get(d['name'], forbidden) for d in doc['declarations'] if d['kind'] == 'primitive'}
    return evaluate(doc, p, DOMAIN, SCENES, memoize=memoize)


def alignment():
    unit = next(u for u in json.loads((ROOT / UNITS).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0017')
    return dict(unit=unit['id'], text_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
        definitions=['rxv', 'rxw', 'rxx', 'rxy', 'rxz', 'rx2', 'rx3', 'iaradoption', 'iarfulfillment', 'iarreplacement'],
        adds_new_text_coverage=False, semantic_completion=False, political_causality_unfilled=True,
        dignity_content_unfilled=True, source_assertions_added=0)


def build_report():
    documents = {}
    for path, text in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text))
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    for condition, first, second in product(range(4), repeat=3):
        holds_first, holds_second = condition & ~first == 0, condition & ~second == 0
        assert values(condition, first, second, indices=(0, 1, 2, 7)) == [holds_first, holds_second, bool(condition), holds_first != holds_second]
    for old, new in product(range(4), repeat=2):
        assert values(old=old, new=new, indices=(3, 5, 6, 8)) == [bool(old & 2), old == 1, new == 2, old == 1 and new == 2]
    expected = [False, True, True, False, False, True, True, True, True, False, False, True, False]
    assert values(memoize=False) == values() == expected
    for path in (CORE, SOURCE):
        assert values(path=path) == expected
        assert values(path=path, old=3, indices=(3, 4, 8)) == [True, False, False]
    parent, child = document(PARENT), document(SOURCE)
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert child['statements'] == parent['statements']
    assert [d for d in child['declarations'] if d['kind'] == 'primitive'] == [d for d in parent['declarations'] if d['kind'] == 'primitive']
    paths = [PARENT, LIBRARY, SOURCE, CORE, BASIS, UNITS,
        'scripts/compose_governing_principles.py', 'scripts/check_governing_principles.py', 'tests/test_governing_principles.py',
        'scripts/check_caused_choice.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/constructed_closure_semantics.py', 'noema/diagnostic_short_circuit.py']
    return dict(status='conditional_principle_and_normative_replacement_verified_on_finite_examples', documents=documents,
        conditional_content_combinations=64, adoption_combinations=16, roundtrips=True, uncached_baseline_checked=True,
        source_alignment=alignment(), limitations=basis()['limitations'],
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Principle content, adoption, fulfillment and replacement checked; source semantics remain incomplete')


if __name__ == '__main__':
    main()
