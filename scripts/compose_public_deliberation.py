"""Ground public information growth and a genuinely shared possible proposal."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_epistemic_revision import CHANGE
from scripts.compose_provisional_order import CONFIG, SOURCE as CONTINUING

PARENT = 'examples/v014/kant-provisional-order.noema'
REVIEW = [('audience', 'a'), ('reviews', 'h[a a a d] c'), ('used', 'h[a a d] c'),
    ('supports', 'h[a a d] c'), ('accessible', 'h[a a d] c'), ('disclosed', 'h[a a d] c')]
GROUND = [('holder', 'a'), ('claim', 'a'), ('stage', 'd')] + REVIEW
PUBLIC = CHANGE + REVIEW
PROPOSAL = [('group', 'a'), ('population', 'a'), ('anchor', 'd'), ('members', 'h[a a d] c'),
    ('proposal', 'i[e]'), ('recipient', 'a'), ('context', 'd'), ('occurs', 'h[a d] c'),
    ('participates', 'h[a a d] c'), ('addresses', 'h[a a d] c'), ('proposes', 'h[a a i[e] d] c')]
POSSIBLE = [(n, t) for n, t in PROPOSAL if n != 'context'] + [
    ('available', 'h[a a d] c'), ('outcomes', 'h[a a d d] c')]
MILESTONE = PUBLIC + [(n, t) for n, t in POSSIBLE if n not in ('population', 'anchor')]
SOURCE = [(n, t) for n, t in MILESTONE if n not in ('after', 'used', 'supports', 'occurs', 'participates')] + [
    ('subject', 'a'), ('about', 'h[a a d] c')]
# The public is the holder whose information is compared, and is also the population.
# The audience of evidence is shared with the audience of public criticism.
CONTINUATION = CONFIG + [('histories', 'h[d] h[d] c')] + [
    (n, t) for n, t in SOURCE if n not in ('holder', 'audience', 'before', 'subject')]
ROOTS = ['rkm', 'rkn', 'rko', 'rkp', 'rkq', 'rkr']


def definitions():
    ground = both(app(v('reviews'), v('holder'), v('review'), v('claim'), v('stage')),
        app(v('used'), v('review'), v('reason'), v('stage')),
        app(v('supports'), v('reason'), v('review'), v('stage')),
        app(v('accessible'), v('audience'), v('reason'), v('stage')))
    text = definition('rkm', params(GROUND), both(app(v('disclosed'), v('audience'), v('claim'), v('stage')),
        quant('g', 'review', 'a', quant('g', 'reason', 'a', ground))))
    item = k('ri2', v('holder'), v('claim'), v('after'), v('assessment'), v('corpus'), v('supported'), v('contents'))
    text += definition('rkn', params(PUBLIC), both(k('ri5', *args(CHANGE)),
        quant('f', 'claim', 'a', op('y', both(app(v('scope'), v('claim')), item),
            k('rkm', *args(GROUND, stage=v('after')))))))
    member = lambda person: app(v('members'), v('group'), v(person), v('anchor'))
    plural = quant('g', 'first', 'a', quant('g', 'second', 'a', both(member('first'), member('second'),
        op('u', op('e', v('first'), v('second'))))))
    citizen = app(v('members'), v('population'), v('person'), v('anchor'))
    joined = quant('f', 'person', 'a', op('y', member('person'), both(
        app(v('participates'), v('person'), v('act'), v('context')),
        app(v('proposes'), v('person'), v('act'), v('proposal'), v('context')))))
    text += definition('rko', params(PROPOSAL), both(plural,
        quant('f', 'person', 'a', op('y', member('person'), citizen)),
        quant('g', 'act', 'a', both(app(v('occurs'), v('act'), v('context')),
            app(v('addresses'), v('act'), v('recipient'), v('context')), joined))))
    goal = 'b context[' + k('rko', *args(PROPOSAL)) + ']'
    for name, ability in (('rkp', 'xb'), ('rkq', 'xc')):
        text += definition(name, params(POSSIBLE), k(ability, v('group'), goal, v('anchor'), v('available'), v('outcomes')))
    text += definition('rkr', params(MILESTONE), both(k('rkn', *args(PUBLIC)),
        k('rkp', *args(POSSIBLE, population=v('holder'), anchor=v('after')))))
    return text


MEANINGS = {
    'rkm': '同じ主体・命題項目・段階への検討行為があり、その同じ検討で用いる理由が検討を支持し、理由と命題項目が同じ公衆に開示・アクセス可能である。別の判断の理由や別の命題の開示を流用しない。',
    'rkn': 'ri5の同一範囲・同一評価による厳密な情報増加を保ち、後段階の範囲内の全ての正しく支持された受容項目にrkmを要求する。私的な既知情報の公開だけを情報増加へ読み替えない。',
    'rko': '基準時点で固定した二人以上の提案集団が同時点の公衆に含まれ、その全員が同じ生起行為に参加し、同じ採用を求める内容記述を同じ相手に共同提示する。集団外の全市民の賛同や、提案内容の実現・真理は要求しない。',
    'rkp': '同じ提案集団に基準時点で利用可能な方法があり、その想定結果の少なくとも一つでrkoが成立する。成員を結果時点で選び直さず、現実の提案済みや成功保証とも区別する。',
    'rkq': '同じ利用可能な方法について想定結果が非空で、その全てでrkoが成立する。可能性rkpより強い成功保証として比較する。',
    'rkr': 'rknの後段階で、同じ情報主体を公衆とするrkpの共同提案が可能である。情報増加と別の段階での提案可能性を混ぜず、両条件の因果関係はこの連言から推定しない。',
    'hzef': 'rkrを既存の理由使用fc・支持fd・行為生起dg・共同参加dfへ接続する内容。命題範囲は同じ評価状況で同じ対象についてのものに限定する。前段階は評価文脈のicで後段階より前にあり、提案方法の結果も開始段階より後にある。',
    'hzeg': 'hzecの到達条件へhzefを渡す。根拠公開と公的批判の公衆、情報の主体と制度の市民集団、開始時点と比較の前段階、情報の対象と制度を共有する。提案集団の市民資格には継続条件と同じcitizensを用いる。到達前の維持と到達を要求する。',
    'hzeh': 'hzegと同じ具体的な到達内容を、到達しない持続も許すhzedへ渡す。',
    'hzei': 'hzegと同じ具体的な到達内容を、到達点でも秩序と公的批判の許可を要求するhzeeへ渡す。',
}
LIMITS = [
    'rknは意味内容による情報の厳密な増加と、公開された支持理由による確認を組み合わせる解釈候補である。Einsichtやbewähretの語義全て、理解の深さ・証明の発見・実践的な確認を尽くさない。',
    'reviewsは同じ主体に帰属する検討と同じ命題項目を結び、usedとsupportsは理由の使用と支持を区別する。検討への帰属、支持の健全性、証拠の信頼性、公開可能性の現実の成立は明示した関係の解釈を要する。全市民が知ること・同意することは補わない。',
    'ri5のcorpus・supported・contents・scope・comparisons・assessmentを固定し、その比較上の限界を保持する。真偽・支持の未知を偽や空集合で補わない。',
    '提案集団は少なくとも二人で、全員が同じ行為・提案記述・相手へ結ばれる。全市民の集団でも真部分集団でもよい。集団の形成手続、代表制、団結の強さ、全員でなくてもよいという譲歩の談話効果は未構成。',
    '提案は閉じた内容記述として渡し、提案した事実の検査で内容を実行評価しない。改正・保護・妨害禁止という提案内容そのもの、宛先が君主である制度的説明は今回の接続だけでは完成しない。',
    'rkrは情報進展と提案可能性が同じ時点で成立する到達条件であり、情報進展が提案能力を生じさせるという因果説明ではない。so weitの程度尺度、一定の短い期間、期待、著者帰属と原文全体の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    future = 'i[actor a plan a start d end d][' + both(app(v('outcomes'), v('actor'), v('plan'), v('start'), v('end')),
        k('ic', v('start'), v('end'), v('assessment'))) + ']'
    scope = 'i[claim a][' + both(app(v('scope'), v('claim')),
        app(v('about'), v('claim'), v('subject'), v('assessment'))) + ']'
    body = both(k('ic', v('before'), v('after'), v('assessment')),
        k('rkr', *args(MILESTONE, scope=scope, used='p fc', supports='p fd', occurs='p dg', participates='p df', outcomes=future)))
    text = definitions() + definition('hzef', params(SOURCE), 'b after[' + body + ']', 'e')
    is_population = op('e', v('owner'), v('population'))
    members = 'i[owner a person a point d][' + op('x',
        both(is_population, app(v('citizens'), v('population'), v('person'), v('point'))),
        both(op('u', is_population), app(v('members'), v('owner'), v('person'), v('point')))) + ']'
    milestone = k('hzef', *args(SOURCE, holder=v('population'), before=v('context'), subject=v('regime'), members=members))
    for name, parent in (('hzeg', 'hzec'), ('hzeh', 'hzed'), ('hzei', 'hzee')):
        text += definition(name, params(CONTINUATION),
            'b context[' + op('t', k(parent, *args(CONTINUING, milestone=milestone)), v('context')) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-provisional-order-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-public-deliberation-basis-v1', document='examples/v014/kant-public-deliberation.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'public-deliberation')
def core_composed(): return projected(ROOTS + ['hzef', 'hzeg', 'hzeh', 'hzei', 'reu'], 'public-deliberation-core')
BUILDERS = ((generic_composed, 'public-deliberation'), (source_composed, 'kant-public-deliberation'), (core_composed, 'public-deliberation-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored public deliberation differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
