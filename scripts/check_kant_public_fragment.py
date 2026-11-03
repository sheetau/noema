"""Small distinguishing corpus for public Kant forms, branches and scope."""
from functools import lru_cache
import hashlib
import html
import json
from pathlib import Path

from scripts.kant_public_fragment import (
    compile_statement, decode, vocabulary, words, forms, table, feature,
    GRAMMAR, VERSION, reserved_forms, root_words, declarations_for,
)
from scripts.kant_geometry_reader import read_geometry
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.check_visible_syntax import call, assertion, logic, quant, variable, quote, vocabulary as baseline_vocabulary
from noema.constructed_discourse import normalize_document

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/kant-public-fragment'


def canonical(body):
    used = set()
    def collect(node):
        if isinstance(node, dict):
            if node.get('kind') in ('call', 'function_ref'):
                used.add(node['symbol'])
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)
    collect(body)
    declarations = declarations_for(tuple(sorted(used)))
    return normalize_document(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=declarations, statements=[assertion(body)]))['statements'][0]


@lru_cache(maxsize=1)
def cases():
    town, home = call('town'), call('home')
    rain = call('rain', town)
    shelter = call('rain', home)
    red = call('red', call('book'))
    bound = lambda body: quant('forall', 'x', quant('exists', 'y', body))
    rows = [
        ('rain-town', '町に雨が降る', rain),
        ('rain-home', '住まいに雨が降る', shelter),
        ('above', '鳥・木の順', call('above', call('birdone'), call('treeone'))),
        ('above-reversed', '木・鳥の順', call('above', call('treeone'), call('birdone'))),
        ('give', '渡す人・相手・物', call('give', call('aki'), call('nao'), call('book'))),
        ('give-reversed', '渡す人と相手を交換', call('give', call('nao'), call('aki'), call('book'))),
        ('not', '降雨の否定', logic('not', rain)),
        ('and-left', '左側で結合する連言', logic('and', logic('and', rain, shelter), red)),
        ('and-right', '右側で結合する連言', logic('and', rain, logic('and', shelter, red))),
        ('or', '二つの場所の選言', logic('or', rain, shelter)),
        ('implies', '条件と帰結', logic('implies', rain, shelter)),
        ('equal', '同一性の左右', logic('equal', town, home)),
        ('equal-reversed', '同一性の左右を交換', logic('equal', home, town)),
        ('quote', '引用された二つの項', logic('equal', quote(town), quote(home))),
        ('quote-inner-not', '引用の内側の否定', logic('equal', quote(logic('not', rain)), quote(shelter))),
        ('quote-outer-not', '引用の外側の否定', logic('not', logic('equal', quote(rain), quote(shelter)))),
        ('not-all', '否定の内側に全称', logic('not', quant('forall', 'x', call('rain', variable('x'))))),
        ('all-not', '全称の内側に否定', quant('forall', 'x', logic('not', call('rain', variable('x'))))),
        ('binding-outer-inner', '外側と内側の束縛', bound(logic('equal', variable('x'), variable('y')))),
        ('binding-inner-outer', '参照する束縛を交換', bound(logic('equal', variable('y'), variable('x')))),
        ('binding-inner-inner', '内側を二度参照', bound(logic('equal', variable('y'), variable('y')))),
        ('binding-outer-outer', '外側を二度参照', bound(logic('equal', variable('x'), variable('x')))),
        ('quote-scope', '引用ごとに束縛を閉じる', logic('equal',
            quote(quant('forall', 'x', call('rain', variable('x')))),
            quote(quant('exists', 'y', call('rain', variable('y')))))),
        ('binder-siblings', '隣の式の束縛を引き継がない', logic('and',
            quant('forall', 'x', call('rain', variable('x'))),
            quant('exists', 'y', call('rain', variable('y'))))),
        ('quote-nested', '入れ子の引用', logic('equal', quote(quote(town)), quote(quote(home)))),
    ]
    # Every existing public root occurs in a well-typed complete sentence.
    used = {'rain', 'town', 'home', 'above', 'give', 'birdone', 'treeone', 'aki', 'nao', 'book', 'red'}
    for name, entry in baseline_vocabulary().document()['entries'].items():
        if name not in used:
            rows.append(('root-'+name, name, call(name, *([call('book')]*len(entry['parameters'])))))
    return [(key, label, canonical(body)) for key, label, body in rows]


