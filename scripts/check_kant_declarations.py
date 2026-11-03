"""Recover declared names, signatures and native bodies without an AST oracle."""
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from noema.constructed_discourse import normalize_document,function_sort,question_sort
from scripts import kant_public_fragment as writing
from scripts import check_kant_statements as previous
from scripts.check_visible_syntax import call,logic,variable,quote,quant
from scripts.check_kant_function_application import abstraction
from scripts.check_kant_content_binding import content
from scripts.check_kant_questions_messages import question
from scripts.visible_word_forms import Word,symbol
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_page_public_context import ROOT
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-declarations'
RUN=ROOT/'.noema-project/runs/kant-declarations-v2'


def name():return symbol(Word('compound',('book','town','book','town')),writing.vocabulary())


def canonical(declaration):
    dependencies=writing.declarations_for(tuple(sorted(writing.used_words(declaration))))
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[*dependencies,declaration],statements=[]))
    return doc['declarations'][-1],LexicalContext(doc).published()


def reader_without_target(published,name):
    reader=LexicalContext.from_published(published)
    # Retain only the target's public spelling. Neither its type nor its body
    # is available to expression inference or final native validation.
    reader.words.pop(name,None);reader.declarations.pop(name,None);reader._imports.clear()
    reader.document['declarations']=[d for d in reader.document['declarations'] if d['name']!=name]
    assert name not in reader.words and name not in reader.declarations
    return reader


@lru_cache(maxsize=1)
def inputs():
    v=variable;book=call('book');red=lambda x:call('red',x)
    def primitive(types,result):return dict(kind='primitive',name=name(),parameters=types,result=result)
    def definition(types,result,body):return dict(kind='definition',name=name(),
        parameters=[dict(name=n,sort=t) for n,t in types],result=result,body=body)
    rows=[
        ('primitive-value','引数のない原始語',primitive([],'individual')),
        ('primitive-relation','順序のある原始語の型',primitive(['individual','number'],'truth')),
        ('primitive-higher','関数を受ける原始語',primitive([function_sort(['individual'],'truth')],question_sort(['number']))),
        ('constant','本体から結果型を読む定義',definition([],'number',dict(kind='number',numerator=1,denominator=4))),
        ('identity','引数をそのまま返す定義',definition([('x','individual')],'individual',v('x'))),
        ('ordered','二引数の順序を保持する定義',definition([('x','individual'),('y','individual')],'truth',call('above',v('x'),v('y')))),
        ('exchanged','交換した二引数を区別する定義',definition([('x','individual'),('y','individual')],'truth',call('above',v('y'),v('x')))),
        ('inner-binder','引数と本体内の束縛を分ける',definition([('x','individual')],'truth',quant('forall','y',call('above',v('x'),v('y'))))),
        ('returned-function','引数を参照する関数を返す',definition([('x','individual')],function_sort(['individual'],'truth'),abstraction([('y','individual')],call('above',v('x'),v('y'))))),
        ('returned-question','質問を返す定義',definition([],question_sort(['individual']),question(abstraction([('x','individual')],red(v('x')))))),
        ('quoted-binding','引用内では引数の範囲を閉じる',definition([('x','individual')],'truth',logic('equal',quote(quant('forall','y',red(v('y')))),quote(quant('forall','y',red(v('y'))))))),
        ('content','内容を返す定義',definition([('x','individual')],'content',content('s',red(v('x'))))),
    ]
    return [(key,label,*canonical(d)) for key,label,d in rows]


def cases():return [(k,l,d) for k,l,d,_ in inputs()]


@lru_cache(maxsize=16)
def checked(index):
    key,label,source,published=inputs()[index]
    drawing=writing.compile_declaration(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=writing.decode_declaration(list(reversed(from_svg(svg))),lexicon=reader_without_target(published,source['name']))
    if recovered!=source:raise ValueError('Declaration differs from source: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],syntax_sha256=syntax_hash(source),
        target_body_and_signature_absent=True,branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


@lru_cache(maxsize=1)
def preserved_rows():
    rows=list(previous.preserved_rows())
    saved=json.loads((ROOT/'reports/kant-statements-v3.json').read_text(encoding='utf-8'))
    for key,_,source in previous.cases():
        if key not in ('ask-truth','returned-question','perform-direct','nested-assumption','sibling-binders','sequence-boundary'):continue
        old=next(r for r in saved['diagnostics'] if r['key']==key)
        if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved statement syntax changed')
        path='output/kant-statements/'+key+'.svg'
        rows.append(dict(path=path,stamp=saved['source_sha256'][path],source=source,context=None))
    return rows


@lru_cache(maxsize=40)
def preserved(index):
    row=preserved_rows()[index];raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved ink changed')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    if writing.decode(list(reversed(from_svg(raw.decode('utf-8')))),lexicon=reader)!=row['source']:
        raise ValueError('Declaration reader changed saved statement')
    return dict(svg=row['path'],syntax_sha256=syntax_hash(row['source']))


def malformed():
    book=call('book')['symbol']
    return {
        'missing-name':(['primitive'],'Missing declaration name'),
        'missing-parameter-end':(['primitive',book,'type_individual'],'Incomplete visible type header'),
        'missing-result':(['primitive',book,'types_end'],'Incomplete visible type header'),
        'extra-result':(['primitive',book,'types_end','type_individual','type_truth'],'Trailing visible words'),
        'missing-body':(['definition',book,'types_end'],'Incomplete visible expression'),
        'unbound-body':(['definition',book,'types_end','bound0'],'Unbound visible variable'),
        'self-dependent':(['definition',book,'types_end',book],'Declaration cannot depend on itself'),
        'head-in-body':(['definition',book,'types_end','primitive'],'Declaration head inside an expression'),
    }


def pins():
    result=previous.pins()
    names={'scripts/check_kant_declarations.py','tests/test_kant_declarations.py',
           'docs/kant-declaration-writing.md','reports/kant-statements-v3.json'}
    names.update(r['path'] for r in preserved_rows())
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,
        preserved_count=len(preserved_rows()),schema='kant-declarations-1',version=writing.VERSION,
        title='宣言名・引数型・定義本体を円から読む',intro='対象の本体と型を読取側から外し、原始語と定義の宣言を実図形から復元します。',
        limits=['One declaration with public spelling and dependencies; not a complete dictionary document',
                'No new semantic judgments; document order, page layout and visual approval remain'])


def build_report():return report(OUT,pins)
