"""Connect both transverse ray calculations and their independent measurements."""
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
from scripts import transverse_ray_visible_profile as profile
from scripts.transverse_ray_visible_profile import ROOT,TransverseRayVisibleVocabulary,write_once
from scripts import check_einstein_longitudinal_elimination_visible as previous
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

SOURCE='examples/v016/einstein-transverse-ray-visible-v1.noema'
BRIDGE='data/einstein-transverse-ray-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-transverse-ray-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='soa sob soe sof sog sol som soo soq ei6c ei6d ei6e ei6f ei6g ei6h ei6i ei6j ei6m ei6p ei6s ei6v ei6k ei6l ei6n ei6o ei6q ei6r ei6t ei6u ei6w ei6x'.split()
SENTENCES=dict(transverseraysentence=(42,1))
SPANS=dict(zfg=('transverseraysentence',1,15),zfc=('transverseraysentence',16,16),zfd=('transverseraysentence',17,18),zfe=('transverseraysentence',19,20),zff=('transverseraysentence',21,22))
ROLE_ASSIGNMENTS=dict(transverserestmap='rest',transversemovingmap='moving')
FORWARD_MAPS=dict(zfa='transverserestmap',zfb='transversemovingmap')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*FORWARD_MAPS,*ROLE_ASSIGNMENTS,'transverserestmaprole','transversemovingmaprole']
READINGS=('data/einstein-transverse-ray-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-transverse-ray-u'+str(i).zfill(4)+'-review-v1.json' for i in range(73,81))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0073–u0080を、直前の原点放出と正方向の設定を両横軸へ適用する類推として読む。原点は両系の時刻零・位置零で一致する選択であり、以後の全時刻での原点一致やt=τを要求しない。',
 'Kでは全速さV、縦成分v、選択横成分w=√(V²−v²)の直線、kでは同じ光が選択横軸に沿って速さVで進む。先行の直線伝播・相対運動の読みを保持し、この成分分解を原理から自動証明したとはしない。',
 '各光線の全区間を現在の時計・四座標・光速度範囲と結ぶ。端点の平方和だけで曲がる光路を受理せず、全eitf/seの条件を保持する。未知の履歴や測定は有限例で補わない。',
 'yとzは別の光線・到達出来事・距離・時刻を選べる。同じV,v,φを共有するが、一方の到達測定を他方へ転用しない。kの座標はη/ζ、Kの距離はy/zであり、これらを等置しない。',
 'Auf analoge '
 'Weiseとundは先の縦方向、及び同じ横二軸の導出への類推・並列として読む。wobeiは同じyの計算に伴う二条件、alsoはその値を入れる帰結である。著者の提示を実行履歴や形式証明と同一視しない。',
 '既存soe/sof/sogとsol/som/soo/soqの実切断による数式を再利用し、aは未定φ(v)のまま保持する。原文に明記されたy条件をzでも同形に用いるという省略補完を明示し、光線外の一般変換はここで確定しない。',
 '数値核のv=0や任意係数の例と現在の正のvの物理設定を区別する。全実数軌道は有限評価を拒否する。有理多項式補題・有限関数指紋・引数の対照検査は、一般実数体や物理的導出・意味同値の自動証明ではない。',
 '原刊900頁のAuf analoge '
 'Weiseからζの式の句点までを同じ一文として、第42本文段落第一文の22tokenへ結ぶ。考察1–15、ηの連鎖16、wobei条件17–18、also帰結19–20、und並列21–22を区別する。数式内部のコンマ・セミコロン・句点を別tokenにしない。',
 '31旧合成定義を再利用し、軸から区間記録への二写像は個体から個体への関数を返す一つの汎用参照で記述する。共通375語、任意48版778語。物理の原始関係は追加しない。',
 '二つの閉じた役割は、yoとypそれぞれについてei6dの静止側又は運動側へ候補写像の値を結び、反対側には独立の存在束縛を置く。参照取得では写像や役割を実行しない。実際の二写像の同じ対をei6fで別に要求する。非選択軸への値や未知の参照を既定値で補わない。',
 'zfa/zfbは元の個体引数をそのまま参照写像へ渡す局所定義であり、原文の不透明な参照から物理条件の成立を導かない。逆投影ではこの二参照の元の型を明示して保存し、転送と役割の検査を分ける。']


