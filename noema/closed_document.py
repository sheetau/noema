"""Remove unused declarations while preserving every statement and quoted name.

Explicit opt-in for editions 0.8--0.16. This is dependency extraction, not
semantic simplification or a claim that retained primitives are explained.
"""
import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from .constructed import parse, format_graph
from .constructed_discourse import normalize_document
from .extraction import ExtractedDocument, _references
from .semantics import require


def prune_document(document, *, roots=()):
    """Keep all statements, optional library roots and their dependency closure.

    Validate the entire input first, including unused declarations. Retain source
    order, duplicate statements, quotation ranks, identifiers and binder scopes.
    Never merge definitions with equal bodies: their quoted names can differ.
    """
    doc = normalize_document(document)
    require(isinstance(roots, (tuple, list)) and all(isinstance(n, str) for n in roots),
            'Roots must be a list or tuple of symbol names')
    lookup = {d['name']: d for d in doc['declarations']}
    require(set(roots) <= lookup.keys(), 'Unknown extraction root')
    pending = set(roots) | _references(doc['statements'])
    retained = set()
    while pending:
        symbol = pending.pop()
        if symbol in retained:
            continue
        retained.add(symbol)
        pending.update(_references(lookup[symbol]) - retained)
    result = deepcopy(doc)
    result['declarations'] = [d for d in result['declarations'] if d['name'] in retained]
    checked = normalize_document(result)
    require(checked == result, 'Extraction changed retained syntax')
    return ExtractedDocument(checked, sorted(set(roots)), list(range(len(doc['statements']))),
        [d['name'] for d in doc['declarations'] if d['name'] in retained],
        [d['name'] for d in doc['declarations'] if d['name'] not in retained])


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def certificate(source, extraction):
    """Check extraction before recording exact syntax hashes, never evaluations."""
    checked = prune_document(source, roots=extraction.roots)
    require(checked == extraction, 'Extraction does not match source')
    record = asdict(extraction)
    del record['document']
    doc = normalize_document(source)
    output = extraction.document
    record.update(schema_version=doc['schema_version'], source_ast_sha256=fingerprint(doc),
        output_ast_sha256=fingerprint(output),
        statement_ast_sha256=[fingerprint(s) for s in doc['statements']],
        retained_declaration_sha256={d['name']: fingerprint(d) for d in output['declarations']},
        retained_primitives=[d['name'] for d in output['declarations'] if d['kind'] == 'primitive'],
        all_statements_preserved=True, definitions_rewritten=False, semantic_completion=False)
    return record


def verify_certificate(source, output, record):
    require(isinstance(record, dict), 'Expected an extraction certificate')
    extraction = prune_document(source, roots=record.get('roots', ()))
    require(normalize_document(output) == extraction.document, 'Output differs from dependency closure')
    require(record == certificate(source, extraction), 'Certificate differs from extraction')
    return extraction


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--input', '-i', type=Path, required=True)
    cli.add_argument('--output', '-o', type=Path, required=True)
    cli.add_argument('--manifest', type=Path)
    cli.add_argument('--root', action='append', default=[], help='Keep an extra reusable definition and its dependencies')
    args = cli.parse_args(argv)
    raw = args.input.read_bytes()
    doc = parse(raw.decode('utf-8'))
    extracted = prune_document(doc, roots=args.root)
    text = format_graph(extracted.document, 'compact') + '\n'
    outputs = [(args.output, text)]
    if args.manifest:
        manifest = dict(source=args.input.as_posix(), output=args.output.as_posix(),
            source_sha256=hashlib.sha256(raw).hexdigest(),
            output_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
            certificate=certificate(doc, extracted))
        outputs.append((args.manifest, json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'))
    paths = [p.resolve() for p, _ in outputs]
    if len(paths) != len(set(paths)):
        cli.error('Output paths must be distinct')
    if any(p.exists() for p in paths):
        cli.error('Output already exists; use a fresh path')
    for path, body in outputs:
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(body)
    print(f'{len(extracted.statement_indices)} statements preserved; '
          f'{len(extracted.retained_symbols)} declarations retained; '
          f'{len(extracted.removed_symbols)} unused declarations removed')


if __name__ == '__main__':
    main()
