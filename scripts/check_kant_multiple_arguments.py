"""Multiple argument branches, tested from actual circle and line primitives."""
from functools import lru_cache
import hashlib,json,time

from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.check_kant_public_fragment import canonical
from scripts.kant_public_lexicon import vocabulary
from scripts.visible_word_forms import Word,symbol
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_fragment import compile_statement,decode
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_presentation_spellings import pins as prior_pins
from scripts.kant_page_public_context import inputs,ROOT
from scripts.kant_presentation_context import presentation_context
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report
from scripts.check_kant_terminal_words import prepare_trial,build_report as page_report
from scripts.kant_public_fragment import VERSION,events

BASELINE='reports/kant-presentation-spellings-v1.json'
PREVIOUS=ROOT/'output/kant-presentation-spellings'
OUT=ROOT/'output/kant-multiple-arguments'
RUN=ROOT/'.noema-project/runs/kant-multiple-arguments-v2'


@lru_cache(maxsize=1)
def fixture():
    names=[symbol(Word('compound',(root,'treeone','fruit','book')),vocabulary()) for root in ('aki','nao')]
    declarations=[]
    for name,order in zip(names,[('s','x','y'),('x','y','s')]):
        declarations.append(dict(kind='definition',name=name,
            parameters=[dict(name=p,sort='situation' if p=='s' else 'individual') for p in order],
            result='truth',body=call('above',variable('x'),variable('y'))))
    names.append(symbol(Word('compound',('book','treeone','fruit','book')),vocabulary()))
    declarations.append(dict(kind='definition',name=names[-1],
        parameters=[dict(name=n,sort='individual') for n in ('a','b','c','d')],result='truth',
        body=logic('and',call('give',*(variable(n) for n in ('a','b','c'))),call('red',variable('d')))))
    spellings={name:dict(parts=[root,'treeone','book'],
        meaning_ja='二つの個体のabove関係を返す。状況引数は使わない型位置の検査用定義。')
        for name,root in zip(names,('aki','nao'))}
    spellings[names[-1]]=dict(parts=['nao','book','book'],meaning_ja='前三引数のgiveと第四引数のredを連言する共通定義。')
    context=LexicalContext(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]),
        declared_spellings=spellings)
    return context,names


@lru_cache(maxsize=1)
def cases():
    context,names=fixture()
    give=lambda *args:call('give',*args)
    a,b,c=call('aki'),call('book'),call('nao')
    rows=[('give','渡す主体・対象・受け手',give(a,b,c)),
        ('exchanged','対象と受け手を交換',give(a,c,b)),
        ('bound-main','本文側の引数から束縛を参照',quant('forall','x',give(variable('x'),b,c))),
        ('bound-first','最初の枝から束縛を参照',quant('forall','x',give(a,variable('x'),c))),
        ('bound-second','二番目の枝から束縛を参照',quant('forall','x',give(a,b,variable('x')))),
        ('quoted','引用ごとの枝と束縛',logic('equal',quote(quant('forall','x',give(a,variable('x'),c))),
            quote(quant('forall','x',give(a,c,variable('x'))))))]
    for name,args,label in zip(names,[(variable('s'),a,c),(a,c,variable('s'))],('first','last')):
        body=dict(kind='call',symbol=name,arguments=list(args))
        rows.append(('situation-'+label,'状況型の引数が'+label,
            dict(kind='forall',variable='s',sort='situation',body=body)))
    rows.append(('three-branches','四つの引数と三本の枝',dict(kind='call',symbol=names[-1],arguments=[a,b,c,call('home')])))
    with use_context(context):return [(key,label,canonical(body)) for key,label,body in rows]


def measure(svg):
    geometry=read_geometry(from_svg(svg))
    flow=decompose_flow(geometry,terminal_words=True,branch_seams=True,large_branches=True,
        local_continuation=True,nested_branches=True,multiple_branches=True)
    groups=flow['branch_groups']
    def depth(chain,level):
        return max([level]+[depth(child,level+1) for n in chain for child in groups.get(n,[])])
    return dict(circles=len(geometry['circles']),branches=sum(map(len,groups.values())),
        multiple_owners=sum(len(g)>1 for g in groups.values()),
        maximum_sides=max(map(len,groups.values()),default=0),
        max_branch_depth=depth(flow['main'],0),main_nuclei=len(flow['main']))


