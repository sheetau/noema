"""Keep reporting a judgment distinct from holding it and from its truth."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, quant
from scripts.compose_situated_criticism import params, args, MESSAGE
from scripts.compose_personal_criteria import JUDGING, APPRAISAL
from scripts.compose_policy_norms import DESCRIPTION
from scripts.compose_institutional_voice import PRESENTATION

PARENT = 'examples/v014/kant-scoped-nonprescription.noema'
BELIEF = [('criterion', DESCRIPTION)] + JUDGING
SOURCE_BELIEF = [(n, t) for n, t in BELIEF if n not in ('judgments', 'matters')]
REPORT = [('person', 'a'), ('activity', 'a'), ('audience', 'h[a] c'), ('message', MESSAGE), ('context', 'd')] + PRESENTATION
SOURCE_REPORT = REPORT[:5]
SETTINGS = [(n, t) for n, t in REPORT if n not in ('person', 'activity', 'context')]
SOURCE_SETTINGS = [('audience', 'h[a] c'), ('message', MESSAGE)]
ROOTS = ['rna', 'rnb', 'rnc', 'rnd']


def definitions():
    judgment = k('rlg', *args(APPRAISAL, subject=v('person'), bindings='l[a][v person]'))
    content = 'i[person a][b context[' + quant('g', 'judgment', 'a', judgment) + ']]'
    text = definition('rna', params(BELIEF), content, 'h[a] e')
    text += definition('rnb', params(BELIEF), 'i[person a][j s[' + app(k('rna', *args(BELIEF)), v('person')) + ']]', 'h[a] f')
    text += definition('rnc', params(REPORT), k('rfo', v('person'), v('activity'), v('audience'), v('person'), v('message'), v('context'), *args(PRESENTATION)))
    text += definition('rnd', params(SETTINGS), 'i[person a activity a][b context[' + k('rnc', *args(REPORT)) + ']]', 'h[a a] e')
    return text


MEANINGS = {
    'rna': '同じ本人を判断主体・判断対象・基準の唯一の引数として、その文脈でrlgの条件を満たす判断があるという内容関数。実際に基準内容が真であることは要求しない。',
    'rnb': 'rnaの同じ本人についての判断存在を述べる主張発話の関数。基準内容そのものを直接主張する発話とは区別する。構成だけでは発話・判断・基準の真理を認めない。',
    'rnc': '実際に起きる同じ提示行為で、本人が非空の受け手群へ、本人を対象とする同じ発話記述を示す。受け手を発話の対象へすり替えない。',
    'rnd': '受け手群と発話記述を固定し、本人と行為からrncの実行条件を表す内容を作る。条件を引用して評価や規範の対象にでき、引用しただけでは発話の実行を断言しない。',
    'hzfr': 'rnaの判断主体と判断対象を既存fa・fbへ接続する。基準にhzfqの閉じた義務記述を渡すと、同じ本人がその政策を自分の義務と考える内容になる。',
    'hzfs': 'hzfrと同じ判断存在を主張する発話の関数。本人の義務判断についての自己報告の内容を構成し、義務そのものや政策の実施を直接主張しない。',
    'hzft': 'rncの実行条件を既存dg・f3・f2へ接続する。話者本人・提示行為・受け手群・本人についての発話記述を同じ文脈で保持する。',
    'hzfu': 'rndをdg・f3・f2へ接続した本人と行為の内容関数。hzfsの閉じた発話記述を渡した接続例では、その義務判断を報告する行為の条件を引用できる。',
}
LIMITS = [
    '発話が本人についての判断存在を報告すること、本人が実際にその判断を持つこと、その判断基準が実際に真であること、政策が成立することを独立に保つ。虚偽の報告が可能で、提示から誠実さを補わない。',
    '受け手群は明示した非空の範囲である。全公衆への到達、受領、理解、同意、口頭か筆記かの媒体を含まない。本人が受け手でもよいが、非空性は必要である。',
    'rnaは指定基準に対する同じ本人の判断が一つ以上あることを述べる。原文が特定の判断個体を命名したこと、全状況での安定した信念、記憶や自己認識の一般理論を要求しない。',
    '基準が未知のまま脱引用する関数は引用できない。原文の義務内容の閉じた記述を静的に代入し、脱引用を除いてから発話記述を引用する。別名の記述の同一性は変更しない。',
    'rnc・hzftは任意の本人についての発話記述を受け取る。自己の義務判断の報告という内容は、同じ基準のrnb・hzfsを渡す接続例によって保証する。型だけで任意の発話内容を同一視しない。',
    'u0015のzu sagen以下の発話内容への部分注記。原文の品位の評価の対象となる行為として埋め込めるよう構成するが、その評価内容は未構成であり、原文が実際の発話を断言したとはしない。品位、寛容という呼称の拒否、称賛と段落全体の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target, result in (('hzfr', 'rna', 'h[a] e'), ('hzfs', 'rnb', 'h[a] f')):
        text += definition(name, params(SOURCE_BELIEF), k(target, *args(BELIEF, judgments='p fa', matters='p fb')), result)
    text += definition('hzft', params(SOURCE_REPORT), k('rnc', *args(REPORT, occurs='p dg', presents='p f3', conveys='p f2')))
    text += definition('hzfu', params(SOURCE_SETTINGS), k('rnd', *args(SETTINGS, occurs='p dg', presents='p f3', conveys='p f2')), 'h[a a] e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-scoped-nonprescription-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-self-reports-basis-v1', document='examples/v014/kant-self-reports.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS + ['rm2', 'rm3', 'rm4', 'rm5', 'rm6', 'rm7'], 'self-reports')
def core_composed(): return projected(ROOTS + ['hzfr', 'hzfs', 'hzft', 'hzfu', 'rm2', 'rm3', 'rm4', 'rm5', 'rm6', 'rm7', 'hzfn', 'hzfo', 'hzfp', 'hzfq'], 'self-reports-core')
BUILDERS = ((generic_composed, 'self-reports'), (source_composed, 'kant-self-reports'), (core_composed, 'self-reports-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored self-report differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
