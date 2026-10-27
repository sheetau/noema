"""Connect the common-origin spherical wave and its arrival equation."""
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
from scripts import rest_spherical_wave_visible_profile as profile
from scripts.rest_spherical_wave_visible_profile import ROOT,RestSphericalWaveVisibleVocabulary,write_once
from scripts import check_einstein_light_proof_task_visible as previous
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

SOURCE='examples/v016/einstein-rest-spherical-wave-visible-v1.noema'
BRIDGE='data/einstein-rest-spherical-wave-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-rest-spherical-wave-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['sqj', 'sqk', 'sql', 'ei73', 'ei74', 'ei75', 'ei76', 'ei77', 'ejaa', 'ejab', 'ejac', 'ejad']
SENTENCES=dict(restsphericalassumptionsentence=(45,1),restsphericalequationsentence=(45,2))
SPANS=dict(zgc=('restsphericalassumptionsentence',1,27),zgd=('restsphericalequationsentence',1,13))
ROLE_ASSIGNMENTS=dict(zfu='wave',zfv='emission')
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,'restsphericalwaverole','restsphericalemissionrole']
READINGS=('data/einstein-rest-spherical-wave-source-reading-v1.json',)
REVIEWS=('data/einstein-rest-spherical-wave-u0087-review-v1.json','data/einstein-rest-spherical-wave-u0088-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0087の二文とu0088の式・句点を原刊901頁へ照合する。werde ... ausgesandtは仮定上の放出設定であり、実験を実施した報告や読者への命令にしない。',
 '放出時のt=τ=0と両系の共通空間原点を、同じ放出出来事と現在の二座標のei46へ結ぶ。両系の原点が全時刻で重なることや、全出来事でt=τになることは加えない。',
 '波は同じ放出に由来する構成光線の非空な全範囲として扱い、各光線の現在のK区間を同じ放出へ結ぶ。ei44は物理的な伝播・局所時計・幾何学的光路長と座標付与を保持し、単に球面式が真なら光が到来したとはしない。仮定上の測定規約であり、実験済みの記録だけに限定しない。',
 '球面波は全対象出来事の現在の座標範囲で、同じ波の到来が正時刻の球面式に過不足なく一致するという幾何学的波面の読みを採る。全範囲は成功標本だけに縮めず、未測定の全実数四組の現実的な実在や場の振幅・偏光・波長の指定は加えない。',
 '二乗式sqkと未来側の正時刻sqlを区別する。零時刻の放出点はei76で別に扱い、負時刻の二乗式の解を伝播後の波面へ含めない。Vは同じ正のtcであり、全K光区間にも現在のei43で同じ値を渡す。',
 'Ist (x,y,z) ... so ist '
 'alsoは、同じ波がいま到来する任意の点についての条件付き帰結と読む。全対象出来事と現在のK記録を量化し、その同じ記録の時刻と三位置を使う。到来後の任意の時刻や波の内部全体を到来波面に混ぜない。',
 'x²+y²+z²=V²t²の三平方・二加法・右辺の積と二平方を既存sqj/sqkで保持する。波の未来側の幾何学的読みを数式の文字そのものへ追加するのではなく、放出・到来・正時刻の内容と分ける。',
 '後続u0089以降の座標変換による計算、kでの球面波の結論、二原理の両立性の証明完了は先取りしない。φを1へ固定しない。有限対照例は全物理的モデルや意味同値の自動証明ではない。',
 '第45段落の第一文27トークンと、表示式を末尾に含む第二文13トークンを別々の本文箇所として指す。数式の外部識別子を意味の代用にはしない。',
 '波と放出は同じ仮定箇所に固定した既存describedreferenceで照合する。波役割は放出を存在量化してei76へ結び、放出役割はその同じ波のei76へ結ぶ。参照取得では役割を実行せず、波の現実の存在や仮定の成立を断言しない。',
 '旧合成定義12個と波の構成光線の旧意味規約1個を再利用する。新参照型0個、共通375語、任意52版787語。物体の物質点や系列の出来事の所属と同一視しない。']


@lru_cache(maxsize=1)
def vocabulary():return RestSphericalWaveVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][141:142]):visit(n)
    require(len(seen)==242,'Rest-spherical-wave source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][141:142])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','nao',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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


def reference_roles():return {old:names()['restspherical'+role+'role'] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown wave reference');return 'zgc'


def role_definitions():
    n=names();m=mapping();voc=vocabulary();k=lambda old:call(n[old])
    wavebody=dict(kind='exists',variable='vc',sort='individual',body=call(m['ei76'],v('va'),v('vc'),v('vb')))
    # The wave role has no dependency on either reference. The emission role
    # refers to that wave but never to its own reference.
    defs=[definition(n['restsphericalwaverole'],[('va','individual'),('vb','situation')],'truth',wavebody),
          definition(n['restsphericalemissionrole'],[('va','individual'),('vb','situation')],'truth',call(m['ei76'],k('zfu'),v('va'),v('vb')))]
    for old,role in reference_roles().items():
        defs.append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],k('eirf'),k(reference_anchor(old)),qf(role),k('ri'))))
    return defs


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][111:112],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==2,'Source selection changed')
    tokens=segments[0]['text'].split();equation=segments[1]['text']
    require(len(tokens)==39 and tokens[:3]==['Zur','Zeit','[M0141]'],'Wave assumption opening changed')
    require(tokens[26:29]==['ausbreitet.','Ist','([M0144])'] and equation=='[M0145].','Sentence or equation boundary changed')
    first=tokens[:27];second=tokens[27:]+[equation]
    return dict(rule='Whitespace-delimited fixed transcription; displayed equation completes the second sentence; 1-based inclusive positions.',
        sentences={'restsphericalassumptionsentence':dict(position=[45,1],tokens=first,text=' '.join(first)),
                   'restsphericalequationsentence':dict(position=[45,2],tokens=second,text=' '.join(second))},
        spans={n:list(p) for n,p in SPANS.items()},anchor='Two sentences and the displayed equation on page 901.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(87,89)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-rest-spherical-wave-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[141],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=52,core_edition=12,new_source_assertions=1,total_source_assertions=86,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible rest-spherical-wave document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['restsphericalassumptionsentence'],27),(values['restsphericalequationsentence'],13)]},
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
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
           for old,role in reference_roles().items()}
    refs=TemporalReferences(roles=roles,notes={})
    def described(document,node,role,context):
        if node==values['zgc']:return refs.described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved rest-spherical-wave bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-light-proof-task-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/rest_spherical_wave_visible_profile.py','scripts/check_einstein_rest_spherical_wave_visible.py',
        'scripts/visible_rest_spherical_wave_visible_collection.py','tests/test_rest_spherical_wave_visible_profile.py','docs/einstein-rest-spherical-wave-visible-v1.md',
        'scripts/check_rest_spherical_wave.py','scripts/compose_rest_spherical_wave.py',
        'scripts/check_spherical_wave.py','examples/v014/rest-spherical-wave-core.noema','reports/rest-spherical-wave-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-rest-spherical-wave-visible-evidence-1',core_words=375,profile_words=787,profile_edition=52,
        new_public_relations=1,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=86,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
