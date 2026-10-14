"""Check signed questions and answers sharing a closed base proposition."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_question_responses import ROOT, PARENT, BUILDERS, PAIR, NORM, TRUE

REPORT = ROOT / 'reports/question-responses-v1.json'
FALSE = 'u[' + TRUE + ']'
EXTRA = '''r jyfirst[] a.r jysecond[] a.r jyauthor[] a.r jyctx[] d.
r jytruth[d] c.d jybase[] e[b scene[k jytruth[v scene]]].
d jyalias[] e[b scene[k jytruth[v scene]]].
r jyasks[a a i[f] d] c.r jyasserts[a a i[e] d] c.
r jybefore[a a d] c.r jyresponds[a a a d] c.
r jyassessor[] a.r jyholder[] a.r jyrole[] a.r jyvalid[j[a]] c.
r jyactual[j[a] d] c.d jypolicy[bindings j[a]] e[b scene[k jyactual[v bindings v scene]]].
'''
DOMAIN = ('first', 'second', 'author', 'assessor', 'holder', 'role', 'other')
SCENES = ('now', 'elsewhere')


def body(expr): return expr['body']
def query(expr): return dict(kind='ask', body=expr)
def at(expr): return dict(kind='evaluate', content=expr, situation=body(quoted('call', 'jyctx')))
def call(name, arguments): return dict(kind='call', symbol=name, arguments=arguments)


def setup(text, source=False, question_sign=False, answer_sign=False, alias=False):
    doc = candidate(text, EXTRA)
    if source:
        refs = dict(assessor='k jyassessor[]', holder='k jyholder[]', role='k jyrole[]',
            target='r[p jypolicy]', bindings='l[a][k jyholder[]]', valid='p jyvalid')
        base = apply_description(doc, quoted('function_ref', 'hzct'), [description(doc, refs[n]) for n, _ in NORM])
    else:
        base = quoted('call', 'jybase')
    question = apply_description(doc, quoted('function_ref', 'rij'), [base, description(doc, TRUE if question_sign else FALSE)])
    answer_base = quoted('call', 'jyalias') if alias else base
    answer = apply_description(doc, quoted('function_ref', 'rii'), [answer_base, description(doc, TRUE if answer_sign else FALSE)])
    arguments = [body(quoted('call', n)) for n in ('jyfirst', 'jysecond', 'jyauthor', 'jyctx')] + [question, answer]
    if not source: arguments += [body(quoted('function_ref', n)) for n in ('jyasks', 'jyasserts', 'jybefore', 'jyresponds')]
    doc['statements'] = [query(call('hzcu' if source else 'ril', arguments))]
    return parse(format_graph(doc, 'compact')), base, question, answer


def model_for(s, bits=(True,) * 4, variant='baseline', source=False, allowed=True, forbidden=False, valid=True):
    doc, _, question, answer = s
    model = guarded(doc)
    asks, asserts, before, responds = bits
    author = 'other' if variant == 'wrong_author' else 'author'
    scene = 'elsewhere' if variant == 'wrong_context' else 'now'
    response_node = 'first' if variant == 'same_node' else 'second'
    expected_question, expected_answer = syntax(question), syntax(answer)
    def asking(node, person, content, context):
        return asks and (node, person, context) == ('first', author, scene) and content.syntax == expected_question
    def asserting(node, person, content, context):
        return asserts and (node, person, context) == (response_node, 'author', 'now') and content.syntax == expected_answer
    def preceding(first, second, context):
        return before and (first, second, context) == (('second', 'first', 'now') if variant == 'reversed_order' else ('first', response_node, 'now'))
    def responding(person, first, second, context):
        expected = ('author', 'second', 'first', 'now') if variant == 'reversed_response' else ('author', 'first', response_node, 'now')
        return responds and (person, first, second, context) == expected
    model.update(jyfirst=lambda: 'first', jysecond=lambda: 'first' if variant == 'same_node' else 'second',
        jyauthor=lambda: 'author', jyctx=lambda: 'now')
    names = ('hzcr', 'uc', 'ue', 'hzcs') if source else ('jyasks', 'jyasserts', 'jybefore', 'jyresponds')
    model.update(zip(names, (asking, asserting, preceding, responding)))
    if source:
        target = syntax(description(doc, 'p jypolicy'))
        def rule(a, h, r, d, bindings, sign, context, wanted):
            return (a, h, r, d.syntax, bindings.items, context) == ('assessor', 'holder', 'role', target, ('holder',), 'now') and sign is wanted
        model.update(jyassessor=lambda: 'assessor', jyholder=lambda: 'holder', jyrole=lambda: 'role',
            jyvalid=lambda bindings: valid and bindings.items == ('holder',),
            h7l=lambda *xs: allowed and rule(*xs, True), h7k=lambda *xs: forbidden and rule(*xs, False))
    return model


def evaluate(doc, model): return values(doc, model, DOMAIN, SCENES)


def signed_checks(text):
    cases = []
    for truth, sign in product((False, True), repeat=2):
        polarity = TRUE if sign else FALSE
        extra = EXTRA + 'q[t[k rii[k jybase[] ' + polarity + ']][k jyctx[]]].'
        extra += 'q[e[k rij[k jybase[] ' + polarity + ']][k rik[k jybase[] ' + polarity + ']]].'
        doc = candidate(text, extra)
        model = guarded(doc); model.update(jytruth=lambda scene: truth, jyctx=lambda: 'now')
        actual = evaluate(doc, model)
        if actual != [truth == sign, False]: raise ValueError('Question polarity or force changed')
        cases.append(dict(truth=truth, sign=sign, results=actual))
    return cases


def discourse_checks(texts, source=False):
    setups = [setup(t, source) for t in texts]
    cases = []
    for bits in product((False, True), repeat=4):
        rows = [evaluate(s[0], model_for(s, bits, source=source)) for s in setups]
        if rows != [[all(bits)]] * len(setups): raise ValueError('Text order substituted for an answer relation')
        cases.append(dict(bits=list(bits), results=rows[0]))
    contrasts = {}
    for variant in ('wrong_author', 'wrong_context', 'reversed_order', 'reversed_response', 'same_node'):
        rows = [evaluate(s[0], model_for(s, variant=variant, source=source)) for s in setups]
        if rows != [[False]] * len(setups): raise ValueError('Attribution contrast failed: ' + variant)
        contrasts[variant] = rows[0]
    for label, options in (('positive_question', dict(question_sign=True)), ('positive_answer', dict(answer_sign=True)), ('answer_alias', dict(alias=True))):
        rows = []
        for text, expected in zip(texts, setups):
            changed = setup(text, source, **options)
            rows.append(evaluate(changed[0], model_for(expected, source=source)))
        if rows != [[False]] * len(setups): raise ValueError('Closed description identity lost: ' + label)
        contrasts[label] = rows[0]
    for s in setups:
        # All underlying truth/actuality callbacks remain guarded; only attributions run.
        if evaluate(s[0], model_for(s, source=source)) != [True]: raise ValueError('Unknown truth blocked discourse')
        model = model_for(s, source=source)
        name = 'hzcs' if source else 'jyresponds'; model[name] = guarded(s[0])[name]
        try: evaluate(s[0], model)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc): raise
        else: raise ValueError('Unknown response relation guessed')
        for notation in ('compact', 'full'):
            form = format_graph(s[0], notation)
            if parse(form) != s[0] or parse(decode(encode(form, 'v2'))) != s[0]: raise ValueError('Closed response roundtrip changed')
    for text in texts:
        unrelated = setup(text, source, alias=True)
        if evaluate(unrelated[0], model_for(unrelated, source=source)) != [True]:
            raise ValueError('Generic discourse relation incorrectly claimed content identity')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, underlying_truth_not_required=True,
        unknown_response_refused=True, shared_base_constructed=True, closed_roundtrips=True,
        generic_relation_does_not_enforce_content_identity=True)


def normative_checks(texts):
    cases = []
    for allowed, forbidden, valid in product((False, True), repeat=3):
        rows = []
        for text in texts:
            s = setup(text, True); doc = deepcopy(s[0])
            doc['statements'] += [query(at(dict(kind='disquote', description=s[1]))), query(at(dict(kind='disquote', description=s[3])))]
            rows.append(evaluate(doc, model_for(s, source=True, allowed=allowed, forbidden=forbidden, valid=valid)))
        permitted = allowed and not forbidden and valid
        want = [True, permitted, not permitted]
        if rows != [want] * len(texts): raise ValueError('Entitlement, negative response and occurrence conflated')
        cases.append(dict(allowed=allowed, forbidden=forbidden, valid=valid, results=want))
    for text in texts:
        s = setup(text, True); doc = deepcopy(s[0]); doc['statements'] = [query(at(dict(kind='disquote', description=s[3])))]
        model = model_for(s, source=True); model['h7l'] = guarded(s[0])['h7l']
        try: evaluate(doc, model)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc): raise
        else: raise ValueError('Unknown permission became false')
    return dict(cases=cases, actual_policy_not_executed=True, unknown_permission_refused=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored question responses differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Question response roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    segments = []
    for phrase, symbols in (('berechtigt sein', ['hzct']), ('Ich sage:', ['hzcu']), ('das ist ganz unmöglich', ['rii', 'rij', 'hzcu'])):
        if unit['text'].count(phrase) != 1: raise ValueError('Source phrase not unique')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
            range=[start, start + len(phrase)], text=phrase, definitions=symbols))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_question_responses.py', 'scripts/check_question_responses.py',
        'scripts/check_assessed_payments.py', 'scripts/check_closed_policies.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'noema/description_templates.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_question_response_interpretation', documents=documents, sizes=sizes,
        signed=signed_checks(texts[0]), generic=discourse_checks([texts[0], texts[2]]),
        source=discourse_checks(texts[1:], True), normative=normative_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=6, new_primitives=2, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Question response report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Signed questions, shared-base responses, attribution and nonfactive permission checked')


if __name__ == '__main__': main()
