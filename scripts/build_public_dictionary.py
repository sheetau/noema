"""Build a standalone bilingual dictionary and English JSON from pinned prose."""
import argparse
import hashlib
import json

from noema.dictionary import CATALOG, ROOT, load_translations, read_source


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def build():
    bundle = load_translations()
    original = read_source(language='ja', bundle=bundle)
    english = read_source(bundle=bundle)
    english['schema'] = 'noema-general-catalog-localized-1'
    english['localization'] = dict(language='en', source=CATALOG,
        source_sha256=bundle['source_sha256'][CATALOG], translations='noema/resources/dictionary-english-v1.json',
        status='documentation_translation', review_scope=bundle['review_scope'])
    target = ROOT / 'data/general-language-catalog-en-v1.json'
    target.write_text(json.dumps(english, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    sources = {p: read_source(p, language='ja', bundle=bundle) for p in bundle['source_sha256'] if p != CATALOG}
    payload = dict(entries=original['entries'], sources=sources,
                   translations={r['ja']: r['en'] for r in bundle['strings'].values()},
                   review_scope=bundle['review_scope'])
    template = (ROOT / 'scripts/templates/dictionary.html').read_text(encoding='utf-8')
    if template.count('/* DICTIONARY_DATA */null') != 1:
        raise ValueError('Missing unique dictionary data insertion point')
    page = template.replace('/* DICTIONARY_DATA */null', dumps(payload))
    out = ROOT / 'docs/dictionary/index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding='utf-8', newline='\n')
    return dict(entries=len(original['entries']), sources=len(bundle['source_sha256']),
                translated_strings=len(bundle['strings']), artifacts={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (target, out)})


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(build(), indent=2))
