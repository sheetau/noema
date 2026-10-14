"""Check constructed actions against the existing action definition and permission target."""
from copy import deepcopy
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph, promote
from noema.constructed_semantics import evaluate_document, Content, FunctionValue
from noema.finite_semantics import Content as LegacyContent
from noema.script import transcribe
from noema.semantics import SemanticError
from scripts.check_public_divergent_judgments import setup as previous_setup, model_for as previous_model, DOMAIN, SCENES
from scripts.compose_public_divergent_judgments import FRAME
from scripts.compose_constructed_actions import ROOT, PARENT, SOURCE, CORE, BASIS, INPUTS, ELIGIBLE, FIELD_SYMBOLS, append_constructors, build_documents, basis
from scripts.compose_limits import call as k

REPORT = ROOT / 'reports/constructed-actions-v1.json'


def setup():
    data = previous_setup((ROOT / 'examples/v014/public-divergent-judgments-core.noema').read_text(encoding='utf-8'))
    doc = promote(data['document']); doc['statements'] = []
    doc, _ = append_constructors(doc)
    args = {name: data['bindings'][name] if name in ('owncriterion', 'standardcriterion') else 'r[' + data['bindings'][name] + ']'
            for name, _ in INPUTS}
    target = k('rqe', *(args[name] for name, _ in INPUTS))
    message = k('rqa', args['owncriterion'])
    purpose = k('rqb', args['recipient'], args['subject'], message)
    extra = 'r jacapture[i[h[a] f] i[e] i[h[a a] e]] c.r jaframes[a a a d] c.r jaroles[a d] a.'
    direct = {**data['bindings'], 'message': message, 'goal': purpose}
    fields = {name: 'i[frame a anchor d][' + args[name] + ']' for name, _ in INPUTS}
    fields.update(person=k('jzperson'), activity=k('jzactivity'), target=target, anchor=k('jzanchor'), frames='p jaframes', roles='p jaroles')
    queries = [k('jacapture', message, purpose, target),
        't[c[' + k('hzgy', *(direct[name] for name, _ in FRAME)) + '][' + k('jzperson') + ' ' + k('jzactivity') + ']][' + k('jzcontext') + ']',
        't[c[s[' + target + ']][' + k('jzperson') + ' ' + k('jzactivity') + ']][' + k('jzcontext') + ']',
        k('rqf', target, *(args[name] for name, _ in INPUTS)),
        k('rqg', *(fields[name] for name, _ in ELIGIBLE)),
        k('rdm', k('jzauthority'), k('jzperson'), k('jzrole'), k('jzactivity'), target, 'e[n p a b][n p a b]', k('jzanchor'), 'p h7a', 'p h7b'),
        't[s[' + purpose + ']][' + k('jzcontext') + ']']
    doc = parse(format_graph(doc, 'compact') + extra + ''.join('q[' + query + '].' for query in queries))
    return dict(previous=data, document=doc, arguments=args, target=target, message=message, purpose=purpose)


def model_for(data, performed=True, intended=True, permitted=True, reviewed=False, variant='baseline'):
    old = deepcopy(data['previous'])
    original = previous_model(old, bits=(performed, intended, permitted, True, True), variant=variant, reviewed=reviewed)
    def convert(fn):
        def call(*args):
            value = fn(*args)
            return Content(value.situations, value.values) if isinstance(value, LegacyContent) else value
        return call
    def forbidden(*args):
        raise ValueError('Undeclared model interpretation executed')
    model = {d['name']: convert(original[d['name']]) if d['name'] in original else forbidden
        for d in data['document']['declarations'] if d['kind'] == 'primitive'}
    def capture(message, purpose, target):
        # Existing concrete interpretation compares exact description syntax.
        # Supply the newly constructed descriptions before any action is run.
        old.update(message_syntax=message.syntax, goal_syntax=purpose.syntax, target_syntax=target.syntax)
        return all(value.rank == 0 for value in (message, purpose, target))
    model.update(jacapture=capture,
        jaframes=lambda person, activity, frame, anchor: variant != 'no_frame' and (person, activity, frame, anchor) == ('person', 'speechact', 'entry', 'anchor'),
        jaroles=lambda person, anchor: 'office' if variant == 'role_mismatch' else 'scholar')
    return model


