"""Write an independently parseable dependency extraction; never overwrite."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--input', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--root', action='append', default=[])
    selection = cli.add_mutually_exclusive_group()
    selection.add_argument('--statement', type=int, action='append', help='Zero-based statement index; source order is preserved')
    selection.add_argument('--definitions-only', action='store_true', help='Explicitly omit all source statements')
    cli.add_argument('--basis-input', type=Path)
    cli.add_argument('--basis-output', type=Path)
    cli.add_argument('--basis-version', default='extracted-basis-v1')
    cli.add_argument('--manifest', type=Path)
    args = cli.parse_args(argv)
    if (args.basis_input is None) != (args.basis_output is None):
        cli.error('--basis-input and --basis-output must be supplied together')
    raw = args.input.read_bytes()
    doc = parse(raw.decode('utf-8'))
    extracted = extract_document(doc, roots=args.root, statement_indices=[] if args.definitions_only else args.statement)
    body = format_graph(extracted.document, 'compact') + '\n'
    outputs = [(args.output, body)]
    if args.basis_input:
        basis = json.loads(args.basis_input.read_text(encoding='utf-8'))
        projected = extract_basis(doc, basis, extracted, version=args.basis_version, document_path=args.output.as_posix())
        outputs.append((args.basis_output, json.dumps(projected, ensure_ascii=False, indent=2) + '\n'))
    if args.manifest:
        record = asdict(extracted)
        del record['document']
        record.update(source=args.input.as_posix(), source_sha256=hashlib.sha256(raw).hexdigest(),
                      output=args.output.as_posix(), output_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
        if args.basis_input:
            record['source_basis_sha256'] = hashlib.sha256(args.basis_input.read_bytes()).hexdigest()
        outputs.append((args.manifest, json.dumps(record, ensure_ascii=False, indent=2) + '\n'))
    paths = [path.resolve() for path, _ in outputs]
    if len(set(paths)) != len(paths):
        cli.error('Output paths must be distinct')
    if any(path.exists() for path in paths):
        cli.error('Output already exists; use a fresh path')
    # Validate every artifact before starting writes. Exclusive creation also
    # prevents overwrites if another process creates a path after this check.
    for path, content in outputs:
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
    print(f'{len(extracted.retained_symbols)} declarations and {len(extracted.statement_indices)} statements retained; '
          f'{len(extracted.removed_symbols)} unrelated declarations omitted')


if __name__ == '__main__':
    main()
