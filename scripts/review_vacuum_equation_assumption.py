"""Review the opening assumption, six displayed equations and vector explanation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_vacuum_equation_assumption import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_vacuum_equation_assumption import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/vacuum-equation-assumption-v1.json'
REVIEWS=tuple(f'data/einstein-vacuum-equation-assumption-u{n:04d}-review-v1.json' for n in range(153,156))
CLAUSES=(
 (('Die Maxwell-Hertzschen Gleichungen für den leeren Raum ',['ejsz','ejsm','ejsy','eisch','eispf'],'同じ真空領域・物理的な二場・六回転式を歴史的な同じ呼称へ結ぶ。'),
  ('mögen gültig sein für das ruhende System [M0286], ',['ejs6','ejta','ug','ra'],'既出のKについてその同じ内容を著者が仮定する。絶対静止や検証済みの法則へ替えない。'),
  ('so daß gelten möge:',['ejta','eisox','uf','eispl'],'コロン後の六式が同じ仮定を具体化するという導入。真空からの独立した証明とはしない。')),
 (('[M0287]',['s5t','s5u','s5v','s5w','s5x','s5y','ejsz','ejs6','ejta'],'六式と18偏微分を、同じ二場・全領域・光速度に対する条件として保持する。式の表示は前の仮定の具体化で、後の成分説明へ続く。'),),
 (('wobei ([M0288]) den Vektor der elektrischen, ',['ejs4','ejs3','ejs2','ejsx','ejs7','eispi','eispj'],'同じ電気側の場の三成分(X,Y,Z)を、同じ領域の全有効座標での値の規則へ結び、場の物理的な意味と単位も共有する。'),
  ('([M0289]) den der magnetischen Kraft bedeutet.',['ejs5','ejs3','ejs2','ejsx','ejs7','eispi','eispk'],'省略されたVektorを前項から受け、磁気側の三成分(L,M,N)を同じ仕方で別の場へ結ぶ。語尾Kraftを両方の場の強さの説明として読む。')),
)
SEMANTICS=(
 'ejsx/ejsyで同じK・領域・二場・尺度に四単位と二換算係数を結び、ejszで同じ全領域の真空と六式を合わせる。ejtaはこの閉じた内容をugへ渡し、同じ呼称と六式の表示箇所を内容へ固定する。',
 's5t/s5uは同じ場・領域の同じ四座標で18偏微分を結び、s5wは三軸の循環順序と電気側/磁気側の逆の符号を持つ六条件を要求する。s5yの全領域と正のVを現在の二場・領域・tcへ適用し、現実に真かどうかとは別に仮定の表示として記述する。',
 '二つの順序付き表記を、ejs4/ejs5という別の閉じた規則へ結ぶ。規則は現在の物理的な場のejsyと、全有効四座標で同じ三成分値を取るejs3を含む。ejs2は全三成分の有効性と対応する等号を保ち、別の場との交換や一地点だけの一致へ縮めない。',
)
WHOLE=(
 '導入全文を直前の見出し、コロン後の六式、wobei以下まで連続して再読した。固有名・真空・静止系K・仮定の採用・後続式による具体化を、明示した読みの下で欠落なく記述したと判断する。',
 '原刊の三行二列を各左辺・右辺・符号・微分軸まで再読し、前の仮定と後の成分説明へ照合した。六式全体を保持したと判断する。原著者の物理法則の真理や、後の変換がこの六式だけから導けることを証明した判断ではない。',
 'wobeiから句点までを六式の成分説明として再読した。電気側と磁気側のベクトル、両三成分の順、bedeutetによる意味説明を、明示した場の強さの読みの下で欠落なく保持したと判断する。後続の磁気的質量についての説明まで確認済みとする判断ではない。',
)


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_vacuum_equation_assumption.py','tests/test_vacuum_equation_assumption_review.py'}
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
            f"固定{s['unit']}の全範囲と全数式要素{[m['id'] for m in s['math']]}を原刊907頁へ照合した。導入、六式、成分説明を一続きの文として読み、版とハッシュを固定した。",
            SEMANTICS[i],
            'K=ra、長さta・時間rb・速度tb、V=tc、二場znl/znm、領域znkを既出本文へ接続する。電気側と磁気側の成分順をyn/yo/ypへ固定し、仮定範囲znoと第六節全体eispg、導入・表示式・説明の箇所を区別する。',
            '同じ仮定文の導入ug、表示式と内容eisox、具体化と成分説明uf、二表記の意味規則eispi、著者と論説への帰属eir3を合成する。原文のmögenを現実の真理や証明済みの断言にせず、wobeiを無関係な別の主張にしない。',
            '四単位と二係数は同じ場の規約の証人で、値を1や1/Vへ固定しない。物質占有の不在は全指定領域へ課し、場の非零を排除しない。六回転式に発散条件を足さず、成分の一致に領域外や第四の時刻成分を要求しない。',
            '電気側は静止試験電荷への力/電荷、磁気側は電気的寄与と区別した運動電荷への横向き作用で同定する既存規約eirm/eiruを共有する。ここでのKraftは場の強さとして読み、機械力の単位そのもの、物質中の現代H、磁気的質量の独立説明へ無条件に同一化しない。三成分表記の一般関係は内容を閉じた合成規則から受け取る。',
            '現在の場・系・全単位引数、二値の全六証人位置、同じ真空・二場・Vへの接続、三成分の全診断点、六式の18微分位置と符号、引用・仮定・呼称・説明・本文順序を対照した。全実数・全関数域は有限列挙を拒否し、既存の偏微分接続の証拠もハッシュで固定する。検査成功を意味判断へ自動変換しない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる全単位の通読判断。独立査読や意味同値の自動証明ではない。','仮定された式を記述したことと、現実の物理法則の真理や後続の変換の健全性を証明することは別である。','u0156以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv)
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='sixth_section_opening_assumption_three_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},semantic_equivalence_automatically_proved=False,source_sha256=pins)
