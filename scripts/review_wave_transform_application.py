"""Whole-unit readings of the wave inquiry, transformation displays and gloss."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_wave_transform_application import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_wave_transform_application import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/wave-transform-application-v1.json'
FIRST_SOURCE='data/einstein-wave-inquiry-reading-v1.json';FIRST_DOC='docs/wave-inquiry-v1.md'
REVIEWS=['data/einstein-wave-transform-u'+str(n).zfill(4)+'-review-v1.json' for n in range(182,188)]
DETAILS=[
 ('問いと両変換の適用','先行の同じ波をkに静止する観測者が調べる条件で性質を問う。続けて第六節の電気・磁気の最終場変換と第三節の座標・時刻の最終変換を適用し、直接次の表示を得るという著者の提示を保つ。','第一文のWir fragenは同じ仮定の質問族へのeisse、後半は同じ割当の適用条件と結果へのeissg、両先行節は別々のeisov、コロンは後続表示へのufとueに接続する。'),
 ('六つの変換後成分','X′とL′の縦成分を保ち、Y′=β(Y0−vN0/V)sinΦ′、Z′=β(Z0+vM0/V)sinΦ′、M′=β(M0+vZ0/V)sinΦ′、N′=β(N0−vY0/V)sinΦ′を同じ位相で結ぶ。電気側と磁気側、符号、交差相手を保つ。','直前の両変換の適用によって得る表示の六成分として、同じ結果内容ekcnへeisoxで結ぶ。別の波や実測結果の追加ではない。'),
 ('変換後の共通位相','Φ′=ω′(τ−(a′ξ+b′η+c′ζ)/V)の等式を、旧位相を同じ逆座標写像へ適用した関数へ結ぶ。空間三項全体をVで割り、ω′を括弧全体に掛ける。','直前の六成分と一組の七表示式として、同じ新座標で使う位相を明示する。末尾のコンマで次のパラメータの補足へ続く。'),
 ('wobeiの補足開始','直前の変換後の表示で使う同じω′とa′,b′,c′について、続く四式を指定する補足の開始として読む。独立の別の波の仮定にしない。','同じ結果ekcnを保持してekcoとして明示するeissb、表示への内容対応eisox、同じ表示からの説明関係ufを使い、後続M0327とgesetzt ist.と一つの補足にする。'),
 ('四つの変換パラメータ','ω′=ωβ(1−av/V)、a′=(a−v/V)/(1−av/V)、b′=b/[β(1−av/V)]、c′=c/[β(1−av/V)]という四式を同じV,v,ω,a,b,cで指定する。横軸の二式へ同じβと分母を用いる。','wobeiで導入された同じ表示のパラメータ指定としてekclのsdq2へ結ぶ。四つの新値は同じ入力から構成し、既知の答え又は別の測定記録を補わない。'),
 ('gesetzt istの指定完結','wobeiに始まる同じ補足を、前に置かれた四つの式でω′とa′,b′,c′を指定したものとして完結する。過去に実験を実行したという意味にはしない。','同じパラメータ補足の内容ekco、表示への対応、先行表示の同じ設定の明示を著者へ帰属する。語だけを独立した真偽命題にせず、M0327とwobeiの範囲を共有する。'),
]

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,FIRST_SOURCE,FIRST_DOC,*DEPENDENCIES,'scripts/review_wave_transform_application.py','tests/test_wave_transform_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,FIRST_SOURCE,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        title,meaning,presentation=DETAILS[i]
        if i==0:
            clauses=[dict(range=[0,144],text=s['text'][:144],statements=[366],definitions=['ekb3','ekb4','ekb5','ekb7','ekca','ekcd','eisse'],reason='同じ波の仮定と観測者の静止・調査条件を固定し、その物理的な二場の記述を著者が実際に問う。仮定を現実の実験報告に変えず、候補ごとに別の波を選び直さない。'),dict(range=[144,len(s['text'])],text=s['text'][144:],statements=[367],definitions=['ekci','ekcl','ekcp','ekcq','ekcr','eissg','eisov','ejvm','ejeh'],reason=meaning+' '+presentation)]
        else:
            symbols=['ekck','ekcn','ekcs','ekcu','s6k','s6l','s6f','seat'] if i in (1,2) else ['ekcl','ekco','ekcv','ekcx','sdq2','sdn2','sdo2','sdp2','eissb']
            clauses=[dict(range=s['range'],text=s['text'],statements=s['statements'],definitions=symbols,reason=meaning+' '+presentation)]
        assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
        reasons=[
          f'固定原文{s["unit"]}の全範囲と数式要素を保存本文・MathML・原刊911頁へ照合した。u0182の冒頭は先の910–911頁の照合も引き継ぐ。今回の対象は{title}であり、前後の表示と補足から切り離さず全体を再読した。',
          meaning,
          '同じK/k、V/v、長さ時間と二場の単位、波・源・過程・領域・近似の割当を保つ。先行35役割と観測者6役割の条件・結果を共有し、37存在証人を内容の断片ごとに別々に選ばない。M0325、M0326、M0327の区別も保存した在庫で確認した。',
          presentation,
          '実際の物理場と近似表示を区別し、誤差を零にしない。源を局所領域内に要求せず、全過程の座標対応と局所所属の同値を分ける。通常の周波数νと角周波数ω、物理的な測定済みと理想的な座標記述を混同しない。横波条件や完全な場方程式を勝手に補わない。',
          '静止は全区間の代表位置、同じ出来事は所属と両系の座標記録、変換は四成分の正逆写像と六場の混合、位相は逆写像による関数の引戻し、近似は非空の全領域の成分誤差として合成する。提示関係の基本語は一般の発話・参照関係であり、未知の物理内容や一文全体の代用ではない。',
          '同一出来事と別出来事、四座標の変異、六成分と位相の個別の誤り、非零の成分誤差、41引数と37証人、両先行節・引用・直接性を局所診断した。診断波形を正弦とはせず、全実数・全関数域の列挙を拒否する。原著者の物理法則の証明と、表現と読解の確認を分ける。',
          f'先行の波の仮定、問い、両変換の適用から続けて再読し、{title}の内容・参照・範囲・提示を、明示した局所近似と同じ設定の読みの下で欠落なく記述したと判断する。後続の物理的な周期数、光源への視線角、ドップラー原理と光行差はこの判断へ先取りしない。',
        ]
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS+['u0182第一文の問いは、同じ仮定の波を同じ観測者・系・単位で固定し、実際の二場の記述を答えとする質問として読む。著者による実際の質問提示と仮定上の調査を分ける。'],limits=['明示した局所近似・同じ割当・理想座標の読みの下でのアシスタントによる判断であり、独立査読や意味同義性の自動証明ではない。','物理法則と正弦の全域的な真理、全実数算術の一般定理を有限診断で証明していない。先行の物理的導出に関する留保と反例は保持する。','u0178及びu0188以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,FIRST_SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,FIRST_DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='wave_inquiry_both_transformations_and_display_gloss_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':6},semantic_equivalence_automatically_proved=False,source_sha256=pins)
