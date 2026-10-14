"""Compose temporal cohorts with response scope, without collective unanimity."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_successive_cohorts import PAIR, COHORT, MEMBERSHIP, FRAME
from scripts.compose_deserved_responses import PRESENTATION

PARENT = 'examples/v014/kant-limited-release.noema'
PAIRING = [('firstgroup', 'a'), ('nextgroup', 'a'), ('earlier', 'a'), ('later', 'a')] + MEMBERSHIP + FRAME
SOURCE_PAIRING = [(n, t) for n, t in PAIRING if n not in ('human', 'before')]
SCOPE = [('group', 'a'), ('epoch', 'a'), ('context', 'd'), ('belongs', 'h[a a d] c'), ('periods', 'h[a d] c')]
REPLY = SCOPE + [('response', 'h[a a a] e')]
TARGET = [('subject', 'a')] + REPLY
DUAL = [('firstgroup', 'a'), ('nextgroup', 'a'), ('earlier', 'a'), ('later', 'a')] + SCOPE[2:] + PRESENTATION[:2]
ROOTS = ['roj', 'rok', 'rol', 'rom', 'ron']


def definitions():
    pair = both(op('u', op('e', v('firstgroup'), v('nextgroup'))), k('rjd', *args(PAIR)),
        app(v('periods'), v('earlier'), v('context')),
        k('rjg', *args(COHORT, group=v('firstgroup'), epoch=v('earlier'))),
        k('rjg', *args(COHORT, group=v('nextgroup'), epoch=v('later'))))
    text = definition('roj', params(PAIRING), pair)
    member = app(v('belongs'), v('group'), v('speaker'), v('context'))
    within = app(v('periods'), v('epoch'), v('point'))
    responds = op('t', app(v('response'), v('speaker'), v('activity'), v('subject')), v('point'))
    text += definition('rok', params(REPLY), 'i[speaker a activity a subject a][b point[' + both(member, within, responds) + ']]', 'h[a a a] e')
    actual = op('t', app(k('rok', *args(REPLY)), v('speaker'), v('activity'), v('subject')), v('point'))
    some = quant('g', 'speaker', 'a', quant('g', 'activity', 'a', actual))
    text += definition('rol', params(TARGET), 'b point[' + some + ']', 'e')
    nonempty = quant('g', 'speaker', 'a', member)
    everyone = quant('f', 'speaker', 'a', op('y', member, quant('g', 'activity', 'a', actual)))
    text += definition('rom', params(TARGET), 'b point[' + both(nonempty, everyone) + ']', 'e')
    eventually = quant('f', 'speaker', 'a', op('y', member,
        quant('g', 'point', 'd', quant('g', 'activity', 'a', actual))))
    text += definition('ron', params(TARGET), both(nonempty, eventually))
    return text


MEANINGS = {
    'roj': '同じ母集団・生存・所属・基準文脈で、異なる二集団を順序付けられた二時代へrjgで結ぶ。基準文脈は前の時代に属する。直後の時代であること、構成員が互いに異なることは要求しない。',
    'rok': '同じ基準文脈で集団に属する話者が、指定時代内の時点で、同じ行為・同じ対象者について応答する内容関数。集団の所属、応答者、時点を一緒に限定する。実際の応答はこの関数の記述だけでは断言しない。',
    'rol': '同じ時点に、指定集団の少なくとも一人が指定時代内で同じ対象者へ応答する。代表資格や集団全体の意思、全員による応答を伴わない。',
    'rom': '指定集団が空でなく、全構成員が同じ時点に同じ対象者へ応答する。行為は各人で異なってよい。時代内の別々の時点で応答するだけでは足りない。',
    'ron': '指定集団が空でなく、各構成員が指定時代内のいずれかの時点に同じ対象者へ応答する。時点も行為も各人で異なってよい。同時の応答や将来の必然性は要求しない。',
    'hzgi': 'rojの人間をaa、時間順序を同じ基準文脈のicへ接続する。現在と後続時代の人々という世界・後世の部分解釈。選んだ母集団と時代範囲を隠さない。',
    'hzgj': '現在集団・現在時代のrokと、後続集団・後続時代のrokのいずれかに合うhzgbの提示行為を記述する。話者・行為・対象者は両側で共通に束縛する。両集団が実際に応答したこと、全員の称賛、集団の代表を断言しない。',
}
LIMITS = [
    '世界を地球そのものではなく、明示した現在の人々として読む候補である。母集団の全世界への網羅性、感謝、称賛と肯定的報告の違い、文化・社会の構成は未確定である。',
    '後世は直後の一世代に限定しない。rojはrjfの直後関係ではなくrjdの先後を使い、中間の時代と同一人物の生存期間の重なりを許す。ただし時代区間そのものの重なりは許さない。無限の未来全体を有限の検査で確認したとはしない。',
    'rjgの生存と所属を照合する時点は基準文脈で固定する。役職の代表権、構成員の全員同意、集団の共同意図、遺伝的な世代交代はここから導かない。',
    'rokからronは所属・時代・応答の作用範囲を説明する一般式であり、rojの時代・生存条件は自動では追加しない。原文の集団として解釈するときは、hzgiの照合結果を別途確認する。',
    'hzgjは選択的な応答記述である。ro6の応答記述として渡せるが、記述の適合から実際の応答、両集団での発生、全員の応答、将来必ず起きることへは進めない。全員について述べる場合はromまたはronを明示する。',
    '有限解釈器は条件の両辺や内容の全状況を評価する。所属しない人や範囲外の時点についても入力関数値を要求する場合がある。未知の値を偽として埋めない。',
    'Welt und Nachweltへの集団・時間の部分注記であり、文全体の同義性は未確認。ro6に渡す功績の根拠と応答適合基準、感謝・称賛・人類の未成熟・良心の説明、後続本文、全文確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    before = 'i[first d second d][' + k('ic', v('first'), v('second'), v('context')) + ']'
    text = definitions() + definition('hzgi', params(SOURCE_PAIRING), k('roj', *args(PAIRING, human='p aa', before=before)))
    response = k('hzgb', v('audience'), v('message'))
    def scoped(group, epoch):
        return op('t', app(k('rok', *args(REPLY, group=v(group), epoch=v(epoch), response=response)),
            v('speaker'), v('activity'), v('subject')), v('point'))
    text += definition('hzgj', params(DUAL), 'i[speaker a activity a subject a][b point[' + op('x', scoped('firstgroup', 'earlier'), scoped('nextgroup', 'later')) + ']]', 'h[a a a] e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-limited-release-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-cohort-responses-basis-v1', document='examples/v014/kant-cohort-responses.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'cohort-responses')
def core_composed(): return projected(ROOTS + ['hzgi', 'hzgj', 'ro6'], 'cohort-responses-core')
BUILDERS = ((generic_composed, 'cohort-responses'), (source_composed, 'kant-cohort-responses'), (core_composed, 'cohort-responses-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored cohort responses differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as f: f.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
