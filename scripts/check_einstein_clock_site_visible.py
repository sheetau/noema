"""Connect all-space measurements and clock-site time instructions."""
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
from scripts import clock_site_visible_profile as profile
from scripts.clock_site_visible_profile import ROOT,ClockSiteVisibleVocabulary,write_once
from scripts import check_einstein_parallel_choice_visible as previous
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

SOURCE='examples/v016/einstein-clock-site-visible-v1.noema'
BRIDGE='data/einstein-clock-site-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-clock-site-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiw4 eiw5 eiw6 eiw7 eix2 eix3 eixa eixb eixc eixd eixe eixf eixg eixh eixj eixk eixl eixm eixn eixo eixp eixq eixr eixs eixt eixu eixv eixw eixx eixy eixz eiya eiyb eiyc eiyd eiye eiyf eiyg eiyh eiyi eiyj eiyk eiyl eiym eiyn eiyo eiyp eiyq eiyr eiys eiyt sexd sgf sgg sgh sgi'.split()
SENTENCES=dict(zc2=(30,1),zc3=(30,2))
DESIGNATIONS=dict(eisne=('zc2',1),eisnf=('zc2',2),eisng=('zc2',3),eisnh=('zc2',4),eisni=('zc2',5),eisnj=('zc2',6),eisnl=('zc3',1))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*DESIGNATIONS]
READINGS=('data/einstein-clock-site-time-source-reading-v1.json',)
REVIEWS=('data/einstein-clock-site-time-review-v1.json',)
FORMS=dict(eisne='x',eisnf='y',eisng='z',eisnh='ξ',eisni='η',eisnj='ζ',eisnl='τ')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return ClockSiteVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][106:108]):visit(n)
    require(len(seen)==289,'Clock site source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][106:108])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(DESIGNATIONS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','round',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,(node,index) in DESIGNATIONS.items():add(old,'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][69:71],inverse);return normalize_document(result)



@lru_cache(maxsize=1)
def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def text_boundaries():
    row=author.read(READINGS[0]);text=row['text'];second=row['second_sentence']
    first=author.read('data/einstein-measured-space-sentence-reading-v2.json')['source']
    require(first['range']==[0,240] and text[:240]==first['text'] and text[240:241]==' ','First sentence differs')
    require(second['range']==[241,761] and text[241:761]==second['text'],'Second sentence differs')
    require(text.count('§ 1')==2,'First section references changed')
    return dict(sentences={'zc2':dict(position=[30,1],range=[0,240],text=first['text']),
        'zc3':dict(position=[30,2],range=[241,761],text=second['text'])},
        designation_order={'zc2':['x','y','z','ξ','η','ζ'],'zc3':['τ']},
        reused_designations=['K','k','t'],first_section_reference_occurrences=2,
        rule='Count newly adopted designations in their source order; existing K/k/t are reused, not renamed here.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};row=author.read(READINGS[0]);unit=units[row['unit']]
    require(row['unit']=='einstein-1905:u0045','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-clock-site-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[106,107],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=row['math'],annotations=annotations()['entries'],semantic_review=['第一文の既存判断v2を同じ選択で保持する。Wir denken unsは同じ空間を測定済み・六座標を取得済みの配置として想定し採用するという著者の行為である。',
 '同じK/kと物差しを維持し、Kのx,y,zとkのξ,η,ζをそれぞれの三軸役割へ結ぶ。各測定配置で対象・軸・尺度を保ち、全空間の各地点について同じ実測の存在と全有効候補の一意性へ座標値を結ぶ。',
 '移動系の物差しはKに対する既出の運動に同伴し、自系では静止する。両系の原点一致・正方向一致・座標値一致を追加しない。K/kの名称は先行zcgでの命名を再使用する。',
 'u0045第二文[241,761)の426本文文字を、第一文の同じ二系と計器・移動後設定に追加する思考上の指示として読む。Es werde fernerとebenso werdeを同じ二系の対称な時刻設定へ接続する。',
 '各系の全配備時計は初期と同じ対象で、自系に相対的に静止し校正される。代表位置の完全な静止履歴を使い、時計内部を停止させない。先行設定の共動は保持され、ここで加速機構や絶対静止を追加しない。',
 '時計のある全地点に限り、そこで起きる全対象出来事へ局所表示で時刻を付与する。全空間への実機配置や、空の場所で出来事を生成する条件は加えない。zczは有限測定標本でなく対象の全範囲である。',
 '§1の手順は同じ系の全配備時計対のqoによる光往復全試行の同期である。qlで全必要試行の範囲を指定し、異なる時計間は非空な試行と全試行のdbを要求する。共通参照時計も同じ配備範囲に属する。初期設定では参照時計の選定自体を指定していないため、初期のzbhとの等置は補わない。',
 'eiyn/eiyoは新しい同期方式ではなく、§1のsaf/qoと局所表示を指定系の配備・校正条件へ適用した規則である。二つの第一節参照を同じ文書区分eisdyに結ぶ。方法の適用条件は合成し、参照だけで同期・測定済みを認定しない。',
 '既出tはeiwtの時点規則を変更しない。出来事とその系の生起時点を一般関係eisnkで結び、全対応時点のylとその出来事のzbeを比較する。τは同型の移動系規則に結び、t=τや系間の同時性の一致を追加しない。',
 '原刊897頁末と898頁冒頭を再表示し、二文全761文字602非空白本文文字とM0075〜M0080を確認。第一文の六つの新呼称と第二文のτを採用順へ接続し、K/k/tの既出呼称は再使用する。',
 '旧判断の逆投影、有限境界診断、円文字復号、全頁表示、独立した人の読解を区別する。引用された測定や時刻設定の物理的実現を証明しない。'],
        profile_edition=38,core_edition=12,new_source_assertions=2,total_source_assertions=52,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible clock site document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*DESIGNATIONS)}
SITUATIONS=previous.SITUATIONS

def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def designation(document,node,item,context):
        key=(document,node,TextPresentation.coordinate(item),context)
        rows={(values['eirf'],values[n],i,values['ri']):values[old] for old,(n,i) in DESIGNATIONS.items()}
        return rows[key] if key in rows else result['designationreference'](document,node,item,context)
    return result|dict(sentencereference=sentence,designationreference=designation)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved clock site bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-parallel-choice-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,'data/einstein-measured-space-sentence-reading-v2.json',*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/clock_site_visible_profile.py','scripts/clock_site_visible_profile_contracts.py','scripts/check_einstein_clock_site_visible.py',
        'scripts/visible_clock_site_visible_collection.py','tests/test_clock_site_visible_profile.py','docs/einstein-clock-site-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-clock-site-visible-evidence-1',core_words=375,profile_words=744,profile_edition=38,
        preserved_source_relations=8,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=52,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
