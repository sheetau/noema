"""Local fork ordering, scheduled placement, and exact reads of saved SVGs."""
from functools import lru_cache
import hashlib,json,time

from scripts.check_kant_expression_branches import fixture,cases,pins as prior_pins,ROOT
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report
from scripts.check_kant_terminal_words import prepare_trial,build_report as page_report
from scripts.kant_page_public_context import inputs,framing_context
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg

OUT=ROOT/'output/kant-local-continuation'
RUN=ROOT/'.noema-project/runs/kant-local-continuation-v1'
BASELINE='reports/kant-expression-branches-v2.json'
PREVIOUS=ROOT/'output/kant-expression-branches-v2'


def syntax_hash(source):return hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()


@lru_cache(maxsize=1)
def baseline():
    return json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def reader():return LexicalContext.from_published(framing_context().published())


@lru_cache(maxsize=40)
def preserved(index):
    row=baseline()['cases'][index];name=PREVIOUS/('statement-'+str(row['statement'])+'.svg')
    raw=name.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=baseline()['source_sha256'][name.relative_to(ROOT).as_posix()]:
        raise ValueError('Saved SVG changed')
    recovered=decode(from_svg(raw.decode('utf-8')),lexicon=reader())
    if syntax_hash(recovered)!=row['syntax_sha256']:raise ValueError('Local fork ordering changed saved syntax')
    return dict(statement=row['statement'],syntax_sha256=syntax_hash(recovered))


def measure(drawing):
    geometry=read_geometry(from_svg(to_svg(drawing['shapes'])))
    flow=decompose_flow(geometry,terminal_words=True,branch_seams=True,large_branches=True,local_continuation=True)
    return dict(width=drawing['width'],layout=drawing.get('layout','serial'),
        interleaving_failure=drawing.get('interleaving_failure'),unbranched_paths=drawing['unbranched_paths'],
        circles=len(geometry['circles']),main_nuclei=len(flow['main']),
        branch_lengths=[len(s) for s in flow['side'] if s],
        expression_branches=sum(g['expression_branch'] for g in drawing['groups']),
        lexical_contacts=sum(r['kind']=='tangent' for r in geometry['relations']))


@lru_cache(maxsize=12)
def checked(index):
    context,_=fixture();public=LexicalContext.from_published(context.published())
    key,label,source=cases()[index];drawing=compile_statement(source,lexicon=context)
    svg=to_svg(drawing['shapes'])
    if decode(list(reversed(from_svg(svg))),lexicon=public)!=source:raise ValueError('Local order changed '+key)
    return dict(key=key,label=label,svg=svg,source=source,syntax_sha256=syntax_hash(source),**measure(drawing))


@lru_cache(maxsize=40)
def actual(index):
    row=inputs()['selected'][index];started=time.perf_counter()
    drawing=compile_statement(row['public'],lexicon=framing_context());svg=to_svg(drawing['shapes'])
    recovered=decode(from_svg(svg),lexicon=reader())
    if recovered!=row['public']:raise ValueError('Interleaved page syntax changed')
    return dict(statement=row['statement'],status='matched',svg=svg,
        seconds=round(time.perf_counter()-started,3),syntax_sha256=syntax_hash(recovered),**measure(drawing))


def pins():
    result=prior_pins()
    names={'scripts/kant_interleaved_layout.py','scripts/check_kant_local_continuation.py',
        'tests/test_kant_local_continuation.py',BASELINE}
    names.update(n for n in baseline()['source_sha256'] if n.startswith('output/kant-expression-branches-v2/'))
    for name in names:
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        if name.startswith('output/') and result[name]!=baseline()['source_sha256'][name]:
            raise ValueError('Saved branch evidence changed: '+name)
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT/'diagnostics',run_path=RUN.with_name(RUN.name+'-diagnostics'),pins=pins,
        cases=cases,checked=checked,preserved=preserved,preserved_count=40,
        schema='kant-local-continuation-diagnostics-1',version=VERSION,title='分岐直後の円で読む順序',
        intro='分岐直後の二つの主円のうち右側へ続く方を主列とします。枝の終端位置には依存しません。',
        limits=['Linear side expressions; nested forks remain','No visual freeze or new semantic judgment'])
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,case_function=actual,
        schema='kant-local-continuation-1',context_factory=framing_context,reader_factory=reader,
        lexical_limit='Local first-nucleus ordering; serial placement retained when scheduling fails',
        title='局所的な分岐順による40文の試作',
        intro='主列と枝の次の円を順に配置します。短い側を先に終える配置を優先し、配置不能時は同じ構文の従来配置を使います。外観の固定候補ではありません。')


def build_report():
    result=page_report(out=OUT,pin_function=pins);diagnostics=diagnostic_report(OUT/'diagnostics',pins)
    result.update(diagnostics=diagnostics['diagnostics'],preserved_svg_syntax=diagnostics['preserved_svg_syntax'])
    result['source_sha256'].update(diagnostics['source_sha256'])
    result['limits']=['Local branch order and linear side expressions only; nested forks and multiple slots remain',
        'Fallback layouts are reported separately; long connectors and repeated heads remain',
        'No page decoding, semantic re-review or visual freeze']
    if not any(c['layout']=='interleaved' for c in result['cases']):raise ValueError('No scheduled page layout exercised')
    return result
