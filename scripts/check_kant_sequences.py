"""Delimited sequences, ordered branches and native sequence operations."""
from functools import lru_cache
import hashlib,json
from noema.constructed_discourse import sequence_sort,function_sort,description_sort
from scripts import kant_public_fragment as writing
from scripts.check_visible_syntax import call,logic,quote,quant,variable
from scripts.check_kant_public_fragment import canonical
from scripts.check_kant_function_application import apply,abstraction
from scripts.check_kant_quotation_operations import assemble,disquote
from scripts import check_kant_numbers as numbers
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_page_public_context import ROOT
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-sequences'
RUN=ROOT/'.noema-project/runs/kant-sequences-v2'


def sequence(element,*items):return dict(kind='sequence',element=element,items=list(items))
def length(value):return dict(kind='length',sequence=value)
def position(value,index,item):return dict(kind='position',sequence=value,index=index,value=item)
def concat(left,right):return dict(kind='concat',left=left,right=right)
def fold(value,initial,step):return dict(kind='fold',sequence=value,initial=initial,step=step)


@lru_cache(maxsize=1)
def cases():
    n=numbers.number;v=variable;eq=lambda a,b:logic('equal',a,b)
    book=call('book');town=call('town');home=call('home')
    empty=sequence('individual');one=sequence('individual',book);two=sequence('individual',book,town)
    keep=abstraction([('state','individual'),('item','individual')],v('state'))
    last=abstraction([('state','individual'),('item','individual')],v('item'))
    identity=abstraction([('x','individual')],v('x'));ft=function_sort(['individual'],'individual')
    function_fold=fold(empty,identity,abstraction([('f',ft),('item','individual')],v('f')))
    rows=[
        ('empty','空の個体列',eq(length(empty),n(0))),
        ('empty-number','空列でも要素型を保持する',eq(length(sequence('number')),n(0))),
        ('singleton','一要素列の位置照合',position(one,n(0),book)),
        ('ordered','枝から主列へ要素順を読む',position(two,n(0),book)),
        ('exchanged','要素を交換した列を区別する',position(sequence('individual',town,book),n(0),book)),
        ('three-items','先頭二要素を枝へ置く',position(sequence('individual',book,town,home),n(2),home)),
        ('nested','内側と外側の列終端を区別する',eq(length(sequence(sequence_sort('individual'),empty,one)),n(2))),
        ('concatenated','左右の列を結合する',eq(length(concat(one,sequence('individual',town))),n(2))),
        ('bound','外側の列変数を位置照合へ渡す',quant('forall','xs',position(v('xs'),n(0),book),sequence_sort('individual'))),
        ('captured-item','枝の要素から外側の束縛を参照する',quant('forall','x',position(sequence('individual',v('x'),book),n(0),v('x')))),
        ('quoted','引用の中でも列終端を閉じる',eq(quote(empty),quote(empty))),
        ('descriptions','記述を要素とする列',eq(length(sequence(description_sort('number'),quote(n(1)),quote(n(2)))),n(2))),
        ('fold-last','状態と要素のうち要素を返す',eq(fold(two,home,last),town)),
        ('fold-state','状態と要素のうち状態を返す',eq(fold(two,home,keep),home)),
        ('fold-empty','空列の畳込みと初期状態',eq(fold(empty,book,last),book)),
        ('fold-function','畳込みが返す関数を適用する',eq(apply(function_fold,book),book)),
        ('return-sequence','関数が列を返す',eq(length(apply(abstraction([],empty))),n(0))),
        ('return-concat','関数が結合した列を返す',eq(length(apply(abstraction([],concat(empty,empty)))),n(0))),
        ('return-length','関数が列の長さを返す',eq(apply(abstraction([],length(empty))),n(0))),
        ('return-position','関数が位置照合の真偽を返す',apply(abstraction([('x','individual')],position(one,n(0),v('x'))),book)),
        ('quoted-application','引用適用から得た列を読む',eq(length(disquote(assemble(quote(abstraction([],empty))))),n(0))),
        ('function-items','型列終端と要素の束縛を区別する',eq(length(sequence(ft,identity,abstraction([('y','individual')],v('y')))),n(2))),
    ]
    return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=32)
