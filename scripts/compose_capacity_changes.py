"""Retain individual endpoint changes alongside net counts and process witnesses."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, call, definition
from scripts.compose_capacity_progress import generic_composed as progress

PARENT = 'examples/v014/kant-capacity-progress.noema'
PERSON_PARAMS = 'person a assessed h[a] e property h[a] e before d after d earlier h[d d] c'
PERSON_ARGS = 'v person v assessed v property v before v after v earlier'
COHORT_PARAMS = 'population j[a] scope h[a] c assessed h[a] e property h[a] e before d after d earlier h[d d] c'


def definitions():
    at = lambda name, point: op('t', app(v(name), v('person')), v(point))
    params = [v(name) for name in ('person', 'assessed', 'property', 'before', 'after', 'earlier')]
    valid = call('rem', *params)
    before, after = at('property', 'before'), at('property', 'after')
    text = definition('rem', PERSON_PARAMS, both(app(v('earlier'), v('before'), v('after')),
        at('assessed', 'before'), at('assessed', 'after')))
    for name, first, last in (('ren', False, True), ('reo', True, False), ('rep', True, True), ('req', False, False)):
        text += definition(name, PERSON_PARAMS, both(valid, before if first else op('u', before), after if last else op('u', after)))
    counters = ['k hf[v population i[person a][k ' + name + '[' + PERSON_ARGS + ']]]' for name in ('ren', 'reo', 'rep', 'req')]
    text += 'd rer[population j[a] assessed h[a] e property h[a] e before d after d earlier h[d d] c] j[b][l[b][' + ' '.join(counters) + ']].\n'
    # Keep the two identities explicit instead of treating a numerical match as
    # evidence that incomplete endpoint classifications were legitimate.
    gained, lost, kept, absent = counters
    total = call('ha', call('ha', gained, lost), call('ha', kept, absent))
    difference = call('ha', gained, call('hb', 'n u b b', lost))
    text += definition('res', COHORT_PARAMS, both(
        call('rej', *[v(name) for name in ('population', 'scope', 'assessed', 'before', 'after', 'earlier')]),
        op('e', total, 'd[v population]'),
        op('e', difference, call('rei', *[v(name) for name in ('population', 'property', 'before', 'after')]))))
    return text


MEANINGS = {
    'rem': '同じ本人について前後の評価条件がともに成立し、指定の順序で前が後より先である。性質が成立するかどうかは、この評価条件と区別する。',
    'ren': 'remを満たし、指定性質が前では不成立、後では成立する。前後の新規成立であり、その原因や獲得過程の存在は別である。',
    'reo': 'remを満たし、指定性質が前では成立、後では不成立になる。原因、喪失の全経過、永続性は含めない。',
    'rep': 'remを満たし、指定性質が前後とも成立する。中間の全時点での持続までは要求しない。',
    'req': 'remを満たし、指定性質が前後とも不成立である。中間やそれ以前に一度も成立しなかったことは主張しない。',
    'rer': '対象列の前後変化について、新規成立・不成立化・前後とも成立・前後とも不成立の四人数を、その順の数値列で返す。対象範囲と評価の正当性はresで確認する。',
    'res': '非空の対象範囲を全列挙し全対象の前後評価と順序が整合する。その上で四分類の人数合計が対象人数と一致し、新規成立人数から不成立化人数を引いた値が既存reiの純増と一致する。',
}
LIMITS = [
    '二時点の分類であり、区間全体での継続、獲得の原因や過程、以前の経験を自動的に復元しない。同じ四人数でも個人の同一性は失われるため、個人別のren〜reqも保持する。',
    '前後とも評価条件が成立しなければ四分類のいずれにも数えない。全対象の集計を認定するresはその場合不成立となる。未評価を前後とも不成立へ補わない。',
    '純増0には誰も変わらない場合と、同数の新規成立・不成立化がある場合が含まれる。数値の保存則だけで個人への悪影響がないとは結論しない。',
]


def generic_composed():
    text, basis = progress()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='capacity-changes-basis-v1', document='examples/v014/capacity-changes.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    order = 'i[first d last d][k ic[v first v last v anchor]]'
    extra = definitions() + '''
d hzj[population j[a] before d after d anchor d] j[b][k rer[v population p fo p h4l v before v after ''' + order + ''']].
d hzk[population j[a] scope h[a] c before d after d anchor d] c[
 w[f person a[y[c[v scope][v person]][k aa[v person]]]][k res[v population v scope p fo p h4l v before v after ''' + order + ''']]
].
d hzl[person a process a before d after d anchor d] c[
 w[k ren[v person p fo p h4l v before v after ''' + order + ''']][k h4p[v person v process v before v after v anchor]]
].
d hzm[population j[a] scope h[a] c before d after d anchor d processes h[a] a] c[
 w[k hzk[v population v scope v before v after v anchor]][f person a[
  y[w[c[v scope][v person]][k ren[v person p fo p h4l v before v after ''' + order + ''']]][
   k hzl[v person c[v processes][v person] v before v after v anchor]
  ]
 ]]
].
'''
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-capacity-progress-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-capacity-changes-basis-v1', document='examples/v014/kant-capacity-changes.noema')
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'hzj': '同じ人の集団について、foの評価条件とh4lの自立的使用能力から、前後四分類の人数を返す。純増だけでは見えない不成立化も別に保持する。',
        'hzk': '対象範囲が全て人で、同じ前後と基準文脈における四分類の全対象評価・全列挙・保存則が成立する。',
        'hzl': '前後でh4lが新規成立し、その同じ本人・過程・前後・基準時について既存h4pの自己活動による離脱が成立する。人数の増加だけを過程の証拠にしない。',
        'hzm': 'hzkを満たす同じ集団の、h4lが新規成立した全員について、指定した各本人の過程がhzlの証拠になる。自己活動による離脱の証拠を全新規成立者に揃える強い追加条件であり、新規成立者がいること自体は要求しない。',
    })
    basis['unresolved'] += LIMITS + [
        'hzl/hzmは自分の精神への働きかけを含むh4pを再利用する特定の獲得過程の条件である。他者の援助を排除しないが、啓蒙の全ての獲得をこの過程だけに限定しない。',
        'hzmは指定した証拠過程の対応を検査する。証拠を見つけられないことだけから、能力が獲得されなかった、あるいは過程が存在しないとは結論しない。',
        '新規成立者がいない場合のhzmは全員への証拠条件として空虚に成立し得る。res/hzkは対象集団を非空とするが、別途の新規成立者の存在条件を代用しない。',
        '人数尺度による進歩の原文への適切さ、原因・離脱過程の一般的な意味、個人ごとの保護をどこまで原文が要求するか、全文の意味一致は未完。既存の15件の主張を保持し、新しい本文主張は追加しない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'capacity-changes'), (source_composed, 'kant-capacity-changes')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored capacity changes differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Individual endpoint changes retained beside net gain and self-achievement witnesses')


if __name__ == '__main__':
    main()