def values(data, **options):
    return [r['value'] for r in evaluate_document(data['document'], individuals=DOMAIN, situations=SCENES,
        primitives=model_for(data, **options), max_steps=60_000_000)]


def source_eligibility_case(data, variant='baseline'):
    """Evaluate the actual stored source eligibility definition at a concrete pair."""
    doc = deepcopy(data['document']); doc['statements'] = []
    source = parse((ROOT / CORE).read_text(encoding='utf-8'))
    wanted = {'hzje', 'hzkframe', 'hzkeligible', *FIELD_SYMBOLS.values()}
    existing = {d['name'] for d in doc['declarations']}
    if wanted & existing:
        raise ValueError('Source fixture symbol collision')
    doc['declarations'] += [deepcopy(d) for d in source['declarations'] if d['name'] in wanted]
    extra = 'r jcapturefields[' + ' '.join(type_ for _, type_ in INPUTS) + '] c.'
    extra += 'q[k jcapturefields[' + ' '.join(data['arguments'][name] for name, _ in INPUTS) + ']].'
    extra += 'q[' + k('hzkeligible', k('jzperson'), k('jzactivity'), data['target'], k('jzanchor')) + '].'
    doc = parse(format_graph(doc, 'compact') + extra)
    staged = {**data, 'document': doc}
    model = model_for(staged, variant=variant)
    stored = {}
    def capture(*items):
        stored.update(zip((name for name, _ in INPUTS), items))
        return True
    # The source definition receives the same role function used for permission.
    model['hzje'] = lambda: FunctionValue(('individual', 'situation'), 'individual', model['jaroles'])
    model['hzkframe'] = model['jaframes']
    model['jcapturefields'] = capture
    for name, symbol in FIELD_SYMBOLS.items():
        model[symbol] = lambda frame, anchor, name=name: stored[name]
    result = [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES, primitives=model, max_steps=60_000_000)]
    return result


def attribution_checks(doc):
    selected = deepcopy(doc); selected['statements'] = selected['statements'][-1:]
    rows = []
    for grant in (False, True):
        def forbidden(*args):
            raise ValueError('Attribution executed its content')
        def attributed(node, author, content, scope, context):
            if (node, author, scope, context) != ('node', 'author', 'scope', 'context'):
                raise ValueError('Attribution reference changed')
            if content.rank != 1 or json.loads(content.syntax) != {'kind': 'call', 'symbol': 'hzkclaim', 'arguments': []}:
                raise ValueError('Wrong revised attribution content')
            return grant
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(hzjn=attributed, hzjo=lambda: 'node', wa=lambda: 'author', hzjp=lambda: 'scope', wh=lambda: 'context')
        result = evaluate_document(selected, individuals=('node', 'author', 'scope'), situations=('context',), primitives=model)
        if result != [{'kind': 'assert', 'value': grant}]:
            raise ValueError('Revised attribution was made factive')
        rows.append(dict(attribution=grant, result=result))
    return rows


def full_domain_refusal(doc):
    selected = deepcopy(doc); selected['statements'] = []
    selected = parse(format_graph(selected, 'compact') + 'q[t[s[r b[k hzkclaim[]]]][k wh[]]].')
    def forbidden(*args):
        raise ValueError('A finite interpretation was invented for an unspecified field')
    model = {d['name']: forbidden for d in selected['declarations'] if d['kind'] == 'primitive'}
    for declaration in selected['declarations']:
        type_ = declaration['result']
        if declaration['kind'] == 'primitive' and not declaration['parameters'] and isinstance(type_, dict) and type_['kind'] == 'function':
            function = FunctionValue(tuple(type_['parameters']), type_['result'], forbidden)
            model[declaration['name']] = lambda function=function: function
    model.update(hzjd=lambda: 'person', wh=lambda: 'context')
    try:
        evaluate_document(selected, individuals=('person',), situations=('context',), primitives=model)
    except SemanticError as exc:
        if 'description domain' not in str(exc):
            raise
        return str(exc)
    raise ValueError('The full description domain was silently sampled')


