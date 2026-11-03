"""Existing nonliteral and hypothetical presentation under shorter spellings."""
from functools import lru_cache
import hashlib
import json

from scripts.check_kant_terminal_words import ROOT,checked_with_context,prepare_trial,build_report as trial_report
from scripts.check_kant_discourse_spellings import pins as prior_pins
from scripts.kant_page_public_context import framing_context,load_semantic_spellings,FRAMING_SPELLINGS
from scripts.kant_lexical_context import LexicalContext

OUT=ROOT/'output/kant-framing-spellings'
BASELINE='reports/kant-discourse-spellings-v1.json'
RUN=ROOT/'.noema-project/runs/kant-framing-spellings-v2'


def pins():
    result=prior_pins()
    _,basis_paths=load_semantic_spellings(FRAMING_SPELLINGS)
    names=set(basis_paths)|{BASELINE,'scripts/check_kant_framing_spellings.py',
                          'tests/test_kant_framing_spellings.py','tests/test_kant_geometry_vertex_snap.py',
                          'tests/test_kant_geometry_reader.py'}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


@lru_cache(maxsize=1)
def reader():
    return LexicalContext.from_published(json.loads(json.dumps(framing_context().published())))


@lru_cache(maxsize=40)
def checked(index):
    return checked_with_context(index,framing_context(),reader())


def prepare():
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,
        case_function=checked,schema='kant-framing-spellings-1',
        context_factory=framing_context,reader_factory=reader,
        lexical_limit='27 explicit semantic spellings; remaining long numbered names and repetitive flow are unfinished',
        title='比喩・仮定例と文章参照の語形',
        intro='既存の非字義的提示、異なる記述を結ぶ比喩、仮定的一人称例と関連する文章参照に短い綴りを宣言します。二つの記述の区別、引用、語義・型・定義本体を保持します。')


def build_report():
    return trial_report(out=OUT,pin_function=pins)


if __name__=='__main__':
    prepare()
