"""Complete the 40-body multiple-branch inventory with pinned resumable steps."""
from functools import lru_cache
import hashlib,html,json,time
from scripts import kant_public_fragment as writing,kant_folded_flow as folded
from scripts.kant_page_public_context import ROOT,inputs
from scripts.kant_lexical_context import use_context
from scripts.kant_incremental_dictionary import PublishedStatementReader,empty_document
from scripts.kant_item_rows import pack_rows
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.check_kant_folded_flow import pins as prior_pins
from scripts.long_run import LongRun,atomic_json

BASELINE='reports/kant-presentation-spellings-v1.json'
DICTIONARY='output/kant-presentation-spellings/dictionary.json'
OUT=ROOT/'output/kant-forty-body-layout'
RUN=ROOT/'.noema-project/runs/kant-forty-body-layout-v2'
WIDTH=1420/.53
SAVED={1:('reports/kant-compound-fan-page-v2.json','output/kant-compound-fan-page-v2/statement-1.svg'),
       2:('reports/kant-bounded-frontier-page-v1.json','output/kant-bounded-frontier-page/statement-2.svg'),
       3:('reports/kant-forty-body-prefix-v1.json','output/kant-forty-body-prefix/statement-3.svg'),
       4:('reports/kant-forty-body-prefix-v1.json','output/kant-forty-body-prefix/statement-4.svg')}


def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def published():
    baseline=read(BASELINE)
    if sha(DICTIONARY)!=baseline['source_sha256'][DICTIONARY]:raise ValueError('Published dictionary changed')
    return read(DICTIONARY)


@lru_cache(maxsize=1)
def reader():return PublishedStatementReader(published())


@lru_cache(maxsize=1)
def selected():
    source=inputs()['selected'];baseline=read(BASELINE)
    if len(source)!=40 or len(baseline['cases'])!=40:raise ValueError('Expected all 40 original page items')
    for row,old in zip(source,baseline['cases']):
        if row['statement']!=old['statement'] or syntax_hash(row['public'])!=old['syntax_sha256']:
            raise ValueError('Published page selection changed')
    if published()['native']['declarations']!=inputs()['native']['declarations']:
        raise ValueError('Public dictionary meanings differ from the saved bridge')
    return source


