"""Inventory and export public dictionary prose without altering frozen sources."""
import hashlib
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'data/general-language-catalog-v2.json'
JAPANESE = re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def public_sources():
    catalog = read(CATALOG)
    paths = {CATALOG}
    paths.update(p for row in catalog['entries'].values() for p in row['sources'] if p.endswith('.json'))
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'noema/resources').glob('visible-*.json'))
    pending = list(paths)
    while pending:
        value = read(pending.pop())
        linked = [value.get('basis')]
        linked += [row.get('basis') for row in value.get('libraries', [])]
        for path in linked:
            if path and path not in paths:
                paths.add(path)
                pending.append(path)
    return sorted(paths)


def prose(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from prose(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from prose(child, (*path, index))
    elif isinstance(value, str) and JAPANESE.search(value):
        yield path, value


def inventory():
    sources, strings = {}, {}
    for path in public_sources():
        raw = (ROOT / path).read_bytes()
        sources[path] = hashlib.sha256(raw).hexdigest()
        for pointer, text in prose(json.loads(raw)):
            row = strings.setdefault(digest(text), dict(ja=text, occurrences=[]))
            row['occurrences'].append(dict(source=path, path=list(pointer)))
    return dict(schema='noema-dictionary-localization-inventory-1', source_sha256=sources, strings=strings)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', '-o', type=Path, default=Path('artifacts/dictionary-localization/inventory.json'))
    args = cli.parse_args()
    value = inventory()
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(sources=len(value['source_sha256']), unique_strings=len(value['strings']),
                         japanese_characters=sum(len(r['ja']) for r in value['strings'].values()),
                         inventory=str(path)), indent=2))
