"""Connect the velocity-composition heading, planar point assumption, motion query and transformation rewrite."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.moving_trip_visible_profile import MovingTextReferences
from scripts.designation_purpose_profile import DesignationReferences
from scripts.shared_reference import definition
from scripts import velocity_addition_setting_visible_profile as profile
from scripts.velocity_addition_setting_visible_profile import ROOT,VelocityAdditionSettingVisibleVocabulary,write_once
from scripts import check_einstein_clock_transport_visible as previous
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

SOURCE='examples/v016/einstein-velocity-addition-setting-visible-v1.noema'
BRIDGE='data/einstein-velocity-addition-setting-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-velocity-addition-setting-visible-v1'
LABEL=previous.LABEL
PUBLIC_RELATIONS={'eisoo': 'studiestriplequantitycomposition',
 'eisop': 'theoreminquiry',
 'eisou': 'presentspositionfunctiontask',
 'eisov': 'referstopriorestablishedcontent'}
NEW_DEFINITIONS=['syr',
 'sys',
 'syt',
 'ejms',
 'ejmt',
 'ejmu',
 'ejmv',
 'ejmw',
 'ejmx',
 'ejmy',
 'ejmz',
 'ejm2',
 'ejm3',
 'ejm4',
 'ejm5',
 'ejm6',
 'ejm7',
 'ejna',
 'ejnb',
 'ejnc',
 'ejnd',
 'ejne',
 'ejnf',
 'ejng',
 'ejnh',
 'ejni',
 'ejnj',
 'ejnk',
 'ejnl',
 'ejnm',
 'ejnn',
 'ejno',
 'ejnp',
 'ejnq',
 'ejnt',
 'ejnr',
 'ejns',
 'ejnu',
 'ejnv']
FORWARD_MAPS={}
HEADINGS={'eisor': 6}
SENTENCES={'zkg': (62, 1), 'eisow': (63, 1), 'zkh': (63, 2)}
TOKEN_COUNTS={'zkg': 29, 'eisow': 10, 'zkh': 23}
SPANS={'pointintroductionslice': ('zkg', 18, 19)}
MULTI_SPANS={}
DESIGNATIONS={'eisos': ('zkg', 6), 'eisot': ('zkg', 7)}
ROLE_ASSIGNMENTS={'eisoq': 'velocitysectionrole',
 'zkb': 'movingpointrole',
 'zkc': 'pointlongitudinalrole',
 'zkd': 'pointtransverserole'}
REFERENCE_SORTS={'eisoq': 'individual',
 'zkb': 'individual',
 'zkc': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zkd': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}
REFERENCE_ANCHORS={'eisoq': 'eisor', 'zkb': 'pointintroductionslice', 'zkc': 'eisos', 'zkd': 'eisot'}
ROLE_DEFINITIONS={'eisoq': {'kind': 'definition',
           'name': 'velocitysectionrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisdv',
                    'arguments': [{'kind': 'call', 'symbol': 'eisor', 'arguments': []},
                                  {'kind': 'variable', 'name': 'va'},
                                  {'kind': 'call', 'symbol': 'eisdx', 'arguments': []},
                                  {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                  {'kind': 'number', 'numerator': 2, 'denominator': 1},
                                  {'kind': 'number', 'numerator': 5, 'denominator': 1},
                                  {'kind': 'variable', 'name': 'vb'}]}},
 'zkb': {'kind': 'definition',
         'name': 'movingpointrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'exists',
                           'variable': 'vd',
                           'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                           'body': {'kind': 'call',
                                    'symbol': 'ejmw',
                                    'arguments': [{'kind': 'variable', 'name': 'va'},
                                                  {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                                  {'kind': 'variable', 'name': 'vc'},
                                                  {'kind': 'variable', 'name': 'vd'},
                                                  {'kind': 'call', 'symbol': 'zb6', 'arguments': []}]}}}},
 'zkc': {'kind': 'definition',
         'name': 'pointlongitudinalrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'call',
                           'symbol': 'ejmw',
                           'arguments': [{'kind': 'call', 'symbol': 'zkb', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                         {'kind': 'variable', 'name': 'va'},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'call', 'symbol': 'zb6', 'arguments': []}]}}},
 'zkd': {'kind': 'definition',
         'name': 'pointtransverserole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'ejmw',
                  'arguments': [{'kind': 'call', 'symbol': 'zkb', 'arguments': []},
                                {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                {'kind': 'call', 'symbol': 'zkc', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'zb6', 'arguments': []}]}}}
LOCAL_NAMES=['syr',
 'sys',
 'syt',
 'zkb',
 'zkc',
 'zkd',
 'zkg',
 'zkh',
 'ejms',
 'ejmt',
 'ejmu',
 'ejmv',
 'ejmw',
 'ejmx',
 'ejmy',
 'ejmz',
 'eisoq',
 'eisor',
 'eisos',
 'eisot',
 'ejm2',
 'ejm3',
 'ejm4',
 'ejm5',
 'ejm6',
 'ejm7',
 'ejna',
 'ejnb',
 'ejnc',
 'ejnd',
 'ejne',
 'ejnf',
 'ejng',
 'ejnh',
 'ejni',
 'ejnj',
 'ejnk',
 'ejnl',
 'ejnm',
 'ejnn',
 'ejno',
 'ejnp',
 'eisow',
 'ejnq',
 'ejnt',
 'ejnr',
 'ejns',
 'ejnu',
 'ejnv',
 'velocitysectionrole',
 'movingpointrole',
 'pointlongitudinalrole',
 'pointtransverserole',
 'pointintroductionslice']
READINGS=('data/einstein-velocity-opening-source-reading-v1.json',
 'data/einstein-point-motion-claim-source-reading-v1.json')
REVIEWS=('data/einstein-velocity-opening-u0129-review-v1.json',
 'data/einstein-velocity-opening-u0130-review-v1.json',
 'data/einstein-velocity-opening-u0131-review-v1.json',
 'data/einstein-velocity-opening-u0132-review-v1.json',
 'data/einstein-point-motion-u0133-review-v1.json',
 'data/einstein-point-motion-u0134-review-v1.json')
SEMANTIC_REVIEW=['既存の全時刻・全出来事・全記録の範囲を維持。有限標本から完全性を推定しない。',
 '問いに答えの公式を代入せず、存在・唯一性・発見済みを補わない。',
 '点の速度に光速上限を足さない。二成分と分母は符号付きで、非零分母は明示した解釈の定義域として残す。',
 '正の平方根、共通の分母、同一出来事と各系固有時刻を保持。',
 '原文主張4件と既存注記32件を保持。新しい原始述語を文ごとの代用品にしない。']
RELATIONS=previous.RELATIONS|PUBLIC_RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=VelocityAdditionSettingVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return VelocityAdditionSettingVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][186:190]):visit(n)
    require(len(seen)==303,'Velocity-addition-setting source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][186:190])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','give',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.CONTRACTS))
    def add(old,body,result='individual'):doc['declarations'].append(definition(n[old],[],result,body))
    for old,ordinal in HEADINGS.items():add(old,call(voc._symbols['headingreference'],k('ri'),author.num(ordinal)))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    for old,(first,last) in MULTI_SPANS.items():add(old,call(voc._symbols['sentencespanreference'],k('eirf'),k(first),k(last),k('ri')))
    for old,(node,index) in DESIGNATIONS.items():add(old,call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri')))
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:
        add(old,call(voc._symbols[reference_kind(old)],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')),REFERENCE_SORTS[old])
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown velocity-addition-setting reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    sort=REFERENCE_SORTS[old]
    return 'describedsettingreference' if sort=='situation' else 'describedcutreference' if sort==profile.CUT else 'describedreference'


def role_definitions():
    return renamed(list(ROLE_DEFINITIONS.values()),mapping()|names())


def forwarder_definitions():
    ds={d['name']:d for d in source_excerpt()['declarations']};voc=vocabulary();rows=[]
    for old,target in FORWARD_MAPS.items():
        source=ds[old];contract=voc.document()['primitives'][target]
        require(source['parameters']==contract['parameters'] and source['result']==contract['result'],'Arithmetic forwarder signature differs')
        parameters=[('v'+chr(97+i),sort) for i,sort in enumerate(source['parameters'])]
        rows.append(definition(names()[old],parameters,source['result'],call(voc._symbols[target],*(v(n) for n,_ in parameters))))
    return rows



def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    for d in forwarder_definitions():require(ds[d['name']]==d,'Changed arithmetic forwarder')
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*previous.previous.FORWARD_MAPS,*previous.previous.previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][161:165],inverse);return normalize_document(result)



def text_boundaries():
    units={row['unit']:row['text'] for path in READINGS for row in author.read(path)['segments']}
    setting=' '.join(units[f'einstein-1905:u{i:04d}'] for i in range(130,133))
    question,rewrite=units['einstein-1905:u0133'].split(' Führt ',1)
    rewrite='Führt '+rewrite+' '+units['einstein-1905:u0134']
    sentences={}
    for old,value in zip(SENTENCES,(setting,question,rewrite),strict=True):
        tokens=value.split();require(len(tokens)==TOKEN_COUNTS[old],'Velocity-addition sentence boundary changed')
        sentences[old]=dict(position=list(SENTENCES[old]),tokens=tokens,text=value)
    require(setting.split()[17:19]==['ein','Punkt'],'Point introduction span changed')
    require(setting.split()[24]=='[M0247]' and setting.split()[26]=='[M0248]','Component designation changed')
    units_all=author.read(author.UNITS)['units'];ids=[u['id'] for u in units_all]
    first=ids.index('einstein-1905:u0129');last=ids.index('einstein-1905:u0151')
    require(units_all[first]['text']==units['einstein-1905:u0129'],'Heading source changed')
    require(units_all[last]['text'].startswith('II.'),'Next part boundary changed')
    return dict(rule='Page905: sixth heading is section5. Paragraph62 joins the setting, equations and wobei. Paragraph63 contains the question and rewrite; the colon and three equations remain inside the second sentence.',
        headings={n:ordinal for n,ordinal in HEADINGS.items()},section_units=ids[first:last],
        sentences=sentences,spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},designations={n:list(p) for n,p in DESIGNATIONS.items()})



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Velocity-addition setting source reading differs')
            require([start,end]==[0,len(unit['text'])],'Velocity-addition unit is only partially selected')
            require(unit['id'] not in source_units,'Duplicate velocity-addition unit')
            source_units[unit['id']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(source_units)=={f'einstein-1905:u{i:04d}' for i in range(129,135)},'Velocity-addition setting source selection differs')
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old velocity-addition setting review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old velocity-addition setting review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==set(source_units),'Velocity-addition setting review coverage differs')
    require(backprojection(document())==source_excerpt(),'Velocity-addition setting source backprojection differs')
    return dict(schema='noema-einstein-velocity-addition-setting-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=list(range(186,190)),source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=4,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=62,core_edition=12,new_source_assertions=4,total_source_assertions=133,total_annotations=32,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible velocity-addition-setting document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedcutreference':return CutReferences(roles)
    if kind=='describedsettingreference':return SettingReferences(roles)
    require(kind=='describedreference','Unknown reference type');return TemporalReferences(roles,{})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    headings={(values['ri'],ordinal):values[n] for n,ordinal in HEADINGS.items()}
    def heading(context,item):
        key=(context,TextPresentation.coordinate(item))
        return headings[key] if key in headings else result['headingreference'](context,item)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    def passage(document,first,last,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:
            return MovingTextReferences({(values['eirf'],values[a],values[b],values['ri']):values[n] for n,(a,b) in MULTI_SPANS.items()},{}).span(document,first,last,context)
        return result['sentencespanreference'](document,first,last,context)
    def designation(document,node,index,context):
        if node in {values[n] for n in SENTENCES}:
            return DesignationReferences({(values['eirf'],values[a],i,values['ri']):values[n] for n,(a,i) in DESIGNATIONS.items()}).reference(document,node,index,context)
        return result['designationreference'](document,node,index,context)
    def typed(kind):
        nodes={values[reference_anchor(old)] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
        def lookup(document,node,role,context):
            if node in nodes:return reference_model(values,kind).described(document,node,role,context)
            return result[kind](document,node,role,context)
        return lookup
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedcutreference','describedsettingreference')}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-clock-transport-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/velocity_addition_setting_visible_profile.py','scripts/velocity_addition_setting_visible_profile_contracts.py',
        'scripts/check_einstein_velocity_addition_setting_visible.py','scripts/visible_velocity_addition_setting_visible_collection.py',
        'tests/test_velocity_addition_setting_visible.py','docs/einstein-velocity-addition-setting-visible-v1.md'}
    for name in ('velocity_opening_claim','point_motion_records','point_motion_transform','point_motion_claim'):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256);paths.update(module.DEPENDENCIES)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved velocity-addition-setting bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-velocity-addition-setting-visible-evidence-1',core_words=375,profile_words=855,profile_edition=62,
        new_public_relations=4,new_reference_primitives=0,new_source_assertions=4,total_source_assertions=133,annotations=32,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
