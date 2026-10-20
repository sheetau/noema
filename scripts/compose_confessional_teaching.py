"""Compose one church's profession, adopted standard and actual exposition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts.compose_prescribed_teaching import CRITERIA, CRITERION

PARENTS = ('data/public-civic-opinion-basis-v1.json', 'data/clerical-audiences-basis-v1.json')
LIBRARY = 'examples/v016/confessional-teaching.noema'
BASIS = 'data/confessional-teaching-basis-v1.json'
STANDARD = 'i[' + CRITERIA + ']'
MESSAGE = 'i[h[a] f]'
NAMES = ('person', 'role', 'church', 'congregation', 'students', 'members', 'creed', 'subject', 'standard')
FIELDS = ' '.join(n + ' a' for n in NAMES) + ' reference d'
ARGS = ' '.join('v ' + n for n in NAMES) + ' v reference'
PRIMITIVES = {
    'h246d': ('[a d] c', ['organization', 'reference'],
        '同じ基準で、継続的な成員関係と共同の実践を制度・慣行によって組織する共同体として位置付けられる。建物、当日の集まり、単に同じ性質を持つ人の集合とは区別する。法人格、国家による承認、全員の同意や特定人数は要求しない。'),
    'h246e': ('[a d] i[e]', ['formulation', 'reference'],
        '同じ定式化が表す内容の、同じ固定基準における閉じたNoema記述。自然言語本文や外部URLで代用せず、実際にNoemaで構成した内容を値として与える。内容の真理、全員の信念、特定の宗派はこの参照だけからは導かない。'),
    'h246f': ('[a a d] c', ['formulation', 'subject', 'reference'],
        'この定式化は同じ主題について共同の信仰・立場を公に言い表すため、その主要内容をまとめたものとして位置付けられる。単なる標語、無関係な文章、全知識の網羅や唯一の定式化とは分ける。採用主体・内容・宗教上の領域は別に結ぶ。'),
    'h246g': ('[a a i[e] d] c', ['organization', 'formulation', 'content', 'reference'],
        '同じ組織が、同じ定式化に対応するこの閉じた内容記述を、自ら公に示す共同の立場として採用している。別の内容の採用、個々の成員の私的な信念、内容が客観的に真であることとは区別する。'),
    'h246h': ('[a i[h[a a] e] d] c', ['organization', 'practice', 'reference'],
        '同じ組織が、第一引数を担い手、第二引数をその組織とする記述された実践を、共同の実践として制度・慣行上位置付ける。現在その活動が行われること、成功や全員の参加を含意しない。'),
    'h246i': ('[a a a ' + STANDARD + ' d] c', ['organization', 'formulation', 'standard', 'criteria', 'reference'],
        'この組織が同じ定式化に沿って教示するための指定基準として、この閉じたNoema条件列の記述を採用する。同じ基準の適用事項を尽くす列であり、結果を見て条件を除外しない。定式化、基準の識別子、採用された条件列を別々に保持し、別名の記述へ勝手に採用を移さない。条件列の妥当性・完全性は明示解釈の契約であり、試験例や真理値の一致から認定しない。'),
    'h246j': ('[a d] ' + STANDARD, ['standard', 'reference'],
        '同じ基準・固定基準点に対して明示した、Noemaの条件関数列の閉じた記述。各関数は同じ主題と発話記述を受け、状況ごとの適合内容を返す。採用関係へ渡す値と実評価する列の出所を一つに固定し、現実の発言に合わせて選び直さない。未知の列を空列として補わない。'),
    'h246k': ('[a a a d] c', ['person', 'organization', 'role', 'point'],
        'この人がこの組織にこの職務で仕える制度的・実践的な関係にある。職務保持一般、別組織のための奉仕、一回の無関係な行為とは分ける。組織の教えへの内心の同意、個々の発言の許可や実際の遂行は含意しない。'),
    'h246l': ('[a a a ' + MESSAGE + ' d] c', ['person', 'activity', 'subject', 'message', 'point'],
        '同じ本人の同じ活動が、同じ主題と発話記述を受け手に説明・教示する趣旨の叙述・講説として行われる。単なる中立的引用、無関係な発話、受け手の実際の理解とは区別する。生起・提示者・宛先への提示はrfoで別に結ぶ。本人がその教えを真と確信することは要求しない。'),
}
MEANINGS = {
    'r35r': '継続的な共同組織h246dが、宗教の基礎的教えh245zを主題とする定式化h246fと、その同じNoema内容h246eを共同の立場h246gとして採用し、宗教的奉仕hzxiを共同の実践h246hとして持つ。建物ではなく信条と実践を共有する教会の採用した読み。内容や実践は実行しない。',
    'r35s': '同じ教会・信条・主題r35rに、同じ基準の閉じた条件列h246jがその信条に沿う教示基準として採用されるh246iを結ぶ。信条の内容と教示を評価する条件列を混同せず、採用対象の同一性を保持する。',
    'r35t': '同じ聖職者・職務・教会・会衆・二つの完全な宛先範囲r35qと、同じ信条・主題・採用基準r35s、その組織に同じ職務で仕えるh246kを固定基準で結ぶ。教示済みや教理の真理を前提にしない。',
    'r35u': 'r35tの同じ設定を保持し、同じ本人・活動・主題・発話の説明的な教示h246lと、既存rfwの基準に沿う実際の提示を結ぶ。採用記録と実評価に同じh246jの閉じた記述を渡し、二宛先の非空和集合全員へ同じ発話を示す。活動時にも同じ組織・職務への奉仕、委任、同じ条件列の採用を要求する。信条自体の真理や本人の確信は評価しない。',
    'r35v': '同じ設定・活動について、r35uを満たす型に合う発話記述が存在するという教示内容。特定の検査用発話だけに限定せず、全記述域の存在量化を保持する。義務や任用条件へ引用して渡す対象候補であり、義務自体はここでは追加しない。',
}
LIMITS = [
    'u0012[2984,3185)の教会・信条・それに沿う同じ本人の教示を構成する依存群。義務、同じ条件での過去任用、dennの説明、Eben soの並列、全文帰属は未統合。意味確認文字数は加算しない。',
    'Kircheを共通の教えと宗教的実践を制度的に持つ組織、Symbolをその共同の立場を表す信条という読みで構成する。特定教派・歴史的な特定信条・内容の真理や成員全員の信念一致は追加しない。保存したAdelungの語義を補助根拠とする。',
    '信条内容と条件列は閉じたNoema記述として入力する。原文が個別の教義を指定しないため、それを外から捏造しない。任意の自然言語やURLを内容の代用として通すものではない。',
    '各条件は主題と発話記述の適合を検査するためのNoema関数である。教義を真とするかや本人の信念は自動条件にせず、内容の提示と同意を分ける。空列は既存rfuでは真だが、採用・完全性・実際の提示を空列から推定しない。',
    '基準点で宛先と条件列を固定し、活動時にもその同じ条件列の採用と同じ奉仕・職務委任を確認する。採用主体・信条・基準・条件列が揃って初めて適合を評価し、別の基準点の採用で代用しない。',
    'Vortragを同じ本人による説明・教示の提示として読む。基準に沿う実際の提示r35u/vと、その実行を求める義務は別に構成する。教義の全てを一回の講義で伝えること、全受け手の理解や記憶は要求しない。',
    'rfwの動的な脱引用をv016で保持し、r35vは段階1の引用で扱える。有限評価器はr35vの全発話記述域の列挙を拒否する。個別発話の検査や引用成功を全域実行の証明にしない。',
]


@lru_cache(None)
def parents(): return tuple(load_catalog(ROOT, p) for p in PARENTS)


def definitions():
    text = 'd r35r[church a creed a subject a reference d] c[' + both(
        'k h246d[v church v reference]', 'k h245z[v subject v reference]',
        'k h246f[v creed v subject v reference]', 'k h246g[v church v creed k h246e[v creed v reference] v reference]',
        'k h246h[v church r[p hzxi] v reference]') + '].\n'
    criteria = 'k h246j[v standard v reference]'
    text += 'd r35s[church a creed a subject a standard a reference d] c[' + both(
        'k r35r[v church v creed v subject v reference]', 'k h246i[v church v creed v standard ' + criteria + ' v reference]') + '].\n'
    text += 'd r35t[' + FIELDS + '] c[' + both(
        'k r35q[v person v role v church v congregation v students v members v reference]',
        'k r35s[v church v creed v subject v standard v reference]', 'k h246k[v person v church v role v reference]') + '].\n'
    audiences = ' '.join('i[recipient a][k h6t[v ' + n + ' v recipient v reference]]' for n in ('students', 'members'))
    adoption = 'i[organization a rule a criteria ' + STANDARD + ' at d][k h246i[v organization v creed v rule v criteria v at]]'
    teaching = 'c[k rfw[v church v role v standard ' + audiences + ' v subject v message ' + criteria + (
        ' p h246k ' + adoption + ' p cb p cf p dg p f3 p f2]][v person v activity]')
    text += 'd r35u[' + FIELDS + ' activity a message ' + MESSAGE + '] e[b point[' + both(
        'k r35t[' + ARGS + ']', 'k h246l[v person v activity v subject v message v point]',
        't[' + teaching + '][v point]') + ']].\n'
    text += 'd r35v[' + FIELDS + ' activity a] e[b point[g message ' + MESSAGE + '[t[k r35u[' + ARGS + ' v activity v message]][v point]]]].\n'
    return text


def build():
    old, audience = parents(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['rfw', 'hzxi', 'cb', 'cf', 'dg', 'f3', 'f2']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    for d in closure(audience.document, ['r35q']):
        n = d['name']
        if n in imported:
            assert d == imported[n]['declaration'] and audience.entries[n]['meaning_ja'] == imported[n]['meaning_ja']
        else: doc['declarations'].append(d); imported[n] = audience.entries[n]
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(audience.entries))
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'], arguments=e['arguments'],
        meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    sources = set().union(*(set(c.source_sha256) for c in parents()))
    basis = dict(status='same_confession_adopted_standard_and_expository_teaching', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(sources)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
