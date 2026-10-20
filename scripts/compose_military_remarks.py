"""Compose remarks on shortcomings and their submission for public judgment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT_BASIS = 'data/officer-example-basis-v1.json'
LIBRARY = 'examples/v016/military-remarks.noema'
BASIS = 'data/military-remarks-basis-v1.json'
NAMES = ('person','making','presenting','scholar','notes','audience','field')
FIELDS = ' '.join(n+' a' for n in NAMES)+' reference d'
ARGS = ' '.join('v '+n for n in NAMES)+' v reference'
PRIMITIVES = {
    'h243u': ('[a a d d] c', ['criterion','target','reference','point'],
        '指定対象が、この固定基準で解釈した同じ評価条件を評価点で満たす。評価条件の適用対象としての妥当性、条件の道徳的正当性、誰かの評価結果への賛同は別である。不明を不充足にしない。'),
    'h243v': ('[a a d] c', ['criterion','target','reference'],
        'この固定基準では指定条件が、この対象の備えるべき性質・遂行水準を評価する条件として採られている。単なる好き嫌いや無関係な対象の条件を混ぜず、充足・不充足を見て条件を事後選択しない。採用基準が唯一または無条件に正しいとはしない。'),
    'h243w': ('[a a d] c', ['notes','remark','reference'],
        '指定された注記のまとまりの構成上、この言語的な所見・説明がその一つの部分である。対象事項について明確化・検討・指摘を行う内容の部分であり、無関係な文字列の同居とは区別する。構想された情報的まとまりも対象にでき、外部記録や制作済みを要求しない。'),
    'h243x': ('[a a a i[h[a a d] e] d] c', ['remark','target','criterion','content_family','reference'],
        'この所見が、同じ対象・評価条件・固定基準を指定の閉じた内容関数へ渡した内容を論点として分析・説明・指摘する。対象一般への言及だけでは足りず、所見全体を短い二値命題一つに限定しない。内容の真理、著者の断定や受け手の同意は要求しない。'),
    'h243y': ('[a a a d] c', ['person','activity','work','reference'],
        'この活動の構成は、同じ本人が指定された記述作品を自分の所見として作成する活動である。既存の他人の作品を所有すること、別作品の作成とは区別する。分類・計画としての関係であり、活動の実行・制作完了・外部記録の現存は含意しない。'),
    'h243z': ('[a a a d] c', ['activity','work','audience','reference'],
        'この活動は指定作品を同じ公衆が取り上げて検討できるよう提供する活動として構成されている。単に作品名を言うこと、別作品の流通、宛先のない保管とは区別する。実際の提供・受領・読了・評価は含意しない。'),
    'h244a': ('[a a d] c', ['field','institution','reference'],
        '指定領域は、この軍事組織の軍務に関わる諸活動・仕組み・遂行のあり方を対象とする検討領域である。組織という集団そのものや一つの命令だけとは分ける。現に戦争中であることを要求せず、同種の軍務に共通する問題も排除しない。組織の軍事性は別に確認する。'),
    'h244b': ('[a a a d] c', ['person','activity','work','point'],
        'この評価点で、同じ本人が同じ活動を通じて指定作品の記述を作り出した。単なる実行一般、他人の制作、すでにある作品の所持や複製媒体の移動だけとは区別する。作品の正しさや独創性を含意しない。'),
    'h244c': ('[a a a d] c', ['activity','work','audience','point'],
        'この評価点で、同じ提供活動を通じて指定作品が同じ公衆の検討に供され、取り上げ得る状態になっている。全員の実際の受領・読了・理解・判断・同意は要求しない。単なる活動の生起や非公開の記録だけでは満たさない。'),
}
MEANINGS = {
    'r326': '同じ対象について、固定基準で採用された備えるべき条件h243vが評価点で満たされないh243uという欠点の内容。どの観点で何が不十分かを二引数に分け、未知・無関係な条件・評価点の違いを不充足へ補わない。',
    'r327': '正確な二個体列を公衆と注記作品として受け、その同じ公衆に向けられた読者の一人以上が同じ注記を対象として判断を行うという目的内容。全読者の評価・賛同や判断の正しさは要求しない。目的として引用するときには内容を評価しない。',
    'r33a': '注記のまとまりに少なくとも一つの所見があり、その各所見が同じ検討領域とある明示した評価条件についてr326の不充足内容を論点として扱う。個々の所見は説明・分析を持てる。欠点や条件の現実の成立、所見への賛同は要求しない。',
    'r33b': '同じ本人が同じ学識者の立場で注記を作る活動と、その同じ注記を同じ公衆へ提供する活動を構成する。r33aの同じ領域の所見、h243yの作成、h242gの作品経由、h243zの検討可能な提供、同じ公衆と注記のr327を目指すhztlを結ぶ。現在の制作・提出・公衆の判断は要求しない。',
    'r33c': '同じ任用された将校r32kの本人・職務・組織を、同じ組織の軍務領域h244aと、その同じ本人の学識者としてのr33bへ束縛する。命令された行為を注記の話題全体にせず、職務上の立場と学識者の活動を別に追跡する。',
    'r33d': '本人による同じ作成活動の実行zzq、同じ作品の実際の作成h244b、その記述作品scと外部記録sdを結ぶ内容。計画だけ、別人の作品、別活動での制作を実行済みへ補わない。',
    'r33e': '本人による同じ提出活動の実行zzqと、同じ記述作品sc・外部記録sd、その公衆の検討に供するh244cを結ぶ内容。目的である公衆の判断の達成は実行条件へ混ぜない。',
    'r33f': '同じ本人・作成活動・提出活動・注記・公衆について、r33dの作成とr33eの提供を同じ評価点で結ぶ内容。これは両実行の接続であり、各活動への規範的保護や先後の時刻を追加しない。',
}
LIMITS = [
    'u0012[2332,2512)の注記作成と公衆の判断への提出に向けた依存群。billigermaßen nicht verwehrt werdenの規範内容、同じ命令事例への照応、aberの対照、全文の帰属は未統合であり、意味確認済み文字数を加算しない。',
    'Fehlerは対象の備えるべき条件の不充足として構成する。注記が取り上げる評価条件と対象を明示し、注記の話題を原文外の具体的な軍事的欠陥や数値へ固定しない。欠点への言及を、その欠点が現実にあるという作者の独立した事実主張にしない。',
    'Anmerkungenは同じ軍務領域について分析・説明・指摘する所見の情報的まとまりと読む。構成部分は非空とするが、原文の不定の複数形から固定した個数や列順を捏造しない。各所見の全内容を一つの二値命題に縮めず、不充足内容はその論点を指定する。',
    '作成と提出は同じ注記へ結び、学識者の公的使用は活動構成の分類として扱う。まだ刊行・制作されていない注記の活動候補も許す。書面による見解の提示という先行文の文脈を採り、実行結果では同じ注記の記録を要求する。',
    'zur Beurtheilungは公衆の読者が同じ注記を判断することを目指すという目的であり、全読者の実際の判断・理解・同意ではない。判断の成立と判断の正しさ、提出の成功と目的の達成を区別する。',
    '軍務は同じ軍事組織に関わる活動・仕組みの領域と読む。特定命令の有用性だけや、今行われている戦闘だけへ狭めない。本人の官職と学識者としての立場の数的な不等式や、作成・提出の数的な不等式は原文が要求しないため加えない。',
    '規範への統合では、作成と提出の両方の保護を確認する。両実行の連言だけを対象にして、一方のみを禁じることを見落とさない。現実の禁止の不在、物理的な禁止不能、積極的な実行許可を上位の禁止拒否と同一視しない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = 'd r326[target a criterion a reference d] e[b point['+both(
        'k h243v[v criterion v target v reference]', 'u[k h243u[v criterion v target v reference v point]]')+']].\n'
    text += '''d r327[bindings j[a]] e[b point[
g audience a[g notes a[g reader a[g judgment a[
w[k h7f[v bindings]][w[a[v bindings][n p a b][v audience]][
w[a[v bindings][n p b b][v notes]][w[k aa[v reader]][
w[k h6t[v audience v reader v point]][w[k fa[v reader v judgment v point]][k fb[v judgment v notes v point]]]]]]]
]]]]]].
'''
    text += 'd r33a[notes a field a reference d] c['+both(
        'g remark a[k h243w[v notes v remark v reference]]',
        'f remark a[y[k h243w[v notes v remark v reference]][g criterion a[k h243x[v remark v field v criterion r[p r326] v reference]]]]')+'].\n'
    text += 'd r33b['+FIELDS+'] c['+both(
        'k r33a[v notes v field v reference]',
        'k r2zi[v person v making v scholar v reference]',
        'k r2zi[v person v presenting v scholar v reference]',
        'k cc[v making v audience v reference]', 'k cc[v presenting v audience v reference]',
        'k ce[v audience v reference]', 'k h243y[v person v making v notes v reference]',
        'k h242g[v presenting v notes v audience v reference]',
        'k h243z[v presenting v notes v audience v reference]',
        'k hztl[v person v presenting r[p r327] l[a][v audience v notes] v reference]')+'].\n'
    text += 'd r33c[office a institution a '+FIELDS+'] c['+both(
        'k r32k[v person v office v institution v reference]',
        'k h244a[v field v institution v reference]', 'k r33b['+ARGS+']')+'].\n'
    for name,fields,extra in (
        ('r33d','person a activity a notes a', 'k h244b[v person v activity v notes v point]'),
        ('r33e','person a activity a notes a audience a','k h244c[v activity v notes v audience v point]')):
        text += 'd '+name+'['+fields+'] e[b point['+both('t[k zzq[v person v activity]][v point]',
            'k sc[v notes v point]', 'k sd[v notes v point]', extra)+']].\n'
    text += 'd r33f[person a making a presenting a notes a audience a] e[b point['+both(
        't[k r33d[v person v making v notes]][v point]',
        't[k r33e[v person v presenting v notes v audience]][v point]')+']].\n'
    return text


def build():
    old = parent(); doc = deepcopy(old.document)
    roots = ['h7f','aa','h6t','fa','fb','r2zi','h242g','hztl','r32k','zzq','sc','sd']
    doc.update(declarations=closure(doc,roots),statements=[])
    imported = {d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds = {d['name']:d for d in doc['declarations']}
    primitives = {n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],
        arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis = dict(status='remarks_on_military_shortcomings_and_submission_for_public_judgment',document=LIBRARY,
        primitives=primitives,definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
