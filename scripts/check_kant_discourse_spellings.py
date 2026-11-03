"""Short semantic spellings with unchanged primitive and definition meanings."""
from functools import lru_cache
import hashlib
import json

from scripts.check_kant_terminal_words import (
    ROOT,checked_with_context,prepare_trial,pins as prior_pins,build_report as trial_report,
)
from scripts.kant_page_public_context import (
    inputs,discourse_context,load_semantic_spellings,DISCOURSE_SPELLINGS,
)
from scripts.kant_lexical_context import LexicalContext

OUT=ROOT/'output/kant-discourse-spellings'
BASELINE='reports/kant-shared-context-v1.json'
RUN=ROOT/'.noema-project/runs/kant-discourse-spellings-v1'


def pins():
    result=prior_pins()
    _,basis_paths=load_semantic_spellings(DISCOURSE_SPELLINGS)
    names=set(basis_paths)|{BASELINE,'scripts/check_kant_discourse_spellings.py',
                          'tests/test_kant_semantic_spellings.py'}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


@lru_cache(maxsize=1)
def reader():
    return LexicalContext.from_published(json.loads(json.dumps(discourse_context().published())))


@lru_cache(maxsize=40)
def checked(index):
    return checked_with_context(index,discourse_context(),reader())


def prepare():
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,
        case_function=checked,schema='kant-discourse-spellings-1',
        context_factory=discourse_context,reader_factory=reader,
        lexical_limit='21 explicit semantic spellings; remaining long numbered names are unfinished',
        title='談話・条件付き判断の語形を短くする',
        intro='既存の主張帰属・対比・強調・条件付き判断と、その内容・文章箇所への参照に短い綴りを宣言します。語義・型・定義本体・参照先を保ち、元の40主張を円と線から復号します。')


def build_report():
    return trial_report(out=OUT,pin_function=pins)


if __name__=='__main__':
    prepare()
