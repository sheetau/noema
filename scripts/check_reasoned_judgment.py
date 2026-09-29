"""Check argument bindings and distinct Latin/German goals in explicit models."""
import argparse
import hashlib
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_reasoned_judgment import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/reasoned-judgment-v1.json'


def judgment_checks():
    text = generic_composed()[0] + '''
r fa[a a d] c.r fb[a a d] c.r fc[a a d] c.r fd[a a d] c.
r wa[] a.r wb[] a.r wc[] d.
q[t[k ya[k wa[] k wb[] p fa p fb p fc p fd]][k wc[]]].
'''
    doc = parse(text)
    rows = {}
    for variant in ('baseline', 'wrong_person', 'wrong_matter', 'different_judgment', 'different_reason',
                    'missing_use_of_reason', 'missing_support', 'wrong_scene'):
        model = {'wa': lambda: 'person', 'wb': lambda: 'matter', 'wc': lambda: 'scene',
            'fa': lambda person, act, scene: (person, act, scene) == ('other' if variant == 'wrong_person' else 'person', 'act', 'scene'),
            'fb': lambda act, matter, scene: (act, matter, scene) == ('other' if variant == 'different_judgment' else 'act', 'other' if variant == 'wrong_matter' else 'matter', 'scene'),
            'fc': lambda act, reason, scene: variant != 'missing_use_of_reason' and (act, reason, scene) == ('act', 'reason', 'scene'),
            'fd': lambda reason, act, scene: variant != 'missing_support' and (reason, act, scene) == ('other' if variant == 'different_reason' else 'reason', 'act', 'other' if variant == 'wrong_scene' else 'scene')}
        actual = evaluate_document(doc, individuals=('person', 'matter', 'act', 'reason', 'other'),
                    situations=('scene', 'other'), primitives=model)[0]['value']
        if actual != (variant == 'baseline'):
            raise ValueError('Judgment bindings differ: ' + variant)
        rows[variant] = actual
    return rows


def source_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + '''
q[t[k bk[k ao[]]][k wh[]]].
q[t[k bm[k ao[]]][k wh[]]].
q[t[o[k bl[k ao[]]]][k wh[]]].
q[t[o[k bn[k ao[]]]][k wh[]]].
q[u[e[r[k bl[k ao[]]]][r[k bn[k ao[]]]]]].
q[u[e[k bl[k ao[]]][j s[k bk[k ao[]]]]]].
''')
    from scripts.check_kant_discourse import base_model
    labels = ('latin_goal', 'german_goal', 'latin_directive_content', 'german_directive_content',
              'descriptions_distinct', 'directive_not_assertion')
    variants = ('discernment_without_current_own_use', 'own_use_without_support', 'both', 'neither',
                'no_relevant_matter', 'no_reason', 'no_support', 'wrong_matter', 'no_available_method',
                'empty_assessment', 'courage_absent')
    rows = {}
    for variant in variants:
        own_use = variant not in ('discernment_without_current_own_use', 'neither', 'courage_absent')
        supported = variant not in ('own_use_without_support', 'neither', 'no_support')
        latin = supported and variant not in ('no_relevant_matter', 'no_reason', 'wrong_matter', 'no_available_method', 'empty_assessment')
        model = base_model(doc)
        model.update({'wh': lambda: 'now',
            'ab': lambda faculty, person, scene: (faculty, person) == ('faculty', 'reader'),
            'ac': lambda person, faculty, act, scene: own_use and (person, faculty, act) == ('reader', 'faculty', 'act'),
            'ae': lambda person, plan, scene: variant != 'no_available_method' and (person, plan) == ('reader', 'plan'),
            'af': lambda person, plan, start, end: (person, plan, end) == ('reader', 'plan', 'outcome'),
            'ap': lambda person, plan, start, end: variant != 'empty_assessment' and (person, plan, end) == ('reader', 'plan', 'outcome'),
            'fa': lambda person, act, scene: (person, act, scene) == ('reader', 'act', 'outcome'),
            'fb': lambda act, matter, scene: variant != 'wrong_matter' and (act, matter, scene) == ('act', 'matter', 'outcome'),
            'fc': lambda act, reason, scene: variant != 'no_reason' and (act, reason, scene) == ('act', 'reason', 'outcome'),
            'fd': lambda reason, act, scene: supported and (reason, act, scene) == ('reason', 'act', 'outcome'),
            'fe': lambda person, matter, scene: variant != 'no_relevant_matter' and (person, matter) == ('reader', 'matter'),
            'al': lambda person, goal, scene: variant != 'courage_absent' and person == 'reader' and all(goal.values)})
        actual = [r['value'] for r in evaluate_document(doc,
            individuals=('reader', 'faculty', 'act', 'reason', 'matter', 'plan'),
            situations=('now', 'outcome'), primitives=model, max_steps=4000000)]
        expected = [latin, own_use, latin and variant != 'courage_absent', own_use and variant != 'courage_absent', True, True]
        if actual != expected:
            raise ValueError('Independent Latin reading differs: ' + variant + repr(actual))
        rows[variant] = dict(zip(labels, actual, strict=True))
    return rows


