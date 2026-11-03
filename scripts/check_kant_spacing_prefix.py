"""Compare old and factored connector checks without changing accepted ink."""
from functools import lru_cache
import hashlib,importlib.util,json,time
from scripts import kant_interleaved_layout as current,kant_readable_flow as current_route,kant_public_fragment as p
from scripts.check_kant_compound_fans import fixture,cases as fan_cases
from scripts.kant_lexical_context import use_context
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.kant_page_public_context import ROOT
from scripts.check_kant_folded_flow import pins as prior_pins
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-spacing-prefix'
RUN=ROOT/'.noema-project/runs/kant-spacing-prefix-v1'
BASELINE='reports/kant-forty-body-prefix-v1.json'
OLD_LAYOUT='output/kant-forty-body-prefix/kant_interleaved_layout.py'
OLD_ROUTE='output/kant-forty-body-prefix/kant_readable_flow.py'


def old_module(path,name):
    baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=baseline['source_sha256'][path]:
        raise ValueError('Old geometry implementation changed')
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


def cases():return [fan_cases()[i] for i in (0,1,4)]


@lru_cache(maxsize=4)
def checked(index):
    context,*_=fixture();key,label,source=cases()[index]
    old=old_module(OLD_LAYOUT,'reference_layout');route=old_module(OLD_ROUTE,'reference_route')
    results=[]
    for layout,routing in ((old,route),(current,current_route)):
        original_route=p.route;original_check=p.geometry_check;count=0
        def check(*args,**kw):
            nonlocal count
            count+=1
            return original_check(*args,**kw)
        p.route=routing.route;p.geometry_check=check;started=time.perf_counter()
        try:
            with use_context(context):drawing=layout.compile_stream(p.events(source,multiple=True))
        finally:p.route=original_route;p.geometry_check=original_check
        seconds=time.perf_counter()-started;svg=to_svg(drawing['shapes'])
        if p.decode(from_svg(svg),lexicon=context)!=source:raise ValueError('Spacing optimization changed syntax')
        results.append(dict(svg=svg,seconds=seconds,checks=count))
    before,after=results
    if before['svg']!=after['svg']:raise ValueError('Spacing optimization changed actual SVG')
    return dict(key=key,label=label,source=source,svg=after['svg'],identical_svg=True,
        old_seconds=before['seconds'],new_seconds=after['seconds'],old_checks=before['checks'],new_checks=after['checks'])


def pins():
    result=prior_pins()
    for name in (BASELINE,OLD_LAYOUT,OLD_ROUTE,'scripts/kant_spacing_extension.py','scripts/check_kant_spacing_prefix.py',
                 'tests/test_kant_spacing_prefix.py','docs/kant-spacing-prefix.md'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-spacing-prefix-1',version=current_route.VERSION,title='同じ図形を重複する検査を減らして描く',
        intro='旧判定器の全条件を保ち、接続探索中に変わらない組の距離を繰り返し調べないようにします。',
        limits=['Three distinguishing layouts, not all forty body layouts',
                'Measured seconds are local observations, not a guaranteed whole-corpus speedup'])


def build_report():return report(OUT,pins)
