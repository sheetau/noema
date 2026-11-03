"""One actual sentence after the distinguishing compound-word diagnostics."""
from functools import lru_cache
import hashlib

from scripts.check_kant_compound_fans import pins as diagnostic_pins
from scripts.check_kant_multiple_arguments import actual,saved
from scripts.kant_page_public_context import ROOT,inputs
from scripts.kant_public_fragment import VERSION
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

OUT=ROOT/'output/kant-compound-fan-page-v2'
RUN=ROOT/'.noema-project/runs/kant-compound-fan-page-v2'


def cases():
    first=inputs()['selected'][0]
    return [('statement-'+str(first['statement']),'本文の第1文：複合語を含む引数の枝',first['public'])]


@lru_cache(maxsize=1)
def checked(index):
    if index!=0:raise IndexError(index)
    key,label,source=cases()[0]
    row=actual(0)
    return dict(key=key,label=label,source=source,**row,
        svg_changed=row['svg']!=saved(0))


def pins():
    result=diagnostic_pins()
    for name in ('scripts/check_kant_compound_fan_page.py','tests/test_kant_compound_fan_page.py',
                 'reports/kant-compound-fans-v4.json'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,
        preserved=lambda _:None,preserved_count=0,schema='kant-compound-fan-page-1',version=VERSION,
        title='本文第1文の複数枝：配置試験',
        intro='小例の修正を本文の一文へ適用した試作です。40文全体の配置完了や外観の確定を示すものではありません。',
        limits=['One actual sentence only; remaining page not regenerated or claimed complete'])


def build_report():
    return diagnostic_report(OUT,pins)
