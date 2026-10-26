"""Connect the unfixed normalized function and four shared origin constants."""
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
from scripts import origin_constants_visible_profile as profile
from scripts.origin_constants_visible_profile import ROOT,OriginConstantsVisibleVocabulary,write_once
from scripts import check_einstein_four_coordinate_visible as previous
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

SOURCE='examples/v016/einstein-origin-constants-visible-v1.noema'
BRIDGE='data/einstein-origin-constants-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-origin-constants-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['spu', 'sqa', 'sqc', 'sqd', 'ei7m', 'ei7n', 'ei7o', 'ei7p', 'ei7s', 'ei7q', 'ei7r', 'ei7t', 'ei7u']
SENTENCES=dict(originconstantssentence=(43,2))
SPANS=dict(zfp=('fourcoordinatesentence',14,22),zfq=('originconstantssentence',1,29))
ROLE_ASSIGNMENTS=dict(zfm='stage')
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS]
READINGS=('data/einstein-origin-constants-source-reading-v1.json',)
REVIEWS=('data/einstein-origin-constants-u0085-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0085の全二文とM0137–M0139を原刊900頁へ照合する。冒頭undは直前のβに続けて四式のφを説明する接続として読む。先行aと現在のφ=spcを区別する。',
 'vorläufig '
 'unbekannteは、導出段階zfmで現在のφを含む有効な関数候補が残り、ある許容速度で異なる値を持つ候補も残るという既存sqdの読みを採る。後続のφ=1を先取りせず、主体の全知識についての否定や史実上の心理状態の復元とはしない。',
 'φは同じvの関数である。候補族sqcは先行aの族zerを同じβで正規化し、現在の候補と現在のspcを全許容速度で結ぶ。一速度で一致する候補も許し、異なる候補名だけを未決定性の証拠にしない。',
 'Macht man ... keinerlei '
 'Voraussetzungは、同じ物理条件・系・単位・V,v,φを保つ設定で、運動系の初期空間原点とτの零点についての仮定を採らないという条件。既存zfn/zfoの外部意味規約を維持し、零点の物理的不一致や全前提の廃棄に置き換えない。',
 '各右辺へ加える定数の順はτ,ξ,η,ζ。四定数は互いに独立で零も許すが、同じ設定の全記録対で同じ一組を使う。既存spuは同じV,v,φを使い、四出力の有効性と各加法を保持する。',
 '現在の測定eiyxを使う既存ei26/ei27/ei3aを再利用し、指定設定の同じ出来事・全座標範囲・値としての一意性を保つ。原点仮定を外した設定へ固定zb6やei46の零点条件を再要求しない。未測定の全実数四組の実在は追加しない。',
 'zuzufügenは四式の一般形に必要な加法定数を述べる数学的帰結として読む。人への行為命令や実際の加算履歴にしない。定数の存在を引用内容から現実の成立へ移さない。',
 '原点のアフィン代数と候補の対照検査は補助証拠であり、一般実数体・物理的真理・意味同値の自動証明ではない。次の光速度の保存の証明課題は後続単位へ残す。',
 'u0085冒頭は既存の第43段落第一文14–22へ、原点定数の条件文は同段落第二文1–29へ接続する。前段階とは異なるzfmを同じ閉じた候補段階の役割で参照し、参照取得から内容の真理を導かない。',
 '旧定義13個、既存契約2個を再利用する。新たな参照型は追加せず、共通375語を保つ。任意50版782語。',
 'sqe/sqfは選択した原文の依存閉包に含まれない旧診断用定義なので追加しない。復号本文内のsqc/spc/smq/smb/sqdを直接検査する。四定数は各束縛を二値で区別する診断と本体の記録対検査を分ける。']


@lru_cache(maxsize=1)
def vocabulary():return OriginConstantsVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][138:140]):visit(n)
    require(len(seen)==230,'Origin-constants source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][138:140])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','inside',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=role_definitions()
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {'zfm':names()['affinestagerole']}


def reference_anchor(old):
    require(old=='zfm','Unknown origin stage reference');return 'zfp'


def role_definitions():
    n=names();voc=vocabulary();k=lambda old:call(n[old])
    return [definition(n['zfm'],[],'situation',call(voc._symbols['describedsettingreference'],
        k('eirf'),k('zfp'),qf(n['affinestagerole']),k('ri')))]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][108:110],inverse);return normalize_document(result)



def text_boundaries():
    segment=author.read(READINGS[0])['segments'];require(len(segment)==1,'Source selection changed')
    first,second=segment[0]['text'].split(' Macht man ',1);second='Macht man '+second
    inherited=previous.text_boundaries()['sentences']['fourcoordinatesentence']
    require(first==' '.join(inherited['tokens'][13:]),'Unknown-function continuation changed')
    tokens=second.split();require(len(tokens)==29 and tokens[-1]=='zuzufügen.','Origin condition boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; mathematical placeholders retained; 1-based inclusive positions.',
        sentences={'fourcoordinatesentence':inherited,'originconstantssentence':dict(position=[43,2],tokens=tokens,text=second)},
        spans={n:list(p) for n,p in SPANS.items()},
        anchor='Complete the inherited four-coordinate sentence, then preserve the whole conditional sentence in the same paragraph.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(85,86)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-origin-constants-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[138,139],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=50,core_edition=12,new_source_assertions=2,total_source_assertions=84,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible origin-constants document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|dict(zfm='originconstantsstage')
SITUATIONS=tuple(dict.fromkeys([*previous.SITUATIONS,'originconstantsstage']))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['fourcoordinatesentence'],22),(values['originconstantssentence'],29)]},
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
    key=(values['eirf'],values['zfp'],canonical(dict(kind='function_ref',symbol=reference_roles()['zfm'])),values['ri'])
    settings=SettingReferences({key:values['zfm']})
    def setting(document,node,role,context):
        if node==values['zfp']:return settings.described(document,node,role,context)
        return result['describedsettingreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedsettingreference=setting)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved origin-constants bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-four-coordinate-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/origin_constants_visible_profile.py','scripts/check_einstein_origin_constants_visible.py',
        'scripts/visible_origin_constants_visible_collection.py','tests/test_origin_constants_visible_profile.py','docs/einstein-origin-constants-visible-v1.md',
        'scripts/check_origin_constants_claim.py','scripts/compose_origin_constants_claim.py',
        'examples/v014/origin-constants-claim-core.noema','reports/origin-constants-v1.json',
        'reports/origin-constants-claim-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-origin-constants-visible-evidence-1',core_words=375,profile_words=782,profile_edition=50,
        new_public_relations=2,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=84,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
