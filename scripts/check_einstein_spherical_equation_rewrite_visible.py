"""Connect the same-event sphere-equation rewrite and its calculation assessment."""
from copy import deepcopy
from functools import lru_cache
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from noema.identifiers import load_annotations
from scripts.shared_time import allof
from scripts.shared_reference import definition
from scripts import rest_spherical_wave_visible_profile as profile
from scripts.rest_spherical_wave_visible_profile import ROOT,RestSphericalWaveVisibleVocabulary,write_once
from scripts import check_einstein_rest_spherical_wave_visible as previous
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

SOURCE='examples/v016/einstein-spherical-equation-rewrite-visible-v1.noema'
BRIDGE='data/einstein-spherical-equation-rewrite-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-spherical-equation-rewrite-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS
NEW_DEFINITIONS=['ejae','ejaf','ejag','ejah','ejai','ejaj','ejak']
SENTENCES=dict(sphericalequationrewritesentence=(46,1))
SPANS=dict(zge=('sphericalequationrewritesentence',1,14))
ROLE_ASSIGNMENTS={}
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS]
READINGS=('data/einstein-spherical-equation-rewrite-source-reading-v1.json',)
REVIEWS=('data/einstein-spherical-equation-rewrite-u0089-review-v1.json','data/einstein-spherical-equation-rewrite-u0090-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SOURCE_READINGS=['u0089の全文とu0090の表示式・句点を原刊901頁へ照合する。Diese Gleichungは直前の同じ波のK球面式ejaa、unsere '
 'Transformationsgleichungenは既出の現在の四式ei7cを指す。',
 'wir ... transformieren und erhaltenは著者による論述上の計算提示と読む。読者が実際に計算したことや計算機の実行履歴を加えず、同じ著者・論説・第三節・箇所へ帰属する。',
 '同じ到来出来事の現在K/k記録をejaeで結び、k記録の存在を要求した上で全ての対応するk記録へ式を適用する。任意の到来点を一つの成功点へ固定せず、別の出来事の座標や欠けたk記録による空の全称で済ませない。',
 '四式はei7cの全現在座標範囲を保ち、同じφ(v)=a(v)β(v)、V,vと原点の規約を使う。u0085で述べた一般の加法定数は、この共通零原点の波の設定へ新たに足さない。',
 'ξ²+η²+ζ²=V²τ²は同じk記録の三位置と時刻の二乗式sqkである。二乗式だけから未来側、φの正値やφ=1、kでの全到来波面、二原理の両立性の証明完了を導かない。これらの後続記述はu0091以降へ残す。',
 'einfacher '
 'Rechnungは、同じ計算の有限手順列について文脈上の負担合計が低いという明示的な読みを採る。既存s2w/s2x/s2yとzlw/zlx/zla/zlb/zlcを合成し、原文にない手順数・数値閾値・実行時間を固定しない。',
 '低負担の計算は、四式とK波面を含む同じ前提ejagから同じk式ejafまでつながる方法として存在量化する。許容変形の根拠と負担の尺度は既存の意味規約に従い、評価内容の提示から一般的な証明認定を行わない。',
 '保存済みの有理多項式証拠では変換後の球面残差がφ²倍になる。現在の記録・全称範囲・引用・計算評価の有限対照はその接続を検査するものであり、一般実切断上の物理的導出や原文との意味同値の自動証明ではない。']
SEMANTIC_REVIEW=[*SOURCE_READINGS,
    '第46段落第一文の13トークンと末尾の表示式・句点を合わせた14トークン全体をzgeの本文箇所とする。数式識別子は意味の代用にしない。',
    '既存の7合成定義と本文参照を使う。意味規約と参照型は追加せず、共通375語・任意52版787語をそのまま維持する。',
    '検査の対象は円文字から復号したNative定義である。旧モデルの再利用と旧検査結果の再利用を区別する。']


@lru_cache(maxsize=1)
def vocabulary():return RestSphericalWaveVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][142:143]):visit(n)
    require(len(seen)==286,'Spherical-equation-rewrite source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][142:143])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {}
def role_definitions():return []


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][112:113],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==2,'Source selection changed')
    tokens=segments[0]['text'].split()+[segments[1]['text']]
    require(len(tokens)==14 and tokens[:2]==['Diese','Gleichung'] and tokens[-1]=='[M0146].','Sentence or equation boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; the displayed equation completes the sentence; 1-based inclusive positions.',
        sentences={'sphericalequationrewritesentence':dict(position=[46,1],tokens=tokens,text=' '.join(tokens))},
        spans={n:list(p) for n,p in SPANS.items()},anchor='The transformation sentence and displayed equation on page 901.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(89,91)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-spherical-equation-rewrite-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[142],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={},
        semantic_review=SEMANTIC_REVIEW,profile_edition=52,core_edition=12,new_source_assertions=1,total_source_assertions=87,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible spherical-equation-rewrite document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['sphericalequationrewritesentence'],14)]},
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
    write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved spherical-equation-rewrite bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-rest-spherical-wave-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/rest_spherical_wave_visible_profile.py','scripts/check_einstein_spherical_equation_rewrite_visible.py',
        'scripts/visible_rest_spherical_wave_visible_collection.py','tests/test_spherical_equation_rewrite_visible.py','docs/einstein-spherical-equation-rewrite-visible-v1.md',
        'scripts/check_spherical_equation_rewrite.py','scripts/compose_spherical_equation_rewrite.py',
        'scripts/check_calculation_discourse.py','examples/v014/spherical-equation-rewrite-core.noema','reports/spherical-equation-rewrite-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-spherical-equation-rewrite-visible-evidence-1',core_words=375,profile_words=787,profile_edition=52,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=87,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
