"""Connect pointwise possible starts and the all-space derivative claim."""
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
from scripts import arbitrary_start_visible_profile as profile
from scripts.arbitrary_start_visible_profile import ROOT,ArbitraryStartVisibleVocabulary,write_once
from scripts import check_einstein_differential_visible as previous
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

SOURCE='examples/v016/einstein-arbitrary-start-visible-v1.noema'
BRIDGE='data/einstein-arbitrary-start-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-arbitrary-start-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='ei26 ei27 ei3a ei3b ei3c ei3d ei3e ei3f ei3g ei3h ei3i ei3j ei3k ei3l ei3m ei3n ei3o ei3p ei3q ei3r ei3s ei3t ei3u ei3v ski skj skk skl skm skn skv'.split()
SENTENCES=dict(zeg=(36,1))
SPANS=dict(zeh=('zeg',21,32),arbitraryweanchor=('zeg',6,6))
ROLE_ASSIGNMENTS=dict(zee='discussionactor')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,'arbitrarystartrole']
READINGS=('data/einstein-arbitrary-start-claim-source-reading-v1.json',)
REVIEWS=('data/einstein-arbitrary-start-claim-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0058全213文字・175本文文字とM0105 '
 'x′,y,zを対象とする。注意喚起、議論主体wir、原点の代わりの任意の他の点、光の出発点として選べた可能性、deshalbの帰結、同じ整理後の式、全空間値を保持する。',
 'hätten wählen '
 'könnenは同じ思考設定で選べた試行と、その可能な結果の存在として読む。元と候補の同じ地点・補助座標・K出発時刻を結び、実際に全地点で光を発したことや全結果での成功とはしない。地点ごとに試行や可能設定を選べる。wirは議論を行う側として保持し、構成員を確定しない。',
 '先行する原点での試行を含め、全ての有効実数値のx′,y,zを量化する。原点以外だけを結論の範囲にせず、存在する有限の記録地点だけへ縮めない。全地点と候補試行の存在は著者が述べる内容であり、この通読判断が現実の存在を証明したとはしない。',
 '同じ候補τ、V、v、二基準系と単位を保つ。任意の候補設定で現在の全座標対応と全時計指示、完全な光往復、両K光区間の原理と局所表示をei3kへ結ぶ。時刻は前段と同じパラメータであり、ここで全時刻の量化やt=τを新たに補わない。',
 'skiは空間三引数の原点だけを移し、時刻引数・τ値・尺度を変更しない。sklは移した近傍全体の式と元の同じ関数の指定点での全微分可能性・二偏微分を結ぶ。十分な局所正則性を明示した既出の読みを引き継ぎ、原文がε–δ条件を逐語的に述べたとはしない。',
 '結論skv/skn/skmは全空間点ごとに同じτの二偏微分値を存在量化し、その値で既存sjyのτx′+v/(V²-v²)*τt=0を要求する。原点の候補値zd6/zd7を全空間で同じ定数とせず、具体的τの関数形やy,z方向の条件を先取りしない。',
 'Es ist zu '
 'bemerkenは選択可能性への注意喚起、deshalbはその内容から同じ微分式の全空間範囲への帰結の提示と読む。著者・論説・第三節と直前の式からの本文順序を保持し、提示の帰属と処理系による物理的含意の証明を区別する。',
 '旧空間平行移動・可能選択・局所微分・全空間量化とその証拠を再利用し、新規原始語は追加しない。有限の例は作用範囲と引数を調べるものであり、全実数・全地点の一般物理定理を代用しない。',
 '原刊899頁の一文32トークンを第36段落第一文へ接続する。後半の帰結は21–32、wirの参照anchorは6だけとする。先行する二つの微分式からの順序を保つ。',
 'われわれの指示対象は同じ文書・wirの箇所・提示文脈で照合する解釈入力として保持する。本文の閉じた役割は候補が同じ設定で選べる試行の存在を記述する。役割に合う任意の主体を勝手に選ぶ手続ではなく、著者単独との同一性、具体的構成員や世界での唯一性を追加しない。参照取得から引用した役割を実行しない。',
 '31旧合成定義と三つの旧関係を保持する。共通375語、任意43版760語。新しい文専用原始語は作らない。有限の束縛診断を、全空間の存在や物理的導出の証明としない。']


@lru_cache(maxsize=1)
def vocabulary():return ArbitraryStartVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][118:120]):visit(n)
    require(len(seen)==399,'Arbitrary-start source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][118:120])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','rain',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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


def reference_roles():return {'zee':names()['arbitrarystartrole']}


def reference_anchor(old):
    require(old=='zee','Unknown arbitrary-start reference');return 'arbitraryweanchor'


def role_definitions():
    n=names();m=mapping()
    body=dict(kind='exists',variable='vc',sort='individual',body=call(m['zec'],v('va'),v('vc'),call(n['zb6'])))
    return [definition(n['arbitrarystartrole'],[('va','individual'),('vb','situation')],'truth',body)]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][88:90],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==1,'Source sentence split changed')
    text=segments[0]['text'];tokens=text.split()
    require(len(tokens)==32 and tokens[5]=='wir' and tokens[20:23]==['es','gilt','deshalb'],'Fixed arbitrary-start boundary changed')
    require(tokens[-1]=='[M0105].' and [m['id'] for m in segments[0]['math']]==['M0105'],'Math boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; punctuation attached; 1-based inclusive positions.',
        sentences={'zeg':dict(position=[36,1],tokens=tokens,text=text)},spans={n:list(p) for n,p in SPANS.items()},
        anchor='One sentence from Es ist zu bemerken through all x-prime,y,z values; the next transverse-axis argument is excluded.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u0058'},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-arbitrary-start-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[118,119],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=43,core_edition=12,new_source_assertions=2,total_source_assertions=64,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible arbitrary-start document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['zeg'],32)]},
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
    roles=reference_roles()
    key=(values['eirf'],values['arbitraryweanchor'],canonical(dict(kind='function_ref',symbol=roles['zee'])),values['ri'])
    individuals=TemporalReferences({key:values['zee']},{})
    nodes={values[n] for n in (*SENTENCES,*SPANS)}
    def individual(doc,node,role,context):
        return individuals.described(doc,node,role,context) if node in nodes else result['describedreference'](doc,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=individual)



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved arbitrary-start bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-differential-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/arbitrary_start_visible_profile.py','scripts/arbitrary_start_visible_profile_contracts.py','scripts/check_einstein_arbitrary_start_visible.py',
        'scripts/visible_arbitrary_start_visible_collection.py','tests/test_arbitrary_start_visible_profile.py','docs/einstein-arbitrary-start-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-arbitrary-start-visible-evidence-1',core_words=375,profile_words=760,profile_edition=43,
        new_public_relations=3,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=64,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
