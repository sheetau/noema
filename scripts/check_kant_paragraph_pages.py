"""Compose a real page prefix and distinguishing rejection/budget boundaries."""
from functools import lru_cache
import hashlib, json
from scripts import kant_paragraph_pages as layout, kant_ordered_pages as pages
from scripts import kant_public_fragment as writing
from scripts.kant_incremental_dictionary import Reader, PublishedStatementReader
from scripts.kant_page_public_context import ROOT, inputs
from scripts.check_kant_saved_item_join import pins as prior_pins, saved, PREFIX, BASELINE, DICTIONARY
from scripts.check_kant_statements import call
from scripts.visible_syntax_geometry import from_svg, to_svg
from scripts.long_run import LongRun, atomic_json

OUT = ROOT/'output/kant-paragraph-pages'
RUN = ROOT/'.noema-project/runs/kant-paragraph-pages-v1'


@lru_cache(maxsize=1)
def fixtures():
    published = json.loads(saved(DICTIONARY, BASELINE))
    source = {r['statement']: r['public'] for r in inputs()['selected']}
    ink = [from_svg(saved(f'output/kant-forty-body-prefix/statement-{n}.svg', PREFIX).decode('utf-8')) for n in (1, 2, 3, 4)]
    small = [dict(kind='assert', body=call(name, call('book'))) for name in ('red', 'round')]
    small_ink = [writing.compile_statement(s)['shapes'] for s in small]
    return [dict(key='kant-prefix', paragraphs=[[ink[0]], ink[1:]], reader=PublishedStatementReader(published),
        records=[source[n] for n in (1, 2, 3, 4)], width=1420/.53, height=900., budget=256),
        dict(key='unavailable-junction', paragraphs=[small_ink], reader=Reader(), records=small,
            width=400., height=900., budget=256),
        dict(key='bounded-flow', paragraphs=[ink[1:]], reader=PublishedStatementReader(published),
            records=[source[n] for n in (2, 3, 4)], width=1420/.53, height=900., budget=80)]


def checked(index, checkpoint=None):
    fixture = fixtures()[index]
    reader = fixture['reader']
    expected = reader.fork()
    for record in fixture['records']:
        expected.register(record)
    composed = layout.compose(fixture['paragraphs'], reader=reader,
        row_width=fixture['width'], page_height=fixture['height'], circle_budget=fixture['budget'], checkpoint=checkpoint)
    if composed.pop('expected') != expected.result(True):
        raise ValueError('Independent input reading differs from the saved native source')
    svgs = [to_svg(s) for s in composed.pop('pages')]
    recovered = pages.decode_pages([list(reversed(from_svg(s))) for s in svgs], reader=reader, include_spellings=True)
    if recovered != expected.result(True):
        raise ValueError('Actual paragraph pages changed source item order, bindings or references')
    return dict(key=fixture['key'], page_svgs=svgs, items=len(fixture['records']), exact=True, **composed)


def pins():
    result = prior_pins()
    names = {'scripts/kant_paragraph_pages.py', 'scripts/check_kant_paragraph_pages.py',
        'tests/test_kant_paragraph_pages.py', 'docs/kant-paragraph-pages.md',
        'reports/kant-saved-item-join-v2.json', 'output/kant-forty-body-prefix/statement-1.svg'}
    result.update({n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    source_pins = pins()
    with LongRun(RUN, dict(schema='kant-paragraph-pages-1', source_sha256=source_pins), resume=RUN.exists()) as run:
        results = []
        for index, fixture in enumerate(fixtures()):
            run.emit('progress', stage='Compose and recover paragraph pages', completed=index, total=3)
            def checkpoint(key, inputs, action):
                return run.step(fixture['key']+'/'+key, inputs, action)
            results.append(checked(index, checkpoint))
        if pins() != source_pins:
            raise ValueError('Paragraph inputs changed')
        OUT.mkdir(parents=True, exist_ok=True)
        cards = []
        for result in results:
            section = []
            for index, svg in enumerate(result['page_svgs']):
                path = OUT/(result['key']+'-page-'+str(index+1)+'.svg')
                path.write_text(svg, encoding='utf-8', newline='\n')
                source_pins[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
                section.append('<div class="page">'+svg+'</div>')
            cards.append('<section><h2>'+result['key']+'</h2>'+''.join(section)+'</section>')
        (OUT/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>段落・ページの点検</title>'
            '<style>body{margin:24px;background:#f7f6f1;color:#203438;font:16px sans-serif}.page{background:white;padding:20px;margin:24px 0}svg{max-width:100%;height:auto}</style>'
            '<h1>保存図形から段落とページを組む</h1><p>実本文の先頭4項目と境界の対照例です。全40項目・完成外観ではありません。</p>'
            +''.join(cards)+'</html>\n', encoding='utf-8', newline='\n')
        atomic_json(OUT/'structural-report.json', dict(schema='kant-paragraph-pages-1', diagnostics=results,
            source_sha256=dict(sorted(source_pins.items())), limits=[
                'Real first four source items plus unavailable-junction and circle-budget controls',
                'Paragraph whitespace is presentation; native decoding does not recover source paragraph identifiers',
                'No compression or final appearance approval; whole 40-item multiple layout is still running']))
        run.emit('progress', stage='Paragraph report saved', completed=3, total=3)


def build_report():
    result = json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))
    if any(result['source_sha256'].get(n) != stamp for n, stamp in pins().items()):
        raise ValueError('Paragraph implementation changed')
    if any(hashlib.sha256((ROOT/n).read_bytes()).hexdigest() != stamp for n, stamp in result['source_sha256'].items()):
        raise ValueError('Paragraph evidence changed')
    return result
