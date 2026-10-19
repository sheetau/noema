"""Reuse scoped assurance for the present inability in the second sentence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-affection-sentence.noema'
PARENT_BASIS = 'data/affection-sentence-basis-v1.json'
FULL = 'examples/v016/kant-confirmed-incapacity.noema'
CORE = 'examples/v016/confirmed-incapacity-core.noema'
BASIS = 'data/confirmed-incapacity-basis-v1.json'
ANNOTATIONS = 'data/confirmed-incapacity-identifiers-v1.json'
RESTORED_FROM = 'examples/v016/kant-nature-sentence.noema'
MEANINGS = {
    'r2en': '第一文と同じ非空の人物範囲の各人について、現在の基準における自分の理解力の行使不能r2cfだけを取り出す。愛着・その取得・過去の許容不在・因果を確言の焦点へ含めない。未来の能力や回復時期は述べない。',
    'r2eo': '第二文の主張と期待背景の帰属r2elに、同じ著者・箇所・主張r2ei・文脈における現在の不能r2enへの確言hzxuを結ぶ。既存の提示態度を再利用し、実際の知識・内心の確信・世界の真理を帰属から導かない。',
}
LIMITS = [
    'wirklichを、現在の不能を確かなこととして述べる確認的な提示と読む。既存hzxuを再利用し、未知語全体の判定関係や、別の能力内容を追加しない。現代辞典は用法の比較資料であり、1784年の唯一の読解を自動的に確定する根拠ではない。',
    'vor der Handを現在の基準への限定として読む。基準状況は瞬間に限定されず、本文が扱う現在の局面を解釈する。明示されない期間・将来の回復・永久の不能を追加しない。',
    'Erとその後の同じ人称は第一文の各人への説明の継続、sieはその人自身の未成熟への参照とする。hzznで人物範囲を固定し、万人・全時代の無条件の一般法則や特定の実在人へ置き換えない。',
    '愛着の取得と現在の不能・原因の併記、愛着だけの期待比較の読みを前版から継承する。比較対象と尺度、心理的比較状況、能力の通常機会、許容の履歴、因果関係は公開した意味規約に依存する。',
    '自分の理解力の使用bmには、他人の指導なしというbbの条件を加えない。不能は指定された現在の判断基盤・通常機会の評価であり、全ての可能な援助下で永久に不能という意味ではない。',
    'この肯定文のweil節は、試行の許容不在から現在の不能への実際の寄与として読む。愛着を原因へ変えず、試行そのものの不在、単なる説明への採用、唯一・必要・十分な原因とも区別する。',
    '原文一文の判断は以上の明示した読みの下でのアシスタントによる判断である。独立査読、同義性の自動証明、発話の全ての語感や他の読解の同時保存は未実施。第三段落全体と二作品の全文は未完である。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + '''
d r2en[] e[k r2ef[p r2cf]].
d r2eo[] c[w[k r2el[]][k hzxu[k hzzr[] k wa[] r[k r2ei[]] r[k r2en[]] k wh[]]]].
''')
    assert len(statements) == 52 and statements[11]['body']['symbol'] == 'r2el'
    statements[11] = dict(kind='assert', body=dict(kind='call', symbol='r2eo', arguments=[]))
    original = parse((ROOT / RESTORED_FROM).read_text(encoding='utf-8'))
    restored = original['statements'][11:13]
    assert [s['body']['symbol'] for s in restored] == ['h2c', 'h3b']
    assert all(s not in statements for s in restored)
    statements.extend(deepcopy(restored))
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2eo', 'r2em']), statements=doc['statements'][11:13])
    added = doc['declarations'][size:]; assert len(added) == 2
    basis = dict(status='second_sentence_with_focused_confirmation_of_current_inability', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS,
        restored_statements=dict(document=RESTORED_FROM, original_indices=[11, 12], current_indices=[52, 53],
            reason='The preceding revision mistakenly replaced third- and fourth-sentence partial attributions as though they belonged to the second sentence. Restore both unchanged.'))
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/affection-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Two definitions, no new primitive; scoped assurance added to the second sentence', flush=True)
