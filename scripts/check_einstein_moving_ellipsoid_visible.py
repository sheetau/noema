"""Connect general moving solid ellipsoids, arbitrary centers and ordered semiaxes."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.shared_reference import definition
from scripts import physical_meaning_heading_visible_profile as profile
from scripts.physical_meaning_heading_visible_profile import ROOT,PhysicalMeaningHeadingVisibleVocabulary,write_once
from scripts import check_einstein_sphere_zero_slice_visible as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts import check_einstein_two_principles as principles
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_parallel_collection import decode_files
from scripts.visible_parallel_render import iter_rendered_volumes
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require
from scripts.visible_selection_vocabulary import SelectionVocabulary
from scripts.visible_vocabulary_session import vocabulary_session

SOURCE='examples/v016/einstein-moving-ellipsoid-visible-v1.noema'
BRIDGE='data/einstein-moving-ellipsoid-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-moving-ellipsoid-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS
NEW_DEFINITIONS=['stg', 'sth', 'ejf3', 'ejf4', 'ejf5', 'ejf6', 'ejf7', 'ejga', 'ejgb', 'ejgc', 'ejgd', 'ejge', 'ejgf']
SENTENCES={'zh3': (54, 4)}
SPANS={}
ROLE_ASSIGNMENTS={}
FORWARD_MAPS={}
LOCAL_NAMES=['stg', 'sth', 'ejf3', 'ejf4', 'ejf5', 'ejf6', 'ejf7', 'ejga', 'ejgb', 'ejgc', 'ejgd', 'ejge', 'ejgf', 'zh3']
READINGS=('data/einstein-moving-ellipsoid-source-reading-v1.json',)
REVIEWS=('data/einstein-moving-ellipsoid-u0114-review-v1.json', 'data/einstein-moving-ellipsoid-u0115-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0114–u0115を原刊903頁へ照合する。Ein starrer '
 'Körperは、この二系・速度・尺度の設定で静止側に球形を持つ任意の剛体についての一般的な帰結と読む。物体・半径・静止側中心を量化し、特定zhw・固定R・原点中心だけへ範囲を縮めない。',
 '静止して測れば球形という前提は、同じ全物質点の剛性・静止・閉球の全位置被覆・現在測定記録に接続する。内部と境界を占める理想的な連続体という明示したモデルを継承し、全ての空洞を持つ球殻の語義を定めたとはしない。加速過程や過去に実施した測定の履歴は補わない。',
 'vom ruhenden System aus betrachtetはKの同時刻座標で形を記述すること。望遠鏡に届く光の見かけの画像とはしない。各系の時刻規約を保ち、Kとkの同時刻面を等置しない。',
 '運動中の形状はKの全対象時刻で述べる。静止側の任意中心(cx,cy,cz)はKで(cx/β+vt,cy,cz)となる表現を用い、形状の不変と空間集合の静止を区別する。時間零だけ又は一つの中心だけに限定しない。',
 '回転楕円体は三位置差の規格化二乗和で合成し、横二方向の同じ半軸により縦軸周りの回転対称性を表す。全物質点の包含と閉領域の全位置被覆、独立な物質境界と全現在記録の表面式の一致を共に保持する。',
 '原文のAchsenに付く三値は、表示通り中心から表面までの半軸として読む。順にR√(1−(v/V)²),R,Rであり、直径2Rや全方向の一様縮小に替えない。stgが正の縦半軸とR/β、R√(1−(v/V)²)の両表示を結ぶ。',
 'alsoは先の球面式・変換・零断面の式からの著者の帰結の提示。例の計算を全物体の数学的証明と認定せず、全ての適格物体についての主張内容と、その帰属を区別する。既存の0<v<Vの比較設定を継承する。',
 '全実数位置・時刻・半径・中心の量化を有限標本に変更しない。有限検査は区別例と引数・範囲を点検する。原著者の物理的主張の真理や、独立した意味同値の自動証明ではない。u0116以降の一般形状への収縮・極限・時計は後続である。',
 '原刊903頁で改段落のない続きとして第54段落の第四文へ接続する。zh3は一般の物体・観測系の挿入・半軸表示を含む33トークンの文全体で、句点はM0200内にある。',
 '既存13定義と文位置参照を再利用する。共通375語、固定アルファベット、任意profile58の802語を維持し、新しい一般語彙や参照型を追加しない。']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=PhysicalMeaningHeadingVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return PhysicalMeaningHeadingVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][167:168]):visit(n)
    require(len(seen)==264,'Moving-ellipsoid source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][167:168])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','above',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


@lru_cache(maxsize=1)
@_with_authoring_session
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)











def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][142:143],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==2,'Source selection changed')
    text=' '.join(row['text'] for row in segments);tokens=text.split()
    require(len(tokens)==33 and tokens[-4:]==['mit','den','Achsen','[M0200]'],'Ellipsoid sentence boundary changed')
    return dict(rule='Adopted paragraph54 continues after the zero-slice displayed equation without a new paragraph indent; sentence4 includes the generic body, viewing-system insertion and ordered semiaxes. Whitespace tokens; final period is inside M0200.',
        sentences={'zh3':dict(position=[54,4],tokens=tokens,text=text)},spans={})


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in (114,115)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-moving-ellipsoid-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[167],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles={},role_definitions=[],forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},reference_anchors={},
        new_public_relations=0,new_reference_primitives=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=58,core_edition=12,new_source_assertions=1,total_source_assertions=112,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible moving-ellipsoid document differs');return result


BASE=previous.BASE|{n:n for n in SENTENCES}
SITUATIONS=previous.SITUATIONS








def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    return result|dict(sentencereference=sentence)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-sphere-zero-slice-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/physical_meaning_heading_visible_profile.py','scripts/check_einstein_moving_ellipsoid_visible.py',
        'scripts/visible_physical_meaning_heading_visible_collection.py','tests/test_moving_ellipsoid_visible.py','docs/einstein-moving-ellipsoid-visible-v1.md',
        'scripts/check_moving_ellipsoid.py','scripts/compose_moving_ellipsoid.py','examples/v014/moving-ellipsoid-core.noema','reports/moving-ellipsoid-v1.json',
        'scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py',
        'scripts/check_final_transform_claim.py','scripts/check_four_coordinate_claim.py','scripts/check_transverse_measured_length.py',
        'scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved moving-ellipsoid bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-moving-ellipsoid-visible-evidence-1',core_words=375,profile_words=802,profile_edition=58,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=112,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
