"""Preserve an actual source statement and audit vocabulary use, not truth."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.integration_audit import audit_integration, dependency_path
from noema.meaning_basis import audit_basis
from noema.script import encode, decode

ROOT = Path(__file__).resolve().parents[1]
EINSTEIN = 'examples/v014/einstein-additive-charge.noema'
KANT = 'examples/v014/kant-unrestricted-others.noema'
PARENT_BASIS = 'data/einstein-additive-charge-basis-v1.json'
MANUSCRIPT = 'examples/v014/einstein-density-manuscript.noema'
BASIS = 'data/einstein-density-manuscript-basis-v1.json'
REVIEW = 'data/density-formula-review-v2.json'
REPORT = 'reports/manuscript-integration-v1.json'
PREVIOUS_REVIEW = 'data/density-formula-review-v1.json'
CONNECTED = ('sens', 'sent', 'senu', 'senv', 'senw', 'senx', 'seny', 'zqd', 'zqe', 'zqf')
AVAILABLE = ('seoe', 'seof', 'seom', 'seon', 'seou', 'seov')
KANT_AVAILABLE = ('hzgv', 'hzgy', 'hzg3', 'hzg4')


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def serialize(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inventory(doc, watched):
    result = audit_integration(doc)
    return {key: result[key] for key in ('statement_count', 'declaration_count', 'definition_count',
        'primitive_count', 'unreferenced_definitions', 'quoted_references_included',
        'structural_audit_only', 'semantic_equivalence_verified')} | {
        'statement_reachable_count': len(result['statement_reachable_symbols']),
        'unreferenced_definition_count': len(result['unreferenced_definitions']),
        'watched_symbols': {s: {'referenced_by_any_statement': s in result['statement_reachable_symbols'],
            'statement_indices': [row['index'] for row in result['statements'] if s in row['reachable_symbols']]}
            for s in watched}}


def build_outputs():
    source = parse((ROOT / EINSTEIN).read_text(encoding='utf-8'))
    kant = parse((ROOT / KANT).read_text(encoding='utf-8'))
    index = 174
    require(len(source['statements']) == 175, 'Source statement inventory changed')
    extraction = extract_document(source, statement_indices=[index])
    doc = extraction.document
    text = format_graph(doc, 'compact') + '\n'
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        require(parse(form) == doc and parse(decode(encode(form, 'v2'))) == doc, 'Manuscript roundtrip changed')
    basis = extract_basis(source, read_json(PARENT_BASIS), extraction,
        version='einstein-density-manuscript-basis-v1', document_path=MANUSCRIPT)
    basis_audit = audit_basis(doc, basis)
    paths = {s: dependency_path(source, index, s) for s in CONNECTED + AVAILABLE}
    require(all(paths[s] is not None for s in CONNECTED), 'Expected source binding disappeared')
    require(all(paths[s] is None for s in AVAILABLE), 'Later interpretation is now integrated; revise this review')
    statement = source['statements'][index]
    # Preserve the historical authored quote exactly; do not substitute a stronger interpretation.
    require(statement['kind'] == 'assert' and statement['body']['symbol'] == 'seny', 'Not the source presentation')
    quoted = statement['body']['arguments'][-1]
    require(quoted['kind'] == 'quote' and quoted['body']['symbol'] == 'senx', 'Source quote changed')
    require([a['symbol'] for a in quoted['body']['arguments']] == ['tc', 'zqd', 'zqe', 'zqf'],
        'Fixed source interpretations changed')
    old = read_json(PREVIOUS_REVIEW)
    review = deepcopy(old)
    review.update(version='density-formula-review-v2', supersedes=PREVIOUS_REVIEW, document=MANUSCRIPT,
        source_document=EINSTEIN, source_statement_index=index, extracted_statement_index=0,
        statement_sha256=digest(serialize(statement).encode('utf-8')),
        quoted_content_sha256=digest(serialize(quoted).encode('utf-8')),
        integrated_symbols=list(CONNECTED), available_not_in_source_statement=list(AVAILABLE),
        dependency_paths=paths)
    replacements = {
        'source_context_bindings': ('structurally_connected',
            'senu/senv bind matter, event, ordered frames, points and assignments; senx fixes tc/zqd/zqe/zqf.',
            'Structural reference paths do not complete the meaning of those physical assignments.'),
        'discourse_role': ('structurally_connected',
            'The preserved seny statement attributes the exact quoted senx content using uh, uf and ue.',
            'A chosen reading of wobei and its source attribution remain partial; the preceding M0389 is not complete.'),
        'concept_grounding': ('open',
            'Velocity, local density and additive charge explanations exist as seoe/seof, seom/seon and seou/seov.',
            'None is referenced by this source statement. Substituting them may add regularity or interpretation assumptions.'),
        'whole_unit_decision': ('open',
            'Context and discourse structures are present; meaning integration, source assumptions and whole-unit comparison remain open.',
            'No semantic-completion count is authorized by this packet.')}
    for check in review['checks']:
        if check['id'] in replacements:
            check['status'], check['evidence'], check['limit'] = replacements[check['id']]
    review['checks'].insert(-1, dict(id='meaning_expansion_in_statement', status='open',
        evidence='The authored assignment argument is zqd. Later explanatory definitions are absent from its dependency closure.',
        limit='A future explicit interpretation contract must justify connection and check extra conditions; availability alone is insufficient.'))
    review['evidence_reports'] = ['reports/density-referents-v1.json', 'reports/equation-presentation-v1.json',
        'reports/material-velocity-v1.json', 'reports/local-density-v1.json', 'reports/additive-charge-v1.json']
    review['basis_caveat_policy'] = 'All ancestral caveats remain in the extracted basis; this packet scopes relevant obligations without clearing unrelated caveats.'
    artifacts = {MANUSCRIPT: text, BASIS: serialize(basis), REVIEW: serialize(review)}
    inventories = {EINSTEIN: inventory(source, CONNECTED + AVAILABLE), KANT: inventory(kant, KANT_AVAILABLE)}
    require(all(not row['referenced_by_any_statement'] for s, row in inventories[EINSTEIN]['watched_symbols'].items() if s in AVAILABLE),
        'Later interpretation appears elsewhere in the manuscript; revise inventory')
    require(all(not row['referenced_by_any_statement'] for row in inventories[KANT]['watched_symbols'].values()),
        'Kant manuscript integration changed; revise inventory')
    inputs = [EINSTEIN, KANT, PARENT_BASIS, PREVIOUS_REVIEW, *review['evidence_reports'],
        'noema/integration_audit.py', 'noema/extraction.py', 'scripts/check_manuscript_integration.py',
        'tests/test_integration_audit.py', 'docs/semantic-review-v1.md',
        'artifacts/written-units-v1/einstein-1905.json']
    report = dict(status='structural_manuscript_integration_audit_not_semantic_completion',
        inventories=inventories, selected_source_statement=index, dependency_paths=paths,
        extracted_document=MANUSCRIPT, retained_declarations=len(extraction.retained_symbols),
        removed_declarations=len(extraction.removed_symbols), preserved_author_statements=1,
        new_definitions=0, new_primitives=0, new_author_statements=0,
        review=REVIEW, basis_audit=basis_audit, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        limitations=['Reference paths include quotations but do not execute them.',
            'External function interpretations cannot be resolved by this audit.',
            'Unreferenced definitions may be useful libraries; this is not a dead-code deletion recommendation.',
            'No new source range is claimed and the partial-draft inventory is unchanged.'],
        source_sha256={name: digest((ROOT / name).read_bytes()) for name in inputs},
        output_sha256={name: digest(body.encode('utf-8')) for name, body in artifacts.items()})
    artifacts[REPORT] = serialize(report)
    return artifacts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    outputs = build_outputs()
    if args.verify_only:
        for name, body in outputs.items():
            require((ROOT / name).read_bytes() == body.encode('utf-8'), 'Stored artifact differs: ' + name)
    else:
        require(not any((ROOT / name).exists() for name in outputs), 'Output already exists; use --verify-only')
        for name, body in outputs.items():
            with (ROOT / name).open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Two manuscripts audited; one unchanged authored statement extracted; semantic completion remains unverified')


if __name__ == '__main__':
    main()
