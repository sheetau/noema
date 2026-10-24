"""Close u0203 and the moving-sphere display after their spanning sentence."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_same_light_portion import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,MEANINGS,INDEX
from scripts.read_same_light_portion import INVENTORY,SOURCE,DOC,READING,PREVIOUS

REPORT='reports/same-light-portion-v1.json'
REVIEWS=['data/einstein-same-light-portion-u0203-review-v1.json','data/einstein-same-light-portion-u0204-review-v1.json']
PRIOR_DOCS=['docs/density-unit-scope-v1.md','docs/equal-volume-supposition-v1.md','docs/volume-denial-v1.md']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']}
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,DOC,READING,REPORT,*PREVIOUS,*PRIOR_DOCS,'scripts/review_same_light_portion.py','tests/test_same_light_portion_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,SOURCE,*PREVIOUS):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    previous=[json.loads(read(p)) for p in PREVIOUS];out=[]
    for offset,index in enumerate((202,203)):
        u=inv['units'][index];text=u['text'];indices=[385,386,387,388] if offset==0 else [388]
        if offset==0:
            clauses=[dict(range=r['range'],text=r['source'],statements=[385+i],definitions=r['definitions'],reason=r['requirements'][-1]['reason']) for i,r in enumerate(previous)]
            clauses.append(dict(range=[422,597],text=text[422:597],statements=[INDEX],definitions=list(MEANINGS)+['secb','eknk','eknp'],reason='Sindからの同じ方向余弦と移動球面の指定を、続くu0204の表示とu0205[0,107)の無流出入・同じ初期部分の持続へ結ぶ。条件の前半を独立の断言にしない。'))
            meaning='第一文は校正された両系の同じ平均密度と相対性原理による帰結提示、第二文は実際の体積とは別の等体積の仮置きと仮の総量比、第三文は実際の等体積への強い図式的否定、第四文は波面方向・移動球面とその表面要素の無流出入へ続く条件を保持する。'
            presentation='da/soの根拠、Es wäre/wennの思考上の比較、daherの帰結提示、Dies/jedochの参照と対照、Sind/soの同じ設定を保つ。第四文はu0204–u0205[0,107)まで読んで初めて完結し、その後方参照と記述可能性も同じ本文へ帰属する。'
        else:
            clauses=[dict(range=[0,len(text)],text=text,statements=[INDEX],definitions=['secb','secc','eknc','eknk','ekny','ekn5'],reason='直前のK系の方向余弦a,b,cと光速度Vによる中心(Vat,Vbt,Vct)からの二乗距離をR²へ等置し、直後の無流出入が適用される同じ球面を表示する。境界と閉内部、波面法線と球面法線を区別する。')]
            meaning='M0355の(x−Vat)²+(y−Vbt)²+(z−Vct)²=R²を、同じK時刻tの三位置と光速度・単位波面方向・正の半径による移動球面として保持する。三つの符号、Vと各方向余弦と時刻の積、三平方の和、R²を保つ。'
            presentation='この表示はu0203末尾のKugelflächeを指定し、u0205冒頭の無流出入と同じ光の部分の持続を述べる文の中にある。独立の別の波又は新系kの同時断面式として提示しない。'
        reasons=[
          f'固定原文{u["id"]}の全範囲と全MathML要素を原刊913頁へ照合し、直前の三文から表示を挟んだ一文の終わりまで通読した。保存された文字列・範囲・数式ハッシュを固定する。',
          meaning,
          '同じK,V,波・過程・光の部分zvaaと校正単位を保つ。第二文の比較体積を実際の新系体積へ混ぜず、第四文の球面と光の部分は前の同じ対象を引き継ぐ。a,b,cは波面法線の方向余弦であり球面の各点の外向き法線ではない。',
          presentation,
          '平均密度と瞬間密度を区別する。第三文は無限定の図式的否定という明示した強い読みであり、特殊方向の等体積反例を隠さない。永久の持続は球の全時刻で採用する理想平面波モデルの条件を明示し、局所近似からの無条件の外挿を認定しない。光子の存在論や微視的な交換履歴の識別も追加しない。',
          '物理的な密度・流・部分・単位の基本規約へ、体積積分、仮の総量、実際の体積否定、球面運動、各点の相対流、初期部分の一対一な輸送を合成して接続する。一般関係を原文一文全体の代用として新設しない。',
          '各文の既存判断を同じ依存関係で保持し、今回の初期部分の対応・全時刻の量化・同量だが異なる分布・引用内容の非実行・根拠と記述の向きを検査した。物理的な真理、独立査読、全実数理論又は意味同義性の自動証明ではない。',
          f'{u["id"]}の全内容を前後の一続きの議論と合わせて再読し、明示した平均密度・仮の等体積・第三文の強い否定・初期部分の連続体輸送の読みの下で、参照・条件・内容・提示を欠落なく記述したと判断する。u0205の次の問いとd.h.はこの単位の完成へ混入しない。',
        ]
        count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',text)));assert count==(475 if offset==0 else 0)
        source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[dict(id=n,sha256=math[n]['sha256']) for n in u['math_ids']])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,indices),clauses=clauses,interpretation=LIMITS+['先行三文の平均密度、仮の等体積比較、無限定の体積否定は各文の保存済み判断に従う。第三文の強い読みを一般的不変性だけの弱い否定へ置換せず、等体積の反例を保持する。'],limits=['明示した読みの下でのアシスタントによる通読判断であり、独立査読又は意味同義性の自動証明ではない。','原文の著者帰属と物理的な正しさは別であり、既存の留保・反例は保存する。','u0205の問いと言換え、後続本文及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,READING,*PREVIOUS],formal_checks=[REPORT],semantic_reading=[DOC,*PRIOR_DOCS]),reviewed_prose_characters=count,source_sha256=pins))
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
    return dict(status='density_hypothetical_ratio_volume_denial_and_moving_sphere_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},u0205_additional_prose_characters=94,semantic_equivalence_automatically_proved=False,source_sha256=pins)
