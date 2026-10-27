"""Connect third-frame introduction, the same prior intention, and all chained transform equations."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.moving_trip_visible_profile import MovingTextReferences
from scripts.designation_purpose_profile import DesignationReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from noema.identifiers import load_annotations
from scripts.shared_time import allof
from scripts.shared_reference import definition
from scripts import third_frame_claim_visible_profile as profile
from scripts.third_frame_claim_visible_profile import ROOT,ThirdFrameClaimVisibleVocabulary,write_once
from scripts import check_einstein_phi_determination_intent_visible as previous
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
from scripts.visible_selection_vocabulary import SelectionVocabulary
from scripts.visible_vocabulary_session import vocabulary_session

SOURCE='examples/v016/einstein-third-frame-claim-visible-v1.noema'
BRIDGE='data/einstein-third-frame-claim-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-third-frame-claim-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['sfb', 'sfc', 'srd', 'sre', 'srf', 'srg', 'srh', 'eja2', 'eja3', 'eja4', 'eja5', 'eja6', 'eja7', 'ejba', 'ejbb', 'ejbc', 'ejbd', 'ejbe', 'ejbf', 'ejbg', 'ejbh', 'ejbi', 'ejbj', 'ejbk', 'ejbl', 'ejbm', 'ejbn', 'ejbo', 'ejbp']
SENTENCES=dict(thirdframeintroduction=(49,1),thirdframezero=(49,2),zgp=(49,3))
SPANS={}
ROLE_ASSIGNMENTS=dict(zgi='thirdframe',zgk='thirdframezeroevent')
DESIGNATIONS=dict(eisnr=('thirdframeintroduction',1),eisns=('zgp',1),eisnt=('zgp',2),eisnu=('zgp',3),eisnv=('thirdframezero',1))
FORMS=dict(eisnr='K′',eisns='x′',eisnt='y′',eisnu='z′',eisnv='t′')
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,'zgo',*ROLE_ASSIGNMENTS,*DESIGNATIONS,'thirdframerole','thirdframezerorole']
READINGS=('data/einstein-third-frame-claim-source-reading-v1.json',)
REVIEWS=('data/einstein-third-frame-claim-u0093-review-v1.json','data/einstein-third-frame-claim-u0094-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['固定u0093の三文全体とu0094の四連鎖等式を原刊901頁へ照合する。前文のφ決定意図、第三系導入と並進、三原点と零時刻、座標命名、同じ四式の二回適用とその結果を一つの意味群として読む。',
 'zu diesem '
 'Zweckeは前文で表明した同じ正規化後φ=spcの決定を目指す手段関係。行為内容ejbhの実行とzgmの同じ関数・段階への意図を保ち、意図が新たに生じることを目的にせず、決定の成功・唯一解・具体的方法の完了を要求しない。',
 'noch ein drittesは既出Kとkに加える相異なる第三系K′。並進は全固定配置・全比較時点のeioj、速度成分−v,0,0、原点の全時点横座標零とsfcの対応軸へ結ぶ。印字Ξはkの縦軸と読む。',
 'mögen ... zusammenfallenとes '
 'seiは議論上の仮定。基準出来事zgkでK/kの現在ei46とK′の原点・現在記録の全四成分零を結ぶ。光の放出出来事へ限定せず、異なる出来事の原点や零時刻を組み合わせない。',
 'Wir nennenの対象はK′で測る三位置座標。命名宣言と、同じ地点・長さ単位・状況の現在eixuへの対応を両方保持する。t′は第二文と表示式の同じ第三系時刻であり、三位置座標の命名に第四の命名を補わない。',
 '四つの連鎖等式は同じ出来事の三系の現在記録に対し、vと−vで同じ正規化後φの四式を二回適用する中間式と、各成分のφ(v)φ(−v)倍という最終式を両方保持する。全対象への記録の存在と各系の値の一意性を要求し、同値の別記録を許す。',
 'β(−v)は正の枝srdであり、φの正負引数の等値、φ=1、倍率1、K′とKの相対静止や恒等変換をここで主張しない。x′の現在の第三系座標と以前の補助x′=x−vtを区別する。',
 'wirは著者の論述上の声。導入・仮定・命名・結果提示を同じ著者と第三節へ帰属する。有限対照検査、保存済み代数証拠、原刊との通読判断を区別し、一般物理的導出や意味同値の自動証明と扱わない。',
 '原刊901頁を第49段落の3文へ接続する。第三文はコロン後の四連鎖等式と末尾句点まで含む。原文箇所zgoは第一・第二文、zgpは第三文である。',
 '第三系と共通零出来事は既存describedreferenceと閉じた役割で参照し、参照取得では導入・物理条件を実行しない。第三系はK/kと別、零出来事は同じ物理設定zb6へ結び、光放出に限定しない。',
 '新規呼称を採用順で参照し、K′/x′/y′/z′/t′の表記を5注記として保持する。t′の新しい命名行為は加えない。既出補助x′と第三系座標を語形だけで同一視しない。',
 '旧29定義と7規約を維持する。共通375語とアルファベット不変、任意profile55は796語、新参照型0。物質・軸幾何の基礎を今回新たに証明したとはしない。']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=ThirdFrameClaimVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return ThirdFrameClaimVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][146:148]):visit(n)
    require(len(seen)==285,'Third-frame-claim source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][146:148])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|{'zgo',*ROLE_ASSIGNMENTS,*DESIGNATIONS}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','inside',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def reference_roles():return {old:names()[role] for old,role in [('zgi','thirdframerole'),('zgk','thirdframezerorole')]}


def reference_anchor(old):return {'zgi':'zgo','zgk':'thirdframezero'}[old]


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    x=v('va');s=v('vb')
    third=allof(r('va',x),op('not',op('equal',x,k('ra'))),op('not',op('equal',x,k('zbm'))),r('eisd3',k('zgo'),x,k('eirf'),s))
    zero=r('eja3',x,k('zb6'))
    return [definition(n[name],[('va','individual'),('vb','situation')],'truth',body)
        for name,body in [('thirdframerole',third),('thirdframezerorole',zero)]]


@lru_cache(maxsize=1)
@_with_authoring_session
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    add('zgo','individual',call(voc._symbols['sentencespanreference'],k('eirf'),k('thirdframeintroduction'),k('thirdframezero'),k('ri')))
    for old,(node,index) in DESIGNATIONS.items():add(old,'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri')))
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:
        add(old,'individual',call(voc._symbols['describedreference'],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][116:118],inverse);return normalize_document(result)



def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==2,'Source selection changed')
    pieces=segments[0]['text'].split('. ')
    require(len(pieces)==3 and pieces[0].startswith('Wir führen') and pieces[1].startswith('Zur Zeit') and pieces[2].startswith('Wir nennen') and pieces[2].endswith('Transformationsgleichungen:') and segments[1]['text']=='[M0161]','Sentence boundary changed')
    sentences=[pieces[0]+'.',pieces[1]+'.',pieces[2]+' '+segments[1]['text']]
    require([len(s.split()) for s in sentences]==[36,21,17],'Token boundary changed')
    return dict(rule='Fixed transcription, three source sentences; last sentence includes the displayed four chained equations and final period.',
        sentences={n:dict(position=list(SENTENCES[n]),tokens=text.split(),text=text) for n,text in zip(SENTENCES,sentences,strict=True)},
        sentence_span=dict(zgo=['thirdframeintroduction','thirdframezero']),
        designation_order=dict(thirdframeintroduction=['K′'],thirdframezero=['t′'],zgp=['x′','y′','z′']),
        formula_continuation='M0161',anchor='Paragraph following the phi determination intention, page 901.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(93,95)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        entry=c.entries[old];decl=entry['declaration'];contract=profile.CONTRACTS[new]
        require(decl['parameters']==contract['parameters'] and decl['result']==contract['result'] and entry['arguments']==contract['arguments'] and entry['meaning_ja'].split('] ',1)[-1]==contract['meaning_ja'],'Source contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-third-frame-claim-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[146,147],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,annotations=annotations()['entries'],
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=55,core_edition=12,new_source_assertions=2,total_source_assertions=92,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible third-frame-claim document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,'zgo',*DESIGNATIONS)}|ROLE_ASSIGNMENTS
SITUATIONS=previous.SITUATIONS


def text_model(values):
    return MovingTextReferences({(values['eirf'],values['thirdframeintroduction'],values['thirdframezero'],values['ri']):values['zgo']},{})


def designation_model(values):
    return DesignationReferences({(values['eirf'],values[node],index,values['ri']):values[old] for old,(node,index) in DESIGNATIONS.items()})


def reference_model(values):
    return TemporalReferences({(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS},{})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,last,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:return text_model(values).span(document,first,last,context)
        return result['sentencespanreference'](document,first,last,context)
    def designation(document,node,index,context):
        if node in {values[n] for n in SENTENCES}:return designation_model(values).reference(document,node,index,context)
        return result['designationreference'](document,node,index,context)
    def described(document,node,role,context):
        if node in {values[reference_anchor(n)] for n in ROLE_ASSIGNMENTS}:return reference_model(values).described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencespanreference=span,designationreference=designation,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-phi-determination-intent-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/third_frame_claim_visible_profile.py','scripts/check_einstein_third_frame_claim_visible.py',
        'scripts/visible_third_frame_claim_visible_collection.py','tests/test_third_frame_claim_visible.py','docs/einstein-third-frame-claim-visible-v1.md',
        'scripts/check_third_frame_claim.py','scripts/compose_third_frame_claim.py',
        'scripts/check_third_frame_geometry.py','scripts/compose_third_frame_geometry.py','reports/third-frame-geometry-v1.json','examples/v014/third-frame-geometry-core.noema',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','examples/v014/third-frame-claim-core.noema','reports/third-frame-claim-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    paths.update(annotations()['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved third-frame-claim bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-third-frame-claim-visible-evidence-1',core_words=375,profile_words=796,profile_edition=55,
        new_public_relations=7,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=92,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
