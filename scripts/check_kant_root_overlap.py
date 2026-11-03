"""Small structural controls for legal, compositional root overlaps."""
from functools import lru_cache
import hashlib
import importlib.util
import json
import re
import time

from scripts import kant_public_fragment as writing
from scripts.kant_root_overlap import _templates, nucleus_tokens
from scripts.kant_lexical_context import LexicalContext, use_context
from scripts.kant_geometry_rules import check_circle_pairs
from scripts.kant_page_public_context import ROOT, inputs
from scripts.kant_reference_anchor_context import anchor_context
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call, logic, quant, variable, quote
from scripts.check_kant_multiple_arguments import measure, syntax_hash
from scripts.visible_word_forms import Word, symbol
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.long_run import LongRun, atomic_json

OUT = ROOT/'output/kant-root-overlap'
RUN = ROOT/'.noema-project/runs/kant-root-overlap-v1'
BASELINE = 'reports/kant-reference-anchor-spellings-v1.json'
SAVED = 'output/kant-reference-anchor-spellings/statement-2.svg'
PREFIX = 'output/kant-root-overlap-prefix/'


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def fixture():
    # Reusable above definitions are diagnostics, never new source primitives.
    names = [symbol(Word('compound', parts), writing.vocabulary()) for parts in
        [('book','give','inside','book'), ('above','book','nao')]]
    declarations = [dict(kind='definition', name=name,
        parameters=[dict(name=n, sort='individual') for n in ('x','y')], result='truth',
        body=call('above', variable('x'), variable('y'))) for name in names]
    context = LexicalContext(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=declarations, statements=[]), compact=False)
    return context, names


@lru_cache(maxsize=1)
def cases():
    context, names = fixture()
    def invoke(name, *args):
        return dict(kind='call', symbol=name, arguments=list(args))
    a, b = call('aki'), call('book')
    bound = quant('forall','x', quant('exists','y', invoke(names[0],variable('x'),variable('y'))))
    swapped = quant('forall','x', quant('exists','y', invoke(names[0],variable('y'),variable('x'))))
    rows = [('two-pairs', invoke(names[0],a,b)), ('reverse-pair', invoke(names[1],a,b)),
        ('swapped', invoke(names[0],b,a)), ('bound', bound),
        ('quoted', logic('equal',quote(bound),quote(swapped))),
        ('branch', logic('and',call('red',a),invoke(names[0],a,b)))]
    with use_context(context):
        return [(key,canonical(body)) for key,body in rows]


def overlaps(shapes):
    geometry = writing.read_geometry(shapes)
    flow = writing.decompose_flow(geometry, terminal_words=True, branch_seams=True,
        large_branches=True, local_continuation=True, nested_branches=True, multiple_branches=True)
    return sum(len(nucleus_tokens(geometry,n)[0])==2 for n in flow['nuclei'])


def inventory():
    rows=[]
    for a in writing.root_words():
        for b in writing.root_words():
            for index,glyph in enumerate(_templates(a,b)):
                shapes=list(reversed(from_svg(to_svg(glyph['shapes']))))
                geometry=writing.read_geometry(shapes)
                actual=nucleus_tokens(geometry,dict(circles=list(range(len(geometry['circles'])))))[0]
                if actual!=(a,b):raise ValueError('Root order changed')
                rows.append(dict(first=a,second=b,variant=index,exact=True))
    return rows


