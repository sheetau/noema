"""Recover shortened passage anchors and measure their actual source impact."""
from functools import lru_cache
import hashlib,json,time
from scripts import kant_public_fragment as writing
from scripts.kant_passage_anchor_context import passage_context,SPELLINGS
from scripts.kant_reference_anchor_context import anchor_context
from scripts.kant_page_public_context import ROOT,inputs,load_semantic_spellings
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.check_kant_reference_anchor_spellings import circle_cost
from scripts.check_kant_root_overlap import pins as prior_pins
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.long_run import LongRun,atomic_json

OUT=ROOT/'output/kant-passage-anchor-spellings'
RUN=ROOT/'.noema-project/runs/kant-passage-anchor-spellings-v1'
BASELINE='reports/kant-reference-anchor-spellings-v1.json'
LAYOUT='reports/kant-presentation-spellings-v1.json'
PREFIX='reports/kant-forty-body-prefix-v2.json'
BODY_NUMBERS=(5,9)


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def reader():return LexicalContext.from_published(passage_context().published())


def density(index):
    source=inputs()['selected'][index]
    saved=read(LAYOUT)['cases'][index]
    previous=read(BASELINE)['density'][index]
    if source['statement']!=saved['statement'] or syntax_hash(source['public'])!=saved['syntax_sha256']:
        raise ValueError('Source density selection changed')
    options=dict(multiple=False,unbranched={tuple(p) for p in saved['unbranched_paths']},nested=saved['layout']!='serial-fallback')
    streams=[];counts=[]
    for context in (anchor_context(),passage_context()):
        with use_context(context):
            stream=writing.events(source['public'],**options)
            streams.append(stream)
            counts.append(circle_cost(stream,context)['circles'])
    if counts[0]!=previous['predicted_after']['circles']:
        raise ValueError('Prior density cannot be reproduced')
    return dict(statement=source['statement'],before_circles=counts[0],predicted_circles=counts[1],
        changed_events=streams[0]!=streams[1],syntax_sha256=syntax_hash(source['public']))


def word_case(name):
    token=inputs()['bridge']['mapping'][name]
    term=dict(kind='call',symbol=token,arguments=[])
    source=dict(kind='assert',body=dict(kind='equal',arguments=[term,term]))
    before=writing.compile_statement(source,lexicon=anchor_context(),multiple=True,overlap=True)
    after=writing.compile_statement(source,lexicon=passage_context(),multiple=True,overlap=True)
    old_svg,svg=to_svg(before['shapes']),to_svg(after['shapes'])
    for ink,ctx in ((old_svg,anchor_context()),(svg,reader())):
        if writing.decode(list(reversed(from_svg(ink))),lexicon=ctx)!=source:
            raise ValueError('Passage anchor changed symbol: '+name)
    return dict(key=name,source=source,svg=svg,previous_svg=old_svg,exact=True,
        before_circles=measure(old_svg)['circles'],circles=measure(svg)['circles'],
        before_width=before['width'],width=after['width'])


def body_case(number):
    source=next(r['public'] for r in inputs()['selected'] if r['statement']==number)
    path='output/kant-forty-body-prefix-v2/statement-'+str(number)+'.svg'
    if sha(path)!=read(PREFIX)['source_sha256'][path]:raise ValueError('Saved body changed')
    old_svg=(ROOT/path).read_text(encoding='utf-8')
    original=LexicalContext.from_published(read('output/kant-presentation-spellings/dictionary.json'))
    if writing.decode(from_svg(old_svg),lexicon=original)!=source:
        raise ValueError('Saved body no longer matches the source')
    started=time.perf_counter()
    after=writing.compile_statement(source,lexicon=passage_context(),multiple=True,overlap=True)
    svg=to_svg(after['shapes'])
    if writing.decode(list(reversed(from_svg(svg))),lexicon=reader())!=source:
        raise ValueError('Actual passage source changed')
    return dict(key='statement-'+str(number),statement=number,svg=svg,previous_svg=old_svg,exact=True,
        before_circles=measure(old_svg)['circles'],seconds=time.perf_counter()-started,
        branch_limits=after.get('branch_limits',[]),unbranched_paths=after['unbranched_paths'],
        syntax_sha256=syntax_hash(source),width=after['width'],**measure(svg))


