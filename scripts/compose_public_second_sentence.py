"""Integrate the forecast, its metaphor, expressive tone and reason presentation."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-guardian-forecast.noema'
PARENT_BASIS = 'data/guardian-forecast-basis-v1.json'
FULL = 'examples/v016/kant-public-second-sentence.noema'
CORE = 'examples/v016/public-second-sentence-core.noema'
BASIS = 'data/public-second-sentence-basis-v1.json'
ANNOTATIONS = 'data/public-second-sentence-identifiers-v1.json'
PRIMITIVES = {
    'h223l': ('[a a i b[h[a d] c] i b[h[a d] a] d] c',
              ['node', 'presenter', 'scope', 'referent_family', 'context'],
              '提示者が指定の文章箇所・文脈で、引用された対象範囲の各個体・参照状況に対応する参照族の対象を、低く扱う呼び方で提示する。対象族は同じ範囲の引数へ適用するものとして解釈する。呼称による評価的な扱いの帰属であり、対象の実際の価値・能力・社会的身分や、提示者の内心の感情強度を認定しない。人数や本文の主張の真偽とは別で、範囲と参照族の内容を帰属時に実行しない。特定の語や作品に限定しない。'),
    'h223m': ('[] a', [],
              '固定原文kant-1784:u0011第二文で大衆を指すdes großen Haufensの箇所[218,236)。人数や対象の意味自体は既存h223i/r2m7で記述する。'),
}
MEANINGS = {
    'r2mh': '同じ第二文の公衆範囲h222eと大衆参照族h223iを引用し、当該箇所h223mで著者waが大衆を低く扱う語調で提示することをh223lへ結ぶ。大衆の人数、後見役の任用、誰が自己思考者かという主張へ評価語調を混ぜない。',
    'r2mi': '同じ第二文の閉じた予測と比較背景r2mf、自己離脱を頚木の除去として提示するhzpp、第一文への理由提示hzp6、大衆の評価的な呼称r2mhを一つの本文記述に統合する。予測の各発信者のhzoeは同じ人・過程・前後点のhzod/h4pを要求し、それはhzppの対象h4qの証人になる。身体的な装具や除去の事実、知的過程と物理過程の同一性を要求しない。',
}
LIMITS = [
    'daを先行文の自由を残す場合への照応、werdenをその場合の将来予測、immerを指定した議論期間の全評価機会として読む。成功する機会だけを選ばず、機会は非空で後続点を持つ。無限の全未来を有限試験で尽くしたとはしない。',
    'einigeは異なる二人以上で、ちょうど二人・全員ではないこと・後見役が二人以上であることは要求しない。sogarの焦点はその中の少なくとも一人の任用された後見役。非後見役にも成功者がいるとは断言しない。',
    '自己思考者は数値なしの独立判断への性向を持つ人。同じ発信者が自ら知的自立を達成し、その完了後に始まる伝達によって周囲の複数人が同じ性向を取得する。自己関与は必要だが他者の助力を排除しない。将来は取得完了にかかり、すでに始まった伝達の継続も許す。',
    '頚木は首・頭側に装着され牽引を別の荷へ伝える枠を本人が除く描写。その同じ人物役を知的自己離脱の達成h4qへ対応させる。予測のh4pからh4qへの存在導入で照応を確認し、別の人や経路外の達成で代用しない。物理的な装具の現実存在や二過程の同一性は加えない。',
    'Haufenはこの文脈の大勢の被指導者を一括して低く扱う呼称と読む。語調を人数条件へ還元せずh223lで別に帰属する。固定身分・貧困・全員の無思考・地理的な密集を加えない。侮蔑の数値的な強さ、読者全員の感情反応は主張しない。',
    'Geistは理由ある自己評価と人としての自己思考への使命の承認へ向かう性向、Berufは職業に限定されない人の課題、um sichは社会的接点、verbreitenは複数の他者への新しい取得という読み。既存の判断・規範・伝達・因果・持続を保持する。',
    'Dennは先行文に対する著者の理由提示であり、第二文から第一文が論理的に導けるという証明ではない。sogarの見込みの比較と呼称の評価は別々に扱う。原著者の哲学的予測の実際の正しさは検証対象ではない。',
    '固定原文第二文319文字・274非空白文字についてのアシスタントの読解判断。基本関係の意味規約に従う明示した読みであり、自動同義性証明・独立査読・あらゆる語用的連想の列挙ではない。第四段落残部と二作品全文の確認は別に必要である。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    text += '''
d r2mh[] c[
 k h223l[k h223m[] k wa[] r b[p h222e] r b[p h223i] k hzp3[]]
].
d r2mi[] c[w[k r2mf[]][w[k hzpp[]][w[k hzp6[]][k r2mh[]]]]].
'''
    doc = parse(format_graph(doc, 'compact') + text)
    added = doc['declarations'][len(old.document['declarations']):]
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2mi', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2mi']), statements=[statement])
    declarations = {d['name']: d for d in added}
    primitives = {n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                          arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()}
    basis = dict(status='second_sentence_integrated_under_explicit_reading',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives=primitives,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/guardian-forecast-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