def build_report():
    texts, evidence = build_documents()
    meanings = basis(texts, evidence)
    if json.loads((ROOT / BASIS).read_text(encoding='utf-8')) != meanings:
        raise ValueError('Constructed action basis differs')
    documents = {}
    for path, text in texts.items():
        if (ROOT / path).read_text(encoding='utf-8') != text:
            raise ValueError('Stored constructed action differs: ' + path)
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(transcribe(form, alphabet='v2')) != doc:
                raise ValueError('Constructed action roundtrip differs')
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']),
            characters=len(text), attribution=attribution_checks(doc), full_domain_refusal=full_domain_refusal(doc))
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8')); source = parse(texts[SOURCE])
    if source['declarations'][:len(parent['declarations'])] != parent['declarations'] or source['statements'][:-1] != parent['statements'][:-1]:
        raise ValueError('Historical declaration or unaffected statement changed')
    names = {d['name'] for d in parse(texts[CORE])['declarations']}
    required = {'rqg', 'rqf', 'rqe', 'rqd', 'rqa', 'rqb', 'rpu', 'rpt', 'rpq', 'hzb4', 'hzu', 'hzx'}
    if not required <= names or {'hzjc', 'hzjq', 'hzjr'} & names or any(n.startswith('jtemplate') for n in names):
        raise ValueError('Actual source dependency binding differs')
    data = setup(); matrix = []
    for bits in product((False, True), repeat=4):
        performed, intended, permitted, reviewed = bits
        result = values(data, performed=performed, intended=intended, permitted=permitted, reviewed=reviewed)
        actual = performed and intended
        if result != [True, actual, actual, True, True, permitted, reviewed]:
            raise ValueError(('Action comparison differs', bits, result))
        matrix.append(dict(performed=performed, intended=intended, permitted=permitted, reviewed=reviewed, result=result))
    contrasts = {}
    for variant in ('other_judge', 'other_issue', 'other_standard', 'empty_candidates', 'other_message', 'other_goal',
                    'other_voice', 'outsider', 'not_scholar', 'other_permitted_target', 'public_prohibited', 'no_frame', 'role_mismatch'):
        actual = variant in ('other_permitted_target', 'public_prohibited', 'no_frame', 'role_mismatch')
        eligible = variant not in ('no_frame', 'role_mismatch')
        permitted = variant not in ('other_permitted_target', 'public_prohibited')
        result = values(data, variant=variant)
        if result != [True, actual, actual, True, eligible, permitted, False]:
            raise ValueError(('Action contrast differs', variant, result))
        contrasts[variant] = result
    source_cases = {}
    for variant, eligible in (('baseline', True), ('no_frame', False), ('role_mismatch', False)):
        result = source_eligibility_case(data, variant)
        if result != [True, eligible]:
            raise ValueError('Actual source eligibility differs: ' + variant)
        source_cases[variant] = result
    previous = json.loads((ROOT / 'reports/quantified-permissions-v1.json').read_text(encoding='utf-8'))
    note = deepcopy(previous['source_note'])
    note['status'] = 'experimental_revised_eligibility_not_added_to_coverage_inventory'
    paths = [PARENT, SOURCE, CORE, BASIS, 'examples/v014/kant-unrestricted-others.noema',
        'examples/v014/public-divergent-judgments-core.noema', 'reports/quantified-permissions-v1.json',
        'scripts/compose_constructed_actions.py', 'scripts/check_constructed_actions.py',
        'scripts/compose_constructed_purposes.py', 'scripts/compose_public_divergent_judgments.py',
        'scripts/compose_quantified_permissions.py', 'scripts/check_public_divergent_judgments.py',
        'noema/specialization.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/constructed.py',
        'noema/guarded_ranked_semantics.py', 'tests/test_constructed_actions.py']
    return dict(status='partial_exact_action_construction_connected_to_revised_author_attribution', documents=documents,
        preserved_parent_declarations=True, preserved_unaffected_statements=15, revised_attributions=1, new_attributions=0,
        new_definitions=10, new_primitives=15, template_derivation=evidence,
        finite_interpretation=dict(matrix=matrix, contrasts=contrasts, actual_source_eligibility=source_cases,
            full_universal_permission_evaluated=False),
        actual_source_dependencies=dict(required_reached=sorted(required), old_opaque_eligibility_not_reached=True),
        source_note=note, limitations=meanings['unresolved'], verified_semantic_units=0,
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args(argv)
    result = build_report()
    if args.verify_only:
        if json.loads(REPORT.read_text(encoding='utf-8')) != result:
            raise ValueError('Stored constructed action report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Exact action construction and actual source eligibility checked; 16 truth cases and 13 contrasts agree')


if __name__ == '__main__':
    main()
