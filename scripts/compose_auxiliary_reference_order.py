"""Correct u0176 text locations while retaining every historical declaration."""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import DescriptionValue, evaluate_document
from noema.extraction import extract_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'examples/v014/einstein-reviewed-complete-v1.noema'
PARENT_BASIS = 'data/einstein-reviewed-complete-basis-v1.json'
PARENT_ANNOTATIONS = 'data/einstein-reviewed-complete-identifiers-v1.json'
FULL = 'examples/v014/einstein-auxiliary-reference-order-v1.noema'
BASIS = 'data/auxiliary-reference-order-basis-v1.json'
ANNOTATIONS = 'data/auxiliary-reference-order-identifiers-v1.json'
SOURCE = 'data/einstein-auxiliary-reference-order-reading-v1.json'
DOC = 'docs/auxiliary-reference-order-v1.md'
REPORT = 'reports/auxiliary-reference-order-v1.json'
INVENTORY = 'artifacts/written-units-v1/einstein-1905.json'
FACSIMILE = 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
OLD_REVIEW = 'data/einstein-auxiliary-role-u0176-review-v1.json'
OLD_READING = 'data/einstein-auxiliary-role-source-reading-v1.json'
WHOLE = 'magauxsecondsentence'
RENAMES = dict(ejzz='magauxmainclauseorder', ejz2='magauxwholeassertion',
               ejz3='magauxwholemessage', ejz4='magauxwholepresentation')
