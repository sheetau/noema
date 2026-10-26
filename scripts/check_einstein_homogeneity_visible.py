"""Connect attributed homogeneity and affine necessity to visible text."""
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
from scripts import homogeneity_visible_profile as profile
from scripts.homogeneity_visible_profile import ROOT,HomogeneityVisibleVocabulary,write_once
from scripts import check_einstein_event_coordinate_visible as previous
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

SOURCE='examples/v016/einstein-homogeneity-visible-v1.noema'
BRIDGE='data/einstein-homogeneity-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-homogeneity-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eizc eizd eize eizf eizg eizh eizi eizj eizk eizl shx shy sia sie'.split()
SENTENCES=dict(zdf=(32,1))
SPANS=dict(zde=('zdf',12,18))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS]
READINGS=('data/einstein-homogeneity-claim-source-reading-v1.json',)
REVIEWS=('data/einstein-homogeneity-claim-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return HomogeneityVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][109:110]):visit(n)
    require(len(seen)==215,'Homogeneity source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][109:110])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','aki',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    result['statements']=renamed(doc['statements'][79:80],inverse);return normalize_document(result)



def text_boundaries():
    row=author.read(READINGS[0]);tokens=row['text'].split()
    require(len(tokens)==18 and tokens[11:]==['Homogenitätseigenschaften,','welche','wir','Raum','und','Zeit','beilegen.'],'Homogeneity property span changed')
    return dict(rule='Whitespace-delimited transcription; punctuation attached; 1-based inclusive positions.',
        sentences={'zdf':dict(position=[32,1],tokens=tokens)},spans={'zde':['zdf',12,18]},
        anchor='The whole sentence states the affine necessity; its homogeneity attribution has a distinct internal token span.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};row=author.read(READINGS[0]);unit=units[row['unit']]
    require(row['unit']=='einstein-1905:u0047','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-homogeneity-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[109],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=row['math'],semantic_review=['u0047全129文字・112本文文字を対象とする。Zunächst、ist klar、müssen、wegen、welche wir Raum und Zeit '
 'beilegenを省かず、前段の同じ四座標と方程式探索課題へ結ぶ。',
 '一様性は、この運動学で同じ系・計器・尺度の四座標を比較するとき、同じ空間変位・時間変位の比較規則が出発点の場所・時刻に依存しないという読みを採る。前段の実測地点と局所時計へ接続した全座標範囲を使い、単なる任意の記号関数の性質や、全物理法則の一様性一般と同義だとはしない。',
 'shsは空でない全入力範囲の全出発点対と、両移動後の点も範囲内となる全有効四変位を扱う。空間三方向・時間方向・混合変位を含む。零変位や一地点の成功だけで済ませず、全実数の量化を有限試験点へ替えない。',
 'linearは、この段階で原点一致が指定されていないため、各出力量が同じ一つの行列と成分別定数で表されるアフィン形として読む。原点保存・零定数を補わず、任意の非線形な同値表記まで式の見かけが一次であることを要求しない。',
 '三位置成分と一時刻成分の数値を、固定した長さ・時間単位で扱う。行列の混合係数はその単位に従う数値で、時間と長さそのものを同じ量として加える規約ではない。入力・出力の四役割以外をsieで零へ正規化し、隠れた情報を使わせない。',
 '一様性から一般の実数域で行列表示を導く証明は主張しない。原文に明記されない連続性などを仮定へ足して証明済みにせず、著者がその理由で必要だと述べることと、処理系が含意を証明したことを分ける。',
 '同じ現行座標対応に適合する変換のアフィン形を、先行方程式探索課題の必要条件として帰属する。係数の数値、具体的なLorentz変換、解の発見済みは加えない。明白さは著者の提示であり、検査器の自明性認定ではない。',
 'Zunächstはこの課題を検討する主要段階の最初である。課題以前の計器設定や現在段階内の一様性の説明を別の先行主要段階として混ぜない。有限検査・原文通読・同義性の自動証明は区別する。',
 '第32段落第1文全体zdfと、その12–18トークンの一様性帰属zdeを区別する。課題zdbとの本文順序を保持する。',
 '14旧合成定義と3旧契約を再利用する。文全体を新たな意味原子に置き換えない。'],
        profile_edition=40,core_edition=12,new_source_assertions=1,total_source_assertions=54,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible homogeneity document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}
SITUATIONS=previous.SITUATIONS

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['zdf'],18)]},
        {(values['eirf'],values['zdf'],12,values['zdf'],18,values['ri']):values['zde']})

def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first==values['zdf'] or last==values['zdf']:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved homogeneity bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-event-coordinate-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/homogeneity_visible_profile.py','scripts/homogeneity_visible_profile_contracts.py','scripts/check_einstein_homogeneity_visible.py',
        'scripts/visible_homogeneity_visible_collection.py','tests/test_homogeneity_visible_profile.py','docs/einstein-homogeneity-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-homogeneity-visible-evidence-1',core_words=375,profile_words=749,profile_edition=40,
        preserved_source_relations=3,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=54,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
