"""Describe associations by their members' commissioned tasks, not a noun ID."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_solemn_undertakings import SOURCE_PURPOSE

PARENT = 'examples/v014/kant-solemn-undertakings.noema'
TASK = 'i[h[a] e]'
MEMBERSHIP = 'h[a a d] c'
SERVES = 'h[a a a d] c'
DESIGNATES = 'h[a a ' + TASK + ' d] c'
POPULATION = [('group', 'a'), ('context', 'd'), ('belongs', MEMBERSHIP), ('human', 'h[a] c')]
OFFICE = [('person', 'a'), ('principal', 'a'), ('role', 'a'), ('task', TASK), ('context', 'd'),
    ('human', 'h[a] c'), ('entrusted', 'h[a a d] c'), ('serves', SERVES), ('designates', DESIGNATES)]
ASSOCIATION = [('group', 'a'), ('task', TASK), ('context', 'd'), ('belongs', MEMBERSHIP)] + OFFICE[5:]
SOURCE = [(n, t) for n, t in ASSOCIATION if n not in ('human', 'entrusted')]
RELIGIOUS = [(n, t) for n, t in SOURCE if n != 'task']
UNDERTAKING = [(n, t) for n, t in SOURCE_PURPOSE if n != 'parties'] + [(n, t) for n, t in RELIGIOUS if n != 'context']
ROOTS = ['rir', 'ris', 'rit', 'riu']


def definitions():
    member = lambda person: app(v('belongs'), v('group'), v(person), v('context'))
    two = quant('g', 'left', 'a', quant('g', 'right', 'a', both(member('left'), member('right'), op('u', op('e', v('left'), v('right'))))))
    text = definition('rir', params(POPULATION), both(two, quant('f', 'person', 'a', op('y', member('person'),
        both(app(v('human'), v('person')), op('u', op('e', v('person'), v('group'))))))))
    text += definition('ris', params(OFFICE), both(app(v('human'), v('person')),
        app(v('entrusted'), v('person'), v('role'), v('context')),
        app(v('serves'), v('person'), v('principal'), v('role'), v('context')),
        app(v('designates'), v('principal'), v('role'), v('task'), v('context'))))
    qualified = quant('g', 'principal', 'a', quant('g', 'role', 'a', k('ris', *args(OFFICE))))
    text += definition('rit', params(ASSOCIATION), both(k('rir', *args(POPULATION)),
        quant('f', 'person', 'a', op('y', member('person'), qualified))))
    text += definition('riu', 'group a belongs ' + MEMBERSHIP,
        'i[person a context d][' + app(v('belongs'), v('group'), v('person'), v('context')) + ']', 'h[a d] c')
    return text


MEANINGS = {
    'rir': '指定文脈の同じ団体への所属が二人以上について成立し、全構成員が人であり団体自身とは異なる。人数だけの集合ではなく、団体と人の所属関係を保持する。',
    'ris': '同じ人・職務・組織・文脈について、その職務が委ねられ、本人がその組織にその職務で奉仕し、その組織がその職務の仕事として同じ活動記述を指定している。仕事の現実の実行・成功・個別行為の許可は要求しない。',
    'rit': 'rirの同じ団体の全構成員について、指定活動を仕事とするrisの組織と職務が存在する。組織と職務は人ごとに選べ、全員が同じ組織に属することや団体自身が各人の任用元であることを要求しない。',
    'riu': '同じ団体と所属関係を固定し、本人と文脈を受け取る構成員判定を作る。引受けの当事者へ渡すときも独立した別名簿へ交換しない。',
}
LIMITS = [
    'belongsは同じ団体にその人が構成員として属する関係。単に同じ場所に居合わせることや同じ職業であることと区別し、現実の所属の認定、入会・脱退・組織の存続基準は別に説明する。',
    'servesは既存の組織の名による発話と同じ奉仕関係の規約を使う。designatesは組織がその職務の仕事として活動記述を位置付ける関係で、本人の私的な活動や単発の実行とは区別する。任用・制度・役割の一般的な成立の基礎説明は残る。',
    '対象活動を閉じた記述で保持する。教義の真理、本人の確信、活動の達成を脱引用して要求しない。同義な別名の活動を自動的に同じ仕事として認定しない。',
    'rirは二人以上が現に所属する団体の条件であり、一人だけになった団体や無人期間の組織の存続を否定する一般理論ではない。ritも組織・職業一般の必要十分条件ではない。',
    '人ごとの職務の組織と、団体や契約の識別子は別の役割である。一致してよいが自動同一化しない。構成員による契約から団体全体の法人行為・代表権・契約能力を導かない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += definition('hzcx', params(SOURCE), k('rit', *args(ASSOCIATION, human='p aa', entrusted='p cf')))
    text += definition('hzcy', params(RELIGIOUS), k('hzcx', *args(SOURCE, task='r[p so]')))
    membership = k('riu', v('group'), v('belongs'))
    text += definition('hzcz', params(UNDERTAKING), both(k('hzcy', *args(RELIGIOUS)),
        k('hzcw', *args(SOURCE_PURPOSE, parties=membership))))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-solemn-undertakings-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-office-associations-basis-v1', document='examples/v014/kant-office-associations.noema')
    basis['definitions'].update(MEANINGS | {
        'hzcx': 'ritの人をaa、職務の委任をcfへ接続する。所属・奉仕・職務の仕事の指定は意味規約を明示した関係引数。',
        'hzcy': 'hzcxの活動記述を、宗教的な生き方・安寧についての判断soへ固定する。宗教上の指導職にある人々の団体への部分候補であり、全ての聖職者や教会制度の語義を尽くすとはしない。',
        'hzcz': 'hzcyの同じ団体の構成員判定riuを、そのままhzcwの目的付き・厳粛な相互引受けの当事者として渡す。基準文脈の構成員全員が引き受ける条件で、契約の成立から団体の代表権や規範的効力は導かない。'})
    basis['unresolved'] += LIMITS + [
        'u0013のGesellschaft von Geistlichenへの部分候補。soは宗教的な生き方に関する判断の既存の部分説明であり、礼拝・祭儀・教示・叙任や聖職の全機能を表し終えたものではない。cfの委任と活動指定だけで資格や制度の正当性は保証しない。',
        '同じ教会に全員が所属する、団体自身が教会である、全員が目的主体であるという追加条件を置かない。KirchenversammlungとKlassisの例示・歴史的制度・呼称、教会と団体の同定、組織としての行為の帰属は未完。',
        '所属関係の範囲は明示した解釈で与え、未知の所属を偽として落とさない。hzczの当事者は基準文脈に固定し、各過去の宣誓時点で別の人々へ選び直さない。新しい著者主張・原始記号は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'office-associations')
def core_composed(): return projected(ROOTS + ['hzcx', 'hzcy', 'hzcz', 'rim', 'rin'], 'office-associations-core')
BUILDERS = ((generic_composed, 'office-associations'), (source_composed, 'kant-office-associations'), (core_composed, 'office-associations-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored office association differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
