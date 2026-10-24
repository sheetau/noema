"""Record six whole-unit readings of the ninth-section opening."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-ninth-section-opening.noema';CORE='examples/v014/ninth-section-opening-core.noema'
BASIS='data/ninth-section-opening-basis-v1.json';ANNOTATIONS='data/ninth-section-opening-identifiers-v1.json'
SOURCE='data/einstein-ninth-section-opening-reading-v1.json';REPORT='reports/ninth-section-opening-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/ninth-section-opening-v1.md'
REVIEWS=tuple(f'data/einstein-ninth-section-opening-u{n:04d}-review-v1.json' for n in range(227,233))
CLAUSES=(
 (('§ 9. ',['ekzp','eihq'],'第二部に直接属する深さ2と表示番号9を区別し、既存区分eisv6へ結ぶ。'),
  ('Transformation der Maxwell-Hertzschen Gleichungen ',['ekzo','eispd','eispf','ekzn','eiu2'],'同じ出来事の二系表示に従って同じ方程式の形を変える研究主題を案内する。'),
  ('mit Berücksichtigung der Konvektionsströme.',['ekyy','ekzn','ekyq','seme','ekxl'],'電荷分布の密度と実際の流速を保持する対流項を含め、真空の主題へ戻さない。')),
 (('Wir gehen aus von den Gleichungen:',['ekzi','ug','ekzc','ekyz','ekyq'],'著者が後続の原系方程式とその解釈を議論の出発前提として採用する。コロン後の表示との説明関係を保つ。'),),
 (('[M0383]',['ekza','ekzd','s5u','seme','semc','s5v','eisox'],'三行二列の六回転式を同じ二場・地点・領域・ρ・三流速・Vに接続し、18偏微分と全ての符号・対流項を保持する。'),),
 (('wobei',['ekzi','uf','eiswh','ekzh'],'直前の六式に続くρの式と記号の意味説明を導く語として接続する。独立の法則の断言又は無関係な話題の追加へ替えない。'),),
 (('[M0384]',['ekzb','ekze','s5t','semd','eisox'],'ρが同じ電気側の三対角偏微分の和に等しい表示。磁気側の発散式や後続のρ′へ取り替えない。'),),
 (('die [M0385]-fache Dichte der Elektrizität ',['ekzh','ekyz','ekzf','eiswd','ekxg','ekxf','seml'],'先行式のρを主語として受け、同じ電荷分布の実際の密度の4π倍を意味すると説明する。総量や未規格化密度と区別する。'),
  ('und ([M0386]) den Geschwindigkeitsvektor der Elektrizität bedeutet. ',['ekzh','ekzg','eiswe','ekxl','ekxi','ekxh','seoc'],'同じ分布の全成員の座標時刻速度を三空間成分の順序付き表記へ結び、同じbedeutetの第二対象とする。'),
  ('Denkt man sich die elektrischen Massen unveränderlich an kleine, starre Körper ',['ekyx','ekyo','ekyc','ekx3','ekx2','ekxx','eigy'],'電荷を小さい剛体の完全な物質部分へ不変に付着させるという仮定を、担体別の物理的履歴と同一出来事へ結ぶ。'),
  ('(Ionen, Elektronen) gebunden, ',['ekys','ekyr','eisv2','eisv3','eisv4'],'別の二つの歴史的な担体名を、この箇所で使う共通の古典的モデルへ対応させる。現代の二種を同一視したり名称だけで意味を代用したりしない。'),
  ('so sind diese Gleichungen die elektromagnetische Grundlage ',['ekzj','eiswm','ekzc','ekyq','ekyw','eiswa','eisdi'],'先行の同じ原系方程式を指し、担体の解釈を採用する同じ理論の基礎法則として位置付ける。物理的真理や理論全体の導出済みとはしない。'),
  ('der Lorentzschen Elektrodynamik und Optik bewegter Körper.',['eisv5','ekyv','ekyu','ekyt','eie6','ekwm'],'同じLorentz理論の運動を含む電気力学と動く物体の光学という二主題を保持する。')),
)
SEMANTICS=(
 'ekznは同じ二場と領域の物理的解釈ekyy、原系方程式ekyq、光速度と速度単位を結ぶ。ekzoはこの規約と同一出来事の座標表示eiu2を既存eispdへ渡す。対流項を含む内容から主題を作り、変換の成功・不変性を見出しから主張しない。',
 'ekzcは同じcontextで原系解釈ekyzに従う任意の設定について同じekyqを要求する閉じた内容。ekziはその引用をugの出発前提にし、コロン後の六式を同じ導入の具体化へ結ぶ。物理的な対象例の実在や実験確認を導入へ付け足さない。',
 'ekzaは非空領域の全有効点で、同じ二場の18偏微分s5uと規格化密度・三流速による六式semeを要求する。semcは電気側の時間微分にρuを加え、s5vは磁気側の符号が逆の回転を使う。正のVの下で分母を払った式を用いる。ekzdはその表示内容を同じ原系解釈へ結ぶ。',
 'ekziは六式の表示からwobei、ρの発散式、意味説明へのufを保つ。ekzkはこれらを同じ文中の相異なる箇所として順序付ける。接続詞を単なる削除可能な区切りとして省かず、後続の説明が直前の式の記号解釈である役割を保持する。',
 'ekzbは電場の各成分と同じ軸について実際のs5t偏微分を要求し、その三対角値の和と同じρの等号semdを保つ。ekzeがこの表示内容、ekzc/ekyqが六回転式と共有した全体である。表示を分けても同じ場・系・領域・評価点を変えない。',
 'ekzhは同じ原系の密度と速度の意味を別の射影で指定する。ekyxは完全な付着・小ささ・剛性・二つの担体名を同じモデルへ接続し、同じLorentz理論が条件付きの原系法則を自らの基礎として採用するeiswaをeisdiと結ぶ。ekzjの照応はこの先行方程式の内容ekzcを保持する。',
)
WHOLE=(
 '二行の見出しを先行第八節末尾と後続本文へ照合して再読した。番号・階層・歴史的呼称・方程式の変換・対流電流を含むこと・主題提示を保持したと判断する。',
 '導入、コロン後の六式、wobeiとρの式、bedeutetまでを一続きに再読した。著者が同じ式を出発点にする提示を保持したと判断する。単なる物理法則の証明又は式の引用だけへ縮めない。',
 '原刊の六つの左辺・右辺、全ての1/V、ρu、偏微分の成分・軸、差の順を再読し、前の導入と後のρの説明へ照合した。六式全体を明示した読みの下で保持したと判断する。',
 'wobeiを前後の式と第一文のbedeutetまで含めて再読した。同じ六式への記号説明の導入として、その接続と指示範囲を保持したと判断する。',
 'ρの表示の左辺、三つの分子・分母、二つの加号を原刊と照合し、続く4π密度の説明の主語として再読した。原系の同じ電気側発散の式を保持したと判断する。',
 '二文を全文再読した。4π密度と三速度成分、仮定・電荷付着の不変性・小ささ・剛性・二名称、先行式への照応、電磁的基礎、同じLorentz理論と二主題を保持したと判断する。明示した古典的密度・流速・担体モデルを越える現代的粒子像や理論の物理的真理を認定する判断ではない。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS));out=[]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_ninth_section_opening.py','tests/test_ninth_section_opening_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    assert len(source['segments'])==6
    bindings={statement:selection_binding(catalog,[statement]) for statement in (408,409)}
    for i,s in enumerate(source['segments']):
        statement=409 if i==0 else 408;clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text,(i,offset,text)
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[statement],definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲と全数式要素{[m['id'] for m in s['math']]}を原刊916頁へ照合した。六つの原文単位とその前後の接続を保持し、原文・MathML・原刊像のハッシュを固定した。",
            SEMANTICS[i],
            '同じ原系K、長さta・時間rb・速度tb、V=tc、同じ二場・領域・分布・ρ・流速・単位を保持する。ρの表記と密度場の射影、三速度成分と流速場の射影を分け、同じ論説と第九節の範囲へ接続する。diese Gleichungenは先行の原系方程式であり、変換後の表示を指さない。',
            '見出しは研究主題の案内、最初の文は出発前提の採用と式・意味の説明、第二文は担体解釈の下での条件付き基礎の主張として分ける。ug・eisox・uf・表記規約・uh・照応・eir3を同じ著者と論説へ接続し、引用内容を提示関係の評価で真として実行しない。',
            '第一文の解釈条件へ付着や方程式の成立を入れず、後の条件付き基礎と同じ型を受け取るだけの担体パケットを制約しない。六式と発散の表示を分け、磁気側発散零・後続の電荷不変・変換の成功を足さない。密度は有限の球平均極限、流速は同一分布の全成員に共有される座標時刻速度という採用読解を保つ。',
            '電荷の物理的保有量と単位、領域加法性・密度極限・規格化、物質の履歴・剛性・小ささ・部分ごとの固定電荷、同じ世界線出来事、理論の研究対象と基礎依存は既存定義で説明する。追加した一般関係は設定からの型付き場射影による記号解釈二つと、先行の閉じた内容への照応であり、原文の一文をそのまま原始関係の意味へ収納しない。',
            '物理量の引数、二つの表示式の偏微分・密度・流速、七局所証人・十九射影証人・三内容の各三十一量化位置、二表記、出発前提・説明・照応・本文順序・階層を対照する。旧408主張・規約・判断の保存と原刊・MathMLの照合を別々に確認する。有限検査を連続体全域又は原文同義性の自動証明へ転用しない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=bindings[statement],source_order_statements=[statement],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位の判断。独立査読や意味同義性の自動証明ではない。','仮定した方程式・担体モデル・条件付き基礎を記述することと、物理的な真理又は変換の健全性の証明は別である。','二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inventory)
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='ninth_section_opening_six_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':6},semantic_equivalence_automatically_proved=False,source_sha256=pins)
