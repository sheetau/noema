"""Assess a designation through asymmetric respect in its adopted uses."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_self_report_dignity import FRAME,FRAME_NAMES,FARGS,name_args
from scripts.compose_designation_rejection import PATTERN,USE_CODE

PARENTS=('data/designation-rejection-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/haughty-designation.noema';BASIS='data/haughty-designation-basis-v1.json'
PAIR='actor a other a activity a source a office a community a reference d point d'
PAIRARGS='v actor v other v activity v source v office v community v reference v point'
PRIMITIVES={
 'h26nl':('[a a a d d] c',['actor','person','community','reference','point'],
   '同じ共同体・固定評価基準において、主体はこの人を、その人自身の判断と選択に固有の立場を持つ者として扱い、主体の都合だけに従属する下位の者として扱わない。ここで比較する対人的な最低限の尊重の内容を指定する。全判断の正しさへの賛同、全行為の無制限な許可、称賛・親愛・敬称、法的職階や実力の同一性とは別である。この扱いが要求されること、本人の方針、現実の実行は別々に結ぶ。'),
 'h26nm':('[a a a '+PATTERN+' a d d] c',['actor','activity','name','pattern','community','reference','point'],
   '同じ人が同じ活動で、同じ名称に結ばれた段階3の閉じた性質記述を、その人自身を位置付ける言い方として自ら採用している。自己への名称適用・名称の意味保持は別に検査する。単なる引用、他人の用法の報告、批判又は皮肉としての言及だけを採用としない。記述の真理、正当な資格、他者の承認、内心の全信念は含意しない。'),
}
MEANINGS={
 'r5w7':'固定基準を保ち、主体・扱いを受ける人・共同体の正確な三対象列から、h26nlの同じ対人的尊重の内容を返す。逆順にすると誰が誰を扱うかが変わり、同じ真理値だけで列を置換しない。',
 'r5xa':'固定基準の閉じた名前をr5w7へ適用した段階0の尊重内容族記述。要求と実践方針へ同じ記述を渡し、引用時には実際の扱いを実行しない。',
 'r5xb':'異なる二人について、同じ主体・同じ活動・同じ場面で、相手から自分への尊重を肯定する実践的立場と、自分から相手への尊重を否定する実践的立場を取る。固定基準の参照を確認し、二つの立場に同じ内容族と逆向きの列を渡す。',
 'r5xc':'r5xbの対人上の非対称に加え、同じ規範出所が主体に同じ立場で、同じ相手への同じ尊重内容を要求している。自分だけを上位に置く立場が相手への必要な尊重に反するという評価であり、単なる職階差や裁量の資格不足からは認定しない。',
 'r5xd':'同じ名称の段階3の意味r5wuを同じ共同体・基準で保持し、同じ人が同じ活動で自分へその名称を適用し、その意味を自分の位置付けとして採用する。内容の裁量・自由方針の実際の成立は要求しない。',
 'r5xe':'同じ意味設定を固定し、人物・活動・名称・場面ごとのr5xdの自己適用と採用を返す。名称評価の仮定用例へ接続する関係。',
 'r5xf':'r5xdの同じ用例において、固定した対象集団の少なくとも一人に対し、同じ活動の主体がr5xcの非対称と尊重要求への違反を持つ。別人・別活動の態度や、集団外の相手の扱いを用例へ継ぎ合わせない。',
 'r5xg':'非空の固定人物範囲と仮定場面範囲について、r5xeの同じ名称の全採用用例がr5xfを満たし、少なくとも一つの採用用例があることを既存rnvで構成する。名称の採用における高慢さという明示読解。現在の名称使用、拒否する本人の高慢な性格、全世界の全用法は断言しない。',
}
LIMITS=[
 'u0015第一文のden hochmüthigen Namen der Toleranzに向けた名称評価の依存群。評価対象は呼称とその採用に含まれる立場であり、名称を拒否する君主本人を高慢と分類するのではない。本文・登録簿・確認済み分量は変更しない。',
 'hochmüthigは自己を上に置き、他者への必要な尊重を損なうという否定的な対人評価として読む。DWBのhochmuth第二義と、AA6:465の相手から尊重を求めつつ相手には与えないという後年の説明を補助にする。後年の倫理学全体、永続的な性格、悪意の自覚、権力の現実の行使、病理的診断を原文へ追加しない。',
 '寛容という呼称を、自分の裁量から自由を授ける側として自己を位置付ける説明r5wuに固定する。その自己位置付けの採用用例が、相手の自立した立場を自分だけと同等には扱わない非対称を含む、という本箇所の読みを評価式にする。規範上の裁量が存在しないことだけを高慢とせず、実際の自由政策が成立する場合もその呼称を批判し得る。',
 '対人的な尊重の内容はh26nlの具体的な扱いとして固定する。物理的能力、王と臣民の職務の差、単なる敬称、本人の好悪と同一視しない。要求h7kと実践方針h244jと実際の扱いを別に評価し、尊重が実行されていないことだけから意図的な拒否を推論しない。',
 '一つの用例で相手への非対称を示すには、同じ集団の少なくとも一人が必要である。あらゆる他者を常に軽視するという全称的性格は加えない。名称評価は指定した全採用用例に関する全称であり、肯定的な反例用例が一つあれば成立しない。',
 '候補人物集団と仮定場面関数は評価結果に先立って固定した関連用法の全範囲を入力する。実際に高慢だった人や都合のよい例だけを選ばない。非空の人物・場面・採用用例を要求し、引用や批判としての言及を自己採用へ昇格させない。これは全可能世界の網羅や統計的な典型性の証明ではない。',
 '同じ名称・共同体・固定基準・規範出所・公的立場・宗教的自由の対象集団を共有する。名前の具体的参照、候補人物と仮定場面の本文接続、著者への評価帰属は全文統合で固定する。評価を君主の条件の内部に隠して、評価が偽なら主文が空虚に成立する構成にしない。',
 'selbstの強調、alsoの帰結提示、一般的な君主、前回の自己報告と品位評価、啓蒙・称賛・最初の政府側の解放・良心事項の自由、一文全体と後続の通読は残る。有限モデルの検査は原文との同義性を自動認定しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r5w7[reference d] h[j[a]] e[i[bindings j[a]][b point['+bind(('actor','other','community'),'k h26nl[v actor v other v community v reference v point]')+']]].\n'
    text+='d r5xa[reference i[d]] '+USE_CODE+'[o a[r[p r5w7]][v reference]].\n'
    code='k r5xa[k h223h[v reference]]';forward='l[a][v actor v other v community]';reverse='l[a][v other v actor v community]'
    stance=lambda b,s:'k h244j[v actor v activity '+code+' '+b+' '+s+' v point]'
    text+='d r5xb['+PAIR+'] c['+both('k aa[v actor]','k aa[v other]','u[e[v actor][v other]]',
        'e[s[k h223h[v reference]]][v reference]',stance(reverse,TRUE),stance(forward,FALSE))+'].\n'
    text+='d r5xc['+PAIR+'] c['+both('k r5xb['+PAIRARGS+']','k h7k[v source v actor v office '+code+' '+forward+' '+TRUE+' v point]')+'].\n'
    adopted='k h26nm[v actor v activity v label k r5wu['+name_args(FRAME_NAMES)+'] v community v reference v point]'
    text+='d r5xd[actor a activity a label a '+FRAME+' point d] c['+both('k r5wv[v label '+FARGS+']',
        'k r5ww[v actor v activity v label v actor v point]',adopted)+'].\n'
    text+='d r5xe['+FRAME+'] h[a a a d] c[i[actor a activity a label a point d][k r5xd[v actor v activity v label '+FARGS+' v point]]].\n'
    target='g other a['+both('k h246c[v group v other v reference]','k r5xc['+PAIRARGS+']')+']'
    text+='d r5xf['+FRAME+'] h[a a a d] c[i[actor a activity a label a point d]['+both('k r5xd[v actor v activity v label '+FARGS+' v point]',target)+']].\n'
    people='i[name a person a anchor d][k h246c[v candidates v person v anchor]]'
    cases='i[name a anchor d point d][c[v cases][v point]]'
    text+='d r5xg[label a '+FRAME+' candidates a cases h[d] c] c[k rnv[v label v reference '+people+' '+cases+' k r5xe['+FARGS+'] k r5xf['+FARGS+']]].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5wv','r5ww','h246c','h244j','rdr'],['aa','h7k','rnv'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='designation_appraisal_through_asymmetric_respect_in_adopted_uses',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
