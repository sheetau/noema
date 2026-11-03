"""Numeral boundaries, native composition and preserved nonnumeric ink."""
from functools import lru_cache
import hashlib,json
from scripts import kant_public_fragment as writing
from scripts.kant_number_grammar import components,number_tokens,END
from scripts.check_visible_syntax import logic,quote,quant,variable
from scripts.check_kant_public_fragment import canonical
from scripts.check_kant_function_application import apply,abstraction
from scripts.check_kant_quotation_operations import assemble,disquote
from scripts.check_kant_shared_stems import records as source_records,pins as inherited_pins
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_page_public_context import ROOT
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-numbers'
RUN=ROOT/'.noema-project/runs/kant-numbers-v1'
BASELINE='reports/kant-bounded-frontiers-v2.json'


def number(a,b=1):return dict(kind='number',numerator=a,denominator=b)


@lru_cache(maxsize=1)
def cases():
    eq=lambda a,b:logic('equal',a,b)
    rows=[('digit-'+str(i),'九進の桁 '+str(i)+' と '+str((i+1)%9),eq(number(i),number((i+1)%9))) for i in range(9)]
    rows += [
        ('place-value','上位桁・内部の0・桁の順序',eq(number(81),number(9))),
        ('negative','負の整数の区別',eq(number(-10),number(-8))),
        ('fraction','符号と互いに素な分子・分母',eq(number(-10,3),number(11,7))),
        ('siblings','隣り合う数値の範囲',logic('and',eq(number(-9),number(9)),eq(number(81),number(80)))),
        ('bound','数型の変数と数値を区別する',quant('forall','x',eq(variable('x'),number(0)),'number')),
        ('quoted','引用内の数値を読む',eq(quote(number(-7,3)),quote(number(7,3)))),
        ('applied','数値を関数の引数に渡す',eq(apply(abstraction([('x','number')],variable('x')),number(42)),number(42))),
        ('returned','関数本体から数を返す',eq(apply(abstraction([],number(11))),number(11))),
        ('quoted-application','引用適用が返す数を取り出す',eq(disquote(assemble(
            quote(abstraction([('x','number')],number(-3,2))),quote(number(5)))),number(-3,2))),
    ]
    return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=24)
def checked(index):
    key,label,source=cases()[index]
    drawing=writing.compile_statement(source,multiple=True);svg=to_svg(drawing['shapes'])
    if writing.decode(list(reversed(from_svg(svg))))!=source:raise ValueError('Numeral changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],
        syntax_sha256=syntax_hash(source),branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


@lru_cache(maxsize=1)
def preserved_rows():
    baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    result=[]
    for row in source_records():
        old=next(r for r in baseline['diagnostics'] if r['key']==row['key'])
        if syntax_hash(row['source'])!=old['syntax_sha256']:raise ValueError('Preserved source changed')
        path='output/kant-bounded-frontiers/'+row['key']+'.svg'
        result.append(dict(row,path=path,stamp=baseline['source_sha256'][path]))
    return result


@lru_cache(maxsize=24)
def preserved(index):
    row=preserved_rows()[index];raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Preserved ink changed')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    if writing.decode(list(reversed(from_svg(raw.decode('utf-8')))),lexicon=reader)!=row['source']:
        raise ValueError('Numeral mode changed nonnumeric syntax')
    return dict(svg=row['path'],syntax_sha256=syntax_hash(row['source']))


def malformed():
    d,sep=components();pos='number_positive';neg='number_negative'
    return {
        'empty':([pos,END],'requires a digit'),
        'leading-zero':([pos,d[0],d[1],END],'Leading zero'),
        'negative-zero':([neg,d[0],END],'Negative zero'),
        'empty-denominator':([pos,d[1],sep,END],'requires a digit'),
        'zero-denominator':([pos,d[1],sep,d[0],END],'reduced denominator'),
        'unit-denominator':([pos,d[1],sep,d[1],END],'reduced denominator'),
        'reducible':([pos,d[2],sep,d[4],END],'reduced denominator'),
        'zero-fraction':([pos,d[0],sep,d[2],END],'reduced denominator'),
        'repeated-separator':([pos,d[1],sep,d[2],sep,d[3],END],'Expected numeral end'),
        'wrong-component':([pos,d[1],'type_number',END],'Expected numeral end'),
        'missing-end':([pos,d[1]],'Expected numeral end'),
    }


def raw_numeral_svg(parts,*,branch=False,seam=False):
    # Deliberately bypass the native encoder to test rejection from actual ink.
    from scripts.kant_interleaved_layout import compile_stream
    tokens=['equal',*parts,*number_tokens(number(1))]
    stream=[dict(token=t,side=None,depth=0,path=[]) for t in tokens]
    if branch:stream[2]['side']=[dict(token='bound0',side=None,depth=1,path=[0])]
    if seam:stream[3]['lexical_seam']=True
    return to_svg(compile_stream(stream)['shapes'])


def pins():
    result=inherited_pins()
    names={BASELINE,'scripts/kant_number_grammar.py','scripts/kant_public_fragment.py',
        'scripts/kant_function_grammar.py','scripts/kant_interleaved_layout.py',
        'scripts/check_kant_numbers.py','tests/test_kant_numbers.py','docs/kant-number-writing.md'}
    names.update(r['path'] for r in preserved_rows())
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,
        preserved_count=len(preserved_rows()),schema='kant-numbers-1',version=writing.VERSION,
        title='数値を円から読む',intro='符号・九進の桁・分母への切替・終端を読み、元の整数と分数へ戻します。',
        limits=['Native rational numbers, composition and preserved nonnumeric examples',
                'Remaining constructors, declarations, full pages and visual approval remain incomplete'])


def build_report():return report(OUT,pins)
