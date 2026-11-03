"""Actual-SVG controls for a terminal nearest-binding argument tangent."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import html
import json
from unittest.mock import patch

from scripts import kant_public_fragment as writing
from scripts.check_kant_multiple_arguments import fixture, cases as prior_cases, measure, syntax_hash
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call, variable, quant, quote, logic
from scripts.kant_lexical_context import LexicalContext, use_context
from scripts.kant_geometry_reader import read_geometry
from scripts.visible_syntax_geometry import from_svg, to_svg
from scripts.kant_page_public_context import ROOT, inputs
from scripts.kant_passage_anchor_context import passage_context
from scripts.check_kant_junction_bounds import pins as prior_pins
from scripts.long_run import LongRun, atomic_json

OUT=ROOT/'output/kant-bound-argument-contact'
RUN=ROOT/'.noema-project/runs/kant-bound-argument-contact-v2'
RAILS=((0.,32.),(32.,0.),(32.,64.),(64.,32.))


def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def contacts(svg):
    geometry=read_geometry(from_svg(svg));result=[]
    for relation in geometry['relations']:
        if relation['kind']!='tangent':continue
        circles=[geometry['circles'][c] for c in relation['circles']]
        if {c['size'] for c in circles}!={'small','medium'}:continue
        circles.sort(key=lambda c:0 if c['size']=='medium' else 1)
        result.append(dict(medium=circles[0]['center'],small=circles[1]['center']))
    return result


@lru_cache(maxsize=1)
def cases():
    context,names=fixture()
    def predicate(ref):
        return dict(kind='call',symbol=names[0],arguments=[variable(ref),call('aki'),call('nao')])
    inner=quant('forall','s',predicate('s'),'situation')
    four=dict(kind='call',symbol=names[2],arguments=[call('aki'),call('nao'),variable('x'),call('book')])
    bodies=[('nested-inner',quant('forall','outer',quant('exists','inner',predicate('inner'),'situation'),'situation')),
        ('nested-outer',quant('forall','outer',quant('exists','inner',predicate('outer'),'situation'),'situation')),
        ('quoted',logic('equal',quote(inner),quote(inner))),
        ('individual',quant('forall','x',four))]
    with use_context(context):
        return [(key,source) for key,_,source in prior_cases()[6:8]]+[(key,canonical(body)) for key,body in bodies]


def checked(source,context,*,rail=None):
    original=writing.forms
    # Inventory witnesses restrict legal candidate rails, never change forms
    # or decoding. Production compilation has no such restriction.
    def restricted(token,*position):
        limits={'wrbookzq':rail[0],'bound0':rail[1]} if rail else {}
        if rail and rail[0]==64.:limits['wrtreeonezq']=64.
        if position and token in limits and position[1]!=limits[token]:return []
        return original(token,*position)
    with patch.object(writing,'forms',restricted):
        drawing=writing.compile_statement(source,lexicon=context,multiple=True,overlap=True)
    svg=to_svg(drawing['shapes'])
    reader=LexicalContext.from_published(context.published())
    if writing.decode(list(reversed(from_svg(svg))),lexicon=reader)!=source:
        raise ValueError('Bound argument contact changed syntax')
    return dict(svg=svg,exact=True,syntax_sha256=syntax_hash(source),width=drawing['width'],
        contacts=contacts(svg),branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def inventory(rail):
    row=checked(cases()[0][1],fixture()[0],rail=rail)
    if not any((r['medium'][1],r['small'][1])==rail for r in row['contacts']):
        raise ValueError('Missing allowed bound-contact placement')
    return dict(row,medium_rail=rail[0],small_rail=rail[1])


def actual(number):
    source=next(r['public'] for r in inputs()['selected'] if r['statement']==number)
    row=checked(source,passage_context())
    previous='output/kant-passage-anchor-spellings/statement-'+str(number)+'.svg'
    baseline=json.loads((ROOT/'reports/kant-passage-anchor-spellings-v1.json').read_text(encoding='utf-8'))
    if sha(previous)!=baseline['source_sha256'][previous]:raise ValueError('Previous SVG changed')
    saved=(ROOT/previous).read_text(encoding='utf-8')
    if writing.decode(from_svg(saved),lexicon=LexicalContext.from_published(passage_context().published()))!=source:
        raise ValueError('Previous SVG no longer recovers the source')
    return dict(row,statement=number,previous_svg_sha256=sha(previous),
        previous_svg_exact=True,changed_svg=saved!=row['svg'])


def rejected_scope(quoted=False):
    """Remove the actual binder from a valid event stream; no hidden AST input."""
    from scripts.kant_interleaved_layout import compile_stream
    context=fixture()[0]
    with use_context(context):
        events=deepcopy(writing.events(cases()[0][1],multiple=True))
        if [e['token'] for e in events[:2]]!=['forall_typed','type_situation']:
            raise ValueError('Unexpected scope diagnostic header')
        events=events[2:]
        if quoted:
            events.insert(0,dict(token='quote',side=None,depth=0,path=()))
        svg=to_svg(compile_stream(events)['shapes'])
    if not contacts(svg):raise ValueError('Scope rejection must exercise an actual bound contact')
    try:writing.decode(from_svg(svg),lexicon=context)
    except ValueError as error:
        if str(error)!='Unbound visible variable':raise
        return dict(rejected=True,error=str(error),svg=svg)
    raise ValueError('Unbound contact was accepted')


def rejected_main():
    """An otherwise complete application may not use this contact on its main flow."""
    context,names=fixture()
    body=dict(kind='call',symbol=names[2],arguments=[call('aki'),call('nao'),call('book'),variable('x')])
    with use_context(context):source=canonical(quant('forall','x',body))
    drawing=writing.compile_statement(source,lexicon=context,branch=False,contacts=False)
    owner,last=drawing['groups'][-2:]
    if owner['token']!='wrbookzq' or last['token']!='bound0':raise ValueError('Unexpected main diagnostic')
    prefix=drawing['shapes'][:last['shape_start']]
    for y in (0.,32.,64.):
        if abs(y-owner['center'][1])!=32.:continue
        shapes=prefix+writing.forms('bound0',owner['center'][0],y)[0]['shapes']
        try:read_geometry(shapes)
        except ValueError:continue
        svg=to_svg(shapes)
        try:writing.decode(from_svg(svg),lexicon=context)
        except ValueError as error:
            if not str(error).startswith('Contact must join'):raise
            return dict(rejected=True,error=str(error),svg=svg)
        raise ValueError('Main-flow bound contact was accepted')
    raise ValueError('No legal main-flow contact diagnostic')


def pins():
    result=prior_pins()
    names={'scripts/check_kant_bound_argument_contact.py','tests/test_kant_bound_argument_contact.py',
        'docs/kant-bound-argument-contact.md','scripts/kant_interleaved_layout.py','scripts/kant_public_fragment.py',
        'output/kant-bound-contact-prefix/kant_interleaved_layout.py',
        'output/kant-bound-contact-prefix/kant_public_fragment.py'}
    result.update({n:sha(n) for n in names})
    return dict(sorted(result.items()))


def prepare():
    source_pins=pins();OUT.mkdir(parents=True,exist_ok=True)
    jobs=[('inventory-'+str(i),lambda rail=rail:inventory(rail)) for i,rail in enumerate(RAILS)]
    jobs += [(key,lambda source=source:checked(source,fixture()[0])) for key,source in cases()]
    jobs += [('unbound',rejected_scope),('quote-escape',lambda:rejected_scope(True)),('main-flow',rejected_main)]
    jobs += [('statement-'+str(n),lambda n=n:actual(n)) for n in (5,9)]
    rows={}
    with LongRun(RUN,dict(schema='kant-bound-argument-contact-1',source_sha256=source_pins),resume=RUN.exists()) as run:
        for i,(key,action) in enumerate(jobs):
            run.emit('progress',stage=key,completed=i,total=len(jobs))
            row=run.step(key,dict(case=key),action)
            (OUT/(key+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
            rows[key]={k:v for k,v in row.items() if k!='svg'}
        sections=[]
        for key,_ in jobs:
            if key in ('unbound','quote-escape','main-flow'):continue
            sections.append('<section><h2>'+html.escape(key)+'</h2>'+ (OUT/(key+'.svg')).read_text(encoding='utf-8')+'</section>')
        page='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>束縛引数の上下接触</title>
<style>body{font:16px/1.8 "Yu Gothic",sans-serif;margin:32px;background:#f7f6f1;color:#203438}section{background:white;padding:20px;margin:20px 0;overflow:auto}svg{height:130px}</style>
<h1>束縛引数の上下接触</h1><p>中円は述語名の最後、小円は最寄りの束縛変数を表す引数です。四配置の見本と構文確認用の小例です。全体の外観を固定する候補ではありません。</p>'''+''.join(sections)+'</html>'
        (OUT/'index.html').write_text(page,encoding='utf-8',newline='\n')
        (OUT/'dictionary.json').write_text(json.dumps(fixture()[0].published(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        if pins()!=source_pins:raise ValueError('Inputs changed during bound-contact checks')
        source_pins.update({p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUT.iterdir() if p.name!='structural-report.json'})
        atomic_json(OUT/'structural-report.json',dict(schema='kant-bound-argument-contact-1',cases=rows,
            source_sha256=dict(sorted(source_pins.items())),limits=[
                'Inventory witnesses restrict legal candidate rails; production layout remains free',
                'A tangent is only a complete bound0 argument branch; native scope and type checks remain required',
                'Six structural controls, three rejection controls, four rail witnesses, two source statements',
                'No changed word meanings, references, semantic judgment, full-history audit or appearance freeze']))
        run.emit('progress',stage='Report saved',completed=len(jobs),total=len(jobs))


def build_report():
    result=json.loads((OUT/'structural-report.json').read_text(encoding='utf-8'))
    if any(result['source_sha256'].get(n)!=h for n,h in pins().items()):raise ValueError('Implementation changed')
    if any(sha(n)!=h for n,h in result['source_sha256'].items()):raise ValueError('Saved evidence changed')
    return result
