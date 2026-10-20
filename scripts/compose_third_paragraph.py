"""Close the extrication image and relate the paragraph's two person domains."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_scalar_backgrounds import PAIR

PARENT = 'examples/v016/kant-self-formed-course.noema'
PARENT_BASIS = 'data/self-formed-course-basis-v1.json'
FULL = 'examples/v016/kant-third-paragraph.noema'
CORE = 'examples/v016/third-paragraph-core.noema'
BASIS = 'data/third-paragraph-basis-v1.json'
ANNOTATIONS = 'data/third-paragraph-identifiers-v1.json'
SELECTION = [10, 11, 12, 13, 14, 15, 51, 52, 53, 54]
MEANINGS = {
    'r2ko': '同じ足枷の先行描写と参照対応r2giを保持し、第五文の自己活動による自立達成h4qを、同じ本人が指定された身体拘束を取り除くh3nで描くというqhの帰属。heraus zu wikkelnを拘束から自分を解き放つ読みとして接続する。縄の巻き方や投擲動作、現実の身体拘束は加えない。',
    'r2kp': '第一文から第四文までの同じ提示基準wh・箇所hzzqで扱う人aaかつhzznの全員が、第五文の同じ評価文脈の計数母集団h4iにも入る。等しい集合や、成功者も現在未成熟であることは要求しない。',
    'r2kq': 'r2kpによる母集団の接続と、自己活動が両成果へ寄与するr2kkの数量前景を同じ状況で要求する内容。対象集団を成功者だけの無関係な標本へ置き換えない。',
    'r2kr': 'r2kpの同じ母集団接続とr2klの譲歩背景を同じ状況で要求する内容。成功者数を背景に重複させず、冒頭の対象者への現在の不能を成功者全員へ広げない。',
    'r2ks': '閉じたr2kqの数量前景とr2krの譲歩背景を既存rstの対にする。前景の否定は背景の否定と区別する。',
    'r2kt': '同じ第五文の箇所h5t・著者wa・文脈wh・前景と譲歩の範囲へr2ksを帰属する。第四文の主節と理由からの推論提示と本文順序を保持し、内容の現実的な真理や論理的導出は主張しない。',
}
LIMITS = [
    'heraus zu wikkelnは、先行する足枷・その除去・不確かな跳躍から続く自己解放の像として読む。既存h3nは本人が因果的に身体拘束を取り除く過程を表すが、投げ捨てる具体動作は条件にしていない。縄の材質・巻数・捻る手順をこの文へ補わない。',
    '第三段落前半は文脈上の未成熟な個々人の範囲hzznについての説明、第五文はその人々を含み、困難を克服した人も含め得る比較母集団h4iについての少数者の主張とする。範囲は結論から選ばず、両者の包含を明示する。全員を現在未成熟な人へ限定して成功者を数える読みではない。',
    '第五文は一人以上いる少数者、同じ作業による自立と確かな活動、完了点の時間順、実際の該当者への譲歩背景という既存の読みを採る。数量上限、代替条件、通常予想の選択は公開規約に従う文脈入力。',
    '確かな知的活動は理由ある独立判断と有効な通常比較での遂行を全活動の判断に要求する。誤りの絶対的不在、恒久的な能力、身体歩行の実在を成功者条件に加えない。',
    '先頭四文の採用解釈と判断を保持する。全種類・全時代の語感を同時に保存する判断ではなく、著者の哲学的主張が現実に正しいことの証明でもない。',
    '単位全体の判断は、原文との再読によるアシスタントの判断として別記する。形式検査の成功や全範囲の対応だけから自動生成するものではない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def additions():
    return '''
d r2ko[] c[w[k r2gi[]][k qh[k h5t[] k wa[] r[p h4q] r[p h3n] k wh[]]]].
d r2kp[context d] c[f person a[y[w[k aa[v person]][k hzzn[k hzzq[] v person k wh[]]]][
 k h4i[v person v context]]]].
d r2kq[] e[b point[w[k r2kp[v point]][t[k r2kk[]][v point]]]].
d r2kr[] e[b point[w[k r2kp[v point]][t[k r2kl[]][v point]]]].
d r2ks[] ''' + PAIR + '''[k rst[r c[k r2kq[]] r c[k r2kr[]]]].
d r2kt[] c[w[k rqtv[k h5t[] k wa[] k r2ks[] k h5t[] k h222d[] k wh[]]][w[
 k ud[k wa[] i[node a][x[e[v node][k h3a[]]][e[v node][k h3s[]]]] k h5t[] k wh[]]
 ][k ue[k h3s[] k h5t[] k wh[]]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions())
    assert len(statements) == 54 and statements[15]['body']['symbol'] == 'r2kn'
    statements[15] = dict(kind='assert', body=dict(kind='call', symbol='r2kt', arguments=[]))
    statements.append(dict(kind='assert', body=dict(kind='call', symbol='r2ko', arguments=[])))
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2kt', 'r2ko']), statements=[statements[15], statements[54]])
    added = doc['declarations'][len(old.document['declarations']):]
    basis = dict(status='third_paragraph_adopted_under_explicit_reading',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives={},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/self-formed-course-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
