"""Integrate the common shared-application branch rule into one actual sentence."""
from functools import lru_cache
import hashlib,json

from scripts.kant_page_public_context import ROOT,inputs
from scripts.check_kant_shared_application_branches import pins as diagnostic_pins
from scripts.check_kant_multiple_arguments import actual,saved,baseline
from scripts.kant_public_fragment import VERSION
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report

OUT=ROOT/'output/kant-shared-application-page'
RUN=ROOT/'.noema-project/runs/kant-shared-application-page-v1'


@lru_cache(maxsize=1)
def selected_index():return next(i for i,r in enumerate(inputs()['selected']) if r['statement']==2)


def cases():
    row=inputs()['selected'][selected_index()]
    return [('statement-2','本文第2文：共有した述語の残りの引数を枝へ置く',row['public'])]


@lru_cache(maxsize=1)
def checked(index):
    if index!=0:raise IndexError(index)
    selected=selected_index();key,label,source=cases()[0]
    row=actual(selected);old=baseline()['cases'][selected]
    if row['syntax_sha256']!=old['syntax_sha256']:raise ValueError('Previously checked actual syntax changed')
    return dict(key=key,label=label,source=source,**row,previous_circles=old['circles'],
        previous_width=old['width'],svg_changed=row['svg']!=saved(selected))


def pins():
    result=diagnostic_pins()
    for name in ('scripts/check_kant_shared_application_page.py','tests/test_kant_shared_application_page.py',
                 'reports/kant-shared-application-branches-v1.json'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,
        preserved_count=0,schema='kant-shared-application-page-1',version=VERSION,
        title='本文第2文の共有と引数の枝',
        intro='同じ状況を二述語で共有し、各述語の残りの引数を共通の規則で配置した試作です。全頁の適用と外観確認は未完です。',
        limits=['One actual shared-conjunction sentence; no semantic changes or visual freeze'])


def build_report():return diagnostic_report(OUT,pins)
