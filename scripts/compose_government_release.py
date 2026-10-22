"""Separate a public institution, its human agents, and first release events."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/conscience-choice-basis-v1.json','data/grateful-regard-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/government-release.noema';BASIS='data/government-release-basis-v1.json'
GOAL='i[h[a] e]';ACHIEVES='h[a a a '+GOAL+' d] c'
CHOICE='government a person a community a matter a judgment a reference d'
CARGS='v government v person v community v matter v judgment v reference'
EPISODE='actor a activity a government a group a community a reference d candidate d first d acted d last d'
EARGS='v actor v activity v government v group v community v reference v candidate v first v acted v last'
FRAME='group a reference d candidate d';FARGS='v group v reference v candidate'
HISTORY='i[at d][k h257z[v reference v candidate v at]]'
BEFORE='i[left d right d][k ic[v left v right v candidate]]'
PRIMITIVES={
 'h26n2':('[a a a d] c',['person','activity','government','point'],
  'この人が同じ活動において、この政府の公的な職務・権限の行使を担う資格で行為している。本人の実際の能動的参加はdf、生起はdg、政府の公的管轄は別に結ぶ。単なる職員所属、私的な行為、別活動の権限、政府の利益との偶然の一致からは成立しない。正当性、唯一の行為者、全職員の参加、政府組織が人であることを含意しない。'),
}
MEANINGS={
 'r5zj':'同じ政府が同じ共同体の公的運営・執行を指揮する制度上の立場h237nと、公的な命令・禁止・裁定の統治管轄h256sを持つ。政府を人一人又は私的団体へ置き換えない。',
 'r5zk':'同じ生起した活動に、人である能動的当事者が同じ政府の公的な資格で参加する。政府個体をdfの人引数へ渡さず、役所への所属だけを公的行為としない。',
 'r5zl':'r5zkの同じ政府の公的活動が、同じ本人の同じ良心事項・判断候補・立場へh26hoの介入となる。規範の出所と人間の行為者を分け、下位担当者による介入を君主個人の非参加で見逃さない。',
 'r5zm':'同じ良心事項の判断候補について、政府からのr5zbの両方向の許容と非指図、政府の公的活動r5zlによる介入の不在を要求する。組織を人と見なした旧個人向けの介入条件へ置換しない。',
 'r5zn':'同じ政府・共同体・固定基準に相対的な各人の自由。r5zjの政府資格、r5zeの全評価、本人の全良心事項・全判断候補についてr5zmを要求する。本人の能力や判断の実行とは別である。',
 'r5zo':'非空で全員人間の固定集団の全員に同じ政府側のr5znを適用する。同じ集団を前後・候補政府間で固定し、自由な成員だけへ縮めない。原文の人類範囲との完全一致は本文の設定に残る。',
 'r5zp':'同じ政府・共同体・基準の閉じた名前を、各人の政府側の自由r5znへ適用した段階0の状態記述。g3の受益者には集団でなく個々人を渡せる。',
 'r5zq':'r5zpへ渡す政府・共同体・基準の三呼称を、既存r5ziで元の三対象へ照合する。人間であるという条件を政府参照へ追加しない。',
 'r5zr':'同じ本人の良心事項の判断候補に、政府の実行又は不実行の要求、又は政府の公的活動による介入がある。単に積極的許容が未成立であることだけを政府側の後見・拘束としない。',
 'r5zs':'同じ人の自由が、同じ履歴内の同じ過程の前で偽、後で真になり、本人がその過程の変化対象である。同じ人間の行為者が同じ政府の公的資格で同じ活動に参加し、行為点は両端の間、g3は同じ個人・自由記述・結果点へ結ぶ。時間先行だけを因果にせず、過程と単なる前後の対を分ける。',
 'r5zt':'同じ固定集団の前状態で全評価が揃い、少なくとも一人にr5zrの政府側の拘束があり、後では全員に自由がある。前で自由でなかった全員について同じ活動・前後点のr5zsを要求する。前から自由な人まで新規に解放されたとせず、その人も後の全員自由から外さない。',
 'r5zu':'同じ行為者・活動・政府・集団・共同体・履歴・結果点について、r5ztを満たす前状態と行為点がある。別の政府・出来事・結果点の証人を混ぜない。',
 'r5zv':'同じ政府側の自由記述r5zpと同じ個人を、既存r5yfの行為・遅れた結果生成による恩恵へ接続する。集団個体を人への因果の受益者にせず、事実の恩恵とそれを認める態度を区別する。',
 'r5zw':'固定基準で、指定集団がある政府・共同体に相対的なr5zoの自由を持つという共通の結果内容。全政府からの自由又は能力取得とはしない。最初の比較には同じ内容を渡し、具体的達成では政府と出来事も別に保持する。',
 'r5zx':'r5zwの固定基準を閉じた名前で固定した共通の集団状態記述。g3へ集団を渡すための記述ではなく、robの達成比較で共有する内容である。',
 'r5zy':'同じ対象集団・共通の結果記述が一致し、同じ行為者・活動・結果点に、ある政府・共同体についてr5zuの解放がある達成関係。比較する別の行為者に現在の君主の政府だけを強制しない。',
 'r5zz':'既存robで、全人間を比較者にし、同じ履歴・固定集団・共通の結果内容・r5zyの具体的達成を用いて最初を判定する。指定行為者自身の先行達成も除き、同時の別人の達成は許す。全比較者の候補点までの評価を要求する。',
 'r5z2':'r5zzの最初の同じ行為者・活動・結果点に、指定した政府・共同体のr5zuを結ぶ。一般的な最初の証人と、称揚・恩恵へ渡す具体的な解放の出来事を一致させる。',
}
LIMITS=[
 'u0015第一文のder zuerst ... von Seiten der Regierung entschlugを、政府による良心上の自己判断への拘束から、その同じ政府側の自由へ移す公的な出来事と読む。先行する全面的な能力不足の定義を、政府だけが取り除けば全員に能力が備わるという主張へ変えない。',
 'wenigstensは少なくとも政府側の解放という限定とする。この構成は政府側だけを肯定し、家族・教会その他からも自由であることも、それらから自由ではないことも加えない。原文での限定の提示・著者帰属は後続の文統合へ残す。',
 '政府は公的運営と管轄を持つ組織、実際の活動の能動的当事者は人として分ける。h26n2でその活動における公的資格を固定し、政府の職員であるだけ、私的な活動、別政府の活動を混ぜない。',
 '解放の前で少なくとも一人には積極的な指図又は介入がある。全員が以前に不自由だったこと、前から自由な人が同じ出来事で新たに自由になったことは要求しない。ただし前で不自由な全員の同じ自由への変化・結果生成を求める。',
 '同じ活動を変化の過程かつ公的な行為として扱う。前状態・行為点・結果点を分け、行為は両端の間に置く。g3の一般的因果理論を解決したとはせず、意図・唯一原因・即時性・結果の永久継続も足さない。',
 '最初は同じ全人間比較範囲・履歴・固定集団・共通の解放内容についての最初の達成である。比較対象を今の君主の政府だけに狭めず、別政府での先行達成を調べる。唯一の最初又は唯一の原因は要求しない。評価の完備性は明示したassessed入力で供給し、無記録を不達成にしない。',
 'r5zwの存在的な共通の結果内容だけでは出来事を認定しない。r5zyは必ずr5zuの具体的政府と拘束・変化・因果を求める。既に別政府で自由があったことは、それだけで過去の解放行為の証人にはならない。',
 '本文の人類範囲と解放時の人口、同じ君主の政府・共同体・役職、具体的な比較評価基準と原文の誇張を含む主張の位置付け、称揚根拠・恩恵・感謝と一文全体の束縛は未完。本文112主張・v196・17単位判断を保存し、意味確認文字数を増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    text='d r5zj[government a community a point d] c['+both('k h237n[v government v community v point]','k h256s[v government v community v point]')+'].\n'
    text+='d r5zk[activity a government a point d] c['+both('k dg[v activity v point]','g agent a['+both('k aa[v agent]','k df[v agent v activity v point]','k h26n2[v agent v activity v government v point]')+']')+'].\n'
    target='r b[p r5y7] l[a][v person v community v matter v judgment k h26ny[v person v community v reference]] v reference v point'
    text+='d r5zl['+CHOICE+' activity a point d] c['+both('k r5zk[v activity v government v point]','k h26ho[v activity v person '+target+']')+'].\n'
    choice='k r5y5[v person v matter v judgment v reference]'
    intervention='g activity a[k r5zl['+CARGS+' v activity v point]]'
    text+='d r5zm['+CHOICE+' point d] c['+both(choice,'k r5zb['+CARGS+' v point]','u['+intervention+']')+'].\n'
    text+='d r5zn[government a community a reference d] h[a] e[i[person a][b point['+both('k r5zj[v government v community v point]',
        'k r5ze[v government v person v community v reference v point]','f matter a[f judgment a[y['+choice+'][k r5zm['+CARGS+' v point]]]]')+']]].\n'
    state=lambda point:'t[c[k r5zn[v government v community v reference]][v person]][v '+point+']'
    member='k h246c[v group v person v reference]'
    text+='d r5zo[government a group a community a reference d] e[b point['+both('k r5ty[v group v reference]','f person a[y['+member+']['+state('point')+']]')+']].\n'
    text+='d r5zp[government i[a] community i[a] reference i[d]] '+GOAL+'[o a[r[p r5zn]][v government v community v reference]].\n'
    text+='d r5zq[government a community a reference d] c[k r5zi[v government v community v reference]].\n'
    text+='d r5zr[government a person a community a reference d point d] c[g matter a[g judgment a['+both(choice,
        'x[u[k r5za['+CARGS+' v point]]]['+intervention+']')+']]].\n'
    code='k r5zp[k h223g[v government] k h223g[v community] k h223h[v reference]]'
    le=lambda a,b:'x[e[v '+a+'][v '+b+']][k ic[v '+a+' v '+b+' v candidate]]'
    personal=EPISODE.replace('group a','person a');pargs=EARGS.replace('v group','v person')
    text+='d r5zs['+personal+'] c['+both('k aa[v actor]','k aa[v person]','k r5zq[v government v community v reference]',
        'k r5zj[v government v community v first]','k th['+HISTORY+' '+BEFORE+' v activity v first v last p ag c[k r5zn[v government v community v reference]][v person]]',
        'k h257z[v reference v candidate v acted]',le('first','acted'),le('acted','last'),
        'k dg[v activity v acted]','k df[v actor v activity v acted]','k h26n2[v actor v activity v government v acted]',
        'k la[v person v activity v first v last]','k g3[v activity v person '+code+' v last]')+'].\n'
    before_checked='f person a[y['+member+'][k r5ze[v government v person v community v reference v first]]]'
    before_bound='g person a['+both(member,'k r5zr[v government v person v community v reference v first]')+']'
    changed='f person a[y['+both(member,'u['+state('first')+']')+'][k r5zs['+pargs+']]]'
    text+='d r5zt['+EPISODE+'] c['+both('k r5ty[v group v reference]',before_checked,before_bound,
        't[k r5zo[v government v group v community v reference]][v last]',changed)+'].\n'
    short=EPISODE.replace(' first d acted d','');shortargs=EARGS.replace(' v first v acted','')
    text+='d r5zu['+short+'] c[g first d[g acted d[k r5zt['+EARGS+']]]].\n'
    text+='d r5zv[actor a activity a government a person a community a reference d candidate d point d] c['+both('k r5zq[v government v community v reference]',
        'k r5yf[v actor v activity v person '+code+' v reference v candidate v point]')+'].\n'
    text+='d r5zw[reference d] h[a] e[i[group a][b point[g government a[g community a[t[k r5zo[v government v group v community v reference]][v point]]]]]].\n'
    text+='d r5zx[reference i[d]] '+GOAL+'[o a[r[p r5zw]][v reference]].\n'
    common='k r5zx[k h223h[v reference]]'
    text+='d r5zy['+FRAME+'] '+ACHIEVES+'[i[actor a activity a target a requested '+GOAL+' last d]['+both('e[v target][v group]','e[v requested]['+common+']',
        'g government a[g community a[k r5zu['+shortargs+']]]')+']].\n'
    text+='d r5zz[actor a activity a '+FRAME+' anchor d last d assessed h[a d] c] c[k rob['+HISTORY+' '+BEFORE+' p aa v group '+common+' k r5zy['+FARGS+'] v assessed v anchor v actor v activity v last]].\n'
    text+='d r5z2['+short+' anchor d assessed h[a d] c] c['+both('k r5zu['+shortargs+']',
        'k r5zz[v actor v activity '+FARGS+' v anchor v last v assessed]')+'].\n'
    return text
def build():
    doc=deepcopy(parents()[0].document);doc.update(declarations=[],statements=[]);imported={}
    roots=(['r5y5','r5y7','r5za','r5zb','r5ze','r5zi','r5ty','h246c','h26ny','h26ho','h223g','h223h'],['r5yf'],['h237n','h256s','aa','dg','df','ag','la','g3','th','h257z','ic','rob'])
    for lib,selected in zip(parents(),roots):
        for d in closure(lib.document,selected):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(p.entries) for p in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(p.source_sha256) for p in parents()))
    basis=dict(status='institutional_government_release_and_first_same_content_achievement',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
