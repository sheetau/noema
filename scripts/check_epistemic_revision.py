"""Reject mere sentence growth, aliases and error removal by losing good information."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_epistemic_revision import ROOT, PARENT, BUILDERS, CHANGE, SOURCE

REPORT = ROOT / 'reports/epistemic-revision-v1.json'
CLAIMS = ('p', 'q', 'notp', 'notq', 'aliasp', 'aliasnotp', 'tautology', 'pandq')
DOMAIN = (*CLAIMS, 'holder', 'other')
WORLDS = ('w11', 'w10', 'w01', 'w00')
SCENES = ('before', 'after', *WORLDS)
EXTRA = '''r jkholder[] a.r jkbefore[] d.r jkafter[] d.r jkassessment[] d.
r jkscope[a] c.r jkcorpus[a a d] c.r jksupported[a a d] c.r jktruth[a d] c.r jkcomparisons[d] c.
d jkcontents[claim a] e[b point[k jktruth[v claim v point]]].
r jkgoal[a i[e] d] c.
'''
REFS = {n: 'k jk' + n + '[]' for n in ('holder', 'before', 'after', 'assessment')}
REFS.update({n: 'p jk' + n for n in ('scope', 'corpus', 'supported', 'contents', 'comparisons')})


def setup(text, source=False):
    names = ('hzc5', 'hzc6', 'hzc7') if source else ('ri4', 'ri5', 'ri6', 'ri7')
    queries = []
    for name in names:
        expression = k(name, *(REFS[n] for n, _ in (SOURCE if source else CHANGE)))
        if source: expression = 't[' + expression + '][k jkassessment[]]'
        queries.append('q[' + expression + '].')
    return candidate(text, EXTRA + ''.join(queries))


def model_for(doc, keep=True, add=True, warrant=True, old_error=True, new_error=False, variant='baseline'):
    model = guarded(doc)
    old = {'p'} | ({'notp'} if old_error else set())
    new = ({'p'} if keep else set()) | ({'q'} if add else set()) | ({'notp'} if new_error else set())
    if variant == 'true_alias': old, new = {'p'}, {'aliasp'}
    if variant == 'false_alias': old, new = {'p', 'notp'}, {'p', 'aliasnotp'}
    if variant == 'tautology_added': old, new = {'p'}, {'p', 'tautology'}
    if variant == 'partial_cleanup': old, new = {'p', 'notp', 'notq'}, {'p', 'notq'}
    if variant == 'new_error_content': old, new = {'p', 'notp'}, {'p', 'notq'}
    if variant == 'scope_excludes_error': old, new = {'p', 'notp'}, {'p', 'q', 'notq'}
    if variant == 'support_acquired': old, new = {'p', 'q'}, {'p', 'q'}
    if variant == 'discard_all': old, new = {'p', 'notp'}, set()
    if variant == 'stronger_replacement': old, new = {'p', 'notp'}, {'pandq'}
    if variant == 'weaker_replacement': old, new = {'pandq', 'notp'}, {'p'}
    comparisons = () if variant == 'empty_comparisons' else ('w10', 'w01', 'w00') if variant == 'missing_assessment' else ('w11',) if variant == 'single_actual' else WORLDS
    scope = () if variant == 'empty_scope' else tuple(c for c in CLAIMS if c != 'notq') if variant == 'scope_excludes_error' else CLAIMS
    def corpus(holder, claim, stage):
        expected = 'other' if variant == 'other_holder' and stage == 'after' else 'holder'
        return holder == expected and claim in (old if stage == 'before' else new if stage == 'after' else set())
    def supported(holder, claim, stage):
        if holder != 'holder' or stage not in ('before', 'after'): return False
        if variant == 'support_lost' and claim == 'p' and stage == 'after': return False
        if variant == 'support_acquired' and claim == 'q': return stage == 'after'
        return claim in ('p', 'aliasp', 'tautology', 'pandq') or claim == 'q' and warrant
    def truth(claim, world):
        if variant == 'stage_truth_changed' and world in ('before', 'after'): return world == 'after'
        p = world in ('w11', 'w10', 'before', 'after')
        q = world in ('w11', 'w01', 'before', 'after')
        return {'p': p, 'q': q, 'notp': not p, 'notq': not q, 'aliasp': p, 'aliasnotp': not p, 'tautology': True, 'pandq': p and q}.get(claim, False)
    model.update(jkholder=lambda: 'holder', jkbefore=lambda: 'before', jkafter=lambda: 'before' if variant == 'same_stage' else 'after',
        jkassessment=lambda: 'w11', jkscope=lambda claim: claim in scope, jkcorpus=corpus, jksupported=supported,
        jktruth=truth, jkcomparisons=lambda world: world in comparisons)
    return model


def evaluate(doc, model): return values(doc, model, DOMAIN, SCENES)


def checks(texts, source=False):
    docs = [setup(t, source) for t in texts]; cases = []
    for keep, add, warrant, old_error, new_error in product((False, True), repeat=5):
        cleaned = keep and old_error and not new_error
        want = [keep, keep and add and warrant, cleaned, cleaned]
        if source: want = want[1:]
        rows = [evaluate(d, model_for(d, keep, add, warrant, old_error, new_error)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Counts or false additions substituted for information/revision')
        cases.append(dict(keep=keep, add=add, warrant=warrant, old_error=old_error, new_error=new_error, results=want))
    expected = {
        'true_alias': [True, False, False, False], 'false_alias': [True, False, False, False],
        'tautology_added': [True, False, False, False], 'partial_cleanup': [True, False, True, False],
        'new_error_content': [True, False, False, False], 'scope_excludes_error': [True, True, True, True],
        'support_acquired': [True, True, False, False], 'discard_all': [False, False, False, False],
        'other_holder': [False, False, False, False], 'support_lost': [False, False, False, False],
        'empty_scope': [True, False, False, False], 'empty_comparisons': [False, False, False, False],
        'missing_assessment': [False, False, False, False], 'single_actual': [True, False, True, True],
        'same_stage': [False, False, False, False], 'stage_truth_changed': [True, True, True, True],
        'stronger_replacement': [True, True, True, True], 'weaker_replacement': [False, False, False, False],
    }
    contrasts = {}
    for variant, expected_row in expected.items():
        want = expected_row[1:] if source else expected_row
        rows = [evaluate(d, model_for(d, variant=variant)) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Revision contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for d in docs:
        for name in ('jkscope', 'jkcorpus', 'jksupported', 'jktruth', 'jkcomparisons'):
            model = model_for(d); model[name] = guarded(d)[name]
            try: evaluate(d, model)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown corpus, warrant or truth guessed')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, unknown_relations_refused=True,
        fixed_holder_scope_and_assessment=True, semantic_information_not_sentence_count=True)


def goal_checks(texts):
    for text in texts:
        base = setup(text, True); base['statements'] = []
        quotes = []
        for name in ('hzc5', 'hzc6', 'hzc7'):
            target = k(name, *(REFS[n] for n, _ in SOURCE))
            doc = parse(format_graph(base, 'compact') + 'q[k jkgoal[k jkholder[] r[' + target + '] k jkassessment[]]].')
            description = doc['statements'][0]['body']['arguments'][1]
            model = guarded(doc)
            model.update(jkholder=lambda: 'holder', jkassessment=lambda: 'w11',
                jkgoal=lambda holder, content, context: (holder, content.syntax, context) == ('holder', syntax(description), 'w11'))
            if evaluate(doc, model) != [True]: raise ValueError('Stating a revision goal executed its unknown contents')
            for notation in ('compact', 'full'):
                form = format_graph(doc, notation)
                if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Revision goal roundtrip differs')
            quotes.append(name)
    return dict(constructors=quotes, unknown_goal_not_evaluated=True, roundtrips=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored epistemic revision differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Epistemic revision roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    segments = []
    for phrase, symbols in (('Erkenntnisse zu erweitern', ['ri5', 'hzc5']), ('von Irrthümern zu reinigen', ['ri6', 'ri7', 'hzc6', 'hzc7'])):
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=symbols))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_epistemic_revision.py', 'scripts/check_epistemic_revision.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_epistemic_revision_interpretation', documents=documents, sizes=sizes,
        generic=checks([texts[0], texts[2]]), source=checks(texts[1:], True), goals=goal_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=9, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Epistemic revision report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Warranted information, error reduction, aliases and preservation of prior information checked')


if __name__ == '__main__': main()
