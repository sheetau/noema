"""Measure the exact old circle cost, then check shorter reference ink locally."""
from functools import lru_cache
from collections import Counter
import hashlib, json, time
from scripts import kant_public_fragment as writing
from scripts.kant_reference_anchor_context import anchor_context, previous_context, SPELLINGS, BASELINE, DICTIONARY
from scripts.kant_page_public_context import ROOT, inputs, load_semantic_spellings
from scripts.kant_lexical_context import use_context, LexicalContext
from scripts.visible_syntax_geometry import from_svg, to_svg
from scripts.check_kant_paragraph_pages import pins as prior_pins
from scripts.check_kant_multiple_arguments import measure, syntax_hash
from scripts.long_run import LongRun, atomic_json

OUT = ROOT/'output/kant-reference-anchor-spellings'
RUN = ROOT/'.noema-project/runs/kant-reference-anchor-spellings-v1'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def circle_cost(stream, context):
    roots = Counter()
    grammar = Counter()
    def glyph(token):
        sizes = {sum(s['kind']=='circle' for s in form['shapes']) for form in writing.forms(token)}
        if len(sizes) != 1:
            raise ValueError('Allograph-dependent circle count needs actual placement')
        count = sizes.pop()
        (roots if token in writing.root_words() else grammar)[token] += count
    def walk(chain):
        for event in chain:
            glyph(event['token'])
            for side in writing.event_sides(event):
                if isinstance(side, str):
                    for token in context.parts[side]:
                        glyph(token)
                else:
                    walk(side)
    walk(stream)
    return dict(circles=sum(roots.values())+sum(grammar.values()),
        roots=dict(roots), grammar=dict(grammar))


def density(index):
    row = inputs()['selected'][index]
    old = read(BASELINE)['cases'][index]
    if row['statement'] != old['statement'] or syntax_hash(row['public']) != old['syntax_sha256']:
        raise ValueError('Density source differs from the saved public syntax')
    path = 'output/kant-presentation-spellings/statement-'+str(row['statement'])+'.svg'
    if sha(path) != read(BASELINE)['source_sha256'][path]:
        raise ValueError('Saved density SVG changed')
    actual = sum(s['kind']=='circle' for s in from_svg((ROOT/path).read_text(encoding='utf-8')))
    options = dict(multiple=False, unbranched={tuple(p) for p in old['unbranched_paths']}, nested=old['layout']!='serial-fallback')
    streams = []
    costs = []
    for context in (previous_context(), anchor_context()):
        with use_context(context):
            stream = writing.events(row['public'], **options)
            streams.append(stream)
            costs.append(circle_cost(stream, context))
    if costs[0]['circles'] != actual or actual != old['circles']:
        raise ValueError('Token accounting does not explain the actual saved circles')
    return dict(statement=row['statement'], saved_circles=actual, before=costs[0], predicted_after=costs[1],
        changed_events=streams[0]!=streams[1], syntax_sha256=old['syntax_sha256'])


def word_case(name):
    token = inputs()['bridge']['mapping'][name]
    term = dict(kind='call', symbol=token, arguments=[])
    source = dict(kind='assert', body=dict(kind='equal', arguments=[term, term]))
    before = writing.compile_statement(source, lexicon=previous_context(), multiple=True)
    after = writing.compile_statement(source, lexicon=anchor_context(), multiple=True)
    old_svg, svg = to_svg(before['shapes']), to_svg(after['shapes'])
    reader = LexicalContext.from_published(anchor_context().published())
    if writing.decode(list(reversed(from_svg(svg))), lexicon=reader) != source:
        raise ValueError('Short reference changed a native symbol')
    return dict(key=name, source=source, svg=svg, previous_svg=old_svg,
        before_circles=measure(old_svg)['circles'], after_circles=measure(svg)['circles'], exact=True,
        limit='Lexical identity diagnostic, not an additional original-source assertion')


def body_case():
    source = inputs()['selected'][1]['public']
    started = time.perf_counter()
    drawing = writing.compile_statement(source, lexicon=anchor_context(), multiple=True)
    svg = to_svg(drawing['shapes'])
    reader = LexicalContext.from_published(anchor_context().published())
    if writing.decode(list(reversed(from_svg(svg))), lexicon=reader) != source:
        raise ValueError('Short reference changed actual source body 2')
    old = read(BASELINE)['cases'][1]
    if syntax_hash(source) != old['syntax_sha256']:
        raise ValueError('Body source changed')
    return dict(key='statement-2', svg=svg, source=source, seconds=time.perf_counter()-started,
        syntax_sha256=syntax_hash(source), before_circles=old['circles'],
        branch_limits=drawing.get('branch_limits', []), unbranched_paths=drawing['unbranched_paths'],
        exact=True, **measure(svg))


