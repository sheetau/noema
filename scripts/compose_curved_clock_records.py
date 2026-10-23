"""Connect current clock displays to complete smooth paths before attribution."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_polygon_clock_claim import ROOT,read,PATH,COMPARE as POLYGON_COMPARE,rec,reading,place,elapsed
from scripts.compose_curved_clock import CURVE as OLD_CURVE,PHI
from scripts.compose_clock_transfer_records import stamp,sub,eq,path
from scripts.compose_rod_methods import interval
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,lam

PARENT='examples/v014/einstein-polygon-clock-claim.noema';PARENT_BASIS='data/polygon-clock-claim-basis-v1.json'
FULL='examples/v014/einstein-curved-clock-records.noema';CORE='examples/v014/curved-clock-records-core.noema'
BASIS='data/curved-clock-records-basis-v1.json';ANNOTATIONS='data/curved-clock-records-identifiers-v1.json'
CURVE=[p for p in PATH if p[0] not in ('segments','start','end')]+[(n,PHI) for n in ('x','y','z','vx','vy','vz')]
COMPARE=CURVE+POLYGON_COMPARE[len(PATH):]
POINT=CURVE+[(n,'a') for n in ('event','display','observed','place')]
MEANINGS={
 'ejlm':'同じ曲線の時計の現在表示ejj6を、指定した出来事・表示出来事・観測記録・場所へ結ぶ。観測記録と候補記録関数の四値、場所関数、候補指示と対象/表示の全指示を共有し、三位置が同じ記録時刻の曲線に一致する。',
 'ejln':'指定した実時刻にejlmを満たす一組の出来事・表示・観測記録・場所が存在する。四つの証人を共有し、記録の時刻も同じ値である。',
 'ejlo':'正の全K区間で同じ時計の完全な代表軌跡と校正を持ち、全現在候補が同じ曲線・記録/指示/場所関数に一致し、全実時刻にejlnの表示が存在する。測定済み標本だけへ縮めず、候補選択に指示の正しさを混ぜない。',
 'ejlp':'既存sxvのC1位置・連続速度・共通の正の光速未満の速さを、ejloの現在表示と完全な代表軌跡へ結ぶ。出発/帰着の異なる出来事と現在表示を同じ端点へ固定する。時計の遅れの法則は含まない。',
 'ejlq':'同じ曲線の運動ejlpと現在の初期同期・参照時計の全期間の残留・到着比較ejk2を結ぶ設定。初期地点が同じ場合も許し、移動時計の全期間の指示率や到着遅れを前件に追加しない。',
 'ejlr':'同じ曲線の出発と到着が正の時間を隔てる別出来事で、同じ場所と三座標位置へ帰還する。ejlbの端点条件を再利用し、空の区間列を実際の移動経路にしない。',
 'ejls':'同じ曲線の到着での現在の二指示について、非同期と移動時計の遅れ、全所要時間の厳密差、共通秒換算、二次近似と固定全所要時間の四次以上の留保をejlaへ接続する。',
 'ejlt':'同じ曲線の正の出発/帰着K時間差を正の共通換算尺度で秒へ変換した所要時間。絶対座標時刻、移動時計の指示経過、一定の周回数を代用しない。',
 'ejlu':'同じ曲線設定に、移動時計が共通速さの平方根の率、参照時計が率1で全区間を進むejkbを加え、端点の実際の指示差も同じ率へ結ぶ補足のモデル法則。幾何から加速応答を証明したものではなく、後の解釈注記用である。',
 'ejlv':'任意の曲線関数・記録/指示/場所関数・時計・速さ・二設定について、ejlqなら前段と同じ結果ejlsという内容。全関数・全実数の範囲を保持し、帰還の条件は一般の拡張へ混ぜない。',
 'ejlw':'同じ任意範囲で、曲線設定ejlqと帰還ejlrなら同じejlsという条件付き内容。出発地点に戻る閉曲線の場合の帰結を表す。',
 'ejlx':'現在の前段の折れ線結果ejlcが成立するなら、その曲線への拡張ejlvも成立するという仮定の内容。先行結果の参照名だけでなく内容へ接続する。仮定の著者帰属は後続。',
 'ejly':'同じ文脈で、前段の折れ線結果ejlcと曲線への拡張仮定ejlxを合わせた推論前提。閉曲線の帰結ejlwの提示へ接続するための内容であり、仮定が実証されたという断言ではない。',
}
LIMITS=[
 'u0128全552非空白本文文字とM0237–M0241を原刊904–905頁で通読する。今回は曲線と現在表示、同じ初期/到着比較、前段結果からの拡張仮定の意味依存群を構成する。著者の発話と地球時計比較の接続、一単位全体の意味判断は後続であり、意味確認済み件数は増やさない。',
 'stetig gekrümmte Kurveは、正のK時間区間で三位置と三速度成分が連続し、速度が位置の相対微分であるC1曲線として読む。端点は片側微分であり、繰返し周回での速度の周期性や曲率の正値までは要求しない。konstanter Geschwindigkeitは速度ベクトルの固定ではなく正の共通速さと読む。',
 '現在の対象出来事と同所表示、四座標記録、場所、唯一の指示、同じ時計の完全な代表軌跡を用いる。全現在候補の正しい対応と全実時刻での存在を分け、候補指示が正しいものだけを選んで全称条件を空にしない。',
 '同じ物理的位置への再訪と別の到着出来事を区別する。帰還時には初期の二時計が同じ出来事を共有できる。全期間の同期/静止、共通の初期指示原点、参照時計の残留、到着直後の同所比較は前段から保持する。',
 'ejk2/ejlb/ejlaは有限列・区間始終関数を本体で使わないため空列と端点定数関数で引数を接続する。曲線を零個の折れ線区間で近似したという意味ではない。前件ejlqにはejluの指示法則を混入しない。',
 '全所要時間の共通秒換算と実際の到着指示差の近似留保を前段から保持する。原文の所要時間tはejltへ接続できる。厳密率を近似残差の構成基準とする読みであり、任意の速度依存所要時間について無条件の四次誤差を主張しない。',
 'Nimmt man anの仮定、bewieseneの著者による証明済みの位置付け、so erhält manの同じ推論範囲、tの所要時間の説明、後続darausの推論、Unruhuhrの機構・完全に同じ構造・その他同条件・赤道と極・ごく小さい歩度差を後続で接続する。現在の定義追加だけを発話の全文記述として数えない。',
 '全実時刻・全曲線関数・微分と連続性を有限標本へ替えない。検査用の閉じた多項式曲線は表示との対応にだけ用い、その速さが一定とは認定しない。有限検査、原文の意味判断、加速時計の物理的真理は別である。原始記号を追加しない。',
]

def polygon_args(items):
    unused={'segments':'l[a][]','start':lam('ignored','a',v('first')),'end':lam('ignored','a',v('last'))}
    return [unused.get(n,v(n)) for n,_ in items]

def all_cases(body):
    for n,s in reversed(COMPARE):body=q('f',n,s,body)
    return body

def definitions():
    cl=v('clock');setting=v('setting');first=v('first');last=v('last');event=v('event');observed=v('observed');display=v('display');where=v('place');time=v('time')
    lo=stamp(rec(first));hi=stamp(rec(last));at=stamp(observed);inside=lambda t:k('lg',lo,hi,t)
    actual=[cl,event,display,observed,where,setting]
    text=define('ejlm',POINT,both(k('ejj6',*actual[:-1],reading(event),setting),k('sha',rec(event),'p ba'),k('shh',observed,rec(event)),op('e',where,place(event)),inside(at),*(eq(k('zc6',observed,k(axis)),app(v(component),at)) for axis,component in zip(('yn','yo','yp'),('x','y','z')))))
    witnesses=('event','display','observed','place')
    text+=define('ejln',CURVE+[('time',R)],both(k('ba',time),bind(witnesses,'a','g',both(k('ejlm',*args(POINT)),eq(at,time)))))
    every=bind(witnesses,'a','f',op('y',both(k('ejj5',*actual),inside(at)),k('ejlm',*args(POINT))))
    coverage=q('f','time',R,op('y',inside(time),k('ejln',*args(CURVE),time)))
    text+=define('ejlo',CURVE,both(k('ca',cl),k('ci',k('rb')),k('eisdf',cl,setting),k('eisdd',k('ra'),k('ta'),k('rb'),setting),k('bg',lo,hi),k('lg',*interval(k('ra'),setting),lo),k('lg',*interval(k('ra'),setting),hi),k('se',*path(cl,lo,hi,setting)),every,coverage))
    endpoints=[k('ejj7',cl,e,rec(e),place(e),reading(e),setting) for e in (first,last)]
    text+=define('ejlp',CURVE,both(k('sxv',*args(OLD_CURVE)),k('ejlo',*args(CURVE)),op('u',op('e',first,last)),*endpoints))
    text+=define('ejlq',COMPARE,both(k('ejlp',*args(CURVE)),k('ejk2',*polygon_args(POLYGON_COMPARE))))
    text+=define('ejlr',CURVE,k('ejlb',*polygon_args(PATH)))
    text+=define('ejls',COMPARE,k('ejla',*polygon_args(POLYGON_COMPARE)))
    text+=define('ejlt',CURVE+[('seconds',R)],both(k('sbg',elapsed(first,last)),k('ba',v('seconds')),q('g','scale',R,both(k('svp',v('scale'),setting),eq(v('seconds'),k('shv',v('scale'),elapsed(first,last)))))))
    rate=k('stw',k('tc'),v('speed'));one=k('bb','n p b b');rs=v('referencestart');re=v('referenceend')
    text+=define('ejlu',COMPARE,both(k('ejlq',*args(COMPARE)),k('ejkb',cl,lo,hi,reading(first),rate,setting),k('ejkb',v('reference'),lo,hi,rs,one,setting),k('ejis',rate,lo,hi,reading(first),reading(last)),k('ejis',one,lo,hi,rs,re)))
    settingrule=k('ejlq',*args(COMPARE));result=k('ejls',*args(COMPARE))
    text+=content('ejlv',all_cases(op('y',settingrule,result)))
    text+=content('ejlw',all_cases(op('y',both(settingrule,k('ejlr',*args(CURVE))),result)))
    text+=content('ejlx',op('y','t[k ejlc[]][v point]','t[k ejlv[]][v point]'))
    text+=content('ejly',both('t[k ejlc[]][v point]','t[k ejlx[]][v point]'))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==347;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_complete_curved_clock_records_and_extension_content_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/polygon-clock-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
