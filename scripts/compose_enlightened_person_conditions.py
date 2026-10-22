"""Bind standing practical judgment and grounded fear to the same person."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_qualified_prince_frame import PROFILE

PARENTS=('data/prince-conclusion-basis-v1.json','data/prospect-grounded-apprehension-basis-v1.json','data/qualified-prince-frame-basis-v1.json','data/religious-collective-assessment-basis-v1.json')
LIBRARY='examples/v016/enlightened-person-conditions.noema'
BASIS='data/enlightened-person-conditions-basis-v1.json'
PRIMITIVES={
 'h26vd':('[a d] c',['topic','reference'],
  '同じ固定基準で、この主題は、人が自分の理解力で信念と行為の理由を吟味すること、および共同生活でその使用を認め又は制限する仕方を扱う領域である。宗教上の教え・実践の判断に加え、法・統治方針の吟味と公的な討論を含む。特定の宗教への同意、現行法への賛成、君主の地位、軍事技術の熟練は領域の条件ではない。個別専門知識の全体や全人知を網羅する領域へ拡張しない。対象の全関連事項はh26kaで本人ごとに評価前に固定し、宗教だけ又は成功した事項だけに縮めない。'),
}
MEANINGS={
 'r6eu':'同じ人・固定基準について、h26vdの宗教と法・統治を含む判断領域に属し、h26kaでその本人に関係する全事項として選ばれる事柄。能力の有無、信仰、職業、現在の成功によって選別しない。',
 'r6ev':'r6euの全事項とr5s7の同じ事項名を既存r5syに渡し、自立的で適切かつ安定した判断の既有能力評価が整うことを返す。参照の一致と全事項の非空性を保持する。',
 'r6ew':'r6evと同じ全事項・質・固定基準をr5szへ渡し、本人側の既有基盤を保持する通常機会での行使能力を返す。今すぐの機会、過去の取得、全事項を一度に実行する一方法とは分ける。',
 'r6ex':'同じ領域と固定基準にr6ewを接続した人物性質。閉じた基準名h223hの指示を下位で元の基準と照合し、他人の技能や別基準の成功を流用しない。',
 'r6ey':'同じ領域と基準の閉じた名前をr6exへ適用する段階7の人物性質記述。引用を作る際には能力・事項・基準名を実行しない。',
 'r6ez':'同じ本人と同じ点について、r6exの判断能力とr6etの支持のない不利益予期の不在を連言する。能力のある別人と恐れのない別人を寄せ集めず、一方から他方を導かない。',
 'r6e2':'同じ領域と基準の閉じた名前をr6ezへ適用した段階7の人物条件。軍隊、公的平穏の保証、発言可能性まで完了した範囲とはしない。',
 'r6e3':'同じ著者・節・仮定範囲の人物範囲記述に束縛された当人について、r6eyの能力をその本人自身の性質として強調する。h223g/h223hの対象一致を照合し、他者への働きかけだけの話へ替えない。',
 'r6e4':'同じ著者・節・仮定範囲・人物範囲の下で、r6e2の能力と根拠のない恐れの不在を、その人物の前提条件として提示する。現実の実在・条件の真理・発言の成功をここでは断定しない。',
 'r6e5':'r6e3の本人の強調とr6e4の前提提示を同じ節・範囲・領域・固定基準へ接続する。後続で渡す人物範囲の内容を宗教専用の旧範囲へ勝手に置換しない。',
}
LIMITS=[
 'u0017第一文selbst aufgeklärtを、宗教上の判断と法・統治・公的討論を含む実践上の判断領域で、本人が自立的で適切かつ安定して自分の理解力を使える到達状態として読む。u0016で宗教から立法へ広がる文脈を採る明示的な読みであり、全知や全専門技能、歴史的な啓蒙の唯一の定義ではない。',
 '旧r5xvは宗教領域専用のまま保存する。新しい主題を旧r5tbへ渡して宗教判定を偽にしたり、宗教という名前だけを政治全般へ再解釈したりしない。既存のr5sy/r5szと事項ごとのr5sv/r5ssは変更しない。',
 'h26vdは領域指定、h26kaはその本人に求める全関連事項の固定、h26j3/j4は課題に実際に必要な全条件の内容である。範囲と条件の適切さは解釈入力に責任があり、単なる原語名を未説明の内容として置かない。無限定の専門的全知ではなく、同じ領域で本人が判断を問われる事項を網羅する。',
 'selbstは当人自身への対照的な強調として読む。当人だけの排他性、意外な最低確率、他人の未啓蒙又は既啓蒙は追加しない。nurの限定とは別の関係で扱う。',
 '恐れの条件は前群r6etを同じ本人・点・基準へ結ぶ。能力から恐れの不在を因果的又は論理的に導かず、根拠のある恐れは許す。恐れの全対象記述は有限リストへ変更しない。',
 '本文119主張・登録簿v203・19全単位判断は保持する。軍隊の規律と人数・利用可能性・平穏の保証、こうした者だけが言えるという限定、自由国との対比、引用命令、影の比喩と全文の提示は後続で統合する。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r6eu[person a topic a matter a reference d] c['+both('k aa[v person]','k h26vd[v topic v reference]','k h26ka[v person v topic v matter v reference]')+'].\n'
    for n,target in (('r6ev','r5sy'),('r6ew','r5sz')):
        text+='d '+n+'[topic a reference d standardcontext i[d]] h[a] e[k '+target+'[v topic v reference p r6eu k r5s7[v reference] v standardcontext]].\n'
    text+='d r6ex[topic a reference d] h[a] e[k r6ew[v topic v reference k h223h[v reference]]].\n'
    text+='d r6ey[topic i[a] reference i[d]] '+PROFILE+'[o a[r h[p r6ex]][v topic v reference]].\n'
    text+='d r6ez[topic a reference d] h[a] e[i[person a][b point['+both('t[c[k r6ex[v topic v reference]][v person]][v point]','t[k r6et[v person v reference]][v point]')+']]].\n'
    text+='d r6e2[topic i[a] reference i[d]] '+PROFILE+'[o a[r h[p r6ez]][v topic v reference]].\n'
    fields='clause a author a scope a topic a reference d boundary '+PROFILE+' context d'
    args='v clause v author v scope v topic v reference v boundary v context'
    names=both('e[s[k h223g[v topic]]][v topic]','e[s[k h223h[v reference]]][v reference]')
    own='k r6ey[k h223g[v topic] k h223h[v reference]]'
    pair='k r6e2[k h223g[v topic] k h223h[v reference]]'
    text+='d r6e3[focus a '+fields+'] c['+both(names,'k h26nq[v focus v author v scope v clause v boundary '+own+' v context]')+'].\n'
    text+='d r6e4['+fields+'] c['+both(names,'k h26nn[v clause v author v scope v boundary '+pair+' v context]')+'].\n'
    text+='d r6e5[focus a '+fields+'] c['+both('k r6e3[v focus '+args+']','k r6e4['+args+']')+'].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(('aa','h26ka','r5s7','r5sz','h223g','h223h','h26nq'),('r6et',),('h26nn',),('r5sy',))):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='same_person_practical_enlightenment_and_grounded_apprehension_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
