"""Separate clinical judgment roles from general health expertise."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-effort-agents.noema'
PARENT_BASIS = 'data/effort-agents-basis-v1.json'
FULL = 'examples/v016/kant-clinical-roles.noema'
CORE = 'examples/v016/clinical-roles-core.noema'
LIBRARY = 'examples/v016/qualified-principal-roles.noema'
BASIS = 'data/clinical-roles-basis-v1.json'
ANNOTATIONS = 'data/clinical-roles-identifiers-v1.json'
CLINICAL = 'その事柄は、同じ本人の身体の病気・損傷・機能の不調を見分け、その防止・軽減・回復のための対応を判断することに関する。一般的な体力増進や好みへの助言だけとは区別する。病気が現にあること、診断の正しさ、措置の実行や成功は、この話題の関係からは導かない。'
MEANINGS = {
    'rqxs': '同じ主体・役割・状況に、役割の保持、指定活動への援助機能、その同じ機能の主要性、指定された性質の資格要求を結ぶ。異なる役割から四条件を寄せ集めず、資格の記述を実行して本人の能力を推定しない。',
    'rqxt': '旧srの健康上の専門的な助言役を保存する。rqxjの継続的な援助実践と、sqの機能・rqxiの資格要求を持つ同じ社会的役割を要求する。身体の病気・損傷への対応を主要な機能とする条件は含まない。',
    'hzw3': '本人が同じ判断で同じ事柄を評価し、その事柄が本人の身体的健康shと、病気・損傷・不調への対応hzw2に関わる内容。受け手が自分で行う判断の仕事を記述する。援助の対象として引用するだけでは、その本人の実行や現に病気であることを要求しない。',
    'hzw4': '本人が、他者についてhzw3の判断を援助する専門的な知識・技能hzwqを備えるという内容。役割の資格要求として引用する場合と、本人の実際の技能として評価する場合を区別する。',
    'sr': 'rqxjの継続的な健康上の援助者であり、同じ社会的役割に、身体の病気・損傷・不調への対応hzw3の判断を援助する機能、その主要性、専門性hzw4の資格要求を結ぶ。医師のこの用例に向けた治療上の判断役としての説明。実際の技能、治療の成功、現代の免許や法的な職種境界を追加しない。処置を行う実践と制度上の役割境界の説明は残る。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not {'rqxs', 'rqxt', 'hzw2', 'hzw3', 'hzw4'} & set(old.entries)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'sr')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at], statements=[])
    saved = deepcopy(old.entries['sr']['declaration']); saved['name'] = 'rqxt'
    prefix['declarations'].append(saved)
    text = '''r hzw2[a a d] c.
d rqxs[person a task i[h[a] e] qualification i[h[a] e] scene d holds h[a a d] c serves h[a i[h[a] e] d] c principal h[a i[h[a] e] d] c requires h[a i[h[a] e] d] c] c[
 g role a[w[c[v holds][v person v role v scene]][w[c[v serves][v role v task v scene]][w[c[v principal][v role v task v scene]][c[v requires][v role v qualification v scene]]]]]
].
d hzw3[person a] e[b scene[g judgment a[w[k fa[v person v judgment v scene]][g topic a[w[k fb[v judgment v topic v scene]][w[k sh[v topic v person v scene]][k hzw2[v topic v person v scene]]]]]]]].
d hzw4[person a] e[b scene[k hzwq[v person r[p hzw3] v scene]]].
d sr[person a scene d] c[w[k rqxj[v person v scene]][k rqxs[v person r[p hzw3] r[p hzw4] v scene p hzwn p hzwo p hzwu p hzwp]]].'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at + 1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='clinical_judgment_role_distinguished_from_general_health_expertise', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['歴史辞典の治療に関する知識と実践を参照し、まず判断を援助する役割の対象・主要性・専門性を結ぶ。医師の全ての仕事を判断だけへ還元しない。',
            '役割の要件と本人の能力は分離する。現代の免許、看護等との法的な排他性、全ての地域・時代・比喩的用法へ一般化しない。',
            '前版の目的・努力の文脈指定は原版の選択に固定された記録であり、今回の語義変更に対する全文同義の確認へ自動昇格しない。',
            '条件文、第二段落、二作品全文の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            labels, meaning = (['topic', 'person', 'scene'], CLINICAL) if n == 'hzw2' else (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'], arguments=labels, meaning_ja=meaning)
        else:
            basis['definitions'][n] = MEANINGS.get(n, old.entries[n]['meaning_ja'] if n in old.entries else '')
            assert basis['definitions'][n]
    core = deepcopy(doc); core['statements'] = [doc['statements'][i] for i in (4, 42)]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqxs']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/effort-agents-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items():
        write_exact(ROOT / p, s)
    print('Clinical judgment roles composed', flush=True)


if __name__ == '__main__':
    main()
