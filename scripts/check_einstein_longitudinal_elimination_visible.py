"""Connect K-time relative propagation and elimination of t on the same light ray."""
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
from scripts import longitudinal_elimination_visible_profile as profile
from scripts.longitudinal_elimination_visible_profile import ROOT,LongitudinalEliminationVisibleVocabulary,write_once
from scripts import check_einstein_spatial_method_visible as previous
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

SOURCE='examples/v016/einstein-longitudinal-elimination-visible-v1.noema'
BRIDGE='data/einstein-longitudinal-elimination-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-longitudinal-elimination-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='sna snb sni snj snt snu ei5w ei5x ei5y ei5z ei6b ei52 ei55 ei56 ei53 ei54 ei57 ei6a'.split()
SENTENCES=dict(ze5=(40,1),ze6=(41,1))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES]
READINGS=('data/einstein-longitudinal-elimination-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-longitudinal-elimination-u'+str(i).zfill(4)+'-review-v1.json' for i in range(69,73))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0069は原刊899頁から900頁へ続く文。Nun ... aberは、同じ光をkで測るVから、Kの時刻でk原点に対して測るV−vへ観点を移す対照として読む。以前の光速原理の撤回や論理的矛盾ではない。',
 '対照は既存Kantのh222qの同じ基本規約を、0.14の閉じた引用型に合わせたeisnpで再使用する。特定の接続語や物理式専用の意味規約は加えない。',
 '同じk原点の全設定内の代表履歴と、この光線のK時刻0からtまでの一次軌道を結ぶ。全区間の相対変位を使い、原点の静止、V−vをτで測る速度、x′=ξを仮定しない。',
 '原点放出・空間零点と両時刻零は先行ei5aの明示的な読みを継承する。原点は同じ放出出来事に位置するが、後の光の到達出来事に原点もあるとは要求しない。同時刻の原点位置を使う。',
 '現在の設定は正のvを含み、光線条件はv<Vを保持する。t>0、V−v>0の範囲で割る。数値核はv=0も比較できるが、今回の物理設定を静止系対へ変更しない。',
 'Setzen wir ... einは、この同じtの値を先行するξの式へ代入して結果を得るという著者の計算提示として読む。実際の計算行為の履歴・実行日時・読者の参加を補わない。',
 '既存sni/sntとsnj/snuの同じ到達出来事・V,v,a=φ(v),x′を再利用する。aを1や最終確定係数へ固定しない。光線上の一致だけから全空間の座標変換を決定せず、横方向の光線はu0073以降に残す。',
 '一般実数域の量化は有限評価を拒否する。一次軌道の有限指紋、同じ時計・原点の結合、既存の有理多項式補題と数値代入は限定された証拠であり、一般実数体・物理法則・原文との同義性の自動証明ではない。',
 '原刊899–900頁を表示し、Anfangs-/punktの改ページ接続と二つの分数式を確認した。既存の本文区分規約の第40・41段落各第一文へ、それぞれ23・16tokenを結ぶ。表示式は導入文を完結させ、改ページを文の切れ目にしない。数式内の句点を別tokenとして加えない。',
 '18個の既存合成定義を再利用し、二箇所と共通観点を明示する旧eisnp契約1個を任意語彙へ公開する。単純な二内容の対比や訂正的対置へ置換せず、8引数と閉じた性質記述型を保持する。共通375語、任意47版777語。新しい物理原始関係や参照方式は追加しない。']


@lru_cache(maxsize=1)
def vocabulary():return LongitudinalEliminationVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][129:131]):visit(n)
    require(len(seen)==291,'Longitudinal-elimination source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][129:131])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','fruit',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][99:101],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==4,'Source selection changed')
    first=' '.join(s['text'] for s in segments[:2]);second=' '.join(s['text'] for s in segments[2:])
    one,two=first.split(),second.split()
    require(len(one)==23 and one[:4]==['Nun','bewegt','sich','aber'],'Relative-motion boundary changed')
    require(one[8:11]==['Anfangspunkt','von','[M0124]'] and one[18:] == ['[M0125],','so','daß','gilt:','[M0126]'],'Same reference and K-speed formula changed')
    require(len(two)==16 and two[:5]==['Setzen','wir','diesen','Wert','von'] and two[5]=='[M0127]' and two[10]=='[M0128]' and two[-1]=='[M0129]','Substitution boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; formula punctuation retained inside MathML; 1-based positions.',
        sentences={name:dict(position=list(SENTENCES[name]),tokens=tokens,text=body) for name,tokens,body in (('ze5',one,first),('ze6',two,second))},
        anchor='Two logical body paragraphs, each completed by its displayed formula. The page break does not divide the first sentence.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(69,73)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-longitudinal-elimination-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[129,130],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        semantic_review=SEMANTIC_REVIEW,profile_edition=47,core_edition=12,new_source_assertions=2,total_source_assertions=75,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible longitudinal-elimination document differs');return result


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
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved longitudinal-elimination bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-spatial-method-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/longitudinal_elimination_visible_profile.py','scripts/longitudinal_elimination_visible_profile_contracts.py','scripts/check_einstein_longitudinal_elimination_visible.py',
        'scripts/visible_longitudinal_elimination_visible_collection.py','tests/test_longitudinal_elimination_visible_profile.py','docs/einstein-longitudinal-elimination-visible-v1.md',
        'scripts/check_frame_light_law.py','scripts/check_origin_light_ray.py','scripts/check_longitudinal_elimination.py',
        'examples/v014/frame-light-law-core.noema','examples/v014/origin-light-ray-core.noema','examples/v014/longitudinal-elimination-core.noema',
        'scripts/check_calculation_discourse.py','scripts/compose_calculation_discourse.py','scripts/check_moving_trip_geometry.py',
        'scripts/compose_frame_light_law.py','scripts/compose_origin_light_ray.py','scripts/compose_longitudinal_elimination.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_translated_light_trial.py','reports/longitudinal-light-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-longitudinal-elimination-visible-evidence-1',core_words=375,profile_words=777,profile_edition=47,
        new_public_relations=1,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=75,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
