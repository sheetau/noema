"""Bind kind anaphora to fixed features and prior depicted activities."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, definition, call, lam
from scripts.compose_conditional_release import content_definition

PARENT = 'examples/v014/kant-learned-familiarity.noema'
ARGS = 'first a firstcase d second a secondcase d selected h[a] c feature h[a a d] c'


def definitions():
    same = quant('f', 'aspect', 'a', op('y', app(v('selected'), v('aspect')),
        op('z', app(v('feature'), v('first'), v('aspect'), v('firstcase')),
            app(v('feature'), v('second'), v('aspect'), v('secondcase')))))
    text = definition('rck', ARGS, both(quant('g', 'aspect', 'a', app(v('selected'), v('aspect'))), same))
    args = [v(name) for name in ('first', 'firstcase', 'second', 'secondcase', 'selected', 'feature')]
    text += definition('rcl', ARGS + ' eligible h[a d] c', both(
        app(v('eligible'), v('first'), v('firstcase')), app(v('eligible'), v('second'), v('secondcase')),
        call('rck', *args)))
    return text


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'referenced-kinds-basis-v1', 'document': 'examples/v014/referenced-kinds.noema', 'primitives': [],
        'definitions': {
            'rck': '空でない指定された性質群について、二つの対象がそれぞれの状況で各性質を持つかどうかが一致する。同じ対象の異なる状況も比較できる。指定外の性質、対象そのものの同一性、自然種全体の同一性は要求しない。',
            'rcl': '二つの対象がそれぞれの状況で同じ適格範囲に属し、rckの指定された性質の一致がある。範囲外の対象を、共通の性質が欠けているだけで同じ種類へ取り込まない。'},
        'unresolved': [
            '種類を決める性質と適格範囲は明示的に与える。共通する性質があるだけで、あらゆる文脈の同じ種類とはしない。近似的な類似度や重み付きの近さではない。',
            '性質の真偽は既知の完全な解釈として与える。二つの未確認を二つの偽として同一化してはいけない。有限評価は与えた有限領域についての検査である。',
            '性質群と解釈を固定した一致は対称的・推移的である。比較するたびに性質群を変える場合には同じ保証をしない。空の性質群では一致を認定しない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = 'r h3u[a d a d] c.r h3v[a a a d] c.r h3w[a d] c.\n'
    blocked = quant('g', 'object', 'a', quant('g', 'limb', 'a', both(
        call('h2f', v('limb'), v('person'), v('point')),
        call('h2h', v('object'), v('limb'), v('person'), v('movement'), v('point')))))
    extra += definition('h3z', 'person a movement a point d', both(
        call('h3h', v('person'), v('movement'), v('point')), op('u', blocked)))
    reference = call('h3u', v('person'), v('anchor'), v('standard'), v('standardcase'))
    ditch = call('h3d', v('person'), v('anchor'))
    eligible = 'i[activity a scene d][' + call('h3z', v('person'), v('activity'), v('scene')) + ']'
    features = lam('aspect', 'a', call('h3w', v('aspect'), v('anchor')))
    has = 'i[activity a aspect a scene d][' + call('h3v', v('person'), v('activity'), v('aspect'), v('scene')) + ']'
    valid = both(call('h2t', v('person'), v('anchor'), v('standardcase')),
        call('h3c', v('person'), v('anchor'), v('standardcase'), ditch),
        call('dg', v('standard'), v('standardcase')),
        call('h2u', v('person'), ditch, v('standard'), v('standardcase')),
        call('h2v', v('standard'), v('standardcase')),
        call('rcl', v('movement'), v('point'), v('standard'), v('standardcase'), features, has, eligible))
    extra += definition('h3x', 'person a movement a point d anchor d', both(
        quant('g', 'standard', 'a', quant('g', 'standardcase', 'd', reference)),
        quant('f', 'standard', 'a', quant('f', 'standardcase', 'd', op('y', reference, valid)))))
    extra += content_definition('h3y', 'person a', 'point', quant('g', 'movement', 'a',
        call('h3x', v('person'), v('movement'), v('point'), call('wh'))))
    extra += definition('h4g', 'person a anchor d', quant('g', 'standard', 'a', quant('g', 'standardcase', 'd',
        both(reference, call('h3x', v('person'), v('standard'), v('standardcase'), v('anchor'))))))
    history = lam('point', 'd', call('h2r', v('person'), v('case'), v('point')))
    before = 'i[first d last d][' + call('ic', v('first'), v('last'), v('case')) + ']'
    for name, operation in (('h4a', 'rch'), ('h4b', 'rci')):
        extra += content_definition(name, 'person a', 'case', both(call('h4g', v('person'), call('wh')),
            call(operation, v('person'), 'r[p h3y]', v('case'), history, before, 'p h3e', 'p h3g', 'p h3f')))
    extra += content_definition('h4c', 'person a', 'case', both(
        op('t', call('h4b', v('person')), v('case')), op('t', call('h3o', v('person')), v('case')),
        call('ea', v('person'), 'r[p h4b]', v('person'), 'r[p h3o]', v('case'))))
    cases = lam('case', 'd', call('h2t', v('person'), call('wh'), v('case')))
    extra += content_definition('h4d', 'person a', 'anchor', both(op('e', v('anchor'), call('wh')),
        call('rc', v('person'), 'p h3n', 'p h4c', cases), call('re', v('person'), 'p h3n', cases)))
    selected = quant('g', 'object', 'a', call('h2s', v('object'), v('person'), call('wh')))
    extra += content_definition('h4e', '', 'anchor', both(op('e', v('anchor'), call('wh')),
        quant('f', 'person', 'a', op('y', both(call('aa', v('person')), selected),
            op('t', call('h4d', v('person')), v('anchor'))))))
    extra += definition('h4f', '', both(call('uc', call('h3s'), call('wa'), 'r[k h4e[]]', call('wh')),
        call('ue', call('h3a'), call('h3s'), call('wh'))))
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    if statements[-1]['body'] != {'kind': 'call', 'symbol': 'h3t', 'arguments': []}:
        raise ValueError('Expected the prior broad-activity reason attribution')
    # The old broad unfamiliarity claim does not follow from the refined one.
    # Keep its definition for comparison, but replace its source assertion.
    doc['statements'] = statements[:-1] + [{'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'h4f', 'arguments': []}}]
    basis = deepcopy(json.loads((ROOT / 'data/kant-learned-familiarity-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-referenced-kinds-basis-v1', document='examples/v014/kant-referenced-kinds.noema')
    generic = generic_composed()[1]
    basis['definitions'].update(generic['definitions'])
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h3u', ['person', 'anchor', 'activity', 'depicted_case'], 'この人物・基準文脈について、そのような運動の参照元として前の跳躍の描写から選ぶ活動と描写状況。参照元の整合性はh3xで別に検査する。現実の経験や同じ出来事の再現を主張しない。'),
        ('h3v', ['person', 'activity', 'aspect', 'case'], 'この人のこの運動が、この描写状況で指定された性質を持つ。性質は種類の比較に用いる観点であり、真偽不明を偽とみなさない。個別の性質の身体的・運動学的な構成説明は呼出側で与える。'),
        ('h3w', ['aspect', 'anchor'], 'この基準文脈で、そのような運動の種類の照合に用いる性質。比較する活動や仮定状況ごとに性質群を選び直さない。原文から具体的にどこまでを採るかは未確定。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h3z': '同じ人によるこの身体移動と、同じ運動・状況についての足側の物理的阻害の不在。既存h3jの運動を個別に参照できる形にした。',
        'h3x': '参照元が非空で、その全てが同じ基準文脈の仮定集合にある、最小の溝への同じ本人の不確かな跳躍である。候補と各参照元がh3zを満たし、同じ非空の性質群で一致する。複数参照元の異なる種類を混ぜず、未知の参照先を任意の身体運動として扱わない。',
        'h3y': '文書の基準文脈whに固定した参照元と性質群について、本人のh3xに該当する運動があるという活動内容。その活動を習慣の対象として記述参照する。',
        'h4g': '参照元が少なくとも一つあり、それを候補にしたh3xが成立する。全参照元が正当で同じ性質の一致する種類を示すことを、今の活動の実行を要求せずに検査する。参照元や性質群の欠落を不慣れへ変換しない。',
        'h4a': '同じ仮定の履歴で、種類を照合した活動記述h3yへの経験に由来する慣れが現在ある。一般の身体移動h3jへの慣れからは導かない。',
        'h4b': '種類の参照h4gと同じ仮定の履歴が正当で、h3yへの経験由来の慣れが成立しない。活動記述をh3yへ固定し、経験・寄与・定着の対象を混ぜない。不正な種類へのh4aの単純な否定とは区別する。',
        'h4c': '種類を照合した活動への不慣れh4bを、同じ仮定内の不確かな跳躍h3oの原因説明に採用し、両内容の成立も要求する。',
        'h4d': '基準文脈whで、除去h3nが成立する同じ仮定にh4cの理由付き帰結を置き、前件の実現可能な仮定を少なくとも一つ要求する。',
        'h4e': '同じ基準文脈で除去対象が指定される人々に、h4dの理由付き条件文を提示する内容。',
        'h4f': '著者への帰属と本文順序を保ち、活動の種類の参照を持つh4eを提示する。旧h3tの一般的な身体移動への不慣れの主張を本文で置き換える。旧定義は比較用に保持する。'})
    basis['unresolved'] += generic['unresolved'] + [
        '種類の参照を明示したが、原文dergleichenが共有させる具体的な性質群と参照元の選択は未確定。単なる同じ出来事、全身体運動、跳躍だけという読みのいずれも暗黙に採用しない。',
        '経験は活動の記述を対象にするため、その内容を現在実行しない。異なる記述に該当する経験をh3yの経験へ移すには、別途その適用の根拠が必要である。記述の別名を意味の同一性だけで自動統合しない。',
        '本文では末尾の旧h3tをh4fに置き換えた。広い活動への慣れの不在と限定された種類への慣れの不在は同義ではないので、両者を累積して帰属させない。原資料・旧文書は変更しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'referenced-kinds'), (source_composed, 'kant-referenced-kinds')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored referenced kinds differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Fixed feature scope and prior depicted activity references composed')


if __name__ == '__main__':
    main()
