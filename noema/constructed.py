"""Explicit opt-in CLI/API for the typed quotation construction prototype (edition 0.16).

The historical parser and interpreter remain unchanged. This module does not
claim a consistency/termination theorem for arbitrary higher-order primitives.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from .constructed_discourse import parse_document, format_document, normalize_document
from .script import transcribe
from .semantics import require


def parse(text):
    return parse_document(transcribe(text, reverse=True))


def format_graph(document, notation='full'):
    require(notation in ('compact', 'full'), 'Unknown notation')
    return format_document(document, compact=notation == 'compact')


def promote(document):
    require(document['schema_version'] in ('0.14', '0.15'), 'Explicitly promote an edition 0.14 or 0.15 document')
    result = deepcopy(document)
    result['schema_version'] = result['lexicon_version'] = '0.16'
    return normalize_document(result)


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('operation', choices=('parse', 'format', 'render'))
    cli.add_argument('--input', '-i', type=Path, required=True)
    cli.add_argument('--output', '-o', type=Path)
    cli.add_argument('--notation', choices=('full', 'compact'), default='compact')
    cli.add_argument('--script', action='store_true')
    args = cli.parse_args(argv)
    text = args.input.read_text(encoding='utf-8')
    doc = parse(text)
    if args.operation == 'parse':
        body = json.dumps(doc, ensure_ascii=False, indent=2)
    elif args.operation == 'format':
        body = format_graph(doc, args.notation)
        if args.script:
            body = transcribe(body, alphabet='v2')
    else:
        from .constructed_render import render
        body = render(text, alphabet='v2', notation=args.notation)
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(body + '\n')
    else:
        print(body)


if __name__ == '__main__':
    main()
