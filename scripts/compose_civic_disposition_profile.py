"""Compose empirical dispositions and a fixed weighted profile trajectory."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-spirit-sentence-basis-v1.json'
LIBRARY='examples/v016/civic-disposition-profile.noema';BASIS='data/civic-disposition-profile-basis-v1.json'
TRUE='e[n p a b][n p a b]';ZERO='n p a b'
SCOPE='community a reference d';ARGS='v community v reference'
PAIR=ARGS+' v person v feature'
MEMBER='k r6hd[v person v community v reference]'
FEATURE='k h27b7['+PAIR+']'
PRIMITIVES={
 'h27b5':('[a d] j[a]',['community','reference'],'固定した共同体・比較基準で対象にする全人間成員の有限列。r6hdとの一致・非空・重複なしをr6jzで検査する。変化した人だけを選ばず、評価点や変化の成否を選択引数にしない。'),
 'h27b6':('[a d a] j[a]',['community','reference','person'],'固定基準でこの本人について比較する心的応答特徴の全有限列。同じ人の感情・欲求・動機・構えの現れ方を対象にし、思考課題への正答だけへ限定しない。列の完全性はh27b7に対して検査する。'),
 'h27b7':('[a d a a] c',['community','reference','person','feature'],'この比較で固定した本人の心的応答特徴の全範囲。特徴は、何に直面したときのどの感情的・動機的応答かという判定条件を伴う。同名ラベルを真にする入力ではなく、実際の応答はh27cf、傾向はr6jyで別に扱う。異なる特徴の重複・細分化による重みの変更は同じ比較の途中で行わない。'),
 'h27ca':('[a d a a d d] c',['community','reference','person','feature','anchor','candidate'],'同じ本人・特徴・基準点の応答傾向を調べる比較場面の全範囲。刺激・状況の変動を含め、応答の成否から範囲を選ばない。全基準点で同じ特徴の判定条件を用いる。'),
 'h27cb':('[a d a a d d] c',['community','reference','person','feature','anchor','candidate'],'この比較場面で、基準点の本人の関連した心理的構成を保持する。新たな訓練や別人の傾向へ交換しない。比較する二時点の心理的構成自体を同一にする要求ではない。'),
 'h27cc':('[a d a a d] c',['community','reference','person','feature','candidate'],'この比較場面で、同じ特徴の判定に関わる刺激・対象又は局面へ本人が直面し、その応答が現れ得る。応答の成立・活動の実行・成功とは分ける。'),
 'h27cd':('[a d a a d d d] c',['community','reference','person','feature','anchor','preferred','other'],'同じ比較で背景・刺激・妨害などからpreferredをotherより通常とする厳密な優先関係。応答の成否で優先を定めない。rqt4で非反射性・推移性・極小候補への到達を検査する。'),
 'h27ce':('[a d a a d d] c',['community','reference','person','feature','anchor','candidate'],'同じ比較場面で、指定特徴の心的応答について入力が判明し評価できる。未評価を無反応や無傾向へ変えない。'),
 'h27cf':('[a d a a d] c',['community','reference','person','feature','candidate'],'この場面で、本人が指定特徴の判定条件に合う感情・欲求・動機・構えの応答を示す。例えば想起した活動への好意、危険に直面した恐れ、外的指示への迎合などの個別応答を同じ基準で判定する。単発の応答から傾向・能力・道徳的原則を単独では導かない。'),
 'h27cg':('[a d a a] b',['community','reference','person','feature'],'本人と応答特徴の組に比較の前から割り当てた正の有理重み。心理的な善さの得点ではなく変化量の比較尺度であり、結果による再重み付けをしない。人や特徴の数による寄与差はこの公開尺度の一部。'),
 'h27ch':('[a d d d d] c',['community','reference','start','end','point'],'同じ共同体・固定基準・両端に対応する全比較履歴の時点範囲。急な変化がある時点を除いて滑らかに見せる抽出をしない。各介入の履歴を接続するときにも元の基準を保持する。'),
 'h27ci':('[a d d d d d] c',['community','reference','start','end','left','right'],'同じ全履歴でleftがrightより先である順序。taで範囲内の厳密な全順序を要求する。通常性の優先関係とは別。'),
 'h27cj':('[a d] b',['community','reference'],'同じ比較尺度で一段階に許す変化量の正の上限。履歴の分解能とともに先に固定し、実際に観測した最大の飛躍に合わせて拡大しない。時間当たりの物理的速度そのものではない。'),
}
MEANINGS={
 'r6jx':'固定した本人・応答特徴について、全比較場面で心理的基盤の保持・局面への直面・入力の判明を要求し、非空で整った通常性の比較を確認する。応答傾向の真偽とは独立した評価条件。',
 'r6jy':'r6jxを満たす同じ比較の全ての極小通常場面で、本人が同じ特徴の応答を示す傾向。例外場面での不成立を許し、現実の基準点で実際に応答したことは要求しない。',
 'r6jz':'同じ民衆の全人間成員と各人の全応答特徴を非空・重複なしで列挙し、各組の固定重みが正であることを要求する。個人の出入りや特徴の選び直しで変化を作らない。',
 'r6j2':'同じ全成員・特徴の組について、二点でr6jyの真偽が異なる場合だけ固定重みを加える距離。真の個数の差とは異なり、増加と減少が相殺しない。妥当性はr6j3と組み合わせて要求する。',
 'r6j3':'r6jzと、始点・終点を含む全順序の履歴を確認し、両端を含む区間内の全員・全特徴・全点でr6jxを要求する。欠けた評価から偽の傾向を作らない。',
 'r6j4':'同じ有効な比較区間で、始点と終点の心的応答傾向の組が正の距離だけ変化する。方向・善さ・単調性・原因をこれだけで断定しない。',
 'r6j5':'r6j4の変化について固定した正の段階上限を用い、上限より大きく異なる任意の順序付き二点の間に、両端それぞれへ正で元の距離より小さい距離を持つ中間点を要求する。全区間にもそのような中間を一つ要求する。停滞や局所的な逆行を許し、大飛躍を同じ状態の時点追加だけで隠さない。',
 'r6j6':'同じ共同体・基準の本人と特徴を引数として残した、r6jyによる心的応答傾向の内容族。後続の因果比較へ同じ性質を渡す入口であり、成長や条件文全体を断定する文ではない。',
}
LIMITS=[
 'Sinnesart des Volksを、同じ民衆各人の経験的な感情・動機・構えに関する応答傾向の組として読む。感覚器官だけ、理由ある判断の正答数だけ、普遍的な道徳原則の確立だけへ限定しない。',
 '比較基準の全成員と全関連特徴を有限に固定し、全員の変化や多数派を要求しない。特徴の選定・重み・段階上限は公開する解釈入力であり、原文が数値や心理測定法を指定しているとはしない。全ての心理状態の完全な尺度を得たとも主張しない。',
 'r6j5は、固定した特徴尺度で分解できる漸次的変化の読み。二値特徴が粗すぎて中間を表せない場合には成立せず、基準の解像度の妥当性を改めて検討する。一回の変化を同じ状態の時点追加だけで漸次的にはしない。局所的逆行・同じ総件数での特徴交換を許す。',
 '旧ianresponse/ianchangeの理由ある判断に限定した単調な件数増加は、今回のSinnesartの全内容としては採用しない。旧候補とその検証証拠は保存する。',
 'AdelungのSinnの語義と後年のカントAA VII 285–286を比較資料として保存した。後年のTemperament分類を1784年の原文の唯一の意味へ遡及させず、先天的な気質だけへ限定もしない。',
 '今回は心的傾向の内容とその変化の条件。wirkt zurükの因果的な寄与と対象への戻り、allmähligが作用過程にかかること、前件・後件の人口と時点の量化、行為能力以降の統合は残る。プロフィールが変わっただけで前件の作用を証明したとはしない。全文判断と意味確認文字数は増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    fixed=PAIR+' v anchor';selected='k h27ca['+fixed+' v scene]'
    cases='i[scene d]['+selected+']';order='i[left d right d][k h27cd['+fixed+' v left v right]]'
    checked=both('k h27cb['+fixed+' v scene]','k h27cc['+PAIR+' v scene]','k h27ce['+fixed+' v scene]')
    text='d r6jx['+SCOPE+' person a feature a anchor d] c['+both(MEMBER,FEATURE,
      'f scene d[y['+selected+']['+checked+']]','k rqt4['+cases+' '+order+' i[scene d]['+TRUE+']]')+'].\n'
    text+='d r6jy['+SCOPE+' person a feature a anchor d] c['+both('k r6jx['+fixed+']',
      'k rqt4['+cases+' '+order+' i[scene d][k h27cf['+PAIR+' v scene]]]')+'].\n'
    pop='k h27b5['+ARGS+']';features='k h27b6['+ARGS+' v person]'
    each=lambda body:'f person a[y['+MEMBER+'][f feature a[y['+FEATURE+']['+body+']]]]'
    text+='d r6jz['+SCOPE+'] c['+both('k rcm['+pop+' i[person a]['+MEMBER+']]',
      'f person a[y['+MEMBER+'][k rcm['+features+' i[feature a]['+FEATURE+']]]]',
      each('k hc['+ZERO+' k h27cg['+PAIR+']]'))+'].\n'
    diff='u[z[k r6jy['+PAIR+' v left]][k r6jy['+PAIR+' v right]]]'
    inner='q['+features+']['+ZERO+'][i[subtotal b feature a][k ha[v subtotal k hb[k h27cg['+PAIR+'] k hd['+diff+']]]]]'
    text+='d r6j2['+SCOPE+' left d right d] b[q['+pop+']['+ZERO+'][i[total b person a][k ha[v total '+inner+']]]].\n'
    hist='i[point d][k h27ch['+ARGS+' v start v end v point]]'
    before='i[left d right d][k h27ci['+ARGS+' v start v end v left v right]]'
    inside=lambda point:'c[k rlz['+hist+' '+before+' v start v end]][v '+point+']'
    text+='d r6j3['+SCOPE+' start d end d] c['+both('k r6jz['+ARGS+']','k ta['+hist+' '+before+']',
      'k h27ch['+ARGS+' v start v end v start]','k h27ch['+ARGS+' v start v end v end]',
      'k h27ci['+ARGS+' v start v end v start v end]',
      'f point d[y['+inside('point')+']['+each('k r6jx['+PAIR+' v point]')+']]')+'].\n'
    dist=lambda l,r:'k r6j2['+ARGS+' v '+l+' v '+r+']'
    prior=lambda l,r:'k h27ci['+ARGS+' v start v end v '+l+' v '+r+']'
    text+='d r6j4['+SCOPE+' start d end d] c['+both('k r6j3['+ARGS+' v start v end]','k hc['+ZERO+' '+dist('start','end')+']')+'].\n'
    middle=lambda l,r:'g middle d['+both(inside('middle'),prior(l,'middle'),prior('middle',r),
      *['k hc['+ZERO+' '+d+']' for d in (dist(l,'middle'),dist('middle',r))],
      *['k hc['+d+' '+dist(l,r)+']' for d in (dist(l,'middle'),dist('middle',r))])+']'
    large=both(inside('left'),inside('right'),prior('left','right'),'k hc[k h27cj['+ARGS+'] '+dist('left','right')+']')
    text+='d r6j5['+SCOPE+' start d end d] c['+both('k r6j4['+ARGS+' v start v end]',
      'k hc['+ZERO+' k h27cj['+ARGS+']]','f left d[f right d[y['+large+']['+middle('left','right')+']]]',middle('start','end'))+'].\n'
    text+='d r6j6['+SCOPE+'] h[a a] e[i[person a feature a][b anchor[k r6jy['+PAIR+' v anchor]]]].\n'
    return text

def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('r6hd','rqt4','rcm','ta','rlz','hb')),statements=[])
    imported={d['name']:p.entries[d['name']] for d in doc['declarations']}
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(p.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='fixed_empirical_disposition_profile_and_trajectory_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(parent().source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
