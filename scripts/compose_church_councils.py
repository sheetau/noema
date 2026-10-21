"""Compose institutional deliberation and the regional middle council level."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts.compose_spiritual_guardians import quant

PARENTS = ('data/guardian-irrationality-basis-v1.json', 'data/delegated-associations-basis-v1.json')
LIBRARY = 'examples/v016/church-councils.noema'
BASIS = 'data/church-councils-basis-v1.json'
PRIMITIVES = {
    'h254h': ('[a a d] c', ['activity', 'issue', 'point'],
        'この活動は、この同じ論点について、共同の判断・方針を選ぶために見解と理由を参加者間で検討する審議である。単なる一方向の告知、雑談や黙って同席することと分ける。全員一致、結論の到達、理由の正しさ、採用した判断の実行は要求しない。組織の会議行為としての帰属は別に結ぶ。'),
    'h254i': ('[a a d] c', ['activity', 'body', 'point'],
        'この活動は、この会議体の構成員がその会議体として参与する公式の会議手続に位置付く。構成員の私的な会話や、別の会議体の手続とは区別する。全員の出席、定足数、決議の法的効力や特定の会場を含意しない。'),
    'h254j': ('[a a d] c', ['body', 'issue', 'point'],
        '同じ制度・慣行の中で、この会議体はこの論点の共同の方針・判断を議決する担当を持つ。個人への任意の助言や、関係のない分野の決定担当と分ける。その制度の道徳的正当性、他の全領域への権限、実際の議決や実行は含意しない。'),
    'h254k': ('[a a d] c', ['issue', 'church', 'point'],
        'この論点は、この同じ宗教組織の共同の教え、宗教的な奉仕・生活実践、またはそれらを営む制度と運営に関わる。成員の無関係な私事ではなく、共同の宗教上の事柄として扱う範囲である。どの見解を採るか、教義の真理や論点の解決は含意しない。'),
    'h254l': ('[a a d] c', ['body', 'polity', 'reference'],
        'この会議体・統治機関は、この固定基準における同じ教会の統治制度の機関範囲に属する。個々の成員の役職や国家の統治機関と分ける。上下関係を確認する際は当該範囲を全て与え、都合の悪い中間機関を除かない。'),
    'h254m': ('[a a a d] c', ['higher', 'lower', 'polity', 'reference'],
        'この同じ教会統治制度では、前者の機関が後者より上の段階で、下位で処理しきれない事柄や決定への申立てを扱う位置にある。間接の上位も含めた関係として与える。年齢・名声・教義の正しさの比較ではなく、各決定の道徳的正当性や現実の申立ては含意しない。範囲内の非反射性・推移性と直接の段階差は合成側で確認する。'),
    'h254n': ('[a a d] c', ['body', 'church', 'reference'],
        'この機関は、この地域の一教会自身における共同の宗教上の事柄を最初の段階で扱う内部の統治会議体である。複数教会を横断する上級会議、別の教会の内部会議、単なる個人の担当と分ける。構成員の固定人数、特定の任期や議決の正当性は含意しない。'),
    'h254o': ('[a a d] c', ['church', 'district', 'reference'],
        'この教会は、この固定基準で近隣の諸教会をまとめる地域的な教会行政区分に位置付けられる。国全体や世界全体を任意に一地区と読み替えず、地域と当該制度・慣行を固定する。同地区の全教会が一つの教派に属することや、同地区というだけでこの会議の構成組織であることは含意しない。'),
    'h254p': ('[a a d] c', ['district', 'region', 'reference'],
        '同じ固定基準の地域区分において、前者は後者を構成する、後者全体とは異なる地域的な部分区分である。同じ範囲の別名、単なる隣接、政治的主権や国家の領有関係ではない。'),
    'h254q': ('[a a a d] c', ['body', 'region', 'polity', 'reference'],
        'この統治制度のこの機関は、この地域区分全体にわたる諸下位区分の共同の事柄を扱う管轄を持つ。会場の所在地や一つの下位区分だけの管轄と分ける。実際の全案件の処理、他制度への権限や道徳的正当性は含意しない。'),
    'h254r': ('[a a d] c', ['region', 'polity', 'reference'],
        'この地域区分は、同じ教会統治制度で州に対応する広域区分として位置付く。複数の地方地区をまとめる段階であり、国家全体や一教会の地域と区別する。現在の国家の行政区分や境界へ自動的に一致させない。'),
}
MEANINGS = {
    'r46d': '同じ人が同じ会議体に属し、その同じ活動が生起し本人が担い手であり、同じ会議体の会議手続として同じ論点を審議する。論点は同じ会議体の議決担当に属し、同じr35rの教会の共同の宗教上の事柄である。行為・論点・教会・信条・主題を別の証人で混ぜない。決議の到達やその正当性は要求しない。',
    'r46e': '同じ人・会議体について、r46dの活動・論点・教会・信条・主題が存在する内容。会議体の共同の実践へ引用して渡すための、審議活動の合成記述。引用するだけで活動や判断の真理を実行しない。',
    'r46f': '全員聖職者の団体r456または教会からの職務代表団体r46cが、同じ基準でr46eの共同の宗教上の審議を制度・慣行上の実践h246hとして持つ。この文脈での教会会議の読み。現在の会合、全員の出席や決議済みを分類条件にしない。',
    'r46g': '指定の完全な機関範囲と厳密な上位関係reyにおいて、上位と下位の間に別の範囲内機関がない。直接の一段階差を、全間接上位を含む非反射的・推移的な関係から構成する。範囲外の対象は間に挿入しないが、実際の中間機関を範囲から落としてよいという意味ではない。',
    'r46h': '同じ教会統治制度・固定基準の完全な機関範囲h254lと上位関係h254mにおいて、この会議体は指定の地方会議体の直接上、指定の広域会議体の直接下にある。同じ中間機関と同じ制度の二辺を共有する。',
    'r46i': '同じ会議体が代表するh254gの構成組織に相異なる二教会以上があり、その全構成組織が同じ固定基準の一つの近隣地区h254oに位置付く。地区内の全宗派・全教会を所属と同一視せず、構成組織の取りこぼしを別地区として除外しない。',
    'r46j': '同じ教会会議r46fが職務代表によるr46cを満たし、r46iの同じ近隣地区の教会を代表する。その地区は同じ教会統治制度の州区分の真部分で、同じ上位会議はその州全体の共同事項を管轄し、同じ審議を実践とする。各構成教会の地方内部会議について、同じ会議体がその直接上、同じ州会議の直接下となるr46hを結ぶ。Classisの地域的中間会議として採る制度的構成。',
    'r46k': '同じ会議体・固定基準に対し、r46jを満たす地区・州区分・統治制度・州会議があるという分類。特定の実在会議名を補わず、構成員全員を牧師へ限定しない。オランダでの呼称、敬称と例示の談話はこの分類へ別に接続する。',
}
LIMITS = [
    'u0013冒頭の問いへ向けたKirchenversammlungとKlassisの制度的内容を構成する依存群。聖職者の団体・代表団体に、共同の宗教上の審議という実践と、地方内部会議・地区会議・州会議の段階を接続する。全教派・全時代の教会会議の必要十分条件を主張しない。',
    '保存したドルト1619教会規則第30・31条を審議対象と決定の制度、第36・37・41・47条を地方・地区・州の構成の根拠とする。多数決、牧師/長老各一人、会期間隔、議長交替など個別の手続条件は原文の名詞句へ輸入しない。近隣地区の上に州会議があるという地域的・中間的な読解はHuygensの史料案内とも照合する。',
    '教会会議の分類は共同実践h246hへの閉じたr46e記述の指定であり、現在の審議や決議を要求しない。実践内容を評価する場合だけr46dの行為生起・同一の論点・本人・会議体・教会を確認する。個々の決議や不変の信条への契約を結ぶ道徳的権限は別問題である。',
    '機関範囲h254lと構成組織範囲h254gの完全さは解釈の入力契約。直接の一段階差を得るために中間機関や反例の教会を除かない。異なる統治制度・地域・基準時の辺をつながない。現在の政治的国境や組織名から関係を補わない。',
    'Klassisの自己呼称・Holländern・ehrwürdig・etwa、原文の否定疑問、相互宣誓、変更不能な信条、全構成員とその成員を介する人民への上位後見・持続、次の否定回答は未統合。名前や型だけでこれらを記述済みと数えず、本文96主張・登録簿v180・意味確認分量は保持する。',
]


@lru_cache(None)
def parents(): return tuple(load_catalog(ROOT, path) for path in PARENTS)


def definitions():
    fields = 'person a body a activity a issue a church a creed a subject a'
    text = 'd r46d[' + fields + '] e[b point[' + both(
        'k h246c[v body v person v point]', 'k dg[v activity v point]', 'k f3[v person v activity v point]',
        'k h254i[v activity v body v point]', 'k h254h[v activity v issue v point]',
        'k h254j[v body v issue v point]', 'k h254k[v issue v church v point]',
        'k r35r[v church v creed v subject v point]') + ']].\n'
    names = ('activity', 'issue', 'church', 'creed', 'subject')
    text += 'd r46e[person a body a] e[b point[' + quant(names,
        't[k r46d[v person v body ' + ' '.join('v '+n for n in names) + ']][v point]', 'g') + ']].\n'
    practice = lambda body: 'k h246h[v ' + body + ' r[p r46e] v reference]'
    text += 'd r46f[body a reference d] c[' + both(
        'x[k r456[v body v reference]][k r46c[v body v reference]]', practice('body')) + '].\n'
    between = both('c[v scope][v middle]', 'c[v order][v higher v middle]', 'c[v order][v middle v lower]')
    text += 'd r46g[higher a lower a scope h[a] c order h[a a] c] c[' + both(
        'k rey[v higher v lower v scope v order]', 'u[g middle a[' + between + ']]') + '].\n'
    scope = 'i[node a][k h254l[v node v polity v reference]]'
    order = 'i[high a low a][k h254m[v high v low v polity v reference]]'
    text += 'd r46h[body a local a upper a polity a reference d] c[' + both(
        'k r46g[v body v local ' + scope + ' ' + order + ']',
        'k r46g[v upper v body ' + scope + ' ' + order + ']') + '].\n'
    represented = lambda church: 'k h254g[v body v ' + church + ' v reference]'
    text += 'd r46i[body a district a reference d] c[' + both(
        quant(('left', 'right'), both(represented('left'), represented('right'), 'u[e[v left][v right]]'), 'g'),
        'f church a[y[' + represented('church') + '][k h254o[v church v district v reference]]]') + '].\n'
    fields = 'body a district a province a polity a upper a reference d'
    local = 'g local a[' + both('k h254n[v local v church v reference]',
        'k r46h[v body v local v upper v polity v reference]') + ']'
    text += 'd r46j[' + fields + '] c[' + both(
        'k r46f[v body v reference]', 'k r46c[v body v reference]', 'k r46i[v body v district v reference]',
        'k h254p[v district v province v reference]', 'k h254r[v province v polity v reference]',
        'k h254q[v upper v province v polity v reference]', practice('upper'),
        'f church a[y[' + represented('church') + '][' + local + ']]') + '].\n'
    names = ('district', 'province', 'polity', 'upper')
    text += 'd r46k[body a reference d] c[' + quant(names,
        'k r46j[v body ' + ' '.join('v '+n for n in names) + ' v reference]', 'g') + '].\n'
    return text


def build():
    old, delegated = parents(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['rey', 'r35r', 'dg', 'f3']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    for d in closure(delegated.document, ['r456', 'r46c']):
        n = d['name']
        if n in imported: assert d == imported[n]['declaration'] and delegated.entries[n]['meaning_ja'] == imported[n]['meaning_ja'], n
        else: doc['declarations'].append(d); imported[n] = delegated.entries[n]
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(delegated.entries))
    doc = parse(format_graph(doc, 'compact') + ''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'], arguments=e['arguments'],
        meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n,row in PRIMITIVES.items()})
    paths = set().union(*(set(c.source_sha256) for c in parents()))
    basis = dict(status='religious_deliberative_practice_and_regional_council_level', document=LIBRARY, primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'} | MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc,'compact')+'\n', BASIS: json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
