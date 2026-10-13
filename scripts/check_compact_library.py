"""Compare evaluations before/after extracting their exact reference closure."""
import argparse
from copy import deepcopy
import hashlib
import json
from unittest.mock import patch

from noema.extraction import extract_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts import check_office_speech as office
from scripts import check_protected_speech as protected
from scripts import check_public_assessment as assessment
from scripts.compose_compact_library import ROOT, PARENT, ROOTS, composed

REPORT = ROOT / 'reports/compact-library-v1.json'


def replay_checks():
    records = {}
    for module, checks in ((office, [office.finite_checks]), (protected, [protected.finite_checks]),
                            (assessment, [assessment.finite_checks, assessment.source_checks])):
        original = module.values
        successful = failed = 0
        cache = {}
        def compare(doc, model, domain, scenes):
            nonlocal successful, failed
            key = id(doc)
            if key not in cache:
                # Keep the source alive so Python cannot reuse its id.
                cache[key] = (doc, extract_document(doc).document)
            small = cache[key][1]
            names = {d['name'] for d in small['declarations'] if d['kind'] == 'primitive'}
            reduced = {name: callback for name, callback in model.items() if name in names}
            try:
                expected = original(doc, model, domain, scenes)
            except ValueError as error:
                try:
                    original(small, reduced, domain, scenes)
                except ValueError as observed:
                    if type(error) is not type(observed) or str(error) != str(observed):
                        raise ValueError('Extraction changed refusal behavior') from observed
                else:
                    raise ValueError('Extraction silently completed an unknown interpretation') from error
                failed += 1
                raise
            actual = original(small, reduced, domain, scenes)
            if actual != expected:
                raise ValueError('Extracted interpretation differs')
            successful += 1
            return expected
        with patch.object(module, 'values', compare):
            for check in checks:
                check()
        if module.values is not original:
            raise ValueError('Replay evaluator was not restored')
        records[module.__name__] = {'matching_evaluations': successful, 'matching_refusals': failed,
                                   'distinct_query_documents': len(cache)}
    return records


def build_report():
    parent_text = (ROOT / PARENT).read_text(encoding='utf-8')
    parent = parse(parent_text)
    documents, sizes = {}, {}
    for library_only in (False, True):
        text, basis, extracted = composed(library_only)
        stem = 'public-speech-core' if library_only else 'kant-compact-library'
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored compact library differs')
        doc = parse(text)
        if doc != extracted.document:
            raise ValueError('Extraction did not preserve normalized structure')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Compact library roundtrip differs')
        if not library_only and doc['statements'] != parent['statements']:
            raise ValueError('Original author statements were altered')
        if library_only and doc['statements']:
            raise ValueError('Definition library contains unexpected author statements')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'declarations': len(doc['declarations']),
                      'statements': len(doc['statements']), 'removed_declarations': len(extracted.removed_symbols),
                      'retained_symbols': extracted.retained_symbols}
    row = deepcopy(json.loads((ROOT / 'reports/public-assessment-v1.json').read_text(encoding='utf-8'))['alignment']['segments'][0])
    row['review_ja'] = '既存の公的発言・判断目的の部分草案について、参照先の閉包を保持した独立文書を作成した。本文と定義の構文は変更しておらず、原文との新しい意味一致を主張しない。'
    paths = [*documents, PARENT, 'data/public-speech-core-basis-v1.json', 'data/kant-compact-library-basis-v1.json',
        'data/kant-public-assessment-basis-v1.json', 'scripts/compose_compact_library.py', 'scripts/check_compact_library.py',
        'scripts/extract_document.py', 'noema/extraction.py', 'noema/meaning_basis.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'scripts/check_office_speech.py',
        'scripts/check_protected_speech.py', 'scripts/check_public_assessment.py', 'reports/public-assessment-v1.json']
    return json.loads(json.dumps({'status': 'dependency_extraction_not_semantic_rewriting', 'documents': documents,
        'source_characters': len(parent_text), 'sizes': sizes, 'roots': ROOTS, 'replays': replay_checks(),
        'roundtrips': True, 'all_original_statements_preserved_in_compact_document': True,
        'names_aliases_and_quoted_syntax_preserved': True,
        'alignment': {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Compact library report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(report['replays']))


if __name__ == '__main__':
    main()
