"""Separate a motive disposition from its contextual attribution as a fault."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-motive-causes.noema'
PARENT_BASIS = 'data/motive-causes-basis-v1.json'
FULL = 'examples/v016/kant-evaluated-motives.noema'
CORE = 'examples/v016/evaluated-motives-core.noema'
LIBRARY = 'examples/v016/evaluated-state.noema'
BASIS = 'data/evaluated-motives-basis-v1.json'
ANNOTATIONS = 'data/evaluated-motives-identifiers-v1.json'
MEANINGS = {
    'rqxb': '同じ本人・基準文脈・労力の要因記述mbについて、mhとhzwmで定めた通常候補の全てにmfを要求する回避傾向。旧mjの評価を含まない内容を保持する。例外を許し、この条件だけから休息や省力を落ち度としない。',
    'rqxc': '同じ本人・基準文脈・恐れの要因記述mcについて、mhとhzwmで定めた通常候補の全てにmgを要求する回避傾向。旧mkの評価を含まない内容を保持する。この条件だけから慎重な危険回避を落ち度としない。',
    'rqxd': '同じ本人・性質記述・評価状況について、その内容が成立し、かつhziqにより本人の選択や不作為に関する落ち度として帰せられる。内容の成立と帰責を独立に要求する。評価基準は指定状況の解釈に属し、因果・不履行・評価の不明から帰責を導かない。記述の実行を伴う一般形。',
    'mj': '同じ本人と状況に労力を理由とする回避傾向rqxbがあり、その同じ傾向がhziqにより本人の落ち度として評価される。rqxdの固定した特殊化。原文のFaulheitを批判的に述べる文脈的な読みであり、休息や努力回避の全て、語の全用法を定義しない。',
    'mk': '同じ本人と状況に恐れを理由とする回避傾向rqxcがあり、その同じ傾向がhziqにより本人の落ち度として評価される。rqxdの固定した特殊化。原文のFeigheitを批判的に述べる文脈的な読みであり、恐怖や慎重な回避だけで真にせず、語の全用法を定義しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent()
    assert not {'rqxb', 'rqxc', 'rqxd'} & set(old.entries)
    doc = deepcopy(old.document)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'mj')
    prefix = deepcopy(doc);prefix.update(declarations=doc['declarations'][:at], statements=[])
    for before, after in [('mj', 'rqxb'), ('mk', 'rqxc')]:
        row = deepcopy(old.entries[before]['declaration']);row['name'] = after
        prefix['declarations'].append(row)
    generic = 'd rqxd[person a state i[h[a] e] scene d] c[w[t[c[s[v state]][v person]][v scene]][k hziq[v person v state v scene]]].'
    parsed = parse(format_graph(prefix, 'compact') + generic)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at:]
    base = deepcopy(doc);base['statements'] = []
    replacements = ''.join('d znew' + name + '[person a] e[b scene[w[t[k ' + raw +
        '[v person]][v scene]][k hziq[v person r[p ' + raw + '] v scene]]]].'
        for name, raw in [('mj', 'rqxb'), ('mk', 'rqxc')])
    changes = {}
    for row in parse(format_graph(base, 'compact') + replacements)['declarations'][-2:]:
        row = deepcopy(row);row['name'] = row['name'][4:];changes[row['name']] = row
    doc['declarations'] = [changes.get(d['name'], d) for d in doc['declarations']]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='contextually_evaluated_motive_dispositions', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS,
        primitives={}, definitions={}, predecessor_source_sha256=old.source_sha256,
        limitations=[
            '批判的な原文の読みとして傾向への帰責を加える。Faulheit・Feigheitの一般語彙全体や唯一の歴史的読解を確定しない。',
            'hziqの評価基準は状況の意味に含める。本文では因果内容全体をucで著者へ帰属するので、アシスタント自身の非難や普遍的な道徳的真理を主張しない。',
            '正当な帰責の全理論・数値閾値・個人の診断は追加しない。評価が未知なら肯定にも否定にも補完しない。',
            '通常性・行為範囲の文脈的選択、自然による解放・生涯・容易さ、第二段落全体の意味確認は残る。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'],
                arguments=old.entries[n]['arguments'], meaning_ja=old.entries[n]['meaning_ja'])
        else:
            basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc);core['statements'] = [doc['statements'][2]]
    core['declarations'] = closure(doc, ['uc', 'mw', 'wa', 'mx', 'wh', 'ue', 'wg'])
    library = deepcopy(doc);library.update(declarations=closure(doc, ['rqxd']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/motive-causes-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(library, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    for name, body in build().items():
        p = ROOT / name
        if p.exists():
            assert p.read_text(encoding='utf-8') == body, name
        else:
            with p.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Evaluated motives composed without new primitives', flush=True)


if __name__ == '__main__':
    main()
