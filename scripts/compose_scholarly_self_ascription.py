"""Compose first-person civic self-ascription and written public address."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT_BASIS = 'data/office-obedience-basis-v1.json'
LIBRARY = 'examples/v016/scholarly-self-ascription.noema'
BASIS = 'data/scholarly-self-ascription-basis-v1.json'
PRIMITIVES = {
    'h242d': ('[a i[h[j[a]] e] j[a] c d] c',
              ['judgment', 'content', 'bindings', 'polarity', 'reference'],
              'この判断が、閉じた内容関数へ同じ順序の個体列を適用した内容を、指定の極性で認めている。hznnと同じ判断の肯否を複数の束縛で扱う。判断主体はfaで別に結び、内容の真理・成功・本人の行動を実行しない。同じ真理値の別の記述を自動的に同一視しない。'),
    'h242e': ('[a d] c', ['society', 'point'],
              'この社会的な結び付きは、個別の政治的共同体を越えて、人々を同じ世界に属する市民として位置付ける社会の構想である。一国の住民集団や局所的な職務集団だけとは分ける。単一の世界政府、現存する国際機関の名称、全人類の実際の相互承認は含意しない。世界市民社会という対象の読みを明示する分類関係である。'),
    'h242f': ('[a a d] c', ['person', 'society', 'point'],
              'この人が、この市民的な社会の構想における成員として位置付けられる。特定国家の法的国籍や住所とは同一視しない。本人がそう考えていることは別の判断関係で扱い、この関係自体はその成員性を述べる。'),
    'h242g': ('[a a a d] c', ['activity', 'written_work', 'audience', 'reference'],
              'この活動の内容上の構成では、同じ記された作品を介して、同じ宛先へ本人の見解を向ける。作品への単なる言及、別の作品の流通、別の宛先への発信では満たさない。書かれた記録と媒体は別に構成する。特定の印刷・製本技術、実際の発信・読了・理解・賛同は含意しない。'),
    'h242h': ('[a a d] c', ['judgment', 'person', 'reference'],
              'この判断において、指定本人が内容の対象となる本人を自分自身として捉える一人称の位置付けがある。対象が偶然判断者と同一であるだけの第三者についての判断とは分ける。判断主体、具体的な肯定内容、束縛先の同一性は合成側で確認し、自己評価の正しさは要求しない。'),
}
MEANINGS = {
    'r3p': '本人・政治的共同体・世界市民社会の順にちょうど三個体を受け、本人が同じ政治的共同体の成員であるという内容を構成する。地域内の一職務集団への所属ではなく共同体の成員性h237cを用いる。第三位置は対になるr3qと同じ束縛を保つために保持する。',
    'r3q': 'r3pと同じ三個体列から、第三位置が世界市民社会の構想h242eであり、同じ本人がその社会の成員h242fであるという内容を構成する。別の人や一国の国籍へ取り替えない。',
    'r3r': '同じ本人が同じ基準で行う一つの判断に、一人称として自分を捉えるh242hがあり、同じ本人・共同体・世界市民社会の束縛でr3pとr3qを正極性で認める。内容は引用し、世界市民社会への実際の所属や判断の正しさを評価しない。',
    'r3s': '本人・活動・学識者としての立場・書かれた作品・公衆・基準について、公的使用r2zi、同じ活動の宛先ccと本来の全読者世界ce、記された作品sc、参照可能な外部記録sd、同じ作品を同じ宛先へ向ける活動上の経路h242gを結ぶ。職業名や口頭での対話だけで代用しない。',
    'r3t': '先行する事務で割り当てられた同じ本人・職務・基準の範囲r3mに、同じ事務の共同体を指すこと、自分をその共同体と世界市民社会の成員と捉えるr3r、同じ本人の学識者としての書面による公的使用r3sを結ぶ。同じ人の二つの立場を引数で分け、両立を一律に排除しない。',
}
LIMITS = [
    'u0012[1743,2122)の条件側へ向けた依存群であり、当該文の完成・帰属・意味判断ではない。本文81主張と既存の確認文字数は変更しない。',
    'ansiehtを本人の一人称の自己理解として扱い、同じ人が内容を肯定することと、その成員性の真理を分ける。第三者についての判断対象が偶然本人であったというだけでは足りない。',
    '世界市民社会を一国を越えた市民的な社会の構想として明示する。現在の世界政府や国際機関の実在、法的な国籍、全員の自覚を補わない。政治的共同体のh237cの意味を無断で拡張しない。',
    'ganzenを、担当職務の部分集団に限らない共同体全体への成員性という読みで扱う。全構成員が同じ判断をするという全称命題ではない。ja sogarの段階的な強調はまだ談話へ接続していない。',
    '書かれた作品の存在・記録の保持・参照可能性は、この分類を評価する状況における条件である。活動の実際の発信や読者の受領は要求しない。この前件を本文へ条件付きで引用するときに、現実の発信済み作品の存在へ昇格させない。',
    'r3tは意味要素を束縛する候補であり、mithinによる説明、So fernの条件化、aber/allerdingsの留保、機械の部分という照応・描写、zum Theile、職務を損なわないことと論じうることの結合は次に残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = ''
    for name, body in [('r3p', 'k h237c[v person v community v point]'),
                       ('r3q', both('k h242e[v world v point]', 'k h242f[v person v world v point]'))]:
        text += 'd ' + name + '[bindings j[a]] e[b point[g person a[g community a[g world a[' + both(
            'k h7g[v bindings]', 'a[v bindings][n p a b][v person]',
            'a[v bindings][n p b b][v community]', 'a[v bindings][n p c b][v world]', body) + ']]]]].\n'
    text += 'd r3r[person a community a world a reference d] c[g judgment a[' + both(
        'k fa[v person v judgment v reference]',
        'k h242h[v judgment v person v reference]',
        'k h242d[v judgment r[p r3p] l[a][v person v community v world] e[v person][v person] v reference]',
        'k h242d[v judgment r[p r3q] l[a][v person v community v world] e[v person][v person] v reference]') + ']].\n'
    text += 'd r3s[person a activity a scholar a writing a audience a reference d] c[' + both(
        'k r2zi[v person v activity v scholar v reference]',
        'k cc[v activity v audience v reference]', 'k ce[v audience v reference]',
        'k sc[v writing v reference]', 'k sd[v writing v reference]',
        'k h242g[v activity v writing v audience v reference]') + '].\n'
    text += ('d r3t[person a office a work a community a world a activity a scholar a '
             'writing a audience a reference d] c[' + both(
        'k r3m[v person v office v work v reference]',
        'e[v community][k h237i[v work v reference]]',
        'k r3r[v person v community v world v reference]',
        'k r3s[v person v activity v scholar v writing v audience v reference]') + '].\n')
    return text


def build():
    old = parent()
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['h7g', 'h237c', 'fa', 'r2zi', 'cc', 'ce', 'sc', 'sd', 'r3m', 'h237i']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    declarations = {d['name']: d for d in doc['declarations']}
    meanings, primitives = {}, {}
    for n, entry in imported.items():
        d = entry['declaration']
        if entry['kind'] == 'definition':
            meanings[n] = entry['meaning_ja']
        else:
            primitives[n] = dict(parameters=d['parameters'], result=d['result'],
                                 arguments=entry['arguments'], meaning_ja=entry['meaning_ja'])
    primitives.update({n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                               arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()})
    basis = dict(status='scholarly_self_ascription_and_written_address_dependency_group', document=LIBRARY,
                 primitives=primitives, definitions=meanings | MEANINGS,
                 imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(old.source_sha256)},
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
