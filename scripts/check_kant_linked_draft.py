"""Check exact projections and both meanings of colliding Kant symbols."""
import argparse
from copy import deepcopy
import hashlib
import json

from noema.grammar import format_graph, parse
from noema.linking import project_document
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_attempt_history import QUERIES, source_model as attempt_model, values as attempt_values
from scripts.check_retained_attitudes import QUERY, source_model as attitude_model, values as attitude_values
from scripts.check_confinement_onset import PARAMS, source_model as onset_model, values as onset_values
from scripts.compose_kant_linked_draft import ROOT, SOURCES, ANCESTOR, linkage, source_composed

REPORT = ROOT / 'reports/kant-linked-draft-v1.json'


def projection_checks():
    linked, pairs, ancestor = linkage()
    current = project_document(linked, 'current')
    branch = project_document(linked, 'confinement')
    branch['statements'] = deepcopy(ancestor['statements']) + branch['statements']
    if current != pairs['current'][0] or branch != pairs['confinement'][0]:
        raise ValueError('A source cannot be recovered exactly')
    return {'both_complete_source_asts_recovered': True,
        'common_declarations': len(ancestor['declarations']),
        'common_statement_prefix_present_once': len(ancestor['statements']),
        'source_declarations': {label: len(pair[0]['declarations']) for label, pair in pairs.items()},
        'linked_declarations': len(linked.document['declarations']), 'linked_statements': len(linked.document['statements']),
        'renamed_branch_symbols': {old: new for old, new in linked.symbols['confinement'].items() if old != new},
        'statement_maps': linked.statements}


def evaluation_checks():
    text = source_composed()[0]
    rows = {'permission_history': {}, 'retained_attitude': {}, 'confinement': {}}
    doc = candidate(text, QUERIES)
    for name, args, expected in (
        ('baseline', {}, [True, True, True, True]),
        ('allowed', {'allowed': True}, [False, True, True, False]),
        ('tried_without_permission', {'attempted': True}, [True, False, True, True]),
        ('able', {'able': True}, [True, True, False, False]),
        ('future_permission', {'allowed': True, 'variant': 'permission_future'}, [True, True, True, True]),
    ):
        actual = attempt_values(doc, attempt_model(doc, **args))
        if actual != expected:
            raise ValueError('Current meaning of rac/rae changed after linking: ' + name)
        rows['permission_history'][name] = actual
    doc = candidate(text, QUERY)
    for name, expected in (('baseline', [True, True]), ('lost_middle', [False, True])):
        actual = attitude_values(doc, attitude_model(doc, name))
        if actual != expected:
            raise ValueError('Current meaning of raf changed after linking: ' + name)
        rows['retained_attitude'][name] = actual
    doc = candidate(text, PARAMS + '''
q[k zbd[k za[] k zb[] k zf[] k zg[] k zc[] k zd[] k ze[]]].
q[t[k zbb[k za[] k zb[] k zf[]]][k ze[]]].q[t[k q2[k za[] k zb[]]][k ze[]]].
''')
    for name in ('baseline', 'already_confined', 'unassessed_before', 'no_change', 'different_affected_subject', 'no_application'):
        actual = onset_values(doc, onset_model(doc, name))
        if actual != [name == 'baseline', True, False]:
            raise ValueError('Relocated confinement definition changed: ' + name)
        rows['confinement'][name] = actual
    return rows


def alignment():
    linked, _, _ = linkage()
    result = []
    for filename, label in (('retained-attitudes-v1', 'current'), ('attempt-history-v1', 'current'), ('confinement-onset-v1', 'confinement')):
        source = json.loads((ROOT / ('reports/' + filename + '.json')).read_text(encoding='utf-8'))['alignment']
        segments = source.get('segments', [source])
        for segment in segments:
            row = deepcopy(segment)
            row['definitions'] = [linked.symbols[label][name] for name in row['definitions']]
            row['inherited_from_report'] = 'reports/' + filename + '.json'
            result.append(row)
    return {'segments': result, 'new_source_ranges': False, 'semantic_completion': False,
            'linking_does_not_resolve_unrepresented_meanings': True}


def build_report():
    text, basis = source_composed()
    doc = parse(text)
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
            (ROOT / 'data/kant-linked-draft-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored linked document or basis differs')
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
            raise ValueError('Linked document roundtrip differs')
    paths = [basis['document'], 'data/kant-linked-draft-basis-v1.json', 'noema/linking.py',
        'scripts/compose_kant_linked_draft.py', 'scripts/check_kant_linked_draft.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'reports/retained-attitudes-v1.json',
        'reports/attempt-history-v1.json', 'reports/confinement-onset-v1.json']
    for stem in (*SOURCES.values(), ANCESTOR):
        paths.extend(('examples/v014/' + stem + '.noema', 'data/' + stem + '-basis-v1.json'))
    return {'status': 'linked_partial_kant_drafts_not_a_complete_translation',
        'documents': {basis['document']: audit_basis(doc, basis)}, 'projections': projection_checks(),
        'evaluations': evaluation_checks(), 'alignment': alignment(), 'roundtrips': True,
        'notation_size': {'linked_characters': len(text), 'sum_of_source_characters': sum(
            len((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8')) for stem in SOURCES.values())},
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Linked Kant report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Both original drafts project exactly; renamed definitions preserve tested distinctions')


if __name__ == '__main__':
    main()
