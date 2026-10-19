"""Separate a group's caused judgment from explanatory adoption and burden."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-payment-reading.noema'
PARENT_BASIS = 'data/payment-reading-basis-v1.json'
FULL = 'examples/v016/kant-guardian-causation.noema'
CORE = 'examples/v016/guardian-causation-core.noema'
LIBRARY = 'examples/v016/selected-majority.noema'
BASIS = 'data/guardian-causation-basis-v1.json'
ANNOTATIONS = 'data/guardian-causation-identifiers-v1.json'
MEANINGS = {
    'rqyb': '旧doの、後見人群の立場・活動と人々の負担・危険判断が成立し、その活動を結果の原因説明へ採用する内容を保存する。実際の因果的寄与は要求しない。',
    'rqyc': '認識された重複のない人間の母集団について、指定した性質を満たす割合が厳密な過半数であり、既存u4の「はるかに最大の部分」という文脈基準も満たす内容。u5の選択性質を引数化し、負担と判断の連言にも判断だけにも適用できる。基準を固定数値へ置き換えない。',
    'rqyd': '同じ母集団について危険だという判断uxの割合がrqycを満たし、文脈で女性とされる非空の範囲が全てその母集団に含まれて同じ判断を持つ内容。実際の危険性、成熟への一歩の負担、その人々の美しさはここでは要求しない。',
    'do': '後見人群の現在の立場dk、同じ群の共同活動dl、同じ母集団mvについての既存dnの負担と判断が成立する。その活動が同じ母集団の危険判断の分布rqydへ実際に因果的に寄与し、その結果も成立する。説明への採用eaで実際の寄与を代用せず、負担そのものを因果結果の記述へ含めない。唯一原因性、単独十分性、介入機構、意図の条件は追加しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not {'rqyb', 'rqyc', 'rqyd'} & set(old.entries)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'do')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at], statements=[])
    saved = deepcopy(old.entries['do']['declaration']); saved['name'] = 'rqyb'; prefix['declarations'].append(saved)
    text = '''
d rqyc[population j[a] selected h[a] e] e[b scene[
 w[k hr[v population v scene]][w[
 k pd[v population p aa i[person a][t[c[v selected][v person]][v scene]] i[ratio b][k u4[v ratio v scene]]]
 ][k hc[n p b c k pb[v population i[person a][t[c[v selected][v person]][v scene]]]]]]
]].
d rqyd[group a] e[b scene[w[t[k rqyc[k mp[v group] p ux]][v scene]][
 k ro[i[person a][k hg[k mp[v group] v person]] i[person a][k da[v person v scene]]
 i[person a][t[k ux[v person]][v scene]]]
]]].
d do[group a] e[b scene[w[t[k dk[v group]][v scene]][w[t[k dl[v group]][v scene]][
 w[t[k dn[k mv[]]][v scene]][w[t[k rqyd[k mv[]]][v scene]][
 k hzie[v group r[p dl] k mv[] r[p rqyd] v scene]
 ]]]]]].'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at+1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='actual_causal_contribution_to_judgment_distribution', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS,
        primitives={}, definitions={}, predecessor_source_sha256=old.source_sha256,
        limitations=['既存の因果的寄与hzieを再利用する。現実の因果を発見・証明する処理ではない。',
            '後見人の活動から危険判断が生じるという読みの一部を具体化する。sorgenの目的的な働きかけ、評価と焦点、一文全体の意味確認は未完。',
            '既存dnの負担の挿入的な読みと、集団の範囲・程度の基準を保持する。その語義の全体確認とはしない。',
            '旧doをrqybとして保持し、説明への採用を述べる表現能力も残す。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'],
                arguments=old.entries[n]['arguments'], meaning_ja=old.entries[n]['meaning_ja'])
        else: basis['definitions'][n] = MEANINGS.get(n, old.entries[n]['meaning_ja'] if n in old.entries else None)
    core = deepcopy(doc); core['statements'] = [doc['statements'][7]]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqyc', 'rqqu', 'ec']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/payment-reading-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items(): write_exact(ROOT / p, s)
    print('Actual contribution to judgment distribution composed', flush=True)


if __name__ == '__main__': main()
