"""Recursive visible branches with independent syntax and binding contrasts."""
from copy import deepcopy
from functools import lru_cache
import hashlib,json,time

from scripts.check_kant_expression_branches import fixture as base_fixture,ROOT
from scripts.check_kant_local_continuation import pins as prior_pins
from scripts.kant_structural_trial import prepare as diagnostic_trial,report as diagnostic_report
from scripts.check_kant_terminal_words import prepare_trial,build_report as page_report
from scripts.kant_page_public_context import inputs,framing_context
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary
from scripts.visible_word_forms import Word,symbol
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.check_kant_public_fragment import canonical
from scripts.kant_public_fragment import compile_statement,decode,VERSION
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg

OUT=ROOT/'output/kant-nested-branches'
RUN=ROOT/'.noema-project/runs/kant-nested-branches-v2'
BASELINE='reports/kant-local-continuation-v1.json'
PREVIOUS=ROOT/'output/kant-local-continuation'


def fixture():
    base,apply=base_fixture()
    name=symbol(Word('compound',('book','treeone','fruit','nao')),vocabulary())
    document=deepcopy(base.document)
    document['declarations'].append(dict(kind='definition',name=name,
        parameters=[dict(name=n,sort='individual') for n in ('x','y')],
        result='individual',body=variable('x')))
    context=LexicalContext(document,declared_spellings={**base.declared_spellings,
        name:dict(parts=['nao','book','aki'],meaning_ja='第一引数を返す二引数の定義。')})
    def select(a,b):return dict(kind='call',symbol=name,arguments=[a,b])
    return context,apply,select


@lru_cache(maxsize=1)
def cases():
    context,f,select=fixture()
    small=lambda a,b:logic('or',call('rain',call('town')),f(2,a,b))
    rows=[('order','枝内の二つの引数',small(call('aki'),call('nao'))),
        ('reverse','同じ枝の引数を入れ替える',small(call('nao'),call('aki'))),
        ('bound-main','枝内の主列から外側の束縛を参照',quant('forall','x',small(variable('x'),call('aki')))),
        ('bound-side','枝内の横枝から外側の束縛を参照',quant('forall','x',small(call('aki'),variable('x')))),
        ('inner-binder','枝内で束縛し、その横枝から参照',logic('or',call('rain',call('town')),
            quant('forall','x',f(2,call('aki'),variable('x'))))),
        ('shared','枝内にある二つの述語の共有引数',logic('or',call('rain',call('town')),
            logic('and',f(0,call('book')),call('round',call('book'))))),
        ('quoted','引用された式の内側の枝',logic('equal',quote(small(call('aki'),call('nao'))),
            quote(call('rain',call('home')))))]
    for depth in (2,3):
        body=call('book')
        for i in range(depth):body=select(call('aki' if i%2 else 'nao'),body)
        rows.append(('depth-'+str(depth),'入れ子の選択定義 '+str(depth)+'段',
            logic('or',call('rain',call('town')),f(0,body))))
    with use_context(context):return [(key,label,canonical(body)) for key,label,body in rows]


def syntax_hash(source):return hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()


def measure(svg):
    geometry=read_geometry(from_svg(svg))
    flow=decompose_flow(geometry,terminal_words=True,branch_seams=True,large_branches=True,
        local_continuation=True,nested_branches=True)
    branches=flow['branches']
    def depth(chain,level):
        return max([level]+[depth(branches[n],level+1) for n in chain if n in branches])
    return dict(circles=len(geometry['circles']),branches=len(branches),
        nested_forks=sum(n not in flow['main'] for n in branches),
        max_branch_depth=depth(flow['main'],0),main_nuclei=len(flow['main']))


@lru_cache(maxsize=12)
def checked(index):
    context,_,_=fixture();key,label,source=cases()[index]
    drawing=compile_statement(source,lexicon=context);svg=to_svg(drawing['shapes'])
    if decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(context.published()))!=source:
        raise ValueError('Nested branch changed '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        layout=drawing.get('layout','serial'),unbranched_paths=drawing['unbranched_paths'],
        syntax_sha256=syntax_hash(source),**measure(svg))


