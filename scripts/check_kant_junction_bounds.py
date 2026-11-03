"""Compare old/new connector decisions on unchanged, actually decoded bodies."""
from functools import lru_cache
import hashlib,importlib.util,json,time
from scripts import kant_public_fragment as writing
from scripts.kant_readable_flow import route as indexed_route
from scripts.kant_passage_anchor_context import passage_context
from scripts.kant_page_public_context import ROOT,inputs
from scripts.kant_lexical_context import LexicalContext
from scripts.check_kant_passage_anchor_spellings import pins as prior_pins
from scripts.check_kant_multiple_arguments import syntax_hash
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.long_run import LongRun,atomic_json

OUT=ROOT/'output/kant-junction-bounds'
RUN=ROOT/'.noema-project/runs/kant-junction-bounds-v1'
OLD='output/kant-junction-prefix/kant_readable_flow.py'
BASELINE='reports/kant-passage-anchor-spellings-v1.json'
NUMBERS=(5,9)


def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def previous_route():
    if sha(OLD)!='d216161890a851ab93897bfe5785cebf8d5e0621be80dccc761e87e0b8fc31cf':
        raise ValueError('Previous junction implementation changed')
    spec=importlib.util.spec_from_file_location('kant_previous_junction_route',ROOT/OLD)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.route


def checked(number,indexed):
    source=next(r['public'] for r in inputs()['selected'] if r['statement']==number)
    context=passage_context()
    route=indexed_route if indexed else previous_route()
    saved=writing.route;writing.route=route
    try:
        started=time.perf_counter()
        drawing=writing.compile_statement(source,lexicon=context,multiple=True,overlap=True)
        seconds=time.perf_counter()-started
    finally:writing.route=saved
    svg=to_svg(drawing['shapes'])
    path='output/kant-passage-anchor-spellings/statement-'+str(number)+'.svg'
    baseline=read(BASELINE)
    if sha(path)!=baseline['source_sha256'][path]:raise ValueError('Saved spelling output changed')
    if svg!=(ROOT/path).read_text(encoding='utf-8'):
        raise ValueError('Connector optimization changed actual SVG')
    reader=LexicalContext.from_published(context.published())
    if writing.decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Connector optimization changed native syntax')
    return dict(statement=number,indexed=indexed,seconds=seconds,exact_svg=True,exact_native=True,
        svg_sha256=hashlib.sha256(svg.encode()).hexdigest(),syntax_sha256=syntax_hash(source),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing['unbranched_paths'])


def pins():
    result=prior_pins()
    names={OLD,BASELINE,'output/kant-junction-prefix/profile-summary.json',
        'scripts/kant_junction_index.py','scripts/check_kant_junction_bounds.py',
        'docs/kant-junction-bounds.md','tests/test_kant_junction_index.py','tests/test_kant_junction_layout.py',
        *('output/kant-passage-anchor-spellings/statement-'+str(n)+'.svg' for n in NUMBERS)}
    result.update({n:sha(n) for n in names})
    return dict(sorted(result.items()))


def prepare():
    source_pins=pins()
    with LongRun(RUN,dict(schema='kant-junction-bounds-1',source_sha256=source_pins),resume=RUN.exists()) as run:
        rows=[];completed=0
        for number in NUMBERS:
            variants=[]
            for indexed in (False,True):
                run.emit('progress',stage=('Indexed' if indexed else 'Legacy')+' route on body '+str(number),completed=completed,total=4)
                variants.append(run.step(str(number)+'-'+str(indexed),dict(statement=number,indexed=indexed),
                    lambda number=number,indexed=indexed:checked(number,indexed)))
                completed+=1
            old,new=variants
            if old['svg_sha256']!=new['svg_sha256']:raise ValueError('Old/new SVG differ')
            rows.append(dict(statement=number,old=old,new=new,observed_speedup=old['seconds']/new['seconds']))
        if pins()!=source_pins:raise ValueError('Junction inputs changed during comparison')
        OUT.mkdir(parents=True,exist_ok=True)
        profile=read('output/kant-junction-prefix/profile-summary.json')
        atomic_json(OUT/'structural-report.json',dict(schema='kant-junction-bounds-1',cases=rows,
            bounded_profile=dict(statement=profile['statement'],complete_body=profile['complete_body'],
                seconds=profile['seconds'],route_calls=profile['route_calls']),
            source_sha256=source_pins,limits=[
                'The ellipse broad phase only rejects impossible endpoint membership; retained pairs use the legacy predicate',
                'Coordinates outside the bounded finite numeric range use the full legacy checks',
                'Two complete actual bodies, one timing pair each; observed speed is not a corpus-wide guarantee',
                'The bounded 120-second body-35 profile produced no completed body or SVG',
                'No new semantic judgments, changed geometry, or full-history audit']))
        run.emit('progress',stage='Junction comparison saved',completed=4,total=4)


def build_report():
    result=read(OUT/'structural-report.json')
    if any(result['source_sha256'].get(n)!=h for n,h in pins().items()):
        raise ValueError('Junction implementation changed')
    if any(sha(n)!=h for n,h in result['source_sha256'].items()):
        raise ValueError('Junction evidence changed')
    return result
