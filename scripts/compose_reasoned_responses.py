"""Keep judgments used as reasons distinct from coincidence and justified support."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_personal_criteria import APPRAISAL, JUDGING
from scripts.compose_policy_norms import DESCRIPTION

PARENT = 'examples/v014/kant-recognized-benefits.noema'
PAIR = [('person', 'a'), ('subject', 'a'), ('reason', 'a'), ('assessment', 'a'),
    ('reasoncriterion', DESCRIPTION), ('reasonbindings', 'j[a]'), ('assessmentcriterion', DESCRIPTION), ('assessmentbindings', 'j[a]'), ('context', 'd')]
RELATIONS = JUDGING + [('uses', 'h[a a d] c'), ('supports', 'h[a a d] c')]
CONFIG = [('reasoncriterion', DESCRIPTION), ('reasonbindings', 'h[a a] j[a]'),
    ('assessmentcriterion', DESCRIPTION), ('assessmentbindings', 'h[a a] j[a]')] + RELATIONS + [
    ('response', 'h[a a a] e'), ('motivates', 'h[a a a d] c')]
SOURCE = [(n, t) for n, t in CONFIG if n not in ('judgments', 'matters', 'uses', 'supports')]
ROOTS = ['rot', 'rou', 'rov', 'row']


def definitions():
    first = k('rlg', *args(APPRAISAL, judgment=v('reason'), criterion=v('reasoncriterion'), bindings=v('reasonbindings')))
    second = k('rlg', *args(APPRAISAL, judgment=v('assessment'), criterion=v('assessmentcriterion'), bindings=v('assessmentbindings')))
    text = definition('rot', params(PAIR + RELATIONS), both(op('u', op('e', v('reason'), v('assessment'))), first, second,
        app(v('uses'), v('assessment'), v('reason'), v('context'))))
    text += definition('rou', params(PAIR + RELATIONS), both(k('rot', *args(PAIR + RELATIONS)), app(v('supports'), v('reason'), v('assessment'), v('context'))))
    for name, condition in (('rov', 'rot'), ('row', 'rou')):
        judged = k(condition, *args(PAIR + RELATIONS,
            reasonbindings=app(v('reasonbindings'), v('person'), v('subject')),
            assessmentbindings=app(v('assessmentbindings'), v('person'), v('subject'))))
        witness = quant('g', 'reason', 'a', quant('g', 'assessment', 'a', both(judged,
            app(v('motivates'), v('person'), v('activity'), v('assessment'), v('context')))))
        body = both(op('t', app(v('response'), v('person'), v('activity'), v('subject')), v('context')), witness)
        text += definition(name, params(CONFIG), 'i[person a activity a subject a][b context[' + body + ']]', 'h[a a a] e')
    return text


MEANINGS = {
    'rot': '同じ本人・対象・時点について、異なる二つの判断がそれぞれの基準記述と引数列を肯定し、第二の判断で第一の判断を理由として使う。単なる共存、逆向きの理由関係、自己参照で代用しない。判断内容の真理や支持の妥当性は要求しない。',
    'rou': 'rotに加え、同じ第一の判断が同じ第二の判断を支えるという評価がある。理由として用いることと、その理由による支持を別々に扱う。支持の評価だけで原文や判断内容の真理を証明しない。',
    'rov': '本人の同じ対象についてrotの二判断があり、第二の判断を同じ応答行為の動機として本人へ結び、その応答も実際に成立する。判断・行為・対象・時点を全条件で共有する。',
    'row': 'rovの理由関係をrouへ強めた応答内容。採用された理由の支持も要求するが、正当な称賛・義務・恩返し・感謝の情緒をそれだけで認定しない。',
    'hzgm': 'rovの判断主体・対象・理由の使用を既存fa・fb・fcへ接続する。支持fdも渡すが、その成立を条件にしない。恩恵の認識に基づく評価を動機とする応答の作例に使う。',
    'hzgn': 'rowの判断・対象・理由の使用・支持をfa・fb・fc・fdへ接続する。hzgmと同じ記述・引数・人物・行為を保ち、支持の有無だけを区別する。',
}
LIMITS = [
    'reasoncriterionとassessmentcriterionは別の閉じた基準記述である。同じ本人が同じ対象について判断していても、理由として使用している関係がなければrotは成立しない。',
    'usesは第二の判断に第一の判断を理由として用いる関係、supportsは第一が第二を支えるという評価である。両者は向きが異なり、相互に推論しない。支持の規範や認知過程の基礎説明は別途必要である。',
    'motivatesは本人・応答行為・評価判断・時点の動機関係として明示する。評価と応答がともに成立することだけから埋めない。唯一の動機、因果機構や十分原因を表す関係ではない。',
    '二つの判断を異なる個体とするのは、ここで表す二段階の理由構造の条件である。一つの判断の内部に複数の内容がある場合や、長い推論網の無循環性は定義していない。',
    '基準は実際の状況で真でなくても判断候補全体で肯定され得る。支持があることを、誤認の不可能性や判断の道徳的正当性と同一視しない。',
    '原文側では恩恵を認める基準と、同じ行為者が指定応答に値する基準を使う。動機となる評価と応答先を保持し、感謝という未説明の基本記号には置き換えない。',
    '感謝の認知・動機面への部分注記である。好意・敬意・感情、善意や間接的恩恵、感謝を表す発話と称賛の区別、社会的な恩返しの規範、原文全体の意味確認は未完。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, generic in (('hzgm', 'rov'), ('hzgn', 'row')):
        text += definition(name, params(SOURCE), k(generic, *args(CONFIG, judgments='p fa', matters='p fb', uses='p fc', supports='p fd')), 'h[a a a] e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-recognized-benefits-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-reasoned-responses-basis-v1', document='examples/v014/kant-reasoned-responses.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS; audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text); selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'reasoned-responses')
def core_composed(): return projected(ROOTS + ['hzgm', 'hzgn', 'hzgk', 'hzgl', 'hzgj', 'ros', 'ro6'], 'reasoned-responses-core')
BUILDERS = ((generic_composed, 'reasoned-responses'), (source_composed, 'kant-reasoned-responses'), (core_composed, 'reasoned-responses-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored reasoned response differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
