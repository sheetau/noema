"""English-default access to public dictionary prose; frozen sources stay intact.

Run from a repository checkout. Localized explanations are documentation, not
new source-language semantic judgments. No models are needed to read them.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'data/general-language-catalog-v2.json'
TRANSLATIONS = Path(__file__).with_name('resources') / 'dictionary-english-v1.json'
JAPANESE = re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')


class LocalizationError(ValueError):
    """Missing, stale, or incomplete dictionary documentation translation."""


def load_translations(path=TRANSLATIONS):
    bundle = json.loads(Path(path).read_text(encoding='utf-8'))
    if bundle.get('schema') != 'noema-dictionary-translations-1':
        raise LocalizationError('Unsupported dictionary translation schema')
    for key, row in bundle['strings'].items():
        if hashlib.sha256(row['ja'].encode('utf-8')).hexdigest() != key:
            raise LocalizationError('Japanese source digest differs: ' + key)
        if not isinstance(row.get('en'), str) or not row['en'].strip() or JAPANESE.search(row['en']):
            raise LocalizationError('Missing English text: ' + key)
    return bundle


def translate_value(value, bundle):
    """Translate prose only; preserve JSON structure and all non-Japanese values."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key == 'meaning_ja':
                if 'meaning_en' in value:
                    raise LocalizationError('Source already has meaning_en; review its locale selection')
                result['meaning_ja'] = deepcopy(child)
                result['meaning_en'] = translate_value(child, bundle)
            else:
                result[key] = translate_value(child, bundle)
        return result
    if isinstance(value, list):
        return [translate_value(child, bundle) for child in value]
    if isinstance(value, str) and JAPANESE.search(value):
        key = hashlib.sha256(value.encode('utf-8')).hexdigest()
        row = bundle['strings'].get(key)
        if not row or row['ja'] != value:
            raise LocalizationError('No English translation for source text: ' + key)
        return row['en']
    return deepcopy(value)


def read_source(source=CATALOG, *, language='en', root=ROOT, bundle=None):
    if language not in ('en', 'ja'):
        raise LocalizationError('Supported languages: en, ja')
    bundle = load_translations() if bundle is None else bundle
    if source not in bundle['source_sha256']:
        raise LocalizationError('Source is not in the public dictionary manifest: ' + source)
    raw = (Path(root) / source).read_bytes()
    if hashlib.sha256(raw).hexdigest() != bundle['source_sha256'][source]:
        raise LocalizationError('Dictionary source changed; review its translations: ' + source)
    value = json.loads(raw)
    return value if language == 'ja' else translate_value(value, bundle)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=('en', 'ja'), default='en')
    parser.add_argument('--source', default=CATALOG, help='Manifest-listed repository-relative JSON path')
    parser.add_argument('--entry', help='Select a shared-catalog entry by name')
    parser.add_argument('--output', '-o', type=Path)
    args = parser.parse_args(argv)
    try:
        value = read_source(args.source, language=args.language)
        if args.entry:
            if args.entry not in value.get('entries', {}):
                raise LocalizationError('Unknown catalog entry: ' + args.entry)
            value = value['entries'][args.entry]
        body = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
        else:
            print(body, end='')
    except (LocalizationError, OSError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
