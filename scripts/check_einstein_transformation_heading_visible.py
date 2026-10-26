"""Connect the directed space-time transformation topic and third section heading."""
from copy import deepcopy
from functools import lru_cache
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.shared_time import allof
from scripts.shared_reference import definition
from scripts import transformation_heading_visible_profile as profile
from scripts.transformation_heading_visible_profile import ROOT,TransformationHeadingVisibleVocabulary,write_once
from scripts import check_einstein_simultaneity_conclusion_visible as previous
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

SOURCE='examples/v016/einstein-transformation-heading-visible-v1.noema'
BRIDGE='data/einstein-transformation-heading-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-transformation-heading-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiuz eiu2 eiu3 eiu4 sgu sha'.split()
HEADINGS=dict(eismt=4)
LOCAL_NAMES=[*NEW_DEFINITIONS,*HEADINGS,'eisms','zc7','sectionrole','timecomponentrole']
READINGS=('data/einstein-transformation-heading-source-reading-v1.json',)
REVIEWS=('data/einstein-transformation-heading-review-v1.json',)
FORMS={}
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return TransformationHeadingVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][102:103]):visit(n)
    require(len(seen)==106,'Transformation heading source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][102:103])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(HEADINGS)|{'eisms','zc7'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','rain',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def role_definitions():
    m=mapping();n=names();k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    x=v('va');s=v('vb');event=v('vc');tup=v('vd');frame=v('ve')
    section=r('eisdv',k('eismt'),x,k('eisdx'),k('eirf'),author.num(2),author.num(3),s)
    time=allof(*[op('not',op('equal',x,k(axis))) for axis in ('yn','yo','yp')],
        r('zbd',event),r('va',frame),r('zc5',tup),r('eiuk',event,frame,k('rb'),s),
        r('sca',r('zc6',tup,x),r('zbe',event,frame,k('rb'),s)))
    for binder in reversed(('vc','vd','ve')):time=dict(kind='exists',variable=binder,sort='individual',body=time)
    return [definition(n[name],[('va','individual'),('vb','situation')],'truth',body)
        for name,body in [('sectionrole',section),('timecomponentrole',time)]]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,ordinal in HEADINGS.items():add(old,'individual',call(voc._symbols['headingreference'],k('ri'),author.num(ordinal)))
    doc['declarations']+=role_definitions()
    for old,role in [('eisms','sectionrole'),('zc7','timecomponentrole')]:
        add(old,'individual',call(voc._symbols['describedreference'],k('eirf'),k('eismt'),dict(kind='quote',body=dict(kind='function_ref',symbol=n[role])),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][62:63],inverse);return normalize_document(result)



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0]);row=reading['segments'][0];unit=units[row['unit']]
    require(len(reading['segments'])==1 and row['unit']=='einstein-1905:u0042','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-transformation-heading-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[102],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        heading_ordinal=4,division=reading['division'],math=row['math'],semantic_review=[
            '原刊897頁u0042全155文字の第三節見出し。第一部の見出しを含めた実際の見出し出現順は4、階層深さ2、表示番号3を区別する。節範囲u0042からu0108、次の同階層見出しu0109を保持する。',
            '見出し箇所eismtと区分eismsを分け、既存describedreferenceに第一部直下の第三節という役割を結ぶ。役割の取得は階層関係の真理や主題の実行を意味しない。',
            '時刻成分zc7は三位置軸と異なり、同じ局所時刻の候補値を四組の指定欄に持つ役割として引用する。参照取得時に実測・一意性・非空性を主張せず、引用を実行しない。物理的な完全割当てと四成分の妥当性はeiuz/shaで別に保持する。',
            'eiuzは同じ出来事・系・文脈・長さ/時間単位と実際の三位置座標/時刻を結び、sdの全実数座標一意性とeiukの局所時計・表示・参照時計・全実数時刻一意性を残す。数値組だけでは割当てにならない。',
            'eiu2は同じ一出来事の二つの四組をsguで結び、eiuoの相対運動を第一系から第二系の向きで指定する。異なる出来事の寄せ集め、第一系の時刻の転用、絶対静止の特権へ替えない。',
            '研究主題は閉じた対応関係から変換規則・条件・説明・導出を扱う。見出しから具体式、発見済み、証明済み、全域性、可逆性、線形性を導かない。本文順序は直前の同時性結論zbkから結ぶ。',
            '二値域の束縛診断、数値組と同じ物理的対象の照合、全実数量化の実行拒否を別に検査する。有限診断・SVG復号・意味判断・第三者読解を区別する。'],
        profile_edition=35,core_edition=12,new_source_assertions=1,total_source_assertions=47,total_annotations=16,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible transformation heading document differs');return result


BASE=previous.BASE|dict(eismt='eismt',eisms='eisms',zc7='timecomponent')
SITUATIONS=previous.SITUATIONS


def reference_model(values):
    return TemporalReferences({(values['eirf'],values['eismt'],canonical(dict(kind='function_ref',symbol=names()[role])),values['ri']):values[old]
        for old,role in [('eisms','sectionrole'),('zc7','timecomponentrole')]},{})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values);old_heading=result['headingreference'];old_ref=result['describedreference']
    def heading(context,item):
        key=(context,TextPresentation.coordinate(item))
        return values['eismt'] if key==(values['ri'],4) else old_heading(context,item)
    def described(document,node,role,context):
        if node==values['eismt']:return reference_model(values).described(document,node,role,context)
        return old_ref(document,node,role,context)
    return result|dict(headingreference=heading,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved transformation heading bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-simultaneity-conclusion-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/transformation_heading_visible_profile.py','scripts/transformation_heading_visible_profile_contracts.py','scripts/check_einstein_transformation_heading_visible.py',
        'scripts/visible_transformation_heading_visible_collection.py','tests/test_transformation_heading_visible_profile.py','docs/einstein-transformation-heading-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-transformation-heading-visible-evidence-1',core_words=375,profile_words=705,profile_edition=35,
        preserved_source_relations=3,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=47,annotations=16,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