@lru_cache(maxsize=1)
def old_reader():
    path=ROOT/PREFIX/'kant_public_fragment.py'
    if sha(path)!='ba61013d6358adc60e69291996551a8f9ff51e587d47eb714f3d633f4eb7dea0':
        raise ValueError('Saved reader changed')
    spec=importlib.util.spec_from_file_location('kant_root_overlap_previous',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def checked(index):
    key,source=cases()[index];context,_=fixture()
    before=writing.compile_statement(source,lexicon=context,multiple=True)
    after=writing.compile_statement(source,lexicon=context,multiple=True,overlap=True)
    old_svg,svg=to_svg(before['shapes']),to_svg(after['shapes'])
    reader=LexicalContext.from_published(context.published())
    if writing.decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Overlapping word changed syntax: '+key)
    legacy=from_svg(old_svg)
    if old_reader().decode(legacy,lexicon=reader)!=source or writing.decode(legacy,lexicon=reader)!=source:
        raise ValueError('Legacy syntax changed: '+key)
    return dict(key=key,svg=svg,previous_svg=old_svg,exact=True,
        overlaps=overlaps(from_svg(svg)),before_width=before['width'],width=after['width'],
        before_circles=measure(old_svg)['circles'],branch_limits=after.get('branch_limits',[]),
        unbranched_paths=after['unbranched_paths'],syntax_sha256=syntax_hash(source),**measure(svg))


def body_case():
    previous=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    if sha(SAVED)!=previous['source_sha256'][SAVED]:raise ValueError('Saved body changed')
    source=inputs()['selected'][1]['public'];context=anchor_context()
    if syntax_hash(source)!=previous['actual_body']['syntax_sha256']:raise ValueError('Source changed')
    old_svg=(ROOT/SAVED).read_text(encoding='utf-8')
    reader=LexicalContext.from_published(context.published())
    if old_reader().decode(from_svg(old_svg),lexicon=reader)!=source:
        raise ValueError('Saved source does not match the old decoder')
    if writing.decode(from_svg(old_svg),lexicon=reader)!=source:
        raise ValueError('New decoder changed saved source')
    started=time.perf_counter()
    drawing=writing.compile_statement(source,lexicon=context,multiple=True,overlap=True)
    svg=to_svg(drawing['shapes'])
    if writing.decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Overlap changed actual source body 2')
    from scripts.kant_folded_flow import _bounds
    left,right=_bounds(from_svg(old_svg));new_left,new_right=_bounds(from_svg(svg))
    return dict(key='statement-2',svg=svg,previous_svg=old_svg,exact=True,
        seconds=time.perf_counter()-started,overlaps=overlaps(from_svg(svg)),
        before_width=right-left,width=new_right-new_left,
        before_circles=measure(old_svg)['circles'],syntax_sha256=syntax_hash(source),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def saved_page():
    page=(ROOT/'output/kant-shared-argument/index.html').read_text(encoding='utf-8')
    svgs=re.findall(r'<svg\b.*?</svg>',page,re.S)
    for svg in svgs:check_circle_pairs(from_svg(svg))
    return dict(svg_count=len(svgs),circles=sum(sum(s['kind']=='circle' for s in from_svg(svg)) for svg in svgs),legal=True)


def pins():
    from scripts.check_kant_reference_anchor_spellings import pins as prior_pins
    result=prior_pins()
    names=[BASELINE,SAVED,'output/kant-shared-argument/index.html',
        'scripts/kant_root_overlap.py','scripts/check_kant_root_overlap.py',
        'tests/test_kant_root_overlap.py','docs/kant-root-overlap.md',
        *(PREFIX+n for n in ('kant_public_fragment.py','kant_saved_item_join.py','kant_interleaved_layout.py'))]
    result.update({n:sha(n) for n in names})
    return dict(sorted(result.items()))


def prepare():
    source_pins=pins()
    with LongRun(RUN,dict(schema='kant-root-overlap-1',source_sha256=source_pins),resume=RUN.exists()) as run:
        run.emit('progress',stage='Legal root pair inventory',completed=0,total=8)
        shapes=run.step('inventory',{},inventory)
        rows=[]
        for i,(key,_) in enumerate(cases()):
            run.emit('progress',stage='Small syntax control: '+key,completed=i+1,total=8)
            rows.append(run.step('control-'+key,dict(index=i),lambda i=i:checked(i)))
        run.emit('progress',stage='Actual source body 2',completed=7,total=8)
        body=run.step('body-2',{},body_case)
        if pins()!=source_pins:raise ValueError('Inputs changed during overlap checks')
        OUT.mkdir(parents=True,exist_ok=True)
        cards=[]
        for row in [*rows,body]:
            for suffix,field in [('', 'svg'),('-before','previous_svg')]:
                path=OUT/(row['key']+suffix+'.svg')
                path.write_text(row[field],encoding='utf-8',newline='\n')
                source_pins[path.relative_to(ROOT).as_posix()]=sha(path)
            cards.append('<section><h2>'+row['key']+'</h2><p>分離形</p>'+row['previous_svg']+'<p>重ねた形</p>'+row['svg']+'</section>')
        (OUT/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>語内部の合法な重なり</title>'
            '<style>body{font:16px sans-serif;background:#f7f6f1;color:#203438;margin:24px}section{overflow:auto;padding:20px;margin:20px 0;background:white}svg{height:130px;max-width:none}</style>'
            '<h1>語内部の合法な重なり</h1><p>同じ根語形の円サイズと線方向を保つ配置試作。全体の完成候補・外観固定ではありません。</p>'
            +''.join(cards)+'</html>\n',encoding='utf-8',newline='\n')
        def summary(row):return {k:v for k,v in row.items() if k not in ('svg','previous_svg')}
        atomic_json(OUT/'structural-report.json',dict(schema='kant-root-overlap-1',
            root_variants=shapes,cases=[summary(r) for r in rows],actual_body=summary(body),
            shared_argument_page=saved_page(),source_sha256=dict(sorted(source_pins.items())),
            limits=['Optional word-internal overlap only; encoding defaults remain unchanged',
                'Circle counts are unchanged; width reduction is measured, not guaranteed for every layout',
                'Full-name headers and spelling right-hand sides remain explicit',
                'Six structural controls and one actual source item; no whole-corpus or semantic-model claim',
                'No final appearance approval or freeze']))
        run.emit('progress',stage='Overlap report saved',completed=8,total=8)


def build_report():
    result=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))
    if any(result['source_sha256'].get(n)!=h for n,h in pins().items()):
        raise ValueError('Overlap implementation changed')
    if any(sha(n)!=h for n,h in result['source_sha256'].items()):
        raise ValueError('Overlap evidence changed')
    return result
