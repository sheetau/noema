"""Apply the shared-stem rule to the saved second Kant statement."""
from functools import lru_cache
import hashlib,json,time

from scripts.check_kant_shared_application_page import cases
from scripts.check_kant_shared_stems import ink,pins as diagnostic_pins
from scripts.kant_page_public_context import ROOT
from scripts.kant_presentation_context import presentation_context
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

BASELINE='reports/kant-shared-application-page-v1.json'
OLD='output/kant-shared-application-page/statement-2.svg'
OUT=ROOT/'output/kant-shared-stem-page'
RUN=ROOT/'.noema-project/runs/kant-shared-stem-page-v1'


@lru_cache(maxsize=1)
def checked(index):
    if index!=0:raise IndexError(index)
    key,label,source=cases()[0]
    baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'));old=baseline['diagnostics'][0]
    if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Actual sentence syntax changed')
    raw=(ROOT/OLD).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=baseline['source_sha256'][OLD]:raise ValueError('Saved statement ink changed')
    context=presentation_context();reader=LexicalContext.from_published(context.published())
    before=raw.decode('utf-8')
    if decode(list(reversed(from_svg(before))),lexicon=reader)!=source:raise ValueError('Saved statement failed to decode')
    started=time.perf_counter()
    drawing=compile_statement(source,lexicon=context,multiple=True)
    svg=to_svg(drawing['shapes'])
    if decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:raise ValueError('New statement changed syntax')
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],seconds=time.perf_counter()-started,
        syntax_sha256=syntax_hash(source),previous_svg=OLD,previous_width=old['width'],
        previous_circles=old['circles'],previous_branches=old['branches'],previous_ink=ink(before),ink=ink(svg),
        identical_svg=svg==before,branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=diagnostic_pins()
    for name in (BASELINE,OLD,'reports/kant-shared-stems-v1.json','scripts/check_kant_shared_stem_page.py',
                 'scripts/check_kant_shared_application_page.py','tests/test_kant_shared_stem_page.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-shared-stem-page-1',version=VERSION,title='本文第2文の線を共有する',
        intro='共有した述語と引数を、一枝でも線の途中で分岐できる共通規則で配置します。',
        limits=['One actual statement; unchanged native syntax and lexical references',
                'Remaining statements, page layout and visual completion are not certified'])


def build_report():return report(OUT,pins)
