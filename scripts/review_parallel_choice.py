"""Review the complete motion-setting and symmetry-permission paragraph."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_parallel_choice import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

DOC='docs/parallel-choice-v1.md';SOURCE='data/einstein-parallel-choice-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
REPORT='reports/parallel-choice-v1.json';REVIEW='data/einstein-parallel-choice-review-v1.json'
PRIORS=('data/einstein-frame-instruments-review-v1.json',)
DEPENDENCIES=('reports/frame-motion-v1.json','reports/moving-axes-v1.json','reports/axis-states-v1.json')
REASONS=(
 '原刊897頁のEs werde nunからparallel seienまでをu0044全687文字・526本文文字と照合した。M0066〜M0074のk/v/x/K/t/K/k/t/tを保持し、二文と括弧全体を対象とする。',
 '同じ原点・三軸・物差し・全時計への正X定速度、静止基準の全軸、全時刻の配置存在と一意性、一つの全区間平行候補の存在内容、それを仮定してよい権原と対称性の理由を接続した。',
 '初期zb4から移動後zb6への同じ対象と既出速度zb7を維持する。k/Kの命名をzbm/raへ固定し、tの全記号使用を同じ静止系ra・単位rbの規則へ結ぶ。候補ごとに同じ対象を保ち、時刻ごとに別候補を選ばない。',
 '第一文は設定操作への指示、第二文前半はその仮定内での帰結、後半は仮定採用の認識上の許容と理由の帰属として保持した。括弧を同じ時刻記号の解釈を限定する挿入説明に結んだ。',
 '加速機構、加速中の剛性、初期長さ保存、時計同期・内部停止、二原点一致・X支持直線一致・正方向一致を追加しない。許容から採用済み・物理的真理・存在証明を導かない。対称性の具体的な回転角や反射面を原文へ補わない。',
 '配置は全軸成員と原点の実位置へ、時点範囲は全実時刻へ結ぶ。対称性は同じ設定を保つ空間操作への物理的分類とsfsの可逆性・条件保存に分ける。権原、全記号使用と解釈適用は一般的な意味規約として与え、文全体を単一原始記号へ置き換えない。',
 '原刊画像・固定原文・先行三依存群の証拠と今回の結合・量化・引用の検査を保存する。全実数履歴や空間的対称性の物理的実証、原文との同義性の自動証明とは区別する。',
 '原文二文を前の初期設定と後の測定の導入に照らして再読した。対称性を理由に全時刻で平行な一つの運動の存在を仮定してよいという明示した読みで、物理条件、対象照応、全量化、設定と主張の力、括弧説明を保持したと判断する。',
)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][43]
    assert u['id']=='einstein-1905:u0044' and len(u['text'])==687
    assert u['text_sha256']=='ac47cdbc668ed13b37de8f87f8e35303185a24899f06aa94af78d1768b8a5ae5'
    count=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']));assert count==526
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']}
    forms=dict(zip(('M0066','M0067','M0068','M0069','M0070','M0071','M0072','M0073','M0074'),('k','v','x','K','t','K','k','t','t')))
    bindings=('zbm','zb7','yn','ra','eiwt','ra','zbm','eiwt','eism5')
    for n,s in forms.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/review_parallel_choice.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-parallel-choice-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['897'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=count,math=[dict(id=n,sha256=math[n]['sha256'],reading=s,binding=b) for (n,s),b in zip(forms.items(),bindings)])],observations=['原点への定速度を全軸・物差し・時計へ共有させる設定指示である。','Jeder Zeitの全時刻とeine bestimmte Lageの一意の配置を保持する。','befugt anzunehmenとsein kannを、全時刻で平行な一つの運動の存在内容を仮定してよい権原として読む。','括弧のimmerは同じt記号を常に静止系時刻と解釈する規定である。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);segment=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,REPORT,*PRIORS,*DEPENDENCIES,'scripts/review_parallel_choice.py','tests/test_parallel_choice_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=segment['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=segment['unit_sha256'],text=segment['text'],range=segment['range'],math=[{k:m[k] for k in ('id','sha256')} for m in segment['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読、運動候補の実在・対称性の十分性や物理的真理の証明、同義性の自動証明ではない。','u0045以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='complete_frame_motion_and_symmetry_permission_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0044':526},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
