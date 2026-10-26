"""Connect all-space measurements and event-coordinate time instructions."""
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
from scripts import event_coordinate_visible_profile as profile
from scripts.event_coordinate_visible_profile import ROOT,EventCoordinateVisibleVocabulary,write_once
from scripts import check_einstein_clock_site_visible as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts import check_einstein_two_principles as principles
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-event-coordinate-visible-v1.noema'
BRIDGE='data/einstein-event-coordinate-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-event-coordinate-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiy2 eiy3 eiy5 eiy6 eiy7 eiyu eiyv eiyw eiyx eiyy eiyz eiza eizb sgt sgv sgw sgx sgy sgz shb shh shl'.split()
SENTENCES=dict(zda=(31,1))
SPANS=dict(zdb=('zda',28,42))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS]
READINGS=('data/einstein-event-coordinate-task-source-reading-v1.json',)
REVIEWS=('data/einstein-event-coordinate-task-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return EventCoordinateVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][108:109]):visit(n)
    require(len(seen)==221,'Event coordinate source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][108:109])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','give',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][78:79],inverse);return normalize_document(result)



def text_boundaries():
    row=author.read(READINGS[0]);tokens=row['text'].split()
    require(len(tokens)==42 and tokens[27:35]==['und','es','ist','nun','die','Aufgabe','zu','lösen,'] and tokens[-1]=='finden.','Equation task span changed')
    return dict(rule='Whitespace-delimited transcription; math placeholders atomic; punctuation attached; 1-based inclusive positions.',
        sentences={'zda':dict(position=[31,1],tokens=tokens)},spans={'zdb':['zda',28,42]},
        anchor='The whole sentence is anchored at its opening correspondence claim; the subsequent equation task has a separate token span.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};row=author.read(READINGS[0]);unit=units[row['unit']]
    require(row['unit']=='einstein-1905:u0046','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-event-coordinate-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[108],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=row['math'],semantic_review=['u0046全289文字・227本文文字を対象とする。原刊898頁ではWertsystemと続けて印字され、固定本文のWert Systemという分かち書きは同じ値の組を指すものとして読む。固定原文を変更しない。',
 'Zu jedemの対象は、その系で出来事の場所と時刻を完全に指定する有効な四座標の全範囲である。対象出来事zc4も同じ全比較範囲を保持し、成功する標本に限定しない。任意の実数四組が物理的に実現するという全域性は加えない。',
 '場所の完全な特定は、現在の三軸測定eixuを満たす全地点を比較し、shlで唯一の場所を要求するという内容として表す。前段の全空間測定eixsを受け、測れなかった地点を除いて唯一と見なさない。この一意性の条件を幾何学的に証明したと主張するわけではない。',
 '時刻は同じ出来事の同じ場所におけるeiyiの一意な局所表示と、eiyjの系内時点の値に一致する。時点の記述名の一意性や、同じ時空位置における出来事個体の一意性を要求しない。時計のない地点への新しい時刻拡張は加えない。',
 '同じ一つの出来事に二系の四座標を結ぶ。全対象出来事の両系での値の存在・一意性と、同じK側の値から同じk側の値へ対応する条件を保つ。別記録の同値を数値の一致で扱い、逆方向の一意性や両系の値の一致は追加しない。',
 'M0081のx,y,z,t、M0082のk、M0083のξ,η,ζ,τを既出の同じ系・三軸・時計規則へ接続する。tの規則eiwtを変更せず、新たな命名宣言や二系共通の瞬間を補わない。',
 '後半は今解くべき課題として方程式系を見いだすことの提示である。非空の有限方程式列を左右の実数値を返す関数の列として扱い、対応範囲内で全式の解と対応が過不足なく一致することを求める。特定の代数構文・線形性・Lorentz変換や探索アルゴリズムを先取りしない。',
 '対応の主張と課題は同じ第三節の仮定の範囲内に帰属する。引用から実測・解の存在・発見済みを導かない。有限対照検査、原文の意味判断、一般の物理的真理や同義性の証明は区別する。',
 '文全体を第31段落第一文として、その冒頭の対応主張へ固定する。後半の課題zdbは同文28–42トークン。二箇所の区別と順序を保持し、質問の参照から答えの存在や発見済みを導かない。',
 '22旧合成定義と2旧契約を再利用し、既存の四成分・時間役割・八つの量の呼称を維持する。新しい原文専用の意味原子は追加しない。'],
        profile_edition=39,core_edition=12,new_source_assertions=1,total_source_assertions=53,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible event coordinate document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}
SITUATIONS=previous.SITUATIONS

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['zda'],42)]},
        {(values['eirf'],values['zda'],28,values['zda'],42,values['ri']):values['zdb']})

def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first==values['zda'] or last==values['zda']:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved event coordinate bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-clock-site-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/event_coordinate_visible_profile.py','scripts/event_coordinate_visible_profile_contracts.py','scripts/check_einstein_event_coordinate_visible.py',
        'scripts/visible_event_coordinate_visible_collection.py','tests/test_event_coordinate_visible_profile.py','docs/einstein-event-coordinate-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-event-coordinate-visible-evidence-1',core_words=375,profile_words=746,profile_edition=39,
        preserved_source_relations=2,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=53,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