@lru_cache(maxsize=1)
def baseline():return json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def reader():return LexicalContext.from_published(framing_context().published())


@lru_cache(maxsize=40)
def preserved(index):
    row=baseline()['cases'][index];name=PREVIOUS/('statement-'+str(row['statement'])+'.svg')
    raw=name.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=baseline()['source_sha256'][name.relative_to(ROOT).as_posix()]:
        raise ValueError('Saved SVG changed')
    recovered=decode(from_svg(raw.decode('utf-8')),lexicon=reader())
    if syntax_hash(recovered)!=row['syntax_sha256']:raise ValueError('Saved syntax changed')
    return dict(statement=row['statement'],syntax_sha256=syntax_hash(recovered))


@lru_cache(maxsize=40)
def actual(index):
    row=inputs()['selected'][index];started=time.perf_counter()
    drawing=compile_statement(row['public'],lexicon=framing_context());svg=to_svg(drawing['shapes'])
    if decode(from_svg(svg),lexicon=reader())!=row['public']:raise ValueError('Nested page syntax changed')
    return dict(statement=row['statement'],status='matched',svg=svg,width=drawing['width'],
        layout=drawing.get('layout','serial'),interleaving_failure=drawing.get('interleaving_failure'),
        unbranched_paths=drawing['unbranched_paths'],seconds=round(time.perf_counter()-started,3),
        syntax_sha256=syntax_hash(row['public']),**measure(svg))


def pins():
    result=prior_pins();names={BASELINE,'scripts/check_kant_nested_branches.py','tests/test_kant_nested_branches.py',
        'scripts/long_run.py','tests/test_long_run.py'}
    names.update(n for n in baseline()['source_sha256'] if n.startswith('output/kant-local-continuation/'))
    for name in names:
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        if name.startswith('output/') and result[name]!=baseline()['source_sha256'][name]:
            raise ValueError('Saved branch evidence changed: '+name)
    return dict(sorted(result.items()))


def prepare():
    diagnostic_trial(out=OUT/'diagnostics',run_path=RUN.with_name(RUN.name+'-diagnostics'),pins=pins,
        cases=cases,checked=checked,preserved=preserved,preserved_count=40,
        schema='kant-nested-branch-diagnostics-1',version=VERSION,title='枝の内側にも同じ文法を使う',
        intro='引数の順序、引用、束縛を保ったまま、各枝を同じ規則で再帰的に読みます。外観の完成候補ではありません。',
        limits=['One side argument per fork; page decoding remains','No new semantic judgment or visual freeze'])
    prepare_trial(out=OUT,baseline=BASELINE,run_path=RUN,pin_function=pins,case_function=actual,
        schema='kant-nested-branches-1',context_factory=framing_context,reader_factory=reader,
        lexical_limit='Recursive local branch ordering; placement fallback recorded per sentence',
        title='入れ子の枝を含む40文の試作',
        intro='主列と枝の内側に同じ前置文法と局所的な順序を適用します。配置不能な枝は構文を保って主列へ戻します。未固定です。')


def build_report():
    result=page_report(out=OUT,pin_function=pins);diagnostics=diagnostic_report(OUT/'diagnostics',pins)
    result.update(diagnostics=diagnostics['diagnostics'],preserved_svg_syntax=diagnostics['preserved_svg_syntax'])
    result['source_sha256'].update(diagnostics['source_sha256'])
    if any(c['nested_forks']==0 for c in result['diagnostics']):raise ValueError('Nested diagnostic was flattened')
    if max(c['max_branch_depth'] for c in result['diagnostics'])<4:raise ValueError('Deeper branch case missing')
    result['limits']=['Recursive branches; still at most one side argument per nucleus',
        'Layout fallbacks and central-rail repetition remain; no visual freeze',
        'No document/page decoding or new semantic judgments']
    return result
