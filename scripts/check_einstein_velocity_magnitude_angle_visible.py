"""Connect the first-order law, nonnegative speeds, directed angle and signed composition claim."""
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
from scripts import velocity_magnitude_angle_visible_profile as profile
from scripts.velocity_magnitude_angle_visible_profile import ROOT,VelocityMagnitudeAngleVisibleVocabulary,write_once
from scripts import check_einstein_velocity_addition_setting_visible as previous
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

SOURCE='examples/v016/einstein-velocity-magnitude-angle-visible-v1.noema'
BRIDGE='data/einstein-velocity-magnitude-angle-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-velocity-magnitude-angle-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[190, 191, 0, 1, 2, 3, 4]
SOURCE_VISUAL_REVIEW=[{'actually_displayed': True,
  'independent_human_reading': False,
  'path': 'artifacts/einstein-curved-clock-records-v1/page-905.jpg',
  'sha256': 'b5dc0e1186c2a6a548792d23276455f84d64d77949dffa7299f0d8a36b813acd',
  'tool_chunk': '3dc7a6'},
 {'actually_displayed': True,
  'independent_human_reading': False,
  'path': 'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg',
  'sha256': 'fda62af14de6978b5938e09fa98e63bbf2b29010c1b4250a4b7f41e62bc57591',
  'tool_chunk': 'a5ba31'}]
PUBLIC_RELATIONS={'eisdj': 'intendedtheorydestination',
 'eisox': 'claimcontentcorrespondence',
 'eiso7': 'presentsquantityinterpretation'}
NEW_DEFINITIONS=['szn',
 'szq',
 's2c',
 's2r',
 's2s',
 's2t',
 'sedh',
 'sedi',
 'ejnw',
 'ejnx',
 'ejny',
 'ejnz',
 'ejn2',
 'ejn3',
 'ejn4',
 'ejn5',
 'ejn6',
 'ejoa',
 'ejob',
 'ejoc',
 'ejod',
 'ejoe',
 'ejoh',
 'ejoi',
 'ejoj',
 'ejok',
 'ejol',
 'ejop',
 'ejoq',
 'ejom',
 'ejof',
 'ejog',
 'ejon',
 'ejoo',
 's2g',
 'ejor',
 'ejos',
 'ejot',
 'ejou',
 'ejov',
 'ejow',
 'ejox',
 'ejoy',
 'ejoz',
 'ejo2',
 'ejo3',
 'ejo4',
 'ejo5',
 'ejo6',
 'ejo7',
 'ejpa',
 'ejpb',
 'ejpc',
 'ejpd',
 'ejpe',
 'ejpf',
 'ejpg',
 'ejph',
 'ejpi',
 'ejpj',
 'ejpk']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'eisoy': (64, 1), 'quantityanglesentence': (64, 2), 'calculationwholesentence': (64, 3)}
TOKEN_COUNTS={'eisoy': 15, 'quantityanglesentence': 18, 'calculationwholesentence': 6}
SPANS={'eisoz': ('quantityanglesentence', 1, 3),
 'eiso6': ('quantityanglesentence', 1, 5),
 'zku': ('quantityanglesentence', 5, 5),
 'zkv': ('quantityanglesentence', 6, 18),
 'zkx': ('calculationwholesentence', 1, 5),
 'zkw': ('calculationwholesentence', 6, 6),
 'speedequationsspan': ('quantityanglesentence', 3, 3)}
MULTI_SPANS={}
DESIGNATIONS={'eiso2': ('quantityanglesentence', 1),
 'eiso3': ('quantityanglesentence', 2),
 'eiso5': ('quantityanglesentence', 3)}
ROLE_ASSIGNMENTS={'zkp': 'labmagnituderole',
 'zkq': 'movingmagnituderole',
 'zkt': 'anglepairrole',
 'eiso4': 'anglemeasurerole',
 'zkr': 'labmagnitudeequationrole',
 'zks': 'movingmagnitudeequationrole'}
