"""Redraw changed event streams and reread unchanged saved SVGs in one trial."""
from functools import lru_cache
import hashlib,json,time

from scripts.check_kant_nested_branches import pins as prior_pins,measure,syntax_hash,ROOT
from scripts.check_kant_terminal_words import prepare_trial,build_report as trial_report
from scripts.kant_presentation_context import presentation_context,SPELLINGS
from scripts.kant_page_public_context import inputs,framing_context,load_semantic_spellings
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_fragment import events,compile_statement,decode
from scripts.visible_syntax_geometry import to_svg,from_svg

BASELINE='reports/kant-nested-branches-v2.json'
PREVIOUS=ROOT/'output/kant-nested-branches'
OUT=ROOT/'output/kant-presentation-spellings'
RUN=ROOT/'.noema-project/runs/kant-presentation-spellings-v1'


@lru_cache(maxsize=1)
def baseline():return json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def reader():return LexicalContext.from_published(presentation_context().published())


def event_stream(source,context,old):
    with use_context(context):
        return events(source,unbranched={tuple(p) for p in old['unbranched_paths']},
            nested=old['layout']!='serial-fallback')


@lru_cache(maxsize=40)
def actual(index):
    row=inputs()['selected'][index];source=row['public'];number=row['statement']
    old=next(r for r in baseline()['cases'] if r['statement']==number)
    previous=PREVIOUS/f'statement-{number}.svg';raw=previous.read_bytes()
    previous_name=previous.relative_to(ROOT).as_posix()
    if hashlib.sha256(raw).hexdigest()!=baseline()['source_sha256'][previous_name]:
        raise ValueError('Saved SVG changed')
    before=event_stream(source,framing_context(),old)
    after=event_stream(source,presentation_context(),old)
    started=time.perf_counter()
    if before==after:
        svg=raw.decode('utf-8')
        result={key:old[key] for key in ('width','circles','branches','nested_forks',
            'max_branch_depth','main_nuclei','layout','unbranched_paths','interleaving_failure')}
        action='reused-svg'
    else:
        drawing=compile_statement(source,lexicon=presentation_context());svg=to_svg(drawing['shapes'])
        result=dict(width=drawing['width'],layout=drawing.get('layout','serial'),
            unbranched_paths=drawing['unbranched_paths'],
            interleaving_failure=drawing.get('interleaving_failure'),**measure(svg))
        action='redrawn'
    recovered=decode(list(reversed(from_svg(svg))),lexicon=reader())
    if recovered!=source or syntax_hash(recovered)!=old['syntax_sha256']:
        raise ValueError('Presentation spelling changed recovered native syntax')
    return dict(statement=number,status='matched',svg=svg,action=action,
        seconds=round(time.perf_counter()-started,3),syntax_sha256=syntax_hash(recovered),
        previous_svg_sha256=hashlib.sha256(raw).hexdigest(),**result)


def pins():
    result=prior_pins();_,basis_paths=load_semantic_spellings(SPELLINGS)
    names=set(basis_paths)|{BASELINE,'scripts/kant_presentation_context.py',
        'scripts/check_kant_presentation_spellings.py','docs/kant-presentation-spellings.md',
        'tests/test_kant_presentation_spellings.py'}
    names.update(n for n in baseline()['source_sha256'] if n.startswith('output/kant-nested-branches/'))
    for name in names:
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        if name.startswith('output/') and result[name]!=baseline()['source_sha256'][name]:
            raise ValueError('Saved presentation baseline changed: '+name)
    return dict(sorted(result.items()))


def prepare():
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,case_function=actual,
        context_factory=presentation_context,reader_factory=reader,schema='kant-presentation-spellings-1',
        lexical_limit='31 declared spellings; four reusable presentation relations shortened',
        title='提示の共通関係を短い綴りで読む',
        intro='同じ主張の確言、二状況の記述対応、主張と背景の帰属、本文の正順に、既存の意味を保つ綴りを使います。イベント列が変わる文だけ描き直し、保存図形も新しい公開辞書で読みます。')


def build_report():
    result=trial_report(out=OUT,pin_function=pins)
    result['redrawn_statements']=[r['statement'] for r in result['cases'] if r['action']=='redrawn']
    result['reused_svg_statements']=[r['statement'] for r in result['cases'] if r['action']=='reused-svg']
    result['limits']=['Same native declarations, meanings and references; no new semantic judgments',
        'Only changed event streams redrawn; all 40 actual SVGs decoded with the published dictionary',
        'Remaining long words, repeated starts, page/document decoding and permitted unused shapes remain',
        'No visual approval or writing freeze']
    return result
