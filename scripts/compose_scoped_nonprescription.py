"""Scope a regulator's non-prescription and distinguish a duty judgment from fact."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_described_norms import DESCRIPTION as EXECUTION, RULE, TRUE
from scripts.compose_policy_norms import DESCRIPTION as POLICY, RULE as POLICY_RULE

PARENT = 'examples/v014/kant-named-epochs.noema'
HEAD = [('person', 'a'), ('office', 'a'), ('organization', 'a'), ('context', 'd'),
    ('members', 'h[a a d] c'), ('holders', 'h[a a a d] c'), ('above', 'h[a a a d] c')]
FRAME = [('people', 'h[a] c'), ('roles', 'h[a] a'), ('topic', 'a'), ('anchor', 'd'), ('context', 'd'),
    ('activities', 'h[a a a d] c'), ('descriptions', 'h[a a] ' + EXECUTION),
    ('assessed', 'h[a a d] c'), ('eligible', 'h[a] c')]
FIELD = [('source', 'a')] + FRAME + [('required', RULE), ('allowed', RULE)]
CONFIG = [(n, t) for n, t in FIELD if n not in ('source', 'context')]
DUTY = [('assessor', 'a'), ('office', 'a'), ('policy', POLICY), ('required', POLICY_RULE), ('allowed', POLICY_RULE)]
SOURCE_FIELD = [(n, t) for n, t in FIELD if n not in ('eligible', 'required', 'allowed')]
SOURCE_CONFIG = [(n, t) for n, t in SOURCE_FIELD if n not in ('source', 'context')]
SOURCE_DUTY = DUTY[:3]
ROOTS = ['rm2', 'rm3', 'rm4', 'rm5', 'rm6', 'rm7']


def definitions():
    member = lambda role: app(v('members'), v(role), v('organization'), v('context'))
    holder = lambda person: app(v('holders'), v(person), v('office'), v('organization'), v('context'))
    scope = 'i[role a][' + member('role') + ']'
    order = 'i[first a second a][' + app(v('above'), v('first'), v('second'), v('organization'), v('context')) + ']'
    text = definition('rm2', params(HEAD), both(k('rex', scope, order), member('office'), holder('person'),
        quant('f', 'other', 'a', op('y', holder('other'), op('e', v('other'), v('person')))),
        quant('f', 'role', 'a', op('y', both(member('role'), op('u', op('e', v('role'), v('office')))),
            app(v('above'), v('office'), v('role'), v('organization'), v('context'))))))
    selected = app(v('people'), v('person'))
    relevant = app(v('activities'), v('person'), v('activity'), v('topic'), v('anchor'))
    text += definition('rm3', params(FRAME), both(quant('g', 'person', 'a', selected),
        quant('f', 'person', 'a', op('y', selected, both(app(v('eligible'), v('person')),
            quant('g', 'activity', 'a', relevant), quant('f', 'activity', 'a', op('y', relevant,
                app(v('assessed'), v('person'), v('activity'), v('context')))))))))
    fields = [v('source'), v('person'), app(v('roles'), v('person')), v('activity'), app(v('descriptions'), v('person'), v('activity'))]
    requirement = lambda sign: app(v('required'), *fields, sign, v('context'))
    permission = lambda sign: k('rdm', *fields, sign, v('context'), v('required'), v('allowed'))
    everyone = lambda condition: quant('f', 'person', 'a', quant('f', 'activity', 'a',
        op('y', both(selected, relevant), condition)))
    text += definition('rm4', params(FIELD), both(k('rm3', *args(FRAME)), everyone(both(
        op('u', requirement(TRUE)), op('u', requirement(op('u', TRUE)))))))
    text += definition('rm5', params(FIELD), both(k('rm3', *args(FRAME)), everyone(both(permission(TRUE), permission(op('u', TRUE))))))
    policy = both(k('rdr', v('bindings'), 'n p b b'), quant('g', 'source', 'a', both(
        'a[v bindings][n p a b][v source]', k('rm5', *args(FIELD)))))
    text += definition('rm6', params(CONFIG), 'i[bindings j[a]][b context[' + policy + ']]', 'h[j[a]] e')
    valid = 'i[items j[a]][' + k('rdr', v('items'), 'n p b b') + ']'
    obligation = k('rds', v('assessor'), v('person'), v('office'), v('policy'), v('bindings'), TRUE,
        v('context'), valid, v('required'), v('allowed'))
    content = both(k('rdr', v('bindings'), 'n p b b'), quant('g', 'person', 'a', both(
        'a[v bindings][n p a b][v person]', obligation)))
    text += definition('rm7', params(DUTY), 'i[bindings j[a]][b context[' + content + ']]', 'h[j[a]] e')
    return text


MEANINGS = {
    'rm2': '同じ組織・文脈で役職順序が非反射的かつ推移的で、指定役職が範囲内の他の全役職より上にあり、指定本人だけがその役職を保持する。単に上位役職が見つからない場合とは区別する。',
    'rm3': '対象者が非空で全員が適格であり、同じ主題と基準時点で固定した各人の対象活動が非空で、その全活動について現在の評価が済んでいる。',
    'rm4': 'rm3の同じ出所・対象者・立場・活動・実行記述に対して、実行要求も不実行要求もない。積極的な許可、実行可能性、他の出所の規範は補わない。',
    'rm5': 'rm3の同じ範囲について、実行と不実行の双方が積極的に許され、反対要求との衝突がない。その出所が何も要求せず両方を許すという規範上の選択を表す。',
    'rm6': 'ちょうど一個体の引数列を規範の出所として受け取り、固定した主題・対象者・活動・記述のrm5を返す政策内容関数。別の出所や余分な引数へ置き換えない。',
    'rm7': 'ちょうど一人の引数列について、指定の規範的な評価出所が、その同じ本人に指定役職で、同じ政策記述と本人を引数にした内容の成立を要求するという内容関数。政策の成立は実行評価しない。',
    'hzfn': 'rm2の唯一の最高役職保持者が人aaであり、同じ役職を同じ時点に委ねられているcfを要求する。君主の制度的位置への部分候補であり、最高役職だけから国家・世襲・正当性・命令権を補わない。',
    'hzfo': 'rm5の適格性を人aa、実行と不実行の規範を同じ出所のh7a・h7bへ接続する。宗教という主題の具体的な活動範囲は入力で保持する。',
    'hzfp': 'rm6に人aaとh7a・h7bを固定し、同じ本人を規範の出所として、主題範囲内の人々へ両方の選択を許す政策内容を作る。',
    'hzfq': 'rm7の外側の義務をh7k・h7lへ接続する。政策の規範の出所と、本人の義務を評価する出所を別に保持する。',
}
LIMITS = [
    'rm2は同じ組織の役職範囲内の唯一の最高保持者という強い構造条件。政治共同体の成立、主権、世襲、実効支配、正当性、他組織に対する優越は含まない。空席・共同保持・比較不能な別の頂点を一人の最高者へ補完しない。',
    '自由の条件は指定した一つの規範源・主題・対象範囲に限る。他の規範源、物理的な実行可能性、宗教の全語義、権利の保障や実際の不干渉までは含まない。',
    '活動範囲は同じ主題と基準時点に固定する。評価不足や空範囲を、命令がないことや全面的な自由の証拠として使わない。対象範囲の現実的な網羅性は残る。',
    '規範対象の記述は本人・活動ごとに保持し、同じ真偽を持つ別名へ移さない。記述の内部を実行して自由や義務を認定しない。',
    '本人が義務だと考える内容は、hzfqを閉じた基準記述として既存rlgの同じ本人・判断・候補状況へ渡す。本人の判断、実際の義務、実際の政策を区別する。候補モデルは信念一般の完成した理論ではない。',
    'u0015冒頭の君主と、宗教上の非指図・自由を自分の義務とする内容への部分注記。口頭での表明、品位の評価、寛容という名称の拒否、称賛、政府による解放、後続の職務・公的使用・波及・自己発達は未完。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += definition('hzfn', params(HEAD), both(k('rm2', *args(HEAD)), k('aa', v('person')), k('cf', v('person'), v('office'), v('context'))))
    text += definition('hzfo', params(SOURCE_FIELD), k('rm5', *args(FIELD, eligible='p aa', required='p h7a', allowed='p h7b')))
    text += definition('hzfp', params(SOURCE_CONFIG), k('rm6', *args(CONFIG, eligible='p aa', required='p h7a', allowed='p h7b')), 'h[j[a]] e')
    text += definition('hzfq', params(SOURCE_DUTY), k('rm7', *args(DUTY, required='p h7k', allowed='p h7l')), 'h[j[a]] e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-named-epochs-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-scoped-nonprescription-basis-v1', document='examples/v014/kant-scoped-nonprescription.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS + ['rlg'], 'scoped-nonprescription')
def core_composed(): return projected(ROOTS + ['rlg', 'hzfn', 'hzfo', 'hzfp', 'hzfq', 'fa', 'fb'], 'scoped-nonprescription-core')
BUILDERS = ((generic_composed, 'scoped-nonprescription'), (source_composed, 'kant-scoped-nonprescription'), (core_composed, 'scoped-nonprescription-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored non-prescription differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
