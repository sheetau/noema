"""Bind intended judgment and actual contribution to the same performed act."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-guardian-causation.noema'
PARENT_BASIS = 'data/guardian-causation-basis-v1.json'
FULL = 'examples/v016/kant-guardian-purpose.noema'
CORE = 'examples/v016/guardian-purpose-core.noema'
LIBRARY = 'examples/v016/purposeful-performance.noema'
BASIS = 'data/guardian-purpose-basis-v1.json'
ANNOTATIONS = 'data/guardian-purpose-identifiers-v1.json'
MEANINGS = {
    'rqye': '指定した行為が評価状況で実際に生じるという内容。既存dgの内容化であり、参加者・目的・結果はここへ含めない。',
    'rqyf': '指定した非空の行為者群の全員が、同じ実際に生じる行為へ参加し、その行為において同じ閉じた内容記述を目的として目指す。目的は実行評価せず、達成・実現可能性・各人の単独での十分性を要求しない。',
    'rqyg': '同じ非空で重複のない後見人群の各人が、同じ生起する行為に参加し、同じ母集団mvの危険判断分布rqydをその行為の目的として目指す。既存hzuを使い、実際の危険や負担を目的へ混ぜない。各人の目的を要求する読みを明示し、集合的な目的の全理論とはしない。',
    'rqyh': '前版doを保存する。後見人群の立場と共同活動、人々の負担と危険判断が成立し、共同活動という集団の性質が危険判断分布へ寄与する。特定の行為への目的と因果の結合は要求しない。',
    'do': '後見人群の立場dk、同じ母集団mvの負担と判断dn、危険判断分布rqydが成立する。同じ群の各人がrqydを目指して参加する一つの生起行為rqygがあり、その同じ行為の生起rqyeが同じ母集団のrqydへ実際に寄与する。目的のない影響や、別行為の目的と因果を混ぜない。因果の唯一性・単独十分性・目標達成の保証を付け加えない。',
}


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not {'rqye', 'rqyf', 'rqyg', 'rqyh'} & set(old.entries)
    # Existing primitive, unchanged; move before its new caller, not duplicate.
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] != 'hzu']
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'do')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at], statements=[])
    prefix['declarations'].append(deepcopy(old.entries['hzu']['declaration']))
    saved = deepcopy(old.entries['do']['declaration']); saved['name'] = 'rqyh'
    prefix['declarations'].append(saved)
    text = '''
d rqye[act a] e[b scene[k dg[v act v scene]]].
d rqyf[agents h[a] c act a goal i[e] scene d occurs h[a d] c performs h[a a d] c aims h[a a i[e] d] c] c[
 w[c[v occurs][v act v scene]][w[g actor a[c[v agents][v actor]]][
 f actor a[y[c[v agents][v actor]][w[c[v performs][v actor v act v scene]][c[v aims][v actor v act v goal v scene]]]]
 ]]
].
d rqyg[group a act a scene d] c[w[k hi[k mp[v group] p aa]][
 k rqyf[i[actor a][k hg[k mp[v group] v actor]] v act r[k rqyd[k mv[]]] v scene p dg p df p hzu]
]].
d do[group a] e[b scene[w[t[k dk[v group]][v scene]][w[t[k dn[k mv[]]][v scene]][
 w[t[k rqyd[k mv[]]][v scene]][g act a[w[k rqyg[v group v act v scene]][
 k hzie[v act r[p rqye] k mv[] r[p rqyd] v scene]
 ]]]]]]].
'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at+1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='purpose_and_contribution_bound_to_same_act', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS,
        primitives={}, definitions={}, predecessor_source_sha256=old.source_sha256,
        limitations=['目的hzuと寄与hzieを再利用する。新しい基本関係は追加しない。',
            '各後見人が同じ行為で同じ目的を目指す読みを採る。全ての集合的意図の意味を尽くさず、本文全体の確定訳とはしない。',
            '成功を伴う結果の読みを継続する。sorgenという動詞だけから成功を導かず、未達の目的的活動もrqyf・rqygで別に表せる。',
            '監督・評価・焦点の語義と当該文全体の照合は未完。現実の意図や因果を発見する機構ではない。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'],
                arguments=old.entries[n]['arguments'], meaning_ja=old.entries[n]['meaning_ja'])
        else: basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc); core['statements'] = [doc['statements'][7]]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqyf']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/guardian-causation-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items(): write_exact(ROOT / p, s)
    print('Same-act purpose and causal contribution composed', flush=True)


if __name__ == '__main__': main()
