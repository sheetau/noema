"""Connect the complete observational list, experimental comparisons and scoped motion summary."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.moving_trip_visible_profile import MovingTextReferences
from scripts.designation_purpose_profile import DesignationReferences
from scripts.shared_reference import definition
from scripts import tenth_observables_visible_profile as profile
from scripts.tenth_observables_visible_profile import ROOT,TenthObservablesVisibleVocabulary,write_once
from scripts import check_einstein_tenth_energy_visible as previous
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

from scripts.tenth_observables_reference_roles import build_roles
SOURCE='examples/v016/einstein-tenth-observables-visible-v1.noema'
BRIDGE='data/einstein-tenth-observables-visible-bridge-v1.json'
SOURCE_ORDER=[280, 268, 269, 270, 271, 272, 273, 274, 275, 276, 281]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-p920-0.jpg',
  'sha256': '75fa5ab4f9e6a4d3bbd0004ef82257c531ab5b60bdc141c8edc006e208f3bd2c',
  'actually_displayed': True,
  'display_method': 'Current goal turn: tools.view_image forwarded with image()',
  'independent_human_reading': False},
 {'path': 'artifacts/written-facsimiles-v1/einstein-p921-0.jpg',
  'sha256': '29767bdc575e6f71bbd89fa298314413315cf508ad2afe515c5c5940fe726a88',
  'actually_displayed': True,
  'display_method': 'Current goal turn: tools.view_image forwarded with image()',
  'independent_human_reading': False}]
PUBLIC_RELATIONS={'eis3r': 'instrumentquantitycalibration',
 'eis3s': 'physicalsignalacquisition',
 'eis3t': 'performedbinarycalculation',
 'eis3u': 'causalrecordavailability',
 'eis3v': 'orderedcontentpart',
 'eis36': 'claimindependentmethod',
 'eis37': 'performedquantitycomparison',
 'eis4a': 'oscillatingfieldmeasurementcoupling',
 'eis4b': 'measurementperiodthreshold',
 'eis4f': 'potentialworkchargeunit',
 'eis4t': 'mechanicalinteractioncontribution',
 'eis6v': 'undertakesorderedpresentation',
 'eis6w': 'backgroundmotioncandidate'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['le',
 'lf',
 'setk',
 'seto',
 'sets',
 'seur',
 'seus',
 'seut',
 'seuu',
 'seuv',
 'seuw',
 'sevc',
 'sevf',
 'sevh',
 'eqh',
 'eqs',
 'eqt',
 'equ',
 'eqv',
 'eqw',
 'eqx',
 'eqy',
 'eqz',
 'eq2',
 'eq3',
 'eq4',
 'eq5',
 'eq6',
 'eq7',
 'era',
 'erb',
 'erc',
 'erf',
 'erg',
 'ere',
 'erh',
 'eri',
 'erj',
 'erk',
 'erl',
 'erm',
 'ern',
 'ero',
 'erp',
 'erq',
 'err',
 'ers',
 'ert',
 'eru',
 'erv',
 'erw',
 'erx',
 'ery',
 'erz',
 'er2',
 'er3',
 'er4',
 'er5',
 'er6',
 'er7',
 'esa',
 'esb',
 'esc',
 'esd',
 'ese',
 'esf',
 'esg',
 'esh',
 'esi',
 'esj',
 'esk',
 'esl',
 'esm',
 'esn',
 'eso',
 'esp',
 'esq',
 'esr',
 'ess',
 'est',
 'esu',
 'esv',
 'esw',
 'esx',
 'esy',
 'esz',
 'es2',
 'es3',
 'es4',
 'es5',
 'es6',
 'eta',
 'es7',
 'etd',
 'etg',
 'etj',
 'etb',
 'etc',
 'ete',
 'etf',
 'eth',
 'eti',
 'etk',
 'etl',
 'et7',
 'eua',
 'eub',
 'euc',
 'eud',
 'eue',
 'euf',
 'eug',
 'euh',
 'eui',
 'euj',
 'euk',
 'eul',
 'eum',
 'eun',
 'euo',
 'eup',
 'euq',
 'eur',
 'eus',
 'eut',
 'euu',
 'euv',
 'euw',
 'eux',
 'euy',
 'euz',
 'eu2',
 'eu3',
 'eu6',
 'eu7',
 'eva',
 'evc',
 'evd',
 'eve']
REUSED_BODIES={}
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'eis3w': [115, 1],
 'eis3y': [116, 1],
 'eis3z': [116, 2],
 'eis4c': [117, 1],
 'tenthobservablespotentialsentence': [118, 1],
 'tenthobservablescurvaturecondition': [119, 1],
 'tenthobservablescurvaturederivation': [119, 2],
 'eis6j': [120, 1]}
SPANS={'eis32': ['eis3z', 35, 'eis3z', 35],
 'tenthobservablesamtoken': ['eis3z', 17, 'eis3z', 17],
 'tenthobservablesaetoken': ['eis3z', 22, 'eis3z', 22],
 'eis4d': ['eis4c', 10, 'eis4c', 28],
 'eis4e': ['eis4c', 17, 'eis4c', 25],
 'eis4q': ['tenthobservablespotentialsentence', 1, 'tenthobservablespotentialsentence', 27],
 'eis4r': ['tenthobservablespotentialsentence', 28, 'tenthobservablespotentialsentence', 28],
 'eis4u': ['tenthobservablescurvaturecondition', 1, 'tenthobservablescurvaturederivation', 8],
 'eis4v': ['tenthobservablescurvaturederivation', 9, 'tenthobservablescurvaturederivation', 9],
 'eis4w': ['tenthobservablescurvaturederivation', 10, 'tenthobservablescurvaturederivation', 10],
 'eis4x': ['tenthobservablescurvaturederivation', 11, 'tenthobservablescurvaturederivation', 11],
 'tenthobservablesrtoken': ['tenthobservablescurvaturecondition',
                            6,
                            'tenthobservablescurvaturecondition',
                            6],
 'tenthobservablesntoken': ['tenthobservablescurvaturecondition',
                            19,
                            'tenthobservablescurvaturecondition',
                            19]}
MULTI_SPANS={'eis3x': ['eis3y', 'eis3z']}
DESIGNATIONS={'eis33': ['tenthobservablesamtoken', 1],
 'eis34': ['tenthobservablesaetoken', 1],
 'eis4s': ['eis4r', 1],
 'eis4y': ['tenthobservablesrtoken', 1],
 'eis4z': ['tenthobservablesntoken', 1]}
FORMS={'eis33': 'A_m', 'eis34': 'A_e', 'eis4s': 'P', 'eis4y': 'R', 'eis4z': 'N'}
ROLE_ASSIGNMENTS={'eis4g': 'observedroleeis4g',
 'eis4h': 'observedroleeis4h',
 'eis4i': 'observedroleeis4i',
 'eis4j': 'observedroleeis4j',
 'eis4k': 'observedroleeis4k',
 'eis4l': 'observedroleeis4l',
 'eis4m': 'observedroleeis4m',
 'eis4n': 'observedroleeis4n',
 'eis4o': 'observedroleeis4o',
 'eis4p': 'observedroleeis4p',
 'eis5a': 'observedroleeis5a',
 'eis5b': 'observedroleeis5b',
 'eis5c': 'observedroleeis5c',
 'eis5d': 'observedroleeis5d',
 'eis5e': 'observedroleeis5e',
 'eis5f': 'observedroleeis5f',
 'eis5g': 'observedroleeis5g',
 'eis5h': 'observedroleeis5h',
 'eis5i': 'observedroleeis5i',
 'eis5j': 'observedroleeis5j',
 'eis5k': 'observedroleeis5k',
 'eis5l': 'observedroleeis5l',
 'eis5m': 'observedroleeis5m',
 'eis5n': 'observedroleeis5n',
 'eis5o': 'observedroleeis5o',
 'eis5p': 'observedroleeis5p',
 'eis5q': 'observedroleeis5q',
 'eis5r': 'observedroleeis5r',
 'eis5s': 'observedroleeis5s',
 'eis35': 'observedroleeis35'}
REFERENCE_ANCHORS={'eis4g': 'eis4q',
 'eis4h': 'eis4q',
 'eis4i': 'eis4q',
 'eis4j': 'eis4r',
 'eis4k': 'eis4q',
 'eis4l': 'eis4q',
 'eis4m': 'eis4q',
 'eis4n': 'eis4q',
 'eis4o': 'eis4q',
 'eis4p': 'eis4q',
 'eis5a': 'eis4u',
 'eis5b': 'eis4u',
 'eis5c': 'eis4u',
 'eis5d': 'eis4u',
 'eis5e': 'eis4u',
 'eis5f': 'eis4u',
 'eis5g': 'eis4u',
 'eis5h': 'eis4u',
 'eis5i': 'eis4u',
 'eis5j': 'eis4u',
 'eis5k': 'eis4u',
 'eis5l': 'eis4u',
 'eis5m': 'eis4u',
 'eis5n': 'eis4u',
 'eis5o': 'eis4u',
 'eis5p': 'eis4u',
 'eis5q': 'eis4u',
 'eis5r': 'tenthobservablesntoken',
 'eis5s': 'tenthobservablesrtoken',
 'eis35': 'eis3x'}
REFERENCE_SORTS={'eis4g': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eis4h': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis4i': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis4j': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis4k': 'individual',
 'eis4l': 'number',
 'eis4m': 'number',
 'eis4n': 'individual',
 'eis4o': 'individual',
 'eis4p': 'number',
 'eis5a': 'individual',
 'eis5b': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': 'truth'},
 'eis5c': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': {'kind': 'function',
                      'parameters': ['individual'],
                      'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'eis5d': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eis5e': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eis5f': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eis5g': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eis5h': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis5i': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis5j': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis5k': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function',
                      'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                      'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'eis5l': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function',
                      'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                      'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'eis5m': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                          {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                          {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                          {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': 'truth'},
 'eis5n': 'individual',
 'eis5o': 'individual',
 'eis5p': 'individual',
 'eis5q': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis5r': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis5s': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis35': 'individual'}
REFERENCE_KINDS={'eis4g': 'describedcutfunctionreference',
 'eis4h': 'describedcutreference',
 'eis4i': 'describedcutreference',
 'eis4j': 'describedcutreference',
 'eis4k': 'describedreference',
 'eis4l': 'describedrationalreference',
 'eis4m': 'describedrationalreference',
 'eis4n': 'describedreference',
 'eis4o': 'describedreference',
 'eis4p': 'describedrationalreference',
 'eis5a': 'describedreference',
 'eis5b': 'describedcuttruthfunctionreference',
 'eis5c': 'describedcutindividualcutfunctionfamilyreference',
 'eis5d': 'describedindividualcutfunctionreference',
 'eis5e': 'describedcutfunctionreference',
 'eis5f': 'describedcutfunctionreference',
 'eis5g': 'describedcutfunctionreference',
 'eis5h': 'describedcutreference',
 'eis5i': 'describedcutreference',
 'eis5j': 'describedcutreference',
 'eis5k': 'describedindividualfourcutfunctionfamilyreference',
 'eis5l': 'describedindividualfourcutfunctionfamilyreference',
 'eis5m': 'describedfourcuttruthfunctionreference',
 'eis5n': 'describedreference',
 'eis5o': 'describedreference',
 'eis5p': 'describedreference',
 'eis5q': 'describedcutreference',
 'eis5r': 'describedcutreference',
 'eis5s': 'describedcutreference',
 'eis35': 'describedreference'}
LOCAL_NAMES=['eis3w',
 'eis3y',
 'eis3z',
 'eis4c',
 'tenthobservablespotentialsentence',
 'tenthobservablescurvaturecondition',
 'tenthobservablescurvaturederivation',
 'eis6j',
 'eis32',
 'tenthobservablesamtoken',
 'tenthobservablesaetoken',
 'eis4d',
 'eis4e',
 'eis4q',
 'eis4r',
 'eis4u',
 'eis4v',
 'eis4w',
 'eis4x',
 'tenthobservablesrtoken',
 'tenthobservablesntoken',
 'eis3x',
 'eis4g',
 'eis4h',
 'eis4i',
 'eis4j',
 'eis4k',
 'eis4l',
 'eis4m',
 'eis4n',
 'eis4o',
 'eis4p',
 'eis5a',
 'eis5b',
 'eis5c',
 'eis5d',
 'eis5e',
 'eis5f',
 'eis5g',
 'eis5h',
 'eis5i',
 'eis5j',
 'eis5k',
 'eis5l',
 'eis5m',
 'eis5n',
 'eis5o',
 'eis5p',
 'eis5q',
 'eis5r',
 'eis5s',
 'eis35',
 'eis33',
 'eis34',
 'eis4s',
 'eis4y',
 'eis4z',
 'observedroleeis4g',
 'observedroleeis4h',
 'observedroleeis4i',
 'observedroleeis4j',
 'observedroleeis4k',
 'observedroleeis4l',
 'observedroleeis4m',
 'observedroleeis4n',
 'observedroleeis4o',
 'observedroleeis4p',
 'observedroleeis5a',
 'observedroleeis5b',
 'observedroleeis5c',
 'observedroleeis5d',
 'observedroleeis5e',
 'observedroleeis5f',
 'observedroleeis5g',
 'observedroleeis5h',
 'observedroleeis5i',
 'observedroleeis5j',
 'observedroleeis5k',
 'observedroleeis5l',
 'observedroleeis5m',
 'observedroleeis5n',
 'observedroleeis5o',
 'observedroleeis5p',
 'observedroleeis5q',
 'observedroleeis5r',
 'observedroleeis5s',
 'observedroleeis35',
 'le',
 'lf',
 'setk',
 'seto',
 'sets',
 'seur',
 'seus',
 'seut',
 'seuu',
 'seuv',
 'seuw',
 'sevc',
 'sevf',
 'sevh',
 'eqh',
 'eqs',
 'eqt',
 'equ',
 'eqv',
 'eqw',
 'eqx',
 'eqy',
 'eqz',
 'eq2',
 'eq3',
 'eq4',
 'eq5',
 'eq6',
 'eq7',
 'era',
 'erb',
 'erc',
 'erf',
 'erg',
 'ere',
 'erh',
 'eri',
 'erj',
 'erk',
 'erl',
 'erm',
 'ern',
 'ero',
 'erp',
 'erq',
 'err',
 'ers',
 'ert',
 'eru',
 'erv',
 'erw',
 'erx',
 'ery',
 'erz',
 'er2',
 'er3',
 'er4',
 'er5',
 'er6',
 'er7',
 'esa',
 'esb',
 'esc',
 'esd',
 'ese',
 'esf',
 'esg',
 'esh',
 'esi',
 'esj',
 'esk',
 'esl',
 'esm',
 'esn',
 'eso',
 'esp',
 'esq',
 'esr',
 'ess',
 'est',
 'esu',
 'esv',
 'esw',
 'esx',
 'esy',
 'esz',
 'es2',
 'es3',
 'es4',
 'es5',
 'es6',
 'eta',
 'es7',
 'etd',
 'etg',
 'etj',
 'etb',
 'etc',
 'ete',
 'etf',
 'eth',
 'eti',
 'etk',
 'etl',
 'et7',
 'eua',
 'eub',
 'euc',
 'eud',
 'eue',
 'euf',
 'eug',
 'euh',
 'eui',
 'euj',
 'euk',
 'eul',
 'eum',
 'eun',
 'euo',
 'eup',
 'euq',
 'eur',
 'eus',
 'eut',
 'euu',
 'euv',
 'euw',
 'eux',
 'euy',
 'euz',
 'eu2',
 'eu3',
 'eu6',
 'eu7',
 'eva',
 'evc',
 'evd',
 'eve']
TEXT_SENTENCES={'eis3w': 'Wir wollen nun die aus dem Gleichungssystem (A) resultierenden, dem Experimente zugänglichen '
          'Eigenschaften der Bewegung des Elektrons aufzählen.',
 'eis3y': '1. Aus der zweiten Gleichung des Systems (A) folgt, daß eine elektrische Kraft [M0430] und '
          'eine magnetische Kraft [M0431] dann gleich stark ablenkend wirken auf ein mit der '
          'Geschwindigkeit [M0432] bewegtes Elektron, wenn [M0433].',
 'eis3z': 'Man ersieht also, daß die Ermittelung der Geschwindigkeit des Elektrons aus dem Verhältnis '
          'der magnetischen Ablenkbarkeit [M0434] und der elektrischen Ablenkbarkeit [M0435] nach '
          'unserer Theorie für beliebige Geschwindigkeiten möglich ist durch Anwendung des Gesetzes: '
          '[M0436]',
 'eis4c': 'Diese Beziehung ist der Prüfung durch das Experiment zugänglich, da die Geschwindigkeit des '
          'Elektrons auch direkt, z. B. mittels rasch oszillierender elektrischer und magnetischer '
          'Felder, gemessen werden kann.',
 'tenthobservablespotentialsentence': '2. Aus der Ableitung für die kinetische Energie des Elektrons '
                                      'folgt, daß zwischen der durchlaufenen Potentialdifferenz und der '
                                      'erlangten Geschwindigkeit [M0437] des Elektrons die Beziehung '
                                      'gelten muß: [M0438]',
 'tenthobservablescurvaturecondition': '3. Wir berechnen den Krümmungsradius [M0439] der Bahn, wenn '
                                       'eine senkrecht zur Geschwindigkeit des Elektrons wirkende '
                                       'magnetische Kraft [M0440] (als einzige ablenkende Kraft) '
                                       'vorhanden ist.',
 'tenthobservablescurvaturederivation': 'Aus der zweiten der Gleichungen (A) erhalten wir: [M0441] oder '
                                        '[M0442]',
 'eis6j': 'Diese drei Beziehungen sind ein vollständiger Ausdruck für die Gesetze, nach denen sich '
          'gemäß vorliegender Theorie das Elektron bewegen muß.'}
TOKENS={'eis3w': ['Wir',
           'wollen',
           'nun',
           'die',
           'aus',
           'dem',
           'Gleichungssystem',
           '(A)',
           'resultierenden,',
           'dem',
           'Experimente',
           'zugänglichen',
           'Eigenschaften',
           'der',
           'Bewegung',
           'des',
           'Elektrons',
           'aufzählen.'],
 'eis3y': ['1.',
           'Aus',
           'der',
           'zweiten',
           'Gleichung',
           'des',
           'Systems',
           '(A)',
           'folgt,',
           'daß',
           'eine',
           'elektrische',
           'Kraft',
           '[M0430]',
           'und',
           'eine',
           'magnetische',
           'Kraft',
           '[M0431]',
           'dann',
           'gleich',
           'stark',
           'ablenkend',
           'wirken',
           'auf',
           'ein',
           'mit',
           'der',
           'Geschwindigkeit',
           '[M0432]',
           'bewegtes',
           'Elektron,',
           'wenn',
           '[M0433].'],
 'eis3z': ['Man',
           'ersieht',
           'also,',
           'daß',
           'die',
           'Ermittelung',
           'der',
           'Geschwindigkeit',
           'des',
           'Elektrons',
           'aus',
           'dem',
           'Verhältnis',
           'der',
           'magnetischen',
           'Ablenkbarkeit',
           '[M0434]',
           'und',
           'der',
           'elektrischen',
           'Ablenkbarkeit',
           '[M0435]',
           'nach',
           'unserer',
           'Theorie',
           'für',
           'beliebige',
           'Geschwindigkeiten',
           'möglich',
           'ist',
           'durch',
           'Anwendung',
           'des',
           'Gesetzes:',
           '[M0436]'],
 'eis4c': ['Diese',
           'Beziehung',
           'ist',
           'der',
           'Prüfung',
           'durch',
           'das',
           'Experiment',
           'zugänglich,',
           'da',
           'die',
           'Geschwindigkeit',
           'des',
           'Elektrons',
           'auch',
           'direkt,',
           'z.',
           'B.',
           'mittels',
           'rasch',
           'oszillierender',
           'elektrischer',
           'und',
           'magnetischer',
           'Felder,',
           'gemessen',
           'werden',
           'kann.'],
 'tenthobservablespotentialsentence': ['2.',
                                       'Aus',
                                       'der',
                                       'Ableitung',
                                       'für',
                                       'die',
                                       'kinetische',
                                       'Energie',
                                       'des',
                                       'Elektrons',
                                       'folgt,',
                                       'daß',
                                       'zwischen',
                                       'der',
                                       'durchlaufenen',
                                       'Potentialdifferenz',
                                       'und',
                                       'der',
                                       'erlangten',
                                       'Geschwindigkeit',
                                       '[M0437]',
                                       'des',
                                       'Elektrons',
                                       'die',
                                       'Beziehung',
                                       'gelten',
                                       'muß:',
                                       '[M0438]'],
 'tenthobservablescurvaturecondition': ['3.',
                                        'Wir',
                                        'berechnen',
                                        'den',
                                        'Krümmungsradius',
                                        '[M0439]',
                                        'der',
                                        'Bahn,',
                                        'wenn',
                                        'eine',
                                        'senkrecht',
                                        'zur',
                                        'Geschwindigkeit',
                                        'des',
                                        'Elektrons',
                                        'wirkende',
                                        'magnetische',
                                        'Kraft',
                                        '[M0440]',
                                        '(als',
                                        'einzige',
                                        'ablenkende',
                                        'Kraft)',
                                        'vorhanden',
                                        'ist.'],
 'tenthobservablescurvaturederivation': ['Aus',
                                         'der',
                                         'zweiten',
                                         'der',
                                         'Gleichungen',
                                         '(A)',
                                         'erhalten',
                                         'wir:',
                                         '[M0441]',
                                         'oder',
                                         '[M0442]'],
 'eis6j': ['Diese',
           'drei',
           'Beziehungen',
           'sind',
           'ein',
           'vollständiger',
           'Ausdruck',
           'für',
           'die',
           'Gesetze,',
           'nach',
           'denen',
           'sich',
           'gemäß',
           'vorliegender',
           'Theorie',
           'das',
           'Elektron',
           'bewegen',
           'muß.']}
TOKEN_COUNTS={'eis3w': 18,
 'eis3y': 34,
 'eis3z': 35,
 'eis4c': 28,
 'tenthobservablespotentialsentence': 28,
 'tenthobservablescurvaturecondition': 25,
 'tenthobservablescurvaturederivation': 11,
 'eis6j': 20}
SOURCE_UNITS={'einstein-1905:u0265': {'text': 'Wir wollen nun die aus dem Gleichungssystem (A) resultierenden, dem '
                                 'Experimente zugänglichen Eigenschaften der Bewegung des Elektrons '
                                 'aufzählen.',
                         'sha256': 'aebed0515c149dd80f8d7806a3bfba2cea2a8e3f289717dec035a13b1a577cca'},
 'einstein-1905:u0266': {'text': '1. Aus der zweiten Gleichung des Systems (A) folgt, daß eine '
                                 'elektrische Kraft [M0430] und eine magnetische Kraft [M0431] dann '
                                 'gleich stark ablenkend wirken auf ein mit der Geschwindigkeit [M0432] '
                                 'bewegtes Elektron, wenn [M0433]. Man ersieht also, daß die '
                                 'Ermittelung der Geschwindigkeit des Elektrons aus dem Verhältnis der '
                                 'magnetischen Ablenkbarkeit [M0434] und der elektrischen Ablenkbarkeit '
                                 '[M0435] nach unserer Theorie für beliebige Geschwindigkeiten möglich '
                                 'ist durch Anwendung des Gesetzes:',
                         'sha256': 'f412331c589805926726124c5193ea7aeb9f254b29e82b1340ebda0e3a4c0da4'},
 'einstein-1905:u0267': {'text': '[M0436]',
                         'sha256': '146c9cf8107cae9d5898245f70521f04dadd1f42dd29bfd75c72ae07403a5ffc'},
 'einstein-1905:u0268': {'text': 'Diese Beziehung ist der Prüfung durch das Experiment zugänglich, da '
                                 'die Geschwindigkeit des Elektrons auch direkt, z. B. mittels rasch '
                                 'oszillierender elektrischer und magnetischer Felder, gemessen werden '
                                 'kann.',
                         'sha256': '08a7b120ddb391f192ba55c208e8bd2494ef4edb876411d577faafc6898a27c9'},
 'einstein-1905:u0269': {'text': '2. Aus der Ableitung für die kinetische Energie des Elektrons folgt, '
                                 'daß zwischen der durchlaufenen Potentialdifferenz und der erlangten '
                                 'Geschwindigkeit [M0437] des Elektrons die Beziehung gelten muß:',
                         'sha256': '5a4dc69f8bc2ae76adcecf046152a076c967866e61c33c0c62735b8f32d8ed45'},
 'einstein-1905:u0270': {'text': '[M0438]',
                         'sha256': '3693faa806a64e30de4abf614c4d5b54dab8500dc41962d3ed33d13250c2f5cc'},
 'einstein-1905:u0271': {'text': '3. Wir berechnen den Krümmungsradius [M0439] der Bahn, wenn eine '
                                 'senkrecht zur Geschwindigkeit des Elektrons wirkende magnetische '
                                 'Kraft [M0440] (als einzige ablenkende Kraft) vorhanden ist. Aus der '
                                 'zweiten der Gleichungen (A) erhalten wir:',
                         'sha256': 'abd4c1d2c9eaa74f0d94e647b6d8b8df3c1f2133f7407d2fb18c0b464eb83108'},
 'einstein-1905:u0272': {'text': '[M0441]',
                         'sha256': '665f1fcf088f2e9d77d841939ea0aadd403a52d12ac14bf19a81483073beb996'},
 'einstein-1905:u0273': {'text': 'oder',
                         'sha256': 'b81d9593a3f6c4f7d125fd1da37c9b1fb180574cfb728f3db3c70eda3053e079'},
 'einstein-1905:u0274': {'text': '[M0442]',
                         'sha256': '8928a6969bc38493f13ee2283578edbf2941ef421b9a2e763458494d89239493'},
 'einstein-1905:u0275': {'text': 'Diese drei Beziehungen sind ein vollständiger Ausdruck für die '
                                 'Gesetze, nach denen sich gemäß vorliegender Theorie das Elektron '
                                 'bewegen muß.',
                         'sha256': 'dea9b7855d01d49354d3010cf2f5bf66e2318f6fc5241278977e0f200cddcfc4'}}
BOUNDARY_RULE=('Paragraphs 115..120 follow inspected pages 920..921. List numbers and z. B. are not sentence breaks. '
 'The second sentence of item 3 continues through both displays and oder.')
REVIEWS=('data/einstein-experimental-list-opening-review-v1.json',
 'data/einstein-deflection-speed-determination-u0266-review-v1.json',
 'data/einstein-deflection-speed-determination-u0267-review-v1.json',
 'data/einstein-direct-speed-experiment-u0268-review-v1.json',
 'data/einstein-traversed-potential-u0269-review-v1.json',
 'data/einstein-traversed-potential-u0270-review-v1.json',
 'data/einstein-local-magnetic-radius-u0271-review-v1.json',
 'data/einstein-local-magnetic-radius-u0272-review-v1.json',
 'data/einstein-local-magnetic-radius-u0273-review-v1.json',
 'data/einstein-local-magnetic-radius-u0274-review-v1.json',
 'data/einstein-complete-motion-expression-review-v1.json')
REVIEW_SELECTION=[{'unit': 'einstein-1905:u0265',
  'review': 'data/einstein-experimental-list-opening-review-v1.json',
  'statements': [280]},
 {'unit': 'einstein-1905:u0266',
  'review': 'data/einstein-deflection-speed-determination-u0266-review-v1.json',
  'statements': [268]},
 {'unit': 'einstein-1905:u0267',
  'review': 'data/einstein-deflection-speed-determination-u0267-review-v1.json',
  'statements': [269]},
 {'unit': 'einstein-1905:u0268',
  'review': 'data/einstein-direct-speed-experiment-u0268-review-v1.json',
  'statements': [270]},
 {'unit': 'einstein-1905:u0269',
  'review': 'data/einstein-traversed-potential-u0269-review-v1.json',
  'statements': [271]},
 {'unit': 'einstein-1905:u0270',
  'review': 'data/einstein-traversed-potential-u0270-review-v1.json',
  'statements': [272]},
 {'unit': 'einstein-1905:u0271',
  'review': 'data/einstein-local-magnetic-radius-u0271-review-v1.json',
  'statements': [273]},
 {'unit': 'einstein-1905:u0272',
  'review': 'data/einstein-local-magnetic-radius-u0272-review-v1.json',
  'statements': [274]},
 {'unit': 'einstein-1905:u0273',
  'review': 'data/einstein-local-magnetic-radius-u0273-review-v1.json',
  'statements': [275]},
 {'unit': 'einstein-1905:u0274',
  'review': 'data/einstein-local-magnetic-radius-u0274-review-v1.json',
  'statements': [276]},
 {'unit': 'einstein-1905:u0275',
  'review': 'data/einstein-complete-motion-expression-review-v1.json',
  'statements': [281]}]
READINGS=('data/closing-acknowledgment-basis-v1.json',
 'data/complete-motion-expression-basis-v1.json',
 'data/deflection-speed-determination-basis-v1.json',
 'data/direct-speed-experiment-basis-v1.json',
 'data/einstein-author-credit-basis-v1.json',
 'data/electron-deflection-response-basis-v1.json',
 'data/experimental-list-opening-basis-v1.json',
 'data/experimental-relation-tests-basis-v1.json',
 'data/local-magnetic-radius-basis-v1.json',
 'data/traversed-potential-basis-v1.json')
DIAGNOSTIC_VALIDATORS=['scripts/audit_opening_scope.py',
 'scripts/check_aberration_line.py',
 'scripts/check_angle_composition.py',
 'scripts/check_arbitrary_small_charge.py',
 'scripts/check_attached_material_charge.py',
 'scripts/check_body_rest_field_method.py',
 'scripts/check_calendar_dateline.py',
 'scripts/check_clock_site_time.py',
 'scripts/check_closing_acknowledgment.py',
 'scripts/check_comoving_labels.py',
 'scripts/check_complete_motion_expression.py',
 'scripts/check_conductor_cases.py',
 'scripts/check_convective_foundation_reading.py',
 'scripts/check_coordinate_correspondence.py',
 'scripts/check_coordinate_measurement.py',
 'scripts/check_dated_reading.py',
 'scripts/check_deflection_ratio.py',
 'scripts/check_deflection_speed_determination.py',
 'scripts/check_described_appraisals.py',
 'scripts/check_direct_speed_experiment.py',
 'scripts/check_distant_direction_geometry.py',
 'scripts/check_electric_action.py',
 'scripts/check_electron_alternative_conventions.py',
 'scripts/check_electron_axis_motion.py',
 'scripts/check_electron_comoving_equations_v2.py',
 'scripts/check_electron_convention_caution.py',
 'scripts/check_electron_coordinate_claim.py',
 'scripts/check_electron_coordinate_normalization.py',
 'scripts/check_electron_deflection_response.py',
 'scripts/check_electron_directional_masses.py',
 'scripts/check_electron_energy_balance.py',
 'scripts/check_electron_force_measurement.py',
 'scripts/check_electron_kinetic_work.py',
 'scripts/check_electron_mass_rewrite.py',
 'scripts/check_electron_power_law.py',
 'scripts/check_electron_transformed_dynamics.py',
 'scripts/check_energy_boundary.py',
 'scripts/check_experimental_list_opening.py',
 'scripts/check_experimental_relation_tests.py',
 'scripts/check_integral_substitution.py',
 'scripts/check_intellectual_credit.py',
 'scripts/check_kinetic_energy_chain.py',
 'scripts/check_kinetic_energy_consequences.py',
 'scripts/check_local_magnetic_radius.py',
 'scripts/check_magnetic_action.py',
 'scripts/check_magnetic_curvature.py',
 'scripts/check_mass_coefficients.py',
 'scripts/check_material_acceleration.py',
 'scripts/check_material_energy_extension.py',
 'scripts/check_material_mass_claim.py',
 'scripts/check_material_relative_frame.py',
 'scripts/check_material_shape_dimensions.py',
 'scripts/check_moving_trip_geometry.py',
 'scripts/check_ninth_section_opening.py',
 'scripts/check_phi_normalization.py',
 'scripts/check_plane_waveforms.py',
 'scripts/check_point_particle_dynamics.py',
 'scripts/check_potential_speed.py',
 'scripts/check_problem_series_reduction.py',
 'scripts/check_quantities.py',
 'scripts/check_radiative_intensity.py',
 'scripts/check_real_products.py',
 'scripts/check_resting_charge_force.py',
 'scripts/check_rod_methods.py',
 'scripts/check_rod_setup.py',
 'scripts/check_speed_boundary_forecast.py',
 'scripts/check_sustained_assistance.py',
 'scripts/check_tau_differential.py',
 'scripts/check_translated_light_trial.py',
 'scripts/check_transverse_segment.py',
 'scripts/check_transverse_time.py',
 'scripts/check_traversed_potential.py',
 'scripts/check_unreceived_reference.py',
 'scripts/check_wave_cycle_frequency.py',
 'scripts/check_wave_inquiry.py',
 'scripts/check_wave_transform_application.py',
 'scripts/compose_amplitude_specialization.py',
 'scripts/compose_arbitrary_small_charge.py',
 'scripts/compose_axis_projection.py',
 'scripts/compose_calendar_dateline.py',
 'scripts/compose_closing_acknowledgment.py',
 'scripts/compose_complete_motion_expression.py',
 'scripts/compose_convention_comparison.py',
 'scripts/compose_coordinate_measurement.py',
 'scripts/compose_dated_reading.py',
 'scripts/compose_deflection_ratio.py',
 'scripts/compose_deflection_speed_determination.py',
 'scripts/compose_direct_speed_experiment.py',
 'scripts/compose_doppler_infinity.py',
 'scripts/compose_electric_action.py',
 'scripts/compose_electromotive_wording.py',
 'scripts/compose_electron_alternative_conventions.py',
 'scripts/compose_electron_axis_motion.py',
 'scripts/compose_electron_comoving_equations.py',
 'scripts/compose_electron_comoving_equations_v2.py',
 'scripts/compose_electron_convention_caution.py',
 'scripts/compose_electron_deflection_response.py',
 'scripts/compose_electron_directional_masses.py',
 'scripts/compose_electron_energy_balance.py',
 'scripts/compose_electron_force_measurement.py',
 'scripts/compose_electron_kinetic_work.py',
 'scripts/compose_electron_mass_rewrite.py',
 'scripts/compose_electron_power_law.py',
 'scripts/compose_electron_rest_law_claim.py',
 'scripts/compose_electron_transformed_dynamics.py',
 'scripts/compose_energy_boundary.py',
 'scripts/compose_ether_dispensability.py',
 'scripts/compose_experimental_list_opening.py',
 'scripts/compose_experimental_relation_tests.py',
 'scripts/compose_field_equations.py',
 'scripts/compose_force_mass_units.py',
 'scripts/compose_intellectual_credit.py',
 'scripts/compose_kinetic_energy_chain.py',
 'scripts/compose_kinetic_energy_consequences.py',
 'scripts/compose_limits.py',
 'scripts/compose_local_magnetic_radius.py',
 'scripts/compose_magnetic_action.py',
 'scripts/compose_magnetic_curvature.py',
 'scripts/compose_mass_coefficients.py',
 'scripts/compose_material_acceleration.py',
 'scripts/compose_material_energy_extension.py',
 'scripts/compose_material_mass_claim.py',
 'scripts/compose_material_relative_frame.py',
 'scripts/compose_material_shape_dimensions.py',
 'scripts/compose_material_velocity.py',
 'scripts/compose_origin_clock.py',
 'scripts/compose_parameterized_goals.py',
 'scripts/compose_personal_criteria.py',
 'scripts/compose_planar_shape_limit.py',
 'scripts/compose_point_particle_dynamics.py',
 'scripts/compose_potential_speed.py',
 'scripts/compose_radiative_intensity.py',
 'scripts/compose_relativity_conjecture.py',
 'scripts/compose_rest_force.py',
 'scripts/compose_rod_methods.py',
 'scripts/compose_shape_contraction.py',
 'scripts/compose_situated_criticism.py',
 'scripts/compose_solid_sphere_geometry.py',
 'scripts/compose_speed_boundary_forecast.py',
 'scripts/compose_subject_bound_departure.py',
 'scripts/compose_sustained_assistance.py',
 'scripts/compose_traversed_potential.py',
 'scripts/compose_two_postulates.py',
 'scripts/compose_unreceived_reference.py',
 'scripts/compose_vacuum_field_domain.py',
 'scripts/compose_wave_cycle_frequency.py',
 'scripts/compose_wave_transform_application.py',
 'scripts/review_complete_motion_expression.py',
 'scripts/review_deflection_speed_determination.py',
 'scripts/review_direct_speed_experiment.py',
 'scripts/review_experimental_list_opening.py',
 'scripts/review_local_magnetic_radius.py',
 'scripts/review_traversed_potential.py']
SEMANTIC_REVIEW=['Preserve the three numbered relations, their scope, derivations and the author-attributed '
 'completeness claim.',
 'Calibration, performed acquisition, calculation and record availability remain distinct from '
 'experimental possibility.',
 'Independent direct speed measurement must not assume the deflection ratio being tested.',
 'Retain the signed traversed potential, the same electrostatic work process and the full printed '
 'equality chain.',
 'Potential interval bounds are not initial and final potential values; no speed formula is used to '
 'identify the potential.',
 'The magnetic local event and trajectory are distinct from the preceding electrostatic acceleration.',
 'Retain sole normal deflection, actual local geometric curvature, signed charge/field and both printed '
 'radius expressions.',
 'Background-compatible candidate motions may violate the tested law; do not choose only confirming '
 'candidates.',
 'Closed projections neither prove existence/uniqueness nor provide a common witness; the joint source '
 'bodies remain required.']
OUT=ROOT/'output/einstein-tenth-observables-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=[*profile.LIMITS,*SEMANTIC_REVIEW]

_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=TenthObservablesVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return TenthObservablesVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==608,'Tenth-observables source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','give','fruit','fruit','fruit',temporal.PARTS[i//256],temporal.PARTS[(i//16)%16],temporal.PARTS[i%16])),vocabulary())
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
    def add(old,body,result='individual'):doc['declarations'].append(definition(n[old],[],result,body))
    for old,ordinal in HEADINGS.items():add(old,call(voc._symbols['headingreference'],k('ri'),author.num(ordinal)))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(first,start,last,end) in SPANS.items():add(old,call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(first),author.num(start),k(last),author.num(end),k('ri')))
    for old,(first,last) in MULTI_SPANS.items():add(old,call(voc._symbols['sentencespanreference'],k('eirf'),k(first),k(last),k('ri')))
    for old,(node,index) in DESIGNATIONS.items():add(old,call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri')))
    doc['declarations']+=voc.imports(set(profile.CONTRACTS))
    doc['declarations']+=role_definitions()+forwarder_definitions()
    for old in ROLE_ASSIGNMENTS:
        add(old,call(voc._symbols[reference_kind(old)],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')),REFERENCE_SORTS[old])
    inherited={d['name']:d for d in doc['declarations']}
    for d in renamed([d for d in source_excerpt()['declarations'] if d['name'] in REUSED_DEFINITIONS],m):
        require(inherited.get(d['name'])==d,'Inherited mathematical definition differs: '+d['name'])
    doc['declarations']+=new_definitions()
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-observables reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-observables reference')
    return REFERENCE_KINDS[old]


def role_definitions():
    role_mapping=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|mapping()
    planned=build_roles(catalogs()['einstein-1905'].document)
    require({old:d['name'] for old,d in planned.items()}==ROLE_ASSIGNMENTS,'Role assignment changed')
    return renamed(list(planned.values()),role_mapping)


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
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*FORWARD_MAPS}
    ancestor=previous
    while ancestor is not None:
        forwarded.update(getattr(ancestor,'FORWARD_MAPS',{}));ancestor=getattr(ancestor,'previous',None)
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][343:354],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    units={r['id']:r for r in inventory['units']}
    for name,row in SOURCE_UNITS.items():
        require(units[name]['text']==row['text'] and units[name]['text_sha256']==row['sha256'],'Source text boundary changed')
    require(previous.SENTENCES['eis3p']==[114,1],'Previous paragraph boundary changed')
    order={n:i for i,n in enumerate(SENTENCES)}
    for n,text in TEXT_SENTENCES.items():
        require(text.split()==TOKENS[n] and len(TOKENS[n])==TOKEN_COUNTS[n],'Token count changed')
    for n,(first,start,last,end) in SPANS.items():
        require(1<=start<=TOKEN_COUNTS[first] and 1<=end<=TOKEN_COUNTS[last],'Span outside sentence')
        require(order[first]<order[last] or first==last and start<=end,'Reversed span')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Original facsimile changed')
    return dict(rule=BOUNDARY_RULE,sentences=TEXT_SENTENCES,coordinates=SENTENCES,tokens=TOKENS,
        spans=SPANS,designations=DESIGNATIONS,designation_forms=FORMS,source_units=SOURCE_UNITS)



def annotations():
    import xml.etree.ElementTree as ET
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations'])
    rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    require(set(rows)=={'eis33','eis34'},'Retained designation inventory changed')
    for old,row in rows.items():require(any(f['text']==FORMS[old] for f in row['forms']),'Retained printed form changed')
    anchor=author.read('data/tenth-observables-text-anchors-v1.json')
    require(anchor['forms']==FORMS and anchor['designations']==DESIGNATIONS,'Reviewed designation changed')
    require(anchor['new_visible_designation_forms']=={'eis4s':'P','eis4y':'R','eis4z':'N'},'New designation inventory changed')
    inventory={r['id']:r for r in author.read('artifacts/written-units-v1/einstein-1905.json')['math']}
    formulas={'eis4s':'M0438','eis4y':'M0439','eis4z':'M0440'};paths=set(data.show()['source_sha256'])
    expected={'eis4s':'M0438で同じ通過電位差を呼ぶ記号P。','eis4y':'第三項で同じ局所曲率半径を呼ぶ記号R。','eis4z':'第三項で同じ磁場z成分を呼ぶ記号N。'}
    additions={}
    for old,mid in formulas.items():
        identifiers=[n.text for n in ET.fromstring(inventory[mid]['mathml']).iter() if n.tag.rsplit('}',1)[-1]=='mi']
        require(identifiers[0]==FORMS[old] and (old=='eis4s' or len(identifiers)==1),'Original designation changed')
        entry=catalogs()['einstein-1905'].entries[old]
        require(entry['meaning_ja']==expected[old],'Source designation meaning changed')
        paths.update((entry['meaning_basis'],entry['declaration_document']))
        additions[old]=dict(symbol=old,role='designation',forms=[dict(text=FORMS[old],language='de',role='printed_identifying_form')])
    paths.update(('artifacts/written-units-v1/einstein-1905.json','data/tenth-observables-text-anchors-v1.json'))
    return dict(entries=rows,new_visible_entries=additions,source_formulas=formulas,
        source_identifier_annotations_modified=False,source_sha256={p:author.digest(p) for p in sorted(paths)})


def bridge():
    c=catalogs()['einstein-1905']
    require(c.document_path=='examples/v014/einstein-auxiliary-reference-order-v1.noema','Active source changed')
    units={r['id']:r for r in author.read('artifacts/written-units-v1/einstein-1905.json')['units']}
    state=author.read('data/work-state.json');index=author.read(state['review_index'])
    registered={r['review']:r for r in index['works']['einstein-1905']['reviews']}
    for row in REVIEW_SELECTION:
        review=author.read(row['review']);unit=units[row['unit']]
        require(review['unit']==row['unit'] and review['decision']=='equivalent_under_stated_reading' and not review['unresolved'],'Source review incomplete')
        require(review['source']['text']==unit['text'] and review['source']['unit_sha256']==unit['text_sha256'],'Source evidence differs')
        require(registered[row['review']]['statements']==row['statements'],'Registered review selection changed')
    require(SOURCE_ORDER==[280,*range(268,277),281],'Selection changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    contracts=profile.CONTRACTS
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=contracts[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-tenth-observables-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=SOURCE_UNITS,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        reused_typed_bodies=REUSED_BODIES,new_public_relations=13,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=84,core_edition=12,new_source_assertions=11,
        total_source_assertions=265,total_annotations=94,source_reviews=REVIEW_SELECTION,parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,
        document_integration_credit=0,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible tenth-observables document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[first],start,values[last],end,values['ri']):values[n] for n,(first,start,last,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    from scripts.field_symmetry_visible_profile import IndividualCutFunctionReferences
    from scripts.affine_time_visible_profile import TypedFunctionReferences as AffineReferences
    from scripts.tenth_motion_visible_profile import TypedFunctionReferences as MotionReferences
    from scripts.four_coordinate_visible_profile import IndividualFourCutFamilyReferences
    from scripts.vacuum_assumption_visible_profile import FourCutTruthFunctionReferences
    require(kind in REFERENCE_KINDS.values(),'Unknown observables reference kind')
    rows={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old]
          for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(rows,{})
    if kind=='describedrationalreference':return __import__('scripts.energy_reference_visible_profile',fromlist=['RationalReferences']).RationalReferences(rows)
    if kind=='describedcutreference':return CutReferences(rows)
    if kind=='describedindividualcutfunctionreference':return IndividualCutFunctionReferences(rows)
    if kind=='describedcutfunctionreference':return AffineReferences(kind,rows)
    if kind=='describedindividualfourcutfunctionfamilyreference':return IndividualFourCutFamilyReferences(rows)
    if kind=='describedfourcuttruthfunctionreference':return FourCutTruthFunctionReferences(rows)
    return MotionReferences(kind,rows)


def designation_model(values):
    # Earlier fixture layers sometimes replaced the entire designation handler.
    # Recover retained lookups represented by this finite fixture from the
    # actual linked Native definitions. Earlier paragraphs outside BASE keep
    # their own diagnostic models; this is not a model of every individual.
    inverse={value:key for key,value in names().items()}
    getter=vocabulary()._symbols['designationreference'];rows={}
    for declaration in document()['declarations']:
        body=declaration.get('body',{})
        if declaration.get('parameters') or body.get('kind')!='call' or body['symbol']!=getter:continue
        old=inverse[declaration['name']]
        if old not in values:continue
        args=body['arguments'];require(len(args)==4,'Unexpected designation lookup arity')
        require(all(args[i].get('kind')=='call' and not args[i]['arguments'] for i in (0,1,3)),'Designation anchor is not a closed reference')
        require(args[2].get('kind')=='number' and args[2]['denominator']==1,'Designation ordinal changed')
        key=(values[inverse[args[0]['symbol']]],values[inverse[args[1]['symbol']]],args[2]['numerator'],values[inverse[args[3]['symbol']]])
        value=values[old]
        require(key not in rows or rows[key]==value,'Conflicting retained designation lookup')
        rows[key]=value
    require(rows,'No Native designation references')
    return DesignationReferences(rows)


@_with_authoring_session
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
        key=(document,first,start,last,end,context)
        own={(values['eirf'],values[first],a,values[last],b,values['ri']) for first,a,last,b in SPANS.values()}
        if key in own:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    def passage(document,first,last,context):
        if first in {values[n] for n in TEXT_SENTENCES} or last in {values[n] for n in TEXT_SENTENCES}:
            return MovingTextReferences({(values['eirf'],values[a],values[b],values['ri']):values[n] for n,(a,b) in MULTI_SPANS.items()},{}).span(document,first,last,context)
        return result['sentencespanreference'](document,first,last,context)
    designations=designation_model(values)
    def designation(document,node,index,context):
        return designations.reference(document,node,index,context)
    def typed(kind):
        nodes={values[reference_anchor(old)] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
        def lookup(document,node,role,context):
            if node in nodes:return reference_model(values,kind).described(document,node,role,context)
            require(kind in result,'Unknown typed reference')
            return result[kind](document,node,role,context)
        return lookup
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in tuple(sorted(set(REFERENCE_KINDS.values())))}



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    from scripts.visible_pin_snapshot import digest_snapshot
    with digest_snapshot(author,root=ROOT):
        return _source_pins(include_outputs=include_outputs)


def _source_pins(*,include_outputs=True):
    from noema.semantic_reviews import validate_hashes
    pins=previous.source_pins();state=author.read('data/work-state.json')
    active=author.read(state['review_index'])['works']['einstein-1905']
    require(active['document']=='examples/v014/einstein-auxiliary-reference-order-v1.noema','Unplanned active manuscript')
    paths={*pins,'data/work-state.json',state['review_index'],active['identifier_annotations'],SOURCE,BRIDGE,
        profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,*DIAGNOSTIC_VALIDATORS,
        'scripts/tenth_observables_visible_profile.py','scripts/tenth_observables_visible_profile_contracts.py',
        'scripts/tenth_observables_reference_roles.py','scripts/check_einstein_tenth_observables_visible.py',
        'scripts/visible_tenth_observables_visible_collection.py','tests/test_tenth_observables_visible.py',
        'tests/test_tenth_observables_reference_roles.py','data/tenth-observables-text-anchors-v1.json',
        'docs/einstein-tenth-observables-visible-v1.md'}
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved observables bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-tenth-observables-visible-evidence-1',core_words=375,profile_words=1061,profile_edition=84,
        new_public_relations=13,new_reference_primitives=0,new_source_assertions=11,total_source_assertions=265,annotations=94,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)


def new_definitions():
    ds={d['name']:d for d in catalogs()['einstein-1905'].document['declarations']}
    result=[]
    for name in NEW_DEFINITIONS:
        d=deepcopy(ds[name])
        if name in REUSED_BODIES:
            reused=deepcopy(ds[REUSED_BODIES[name]]);reused['name']=name
            require(reused==d,'Retained typed body no longer matches')
            d=reused
        result.append(d)
    return renamed(result,mapping())