REFERENCE_SORTS={'zkp': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zkq': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zkt': {'kind': 'function',
         'parameters': ['truth'],
         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eiso4': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zkr': 'individual',
 'zks': 'individual'}
REFERENCE_ANCHORS={'zkp': 'eiso2',
 'zkq': 'eiso3',
 'zkt': 'eiso5',
 'eiso4': 'eiso5',
 'zkr': 'speedequationsspan',
 'zks': 'speedequationsspan'}
ROLE_DEFINITIONS={'zkp': {'kind': 'definition',
         'name': 'labmagnituderole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'ejoi',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'zb6', 'arguments': []}]}},
 'zkq': {'kind': 'definition',
         'name': 'movingmagnituderole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'ejoj',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'zb6', 'arguments': []}]}},
 'zkt': {'kind': 'definition',
         'name': 'anglepairrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['truth'],
                                  'result': {'kind': 'function',
                                             'parameters': ['number'],
                                             'result': 'truth'}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'exists',
                           'variable': 'vd',
                           'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                           'body': {'kind': 'exists',
                                    'variable': 've',
                                    'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                    'body': {'kind': 'exists',
                                             'variable': 'vf',
                                             'sort': {'kind': 'function',
                                                      'parameters': ['number'],
                                                      'result': 'truth'},
                                             'body': {'kind': 'and',
                                                      'arguments': [{'kind': 'and',
                                                                     'arguments': [{'kind': 'call',
                                                                                    'symbol': 'sbg',
                                                                                    'arguments': [{'kind': 'call',
                                                                                                   'symbol': 'zb7',
                                                                                                   'arguments': []}]},
                                                                                   {'kind': 'and',
                                                                                    'arguments': [{'kind': 'call',
                                                                                                   'symbol': 'ejm2',
                                                                                                   'arguments': [{'kind': 'call',
                                                                                                                  'symbol': 'ra',
                                                                                                                  'arguments': []},
                                                                                                                 {'kind': 'call',
                                                                                                                  'symbol': 'zbm',
                                                                                                                  'arguments': []},
                                                                                                                 {'kind': 'call',
                                                                                                                  'symbol': 'zb6',
                                                                                                                  'arguments': []},
                                                                                                                 {'kind': 'call',
                                                                                                                  'symbol': 'zb7',
                                                                                                                  'arguments': []},
                                                                                                                 {'kind': 'call',
                                                                                                                  'symbol': 'bb',
                                                                                                                  'arguments': [{'kind': 'number',
                                                                                                                                 'numerator': 0,
                                                                                                                                 'denominator': 1}]},
                                                                                                                 {'kind': 'call',
                                                                                                                  'symbol': 'bb',
                                                                                                                  'arguments': [{'kind': 'number',
                                                                                                                                 'numerator': 0,
                                                                                                                                 'denominator': 1}]}]},
                                                                                                  {'kind': 'and',
                                                                                                   'arguments': [{'kind': 'call',
                                                                                                                  'symbol': 'ejoj',
                                                                                                                  'arguments': [{'kind': 'call',
                                                                                                                                 'symbol': 'zkq',
                                                                                                                                 'arguments': []},
                                                                                                                                {'kind': 'call',
                                                                                                                                 'symbol': 'zb6',
                                                                                                                                 'arguments': []}]},
                                                                                                                 {'kind': 'call',
                                                                                                                  'symbol': 'ejou',
                                                                                                                  'arguments': [{'kind': 'call',
                                                                                                                                 'symbol': 'zb7',
                                                                                                                                 'arguments': []},
                                                                                                                                {'kind': 'call',
                                                                                                                                 'symbol': 'bb',
                                                                                                                                 'arguments': [{'kind': 'number',
                                                                                                                                                'numerator': 0,
                                                                                                                                                'denominator': 1}]},
                                                                                                                                {'kind': 'call',
                                                                                                                                 'symbol': 'zb7',
                                                                                                                                 'arguments': []},
                                                                                                                                {'kind': 'call',
                                                                                                                                 'symbol': 'zkc',
                                                                                                                                 'arguments': []},
                                                                                                                                {'kind': 'call',
                                                                                                                                 'symbol': 'zkd',
                                                                                                                                 'arguments': []},
                                                                                                                                {'kind': 'call',
                                                                                                                                 'symbol': 'zkq',
                                                                                                                                 'arguments': []},
                                                                                                                                {'kind': 'apply',
                                                                                                                                 'function': {'kind': 'variable',
                                                                                                                                              'name': 'va'},
                                                                                                                                 'arguments': [{'kind': 'equal',
                                                                                                                                                'arguments': [{'kind': 'number',
                                                                                                                                                               'numerator': 0,
                                                                                                                                                               'denominator': 1},
                                                                                                                                                              {'kind': 'number',
                                                                                                                                                               'numerator': 0,
                                                                                                                                                               'denominator': 1}]}]},
                                                                                                                                {'kind': 'apply',
                                                                                                                                 'function': {'kind': 'variable',
                                                                                                                                              'name': 'va'},
                                                                                                                                 'arguments': [{'kind': 'not',
                                                                                                                                                'arguments': [{'kind': 'equal',
                                                                                                                                                               'arguments': [{'kind': 'number',
                                                                                                                                                                              'numerator': 0,
                                                                                                                                                                              'denominator': 1},
                                                                                                                                                                             {'kind': 'number',
                                                                                                                                                                              'numerator': 0,
                                                                                                                                                                              'denominator': 1}]}]}]},
                                                                                                                                {'kind': 'variable',
                                                                                                                                 'name': 'vd'},
                                                                                                                                {'kind': 'variable',
                                                                                                                                 'name': 've'},
                                                                                                                                {'kind': 'variable',
                                                                                                                                 'name': 'vf'},
                                                                                                                                {'kind': 'variable',
                                                                                                                                 'name': 'vc'}]}]}]}]},
                                                                    {'kind': 'call',
                                                                     'symbol': 'ejos',
                                                                     'arguments': [{'kind': 'call',
                                                                                    'symbol': 'zkc',
                                                                                    'arguments': []},
                                                                                   {'kind': 'call',
                                                                                    'symbol': 'zkd',
                                                                                    'arguments': []},
                                                                                   {'kind': 'variable',
                                                                                    'name': 'vd'},
                                                                                   {'kind': 'variable',
                                                                                    'name': 've'},
                                                                                   {'kind': 'variable',
                                                                                    'name': 'vf'},
                                                                                   {'kind': 'variable',
                                                                                    'name': 'vc'}]}]}}}}}},
 'eiso4': {'kind': 'definition',
           'name': 'anglemeasurerole',
           'parameters': [{'name': 'va',
                           'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'ejow',
                    'arguments': [{'kind': 'variable', 'name': 'va'},
                                  {'kind': 'call', 'symbol': 'zb6', 'arguments': []}]}},
 'zkr': {'kind': 'definition',
         'name': 'labmagnitudeequationrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'zb',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'rd', 'arguments': []},
                                {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'ejoi'}},
                                {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'ejok'}},
                                {'kind': 'call', 'symbol': 'eisoq', 'arguments': []},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zks': {'kind': 'definition',
         'name': 'movingmagnitudeequationrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'zb',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'rd', 'arguments': []},
                                {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'ejoj'}},
                                {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'ejol'}},
                                {'kind': 'call', 'symbol': 'eisoq', 'arguments': []},
                                {'kind': 'variable', 'name': 'vb'}]}}}
