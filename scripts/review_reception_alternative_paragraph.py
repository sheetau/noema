"""Review the reception alternative, its drawback, and the following convention."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from noema.grammar import parse
from noema.finite_semantics import evaluate_document
from scripts.check_einstein_principles_paragraph import calls
from scripts.check_practical_time_convention import relation,forbidden
from scripts.compose_practical_time_convention import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS as THIRD_LIMITS
from scripts.compose_reception_position_dependence import LIMITS as SECOND_LIMITS
from scripts.compose_reception_time_alternative import LIMITS as FIRST_LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
SOURCE='data/einstein-reception-time-source-reading-v1.json'
STEMS=('reception-time-alternative','reception-position-dependence','practical-time-convention')
READINGS=tuple('data/'+s+'-reading-v1.json' for s in STEMS)
REPORTS=tuple('reports/'+s+'-v1.json' for s in STEMS)
DOCS=tuple('docs/'+s+'-v1.md' for s in STEMS)
REVIEW='data/einstein-reception-alternative-paragraph-review-v1.json'
UNIT='einstein-1905:u0012';ORDER=[231,232,233]
INTERPRETATION=FIRST_LIMITS[:-1]+SECOND_LIMITS[:-1]+THIRD_LIMITS[:-1]+[
 '第一文は方式を採りそれだけで済ませてもよいという譲歩付きの可能性、第二文は同じ方式の空間的位置依存という不都合と経験的知識、第三文ははるかに実用的な規定へ考察を通じて進む導入として読む。採用の可能性と欠点は両立し、前文の撤回や方式の全面否定へ替えない。',
 '三文269・151・71非空白文字を全段落491文字として一度だけ数える。以下の考察への指示はu0013冒頭からu0018の時刻付与定義へ固定するが、指示対象の全記述・全検査をこの段落の完了に含めない。',
]
REASONS=(
 '原刊893頁に照合した固定u0012全569文字・491非空白文字を、三範囲[0,309)、[310,488)、[489,569)で覆う。文間の空白以外の欠落・重複はなく、数式や注番号はない。',
 '原点で時計とともにいる観測者、原出来事を知らせ真空を通って届く各光信号、その受信に対応する指針表示の割当、これだけで済ませる採用可能性、同じ方式の位置非独立性と不都合、経験から知る挿入、はるかに実用的な規定と考察による到達を保つ。全称・可能性・非独立性・比較級・程度を省かない。',
 '第一文の方式eisg7と課題eisheを第二文の配置比較と第三文の比較先へ共用する。各配置は同じ規則eikdへ結び、原出来事・尺度・比較可能な時計規約を保持する。第三文の新規定eishqは同じ課題のqu・rjへ、同じ考察eishrはu0013冒頭からrjまでへ結び、他の方法や論説を混ぜない。',
 '三文を同じ著者・論説へ帰属する。第一文のallerdingsの譲歩と可能性、第二文のaberの対比と経験的知識の挿入、第三文の主張とfolgendeの前方参照を分け、本文順序を保持する。引用内容の帰属を実際の物理的実験や全命題の真理認定へ替えない。',
 '受信時の読みを元の出来事の生起時刻と同一にせず、光伝播補正や遠隔同期を第一方式へ足さない。任意の二位置で必ず値が違うともせず、時計の初期ずれや別単位の差を非独立性の根拠にしない。新方式の最適性、全条件での優越、数値閾値、後続考察の証明完了を補わない。',
 '光信号の証拠と伝播・受信、時計の表示・値・割当、配置の欄と共通比較条件、実数値の相違、方式が伴う特徴・課題上の不都合・経験的知識、共通尺度での評価・厳密な優越・顕著な程度差、規則の参照と考察による到達を意味規約付きの関係へ分けて合成した。原文一文の真偽を未説明の一入力へ置き換えていない。',
 '三つの文別読解記録・局所報告・原刊照合、現行本文・依存定義・意味規約を固定する。受信記録の全欄、二配置の同じ原出来事・尺度・値、存在量化、同じ経験の対象、比較の両程度と方向と強さ、前方参照の始終点を対照検査した。有限例を実測・全実数の検証・意味同値の証明へ昇格させない。',
 '受信側だけで評価する代案、その方式に伴う位置依存の不都合、後続の同期時計による規定へ進む予告という三文を続けて再読した。前段落の局所定義の限界からの接続と、採用可能性を残した比較を保持する。明示した解釈の下で本段落に未処理の内容・参照・範囲・提示はないと判断する。後続u0013以降の考察の詳細は別単位として残る。',
)

@lru_cache(None)
def discourse_checks():
    doc=parse(read(FULL));doc['statements']=[doc['statements'][i] for i in ORDER]
    names={'rd':'author','eirf':'paper','ri':'now','eisgq':'prior','eishg':'first','eishp':'second','eishs':'third','eishr':'argument','eish2':'begin','rj':'end','eishe':'task'}
    rows={
        'eir3':{('first','author','paper','eiki','now'),('second','author','paper','eikq','now'),('third','author','paper','eikw','now')},
        'eisg6':{('first','author','eij5','eikh','paper','now')},
        'zbc':{('second','author','eikh','eikp','task','now')},
        'eisho':{('second','author','eikn','eiko','paper','now')},
        'eishz':{('third','author','argument','begin','end','paper','now')},
        'ue':{('prior','first','now'),('first','second','now'),('second','third','now'),('third','begin','now'),('begin','end','now')},
    }
    m={n:(lambda x=x:x) for n,x in names.items()}|{n:relation(rs) for n,rs in rows.items()}
    def run(extra=None):
        model=m|(extra or {})
        return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(names.values())-{'now'}),situations=('now',),primitives={d['name']:model.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=10000,memoize_definitions=True,memoize_expressions=True)]
    assert run()==[True,True,True];count=1
    for relation_name,source_row,index in (
        ('eisg6',('first','author','eij5','eikh','paper','now'),0),
        ('zbc',('second','author','eikh','eikp','task','now'),1),
        ('eisho',('second','author','eikn','eiko','paper','now'),1),
        ('eishz',('third','author','argument','begin','end','paper','now'),2),
        ('ue',('first','second','now'),1),('ue',('second','third','now'),2),
    ):
        expected=[True]*3;expected[index]=False
        assert run({relation_name:relation(rows[relation_name]-{source_row})})==expected;count+=1
    assert run({'eisg4':forbidden,'eishn':forbidden,'eishx':forbidden,'ce':forbidden})==[True]*3;count+=1
    return dict(cases=count,three_native_presentations_share_one_document=True,modal_contrast_and_forward_reference_preserved=True)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][11]
    assert u['id']==UNIT and len(u['text'])==569 and sum(not c.isspace() for c in u['text'])==491 and not u['math_ids']
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);covered=set()
    for path,span,index,chars,segment in zip(READINGS,([0,309],[310,488],[489,569]),ORDER,(269,151,71),source['segments']):
        rec=json.loads(read(path));validate_hashes(ROOT,rec['source_sha256'])
        assert rec['unit']==UNIT and rec['range']==span and rec['source_text_sha256']==u['text_sha256'] and rec['source']==u['text'][slice(*span)]
        assert rec['selection']==selection_binding(catalog,[index]) and rec['source_nonblank_characters']==chars
        assert segment['range']==span and segment['text']==rec['source'] and segment['unit_sha256']==u['text_sha256']
        assert not covered.intersection(range(*span));covered.update(range(*span))
    assert all(i in covered or c.isspace() for i,c in enumerate(u['text']))
    ds={d['name']:d for d in catalog.document['declarations']}
    def get(parent,callee):
        cs=[c for c in calls(ds[parent]['body']) if c['symbol']==callee];assert len(cs)==1;return cs[0]['arguments']
    constant=lambda name:dict(kind='call',symbol=name,arguments=[])
    # The comparison target and task remain identical across all three sentences.
    assert get('eikf','eike')[:2]==get('eikn','eikm')[:2]==[constant('eisg7'),constant('eishe')]
    assert get('eikv','eikt')[1:3]==[constant('eisg7'),constant('eishe')]
    assert get('eikv','eikt')[0]==get('eiku','eishx')[0]==get('eikv','eishy')[2]==constant('eishq')
    assert get('eikv','eishy')[1]==get('eikx','eishz')[2]==constant('eishr')
    assert get('eiku','eishx')[2]==dict(kind='quote',body=dict(kind='function_ref',symbol='qu'))
    assert get('eiku','eishx')[3]==get('eikx','eishz')[4]==constant('rj')
    assert get('eikk','eisg3')[-2]==dict(kind='quote',body=dict(kind='function_ref',symbol='eikd'))
    for name in ('eiki','eikq','eikw'):assert ds[name]['body']['kind']=='message' and ds[name]['body']['force']=='assert'
    assert get('eikr','zbc')[2:4]==[dict(kind='quote',body=constant(n)) for n in ('eikh','eikp')]
    assert get('eikr','eisho')[2:4]==[dict(kind='quote',body=constant(n)) for n in ('eikn','eiko')]
    load_annotations(ROOT,BASIS,ANNOTATIONS);discourse_checks()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,*READINGS,*REPORTS,*DOCS,'scripts/review_reception_alternative_paragraph.py','tests/test_reception_alternative_paragraph_review.py','tests/test_reception_time_native_method.py','tests/test_reception_position_unit_binding.py','scripts/check_einstein_principles_paragraph.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,*READINGS,*REPORTS):
        rec=json.loads(read(path));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=UNIT,reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),selection=selection_binding(catalog,ORDER),source_order_statements=ORDER,interpretation=INTERPRETATION,
        limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明・時計や光の実測による妥当性の証明ではない。','後続の考察u0013以降と二作品全体の記述は未完で、目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=list(REPORTS),semantic_reading=list(DOCS)),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    rec=review_record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    result=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    assert result['source_nonblank_characters']==491
    return dict(status='reception_alternative_drawback_and_practical_convention_holistically_reviewed',document=FULL,source_units={UNIT:491},discourse=discourse_checks(),whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
