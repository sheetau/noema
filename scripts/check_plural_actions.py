"""Check plural public judgments, shared action arguments, and exact norm targets."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, Content, FunctionValue, SequenceValue
from noema.script import transcribe
from noema.semantics import SemanticError
from scripts.check_constructed_actions import setup as previous_setup, model_for as previous_model
from scripts.check_constructed_actions import DOMAIN, SCENES
from scripts.compose_plural_actions import ROOT, PARENT, SOURCE, CORE, BASIS, INPUTS, FIELD_SYMBOLS, build_documents, basis
from scripts.compose_limits import call as k

REPORT = ROOT / 'reports/plural-actions-v1.json'


@lru_cache(maxsize=1)
def setup():
    old = previous_setup()
    doc = deepcopy(old['document']); doc['statements'] = []
    source = parse((ROOT / CORE).read_text(encoding='utf-8'))
    existing = {d['name'] for d in doc['declarations']}
    wanted = {'rqh', 'rqi', 'rqj', 'rqn', 'rqo', 'rqk', 'rql', 'rqm', 'rqp',
              'hzleligible', 'hzlcollection', 'hzlframes', 'hzkframe', 'hzje', *FIELD_SYMBOLS.values()}
    doc['declarations'] += [deepcopy(d) for d in source['declarations'] if d['name'] in wanted - existing]
    for declaration in list(doc['declarations']):
        if declaration['kind'] == 'primitive' and declaration['name'].startswith('jz'):
            second = deepcopy(declaration); second['name'] = 'jb' + second['name'][2:]
            doc['declarations'].append(second)
    args = [old['arguments'], {n: x.replace('jz', 'jb') for n, x in old['arguments'].items()}]
    messages = [k('rqa', a['owncriterion']) for a in args]
    purposes = [k('rqb', a['recipient'], a['subject'], m) for a, m in zip(args, messages)]
    singles = [k('rqi', *(a[n] for n, _ in INPUTS)) for a in args]
    original = [k('rqe', *(a[n] for n, _ in INPUTS)) for a in args]
    diffs = [k('rqj', *(a[n] for n, _ in INPUTS if n in ('subject', 'owncriterion', 'standardcriterion', 'comparisons'))) for a in args]
    fields = ['p ' + FIELD_SYMBOLS[n] for n, _ in INPUTS]
    frames = k('hzlframes', k('jpcollection'), k('jzanchor'))
    target = k('rqm', frames, k('jzanchor'), *fields)
    extra = 'r jpcollection[] a.r jpfirst[] a.r jpsecond[] a.'
    extra += 'r jpcapture[a ' + ' '.join(t for _, t in INPUTS) + ' i[h[a] f] i[e] i[h[a a] e]] c.'
    extra += 'r jpcompound[i[h[a a] e]] c.'
    seeds = [k('jpcapture', k('jpfirst' if i == 0 else 'jpsecond'), *(a[n] for n, _ in INPUTS), messages[i], purposes[i], singles[i]) for i, a in enumerate(args)]
    truth = lambda desc: 't[c[s[' + desc + ']][k jzperson[] k jzactivity[]]][k jzcontext[]]'
    permission = lambda desc: k('rdm', k('jzauthority'), k('jzperson'), k('jzrole'), k('jzactivity'), desc,
        'e[n p a b][n p a b]', k('jzanchor'), 'p h7a', 'p h7b')
    queries = seeds + [k('jpcompound', target)] + [truth(x) for x in singles + diffs] + [truth(target),
        k('hzleligible', k('jzperson'), k('jzactivity'), target, k('jzanchor'))] + [permission(x) for x in singles + [target]]
    doc = parse(format_graph(doc, 'compact') + extra + ''.join('q[' + x + '].' for x in queries))
    return dict(document=doc, previous=old, arguments=args, messages=messages, purposes=purposes,
        singles=singles, original=original, target=target, truth=truth, seeds=seeds)


def model_for(data, differences=(True, False), missing=None, variant='baseline', permissions=(False, False, True), prohibited=None):
    staged = {**data['previous'], 'document': data['document']}
    model = previous_model(staged)
    stored, targets = {}, {}
    ids, topics, judgments = ('entry', 'other'), ('topic', 'other_topic'), ('judgment', 'review')
    def capture(frame, *values):
        stored[frame] = dict(zip([n for n, _ in INPUTS] + ['message', 'purpose', 'target'], values))
        targets[ids.index(frame)] = values[-1].syntax
        return True
    def compound(desc):
        targets[2] = desc.syntax
        return True
    for index, prefix in enumerate(('jz', 'jb')):
        topic, judgment, frame = topics[index], judgments[index], ids[index]
        model.update({prefix + name: model['jz' + name] for name in ('organization', 'role', 'recipient', 'channel', 'audience')})
        model[prefix + 'subject'] = lambda topic=topic: topic
        model[prefix + 'judgmentfor'] = lambda person, point, judgment=judgment: judgment
        def own(bindings, index=index, topic=topic):
            return Content(SCENES, tuple(bindings.items == (topic,) and (point == 'right' or (not differences[index] and point == 'left')) for point in SCENES))
        def standard(bindings, topic=topic):
            return Content(SCENES, tuple(bindings.items == (topic,) and point in ('left', 'right') for point in SCENES))
        model[prefix + 'own'], model[prefix + 'standard'] = own, standard
        model[prefix + 'linked'] = lambda j, desc, binding, point, judgment=judgment, topic=topic, frame=frame: (
            j == judgment and binding.items == (topic,) and desc.syntax == stored[frame]['owncriterion'].syntax)
        model[prefix + 'adopted'] = lambda org, desc, point, frame=frame: org == 'organization' and desc.syntax == stored[frame]['standardcriterion'].syntax
        model[prefix + 'candidates'] = lambda j, anchor, point, judgment=judgment: j == judgment and point == 'right'
        model[prefix + 'comparisons'] = lambda subject, point, topic=topic: subject == topic and point in ('left', 'right')
        model[prefix + 'voices'] = lambda person, act, principal, role, subject, desc, point, topic=topic, frame=frame: (
            (person, act, principal, role, subject, point) == ('person', 'speechact', 'person', 'scholar', topic, 'speech')
            and desc.syntax == stored[frame]['message'].syntax)
    def conveys(act, reader, subject, desc, point):
        return (act, reader, point) == ('speechact', 'reader', 'speech') and any(subject == topic and desc.syntax == stored[frame]['message'].syntax
            and missing != ('presentation', index) for index, (frame, topic) in enumerate(zip(ids, topics)))
    def aim(person, act, desc, point):
        return (person, act, point) == ('person', 'speechact', 'speech') and any(desc.syntax == stored[frame]['purpose'].syntax
            and missing != ('intent', index) for index, frame in enumerate(ids))
    def norm(source, person, role, act, desc, sign, point, required=False):
        if (source, person, role, act, point) != ('authority', 'person', 'scholar', 'speechact', 'anchor'):
            return False
        return any(desc.syntax == syntax and (prohibited == index and not sign if required else permissions[index] and sign)
            for index, syntax in targets.items())
    selected_members = () if variant == 'empty' else ids
    def members(collection, anchor):
        if variant == 'unknown_members':
            raise ValueError('Collection members are unknown')
        return SequenceValue(selected_members if (collection, anchor) == ('entry', 'anchor') else (), '"individual"')
    model.update(jpfirst=lambda: ids[0], jpsecond=lambda: ids[1], jpcollection=lambda: 'entry', jpcapture=capture, jpcompound=compound,
        fa=lambda person, judgment, point: any((person, judgment) == ('person', j) and missing != ('judgment', i) for i, j in enumerate(judgments)),
        fb=lambda judgment, subject, point: (judgment, subject) in tuple(zip(judgments, topics)),
        f2=conveys, hzu=aim,
        h6u=lambda act, channel, subject, desc, point: channel == 'channel' and conveys(act, 'reader', subject, desc, point),
        h7a=lambda *args: norm(*args, required=True), h7b=norm,
        hzlcollection=lambda person, activity, collection, anchor: variant != 'no_collection' and (person, activity, collection, anchor) == ('person', 'speechact', 'entry', 'anchor'),
        hzlframes=members,
        hzkframe=lambda person, activity, frame, anchor: (person, activity, anchor) == ('person', 'speechact', 'anchor')
            and frame in ids and not (variant == 'foreign_member' and frame == 'other'),
        hzje=lambda: FunctionValue(('individual', 'situation'), 'individual', lambda person, anchor: 'office' if variant == 'role_mismatch' else 'scholar'))
    for name, symbol in FIELD_SYMBOLS.items():
        model[symbol] = lambda frame, anchor, name=name: stored[frame][name]
    return model


def values(data=None, indices=None, **options):
    data = data or setup()
    if indices is not None:
        doc = deepcopy(data['document'])
        doc['statements'] = [doc['statements'][i] for i in indices]
        data = {**data, 'document': doc}
    return [r['value'] for r in evaluate_document(data['document'], individuals=DOMAIN, situations=SCENES,
        primitives=model_for(data, **options), max_steps=60_000_000)]


def attribution_checks(doc):
    selected = deepcopy(doc); selected['statements'] = selected['statements'][-1:]
    rows = []
    for grant in (False, True):
        def forbidden(*args):
            raise ValueError('Attribution executed quoted content')
        def attributed(node, author, content, scope, context):
            assert (node, author, scope, context) == ('node', 'author', 'scope', 'context')
            assert content.rank == 1 and json.loads(content.syntax) == {'kind': 'call', 'symbol': 'hzlclaim', 'arguments': []}
            return grant
        model = {d['name']: forbidden for d in selected['declarations'] if d['kind'] == 'primitive'}
        model.update(hzjn=attributed, hzjo=lambda: 'node', wa=lambda: 'author', hzjp=lambda: 'scope', wh=lambda: 'context')
        result = evaluate_document(selected, individuals=('node', 'author', 'scope'), situations=('context',), primitives=model)
        assert result == [{'kind': 'assert', 'value': grant}]
        rows.append(result)
    return rows


def full_domain_refusal(doc):
    selected = deepcopy(doc); selected['statements'] = []
    selected = parse(format_graph(selected, 'compact') + 'q[t[s[r b[k hzlclaim[]]]][k wh[]]].')
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
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis(evidence)
    documents = {}
    for path, text in texts.items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text),
            attribution=attribution_checks(doc), full_domain_refusal=full_domain_refusal(doc))
    parent, source, core = [parse((ROOT / p).read_text(encoding='utf-8')) for p in (PARENT, SOURCE, CORE)]
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1] and len(source['statements']) == 16
    names = {d['name'] for d in core['declarations']}
    assert {'rqm', 'rqp', 'rqh', 'rqi', 'rqj', 'rqk', 'rql', 'rqn', 'rqo', 'rpu', 'hzb4', 'hzu', 'hzx'} <= names
    assert not {'rqg', 'rqf', 'rqe', 'rqd', 'hzkclaim', 'hzkeligible', 'hzjc'} & names
    matrix = []
    for differences in product((False, True), repeat=2):
        result = values(differences=differences)
        assert result == [True] * 5 + list(differences) + [any(differences), True, False, False, True], (differences, result)
        matrix.append(dict(differences=list(differences), result=result))
    contrasts = {}
    for missing in product(('presentation', 'intent', 'judgment'), (0, 1)):
        result = values(missing=missing)
        expected = [True] * 3 + [missing[1] != i for i in (0, 1)] + [True, False, False, True, False, False, True]
        assert result == expected, (missing, result)
        contrasts['missing_' + missing[0] + '_' + str(missing[1])] = result
    for variant in ('empty', 'no_collection', 'foreign_member', 'role_mismatch'):
        result = values(variant=variant)
        assert result == [True] * 6 + [False, variant != 'empty', False, False, False, True], (variant, result)
        contrasts[variant] = result
    permissions = []
    for flags in product((False, True), repeat=3):
        # Norm checks require registered descriptions, not execution of the
        # action contents. Keep both frame seeds and the compound seed.
        result = values(permissions=flags, indices=(0, 1, 2, 9, 10, 11))
        assert result[-3:] == list(flags)
        permissions.append(dict(grants=list(flags), results=result[-3:]))
    note = deepcopy(json.loads((ROOT / 'reports/constructed-actions-v1.json').read_text(encoding='utf-8'))['source_note'])
    note['status'] = 'experimental_plural_target_revision_not_added_to_coverage_inventory'
    paths = [PARENT, SOURCE, CORE, BASIS, 'scripts/compose_plural_actions.py', 'scripts/check_plural_actions.py',
        'scripts/check_constructed_actions.py', 'scripts/compose_constructed_actions.py', 'scripts/check_public_divergent_judgments.py',
        'scripts/compose_quantified_permissions.py', 'reports/constructed-actions-v1.json', 'tests/test_plural_actions.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/guarded_ranked_semantics.py']
    return dict(status='partial_plural_judgments_with_some_divergence', documents=documents, preserved_parent_declarations=True,
        preserved_unaffected_statements=15, revised_attributions=1, new_definitions=12, new_primitives=2,
        finite_interpretation=dict(difference_matrix=matrix, contrasts=contrasts, independent_permissions=permissions, full_universal_permission_evaluated=False),
        source_note=note, limitations=basis(evidence)['unresolved'], verified_semantic_units=0,
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    result = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == result
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Plural judgments, some divergence, and independent exact permissions verified')


if __name__ == '__main__':
    main()
