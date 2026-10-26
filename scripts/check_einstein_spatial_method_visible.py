"""Connect the spatial method, moving light law and two longitudinal ray equations."""
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
from scripts import spatial_method_visible_profile as profile
from scripts.spatial_method_visible_profile import ROOT,SpatialMethodVisibleVocabulary,write_once
from scripts import check_einstein_affine_time_visible as previous
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

SOURCE='examples/v016/einstein-spatial-method-visible-v1.noema'
BRIDGE='data/einstein-spatial-method-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-spatial-method-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='snd sne snf sng snh snr sns s2w s2x s2y eiy4 ei42 ei43 ei44 ei45 ei46 ei47 ei5a ei5b ei5c ei5d ei5e ei5f ei5g ei5h ei5i ei5j ei5k ei5l ei5m ei5n ei5o ei5p ei5q ei5r ei5s ei5t ei5u ei5v'.split()
SENTENCES=dict(spatialmethodsentence=(39,1),spatialraysentence=(39,2))
SPANS=dict(ze7=('spatialmethodsentence',1,12),ze2=('spatialmethodsentence',13,44),ze3=('spatialraysentence',1,14),ze4=('spatialraysentence',15,16))
ROLE_ASSIGNMENTS=dict(zey='movingray',zez='restray',eisnn='method')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*('spatial'+role+'role' for role in ROLE_ASSIGNMENTS.values())]
READINGS=('data/einstein-spatial-method-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-spatial-method-u'+str(i).zfill(4)+'-review-v1.json' for i in range(65,69))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0065–u0068を先行τの利用、空間三座標の計算方法、二原理の挿入説明、原点から正のξ方向への光線、二つの式とoderの書換えとして読む。',
 'leichtは、この論説で利用できると提示された同じ計算方法の必要な手順が文脈上低負担であるという評価として読む。既存s2w/s2x/s2yの連続した有限手順・非負負担・合計基準を使い、本人の能力上限や実際の計算時間は補わない。',
 'manは同じ議論でこの方法を用いる主体として著者に代表させる。全人類・全読者が低負担で計算できるという全称にはしない。数値負担・閾値・手順数は原文にないため固定しない。',
 '計算の手順と許容変形は既存zlx/zlaの文脈入力である。計算が提示する候補写像の目標を現在のeiy4へ結ぶが、実行履歴・原文に省略された機械証明・規則の健全性を捏造しない。容易という著者の評価は偽でも記述できる。',
 'durch Gleichungenを、同じkの全区間に経路長=V×経過時間を要求するei43の式を手順中で使うこととして読む。先行τを保持し、任意の低負担の別計算で代用しない。',
 '二原理からkの法則を要請することはzcによる著者の帰結として保持する。測定規約の接続、全区間、同じV、光源の運動への独立性を保持し、引用から現実の法則の証明へ変えない。',
 '正のξ光線は直前の零点規約とξ=Vτに合わせた原点放出の読みを継承する。各系の全直線一定速度軌道ei47を用い、τ=0だけから全空間原点を導かない。',
 '表示式のξは同じ光線上の到達出来事の値である。τの代入には同じV,v,φ(v),x′,tを用いる。光線外の全変換をこの二式だけで決定せず、V−vと後続のtの消去はu0069以降に分ける。',
 '候補空間写像を代入する四式の構成は目標条件であり、その候補が現在の測定対応に一致することの自動証明ではない。有限検査・著者の提示・全文読解判断を区別する。',
 '第39段落第一文44tokenと第二文16tokenへ接続する。容易な座標計算の主節1–12と、二原理の括弧書きを含む方法説明13–44を別箇所とし、光線の条件と第一式1–14、oderと第二式15–16へ続ける。箇所への参照範囲は主張内容の全意味範囲を制限しない。第一文全体への参照も保持する。',
 '光線二参照はei5aの静止側と運動側それぞれの役割に、方法は同じ著者が提示文脈で利用できる役割に結ぶ。既存の汎用describedreferenceを使い、役割や物理条件を参照取得時に実行しない。二つの光線が同じ対である条件はei5lの本文で別に要求する。',
 '39個の既存合成定義と7個の旧関係契約を再利用する。共通375語、任意46版776語。新たな物理の原始関係や参照方式は追加しない。有限の識別モデルと全実数・物理的真理の証明を区別する。']


