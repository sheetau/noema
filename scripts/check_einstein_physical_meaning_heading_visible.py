"""Connect the fourth section topic to current equations, moving rigid bodies and moving clocks."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.shared_reference import definition
from scripts import physical_meaning_heading_visible_profile as profile
from scripts.physical_meaning_heading_visible_profile import ROOT,PhysicalMeaningHeadingVisibleVocabulary,write_once
from scripts import check_einstein_final_transform_claim_visible as previous
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

SOURCE='examples/v016/einstein-physical-meaning-heading-visible-v1.noema'
BRIDGE='data/einstein-physical-meaning-heading-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-physical-meaning-heading-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['ejer', 'ejes', 'ejet', 'ejeu', 'ejev', 'ejew']
HEADINGS={'zht':5}
ROLE_ASSIGNMENTS={'eisn5': 'physicalmeaningsectionrole'}
FORWARD_MAPS={}
LOCAL_NAMES=['ejer', 'ejes', 'ejet', 'ejeu', 'ejev', 'ejew', 'zht', 'eisn5', 'physicalmeaningsectionrole']
READINGS=('data/einstein-physical-meaning-heading-source-v1.json',)
REVIEWS=('data/einstein-physical-meaning-heading-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['原刊903頁のu0109全体を対象とする。第四節は第一部に直接属する深さ2・表示番号4であり、範囲はu0109–u0128。見出しの案内と後続本文の物理的主張・完成を区別する。',
 'erhaltenen '
 'Gleichungenは第三節末に得た同じ四座標変換を指す。ejeuは同じ現在のK/k記録の範囲とssnの四式を保持し、名前だけの方程式又は別の旧範囲へ置き換えない。見出し自体は実測や変換則の真理を断言しない。',
 'bewegte starre '
 'Körperは同じ二系の比較で、同伴側kの尺度と同時性で剛性を持ち、Kに対して動く物体の主題として読む。eigyの全物質点間距離とeiagの全履歴を保持する。中心又は二端だけで剛性を済ませない。',
 'bewegte Uhrenは時計の代表配置の位置変化として読む。針や内部機構が動いているだけの静置時計を含めず、内部の全物質点を静止又は等速へ固定しない。見出しから時計の同期・校正・特定の遅れを追加しない。',
 '対象の運動は区間内に位置変化があるという分類であり、見出しに印刷されていない特定の軸方向・一定速度・収縮率を加えない。各系の期間は各系の時刻規約を使う。',
 '物理的意味は既存zhrの研究の提示を、物理的記録と方程式、剛性と時計配置の合成内容へ接続して読む。文字列や原語の名称だけを意味に替えず、二対象の一方を落とさない。',
 '有限検査は局所的な運動の証人、全履歴への引数接続、二対象と同じ四式の引用、見出しの階層と順序を調べる。実数全域は有限評価の拒否を保持し、例化した二時刻で全履歴を証明したとはしない。u0110以降及び著者脚注u0281の本文統合は後続。',
 '見出しの出現順5、表示番号4、階層深さ2を区別する。区分を第一部直下の第四節という閉じた役割で参照し、引用を実行しない。',
 '旧6定義と採用済み1規約を再利用。共通375語とアルファベットを維持し、任意profile58/802語。新しい参照型は追加しない。']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=PhysicalMeaningHeadingVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return PhysicalMeaningHeadingVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][162:163]):visit(n)
    require(len(seen)==207,'Physical-meaning-heading source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][162:163])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above', 'round', 'treeone', 'treeone', 'home', 'rain')+(temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


@lru_cache(maxsize=1)
@_with_authoring_session
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    add('zht','individual',call(voc._symbols['headingreference'],k('ri'),author.num(5)))
    doc['declarations']+=role_definitions()
    add('eisn5','individual',call(voc._symbols['describedreference'],k('eirf'),k('zht'),qf(reference_roles()['eisn5']),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old=='eisn5','Unknown fourth section reference')
    return 'zht'


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old])
    body=call(m['eisdv'],k('zht'),v('va'),k('eisdx'),k('eirf'),author.num(2),author.num(4),v('vb'))
    return [definition(n['physicalmeaningsectionrole'],[('va','individual'),('vb','situation')],'truth',body)]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][137:138],inverse);return normalize_document(result)



def text_boundaries():
    units=author.read(author.UNITS)['units'];headings=[u for u in units if u['kind']=='heading']
    require(headings[4]['id']=='einstein-1905:u0109' and headings[5]['id']=='einstein-1905:u0129','Heading order changed')
    require(headings[4]['text']==author.read(READINGS[0])['segments'][0]['text'],'Heading text changed')
    return dict(heading_ordinal=5,displayed_number=4,depth=2,parent='eisdx',heading='zht',section='eisn5',first_unit='einstein-1905:u0109',last_unit='einstein-1905:u0128',next_heading='einstein-1905:u0129',text=headings[4]['text'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(109,110)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        entry=c.entries[old];d=entry['declaration']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=entry['arguments'],meaning_ja=entry['meaning_ja'].split('] ',1)[-1]),'Source contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-physical-meaning-heading-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[162],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        heading_ordinals=HEADINGS,text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=1,new_reference_primitives=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=58,core_edition=12,new_source_assertions=1,total_source_assertions=107,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible physical-meaning-heading document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS





def reference_model(values):
    key=(values['eirf'],values['zht'],canonical(dict(kind='function_ref',symbol=reference_roles()['eisn5'])),values['ri'])
    return TemporalReferences({key:values['eisn5']},{})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    def heading(context,item):
        key=(context,TextPresentation.coordinate(item))
        return values['zht'] if key==(values['ri'],5) else result['headingreference'](context,item)
    def described(document,node,role,context):
        if node==values['zht']:return reference_model(values).described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    return result|dict(headingreference=heading,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-final-transform-claim-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/physical_meaning_heading_visible_profile.py','scripts/check_einstein_physical_meaning_heading_visible.py',
        'scripts/visible_physical_meaning_heading_visible_collection.py','tests/test_physical_meaning_heading_visible.py','docs/einstein-physical-meaning-heading-visible-v1.md',
        'scripts/check_physical_meaning_heading.py','scripts/compose_physical_meaning_heading.py',
        'scripts/check_physical_meaning_heading.py','scripts/compose_physical_meaning_heading.py','reports/physical-meaning-heading-v1.json','examples/v014/physical-meaning-heading-core.noema',
        'scripts/check_transverse_comparison_scope.py','scripts/compose_transverse_comparison_scope.py','reports/transverse-comparison-scope-v1.json','examples/v014/transverse-comparison-scope-core.noema',
        'scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','scripts/check_first_principle.py','scripts/check_material_relative_frame.py','scripts/check_four_coordinate_claim.py','examples/v014/physical-meaning-heading-core.noema','reports/physical-meaning-heading-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved physical-meaning-heading bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-physical-meaning-heading-visible-evidence-1',core_words=375,profile_words=802,profile_edition=58,
        new_public_relations=1,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=107,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
