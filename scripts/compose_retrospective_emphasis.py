"""A prior authorial choice and current principal emphasis on a quoted concept."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/self-departure-sentence-basis-v1.json'
LIBRARY='examples/v016/retrospective-emphasis.noema';BASIS='data/retrospective-emphasis-basis-v1.json'
CONCEPT='i[h[a] e]'
FRAME='author a work a concept '+CONCEPT+' topic a reference d point d'
PRIMITIVES={
 'h26sb':('[a a '+CONCEPT+' a d d] c',['activity','work','concept','topic','reference','point'],
   '同じ活動は、この論述作品で、閉じた性質記述が表す同じ概念をどの主題について論じるか、その主題への重点の置き方を設定し提示する活動である。対象概念・作品・主題・固定基準と設定点を保持する。単なる私的な関心、別作品の言及、語の出現数、引用された概念の実例の達成ではない。活動の生起・主体の参加・主題が実際に最優先かは合成側で別に要求する。'),
 'h26sc':('[a a '+CONCEPT+' a a d d] c',['author','work','concept','left','right','reference','point'],
   '同じ著者・論述作品・閉じた概念・固定基準・点で、左主題を論じることへの重点は右主題への重点以下である。論述上の重要さの相対比較であり、文字数・登場順・唯一の主題・概念の真理・現実の達成の比較ではない。同順位を許し、比較可能性と推移性は合成側で確認する。'),
 'h26sd':('[a a '+CONCEPT+' a d] c',['author','work','concept','topic','reference'],
   '同じ著者・作品・閉じた概念・固定基準について、どこに論述の重点を置くかを比較する全関連主題に属する。最も強調された主題や実際に解決した事項だけを選ばず、設定の前後でも同じ範囲を使う。主題の網羅性は明示した解釈入力であり、この関係だけで最上位性や論述への実際の採用を肯定しない。'),
}
MEANINGS={
 'r6bq':'同じ著者・作品・概念・基準の全関連主題h26sdを対象に、同じ点の重点比較h26scの向きを反転してrceの最小を取り、指定主題が最大の重点を持つことを構成する。範囲所属・非空性・反射性・推移性・全比較可能性を要求し、同順位を許す。',
 'r6br':'一つの同じ活動が生起し、著者が参加し、それが同じ作品・概念・主題の重点を設定・提示するh26sbであり、その点で指定主題がr6bqの最大重点にある。単なる希望・私的関心又は別の活動の結果を設定済みにしない。',
 'r6bs':'同じ著者の現在点を基準とするia/icの有効な順序付き履歴内の前の点に、同じ作品・概念・主題のr6brを行う活動があり、現在点でも同じ主題がr6bqの最大重点にある。設定したという回顧と現在の論述上の結果を結び、開始日・最初の設定・全中間時点の連続維持を補わない。',
 'r6bt':'同じ宗教領域h26j7についてr6bsを、既存biの啓蒙過程の閉じた性質記述へ接続する。biは同じ本人が自己に帰責される未成熟から自立的行使能力へ移るbeから構成され、原語の綴りだけで概念を指定しない。重点を述べる際にその過程の実例を実行しない。',
}
LIMITS=[
 'u0016第一文のIch habe den Hauptpunkt der Aufklärung ... vorzüglich in Religionssachen gesetztへの依存群。Hauptpunktとvorzüglichを宗教事項が論述の最大の重点であるという読みへ結び、他分野の完全な排除や唯一の最大は要求しない。',
 'habe gesetztは現在の論述を振り返り、同じ著者による前の設定・提示と、現在もその主題に最大の重点がある結果を述べる読み。現在の思いつきだけや、設定したかっただけにはしない。具体的な年・日付、最初に設定した人、発話時までの全時点での維持は追加しない。',
 '主題比較は同じ作品・概念・固定基準を共有する。同じ語を多く書いたことや、現実の啓蒙がその分野で最も成功したこととは区別する。比較範囲を結論から逆算して絞らず、未知を低い重点とみなさない。',
 '啓蒙の性質は既存biを引用し、そのbe/rqrj/bp/upの同じ本人・離脱の関係を保つ。宗教という主題への重点は引用概念についての論述関係であり、全人間の現実の離脱をこの回顧の中へ追加しない。',
 '固定原文die des AusgangesとAAのd. i. des Ausgangesの照合はninth-paragraph-source-reading-v1に記録した。離脱句を説明として読むが、その説明の談話提示、ichの本文著者への閉じた接続、二つの理由と全文帰属は未接続。',
 '正本117主張、18全単位判断、確認13,741文字を保持する。比較や時制の有限試験を第一文全体の意味判断へ変換しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    scope='i[item a][k h26sd[v author v work v concept v item v reference]]'
    order='i[left a right a][k h26sc[v author v work v concept v right v left v reference v point]]'
    text='d r6bq['+FRAME+'] c[k rce[v topic '+scope+' '+order+']].\n'
    text+='d r6br[activity a '+FRAME+'] c['+both('k dg[v activity v point]','k df[v author v activity v point]',
        'k h26sb[v activity v work v concept v topic v reference v point]','k r6bq[v author v work v concept v topic v reference v point]')+'].\n'
    history='i[at d][k ia[v author v point v at]]';before='i[first d last d][k ic[v first v last v point]]'
    earlier='g previous d['+both('k ia[v author v point v previous]','k ic[v previous v point v point]',
        'g activity a[k r6br[v activity v author v work v concept v topic v reference v previous]]')+']'
    text+='d r6bs['+FRAME+'] c['+both('k aa[v author]','k ta['+history+' '+before+']','k ia[v author v point v point]',earlier,
        'k r6bq[v author v work v concept v topic v reference v point]')+'].\n'
    text+='d r6bt[author a work a topic a reference d point d] c['+both('k h26j7[v topic v reference]',
        'k r6bs[v author v work r[p bi] v topic v reference v point]')+'].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,('rce','dg','df','ia','ic','ta','aa','h26j7','bi')),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='retrospective_principal_discourse_emphasis_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
