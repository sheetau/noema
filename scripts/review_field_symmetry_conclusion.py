"""Review the complete symmetry passage, final equations and author footnote."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_field_symmetry_conclusion import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_field_symmetry_conclusion import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,UNITS,source_record

REPORT='reports/field-symmetry-conclusion-v1.json'
REVIEWS=tuple(f'data/einstein-field-symmetry-conclusion-u{n:04d}-review-v1.json' for n in UNITS)
CLAUSES=(
 (('Ferner folgt aus Symmetriegründen',['ejvn','ejvh','ejvi','eisn2','ejvt','ejvr'],'先の積1に加え、対称性を理由として偶性が従うという提示と、番号1)で参照する例示的脚注を接続する。'),),
 (('[M0312];',['ejvi','sar2','znz','ejvn','eisox'],'同じ第六節の係数のvと-vでの値の等しさを述べ、次の帰結へ続く。v=0の同じ引数の恒等も許す。'),),
 (('es ist also',['ejvj','ejvo','zc'],'先の積1と偶性を受けて、続く係数の値1を著者がしたがってと提示する。'),),
 (('[M0313],',['ejvk','sat2','ejvo','eisox'],'同じ係数の値が1という結論を表示する。負の枝を除く条件を前提へ追加しない。'),),
 (('und unsere Gleichungen nehmen die Form an:',['ejvl','ejvp','ejvx'],'同じ著者が先の共通係数付き六式を自らの式として受け、値1を用いた次の六式の形へ接続する。'),),
 (('[M0314]',['ejvm','sau2','s6k','s6l','s6m','sai2','saj2','ejvp'],'全六成分・対応する符号・β・v/Vを保持し、同じ物理的な両場と全領域を同じ逆座標写像で結ぶ。'),),
 (('Ist z. B. [M0443] und [M0444], ',['ejvf','sbe2','ejvr','eir5'],'同じ点の五成分が零でNが非零という仮定例を、本文の対称性の論点を考える具体例として結ぶ。場全体の一様性や実測の事実は要求しない。'),
  ('so ist aus Symmetriegründen klar, ',['ejvq','eisn2','zdg'],'この仮定なら、続く応答の必要性が対称性を理由に明白だという著者の位置付けを保つ。'),
  ('daß bei Zeichenwechsel von [M0445] ohne Änderung des numerischen Wertes ',['sbf2','sbd2','ejvg'],'同じVと同じ点のNを固定し、速度をvから-vへ変える。大きさだけを保つという明示的な読みで符号反転を構成する。'),
  ('auch [M0446] sein Vorzeichen ändern muß, ohne seinen numerischen Wert zu ändern.',['ejvg','ejvh','sba2','sbb2','ejrj'],'同じ変換規則によるY′も大きさを保って反対符号となる必要性を構成する。零の応答同士を厳密な符号反転とせず、非自明なv≠0の範囲を明示する。')),
)
SEMANTICS=(
 '先の積1に対する追加の帰結として、対称性を理由にする偶性と脚注の論拠を接続する。理由の種類と著者による推論の提示を保持する。',
 '同じ係数の正負速度での二つの値の等しさを構成する。速度零を不当に除かず、係数の値1や正値を偶性自体に混ぜない。',
 '先の積1と偶性を合わせた現在の前提ejvjから、係数の値1への著者の帰結をalsoとして保持する。',
 '同じ係数を実数1へ等置する内容を表示する。著者の推論の妥当性と、著者がこの結論を提示することの記述を区別する。',
 '同じ著者の同じ六式が、既に述べた値1によって次の最終形となるという提示を構成する。',
 'X′=X,L′=Lと残る四つの混合を保持する。Y′とN′は減算、Z′とM′は加算であり、同じβとv/Vを使う。対応する出来事の四座標と全領域の一致を維持する。',
 '五つの零成分と非零Nを同じ点で仮定し、同じ大きさで速度を反転するとY′も同じ大きさで符号を反転しなければならないことが、対称性から明白だという条件付きの例示を保持する。',
)
WHOLE=(
 'u0167全体を原刊909頁で再読し、Ferner、folgt、Symmetriegründenと著者脚注1)を、追加・帰結・理由・参照へ欠落なく接続したと判断する。',
 'u0168全体を原刊909頁で再読し、同じφ、両速度の符号、等号、続く帰結への接続を保持したと判断する。',
 'u0169全体を前後の数式と連続して再読し、alsoの理由付き帰結を同じ著者と現在の係数へ接続したと判断する。',
 'u0170全体を原刊909頁で再読し、同じφ(v)の値1を著者の結論表示として保持したと判断する。',
 'u0171全体を前後の数式と連続して再読し、und、unsere Gleichungen、nehmen die Form anの同じ式と著者への参照、次の形の導入を保持したと判断する。',
 'u0172の全六式を原刊909頁と照合して再読した。成分、プライム、混合の正負、β、v/V、係数1、対応する場の引数と領域を欠落なく記述したと判断する。',
 'u0282全体を原刊909頁下部で再読した。仮定例、五つの零と非零N、対称性による明白さ、速度とY′の大きさを保つ符号反転、必要性、本文への参照と説明を明示した読みの下で保持したと判断する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_field_symmetry_conclusion.py','tests/test_field_symmetry_conclusion_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲と全数式要素{[m['id'] for m in s['math']]}を原刊909頁へ照合した。u0167–u0172と脚注u0282を連続して読み、A0023からcite_note-4への参照も確認した。字形差と脚注の配置は原資料を保持して明示する。",
            SEMANTICS[i],
            'K/kはra/zbm、V/vはtc/zb7、旧新の二場はznl/znmとznr/zns、領域はznk/znt、脚注の同じ旧系の点はzn7。係数znzは第六節のφ/ψであり、第三節の係数へ戻さない。本文の理由箇所zn4と脚注zoaを同じ論説の番号1)で接続する。',
            'zcで三段階の理由付き帰結、eisn2で対称性の理由、zdgで脚注の明白さ、ejrjで非空の仮定状況に対する必要性、eir5で例示、eisfoで脚注参照を構成する。著者・論説・数式表示への帰属を保持し、引用内容を無条件の真理として実行しない。',
            '脚注は同じ一点の仮定であり場全体を定数にしない。符号と大きさの双方を要求し、非自明な反転にはv≠0、本文の偶性にはv=0も許す。積1と偶性の前提へ正値を加えず、-1の反例を保持する。最終六式には著者が採る値1を用いる。',
            '既存の実数・場評価・逆座標写像・全点一致・内容・必要性・著者の提示を合成し、未説明の一文専用の基本関係は追加しない。追加参照個体は三つの数式表示だけであり、脚注の条件と応答をその名前で代用しない。',
            '仮定の全条件、同じ点の五つの零・非零N、非定数場、正負速度と大きさ、必要性、係数の各枝、全六成分と領域、本文・表示・脚注の全引数を対照した。既存の原成分からの応答縮約・負の枝の記号的反例をハッシュ照合し、有限列挙拒否を保持する。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,INDICES),source_order_statements=[157,158,159],attached_note_statements=[160,161],clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる全単位の通読判断。独立査読や意味同値の自動証明ではない。','対称性からの物理的な応答や、積1と偶性から値1を選ぶ推論の正しさは認定せず、著者の理由と結論を記述する。','u0173以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inv)
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='field_symmetry_conclusion_seven_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':7},semantic_equivalence_automatically_proved=False,source_sha256=pins)