@lru_cache(maxsize=1)
def vocabulary():return TransverseRayVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][131:136]):visit(n)
    require(len(seen)==295,'Transverse-ray source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][131:136])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','red',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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


def reference_roles():return {old:names()[old+'role'] for old in ROLE_ASSIGNMENTS}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown transverse-map reference')
    return 'zfg'


def role_definitions():
    n=names();m=mapping();voc=vocabulary();k=lambda old:call(n[old])
    defs=[]
    for old,side in ROLE_ASSIGNMENTS.items():
        branches=[]
        for axis,witness in (('yo','vc'),('yp','vd')):
            selected=dict(kind='apply',function=v('va'),arguments=[k(axis)])
            first,second=(selected,v(witness)) if side=='rest' else (v(witness),selected)
            branches.append(dict(kind='exists',variable=witness,sort='individual',body=call(m['ei6d'],first,second,k(axis),k('zb6'))))
        defs.append(definition(n[old+'role'],[('va',profile.MAP),('vb','situation')],'truth',allof(*branches)))
        defs.append(definition(n[old],[],profile.MAP,call(voc._symbols['describedindividualfunctionreference'],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri'))))
    for old,target in FORWARD_MAPS.items():
        defs.append(definition(n[old],[('va','individual')],'individual',dict(kind='apply',function=k(target),arguments=[v('va')])))
    return defs


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][101:106],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==8,'Source selection changed')
    text=' '.join(s['text'] for s in segments);tokens=text.split()
    require(len(tokens)==22 and tokens[:5]==['Auf','analoge','Weise','finden','wir'],'Transverse introduction changed')
    require(tokens[14:]==['Lichtstrahlen:','[M0130]','wobei','[M0131]','also','[M0132]','und','[M0133]'],'Transverse formula chain changed')
    return dict(rule='Whitespace-delimited fixed transcription; mathematical punctuation retained inside placeholders; 1-based inclusive positions.',
        sentences={'transverseraysentence':dict(position=[42,1],tokens=tokens,text=text)},spans={n:list(p) for n,p in SPANS.items()},
        anchor='One sentence across the analogy, eta chain, accompanying conditions, therefore result and parallel zeta result.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(73,81)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-transverse-ray-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[131,132,133,134,135],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=48,core_edition=12,new_source_assertions=5,total_source_assertions=80,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible transverse-ray document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|{n:n for n in ('transverseresty','transverserestz','transversemovingy','transversemovingz')}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['transverseraysentence'],22)]},
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
    refs=profile.IndividualFunctionReferences({(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old] for old,role in reference_roles().items() if old in values})
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span)|refs.handlers()


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved transverse-ray bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-longitudinal-elimination-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/transverse_ray_visible_profile.py','scripts/check_einstein_transverse_ray_visible.py',
        'scripts/visible_transverse_ray_visible_collection.py','tests/test_transverse_ray_visible_profile.py','docs/einstein-transverse-ray-visible-v1.md',
        'scripts/check_frame_light_law.py','scripts/check_origin_light_ray.py','scripts/check_transverse_ray_claim.py',
        'examples/v014/frame-light-law-core.noema','examples/v014/origin-light-ray-core.noema','examples/v014/transverse-ray-claim-core.noema',
        'scripts/check_calculation_discourse.py','scripts/compose_calculation_discourse.py','scripts/check_moving_trip_geometry.py',
        'scripts/compose_frame_light_law.py','scripts/compose_origin_light_ray.py','scripts/compose_transverse_ray_claim.py',
        'scripts/check_coordinate_correspondence.py','reports/transverse-space-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-transverse-ray-visible-evidence-1',core_words=375,profile_words=778,profile_edition=48,
        new_public_relations=0,new_reference_primitives=1,new_source_assertions=5,total_source_assertions=80,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
