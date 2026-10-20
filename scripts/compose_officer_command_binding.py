"""Bind institutional rank, an appointed officer, and the addressed command."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT_BASIS = 'data/scholarly-compatibility-basis-v1.json'
LIBRARY = 'examples/v016/officer-command-binding.noema'
BASIS = 'data/officer-command-binding-basis-v1.json'
PRIMITIVES = {
    'h242v': ('[a a j[a] c i[h[j[a] c] f] d] c',
              ['notice', 'recipient', 'bindings', 'polarity', 'message_family', 'point'],
              '同じ提示行為で、この受け手へ、閉じた発話関数に同じ順序の個体列と同じ極性を渡した発話を示す。f2の対象引数を明示した複数束縛と極性へ一般化する。発話の命令・主張・質問という働きは渡す記述で構成し、関係だけで命令と決めない。生起・提示者・束縛先の受け手との同一性は合成側で結ぶ。内容の真理、受領、理解、服従、制度的な正当性は含意しない。'),
    'h242w': ('[a a d] c', ['role', 'institution', 'reference'],
              'この役職が、同じ制度的組織・基準の役職体系の範囲に属する。現在の保持者がいる役職だけに範囲を縮めず、別組織の同名の役職を混ぜない。役職間の上下、特定人物による保持・任用、指示の発出は別に確認する。'),
    'h242x': ('[a a a d] c', ['higher', 'lower', 'institution', 'reference'],
              '同じ組織・基準の役職体系で、第一役職が第二役職より上位の職務上の指揮関係に位置する。単なる社会的名声、年齢、給料の比較とは区別する。直接隣接の報告先だけでなく間接の上位も含めた順序として与え、非反射性・推移性は合成側で確認する。現在の命令発出や個別命令の正当性を含意しない。'),
}
MEANINGS = {
    'r32j': 'h7fでちょうど二個体の列を要求し、その同じ順序の本人・行為にh7hの実行内容を適用して、真偽が指定極性に一致するよう求める命令の発話を作る。肯定・否定の命令を同じ対象へ束縛し、命令の実際の発出や履行は別に扱う。長さ不適合の否定命令を自動的に充足したことにせず、提示側でもh7fを検査する。',
    'r32k': '既存r2toの将校分類を、同じ本人・明示した役職・軍事組織・基準へ固定する。人、役職保持hzwn、有効な任用hzxf、軍事組織h233d、同組織の将校階級h233e、委ねられた職務cfを結び、別の役職で将校であることを借りない。',
    'r32l': '同じ組織・基準の役職範囲h242wと指揮上の上下h242xを既存hzaeへ渡す。保持関係は同じ人・役職のhzwnと同じ組織への有効な任用hzxfをともに要求する。相異なる二人、同じ役職範囲の非反射的・推移的な上位関係、両者の職務を保持し、自分自身や他組織の上位者を上官として混ぜない。',
    'r32m': '同じ生起する提示行為dgで同じ提示者f3が、同じ受け手へ、その受け手自身と指定行為を順に束縛したr32jの同じ極性の命令を示す。h7fでちょうど二引数を確認し、内容の実際の真理・受領・正当性・規範の有効性を脱引用しない。',
    'r32n': 'r32kの同じ将校・役職・軍事組織に、r32lの同じ上官・上位役職と、r32mの同じ発出者・受け手・提示行為・対象行為・極性を結ぶ。制度的な上下関係、命令が発出されたこと、本人の実行を区別する。',
}
LIMITS = [
    'u0012[2123,2331)に向けた将校・上官・命令の依存群。一文全体の帰属、条件、重大な害の評価、服従要求はまだ接続しない。原文対応率と意味確認済み文字数は増やさない。',
    'Offizierは既存の任官された将校という読みを保持し、今回の役職と軍事組織を明示的に固定する。兵卒、下士官、単なる指導者、命令できるだけの人へ広げない。制度や命令の正当性を認定することとは別である。',
    'von seinen Oberenは同じ組織の職務上の上位者という関係で扱う。複数形から上官が必ず二人以上同時に命じたという条件を足さず、全文への量化時に対象となる上官を明示する。全組織を通じた唯一の上官とも扱わない。',
    'etwas anbefohlenの命令内容は同じ本人・行為の実行または不実行の指定極性として構成する。命令対象の行為は未指定のまま引数に残し、勝手に教練や戦闘など特定の行為へ固定しない。',
    '命令が出たことから受領、理解、意図、正当な権限、実行要求の規範的妥当性、実際の服従を導かない。後続のer muß gehorchenは別の要求として、同じ命令内容との対応を確認して接続する必要がある。',
    '発話内容を順序付き束縛と極性へ適用する一般化は、文ごとの完成内容を原始記号に隠すものではない。命令の働きは既存j m、内容はh7hと同一性から構成する。旧f2の意味・型・利用例は変更しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = 'd r32j[bindings j[a] polarity c] f[j m[b point[' + both(
        'k h7f[v bindings]', 'e[t[k h7h[v bindings]][v point]][v polarity]') + ']]].\n'
    text += 'd r32k[person a office a institution a reference d] c[' + both(
        'k aa[v person]', 'k hzwn[v person v office v reference]',
        'k hzxf[v person v office v institution v reference]', 'k h233d[v institution v reference]',
        'k h233e[v office v institution v reference]', 'k cf[v person v office v reference]') + '].\n'
    holders = 'i[person a role a organization a point d][' + both(
        'k hzwn[v person v role v point]', 'k hzxf[v person v role v organization v point]') + ']'
    text += ('d r32l[issuer a person a higher a office a institution a reference d] c['
             'k hzae[v issuer v person v higher v office v institution v reference '
             'p h242w ' + holders + ' p h242x]].\n')
    bindings = 'l[a][v person v action]'
    text += 'd r32m[issuer a person a notice a action a polarity c reference d] c[' + both(
        'k dg[v notice v reference]', 'k f3[v issuer v notice v reference]', 'k h7f[' + bindings + ']',
        'k h242v[v notice v person ' + bindings + ' v polarity r[p r32j] v reference]') + '].\n'
    text += 'd r32n[person a office a institution a issuer a higher a notice a action a polarity c reference d] c[' + both(
        'k r32k[v person v office v institution v reference]',
        'k r32l[v issuer v person v higher v office v institution v reference]',
        'k r32m[v issuer v person v notice v action v polarity v reference]') + '].\n'
    return text


def build():
    old = parent()
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = deepcopy(old.document)
    roots = ['h7h', 'h7f', 'aa', 'hzwn', 'hzxf', 'h233d', 'h233e', 'cf', 'hzae', 'dg', 'f3']
    doc.update(declarations=closure(doc, roots), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    doc = parse(format_graph(doc,'compact') + ''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items()) + definitions())
    ds = {d['name']:d for d in doc['declarations']}
    meanings, primitives = {}, {}
    for n,e in imported.items():
        d=e['declaration']
        if e['kind']=='definition': meanings[n]=e['meaning_ja']
        else: primitives[n]=dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='officer_superior_and_addressed_command_dependency',document=LIBRARY,
        primitives=primitives,definitions=meanings|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