MEANINGS = {
    'magauxmainclauseorder': '同じ著者・論説に帰属する補助概念の主節内容ejzyをzpvで提示する。主節zpvは同じ第二文の末尾の根拠節zptより前にあり、両箇所を区別する。物理的内容ejzvは維持する。',
    'magauxwholeassertion': '第二文全体magauxsecondsentenceで、補助概念の役割と同じ概念の導入理由を含むejzwを著者が主張し、Man siehtにより同じ全体内容を明白と提示する。主節だけへ提示の範囲を狭めない。',
    'magauxwholemessage': '第二文全体の主張と明白さの提示を含むメッセージ。引用した全体内容を実行又は証明したとはしない。',
    'magauxwholepresentation': '同じ著者・論説に第二文全体のメッセージを帰属する。第一文zpsが第二文全体より前にあることと、主節zpvが文全体とは別の箇所であることを保持する。文内部の主節と文全体に前後関係を課さない。',
}
REFERENCE_MEANING = 'u0176のMan siehtで始まりbesitzen.で終わる第二文全体の談話箇所。主節zpv、末尾の根拠節zpt、導入理由の旧箇所zpwと区別する。同じ文書・提示文脈で照合する位置参照であり、本文の物理的内容、真理又は明白さを参照だけから導かない。'
LIMITS = [
    '原文u0176の参照範囲と本文順序の修正であり、磁気類推、補助性、場依存性、導入理由の採用解釈を維持する。',
    '旧本文・全宣言・意味規約・判断・検証器を保存する。新しい二主張の意味判断は別途全単位を通読して行う。',
    '原文の節順序を有限関係表の並びで代用しない。本文上の前後と意味上の依存順序を区別する。',
    '新しい基本記号は文全体の位置参照のみ。物理的主張を一つの新しい基本関係へ置き換えない。',
]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write_once(path, value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    target = ROOT / path
    assert not target.exists() or target.read_text(encoding='utf-8') == text, path
    if not target.exists():
        target.write_text(text, encoding='utf-8', newline='\n')


def symbols(node, mapping):
    if isinstance(node, dict):
        result = {k: symbols(v, mapping) for k, v in node.items()}
        if result.get('kind') in ('call', 'function_ref'):
            result['symbol'] = mapping.get(result['symbol'], result['symbol'])
        return result
    if isinstance(node, list):
        return [symbols(v, mapping) for v in node]
    return node


def calls(node, name):
    if isinstance(node, dict):
        if node.get('kind') == 'call' and node.get('symbol') == name:
            yield node
        for value in node.values():
            yield from calls(value, name)
    elif isinstance(node, list):
        for value in node:
            yield from calls(value, name)


@lru_cache(None)
def parent():
    catalog = load_catalog(ROOT, PARENT_BASIS)
    assert catalog.document_path == PARENT
    return catalog.document


@lru_cache(None)
def document():
    old = parent()
    ds = {d['name']: d for d in old['declarations']}
    assert not ({WHOLE} | set(RENAMES.values())) & set(ds)
    assert [s['body']['symbol'] for s in old['statements'][38:42]] == ['ejzh', 'ejzs', 'ejzz', 'ejz4']
    new = deepcopy(old)
    new['declarations'].append(dict(kind='primitive', name=WHOLE, parameters=[], result='individual'))
    for name, replacement in RENAMES.items():
        declaration = deepcopy(ds[name])
        declaration['name'] = replacement
        declaration['body'] = symbols(declaration['body'], RENAMES | {'zpw': WHOLE})
        order = list(calls(declaration['body'], 'ue'))
        if name == 'ejzz':
            assert len(order) == 1
            args = order[0]['arguments']
            assert [a['symbol'] for a in args] == ['zpt', 'zpv', 'ri']
            args[0], args[1] = args[1], args[0]
        elif name == 'ejz4':
            assert len(order) == 1
            args = order[0]['arguments']
            assert [a['symbol'] for a in args] == ['zpv', WHOLE, 'ri']
            args[0]['symbol'] = 'zps'
        else:
            assert not order
        new['declarations'].append(declaration)
    for index in (40, 41):
        new['statements'][index] = symbols(new['statements'][index], RENAMES)
    assert new['declarations'][:len(old['declarations'])] == old['declarations']
    assert [i for i, (a, b) in enumerate(zip(old['statements'], new['statements'], strict=True)) if a != b] == [40, 41]
    return new


def basis():
    added = document()['declarations'][len(parent()['declarations']):]
    return dict(status='auxiliary_reference_order_corrected_semantic_review_separate',
        document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        primitives={WHOLE: dict(parameters=[], result='individual', arguments=[], meaning_ja=REFERENCE_MEANING)},
        definitions=MEANINGS, new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
        limitations=LIMITS)


def source_record():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'einstein-1905:u0176')
    text = unit['text']
    assert digest(text.encode('utf-8')) == unit['text_sha256'] == 'e029084fdb89b86b6fdb670a0fd282e2bfa8194139b4ab9bb3a2c86804649e99'
    second, relative, grounds = (text.index(s) for s in ('Man sieht', 'welcher', 'daß die elektrischen'))
    ranges = {'zps': [0, second - 1], 'zpv': [second, relative - 1],
              'zpw': [relative, len(text)], 'zpt': [grounds, len(text)], WHOLE: [second, len(text)]}
    return dict(status='source_locations_collated_semantic_review_separate', unit=unit['id'],
        unit_sha256=unit['text_sha256'], text=text, range=[0, len(text)], math=[],
        source_nonblank_characters=sum(not c.isspace() for c in text),
        locations={n: dict(range=span, text=text[slice(*span)]) for n, span in ranges.items()},
        observations=['原刊910頁を実表示し、Analogesの第一文とMan siehtからbesitzenまでの第二文を通読した。',
            '補助概念を述べる主節、welcherで始まる導入理由、daßで始まる根拠節がこの順に並ぶ。',
            '第二文全体は主節を含むため、主節が文全体より前にあるとは扱わない。',
            '本文の内容を変えず、主節と根拠節の順序、全体内容の提示範囲を訂正する。'],
        independent_human_reading=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in (INVENTORY, FACSIMILE, OLD_READING, DOC)})


def prepare():
    body = format_graph(document(), 'compact') + '\n'
    assert parse(body) == document()
    write_once(FULL, body)
    write_once(BASIS, basis())
    annotations = read(PARENT_ANNOTATIONS)
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    write_once(ANNOTATIONS, annotations)
    write_once(SOURCE, source_record())


