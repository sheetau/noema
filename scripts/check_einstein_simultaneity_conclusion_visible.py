"""Connect the simultaneity conclusion with its strong reading and interpretive norms."""
from copy import deepcopy
from functools import lru_cache
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.rod_experiment_profile import SettingReferences
from scripts.shared_reference import definition
from scripts import simultaneity_conclusion_visible_profile as profile
from scripts.simultaneity_conclusion_visible_profile import ROOT,SimultaneityConclusionVisibleVocabulary,write_once
from scripts import check_einstein_observer_contrast_visible as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts import check_einstein_two_principles as principles
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-simultaneity-conclusion-visible-v1.noema'
BRIDGE='data/einstein-simultaneity-conclusion-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-simultaneity-conclusion-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiui eiuj eiuk eiul eium eiun eiuo eiup eiuq eiur eius eiut eiuu eiuv eiuw eiux eiuy sdx sea sed'.split()
SENTENCES=dict(zbk=(27,1))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,'zbj','comparisonrole']
READINGS=('data/einstein-simultaneity-conclusion-source-reading-v1.json',)
REVIEWS=('data/einstein-simultaneity-conclusion-review-v1.json',)
FORMS={}
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return SimultaneityConclusionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][101:102]):visit(n)
    require(len(seen)==189,'Simultaneity conclusion source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][101:102])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','town',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def comparison_role():
    m=mapping();n=names()
    f=lambda old:dict(kind='function_ref',symbol=m[old])
    body=call(m['sdx'],*[v(x) for x in ('vc','vd','ve','vf')],v('va'),*[f(x) for x in ('zbd','va','eiup','eium')])
    for x in reversed(('vc','vd','ve','vf')):body=dict(kind='exists',variable=x,sort='individual',body=body)
    return definition(n['comparisonrole'],[('va','situation'),('vb','situation')],'truth',body)


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,pos in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),*[author.num(x) for x in pos]))
    doc['declarations'].append(comparison_role())
    add('zbj','situation',call(voc._symbols['describedsettingreference'],k('eirf'),k('zbk'),dict(kind='quote',body=dict(kind='function_ref',symbol=n['comparisonrole'])),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][61:62],inverse);return normalize_document(result)



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0]);row=reading['segments'][0];unit=units[row['unit']]
    require(len(reading['segments'])==1 and row['unit']=='einstein-1905:u0041','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-simultaneity-conclusion-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[101],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        text_boundaries=dict(paragraph=27,sentence=1,whole_unit=True),math=row['math'],semantic_review=[
            '原刊897頁u0041全325文字。直前の観測者の対照から改段した一文を第27段落第一文として参照する。',
            'zbjは比較設定であり、直前の棒の個別実験ydへ同一視しない。既存sdxの有効な出来事対・系対を持つ設定という閉じた役割記述を引用する。',
            '設定参照の取得は引用役割を実行せず、比較域の非空性や結論の真理を含意しない。空の比較設定も参照できる。役割定義にsea/sed/zbjを含めず結論による選別と循環を避ける。',
            '同じ局所時計・表示出来事・共通参照時計・単位と全実数候補の一意性を保持する。sdxは二出来事と二系の四時刻すべての利用可能性を要求し、未付与を非同時へ替えない。',
            '相対運動は既存eiokの完全な固定配置と非零の速度ベクトル。軸・符号の限定、出来事の位置差、速度上限を追加しない。',
            '絶対的意味を与えてはならないという明示的許否と、第二系で非同時と捉える認識上の要請は、物理的真偽や実際の判断・発言と別である。',
            '後半の全称条件sedを変化例の存在へ弱めない。変わる対と保存される対の混在モデルで全称の不成立を確認する。空域での不変性を絶対性の証拠にしない。',
            'alsoは先行eiueを理由とし、sondernは制限eiusと積極的捉え方eiuuの訂正的対置。著者帰属は引用した強い一般化を実行せず、その真理を主張しない。',
            '有限診断と全実数での証明、SVG復号と人の独立読解を区別する。'],
        profile_edition=34,core_edition=12,new_source_assertions=1,total_source_assertions=46,total_annotations=16,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible simultaneity conclusion document differs');return result


BASE=previous.BASE|dict(zbk='zbk',zbj='comparison')
SITUATIONS=(*previous.SITUATIONS,'comparison')


def setting_model(values):
    syntax=canonical(dict(kind='function_ref',symbol=names()['comparisonrole']))
    return SettingReferences({(values['eirf'],values['zbk'],syntax,values['ri']):values['zbj']})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values);old_sentence=result['sentencereference'];old_setting=result['describedsettingreference']
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return values['zbk'] if key==(values['ri'],27,1) else old_sentence(context,paragraph,item)
    def setting(document,node,role,context):
        if node==values['zbk']:return setting_model(values).described(document,node,role,context)
        return old_setting(document,node,role,context)
    return result|dict(sentencereference=sentence,describedsettingreference=setting)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved simultaneity conclusion bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-observer-contrast-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/simultaneity_conclusion_visible_profile.py','scripts/simultaneity_conclusion_visible_profile_contracts.py','scripts/check_einstein_simultaneity_conclusion_visible.py',
        'scripts/visible_simultaneity_conclusion_visible_collection.py','tests/test_simultaneity_conclusion_visible_profile.py','docs/einstein-simultaneity-conclusion-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-simultaneity-conclusion-visible-evidence-1',core_words=375,profile_words=702,profile_edition=34,
        preserved_source_relations=3,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=46,annotations=16,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
