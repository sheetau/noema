"""Connect the same material surface on the K-zero-time slice in both frames."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.shared_reference import definition
from scripts import physical_meaning_heading_visible_profile as profile
from scripts.physical_meaning_heading_visible_profile import ROOT,PhysicalMeaningHeadingVisibleVocabulary,write_once
from scripts import check_einstein_sphere_setting_visible as previous
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

SOURCE='examples/v016/einstein-sphere-zero-slice-visible-v1.noema'
BRIDGE='data/einstein-sphere-zero-slice-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-sphere-zero-slice-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS
NEW_DEFINITIONS=['ste', 'stf', 'ejfr', 'ejfs', 'ejft', 'ejfu', 'ejfv', 'ejfw', 'ejfx', 'ejfy', 'ejfz', 'ejf2']
SENTENCES={'zh2': (54, 3)}
SPANS={}
ROLE_ASSIGNMENTS={}
FORWARD_MAPS={}
LOCAL_NAMES=['ste', 'stf', 'ejfr', 'ejfs', 'ejft', 'ejfu', 'ejfv', 'ejfw', 'ejfx', 'ejfy', 'ejfz', 'ejf2', 'zh2']
READINGS=('data/einstein-sphere-zero-slice-source-reading-v1.json',)
REVIEWS=('data/einstein-sphere-zero-slice-u0112-review-v1.json',
 'data/einstein-sphere-zero-slice-u0113-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0112–u0113を原刊903頁へ照合する。dieser Oberflächeは直前の同じ物体zhwの境界を指す。閉球連続体という前の明示した読みと、同じ半径zhx・速度zb7・光速tc・K/kを保持する。',
 '対象はKのt=0という一つの同時刻断面である。比較元ejftも同じK零断面の出来事を選び、その同じ出来事のk記録を用いる。k側のτ=0は要求せず、全k時刻の球面記述を一つのK断面と論理的に同一視しない。',
 '期間は各系の座標規約に従う。扱うK零断面の表面記録がkの対象期間にも属する範囲として読む。これは対象区間の選択であり、二系の区間端や時刻値の一致ではない。表面に対応するk記録が欠ければejftを真としない。K側では零時刻の全適格記録を扱い、表面の正例だけへ選別しない。',
 'ejfsは独立な占有領域の境界と指定式の双方向の一致を全記録に課し、非空の表面記録を要求する。全物質点の履歴・形状・記録存在はejffから保つ。任意の実数四組が測定済みであることや、有限標本が全連続体を尽くすことは追加しない。',
 'M0199の分母は(√(1−(v/V)²))²であり、√を消してからさらに二重に二乗する誤りを避ける。横のy²,z²へ縮小係数を掛けず、右辺は同じR²である。stfは同じβ・速度・光速の許容域とt=0を保持する。',
 'ausgedrücktは既出の最終四式を用いて同じ表面をK座標で表す提示としてzd3へ接続する。著者の書換えの帰属と、処理系による代数的・物理的証明を区別する。新しい変換法則や同時性の規約を導入しない。',
 '有限検査は現在の出来事と二記録、両方向の表面一致、t=0の選択、実切断の有理境界例を点検する。保存された旧多項式証拠は数値核の関係を支えるが、旧zhu/shdの物質境界・座標解釈を現行の根拠として復活させない。',
 '続くu0114–u0115の回転楕円体という形状分類と三半軸、u0116以降の一般形状への帰結は別の後続の主張として残す。',
 '原刊903頁の字下げを照合し、第54段落の第三文として本文と表示式を結ぶ。zh2は座標と零時刻の指定を含む全12トークンの文で、直前のeisn6とは別の箇所である。',
 '既存12定義と文位置参照を再利用する。共通375語、アルファベット、任意profile58/802語を維持し、新しい一般語彙や参照型を追加しない。']


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
    for n in _references(c.document['statements'][166:167]):visit(n)
    require(len(seen)==256,'Sphere-zero-slice source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][166:167])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','home',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    result['statements']=renamed(doc['statements'][141:142],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==2,'Source selection changed')
    text=' '.join(row['text'] for row in segments);tokens=text.split()
    require(len(tokens)==12 and tokens[-2:]==['[M0198]:','[M0199]'],'Zero-time sentence boundary changed')
    return dict(rule='Adopted paragraph54 continues after its first displayed equation without a new paragraph indent; sentence3 includes the coordinate/time qualification and displayed equation. Whitespace tokens; final period is inside M0199.',
        sentences={'zh2':dict(position=[54,3],tokens=tokens,text=text)},spans={})


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in (112,113)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-sphere-zero-slice-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[166],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles={},role_definitions=[],forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},reference_anchors={},
        new_public_relations=0,new_reference_primitives=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=58,core_edition=12,new_source_assertions=1,total_source_assertions=111,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible sphere-zero-slice document differs');return result


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
    prior_path='reports/einstein-sphere-setting-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/physical_meaning_heading_visible_profile.py','scripts/check_einstein_sphere_zero_slice_visible.py',
        'scripts/visible_physical_meaning_heading_visible_collection.py','tests/test_sphere_zero_slice_visible.py','docs/einstein-sphere-zero-slice-visible-v1.md',
        'scripts/check_sphere_zero_slice.py','scripts/compose_sphere_zero_slice.py','examples/v014/sphere-zero-slice-core.noema','reports/sphere-zero-slice-v1.json',
        'scripts/check_sphere_slice.py','scripts/compose_sphere_slice.py','examples/v014/sphere-slice.noema','reports/sphere-slice-v1.json',
        'scripts/check_final_transform_claim.py','scripts/check_four_coordinate_claim.py','scripts/check_transverse_measured_length.py',
        'scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved sphere-zero-slice bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-sphere-zero-slice-visible-evidence-1',core_words=375,profile_words=802,profile_edition=58,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=111,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
