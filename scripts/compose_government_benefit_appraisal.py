"""Compose comparative prospects and an institution's nonfactive policy appraisal."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/dignity-conforming-treatment-basis-v1.json','data/civic-spirit-sentence-basis-v1.json')
LIBRARY='examples/v016/government-benefit-appraisal.noema';BASIS='data/government-benefit-appraisal-basis-v1.json'
CODE='i[h[j[a]] e]';POLICY='h[j[a]] e';FIELDS='government a community a reference d';ARGS='v government v community v reference'
ZERO='n p a b';ONE='n p b b';TRUE='e['+ZERO+']['+ZERO+']';FALSE='u['+TRUE+']'
BASE='actor a beneficiary a code '+CODE+' policy '+POLICY+' reference d candidate d'
BARGS='v actor v beneficiary v code v policy v reference v candidate'
PRIMITIVES={
 'h27dm':('[a d] j[a]',['beneficiary','reference'],'固定した受益対象・評価基準について比較する、受益対象にとって好ましい状態目標の全一覧。収入だけでなく統治の遂行等も設定可能だが、本文が具体的目標を列挙したとはしない。目標を選び直して有利な側だけを数えず、完全性・非空・重複なしを合成側で確認する。'),
 'h27dn':('[a a d] c',['beneficiary','goal','reference'],'同じ受益対象の状態を比較する固定基準に、この望ましい目標が属する。職員個人や別集団だけの利益を政府自身の利益に流用しない。両比較側・全判断候補で同じ範囲を使う。'),
 'h27do':('[a a d] b',['beneficiary','goal','reference'],'同じ受益対象・目標・基準について、目標達成を比較する加法的な重み。有理数の正値を合成側で要求する。目標間の損益交換を表す明示的モデルの入力であり、金銭額や道徳的価値と同一視せず、原文の数値を復元したとはしない。'),
 'h27dp':('[a a d] e',['beneficiary','goal','reference'],'同じ受益対象が同じ固定目標を達成していることのNoema内容。判断候補や政策側に応じて内容を入れ替えず、原語や目標名だけを真偽値に置換しない。候補結果の点で実評価する。'),
 'h27dq':('[a '+CODE+' d d c] j[a]',['actor','policy','reference','candidate','positive'],'同じ主体・閉じた政策記述・固定基準・評価候補において、その政策を実現する側又はしない側の、比較上の結果場合の全一覧。各側の完全性と非空は合成側で検査する。結果の番号は側内で使い、両側で同じ番号が同じ点を指すとは限らない。'),
 'h27dr':('[a '+CODE+' d d c a] c',['actor','policy','reference','candidate','positive','outcome'],'指定した政策の実現又は不実現に対応する比較で、この結果場合が完全な候補範囲に入る。同じ背景・見通し期間・関連事情を比較の両側で保つ。単なる観察上の相関を政策の効果と同一視せず、この対応の妥当性は解釈入力として別に責任を持つ。'),
 'h27ds':('[a '+CODE+' d d c a] d',['actor','policy','reference','candidate','positive','outcome'],'同じ政策比較・側・結果場合を評価する状況。政策の実現極性と目標内容をこの同じ点で評価する。別人・別政策・別判断候補の結果を流用しない。'),
 'h27dt':('[a '+CODE+' d d c a] b',['actor','policy','reference','candidate','positive','outcome'],'同じ側の結果場合に与える見込みの有理数重み。非負かつ全場合の和が1であることを合成側で検査する。現実の統計確率とは限らず、評価候補の見込みである。零の重みの候補も完全な範囲にあれば残す。'),
 'h27du':('[a a d d d] c',['beneficiary','goal','reference','candidate','outcome_point'],'同じ受益対象・固定目標・評価候補・結果点について、目標達成の評価が整っている。目標の真理はh27dpで別に実行し、未評価を未達へ補わない。'),
 'h27dv':('[a '+CODE+' j[a] d] c',['judgment','criterion','bindings','point'],'同じ判断が、この閉じた基準記述と順序付き引数列の内容を肯定する判断として結び付く。同じ外延の別名、単なる検討、否定的判断へ置換しない。判断の所有・公的資格・内容候補の真偽は合成側で別に確認する。'),
 'h27dw':('[a d d] c',['judgment','point','candidate'],'同じ判断を同じ点で解釈するために採る内容候補の完全な範囲。現実の点が含まれることや判断の正しさは要求しない。非空と全候補での肯定内容は合成側で確認する。矛盾した信念一般の理論ではない。'),
 'h27dx':('[a a d] c',['institution','judgment','point'],'この判断が同じ点で、この組織の意思形成手続上、組織自身の見解として引き受けられている。任意の職員の私見、専門家の助言を受領しただけの場合、発表しただけで機関の立場ではない場合を除く。全職員の私的な同意、全会一致、判断の正しさ、対応する政策の規範的採用や実行は含意しない。'),
}
MEANINGS={
 'r6lr':'同じ受益対象・基準の全目標を非空・重複なしで列挙し、各目標の比較重みが正であることを確認する。目標範囲と重みは候補間・政策の両側で固定する。',
 'r6ls':'同じ主体・受益対象・政策記述とその内容・基準・評価候補・実現極性について、全結果列、各点での政策の真偽、全目標の評価、非負かつ総和1の見込みを確認する。渡された記述と内容の一致は利用側で同じ具体的定義へ固定する。',
 'r6lt':'同じ受益対象の固定した全目標について、その結果点での達成の指示値に同じ正の重みを掛けて合計する。妥当な設定はr6lr/r6lsが確認する。',
 'r6lu':'両側でr6lsを満たし、政策を実現する側の重み付き目標達成の見込みが、実現しない側より厳密に大きい。全目標の保証集合の包含を要求せず、同じ基準での損失と不確実な利得も比較する。',
 'r6lv':'同じ政府自身を主体と受益対象にし、同じ全人間成員への具体的な扱いr6llとその記述r6lmをr6luへ渡す。空の外側引数列でだけ評価できる、候補点ごとの利益比較内容。政府・共同体・基準の名前照合は外側r6lxで要求する。',
 'r6lw':'政府・共同体・基準の閉じた名前をr6lvへ適用した閉じた利益判断内容の記述。扱いの記述r6lmと利益判断の記述r6lwを区別し、作成だけではいずれも実行しない。',
 'r6lx':'同じ政府資格・名前照合の下で、一人の人間が同じ生起判断に能動的に公的資格で参加し、政府がその判断を自身の見解として引き受ける。rlgで同じ政府を主題とする肯定判断を、同じr6lw・空引数・判断点・非空の全候補へ結ぶ。現実の利益や規則採用は要求しない。',
 'r6ly':'同じ政府・共同体・基準・評価点について、r6lxの同じ人と同じ判断が存在する。資格・判断・組織的引受け・内容を別々の証人から寄せ集めない。',
 'r6lz':'同じ政府・共同体・基準にr6lyの判断内容を割り当て、後続の政治的終点へ適用できるようにする。',
}
LIMITS=[
 'u0017のdie es ihr selbst zuträglich findetを、同じ政府が同じ尊厳に応じた扱いを自分自身にも有益と肯定する、非事実的な判断として読む。尊厳の根拠を政府の利益に置換せず、実際の利益・規範採用・履行を判断から導かない。',
 '有益さは固定した全目標と正の重みによる達成の見込みの厳密な増加として形式化する。有限の結果場合と有理数の加法的比較は明示的な採用モデルで、原文に確率計算や数値的効用理論を帰属しない。語義の唯一の必要十分条件、非加法的・比較不能な価値の一般理論は主張しない。',
 '旧rx7の保証集合の真包含では、重い利得と軽い損失の交換や、保証に至らない見込みの改善を排除するため、その条件をこの文の必須要件にしない。具体的な目標・確率・重み・期間は原文にないので捏造せず、同じ基準で公開する解釈入力に残す。',
 '目標内容はNoemaの内容で供給し、実現・不実現の全結果点で評価する。比較の背景一致と政策への帰属は結果範囲の解釈入力であり、有限検査が現実の政策効果を同定するものではない。',
 '政府を人間の判断主体へ無条件に渡さず、同じ人間の同じ判断行為の生起・能動的参加・公的資格と、組織自身の立場としての引受けを結ぶ。組織の意思形成制度の細部や全職員の一致は補わない。',
 '判断候補は現実と異なってよく、実際には不利又は扱いが未履行でも肯定判断は成立し得る。候補の選定・妥当性や論理的全知・矛盾した信念一般を解決したとはしない。名前・記述・対象・時点を保ち、同じ真偽になる別名へ認知的結合を流用しない。',
 '原則への因果作用、endlich/auch/sogar、同じ政治的終点のnun、Wenn/so全体、著者注・全文帰属・通読判断は残る。今回の依存群を全文の意味確認へ加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    goals='k h27dm[v beneficiary v reference]';scope='k h27dn[v beneficiary v goal v reference]'
    weight='k h27do[v beneficiary v goal v reference]'
    text='d r6lr[beneficiary a reference d] c['+both('k rcm['+goals+' i[goal a]['+scope+']]','f goal a[y['+scope+'][k hc['+ZERO+' '+weight+']]]')+'].\n'
    key='v actor v code v reference v candidate v positive';outcomes='k h27dq['+key+']'
    selected='k h27dr['+key+' v outcome]';point='k h27ds['+key+' v outcome]';mass='k h27dt['+key+' v outcome]'
    assessed='f goal a[y['+scope+'][k h27du[v beneficiary v goal v reference v candidate '+point+']]]'
    total='q['+outcomes+']['+ZERO+'][i[sum b outcome a][k ha[v sum '+mass+']]]'
    text+='d r6ls['+BASE+' positive c] c['+both('k r6lr[v beneficiary v reference]',
      'k rcm['+outcomes+' i[outcome a]['+selected+']]',
      'f outcome a[y['+selected+']['+both('e[t[c[v policy][l[a][]]]['+point+']][v positive]',assessed,'u[k hc['+mass+' '+ZERO+']]')+']]',
      'e['+total+']['+ONE+']')+'].\n'
    score='q['+goals+']['+ZERO+'][i[sum b goal a][k ha[v sum k hb['+weight+' k hd[t[k h27dp[v beneficiary v goal v reference]][v point]]]]]]'
    text+='d r6lt[beneficiary a reference d point d] b['+score+'].\n'
    expected='q['+outcomes+']['+ZERO+'][i[sum b outcome a][k ha[v sum k hb['+mass+' k r6lt[v beneficiary v reference '+point+']]]]]'
    expectation=lambda sign:expected.replace('v positive',sign)
    text+='d r6lu['+BASE+'] c['+both('k r6ls['+BARGS+' '+FALSE+']','k r6ls['+BARGS+' '+TRUE+']','k hc['+expectation(FALSE)+' '+expectation(TRUE)+']')+'].\n'
    names='k h223g[v government] k h223g[v community] k h223h[v reference]'
    text+='d r6lv['+FIELDS+'] '+POLICY+'[i[bindings j[a]][b candidate['+both('e[d[v bindings]]['+ZERO+']',
      'k r6lu[v government v government k r6lm['+names+'] k r6ll['+ARGS+'] v reference v candidate]')+']]].\n'
    text+='d r6lw[government i[a] community i[a] reference i[d]] '+CODE+'[o a[r[p r6lv]]['+ARGS+']].\n'
    text+='d r6lx['+FIELDS+' person a judgment a point d] c['+both('k r6k3['+ARGS+']','k r6ln['+ARGS+']','k aa[v person]',
      'k dg[v judgment v point]','k df[v person v judgment v point]','k h26n2[v person v judgment v government v point]',
      'k h27dx[v government v judgment v point]',
      'k rlg[v person v judgment v government k r6lw['+names+'] l[a][] v point p fa p fb p h27dv p h27dw]')+'].\n'
    text+='d r6ly['+FIELDS+' point d] c[g person a[g judgment a[k r6lx['+ARGS+' v person v judgment v point]]]].\n'
    text+='d r6lz['+FIELDS+'] e[b point[k r6ly['+ARGS+' v point]]].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for old,roots in zip(libs,(('r6ll','r6lm','r6ln','r6k3'),('rlg','fa','fb','hb'))):
        for d in closure(old.document,roots):
            n=d['name'];e=old.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(c.entries) for c in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in libs))
    basis=dict(status='same_government_nonfactive_comparative_policy_appraisal_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
