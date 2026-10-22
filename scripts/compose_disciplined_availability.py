"""Bind normal military availability to actual roles and nonempty commands."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_described_norms import DESCRIPTION

PARENT='data/numerous-armed-formation-basis-v1.json'
OLD='examples/v016/commanded-protection.noema'
OLD_BASES=('data/unrestricted-others-basis-v1.json','data/scoped-obedience-basis-v1.json',
           'data/joint-readiness-basis-v1.json','data/commanded-protection-basis-v1.json')
LIBRARY='examples/v016/disciplined-availability.noema';BASIS='data/disciplined-availability-basis-v1.json'
PREFIX=['institution','community','reference']
PLAN=PREFIX+['commander','group','plan','anchor']
ITEM=PREFIX+['commander','group','person','plan','item','anchor']
PRIMITIVES={
 'h26vg':('[a a d a a a d] c',PLAN,
  '同じ制度・共同体・固定基準で、この指揮担当者が同じ集団にこの計画を現在の編成と指揮・連絡・資源の下で実行させられる。通常の軍務として対象になる計画を全て含め、成功する計画だけを残さない。新たな軍隊の編成、訓練、指揮担当の獲得を先に要するものは含めず、その通常の用途に間に合う実際の利用可能性とする。固定距離や秒数、現在の出動、法的正当性は含意しない。'),
 'h26vh':('[a a d a a a d d] c',PLAN+['end'],
  '同じ制度・共同体・基準・指揮者・集団・計画・開始点の通常の軍務遂行について、想定する結果状況。部隊又は各人の成功だけで結果範囲を絞らない。通常の運用という背景条件は固定基準で明示する。'),
 'h26vi':('[a a d a a a d d] c',PLAN+['end'],
  '同じ設定の通常の軍務遂行について評価する結果状況。背景条件と選択規則を先に固定し、失敗を見て除外しない。非空で想定結果に含まれ、全選択結果で全成員の命令内容が満たされることは合成側で検査する。あらゆる異常事態での成功を要求する入力ではない。'),
 'h26vj':('[a a d a a a a a d] c',ITEM,
  '同じ制度・共同体・基準・指揮者・集団・構成員・計画・開始点について選択する命令記録。履行できる命令だけを採らず、同じ人の任務上の全役職に対する要求を網羅する。待機・行為の差控えも内容になり得るが、空の記録を規律の証拠としない。'),
 'h26vk':('[a a d a a a a a d] a',ITEM,'同じ命令記録が受け手へ要求する際の役職。別の制度・軍隊・人物の役職と取り替えない。'),
 'h26vl':('[a a d a a a a a d] a',ITEM,'同じ命令記録の対象となる行為。閉じた行為記述と極性は別に結び、同じ真理値の別行為へ取り替えない。'),
 'h26vm':('[a a d a a a a a d] '+DESCRIPTION,ITEM,'同じ命令記録の閉じた行為記述。受け手と行為を適用して結果状況で評価する。引用の構文を保ち、同じ真理値の別記述との同一視をしない。'),
 'h26vn':('[a a d a a a a a d] c',ITEM,'同じ命令記録の極性。真は内容の実現、偽はその不成立を要求する。実現の成否そのものではない。'),
 'h26vo':('[a a d a a a a a a '+DESCRIPTION+' c d] c',
  PREFIX+['issuer','group','plan','recipient','role','activity','description','polarity','anchor'],
  '同じ制度・共同体・固定基準において、この計画の遂行のため同じ開始点で固定する、指定指揮者から同じ集団の同じ受け手・役職への行為記述・極性の要求。現在既に発令したという出来事とは分け、計画に従って与える要求も含む。別の計画・発令者・受け手の要求を流用せず、結果を見て免除しない。要求の合法性や受け手の賛同は含めない。'),
}
MEANINGS={
 'r6fe':'同じ制度・軍隊・共同体・人物・開始点について、この役職が置かれ、本人が保持し、同じhzzmissionの任務に責任を持つ。命令対象の役職範囲を外部の真偽入力で縮めず、既存の役職関係から導く。',
 'r6ff':'同じ指揮者・制度・軍隊・共同体・構成員・計画・固定基準・開始点の命令を既存rvf/rtyへ結ぶ内容。役職範囲はr6feで導き、全行為記述の要求網羅性と、同じ記録の妥当性・結果での履行を保つ。',
 'r6fg':'同じ人・計画・開始点の命令記録は非空であり、全選択記録の役職がr6feの同じ制度・軍隊・人物・任務の役職である。空の要求や無関係の役職だけで規律を満たさない。実際の要求と履行はr6ffが別に検査する。',
 'r6fh':'同じ指揮者・制度・軍隊・共同体・固定基準・点で、r6fbの人数と武力行使準備能力があり、全利用可能計画の全成員に非空の任務上の命令記録r6fgがあり、rutにより少なくとも一計画が利用でき、全利用可能計画の非空の全選択結果で全成員の命令内容r6ffが成立する。名簿・所属・開始点と利用可能性は全要件で共通。',
 'r6fi':'同じ指揮者・軍隊・共同体・固定基準についてr6fhを満たす制度が一つ以上ある内容。軍務の割当と準備能力、人数、規律と利用可能性に同じ制度の証人を使う。',
 'r6fj':'同じ指揮者・共同体・固定基準についてr6fiを満たす軍隊が一つ以上ある内容。人数を満たす軍隊と本人が使える規律ある軍隊を別々に選ばない。公的平穏の因果保証はこの条件だけでは得られない。',
}
LIMITS=[
 'u0017第一文wohldisciplinirtesとzur Hand hatに向けた依存群。規律は、通常の軍務の対象範囲で任務上の命令に全成員が安定して適合するという強い操作的な読み。全利用可能計画と全選択結果を要求するが、通常の範囲外の異常事態まで無例外の成功としない。訓練の履歴、服従する心理的な理由、例外の確率を別の語義として追加してはいない。',
 '手元での利用は、同じ指揮担当者が現在の編成・資源・連絡の下で通常の用途に間に合う形で実行させられることと読む。抽象的に部隊が活動できることだけでは足りず、新たな軍隊や指揮担当を獲得する可能性とは分ける。h26vgはこの実際の利用可能性の文脈入力であり、地理的距離・輸送・全伝達機構の分解までは行わない。',
 '対象計画、結果範囲と選択規則は結果から独立に固定する。役職範囲は同じ制度の実際の任務上の役職から導き、各構成員について空でない記録を要求する。待機や差控えを含むため、現実に戦闘・強制を行っている必要はない。指揮権の正当性は追加しない。',
 '旧rvf/rty/rtx/rtw/rpm/rplとrut/ruqを変更せず再利用する。要求網羅性の全記述域量化は保持する。有限診断の二記述へのインスタンス化を全域の証明とは扱わず、全域の直接実行は拒否する。',
 '旧rvhの共同体の活動可能性・保有の保護を公的平穏へ流用しない。次は同じ軍隊の利用と同じ共同体のr572の平穏を因果比較へ結ぶ必要がある。第一文全体の限定・Freistaat・引用命令・談話・通読は未完。本文119主張・登録簿v203・19全単位判断と確認文字数は変更しない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rvf','rut'));meanings={};origins={}
    for p in OLD_BASES:
        for n,m in json.loads((ROOT/p).read_text(encoding='utf-8'))['definitions'].items():
            if n in {d['name'] for d in ds if d['kind']=='definition'}:meanings[n]=m;origins[n]=p
    return ds,meanings,origins

def definitions():
    frame='commander a institution a group a community a';args='v commander v institution v group v community'
    pre='v institution v community v reference'
    member=frame+' person a plan a reference d anchor d'
    ma=args+' v person v plan v reference v anchor'
    role='k r6fe[v institution v group v community v person v role v anchor]'
    text='d r6fe[institution a group a community a person a role a anchor d] c['+both(
      'k hzyoffices[v role v institution v group v anchor]',
      'k hzyholders[v person v role v institution v group v anchor]',
      'k hzyresponsibilities[v role v institution v group v community r[p hzzmission] v anchor]')+'].\n'
    scope='i[chief a cohort a person a plan a role a anchor d]['+role+']'
    selectors=['i[chief a cohort a person a plan a item a anchor d][k '+n+'['+pre+' v chief v cohort v person v plan v item v anchor]]' for n in ('h26vj','h26vk','h26vl','h26vm','h26vn')]
    orders='i[issuer a cohort a plan a recipient a role a activity a code '+DESCRIPTION+' polarity c anchor d][k h26vo['+pre+' v issuer v cohort v plan v recipient v role v activity v code v polarity v anchor]]'
    text+='d r6ff['+member+'] e[k rvf[v commander v group v person v plan v anchor '+scope+' '+' '.join(selectors)+' '+orders+']].\n'
    itemargs=pre+' v commander v group v person v plan v item v anchor'
    item='k h26vj['+itemargs+']'
    text+='d r6fg['+member+'] c['+both('g item a['+item+']','f item a[y['+item+'][k r6fe[v institution v group v community v person k h26vk['+itemargs+'] v anchor]]]')+'].\n'
    avail='k h26vg['+pre+' v commander v group v plan v point]'
    valid='f plan a[y['+avail+'][f person a[y[k hzzmembers[v group v person v point]][k r6fg['+args+' v person v plan v reference v point]]]]]'
    goals='i[chief a cohort a person a plan a anchor d][k r6ff[v chief v institution v cohort v community v person v plan v reference v anchor]]'
    providers=['i[chief a cohort a plan a anchor d'+(' end d' if n!='h26vg' else '')+'][k '+n+'['+pre+' v chief v cohort v plan v anchor'+(' v end' if n!='h26vg' else '')+']]' for n in ('h26vg','h26vh','h26vi')]
    ready='k rut[v commander v group k h26vf[v group v reference v point] v point p hzzmembers '+goals+' '+' '.join(providers)+']'
    text+='d r6fh['+frame+' reference d] e[b point['+both('t[k r6fb['+args+' v reference]][v point]',valid,ready)+']].\n'
    text+='d r6fi[commander a group a community a reference d] e[b point[g institution a[t[k r6fh['+args+' v reference]][v point]]]].\n'
    text+='d r6fj[commander a community a reference d] e[b point[g group a[t[k r6fi[v commander v group v community v reference]][v point]]]].\n'
    return text

def build():
    p=parent();doc=deepcopy(p.document);doc['statements']=[]
    ds,means,origins=legacy();existing={d['name']:d for d in doc['declarations']}
    for d in ds:
        if d['name'] in existing:
            assert existing[d['name']]==d,d['name']
            if d['name'] in means:assert p.entries[d['name']]['meaning_ja']==means[d['name']],d['name']
        else:doc['declarations'].append(d)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in p.entries.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|{OLD,*OLD_BASES}
    basis=dict(status='same_army_normal_command_compliance_and_present_availability_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in p.entries.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in p.entries.items()}|origins,
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