def pinned_svg(path,report):
    raw=(ROOT/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=report['source_sha256'][path]:raise ValueError('Saved ink changed: '+path)
    return raw.decode('utf-8')


def checked(index):
    row=selected()[index];number=row['statement'];source=row['public'];started=time.perf_counter()
    old=read(BASELINE)['cases'][index];context=reader().context
    if number in SAVED:
        report_path,path=SAVED[number];report=read(report_path)
        metric=next((r for r in report['diagnostics'] if r.get('statement')==number),report['diagnostics'][0])
        if metric['syntax_sha256']!=syntax_hash(source):raise ValueError('Saved multiple-body source changed')
        svg=pinned_svg(path,report);action='reused-multiple';width=metric['width']
        limits=metric.get('branch_limits',[]);unbranched=metric.get('unbranched_paths',[])
    else:
        with use_context(context):
            before=writing.events(source,multiple=False,unbranched={tuple(p) for p in old['unbranched_paths']},
                nested=old['layout']!='serial-fallback')
            after=writing.events(source,multiple=True)
        if before==after:
            svg=pinned_svg('output/kant-presentation-spellings/statement-'+str(number)+'.svg',read(BASELINE))
            action='reused-identical-events';width=old['width'];limits=[];unbranched=old['unbranched_paths']
        else:
            drawing=writing.compile_statement(source,lexicon=context,multiple=True)
            svg=to_svg(drawing['shapes']);width=drawing['width'];action='redrawn'
            limits=drawing.get('branch_limits',[]);unbranched=drawing['unbranched_paths']
    shapes=list(reversed(from_svg(svg)))
    if writing.decode(shapes,lexicon=context)!=source:raise ValueError('Actual body geometry changed native syntax')
    page=folded.fold(shapes,WIDTH);page_svg=to_svg(page['shapes'])
    result=folded.decode_page(list(reversed(from_svg(page_svg))),reader=reader())
    expected=dict(empty_document(),statements=[source])
    if result!=expected:raise ValueError('Folded actual body changed native syntax')
    return dict(statement=number,action=action,svg=svg,folded_svg=page_svg,row_svgs=[to_svg(s) for s in page['row_shapes']],
        width=width,rows=len(page['row_shapes']),syntax_sha256=syntax_hash(source),
        branch_limits=limits,unbranched_paths=unbranched,seconds=time.perf_counter()-started,**measure(svg))


def pins():
    result=prior_pins();baseline=read(BASELINE)
    names={BASELINE,DICTIONARY,'scripts/check_kant_forty_body_layout.py','tests/test_kant_forty_body_layout.py',
           'scripts/kant_spacing_extension.py','reports/kant-spacing-prefix-v1.json',
           'docs/kant-forty-body-layout.md',*(p for pair in SAVED.values() for p in pair),
           *('output/kant-presentation-spellings/statement-'+str(r['statement'])+'.svg' for r in baseline['cases'])}
    result.update({n:sha(n) for n in names})
    return dict(sorted(result.items()))


def prepare():
    source_pins=pins()
    with LongRun(RUN,dict(schema='kant-forty-body-layout-1',source_sha256=source_pins,width=WIDTH),resume=RUN.exists()) as run:
        run.emit('progress',stage='Load pinned syntax and shared dictionary',completed=0,total=40)
        run.step('source-selection',{},lambda:dict(statements=[r['statement'] for r in selected()],dictionary_sha256=sha(DICTIONARY)))
        rows=[]
        for i in range(40):
            run.emit('progress',stage='Multiple-body geometry and folded recovery',completed=i,total=40)
            row=run.step('body-'+str(i),dict(index=i),lambda i=i:checked(i));rows.append(row)
        if pins()!=source_pins:raise ValueError('Body inputs changed')
        OUT.mkdir(parents=True,exist_ok=True)
        cards=[]
        for row in rows:
            for suffix,key in (('','svg'),('-folded','folded_svg')):
                path=OUT/('statement-'+str(row['statement'])+suffix+'.svg')
                path.write_text(row[key],encoding='utf-8',newline='\n');source_pins[path.relative_to(ROOT).as_posix()]=sha(path)
            cards.append('<section><h2>項目 '+str(row['statement'])+'</h2>'+row['folded_svg']+'</section>')
        (OUT/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>40項目の複数枝と折返し</title>'
            '<style>body{margin:30px;background:#f7f6f1;color:#203438;font:16px sans-serif}section{padding:20px;background:white;margin:20px 0}svg{max-width:100%;height:auto}h2{font-size:16px}</style>'
            '<h1>元ページの40項目：配置と復号</h1><p>項目別の点検用です。最終のページ配置・外観固定ではありません。</p>'+''.join(cards)+'</html>\n',encoding='utf-8')
        atomic_json(OUT/'structural-report.json',dict(schema='kant-forty-body-layout-1',version=writing.VERSION,
            bodies=[{k:v for k,v in r.items() if k not in ('svg','folded_svg','row_svgs')} for r in rows],
            total_rows=sum(r['rows'] for r in rows),total_circles=sum(r['circles'] for r in rows),
            source_sha256=dict(sorted(source_pins.items())),limits=[
                'Forty bodies with the explicit saved shared dictionary; full dictionary publication is separate',
                'Item-wise folded previews, not final paragraph/page composition or visual approval']))
        run.emit('progress',stage='All 40 body previews saved',completed=40,total=40)


def build_report():
    result=read(OUT/'structural-report.json')
    if any(result['source_sha256'].get(n)!=v for n,v in pins().items()):raise ValueError('Body implementation changed')
    if any(sha(n)!=v for n,v in result['source_sha256'].items()):raise ValueError('Body output changed')
    return result
