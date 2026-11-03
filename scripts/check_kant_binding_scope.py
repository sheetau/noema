"""Visible outward binding references and preservation of the last 40 SVGs."""
from functools import lru_cache
import hashlib
import html
import json
from pathlib import Path

from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call, logic, quant, variable, quote
from scripts.kant_public_fragment import compile_statement, decode, events, VERSION
from scripts.kant_lexical_context import LexicalContext
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.long_run import LongRun, atomic_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/kant-binding-scope'
BASELINE = 'reports/kant-lexical-contact-v1.json'
RUN = ROOT/'.noema-project/runs/kant-binding-scope-v2'


def nested(names, body):
    for i, name in reversed(list(enumerate(names))):
        body = quant('forall' if i % 2 == 0 else 'exists', name, body)
    return body


def abstraction(name, body):
    return dict(kind='lambda', parameters=[dict(name=name, sort='individual')], body=body)


@lru_cache(maxsize=1)
def cases():
    rows = []
    for depth in (3, 5):
        names = ('a', 'b', 'c', 'd', 'e')[:depth]
        for slot, name in enumerate(names):
            rows.append((f'depth-{depth}-slot-{slot}', f'{depth}段の第{slot+1}束縛への参照',
                         nested(names, call('rain', variable(name)))))
    for order in (('a','b','c'), ('c','b','a'), ('b','a','c')):
        rows.append(('order-'+''.join(order), '三つの引数の参照順 '+''.join(order),
                     nested(('a','b','c'), call('give', *(variable(n) for n in order)))))
    rows += [
        ('lambda-outer', 'lambdaの内側から外側の量化変数を参照', nested(('a','b','c'),
            logic('equal', abstraction('d', variable('a')), abstraction('e', variable('e'))))),
        ('quote-reset', '引用ごとに束縛の範囲を作り直す', nested(('a','b','c'), logic('equal',
            quote(nested(('x','y','z'), call('above', variable('x'), variable('z')))),
            quote(nested(('x','y','z'), call('above', variable('z'), variable('x'))))))),
        ('ranked-quote', '順位付き引用内の外側参照', logic('equal',
            dict(quote(nested(('x','y','z'), call('rain', variable('x')))), rank=2),
            dict(quote(nested(('x','y','z'), call('rain', variable('z')))), rank=2))),
        ('shadowing', '同名の内側束縛と外側の別変数', nested(('x','y','x'),
            call('above', variable('x'), variable('y')))),
        ('siblings', '隣の式の束縛を引き継がない', logic('and',
            nested(('a','b','c'), call('rain', variable('a'))),
            nested(('a','b','c'), call('rain', variable('c'))))),
    ]
    return [(key, label, canonical(body)) for key, label, body in rows]


@lru_cache(maxsize=32)
def checked(index):
    key, label, source = cases()[index]
    drawing = compile_statement(source)
    svg = to_svg(drawing['shapes'])
    recovered = decode(list(reversed(from_svg(svg))))
    if recovered != source:
        raise ValueError('Binding reference changed: '+key)
    return dict(key=key, label=label, svg=svg, source=source,
                shifts=sum(e['token']=='bound_shift' for e in events(source)),
                syntax_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest())


@lru_cache(maxsize=1)
def baseline():
    report = json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    directory = ROOT/'output/kant-lexical-contact'
    reader = LexicalContext.from_published(json.loads((directory/'dictionary.json').read_text(encoding='utf-8')))
    return report, directory, reader


@lru_cache(maxsize=40)
def preserved(index):
    report, directory, reader = baseline()
    row = report['cases'][index]
    name = (directory/('statement-'+str(row['statement'])+'.svg')).relative_to(ROOT).as_posix()
    raw = (ROOT/name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != report['source_sha256'][name]:
        raise ValueError('Previous SVG changed: '+name)
    recovered = decode(from_svg(raw.decode('utf-8')), lexicon=reader)
    stamp = hashlib.sha256(json.dumps(recovered,sort_keys=True).encode()).hexdigest()
    if stamp != row['syntax_sha256']:
        raise ValueError('Previous binding or syntax changed: '+name)
    return dict(statement=row['statement'], syntax_sha256=stamp)


def pins():
    # Reuse the production dependency list, not its historical code hashes.
    from scripts.check_kant_lexical_contact import pins as prior_pins
    result = prior_pins()
    names = {BASELINE, 'scripts/check_kant_binding_scope.py', 'tests/test_kant_binding_scope.py'}
    names.update(n for n in baseline()[0]['source_sha256'] if n.startswith('output/kant-lexical-contact/'))
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    dictionary = 'output/kant-lexical-contact/dictionary.json'
    if result[dictionary] != baseline()[0]['source_sha256'][dictionary]:
        raise ValueError('Previous public dictionary changed')
    return dict(sorted(result.items()))


def prepare():
    source_pins = pins()
    with LongRun(RUN, dict(schema='kant-binding-scope-run-1',source_sha256=source_pins), resume=RUN.exists()) as run:
        rows = []
        for i, (key, _, source) in enumerate(cases()):
            run.emit('progress',stage='Decode binding diagnostics',completed=i,total=len(cases()))
            rows.append(run.step(key, source, lambda i=i: checked(i)))
        old = []
        for i, row in enumerate(baseline()[0]['cases']):
            run.emit('progress',stage='Read preserved SVGs',completed=i,total=40)
            old.append(run.step('preserved-'+str(row['statement']), row, lambda i=i: preserved(i)))
        if pins() != source_pins:
            raise ValueError('Inputs changed during binding checks')
        OUT.mkdir(parents=True,exist_ok=True)
        cards=[]
        for row in rows:
            name=row['key']+'.svg'
            (OUT/name).write_text(row['svg'],encoding='utf-8',newline='\n')
            source_pins[(OUT/name).relative_to(ROOT).as_posix()]=hashlib.sha256(row['svg'].encode()).hexdigest()
            cards.append('<section><h2>'+html.escape(row['label'])+'</h2><div>'+row['svg']+'</div></section>')
        markup='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>束縛参照の共通規則</title>
<style>body{font:16px/1.8 sans-serif;max-width:1500px;margin:auto;padding:24px;background:#f7f6f1}section{background:white;padding:16px;margin:16px 0}section div{overflow:auto}svg{height:130px;max-width:none}h2{font-size:17px}</style>
<h1>外側への束縛参照</h1><p>直近と一つ外側の字形を保ち、それより外側は参照範囲を一段狭める接頭形で表します。引用では範囲を作り直します。以下は読取を区別するための検査例で、完成版の外観見本ではありません。</p>'''+''.join(cards)+'</html>\n'
        (OUT/'index.html').write_text(markup,encoding='utf-8',newline='\n')
        atomic_json(OUT/'structural-report.json', dict(schema='kant-binding-scope-1',version=VERSION,
            diagnostics=[{k:v for k,v in r.items() if k not in ('svg','source')} for r in rows],
            preserved_svg_syntax=old,source_sha256=dict(sorted(source_pins.items())),
            limits=['Individual quantifiers and single-parameter individual lambdas only',
                    'Recursive reference rule; native depth and drawing resource budgets still apply',
                    'Structural binding diagnostics, not a full-domain semantic proof or visual freeze']))
        run.emit('progress',stage='Binding report saved',completed=len(rows)+len(old),total=len(rows)+len(old))


def build_report():
    report=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))
    if any(report['source_sha256'].get(n)!=v for n,v in pins().items()):
        raise ValueError('Binding implementation changed')
    for name,stamp in report['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=stamp:
            raise ValueError('Binding artifact changed: '+name)
    return report
