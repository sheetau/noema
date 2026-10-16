"""Check self-reference without borrowing the prior answer's citation."""
import argparse
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.script import transcribe
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from scripts import check_footnote_joint as previous
from scripts.compose_subject_bound_departure import closure
from scripts.compose_current_answer import ROOT, PARENT, PARENT_BASIS, FULL, BASIS, ANNOTATIONS, build

REPORT = ROOT / 'reports/current-answer-v1.json'
DOMAIN = previous.INDIVIDUALS + ('selfmention',)
VARIANTS = ('baseline', 'missing_occurrence', 'missing_containment', 'prior_citation_only',
    'other_mention', 'other_work', 'other_question', 'other_context', 'other_container',
    'same_documents', 'same_mentions')


def document(combined=False):
    doc = parse((ROOT / FULL).read_text(encoding='utf-8'))
    roots = [*previous.SYMBOLS, 'hzlt'] if combined else ['hzlt']
    doc['declarations'] = closure(doc, roots)
    doc['statements'] = doc['statements'][18:25] if combined else doc['statements'][-1:]
    return doc


def model(doc, variant='baseline', prior_variant='baseline'):
    values = previous.model(previous.document(), prior_variant)
    mention = 'citation' if variant == 'same_mentions' else 'selfmention'
    work = 'answer' if variant == 'same_documents' else 'document'
    values.update(hzls=lambda: mention, hzik=lambda: work)
    occurs, inside, answers = values['dg'], values['hzjk'], values['hzjj']
    values['dg'] = lambda act, ctx: occurs(act, ctx) or (
        variant != 'missing_occurrence' and (act, ctx) == (mention, 'note'))
    values['hzjk'] = lambda act, medium, ctx: inside(act, medium, ctx) or (
        variant != 'missing_containment' and (act, medium, ctx) == (
            mention, 'other' if variant == 'other_container' else work, 'note'))

    def current(act, target, question, ctx):
        if variant == 'unknown_current_answer' and act == mention:
            return previous.unknown()
        row = ('other' if variant == 'other_mention' else mention,
               'other' if variant == 'other_work' else work,
               'other' if variant == 'other_question' else 'question',
               'branch' if variant == 'other_context' else 'note')
        return answers(act, target, question, ctx) or (
            variant != 'prior_citation_only' and (act, target, question, ctx) == row)

    values['hzjj'] = current
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {n: values[n] for n in required}


def evaluate(doc, values):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN,
        situations=previous.SCENES, primitives=values, max_steps=3000000,
        memoize_definitions=False, memoize_expressions=False)]


def checks():
    doc = document(); rows = {}
    for variant in VARIANTS:
        rows[variant] = evaluate(doc, model(doc, variant))
        assert rows[variant] == [variant == 'baseline'], (variant, rows[variant])
    try:
        evaluate(doc, model(doc, 'unknown_current_answer'))
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown current answer relation was guessed')
    combined = document(True); joined = {}
    for prior, false_indices in previous.EXPECTED_FALSE.items():
        actual = evaluate(combined, model(combined, prior_variant=prior))
        assert actual == [i not in false_indices for i in range(6)] + [True], (prior, actual)
        joined[prior] = actual
    for variant in VARIANTS[1:-2]:
        actual = evaluate(combined, model(combined, variant))
        assert actual == [True] * 6 + [False], (variant, actual)
        joined['current/' + variant] = actual
    # Being presented as an answer places no constraint on an independent
    # correctness judgment: both valuations are compatible with the same text.
    extra = deepcopy(doc); extra['statements'] = []
    extra = parse(format_graph(extra, 'compact') +
                  'r jcorrect[] c.s[k hzlt[]].q[k jcorrect[]].')
    for truth in (False, True):
        values = model(doc); values['jcorrect'] = lambda truth=truth: truth
        assert evaluate(extra, values) == [True, truth]
    return dict(source_contrasts=rows, joint_seven_statement_contrasts=joined,
        unknown_refused=True, correctness_not_entailed=True)


def structure():
    old, new = load_catalog(ROOT, PARENT_BASIS), load_catalog(ROOT, BASIS)
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 25
    assert new.document['declarations'][:-2] == old.document['declarations']
    assert set(new.entries) - set(old.entries) == {'hzls', 'hzlt'}
    for name, entry in old.entries.items():
        assert new.entries[name] == entry, name
    for index in (16, 17):
        assert selection_binding(old, [index]) == selection_binding(new, [index])
    assert load_annotations(ROOT, BASIS, ANNOTATIONS).show()['entries'] == load_annotations(
        ROOT, PARENT_BASIS, 'data/courteous-reference-identifiers-v1.json').show()['entries']
    return dict(previous_statements_preserved=24, new_local_references=1,
        new_primitive_relations=0, new_definitions=1,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')),
        previous_meanings_and_review_bindings_preserved=True)


def build_report():
    for name, text in build().items():
        assert (ROOT/name).read_text(encoding='utf-8') == text
    doc = parse((ROOT/FULL).read_text(encoding='utf-8'))
    for notation in ('compact', 'full'):
        text = format_graph(doc, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    prior = json.loads((ROOT/'reports/footnote-joint-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, prior['source_sha256'])
    audit = json.loads((ROOT/'data/footnote-audit-v1.json').read_text(encoding='utf-8'))
    phrase = 'die gegenwärtige'; start = audit['text'].index(phrase)
    paths = set(prior['source_sha256']) | set(build()) | set(load_catalog(ROOT, BASIS).source_sha256) | {
        'reports/footnote-joint-v1.json', 'scripts/compose_current_answer.py',
        'scripts/check_current_answer.py', 'tests/test_current_answer.py', 'docs/current-answer-v1.md',
    }
    return dict(status='partial_current_answer_reference_checked', document=FULL,
        checks=checks(), structure=structure(), roundtrips=True,
        alignment=dict(segments=[dict(unit=audit['unit'], unit_sha256=audit['unit_sha256'],
            range=[start, start+len(phrase)], source=phrase, status='partial_explicit_current_answer',
            definitions=['hzlt'], remaining=['Whole footnote semantics remain incomplete.'])]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli = argparse.ArgumentParser(); cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args(); report = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Current answer and prior answer share the title question without merging references')


if __name__ == '__main__':
    main()
