"""Whole source readings of both transverse ray calculations."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_transverse_ray_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,SELECTIONS,LIMITS
from scripts.check_transverse_ray_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/transverse-ray-claim-v1.json'
REVIEWS=tuple(f'data/einstein-transverse-ray-u{n:04d}-review-v1.json' for n in range(73,81))
# The introductory "finden wir" includes the ensuing results, so its whole
# reading selects the entire group rather than just the consideration node.
REVIEW_SELECTIONS=((295,296,297,298,299),*SELECTIONS[1:])
CLAUSES=(
 (
  ('Auf analoge Weise finden wir ',['ei6j','zep','ei6m','ei6s','ei6v'],'同じ著者が先の縦方向と同様の計算を使って後続の式を得る提示として読む。'),
  ('durch Betrachtung von längs den beiden anderen Achsen bewegte Lichtstrahlen:',['ei6f','ei6e','ei6d','ei6c','ug'],'異なる二横軸に沿う光線を両方考察し、各々の現在の測定と全光路から後続式へ進む。'),
 ),
 (('[M0130]',['sol','soe','smh','ei6m','ei6o'],'同じy光線でη=Vτ=aV(t−vx′/(V²−v²))を得る連鎖を保つ。'),),
 (('wobei',['ei6p','ei6r','som'],'同じy光線の計算に伴う二条件を後続式で補足する接続として読む。'),),
 (('[M0131]',['som','sof','sne','skz','ei6p'],'同じ到達出来事でy/√(V²−v²)=tとx′=0を併記する。'),),
 (('also',['ei6h','ei6s','zd3','ei6u'],'この二条件を先のηの式へ代入した帰結として次の結果を提示する。'),),
 (('[M0132]',['soo','sog','sob','ei6s','ei6u'],'同じy光線の値によるη=aVy/√(V²−v²)を保持する。'),),
 (('und',['ei6v','zep','ei6x','ei6f'],'もう一方の横方向の同形の結果を、ηの計算に続く並列・類推として読む。'),),
 (('[M0133]',['soq','sog','sob','ei6i','ei6v','ei6x'],'同じz光線にその時刻条件を用い、ζ=aVz/√(V²−v²)を得る。'),),
)
# Per-unit judgments are supplied by reading, not inferred from a successful test.
READINGS=(
 dict(references='先行節点ze6の縦方向計算から、zfgの両横軸の考察、zfc/zfe/zffのηとζへ進む。yo/ypは縦軸ynと互いに異なり、各光は別の二記録へ結ぶ。',role='ugによる考察、zepによる先行計算との類推、後続のzc/zd3による式の帰結を同じ著者・論説・第三節へ帰属する。findenはこの後続結果を得る提示として全五主張と合わせて読む。',limits='原文の省略を直前と同じ零原点・正方向の光線の設定で補う。両横軸を一方だけに狭めず、実際の計算履歴や光線外の一般変換を加えない。',conventions='既存の両系全光速度ei45と全軌道eitf/se、零原点ei46、既存ug/zep/zc/zd3を組み合わせる。未説明の新原始語で考察全体を代用しない。'),
 dict(references='ηはzfb(yo)の同じ到達出来事のk横座標、τはそのk時刻、tとx′は同じ出来事のK測定から取る。aは共通のφのvでの値である。',role='現在のy光線の前提ei6gからsolを得る著者の帰結としてei6m/ei6oで提示する。前の両軸考察に続く最初のηの表示である。',limits='VτとaVの代入表示の両等号を保持し、平方根のないV²−v²を後続の横成分の分母と混同しない。ここではaを1にせず、t=τやy=ηを加えない。',conventions='soeは実切断のVτとV*smhを同じηへ等置する。smhは先行τの同じ有理式であり、全時間式smjと同じ端点のsnfへ現在の物理前提で結ぶ。'),
 dict(references='wobeiが補うのは直前の同じy光線のηの式である。ei6pは同じ前提ei6gを使い、somの時刻と補助座標の二条件を示す。',role='同じ導出に付随する条件の補足と読む。原刊では直後に二条件が置かれ、時刻値を入れた帰結alsoが続く。',limits='単語だけを独立した主張とせず、前のηの表示と次の二条件の選択を合わせる。条件を別の光線の測定や一般の時刻定義へ変えない。',conventions='同じ前提から条件を与える既存zc、閉引用som、前後順序ueと同じ著者の帰属を使う。'),
 dict(references='yとtは同じy光線のK到達値であり、x′は同じx−vt。wは同じV,vの√(V²−v²)であって、kで測る全光速Vではない。',role='ei6p/ei6rにより前のηの計算に伴う二条件として示す。二つのセミコロンを含む表示を一つの併記と読む。',limits='時刻の式とx′=0の両方を保持する。正の時刻・横距離・横成分、0≤v<Vの数値範囲と現在のv>0を保持し、零分母を許さない。',conventions='sofはt=y/w、y=w*tとx′=0を同時に表す。skzとsleは正の平方根を、sneはKのx−vtを構成する。'),
 dict(references='alsoは直前のtとx′の値から、先の同じηの式を経て後続のηの結果へ進む。ei6hは同じ光線・式・値を一つの計算前提へ結ぶ。',role='zd3による条件付きの書換えの帰結としてei6s/ei6uで提示する。原刊の短い接続語を前後の二式と合わせて読む。',limits='独立した一般的含意や条件なしの恒等式へ縮めない。同じ到達出来事と未定係数を保ち、代入を実際に行った日時や人物の追加はしない。',conventions='既存の型付き閉引用sol/sooと、実切断のsoe/sof/sog、計算の提示zd3を再利用する。'),
 dict(references='ηとyは同じy光線の別系の横座標。a,V,vと√(V²−v²)は先の式と同一であり、z側の距離を使わない。',role='ei6s/ei6uによるηの時間消去の結果であり、直前のalsoと同じ前提の下で提示する。',limits='未定aを固定せず、ηをyへ等置しない。式は選んだ光線上で得た関係として読み、これだけで全空間の座標変換を証明したとはしない。',conventions='sogは同じ到達値のηをsob=a*V*y/√(V²−v²)へ結ぶ。実切断の積と商、正の平方根、時刻消去の条件を既存定義で表す。'),
 dict(references='undは直前のηの結果と、次のζの結果を同じ両横軸の考察の下で結ぶ。ei6vはzfeからzffへの類推を持つ。',role='第二の横軸にも同様の計算を適用して得る結果の並列と読む。同じ著者による順序と、両横軸考察の参照を保持する。',limits='ηの測定値をζへそのまま転用しない。z側にも別の光線・到達出来事・同形の時刻条件を補う採用解釈を明示する。',conventions='ei6fの両軸条件、既存zepの類推とzcの帰結、同じ著者帰属とueの順序を使う。'),
 dict(references='ζとzはzfb(yp)の同じ到達出来事でのk/K横座標であり、ηとyの出来事からは分ける。a,V,vは同じ設定の共通値である。',role='ei6v/ei6xによりηの導出と同様に得る第二の横座標の結果として提示する。原刊の句点までを確認した。',limits='zにもt=z/√(V²−v²)、x′=0を用いる省略補完を明示する。未定係数を確定せず、光線外への拡張や一般的な変換の証明を加えない。',conventions='同じ軸を引数に取るsog/sobを再利用し、ei6iがz固有の現在光線と時刻条件を結ぶ。式ごとに新原始語を追加しない。'),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_transverse_ray_claim.py','tests/test_transverse_ray_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        r=READINGS[i]
        reasons=(
            s['unit']+'の固定原文全体「'+s['text']+'」を原刊900頁へ照合した。前の縦方向の式から、両横軸の説明とη・ζの式を続けて読んだ。',
            ' '.join(c['reason'] for c in clauses),r['references'],r['role'],r['limits'],r['conventions'],
            '原刊画像・固定原文とMathML・現在のNoema定義と意味規約を根拠とする。全軌道への結合、軸・時計・到達値・未定係数の対照検査と既存の有理代数証拠を補助とし、有限検査から一般実数体や物理的導出・意味同値を証明したとはしない。',
            'この単位の全範囲を、直前の原点光線と後続式の流れの中で再読した。明示した正方向の原点光線と類推の解釈の下で、上記の参照・数式・提示上の役割を選択全体が欠落なく保持すると判断する。',
        )
        assert len(reasons)==len(REQUIREMENTS);indices=list(REVIEW_SELECTIONS[i])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['正の原点光線を両横軸へ適用し、同じ形の計算を補う読みの下でのアシスタントの通読判断。独立査読や一般の物理的導出・同義性の自動証明ではない。','u0081以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for path,r in zip(REVIEWS,records()):
        assert json.loads(read(path))==r
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='both_transverse_ray_calculations_whole_units_reviewed',document=FULL,source_units={s['unit']:s['source_nonblank_characters'] for s in source_record()['segments']},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':8},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