def matter_checks():
    doc = parse(generic_composed()[0] + '''
r fa[a a d] c.r fb[a a d] c.r fc[a a d] c.r fd[a a d] c.r fe[a a d] c.
r fg[a a d] c.r fh[a a d d] c.r fi[a a d d] c.r wa[] a.r wb[] d.
q[k yb[k wa[] k wb[] p fe p fa p fb p fc p fd p fg p fh p fi]].
''')
    rows = {}
    for variant in ('different_methods_for_each_matter', 'second_method_unavailable', 'failures_in_scope',
                    'second_reason_unsupported', 'no_relevant_matters', 'only_first_matter_relevant'):
        def outcomes(person, plan, start, end):
            return person == 'person' and plan in ('planone', 'plantwo') and end in (
                ('one', 'two') if variant == 'failures_in_scope' else ('one',) if plan == 'planone' else ('two',))
        model = {'wa': lambda: 'person', 'wb': lambda: 'now',
            'fa': lambda person, act, scene: person == 'person' and (act, scene) in (('actone', 'one'), ('acttwo', 'two')),
            'fb': lambda act, matter, scene: (act, matter) in (('actone', 'first'), ('acttwo', 'second')),
            'fc': lambda act, reason, scene: act in ('actone', 'acttwo') and reason == 'reason',
            'fd': lambda reason, act, scene: reason == 'reason' and act in ('actone', 'acttwo') and not (variant == 'second_reason_unsupported' and act == 'acttwo'),
            'fe': lambda person, matter, scene: person == 'person' and variant != 'no_relevant_matters'
                  and matter in (('first',) if variant == 'only_first_matter_relevant' else ('first', 'second')),
            'fg': lambda person, plan, scene: person == 'person' and plan in (
                ('planone',) if variant == 'second_method_unavailable' else ('planone', 'plantwo')),
            'fh': outcomes, 'fi': outcomes}
        actual = evaluate_document(doc, individuals=('person', 'first', 'second', 'actone', 'acttwo', 'reason', 'planone', 'plantwo'),
                    situations=('now', 'one', 'two'), primitives=model, max_steps=2000000)[0]['value']
        expected = variant in ('different_methods_for_each_matter', 'only_first_matter_relevant')
        if actual != expected:
            raise ValueError('Relevant matter or method scope differs: ' + variant)
        rows[variant] = actual
    return rows


def attribution_check():
    from scripts.check_kant_discourse import base_model, NODES, DOMAIN
    doc = parse(source_composed()[0])
    model = base_model(doc)
    def forbidden(*args):
        raise ValueError('Attribution evaluated an independent Latin goal')
    for d in doc['declarations']:
        if d['kind'] == 'primitive' and d['parameters'] and d['name'] not in ('ua', 'ub', 'uc', 'ud', 'ue', 'uf'):
            model[d['name']] = forbidden
    seen = []
    def describe(node, author, description, context):
        seen.append([node, json.loads(description.syntax)['symbol']])
        return author == 'author' and context == 'text'
    model.update(ua=describe, ub=describe, uc=describe, ud=lambda *args: True,
        ue=lambda a, b, context: a in NODES and b in NODES and NODES.index(a) < NODES.index(b),
        uf=lambda author, explained, gloss, context: (author, explained, gloss, context) == ('author', 'latin', 'german', 'text'))
    result = evaluate_document(doc, individuals=DOMAIN, situations=('text',), primitives=model)
    if result != [{'kind': 'assert', 'value': True}] or seen != [[n, s] for n, s in zip(NODES, ('bi', 'bf', 'bp', 'bl', 'bn', 'bo'), strict=True)]:
        raise ValueError('Source explanation edge or quotations changed')
    return {'references': seen, 'explanation_direction': ['latin', 'german'], 'contents_evaluated': False}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored judgment document differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Judgment roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    from scripts.check_kant_discourse import source_alignment
    alignment = source_alignment()
    alignment['segments'][3]['reading'] = 'independent_lexical_review_compositional_discernment_candidate'
    alignment['latin_is_alias_of_german_goal'] = False
    review = json.loads((ROOT / 'data/latin-motto-review-v1.json').read_text(encoding='utf-8'))
    files = [*documents, 'data/reasoned-judgment-basis-v1.json', 'data/kant-reasoned-judgment-basis-v1.json',
        'data/latin-motto-review-v1.json', 'examples/v013/contextual-ability.noema', 'data/contextual-ability-basis-v1.json',
        'examples/v013/kant-described-explanations.noema', 'data/kant-described-explanations-basis-v1.json',
        'scripts/compose_reasoned_judgment.py', 'scripts/check_reasoned_judgment.py', 'scripts/check_kant_discourse.py',
        'data/kant-opening-alignment-v1.json', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'independent_latin_goal_compositional_reading', 'documents': documents,
        'judgment_checks': judgment_checks(), 'matter_checks': matter_checks(),
        'source_checks': source_checks(), 'attribution': attribution_check(),
        'source_alignment': alignment, 'lexical_review': review, 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Reasoned judgment report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('8 judgment bindings, 6 matter/method scopes and 11 Latin/German goal cases checked')


if __name__ == '__main__':
    main()
