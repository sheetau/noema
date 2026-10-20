"""Connect acquired familiarity with a projected free-judgment kind and cause."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-uncertain-judgment.noema'
PARENT_BASIS = 'data/uncertain-judgment-basis-v1.json'
FULL = 'examples/v016/kant-unfamiliar-judgment.noema'
CORE = 'examples/v016/unfamiliar-judgment-core.noema'
LIBRARY = 'examples/v016/free-judgment-kind.noema'
BASIS = 'data/unfamiliar-judgment-basis-v1.json'
ANNOTATIONS = 'data/unfamiliar-judgment-identifiers-v1.json'
MEANINGS = {
    'r2he': '前版r2gxの同じ本人・判断活動・時点を保ち、課題を存在量化する。自分の理解力による、他者の指導なしの判断活動という種類の条件。特定の課題への同一性、理由の支持、不確かさは種類の条件に含めない。',
    'r2hf': 'r2heを満たす本人の判断活動があるという、引用可能な活動種類の内容。前版の不確かな判断r2haの同じ活動もこの種類に属するが、この種類自体は不確かさを要求しない。',
    'r2hg': '同じ本人と仮定終点について、知的活動側の有効な履歴で、r2hfという同じ活動記述への過去の経験が現在へ寄与し、現在の反応も定着している。既存rchへ記述と履歴を固定する。',
    'r2hh': '同じ仮定履歴が有効で終点を含み、r2hgの経験由来の慣れが成立しない。既存rciを同じ活動記述へ適用する。未確認・不正な履歴、経験が一度もないこと、判断能力の欠如とは区別する。',
    'r2hi': '同じ有効な仮定履歴で、r2hfの過去の経験が少なくとも一つある。現在への寄与と定着は要求しない。経験の有無と現在の慣れを分ける対照用内容。',
    'r2hj': '同じ本人・仮定終点で、不慣れr2hhと前版の不確かな判断r2hbが成立し、同じ二記述を結ぶhzieの因果的寄与がある。両内容の併存や原因説明への採用だけから寄与を導かない。',
    'r2hk': '同じ二内容が成立し、その二記述がeaで原因説明に採用される。r2hjとの対照用であり、これだけでは実際の因果的寄与を満たさない。eaの対象引数は要因と結果の主体であり、説明者の指定ではない。',
    'r2hl': '同じ本人・非空の仮定集合で、依存離脱r2gtなら理由付きの帰結r2hjが成立し、離脱を満たす仮定もある。現在の離脱や、全員の不慣れを事実として追加しない。',
    'r2hm': '提示文脈whに固定した同じ知的活動側の仮定集合にr2hlを適用する。第四文の理由付き条件骨格候補であり、本文への著者帰属・身体的描写との対応・譲歩と尺度限定は未接続である。',
}
LIMITS = [
    'dergleichen freier Bewegungの対象側を、自分の理解力を他者の指導なしに使う判断活動の種類として読む。特定課題の同一性と不確かさを種類の条件から除く構成であり、身体運動の全種類や全ての精神的活動を同一視しない。共有すべき性質の唯一の原文解釈とはしない。',
    '経験・寄与・定着は同じ閉じたr2hfの記述へ結ぶ。種類の記述を引用したことだけでは、その活動が現在実行されることを要求しない。過去の経験の実在や現在への寄与を自動発見する処理でもない。',
    '慣れは経験に由来する現在の定着として構成する。過去に経験があっても、寄与や定着が失われれば不慣れを許す。生得的な反応、成功、理由の支持、主観的自信とは分ける。',
    '理由は離脱を満たす仮定の中に置く。現実の提示時点にも不慣れが投射する読み、唯一・十分・必要な原因、心理機構の全説明は追加しない。hzieは明示された意味上の因果入力であり、有限検査が実世界の原因を実証するものではない。',
    '最も小さい困難の尺度、nurの限定、auchとdennochの譲歩・期待、身体的描写との対応と種類照応の全体判断は残る。本文54文は変更せず、第四文の意味確認済み分量は加えない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def additions():
    text = '''
d r2he[person a judgment a point d] c[g topic a[k r2gx[v person v judgment v topic v point]]].
d r2hf[person a] e[b point[g judgment a[k r2he[v person v judgment v point]]]].
'''
    for name, operation in [('r2hg', 'rch'), ('r2hh', 'rci'), ('r2hi', 'rcj')]:
        args = 'v person r[p r2hf] v point i[past d][k hzzzs[v person v point v past]] i[first d last d][k ic[v first v last v point]] p h3e'
        if operation != 'rcj': args += ' p h3g p h3f'
        text += 'd '+name+'[person a] e[b point[k '+operation+'['+args+']]].\n'
    for name, relation in [('r2hj', 'hzie'), ('r2hk', 'ea')]:
        text += 'd '+name+'[person a] e[b point[w[t[k r2hh[v person]][v point]][w[t[k r2hb[v person]][v point]][k '+relation+'[v person r[p r2hh] v person r[p r2hb] v point]]]]].\n'
    return text + '''
d r2hl[person a cases h[d] c] c[w[k rc[v person p r2gt p r2hj v cases]][k re[v person p r2gt v cases]]].
d r2hm[person a] e[b anchor[w[e[v anchor][k wh[]]][k r2hl[v person i[scene d][k hzzzy[v person v anchor v scene]]]]]].
'''


def build():
    old = parent(); doc = deepcopy(old.document); statements = doc['statements']; doc['statements'] = []
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions()); doc['statements'] = statements
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2hm', 'r2hk', 'r2hi']), statements=[])
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['r2he', 'r2hf']), statements=[])
    added = doc['declarations'][len(old.document['declarations']):]; assert len(added) == 9
    basis = dict(status='unasserted_unfamiliarity_and_causal_conditional_candidate', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS, primitives={},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/uncertain-judgment-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact')+'\n', LIBRARY: format_graph(lib, 'compact')+'\n',
        BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Unfamiliar activity kind and causal conditional composed; 54 statements preserved', flush=True)
