"""Actual-page evidence for circle contact as internal word composition."""
from functools import lru_cache
import hashlib

from scripts.check_kant_terminal_words import ROOT,checked_with_context,prepare_trial,build_report as trial_report
from scripts.check_kant_framing_spellings import pins as prior_pins,reader
from scripts.kant_page_public_context import framing_context

OUT=ROOT/'output/kant-lexical-contact'
BASELINE='reports/kant-framing-spellings-v1.json'
RUN=ROOT/'.noema-project/runs/kant-lexical-contact-v1'


def pins():
    result=prior_pins()
    names={BASELINE,'scripts/check_kant_lexical_contact.py','tests/test_kant_lexical_contact.py'}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


@lru_cache(maxsize=40)
def checked(index):
    return checked_with_context(index,framing_context(),reader())


def prepare():
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,
        case_function=checked,schema='kant-lexical-contact-1',
        context_factory=framing_context,reader_factory=reader,
        lexical_limit='27 semantic spellings; internal medium contacts, not general subtree or page composition',
        title='複合語の内部を円周接触で結ぶ',
        intro='同じ複合語の隣り合う二つの単独中円を、隣接する段で接触させます。接触は語の内部だけに用い、語順・引数・引用・束縛と既存の意味を保ちます。円と線の規則を満たす経路だけを選びます。')


def build_report():
    report=trial_report(out=OUT,pin_function=pins)
    if not any(r['lexical_contacts'] for r in report['cases']):
        raise ValueError('No actual-page lexical contact was exercised')
    return report


if __name__=='__main__':
    prepare()