@lru_cache(maxsize=1)
def vocabulary():return SpatialMethodVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][125:129]):visit(n)
    require(len(seen)==339,'Spatial-method source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][125:129])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','book',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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


def reference_roles():return {old:names()['spatial'+role+'role'] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown spatial-method reference')
    return 'ze7' if old=='eisnn' else 'ze3'


def role_definitions():
    n=names();m=mapping();voc=vocabulary();k=lambda old:call(n[old])
    defs=[]
    for old,role in ROLE_ASSIGNMENTS.items():
        if old=='eisnn':body=call(m['zlw'],k('rd'),v('va'),v('vb'))
        else:
            first,second=(v('vc'),v('va')) if old=='zey' else (v('va'),v('vc'))
            body=dict(kind='exists',variable='vc',sort='individual',body=call(m['ei5a'],first,second,k('zb6')))
        defs.append(definition(n['spatial'+role+'role'],[('va','individual'),('vb','situation')],'truth',body))
        defs.append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri'))))
    return defs


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][95:99],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==4,'Source selection changed')
    text=' '.join(s['text'] for s in segments)
    first,second=text.split(' Für ',1);second='Für '+second
    one,two=first.split(),second.split()
    require(len(one)==44 and one[:4]==['Mit','Hilfe','dieses','Resultates'],'Method boundary changed')
    require(one[11:14]==['ermitteln,','indem','man'] and one[21]=='(wie' and one[33]=='verlangt)','Principle clause changed')
    require(one[-2:]==['[M0119]','fortpflanzt.'],'Moving light speed changed')
    require(len(two)==16 and two[4]=='[M0120]' and two[9]=='[M0121]' and two[13:]==['[M0122],','oder','[M0123].'],'Ray boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; punctuation attached; 1-based inclusive positions.',
        sentences={name:dict(position=list(SENTENCES[name]),tokens=tokens,text=body) for name,tokens,body in (('spatialmethodsentence',one,first),('spatialraysentence',two,second))},
        spans={n:list(p) for n,p in SPANS.items()},
        anchor='Distinct ordered locations within two complete sentences; a location does not truncate the attributed content.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(65,69)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-spatial-method-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[125,126,127,128],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=46,core_edition=12,new_source_assertions=4,total_source_assertions=73,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible spatial-method document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|dict(zey='spatialmovingray',zez='spatialrestray',eisnn='spatialmethod')
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['spatialmethodsentence'],44),(values['spatialraysentence'],16)]},
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
    refs=TemporalReferences({(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old] for old,role in roles.items()}, {})
    nodes={values[x] for x in (*SENTENCES,*SPANS)}
    def described(doc,node,role,context):
        return refs.described(doc,node,role,context) if node in nodes else result['describedreference'](doc,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved spatial-method bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-affine-time-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/spatial_method_visible_profile.py','scripts/spatial_method_visible_profile_contracts.py','scripts/check_einstein_spatial_method_visible.py',
        'scripts/visible_spatial_method_visible_collection.py','tests/test_spatial_method_visible_profile.py','docs/einstein-spatial-method-visible-v1.md',
        'scripts/check_frame_light_law.py','scripts/check_origin_light_ray.py','scripts/check_spatial_method_claim.py',
        'examples/v014/frame-light-law-core.noema','examples/v014/origin-light-ray-core.noema','examples/v014/spatial-method-claim-core.noema',
        'scripts/check_calculation_discourse.py','scripts/compose_calculation_discourse.py','scripts/check_moving_trip_geometry.py',
        'scripts/compose_frame_light_law.py','scripts/compose_origin_light_ray.py','scripts/compose_spatial_method_claim.py',
        'scripts/check_coordinate_correspondence.py'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-spatial-method-visible-evidence-1',core_words=375,profile_words=776,profile_edition=46,
        new_public_relations=7,new_reference_primitives=0,new_source_assertions=4,total_source_assertions=73,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