@lru_cache(maxsize=12)
def checked(index):
    context,_=fixture();key,label,source=cases()[index]
    drawing=compile_statement(source,lexicon=context,multiple=True);svg=to_svg(drawing['shapes'])
    if decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(context.published()))!=source:
        raise ValueError('Multiple branches changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),branch_limits=drawing['branch_limits'],
        unbranched_paths=drawing['unbranched_paths'],**measure(svg))


def syntax_hash(source):return hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()


@lru_cache(maxsize=1)
def baseline():return json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def reader():return LexicalContext.from_published(presentation_context().published())


def saved(index):
    row=baseline()['cases'][index]
    path=PREVIOUS/f'statement-{row["statement"]}.svg';raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=baseline()['source_sha256'][path.relative_to(ROOT).as_posix()]:
        raise ValueError('Saved multiple-branch baseline changed')
    return raw.decode('utf-8')


@lru_cache(maxsize=40)
def preserved(index):
    row=baseline()['cases'][index];recovered=decode(from_svg(saved(index)),lexicon=reader())
    if syntax_hash(recovered)!=row['syntax_sha256']:raise ValueError('Saved syntax changed')
    return dict(statement=row['statement'],syntax_sha256=syntax_hash(recovered))


@lru_cache(maxsize=40)
def actual(index):
    row=inputs()['selected'][index];source=row['public'];started=time.perf_counter()
    with use_context(presentation_context()):
        changed=events(source,multiple=True)!=events(source,multiple=False)
    if changed:
        drawing=compile_statement(source,lexicon=presentation_context(),multiple=True)
        svg=to_svg(drawing['shapes']);layout=drawing.get('layout','serial')
        width=drawing['width'];limits=drawing['branch_limits'];unbranched=drawing['unbranched_paths']
    else:
        old=baseline()['cases'][index];svg=saved(index);layout=old['layout']
        width=old['width'];limits=[];unbranched=old['unbranched_paths']
    recovered=decode(from_svg(svg),lexicon=reader())
    if recovered!=source:raise ValueError('Multiple argument page syntax changed')
    return dict(statement=row['statement'],status='matched',svg=svg,width=width,layout=layout,
        action='redrawn' if changed else 'reused-svg',branch_limits=limits,unbranched_paths=unbranched,
        syntax_sha256=syntax_hash(recovered),seconds=round(time.perf_counter()-started,3),**measure(svg))


def pins():
    result=prior_pins()
    names={BASELINE,'scripts/check_kant_multiple_arguments.py','tests/test_kant_multiple_arguments.py',
        'docs/kant-multiple-arguments.md'}
    names.update(n for n in baseline()['source_sha256'] if n.startswith('output/kant-presentation-spellings/'))
    for name in names:
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        if name.startswith('output/') and result[name]!=baseline()['source_sha256'][name]:
            raise ValueError('Saved multiple-branch evidence changed: '+name)
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT/'diagnostics',run_path=RUN.with_name(RUN.name+'-diagnostics'),pins=pins,
        cases=cases,checked=checked,preserved=preserved,preserved_count=40,
        schema='kant-multiple-argument-diagnostics-1',version=VERSION,
        title='同じ核から複数の引数を読む',
        intro='枝数と公開型から引数位置を決め、線の分岐から元の構文へ戻します。',
        limits=['No semantic change or visual freeze'])
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,case_function=actual,
        context_factory=presentation_context,reader_factory=reader,schema='kant-multiple-arguments-1',
        lexical_limit='Public argument order and multiple branches; layout reductions recorded',
        title='複数引数の枝を含む40文の試作',
        intro='複数枝で変わる文だけ描き直し、枝数・局所的な入口順・公開型から元の構文を復元します。外観は未固定です。')


def build_report():
    result=page_report(out=OUT,pin_function=pins)
    diagnostics=diagnostic_report(OUT/'diagnostics',pins)
    result.update(diagnostics=diagnostics['diagnostics'],preserved_svg_syntax=diagnostics['preserved_svg_syntax'])
    result['source_sha256'].update(diagnostics['source_sha256'])
    if any(r['maximum_sides']<2 for r in result['diagnostics']):raise ValueError('Diagnostic lost multiple branches')
    result['limits']=['Multiple branches are an explicit compile option until visual approval',
        'No page/document decoding or new semantic judgments; layout and unused forms remain',
        'Reduced branch counts recorded; no proof that every proposed layout can be placed']
    return result