LOCAL_NAMES=['szn',
 'zkp',
 'zkq',
 'zkr',
 'zks',
 'szq',
 's2c',
 'zkt',
 'zku',
 'zkv',
 's2r',
 's2s',
 's2t',
 'zkw',
 'zkx',
 'sedh',
 'sedi',
 'ejnw',
 'ejnx',
 'ejny',
 'ejnz',
 'ejn2',
 'ejn3',
 'ejn4',
 'ejn5',
 'ejn6',
 'ejoa',
 'ejob',
 'ejoc',
 'eisoy',
 'eisoz',
 'eiso2',
 'eiso3',
 'ejod',
 'ejoe',
 'ejoh',
 'ejoi',
 'ejoj',
 'ejok',
 'ejol',
 'ejop',
 'ejoq',
 'ejom',
 'ejof',
 'ejog',
 'ejon',
 'ejoo',
 's2g',
 'ejor',
 'ejos',
 'ejot',
 'ejou',
 'ejov',
 'ejow',
 'eiso4',
 'eiso5',
 'eiso6',
 'ejox',
 'ejoy',
 'ejoz',
 'ejo2',
 'ejo3',
 'ejo4',
 'ejo5',
 'ejo6',
 'ejo7',
 'ejpa',
 'ejpb',
 'ejpc',
 'ejpd',
 'ejpe',
 'ejpf',
 'ejpg',
 'ejph',
 'ejpi',
 'ejpj',
 'ejpk',
 'labmagnituderole',
 'movingmagnituderole',
 'anglepairrole',
 'anglemeasurerole',
 'labmagnitudeequationrole',
 'movingmagnitudeequationrole',
 'quantityanglesentence',
 'calculationwholesentence',
 'speedequationsspan']
READINGS=('data/einstein-velocity-first-order-source-reading-v1.json',
 'data/einstein-velocity-magnitude-source-reading-v1.json',
 'data/einstein-velocity-angle-source-reading-v1.json',
 'data/einstein-velocity-angle-claim-source-reading-v1.json',
 'data/einstein-velocity-composition-source-reading-v1.json')
REVIEWS=('data/einstein-velocity-magnitude-u0136-review-v1.json',
 'data/einstein-velocity-angle-u0135-review-v1.json',
 'data/einstein-velocity-angle-u0137-review-v1.json',
 'data/einstein-velocity-angle-u0138-review-v1.json',
 'data/einstein-velocity-composition-u0139-review-v1.json',
 'data/einstein-velocity-composition-u0140-review-v1.json')
