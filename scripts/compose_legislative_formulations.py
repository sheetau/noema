"""Bind legislative responsibility, complete formulations and prior enactment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/religious-emphasis-sentence-basis-v1.json'
LIBRARY='examples/v016/legislative-formulations.noema';BASIS='data/legislative-formulations-basis-v1.json'
CLAUSE='i[h[j[a]] e]'
PRIMITIVES={
 'h26tb':('[a a a d] c',['office','community','law','reference'],
   '同じ政治的共同体と固定基準で、この公的統治職が担う公的規律の制定・維持・改訂の対象範囲に、この法の規範内容が入る。職の保持者個人の所有物、本人だけが起草した法、現に支持する法だけという意味ではない。君主的役職とその保持、法の全条項、実際の採択は別に構成する。批判されるかや許可があるかで範囲を選ばない。'),
 'h26tc':('[a a d] c',['form','part','reference'],
   '同じ固定基準で、この法的な定式の規範内容を表す全構成部分の一つである。都合のよい条項だけへ縮めず、見出し・紙・ページなど規範内容でない物理要素の全列挙とは区別する。部分の意味はh26tdで閉じた内容へ結ぶ。'),
 'h26td':('[a '+CLAUSE+' d] c',['part','content','reference'],
   '同じ解釈基準で、指定した表現部分はこの閉じたNoema規範内容を表す。その内容関数は法・人民・共同体の順の三対象列を受け、当該法の規律状態を指定する。単なる主題への言及、内容名の引用、いくつかの語が一致することではない。語の用法と構文に基づく表現と内容の対応を入力として明示し、表す規律の現実の成立・正当性・履行は要求しない。'),
 'h26te':('[a d] c',['form','reference'],
   'この対象は同じ基準で、法として定める内容を言語的に構成し示す定式・文案である。記号列の配置と読解による規範の指定を持ち、法そのものや紙の写し、単なる判断の名称とは区別する。既に印刷された現物や公表済みであることは要求せず、構想する文案も含める。どの全規範内容を表すかは合成側で確認する。'),
 'h26tf':('[a a a d] c',['baseline','revision','community','reference'],
   '同じ共同体・固定基準で、後者の法内容は前者が扱う公的規律をどのように定めるかという同じ課題について、その定め方を改める案として対応する。条項の追加・削除・意味の変更又は内容を保った表現の変更を許す。単なる偶然の話題類似、改訂の実際の採択、改訂の優越性又は客観的な正しさは意味しない。比較方向を逆転せず、全条項の一対一対応を要求しない。'),
}
MEANINGS={
 'r6ck':'同じ共同体・固定基準で、本人が君主r2ujであり、同じ本人が保持する同じ最高統治職の公的規律の対象範囲h26tbに法内容が属する。別職の所管や別の保持者から立法への所有的参照を借りない。',
 'r6cl':'同じ法の非空の全規範条項と、同じ定式の非空の全規範表現部分が、h26ccの閉じた内容とh26tdにより双方向に対応する。全条項を表し、法にない規範を余分に表さず、重複表現や一条項を表す複数部分を排除しない。規範の真理は実行しない。',
 'r6cm':'同じ統治者・人民・共同体・法・定式・固定基準について、r6ckの立法範囲、r5eiの完全な人民と全法条項、r6clの定式による全内容表現を同時に要求する。全臣民の選択や許可は別に結ぶ。',
 'r6cn':'同じ法・人民・共同体・定式の構成を保ち、同じ有効な候補履歴内で評価点より前に、指定主体がその同じ法を同じ人民へ課すr5ekの活動があった。現在の採択や提案だけ、別の法の採択、条項状態の偶然の成立を過去の制定へ替えない。現在の継続的効力はこの過去性から推論しない。',
 'r6co':'同じ現在の統治者のr6cmの立法範囲について、その法と定式にr6cnの既に行われた公的採択がある。過去の採択主体は別に存在量化し、今の統治者本人の制定だけに狭めない。',
 'r6cp':'同じ統治者・人民・共同体・基準における比較元と改訂候補の両法内容・両定式をr6cmへ結び、定式を区別し、同じ規律課題への改訂方向h26tfを保持する。変更後の法内容の同一性や差異は強制せず、表現のみの改訂と規範内容の改訂をともに許す。改善の判断・現実の採択・批判の提示は別。',
}
LIMITS=[
 'u0016第二文のseiner Gesetzgebung、bessere Abfassung derselben、der schon gegebenenを結ぶための依存群。今回は立法範囲・同じ全法内容と定式・過去の採択・比較元と改訂候補の方向を構成し、bessereという優越判断、公的提示・批判・許可・危険・洞察・全文提示は未接続。',
 'Gesetzgebungは同じ国家元首の最高統治職が担う公的規律の制定・維持・改訂という読み。個人の所有物や本人の著作、本人が採択したものだけにはしない。法は既存h26ca/h26cb/h26cc/r5eiの完全な人民・共同体・全規範条項を持ち、名前だけの法へ戻さない。',
 'Abfassungを公的規律の定式・文案とし、条項を表す内容と媒体の写しを区別する。規範内容を保持した書き方の改訂に限定せず、条項の追加・削除・変更も同じ規律課題の改訂に含める。どちらがよいかをこの対応から導かない。',
 '表現する全内容を同じ規範関数へ結ぶ。全条項が少なくとも一部分に表され、全規範部分が少なくとも一条項を表す。複数部分で同じ条項を表してよく、特定の句読点・物理的な条番号・一対一対応を原文へ追加しない。言語表現と内容の対応そのものは明示した解釈入力であり、有限試験が任意の自然言語を自動解釈するわけではない。',
 'der schon gegebenenは、同じ法内容が同じ人民へ既に公的に課されたことを先行採択活動に結ぶ。現在の君主と過去の制定者は同一に限定しない。旧草案rspの単一の条件付き規定だけに法律全体を縮めず、r5ekによる全条項を使う。具体的な公布日、制定者の名、全期間の継続効力を補わない。',
 '法の表現は引用内容を実行せず、既に採択されたという内容ではr5ekの採択・制度的効果・全条項状態を同じ先行点で実行する。二つの境界を混同しない。全臣民r6boと法の人民r45dは役割が異なり、無条件に同じ集団へ同定しない。',
 '原刊492–493頁の第二文とAA VIII41行15–22を照合したv2を用いる。固定本文は保存する。正本118主張、第一文336文字・18全単位判断を変更せず、第二文全体を意味確認済みとはしない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    office='g office a['+both('k h234f[v office v community v reference]','k r2ui[v ruler v office v community v reference]',
        'k h26tb[v office v community v law v reference]')+']'
    text='d r6ck[ruler a community a law a reference d] c['+both('k r2uj[v ruler v community v reference]',office)+'].\n'
    clauses='k h26cb[v law v clause v reference]';parts='k h26tc[v form v part v reference]'
    expresses='k h26td[v part k h26cc[v clause v reference] v reference]'
    text+='d r6cl[form a law a reference d] c['+both('k h26te[v form v reference]',
        'g clause a['+clauses+']','g part a['+parts+']',
        'f clause a[y['+clauses+'][g part a['+both(parts,expresses)+']]]',
        'f part a[y['+parts+'][g clause a['+both(clauses,expresses)+']]]')+'].\n'
    frame='ruler a people a community a law a form a reference d';args='v ruler v people v community v law v form v reference'
    text+='d r6cm['+frame+'] c['+both('k r6ck[v ruler v community v law v reference]',
        'k r5ei[v people v community v law v reference]','k r6cl[v form v law v reference]')+'].\n'
    history='i[at d][k h257z[v reference v candidate v at]]';order='i[first d last d][k ic[v first v last v candidate]]'
    prior='g earlier d[g activity a['+both('k h257z[v reference v candidate v earlier]','k ic[v earlier v point v candidate]',
        'k r5ek[v actor v people v community v law v activity v reference v candidate v earlier]')+']]'
    text+='d r6cn[actor a people a community a law a form a reference d candidate d point d] c['+both(
        'k r5ei[v people v community v law v reference]','k r6cl[v form v law v reference]',
        'k ta['+history+' '+order+']','k h257z[v reference v candidate v point]',prior)+'].\n'
    text+='d r6co['+frame+' candidate d point d] c['+both('k r6cm['+args+']',
        'g actor a[k r6cn[v actor v people v community v law v form v reference v candidate v point]]')+'].\n'
    text+='d r6cp[ruler a people a community a baseline a revision a oldform a newform a reference d] c['+both(
        'u[e[v oldform][v newform]]','k r6cm[v ruler v people v community v baseline v oldform v reference]',
        'k r6cm[v ruler v people v community v revision v newform v reference]',
        'k h26tf[v baseline v revision v community v reference]')+'].\n'
    return text
def build():
    old=parent();roots=('r2uj','r2ui','h234f','r5ei','h26cb','h26cc','r5ek','ta','h257z','ic')
    doc=deepcopy(old.document);doc.update(declarations=closure(doc,roots),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='legislative_scope_complete_formulations_and_prior_enactment_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
