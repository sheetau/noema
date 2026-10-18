"""Fix the contextual content criterion without changing the manuscript syntax."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-incidental-agreement.noema'
PARENT_BASIS = 'data/incidental-agreement-basis-v1.json'
FULL = 'examples/v016/kant-footnote-reading.noema'
CORE = 'examples/v016/footnote-reading-core.noema'
BASIS = 'data/footnote-reading-basis-v1.json'
ANNOTATIONS = 'data/footnote-reading-identifiers-v1.json'
SELECTION = [0, *range(18, 27), 40, 41]
CONVENTIONS = {
    'hzlf': '同じ問いへの二回答で比較する論点の範囲。両者が述べる主題・主張・理由・問い・要求のうち比較に関係するものを、一致を調べる前に共通の粒度で定める。片方にしかない内容も除外せず、一致した論点だけを後から選ばない。この著者注は実際の全論点の列挙を与えず、当該問いに関係する内容を比べるという範囲指定を用いる。',
    'hzlh': '当該文献がその論点で伝える内容項目。表面の文・語・綴りの個数ではなく、共通の比較粒度で帰属させる意味内容である。指示対象、出来事と参与役割、肯否、数量・量化と作用域、時間・様相、条件、主張・問い・要求の違いを保つ。肯定的な主張の連言は内容ごとに分けて対応させられるが、否定・可能性・引用等の作用域を越えて分割しない。片方の非対応内容を省いて一致を作らず、どちらも述べないことを一致と数えない。実際の抽出を自動化する規則ではない。',
    'hzli': '同じ論点・状況・比較粒度で、比較元が伝える内容上の要求を比較先が保持する対応。指示対象、参与役割、肯否、量化と作用域、時間・様相、条件、発話の種類と問われる対象を保つ。相手に追加内容がある片方向の保持はあり得るので、双方の一致には両方向を要求する。定義名と展開、束縛変数名、同じ役割を保つ言い換え、同じ主張内の独立な連言の並べ替えは、表記が違うことだけを理由に除外しない。同時に真であるだけの別内容、語の一致、任意の論理的同値だけでは対応としない。未知の対応は偽と断定しない。これは意味解釈の規約であり、全同義関係を決めるアルゴリズムではない。',
    'hzkv': '共通の比較論点hzlfと内容項目hzlhについて、双方の全項目に双方向の内容保持hzliによる対応があり、その論点が候補範囲hzlgに過不足なく含まれるというrqryの条件。wiefernを一致する論点の範囲と読む。重み付き割合・最大値・思想の真実性は補わない。文脈で採った共通粒度と帰属の下での一致であり、任意の全思想比較の唯一の尺度を主張しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent()
    doc = deepcopy(old.document)
    basis = dict(status='contextual_thought_content_conventions_for_whole_footnote_reading', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['共通の粒度、帰属内容、内容保持は意味の解釈条件。実文献の全思想抽出や比較答えの自動計算は行わない。',
            '独立な連言の順序と内容の分割は、主張の内容の比較で許す。談話の順序、引用された表記、否定・様相・量化の作用域を勝手に変更しない。',
            '有限の検査例や定義展開だけを、この比較規約の全適用範囲と同一視しない。',
            '本文・文法・基本語・定義本体は増やさない。四つの意味規約の採用範囲を確定し、著者注全体の判断は別のレビューに記録する。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for declaration in doc['declarations']:
        n = declaration['name']
        meaning = CONVENTIONS[n] if n in CONVENTIONS else old.entries[n]['meaning_ja']
        if declaration['kind'] == 'primitive':
            basis['primitives'][n] = dict(parameters=declaration['parameters'], result=declaration['result'],
                arguments=old.entries[n]['arguments'], meaning_ja=meaning)
        else:
            basis['definitions'][n] = meaning
    core = deepcopy(doc)
    core['statements'] = [doc['statements'][i] for i in SELECTION]
    core['declarations'] = closure(doc, [s['body']['symbol'] for s in core['statements']])
    body = format_graph(doc, 'compact') + '\n'
    assert body == (ROOT / PARENT).read_text(encoding='utf-8')
    annotations = json.loads((ROOT / 'data/incidental-agreement-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


def main():
    for name, body in build().items():
        p = ROOT / name
        if p.exists():
            assert p.read_text(encoding='utf-8') == body, name
        else:
            with p.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Content conventions fixed; manuscript syntax unchanged', flush=True)


if __name__ == '__main__':
    main()