def checked(index):
    key,label,source=cases()[index]
    drawing=writing.compile_statement(source,multiple=True);svg=to_svg(drawing['shapes'])
    if writing.decode(list(reversed(from_svg(svg))))!=source:raise ValueError('Sequence changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],syntax_sha256=syntax_hash(source),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


@lru_cache(maxsize=1)
def preserved_rows():
    rows=list(numbers.preserved_rows())
    report=json.loads((ROOT/'reports/kant-numbers-v1.json').read_text(encoding='utf-8'))
    for key,_,source in numbers.cases():
        if key not in ('place-value','fraction','bound','quoted-application'):continue
        old=next(r for r in report['diagnostics'] if r['key']==key)
        if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved numeral syntax changed')
        path='output/kant-numbers/'+key+'.svg'
        rows.append(dict(path=path,stamp=report['source_sha256'][path],source=source,context=None))
    return rows


@lru_cache(maxsize=24)
def preserved(index):
    row=preserved_rows()[index];raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved nonsequence ink changed')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    if writing.decode(list(reversed(from_svg(raw.decode('utf-8')))),lexicon=reader)!=row['source']:
        raise ValueError('Sequence reader changed saved syntax')
    return dict(svg=row['path'],syntax_sha256=syntax_hash(row['source']))


def raw_svg(tokens,*,side_at=None,side_tokens=None):
    from scripts.kant_interleaved_layout import compile_stream
    def stream(parts):return [dict(token=t,side=None,depth=0,path=[]) for t in parts]
    events=stream(tokens)
    if side_at is not None:events[side_at]['side']=stream(side_tokens)
    # Raw words have no lexical boundary metadata. Keep them separated so
    # invalid type cases reach their intended type check, not contact checks.
    return to_svg(compile_stream(events,contacts=False)['shapes'])


def malformed():
    book=numbers.components()[0][0]
    one=numbers.number_tokens(numbers.number(1))
    empty=['sequence','type_individual','types_end']
    return {
        'missing-end':(['equal','sequence','type_individual',book],'Missing visible sequence end'),
        'extra-end':(['equal',*empty,'types_end',*empty],'Type constructor outside'),
        'missing-type':(['equal','sequence','types_end',*empty],'Expected a public type'),
        'element-sort':(['equal','sequence','type_number',book,'types_end','sequence','type_number','types_end'],'Sequence element sort mismatch'),
        'length-sort':(['equal','length',*one,*one],'Expected sequence sort'),
        'concat-sort':(['equal','concat',*empty,'sequence','type_number','types_end',*empty],'Concatenation sequence sort mismatch'),
        'index-sort':(['position',*empty,book,book],'Position requires a number'),
        'value-sort':(['position',*empty,*one,*one],'Position requires a number'),
        'fold-step':(['equal','fold',*empty,book,book,book],'Fold step must map'),
    }


def pins():
    result=numbers.pins()
    names={'scripts/check_kant_sequences.py','tests/test_kant_sequences.py','docs/kant-sequence-writing.md',
           'reports/kant-numbers-v1.json','scripts/kant_function_grammar.py','scripts/kant_public_fragment.py'}
    names.update(r['path'] for r in preserved_rows())
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,
        preserved_count=len(preserved_rows()),schema='kant-sequences-1',version=writing.VERSION,
        title='列と列の操作を円から読む',intro='要素型・列終端・枝の要素順と、長さ・位置・結合・畳込みを復元します。',
        limits=['Native sequence constructors and preserved examples; no new semantic judgments',
                'Remaining constructors, declarations, full-page layout and visual approval remain'])


def build_report():return report(OUT,pins)
