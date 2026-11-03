"""Exact original-page syntax after sharing a public situation argument."""
import hashlib
import json

from scripts.check_kant_terminal_words import (
    ROOT,checked,prepare_trial,pins as prior_pins,build_report as trial_report,reader_context,
)
from scripts.kant_page_public_context import inputs,reference_context
from scripts.kant_lexical_context import use_context
from scripts.kant_public_fragment import decode,events
from scripts.visible_syntax_geometry import from_svg

OUT=ROOT/'output/kant-shared-context'
BASELINE='reports/kant-terminal-words-v1.json'
RUN=ROOT/'.noema-project/runs/kant-shared-context-v1'


def pins():
    result=prior_pins()
    names={BASELINE,'scripts/check_kant_shared_context.py','tests/test_kant_shared_context.py'}
    baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name,expected in baseline['source_sha256'].items():
        if name.startswith('output/kant-terminal-words/'):
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
                raise ValueError('Previous geometry changed: '+name)
            names.add(name)
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def checked_context(index):
    row=checked(index)
    source=inputs()['selected'][index]['public']
    old_path=ROOT/'output/kant-terminal-words'/('statement-'+str(row['statement'])+'.svg')
    if decode(from_svg(old_path.read_text(encoding='utf-8')),lexicon=reader_context())!=source:
        raise ValueError('New reader changed the previous explicit syntax')
    with use_context(reference_context()):
        count=sum(e['token']=='and_shared' for e in events(source))
    return dict(row,shared_heads=count,previous_geometry_matched=True)


def prepare():
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,
        case_function=checked_context,schema='kant-shared-context-1',
        title='二つの述語で同じ状況を共有する',
        intro='各述語の公開型にある最後の状況引数を共有します。残りの引数は元の順序で読み、二つの適用へ同じ状況を戻します。従来の単項述語の共有も保持します。元の40主張と語義・参照先は変えません。')


def build_report():
    return trial_report(out=OUT,pin_function=pins)


if __name__=='__main__':
    prepare()
