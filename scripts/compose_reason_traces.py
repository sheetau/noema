"""Describe finite deductive reasons in Noema without executing quoted claims."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op
from scripts.compose_situated_criticism import params

PARENT = 'examples/v016/kant-plural-actions.noema'
SOURCE = 'examples/v016/reason-traces.noema'
BASIS = 'data/reason-traces-basis-v1.json'
DESC = 'i[e]'
SEEN = 'j[' + DESC + ']'
CONSUMER = 'h[c ' + SEEN + '] c'
STATE = 'h[' + CONSUMER + '] c'
FIELDS = [('premises', 'h[' + DESC + '] c'), ('forms', 'h[a] ' + DESC),
    ('rules', 'h[a] b'), ('left', 'h[a] ' + DESC), ('right', 'h[a] ' + DESC)]
TRACE = [('steps', 'j[a]'), ('goal', DESC)] + FIELDS
REASON = [('reason', 'a'), ('judgment', 'a'), ('context', 'd'),
    ('conclusions', 'h[a d] ' + DESC), ('proofs', 'h[a d] j[a]'),
    ('premisesfor', 'h[a d] h[' + DESC + '] c'), ('claimed', 'h[a ' + DESC + ' d] c')] + FIELDS[1:]
JUDGED = [('person', 'a'), ('subject', 'a'), ('context', 'd'),
    ('judgments', 'h[a a d] c'), ('matters', 'h[a a d] c'), ('used', 'h[a a d] c')] + REASON[3:]
TRUE = 'e[n p a b][n p a b]'
FALSE = 'u[' + TRUE + ']'


def definitions():
    text = ''
    for name, operator in (('rqq', 'y'), ('rqr', 'w')):
        body = op(operator, op('t', v('left'), v('point')), op('t', v('right'), v('point')))
        template = 'r[i[left e right e][b point[' + body + ']]]'
        text += definition(name, 'left ' + DESC + ' right ' + DESC,
            'o a[' + template + '][v left v right]', DESC)
    member = 'q[v seen][' + FALSE + '][i[found c item ' + DESC + '][' + op('x', v('found'), op('e', v('item'), v('target'))) + ']]'
    text += definition('rqs', 'seen ' + SEEN + ' target ' + DESC, member)
    form = app(v('forms'), v('step')); rule = app(v('rules'), v('step'))
    left, right = app(v('left'), v('step')), app(v('right'), v('step'))
    has = lambda expr: k('rqs', v('seen'), expr)
    cases = [app(v('premises'), form),
        both(has(left), has(k('rqq', left, right)), op('e', form, right)),
        both(has(left), has(right), op('e', form, k('rqr', left, right))),
        both(has(k('rqr', left, right)), op('e', form, left)),
        both(has(k('rqr', left, right)), op('e', form, right))]
    cases = [both(op('e', rule, 'n p ' + 'abcde'[index] + ' b'), case) for index, case in enumerate(cases)]
    allowed = cases[0]
    for case in cases[1:]:
        allowed = op('x', allowed, case)
    text += definition('rqt', params([('step', 'a'), ('seen', SEEN)] + FIELDS), allowed)
    # Church-encoded (valid-prefix, seen-formulas) state. No new tuple syntax,
    # numeric-domain quantification, or host-language certificate checker.
    initial = 'i[consume ' + CONSUMER + '][' + app(v('consume'), TRUE, 'l[' + DESC + '][]') + ']'
    valid = both(v('valid'), k('rqt', v('step'), v('seen'), *(v(n) for n, _ in FIELDS)))
    seen = 'm[v seen][l[' + DESC + '][' + form + ']]'
    inner = 'i[valid c seen ' + SEEN + '][' + app(v('consume'), valid, seen) + ']'
    step = 'i[state ' + STATE + ' step a][i[consume ' + CONSUMER + '][' + app(v('state'), inner) + ']]'
    state = 'q[v steps][' + initial + '][' + step + ']'
    last = 'q[v seen][v goal][i[previous ' + DESC + ' item ' + DESC + '][v item]]'
    finish = 'i[valid c seen ' + SEEN + '][' + both(v('valid'),
        op('u', op('e', 'd[v seen]', 'n p a b')), op('e', last, v('goal'))) + ']'
    text += definition('rqu', params(TRACE), app(state, finish))
    last_rule = 'q[v steps][n p a b][i[previous b step a][' + rule + ']]'
    text += definition('rqv', params(TRACE), both(k('rqu', *(v(n) for n, _ in TRACE)), op('u', op('e', last_rule, 'n p a b'))))
    direct_assumption = both(op('e', rule, 'n p a b'), op('e', form, v('goal')))
    independent = 'q[v steps][' + TRUE + '][i[valid c step a][' + both(v('valid'), op('u', direct_assumption)) + ']]'
    text += definition('rqy', params(TRACE), both(k('rqv', *(v(n) for n, _ in TRACE)), independent))
    conclusion = app(v('conclusions'), v('judgment'), v('context'))
    proof = k('rqy', app(v('proofs'), v('reason'), v('context')), conclusion,
        app(v('premisesfor'), v('reason'), v('context')), *(v(n) for n, _ in FIELDS[1:]))
    text += definition('rqw', params(REASON), both(app(v('claimed'), v('judgment'), conclusion, v('context')), proof))
    bound = {n: v(n) for n, _ in REASON}; bound.update(context=v('scene'))
    support = 'i[reason a judgment a scene d][' + k('rqw', *(bound[n] for n, _ in REASON)) + ']'
    judged = k('ya', v('person'), v('subject'), v('judgments'), v('matters'), v('used'), support)
    text += definition('rqx', params(JUDGED), op('t', judged, v('context')))
    return text


def build():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = deepcopy(parent); doc['statements'] = []
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] == 'ya']
    assert len(doc['declarations']) == 1
    doc = parse(format_graph(doc, 'compact') + definitions())
    names = {d['name'] for d in doc['declarations']}
    assert names == {'ya', 'rqq', 'rqr', 'rqs', 'rqt', 'rqu', 'rqv', 'rqw', 'rqx', 'rqy'}
    return format_graph(doc, 'compact') + '\n'


def basis():
    return dict(status='deductive_reason_trace_not_general_insight_definition', document=SOURCE, reused_from=PARENT,
        definitions=dict(ya='既存の、同じ主体・対象・判断で理由を用い、その理由がその判断を支持する条件。',
            rqq='二つの内容記述から、同じ状況での含意の閉じた記述を構成する。',
            rqr='二つの内容記述から、同じ状況での連言の閉じた記述を構成する。',
            rqs='有限列に構文として同一の記述が含まれる。真理値の偶然の一致では代用しない。',
            rqt='前提、含意除去、連言導入、左除去、右除去のいずれかを照合する。参照できるのは検査済みの先行部分に現れる式だけ。',
            rqu='非空の順序付き列の全段階が指定前提から正当に進み、最後の式が指定結論に一致する。途中の不正を後続で取り消さない。',
            rqv='rquに加え、最後が単なる前提の列挙でなく導出規則による段階である。',
            rqy='rqvに加え、結論と同じ記述を前提として実際に使う段階がない。利用可能な前提群に結論が含まれるだけでは排除しない。',
            rqw='同じ判断・文脈の結論を、同じ理由・文脈に結び付いた推論列と前提からrqyに従って導出する。',
            rqx='yaの支持条件をrqwで具体化する。本人の同じ対象に関する判断で、その結論を導く理由が実際に用いられる。'),
        rules={'0':'指定した前提','1':'含意除去','2':'連言導入','3':'連言の左除去','4':'連言の右除去'},
        primitives=[], new_definitions=9, revised_author_statements=0,
        unresolved=['洞察一般、Einsichtenの語義、説明理解の必要十分条件とは扱わない。既知の結論への新しい理由を、情報の増加と区別して扱う基盤である。',
            '前提の採用と真理は別。証明列の妥当性だけで結論や前提の現実の真理を断言しない。',
            'rqyが排除するのは結論と同じ記述を直接前提に用いること。同義の別記述や、前提の正当化に結論を頼る循環まで排除したとは主張しない。',
            'この五規則は命題論理の完全な証明系ではない。仮定の導入・解除、否定、量化、帰納、反事実、経験的説明は別途必要。',
            '含意・連言はrqq/rqrで構成した形を照合する。任意の同義表現や別の構文へ推論を自動移さない。',
            '理由の使用・判断主体・対象・結論と記述の結合は明示した関係の解釈が必要。循環した意味説明の完成とは数えない。',
            '本文の許可条件へ全判断に形式的証明を要求する制約は追加しない。カントの洞察部分と全文の意味確認は未完。',
            '全域的で純粋な項目指定を前提にする。短絡評価でないため、各段階には未使用の参照欄にも型の合う記述を渡す。'])


def main():
    files = {SOURCE: build(), BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}
    for name, text in files.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Stored reason-trace artifact differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__':
    main()
