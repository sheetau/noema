"""Check endpoint partitions and independently bound self-achievement witnesses."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.check_self_achievement import source_model
from scripts.compose_capacity_changes import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/capacity-changes-v1.json'


def finite_checks():
    text = generic_composed()[0]
    extra = 'r za[] a.r zb[a] e.r zc[a] e.r zd[] d.r ze[] d.r zf[d d] c.\n'
    args = 'k za[] p zb p zc k zd[] k ze[] p zf'
    doc = parse(text + extra + ''.join('q[k ' + name + '[' + args + ']].' for name in ('ren', 'reo', 'rep', 'req')))
    rows = []
    for assessed_before, assessed_after, before, after, ordered in product((False, True), repeat=5):
        model = {**arithmetic(), 'za': lambda: 'person',
            'zb': lambda who: Content(('before', 'after'), (assessed_before, assessed_after)),
            'zc': lambda who: Content(('before', 'after'), (before, after)),
            'zd': lambda: 'before', 'ze': lambda: 'after', 'zf': lambda first, last: ordered}
        actual = values(doc, model, ('person',), ('before', 'after'))
        valid = assessed_before and assessed_after and ordered
        expected = [valid and (before, after) == pair for pair in ((False, True), (True, False), (True, True), (False, False))]
        if actual != expected:
            raise ValueError('Endpoint partition differs')
        rows.append({'assessed': [assessed_before, assessed_after], 'states': [before, after], 'ordered': ordered, 'results': actual})
    cohort = parse(text + '''r za[] j[a].r zb[a] c.r zc[a] e.r zd[a] e.r ze[] d.r zf[] d.r zg[d d] c.r zh[] j[b].
q[k res[k za[] p zb p zc p zd k ze[] k zf[] p zg]].
q[e[k rer[k za[] p zc p zd k ze[] k zf[] p zg]][k zh[]]].
''')
    profiles = []
    pairs = ((False, True), (True, False), (True, True), (False, False))
    def profile(first, second, variant='baseline'):
        states = {'one': first, 'two': second}
        population = ('one', 'one', 'two') if variant == 'duplicate' else ('one',) if variant == 'missing' else () if variant == 'empty' else ('two', 'one') if variant == 'reordered' else ('one', 'two')
        valid = variant not in ('unassessed', 'reverse')
        expected = [sum(valid and states[who] == pair for who in population) for pair in pairs]
        model = {**arithmetic(), 'za': lambda: SequenceValue(population, '"individual"'),
            'zb': lambda who: who in ('one', 'two'), 'zc': lambda who: Content(('before', 'after'), (variant != 'unassessed', True)),
            'zd': lambda who: Content(('before', 'after'), states[who]), 'ze': lambda: 'before', 'zf': lambda: 'after',
            'zg': lambda first, last: variant != 'reverse' and (first, last) == ('before', 'after'),
            'zh': lambda: SequenceValue(tuple(Fraction(n) for n in expected), '"number"')}
        actual = values(cohort, model, ('one', 'two'), ('before', 'after'))
        if actual != [valid and variant not in ('duplicate', 'missing', 'empty'), True]:
            raise ValueError('Cohort profile or conservation differs')
        return {'states': [list(first), list(second)], 'counts': expected, 'results': actual}
    for first, second in product(pairs, repeat=2):
        profiles.append(profile(first, second))
    contrasts = {name: profile(pairs[0], pairs[1], name) for name in ('reordered', 'duplicate', 'missing', 'empty', 'unassessed', 'reverse')}
    intermediate = {}
    for name, states, expected in (('temporary_loss', (True, False, True), [False, False, True, False]),
            ('temporary_gain', (False, True, False), [False, False,False, True])):
        model = {**arithmetic(), 'za': lambda: 'person',
            'zb': lambda who: Content(('before', 'middle', 'after'), (True,) * 3),
            'zc': lambda who: Content(('before', 'middle', 'after'), states),
            'zd': lambda: 'before', 'ze': lambda: 'after',
            'zf': lambda first, last: (first, last) == ('before', 'after')}
        actual = values(doc, model, ('person',), ('before', 'middle', 'after'))
        if actual != expected:
            raise ValueError('Endpoint classification was replaced by whole-interval persistence')
        intermediate[name] = actual
    return {'individual_cases': rows, 'cohort_cases': profiles, 'contrasts': contrasts, 'intermediate_changes': intermediate}


def source_checks():
    text = source_composed()[0]
    doc = candidate(text, '''r za[] a.r zb[] a.r zc[] d.r zd[] d.r ze[] d.r zf[] j[a].
r zg[a] c.r zh[a] a.r zi[] j[b].
q[k hzk[k zf[] p zg k zc[] k zd[] k ze[]]].
q[e[k hzj[k zf[] k zc[] k zd[] k ze[]]][k zi[]]].
q[k hzl[k za[] k zb[] k zc[] k zd[] k ze[]]].
q[k hzm[k zf[] p zg k zc[] k zd[] k ze[] p zh]].
''')
    domain = ('person', 'other', 'process', 'otherprocess', 'faculty', 'plan')
    scenes = ('before', 'end', 'anchor')
    rows = {}
    for variant, counts, expected in (
        ('baseline', (1, 0, 0, 1), [True, True, True, True]),
        ('no_causal_result', (1, 0, 0, 1), [True, True, False, False]),
        ('wrong_result_description', (1, 0, 0, 1), [True, True, False, False]),
        ('other_person_changed', (1, 0, 0, 1), [True, True, False, False]),
        ('other_agent', (1, 0, 0, 1), [True, True, False, False]),
        ('no_self_work', (1, 0, 0, 1), [True, True, False, False]),
        ('no_change', (1, 0, 0, 1), [True, True, False, False]),
        ('already_capable', (0, 0, 1, 1), [True, True, False, True]),
        ('later_loss', (1, 0, 0, 1), [True, True, True, True]),
        ('intermediate_gain_lost', (0, 0, 0, 2), [True, True, False, True]),
        ('future_achievement', (1, 0, 0, 1), [True, True, False, False]),
        ('unassessed_before', (0, 0, 0, 1), [False, True, False, False]),
        ('unassessed_after', (0, 0, 0, 1), [False, True, False, False]),
        ('wrong_witness', (1, 0, 0, 1), [True, True, True, False]),
        ('two_gainers_one_witness', (2, 0, 0, 0), [True, True, True, False]),
        ('two_gainers_two_witnesses', (2, 0, 0, 0), [True, True, True, True]),
    ):
        model = source_model(doc, 'later_loss' if variant == 'intermediate_gain_lost' else variant)
        if variant == 'intermediate_gain_lost':
            model['zd'] = lambda: 'anchor'
        model.update(zg=lambda who: who in ('person', 'other'),
            zh=lambda who: 'faculty' if variant == 'wrong_witness' else 'otherprocess' if who == 'other' else 'process',
            zi=lambda: SequenceValue(tuple(Fraction(n) for n in counts), '"number"'))
        if variant.startswith('two_gainers'):
            def extend(name, predicate):
                previous = model[name]
                model[name] = lambda *args: previous(*args) or predicate(*args)
            extend('ae', lambda who, plan, point: (who, plan) == ('other', 'plan') and point in ('end', 'anchor'))
            extend('af', lambda who, plan, start, end: (who, plan, end) == ('other', 'plan', 'end') and start in ('end', 'anchor'))
            extend('ap', lambda who, plan, start, end: (who, plan, end) == ('other', 'plan', 'end') and start in ('end', 'anchor'))
            extend('ab', lambda faculty, who, point: (faculty, who, point) == ('faculty', 'other', 'end'))
            extend('ac', lambda who, faculty, act, point: (who, faculty, act, point) == ('other', 'faculty', 'otherprocess', 'end'))
            if variant == 'two_gainers_two_witnesses':
                extend('ag', lambda process, first, last: (process, first, last) == ('otherprocess', 'before', 'end'))
                extend('la', lambda who, process, first, last: (who, process, first, last) == ('other', 'otherprocess', 'before', 'end'))
                extend('dg', lambda process, point: (process, point) == ('otherprocess', 'end'))
                extend('df', lambda who, process, point: (who, process, point) == ('other', 'otherprocess', 'end'))
                extend('h4m', lambda part, who, point: (part, who, point) == ('faculty', 'other', 'end'))
                extend('h4n', lambda who, part, process, point: (who, part, process, point) == ('other', 'faculty', 'otherprocess', 'end'))
                extend('g3', lambda process, who, desc, point: (process, who, symbol(desc), point) == ('otherprocess', 'other', 'h4l', 'end'))
        actual = values(doc, model, domain, scenes)
        if actual != expected:
            raise ValueError('Native endpoint/witness contrast differs: ' + str((variant, actual)))
        rows[variant] = {'counts': list(counts), 'results': actual}
    only_counts = {**doc, 'statements': doc['statements'][:2]}
    model = source_model(only_counts, 'baseline')
    model.update(zg=lambda who: who in ('person', 'other'),
        zi=lambda: SequenceValue((Fraction(1), Fraction(0), Fraction(0), Fraction(1)), '"number"'))
    for name in ('ag', 'la', 'dg', 'df', 'h4m', 'h4n', 'g3', 'ia'):
        model[name] = guarded(only_counts)[name]
    if values(only_counts, model, domain, scenes) != [True, True]:
        raise ValueError('Endpoint profile inferred a cause')
    for selected, unknown in ((only_counts, 'ap'), (doc, 'g3')):
        unknown_model = source_model(selected, 'baseline')
        unknown_model.update(zg=lambda who: who in ('person', 'other'), zh=lambda who: 'process',
            zi=lambda: SequenceValue((Fraction(1), Fraction(0), Fraction(0), Fraction(1)), '"number"'))
        unknown_model[unknown] = guarded(selected)[unknown]
        try:
            values(selected, unknown_model, domain, scenes)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):
                raise
        else:
            raise ValueError('Unknown assessment or cause was silently counted as false')
    return {'cases': rows, 'endpoint_profile_does_not_evaluate_process_or_cause': True,
        'no_new_gainers_does_not_imply_a_completed_new_achievement': True,
        'unknown_assessment_and_causal_evidence_refused': True,
        'native_capacity_and_self_achievement_definitions_preserved': True}


def alignment():
    old = json.loads((ROOT / 'reports/capacity-progress-v1.json').read_text(encoding='utf-8'))['alignment']
    row = dict(old['segments'][0])
    row['definitions'] = ['hzj', 'hzk', 'hzl', 'hzm']
    row['review_ja'] = '純増を個人別の四分類へ分け、能力の新規成立と本人の自己活動による離脱の証拠を別に接続した。原文の人数尺度・獲得過程の唯一性・全意味との一致は未確認。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'capacity-changes'), (source_composed, 'kant-capacity-changes')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored capacity changes differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Capacity changes roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, 'data/capacity-changes-basis-v1.json', 'data/kant-capacity-changes-basis-v1.json',
        'scripts/compose_capacity_changes.py', 'scripts/check_capacity_changes.py', 'scripts/check_self_achievement.py',
        'reports/capacity-progress-v1.json', 'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_individual_changes_and_process_witnesses_not_complete_progress',
        'documents': documents, 'finite': finite_checks(), 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0, 'new_primitives': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Capacity changes report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Individual endpoint partitions and separately bound achievement witnesses checked')


if __name__ == '__main__':
    main()
