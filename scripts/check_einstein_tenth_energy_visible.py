"""Connect the complete kinetic-work argument, consequences and material extension."""
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
from scripts import energy_reference_visible_profile as profile
from scripts.energy_reference_visible_profile import ROOT,EnergyReferenceVisibleVocabulary,write_once
from scripts import tenth_energy_visible_profile as energy_profile
from scripts import check_einstein_tenth_mass_visible as previous
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

from scripts.tenth_energy_reference_roles import build_roles
SOURCE='examples/v016/einstein-tenth-energy-visible-v1.noema'
BRIDGE='data/einstein-tenth-energy-visible-bridge-v1.json'
SOURCE_ORDER=[264, 265, 266, 267]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-p919-0.jpg',
  'sha256': '0a369b2d6811268e33eabccac3242232301632d20a13d87711cd0137cc891389',
  'actually_displayed': True,
  'display_method': 'functions.exec tools.view_image forwarded with image()',
  'independent_human_reading': False},
 {'path': 'artifacts/written-facsimiles-v1/einstein-p920-0.jpg',
  'sha256': '75fa5ab4f9e6a4d3bbd0004ef82257c531ab5b60bdc141c8edc006e208f3bd2c',
  'actually_displayed': True,
  'display_method': 'functions.exec tools.view_image forwarded with image()',
  'independent_human_reading': False}]
PUBLIC_RELATIONS={'eiszt': 'translationalkineticenergy',
 'eiszu': 'fieldenergywithdrawal',
 'eiszv': 'outgoingradiatedenergy',
 'eiszw': 'mechanicalworkunit',
 'eiszy': 'undertakesquantitydetermination',
 'eiszz': 'electricfieldmodelcorrespondence',
 'eis3l': 'presentsanalogousresults',
 'zrgclosed': 'closedenergyexchange'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['serc',
 'serd',
 'sere',
 'serf',
 'serg',
 'serl',
 'serm',
 'sern',
 'sero',
 'seru',
 'serv',
 'serw',
 'sesb',
 'sese',
 'sesf',
 'setf',
 'eor',
 'eos',
 'eot',
 'eou',
 'eov',
 'eow',
 'eox',
 'eoy',
 'eoz',
 'eo2',
 'eo3',
 'eo4',
 'eo5',
 'eo6',
 'epo',
 'eo7',
 'epp',
 'epa',
 'epb',
 'epc',
 'epd',
 'epe',
 'epf',
 'epg',
 'eph',
 'epi',
 'epj',
 'epk',
 'epl',
 'epm',
 'epn',
 'epq',
 'epr',
 'eps',
 'ept',
 'epu',
 'epv',
 'epw',
 'epx',
 'epy',
 'epz',
 'ep2',
 'ep3',
 'ep4',
 'ep5',
 'ep6',
 'ep7',
 'eqg',
 'eqa',
 'eqb',
 'eqc',
 'eqd',
 'eqe',
 'eqf']
REUSED_BODIES={}
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'eis3a': [112, 1],
 'eis3b': [112, 2],
 'tenthenergybalancesentence': [112, 3],
 'tenthenergyderivationsentence': [112, 4],
 'eis3m': [113, 1],
 'eis3n': [113, 2],
 'eis3p': [114, 1]}
SPANS={'eis3c': ['tenthenergybalancesentence', 1, 'tenthenergybalancesentence', 17],
 'eis3d': ['tenthenergybalancesentence', 18, 'tenthenergybalancesentence', 33],
 'eis3e': ['tenthenergyderivationsentence', 4, 'tenthenergyderivationsentence', 18],
 'eis3f': ['eis3b', 39, 'eis3b', 39],
 'eis3g': ['tenthenergybalancesentence', 28, 'tenthenergybalancesentence', 29],
 'eis3h': ['tenthenergyderivationsentence', 19, 'tenthenergyderivationsentence', 19],
 'eis3i': ['tenthenergybalancesentence', 9, 'tenthenergybalancesentence', 17],
 'eis3o': ['eis3n', 4, 'eis3n', 8],
 'eis3q': ['eis3p', 9, 'eis3p', 13],
 'tenthenergywtoken': ['tenthenergybalancesentence', 29, 'tenthenergybalancesentence', 29]}