def pins():
    result = prior_pins()
    _, basis = load_semantic_spellings(SPELLINGS)
    names = {*basis, BASELINE, DICTIONARY, SPELLINGS,
        'scripts/kant_reference_anchor_context.py', 'scripts/check_kant_reference_anchor_spellings.py',
        'tests/test_kant_reference_anchor_spellings.py', 'docs/kant-reference-anchor-spellings.md',
        *('output/kant-presentation-spellings/statement-'+str(r['statement'])+'.svg' for r in read(BASELINE)['cases'])}
    result.update({n:sha(n) for n in names})
    return dict(sorted(result.items()))


def prepare():
    source_pins = pins()
    names = list(read(SPELLINGS)['entries'])
    with LongRun(RUN, dict(schema='kant-reference-anchor-spellings-1', source_sha256=source_pins), resume=RUN.exists()) as run:
        costs = []
        for index in range(40):
            run.emit('progress', stage='Account for saved circles and changed event streams', completed=index, total=40)
            costs.append(run.step('density-'+str(index), dict(index=index), lambda index=index:density(index)))
        cases = []
        for index, name in enumerate(names):
            run.emit('progress', stage='Read seven shortened reference spellings', completed=index, total=len(names))
            cases.append(run.step('word-'+name, dict(name=name), lambda name=name:word_case(name)))
        run.emit('progress', stage='Draw and recover actual source body 2', completed=0, total=1)
        body = run.step('actual-body-2', {}, body_case)
        if pins() != source_pins:
            raise ValueError('Reference spelling inputs changed')
        OUT.mkdir(parents=True, exist_ok=True)
        cards = []
        for row in [*cases, body]:
            path = OUT/(row['key']+'.svg')
            path.write_text(row['svg'], encoding='utf-8', newline='\n')
            source_pins[path.relative_to(ROOT).as_posix()] = sha(path)
            if 'previous_svg' in row:
                prior = OUT/(row['key']+'-before.svg')
                prior.write_text(row['previous_svg'], encoding='utf-8', newline='\n')
                source_pins[prior.relative_to(ROOT).as_posix()] = sha(prior)
            cards.append('<section><h2>'+row['key']+'</h2>'+row.get('previous_svg','')+row['svg']+'</section>')
        dictionary = OUT/'dictionary.json'
        atomic_json(dictionary, anchor_context().published())
        source_pins[dictionary.relative_to(ROOT).as_posix()] = sha(dictionary)
        (OUT/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>既存参照名の短い綴り</title>'
            '<style>body{margin:24px;background:#f7f6f1;font:16px sans-serif;color:#203438}section{padding:20px;background:white;margin:20px 0;overflow:auto}svg{height:120px;max-width:none}</style>'
            '<h1>既存参照名の短い綴り</h1><p>語の同定用の対照例と実本文第2項目です。全40項目の再配置・外観固定ではありません。</p>'
            +''.join(cards)+'</html>\n', encoding='utf-8', newline='\n')
        atomic_json(OUT/'structural-report.json', dict(schema='kant-reference-anchor-spellings-1',
            density=costs, words=[{k:v for k,v in r.items() if k not in ('svg','previous_svg','source')} for r in cases],
            actual_body={k:v for k,v in body.items() if k not in ('svg','source')},
            saved_circles=sum(r['saved_circles'] for r in costs),
            predicted_circles=sum(r['predicted_after']['circles'] for r in costs),
            saved_root_circles=sum(sum(r['before']['roots'].values()) for r in costs),
            saved_grammar_circles=sum(sum(r['before']['grammar'].values()) for r in costs),
            changed_statements=[r['statement'] for r in costs if r['changed_events']],
            source_sha256=dict(sorted(source_pins.items())), limits=[
                'Density accounting covers all 40 saved baseline SVGs; new 40-body geometry is not complete',
                'Circle predictions keep baseline branch choices; new multiple placement may make different choices',
                'Seven lexical controls and actual body 2 only; no new semantic judgments',
                'Existing alias mappings retained; prefix boundaries and affected drawings must still be checked',
                'No final appearance approval or freeze']))
        run.emit('progress', stage='Reference spelling report saved', completed=1, total=1)


def build_report():
    result = read(OUT/'structural-report.json')
    if any(result['source_sha256'].get(n)!=stamp for n,stamp in pins().items()):
        raise ValueError('Reference spelling implementation changed')
    if any(sha(n)!=stamp for n,stamp in result['source_sha256'].items()):
        raise ValueError('Reference spelling evidence changed')
    return result
