"""Present the public/private use classifications as the author's definitions."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT = 'examples/v016/kant-answer-discourse.noema'
PARENT_BASIS = 'data/answer-discourse-basis-v1.json'
FULL = 'examples/v016/kant-use-definitions.noema'
CORE = 'examples/v016/use-definitions-core.noema'
BASIS = 'data/use-definitions-basis-v1.json'
ANNOTATIONS = 'data/use-definitions-identifiers-v1.json'
CLASS = 'i[h[a a a d] c]'
PRIMITIVES = {
    'h236o': ('[a a a ' + CLASS + ' d] c',
              ['node', 'presenter', 'term_mention', 'classification', 'context'],
              '提示者が指定箇所で、自分はこの語をこの分類として理解する・こう呼ぶと明示し、その語の使用を閉じた分類記述へ結ぶ。分類の引数は本人・活動・立場・基準の順である。外から与えた同義語対応や語の綴りの保存だけとは区別し、実例の存在・実際の活動・心理的理解の成功は含意しない。分類内容は引用先で合成する。'),
    'h236p': ('[] a', [], 'u0012の公的使用の定義文[981,1145)で定義の対象となるöffentlichen Gebraucheという語の言及箇所。語の意味の代用ではなく、分類r2ziへ結ぶ対象である。'),
    'h236q': ('[] a', [], 'u0012の私的使用の定義文[1146,1293)で定義の対象となるPrivatgebrauchという語の言及箇所。語の意味の代用ではなく、分類r2zjへ結ぶ対象である。'),
    'h236r': ('[] a', [], '固定原文kant-1784:u0012の[981,1145)、Ich verstehe aberから始まる公的使用の定義文の箇所。'),
    'h236s': ('[] a', [], '固定原文kant-1784:u0012の[1146,1293)、Den Privatgebrauch nenne ichから始まる私的使用の定義文の箇所。'),
    'h236t': ('[a a ' + CLASS + ' i[h[a a d] c] d] c',
              ['node', 'presenter', 'classification', 'entrusted_role', 'context'],
              '提示者がこの定義箇所で、指定分類の本人・活動・立場・基準について、同じ本人・立場・基準の委任関係が与える職務上の権限の範囲として、その活動類型を位置付ける。職務に伴って認められる使用の範囲という規範的な限定であり、単なる物理的能力や職業名の同一性ではない。委任・権限の現実の存在を引用時に実行せず、その時点の各指示への適合、個々の行為への無条件の実行許可、職務外の行為への許可は導かない。本人・立場の組は分類の第一・第三引数を共有する。'),
    'h236u': ('[a a a i d[e] a ' + CLASS + ' d] c',
              ['node', 'presenter', 'antecedent_node', 'antecedent_content', 'term_mention', 'classification', 'context'],
              '提示者が先行箇所の内容を受けて、そこで使った同じ語を指定分類として明確にする説明へ論述を切り替える。先行内容の撤回や論理的否定ではなく、語の使い方を区別して示す補足的な転換である。先行内容を実行せず、単なる本文順序だけでこの説明関係を代用しない。'),
    'h236v': ('[a a ' + CLASS + ' ' + CLASS + ' d] c',
              ['node', 'presenter', 'classification', 'focus_condition', 'context'],
              '提示者が同じ定義箇所で、閉じた分類記述の構成条件として、同じ四引数を取る指定の条件を取り立てて強調する。内容を実行せず、焦点条件だけで分類に十分であること、他条件の撤回、論理的な排他的唯一性は含意しない。焦点が分類の同じ参与者・立場に属することは合成された記述で保持する。'),
}
MEANINGS = {
    'r2zi': '本人が人であり、同じ本人の理性使用ca、同じ活動での立場cb、学識者としての立場cd、読者世界全体へ向けるcc/ceを同時に満たす公的使用zzoであるという分類。誰か一人の特定例に限らず、各本人・活動・立場・基準を同じ引数で受ける。実際の実行や全読者の受領は要求しない。',
    'r2zj': '本人が人であり、本人自身の理性使用caを、同じ本人に委ねられた市民的職務cfの立場cbで行う類型zzpであるという分類。同じ本人が別の職務を持つ場合も引数で区別する。公的使用の否定や、その時点の禁止による活動の範囲からの除外ではない。',
    'r2zk': '公的使用の定義文h236rで、著者waが同じ語の言及h236pを自分の定義r2ziへ結ぶ。先行回答h235p/r2zfから語義を明確にする転換h236u、同じ学識者の立場r2zmへの強調h236v、本文順序を保持し、分類の実例や先行回答の真理を実行しない。',
    'r2zl': '私的使用の定義文h236sで、同じ著者が語の言及h236qを自分の定義r2zjへ結ぶ。darfを、同じcfの委任に伴って与えられる職務上の使用範囲というh236tの規範的限定として保持する。前の定義からの順序と二つの語・定義箇所の区別を保ち、個別の実行許可の全面的存在へ強めない。',
    'r2zm': '同じ本人・活動・立場・基準について、活動をその立場で行うcbと、その立場が学識者であるcdを取り出す。公的使用分類r2ziの中のals Gelehrterを強調する焦点条件であり、職業名だけの分類へ置き換えない。',
}
LIMITS = [
    '二文を、著者自身がこの論説で採る語の使い方を明示する定義の提示として読む。分類をNoemaで合成して引用し、綴りだけで定義したことにしない。定義の提示を、実際の活動例が存在するという叙述へ変えない。',
    'jemand・er・seiner eigenen Vernunft・ihrを同じ本人と本人の理性へ束縛する。人である条件を加え、学識者としての活動と、委ねられた職務での活動を役割引数で区別する。公的・私的使用の排他的な二分法や、全活動を尽くす二分類は追加しない。',
    '公的使用は全読者世界へ向ける活動類型であり、全読者が実際に読んだこと、特定の刊行媒体、大学の資格を必要条件にはしない。cd/ceの公開された意味規約を使い、単に人前の行為や大人数の職務内集会へ広げない。原刊Gelehrterの強調は同じcb/cdの焦点へ結び、他の定義条件を消さない。',
    '私的使用のdarfは、委任された市民的職務の権限の範囲に認められる理性使用という読みを採る。その時点で個々の発言に積極的許可h7bがあるという読みとは区別する。後続の職務上の指示・禁止によって活動の分類そのものを消さず、委任に基づく類型の限定をh236tで明示する。これは明示した解釈であり、darfを無意味として落とすものではない。',
    'gewissenは本人に委ねられたある具体的な立場を同じ役割引数で受けるものとし、唯一の官職、特定の歴史的人物、秘密の私生活を補わない。Posten, oder Amteは市民的な地位・職務の言い換えを含む分類であり、両方を同時に持つ条件や排他的選言へ変えない。',
    'aberは先行回答を受けてそこで使った語を区別して明確にする転換として読む。規範上の先行対照を撤回せず、定義から前の回答が論理的に証明されたとも主張しない。定義の提示文脈はh232oを保ち、分類は明示的な基準引数で扱う。',
    '旧zzo/zzpとそれを使う回答・意味判断は変更しない。新しい分類は人である条件を明示し、既に人を対象としていた先行構成と照合する。cd等の一般概念をさらに合成する課題を、この二文の通読と混同しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = '''
d r2zi[person a activity a role a reference d] c[w[k aa[v person]][k zzo[v person v activity v role v reference]]].
d r2zj[person a activity a role a reference d] c[w[k aa[v person]][k zzp[v person v activity v role v reference]]].
d r2zm[person a activity a role a reference d] c[w[k cb[v person v activity v role v reference]][k cd[v role v reference]]].
'''
    ctx, author = 'k h232o[]', 'k wa[]'
    text += 'd r2zk[] c[' + both(
        'k h236o[k h236r[] ' + author + ' k h236p[] r[p r2zi] ' + ctx + ']',
        'k h236u[k h236r[] ' + author + ' k h235p[] r d[k r2zf[]] k h236p[] r[p r2zi] ' + ctx + ']',
        'k h236v[k h236r[] ' + author + ' r[p r2zi] r[p r2zm] ' + ctx + ']',
        'k ue[k h235p[] k h236r[] ' + ctx + ']',
        'u[e[k h235p[]][k h236r[]]]') + '].\n'
    text += 'd r2zl[] c[' + both(
        'k h236o[k h236s[] ' + author + ' k h236q[] r[p r2zj] ' + ctx + ']',
        'k h236t[k h236s[] ' + author + ' r[p r2zj] r[p cf] ' + ctx + ']',
        'k ue[k h236r[] k h236s[] ' + ctx + ']',
        'u[e[k h236r[]][k h236s[]]]',
        'u[e[k h236p[]][k h236q[]]]') + '].\n'
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = [dict(kind='assert', body=dict(kind='call', symbol=n, arguments=[])) for n in ('r2zk', 'r2zl')]
    doc['statements'] = statements + new
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=new)
    decls = {d['name']: d for d in added}
    basis = dict(status='public_private_use_definitions_under_explicit_reading', document=FULL,
                 parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/answer-discourse-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
