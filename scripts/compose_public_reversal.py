"""Bind the two directions of influence to one public and prior guardian cohort."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-collective-retention.noema'
PARENT_BASIS = 'data/collective-retention-basis-v1.json'
FULL = 'examples/v016/kant-public-reversal.noema'
CORE = 'examples/v016/public-reversal-core.noema'
BASIS = 'data/public-reversal-basis-v1.json'
ANNOTATIONS = 'data/public-reversal-identifiers-v1.json'
FIELDS = [
    ('public', 'a'), ('guardians', 'a'), ('affected', 'j[a]'), ('former', 'j[a]'),
    ('agitators', 'j[a]'), ('earlieract', 'a'), ('earlier', 'd'),
    ('incitingact', 'a'), ('incited', 'd'), ('pressure', 'a'), ('participants', 'j[a]'),
    ('history', 'i[h[d] c]'), ('before', 'i[h[d d] c]'),
    ('first', 'i[d]'), ('last', 'i[d]'), ('anchor', 'd'),
    ('guardianrole', 'h[a a d] c'), ('incapable', 'h[a d] c'),
    ('incites', 'h[a a j[a] a d] c'),
]
MEANINGS = {
    'r2mo': '同じ集団の完全な構成員列と、選択した人々の非空の列について、重複がなく全員が人であり、選択者全員が集団に属することを要求する。集団の全員と選択者の同一性や、結果に応じた選別を含意しない。',
    'r2mp': '同じ後見人群の同じ先行する参加者が担う一つの共同的な生起行為が、同じ公衆の指定された各被作用者について知的未成熟bfを結果として生じさせ、各人にその状態が実際に成立する。対象範囲は非空で公衆の構成員に含まれる。全公衆員が以前は自立していたという条件や、全員への一律の効果を加えない。',
    'r2mq': '異なる二人以上の扇動者が同じ公衆の後見役で、同じ扇動時点に啓蒙不能の指定条件を満たし、同じ一つの生起行為へ参加する。その同じ行為が同じ公衆を指定された後の圧力行為へ駆り立てるという関係をincitesで要求する。不能と扇動の具体的な定義は引数に残し、参加・人数だけで扇動を認定しない。',
    'r2mr': '同じ公衆への先行するr2mpを保持し、先行する後見人はその時点の同じ公衆の後見役とする。同じ事例のr2mqの扇動条件が成立すれば、公衆が先行の参加後見人全員をr2mnの圧力で未成熟に留める。先行作用と扇動はいずれも圧力開始より前で同じ履歴内だが、両者の間の順序は追加しない。扇動者と先行後見人の一致・不一致を固定しない。',
}
LIMITS = [
    '第三文の公衆・先行の作用者・後の被強制者を同じ事例へ結ぶ部分構成である。先行後見人群の全成員ではなく、実際に先行行為を担ったformerの全員を後の対象にする読みを採る。対象の同一性を、二つの無関係な存在から補わない。',
    '先行作用の被作用者affectedは、公衆の中の文脈で指定された非空の範囲である。全公衆が一様に未成熟となる読み、変化前は全員自立していたという読みを勝手に加えない。原文の集団への述定として範囲が十分かを決める基準とその参照の充足は後続作業に残る。',
    '扇動者は二人以上の後見役という複数の読み。先行の後見人や後の公衆側参加者と同じ集合とはしないが、重なりも禁止しない。本人の不能は扇動条件の内部で各扇動者だけに要求し、全ての後見人へ広げない。',
    '先行する作用と扇動は共に後の圧力より厳密に前であるが、その二つの前後は原文がここで定めていないため固定しない。共通履歴の順序と始終点は有効性を検査する。各記述が原文の同じ事例を指すことは後続の閉じた参照供給で検査する必要がある。',
    'guardianrole・incapable・incitesは具体的な意味構成を渡す関数引数であり、文全体を不透明な新しい基本語で置換していない。これらが未充足なので、本文への閉じた著者帰属や第三文全体の意味確認はまだ行わない。',
    '既存の59文、先頭二文382非空白文字、十三の全単位判断を保持する。頚木の照応、際立て・自己の取り立て、扇動・不能の定義、偏見と害・報復の構成は残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    fields = ' '.join(n + ' ' + t for n, t in FIELDS)
    return '''
d r2mo[group a selected j[a]] c[
 w[k hi[k mp[v group] p aa]][w[k hi[v selected p aa]][
 w[g person a[k hg[v selected v person]]][
 f person a[y[k hg[v selected v person]][k hg[k mp[v group] v person]]]
 ]]]
].
d r2mp[public a guardians a affected j[a] former j[a] act a point d] c[
 w[k r2mo[v public v affected]][w[k r2ml[v guardians v act v former v point]][
 f person a[y[k hg[v affected v person]][
 w[t[k bf[v person]][v point]][k g3[v act v person r[p bf] v point]]
 ]]
 ]]
].
d r2mq[public a agitators j[a] act a pressure a point d
 guardianrole h[a a d] c incapable h[a d] c incites h[a a j[a] a d] c] c[
 w[k hi[v agitators p aa]][
 w[g first a[g second a[w[k hg[v agitators v first]][w[k hg[v agitators v second]][u[e[v first][v second]]]]]]][
 w[k dg[v act v point]][
 w[f person a[y[k hg[v agitators v person]][
 w[c[v guardianrole][v person v public v point]][w[c[v incapable][v person v point]][k df[v person v act v point]]]
 ]]][c[v incites][v act v public v agitators v pressure v point]]
 ]]]
].
d r2mr[''' + fields + '''] c[
 w[k ta[s[v history] s[v before]]][
 w[c[s[v history]][v earlier]][w[c[s[v history]][v incited]][
 w[c[s[v history]][s[v first]]][w[c[s[v history]][s[v last]]][w[c[s[v history]][v anchor]][
 w[c[s[v before]][v earlier s[v first]]][w[c[s[v before]][v incited s[v first]]][
 w[c[s[v before]][s[v first] s[v last]]][
 w[x[e[s[v last]][v anchor]][c[s[v before]][s[v last] v anchor]]][
 w[k r2mp[v public v guardians v affected v former v earlieract v earlier]][
 w[f person a[y[k hg[v former v person]][c[v guardianrole][v person v public v earlier]]]][
 y[k r2mq[v public v agitators v incitingact v pressure v incited v guardianrole v incapable v incites]][
 f person a[y[k hg[v former v person]][
 k r2mn[v public v pressure v person v participants v history v before v first v last v anchor]
 ]]
 ]
 ]]]]]]]]]]]]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2mr']), statements=[])
    basis = dict(status='public_and_guardian_roles_bound_conditional_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives={},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/collective-retention-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