def pins():
    result=prior_pins()
    _,basis=load_semantic_spellings(SPELLINGS)
    names={*basis,BASELINE,LAYOUT,PREFIX,SPELLINGS,
        'scripts/kant_passage_anchor_context.py','scripts/check_kant_passage_anchor_spellings.py',
        'docs/kant-passage-anchor-spellings.md','tests/test_kant_passage_anchor_spellings.py',
        *('output/kant-forty-body-prefix-v2/statement-'+str(n)+'.svg' for n in BODY_NUMBERS)}
    result.update({n:sha(n) for n in names})
    return dict(sorted(result.items()))


def prepare():
    source_pins=pins();names=list(read(SPELLINGS)['entries'])
    with LongRun(RUN,dict(schema='kant-passage-anchor-spellings-1',source_sha256=source_pins),resume=RUN.exists()) as run:
        costs=[];words=[];bodies=[];total=40+len(names)+len(BODY_NUMBERS)
        for i in range(40):
            run.emit('progress',stage='Compare passage event counts',completed=i,total=total)
            costs.append(run.step('density-'+str(i),dict(index=i),lambda i=i:density(i)))
        for i,name in enumerate(names):
            run.emit('progress',stage='Read passage name '+name,completed=40+i,total=total)
            words.append(run.step('word-'+name,dict(name=name),lambda name=name:word_case(name)))
        for i,number in enumerate(BODY_NUMBERS):
            run.emit('progress',stage='Actual source body '+str(number),completed=40+len(names)+i,total=total)
            bodies.append(run.step('body-'+str(number),dict(statement=number),lambda number=number:body_case(number)))
        if pins()!=source_pins:raise ValueError('Passage inputs changed during generation')
        OUT.mkdir(parents=True,exist_ok=True);cards=[]
        for row in [*words,*bodies]:
            for suffix,field in (('', 'svg'),('-before','previous_svg')):
                path=OUT/(row['key']+suffix+'.svg')
                path.write_text(row[field],encoding='utf-8',newline='\n')
                source_pins[path.relative_to(ROOT).as_posix()]=sha(path)
            cards.append('<section><h2>'+row['key']+'</h2><p>従来の綴り</p>'+row['previous_svg']+'<p>短い綴り</p>'+row['svg']+'</section>')
        dictionary=OUT/'dictionary.json';atomic_json(dictionary,passage_context().published())
        source_pins[dictionary.relative_to(ROOT).as_posix()]=sha(dictionary)
        (OUT/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>談話参照の短い綴り</title>'
            '<style>body{font:16px sans-serif;background:#f7f6f1;color:#203438;margin:24px}section{padding:20px;margin:20px 0;overflow:auto;background:white}svg{height:120px;max-width:none}</style>'
            '<h1>談話参照の短い綴り</h1><p>十一の既存参照と実本文2項目の比較。本文の語義・参照先は同じです。全40項目の完成候補ではありません。</p>'
            +''.join(cards)+'</html>\n',encoding='utf-8',newline='\n')
        def summary(row):return {k:v for k,v in row.items() if k not in ('svg','previous_svg','source')}
        atomic_json(OUT/'structural-report.json',dict(schema='kant-passage-anchor-spellings-1',
            density=costs,words=[summary(r) for r in words],actual_bodies=[summary(r) for r in bodies],
            before_predicted_circles=sum(r['before_circles'] for r in costs),
            predicted_circles=sum(r['predicted_circles'] for r in costs),
            changed_statements=[r['statement'] for r in costs if r['changed_events']],
            source_sha256=dict(sorted(source_pins.items())),limits=[
                'Eleven lexical identity diagnostics and actual source bodies 5 and 9 only',
                'Actual-body comparison includes earlier anchor aliases and the common overlap rule',
                'The 40-body circle prediction keeps the old branch choices; it is not a new full rendering',
                'Old alias mappings are retained; new longest-match boundaries require actual SVG decoding',
                'No changes to meanings or referents, no new semantic judgments, no appearance freeze']))
        run.emit('progress',stage='Passage spelling report saved',completed=total,total=total)


def build_report():
    result=read(OUT/'structural-report.json')
    if any(result['source_sha256'].get(n)!=h for n,h in pins().items()):
        raise ValueError('Passage implementation changed')
    if any(sha(n)!=h for n,h in result['source_sha256'].items()):
        raise ValueError('Passage evidence changed')
    return result
