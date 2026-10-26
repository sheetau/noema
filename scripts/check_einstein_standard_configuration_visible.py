"""Connect the three-sentence initial configuration of material frames and instruments."""
from copy import deepcopy
from functools import lru_cache
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.moving_trip_visible_profile import MovingTextReferences
from scripts.shared_time import allof
from scripts.shared_reference import definition
from scripts import standard_configuration_visible_profile as profile
from scripts.standard_configuration_visible_profile import ROOT,StandardConfigurationVisibleVocabulary,write_once
from scripts import check_einstein_transformation_heading_visible as previous
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

SOURCE='examples/v016/einstein-standard-configuration-visible-v1.noema'
BRIDGE='data/einstein-standard-configuration-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-standard-configuration-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiu5 eiu6 eiu7 eiva eivb eivc eivd eive eivf eivg eivh eivi eivj eivk eivl eivm eivn eivo eivp eivq eivr eivs eivt sex sexc sey sez sfa'.split()
SENTENCES=dict(configfirst=(28,1),configsecond=(28,2),configthird=(28,3))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,'zb4','zb5','zbm','initialsettingrole','secondframerole']
READINGS=('data/einstein-frame-instruments-source-reading-v1.json',)
REVIEWS=('data/einstein-frame-instruments-review-v1.json',)
FORMS={}
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return StandardConfigurationVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][103:104]):visit(n)
    require(len(seen)==122,'Standard configuration source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][103:104])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|{'zb5','zbm'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','bird',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def role_definitions():
    m=mapping();n=names();k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    x=v('va');s=v('vb')
    second=allof(r('va',x),op('not',op('equal',x,k('ra'))),r('eisd3',k('zb5'),x,k('eirf'),s))
    setting=allof(r('eivf',k('ra'),x),r('eivf',k('zbm'),x),r('eivg',k('ra'),k('zbm'),x),r('eivl',k('ra'),k('zbm'),x))
    return [definition(n[name],[('va',sort),('vb','situation')],'truth',body)
        for name,sort,body in [('secondframerole','individual',second),('initialsettingrole','situation',setting)]]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    add('zb5','individual',call(voc._symbols['sentencespanreference'],k('eirf'),k('configfirst'),k('configthird'),k('ri')))
    doc['declarations']+=role_definitions()
    for old,role,primitive,result in [('zbm','secondframerole','describedreference','individual'),('zb4','initialsettingrole','describedsettingreference','situation')]:
        add(old,result,call(voc._symbols[primitive],k('eirf'),k('zb5'),dict(kind='quote',body=dict(kind='function_ref',symbol=n[role])),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][63:64],inverse);return normalize_document(result)



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0]);row=reading['segments'][0];unit=units[row['unit']]
    require(len(reading['segments'])==1 and row['unit']=='einstein-1905:u0043','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-standard-configuration-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[103],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_span=['configfirst','configthird'],math=row['math'],semantic_review=[
            '原刊897頁u0043の三文全441文字361非空白文字、M0063/M0064/M0065のX/Y/Zを保持。d. h.は第一文内の説明で文を分割しない。三文の範囲をzb5へ結び、第一文だけで段落を代表させない。',
            '第二系zbmは本文箇所で導入された既出静止系とは異なる系という閉じた役割で参照する。初期設定zb4は同じ両系の軸配置と計器条件を候補設定へ適用する役割で参照する。参照取得は引用を実行せず、条件の真理・物理的存在・唯一性を主張しない。両役割に参照循環はない。',
            '全物質点の直線性・非零方向・原点占有と全期間の剛性・静止を保つ。形状の連続性は既存eismvの入力であり有限点から推定しない。幾何原点と各物体の物質点の同一性を区別する。',
            'X支持直線の一致は方向の平行と原点差の共線性から構成し、軸方向の原点ずれを許し横ずれを拒む。Y/Z平行は逆向きも許す。原点一致・軸物体の同一性・右手性・運動後の条件を追加しない。',
            '同じ仕様の物差しは完全共通規約・非空の全特徴・各特徴の全記述集合の双方向一致を要求する。時計は既存eildを使い、二つの非空群のすべての時計対を比較する。現在の表示値・初期位相・遠隔同期の一致を意味しない。',
            '物差しは全物質点の静止・剛性・尺度校正方法、時計は較正と代表配置の静止を保持。校正方法の存在から実測済みを導かず、時計の針や歯車を止めない。',
            '引用ruhendenは既出静止基準の呼称の再使用、d. h.は同じ二系の説明的言い直し。Seien/mögen/sei/es seienによる三文全体の設定採用指示と、著者帰属・見出しからの本文順序を保つ。引用から物理条件を実行しない。',
            '有限境界診断と全実数履歴・完全仕様の意味を区別する。構文復号、旧意味判断の保存、全頁表示、第三者読解を別に扱う。'],
        profile_edition=36,core_edition=12,new_source_assertions=1,total_source_assertions=48,total_annotations=16,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible standard configuration document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,'zb4','zb5','zbm')}
SITUATIONS=(*previous.SITUATIONS,BASE['zb4'])


def reference_model(values):
    return TemporalReferences({(values['eirf'],values['zb5'],canonical(dict(kind='function_ref',symbol=names()['secondframerole'])),values['ri']):values['zbm']},{})


def setting_model(values):
    return SettingReferences({(values['eirf'],values['zb5'],canonical(dict(kind='function_ref',symbol=names()['initialsettingrole'])),values['ri']):values['zb4']})


def text_model(values):
    return MovingTextReferences({(values['eirf'],values['configfirst'],values['configthird'],values['ri']):values['zb5']},{})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values);old_sentence=result['sentencereference'];old_span=result['sentencespanreference'];old_ref=result['describedreference'];old_setting=result['describedsettingreference']
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else old_sentence(context,paragraph,item)
    def span(document,first,last,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:return text_model(values).span(document,first,last,context)
        return old_span(document,first,last,context)
    def described(document,node,role,context):
        if node==values['zb5']:return reference_model(values).described(document,node,role,context)
        return old_ref(document,node,role,context)
    def setting(document,node,role,context):
        if node==values['zb5']:return setting_model(values).described(document,node,role,context)
        return old_setting(document,node,role,context)
    return result|dict(sentencereference=sentence,sentencespanreference=span,describedreference=described,describedsettingreference=setting)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved standard configuration bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-transformation-heading-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/standard_configuration_visible_profile.py','scripts/standard_configuration_visible_profile_contracts.py','scripts/check_einstein_standard_configuration_visible.py',
        'scripts/visible_standard_configuration_visible_collection.py','tests/test_standard_configuration_visible_profile.py','docs/einstein-standard-configuration-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-standard-configuration-visible-evidence-1',core_words=375,profile_words=719,profile_edition=36,
        preserved_source_relations=14,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=48,annotations=16,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
