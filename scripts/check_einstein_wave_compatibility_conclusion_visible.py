"""Connect the same moving wave and the attributed compatibility conclusion."""
from copy import deepcopy
from functools import lru_cache,wraps
from threading import local
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
from scripts import wave_compatibility_conclusion_visible_profile as profile
from scripts.wave_compatibility_conclusion_visible_profile import ROOT,WaveCompatibilityConclusionVisibleVocabulary,write_once
from scripts import check_einstein_spherical_equation_rewrite_visible as previous
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

SOURCE='examples/v016/einstein-wave-compatibility-conclusion-visible-v1.noema'
BRIDGE='data/einstein-wave-compatibility-conclusion-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-wave-compatibility-conclusion-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['ejal', 'ejam', 'ejan', 'ejao', 'ejap', 'ejaq', 'ejar', 'ejas', 'ejat', 'ejau', 'ejav']
SENTENCES=dict(movingwaveconclusionsentence=(47,1),compatibilityprovedsentence=(47,2))
SPANS=dict(zgf=('movingwaveconclusionsentence',1,16),zgg=('compatibilityprovedsentence',1,10))
ROLE_ASSIGNMENTS={}
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS]
READINGS=('data/einstein-wave-compatibility-conclusion-source-reading-v1.json',)
REVIEWS=('data/einstein-wave-compatibility-conclusion-u0091-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0091の二文全体を原刊901頁へ照合する。Die betrachtete Welleは同じzfu、bewegten Systemは既出のk=zbm、Vは同じtc。auchは既出のK球面波にkでの球面性を加える関係として読む。',
 '球面波は前段と同じ幾何学的な到来波面の読みを採る。全対象出来事の現在記録で到来と正時刻の球面式が過不足なく一致し、波の全構成光線と全適用伝播区間が同じ放出・系・Vへ結ばれる。振幅・偏光・波長やMaxwell場全体の追加はしない。',
 '伝播速度の範囲は検討中の波に属する全適用区間であり、kの他の波や全光源の法則を第一文へ加えない。途中の区間も対象に含め、途中区間の始出来事を元の放出出来事に無理に等置しない。',
 '二乗式ejafは未来方向・全到来一致・全波の区間速度をそれだけでは保証しない。本文はそのような帰結を著者が述べたことをzcで記述する。原著者の物理的推論の妥当性を翻訳の完成条件とせず、欠けた前提を著者の発話へ追加して推論を修理しない。',
 '旧sqzは正のφ・記録存在・同じ到来の追跡を加える旧座標規約上の十分条件として保存するが、この本文の依存には用いない。現在の本文で一般物理的導出を証明するとも、φが正・非零・1だとここで決まるとも述べない。',
 'Hiermitは先行の同じ波の設定・座標変換・両系の波の結論を指す。unsere beiden '
 'Grundprinzipienは現在の相対性内容eifjと真空光速度内容eifyであり、同じ物理的意味の許容設定eiscjで共に成立し得るeif5を使う。別々の設定で一つずつ成り立つことへ弱めない。',
 'ist gezeigtは同じ著者が同じ箇所の内容を証明済みと位置付けるuiで表す。単なる期待・未証明課題や検査器による証明認定に替えない。u0086で以前の段階に証明が未提示だったことを取り消さず、論述の進行を保つ。',
 '語義・対象範囲・量化・参照・帰結と証明済みの提示を全て記述する。有限対照の成功から、一般実数域・連続空間・全物理的モデルや原文との意味同値を自動証明したとはしない。後続u0092の未知φを決める課題とu0093以降の第三系は残る。',
 '採用した連続段落座標47の第一文16トークン・第二文10トークンをそれぞれ全体参照とする。式で分割された抽出body単位数を段落番号と混同しない。',
 '旧11合成定義とuiの意味規約1個を再利用する。共通375語を維持し任意53版788語、新参照型0個。旧sqzは本文依存へ戻さない。',
 '有限診断は復号したNative定義で行う。著者の帰結・証明済みの位置付けを、処理系による物理的証明の認定に変えない。']


_AUTHORING=local()


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=WaveCompatibilityConclusionVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return WaveCompatibilityConclusionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][143:145]):visit(n)
    require(len(seen)==314,'Wave-compatibility-conclusion source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][143:145])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
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
    result['statements']=renamed(doc['statements'][113:115],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==1,'Source selection changed')
    tokens=segments[0]['text'].split()
    require(len(tokens)==26 and tokens[:3]==['Die','betrachtete','Welle'] and tokens[15:17]==['[M0147].','Hiermit'] and tokens[-1]=='sind.','Sentence boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; 1-based inclusive positions; same adopted paragraph for both sentences.',
        sentences={'movingwaveconclusionsentence':dict(position=[47,1],tokens=tokens[:16],text=' '.join(tokens[:16])),
                   'compatibilityprovedsentence':dict(position=[47,2],tokens=tokens[16:],text=' '.join(tokens[16:]))},
        spans={n:list(p) for n,p in SPANS.items()},anchor='The same-wave and compatibility conclusions on page 901.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(91,92)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        entry=c.entries[old];decl=entry['declaration'];contract=profile.CONTRACTS[new]
        require(decl['parameters']==contract['parameters'] and decl['result']==contract['result'] and entry['arguments']==contract['arguments'] and entry['meaning_ja'].split('] ',1)[-1]==contract['meaning_ja'],'Source contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-wave-compatibility-conclusion-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[143,144],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={},
        semantic_review=SEMANTIC_REVIEW,profile_edition=53,core_edition=12,new_source_assertions=2,total_source_assertions=89,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible wave-compatibility-conclusion document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['movingwaveconclusionsentence'],16),(values['compatibilityprovedsentence'],10)]},
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
    prior_path='reports/einstein-spherical-equation-rewrite-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/wave_compatibility_conclusion_visible_profile.py','scripts/check_einstein_wave_compatibility_conclusion_visible.py',
        'scripts/visible_wave_compatibility_conclusion_visible_collection.py','tests/test_wave_compatibility_conclusion_visible.py','docs/einstein-wave-compatibility-conclusion-visible-v1.md',
        'scripts/check_wave_compatibility_conclusion.py','scripts/compose_wave_compatibility_conclusion.py',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','examples/v014/wave-compatibility-conclusion-core.noema','reports/wave-compatibility-conclusion-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved wave-compatibility-conclusion bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-wave-compatibility-conclusion-visible-evidence-1',core_words=375,profile_words=788,profile_edition=53,
        new_public_relations=1,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=89,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
