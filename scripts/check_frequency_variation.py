"""Separate observed majority, normal-case universality, and stable frequency."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_frequency_variation import ROOT, SOURCE, SOURCE_BASIS, LIBRARY, BASIS, LIMITS, catalog, document, build
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_example_deterrence import arithmetic, DOMAIN, SCENES
from scripts.check_caused_deterrence import source_model

INDEX = 'data/semantic-review-index-v82.json'
REPORT = 'reports/frequency-under-variation-v1.json'
AUDIT = 'data/frequency-under-variation-reading-v1.json'
CORE = 'examples/v016/deterrence-frequency-comparison.noema'
DOC = 'docs/frequency-under-variation-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
ITEMS = ('one', 'two', 'three')
WORLDS = ('anchor', 'regular', 'perturbation', 'elsewhere')


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zanchor[] d.r zscenes[d d] c.r zpreferred[d d d] c.r zpopulation[d] j[a].
r zeligible[a d] c.r zresponse[a d] c.r zcriterion[b d] c.r zcomplete[j[a] d] c.
q[k r7[k zpopulation[k zanchor[]] i[item a][k zeligible[v item k zanchor[]]]
 i[item a][k zresponse[v item k zanchor[]]] i[ratio b][k zcriterion[v ratio k zanchor[]]]]].
q[k rqt4[i[scene d][k zscenes[k zanchor[] v scene]]
 i[first d second d][k zpreferred[k zanchor[] v first v second]]
 i[scene d][f item a[y[k zeligible[v item v scene]][k zresponse[v item v scene]]]]]].
q[k r2bd[k zanchor[] p zscenes p zpreferred p zpopulation p zeligible p zresponse p zcriterion p zcomplete]].
''')


def generic_model(observed=2, varied=2, variant='baseline'):
    def population(s):
        values = () if variant == 'empty_population' and s == 'regular' else ITEMS
        if variant == 'omit_exception' and s == 'regular': values = ITEMS[:2]
        if variant == 'duplicate' and s == 'regular': values = ('one', 'one', 'two', 'three')
        if variant == 'reordered': values = values[::-1]
        return SequenceValue(values, '"individual"')
    def response(item, s):
        count = observed if s == 'anchor' else 1 if variant in ('bad_perturbation', 'dominated_exception') and s == 'perturbation' else varied
        return item in ITEMS[:count]
    def preferred(anchor, a, b):
        return anchor == 'anchor' and ((variant == 'dominated_exception' and (a, b) == ('regular', 'perturbation'))
            or variant == 'cycle' and (a, b) in (('regular', 'perturbation'), ('perturbation', 'regular'))
            or variant == 'reflexive' and a == b == 'regular')
    return arithmetic() | dict(zanchor=lambda: 'elsewhere' if variant == 'wrong_anchor' else 'anchor',
        zscenes=lambda a, s: variant != 'empty_scenes' and a == 'anchor' and s in ('regular', 'perturbation'),
        zpreferred=preferred, zpopulation=population,
        zeligible=lambda item, s: item in ITEMS and not (variant == 'ineligible' and s == 'regular' and item == 'three'),
        zresponse=response, zcriterion=lambda ratio, anchor: anchor == 'anchor' and ratio >= (
            Fraction(3, 4) if variant == 'strict_criterion' else Fraction(3, 5)),
        zcomplete=lambda population, scene: set(population.items) == set(ITEMS))


@lru_cache(None)
def generic_checks():
    rows = []
    for observed, varied in product(range(4), repeat=2):
        actual = evaluate(generic(), generic_model(observed, varied), ITEMS, WORLDS, True)
        assert actual == [observed >= 2, varied == 3, varied >= 2], (observed, varied, actual)
        rows.append(dict(observed_successes=observed, varied_successes=varied, values=actual))
    contrasts = {}
    for variant in ('baseline', 'reordered', 'empty_population', 'omit_exception', 'duplicate', 'empty_scenes',
            'cycle', 'reflexive', 'ineligible', 'bad_perturbation', 'dominated_exception', 'strict_criterion', 'wrong_anchor'):
        actual = evaluate(generic(), generic_model(variant=variant), ITEMS, WORLDS, True)
        expected = variant in ('baseline', 'reordered', 'dominated_exception')
        assert actual[2] == expected, (variant, actual)
        contrasts[variant] = actual
    for name in ('zscenes', 'zpreferred', 'zpopulation', 'zeligible', 'zresponse', 'zcriterion', 'zcomplete'):
        v = generic_model(); v[name] = unknown
        try: evaluate(generic(), v, ITEMS, WORLDS, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=7,
        columns=['observed_frequency', 'all_instances_in_normal_situations', 'frequency_under_variation'],
        independent_count_oracle=True, criterion_anchored=True, exceptions_not_erased=True)


@lru_cache(None)
def source_document():
    return parse(format_graph(document(('hzud', 'gw', 'hzuc', 'r7', 'rqt4')), 'compact')+'''
r zanchor[] d.r zscenes[d d] c.r zpreferred[d d d] c.
q[t[k hzud[]][k zanchor[]]].
q[k r2bd[k zanchor[] p zscenes p zpreferred p gk p gw
 i[item a scene d][t[k hzuc[v item]][v scene]] p gl p hr]].
''')


def source_values(observed=True, varied=True, variant='baseline'):
    d = source_document(); base = source_model(d)
    def adapt(name, callback):
        def result(*args):
            context = next((s for s in args if isinstance(s, str) and s in ('regular', 'perturbation')), None)
            mapped = tuple('actual' if s in ('regular', 'perturbation') else s for s in args)
            value = callback(*mapped)
            if name == 'md' and value:
                enough = varied if context else observed
                if variant == 'bad_perturbation' and context == 'perturbation': enough = False
                if not enough and args[0] == 'other': return False
            if name == 'hzie' and variant == 'no_varied_cause' and context: return False
            if name == 'gg' and variant == 'unrecognized_varied_example' and context: return False
            if name == 'hr' and variant == 'incomplete_varied_population' and context: return False
            return value
        return result
    v = {n: adapt(n, f) for n, f in base.items()}
    v.update(zanchor=lambda: 'actual', zscenes=lambda a, s: a == 'actual' and s in ('regular', 'perturbation'),
        zpreferred=lambda a, s, t: False)
    # The candidate uses the fixed anchor criterion, not an easier criterion in varied worlds.
    if variant == 'strict_anchor_criterion': v['gl'] = lambda ratio, context: ratio >= Fraction(3, 4)
    return v


@lru_cache(None)
def source_checks():
    d = source_document(); scenes = SCENES+('regular', 'perturbation'); rows = []
    for observed, varied in product((False, True), repeat=2):
        actual = evaluate(d, source_values(observed, varied), DOMAIN, scenes, True)
        assert actual == [observed, varied], (observed, varied, actual)
        rows.append(dict(observed=observed, varied=varied, values=actual))
    contrasts = {}
    for name in ('baseline', 'bad_perturbation', 'no_varied_cause', 'unrecognized_varied_example',
            'incomplete_varied_population', 'strict_anchor_criterion'):
        actual = evaluate(d, source_values(variant=name), DOMAIN, scenes, True)
        assert actual == [name != 'strict_anchor_criterion', name == 'baseline'], (name, actual)
        contrasts[name] = actual
    for name in ('hzie', 'gg', 'zscenes', 'zpreferred'):
        v = source_values(); v[name] = unknown
        try: evaluate(d, v, DOMAIN, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(independent_conditions=rows, contrasts=contrasts, unknown_inputs_refused=4,
        current_native_failure_fear_avoidance_and_cause_executed=True,
        observed_frequency_does_not_entail_frequency_under_variation=True,
        source_replacement_adopted=False, pure_memoization=True)


def reading():
    unit = next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    text = 'gemeiniglich'; start = unit['text'].index(text)
    return dict(status='frequency_and_normality_separated_with_compositional_candidate', reviewer='assistant_review',
        document=SOURCE, meaning_basis=SOURCE_BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start,start+len(text)], text=text),
        selection=selection_binding(catalog(), [37]),
        references=[dict(title='Ariel Cohen, Genericity (2002), section 4', url='https://tzin.bgu.ac.il/~arikc/gen.pdf',
            use='頻度表現と無修飾の一般文、偶然の現況と反事実に及ぶ一般化を区別する。今回の二段階構成を同論文の提案と帰属しない。')],
        established=['現況の過半数、通常候補内の全称、比較状況を変えて保たれる過半数は異なる。',
            '既存hzudを実行したまま、現況の成立と比較状況での頻度の成立を四組合せで分離できる。'],
        unresolved=LIMITS, whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, semantic_equivalence_automatically_proved=False)


@lru_cache(None)
def structure():
    for p, body in build().items(): assert (ROOT/p).read_text(encoding='utf-8') == body, p
    assert (ROOT/CORE).read_text(encoding='utf-8') == format_graph(source_document(),'compact')+'\n'
    lib = load_catalog(ROOT, BASIS)
    assert lib.entries['r2bd']['kind']=='definition'
    for name, entry in lib.entries.items():
        if name != 'r2bd':
            assert entry['declaration']==catalog().entries[name]['declaration']
            assert entry['meaning_ja']==catalog().entries[name]['meaning_ja']
    for d in (lib.document, source_document()):
        for notation in ('compact','full'):
            text=format_graph(d,notation); assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document']==SOURCE
    for p in index['works']['kant-1784']['reviews']:
        row=json.loads((ROOT/p).read_text(encoding='utf-8'))
        assert row['selection']==selection_binding(catalog(),[s['index'] for s in row['selection']['statements']])
    assert reading()==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))
    return dict(new_general_definitions=1, new_semantic_primitives=0, manuscript_statements_unchanged=52,
        preserved_review_selections=11, current_selection_bound=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT/CORE,format_graph(source_document(),'compact')+'\n')
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn(); print(name+' checked',flush=True)
    r=reading(); paths=set(catalog().source_sha256)|set(build())|{INDEX,AUDIT,
        CORE,DOC,INVENTORY,'scripts/compose_frequency_variation.py','scripts/check_frequency_variation.py',
        'scripts/register_frequency_variation.py','tests/test_frequency_variation.py',
        'scripts/check_caused_deterrence.py','scripts/check_example_deterrence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py'}
    return dict(status='frequency_under_variation_checked_not_source_replacement',document=SOURCE,**results,
        alignment=dict(**r['source'],definitions=['hzud','hzuc','r7','rqt4','r2bd'],status='partial_quantifier_scope_diagnostic'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare(); write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__': main()
