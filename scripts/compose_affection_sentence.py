"""Bind acquired attachment and deprivation to the same people and discourse."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_scalar_backgrounds import PAIR, PC

PARENT = 'examples/v016/kant-nature-sentence.noema'
PARENT_BASIS = 'data/nature-sentence-basis-v1.json'
FULL = 'examples/v016/kant-affection-sentence.noema'
CORE = 'examples/v016/affection-sentence-core.noema'
BASIS = 'data/affection-sentence-basis-v1.json'
ANNOTATIONS = 'data/affection-sentence-identifiers-v1.json'
REFERENCES = {
    'hzzr': 'カント1784第三段落第二文、固定転写のu0010 [126,292) の談話箇所。第一文の箇所hzzqと別に参照する。',
    'hzzs': '同じ第二文の主張全体 [126,292) の原文範囲。意味確認の完了を含意しない。',
    'hzzt': '同じ第二文のsogarと愛着の取得 [137,156) の焦点範囲。不能とその原因をこの強調の焦点へ含めない。',
}
MEANINGS = {
    'r2ee': '同じ本人・状況で、未成熟への愛着の取得と保持r2ck、および試行の許容不在から現在の行使不能への因果r2cgを併記する。愛着から不能への因果は主張しない。',
    'r2ef': '第一文のhzzn・hzzqで固定した非空の人物範囲を保ち、各人が人であることと、引数の性質がその同じ本人・状況に成立することを要求する。人称を別集団や別人へ取り替えない。',
    'r2eg': '第一文と同じ各人が、自分の未成熟へ愛着を獲得して保持する内容。第二文前半の閉じた焦点内容。',
    'r2eh': '第一文と同じ各人に、本性に近い内的定着r2ebがある内容。愛着の取得との期待比較に使う明示的な文脈上の比較候補。',
    'r2ei': '第一文と同じ各人について、愛着の取得と、過去の試行の許容不在による現在の行使不能をr2eeで結ぶ。自立的な理解の不能bfと、指導も許す理解の使用自体の不能r2cfを区別する。',
    'r2ej': '愛着の取得r2egを焦点とし、内的な定着r2ehを比較候補にする主張・期待背景の組。既存rqtsとhzptを使い、著者の提示する期待・同じ基準で焦点を相対的に見込みにくいものとして位置づける。',
    'r2ek': '主張全体r2eiと、愛着に限ったr2ejの期待背景を一つの組に保持する。不能やその原因の主張全体を、sogarの比較対象へ広げない。',
    'r2el': '第二文全体の主張と、愛着に関する期待背景を同じ著者・箇所・文脈へ帰属する。主張範囲hzzsと焦点範囲hzztを分け、世界内容の真理を帰属からは導かない。',
    'r2em': '第一文hzzqから第二文hzzrへの本文順序を同じ文脈で保持する。愛着が不能を引き起こしたという因果や、時間的な順序を代用しない。',
}
LIMITS = [
    '第二文の閉じた記述候補を本文へ接続する。wirklichの確認的な強調、vor der Handの語用、一般的な単数人称と全称の関係、第二文の通し判断は未完である。',
    'sogarには愛着の取得を焦点とする期待比較の読みを採る。比較候補を先行する内的定着の内容とすること、各人への内容を全体として比較することは文脈上の解釈選択であり、文法資料が唯一の読みを証明するものではない。',
    '期待比較の背景と主張の真偽を分離する。数値確率、実際の驚き、全ての代替内容の現実の成立は追加しない。比較の未知を同順位や比較不能に補わない。',
    '愛着と不能は同じ本人へ結ぶ。不能の原因は過去の試行の許容不在であり、愛着を新しい原因としない。能力と取得の既存の評価条件・履歴・比較範囲の限界を継承する。',
    '旧第12・13文の部分帰属を更新し、他の50文と旧定義を保持する。第一文108文字の判断と十二全単位2,212文字の判断を維持するが、第二文の意味確認完了や段落全体の完成は数えない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2ee[person a] e[b point[w[t[k r2ck[v person]][v point]][t[k r2cg[v person]][v point]]]].
d r2ef[property h[a] e] e[b point[w[g person a[k hzzn[k hzzq[] v person v point]]][
 f person a[y[k hzzn[k hzzq[] v person v point]][w[k aa[v person]][t[c[v property][v person]][v point]]]]
]]].
d r2eg[] e[k r2ef[p r2ck]].
d r2eh[] e[k r2ef[p r2eb]].
d r2ei[] e[k r2ef[p r2ee]].
d r2ej[] ''' + PAIR + '''[k rtf[r c[p rqts] r b[r b[k r2eg[]]]
 r b[l[''' + PC + '''][r b[k r2eh[]]]] r[k wa[]] r[k wh[]] r[p hzpt]]].
d r2ek[] ''' + PAIR + '''[k rst[r c[k r2ei[]] k rsv[k r2ej[]]]].
d r2el[] c[k rqtv[k hzzr[] k wa[] k r2ek[] k hzzs[] k hzzt[] k wh[]]].
d r2em[] c[k ue[k hzzq[] k hzzr[] k wh[]]].
'''


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(MEANINGS) | set(REFERENCES)) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + name + '[] a.' for name in REFERENCES) + definitions())
    assert len(statements) == 52 and statements[11]['body']['symbol'] == 'h2c' and statements[12]['body']['symbol'] == 'h3b'
    statements[11:13] = [dict(kind='assert', body=dict(kind='call', symbol=name, arguments=[])) for name in ('r2el', 'r2em')]
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=doc['statements'][11:13])
    added = doc['declarations'][size:]; assert len(added) == 12
    basis = dict(status='attachment_focus_and_deprivation_joined_under_explicit_reading', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={d['name']: dict(parameters=d['parameters'], result=d['result'], arguments=[], meaning_ja=REFERENCES[d['name']])
                    for d in added if d['kind'] == 'primitive'}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/nature-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Nine definitions, three local references; two partial attributions replaced', flush=True)
