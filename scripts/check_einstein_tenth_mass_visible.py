"""Connect mass conventions, theory comparison and material-point extension."""
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
from scripts import tenth_mass_visible_profile as profile
from scripts.activity_role_visible_profile import ROOT,ActivityRoleVisibleVocabulary,write_once
from scripts import activity_role_visible_profile as activity_profile
from scripts import check_einstein_tenth_motion_visible as previous
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

SOURCE='examples/v016/einstein-tenth-mass-visible-v1.noema'
BRIDGE='data/einstein-tenth-mass-visible-bridge-v1.json'
SOURCE_ORDER=[259, 258, 260, 261, 262, 263]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-p918-0.jpg',
  'sha256': '771893807eb2f8f56df6af5c66099a6f06faa47211af0ee6e5d1b25d3d590eab',
  'actually_displayed': True,
  'display_method': 'functions.exec tools.view_image forwarded with image()',
  'independent_human_reading': False,
  'observations': ['The mass inquiry begins a new indented paragraph after equations (A); its first sentence '
                   'continues onto page 919.']},
 {'path': 'artifacts/written-facsimiles-v1/einstein-p919-0.jpg',
  'sha256': '0a369b2d6811268e33eabccac3242232301632d20a13d87711cd0137cc891389',
  'actually_displayed': True,
  'display_method': 'functions.exec tools.view_image forwarded with image()',
  'independent_human_reading': False,
  'observations': ['Wir schreiben continues the same paragraph; the three rewritten rows and und bemerken '
                   'belong to its second sentence.',
                   'The parenthetical spring-balance example is a separate sentence in the same paragraph.',
                   'Wenn wir nun starts its fourth sentence, including the product convention and both '
                   'displayed mass results. The transverse display ends with a period.',
                   'Natürlich begins the next indented paragraph; the semicolon separates clauses, not '
                   'sentences.',
                   'Wir bemerken begins the following indented paragraph; denn follows a semicolon. The '
                   'parenthetical in unserem Sinne lies inside that reason clause.',
                   'Wir bestimmen die kinetische Energie begins a new paragraph beyond this selection.']}]
