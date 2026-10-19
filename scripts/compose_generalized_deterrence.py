"""Separate generic intimidation from robust frequency of avoidance."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_courageous_undertaking import replace_symbols
from scripts.compose_frequency_variation import definition as frequency_definition, MEANING as FREQUENCY_MEANING

PARENT='examples/v016/kant-recognized-example.noema'
PARENT_BASIS='data/recognized-example-basis-v1.json'
FULL='examples/v016/kant-generalized-deterrence.noema'
CORE='examples/v016/generalized-deterrence-core.noema'
LIBRARY='examples/v016/preferred-case-responses.noema'
BASIS='data/generalized-deterrence-basis-v1.json'
ANNOTATIONS='data/generalized-deterrence-identifiers-v1.json'
CASE_MAP={'rqt2':'r2be','rqt3':'r2bf','rqt4':'r2bg'}
MAPPING={'hzud':'r2bk','hzue':'r2bl','hzuf':'r2bm','hzug':'r2bn','hzuh':'r2bo'}
PRIMITIVES={
 'hzyl':(['anchor','candidate'],'同じ基準で、先行する不成功例を知った対象者の反応を一般化して述べる比較状況。例との遭遇・認識の環境や対象者間の差を検討する範囲であり、実際に起きた履歴だけに限定しない。活動の意味と指示する対象集団は基準に固定し、異なる課題や学習済みの別の集団へ交換しない。反応の成功だけで選定しない。'),
 'hzym':(['anchor','preferred','other'],'同じ基準の比較状況について、背景条件の通常性を比べる厳密な優先関係。認識の環境や外的な阻害などの比較理由を与えるもので、萎縮・回避の成立や観測回数そのものを順位とはしない。反射・循環・推移性違反は構成側で検査する。'),
 'hzyn':(['anchor','candidate','preferred_case','other_case'],'同じ基準・比較状況内の事例について、一般的反応を述べるための通常性を比べる厳密な優先関係。特異な受容条件や例の認識環境などを比較理由とする。萎縮した事例だけを優先することは正当化しない。この順位は頻度計算の事例を削除する条件ではない。'),
}
MEANINGS={
 'r2bd':FREQUENCY_MEANING,
 'r2be':'指定した個体事例の範囲に属し、その範囲の他事例に通常性で劣後しない事例を選ぶ。状況型のrqt2と同じ順序条件を、個体型の事例へ適用する。',
 'r2bf':'指定した個体事例の範囲で通常性順序の非反射性・推移性と、各事例が極小または極小事例に劣後する条件を要求する。比較不能な事例を黙って除かない。',
 'r2bg':'r2bfの条件を満たす同じ範囲に極小事例が少なくとも一つあり、その全てで応答が成立する。劣後する事例の例外を許す。数値割合や全事例での成立とは異なる。',
 'r2bh':'比較状況での事例の適格性、対象者が人であること、基準状況の同じ対象集団djへの所属、比較状況での同じ先行例grの認識を結ぶ。対象集団を比較先で選び直さない。',
 'r2bi':'同じ基準・比較状況の範囲について、通常比較状況ごとにr2bhの事例全体でhzucの因果的回避が過半数かつ基準の割合条件を満たす。萎縮の通常事例だけへ分母を縮めず、回避しない例外も残す。',
 'r2bj':'同じ基準に固定した通常比較状況ごとに、r2bhの範囲の通常事例すべてでhzubの因果的萎縮が成立する。現況の全事例が萎縮するという旧条件とは異なり、比較不能な通常事例での失敗は拒否する。',
 'r2bk':'同じ基準における一般的な因果的萎縮r2bjと、通常比較状況での因果的回避の頻度r2biを合わせる。無修飾の一般的反応と明示的な頻度の範囲を分ける。現況の反応だけから補わない。',
 'r2bl':'更新したr2bkを著者へ帰属し、学習の見込みに後続する本文順を保持する。引用した反応の真理は実行しない。',
 'r2bm':'危険の程度e4と更新したr2bkを、既存の同じ質的な期待比較へ渡す。PかつQとPかつ非Qを比較し、頻度の数値を期待比較と同一視しない。',
 'r2bn':'更新後の一般化された反応r2bkと期待背景r2bmを、同じ本文箇所の主張と背景の組にする。',
 'r2bo':'危険の程度・学習の理由・本文順を保持し、一般化した萎縮と回避の主張と期待背景を同じ著者・範囲・文脈へ帰属する。',
}
LIMITS=[
 '無修飾のmacht ... schüchternを通常事例についての一般的な因果反応、gemeiniglichを通常比較状況での事例頻度として読む。唯一の語義や原著者の心理理論の証明とはしない。',
 '対象集団の所属は基準dj、認識された例と反応は比較状況に置く。基準の現況で誰かが実際に萎縮・回避したことを一般化の必須条件にしない。',
 '比較範囲と二つの通常性順序は明示的な解釈入力である。観測から自動推定せず、結果から都合よく順位を作らない。何を通常とするかの経験的根拠はこの形式だけでは証明しない。',
 '萎縮の極小事例と、回避頻度を計る事例全体は異なる。後者は既存の非空・重複なし・適格性・網羅性を保持し、有限・等重みという制約が残る。',
 '架空の例、萎縮の語義全体、学習の見込みの作用範囲、末尾一文と段落全体の通し判断は残る。今回だけで原文の新しい意味確認済み分量を増やさない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT,PARENT_BASIS)


def case_definitions():
    def retag(v):
        if v=='situation': return 'individual'
        if isinstance(v,dict): return {k:retag(x) for k,x in v.items()}
        if isinstance(v,list): return [retag(x) for x in v]
        return v
    result=[]
    for name,target in CASE_MAP.items():
        row=retag(replace_symbols(deepcopy(parent().entries[name]['declaration']),CASE_MAP))
        row['name']=target;result.append(row)
    return result


def additions():
    return '''
r hzyl[d d] c.r hzym[d d d] c.r hzyn[d d a a] c.
d r2bh[item a anchor d scene d] c[w[k gj[v item v scene]][w[k aa[k gd[v item]]][w[
 k dj[k gd[v item] v anchor]
][t[k gr[v item]][v scene]]]]].
d r2bi[] e[b anchor[k r2bd[v anchor p hzyl p hzym p gk
 i[item a scene d][k r2bh[v item v anchor v scene]]
 i[item a scene d][t[k hzuc[v item]][v scene]] p gl p hr]]].
d r2bj[] e[b anchor[k rqt4[i[scene d][k hzyl[v anchor v scene]]
 i[first d second d][k hzym[v anchor v first v second]]
 i[scene d][k r2bg[i[item a][k r2bh[v item v anchor v scene]]
 i[first a second a][k hzyn[v anchor v scene v first v second]]
 i[item a][t[k hzub[v item]][v scene]]]]]]].
d r2bk[] e[b anchor[w[t[k r2bj[]][v anchor]][t[k r2bi[]][v anchor]]]].
'''


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+frequency_definition())
    doc['declarations'].extend(case_definitions())
    doc=parse(format_graph(doc,'compact')+additions())
    for name in ('hzue','hzuf','hzug','hzuh'):
        row=replace_symbols(deepcopy(old.entries[name]['declaration']),MAPPING)
        row['name']=MAPPING[name];doc['declarations'].append(row)
    doc['statements']=deepcopy(statements)
    doc['statements'][37]=replace_symbols(doc['statements'][37],MAPPING)
    doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core.update(declarations=closure(doc,['r2bo']),statements=[doc['statements'][37]])
    library=deepcopy(doc);library.update(declarations=closure(doc,['r2bg','r2bd']),statements=[])
    added=doc['declarations'][size:];by_name={d['name']:d for d in added}
    assert len(added)==15
    basis=dict(status='generic_intimidation_and_frequency_adopted',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=args,meaning_ja=meaning)
            for n,(args,meaning) in PRIMITIVES.items()},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/recognized-example-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p,body in build().items(): write_exact(ROOT/p,body)
    print('Generic intimidation and frequency adopted at statement 37; 52 statements retained',flush=True)


if __name__=='__main__': main()