MULTI_SPANS={}
DESIGNATIONS={'eis3j': ['tenthenergywtoken', 1]}
FORMS={'eis3j': 'W'}
ROLE_ASSIGNMENTS={'eis2a': 'energyroleeis2a',
 'eis2b': 'energyroleeis2b',
 'eis2c': 'energyroleeis2c',
 'eis2d': 'energyroleeis2d',
 'eis2e': 'energyroleeis2e',
 'eis2f': 'energyroleeis2f',
 'eis2g': 'energyroleeis2g',
 'eis2h': 'energyroleeis2h',
 'eis2i': 'energyroleeis2i',
 'eis2j': 'energyroleeis2j',
 'eis2k': 'energyroleeis2k',
 'eis2l': 'energyroleeis2l',
 'eis2m': 'energyroleeis2m',
 'eis2n': 'energyroleeis2n',
 'eis2o': 'energyroleeis2o',
 'zrgcharge': 'energyrolezrgcharge',
 'zrgfield': 'energyrolezrgfield',
 'zrgposition': 'energyrolezrgposition',
 'zrgprofile': 'energyrolezrgprofile',
 'zrgstart': 'energyrolezrgstart',
 'zrgunit': 'energyrolezrgunit',
 'zrhcurve': 'energyrolezrhcurve',
 'zrhdomain': 'energyrolezrhdomain',
 'zrhendpoint': 'energyrolezrhendpoint',
 'zrhstartpoint': 'energyrolezrhstartpoint',
 'zriacceleration': 'energyrolezriacceleration',
 'zrivelocity': 'energyrolezrivelocity',
 'zrgepisode': 'energyrolezrgepisode',
 'zrfenergy': 'energyrolezrfenergy',
 'zrginitial': 'energyrolezrginitial',
 'zrgradiated': 'energyrolezrgradiated',
 'zrgwithdrawn': 'energyrolezrgwithdrawn',
 'eis3k': 'energyroleeis3k'}
REFERENCE_ANCHORS={'eis2a': 'eis3b',
 'eis2b': 'eis3b',
 'eis2c': 'eis3b',
 'eis2d': 'eis3b',
 'eis2e': 'eis3b',
 'eis2f': 'eis3b',
 'eis2g': 'eis3b',
 'eis2h': 'eis3b',
 'eis2i': 'eis3b',
 'eis2j': 'eis3b',
 'eis2k': 'eis3b',
 'eis2l': 'eis3b',
 'eis2m': 'eis3b',
 'eis2n': 'eis3b',
 'eis2o': 'eis3c',
 'zrgcharge': 'eis3b',
 'zrgfield': 'eis3b',
 'zrgposition': 'eis3b',
 'zrgprofile': 'eis3b',
 'zrgstart': 'eis3b',
 'zrgunit': 'eis3b',
 'zrhcurve': 'eis3b',
 'zrhdomain': 'eis3b',
 'zrhendpoint': 'eis3b',
 'zrhstartpoint': 'eis3b',
 'zriacceleration': 'eis3c',
 'zrivelocity': 'eis3b',
 'zrgepisode': 'eis3b',
 'zrfenergy': 'eis3g',
 'zrginitial': 'eis3b',
 'zrgradiated': 'eis3i',
 'zrgwithdrawn': 'eis3d',
 'eis3k': 'eis3n'}
