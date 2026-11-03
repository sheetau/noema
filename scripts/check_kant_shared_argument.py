"""Reversible shared unary arguments, including quotation and binding scopes."""
from functools import lru_cache
import hashlib
import html
import json
from pathlib import Path

from scripts.kant_public_fragment import compile_statement, decode, events, table, VERSION
from scripts.kant_public_lexicon import source_paths
from scripts.check_kant_public_fragment import canonical, cases as prior_cases, checked as prior_checked
from scripts.check_kant_public_words import checked as word_checked, identities, application_checked, application_cases
from scripts.check_visible_syntax import call, logic, quote, quant, variable
from scripts.visible_syntax_geometry import to_svg, from_svg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-shared-argument'


def pair(subject):
    return logic('and',call('red',subject),call('round',subject))


@lru_cache(maxsize=1)
def cases():
    book=call('book');x=variable('x');y=variable('y')
    rows=[
        ('book','一つの本について赤さと丸さを述べる',pair(book),True),
        ('town','同じ町を指す二つの降雨の適用',logic('and',call('rain',call('town')),call('rain',call('town'))),True),
        ('home','住まいを共有する',pair(call('home')),True),
        ('nearest','最寄りの束縛を共有する',quant('forall','x',pair(x)),True),
        ('inner','二重の束縛の内側を共有する',quant('forall','x',quant('exists','y',pair(y))),True),
        ('outer','外側の参照は大円なので主流に残す',quant('forall','x',quant('exists','y',pair(x))),False),
        ('different','対象が異なる場合は共有しない',logic('and',call('red',call('book')),call('round',call('home'))),False),
        ('two-arguments','二引数を単項述語として融合しない',logic('and',call('above',book,call('home')),call('above',book,call('home'))),False),
        ('left-associated','左側の二述語だけが共有する',logic('and',pair(book),call('bird',book)),True),
        ('right-associated','右側の二述語だけが共有する',logic('and',call('red',book),logic('and',call('round',book),call('bird',book))),True),
        ('quoted','引用内でも元の二適用を正確に戻す',logic('equal',quote(pair(book)),quote(pair(call('home')))),True),
        ('quoted-binder','引用ごとの束縛を共有する',logic('equal',quote(quant('forall','x',pair(x))),quote(quant('forall','y',pair(y)))),True),
    ]
    return [(key,label,canonical(body),fuses) for key,label,body,fuses in rows]


@lru_cache(maxsize=24)
def checked(index, sharing=True):
    key,label,source,fuses=cases()[index]
    compiled=compile_statement(source,sharing=sharing)
    svg=to_svg(compiled['shapes'])
    if decode(from_svg(svg))!=source:
        raise ValueError('Shared argument changed native syntax: '+key)
    fused=sum(e['token']=='and_shared' for e in events(source,sharing=sharing))
    if bool(fused)!=(fuses and sharing):
        raise ValueError('Unexpected sharing selection: '+key)
    return dict(key=key,label=label,source=source,compiled=compiled,svg=svg,fused=fused,
                circles=sum(s['kind']=='circle' for s in compiled['shapes']))


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    cards=[]
    for i in range(len(cases())):
        a,b=checked(i),checked(i,False)
        (OUT/(a['key']+'.svg')).write_text(a['svg'],encoding='utf-8',newline='\n')
        cards.append('<section><h2>'+html.escape(a['label'])+'</h2><div class="pair"><div><p>共有形</p>'+a['svg']+
            '</div><div><p>元の適用を省略せず描く形</p>'+b['svg']+'</div></div></section>')
    markup='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>共有引数の可逆な融合</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;max-width:1600px;margin:auto;padding:24px;background:#f7f6f1;color:#203438}h2{font-size:18px}section{padding:18px;background:#fffffe;margin:18px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}.pair>div{overflow:auto}svg{height:130px;max-width:none}</style>
<h1>同じ対象を二つの述語で共有する</h1>
<p>同じ対象への二つの単項述語適用を、共有を表す二円と対象の横枝でまとめます。二つの述語の順序と連言の結合順は残り、実図形から省略前のnative構文へ正確に戻せます。元の生成器の見えないfused_pathsには依存しません。</p>
<p>左右は同じ構文です。大円の参照・異なる対象・二引数の述語は融合しません。引用内では元の構文を正確に展開し、束縛環境は引用ごとに閉じます。</p>
<p><strong>まだ固定前の技術試作です。</strong>全構文、接触による適用、行・頁と倍率の復号、長文全体の外観確認が残ります。</p>
'''+''.join(cards)+'</html>\n'
    (OUT/'index.html').write_text(markup,encoding='utf-8',newline='\n')


def build_report():
    rows=[checked(i) for i in range(len(cases()))]
    explicit=[checked(i,False) for i in range(len(cases()))]
    prior=[prior_checked(i,branch) for i in range(len(prior_cases())) for branch in (True,False)]
    probes=[word_checked(i) for i in (0,47,188,len(identities())-1)]
    applications=[application_checked(i) for i in range(len(application_cases()))]
    pins=set(source_paths())|{
        'scripts/kant_public_fragment.py','scripts/check_kant_shared_argument.py',
        'scripts/check_kant_public_fragment.py','scripts/check_kant_public_words.py',
        'tests/test_kant_shared_argument.py','tests/test_kant_public_fragment.py','tests/test_kant_public_words.py',
        'docs/kant-shared-argument.md','scripts/kant_readable_flow.py','scripts/kant_flow_reader.py',
        'scripts/kant_geometry_reader.py','scripts/balanced_circle_script.py','scripts/branch_circle_script.py',
        'scripts/circle_contact_script.py','scripts/visible_syntax_geometry.py','scripts/check_visible_syntax.py',
        'concept/alphabet-concept.md','data/writing-freeze-v1.json','reports/kant-public-words-v1.json'}
    return dict(schema='kant-shared-argument-1',version=VERSION,status='reversible-local-fusion-not-writing-freeze',
        exact_native_roundtrips=len(rows)+len(explicit),prior_grammar_roundtrips=len(prior),
        lexical_boundary_application_regressions=[r['key'] for r in applications],
        reference_regression_probes=[r['name'] for r in probes],
        prior_complete_word_identity=dict(report='reports/kant-public-words-v1.json',commit='7db25d10',
            scope='375 references at that pinned version; current checks target sharing and lexical seam rail constraints'),
        public_shapes=len(table()),
        cases=[dict(key=a['key'],fused=a['fused'],circles_before=b['circles'],circles_after=a['circles'],
            svg_sha256=hashlib.sha256(a['svg'].encode()).hexdigest()) for a,b in zip(rows,explicit)],
        limits=['Binary conjunction of two unary individual predicates with one identical terminal argument',
                'Large or compound shared terms remain explicit; no implicit semantic equivalence',
                'No flat conjunction normalization; exact association and scope preserved',
                'General types, all native syntax, tangent application and page decoding remain incomplete'],
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(pins)})
