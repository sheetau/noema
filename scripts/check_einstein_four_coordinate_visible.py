"""Connect current four-coordinate equations, calibration and interpretive annotation."""
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
from scripts import four_coordinate_visible_profile as profile
from scripts.four_coordinate_visible_profile import ROOT,FourCoordinateVisibleVocabulary,write_once
from scripts import check_einstein_transverse_ray_visible as previous
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

SOURCE='examples/v016/einstein-four-coordinate-visible-v1.noema'
BRIDGE='data/einstein-four-coordinate-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-four-coordinate-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['soy', 'soz', 'spa', 'spb', 'spc', 'spd', 'spe', 'spf', 'spg', 'sph', 'spq', 'ei6y', 'ei6z', 'ei62', 'ei63', 'ei64', 'ei65', 'ei66', 'ei67', 'ei7a', 'ei7l', 'ei7b', 'ei7c', 'ei7d', 'ei7e', 'ei7f', 'ei7i', 'ei7g', 'ei7h', 'ei7j', 'ei7k']
SENTENCES=dict(fourcoordinatesentence=(43,1))
SPANS=dict(zfj=('fourcoordinatesentence',1,11),zfk=('fourcoordinatesentence',12,13))
ROLE_ASSIGNMENTS=dict(coordinatespatialfamily='family',zfi='annotation')
FORWARD_MAPS=dict(zfh='coordinatespatialfamily')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*FORWARD_MAPS,*ROLE_ASSIGNMENTS,'coordinatespatialfamilyrole','zfirole']
READINGS=('data/einstein-four-coordinate-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-four-coordinate-u'+str(i).zfill(4)+'-review-v1.json' for i in range(81,85))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0081–u0084を原刊900頁の四式とβまで照合する。Setzen wir ... einは同じx′=x−vtの代入を示す著者の計算提示であり、実際の計算履歴や読者の参加を追加しない。',
 '原刊では以前aをφ(v)と呼んだ後、四式で再びφ(v)と書く。同じ数値のままでは式が一致しないため、ここは既存spcによる新しいφ(v)=a(v)*β(v)への再表示として読む。同じ文字の参照先の変化を明示し、aやφを1に固定しない。',
 '四式は現在の同じ出来事のK/k四座標を全範囲で結ぶ。全実数四組が実際の測定記録として存在するという追加主張ではない。余分な解と対応の欠落を双方向の条件で拒否し、同じ値を持つ別記録を一つの識別子へ潰さない。',
 '三光線から一般式への拡張は、先行の同じアフィン係数と零原点を用いる。ei66で全入力の空間行、現在の全対応、実際の原点と三光線の独立な正時刻による五点条件を結ぶ。原文に逐語的にはない十分条件であるため、既存zflの解釈注記として著者発話の外に置く。',
 '先行四式のx′は同じKのx−vtを指し、新しい四式ではτ=φβ(t−vx/V²)、ξ=φβ(x−vt)、η=φy、ζ=φzと記述する。時間式と縦式だけにβがあり、y/zの結果やt/τの役割を交換しない。',
 'wobeiはこの四式で用いたβの記号規約を補うものとして読む。βは正の1/√(1−(v/V)²)であり、v/Vという別の慣習を使わない。定義域は0≤v<V、現在の物理設定では既出v>0を保つ。',
 '有理多項式による再表示・較正補題と有限切断・引用の対照検査を、一般実数体・物理的導出や意味同値の自動証明とはしない。未知性と初期位置の仮定を外した加法定数は次のu0085へ残す。',
 '31旧合成定義と既存の部分解釈契約zflを再利用し、個体から四切断関数を返す族の汎用参照を1個追加する。共通375語、任意49版780語。',
 '空間関数族の閉じた役割は、一つの共通行列と定数ベクトルによりyn/yo/ypの各関数をei6zへ結ぶ。参照取得では役割や関数を実行せず、実際の原点・三光線との接続はei65/ei66で別に要求する。',
 '解釈注記zfiは、四式の箇所を基準にzflによる役割で参照する対象であり、原文内の著者脚注ではない。参照取得から原典への所属や著者の発話を導かない。ei7hの注記をei7gの著者メッセージの外側に保持する。',
 'βの表示には句点がなく、同じ文はu0085冒頭のundからist.まで続く。第43本文段落第一文22tokenを保持し、四式1–11、wobeiとβ12–13を指す。文脈として保持するu0085[0,63]の主張統合を今回の実績に加えない。']


