"""Compose one public act from multiple judgments with at least one divergence."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.extraction import _references
from scripts.compose_constructed_actions import ROOT, INPUTS, SELECTORS, FIELD_SYMBOLS
from scripts.compose_public_divergent_judgments import FRAME
from scripts.compose_quantified_permissions import CLAIM, REFERENCES
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import DESCRIPTION, TRUE

PARENT = 'examples/v016/kant-constructed-actions.noema'
SOURCE = 'examples/v016/kant-plural-actions.noema'
CORE = 'examples/v016/plural-actions-core.noema'
BASIS = 'data/plural-actions-basis-v1.json'
COLLECTION = [('frames', 'j[a]'), ('anchor', 'd')] + SELECTORS
ELIGIBLE = [('person', 'a'), ('activity', 'a'), ('target', DESCRIPTION), ('anchor', 'd'),
    ('collections', 'h[a a a d] c'), ('members', 'h[a d] j[a]'), ('selected', 'h[a a a d] c'), ('roles', 'h[a d] a')] + SELECTORS


def neutral_template(parent):
    """Remove exactly the per-issue divergence conjunct, not personal judgment.

    The removed condition is reintroduced existentially over the collection.
    This is an explicit semantic change for plural acts, not an equivalence
    claim between the neutral action and the old individual action.
    """
    template = deepcopy(next(d for d in parent['declarations'] if d['name'] == 'rqd'))
    body = template['body']
    if body.get('kind') != 'call' or body['symbol'] != 'rpk':
        raise ValueError('Unexpected action template')
    qualification = body['arguments'][0]['body']
    if qualification['kind'] != 'and' or qualification['arguments'][0]['kind'] != 'and':
        raise ValueError('Unexpected qualification structure')
    judged_and_difference = qualification['arguments'][0]
    difference = judged_and_difference['arguments'][1]
    if difference['kind'] != 'exists' or difference['sort'] != 'situation':
        raise ValueError('Expected existential divergence')
    variable = lambda name: {'kind': 'variable', 'name': name}
    apply = lambda function, *args: {'kind': 'apply', 'function': function, 'arguments': list(args)}
    names = {name: parameter['name'] for (name, _), parameter in zip(
        [(n, t) for n, t in FRAME if n not in ('owncriterion', 'standardcriterion')], template['parameters'][4:])}
    point, subject = variable(difference['variable']), variable(names['subject'])
    binding = {'kind': 'sequence', 'element': 'individual', 'items': [subject]}
    own = apply(variable(template['parameters'][0]['name']), binding)
    standard = apply(variable(template['parameters'][2]['name']), binding)
    value = lambda content: {'kind': 'evaluate', 'content': content, 'situation': point}
    expected = {'kind': 'exists', 'variable': difference['variable'], 'sort': 'situation', 'body': {
        'kind': 'and', 'arguments': [apply(variable(names['comparisons']), subject, point),
            {'kind': 'not', 'arguments': [{'kind': 'equal', 'arguments': [value(own), value(standard)]}]}]}}
    if difference != expected:
        raise ValueError('Refuse to remove an unrecognized semantic condition')
    qualification['arguments'][0] = deepcopy(judged_and_difference['arguments'][0])
    template['name'] = 'rqh'
    constructor = deepcopy(next(d for d in parent['declarations'] if d['name'] == 'rqe'))
    if constructor['body']['function'] != {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'rqd'}}:
        raise ValueError('Unexpected quoted action constructor')
    constructor['name'] = 'rqi'
    constructor['body']['function']['body']['symbol'] = 'rqh'
    return [template, constructor], dict(removed_from_each_frame=difference,
        preserved_personal_judgment=True, collection_requires_some_divergence=True)


def definitions():
    # Compare at the same topic/point, using the same criterion codes that are
    # also passed to the neutral personal action constructor.
    left = op('t', app(v('own'), 'l[a][v subject]'), v('point'))
    right = op('t', app(v('standard'), 'l[a][v subject]'), v('point'))
    different = quant('g', 'point', 'd', both(app(v('comparisons'), v('subject'), v('point')), op('u', op('e', left, right))))
    template = 'r[i[own h[j[a]] e standard h[j[a]] e subject a comparisons h[a d] c][i[person a activity a][b context[' + different + ']]]]'
    diff_fields = [(n, t) for n, t in INPUTS if n in ('owncriterion', 'standardcriterion', 'subject', 'comparisons')]
    diff_order = ['owncriterion', 'standardcriterion', 'subject', 'comparisons']
    text = definition('rqj', params(diff_fields), 'o a[' + template + '][' + ' '.join(v(n) for n in diff_order) + ']', DESCRIPTION)
    for name, operator in (('rqn', 'w'), ('rqo', 'x')):
        content = op(operator, op('t', app(v('left'), v('person'), v('activity')), v('context')),
            op('t', app(v('right'), v('person'), v('activity')), v('context')))
        template = 'r[i[left h[a a] e right h[a a] e][i[person a activity a][b context[' + content + ']]]]'
        text += definition(name, 'left ' + DESCRIPTION + ' right ' + DESCRIPTION,
            'o a[' + template + '][v left v right]', DESCRIPTION)
    for name, combine, identity in (('rqk', 'rqn', TRUE), ('rql', 'rqo', op('u', TRUE))):
        initial = 'r[i[person a activity a][b context[' + identity + ']]]'
        step = 'i[acc ' + DESCRIPTION + ' item ' + DESCRIPTION + '][' + k(combine, v('acc'), v('item')) + ']'
        text += definition(name, 'targets j[' + DESCRIPTION + ']', 'q[v targets][' + initial + '][' + step + ']', DESCRIPTION)
    fields = {name: app(v(name), v('frame'), v('anchor')) for name, _ in INPUTS}
    neutral = k('rqi', *(fields[name] for name, _ in INPUTS))
    divergence = k('rqj', *(fields[name] for name, _ in diff_fields))
    def mapped(expression):
        return 'q[v frames][l[' + DESCRIPTION + '][]][i[acc j[' + DESCRIPTION + '] frame a][m[v acc][l[' + DESCRIPTION + '][' + expression + ']]]]'
    text += definition('rqm', params(COLLECTION), k('rqn', k('rqk', mapped(neutral)), k('rql', mapped(divergence))), DESCRIPTION)
    members = app(v('members'), v('collection'), v('anchor'))
    selected = app(v('selected'), v('person'), v('activity'), v('frame'), v('anchor'))
    same_role = op('e', 's[' + fields['role'] + ']', app(v('roles'), v('person'), v('anchor')))
    all_frames = 'q[' + members + '][' + TRUE + '][i[acc c frame a][' + both(v('acc'), selected, same_role) + ']]'
    expected = k('rqm', members, v('anchor'), *(v(name) for name, _ in SELECTORS))
    eligible = both(app(v('collections'), v('person'), v('activity'), v('collection'), v('anchor')),
        op('u', op('e', 'd[' + members + ']', 'n p a b')), all_frames, op('e', v('target'), expected))
    text += definition('rqp', params(ELIGIBLE), quant('g', 'collection', 'a', eligible))
    return text


def build_documents():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = deepcopy(parent); statements, doc['statements'] = doc['statements'], []
    neutral, evidence = neutral_template(parent)
    doc['declarations'] += neutral
    text = definitions() + 'r hzlcollection[a a a d] c.r hzlframes[a d] j[a].'
    refs = {name: 'p ' + FIELD_SYMBOLS[name] for name, _ in INPUTS}
    refs.update(person=v('person'), activity=v('activity'), target=v('target'), anchor=v('anchor'),
        collections='p hzlcollection', members='p hzlframes', selected='p hzkframe', roles=k(REFERENCES['roles']))
    text += definition('hzleligible', params(ELIGIBLE[:4]), k('rqp', *(refs[name] for name, _ in ELIGIBLE)))
    args = {name: k(REFERENCES[name]) for name in REFERENCES}
    args.update(activities='p hzleligible', anchor=v('context'), required='p h7a', permitted='p h7b')
    text += definition('hzlclaim', '', 'b context[' + k('rpu', *(args[name] for name, _ in CLAIM)) + ']', 'e')
    text += definition('hzlattribution', '', k('hzjn', k('hzjo'), k('wa'), 'r b[k hzlclaim[]]', k('hzjp'), k('wh')))
    doc = parse(format_graph(doc, 'compact') + text + 's[k hzlattribution[]].')
    doc['statements'] = statements[:-1] + doc['statements']
    lookup = {d['name']: d for d in doc['declarations']}
    pending, retained = _references(doc['statements'][-1:]), set()
    while pending:
        name = pending.pop()
        if name in retained:
            continue
        retained.add(name); pending.update(_references(lookup[name]) - retained)
    core = normalize_document({**doc, 'declarations': [d for d in doc['declarations'] if d['name'] in retained], 'statements': doc['statements'][-1:]})
    return {SOURCE: format_graph(doc, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n'}, evidence


def basis(evidence):
    return dict(status='partial_plural_judgments_in_one_act', document=SOURCE, parent_document=PARENT,
        parent_basis='data/constructed-actions-basis-v1.json', derivation=evidence,
        definitions=dict(rqh='判断・採用・提示・自己帰属・目的を保ち、各論点に必須だった相違だけを外したひな形。',
            rqi='rqhの行為記述を、同じ基準コードと主張・目的から構成する。',
            rqj='同じ論点・比較候補で本人と標準の基準に差がある条件の記述を作る。',
            rqn='二つの行為内容を同じ本人・行為・文脈でともに満たす記述。', rqo='同じ本人・行為・文脈で少なくとも一方を満たす記述。',
            rqk='有限列の全内容を同じ組で満たす記述を構成する。空列は真の中立内容。',
            rql='有限列の少なくとも一内容を同じ組で満たす記述を構成する。空列は偽の中立内容。',
            rqm='全枠での個人的判断と公的提示、少なくとも一枠での基準との差を、同じ行為内容として構成する。',
            rqp='選択集合の枠列が非空で、全枠が同じ本人・活動に選ばれ、公的役割が許可側と一致し、対象記述がrqmの構成結果である。',
            hzleligible='集合選択・枠列・既存の項目と役割指定をrqpへ結ぶ。',
            hzlclaim='一般許可rpuの対象を複合した行為記述へ結ぶ。個々の許可から複合行為への許可を推論しない。',
            hzlattribution='改訂した一般許可を既存の著者・範囲・文脈へ帰属する。'),
        primitives=dict(hzlcollection='本人・活動・集合識別子・基準文脈の選択関係。', hzlframes='集合識別子・基準文脈に対応する有限の枠列。'),
        unresolved=['有限の列は複数内容を指定する。列の順序や重複は構文に残るが、提示の時間順を主張しない。',
            '全枠で相違を要求せず、少なくとも一枠での差という既存の弱い読みを保持する。洞察Einsichtenの認識上の含意は未完成。',
            '同じ行為への条件の連言であり、別々の行為・人物・文脈での成立を合成しない。',
            '各項目の許可と複合行為の許可は別の記述への規範。分配・集約の規則は追加しない。',
            '集合と枠の網羅性、社会的な対象・採用制度・君主への照応、なおさらの論証、全原文の意味確認は未完。',
            '同義でも異なる構文の記述を自動統合しない。0.16の実行時制限と有限評価器の全域拒否は維持する。'])


def main():
    documents, evidence = build_documents()
    files = documents | {BASIS: json.dumps(basis(evidence), ensure_ascii=False, indent=2) + '\n'}
    for name, body in files.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Existing plural-action artifact differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
        print(name, len(body), 'characters')


if __name__ == '__main__':
    main()
