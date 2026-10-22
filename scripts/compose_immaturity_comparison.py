"""Compose topical self-incurred immaturity and compare its harm and dishonor."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_bodily_acquisition import PROFILES

PARENT='data/self-departure-sentence-basis-v1.json'
LIBRARY='examples/v016/immaturity-comparison.noema';BASIS='data/immaturity-comparison-basis-v1.json'
STATE='i b[h[a] e]'
PRIMITIVES={
 'h26se':('[a '+STATE+' d] c',['person','state','point'],
   '指定状況の評価で、本人について記述された同じ状態が、その人の選択・不作為に関する落ち度として本人に帰せられる。既存hziqと同じ帰責の意味を段階1の閉じた状態記述へ拡張する。原因であるだけ、誰かの非難発言、法的制裁、故意・唯一原因を追加しない。状態の実際の成立は合成側で別に要求する。'),
 'h26sf':('[a d] c',['topic','reference'],
   '同じ固定基準で、自分の理解力を他者の指導なしに使えないことを比べる全関連領域に、この主題が属する。比較する各状態は同じr6bzの主題引数を替えて構成し、宗教だけ、害が小さい領域だけ、実際に未成熟者が見つかった領域だけへ選別しない。全関連領域を与えることは解釈入力であり、具体的な現代の学部分類は補わない。'),
 'h26sg':('['+STATE+' '+STATE+' a d] c',['left','right','people','reference'],
   '同じ人々・固定基準・背景と害の観点で、左の状態が人々の判断・行為・生き方へ不利益を及ぼす性質は、右の状態のそれ以下である。状態の説明は閉じた内容で指定し、名前や現在の罹患者数、実測損失額、語への嫌悪に置き換えない。比較時に状態の現実の成立や害の実現を実行しない。'),
 'h26sh':('['+STATE+' '+STATE+' a d] c',['left','right','people','reference'],
   '同じ人々・固定基準・尊重の観点で、左の状態が本人の理解・判断を担う者としての尊重に反して人を貶める性質は、右の状態のそれ以下である。単なる実際の不人気、他人の嘲笑、恥ずかしい感情、金銭損失や害の大きさとは別の比較。本人の人間としての価値そのものの喪失や社会的身分の低さを意味しない。引用状態を現実に実行しない。'),
 'h26si':('['+STATE+' a d] c',['state','people','reference'],
   '同じ人々・固定基準において、指定状態には判断・行為・生き方に不利益を及ぼす性質がある。h26sgと同じ害の観点での肯定であり、全比較対象が無害なだけの同順位を有害さへ補わない。現実の被害件数や特定の因果連鎖の実証は要求しない。'),
 'h26sj':('['+STATE+' a d] c',['state','people','reference'],
   '同じ人々・固定基準において、指定状態は理解・判断を担う者としての尊重に反して人を貶める性質を持つ。h26shと同じ観点での肯定であり、全比較対象が尊重を損なわないだけの同順位を不名誉へ補わない。実際の非難や恥の感情、本人の価値の消滅とは分ける。'),
}
MEANINGS={
 'r6bu':'同じ事柄・固定基準について、人が自分の理解能力をその事柄を扱う同じ活動で使い、別人の指導adを受けないという活動内容。冒頭bbの理解能力・自己使用・非指導を主題の各事柄へ具体化し、sicher/gutの追加の習熟条件や判断の客観的正しさは加えない。',
 'r6bv':'事柄と固定基準の閉じた呼称をr6buへ適用して、本人を引数とする同じ活動記述を作る。能力プロフィールと達成内容の両方を同じ活動へ結ぶための引用。',
 'r6bw':'同じ人・主題・固定基準の非空の全事柄h26kaについて呼称を照合し、同じr6buとr6bvに対するrqvvの通常行使能力評価をそろえる。事柄・通常機会・本人側の基盤・方法区分の評価が欠けたことを不能としない。',
 'r6bx':'同じr6bwの評価の下で、全事柄それぞれにrqvwの通常行使能力がある。事柄ごとに異なる既有の方法を許し、現在たまたま機会がないことと、基盤の不足を区別する。',
 'r6by':'同じ本人・主題・固定基準でr6bwの評価が整い、全事柄の能力r6bxが成立しない状態。全ての事柄で全く不能と強めず、未評価、主題の空、不使用を未成熟に補わない。',
 'r6bz':'同じr6byの主題別未成熟が実際に成立し、同じ本人の同じ状態の閉じた記述がh26seで本人に帰責される。呼称は同じ主題・基準を指すと検査し、別状態の帰責や単なる原因性を借りない。',
 'r6b2':'主題と固定基準の閉じた呼称を段階1のr6bzへ適用し、主題別の自己に帰責される未成熟の閉じた性質を得る。比較のためにその状態の真理を実行しない。',
 'r6b3':'同じ主題・基準のh223g/h223hによる呼称をr6b2へ渡す。比較の対象内容を自由に供給された別の状態へ取り替えない。',
 'r6b4':'比較する同じ人々が非空で人間のみであり、領域範囲h26sfが非空で、その全主題と基準の呼称が一致する。欠けた範囲や誤参照で別の最大を作らない。',
 'r6b5':'r6b4の同じ範囲で、各領域のr6b3による同じ種類の未成熟をh26sgで比較し、指定領域が最大の有害さを持ち、実際に有害な性質h26siを持つ。同順位の最大を許し、全順序的前順序と範囲所属をrceで検査する。',
 'r6b6':'r6b5と同じ領域・人々・基準の状態記述について、h26shの不名誉の比較で最大でありh26sjの性質を持つ。害の比較から不名誉を自動的に導かない。',
 'r6b7':'指定した同じ宗教領域について、同じ人々・固定基準の有害さr6b5と不名誉r6b6の両最上級を結ぶ。別領域の最大や片方の評価だけでは満たさない。',
}
LIMITS=[
 'u0016第一文後半jene Unmündigkeit ... die schädlichste ... die entehrendste unter allenへの依存群。jeneは冒頭の自己に帰責される未成熟を宗教事項に具体化したものとして読む。未陶冶r6ap、年少者、単なる無知、本人の恥の感情に置換しない。',
 '領域別の未成熟は、本文で採る通常行使能力の枠組みを同じ事柄の全範囲へ適用した読み。現在の偶然の不使用、外的な機会の欠如、将来の学習可能性とは分ける。全領域の能力を宗教だけへ狭めて冒頭bcの意味を変更せず、新しい具体化として構成する。',
 '自己帰責は同じ状態の成立と本人の選択・不作為についての帰責を結ぶ。決意・勇気の不足が原因であることを唯一の必要条件にせず、既存rqrjと同じ区別を保つ。全被害や能力不足が本人の責任だとする追加の一般則は置かない。',
 '比較対象は同じ構成の主題別未成熟の全関連領域。h26sfを害・不名誉や現在の人数から選別せず、比較の人々と基準も共通にする。現実の全状態の成立、全員の同時の未成熟、特定被害の発生を比較時に要求しない。',
 'schädlichsteとentehrendsteは有害・不名誉な性質を肯定した上での相対的な最大という読み。各比較は独立であり、同順位を許す。唯一の最悪、数値尺度、実害の順位、社会的身分や人間としての価値の消滅は補わない。',
 '能力入力・事柄と領域の完全性、害と尊重の観点の実質的妥当性は解釈に責任がある。有限試験は全現実の網羅や評価の正しさを証明しない。能力内容の実評価と、閉じた状態を用いた比較の検査を分ける。',
 '原刊照合v1と既存117主張・18全単位判断を保持する。二つの理由、回顧・照応・説明・追加提示と全文帰属はこれから接続し、意味確認文字数を増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    goal=both('k aa[v person]','g faculty a[g activity a['+both('k ab[v faculty v person v point]',
        'k ac[v person v faculty v activity v point]','k h227z[v activity v matter v reference]',
        'u[g other a['+both('u[e[v other][v person]]','k ad[v other v person v activity v point]')+']]')+']]')
    text='d r6bu[matter a reference d] h[a] e[i[person a][b point['+goal+']]].\n'
    text+='d r6bv[matter i[a] reference i[d]] i[h[a] e][o a[r[p r6bu]][v matter v reference]].\n'
    scope='k h26ka[v person v topic v matter v reference]'
    task='k r6bv[k h26kb[v matter v reference] k h223h[v reference]]'
    tail=' '.join('p '+n for _,n,_ in PROFILES)+' p ae p af p ap'
    args='v person c[k r6bu[v matter v reference]][v person] '+task+' v point '+tail
    valid=both('e[s[k h26kb[v matter v reference]]][v matter]','k rqvv['+args+']')
    text+='d r6bw[topic a reference d] h[a] e[i[person a][b point['+both('k aa[v person]',
        'e[s[k h223h[v reference]]][v reference]','g matter a['+scope+']','f matter a[y['+scope+']['+valid+']]')+']]].\n'
    text+='d r6bx[topic a reference d] h[a] e[i[person a][b point['+both('t[c[k r6bw[v topic v reference]][v person]][v point]',
        'f matter a[y['+scope+'][k rqvw['+args+']]]')+']]].\n'
    text+='d r6by[topic a reference d] h[a] e[i[person a][b point['+both('t[c[k r6bw[v topic v reference]][v person]][v point]',
        'u[t[c[k r6bx[v topic v reference]][v person]][v point]]')+']]].\n'
    names='k h223g[v topic] k h223h[v reference]'
    text+='d r6bz[topic a reference d] h[a] e[i[person a][b point['+both('e[s[k h223g[v topic]]][v topic]',
        'e[s[k h223h[v reference]]][v reference]','t[c[k r6by[v topic v reference]][v person]][v point]',
        'k h26se[v person o a[r b[p r6by]]['+names+'] v point]')+']]].\n'
    text+='d r6b2[topic i[a] reference i[d]] '+STATE+'[o a[r b[p r6bz]][v topic v reference]].\n'
    text+='d r6b3[topic a reference d] '+STATE+'[k r6b2['+names+']].\n'
    text+='d r6b4[people a reference d] c['+both('k r5ty[v people v reference]','e[s[k h223h[v reference]]][v reference]',
        'g topic a[k h26sf[v topic v reference]]','f topic a[y[k h26sf[v topic v reference]][e[s[k h223g[v topic]]][v topic]]]')+'].\n'
    scope='i[item a][k h26sf[v item v reference]]'
    for n,relation,positive in (('r6b5','h26sg','h26si'),('r6b6','h26sh','h26sj')):
        order='i[left a right a][k '+relation+'[k r6b3[v right v reference] k r6b3[v left v reference] v people v reference]]'
        text+='d '+n+'[topic a people a reference d] c['+both('k r6b4[v people v reference]',
            'k rce[v topic '+scope+' '+order+']','k '+positive+'[k r6b3[v topic v reference] v people v reference]')+'].\n'
    text+='d r6b7[topic a people a reference d] c['+both('k h26j7[v topic v reference]','k r6b5[v topic v people v reference]','k r6b6[v topic v people v reference]')+'].\n'
    return text
def build():
    old=parent();roots=('aa','ab','ac','ad','h227z','h26ka','h26kb','h223g','h223h','rqvv','rqvw','ae','af','ap','r5ty','rce','h26j7',*(n for _,n,_ in PROFILES))
    doc=deepcopy(old.document);doc.update(declarations=closure(doc,roots),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='topical_self_incurred_immaturity_and_two_maxima_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
