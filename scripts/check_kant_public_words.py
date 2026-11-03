"""Exact public identity in actual SVG for every root and compound word."""
from functools import lru_cache
import hashlib
import html
import json
from pathlib import Path

from scripts.kant_public_fragment import compile_statement, decode, events, GRAMMAR, VERSION
from scripts.kant_public_lexicon import words, root_words, vocabulary, parts_for, source_paths
from scripts.check_kant_public_fragment import canonical, checked as grammar_checked, cases as grammar_cases
from scripts.check_visible_syntax import logic, call, quote
from scripts.visible_syntax_geometry import to_svg, from_svg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/kant-public-words'


def named(name):
    return next(token for token, (word, _) in words().items() if word == name)


def shared_call(name, *args):
    return dict(kind='call', symbol=named(name), arguments=list(args))


@lru_cache(maxsize=1)
def identities():
    return tuple(words())


@lru_cache(maxsize=375)
def checked(index):
    token = identities()[index]
    reference = dict(kind='function_ref', symbol=token)
    source = canonical(logic('equal', reference, reference))
    compiled = compile_statement(source)
    svg = to_svg(compiled['shapes'])
    restored = decode(from_svg(svg))
    if restored != source:
        raise ValueError('Public reference identity differs: '+words()[token][0])
    return dict(name=words()[token][0], token=token, source=source, compiled=compiled, svg=svg)


@lru_cache(maxsize=1)
def application_cases():
    yes = shared_call('indicatorvalid')
    rain = call('rain', call('town'))
    return [
        ('compound-call', canonical(yes), True),
        ('compound-numeric-result', canonical(logic('equal',
            shared_call('truthindicator', rain), shared_call('truthindicator', yes))), True),
        ('root-boundary', canonical(logic('equal', call('book'), call('home'))), False),
        ('triple-boundary', canonical(call('give', call('book'), call('aki'), call('home'))), False),
        ('compound-function-result', canonical(logic('equal',
            shared_call('dimensionless'), shared_call('dimensionless'))), True),
        ('quoted-compound-call', canonical(logic('equal', quote(yes), quote(yes))), True),
    ]


@lru_cache(maxsize=6)
def application_checked(index):
    key, source, branch = application_cases()[index]
    compiled = compile_statement(source, branch=branch)
    svg = to_svg(compiled['shapes'])
    if decode(from_svg(svg)) != source:
        raise ValueError('Compound application differs: '+key)
    return dict(key=key, source=source, compiled=compiled, svg=svg,
                seams=sum(bool(e.get('lexical_seam')) for e in events(source, branch)))


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [application_checked(i) for i in range(len(application_cases()))]
    cards = []
    for row in rows:
        (OUT/(row['key']+'.svg')).write_text(row['svg'], encoding='utf-8', newline='\n')
        cards.append('<section><h2>'+html.escape(row['key'])+'</h2><div>'+row['svg']+'</div></section>')
    markup = '''<!doctype html><html lang="ja"><meta charset="utf-8"><title>公開された複合語を読む</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;background:#f7f6f1;color:#203438;max-width:1500px;margin:auto;padding:24px}section{background:#fffffe;padding:20px;margin:15px 0}h2{font-size:17px}section div{overflow:auto}svg{height:120px;max-width:none}</style>
<h1>共通の開始記号を加えずに、複合語を読む</h1>
<p>公開された30根語と345複合語の綴りを、そのまま円の構成として使います。既知の綴りを最長一致で読み、隣の語まで取り込む場合だけ、中心同士を結ぶ不可視の直線で語境界を置きます。語の付属番号や元の構文は読取器に渡しません。</p>
<p>375語すべてについて、実図形から関数参照先を保持したnative構文へ戻す検査を行います。これは全375語の全用法や、二作品の全文復号が完成したという意味ではありません。下は複合語の適用、返り値、引用、隣接語の境界を確かめる限定例です。</p>
<p>共有の融合、全構文、行・頁の復号は未完です。見た目の固定候補ではありません。</p>
'''+''.join(cards)+'</html>\n'
    (OUT/'index.html').write_text(markup, encoding='utf-8', newline='\n')


def build_report():
    rows = [checked(i) for i in range(len(identities()))]
    applications = [application_checked(i) for i in range(len(application_cases()))]
    # These cache hits reuse tests in this same project_work process.
    grammar = [grammar_checked(i, branch) for i in range(len(grammar_cases())) for branch in (True, False)]
    pins = set(source_paths()) | {
        'scripts/kant_public_fragment.py', 'scripts/check_kant_public_words.py',
        'scripts/check_kant_public_fragment.py', 'tests/test_kant_public_words.py',
        'tests/test_kant_public_fragment.py', 'docs/kant-public-words.md',
        'scripts/kant_readable_flow.py', 'scripts/kant_flow_reader.py', 'scripts/kant_geometry_reader.py',
        'scripts/balanced_circle_script.py', 'scripts/branch_circle_script.py', 'scripts/circle_contact_script.py',
        'scripts/visible_syntax_geometry.py', 'scripts/check_visible_syntax.py',
        'concept/alphabet-concept.md', 'data/writing-freeze-v1.json'}
    document = vocabulary().document()
    return dict(schema='kant-public-words-1', version=VERSION,
        status='public-identity-and-bounded-application-not-writing-freeze',
        roots=len(root_words()), compounds=len(words())-len(root_words()),
        reference_identity_roundtrips=len(rows), application_roundtrips=len(applications),
        prior_grammar_roundtrips=len(grammar),
        public_meanings_sha256=hashlib.sha256(json.dumps(document,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
        definitions=len(document['definitions']), primitives=len(document['primitives']),
        cases=[dict(name=r['name'],parts=len(parts_for()[r['token']]),
            svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in rows],
        application_cases=[dict(key=r['key'],lexical_seams=r['seams'],
            svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in applications],
        limits=['All published words checked as actual native function references; not all applications',
                'Existing definitions imported without changing their meaning',
                'No shared-subject fusion, arbitrary binding/type grammar, or row/page decoding yet',
                'No semantic-model rerun and no visual freeze'],
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(pins)})
