"""Publish closed subsets of the cumulative Kant definitions, without renaming."""
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-public-assessment.noema'
ROOTS = 'ret reu rev hzn hzo hzp hzq hzr hzs hzt hzw hzx hzy'.split()


def composed(library_only=False):
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    source_basis = json.loads((ROOT / 'data/kant-public-assessment-basis-v1.json').read_text(encoding='utf-8'))
    extracted = extract_document(doc, roots=ROOTS, statement_indices=[] if library_only else None)
    stem = 'public-speech-core' if library_only else 'kant-compact-library'
    basis = extract_basis(doc, source_basis, extracted, version=stem + '-basis-v1',
                          document_path='examples/v014/' + stem + '.noema')
    return format_graph(extracted.document, 'compact') + '\n', basis, extracted


def main():
    for library_only in (False, True):
        text, basis, extracted = composed(library_only)
        stem = 'public-speech-core' if library_only else 'kant-compact-library'
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json',
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored compact library differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters;', len(basis['primitives']), 'primitives;',
              len(basis['definitions']), 'definitions;', len(extracted.document['statements']), 'statements')


if __name__ == '__main__':
    main()
