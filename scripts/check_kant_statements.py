"""Read statement force and closed assumption scopes from circle geometry."""
from functools import lru_cache
import hashlib,json
from noema.constructed_discourse import normalize_document
from scripts import check_kant_questions_messages as previous
from scripts import kant_public_fragment as writing
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.check_kant_function_application import apply,abstraction
from scripts.check_kant_content_binding import content
from scripts.check_kant_quotation_operations import disquote
from scripts.kant_page_public_context import ROOT
from scripts.kant_lexical_context import LexicalContext
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-statements'
RUN=ROOT/'.noema-project/runs/kant-statements-v3'


def statement(kind,body):return dict(kind=kind,body=body)
def suppose(condition,*children):return dict(kind='suppose',condition=condition,statements=list(children))


def canonical(source):
    used=set()
    def collect(value):
        if isinstance(value,dict):
            if value.get('kind') in ('call','function_ref'):used.add(value['symbol'])
            for child in value.values():collect(child)
        elif isinstance(value,list):
            for child in value:collect(child)
    collect(source)
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=writing.declarations_for(tuple(sorted(used))),statements=[source]))['statements'][0]


@lru_cache(maxsize=1)
def cases():
    red=call('red',call('book'));round_=call('round',call('book'))
    bound=quant('forall','x',call('red',variable('x')))
    q=previous.question(abstraction([('x','individual')],call('red',variable('x'))))
    value=content('s',logic('equal',variable('s'),variable('s')))
    msg=previous.message('direct',value)
    a=lambda body:statement('assert',body)
    ask=lambda body:statement('ask',body)
    perform=lambda body:statement('perform',body)
    seq=previous.sequences.sequence('individual',call('book'),call('town'))
    seq_truth=logic('equal',previous.sequences.length(seq),previous.sequences.numbers.number(2))
    rows=[
        ('assert','真偽の本文から断定を読む',a(red)),
        ('ask-truth','同じ真偽の本文への問いを区別する',ask(red)),
        ('ask-question','質問型から問いを読む',ask(q)),
        ('ask-zero','回答項のない質問を読む',ask(previous.question(abstraction([],red)))),
        *[('perform-'+force,'発話を実行する：'+force,perform(previous.message(force,value))) for force in writing.MESSAGE_FORCES],
        ('returned-message','関数が返す発話を実行する',perform(apply(abstraction([],msg)))),
        ('returned-question','関数が返す質問から文種別を読む',ask(apply(abstraction([],q)))),
        ('quoted-question','引用から戻した質問で文種別を読む',ask(disquote(quote(q)))),
        ('returned-truth','関数が返す真偽を問う',ask(apply(abstraction([],red)))),
        ('single-assumption','一つの仮定と一つの子文',suppose(red,a(round_))),
        ('mixed-statements','同じ仮定の中で三種類の文を読む',suppose(red,a(round_),ask(red),perform(msg))),
        ('nested-assumption','内側の仮定を閉じて外側の次の文へ戻る',suppose(red,suppose(round_,ask(red)),a(round_))),
        ('sibling-binders','条件と兄弟文ごとに束縛を閉じる',suppose(bound,a(bound),ask(bound))),
        ('quote-boundary','引用の束縛と次の文の束縛を分ける',suppose(red,
            a(logic('equal',quote(bound),quote(bound))),ask(bound))),
        ('sequence-boundary','列の終端と仮定の終端を分ける',suppose(red,a(seq_truth),ask(round_))),
    ]
    return [(key,label,canonical(source)) for key,label,source in rows]


@lru_cache(maxsize=32)
def checked(index):
    key,label,source=cases()[index]
    drawing=writing.compile_statement(source,multiple=True);svg=to_svg(drawing['shapes'])
    if writing.decode(list(reversed(from_svg(svg))))!=source:raise ValueError('Statement changed native syntax: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],syntax_sha256=syntax_hash(source),
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


@lru_cache(maxsize=1)
def preserved_rows():
    rows=list(previous.preserved_rows())
    saved=json.loads((ROOT/'reports/kant-questions-messages-v1.json').read_text(encoding='utf-8'))
    for key,_,source in previous.cases():
        if key not in ('mixed-answers','bound-question','quoted-application','captured-content','message-sequence'):continue
        old=next(r for r in saved['diagnostics'] if r['key']==key)
        if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved expression syntax changed')
        path='output/kant-questions-messages/'+key+'.svg'
        rows.append(dict(path=path,stamp=saved['source_sha256'][path],source=source,context=None))
    return rows


@lru_cache(maxsize=40)
def preserved(index):
    row=preserved_rows()[index];raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved ink changed')
    reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
    if writing.decode(list(reversed(from_svg(raw.decode('utf-8')))),lexicon=reader)!=row['source']:
        raise ValueError('Statement reader changed saved syntax')
    return dict(svg=row['path'],syntax_sha256=syntax_hash(row['source']))


def malformed():
    book=call('book')['symbol'];red=call('red',call('book'))['symbol']
    truth=[red,book]
    q=['question','function_ref',red]
    return {
        'individual-body':([book],'Statement body has wrong sort'),
        'marked-question':(['ask_truth',*q],'Truth question marker requires truth sort'),
        'empty-assumption':(['suppose',*truth,'types_end'],'Assumption scope requires statements'),
        'condition-sort':(['suppose',book,*truth,'types_end'],'Assumption condition requires truth sort'),
        'missing-end':(['suppose',*truth,*truth],'Missing visible assumption end'),
        'extra-end':(['suppose',*truth,*truth,'types_end','types_end'],'Trailing visible words'),
        'missing-body':(['ask_truth'],'Incomplete visible expression'),
        'marker-in-expression':(['not','ask_truth',*truth],'Statement head inside an expression'),
        'condition-leak':(['suppose','forall',red,'bound0',red,'bound0','types_end'],'Unbound'),
        'sibling-leak':(['suppose',*truth,'forall',red,'bound0',red,'bound0','types_end'],'Unbound'),
    }


def raw_svg(tokens,*,side_at=None,side_tokens=None):
    from scripts.kant_interleaved_layout import compile_stream
    def stream(parts):
        events=[]
        for t in parts:
            event=dict(token=t,side=None,depth=0,path=[])
            if t in writing.root_words():event['word']=t
            events.append(event)
        return events
    events=stream(tokens)
    if side_at is not None:events[side_at]['side']=writing.mark_boundaries(stream(side_tokens))
    # Preserve the fixture's individual root words across statement boundaries.
    # Otherwise a published compound may consume the end of one intended word.
    return to_svg(compile_stream(writing.mark_boundaries(events),contacts=False)['shapes'])


def pins():
    result=previous.pins()
    names={'scripts/check_kant_statements.py','tests/test_kant_statements.py',
           'docs/kant-statement-writing.md','reports/kant-questions-messages-v1.json',
           'noema/constructed_discourse.py','scripts/kant_geometry_rules.py'}
    names.update(r['path'] for r in preserved_rows())
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,
        preserved_count=len(preserved_rows()),schema='kant-statements-1',version=writing.VERSION,
        title='本文型から文を読み、仮定の範囲を閉じる',intro='断定・質問・発話実行と、仮定の内側の文を実図形から復元します。外観は未固定です。',
        limits=['Statement force and assumption scopes only; no new semantic judgments',
                'Declarations, document layout and final visual approval remain'])


def build_report():return report(OUT,pins)
