import hashlib
import json

import pytest

from noema.dictionary import LocalizationError, read_source, translate_value


def bundle(tmp_path, value):
    path = tmp_path / 'basis.json'
    raw = (json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8')
    path.write_bytes(raw)
    strings = {}
    for ja, en in [('同じ行為の生起。成功は含意しない。', 'The occurrence of the same act. Success is not implied.'),
                   ('行為と状況を固定する。', 'Keep the act and situation fixed.')]:
        strings[hashlib.sha256(ja.encode('utf-8')).hexdigest()] = dict(ja=ja, en=en)
    return dict(source_sha256={'basis.json': hashlib.sha256(raw).hexdigest()}, strings=strings)


def test_localized_contract_retains_japanese_and_typed_structure(tmp_path):
    original = dict(primitives={'act': dict(parameters=['individual', 'situation'], result='truth',
                    arguments=['act', 'context'], meaning_ja='同じ行為の生起。成功は含意しない。')},
                    public_contracts={'act': dict(interpretation_inputs=['行為と状況を固定する。'])})
    translations = bundle(tmp_path, original)
    english = read_source('basis.json', root=tmp_path, bundle=translations)
    assert english['primitives']['act']['meaning_ja'] == original['primitives']['act']['meaning_ja']
    assert english['primitives']['act']['meaning_en'] == 'The occurrence of the same act. Success is not implied.'
    assert english['primitives']['act']['parameters'] == ['individual', 'situation']
    assert english['primitives']['act']['arguments'] == ['act', 'context']
    assert english['public_contracts']['act']['interpretation_inputs'] == ['Keep the act and situation fixed.']
    assert read_source('basis.json', language='ja', root=tmp_path, bundle=translations) == original
    assert json.loads((tmp_path / 'basis.json').read_text(encoding='utf-8')) == original


def test_source_change_is_rejected_even_with_valid_json(tmp_path):
    translations = bundle(tmp_path, {'naming_convention': '行為と状況を固定する。'})
    (tmp_path / 'basis.json').write_text('{}', encoding='utf-8')
    with pytest.raises(LocalizationError, match='source changed'):
        read_source('basis.json', root=tmp_path, bundle=translations)


def test_unregistered_source_and_language_are_rejected(tmp_path):
    translations = bundle(tmp_path, {})
    with pytest.raises(LocalizationError, match='not in the public dictionary'):
        read_source('../elsewhere.json', root=tmp_path, bundle=translations)
    with pytest.raises(LocalizationError, match='Supported languages'):
        read_source('basis.json', language='fr', root=tmp_path, bundle=translations)


def test_missing_translation_does_not_fall_back_to_japanese(tmp_path):
    translations = bundle(tmp_path, {})
    with pytest.raises(LocalizationError, match='No English translation'):
        translate_value({'meaning': '登録していない語義'}, translations)


def test_existing_english_contract_requires_explicit_review(tmp_path):
    translations = bundle(tmp_path, {})
    with pytest.raises(LocalizationError, match='already has meaning_en'):
        translate_value({'meaning_ja': '行為と状況を固定する。', 'meaning_en': 'Another reading'}, translations)


def test_nonprose_values_and_order_are_unchanged(tmp_path):
    translations = bundle(tmp_path, {})
    value = {'symbol': 'hzg2', 'parameters': [{'sort': 'individual', 'name': 'va'}],
             'body': {'kind': 'call', 'symbol': 'x', 'arguments': [1, None, False, 'va', 'vb']}}
    assert translate_value(value, translations) == value
