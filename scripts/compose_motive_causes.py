"""Use defeasible motive dispositions and actual contribution to both results."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-footnote-reading.noema'
PARENT_BASIS = 'data/footnote-reading-basis-v1.json'
FULL = 'examples/v016/kant-motive-causes.noema'
CORE = 'examples/v016/motive-causes-core.noema'
LIBRARY = 'examples/v016/causal-factor-results.noema'
BASIS = 'data/motive-causes-basis-v1.json'
ANNOTATIONS = 'data/motive-causes-identifiers-v1.json'
NORMAL = '同じ本人・要因記述・基準文脈について、第一の評価機会を第二より通常とみなす厳密な比較。本人の好みや数値確率ではない。労力による回避と恐れによる回避を同じ比較へ自動的にまとめない。候補は既存mhで定め、回避した事例だけを通常として結果を逆算しない。比較の非反射性・推移性と極小候補の条件はrqt4で検査する。'
MEANINGS = {
    'rqxa': '非空の要因記述列と結果記述列の全組合せで、同じ原因対象と結果対象・状況にrqquを要求する。要因と結果が成立し、実際の因果的寄与がある。説明への採用だけでは足りず、各要因の単独十分性・必要性・唯一原因性は要求しない。二対象は異なっていてもよい。',
    'mj': '同じ本人・基準文脈の非空な評価範囲mhで、労力の要因記述mbに対する通常性hzwmを用い、通常候補の全てにmfの回避理由と行為を要求する。劣後する例外での不成立を許す。労力を理由に避ける傾向の構成であり、Faulheitの規範的評価や全語義を尽くすとはしない。',
    'mk': '同じ本人・基準文脈の非空な評価範囲mhで、恐れの要因記述mcに対する通常性hzwmを用い、通常候補の全てにmgの回避理由と行為を要求する。劣後する例外での不成立を許す。客観的な危険や全場面での回避を含意せず、Feigheitの規範的評価や全語義を尽くすとはしない。',
    'ol': '同じ集団について、二要因mq・mrが第一の結果msと第二の結果okのそれぞれへ実際に因果的に寄与し、その要因と結果も成立する。rqxaの二要因・二結果への固定した特殊化。内容を直接呼び出すことで実行時の脱引用を避け、著者への帰属で引用できる形を保つ。四つの寄与をそれぞれ述べる読みで、単独十分性や二要因が同一人物に共存することは追加しない。',
    'mx': '同じ集団mvについて二要因と二結果の実際の因果条件olが成立する内容。本文ではこの内容を著者へ帰属させ、著者の主張の真実性を帰属そのものから導かない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def generic():
    return '''
d rqxa[source a factors j[i[h[a] e]] target a results j[i[h[a] e]] scene d] c[
 w[u[e[d[v factors]][n p a b]]][w[u[e[d[v results]][n p a b]]][
  q[v factors][e[n p a b][n p a b]][i[valid c factor i[h[a] e]][w[v valid][
   q[v results][e[n p a b][n p a b]][i[good c result i[h[a] e]][
    w[v good][k rqqu[v source v factor v target v result v scene]]
   ]]
  ]]]
 ]]
].
'''


def replacements():
    text = ''
    for name, factor, response in [('mj', 'mb', 'mf'), ('mk', 'mc', 'mg')]:
        text += 'd ' + name + '[person a] e[b anchor[k rqt4[' + \
            'i[scene d][k mh[v person v anchor v scene]] ' + \
            'i[first d second d][k hzwm[v person r[p ' + factor + '] v anchor v first v second]] ' + \
            'i[scene d][k ' + response + '[v person v scene]]]]].'
    clauses = ['t[k ' + n + '[v group]][v scene]' for n in ('mq', 'mr', 'ms', 'ok')]
    clauses += ['k hzie[v group r[p ' + f + '] v group r[p ' + e + '] v scene]'
        for f in ('mq', 'mr') for e in ('ms', 'ok')]
    body = clauses[-1]
    for clause in reversed(clauses[:-1]):
        body = 'w[' + clause + '][' + body + ']'
    text += 'd ol[group a scene d] c[' + body + '].'
    return text


def build():
    old = parent()
    assert not {'rqxa', 'hzwm'} & set(old.entries)
    doc = deepcopy(old.document)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'mj')
    prefix = deepcopy(doc)
    prefix.update(declarations=doc['declarations'][:at], statements=[])
    addition = parse(format_graph(prefix, 'compact') + 'r hzwm[a i[h[a a d] c] d d d] c.' + generic())
    doc['declarations'] = addition['declarations'] + doc['declarations'][at:]
    # Parse replacement bodies in the full existing environment under temporary
    # names, then install them at their original positions.
    text = replacements().replace('d mj[', 'd znewmj[').replace('d mk[', 'd znewmk[').replace('d ol[', 'd znewol[')
    base = deepcopy(doc);base['statements'] = []
    parsed = parse(format_graph(base, 'compact') + text)
    changes = {}
    for d in parsed['declarations'][-3:]:
        d = deepcopy(d);d['name'] = d['name'][4:];changes[d['name']] = d
    doc['declarations'] = [changes.get(d['name'], d) for d in doc['declarations']]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='normal_motive_dispositions_and_actual_causal_results', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['通常性は文脈的な比較条件であり、人格・心理機構の実証や性格診断を行わない。程度・規範的な非難と語義全体の確認は残る。',
            '二要因それぞれが二結果それぞれへ寄与する読みを保持する。二要因の連言だけを一体の原因とする別の読みと同一視しない。',
            '集団の割合・自然による解放・好みと生涯・後見への容易さの既存の部分解釈は引き続き全体の読解対象。今回の変更だけで第一文や第二段落を確認済みにしない。',
            '既存の説明採用ea・na・muと全機会条件ncは別用途と履歴のため保持する。現行olとmj・mkはそれらで実際の因果や例外を許す傾向を代用しない。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            args, meaning = (['person', 'factor_description', 'anchor', 'first', 'second'], NORMAL) if n == 'hzwm' else \
                (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'], arguments=args, meaning_ja=meaning)
        else:
            basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc);core['statements'] = [doc['statements'][2]]
    core['declarations'] = closure(doc, ['uc', 'mw', 'wa', 'mx', 'wh', 'ue', 'wg'])
    library = deepcopy(doc);library['declarations'] = closure(doc, ['rqxa']);library['statements'] = []
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/footnote-reading-identifiers-v1.json').read_text(encoding='utf-8'))
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
    print('Motive dispositions and causal results connected', flush=True)


if __name__ == '__main__':
    main()
