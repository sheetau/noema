"""Actual-page comparison for semantic reference spellings and terminal words."""
from functools import lru_cache
import hashlib
import html
import json
from pathlib import Path
import time

from scripts.long_run import LongRun,atomic_json
from scripts.check_kant_page_public_context import pins as base_pins
from scripts.kant_page_public_context import inputs,reference_context,reference_spellings
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kant-terminal-words'
BASELINE='reports/kant-page-public-context-v1.json'
RUN=ROOT/'.noema-project/runs/kant-terminal-words-v2'


def pins():
    result=base_pins()
    _,basis_paths=reference_spellings()
    names=set(basis_paths)|{BASELINE,'scripts/check_kant_terminal_words.py',
        'tests/test_kant_terminal_words.py','tests/test_kant_public_fragment.py',
        'tests/test_kant_shared_argument.py','tests/test_kant_circle_pair_correction.py',
        'tests/test_kant_readable_flow.py','scripts/check_kant_public_fragment.py',
        'scripts/check_kant_shared_argument.py','scripts/check_kant_circle_pair_correction.py'}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


@lru_cache(maxsize=1)
def reader_context():
    return LexicalContext.from_published(json.loads(json.dumps(reference_context().published())))


@lru_cache(maxsize=40)
def checked(index):
    row=inputs()['selected'][index];ctx=reference_context();started=time.perf_counter()
    drawing=compile_statement(row['public'],lexicon=ctx)
    svg=to_svg(drawing['shapes']);shapes=from_svg(svg)
    recovered=decode(shapes,lexicon=reader_context())
    if recovered!=row['public']:raise ValueError('Terminal word changed the source syntax')
    flow=decompose_flow(read_geometry(shapes),terminal_words=True)
    return dict(statement=row['statement'],status='matched',svg=svg,
        circles=sum(s['kind']=='circle' for s in shapes),width=drawing['width'],
        main_nuclei=len(flow['main']),branch_word_lengths=[len(s) for s in flow['side'] if s],
        seconds=round(time.perf_counter()-started,3),
        syntax_sha256=hashlib.sha256(json.dumps(recovered,sort_keys=True).encode()).hexdigest())


def attempted(index):
    try:return checked(index)
    except ValueError as error:
        return dict(statement=inputs()['selected'][index]['statement'],status='unsupported',error=str(error))


def prepare():
    source_pins=pins();manifest=dict(schema='kant-terminal-word-trial-1',source_sha256=source_pins)
    with LongRun(RUN,manifest,resume=RUN.exists()) as run:
        rows=[];total=len(inputs()['selected'])
        for index in range(total):
            run.emit('progress',stage='Read compound terminal branches',completed=index,total=total)
            row=run.step('sentence-'+str(index),dict(context=reference_context().fingerprint,
                source=inputs()['selected'][index]),lambda index=index:attempted(index))
            rows.append(row)
            print(json.dumps({k:v for k,v in row.items() if k!='svg'}),flush=True)
        if pins()!=source_pins:raise ValueError('Inputs changed during terminal word trial')
        baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
        old={r['statement']:r for r in baseline['cases']}
        OUT.mkdir(parents=True,exist_ok=True)
        atomic_json(OUT/'dictionary.json',reader_context().published())
        cards=[];artifacts=['output/kant-terminal-words/dictionary.json'];cases=[]
        for row in rows:
            item={k:v for k,v in row.items() if k!='svg'}
            if row['status']=='matched':
                if row['syntax_sha256']!=old[row['statement']]['syntax_sha256']:
                    raise ValueError('Recovered public syntax differs from the previous exact bridge')
                name='statement-'+str(row['statement'])+'.svg'
                (OUT/name).write_text(row['svg'],encoding='utf-8',newline='\n')
                artifacts.append('output/kant-terminal-words/'+name)
                item.update(previous_circles=old[row['statement']]['circles'],previous_width=old[row['statement']]['width'])
                body='<div class="ink">'+row['svg']+'</div>'
            else:body='<p>'+html.escape(row['error'])+'</p>'
            cards.append('<section><h2>元の主張 '+str(row['statement'])+'</h2>'+body+'</section>');cases.append(item)
        markup='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>参照語と複合語の枝</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;max-width:1500px;margin:auto;padding:24px;background:#f7f6f1;color:#203438}section{padding:18px;background:#fffffe;margin:18px 0}h2{font-size:18px}.ink{overflow:auto}svg{height:130px;max-width:none}</style>
<h1>短い参照語を複合語の枝へ置く</h1>
<p>著者・提示文脈・本文順序・主張の帰属に短い公開綴りを与え、複合語を一つの引数として横枝へ置きます。状況引数がある述語では最後の状況引数、それ以外は中央引数が枝の位置です。元の40主張と語義・参照先は変えません。</p>
<p><a href="dictionary.json">本文を含まない公開辞書</a>と円・線から復号する試作です。長い語形、一般の枝、行・頁の復号が残るため、まだ外観の固定候補ではありません。</p>
'''+''.join(cards)+'</html>\n'
        (OUT/'index.html').write_text(markup,encoding='utf-8',newline='\n')
        source_pins.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in artifacts})
        result=dict(schema='kant-terminal-words-1',version=VERSION,total=total,
            matched=sum(r['status']=='matched' for r in rows),cases=cases,
            source_sha256=dict(sorted(source_pins.items())),
            limits=['Four semantic discourse spellings; other long numbered names remain',
                    'Terminal words of at most four medium/small nuclei; no arbitrary subtree branches',
                    'No page decoding, general sort/binding completion, semantic re-review or visual freeze'])
        atomic_json(OUT/'structural-report.json',result)
        run.emit('progress',stage='Published terminal word trial',completed=total,total=total)


def build_report():
    report=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))
    if report['matched']!=report['total']:raise ValueError('Terminal word trial has unresolved cases')
    if any(report['source_sha256'].get(n)!=v for n,v in pins().items()):
        raise ValueError('Terminal word trial implementation changed')
    for name,stamp in report['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=stamp:
            raise ValueError('Terminal word artifact changed: '+name)
    return report


if __name__=='__main__':
    prepare()