REFERENCE_SORTS={'eis2a': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis2b': 'individual',
 'eis2c': 'individual',
 'eis2d': 'individual',
 'eis2e': 'individual',
 'eis2f': 'individual',
 'eis2g': 'number',
 'eis2h': 'number',
 'eis2i': 'number',
 'eis2j': 'number',
 'eis2k': 'number',
 'eis2l': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function',
                      'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                      'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'eis2m': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function',
                      'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                     {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                      'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'eis2n': {'kind': 'function',
           'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                          {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                          {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                          {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
           'result': 'truth'},
 'eis2o': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zrgcharge': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zrgfield': 'individual',
 'zrgposition': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zrgprofile': {'kind': 'function',
                'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zrgstart': 'individual',
 'zrgunit': 'individual',
 'zrhcurve': {'kind': 'function',
              'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
              'result': {'kind': 'function',
                         'parameters': ['individual'],
                         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'zrhdomain': {'kind': 'function',
               'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
               'result': 'truth'},
 'zrhendpoint': {'kind': 'function',
                 'parameters': ['individual'],
                 'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zrhstartpoint': {'kind': 'function',
                   'parameters': ['individual'],
                   'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zriacceleration': {'kind': 'function',
                     'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                     'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zrivelocity': {'kind': 'function',
                 'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                 'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zrgepisode': 'individual',
 'zrfenergy': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zrginitial': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zrgradiated': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zrgwithdrawn': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'eis3k': 'individual'}
REFERENCE_KINDS={'eis2a': 'describedcutreference',
 'eis2b': 'describedreference',
 'eis2c': 'describedreference',
 'eis2d': 'describedreference',
 'eis2e': 'describedreference',
 'eis2f': 'describedreference',
 'eis2g': 'describedrationalreference',
 'eis2h': 'describedrationalreference',
 'eis2i': 'describedrationalreference',
 'eis2j': 'describedrationalreference',
 'eis2k': 'describedrationalreference',
 'eis2l': 'describedindividualfourcutfunctionfamilyreference',
 'eis2m': 'describedindividualfourcutfunctionfamilyreference',
 'eis2n': 'describedfourcuttruthfunctionreference',
 'eis2o': 'describedcutreference',
 'zrgcharge': 'describedcutreference',
 'zrgfield': 'describedreference',
 'zrgposition': 'describedcutreference',
 'zrgprofile': 'describedcutfunctionreference',
 'zrgstart': 'describedreference',
 'zrgunit': 'describedreference',
 'zrhcurve': 'describedcutindividualcutfunctionfamilyreference',
 'zrhdomain': 'describedcuttruthfunctionreference',
 'zrhendpoint': 'describedindividualcutfunctionreference',
 'zrhstartpoint': 'describedindividualcutfunctionreference',
 'zriacceleration': 'describedcutfunctionreference',
 'zrivelocity': 'describedcutfunctionreference',
 'zrgepisode': 'describedreference',
 'zrfenergy': 'describedcutreference',
 'zrginitial': 'describedcutreference',
 'zrgradiated': 'describedcutreference',
 'zrgwithdrawn': 'describedcutreference',
 'eis3k': 'describedreference'}
LOCAL_NAMES=['eis3a',
 'eis3b',
 'tenthenergybalancesentence',
 'tenthenergyderivationsentence',
 'eis3m',
 'eis3n',
 'eis3p',
 'eis3c',
 'eis3d',
 'eis3e',
 'eis3f',
 'eis3g',
 'eis3h',
 'eis3i',
 'eis3o',
 'eis3q',
 'tenthenergywtoken',
 'eis2a',
 'eis2b',
 'eis2c',
 'eis2d',
 'eis2e',
 'eis2f',
 'eis2g',
 'eis2h',
 'eis2i',
 'eis2j',
 'eis2k',
 'eis2l',
 'eis2m',
 'eis2n',
 'eis2o',
 'zrgcharge',
 'zrgfield',
 'zrgposition',
 'zrgprofile',
 'zrgstart',
 'zrgunit',
 'zrhcurve',
 'zrhdomain',
 'zrhendpoint',
 'zrhstartpoint',
 'zriacceleration',
 'zrivelocity',
 'zrgepisode',
 'zrfenergy',
 'zrginitial',
 'zrgradiated',
 'zrgwithdrawn',
 'eis3k',
 'eis3j',
 'energyroleeis2a',
 'energyroleeis2b',
 'energyroleeis2c',
 'energyroleeis2d',
 'energyroleeis2e',
 'energyroleeis2f',
 'energyroleeis2g',
 'energyroleeis2h',
 'energyroleeis2i',
 'energyroleeis2j',
 'energyroleeis2k',
 'energyroleeis2l',
 'energyroleeis2m',
 'energyroleeis2n',
 'energyroleeis2o',
 'energyrolezrgcharge',
 'energyrolezrgfield',
 'energyrolezrgposition',
 'energyrolezrgprofile',
 'energyrolezrgstart',
 'energyrolezrgunit',
 'energyrolezrhcurve',
 'energyrolezrhdomain',
 'energyrolezrhendpoint',
 'energyrolezrhstartpoint',
 'energyrolezriacceleration',
 'energyrolezrivelocity',
 'energyrolezrgepisode',
 'energyrolezrfenergy',
 'energyrolezrginitial',
 'energyrolezrgradiated',
 'energyrolezrgwithdrawn',
 'energyroleeis3k',
 'serc',
 'serd',
 'sere',
 'serf',
 'serg',
 'serl',
 'serm',
 'sern',
 'sero',
 'seru',
 'serv',
 'serw',
 'sesb',
 'sese',
 'sesf',
 'setf',
 'eor',
 'eos',
 'eot',
 'eou',
 'eov',
 'eow',
 'eox',
 'eoy',
 'eoz',
 'eo2',
 'eo3',
 'eo4',
 'eo5',
 'eo6',
 'epo',
 'eo7',
 'epp',
 'epa',
 'epb',
 'epc',
 'epd',
 'epe',
 'epf',
 'epg',
 'eph',
 'epi',
 'epj',
 'epk',
 'epl',
 'epm',
 'epn',
 'epq',
 'epr',
 'eps',
 'ept',
 'epu',
 'epv',
 'epw',
 'epx',
 'epy',
 'epz',
 'ep2',
 'ep3',
 'ep4',
 'ep5',
 'ep6',
 'ep7',
 'eqg',
 'eqa',
 'eqb',
 'eqc',
 'eqd',
 'eqe',
 'eqf']
TEXT_SENTENCES={'eis3a': 'Wir bestimmen die kinetische Energie des Elektrons.',
 'eis3b': 'Bewegt sich ein Elektron vom Koordinatenursprung des Systems [M0422] aus mit der '
          'Anfangsgeschwindigkeit 0 beständig auf der [M0423]-Achse unter der Wirkung einer '
          'elektrostatischen Kraft [M0424] , so ist klar, daß die dem elektrostatischen Felde entzogene '
          'Energie den Wert [M0425] hat.',
 'tenthenergybalancesentence': 'Da das Elektron langsam beschleunigt sein soll und infolgedessen keine '
                               'Energie in Form von Strahlung abgeben möge, so muß die dem elektrostatischen '
                               'Felde entzogene Energie gleich der Bewegungsenergie [M0426] des Elektrons '
                               'gesetzt werden.',
 'tenthenergyderivationsentence': 'Man erhält daher, indem man beachtet, daß während des ganzen betrachteten '
                                  'Bewegungsvorganges die erste der Gleichungen (A) gilt: [M0427]',
 'eis3m': '[M0428] wird also für [M0429] unendlich groß.',
 'eis3n': 'Überlichtgeschwindigkeiten haben — wie bei unseren früheren Resultaten — keine '
          'Existenzmöglichkeit.',
 'eis3p': 'Auch dieser Ausdruck für die kinetische Energie muß dem oben angeführten Argument zufolge ebenso '
          'für ponderable Massen gelten.'}
TOKENS={'eis3a': ['Wir', 'bestimmen', 'die', 'kinetische', 'Energie', 'des', 'Elektrons.'],
 'eis3b': ['Bewegt',
           'sich',
           'ein',
           'Elektron',
           'vom',
           'Koordinatenursprung',
           'des',
           'Systems',
           '[M0422]',
           'aus',
           'mit',
           'der',
           'Anfangsgeschwindigkeit',
           '0',
           'beständig',
           'auf',
           'der',
           '[M0423]-Achse',
           'unter',
           'der',
           'Wirkung',
           'einer',
           'elektrostatischen',
           'Kraft',
           '[M0424]',
           ',',
           'so',
           'ist',
           'klar,',
           'daß',
           'die',
           'dem',
           'elektrostatischen',
           'Felde',
           'entzogene',
           'Energie',
           'den',
           'Wert',
           '[M0425]',
           'hat.'],
 'tenthenergybalancesentence': ['Da',
                                'das',
                                'Elektron',
                                'langsam',
                                'beschleunigt',
                                'sein',
                                'soll',
                                'und',
                                'infolgedessen',
                                'keine',
                                'Energie',
                                'in',
                                'Form',
                                'von',
                                'Strahlung',
                                'abgeben',
                                'möge,',
                                'so',
                                'muß',
                                'die',
                                'dem',
                                'elektrostatischen',
                                'Felde',
                                'entzogene',
                                'Energie',
                                'gleich',
                                'der',
                                'Bewegungsenergie',
                                '[M0426]',
                                'des',
                                'Elektrons',
                                'gesetzt',
                                'werden.'],
 'tenthenergyderivationsentence': ['Man',
                                   'erhält',
                                   'daher,',
                                   'indem',
                                   'man',
                                   'beachtet,',
                                   'daß',
                                   'während',
                                   'des',
                                   'ganzen',
                                   'betrachteten',
                                   'Bewegungsvorganges',
                                   'die',
                                   'erste',
                                   'der',
                                   'Gleichungen',
                                   '(A)',
                                   'gilt:',
                                   '[M0427]'],
 'eis3m': ['[M0428]', 'wird', 'also', 'für', '[M0429]', 'unendlich', 'groß.'],
 'eis3n': ['Überlichtgeschwindigkeiten',
           'haben',
           '—',
           'wie',
           'bei',
           'unseren',
           'früheren',
           'Resultaten',
           '—',
           'keine',
           'Existenzmöglichkeit.'],
 'eis3p': ['Auch',
           'dieser',
           'Ausdruck',
           'für',
           'die',
           'kinetische',
           'Energie',
           'muß',
           'dem',
           'oben',
           'angeführten',
           'Argument',
           'zufolge',
           'ebenso',
           'für',
           'ponderable',
           'Massen',
           'gelten.']}
TOKEN_COUNTS={'eis3a': 7,
 'eis3b': 40,
 'tenthenergybalancesentence': 33,
 'tenthenergyderivationsentence': 19,
 'eis3m': 7,
 'eis3n': 11,
 'eis3p': 18}
SOURCE_UNITS={'einstein-1905:u0261': {'text': 'Wir bestimmen die kinetische Energie des Elektrons. Bewegt sich ein '
                                 'Elektron vom Koordinatenursprung des Systems [M0422] aus mit der '
                                 'Anfangsgeschwindigkeit 0 beständig auf der [M0423]-Achse unter der Wirkung '
                                 'einer elektrostatischen Kraft [M0424] , so ist klar, daß die dem '
                                 'elektrostatischen Felde entzogene Energie den Wert [M0425] hat. Da das '
                                 'Elektron langsam beschleunigt sein soll und infolgedessen keine Energie in '
                                 'Form von Strahlung abgeben möge, so muß die dem elektrostatischen Felde '
                                 'entzogene Energie gleich der Bewegungsenergie [M0426] des Elektrons '
                                 'gesetzt werden. Man erhält daher, indem man beachtet, daß während des '
                                 'ganzen betrachteten Bewegungsvorganges die erste der Gleichungen (A) gilt:',
                         'sha256': '717987abceb9d328b08cc733c0d1149933de5dbbf133f63e28c4c0dd3b183fd9'},
 'einstein-1905:u0262': {'text': '[M0427]',
                         'sha256': '165161dcff73a63fffa72ca5f07470f33e7fa46833fd9860ac61571e4faf9124'},
 'einstein-1905:u0263': {'text': '[M0428] wird also für [M0429] unendlich groß. Überlichtgeschwindigkeiten '
                                 'haben — wie bei unseren früheren Resultaten — keine Existenzmöglichkeit.',
                         'sha256': '0628e25115e8b72d5a34aad7bf68d2b7dd80122962cf5912fbde92dedb8f0374'},
 'einstein-1905:u0264': {'text': 'Auch dieser Ausdruck für die kinetische Energie muß dem oben angeführten '
                                 'Argument zufolge ebenso für ponderable Massen gelten.',
                         'sha256': '699eba806d32c852413bb191946a2decc2d86ef393a28787e225a1659d6bfa13'}}
BOUNDARY_RULE=('Paragraphs 112..114 follow the inspected indentation on pages 919..920. The displayed chain completes '
 'paragraph 112 sentence 4; its final period is inside MathML.')
REVIEWS=('data/einstein-electron-kinetic-work-u0261-review-v1.json',
 'data/einstein-electron-kinetic-work-u0262-review-v1.json',
 'data/einstein-kinetic-energy-consequences-u0263-review-v1.json',
 'data/einstein-kinetic-energy-consequences-u0264-review-v1.json')
REVIEW_SELECTION=[{'unit': 'einstein-1905:u0261',
  'review': 'data/einstein-electron-kinetic-work-u0261-review-v1.json',
  'statements': [264]},
 {'unit': 'einstein-1905:u0262',
  'review': 'data/einstein-electron-kinetic-work-u0262-review-v1.json',
  'statements': [265]},
 {'unit': 'einstein-1905:u0263',
  'review': 'data/einstein-kinetic-energy-consequences-u0263-review-v1.json',
  'statements': [266]},
 {'unit': 'einstein-1905:u0264',
  'review': 'data/einstein-kinetic-energy-consequences-u0264-review-v1.json',
  'statements': [267]}]
READINGS=('data/einstein-author-credit-basis-v1.json',
 'data/electron-kinetic-work-basis-v1.json',
 'data/kinetic-energy-consequences-basis-v1.json')
DIAGNOSTIC_VALIDATORS=['scripts/audit_opening_scope.py',
 'scripts/check_aberration_line.py',
 'scripts/check_angle_composition.py',
 'scripts/check_arbitrary_small_charge.py',
 'scripts/check_attached_material_charge.py',
 'scripts/check_body_rest_field_method.py',
 'scripts/check_clock_site_time.py',
 'scripts/check_comoving_labels.py',
 'scripts/check_convective_foundation_reading.py',
 'scripts/check_coordinate_correspondence.py',
 'scripts/check_described_appraisals.py',
 'scripts/check_distant_direction_geometry.py',
 'scripts/check_electric_action.py',
 'scripts/check_electron_alternative_conventions.py',
 'scripts/check_electron_axis_motion.py',
 'scripts/check_electron_comoving_equations_v2.py',
 'scripts/check_electron_convention_caution.py',
 'scripts/check_electron_coordinate_claim.py',
 'scripts/check_electron_coordinate_normalization.py',
 'scripts/check_electron_directional_masses.py',
 'scripts/check_electron_energy_balance.py',
 'scripts/check_electron_force_measurement.py',
 'scripts/check_electron_kinetic_work.py',
 'scripts/check_electron_mass_rewrite.py',
 'scripts/check_electron_power_law.py',
 'scripts/check_electron_transformed_dynamics.py',
 'scripts/check_energy_boundary.py',
 'scripts/check_kinetic_energy_chain.py',
 'scripts/check_kinetic_energy_consequences.py',
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
 'scripts/check_problem_series_reduction.py',
 'scripts/check_quantities.py',
 'scripts/check_radiative_intensity.py',
 'scripts/check_real_products.py',
 'scripts/check_rod_methods.py',
 'scripts/check_rod_setup.py',
 'scripts/check_speed_boundary_forecast.py',
 'scripts/check_tau_differential.py',
 'scripts/check_translated_light_trial.py',
 'scripts/check_transverse_segment.py',
 'scripts/check_transverse_time.py',
 'scripts/check_wave_cycle_frequency.py',
 'scripts/check_wave_inquiry.py',
 'scripts/compose_amplitude_specialization.py',
 'scripts/compose_arbitrary_small_charge.py',
 'scripts/compose_convention_comparison.py',
 'scripts/compose_doppler_infinity.py',
 'scripts/compose_electric_action.py',
 'scripts/compose_electron_alternative_conventions.py',
 'scripts/compose_electron_axis_motion.py',
 'scripts/compose_electron_comoving_equations.py',
 'scripts/compose_electron_comoving_equations_v2.py',
 'scripts/compose_electron_convention_caution.py',
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
 'scripts/compose_field_equations.py',
 'scripts/compose_force_mass_units.py',
 'scripts/compose_kinetic_energy_chain.py',
 'scripts/compose_kinetic_energy_consequences.py',
 'scripts/compose_limits.py',
 'scripts/compose_mass_coefficients.py',
 'scripts/compose_material_acceleration.py',
 'scripts/compose_material_energy_extension.py',
 'scripts/compose_material_mass_claim.py',
 'scripts/compose_material_relative_frame.py',
 'scripts/compose_material_shape_dimensions.py',
 'scripts/compose_material_velocity.py',
 'scripts/compose_origin_clock.py',
 'scripts/compose_planar_shape_limit.py',
 'scripts/compose_point_particle_dynamics.py',
 'scripts/compose_radiative_intensity.py',
 'scripts/compose_relativity_conjecture.py',
 'scripts/compose_rest_force.py',
 'scripts/compose_rod_methods.py',
 'scripts/compose_shape_contraction.py',
 'scripts/compose_situated_criticism.py',
 'scripts/compose_solid_sphere_geometry.py',
 'scripts/compose_speed_boundary_forecast.py',
 'scripts/compose_two_postulates.py',
 'scripts/compose_vacuum_field_domain.py',
 'scripts/review_electron_kinetic_work.py',
 'scripts/review_kinetic_energy_consequences.py']
SEMANTIC_REVIEW=['Preserve the same electron, electrostatic work, units, motion history and contextual slow-acceleration '
 'setting.',
 'The printed middle integral lacks the mass factor. Keep serg; do not substitute serh or assume unit mass.',
 'No radiation and the simplified closed balance are assumptions in the attributed argument, not derived '
 'universal physical laws.',
 'The divergence is a lower-side limit; it is not an infinite real value at the endpoint.',
 'Superluminal exclusion retains the theory scope and the analogy with earlier results.',
 'The material-mass extension retains the earlier small-charge argument without claiming an actual '
 'experiment.',
 'Closed candidate references do not establish existence, uniqueness or shared witnesses; the source joint '
 'bodies remain required.']
OUT=ROOT/'output/einstein-tenth-energy-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|energy_profile.SOURCE_RELATIONS|profile.SOURCE_RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=[*energy_profile.LIMITS,*profile.LIMITS,*SEMANTIC_REVIEW]

_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=EnergyReferenceVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return EnergyReferenceVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==632,'Tenth-energy source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','give','fruit','fruit',temporal.PARTS[i//256],temporal.PARTS[(i//16)%16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.CONTRACTS)|set(energy_profile.CONTRACTS))
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
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-energy reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-energy reference')
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
    result['statements']=renamed(doc['statements'][338:342],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    units={r['id']:r for r in inventory['units']}
    for name,row in SOURCE_UNITS.items():
        require(units[name]['text']==row['text'] and units[name]['text_sha256']==row['sha256'],'Source text boundary changed')
    require(previous.SENTENCES['tenthmaterialextensionsentence']==[111,1],'Previous paragraph boundary changed')
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
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    # The retained identifier file has no W annotation. Record this visible
    # addition separately instead of pretending to inherit or rewriting it.
    require(rows=={} and FORMS=={'eis3j':'W'},'Retained designation inventory changed')
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    formula=next(row for row in inventory['math'] if row['id']=='M0426')
    require(formula['sha256']=='5bb4fd482e166aaea1f54bff925bbdf460e4d3be73153b97985735a11bf3d824','W source formula changed')
    identifiers=[node.text for node in ET.fromstring(formula['mathml']).iter() if node.tag.rsplit('}',1)[-1]=='mi']
    require(identifiers==['W'],'Source designation is not W')
    entry=catalogs()['einstein-1905'].entries['eis3j']
    require(entry['meaning_ja']=='M0426–M0427で運動エネルギーを呼ぶ記号W。','Source designation meaning changed')
    anchor=author.read('data/tenth-energy-text-anchors-v1.json')
    require(anchor['forms']==FORMS and anchor['designations']==DESIGNATIONS,'Reviewed visible designation changed')
    additions={'eis3j':dict(symbol='eis3j',role='designation',forms=[dict(text='W',language='de',role='printed_identifying_form')])}
    paths={*data.show()['source_sha256'],'artifacts/written-units-v1/einstein-1905.json',
        'data/tenth-energy-text-anchors-v1.json',entry['meaning_basis'],entry['declaration_document']}
    return dict(entries=rows,new_visible_entries=additions,source_formula='M0426',
        source_identifier_annotations_modified=False,
        review='The original symbol meaning and printed MathML identify W; this visible form annotation does not identify the physical energy value with its name.',
        source_sha256={p:author.digest(p) for p in sorted(paths)})


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
    require(SOURCE_ORDER==[264,265,266,267],'Selection changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    contracts=energy_profile.CONTRACTS|profile.CONTRACTS
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=contracts[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-tenth-energy-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=SOURCE_UNITS,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        reused_typed_bodies=REUSED_BODIES,new_public_relations=8,new_reference_primitives=1,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=83,core_edition=12,new_source_assertions=4,
        total_source_assertions=254,total_annotations=89,source_reviews=REVIEW_SELECTION,parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,
        document_integration_credit=0,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible tenth-energy document differs');return result


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
    require(kind in REFERENCE_KINDS.values(),'Unknown energy reference kind')
    rows={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old]
          for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(rows,{})
    if kind=='describedrationalreference':return profile.RationalReferences(rows)
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
    profile.prepare();energy_profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
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
    pins=previous.source_pins()
    state=author.read('data/work-state.json');active=author.read(state['review_index'])['works']['einstein-1905']
    require(active['document']=='examples/v014/einstein-auxiliary-reference-order-v1.noema','Unplanned active manuscript')
    paths={*pins,'data/work-state.json',state['review_index'],active['identifier_annotations'],SOURCE,BRIDGE,
        profile.LIBRARY,profile.BASIS,profile.MANIFEST,energy_profile.LIBRARY,energy_profile.BASIS,energy_profile.MANIFEST,
        *READINGS,*REVIEWS,*DIAGNOSTIC_VALIDATORS,
        'scripts/tenth_energy_visible_profile.py','scripts/tenth_energy_visible_profile_contracts.py',
        'scripts/energy_reference_visible_profile.py','scripts/energy_reference_visible_profile_contracts.py',
        'scripts/tenth_energy_reference_roles.py','scripts/check_einstein_tenth_energy_visible.py',
        'scripts/visible_tenth_energy_visible_collection.py','tests/test_tenth_energy_visible.py',
        'tests/test_tenth_energy_reference_roles.py','data/tenth-energy-text-anchors-v1.json',
        'docs/einstein-tenth-energy-visible-v1.md',
        'data/tenth-energy-visible-diagnostic-controls-v2.json','tests/test_tenth_energy_auxiliary_physics_visible.py','tests/test_tenth_energy_diagnostic_adapter.py','tests/test_tenth_energy_physics_visible.py'}
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved tenth-energy bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-tenth-energy-visible-evidence-1',core_words=375,profile_words=1048,profile_edition=83,
        new_public_relations=8,new_reference_primitives=1,new_source_assertions=4,total_source_assertions=254,annotations=89,
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
