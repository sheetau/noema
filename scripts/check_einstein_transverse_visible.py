"""Connect complete transverse light trials and both zero partial derivatives."""
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
from scripts import transverse_visible_profile as profile
from scripts.transverse_visible_profile import ROOT,TransverseVisibleVocabulary,write_once
from scripts import check_einstein_arbitrary_start_visible as previous
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

SOURCE='examples/v016/einstein-transverse-visible-v1.noema'
BRIDGE='data/einstein-transverse-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-transverse-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='skw skx sle skz slf slg slh sli slj slk sll slm slv ei3w ei3x ei3y ei3z ei32 ei34 ei35 ei36 ei37 ei4a ei4b ei4c ei4d ei4e ei4f'.split()
SENTENCES=dict(zeo=(37,1))
SPANS=dict(zen=('zeo',13,33))
ROLE_ASSIGNMENTS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS]
READINGS=('data/einstein-transverse-derivative-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-transverse-derivative-u'+str(i).zfill(4)+'-review-v1.json' for i in range(59,62))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0059全225文字・172本文文字とM0106–M0108、表示式だけのu0060 M0109とu0061 '
 'M0110を一つの文と二式として扱う。類似議論・二横軸・条件への注意・Kからの視点・常に・平方根の速度と両零偏微分を保持する。',
 '固定抽出のH・Zと原刊の対応字形を保存する。H・Zは運動系のη・ζ方向の軸表記として読み、既出のK/k軸の平行性を通じて補助座標のy,zへ接続する。Hを新しい第四軸とせず、固定原文をYへ書き換えない。',
 '静止系Kの全光速Vと、運動する横軸に沿う成分w=√(V²-v²)を区別する。同じ光はKで縦成分vを持ち、往復で横成分だけが反転する。現在の全軌道・同じ三出来事・局所時計・幾何学的経路長へ接続し、Kでの全速さがwであるとはしない。',
 'stetsは、理想的な試行を含む明示した全範囲zej/zemに対する全称条件として保持する。両横方向の非空性と全選択試行を要求し、結果が一致する二標本だけを抜き出さない。全範囲の物理的実現を有限評価が証明したとはしない。',
 '全τ対応と全k時計指示は同じ候補zd4・同じ設定で保つ。局所の正近傍・全微分可能性・二偏微分は同じτと同じ点・時刻へ結ぶ。全空間への適用は先行u0058の範囲を引き継ぎ、時刻は同じ出発時刻のパラメータとする。',
 '同様の議論は、前の正側極限と十分な局所正則性を横方向へ適用する読みとする。中点の時間項が両辺で同じとなることと、実際の偏微分が零であることを区別し、単なる数値係数の零や独立した二つのτ候補にしない。',
 'wenn man beachtetは伝播条件に注意して推論するという読み、analoge '
 'Überlegungは先行する縦方向推論への参照として保持する。著者・同じ第三節・論説と本文順序を結び、引用した帰結を実行して一般物理的導出の自動証明へ替えない。',
 '新規原始語はない。既存の軸引数交換、平方根、局所微分と全空間条件を再利用し、全実数の量化は有限評価を拒否する。u0062以降の線形性からの具体的τ解・未定係数・原点時刻の選択は先取りしない。',
 '原刊899頁を再表示し、Eine analoge Überlegungから二式の句点までを照合した。固定抽出のH/Zを保持し、η/ζ方向としての採用解釈を変更しない。',
 '三収録単位を第37段落第一文の35トークンへ結ぶ。zeoは文全体の類似推論と二式、zenは13–33の注意条件を指す。先行zehからzen、zenからzeoへの提示順序は同一文内の帰属関係として保持する。',
 '28旧合成定義と5旧関係を再利用する。共通375語、任意44版765語。有限の軌道指紋・束縛診断・平方根の有理例を全実数や一般物理的導出の証明としない。']


@lru_cache(maxsize=1)
def vocabulary():return TransverseVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][120:122]):visit(n)
    require(len(seen)==371,'Transverse source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][120:122])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','birdone',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    for old,role in reference_roles().items():
        add(old,'individual',call(voc._symbols['describedreference'],k('eirf'),k('arbitraryweanchor'),qf(role),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {}


def reference_anchor(old):raise ValueError('No new described references in this selection')


def role_definitions():return []


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][90:92],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==3,'Source selection changed')
    text=' '.join(s['text'] for s in segments);tokens=text.split()
    require(len(tokens)==35 and tokens[:3]==['Eine','analoge','Überlegung'],'Fixed transverse boundary changed')
    require(tokens[12:15]==['wenn','man','beachtet,'] and tokens[32]=='fortpflanzt:','Attention clause changed')
    require(tokens[-2:]==['[M0109]','[M0110]'],'Zero-partial formulas changed')
    return dict(rule='Whitespace-delimited fixed transcription; punctuation attached; 1-based inclusive positions.',
        sentences={'zeo':dict(position=[37,1],tokens=tokens,text=text)},spans={n:list(p) for n,p in SPANS.items()},
        anchor='One sentence with an attention clause and two displayed zero partial derivatives; the next explicit tau solution is excluded.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(59,62)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-transverse-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[120,121],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=44,core_edition=12,new_source_assertions=2,total_source_assertions=66,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible transverse document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['zeo'],35)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved transverse bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-arbitrary-start-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/transverse_visible_profile.py','scripts/transverse_visible_profile_contracts.py','scripts/check_einstein_transverse_visible.py',
        'scripts/visible_transverse_visible_collection.py','tests/test_transverse_visible_profile.py','docs/einstein-transverse-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-transverse-visible-evidence-1',core_words=375,profile_words=765,profile_edition=44,
        new_public_relations=5,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=66,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
