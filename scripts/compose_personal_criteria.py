"""Bind an adopted comparative judgment to the same person's undertaking."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_policy_norms import DESCRIPTION
from scripts.compose_mutual_undertakings import PAST
from scripts.compose_epistemic_revision import CHANGE as EPISTEMIC
from scripts.compose_institutional_choices import CHANGE, SOURCE_CHANGE, SOURCE_WISH, CONFIG, PRESERVE, POLICY_SOURCE, FALSE

PARENT = 'examples/v014/kant-institutional-choices.noema'
JUDGING = [('judgments', 'h[a a d] c'), ('matters', 'h[a a d] c'),
    ('linked', 'h[a ' + DESCRIPTION + ' j[a] d] c'), ('candidates', 'h[a d d] c')]
APPRAISAL = [('person', 'a'), ('judgment', 'a'), ('subject', 'a'), ('criterion', DESCRIPTION),
    ('bindings', 'j[a]'), ('context', 'd')] + JUDGING
KNOWLEDGE = [('phases', 'h[a a] d'), ('scopes', 'h[a a] h[a] c'),
    ('corpus', 'h[a a d] c'), ('supported', 'h[a a d] c'), ('contents', 'h[a] e'), ('comparisons', 'h[d] c')]
REASONS = JUDGING + [('standards', 'h[a a d] ' + DESCRIPTION), ('adopted', 'h[a ' + DESCRIPTION + ' d] c'),
    ('used', 'h[a a a d] c')]
BASED = CHANGE + REASONS
SOURCE = SOURCE_CHANGE + [(n, t) for n, t in REASONS if n not in ('judgments', 'matters')]
POLICY = CONFIG + [(n, t) for n, t in REASONS if n not in ('judgments', 'matters')]
ROOTS = ['rlg', 'rlh', 'rli', 'rlj']


def definitions():
    chosen = app(v('candidates'), v('judgment'), v('context'), v('point'))
    content = app('s[v criterion]', v('bindings'))
    text = definition('rlg', params(APPRAISAL), both(
        app(v('judgments'), v('person'), v('judgment'), v('context')),
        app(v('matters'), v('judgment'), v('subject'), v('context')),
        app(v('linked'), v('judgment'), v('criterion'), v('bindings'), v('context')),
        quant('g', 'point', 'd', chosen),
        quant('f', 'point', 'd', op('y', chosen, op('t', content, v('point'))))))
    slots = [('person', 'a'), ('community', 'a'), ('older', 'a'), ('newer', 'a')]
    improvement = k('ri5', *args(EPISTEMIC, holder=v('person'),
        before=app(v('phases'), v('community'), v('older')), after=app(v('phases'), v('community'), v('newer')),
        scope=app(v('scopes'), v('person'), v('community'))))
    text += definition('rlh', params(KNOWLEDGE), 'i[' + params(slots) + '][b assessment[' + improvement + ']]', 'h[a a a a] e')
    state_sort = 'h[a a a a] e'
    initial = 'i[' + params(slots) + '][' + app(v('comparison'), *args(slots)) + ']'
    shifted = 'i[' + params(slots) + '][' + app(v('state'), v('item'), v('person'), v('community'), v('older')) + ']'
    step = 'i[state ' + state_sort + ' item a][' + shifted + ']'
    folded = 'q[v bindings][' + initial + '][' + step + ']'
    text += definition('rli', 'comparison ' + state_sort, 'i[bindings j[a]][b context[' + both(
        k('rdr', v('bindings'), 'n p e b'), quant('g', 'seed', 'a', op('t', app(folded, *[v('seed')] * 4), v('context')))) + ']]', 'h[j[a]] e')
    criterion = app(v('standards'), v('person'), v('community'), v('scene'))
    comparison_bindings = 'l[a][' + ' '.join(args(slots)) + ']'
    judgment = k('rlg', *args(APPRAISAL, subject=v('community'), criterion=criterion,
        bindings=comparison_bindings, context=v('scene')))
    reason = quant('g', 'judgment', 'a', both(
        app(v('adopted'), v('person'), criterion, v('scene')),
        app(v('used'), v('person'), v('act'), v('judgment'), v('scene')), judgment))
    undertaking = k('rhy', *args(PAST, bindings='l[a][v person v community v newer]'))
    witness = quant('g', 'act', 'a', quant('g', 'scene', 'd', both(undertaking, reason)))
    text += definition('rlj', params(BASED), both(k('rlb', *args(CHANGE)),
        quant('f', 'person', 'a', op('y', app(v('parties'), v('person'), v('context')), witness))))
    return text


MEANINGS = {
    'rlg': '同じ人が同じ対象について行った判断が、同じ基準記述と順序付き引数列を対象にし、その判断で採用した非空の候補状況全てで内容が成立する。実際の評価状況で真であることは条件にしない。',
    'rlh': '本人・共同体・旧制度・新制度に、同じ命題範囲・内容・支持・比較範囲と、二制度に対応する認識段階を結び、ri5の正しく支持された情報の厳密な増加を比較内容にする。基準自体は評価状況に相対的で、本人の判断として埋め込んでも現実の増加を要求しない。',
    'rli': '四引数の比較内容を、本人・共同体・旧制度・新制度の順序付き四個体列へ接続する。順序・重複と全ての位置を保持し、長さが四でない列を拒否する。',
    'rlj': 'rlbの制度変更への合意について、各当事者の同じ引受け表明・時点で、本人が採用した基準に関するrlgの判断を理由として使う。判断の基準と引数列を同じ本人・共同体・旧制度・新制度へ固定する。無関係な判断や事後の理由を流用しない。',
    'hzeo': 'rljを、人aa、表明行為dg・f3、同じ文脈の時間順序ic、本人の判断faと対象fbへ接続する変更条件の内容。',
    'hzep': 'hzenの変更側をhzeoの本人の判断に基づく合意へ強める。旧制度を望む側、保護する条項、政策・共同体・モデル・観測の結合は同じ構成を保持する。',
}
LIMITS = [
    '候補状況による判断は、矛盾した信念や論理的全知を含む認識一般の完成した理論ではない。候補は判断と時点に属し、現実の状況を含むとは限らない。',
    'standardsはその人・共同体・判断時点の基準記述、adoptedは本人がその基準を採用していること、linkedは同じ判断対象の記述と引数列、usedは同じ引受け表明でその判断を理由に用いたことを表す。これらの認知過程・媒体の構成説明は残る。',
    'rlhはよりよい理解の一つの明示的な情報比較基準である。理解の仕方、恒真命題の新しい証明、洞察の質の全てを情報の増加へ還元しない。制度と認識段階の対応phasesは制度変更の因果効果を証明しない。',
    '当事者ごとに異なる基準記述を扱える。同じ基準を全員へ強制せず、異なる基準が同じ判断結果を持つことだけで記述への採用を移さない。',
    '同じ表明時点の本人の判断を理由に使うという読みを採る。事前に形成された判断の保持・再利用を一般的に説明したわけではなく、原文のnachのあらゆる読みを網羅しない。',
    '政策として引用する際は、条項と基準選択を既知の閉じた構成へ静的に特殊化する。任意の未知の基準記述を実行時に引用へ埋め込む機構は加えない。',
    '宗教制度の具体的な内容、共同体の代表資格、etwaと接続法の不確定性、君主の位置、著者帰属と全文の意味確認は未完。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    before = 'i[first d second d][' + k('ic', v('first'), v('second'), v('context')) + ']'
    text = definitions() + definition('hzeo', params(SOURCE), 'b context[' + k('rlj', *args(BASED,
        eligible='p aa', history=app(v('histories'), v('context')), before=before,
        occurs='p dg', performs='p f3', judgments='p fa', matters='p fb')) + ']', 'e')
    changes = k('hzeo', *args(SOURCE, older=app(v('olders'), v('community')), newer=app(v('newers'), v('community')),
        agreement=app(v('agreements'), v('community')), parties=app(v('parties'), v('community'))))
    stays = k('hzem', *args(SOURCE_WISH, institution=app(v('olders'), v('community')), proponents=app(v('proponents'), v('community'))))
    no_condition = 'i[community a][b point[' + FALSE + ']]'; policies = []
    for changed in (True, False):
        activity = k('rlf', *args(PRESERVE, institution=app(v('newers' if changed else 'olders'), v('community')),
            persons=app(v('parties' if changed else 'proponents'), v('community'))))
        policy = k('hzek', *args(POLICY_SOURCE,
            changeconditions='i[community a][' + changes + ']' if changed else no_condition,
            stayconditions=no_condition if changed else 'i[community a][' + stays + ']',
            activities='i[community a][' + activity + ']', goals=v('changegoals' if changed else 'staygoals')))
        policies.append(op('t', policy, v('context')))
    text += definition('hzep', params(POLICY), 'b context[' + both(*policies) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-institutional-choices-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-personal-criteria-basis-v1', document='examples/v014/kant-personal-criteria.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS + ['rld', 'rle'], 'personal-criteria')
def core_composed(): return projected(ROOTS + ['rld', 'rle', 'hzeo', 'hzep', 'hzef', 'hzen'], 'personal-criteria-core')
BUILDERS = ((generic_composed, 'personal-criteria'), (source_composed, 'kant-personal-criteria'), (core_composed, 'personal-criteria-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored personal criteria differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
