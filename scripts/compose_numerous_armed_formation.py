"""Unify institutional military identity, assigned readiness and exact strength."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_assigned_formation import MISSION, RELATIONS as FORMATION, DIRECTS

PARENT='data/role-commands-basis-v1.json'
OLD='examples/v016/kant-armed-readiness.noema'
OLD_BASES=('data/contextual-ability-basis-v1.json','data/assigned-formation-basis-v1.json','data/armed-readiness-basis-v1.json')
LIBRARY='examples/v016/numerous-armed-formation.noema';BASIS='data/numerous-armed-formation-basis-v1.json'
PRIMITIVES={
 'h26ve':('[a a d] b',['group','community','reference'],
  '同じ集団・対象共同体について、この固定基準で軍事的な集団の人数が多いと扱う最小人数。実際の人数や結果を見る前に比較対象と運用上の規模に即して定める文脈入力。原文に具体的な人数を補わず、単に一人以上を多数としない。1より大きいことを合成側で確認する。'),
 'h26vf':('[a d d] j[a]',['group','reference','point'],
  '同じ固定基準と評価点について、同じ集団の全構成員を列挙する名簿。実在の成員範囲はhzzmembersと照合し、名簿だけで人数を認定しない。未配置の者、失敗する者を都合よく除かず、他集団や別時点の名簿を流用しない。非空・重複なし・過不足なしは合成側で確認する。'),
}
# Existing input declarations are retained byte-for-AST; give each the explicit
# convention previously explained in grouped legacy parameter records.
LEGACY={
 'hzzoccurs':(['event','point'],'同じ出来事がこの点で生起する。計画・可能性・割当だけから生起を補わない。'),
 'hzzcommanded':(['event','group','point'],'この出来事は同じ集団の指揮の下にある活動である。別集団の活動又は単なる地理的一致と分け、指揮の法的正当性は要求しない。'),
 'hzzopponentof':(['event','point'],'同じ出来事のこの点での使用行為が向けられる相手集団。自集団との不一致と構成員は合成側で確認する。'),
 'hzzactorof':(['event','point'],'同じ出来事のこの点での一つの道具使用行為を担う人物。実際の使用と所属は別に結ぶ。'),
 'hzztargetof':(['event','point'],'同じ出来事のこの点での道具使用行為が向けられる人物。別行為の対象で代用しない。'),
 'hzztoolof':(['event','point'],'同じ出来事のこの点での使用行為に用いる道具。実際の使用と物理的な作用能力は別に結ぶ。'),
 'hzzmembers':(['group','person','point'],'同じ点でこの人物がこの集団の構成員である。準備・任務の同じ集団の範囲を指し、名簿や成功者だけに選別しない。'),
 'hzzopposes':(['group','opponent','community','point'],'同じ対象共同体に関して二集団の目的又は要求が対立する。防衛・侵攻の区別や正当性はここから導かない。'),
 'hzzinstrument':(['tool','point'],'身体の一部そのものではなく外的な物理的手段として使用する道具。これだけで武器の種類や実際の使用は断定しない。'),
 'hzzused':(['event','person','tool','point'],'同じ出来事で同じ人物が同じ道具をこの点で実際に使っている。保有や他人の使用と分ける。'),
 'hzzagainst':(['event','person','target','point'],'同じ出来事でこの人物の使用行為が同じ対象者に向けられている。対象への現実の負傷や制約は要求しない。'),
 'hzzonbehalf':(['event','community','point'],'同じ出来事が指定共同体のための活動として帰属する。帰属だけで実際の利益又は合法性を補わない。'),
 'hzzrestricted':(['tool','target','point'],'この点で同じ道具の物理的作用により、指定対象の身体的行為能力が制約されている。命令や制度上の禁止、別原因による不能と区別する。'),
}
for prefix,labels in (('tool',['operator','tool','target','method','start']),('unit',['group','community','method','start'])):
    for suffix,extra,meaning in (
      ('methods',[],'同じ設定・開始点でこの方法を実行できる。現実の実行や結果の成功は別に評価する。'),
      ('outcomes',['end'],'同じ方法と開始点の想定される結果状況の範囲。成功した結果だけを選別せず、実際の未来と同一視しない。'),
      ('selected',['end'],'同じ方法と開始点について評価対象に選ぶ結果状況。選択基準は固定し、達成に都合のよい結果だけを残さない。非空・想定結果への包含・全選択結果での達成は既存xa/xdで確認する。')):
        LEGACY['hzz'+prefix+suffix]=(labels+extra,meaning)
LEGACY.update({
 'hzyconstituted':(['institution','group','point'],'同じ制度の編成の扱いで、集団が一つの組織単位として置かれている。実際の能力や外部法体系の承認とは別。'),
 'hzyassigned':(['institution','group','community','mission','point'],'同じ制度が同じ集団に、指定共同体について閉じた記述の任務を割り当てている。任務の現在の達成や能力は含意しない。'),
 'hzyoffices':(['role','institution','group','point'],'同じ制度・集団にこの役職が置かれている。誰が保持するかと任務上の責任は別に結ぶ。'),
 'hzyholders':(['person','role','institution','group','point'],'同じ制度・集団でこの人物が同じ役職を保持する。別役職の地位、実際の発令、正当性を補わない。'),
 'hzyresponsibilities':(['role','institution','group','community','mission','point'],'同じ役職が、同じ制度・集団・対象共同体について指定された閉じた任務記述に関わる責任を持つ。別共同体や同じ真理値の別記述へ移転しない。'),
 'hzydirects':(['role','institution','group','point'],'同じ制度のこの役職には、同じ集団の指揮を担当する役割がある。別集団で指揮を担当するだけでは足りず、実際の命令、法的正当性や全指揮官の列挙は要求しない。'),
})
MEANINGS={
 'r6e6':'同じ点で軍事組織h233dである集団について、同じ指揮者・制度・対象共同体・hzzmissionの武力行使準備任務を既存rwbへ結ぶ。構成員は同じhzzmembersの非空の全員で人、指揮者も人である。役職と指揮担当は同じ制度・集団へ固定する。',
 'r6e7':'r6e6の割当と軍事的制度位置に加え、同じ集団・共同体が同じ点でhzzmissionの実際の準備能力を持つ。割当だけ、別集団の技能又は現に戦闘していることを代用しない。',
 'r6fa':'同じ集団・共同体・固定基準の閾値は1より大きく、h26vfの同じ点の名簿がhzzmembersの全成員をrcmで過不足なく非空・重複なしに列挙し、その人数が閾値以上である。名簿の水増しや成功者だけの抽出を多数としない。',
 'r6fb':'同じ指揮者・制度・集団・対象共同体・点について、r6e7の軍事的編成と準備能力、およびr6faの人数条件を合わせる。大きい集団と準備できる集団を別々に選ばない。',
 'r6fc':'同じ指揮者・集団・共同体・基準・点に、r6fbを満たす制度が一つ以上ある。制度は各要件で共通の証人であり、個別に別制度の役職・任務・指揮担当を集めない。',
 'r6fd':'同じ人物・対象共同体・固定基準に、r6fcを満たす集団が一つ以上あるという内容。軍隊の規律、手元での即応的利用、公的平穏の因果保証は後続の追加条件で、ここから自動的に導かない。',
}
LIMITS=[
 'u0017第一文zahlreiches Heerに向けた依存群。Heerは、政治的共同体の軍務を担う制度的な集団であり、指揮担当と構成員の任務があり、同じ集団が武力行使の準備能力を持つという明示的な読みで進める。既存h233dは武装警察や単なる武器保有集団と区別する。陸海軍の歴史的境界やHeerの全用法の必要十分条件を主張しない。',
 '軍事的準備の具体内容は既存rwf/hzzmissionを保持する。身体的制約を行える道具を、別の対立集団の成員へ同じ集団の指揮下で向けて使う活動の遂行能力であり、現時点の戦闘・負傷・強制の発生は要求しない。威嚇や遠隔行為の全種類を一つの作例が網羅するとはしない。',
 '同じ能力内容を任務記述にも渡すため、任務があることと能力を持つことが分離する。既存rwbの全成員に任務上の役職があるという組織化の読みを採用し、指揮担当者が兵の一人であることは課さない。外部法体系での正当性や政治的な善悪は追加しない。',
 'zahlreichは固定した文脈上の閾値に達する非空・重複なしの実人数と読む。原文に具体値はない。閾値・成員範囲を結果に合わせて変えず、名簿との一致と1を超える閾値を検査する。',
 '旧hzz/hzyの入力宣言とxa/xd/rwb/rwf等の構文は変更せず、旧資料でまとめて説明された入力関係に個別の意味規約を付ける。これは旧本文の遡及変更ではなく、現在の合成に用いる入力の明示である。',
 '規律、手元での利用、公的平穏の保証、発言可能者の限定とFreistaat、引用命令、第一文の談話・通読は未統合。本文119主張・登録簿v203・19全単位判断を保持し、意味確認文字数は加算しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def legacy():
    d=parse((ROOT/OLD).read_text(encoding='utf-8'));roots=('hzzmission','rwb',*('hzy'+n for n,_ in FORMATION[1:]+DIRECTS))
    ds=closure(d,roots);meanings={};origins={}
    for p in OLD_BASES:
        for n,m in json.loads((ROOT/p).read_text(encoding='utf-8'))['definitions'].items():
            if n in {r['name'] for r in ds if r['kind']=='definition'}:meanings[n]=m;origins[n]=p
    return ds,meanings,origins

def definitions():
    args='v commander v institution v group v community';frame='commander a institution a group a community a'
    relations='p hzzmembers '+' '.join('p hzy'+n for n,_ in FORMATION[1:]+DIRECTS)
    text='d r6e6['+frame+' point d] c['+both('k aa[v commander]','k h233d[v group v point]',
      'f person a[y[k hzzmembers[v group v person v point]][k aa[v person]]]',
      'k rwb['+args+' r[p hzzmission] v point '+relations+']')+'].\n'
    text+='d r6e7['+frame+' point d] c['+both('k r6e6['+args+' v point]','t[k hzzmission[v group v community]][v point]')+'].\n'
    members='k h26vf[v group v reference v point]';threshold='k h26ve[v group v community v reference]'
    text+='d r6fa[group a community a reference d] e[b point['+both('k hc[n p b b '+threshold+']',
      'k rcm['+members+' i[person a][k hzzmembers[v group v person v point]]]','u[k hc[d['+members+'] '+threshold+']]')+']].\n'
    text+='d r6fb['+frame+' reference d] e[b point['+both('k r6e7['+args+' v point]','t[k r6fa[v group v community v reference]][v point]')+']].\n'
    text+='d r6fc[commander a group a community a reference d] e[b point[g institution a[t[k r6fb['+args+' v reference]][v point]]]].\n'
    text+='d r6fd[commander a community a reference d] e[b point[g group a[t[k r6fc[v commander v group v community v reference]][v point]]]].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,('h233d','aa','rcm','hc')),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']};ds,meanings,origins=legacy()
    assert not set(imported)&{d['name'] for d in ds}
    doc['declarations']+=ds
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());byname={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=byname[n]['parameters'],result=byname[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=byname[n]['parameters'],result=byname[n]['result'],arguments=labels,meaning_ja=m) for n,(labels,m) in LEGACY.items()})
    prims.update({n:dict(parameters=byname[n]['parameters'],result=byname[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(old.source_sha256)|{OLD,*OLD_BASES}
    basis=dict(status='same_armed_formation_assignment_readiness_and_exact_numerosity_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|meanings|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|origins,
      legacy_input_declarations=OLD,import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