@lru_cache(maxsize=1)
def vocabulary():return FourCoordinateVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][136:138]):visit(n)
    require(len(seen)==337,'Four-coordinate source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][136:138])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','give',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    return 'zfj'


def role_definitions():
    n=names();m=mapping();voc=vocabulary();k=lambda old:call(n[old])
    rows=[]
    for axis in ('yn','yo','yp'):
        selected=dict(kind='apply',function=v('va'),arguments=[k(axis)])
        rows.append(call(m['ei6z'],selected,k(axis),v('vc'),v('vd')))
    body=dict(kind='exists',variable='vc',sort=profile.MATRIX,
              body=dict(kind='exists',variable='vd',sort=profile.VECTOR,body=allof(*rows)))
    defs=[definition(n['coordinatespatialfamilyrole'],[('va',profile.MAP),('vb','situation')],'truth',body)]
    defs.append(definition(n['coordinatespatialfamily'],[],profile.MAP,
        call(voc._symbols['describedindividualfourcutfunctionfamilyreference'],k('eirf'),k('zfj'),qf(n['coordinatespatialfamilyrole']),k('ri'))))
    defs.append(definition(n['zfh'],[('va','individual')],profile.TAU,
        dict(kind='apply',function=k('coordinatespatialfamily'),arguments=[v('va')])))
    defs.append(definition(n['zfirole'],[('va','individual'),('vb','situation')],'truth',
        call(m['zfl'],v('va'),k('rd'),dict(kind='quote',body=call(m['ei66'])),dict(kind='quote',body=call(m['ei7b'])),k('eisms'),v('vb'))))
    defs.append(definition(n['zfi'],[],'individual',
        call(voc._symbols['describedreference'],k('eirf'),k('zfj'),qf(n['zfirole']),k('ri'))))
    return defs


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][106:108],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==4,'Source selection changed')
    unit=next(u for u in author.read(author.UNITS)['units'] if u['id']=='einstein-1905:u0085')
    tail=unit['text'].split(' Macht man ',1)[0]
    require(tail=='und [M0137] eine vorläufig unbekannte Funktion von [M0138] ist.','Sentence continuation changed')
    text=' '.join(s['text'] for s in segments)+' '+tail;tokens=text.split()
    require(len(tokens)==22 and tokens[:4]==['Setzen','wir','für','[M0134]'],'Four-coordinate introduction changed')
    require(tokens[10:14]==['[M0135]','wobei','[M0136]','und'] and tokens[-1]=='ist.','Formula or continuation boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; mathematical punctuation retained inside placeholders; 1-based inclusive positions.',
        sentences={'fourcoordinatesentence':dict(position=[43,1],tokens=tokens,text=text)},spans={n:list(p) for n,p in SPANS.items()},
        sentence_context_only=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,len(tail)],text=tail,assertions_integrated_here=False),
        anchor='The beta formula does not end the sentence; retain the following unknown-function clause as reference context only.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(81,85)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-four-coordinate-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[136,137],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=49,core_edition=12,new_source_assertions=2,total_source_assertions=82,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible four-coordinate document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|dict(zfi='additionalconditionannotation')
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['fourcoordinatesentence'],22)]},
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
    key=lambda old:(values['eirf'],values['zfj'],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri'])
    refs=profile.IndividualFourCutFamilyReferences({key('coordinatespatialfamily'):values['coordinatespatialfamily']} if 'coordinatespatialfamily' in values else {})
    notes=TemporalReferences({key('zfi'):values['zfi']},{})
    def described(document,node,role,context):
        if node==values['zfj']:return notes.described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described)|refs.handlers()


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved four-coordinate bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-transverse-ray-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/four_coordinate_visible_profile.py','scripts/check_einstein_four_coordinate_visible.py',
        'scripts/visible_four_coordinate_visible_collection.py','tests/test_four_coordinate_visible_profile.py','docs/einstein-four-coordinate-visible-v1.md',
        'scripts/check_frame_light_law.py','scripts/check_origin_light_ray.py','scripts/check_transverse_ray_claim.py',
        'examples/v014/frame-light-law-core.noema','examples/v014/origin-light-ray-core.noema','examples/v014/four-coordinate-claim-core.noema',
        'scripts/check_calculation_discourse.py','scripts/compose_calculation_discourse.py','scripts/check_moving_trip_geometry.py',
        'scripts/compose_frame_light_law.py','scripts/compose_origin_light_ray.py','scripts/compose_transverse_ray_claim.py',
        'scripts/check_coordinate_correspondence.py','reports/transverse-space-v1.json',
        'scripts/check_spatial_affine_calibration.py','scripts/compose_spatial_affine_calibration.py','scripts/check_four_coordinate_claim.py','scripts/compose_four_coordinate_claim.py',
        'examples/v014/spatial-affine-calibration-core.noema','examples/v014/four-coordinate-claim-core.noema',
        'reports/spatial-affine-calibration-v1.json','reports/four-coordinates-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-four-coordinate-visible-evidence-1',core_words=375,profile_words=780,profile_edition=49,
        new_public_relations=1,new_reference_primitives=1,new_source_assertions=2,total_source_assertions=82,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
