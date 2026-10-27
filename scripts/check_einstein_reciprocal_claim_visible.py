"""Connect mutual rest, identity and the attributed reciprocal-scale conclusion."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.shared_reference import definition
from scripts import third_frame_claim_visible_profile as profile
from scripts.third_frame_claim_visible_profile import ROOT,ThirdFrameClaimVisibleVocabulary,write_once
from scripts import check_einstein_third_frame_claim_visible as previous
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

SOURCE='examples/v016/einstein-reciprocal-claim-visible-v1.noema'
BRIDGE='data/einstein-reciprocal-claim-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-reciprocal-claim-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS
NEW_DEFINITIONS=['sro', 'ejbq', 'ejbr', 'ejbs', 'ejbt', 'ejbu', 'ejbv', 'ejbw', 'ejbx', 'ejby', 'ejbz', 'ejb2', 'ejb3', 'ejb4', 'ejb5', 'ejb6']
SENTENCES=dict(reciprocalpremises=(50,1),zgs=(50,2))
SPANS=dict(zgq=('reciprocalpremises',1,19),zgr=('reciprocalpremises',20,35))
ROLE_ASSIGNMENTS={}
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS]
READINGS=('data/einstein-reciprocal-claim-source-reading-v1.json',)
REVIEWS=('data/einstein-reciprocal-claim-u0095-review-v1.json','data/einstein-reciprocal-claim-u0096-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['固定u0095とu0096を原刊901頁末から902頁冒頭へ照合する。空間式にtが現れない理由、二系の相互静止、恒等変換でなければならないという推論と明白さ、したがって同じφの正負値の積1という三段を保つ。',
 '時間を含まないは、既出四連鎖等式の最終三位置式が同じ位置成分と速度だけの倍率で書かれ、時刻値を右辺に取らないという読み。三式はejbrで実際に合成し、同じ現在の全対応記録へ適用する。時間式自体を無視又は削除する意味ではない。',
 '相互静止は、両向きのeiojによる全固定配置・全比較時点の履歴の共通速度三成分が零という読み。時計内部の針まで停止させず、相対静止だけで二系の尺度や時計率が同一とはしない。',
 '恒等変換は同じ対象出来事のKとK′の四座標値全ての一致。記録識別子や二系個体を同一とせず、同じ値の別記録を許す。原点だけの一致や三位置だけの一致へ弱めない。',
 'sein mußは既存zcの、その前提から結論が従わなければならないという推論の帰属で保持し、ist '
 'klarは既存zdgで同じ結論の明白さの提示として保つ。無条件の論理的真理、実験的実証又は処理系の証明認定に替えない。',
 '一般には相対静止と共通零点だけから尺度・時計率を含む恒等性は導けない。この点を原文にない校正条件で修理せず、著者が述べる推論を記述する。積1の導出にも原文にない非零証人を前提として補わない。',
 'sroは同じ正規化後φ=spcのvと−vの有効な値と積1。積が1でも各値は1とは限らず、負の組も式だけでは排除しない。後続の棒の長さによる対称性や符号規約を先取りしない。',
 '定義の意味と原刊の通読判断、有限対照・保存済み代数証拠、著者の主張の真理を区別する。未知入力の拒否と実切断の全域を有限標本で置換しない境界を保つ。',
 '原刊901頁末から902頁冒頭へ続く第50段落を2文として参照する。第1文の1–19トークンが相互静止、20–35が恒等性の推論。第2文はEs ist also:から積1の表示・句点までを含む。',
 '固定転記の[M0162]undは空白がないため第5トークンとして保存する。原文表記は修正せず、数学内部の空白は境界としない。',
 '既存16定義と文・部分範囲参照を再利用する。新しい基本語・規約・参照型は追加せず、profile55/796語と共通375語・アルファベットを維持する。']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=ThirdFrameClaimVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return ThirdFrameClaimVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][148:151]):visit(n)
    require(len(seen)==240,'Reciprocal-claim source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][148:151])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','birdone',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][123:126],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==2,'Source selection changed')
    pieces=segments[0]['text'].split('. ')
    require(len(pieces)==2 and pieces[0].startswith('Da die Beziehungen') and pieces[1]=='Es ist also:' and segments[1]['text']=='[M0169].','Sentence boundary changed')
    texts=[pieces[0]+'.',pieces[1]+' '+segments[1]['text']];tokens=[s.split() for s in texts]
    require([len(t) for t in tokens]==[35,4] and tokens[0][4]=='[M0162]und' and tokens[0][19:23]==['und','es','ist','klar,'],'Token boundary changed')
    return dict(rule='Fixed whitespace tokens; retain [M0162]und adjacency; 1-based inclusive spans; formula and final period continue the second sentence.',
        sentences={n:dict(position=list(SENTENCES[n]),tokens=ts,text=text) for n,text,ts in zip(SENTENCES,texts,tokens,strict=True)},
        spans={n:list(p) for n,p in SPANS.items()},anchor='One paragraph across pages901–902 after the third-frame equations.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(95,97)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-reciprocal-claim-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[148,149,150],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        new_public_relations=0,new_reference_primitives=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=55,core_edition=12,new_source_assertions=3,total_source_assertions=95,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible reciprocal-claim document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['reciprocalpremises'],35),(values['zgs'],4)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    span_keys={(values['eirf'],values[node],start,values[node],end,values['ri']) for node,start,end in SPANS.values()}
    def span(document,first,start,last,end,context):
        key=(document,first,TextPresentation.coordinate(start),last,TextPresentation.coordinate(end),context)
        if key in span_keys:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-third-frame-claim-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/third_frame_claim_visible_profile.py','scripts/check_einstein_reciprocal_claim_visible.py',
        'scripts/visible_third_frame_claim_visible_collection.py','tests/test_reciprocal_claim_visible.py','docs/einstein-reciprocal-claim-visible-v1.md',
        'scripts/check_reciprocal_claim.py','scripts/compose_reciprocal_claim.py',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','scripts/check_first_principle.py','scripts/check_material_relative_frame.py','scripts/check_four_coordinate_claim.py','examples/v014/reciprocal-claim-core.noema','reports/reciprocal-claim-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved reciprocal-claim bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-reciprocal-claim-visible-evidence-1',core_words=375,profile_words=796,profile_edition=55,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=3,total_source_assertions=95,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
