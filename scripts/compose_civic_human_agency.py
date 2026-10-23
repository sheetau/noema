"""Bind the human relative clause to existing deliberative capacity, not revolt."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/self-directed-choice-basis-v1.json';MAIN='data/civic-spirit-sentence-basis-v1.json'
LIBRARY='examples/v016/civic-human-agency.noema';BASIS='data/civic-human-agency-basis-v1.json'
MEANINGS={
 'r6lc':'同じ民衆の人であり、固定した全市民的行為が非空で完全に列挙され、全てについて既有能力を評価でき、その少なくとも一つで本人の理由に基づいて行う・意図的に控えるr6kmの両方向の能力がある。全行為への万能性、現在の実行、職務上の服従の全面否定を要求しない。',
 'r6ld':'同じ民衆の全人間成員を非空で完全に列挙し、指定された同じ時点に、その全員にr6lcを要求する。総称的人間をこの共同体の全対象へ分配する明示的な読み。集団得点の増加だけから各人の能力を自動的に推論しない。',
 'r6le':'同じ共同体・固定基準を保持し、本人と評価点ごとのr6lcを返す内容族。後続の人間の指示・扱いの対象を同じ本人へ接続するための入口。',
 'r6lf':'同じ共同体・固定基準で、評価点ごとのr6ldを返す内容。「今や」は後続統合で同じ政治的終点へ束縛する。以前の能力欠如や、尊厳を能力獲得の報酬とする条件は含まない。',
}
LIMITS=[
 'u0017のden Menschen, der nun mehr als Maschine istを、同じ民衆の人間が、外から与えられた働きをする側面だけに尽くされず、本人の理由に基づいて行う又は控える実践的な能力を持つという読みで具体化する。数量比較、物理的な機械分類、あらゆる機械には理性がないという普遍命題は追加しない。',
 '能力の本体は既存r6kmであり、新しい「機械以上」判定の原始語は置かない。同じ人・行為の自分の判断による実行と意図的な控え、自由な比較条件、既有基盤、全通常場面を保持する。現在の許可・実行・完全な道徳性とは分ける。',
 '同じ論説AA VIII 37の機構の一員としての職務と、学識者として理性を使う立場の両立を比較する。ある職務の受動的遂行r2zuと能力r6lcが同時に成立し得る。政府のあらゆる指示への不服従を条件にしない。',
 '旧reasoned-variationの「同一指示・異なる理由・異なる応答」の特定の一対を必須にはしない。理由の変化だけによる介入効果や、全機械の応答モデルの否定を原文へ追加しない。旧定義と検査は保存する。',
 '総称的人間は、この同じ民衆についての全人間成員への分配として読む。都合のよい成功者だけに絞らず、各人に少なくとも一つの関連行為で能力を要求する。全人の全行為への能力や、地球上の全人口のその時点の状態へ拡張しない。',
 'この関係節は扱いの対象を能力のある者だけに限定する条件文へ変更しない。後続の尊厳規則は同じ全人間成員を対象とし、r6lcの成功者だけを対象とする選別に使わない。能力のない人の尊厳の否定も導かない。',
 '同じ政治的終点で成立する付随的な人間描写として後続統合に渡す。以前は機械そのものだった、以前は理性も尊厳もなかった、政府がそう思うだけで成立するとはしない。集団的な能力得点の増加r6krとは独立に確認する追加内容である。',
 '尊厳に応じた扱いの具体的内容・政府自身の利益判断・原則への作用と終点・条件文全体と著者帰属は未完。今回も正本122主張と全文意味確認文字数を変更しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def main_catalog():return load_catalog(ROOT,MAIN)

def definitions():
    c='v community v reference';person='k r6hd[v person v community v reference]'
    selected='k h26yo[v community v person v activity v reference]';args=c+' v person v activity v point'
    text='d r6lc[community a reference d person a point d] c['+both(person,
      'k rcm[k h27c2['+c+' v person] i[activity a]['+selected+']]',
      'f activity a[y['+selected+'][k r6kl['+args+']]]',
      'g activity a['+both(selected,'k r6km['+args+']')+']')+'].\n'
    text+='d r6ld[community a reference d point d] c['+both('k rcm[k h27b5['+c+'] i[person a]['+person+']]',
      'f person a[y['+person+'][k r6lc['+c+' v person v point]]]')+'].\n'
    text+='d r6le[community a reference d] h[a] e[i[person a][b point[k r6lc['+c+' v person v point]]]].\n'
    text+='d r6lf[community a reference d] e[b point[k r6ld['+c+' v point]]].\n'
    return text

def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('r6kl','r6km','rcm','h27c2','h27b5')),statements=[])
    imports={d['name']:p.entries[d['name']] for d in doc['declarations']}
    # Keep the existing passive-role content available for the explicit
    # compatibility check; it is not negated by the new human clause.
    m=main_catalog()
    for d in closure(m.document,('r2zu',)):
        n=d['name'];e=m.entries[n]
        if n in imports:assert d==imports[n]['declaration'] and e['meaning_ja']==imports[n]['meaning_ja']
        else:doc['declarations'].append(d);imports[n]=e
    assert not set(MEANINGS)&set().union(p.entries,m.entries)
    doc=parse(format_graph(doc,'compact')+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imports.items() if e['kind']=='primitive'}
    paths=set(p.source_sha256)|set(m.source_sha256)
    basis=dict(status='same_population_deliberative_human_relative_clause_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imports.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imports.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
