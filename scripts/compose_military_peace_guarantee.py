"""Connect one available army, public peace and scoped causal guarantees."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_qualified_prince_frame import PROFILE

PARENTS=('data/disciplined-availability-basis-v1.json','data/civic-peace-concord-basis-v1.json',
         'data/legislative-freedom-sentence-basis-v1.json','data/enlightened-person-conditions-basis-v1.json')
ROOTS=(('r6fh',),('r572',),('rks','rku','rz','h223g','h223h'),('r6ez',))
LIBRARY='examples/v016/military-peace-guarantee.noema';BASIS='data/military-peace-guarantee-basis-v1.json'
STATE='h[a] c';EQUATIONS='h[a '+STATE+'] c';WORLDS='h['+STATE+'] d'
FRAME='commander a institution a group a community a';FARGS='v commander v institution v group v community'
CONTEXT=FRAME+' threat a reference d anchor d background d'
CARGS=FARGS+' v threat v reference v anchor v background'
LABELS=['commander','institution','group','community','threat','reference','anchor','background']
PREFIX='[a a a a a d d d] '
PRIMITIVES={
 'h26vp':('[a a d] c',['community','threat','reference'],
  '同じ政治的共同体と固定基準について、公的平穏の保証を評価する通常の実践的な範囲で考慮すべき、平穏を失わせ得る事態の全候補の一つ。名前だけで脅威の効果を認定せず、その事態の成立内容と軍隊の有無による効果は別に結ぶ。成功する軍隊・危害のない背景に合わせて候補を落とさず、批判や不同意だけを自動的に危害としない。'),
 'h26vq':('[a a d d d] c',['community','threat','reference','anchor','background'],
  '同じ共同体・事態候補・固定基準・評価起点で、この保証を評価する通常の実践的な背景の全範囲に属する。関連する事情と機構を背景ごとに固定し、軍隊と事態の有無を介入で切り替える。保証する軍隊を選んだ後に安全な背景だけへ変更せず、成功しない背景や未評価の背景を除外しない。全論理的可能世界や数値確率の入力とはしない。'),
 'h26vr':(PREFIX+'j[a]',LABELS,
  '同じ指揮者・制度・軍隊・共同体・事態候補・固定文脈・背景の因果モデルの全変数列。軍隊の利用条件、事態の成立、公的平穏の成立を異なる変数として含める。重複・包含・介入解の存在は合成側で確認し、結果に合わせて変数を削らない。'),
 'h26vs':(PREFIX+EQUATIONS,LABELS,
  '同じ因果モデルで変数値を状態割当てから定める構造方程式。軍隊の利用と事態の二要因を切り替える間も同じ機構・背景を保つ。軍隊あり側だけ別の平穏なモデルを使わない。現実の機構への適合は解釈の責任であり、有限試験を歴史的な真理の実証とはしない。'),
 'h26vt':(PREFIX+'a',LABELS,
  '同じモデルで、同じ指揮者が同じ制度・軍隊・共同体についてr6fhの人数・準備能力・規律・現在の利用条件を満たすことを表す変数。軍隊の名前、現実の戦闘、別の部隊の利用と取り替えず、実際の内容との一致を全介入解で検査する。'),
 'h26vu':(PREFIX+'a',LABELS,
  '同じモデルで、同じ事態候補のh26vxの内容が成立するかを表す変数。軍隊の利用や既に平穏が失われたこととは分ける。軍隊が利用できる場合にも事態が存在し得るため、予防・抑止により平穏が保たれる比較を排除しない。'),
 'h26vv':(PREFIX+'a',LABELS,
  '同じモデルで同じ共同体の公的平穏r572が成立するかを表す変数。軍隊の利用と事態の変数とは別にし、活動可能性・保有・思想的一致・無批判など別の目標へ取り替えない。全介入解でr572の実内容と一致させる。'),
 'h26vw':(PREFIX+WORLDS,LABELS,
  '同じモデルの状態割当てに対応する反事実的な評価状況。同じ軍隊の利用条件、同じ共同体の平穏、同じ事態の内容をこの状況で評価し、それぞれモデルの要因値と照合する。現実の評価起点と同一であることは要求せず、別の共同体や軍隊の整合する状況で代用しない。'),
 'h26vx':('[a a d] e',['community','threat','reference'],
  '同じ共同体・事態候補・固定基準で、その事態が成立することの内容。例えば公的衝突へ進み得る組織的な圧力の存在であり、既に共同生活が乱れたことや平穏の否定そのものではない。具体的な事態の内容は解釈として与え、候補名の綴りで代用しない。事態が平穏を失わせる比較上の効果はrksで別に検査し、現実の発生を要求しない。'),
}
MEANINGS={
 'r6fk':'軍隊利用・事態・平穏の異なる三要因を同じ変数列へ結ぶ。平穏要因への射影を目標としてrksの四介入保護比較とrkuの三内容対応を要求する。各条件で解が非空で全解が条件を満たす必要があり、無解・一つだけの成功解・別目標の真偽一致で保証を作らない。',
 'r6fl':'同じ指揮者・制度・軍隊・共同体・事態候補・固定基準・評価起点・背景の全モデル入力をr6fkへ渡す。軍隊内容は同じr6fh、平穏は同じ共同体のr572、事態は同じ候補のh26vxとし、別の制度・集団・共同体の成功を混ぜない。',
 'r6fm':'同じ指揮者・制度・軍隊・共同体のr6fhがこの点で成立し、固定基準の事態候補が非空で、全候補の通常の背景が非空であり、その全背景についてr6flの保証比較が成立する内容。一つの無害な事態・背景だけや空の対象範囲を保証としない。',
 'r6fn':'同じ指揮者・軍隊・共同体・固定基準についてr6fmを満たす制度がある内容。軍隊の任務・能力・人数・規律・利用と、公的平穏の保証に同じ制度の証人を使う。',
 'r6fo':'同じ指揮者・共同体・固定基準についてr6fnを満たす軍隊がある内容。人数が多い部隊、本人が使える部隊、平穏を保証する部隊を別々に選ばない。',
 'r6fp':'同じ領域・共同体・固定基準における人物条件。本人のr6ezの判断能力と根拠のない恐れの不在に、同じ本人のr6foの規律ある多数の軍隊の利用と公的平穏の保証を同じ点で合わせる。別人の能力・恐れ・軍隊を寄せ集めない。',
 'r6fq':'領域・共同体・基準の閉じた呼称をr6fpへ適用して作る段階7の人物条件記述。引用は人物の実在・条件の現実の成立・発言可能性を主張せず、後続の人物範囲と限定の提示へ渡せる。',
}
LIMITS=[
 'u0017第一文zum Bürgen der öffentlichen Ruheを、同じ人物が利用できる規律ある多数の軍隊が、通常の関連事態に対する公的平穏の保証となるという質的な因果比較で読む。Bürgeの法的な債務保証・金銭補償・約束する発話をこの軍隊へ追加しない。',
 '既存rksの強い保護の読みを採る。同じ背景で軍隊なし・事態なしなら平穏、軍隊なし・事態ありなら平穏でなく、軍隊ありなら事態の有無によらず平穏であることを、四条件の非空の全解に要求する。単なる同時成立、平均的改善又は成功の一例ではない。',
 '通常の実践的な事態と背景は全範囲で量化し、非空を要求する。その現実的な範囲・機構の妥当性は公開した解釈入力の責任で、未知のあらゆる災害・異常事態や全未来への絶対保証を加えない。複数事態の相互作用が関連する場合は組み合わさった事態も候補に含め、単独事態だけへ限定しない。',
 '事態の成立と公的平穏の喪失は別内容である。例えば圧力が存在しても軍隊の抑止で共同生活は乱れない場合を許す。比較上の保証は現に戦闘・強制・騒乱が起きたことを要求しない。現在の平穏を単独の別主張として補わず、ここでは同じ軍隊の現在の利用条件と反事実的な保証役割を述べる。',
 '平穏は既存r572の、非空の政治的共同体の公的共同生活を乱す強制・威嚇・集団衝突の不在である。無批判、活動可能性・保有、一致や政府の正当性と取り違えない。脅威の内容は文脈入力として与えるが、平穏と軍隊利用の内容は既存定義を実際に適用して比較へ渡す。',
 '人物条件r6fpには啓蒙・根拠のない恐れの不在と同じ軍隊の保証をまとめる。これらが発言可能性の必要条件であること、Freistaat、引用命令、selbst・Aber・auch・zugleich aber、比喩の提示と全文帰属・通読は後続で結ぶ。本文119主張・登録簿v203・19全単位判断を保持し、確認文字数は加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    fields='variables j[a] equations '+EQUATIONS+' factor a threatfactor a peacefactor a worlds '+WORLDS+' army e peace e threat e'
    goal='i[state '+STATE+'][c[v state][v peacefactor]]'
    causal='v variables v equations v factor '+goal+' v threatfactor'
    text='d r6fk['+fields+'] c['+both('k rz[v variables v peacefactor]',
      'u[e[v peacefactor][v factor]]','u[e[v peacefactor][v threatfactor]]',
      'k rks['+causal+']','k rku['+causal+' v worlds v army v peace v threat]')+'].\n'
    providers=' '.join('k '+n+'['+CARGS+']' for n in ('h26vr','h26vs','h26vt','h26vu','h26vv','h26vw'))
    text+='d r6fl['+CONTEXT+'] c[k r6fk['+providers+' k r6fh['+FARGS+' v reference] k r572[v community v reference] k h26vx[v community v threat v reference]]].\n'
    selected='k h26vp[v community v threat v reference]'
    background='k h26vq[v community v threat v reference v point v background]'
    allbackgrounds=both('g background d['+background+']','f background d[y['+background+'][k r6fl['+FARGS+' v threat v reference v point v background]]]')
    text+='d r6fm['+FRAME+' reference d] e[b point['+both('t[k r6fh['+FARGS+' v reference]][v point]',
      'g threat a['+selected+']','f threat a[y['+selected+']['+allbackgrounds+']]')+']].\n'
    text+='d r6fn[commander a group a community a reference d] e[b point[g institution a[t[k r6fm['+FARGS+' v reference]][v point]]]].\n'
    text+='d r6fo[commander a community a reference d] e[b point[g group a[t[k r6fn[v commander v group v community v reference]][v point]]]].\n'
    text+='d r6fp[topic a community a reference d] h[a] e[i[person a][b point['+both(
      't[c[k r6ez[v topic v reference]][v person]][v point]',
      't[k r6fo[v person v community v reference]][v point]')+']]].\n'
    text+='d r6fq[topic i[a] community i[a] reference i[d]] '+PROFILE+'[o a[r h[p r6fp]][v topic v community v reference]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,rs in zip(sources,ROOTS):
        for d in closure(source.document,rs):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(imported)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(s.source_sha256 for s in sources))
    basis=dict(status='same_available_army_scoped_public_peace_guarantee_and_person_profile_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
