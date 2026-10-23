"""Review the tentative definition and its actual local/remote limits together."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.check_einstein_principles_paragraph import calls
from scripts.compose_clock_definition_scope import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS as SCOPE_LIMITS
from scripts.compose_clock_definition_proposal import LIMITS as PROPOSAL_LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
SOURCE='data/einstein-clock-definition-source-reading-v1.json'
READINGS=('data/clock-definition-proposal-reading-v1.json','data/clock-definition-scope-reading-v1.json')
REPORTS=('reports/clock-definition-proposal-v1.json','reports/clock-definition-scope-v1.json')
DOCS=('docs/clock-definition-proposal-v1.md','docs/clock-definition-scope-v1.md')
REVIEW='data/einstein-clock-definition-paragraph-review-v1.json'
UNIT='einstein-1905:u0011'
INTERPRETATION=PROPOSAL_LIMITS[:-1]+SCOPE_LIMITS[:-1]+[
 '第一文の全困難の見かけの解決可能性と、第二文の局所に限った実際の十分性を分ける。第二文は前文の同じ案を限定し、遠隔では足りないという対比によって次段落の別方式の検討へつながる。第一文172文字と第二文373文字を全段落545文字として一度だけ数える。',
 '局所的な出来事一致は原刊脚注で示した理想化の下の対応入力であり、既に付与した遠隔の普遍的時刻から逆算する循環的な定義にはしない。各系列内の継起・課題の全必要条件・個別の充足・解手続きの適合性は規約を明示した入力である。手続きの同等性は両方向の適合範囲の一致として表し、手続きが存在することや同義性の自動証明を追加しない。',
]
REASONS=(
 '固定u0011全639文字・545非空白文字を二文[0,200)、[201,639)で覆い、原刊893頁に視認照合した。二文間の空白以外の欠落はない。数式・脚注番号はなく、前文の局所同時性に対する既存脚注の留保を無効化しない。',
 '自分の時計の短針の位置を時間に代える案、全ての定義上の困難を克服できるように思えるという留保、局所だけなら実際に十分だが異所系列の連結には不十分になる条件、遠隔出来事の時間的評価が同じ課題に帰着するという挿入を保つ。量化・可能性・場所限定・対比・条件を省かない。',
 'Eine solche Definitionを同じeisf5・eisf6へ結び、両文で同じ著者・時計eisf7・短針eisga・ra・尺度eisgbを用いる。時計の現在の場所と全対象出来事、各系列の全構成員、同じ規則と全必要条件、同じ対象を扱う解手続きの二つの適合範囲を固定する。',
 '第一文は見かけを留保した内容の主張、第二文は限定した十分性と不十分性を実際の内容として主張する。in der Tatの確認を局所の条件へ向け、aberの対比、oder以下の挿入、同じ著者・論説への帰属と二文の本文順序を保持する。',
 '局所の十分性を遠隔を含む全困難の解決へ拡張せず、不十分性を時計の故障・老朽化・全時間定義の不可能性へ替えない。列車・7時・日付・周期回数・全体静止・光伝播補正・遠隔同期の実装を原文へ補わない。近接場所を遠隔へ取り違えず、未知の充足を不成立と認めない。',
 '時間の定義課題、指針の位置と読みの規則、手段による困難の克服、議論上可能な見方と見かけの候補、局所的一致、出来事系列、課題の必要条件・充足と手続きの適合を意味規約付きの基礎関係へ分けて合成した。定義案・十分性・全量化を一文全体の未説明の真偽入力へ置き換えていない。',
 '二つの文別読解記録、局所報告、原刊画像の照合、依存定義と規約を固定する。時計と表示・対象の結合、全困難の共通成功結果、条件全体の十分性と既知の不充足、場所・系列の全範囲、両方向の課題同等性、引用の非実行を対照検査した。実数の全域を有限標本に替えていない。',
 '二文を続けて通読し、初期の解決の見込みから、その案の局所的な成立と遠隔への限界に進む論旨を保持していると判断する。明示した読みの下で内容・参照・範囲・提示の未処理項目はない。後続段落の光信号受信方式と観測者位置への依存は別の原文単位として残る。',
)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][10]
    assert u['id']==UNIT and len(u['text'])==639 and sum(not c.isspace() for c in u['text'])==545 and not u['math_ids']
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256'])
    for path,span,index,chars,segment in zip(READINGS,([0,200],[201,639]),(229,230),(172,373),source['segments']):
        rec=json.loads(read(path));validate_hashes(ROOT,rec['source_sha256'])
        assert rec['unit']==UNIT and rec['range']==span and rec['source_text_sha256']==u['text_sha256'] and rec['source']==u['text'][slice(*span)]
        assert rec['selection']==selection_binding(catalog,[index]) and rec['source_nonblank_characters']==chars
        assert segment['range']==span and segment['text']==rec['source'] and segment['unit_sha256']==u['text_sha256']
    ds={d['name']:d for d in catalog.document['declarations']}
    def get(parent,callee):
        result=[c for c in calls(ds[parent]['body']) if c['symbol']==callee];assert len(result)==1;return result[0]
    # The actual scope claim preserves exactly the candidate definition's objects.
    assert get('eij5','eijj')['arguments']==get('eijm','eijl')['arguments']
    def binders(node,kind):
        found=[]
        if isinstance(node,dict):
            if node.get('kind')==kind:found.append(node)
            for child in node.values():found.extend(binders(child,kind))
        elif isinstance(node,list):
            for child in node:found.extend(binders(child,kind))
        return found
    # Canonical formatting gives the existential and universal binders different
    # names; check the actual binding and compare the remaining fixed arguments.
    adequate=get('eijx','eisgl')['arguments'];inadequate=get('eijy','eisgl')['arguments']
    for parent,kind,arguments in (('eijx','forall',adequate),('eijy','exists',inadequate)):
        quantifiers=binders(ds[parent]['body'],kind);assert len(quantifiers)==1
        assert arguments[8]==dict(kind='variable',name=quantifiers[0]['variable'])
    assert adequate[:8]+adequate[9:]==inadequate[:8]+inadequate[9:]
    assert get('eij7','ue')['arguments']==[dict(kind='call',symbol=n,arguments=[]) for n in ('eisgc','eisgq','ri')]
    assert ds['eijp']['body']['force']==ds['eij6']['body']['force']=='assert'
    assert {'eijj','eij2','eij3','eij4'}<={c['symbol'] for c in calls(ds['eij5']['body'])}
    assert len([c for c in calls(ds['eijz']['body']) if c['symbol']=='eisgn'])==4
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,*READINGS,*REPORTS,*DOCS,'scripts/review_clock_definition_paragraph.py','tests/test_clock_definition_paragraph_review.py','tests/test_clock_definition_common_result.py','scripts/check_einstein_principles_paragraph.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,*READINGS,*REPORTS):
        rec=json.loads(read(path));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=UNIT,reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),selection=selection_binding(catalog,[229,230]),source_order_statements=[229,230],interpretation=INTERPRETATION,
        limits=['明示した解釈に基づくアシスタントの通読判断。独立査読、唯一の歴史的解釈、同義性の自動証明、時計の実測による妥当性の証明ではない。','後続の原文単位と二作品全体の記述は未完で、目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=list(REPORTS),semantic_reading=list(DOCS)),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    rec=review_record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    result=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    assert result['source_nonblank_characters']==545
    return dict(status='clock_definition_proposal_and_scope_holistically_reviewed',document=FULL,source_units={UNIT:545},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