PUBLIC_RELATIONS={'zraconvention': 'forceaccelerationconvention',
 'zrcmust': 'comparisonprocedurerequirement',
 'zrcactor': 'comparisonactor',
 'zrcleft': 'comparisonlefttheory',
 'zrcright': 'comparisonrighttheory',
 'zrctopic': 'comparisonfield',
 'zrccases': 'comparisoncases',
 'zrcconcludes': 'comparisonmismatchconclusion',
 'zrcinterpretations': 'comparisoninterpretations',
 'zrcmeanings': 'comparisonmeaningcorrespondence',
 'zrcunits': 'comparisonunitnormalization',
 'zrccorresponds': 'comparisonphysicalcorrespondence',
 'zrcleftvalue': 'comparisonleftvalue',
 'zrcrightvalue': 'comparisonrightvalue',
 'zrdcharge': 'assignedchargevalue',
 'zrdamount': 'addedchargeamount',
 'zrdadded': 'chargeadditionoperation',
 'eisyr': 'reversibleelasticresponse',
 'eisys': 'calibratedelasticinstrument',
 'eisyt': 'directedloadcomparison',
 'eisyu': 'conditionalcutpairinquiry',
 'eisyv': 'conventionalinquiryframing',
 'eisyw': 'adoptunqualifieddesignation',
 'eisyx': 'directionalcoefficientdesignation',
 'eiszc': 'operationalquantityredefinition',
 'eiszd': 'distinctoperationalquantitydefinition',
 'eisze': 'conventioncomparisonalternative',
 'eiszf': 'theorylawmembership',
 'eiszg': 'theorycomparisonactivity',
 'eiszh': 'relevantcomparisonaspect',
 'eiszi': 'attentiveexamination',
 'eiszj': 'markedlyabovestandard',
 'eiszn': 'ponderablepointidealization',
 'eiszo': 'mechanicalforceattribution',
 'eiszp': 'priorsenselimiteddesignation'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['cj',
 'sepe',
 'sepf',
 'sepg',
 'seph',
 'sepi',
 'seqk',
 'seql',
 'seqm',
 'seqr',
 'seqs',
 'seqt',
 'elq',
 'elr',
 'els',
 'elu',
 'elv',
 'elw',
 'elx',
 'ely',
 'elz',
 'el2',
 'el3',
 'el4',
 'el5',
 'el6',
 'el7',
 'ema',
 'emb',
 'emc',
 'emd',
 'emf',
 'eme',
 'emh',
 'emi',
 'emj',
 'emk',
 'eml',
 'emm',
 'emn',
 'emo',
 'emp',
 'emq',
 'emr',
 'ems',
 'emt',
 'emu',
 'emv',
 'emw',
 'emx',
 'emy',
 'emz',
 'em2',
 'em3',
 'em4',
 'em5',
 'enb',
 'enc',
 'em6',
 'em7',
 'ena',
 'enn',
 'enp',
 'enq',
 'enr',
 'ens',
 'ent',
 'enu',
 'env',
 'enw',
 'en2',
 'en3',
 'en4',
 'en5',
 'en6',
 'en7',
 'eoa',
 'eob',
 'eoc',
 'eod',
 'eoe',
 'eof',
 'eog',
 'eoh',
 'eoi',
 'eoj',
 'eok',
 'eol',
 'eom',
 'eon',
 'eoo',
 'eop',
 'eoq']
REUSED_BODIES={}
FORWARD_MAPS={'zza': 'rationalbelow', 'zzd': 'rationalmultiply'}
HEADINGS={}
SENTENCES={'eisyy': [109, 1],
 'tenthrewritesentence': [109, 2],
 'eisy2': [109, 3],
 'eisy3': [109, 4],
 'tenthcomparisonsentence': [110, 1],
 'tenthmaterialextensionsentence': [111, 1]}
SPANS={'eisyp': ['tenthrewritesentence', 1, 'tenthrewritesentence', 8],
 'eisyq': ['tenthrewritesentence', 9, 'tenthrewritesentence', 9],
 'eisyz': ['tenthrewritesentence', 10, 'tenthrewritesentence', 42],
 'eisy4': ['eisy3', 17, 'eisy3', 21],
 'eisy5': ['eisy3', 44, 'eisy3', 46],
 'eisy6': ['eisy3', 47, 'eisy3', 49],
 'eiszl': ['tenthcomparisonsentence', 1, 'tenthcomparisonsentence', 17],
 'eiszm': ['tenthcomparisonsentence', 18, 'tenthcomparisonsentence', 35],
 'eiszq': ['tenthmaterialextensionsentence', 1, 'tenthmaterialextensionsentence', 15],
 'eiszr': ['tenthmaterialextensionsentence', 16, 'tenthmaterialextensionsentence', 36],
 'eiszs': ['tenthmaterialextensionsentence', 32, 'tenthmaterialextensionsentence', 34],
 'tenthunqualifiedforcephrase': ['eisy3', 7, 'eisy3', 12]}
MULTI_SPANS={}
DESIGNATIONS={'eisy7': ['tenthunqualifiedforcephrase', 1], 'eisza': ['eisy5', 1], 'eiszb': ['eisy6', 1]}
FORMS={'eisy7': 'die auf das Elektron wirkende Kraft',
 'eisza': 'Longitudinale Masse',
 'eiszb': 'Transversale Masse'}
ROLE_ASSIGNMENTS={'zrcsubject': 'massmotionsubjectrole', 'zrcrole': 'masscomparerrole', 'eiszk': 'massordinarystandardrole'}
ROLE_DEFINITIONS={'massmotionaccount': {'kind': 'definition',
                       'name': 'massmotionaccount',
                       'parameters': [],
                       'result': 'content',
                       'body': {'kind': 'content',
                                'variable': 'world',
                                'body': {'kind': 'exists',
                                         'variable': 'law',
                                         'sort': 'individual',
                                         'body': {'kind': 'and',
                                                  'arguments': [{'kind': 'call',
                                                                 'symbol': 'vd',
                                                                 'arguments': [{'kind': 'variable',
                                                                                'name': 'law'},
                                                                               {'kind': 'variable',
                                                                                'name': 'world'}]},
                                                                {'kind': 'call',
                                                                 'symbol': 'eisxn',
                                                                 'arguments': [{'kind': 'variable',
                                                                                'name': 'law'},
                                                                               {'kind': 'call',
                                                                                'symbol': 'eisxh',
                                                                                'arguments': []},
                                                                               {'kind': 'call',
                                                                                'symbol': 'ra',
                                                                                'arguments': []},
                                                                               {'kind': 'variable',
                                                                                'name': 'world'}]}]}}}},
 'masscomparisonparticipant': {'kind': 'definition',
                               'name': 'masscomparisonparticipant',
                               'parameters': [{'name': 'person', 'sort': 'individual'},
                                              {'name': 'activity', 'sort': 'individual'},
                                              {'name': 'world', 'sort': 'situation'}],
                               'result': 'truth',
                               'body': {'kind': 'exists',
                                        'variable': 'left',
                                        'sort': 'individual',
                                        'body': {'kind': 'exists',
                                                 'variable': 'right',
                                                 'sort': 'individual',
                                                 'body': {'kind': 'call',
                                                          'symbol': 'en3',
                                                          'arguments': [{'kind': 'variable',
                                                                         'name': 'person'},
                                                                        {'kind': 'variable',
                                                                         'name': 'activity'},
                                                                        {'kind': 'variable', 'name': 'left'},
                                                                        {'kind': 'variable', 'name': 'right'},
                                                                        {'kind': 'variable',
                                                                         'name': 'world'}]}}}},
 'massmotionsubjectrole': {'kind': 'definition',
                           'name': 'massmotionsubjectrole',
                           'parameters': [{'name': 'candidate', 'sort': 'individual'},
                                          {'name': 'context', 'sort': 'situation'}],
                           'result': 'truth',
                           'body': {'kind': 'call',
                                    'symbol': 'theoreticalinquirytopic',
                                    'arguments': [{'kind': 'variable', 'name': 'candidate'},
                                                  {'kind': 'quote',
                                                   'body': {'kind': 'call',
                                                            'symbol': 'ek36',
                                                            'arguments': []}},
                                                  {'kind': 'quote',
                                                   'body': {'kind': 'call',
                                                            'symbol': 'massmotionaccount',
                                                            'arguments': []}},
                                                  {'kind': 'variable', 'name': 'context'}]}},
 'masscomparerrole': {'kind': 'definition',
                      'name': 'masscomparerrole',
                      'parameters': [{'name': 'candidate', 'sort': 'individual'},
                                     {'name': 'context', 'sort': 'situation'}],
                      'result': 'truth',
                      'body': {'kind': 'call',
                               'symbol': 'methodologicalactivityrole',
                               'arguments': [{'kind': 'variable', 'name': 'candidate'},
                                             {'kind': 'quote',
                                              'body': {'kind': 'function_ref',
                                                       'symbol': 'masscomparisonparticipant'}},
                                             {'kind': 'variable', 'name': 'context'}]}},
 'massordinarystandardrole': {'kind': 'definition',
                              'name': 'massordinarystandardrole',
                              'parameters': [{'name': 'candidate', 'sort': 'individual'},
                                             {'name': 'context', 'sort': 'situation'}],
                              'result': 'truth',
                              'body': {'kind': 'call',
                                       'symbol': 'ordinaryprocedurestandard',
                                       'arguments': [{'kind': 'variable', 'name': 'candidate'},
                                                     {'kind': 'quote',
                                                      'body': {'kind': 'function_ref', 'symbol': 'en4'}},
                                                     {'kind': 'variable', 'name': 'context'}]}}}
REFERENCE_ANCHORS={'zrcsubject': 'eiszm', 'zrcrole': 'eiszm', 'eiszk': 'eiszm'}
REFERENCE_SORTS={'zrcsubject': 'individual', 'zrcrole': 'individual', 'eiszk': 'individual'}
REFERENCE_KINDS={'zrcsubject': 'describedreference', 'zrcrole': 'describedreference', 'eiszk': 'describedreference'}
LOCAL_NAMES=['eisyy',
 'tenthrewritesentence',
 'eisy2',
 'eisy3',
 'tenthcomparisonsentence',
 'tenthmaterialextensionsentence',
 'eisyp',
 'eisyq',
 'eisyz',
 'eisy4',
 'eisy5',
 'eisy6',
 'eiszl',
 'eiszm',
 'eiszq',
 'eiszr',
 'eiszs',
 'tenthunqualifiedforcephrase',
 'zrcsubject',
 'zrcrole',
 'eiszk',
 'eisy7',
 'eisza',
 'eiszb',
 'massmotionaccount',
 'masscomparisonparticipant',
 'massmotionsubjectrole',
 'masscomparerrole',
 'massordinarystandardrole',
 'zza',
 'zzd',
 'cj',
 'sepe',
 'sepf',
 'sepg',
 'seph',
 'sepi',
 'seqk',
 'seql',
 'seqm',
 'seqr',
 'seqs',
 'seqt',
 'elq',
 'elr',
 'els',
 'elu',
 'elv',
 'elw',
 'elx',
 'ely',
 'elz',
 'el2',
 'el3',
 'el4',
 'el5',
 'el6',
 'el7',
 'ema',
 'emb',
 'emc',
 'emd',
 'emf',
 'eme',
 'emh',
 'emi',
 'emj',
 'emk',
 'eml',
 'emm',
 'emn',
 'emo',
 'emp',
 'emq',
 'emr',
 'ems',
 'emt',
 'emu',
 'emv',
 'emw',
 'emx',
 'emy',
 'emz',
 'em2',
 'em3',
 'em4',
 'em5',
 'enb',
 'enc',
 'em6',
 'em7',
 'ena',
 'enn',
 'enp',
 'enq',
 'enr',
 'ens',
 'ent',
 'enu',
 'env',
 'enw',
 'en2',
 'en3',
 'en4',
 'en5',
 'en6',
 'en7',
 'eoa',
 'eob',
 'eoc',
 'eod',
 'eoe',
 'eof',
 'eog',
 'eoh',
 'eoi',
 'eoj',
 'eok',
 'eol',
 'eom',
 'eon',
 'eoo',
 'eop',
 'eoq']
TEXT_SENTENCES={'eisyy': 'Wir fragen nun in Anlehnung an die übliche Betrachtungsweise nach der „longitudinalen“ und '
          '„transversalen“ Masse des bewegten Elektrons.',
 'tenthrewritesentence': 'Wir schreiben die Gleichungen (A) in der Form [M0417] und bemerken zunächst, daß '
                         '[M0418] die Komponenten der auf das Elektron wirkenden ponderomotorischen Kraft '
                         'sind, und zwar in einem in diesem Moment mit dem Elektron mit gleicher '
                         'Geschwindigkeit wie dieses bewegten System betrachtet.',
 'eisy2': '(Diese Kraft könnte beispielsweise mit einer im letzten System ruhenden Federwage gemessen '
          'werden.)',
 'eisy3': 'Wenn wir nun diese Kraft schlechtweg „die auf das Elektron wirkende Kraft“ nennen und die '
          'Gleichung Massenzahl × Beschleunigungszahl = Kraftzahl aufrechterhalten, und wenn wir ferner '
          'festsetzen, daß die Beschleunigungen im ruhenden System [M0419] gemessen werden sollen, so '
          'erhalten wir aus obigen Gleichungen: Longitudinale Masse [M0420] Transversale Masse [M0421]',
 'tenthcomparisonsentence': 'Natürlich würde man bei anderer Definition der Kraft und der Beschleunigung '
                            'andere Zahlen für die Massen erhalten; man ersieht daraus, daß man bei der '
                            'Vergleichung verschiedener Theorien der Bewegung des Elektrons sehr vorsichtig '
                            'verfahren muß.',
 'tenthmaterialextensionsentence': 'Wir bemerken, daß diese Resultate über die Masse auch für die '
                                   'ponderabeln materiellen Punkte gilt; denn ein ponderabler materieller '
                                   'Punkt kann durch Zufügen einer beliebig kleinen elektrischen Ladung zu '
                                   'einem Elektron (in unserem Sinne) gemacht werden.'}
TOKENS={'eisyy': ['Wir',
           'fragen',
           'nun',
           'in',
           'Anlehnung',
           'an',
           'die',
           'übliche',
           'Betrachtungsweise',
           'nach',
           'der',
           '„longitudinalen“',
           'und',
           '„transversalen“',
           'Masse',
           'des',
           'bewegten',
           'Elektrons.'],
 'tenthrewritesentence': ['Wir',
                          'schreiben',
                          'die',
                          'Gleichungen',
                          '(A)',
                          'in',
                          'der',
                          'Form',
                          '[M0417]',
                          'und',
                          'bemerken',
                          'zunächst,',
                          'daß',
                          '[M0418]',
                          'die',
                          'Komponenten',
                          'der',
                          'auf',
                          'das',
                          'Elektron',
                          'wirkenden',
                          'ponderomotorischen',
                          'Kraft',
                          'sind,',
                          'und',
                          'zwar',
                          'in',
                          'einem',
                          'in',
                          'diesem',
                          'Moment',
                          'mit',
                          'dem',
                          'Elektron',
                          'mit',
                          'gleicher',
                          'Geschwindigkeit',
                          'wie',
                          'dieses',
                          'bewegten',
                          'System',
                          'betrachtet.'],
 'eisy2': ['(Diese',
           'Kraft',
           'könnte',
           'beispielsweise',
           'mit',
           'einer',
           'im',
           'letzten',
           'System',
           'ruhenden',
           'Federwage',
           'gemessen',
           'werden.)'],
 'eisy3': ['Wenn',
           'wir',
           'nun',
           'diese',
           'Kraft',
           'schlechtweg',
           '„die',
           'auf',
           'das',
           'Elektron',
           'wirkende',
           'Kraft“',
           'nennen',
           'und',
           'die',
           'Gleichung',
           'Massenzahl',
           '×',
           'Beschleunigungszahl',
           '=',
           'Kraftzahl',
           'aufrechterhalten,',
           'und',
           'wenn',
           'wir',
           'ferner',
           'festsetzen,',
           'daß',
           'die',
           'Beschleunigungen',
           'im',
           'ruhenden',
           'System',
           '[M0419]',
           'gemessen',
           'werden',
           'sollen,',
           'so',
           'erhalten',
           'wir',
           'aus',
           'obigen',
           'Gleichungen:',
           'Longitudinale',
           'Masse',
           '[M0420]',
           'Transversale',
           'Masse',
           '[M0421]'],
 'tenthcomparisonsentence': ['Natürlich',
                             'würde',
                             'man',
                             'bei',
                             'anderer',
                             'Definition',
                             'der',
                             'Kraft',
                             'und',
                             'der',
                             'Beschleunigung',
                             'andere',
                             'Zahlen',
                             'für',
                             'die',
                             'Massen',
                             'erhalten;',
                             'man',
                             'ersieht',
                             'daraus,',
                             'daß',
                             'man',
                             'bei',
                             'der',
                             'Vergleichung',
                             'verschiedener',
                             'Theorien',
                             'der',
                             'Bewegung',
                             'des',
                             'Elektrons',
                             'sehr',
                             'vorsichtig',
                             'verfahren',
                             'muß.'],
 'tenthmaterialextensionsentence': ['Wir',
                                    'bemerken,',
                                    'daß',
                                    'diese',
                                    'Resultate',
                                    'über',
                                    'die',
                                    'Masse',
                                    'auch',
                                    'für',
                                    'die',
                                    'ponderabeln',
                                    'materiellen',
                                    'Punkte',
                                    'gilt;',
                                    'denn',
                                    'ein',
                                    'ponderabler',
                                    'materieller',
                                    'Punkt',
                                    'kann',
                                    'durch',
                                    'Zufügen',
                                    'einer',
                                    'beliebig',
                                    'kleinen',
                                    'elektrischen',
                                    'Ladung',
                                    'zu',
                                    'einem',
                                    'Elektron',
                                    '(in',
                                    'unserem',
                                    'Sinne)',
                                    'gemacht',
                                    'werden.']}
TOKEN_COUNTS={'eisyy': 18,
 'tenthrewritesentence': 42,
 'eisy2': 13,
 'eisy3': 49,
 'tenthcomparisonsentence': 35,
 'tenthmaterialextensionsentence': 36}
SOURCE_FRAGMENTS={'eisyy': [[252, 0, 136]],
 'tenthrewritesentence': [[252, 137, 182], [253, 0, 7], [254, 0, 232]],
 'eisy2': [[254, 233, 332]],
 'eisy3': [[254, 333, 432], [255, 0, 44], [256, 0, 165], [257, 0, 27], [258, 0, 26]],
 'tenthcomparisonsentence': [[259, 0, 244]],
 'tenthmaterialextensionsentence': [[260, 0, 252]]}
SOURCE_UNITS={'einstein-1905:u0252': {'text': 'Wir fragen nun in Anlehnung an die übliche Betrachtungsweise nach der '
                                 '„longitudinalen“ und „transversalen“ Masse des bewegten Elektrons. Wir '
                                 'schreiben die Gleichungen (A) in der Form',
                         'sha256': '72bc7e68c8f2093063ae8c4047fb28373f3033ef0fd76437214287c274ab13cc'},
 'einstein-1905:u0253': {'text': '[M0417]',
                         'sha256': '2081447aeb59cd7fd98d3cbaccdfea0b1fee0d005178ee623dafb91c44d2f074'},
 'einstein-1905:u0254': {'text': 'und bemerken zunächst, daß [M0418] die Komponenten der auf das Elektron '
                                 'wirkenden ponderomotorischen Kraft sind, und zwar in einem in diesem '
                                 'Moment mit dem Elektron mit gleicher Geschwindigkeit wie dieses bewegten '
                                 'System betrachtet. (Diese Kraft könnte beispielsweise mit einer im letzten '
                                 'System ruhenden Federwage gemessen werden.) Wenn wir nun diese Kraft '
                                 'schlechtweg „die auf das Elektron wirkende Kraft“ nennen und die Gleichung',
                         'sha256': '66ecd85488cc0cb99b14bb4d423ee6a07e71c4417885590f97863b6be05a7eda'},
 'einstein-1905:u0255': {'text': 'Massenzahl × Beschleunigungszahl = Kraftzahl',
                         'sha256': '3b717b64ea019c26d56486326e3006a8a4a3c738e4ea25dd88b7e862f7ae841d'},
 'einstein-1905:u0256': {'text': 'aufrechterhalten, und wenn wir ferner festsetzen, daß die Beschleunigungen '
                                 'im ruhenden System [M0419] gemessen werden sollen, so erhalten wir aus '
                                 'obigen Gleichungen:',
                         'sha256': '7a7ae33a9e88aaed659b105e1d08d828cefca337252ae14170ebbd34bcd9a9b1'},
 'einstein-1905:u0257': {'text': 'Longitudinale Masse [M0420]',
                         'sha256': '3782431927d17d55240e2f558f60374ae863efe252da28d4b8160a6f189b9fe8'},
 'einstein-1905:u0258': {'text': 'Transversale Masse [M0421]',
                         'sha256': '9f35ab8bcfa48a4585d85e135349d1cdba00cc4f049aff503b47bcfd22bcd067'},
 'einstein-1905:u0259': {'text': 'Natürlich würde man bei anderer Definition der Kraft und der '
                                 'Beschleunigung andere Zahlen für die Massen erhalten; man ersieht daraus, '
                                 'daß man bei der Vergleichung verschiedener Theorien der Bewegung des '
                                 'Elektrons sehr vorsichtig verfahren muß.',
                         'sha256': 'ac2cac0a6f03a365ba3f74c24686426a172c09cfc6884a6afb3456a3751b881f'},
 'einstein-1905:u0260': {'text': 'Wir bemerken, daß diese Resultate über die Masse auch für die ponderabeln '
                                 'materiellen Punkte gilt; denn ein ponderabler materieller Punkt kann durch '
                                 'Zufügen einer beliebig kleinen elektrischen Ladung zu einem Elektron (in '
                                 'unserem Sinne) gemacht werden.',
                         'sha256': 'e8868abb21c01b1a6ff46e271bc65279abb2006b4250f58ed46eac2da380d6c3'}}
BOUNDARY_RULE=('Continue paragraph numbering after parent 108. Paragraphs 109..111 follow original indentation; page '
 'breaks, displayed equations and semicolons do not create paragraphs. Whitespace token anchors retain '
 'mathematical placeholders as single tokens.')
REVIEWS=('data/einstein-electron-directional-masses-u0252-review-v1.json',
 'data/einstein-electron-mass-rewrite-u0253-review-v1.json',
 'data/einstein-electron-directional-masses-u0254-review-v1.json',
 'data/einstein-electron-directional-masses-u0255-review-v1.json',
 'data/einstein-electron-directional-masses-u0256-review-v1.json',
 'data/einstein-electron-directional-masses-u0257-review-v1.json',
 'data/einstein-electron-directional-masses-u0258-review-v1.json',
 'data/einstein-electron-convention-caution-u0259-review-v1.json',
 'data/einstein-material-mass-claim-u0260-review-v1.json')
REVIEW_SELECTION=[{'unit': 'einstein-1905:u0252',
  'review': 'data/einstein-electron-directional-masses-u0252-review-v1.json',
  'statements': [258, 259]},
 {'unit': 'einstein-1905:u0253',
  'review': 'data/einstein-electron-mass-rewrite-u0253-review-v1.json',
  'statements': [258]},
 {'unit': 'einstein-1905:u0254',
  'review': 'data/einstein-electron-directional-masses-u0254-review-v1.json',
  'statements': [260, 261]},
 {'unit': 'einstein-1905:u0255',
  'review': 'data/einstein-electron-directional-masses-u0255-review-v1.json',
  'statements': [261]},
 {'unit': 'einstein-1905:u0256',
  'review': 'data/einstein-electron-directional-masses-u0256-review-v1.json',
  'statements': [261]},
 {'unit': 'einstein-1905:u0257',
  'review': 'data/einstein-electron-directional-masses-u0257-review-v1.json',
  'statements': [261]},
 {'unit': 'einstein-1905:u0258',
  'review': 'data/einstein-electron-directional-masses-u0258-review-v1.json',
  'statements': [261]},
 {'unit': 'einstein-1905:u0259',
  'review': 'data/einstein-electron-convention-caution-u0259-review-v1.json',
  'statements': [262]},
 {'unit': 'einstein-1905:u0260',
  'review': 'data/einstein-material-mass-claim-u0260-review-v1.json',
  'statements': [263]}]
READINGS=('data/einstein-author-credit-basis-v1.json',
 'data/electron-alternative-conventions-basis-v1.json',
 'data/electron-convention-caution-basis-v1.json',
 'data/electron-directional-masses-basis-v1.json',
 'data/electron-force-measurement-basis-v1.json',
 'data/electron-mass-rewrite-basis-v1.json',
 'data/material-mass-claim-basis-v1.json')
DIAGNOSTIC_VALIDATORS=['scripts/audit_opening_scope.py',
 'scripts/check_angle_composition.py',
 'scripts/check_arbitrary_small_charge.py',
 'scripts/check_attached_material_charge.py',
 'scripts/check_clock_site_time.py',
 'scripts/check_comoving_labels.py',
 'scripts/check_coordinate_correspondence.py',
 'scripts/check_described_appraisals.py',
 'scripts/check_electric_action.py',
 'scripts/check_electron_alternative_conventions.py',
 'scripts/check_electron_comoving_equations_v2.py',
 'scripts/check_electron_convention_caution.py',
 'scripts/check_electron_coordinate_claim.py',
 'scripts/check_electron_coordinate_normalization.py',
 'scripts/check_electron_directional_masses.py',
 'scripts/check_electron_force_measurement.py',
 'scripts/check_electron_mass_rewrite.py',
 'scripts/check_electron_transformed_dynamics.py',
 'scripts/check_mass_coefficients.py',
 'scripts/check_material_acceleration.py',
 'scripts/check_material_mass_claim.py',
 'scripts/check_material_relative_frame.py',
 'scripts/check_ninth_section_opening.py',
 'scripts/check_phi_normalization.py',
 'scripts/check_plane_waveforms.py',
 'scripts/check_point_particle_dynamics.py',
 'scripts/check_problem_series_reduction.py',
 'scripts/check_quantities.py',
 'scripts/check_real_products.py',
 'scripts/check_rod_methods.py',
 'scripts/check_rod_setup.py',
 'scripts/check_tau_differential.py',
 'scripts/check_transverse_time.py',
 'scripts/compose_arbitrary_small_charge.py',
 'scripts/compose_convention_comparison.py',
 'scripts/compose_doppler_infinity.py',
 'scripts/compose_electric_action.py',
 'scripts/compose_electron_alternative_conventions.py',
 'scripts/compose_electron_comoving_equations.py',
 'scripts/compose_electron_comoving_equations_v2.py',
 'scripts/compose_electron_convention_caution.py',
 'scripts/compose_electron_directional_masses.py',
 'scripts/compose_electron_force_measurement.py',
 'scripts/compose_electron_mass_rewrite.py',
 'scripts/compose_electron_rest_law_claim.py',
 'scripts/compose_electron_transformed_dynamics.py',
 'scripts/compose_field_equations.py',
 'scripts/compose_limits.py',
 'scripts/compose_mass_coefficients.py',
 'scripts/compose_material_acceleration.py',
 'scripts/compose_material_mass_claim.py',
 'scripts/compose_material_relative_frame.py',
 'scripts/compose_material_velocity.py',
 'scripts/compose_origin_clock.py',
 'scripts/compose_point_particle_dynamics.py',
 'scripts/compose_relativity_conjecture.py',
 'scripts/compose_rest_force.py',
 'scripts/compose_situated_criticism.py',
 'scripts/compose_two_postulates.py',
 'scripts/review_electron_convention_caution.py',
 'scripts/review_electron_directional_masses.py',
 'scripts/review_electron_mass_rewrite.py',
 'scripts/review_material_mass_claim.py']
SEMANTIC_REVIEW=['同じ電子・瞬間共動系の力・Kでの加速度・単位を保つ条件付き規約として縦横質量を得る。横質量を現代の別規約へ置き換えない。',
 'ばね秤で測り得るという例示は実測済みを含意しない。無修飾の力という呼称の採用は力の定義の唯一性ではない。',
 '力と加速度の別定義による数値差、理論比較での注意要求、理論の真理や優劣を区別する。',
 '比較領域・比較者の方法上の立場・吟味の通常基準は閉じた記述から参照し、引用内容を実行しない。通常基準は強めた要求から逆定義しない。',
 '物質点への拡張は任意に小さい電荷の付加可能性を理由とする著者の説明であり、任意物体で実験が完了したとの主張へ変えない。']
OUT=ROOT/'output/einstein-tenth-mass-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=[*profile.LIMITS,*activity_profile.LIMITS,*SEMANTIC_REVIEW]

_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=ActivityRoleVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return ActivityRoleVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==338,'Tenth-mass source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','give','fruit',temporal.PARTS[i//256],temporal.PARTS[(i//16)%16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.CONTRACTS)|set(activity_profile.CONTRACTS))
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
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-mass reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-mass reference')
    return REFERENCE_KINDS[old]


def role_definitions():
    role_mapping=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|mapping()|{n:vocabulary()._symbols[n] for n in (*activity_profile.CONTRACTS,'theoreticalinquirytopic')}
    return renamed(list(ROLE_DEFINITIONS.values()),role_mapping)


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
    result['statements']=renamed(doc['statements'][329:335],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    units={r['id']:r for r in inventory['units']}
    for name,row in SOURCE_UNITS.items():
        require(units[name]['text']==row['text'] and units[name]['text_sha256']==row['sha256'],'Source text boundary changed')
    require(previous.SENTENCES['tenthtransformedmotionsentence']==[108,1],'Previous paragraph boundary changed')
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
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905']
    require(c.document_path=='examples/v014/einstein-auxiliary-reference-order-v1.noema','Unreviewed source selection')
    units={r['id']:r for r in author.read('artifacts/written-units-v1/einstein-1905.json')['units']}
    state=author.read('data/work-state.json');index=author.read(state['review_index'])
    registered={r['review']:r for r in index['works']['einstein-1905']['reviews']}
    for row in REVIEW_SELECTION:
        review=author.read(row['review']);unit=units[row['unit']]
        require(review['unit']==row['unit'] and review['decision']=='equivalent_under_stated_reading' and not review['unresolved'],'Source review incomplete')
        require(review['source']['text']==unit['text'] and review['source']['unit_sha256']==unit['text_sha256'],'Source evidence differs')
        require(registered[row['review']]['statements']==row['statements'],'Registered review selection changed')
    require(SOURCE_ORDER==[259,258,260,261,262,263],'Selection changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-tenth-mass-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=SOURCE_UNITS,
        source_order_basis=dict(review='data/einstein-electron-directional-masses-u0252-review-v1.json',
            retained_indices=[423,422],active_indices=[259,258],reason='The mass inquiry precedes the rewriting sentence; registration membership is unchanged.'),
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        reused_typed_bodies=REUSED_BODIES,new_public_relations=37,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=81,core_edition=12,new_source_assertions=6,
        total_source_assertions=250,total_annotations=88,source_reviews=REVIEW_SELECTION,parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,
        document_integration_credit=0,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible tenth-mass document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[first],start,values[last],end,values['ri']):values[n] for n,(first,start,last,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    require(kind=='describedreference','Unknown mass reference kind')
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS}
    return TemporalReferences(roles,{})


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
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference',)}



def prepare():
    profile.prepare();activity_profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
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
    paths={*pins,'data/work-state.json',state['review_index'],active['identifier_annotations'],
        SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,
        activity_profile.LIBRARY,activity_profile.BASIS,activity_profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/tenth_mass_visible_profile.py','scripts/tenth_mass_visible_profile_contracts.py',
        'scripts/activity_role_visible_profile.py','scripts/tenth_mass_reference_roles.py',
        'scripts/check_einstein_tenth_mass_visible.py','scripts/visible_tenth_mass_visible_collection.py',
        'tests/test_tenth_mass_visible.py','tests/test_tenth_mass_reference_roles.py',
        'tests/test_tenth_mass_visible_profile.py',*DIAGNOSTIC_VALIDATORS,
        'docs/einstein-tenth-mass-visible-v1.md'}
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved tenth-mass bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-tenth-mass-visible-evidence-1',core_words=375,profile_words=1039,profile_edition=81,
        new_public_relations=37,new_reference_primitives=0,new_source_assertions=6,total_source_assertions=250,annotations=88,
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