SEMANTIC_REVIEW=['共通倍率λによる零近傍の微分として第一近似を保持。実用誤差幅や全入力での不一致へ替えない。',
 'U/wの非負ノルム、符号付き成分、全期間と端点の片側微分を保持。零速度を許す二乗式に角度の非零条件を混入しない。',
 '向き付き角の代表(-π,π]、積分による主値と象限補正は既存の明示解釈。直角の幾何学的指定と縦成分零での商の未定義を区別。',
 'M0257の電子転記の分母sinと原刊cosの差は既存訂正記録を保持。元のMathMLを書き換えない。',
 '非負Uに対して負分母の印刷式が偽になる例を残す。w<V、正分母、絶対値分母、二乗等式へ都合よく変えない。',
 '著者の帰結提示と内容の真理、簡単という負担評価と健全な証明を区別。有限診断は全実数積分・微分の証明ではない。']
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
        chain=VelocityMagnitudeAngleVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return VelocityMagnitudeAngleVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==468,'Velocity-addition-setting source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','inside',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.ALL_CONTRACTS))
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
    require(old in ROLE_ASSIGNMENTS,'Unknown velocity-magnitude-angle reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    sort=REFERENCE_SORTS[old]
    return 'describedtruthcutfunctionreference' if sort==profile.PAIR else 'describedsettingreference' if sort=='situation' else 'describedcutreference' if sort==profile.CUT else 'describedreference'


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
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*previous.previous.FORWARD_MAPS,*previous.previous.previous.FORWARD_MAPS,*previous.previous.previous.previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][165:172],inverse);return normalize_document(result)



def text_boundaries():
    units={u['id']:u['text'] for u in author.read(author.UNITS)['units']}
    first,introduction=units['einstein-1905:u0135'].split(' Wir setzen:',1)
    require(introduction=='','Quantity introduction changed')
    angle,calculation=units['einstein-1905:u0139'].split(' Nach einfacher Rechnung ergibt sich:',1)
    require(calculation=='','Calculation boundary changed')
    quantity=' '.join(['Wir setzen:',*(units[f'einstein-1905:u{i:04d}'] for i in range(136,139)),angle])
    conclusion='Nach einfacher Rechnung ergibt sich: '+units['einstein-1905:u0140']
    sentences={}
    for old,value in zip(SENTENCES,(first,quantity,conclusion),strict=True):
        tokens=value.split();require(len(tokens)==TOKEN_COUNTS[old],'Velocity magnitude/angle sentence boundary changed')
        sentences[old]=dict(position=list(SENTENCES[old]),tokens=tokens,text=value)
    require(quantity.split()[2:6]==['[M0252]','und','[M0253]','[M0254]'],'Speed/angle formula boundary changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph64: first-order consequence, three quantity introductions and angle interpretation in one sentence across page905 semicolon, then calculation with its formula. U and w share M0252; designation ordinals count adopted names, not MathML blocks.',
        headings={},sentences=sentences,spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},designations={n:list(p) for n,p in DESIGNATIONS.items()})



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math={};coverage={}
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Velocity magnitude/angle source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(135,141)}
    require(set(coverage)==expected,'Velocity magnitude/angle source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old velocity magnitude/angle review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old velocity magnitude/angle review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Velocity magnitude/angle review coverage differs')
    require(len(SOURCE_ORDER)==len(set(SOURCE_ORDER))==7 and set(SOURCE_ORDER)=={0,1,2,3,4,190,191},'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Velocity magnitude/angle source backprojection differs')
    return dict(schema='noema-einstein-velocity-magnitude-angle-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=3,new_reference_primitives=1,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=63,core_edition=12,new_source_assertions=7,total_source_assertions=140,total_annotations=32,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible velocity-magnitude-angle document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedtruthcutfunctionreference':return profile.TruthCutFunctionReferences(roles)
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
            require(kind in result,'Unknown typed reference')
            return result[kind](document,node,role,context)
        return lookup
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedcutreference','describedsettingreference','describedtruthcutfunctionreference')}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-velocity-addition-setting-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/velocity_magnitude_angle_visible_profile.py','scripts/velocity_magnitude_angle_visible_profile_contracts.py',
        'scripts/check_einstein_velocity_magnitude_angle_visible.py','scripts/visible_velocity_magnitude_angle_visible_collection.py',
        'tests/test_velocity_magnitude_angle_visible.py','docs/einstein-velocity-magnitude-angle-visible-v1.md'}
    for name in ('velocity_first_order','velocity_magnitude_claim','velocity_angle_measure','velocity_angle_claim','velocity_composition_claim'):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256);paths.update(module.DEPENDENCIES)
    paths.update(row['path'] for row in SOURCE_VISUAL_REVIEW)
    paths.add('tests/test_velocity_magnitude_angle_profile.py')
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved velocity-magnitude-angle bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-velocity-magnitude-angle-visible-evidence-1',core_words=375,profile_words=859,profile_edition=63,
        new_public_relations=3,new_reference_primitives=1,new_source_assertions=7,total_source_assertions=140,annotations=32,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
