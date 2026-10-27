"""Connect the same solid sphere, its current surface equation and attached author explanation."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.moving_trip_visible_profile import MovingTextReferences
from scripts.shared_reference import definition
from scripts import physical_meaning_heading_visible_profile as profile
from scripts.physical_meaning_heading_visible_profile import ROOT,PhysicalMeaningHeadingVisibleVocabulary,write_once
from scripts import check_einstein_physical_meaning_heading_visible as previous
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

SOURCE='examples/v016/einstein-sphere-setting-visible-v1.noema'
BRIDGE='data/einstein-sphere-setting-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-sphere-setting-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS
NEW_DEFINITIONS=['ssy',
 'ssz',
 'ejex',
 'ejey',
 'ejez',
 'eje2',
 'eje3',
 'eje4',
 'eje5',
 'eje6',
 'eje7',
 'ejfa',
 'ejfb',
 'ejfc',
 'ejfd',
 'ejfe',
 'ejff',
 'ejfg',
 'ejfh',
 'ejfi',
 'ejfj',
 'ejfk',
 'ejfl',
 'ejfm',
 'ejfn',
 'ejfo',
 'ejfp',
 'ejfq']
SENTENCES={'zhy': (54, 1), 'sphereequationsentence': (54, 2)}
SPANS={'eisn6': ('sphereequationsentence', 16, 17)}
ROLE_ASSIGNMENTS={'zhw': 'spherebodyrole', 'zhx': 'sphereradiusrole'}
FORWARD_MAPS={}
LOCAL_NAMES=['ssy',
 'ssz',
 'ejex',
 'ejey',
 'ejez',
 'eje2',
 'eje3',
 'eje4',
 'eje5',
 'eje6',
 'eje7',
 'ejfa',
 'ejfb',
 'ejfc',
 'ejfd',
 'ejfe',
 'ejff',
 'ejfg',
 'ejfh',
 'ejfi',
 'ejfj',
 'ejfk',
 'ejfl',
 'ejfm',
 'ejfn',
 'ejfo',
 'ejfp',
 'ejfq',
 'zhy',
 'sphereequationsentence',
 'eisn6',
 'eisoa',
 'eisn7',
 'zhw',
 'zhx',
 'spherebodyrole',
 'sphereradiusrole']
READINGS=('data/einstein-sphere-setting-source-reading-v1.json',)
REVIEWS=('data/einstein-sphere-setting-u0110-review-v1.json',
 'data/einstein-sphere-setting-u0111-review-v1.json',
 'data/einstein-sphere-setting-u0281-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0110–u0111と著者脚注u0281を原刊903頁へ照合する。eine starre '
 'Kugelを、同じ静止系で内部と境界を含む閉球を占める理想的な物質連続体として読む。密度・質量の一様性は指定しない。Kugelgestaltという語だけから内部充填が必然的に従うという語義判断ではなく、この一つの球の明示的なモデル選択である。空洞を持つ殻の全てを今回の物体域へ含めたとはしない。',
 '剛性・静止・形状は同じ全物質点の履歴で与える。eje4の全実数三位置への被覆とeje7の全物質点・全対象時刻の現在記録を保持し、有限測定点の球面への一致を全球体の確認へ替えない。',
 '表面は占有領域の境界eje3で独立に定義する。ejfdは同じ現在記録の全範囲で境界とsszの球面式の双方向の一致を述べる。球面の正例だけを範囲に選別せず、少なくとも一つの境界記録を要求する。任意の実数四組が測定済みであるという追加要求はしない。',
 '半径Rは同じzhx、静止側はk、移動を比較する側はK、速度は同じv=zb7。既出の正X並進・0<v<Vの設定を継承する。両系の同時刻面・時刻値を同一視せず、棒専用の長軸や端点を球へ課さない。',
 'Wir betrachtenは思考上の対象設定の採用、Die Gleichung ... '
 'istとコロンはその設定内の球面式の提示として読む。u0111はkのξ²+η²+ζ²=R²であり、後続u0112のK座標への書換えとt=0選択を先取りしない。既出の最終四式は前文脈に保持し、静止側の球面式だけの主張へ変換則の新しい断言を追加しない。',
 'Das heißtは同じ球を静止時の形で説明する脚注である。ruhend '
 'untersuchtは形状を調べる基準が静止系であることを示し、誰かが測定を実行した過去の出来事や、Kでも球形が保たれることを意味させない。一般の球形の語義に原点中心の条件を入れず、同じ本文の設定でのみ中心零を要求する。',
 '原刊の脚注番号は1、固定HTML上の参照はA0016からcite_note-3、注本文はu0281。inventoryのpage_at_end=921を掲載頁と混同しない。注の付着位置と注本文・本文の発話位置を区別する。',
 '局所の有限対照検査、全実数域の有限評価拒否、原刊通読による意味判断を区別する。著者の球面式の数学的・物理的真理を自動証明することを翻訳の成立条件としない。後続のKの時刻零断面・楕円体・収縮はまだ追加しない。',
 '採用済み第53段落に続く第四節冒頭を第54段落とし、第一文23トークン、第二文と球面式17トークンを保持する。式提示の範囲は第二文16–17で、16のist:内にあるコロンを記録する。',
 '半径は設定箇所に結び付く正の切断、球は同じ半径・設定のejfcを役割とする。引用役割を参照取得時に実行せず、世界での存在や一意性を推論しない。',
 '脚注の付着は第一文のKugel直後・vom直前、原刊番号1の第一出現とする。本文位置と注本文を別参照にし、未知入力は補わない。',
 '旧28定義を再利用し、語彙と参照型を追加しない。共通375語とアルファベット、任意profile58/802語を維持する。']


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
    for n in _references(c.document['statements'][163:166]):visit(n)
    require(len(seen)==230,'Sphere-setting source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][163:166])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|{'zhw','eisoa','eisn7'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','town',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    add('eisoa','individual',call(voc._symbols['footnoteattachmentreference'],k('eirf'),k('zhy'),author.num(1),author.num(1),k('ri')))
    add('eisn7','individual',call(voc._symbols['footnotereference'],k('eirf'),k('eisoa'),author.num(1),k('ri')))
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:
        kind='describedcutreference' if old=='zhx' else 'describedreference'
        add(old,profile.CUT if old=='zhx' else 'individual',call(voc._symbols[kind],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown sphere reference');return 'zhy'


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old])
    return [definition(n['sphereradiusrole'],[('va',profile.CUT),('vb','situation')],'truth',call(m['sbg'],v('va'))),
            definition(n['spherebodyrole'],[('va','individual'),('vb','situation')],'truth',call(m['ejfc'],v('va'),k('zhx'),k('zb6')))]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][138:141],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==3,'Source selection changed')
    first,second=segments[0]['text'].split(' Die Gleichung');second='Die Gleichung'+second+' '+segments[1]['text']
    require((len(first.split()),len(second.split()))==(23,17),'Sentence lengths changed')
    require(first.split()[4:6]==['Kugel','vom'] and second.split()[-2:]==['ist:','[M0196].'],'Attachment or equation boundary changed')
    return dict(rule='Adopted body paragraph54 after paragraph53/page902 and the section4 heading; whitespace tokens, 1-based inclusive spans; ist: remains one token.',
        sentences={'zhy':dict(position=[54,1],tokens=first.split(),text=first),
                   'sphereequationsentence':dict(position=[54,2],tokens=second.split(),text=second)},
        spans={n:list(p) for n,p in SPANS.items()},
        attachment=dict(reference='eisoa',sentence='zhy',printed_number=1,occurrence=1,after_token=5,after='Kugel',before='vom',original_page='903',html_reference='A0016/cite_ref-3'),
        footnote=dict(reference='eisn7',attachment='eisoa',printed_number=1,unit='einstein-1905:u0281',text=segments[2]['text'],tokens=segments[2]['text'].split(),original_page='903',inventory_page_at_end='921',html_id='cite_note-3'))


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in (110,111,281)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-sphere-setting-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[163,164,165],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=0,new_reference_primitives=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=58,core_edition=12,new_source_assertions=3,total_source_assertions=110,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible sphere-setting document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,'zhw','eisoa','eisn7')}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],count) for n,count in zip(SENTENCES,(23,17),strict=True)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_models(values):
    key=lambda old:(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri'])
    individuals=TemporalReferences({key('zhw'):values['zhw']},{(values['eirf'],values['eisoa'],1,values['ri']):values['eisn7']})
    cuts=CutReferences({key('zhx'):values['zhx']} if 'zhx' in values else {})
    attachments=MovingTextReferences({},{(values['eirf'],values['zhy'],1,1,values['ri']):values['eisoa']})
    return individuals,cuts,attachments


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    def described(document,node,role,context):
        if node==values['zhy']:return reference_models(values)[0].described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    def cut(document,node,role,context):
        if node==values['zhy']:return reference_models(values)[1].described(document,node,role,context)
        return result['describedcutreference'](document,node,role,context)
    def attachment(document,node,number,occurrence,context):
        if node==values['zhy']:return reference_models(values)[2].attachment(document,node,number,occurrence,context)
        return result['footnoteattachmentreference'](document,node,number,occurrence,context)
    def note(document,node,number,context):
        if node==values['eisoa']:return reference_models(values)[0].footnote(document,node,number,context)
        return result['footnotereference'](document,node,number,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described,describedcutreference=cut,footnoteattachmentreference=attachment,footnotereference=note)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-physical-meaning-heading-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/physical_meaning_heading_visible_profile.py','scripts/check_einstein_sphere_setting_visible.py',
        'scripts/visible_physical_meaning_heading_visible_collection.py','tests/test_sphere_setting_visible.py','docs/einstein-sphere-setting-visible-v1.md',
        'scripts/check_sphere_setting.py','scripts/compose_sphere_setting.py','examples/v014/sphere-setting-core.noema','reports/sphere-setting-v1.json',
        'scripts/check_solid_sphere_geometry.py','scripts/compose_solid_sphere_geometry.py','examples/v014/solid-sphere-geometry-core.noema','reports/solid-sphere-geometry-v1.json',
        'scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved sphere-setting bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-sphere-setting-visible-evidence-1',core_words=375,profile_words=802,profile_edition=58,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=3,total_source_assertions=110,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