def before(first, second, context):
    assert context in ('ri', 'other'), 'Unknown presentation context'
    if context != 'ri':
        raise ValueError('Unknown presentation context')
    positions = source_record()['locations']
    if first not in positions or second not in positions:
        raise ValueError('Unknown text location')
    return positions[first]['range'][1] <= positions[second]['range'][0]


def quoted(value):
    assert isinstance(value, DescriptionValue)
    node = json.loads(value.syntax)
    assert node.get('kind') in ('call', 'function_ref')
    return node['symbol']


def forbidden(*args):
    raise ValueError('Unprovided semantic input or executed quotation')


@lru_cache(None)
def fixture(target):
    doc = extract_document(document(), roots=[target], statement_indices=[]).document
    doc.update(schema_version='0.16', lexicon_version='0.16')
    decl = next(d for d in doc['declarations'] if d['name'] == target)
    body = dict(kind='call', symbol=target, arguments=[])
    if decl['result'] == 'content':
        if not any(d['name'] == 'ri' for d in doc['declarations']):
            doc['declarations'].append(dict(kind='primitive', name='ri', parameters=[], result='situation'))
        body = dict(kind='evaluate', content=body, situation=dict(kind='call', symbol='ri', arguments=[]))
    doc['statements'] = [dict(kind='ask', body=body)]
    return normalize_document(doc)


def run(target, replacements=None):
    constants = ('ri', 'rd', 'eirf', 'zno', 'zps', 'zpv', 'zpt', 'zpw', WHOLE)
    handlers = {n: lambda n=n: n for n in constants}
    def presentation(node, author, paper, message, context):
        return (node, author, paper, quoted(message), context) in {
            ('zpv', 'rd', 'eirf', 'ejzy', 'ri'),
            (WHOLE, 'rd', 'eirf', 'magauxwholemessage', 'ri')}
    def assertion(node, author, content, scope, context):
        return (node, author, quoted(content), scope, context) == (WHOLE, 'rd', 'ejzw', 'zno', 'ri')
    handlers.update(ue=before, eir3=presentation, uh=assertion, zdg=assertion)
    handlers.update(replacements or {})
    doc = fixture(target)
    return evaluate_document(doc, individuals=constants + ('other',), situations=('ri', 'other'),
        primitives={d['name']: handlers.get(d['name'], forbidden) for d in doc['declarations'] if d['kind'] == 'primitive'},
        memoize_definitions=True, memoize_expressions=True)[0]['value']


@lru_cache(None)
def build_report():
    assert read(BASIS) == basis() and read(SOURCE) == source_record()
    catalog = load_catalog(ROOT, BASIS)
    assert catalog.document == document()
    assert run('magauxmainclauseorder') is True and run('ejzz') is False
    assert run('magauxwholepresentation') is True and run('magauxwholeassertion') is True
    assert not before('zpv', WHOLE, 'ri') and before('zpv', 'zpt', 'ri')
    old = read(OLD_REVIEW)
    validate_hashes(ROOT, old['source_sha256'])
    pins = dict(catalog.source_sha256)
    paths = [FULL, BASIS, ANNOTATIONS, SOURCE, DOC, PARENT_ANNOTATIONS, OLD_REVIEW,
             'scripts/compose_auxiliary_reference_order.py', 'tests/test_auxiliary_reference_order.py']
    pins.update({p: digest((ROOT / p).read_bytes()) for p in paths})
    pins.update(source_record()['source_sha256'])
    return dict(status='auxiliary_text_order_and_whole_sentence_reference_checked',
        document=FULL, retained_old_declarations=len(parent()['declarations']), added_declarations=5,
        retained_statement_count=len(document()['statements']), replaced_statement_indices=[40, 41],
        source_unit='einstein-1905:u0176', actual_source_order_checked=True,
        old_order_rejected_by_source_positions=True, whole_sentence_and_main_clause_distinct=True,
        quoted_physical_content_preserved=True, historical_review_hashes_preserved=True,
        semantic_equivalence_automatically_proved=False, new_semantic_review_required=True,
        source_sha256=pins)
