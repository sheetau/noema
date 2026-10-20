"""Keep ranked appointment terms identical to the independently stated duty."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_confessional_teaching import NAMES, FIELDS, ARGS

PARENTS = ('data/public-civic-opinion-basis-v1.json', 'data/confessional-teaching-basis-v1.json')
LIBRARY = 'examples/v016/ranked-appointment.noema'
BASIS = 'data/ranked-appointment-basis-v1.json'
CODE = 'i b[h[j[a] d] e]'
BIND_NAMES = (*NAMES, 'activity')
BINDINGS = 'l[a][' + ' '.join('v ' + n for n in BIND_NAMES) + ']'
OPEN_FIELDS = 'issuer a person a role a target ' + CODE + ' bindings j[a] reference d polarity c point d'
OPEN_ARGS = 'v issuer v person v role v target v bindings v reference v polarity v point'
PRIMITIVES = {
    'h246m': ('[a ' + CODE + ' j[a] d c d] c',
        ['event', 'target', 'bindings', 'reference', 'polarity', 'point'],
        'この任用行為に付された実行上の条件に、段階1の閉じた内容関数へ同じ順序の個体列と同じ基準点を渡した内容を、指定極性で満たすことが含まれる。最後の点は条件が付された任用時点であり、内容の基準点と区別する。生起・任用主体・本人・職務は同じ行為へ別に結ぶ。過去の履行済み、本人の承諾、採用資格、教義への信念、契約の法的有効性や現在の義務を含意しない。'),
}
MEANINGS = {
    'r35w': '本人・職務・教会・会衆・生徒範囲・会衆成員範囲・信条・主題・基準・活動の正確な十個体列と内容基準を、同じr35vの教示内容へ束縛する閉じたアダプター。余分・不足を許さず、全発話記述域を保持する。段階1で引用できる。',
    'r35x': 'rfxの過去任用の構造を段階1の目標・個体束縛・内容基準へ一般化する。同じ本人のia履歴とic順序がtaを満たし、現在点より前の同じ時点に、同じ行為が生起し、同じ出所が本人へ同じ職務を任用し、同じ目標・束縛・基準・極性を条件として付す。現在の義務や内容の実行は要求しない。',
    'r35y': 'r35xを満たす一組の任用行為と過去時点が存在する。別々の任用や時点から条件を寄せ集めず、最初の任用、一意性や現在までの委任の継続は要求しない。',
    'r35z': '同じ出所・本人・職務・段階1目標・束縛・内容基準・極性について、過去任用条件r35yと現在点の要求h237zが併存する。過去任用から現在の義務を導出する規則ではなく、二事実を別々に要求する。',
    'r352': '同じ教会を制度上の規範出所とし、同じ本人・職務へ、r35wに同じ十個体列と固定基準を渡した教示内容を正極性で要求する内容。実際の教示、信条への確信や法的正当性は要求しない。',
    'r353': '同じ教会を出所として本人が同じ職務へ過去に任用され、その同じ任用にr352と同じ閉じた教示記述・十個体列・内容基準・正極性が条件として付されていたという内容。教会の名による任用として読み、特定の任命者名や儀礼は補わない。',
    'r354': 'r352の現在の教示要求とr353の過去任用条件を、r35zの同じ目標記述・束縛・基準・極性で接続した内容。義務・任用・教示の実行を区別する。原文のdennという著者による説明は別に必要である。',
}
LIMITS = [
    'u0012[2984,3185)の義務と同じ条件での過去任用に向けた依存群。本文、意味確認文字数、文全体の判断は更新しない。denn、Eben so、全文帰属は未統合。',
    '任用主体と義務の制度上の出所には同じ教会を渡す。教会を代表する人物の名、国家や法の承認、本人の同意、私的な信仰や信条の客観的真理を補わない。規範の正当性を任用事実だけから証明しない。',
    '過去は評価点に対する同じ本人の履歴で構成する。教示の内容基準を任用時点へ差し替えず、信条・宛先・基準の束縛を現在の要求と同じに保持する。歴史的に異なる条件から現在の同じ条件を推定する規則ではない。',
    'r352〜r354は指定活動への内容である。一文全体を一つの任意の講義への要求へ縮めず、職務上の教示の適用範囲・時機を本文統合で明示する必要がある。実際に行った活動だけで範囲を選ばず、不実行でも義務を表せることを保つ。',
    '既存rfx/rfy/rfzとh7aの意味・段階0の型は変更しない。h223k、ia、ic、ta、dg、cf、h237zを再利用し、内容を脱引用せず任用と要求を記述する。未知の条件を既知の教示内容で補わない。',
    'r35w内部の全発話記述域を有限の検査用発話へ置換しない。列の接続試験では教示r35vを明記した型付き境界として扱い、教示自体の実評価はconfessional-teachingの既存検査へ参照する。',
]


@lru_cache(None)
def parents(): return tuple(load_catalog(ROOT, p) for p in PARENTS)


def definitions():
    text = 'd r35w[bindings j[a] reference d] e[b point[' + bind(BIND_NAMES,
        't[k r35v[' + ARGS + ' v activity]][v point]') + ']].\n'
    history = 'i[at d][k ia[v person v point v at]]'
    order = 'i[first d last d][k ic[v first v last v point]]'
    text += 'd r35x[event a earlier d ' + OPEN_FIELDS + '] c[' + both(
        'k ta[' + history + ' ' + order + ']', 'k ia[v person v point v earlier]',
        'k ia[v person v point v point]', 'k ic[v earlier v point v point]',
        'k dg[v event v earlier]', 'k cf[v person v role v earlier]',
        'k h223k[v event v issuer v person v role v earlier]',
        'k h246m[v event v target v bindings v reference v polarity v earlier]') + '].\n'
    text += 'd r35y[' + OPEN_FIELDS + '] c[g event a[g earlier d[k r35x[v event v earlier ' + OPEN_ARGS + ']]]].\n'
    text += 'd r35z[' + OPEN_FIELDS + '] c[' + both('k r35y[' + OPEN_ARGS + ']',
        'k h237z[' + OPEN_ARGS + ']') + '].\n'
    concrete = 'v church v person v role r b[p r35w] ' + BINDINGS + ' v reference ' + TRUE + ' v point'
    for name, target in [('r352', 'h237z'), ('r353', 'r35y'), ('r354', 'r35z')]:
        text += 'd ' + name + '[' + FIELDS + ' activity a] e[b point[k ' + target + '[' + concrete + ']]].\n'
    return text


def build():
    old, teaching = parents(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['h223k', 'ia', 'ic', 'ta', 'dg', 'cf', 'h237z']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    for d in closure(teaching.document, ['r35v']):
        n = d['name']
        if n in imported:
            assert d == imported[n]['declaration'] and teaching.entries[n]['meaning_ja'] == imported[n]['meaning_ja']
        else: doc['declarations'].append(d); imported[n] = teaching.entries[n]
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set().union(*(set(p.entries) for p in parents()))
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'], arguments=e['arguments'],
        meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    sources = set().union(*(set(c.source_sha256) for c in parents()))
    basis = dict(status='ranked_same_appointment_terms_and_independent_duty', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(sources)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
