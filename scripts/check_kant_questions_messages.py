"""Recover native logical equivalence, questions and message forces from ink."""
from functools import lru_cache
import hashlib,json
from noema.constructed_discourse import question_sort
from scripts import kant_public_fragment as writing
from scripts.check_visible_syntax import call,logic,quote,quant,variable
from scripts.check_kant_public_fragment import canonical
from scripts.check_kant_function_application import apply,abstraction
from scripts.check_kant_quotation_operations import assemble,disquote
from scripts.check_kant_content_binding import content,evaluate
from scripts import check_kant_sequences as sequences
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_page_public_context import ROOT
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-questions-messages'
RUN=ROOT/'.noema-project/runs/kant-questions-messages-v1'


def question(function):return dict(kind='question',function=function)
def answer(value,*arguments):return dict(kind='answer_matches',question=value,arguments=list(arguments))
def message(force,value):return dict(kind='message',force=force,content=value)
def message_content(value):return dict(kind='message_content',message=value)


@lru_cache(maxsize=1)
def cases():
    v=variable;n=sequences.numbers.number;eq=lambda a,b:logic('equal',a,b)
    book=call('book');town=call('town');red=call('red',book);round_=call('round',book)
    q=question(abstraction([('x','individual')],call('red',v('x'))))
    q2=question(abstraction([('x','individual'),('y','individual')],call('above',v('x'),v('y'))))
    value=content('t',eq(v('t'),v('t')))
    at=lambda c:quant('forall','s',evaluate(c,v('s')),'situation')
    rows=[
        ('iff','同値の二つの項を読む',logic('iff',red,round_)),
        ('iff-exchanged','同値でも元の項順を保持する',logic('iff',round_,red)),
        ('zero-answers','引数なしの質問に照合する',answer(question(abstraction([],red)))),
        ('one-answer','質問の型から一回答を読む',answer(q,book)),
        ('two-answers','二回答の順序を読む',answer(q2,book,town)),
        ('exchanged-answers','交換した回答を区別する',answer(q2,town,book)),
        ('mixed-answers','異なる型の回答を読む',answer(question(abstraction([('x','individual'),('n','number')],
            logic('and',call('red',v('x')),eq(v('n'),n(1))))),book,n(1))),
        ('bound-question','質問型の変数から回答数を得る',quant('forall','q',answer(v('q'),book),question_sort(['individual']))),
        ('returned-question','関数が返す質問に照合する',answer(apply(abstraction([],q)),book)),
        ('quoted-question','引用から質問を取り出す',answer(disquote(quote(q)),book)),
        ('quoted-application','引用適用が返す質問を読む',answer(disquote(assemble(quote(abstraction([],q)))),book)),
        ('returned-answer','回答照合の真偽を関数から返す',apply(abstraction([],answer(q,book)))),
        *[(force,'発話種別 '+force+' と内容の取り出し',at(message_content(message(force,value)))) for force in writing.MESSAGE_FORCES],
        ('contrasting-forces','同じ内容でも発話種別を保つ',eq(message('assert',value),message('ask',value))),
        ('captured-content','発話内容から外側の変数を参照する',quant('forall','x',at(message_content(
            message('direct',content('t',call('above',v('x'),book))))))),
        ('returned-message','関数が返す発話の内容を読む',at(message_content(apply(abstraction([],message('assert',value)))))),
        ('returned-content','内容取り出しの結果を関数から返す',at(apply(abstraction([],message_content(message('ask',value)))))),
        ('quoted-message','引用した発話を取り出す',at(message_content(disquote(quote(message('direct',value)))))),
        ('message-sequence','列の中で三つの発話種別を区別する',eq(sequences.length(sequences.sequence('message',
            *(message(force,value) for force in writing.MESSAGE_FORCES))),n(3))),
        ('message-answer','発話を質問への回答にする',answer(question(abstraction([('m','message')],
            eq(v('m'),message('assert',value)))),message('ask',value))),
        ('returned-iff','関数が同値の真偽を返す',apply(abstraction([],logic('iff',red,round_)))),
    ]
    return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=32)
def checked(index):
    key,label,source=cases()[index]
    drawing=writing.compile_statement(source,multiple=True);svg=to_svg(drawing['shapes'])
    if writing.decode(list(reversed(from_svg(svg))))!=source:raise ValueError('Question/message changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],syntax_sha256=syntax_hash(source),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


@lru_cache(maxsize=1)
def preserved_rows():
    rows=list(sequences.preserved_rows())
    saved=json.loads((ROOT/'reports/kant-sequences-v2.json').read_text(encoding='utf-8'))
    for key,_,source in sequences.cases():
        if key not in ('three-items','nested','fold-function','quoted-application','function-items'):continue
        old=next(r for r in saved['diagnostics'] if r['key']==key)
        if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved sequence syntax changed')
        path='output/kant-sequences/'+key+'.svg'
        rows.append(dict(path=path,stamp=saved['source_sha256'][path],source=source,context=None))
    return rows


@lru_cache(maxsize=32)
def preserved(index):
    row=preserved_rows()[index];raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved ink changed')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    if writing.decode(list(reversed(from_svg(raw.decode('utf-8')))),lexicon=reader)!=row['source']:
        raise ValueError('Question/message reader changed saved syntax')
    return dict(svg=row['path'],syntax_sha256=syntax_hash(row['source']))


def malformed():
    book=sequences.numbers.components()[0][0]
    red=canonical(call('red',call('book')))['body']['symbol']
    q1=['question','function_ref',red]
    q0=['question','lambda_typed','types_end',red,book]
    one=sequences.numbers.number_tokens(sequences.numbers.number(1))
    return {
        'not-question':(['answer_matches',book],'requires a question type'),
        'not-function':(['answer_matches','question',book],'requires a function type'),
        'nontruth-function':(['answer_matches','question','function_ref',book],'Question requires a truth-valued function'),
        'missing-answer':(['answer_matches',*q1],'Incomplete visible expression'),
        'extra-answer':(['answer_matches',*q0,book],'Trailing visible words'),
        'answer-sort':(['answer_matches',*q1,*one],'Answer sort mismatch'),
        'message-sort':(['equal','message_assert',book,'message_assert',book],'Message requires content sort'),
        'extraction-sort':(['equal','message_content',book,'message_content',book],'Message content requires message sort'),
    }


def pins():
    result=sequences.pins()
    names={'scripts/check_kant_questions_messages.py','tests/test_kant_questions_messages.py',
           'docs/kant-question-message-writing.md','reports/kant-sequences-v2.json'}
    names.update(r['path'] for r in preserved_rows())
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,
        preserved_count=len(preserved_rows()),schema='kant-questions-messages-1',version=writing.VERSION,
        title='同値・質問・発話を円から読む',intro='質問の型から回答数を読み、発話種別と内容の範囲を保持します。',
        limits=['Expression constructors only; no new semantic judgments',
                'Statement forces, assumptions, declarations, full-page layout and visual approval remain'])


def build_report():return report(OUT,pins)
