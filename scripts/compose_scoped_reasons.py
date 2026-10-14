"""Extend Noema reason records with explicit local hypotheses and discharge."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op
from scripts.compose_situated_criticism import params
from scripts.compose_reason_traces import DESC, SEEN as SCOPE, TRUE, FALSE, FIELDS as OLD_FIELDS, REASON as OLD_REASON, JUDGED as OLD_JUDGED

PARENT = 'examples/v016/reason-traces.noema'
SOURCE = 'examples/v016/scoped-reasons.noema'
CORE = 'examples/v016/scoped-reasons-core.noema'
EXAMPLE = 'examples/v016/scoped-identity-example.noema'
BASIS = 'data/scoped-reasons-basis-v1.json'
EXTRA = [('scopes', 'h[a] ' + SCOPE), ('bases', 'h[a] ' + SCOPE)]
FIELDS = OLD_FIELDS + EXTRA
TRACE = [('steps', 'j[a]'), ('goal', DESC)] + FIELDS
REASON = OLD_REASON + EXTRA
JUDGED = OLD_JUDGED + EXTRA
CONSUMER = 'h[c j[a]] c'
STATE = 'h[' + CONSUMER + '] c'
ROOTS = {'rra', 'rrb', 'rrc', 'rrd', 'rre', 'rrf', 'rrg'}
EMPTY = 'l[' + DESC + '][]'


def definitions():
    match = both(op('e', app(v('forms'), v('item')), v('target')), op('e', app(v('scopes'), v('item')), v('scope')))
    text = definition('rra', 'seen j[a] target ' + DESC + ' scope ' + SCOPE + ' forms h[a] ' + DESC + ' scopes h[a] ' + SCOPE,
        'q[v seen][' + FALSE + '][i[found c item a][' + op('x', v('found'), match) + ']]')
    form, rule = app(v('forms'), v('step')), app(v('rules'), v('step'))
    left, right = app(v('left'), v('step')), app(v('right'), v('step'))
    scope, base = app(v('scopes'), v('step')), app(v('bases'), v('step'))
    extend = lambda scope, formula: 'm[' + scope + '][l[' + DESC + '][' + formula + ']]'
    has = lambda formula, context=scope: k('rra', v('seen'), formula, context, v('forms'), v('scopes'))
    cases = [app(v('premises'), form),
        both(has(left), has(k('rqq', left, right)), op('e', form, right)),
        both(has(left), has(right), op('e', form, k('rqr', left, right))),
        both(has(k('rqr', left, right)), op('e', form, left)),
        both(has(k('rqr', left, right)), op('e', form, right)),
        k('rqs', scope, form),
        both(has(right, extend(scope, left)), op('e', form, k('rqq', left, right))),
        both(op('e', scope, extend(base, left)), has(form, base))]
    allowed = FALSE
    for index, case in enumerate(cases):
        allowed = op('x', allowed, both(op('e', rule, 'n p ' + 'abcdefgh'[index] + ' b'), case))
    text += definition('rrb', params([('step', 'a'), ('seen', 'j[a]')] + FIELDS), allowed)
    initial = 'i[consume ' + CONSUMER + '][' + app(v('consume'), TRUE, 'l[a][]') + ']'
    valid = both(v('valid'), k('rrb', v('step'), v('seen'), *(v(n) for n, _ in FIELDS)))
    inner = 'i[valid c seen j[a]][' + app(v('consume'), valid, 'm[v seen][l[a][v step]]') + ']'
    step = 'i[state ' + STATE + ' step a][i[consume ' + CONSUMER + '][' + app(v('state'), inner) + ']]'
    state = 'q[v steps][' + initial + '][' + step + ']'
    closed_goal = both(op('e', app(v('forms'), v('item')), v('goal')), op('e', app(v('scopes'), v('item')), EMPTY))
    last = 'q[v seen][' + FALSE + '][i[previous c item a][' + closed_goal + ']]'
    finish = 'i[valid c seen j[a]][' + both(v('valid'), last) + ']'
    text += definition('rrc', params(TRACE), app(state, finish))
    last_rule = 'q[v steps][n p a b][i[previous b step a][' + rule + ']]'
    text += definition('rrd', params(TRACE), both(k('rrc', *(v(n) for n, _ in TRACE)), op('u', op('e', last_rule, 'n p a b'))))
    direct = both(op('e', rule, 'n p a b'), op('e', form, v('goal')))
    independent = 'q[v steps][' + TRUE + '][i[valid c step a][' + both(v('valid'), op('u', direct)) + ']]'
    text += definition('rre', params(TRACE), both(k('rrd', *(v(n) for n, _ in TRACE)), independent))
    conclusion = app(v('conclusions'), v('judgment'), v('context'))
    proof = k('rre', app(v('proofs'), v('reason'), v('context')), conclusion,
        app(v('premisesfor'), v('reason'), v('context')), *(v(n) for n, _ in FIELDS[1:]))
    text += definition('rrf', params(REASON), both(app(v('claimed'), v('judgment'), conclusion, v('context')), proof))
    refs = {n: v(n) for n, _ in REASON}; refs['context'] = v('scene')
    support = 'i[reason a judgment a scene d][' + k('rrf', *(refs[n] for n, _ in REASON)) + ']'
    text += definition('rrg', params(JUDGED), op('t', k('ya', v('person'), v('subject'), v('judgments'), v('matters'), v('used'), support), v('context')))
    return text


def build():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = parse(format_graph(parent, 'compact') + definitions())
    lookup = {d['name']: d for d in doc['declarations']}
    pending, retained = set(ROOTS), set()
    while pending:
        name = pending.pop()
        if name in retained: continue
        retained.add(name); pending.update(_references(lookup[name]) - retained)
    core = deepcopy(doc); core['declarations'] = [d for d in doc['declarations'] if d['name'] in retained]
    # A written proof record, using a closed false proposition as P. The seven
    # assertions specify the two records; they never assert P itself.
    p = 'r[b point[' + FALSE + ']]'
    implication = k('rqq', p, p)
    demo = 'r jrfirst[] a.r jrsecond[] a.r jrcontext[] d.r jrrule[a] b.'
    demo += 'r jrselect[a ' + DESC + ' ' + DESC + '] ' + DESC + '.r jrscopeselect[a ' + DESC + '] ' + SCOPE + '.'
    demo += definition('jrform', 'step a', k('jrselect', v('step'), p, implication), DESC)
    demo += definition('jrscope', 'step a', k('jrscopeselect', v('step'), p), SCOPE)
    rows = [op('u', op('e', k('jrfirst'), k('jrsecond')))]
    for step, form, code, scope in ((k('jrfirst'), p, 'f', 'l[' + DESC + '][' + p + ']'),
                                   (k('jrsecond'), implication, 'g', EMPTY)):
        rows += [op('e', k('jrform', step), form), op('e', k('jrrule', step), 'n p ' + code + ' b'), op('e', k('jrscope', step), scope)]
    refs = dict(steps='l[a][k jrfirst[] k jrsecond[]]', goal=implication,
        premises='i[formula ' + DESC + '][' + FALSE + ']', forms='p jrform', rules='p jrrule',
        left='i[step a][' + p + ']', right='i[step a][' + p + ']', scopes='p jrscope', bases='i[step a][' + EMPTY + ']')
    queries = [k(name, *(refs[n] for n, _ in TRACE)) for name in ('rrc', 'rre')]
    queries += [op('t', 's[' + content + ']', k('jrcontext')) for content in (p, implication)]
    example = parse(format_graph(core, 'compact') + demo + ''.join('s[' + x + '].' for x in rows) + ''.join('q[' + x + '].' for x in queries))
    return {SOURCE: format_graph(doc, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n', EXAMPLE: format_graph(example, 'compact') + '\n'}


def basis():
    return dict(status='scoped_deductive_reasons_not_general_insight', document=SOURCE, core=CORE, example=EXAMPLE, parent=PARENT,
        definitions=dict(rra='先行段階の式と、その段階の仮定列の両方が一致することを要求する。',
            rrb='前提・含意除去・連言導入/除去に、局所仮定・含意導入・一仮定の追加を加える。',
            rrc='全段階が正しく、最終段階が指定結論かつ空の局所仮定列である。',
            rrd='rrcに加え、最終段階が単なる外部前提の列挙ではない。',
            rre='rrdに加え、結論と同じ記述を外部前提として使う段階がない。解除された局所仮定とは区別する。',
            rrf='同じ判断・理由・時点の結論を、局所仮定が全て解除された推論列で支持する。',
            rrg='yaの理由使用と支持をrrfへ接続する。仮定の真偽や本人の心理を推測しない。'),
        rule_codes={'0':'外部前提','1':'含意除去','2':'連言導入','3':'連言の左除去','4':'連言の右除去',
            '5':'現在の仮定列にある式を仮定として使う','6':'一番内側の仮定を解除して含意を導入する','7':'先行する導出へ一つの仮定を追加する'},
        new_definitions=7, new_primitives=0, revised_author_statements=0,
        example_data=dict(declared_record_symbols=6, data_assertions=7, queries=4,
            meaning='閉じた偽の内容をPとし、Pを局所仮定してP⇒Pを導く二段階の記録。仮定の真理を断言しない。6記号は記録の参照・選択・規則・評価時点の明示データである。'),
        unresolved=['仮定列は順序と重複を保つ。式と仮定列を持つ導出記録であり、編集上の開始/終了位置を持つブロック構文ではない。',
            '含意導入はΓとPからQが導けることをΓでのP⇒Qへ移す。Pの現実の真理や、因果・反事実の読みは主張しない。',
            '外部前提の真理や採用の正当性は別。各項目の指定は全域的で純粋な関数を前提にする。',
            '同義表現の自動統合、仮定列の交換・短縮、依存部分の最小化、否定・選言・量化・帰納の証明規則は未実装。',
            '直接の結論前提は排除するが、同義な前提や前提の正当化を介した循環の全てを排除しない。',
            '洞察一般の定義、カント本文への意味を保った接続、両論文全文の意味確認は未完。本文の全判断に証明を要求しない。'])


def main():
    files = build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}
    for name, text in files.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text: raise ValueError('Stored scoped-reason artifact differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__': main()