@lru_cache(maxsize=80)
def checked(index, branch=True, silent=True):
    key, label, source = cases()[index]
    compiled = compile_statement(source, branch=branch, silent=silent)
    svg = to_svg(compiled['shapes'])
    recovered = decode(from_svg(svg))
    if recovered != source:
        raise ValueError('Recovered native syntax differs: '+key)
    return dict(key=key, label=label, source=source, compiled=compiled, svg=svg)


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    cards = []
    for i in range(len(cases())):
        row = checked(i)
        (OUT/(row['key']+'.svg')).write_text(row['svg'], encoding='utf-8', newline='\n')
        cards.append('<section><h2>'+html.escape(row['label'])+'</h2><div class="ink">'+row['svg']+
                     '</div></section>')
    markup = '''<!doctype html><html lang="ja"><meta charset="utf-8"><title>公開語形と構文の局所試作</title>
<style>body{max-width:1500px;margin:24px auto;padding:20px;background:#f7f6f1;color:#203438;font:16px/1.8 "Yu Gothic",sans-serif}h1{font-size:26px}h2{font-size:17px}section{background:#fffffe;margin:16px 0;padding:18px}.ink{overflow:auto}.ink svg{height:115px;max-width:none}p{max-width:1100px}</style>
<h1>公開語形・引数順・引用・束縛をつないだ局所試作</h1>
<p>kant-pageの生成器にある三段の配置探索・円へ直角に接続する経路・面積重心の補償を使います。既存の16語は綴りと語義を再利用し、文頭の共通記号は追加していません。横枝は引数列の中央位置が終端項の場合に作ります。配置の付属情報を渡さず、実際のSVGから元の構文を読み戻しています。</p>
<p><strong>完成候補ではありません。</strong>全語彙・全構文、共有の融合、二円接触、行と頁の復号は未完です。変数は一つの範囲で二段まで、引用は順位0に限ります。下の検査例は違いを確かめるための短文で、kant-page全体の外観を評価する見本ではありません。</p>
<p><a href="../kant-port-flow-probe/index.html">同じカント40主張を元の生成器と比較する接続試作</a></p>
'''+''.join(cards)+'</html>\n'
    (OUT/'index.html').write_text(markup, encoding='utf-8', newline='\n')


def build_report():
    rows = [checked(i) for i in range(len(cases()))]
    plain = [checked(i, False) for i in range(len(cases()))]
    pins = ['scripts/kant_public_fragment.py', 'scripts/check_kant_public_fragment.py',
        'tests/test_kant_public_fragment.py', 'docs/kant-public-fragment.md',
        'scripts/kant_readable_flow.py', 'scripts/kant_flow_reader.py', 'scripts/kant_geometry_reader.py',
        'scripts/balanced_circle_script.py', 'scripts/branch_circle_script.py', 'scripts/circle_contact_script.py',
        'scripts/visible_lexical_script.py', 'scripts/visible_syntax_vocabulary.py',
        'scripts/visible_word_forms.py', 'scripts/visible_syntax_geometry.py',
        'scripts/check_visible_syntax.py', 'noema/constructed_discourse.py', 'noema/grammar.py',
        'noema/resources/visible-lexicon-v1.json', 'noema/resources/visible-vocabulary-v1.json',
        'noema/resources/visible-defined-vocabulary-v1.json',
        'concept/alphabet-concept.md', 'data/writing-freeze-v1.json']
    return dict(schema=VERSION, status='bounded-native-fragment-not-writing-freeze',
        public_roots=len(root_words()), public_words=len(words()), grammar_tokens=len(GRAMMAR), public_allographs=len(table()),
        reserved_public_root_forms=len(root_words()),
        exact_native_roundtrips=len(rows), main_only_roundtrips=len(plain),
        source_meanings_sha256=hashlib.sha256(json.dumps(vocabulary().document(),
            ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        cases=[dict(key=r['key'], circles=sum(s['kind']=='circle' for s in r['compiled']['shapes']),
                    side_dependencies=sum(g['side'] is not None for g in r['compiled']['groups']),
                    svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in rows],
        limits=['16 published roots, fixed binary logical operators, rank-zero quotation',
                'Individual variables: at most two binders per lexical scope',
                'Exact canonical native syntax required; no silent alpha-renaming of input',
                'Shared-subject fusion, tangent application, compound words and page decoding pending',
                'No new semantic judgment and no visual approval requested'],
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in pins})
