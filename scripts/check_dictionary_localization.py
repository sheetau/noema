"""Check translation coverage and source/structural preservation, not equivalence."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
import re

from noema.dictionary import CATALOG, ROOT, load_translations, read_source
from scripts.dictionary_localization import inventory


@lru_cache(maxsize=1)
def build_report():
    inv = inventory()
    bundle = load_translations()
    assert inv['source_sha256'] == bundle['source_sha256'], 'Public source selection or content changed'
    assert set(inv['strings']) == set(bundle['strings']), 'Translation coverage differs'
    fields = Counter()
    identifiers = 0
    for key, row in inv['strings'].items():
        translated = bundle['strings'][key]
        assert translated['ja'] == row['ja']
        for occurrence in row['occurrences']:
            fields.update(str(p) for p in occurrence['path'] if p in ('meaning', 'meaning_ja', 'naming_convention', 'interpretation_inputs', 'contract', 'roles', 'arguments', 'context', 'contrast', 'limitations', 'limits'))
        for name in set(re.findall(r'[A-Za-z][A-Za-z_0-9]{1,}', row['ja'])):
            assert name.lower() in translated['en'].lower(), (key, name)
            identifiers += 1
    original = read_source(language='ja', bundle=bundle)
    translated = read_source(bundle=bundle)
    assert original['counts'] == translated['counts']
    assert set(original['entries']) == set(translated['entries'])
    for name, row in original['entries'].items():
        english = translated['entries'][name]
        for field in ('name', 'symbol', 'declaration', 'spelling', 'sources'):
            assert row[field] == english[field], (name, field)
        assert len(row['roles']) == len(english['roles']), name
    for path in bundle['source_sha256']:
        ja = read_source(path, language='ja', bundle=bundle)
        en = read_source(path, bundle=bundle)
        assert_preserved(ja, en)
    exported = json.loads((ROOT / 'data/general-language-catalog-en-v1.json').read_text(encoding='utf-8'))
    assert exported['entries'] == translated['entries']
    page = (ROOT / 'docs/dictionary/index.html').read_text(encoding='utf-8')
    assert '<html lang="en">' in page and '/* DICTIONARY_DATA */null' not in page
    artifacts = [CATALOG, 'noema/resources/dictionary-english-v1.json', 'data/general-language-catalog-en-v1.json',
                 'docs/dictionary/index.html', 'noema/dictionary.py', 'scripts/dictionary_localization.py',
                 'scripts/build_public_dictionary.py', 'scripts/check_dictionary_localization.py',
                 'scripts/templates/dictionary.html', 'tests/test_dictionary_localization.py']
    return dict(schema='noema-dictionary-localization-check-1', status='coverage_and_structure_checked',
                entries=len(original['entries']), sources=len(inv['source_sha256']),
                unique_translated_strings=len(bundle['strings']),
                translated_occurrences=sum(len(row['occurrences']) for row in inv['strings'].values()),
                fields=dict(sorted(fields.items())), source_identifiers_preserved=identifiers,
                japanese_sources_unchanged=True, declarations_spelling_and_references_unchanged=True,
                translation_method=bundle['method'], review_scope=bundle['review_scope'],
                semantic_equivalence_proven=False,
                source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in artifacts})


def assert_preserved(original, translated):
    if isinstance(original, dict):
        assert set(translated) == set(original) | ({'meaning_en'} if 'meaning_ja' in original else set())
        for key, value in original.items():
            if key == 'meaning_ja':
                assert value == translated[key]
            else:
                assert_preserved(value, translated[key])
    elif isinstance(original, list):
        assert len(original) == len(translated)
        for left, right in zip(original, translated):
            assert_preserved(left, right)
    elif not isinstance(original, str) or not re.search(r'[\u3040-\u30ff\u3400-\u9fff]', original):
        assert original == translated


if __name__ == '__main__':
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
