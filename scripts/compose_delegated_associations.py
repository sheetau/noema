"""Separate all-clerical membership from institutionally delegated membership."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts.compose_spiritual_guardians import quant

PARENT = 'data/guardian-irrationality-basis-v1.json'
LIBRARY = 'examples/v016/delegated-associations.noema'
BASIS = 'data/delegated-associations-basis-v1.json'
MEMBERSHIP = 'h[a a d] c'
MANDATE = 'h[a a a a d] c'
QUALIFIED = 'h[a a a d] c'
PRIMITIVES = {
    'h254f': ('[a a a a d] c', ['principal', 'person', 'role', 'assembly', 'reference'],
        '同じ固定基準で、この組織がこの人をこの職務においてこの会議体の代表として送り、その組織を代表して会議に参与する権限を委ねている。任用一般、本人の同席、別の会議への委任、本人による自称と分ける。委任の存在は別の契約を結ぶ権限や全ての決定の正当性を含意しない。役割の保持・任用・奉仕は別に同じ引数で確認する。'),
    'h254g': ('[a a d] c', ['assembly', 'principal', 'reference'],
        'この固定基準で、この組織はこの会議体が代表する構成組織の範囲に入る。会議体の制度・慣行上の代表範囲を全て与え、代表が来なかったこと、宣誓しなかったこと、資格不明を理由に組織を落とさない。組織とその代表者個人の所属は区別する。地域・教派・段階などによる範囲の具体的な限定は別に構成する。'),
}
MEANINGS = {
    'r454': 'rirの同じ複数人の団体について、同じ基準に属する全構成員が指定の資格関係を満たす。資格で所属自体を絞らず、一人の不適格者も全体の条件へ反映する。人の判定・資格関係は引数なので宗教に限定しない。',
    'r455': '同じ人・役割・教会・固定基準の聖職者r35mと、その人が同じ教会に同じ役割で仕えるh246kを結ぶ。任用元や奉仕する職務を別の証人で補わない。信仰・現実の仕事・秘跡資格は追加しない。',
    'r456': 'h246cの全構成員が人で、各人にr455の整合した聖職者の役割と教会がある複数人の団体。組織・役割は人ごとに異なってよく、全員を一つの教会へ雇用させない。全歴史的な教会会議の定義ではない。',
    'r457': '同じ会議体の人の所属、代表する組織範囲、各組織からの人・役割付き委任を結ぶ一般構成。構成組織は非空で全て指定の組織条件を満たし、各組織に適格な所属代表が少なくとも一人いる。逆に全所属者には同じ構成組織・役割による適格な委任がある。組織別の一意性・人数・排他的な代表関係は加えない。',
    'r46a': '会議体・固定基準・所属関係を束縛した人と評価時点からの当事者判定。所属は常に固定基準で調べ、過去の宣誓時点や将来の履行時点によって当事者を選び直さない。資格による濾過も加えない。時点引数は他の内容関数との接続用で、意図的に所属判定へ使わない。',
    'r46b': '人が同じ役割を持ち、同じ組織からその役割に任用され、その組織に同じ役割で仕える制度上の職務関係。宗教的助言を主要な務めとすることを追加しないので、長老等の代表も牧師と同一視せずに扱える。これだけでは代表委任や教会の分類は成立しない。',
    'r46c': 'r457の所属をh246c、構成組織範囲をh254g、代表委任をh254f、代表の職務資格をr46bへ接続する。構成組織は同じ基準で既存r35rの信条と宗教的実践を持つ教会とする。教会からの職務代表による団体の条件であり、全員が聖職者r455である条件は加えない。審議機能・地域と制度段階・歴史的呼称はこれから別に結ぶ。',
}
LIMITS = [
    '第六段落u0013冒頭のGesellschaft von Geistlichen、Kirchenversammlung、Klassisを区別して構成するための依存群。全文の問い・誓約・権限・上位後見・永続化・例示の談話関係は未統合。本文の96主張、登録簿v180と意味確認文字数は変更しない。',
    '旧hzcyはsoという仕事指定に基づく部分候補。r456は現行r35mの制度上の聖職者と同じ奉仕関係へ接続するが、Klassisの全所属者を牧師に限定する定義には使わない。ドルト教会規則第41条は牧師と長老の代表をともに規定する。歴史上の全会議に同一の細則があったという読みは追加しない。',
    'r457は人の所属と組織の代表範囲の両方を全称で確認する。欠けた代表や資格不明を理由に入力の範囲を縮めない。現実の所属・委任・代表範囲の完全さは明示した解釈の責任で、有限モデルが史実を証明するものではない。',
    'r46cはKirchenversammlungやKlassisの完成した名詞句ではない。審議と共同の教会統治という機能、Klassisの地域的・中間段階の制度、オランダでの自己呼称、ehrwürdigの扱い、etwaの例示は残す。第41条の人数・三か月間隔・議長選出等を原文の意味へ一律に輸入しない。',
    '所属・職務・代表委任が成立しても、不変の信条への宣誓が起きたこと、その契約の権利能力・正当性、全員の同意、本人の信仰を含意しない。新定義群は著者の主張を追加しない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT)


def definitions():
    member = 'c[v belongs][v group v person v reference]'
    fields = 'group a reference d belongs ' + MEMBERSHIP + ' human h[a] c qualified h[a d] c'
    text = 'd r454[' + fields + '] c[' + both(
        'k rir[v group v reference v belongs v human]',
        'f person a[y[' + member + '][c[v qualified][v person v reference]]]') + '].\n'
    text += 'd r455[person a role a church a reference d] c[' + both(
        'k r35m[v person v role v church v reference]', 'k h246k[v person v church v role v reference]') + '].\n'
    cleric = 'i[person a at d][' + quant(('role', 'church'), 'k r455[v person v role v church v at]', 'g') + ']'
    text += 'd r456[group a reference d] c[k r454[v group v reference p h246c p aa ' + cleric + ']].\n'
    fields = ('group a reference d belongs ' + MEMBERSHIP + ' represented ' + MEMBERSHIP +
        ' mandate ' + MANDATE + ' human h[a] c institution h[a d] c qualified ' + QUALIFIED)
    represented = 'c[v represented][v group v principal v reference]'
    witness = both(member, represented,
        'c[v mandate][v principal v person v role v group v reference]',
        'c[v qualified][v person v role v principal v reference]')
    text += 'd r457[' + fields + '] c[' + both(
        'k rir[v group v reference v belongs v human]', 'g principal a[' + represented + ']',
        'f principal a[y[' + represented + '][' + both(
            'c[v institution][v principal v reference]', quant(('person', 'role'), witness, 'g')) + ']]',
        'f person a[y[' + member + '][' + quant(('principal', 'role'), witness, 'g') + ']]') + '].\n'
    text += 'd r46a[group a reference d belongs ' + MEMBERSHIP + '] h[a d] c[i[person a point d][' + member + ']].\n'
    text += 'd r46b[person a role a principal a reference d] c[' + both(
        'k aa[v person]', 'k hzwn[v person v role v reference]',
        'k hzxf[v person v role v principal v reference]', 'k h246k[v person v principal v role v reference]') + '].\n'
    institution = 'i[principal a at d][' + quant(('creed', 'subject'), 'k r35r[v principal v creed v subject v at]', 'g') + ']'
    text += 'd r46c[group a reference d] c[k r457[v group v reference p h246c p h254g p h254f p aa ' + institution + ' p r46b]].\n'
    return text


def build():
    old = parent(); assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['rir', 'r35m', 'r35r', 'h246k', 'h246c']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'],
        arguments=e['arguments'], meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    basis = dict(status='distinct_clerical_and_delegated_memberships', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(old.source_sha256)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
