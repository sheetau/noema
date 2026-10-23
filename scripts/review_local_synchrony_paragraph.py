"""Review all six sentences of local time and the connected synchrony equation."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.check_einstein_principles_paragraph import calls
from scripts.compose_light_roundtrip_definition import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS as LAST_LIMITS
from scripts.compose_local_clock_valuation import LIMITS as FIRST_LIMITS
from scripts.compose_second_local_clock import LIMITS as SECOND_LIMITS
from scripts.compose_local_times_only import LIMITS as THIRD_LIMITS
from scripts.compose_equal_light_times import LIMITS as FOURTH_LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
STEMS=('local-clock-valuation','second-local-clock','local-times-only','equal-light-times','light-roundtrip-definition')
READINGS=tuple('data/'+s+'-reading-v1.json' for s in STEMS)
REPORTS=tuple('reports/'+s+'-v1.json' for s in STEMS)
DOCS=tuple('docs/'+s+'-v1.md' for s in STEMS)
SOURCES=tuple('data/einstein-'+s+'-source-reading-v1.json' for s in ('local-clock','second-local-clock','local-times-only','equal-light-times','light-roundtrip-definition'))
REVIEWS=('data/einstein-local-synchrony-paragraph-review-v1.json','data/einstein-synchrony-equation-review-v1.json')
ORDER=list(range(234,240))
INTERPRETATION=FIRST_LIMITS[:-1]+SECOND_LIMITS[:-1]+THIRD_LIMITS[:-1]+FOURTH_LIMITS[:-1]+LAST_LIMITS[:-1]+[
 'u0013の六文とu0014の数式を一続きの定義説明として読む。二つの局所時刻の可能性、追加規定なしでの比較不能、定義上の等片道時間、仮想的な具体的一往復、同期という語の定義条件を順に保持する。',
 'u0013は955非空白本文文字と28数式出現、u0014は本文文字を持たない式M0030である。範囲の分割は保存原文に従い、第六文のwennを次単位の式へ接続する。二単位の判断を保存するが、式を本文文字数へ重複加算しない。',
]
REASONS=(
 '固定u0013全1347文字を、[0,251)、[252,560)、[561,821)、[822,1070)、[1071,1347)で覆い、文間の空白以外の欠落・重複がない。原刊893–894頁を照合した五記録とM0002–M0029全28出現を確認した。直後のu0014全7文字は数式プレースホルダーM0030であり、そのMathMLと原刊の式を別単位として丸ごと保持する。',
 'A側の局所評価、同じ構成のB時計を加える条件と意思、追加規定なしの比較不能、これまで局所二時間だけという限定、共通時間の定義可能性と等片道時間、仮想的な一光の往復、全必要試行の同期条件を保持する。三時刻の二つの差と数値的等値、条件・可能性・否定・全範囲を省かない。',
 'A/B時計eisib/eisikと地点ziq/zir、同じ系ra・単位rbを全六文で共有する。局所規約eisiw/eisixを前二文のeik4へ結び、後者の共通時間eisjdを第三文の未定義の種類へ照応する。第五文の試行eisjjと同じ光・出発・反射・帰着をqc–qkへ結び、t_A/eisjo、t_B/eisjp、t′_A/eisjqを第六文のeimsにも同じ順序で使う。',
 '同じ著者・論説への六文の帰属と本文順序を保持する。条件付き局所評価、構成一致を追加する意思と挿入、二つのaber、セミコロンの説明、定義可能性、接続法による仮想設定、nämlichの具体化、definitionsgemäßとwennの定義採用を区別する。引用から実際の物理的成立や数式の真理を導かない。',
 '局所的読取りを遠隔の共通時刻へ先取りせず、bisherの未定義を将来まで固定しない。時計の構成一致を初期位相の一致とせず、光の方向や反射・帰着を取り違えない。第四文へ実際の反射を余計に要求せず、第五文で初めて同じ光の反射を固定する。真空光速度の値、任意個数の時計の整合性や後続の対称性・推移性を加えない。',
 '局所観測と指針位置の付与、完全な構成記述、定義済み範囲と追加規定の要否、始終時刻の差、定義案と採用可能な結果、同じ光の一往復と反射、全必要試行・三読み・数値等値、著者の仮想採用と定義採用を意味規約付きの基本関係と既存の合成へ分けた。一文の真偽を原語の綴りや未説明の一入力へ置き換えていない。',
 '五つの局所報告、四つの文別読解と接続した二文の読解、原刊照合、現行本文・依存定義・意味規約を固定した。局所規則・全特徴比較・論述段階・全手続き・全比較組・両方向の差・全試行の引数・非事実的な提示を検査した。有限例を実測・実数全域の証明・意味同値の自動証明に昇格させない。',
 '二地点での局所時間から共通時間の不足を指摘し、追加の定義を提示し、その内容を仮想的一往復と同期式で具体化する六文と式を通読した。第六文のwennをu0014の式へ接続し、両単位を合わせて明示した解釈の下で未処理の内容・参照・範囲・提示はないと判断する。後続u0015の任意個数の同期を矛盾なく実現できるという仮定は別の未完単位である。',
)


@lru_cache(None)
def connection_checks():
    catalog=load_catalog(ROOT,BASIS);ds={d['name']:d for d in catalog.document['declarations']}
    c=lambda n:dict(kind='call',symbol=n,arguments=[])
    quoted=lambda n:dict(kind='quote',body=c(n))
    def get(parent,callee):
        found=[n['arguments'] for n in calls(ds[parent]['body']) if n['symbol']==callee];assert len(found)==1,(parent,callee);return found[0]
    nodes=('eish2','eisio','eisiz','eisjh','eisjr','eisjs');roots=('eilb','eilo','eil6','eimg','eimo','eimr');messages=('eila','eiln','eil5','eimf','eimn','eimq')
    for index,root,node,message,prior in zip(ORDER,roots,nodes,messages,('eishs',)+nodes[:-1]):
        assert catalog.document['statements'][index]['body']==c(root)
        assert get(root,'eir3')==[c(node),c('rd'),c('eirf'),quoted(message),c('ri')]
        assert get(root,'ue')==[c(prior),c(node),c('ri')]
        assert ds[message]['body']['kind']=='message' and ds[message]['body']['force']=='assert'
    assert get('eik7','eiky')[:3]==[c('eisib'),c('ziq'),c('ra')]
    assert get('eilf','eiky')[:3]==[c('eisik'),c('zir'),c('ra')]
    assert get('eily','eilx')[:8]==[c(n) for n in ('eisiw','eisix','eisib','eisik','ziq','zir','ra','rb')]
    assert get('eime','eimd')[:11]==[c(n) for n in ('eisje','eisjf','eisjd','eisiw','eisix','eisib','eisik','ziq','zir','ra','rb')]
    assert get('eiml','eimh')[:13]==[c(n) for n in ('eisib','eisik','ziq','zir','eisjk','eisjl','eisjm','eisjn','ra','rb','eisjo','eisjp','eisjq')]
    assert get('eims','eimi')==[c(n) for n in ('eisjo','eisjp','eisjq')]
    adopt=get('eimp','eisju')
    assert adopt[:11]==[c(n) for n in ('eisjs','rd','eisib','eisik','ziq','zir','ra','rb','eisje','eisjd','eisjj')]
    assert adopt[11:13]==[quoted('eims'),dict(kind='quote',body=dict(kind='function_ref',symbol='eimk'))]
    assert get('eimm','ug')[2]==quoted('eiml')
    assert get('eimo','eisjt')[2:4]==[quoted('eime'),quoted('eiml')]
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    return dict(six_messages_author_and_order_checked=True,same_clock_place_and_time_references_across_six_sentences=True,displayed_equation_bound_to_same_hypothetical_three_readings=True)


@lru_cache(None)
def coverage_checks():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u,w=inv['units'][12:14];covered=set();maths=[]
    for p,span,index in zip(READINGS[:4],((0,251),(252,560),(561,821),(822,1070)),ORDER[:4]):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256'])
        assert rec['unit']==u['id'] and rec['range']==list(span) and rec['source']==u['text'][slice(*span)] and rec['source_text_sha256']==u['text_sha256']
        assert rec['selection']==selection_binding(catalog,[index]);assert not covered.intersection(range(*span));covered.update(range(*span));maths.extend(rec['math'])
    last=json.loads(read(READINGS[-1]));validate_hashes(ROOT,last['source_sha256']);assert last['selection']==selection_binding(catalog,[238,239])
    for s,z,span in zip(last['segments'],(u,w),((1071,1347),(0,7))):
        assert s['unit']==z['id'] and s['range']==list(span) and s['text']==z['text'][slice(*span)] and s['unit_sha256']==z['text_sha256']
        if z==u:
            assert not covered.intersection(range(*span));covered.update(range(*span))
        maths.extend(s['math'])
    assert all(i in covered or c.isspace() for i,c in enumerate(u['text']))
    assert [m['id'] for m in maths]==u['math_ids']+w['math_ids']
    original={m['id']:m for m in inv['math']};assert all(m['sha256']==original[m['id']]['sha256'] for m in maths)
    chars=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']));assert chars==955
    return dict(paragraph_nonblank_prose_characters=chars,all_29_math_occurrences_checked=True,six_sentences_and_display_connected_without_gaps=True)


@lru_cache(None)
def review_record(which):
    connection_checks();coverage_checks();catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][12+which];maths={m['id']:m for m in inv['math']}
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,*READINGS,*REPORTS,*DOCS,*SOURCES,'scripts/review_local_synchrony_paragraph.py','tests/test_local_synchrony_paragraph_review.py','scripts/check_einstein_principles_paragraph.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (*READINGS,*REPORTS,*SOURCES):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[dict(id=n,sha256=maths[n]['sha256']) for n in u['math_ids']]),selection=selection_binding(catalog,ORDER if which==0 else [239]),source_order_statements=ORDER if which==0 else [239],interpretation=INTERPRETATION,limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明・物理的実測による妥当性の証明ではない。','後続u0015以降と二作品全体の記述は未完で、目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=list(SOURCES),formal_checks=list(REPORTS),semantic_reading=list(DOCS)),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for i,p in enumerate(REVIEWS):write_exact(ROOT/p,json.dumps(review_record(i),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    pins={};active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    for i,p in enumerate(REVIEWS):
        rec=review_record(i);assert json.loads(read(p))==rec
        validate_review(ROOT,p,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
        merge_pins(pins,rec['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='local_clock_time_to_light_synchrony_paragraph_and_equation_holistically_reviewed',document=FULL,source_units={'einstein-1905:u0013':955,'einstein-1905:u0014':0},connections=connection_checks(),coverage=coverage_checks(),whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
