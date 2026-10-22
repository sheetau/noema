"""Compose a personified natural unfolding, resistant cover and directed tender care."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_covered_unfolding import FIELDS as GROWTH,COVER
from scripts.compose_dispositional_resistance import FIELDS as RESISTANCE
from scripts.compose_tender_care import RANKED

PARENT='data/germ-regime-connection-basis-v1.json';MAIN='data/civic-spirit-sentence-basis-v1.json'
LIBRARY='examples/v016/nurtured-germ.noema';BASIS='data/nurtured-germ-basis-v1.json'
GOAL='i[h[j[a]] e]'
LEGACIES=(('covered-unfolding',('rw5',)),('load-resistance',('rys',)),('dispositional-resistance',('ryu',)),('tender-care',('ryj','ryk','ryl')))
PRIMITIVES={
 'h27ax':('[a d] c',['body','reference'],'固定基準で自然の変化力を考える物体の全範囲。描写の芽だけ又は成長した物だけを選ばず、生物に限らない。概念の適用範囲であり、現実に有限個しか物体がないとはしない。'),
 'h27ay':('[a a d] c',['power','body','reference'],'同じ物体の内的な組織・構成に基づき、その物体の変化を生み得る働きのまとまり。単なる外的命令・名称・同時に存在する所有物ではなく、hzzbで作動を別に調べられる構成として指す。現在の作動や特定の結果、全外的条件からの独立は含まない。'),
 'h27az':('[a a d] c',['aggregate','power','reference'],'固定基準で、この変化力が指定された概念的なまとまりの構成要素として数えられる。物理的な包含、同一性、擬人化された行為者としての活動は別である。'),
 'h27a2':('[a d d] c',['object','reference','point'],'固定した同一個体の形成史で、対象がまだその形成の初期段階にある。任意の観測や実験の開始点というだけでは成立しない。植物専用の分類でも、全能力が未発現という条件でもない。'),
 'h27a3':('[d a d d d] c',['reference','object','start','end','point'],'固定基準と同じ対象・開始・終点に属する描写側の形成過程の全履歴。都合の悪い中間点を除かず、心理的な発達の履歴や仮想的な負荷試験と区別する。'),
 'h27a4':('[d a d d d d] c',['reference','object','start','end','earlier','later'],'同じ形成履歴での厳密な時間的先行。通常性、負荷の大きさ、本文順序ではない。ta/tgで履歴全体の全順序と両端を検査する。'),
 'h27a5':('[d a d d] c',['reference','process','start','end'],'同じ描写過程がこの開始と終点を結ぶ状態移行。日付の順序だけでは代用せず、対象への関与は別に結ぶ。'),
 'h27a6':('[d a a d d] c',['reference','process','object','start','end'],'同じ開始と終点の間で、指定過程が同じ対象の変化を構成する。別対象の変化や偶然の同時性を含めない。'),
 'h27a7':('[d a a] c',['reference','object','feature'],'固定基準で、この植物体の初期段階から展開する構造・生育機能の全関連範囲。実際に発現したものだけで選ばず、人の二性向の識別子とも区別する。'),
 'h27ba':('[d a a d] c',['reference','object','feature','point'],'同じ植物体の内部に、指定構造・生育機能が発現し得る構成がある。単なる論理的可能性や、外から別個体を取り付ける見込みとは分ける。'),
 'h27bb':('[d a a d] c',['reference','object','feature','point'],'同じ植物体で指定構造・生育機能が顕在化している。能力一般の最大化や、芽が覆いを破って外へ出ることは含めない。'),
 'h27bc':('[a a d] c',['cover','object','point'],'物体の外側に別の物体の層が被さり、その内側に対象が収まっている。上下の高さだけ、近接、別対象の被覆とは区別する。密閉・防護効果・材質・硬さ・破裂は要求しない。'),
 'h27bd':('[d a] j[a]',['reference','actor'],'固定基準で同じ行為者の世話の比較に入る対象の完全な有限列。成功や好意から選び直さず、指定範囲との過不足・空・重複はrylで拒否する。'),
 'h27be':('[d a a] c',['reference','actor','object'],'同じ行為者が世話する植物体を比べる文脈上の全範囲。描写の芽一つだけへ都合よく縮めず、評価時点ごとに変えない。無限比較の測度ではなく有限範囲を明示する。'),
 'h27bf':('[d a a '+GOAL+' j[a] d] c',['reference','actor','act','goal','bindings','point'],'同じ行為者がこの行為の計画・遂行で、渡した閉じた目標を同じ順序付き対象列へ適用した内容を目指す。原語や任意の成功記号で目的内容を代用せず、目標の実際の成立・達成可能性を含意しない。'),
 'h27bg':('[a a d] c',['actor','object','point'],'行為者が同じ対象へ向ける肯定的な感情的受容。利便・管理・利用価値・道徳的正しさだけからは導かない。自然の描写に使う場合も、描写外に現実の感情を主張しない。'),
 'h27bh':('[a a d] c',['actor','object','point'],'同じ行為者・対象・時点の感情的受容の強さを共通尺度で評価できる。未評価をゼロとして補わない。'),
 'h27bi':('[a a d] b',['actor','object','point'],'評価済みの同じ感情強度を共通の非負有理数尺度で与える。原文の数値ではなく順序を表すモデル入力であり、比較範囲で同じ順序保存変換を許す。'),
 'h27bj':('[a a a d d] c',['power','process','object','start','end'],'この内的構成の作動が、同じ対象・形成過程・開始と終点における変化へ実際に因果的に寄与する。単なる同時性・後続・過程の命名と分け、唯一又は十分な原因とはしない。'),
 'h27bk':('[d a] j[a]',['reference','object'],'固定基準と同じ覆いの変形抵抗を調べる試験の完全な有限列。成長時点又は試験成功から選び直さない。'),
 'h27bl':('[d a a] c',['reference','object','test'],'同じ覆いと固定基準に適用する全試験の範囲。列との一致、非空、重複の不在はryu/rcmで要求する。'),
 'h27bm':('[d a] a',['reference','object'],'同じ覆いについて先に固定した負荷の方向・与え方・支持・基準形状・観測時点・温度などの試験方法。異なる方法を同じ測定へ無言で混ぜない。'),
 'h27bn':('[d a] a',['reference','object'],'同じ試験に使う荷重の力の単位。変形長さの単位とは役割を分け、結果に応じて変えない。'),
 'h27bo':('[d a] a',['reference','object'],'同じ試験に使う変形長さの単位。物体の剛体移動量で変形を代用せず、負荷と変形の両読みを同じ単位組へ結ぶ。'),
 'h27bp':('[d a] b',['reference','object'],'同じ負荷単位での正の荷重下限。語義を調べる文脈的基準であり、原文に数値を補わない。正性はrysで要求する。'),
 'h27bq':('[d a] b',['reference','object'],'同じ変形単位での許容変形量の非負上限。試験方法に即した小さい変形の基準であり、工学的硬さの規格値や不変形一般を意味しない。'),
 'h27br':('[d a a a a a d] c',['reference','object','test','protocol','loadunit','deformationunit','candidate'],'同じ候補状況で、この物・試験・方法・力単位・変形長単位に荷重と変形の両読みが適合して評価済みである。現実の評価点で試験済みであることは別である。'),
 'h27bs':('[d a a a a a d] b',['reference','object','test','protocol','loadunit','deformationunit','candidate'],'同じ候補状況と指定試験・方法・単位組における荷重の有理数の読み。未評価の測定をゼロへ補わない。'),
 'h27bt':('[d a a a a a d] b',['reference','object','test','protocol','loadunit','deformationunit','candidate'],'同じ候補状況と指定試験・方法・単位組における、基準形状からの非負の変形長さの読み。最大変形・残留変形等の選択は方法で固定する。'),
 'h27bu':('[d a a a a a d d] c',['reference','object','test','protocol','loadunit','deformationunit','anchor','candidate'],'同じ物の評価点の構成と関連背景を保ち、指定試験法で負荷した場合として採用する全候補。成功だけを選ばず、別の物・方法・単位に替えない。候補の完全性と物理的適合は解釈入力であり、実際の負荷を含意しない。'),
}
MEANINGS={
 'r6jf':'指定された概念的まとまりの要素が、同じ固定基準の全物体の内的変化力であることと一致し、少なくとも一つの要素がある。自然を内的な変化力の全体として捉える読みで、名称qbだけに意味を委ねない。',
 'r6jg':'同じ対象が形成初期にある植物体であり、非空の全関連構造・生育機能が内部に潜在する。Keimの植物側を、種を固定しない形成初期の個体として構成する。未発現と実際の展開はrw5で別に結ぶ。',
 'r6jh':'同じ植物体の同じ全履歴における、開始と終点を含む形成区間。心理的な履歴・仮想的負荷の候補・区間外と区別する。',
 'r6ji':'同じ固定基準の一個体列について、その植物体の非空の全関連構造・生育機能が発現しているという発達目標。空・多対象列では成立せず、同じ目的記述を各対象へ別々に適用できる。',
 'r6jj':'固定基準の閉じた呼称をr6jiへ適用した閉じた目的記述。作成と目的志向への受渡しでは発達目標を実行評価しない。',
 'r6jk':'同じ覆い・固定基準の全試験と方法・単位・閾値をryuへ渡し、指定評価点から負荷した場合の非空の全候補で、十分な負荷にも変形が小さいことを要求する。実際の負荷や試験済みを要求しない。',
 'r6jl':'同じ行為者・植物体・固定基準・時点で、その植物体のr6jjの発達を目的とする世話と肯定的感情を、固定比較範囲内で最大の強度へ結ぶ。ryjの行為・行為者順を現行dfの行為者・行為へ明示的に変換し、目的成功は要求しない。',
 'r6jm':'同じ自然のまとまり・植物の芽・覆い・過程・開始と終点を結び、rw5による潜在性からの展開と区間全体の被覆・抵抗性を要求する。その植物の内的変化力の一つが同区間で作動し同じ変化へ寄与し、擬人化側で自然が展開行為へ参加する。全区間に同じ自然から同じ芽へのr6jlの世話も結ぶ。',
 'r6jn':'同じ自然・芽・覆い・固定基準・開始点から、指定終点までにr6jmの展開過程があるという描写内容。植物側の過程や時点を対象側の心理的過程と物理的に同一視しない。',
 'r6jo':'同じ自然・芽・覆い・固定基準について、指定終点までにr6jnの開始点がある描写内容。後続する非字義的提示へ渡すための内容であり、現実の自然の意志・感情・植物の実在を無条件に主張しない。',
}
LIMITS=[
 'u0017第四文前件の描写側を構成する依存群。自然を、物体の内的構成に基づく変化力の全体として捉え、展開と世話をする働き手として描く。閉じた描写内容へ結ぶ段階であり、対象側r6jdとの比喩対応・全文帰属は次に統合する。',
 '保存したAdelungのNaturとKeimの1811年版転記を語義候補の比較に使う。原文より後であり、原刊画像を再照合したものでも、カントの唯一の意味を辞書が証明したものでもない。Keimは形成初期の植物体として描き、特定の種・種子だけの由来・覆いの破裂・外部への発芽を補わない。',
 '内的変化力は物体の構成に根ざす機能的な因果能力として公開規約を与え、作動・同じ変化への寄与・全体への所属を別に合成する。生物学・因果同定・自然哲学の一般理論への還元を要求せず、物体範囲や形成史を成長成功に応じて変えない。',
 '硬さは同じ覆い・固定方法・単位・閾値の下での小さい変形という操作的な読み。現実に試験済みとはしない。適切な負荷条件・候補の完全性・較正はモデル入力であり、特定の工学規格、任意の力での不変形、破壊強度へ拡張しない。',
 '世話の目的は同じ対象の内在的な構造・機能の発達として実際のNoema内容へ構成する。感情と目的は擬人化内部だけに置く。am zärtlichstenを固定された有限の植物比較範囲内の最大として読み、同率と一対象の範囲を許すが成功による範囲縮小は許さない。強調だけの絶対最上級という別読解は採らない。',
 '世話は形成区間の全時点に要求し、その都度の行為は異なってよい。展開行為と世話行為を必ず同じとはしない。描写として強い継続の読みであり、区間外にも永続する世話や、目標が達成可能であることを含めない。',
 '旧generic ryjはperforms(act,actor,point)、現行dfはdf(actor,act,point)である。旧iawcareとiagdepictionの直接接続はこの順序を反転していたため継承せず、新しいラムダと直接呼出で正す。旧定義・証拠は保存し、その旧接続を意味判断の根拠に使わない。',
 'この依存群だけから第四文全体の意味確認を追加しない。同じ低い制度と覆い、二性向と芽、自然の作用の対象側への対応、条件文の量化、反作用・行為能力・政府・尊厳・著者注参照が残る。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def main_catalog():return load_catalog(ROOT,MAIN)
@lru_cache(None)
def legacy():
    rows={};meanings={};paths=[]
    for stem,roots in LEGACIES:
        path='examples/v016/'+stem+'.noema';basis='data/'+stem+'-basis-v1.json';paths += [path,basis]
        old=parse((ROOT/path).read_text(encoding='utf-8'));ms=json.loads((ROOT/basis).read_text(encoding='utf-8'))['definitions']
        for row in closure(old,roots):
            n=row['name']
            if n in rows:assert rows[n]==row,n
            else:rows[n]=row
            if n in ms:meanings[n]=(ms[n],basis)
    return list(rows.values()),meanings,paths

def definitions():
    power='g body a['+both('k h27ax[v body v reference]','k h27ay[v power v body v reference]')+']'
    text='d r6jf[nature a reference d] c['+both('g power a['+power+']','f power a[e[k h27az[v nature v power v reference]]['+power+']]')+'].\n'
    features='k h27a7[v reference v object v feature]'
    text+='d r6jg[reference d object a point d] c['+both('k h225t[v object v point]','k h27a2[v object v reference v point]',
      'g feature a['+features+']','f feature a[y['+features+'][k h27ba[v reference v object v feature v point]]]')+'].\n'
    ctx='v reference v object v start v end';interval=both('k h27a3['+ctx+' v point]',
      'x[e[v point][v start]][k h27a4['+ctx+' v start v point]]','x[e[v point][v end]][k h27a4['+ctx+' v point v end]]')
    text+='d r6jh[reference d object a start d end d point d] c['+interval+'].\n'
    goal=both('e[v bindings][l[a][v object]]','k h225t[v object v point]','g feature a['+features+']',
      'f feature a[y['+features+'][k h27bb[v reference v object v feature v point]]]')
    text+='d r6ji[reference d] h[j[a]] e[i[bindings j[a]][b point[g object a['+goal+']]]].\n'
    text+='d r6jj[reference i[d]] '+GOAL+'[o a[r[p r6ji]][v reference]].\n'
    fixed=dict(object='v cover',context='v point',tests='k h27bk[v reference v cover]',scope='i[test a][k h27bl[v reference v cover v test]]')
    for n,symbol in zip(('protocol','loadunit','deformationunit','minimum','maximum'),('h27bm','h27bn','h27bo','h27bp','h27bq')):fixed[n]='k '+symbol+'[v reference v cover]'
    for n,symbol,tail in (('assessed','h27br',''),('load','h27bs',''),('deformation','h27bt',''),('prospects','h27bu',' candidate d')):
        fixed[n]='i[object a test a protocol a loadunit a deformationunit a anchor d'+tail+'][k '+symbol+'[v reference v object v test v protocol v loadunit v deformationunit v anchor'+(' v candidate' if tail else '')+']]'
    text+='d r6jk[reference d cover a point d] c[k ryu['+' '.join(fixed[n] for n,t in RESISTANCE)+']].\n'
    code='k r6jj[k h223h[v reference]]'
    fixed=dict(actor='v nature',object='v object',context='v point',objects='k h27bd[v reference v nature]',
      scope='i[item a][k h27be[v reference v nature v item]]',goals='i[item a]['+code+']',
      goalfor='i[item a goal '+GOAL+' context d]['+both('e[v goal]['+code+']','k h225t[v item v context]','g feature a[k h27a7[v reference v item v feature]]')+']',
      aims='i[actor a act a goal '+GOAL+' bindings j[a] context d][k h27bf[v reference v actor v act v goal v bindings v context]]',
      occurs='p dg',performs='i[act a actor a context d][k df[v actor v act v context]]',affection='p h27bg',classified='p h27bh',degree='p h27bi')
    text+='d r6jl[reference d nature a object a point d] c['+both('e[s[k h223h[v reference]]][v reference]',
      'k ryl['+' '.join(fixed[n] for n,t in RANKED)+']')+'].\n'
    scope='v reference v germ v start v end'
    fixed=dict(object='v germ',process='v process',start='v start',end='v end',cover='v cover',
      history='i[point d][k h27a3['+scope+' v point]]',before='i[left d right d][k h27a4['+scope+' v left v right]]',
      transitions='i[process a first d last d][k h27a5[v reference v process v first v last]]',
      affected='i[process a object a first d last d][k h27a6[v reference v process v object v first v last]]',
      features='i[feature a][k h27a7[v reference v germ v feature]]',
      latent='i[object a feature a point d][k h27ba[v reference v object v feature v point]]',
      manifest='i[object a feature a point d][k h27bb[v reference v object v feature v point]]',
      surrounds='p h27bc',resistant='i[cover a point d][k r6jk[v reference v cover v point]]')
    power=both('k h27az[v nature v power v reference]','k h27ay[v power v germ v reference]',
      'g point d['+both('k r6jh['+scope+' v point]','k hzzb[v power v point]')+']',
      'k h27bj[v power v process v germ v start v end]')
    text+='d r6jm[reference d nature a germ a cover a process a start d end d] c['+both('k r6jf[v nature v reference]',
      'k r6jg[v reference v germ v start]','k rw5['+' '.join(fixed[n] for n,t in GROWTH+COVER)+']','g power a['+power+']',
      'k dg[v process v end]','k df[v nature v process v end]',
      'f point d[y[k r6jh['+scope+' v point]][k r6jl[v reference v nature v germ v point]]]')+'].\n'
    text+='d r6jn[reference d nature a germ a cover a start d] e[b end[g process a[k r6jm[v reference v nature v germ v cover v process v start v end]]]].\n'
    text+='d r6jo[reference d nature a germ a cover a] e[b end[g start d[t[k r6jn[v reference v nature v germ v cover v start]][v end]]]].\n'
    return text

def build():
    p=parent();m=main_catalog();doc=deepcopy(p.document);doc['statements']=[];imported=dict(p.entries)
    ds,means,paths=legacy()
    for d in closure(m.document,('h225t','hzzb','df','dg','h223h','rcm','hc'))+ds:
        n=d['name']
        if n in imported:assert d==imported[n]['declaration'],n
        else:
            doc['declarations'].append(d)
            if n not in means:assert d==m.entries[n]['declaration'];imported[n]=m.entries[n]
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(m.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(paths)|set(p.source_sha256)|set(m.source_sha256)
    basis=dict(status='nurtured_germ_inside_resistant_cover_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|{n:r[0] for n,r in means.items()}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{n:r[1] for n,r in means.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
