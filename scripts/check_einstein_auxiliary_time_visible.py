"""Connect auxiliary invariance and synchronized-time questions to visible text."""
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
from scripts import auxiliary_time_visible_profile as profile
from scripts.auxiliary_time_visible_profile import ROOT,AuxiliaryTimeVisibleVocabulary,write_once
from scripts import check_einstein_homogeneity_visible as previous
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

SOURCE='examples/v016/einstein-auxiliary-time-visible-v1.noema'
BRIDGE='data/einstein-auxiliary-time-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-auxiliary-time-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiz2 eiz3 eiz4 eizm eizn eizo eizp eizq eizr eizs eizt eizu eizv eizw eizx eizy eizz sig sih sij sik sil sin'.split()
SENTENCES=dict(zdj=(33,1),zdl=(33,2),zdp=(33,3))
SPANS=dict(zdk=('zdj',4,22))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS]
READINGS=('data/einstein-comoving-time-task-source-reading-v1.json',)
REVIEWS=('data/einstein-comoving-time-task-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return AuxiliaryTimeVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][110:113]):visit(n)
    require(len(seen)==257,'AuxiliaryTime source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][110:113])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','book',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    result['statements']=renamed(doc['statements'][80:83],inverse);return normalize_document(result)



def text_boundaries():
    row=author.read(READINGS[0]);parts=row['text'].split('. ')
    require(len(parts)==3,'Three sentence boundary changed')
    parts=[part+'.' if i<2 else part for i,part in enumerate(parts)]
    require(' '.join(parts)==row['text'],'Sentence reconstruction changed')
    tokens=[part.split() for part in parts]
    require([len(t) for t in tokens]==[22,10,36],'Sentence token counts changed')
    require(tokens[0][:3]==['Setzen','wir','[M0084],'] and tokens[0][3:6]==['so','ist','klar,'] and tokens[0][-1]=='zukommt.','Introduction and invariance boundaries changed')
    require([m['id'] for m in row['math']]==['M0084','M0085','M0086','M0087','M0088','M0089','M0090','M0091'],'Math boundary changed')
    return dict(rule='Whitespace-delimited transcription; punctuation attached; math placeholders are single tokens; 1-based inclusive positions.',
        sentences={n:dict(position=list(SENTENCES[n]),tokens=t,text=p) for n,t,p in zip(SENTENCES,tokens,parts,strict=True)},
        spans={'zdk':['zdj',4,22]},
        anchor='The first sentence anchors auxiliary adoption; its so-ist-klar remainder separately anchors invariance. The second and third sentences anchor the question and its purpose.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};row=author.read(READINGS[0]);unit=units[row['unit']]
    require(row['unit']=='einstein-1905:u0048','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-auxiliary-time-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[110,111,112],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=row['math'],semantic_review=['u0048三文の全437文字・314本文文字を扱う。補助量の導入、全静止点の時間不変な三値、明白さ、まず求める量と四引数、目的、方程式で表す必要、指示全体との一致、第一節の同期規則を保持する。',
 'x′=x-vtは既存sinで定義する補助量である。vは同じ正のX方向速度zb7、tはKの既存の時刻である。運動系の物差しで測るξ、棒の固有長、両系共通の時刻へ置き換えない。',
 '静止点は同じ座標配置の全点eisk7として読む。位置履歴を考察する全範囲zdiのうちx4がk静止とする点と過不足なく結び、物質点に限定しない。各点の自系代表履歴eit2と同じK並進eivwを要求する。時計の全物質点を静止させるeipwは使わない。',
 'K側全比較時点ysをeislaへ一致させ、正の幅と全時点での利用可能性をsilで保つ。K区間内の全実数時刻についてeiwiで時点を確保する。各点各時点のymを同じ代表位置、同じ出来事、同じ測定地点へ結ぶ。全点にK時計の新設を課さず、異なる系の時刻値を等置しない。',
 '不変性は同じ点の全時点間でx′,y,zが変わらないこと。異なる点の値の一致、ξ=x′、静止と等速並進の一般的な同値性の導出証明を追加しない。明白さは著者による提示である。',
 'τの候補条件は先行する全比較出来事zc4と現在のeiy3/eiyz/eiy2/eiyyへ接続する。未測定の任意の実数四組の実現を追加しない。x′への代入後の同じ出来事のτとの一致を全対応対に要求する。',
 'Inbegriffおよびnichts '
 'anderesは、この同じ比較範囲の全出来事におけるkの配備時計の指示全体との過不足ない値対応として読む。全配備時計は初期から同じ集団で、共通参照と全対全試行の第一節同期を満たす。時計のない地点への新しい時刻拡張や、比較範囲外の出来事の時計値を勝手に追加しない。',
 'まずτを求めることと、そのため指示条件を方程式で表す必要は課題の提示である。まだ候補式の探索を実行した、式が一意に存在する、光往復の式を導出したとは記述しない。有限検査、通読判断、一般の物理的真理や同義性の証明は別に扱う。',
 '原刊898頁を再表示し、第33段落の三文と八数式要素、後続の光往復との境界を確認した。zdjは第一文、zdkはその4–22トークン、zdlとzdpは第二・第三文である。',
 '23旧合成定義と4旧契約を再利用する。原文の数式・意味・順序を保持し、文全体を新しい意味原子へ置き換えない。'],
        profile_edition=41,core_edition=12,new_source_assertions=3,total_source_assertions=57,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible auxiliary_time document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}
SITUATIONS=previous.SITUATIONS

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],size) for n,size in zip(SENTENCES,(22,10,36),strict=True)]},
        {(values['eirf'],values['zdj'],4,values['zdj'],22,values['ri']):values['zdk']})

def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:
            return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved auxiliary_time bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-homogeneity-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/auxiliary_time_visible_profile.py','scripts/auxiliary_time_visible_profile_contracts.py','scripts/check_einstein_auxiliary_time_visible.py',
        'scripts/visible_auxiliary_time_visible_collection.py','tests/test_auxiliary_time_visible_profile.py','docs/einstein-auxiliary-time-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-auxiliary-time-visible-evidence-1',core_words=375,profile_words=753,profile_edition=41,
        preserved_source_relations=4,new_reference_primitives=0,new_source_assertions=3,total_source_assertions=57,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
