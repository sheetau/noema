"""Connect all six force-interpretation sentences with explicit units, objects and references."""
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
from scripts import force_interpretation_visible_profile as profile
from scripts.force_interpretation_visible_profile import ROOT,ForceInterpretationVisibleVocabulary,write_once
from scripts import check_einstein_field_symmetry_visible as previous
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

SOURCE='examples/v016/einstein-force-interpretation-visible-v1.noema'
BRIDGE='data/einstein-force-interpretation-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-force-interpretation-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[194, 32, 33, 34, 35, 195]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
  'sha256': '68b45874f2d701b5270ff8c1a1ae9b3658c54058748eb483a53663368b6df049',
  'actually_displayed': True,
  'independent_human_reading': False,
  'inspection': 'current goal turn; image emitted alongside a32dfc',
  'observations': ['u0173はZur Interpretationから二つの言い表しを導入するコロンまでの六文。d. h.を文の境界にしない。',
                   '直前の最初の三式は左列X′・Y′・Z′。第一の番号付き言い表しは909頁末から始まる。']},
 {'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg',
  'sha256': 'e634a38acf3bf76e5d99086296c70a267368c684501148cc789ede1def276ea5',
  'actually_displayed': True,
  'independent_human_reading': False,
  'inspection': 'current goal turn; image emitted alongside ced5d1',
  'observations': ['第一項の続きとAlte Ausdrucksweiseの括弧書き、独立した番号2とNeue Ausdrucksweiseを確認。',
                   '二項の後にAnalogesの段落が続く。後続二項の内容は今回の六文の完了件数へ加えない。']}]
PUBLIC_RELATIONS={'zoh': 'directedcomparisontrial',
 'eisqb': 'baseunitdimensions',
 'eisqc': 'pointchargecarrier',
 'eisqd': 'unitpositionassignment',
 'eisqe': 'directedelectricforcerecord',
 'eisql': 'definitionbasedclaim',
 'eisqo': 'canwordcontent'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['sbz2',
 'scc2',
 'ejwb',
 'ejwc',
 'ejwd',
 'ejwe',
 'ejwf',
 'ejwg',
 'ejwh',
 'ejwi',
 'ejwj',
 'ejwk',
 'ejwl',
 'ejwm',
 'ejwn',
 'ejwo',
 'ejwp',
 'ejwq',
 'ejwr',
 'ejws',
 'ejwt',
 'ejwu',
 'ejwv',
 'ejww',
 'ejwx',
 'ejwy',
 'ejwz',
 'ejw2',
 'ejw3',
 'ejw4',
 'ejw5',
 'ejw6',
 'ejw7',
 'ejxa',
 'ejxb',
 'ejxc',
 'ejxd',
 'ejxe',
 'ejxf',
 'ejxg',
 'ejxh',
 'ejxi']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'eisqm': (76, 1), 'zoy': (76, 2), 'zpg': (76, 3), 'zph': (76, 4), 'zpi': (76, 5), 'eisqn': (76, 6)}
TEXT_SENTENCES={'eisqm': (76, 1), 'zoy': (76, 2), 'zpg': (76, 3), 'zph': (76, 4), 'zpi': (76, 5), 'eisqn': (76, 6)}
TOKEN_COUNTS={'eisqm': 7, 'zoy': 36, 'zpg': 16, 'zph': 19, 'zpi': 28, 'eisqn': 16}
SOURCE_SENTENCES={'eisqm': {'position': [76, 1],
           'text': 'Zur Interpretation dieser Gleichungen bemerken wir folgendes. ',
           'range': [0, 62],
           'tokens': ['Zur', 'Interpretation', 'dieser', 'Gleichungen', 'bemerken', 'wir', 'folgendes.']},
 'zoy': {'position': [76, 2],
         'text': 'Es liegt eine punktförmige Elektrizitätsmenge vor, welche im ruhenden System [M0315] '
                 'gemessen von der Größe „eins“ sei, d. h. im ruhenden System ruhend auf eine gleiche '
                 'Elektrizitätsmenge im Abstand 1 cm die Kraft 1 Dyn ausübe. ',
         'range': [62, 290],
         'tokens': ['Es',
                    'liegt',
                    'eine',
                    'punktförmige',
                    'Elektrizitätsmenge',
                    'vor,',
                    'welche',
                    'im',
                    'ruhenden',
                    'System',
                    '[M0315]',
                    'gemessen',
                    'von',
                    'der',
                    'Größe',
                    '„eins“',
                    'sei,',
                    'd.',
                    'h.',
                    'im',
                    'ruhenden',
                    'System',
                    'ruhend',
                    'auf',
                    'eine',
                    'gleiche',
                    'Elektrizitätsmenge',
                    'im',
                    'Abstand',
                    '1',
                    'cm',
                    'die',
                    'Kraft',
                    '1',
                    'Dyn',
                    'ausübe.']},
 'zpg': {'position': [76, 3],
         'text': 'Nach dem Relativitätsprinzip ist diese elektrische Masse auch im bewegten System gemessen '
                 'von der Größe „eins“. ',
         'range': [290, 402],
         'tokens': ['Nach',
                    'dem',
                    'Relativitätsprinzip',
                    'ist',
                    'diese',
                    'elektrische',
                    'Masse',
                    'auch',
                    'im',
                    'bewegten',
                    'System',
                    'gemessen',
                    'von',
                    'der',
                    'Größe',
                    '„eins“.']},
 'zph': {'position': [76, 4],
         'text': 'Ruht diese Elektrizitätsmenge relativ zum ruhenden System, so ist definitionsgemäß der '
                 'Vektor ([M0316]) gleich der auf sie wirkenden Kraft. ',
         'range': [402, 542],
         'tokens': ['Ruht',
                    'diese',
                    'Elektrizitätsmenge',
                    'relativ',
                    'zum',
                    'ruhenden',
                    'System,',
                    'so',
                    'ist',
                    'definitionsgemäß',
                    'der',
                    'Vektor',
                    '([M0316])',
                    'gleich',
                    'der',
                    'auf',
                    'sie',
                    'wirkenden',
                    'Kraft.']},
 'zpi': {'position': [76, 5],
         'text': 'Ruht die Elektrizitätsmenge gegenüber dem bewegten System (wenigstens in dem betreffenden '
                 'Augenblick), so ist die auf sie wirkende, in dem bewegten System gemessene Kraft gleich '
                 'dem Vektor ([M0317]). ',
         'range': [542, 742],
         'tokens': ['Ruht',
                    'die',
                    'Elektrizitätsmenge',
                    'gegenüber',
                    'dem',
                    'bewegten',
                    'System',
                    '(wenigstens',
                    'in',
                    'dem',
                    'betreffenden',
                    'Augenblick),',
                    'so',
                    'ist',
                    'die',
                    'auf',
                    'sie',
                    'wirkende,',
                    'in',
                    'dem',
                    'bewegten',
                    'System',
                    'gemessene',
                    'Kraft',
                    'gleich',
                    'dem',
                    'Vektor',
                    '([M0317]).']},
 'eisqn': {'position': [76, 6],
           'text': 'Die ersten drei der obigen Gleichungen lassen sich mithin auf folgende zwei Weisen in '
                   'Worte kleiden:',
           'range': [742, 842],
           'tokens': ['Die',
                      'ersten',
                      'drei',
                      'der',
                      'obigen',
                      'Gleichungen',
                      'lassen',
                      'sich',
                      'mithin',
                      'auf',
                      'folgende',
                      'zwei',
                      'Weisen',
                      'in',
                      'Worte',
                      'kleiden:']}}
SPANS={'eisqj': ('zoy', 18, 36),
 'forcezolanchor': ('zoy', 4, 5),
 'forcezomanchor': ('zoy', 25, 27),
 'forcezosanchor': ('zoy', 31, 31),
 'forcezotanchor': ('zoy', 35, 35),
 'forcezopanchor': ('zoy', 28, 31),
 'forcezoqanchor': ('zoy', 32, 35),
 'forcezpoanchor': ('zpi', 8, 12),
 'forcezoxanchor': ('zoy', 13, 17),
 'forcezpdanchor': ('zpg', 13, 16),
 'forcezplanchor': ('zph', 14, 19),
 'forcezpmanchor': ('zpi', 15, 24)}
MULTI_SPANS={}
DESIGNATIONS={}
FORMS={}
INHERITED_DESIGNATIONS={'eisk3': {'form': 'Relativitätsprinzip',
           'introduced_at': ['wu', 1],
           'use': '第三文の相対性原理。M0315のKと取り違えない。eischで同じ既存eion内容を参照する。'},
 'eispj': {'form': '(X,Y,Z)',
           'introduced_at': ['eispm', 1],
           'use': '第四文M0316で同じ三成分の表記を再使用。新しい名付けとして旧anchorを上書きしない。'},
 'eispv': {'form': '(X′,Y′,Z′)',
           'introduced_at': ['eispy', 1],
           'use': '第五文M0317で同じ移動系の三成分を再使用。初出の指定と今回の文位置を区別する。'},
 'M0315': {'use': '第二文の静止系Kは既存ra。同じ文の位置と全体逆写像を保ち、新しい系や原理名を作らない。'}}
ROLE_ASSIGNMENTS={'zol': 'forcezolrole',
 'zom': 'forcezomrole',
 'zon': 'forcezonrole',
 'zoo': 'forcezoorole',
 'zos': 'forcezosrole',
 'zot': 'forcezotrole',
 'zou': 'forcezourole',
 'zop': 'forcezoprole',
 'zoq': 'forcezoqrole',
 'zpo': 'forcezporole',
 'zov': 'forcezovrole',
 'zow': 'forcezowrole',
 'zox': 'forcezoxrole',
 'eisqf': 'forceeisqfrole',
 'zpd': 'forcezpdrole',
 'zpp': 'forcezpprole',
 'eisqk': 'forceeisqkrole',
 'zpe': 'forcezperole',
 'zpf': 'forcezpfrole',
 'eisqg': 'forceeisqgrole',
 'eisqh': 'forceeisqhrole',
 'zpj': 'forcezpjrole',
 'zpk': 'forcezpkrole',
 'zpl': 'forcezplrole',
 'zpm': 'forcezpmrole',
 'eisqi': 'forceeisqirole',
 'zpq': 'forcezpqrole',
 'zpr': 'forcezprrole'}
REFERENCE_SORTS={'zol': 'individual',
 'zom': 'individual',
 'zon': 'individual',
 'zoo': 'individual',
 'zos': 'individual',
 'zot': 'individual',
 'zou': 'individual',
 'zop': 'individual',
 'zoq': 'individual',
 'zpo': 'individual',
 'zov': 'individual',
 'zow': 'individual',
 'zox': 'individual',
 'eisqf': 'individual',
 'zpd': 'individual',
 'zpp': 'individual',
 'eisqk': 'individual',
 'zpe': 'individual',
 'zpf': 'individual',
 'eisqg': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eisqh': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zpj': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zpk': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zpl': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zpm': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'eisqi': {'kind': 'function',
           'parameters': ['individual'],
           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
 'zpq': 'individual',
 'zpr': 'individual'}
REFERENCE_ANCHORS={'zol': 'forcezolanchor',
 'zom': 'forcezomanchor',
 'zon': 'eisqj',
 'zoo': 'eisqj',
 'zos': 'forcezosanchor',
 'zot': 'forcezotanchor',
 'zou': 'eisqj',
 'zop': 'forcezopanchor',
 'zoq': 'forcezoqanchor',
 'zpo': 'forcezpoanchor',
 'zov': 'forcezopanchor',
 'zow': 'forcezoqanchor',
 'zox': 'forcezoxanchor',
 'eisqf': 'forcezomanchor',
 'zpd': 'forcezpdanchor',
 'zpp': 'zph',
 'eisqk': 'zpi',
 'zpe': 'zph',
 'zpf': 'zpi',
 'eisqg': 'eisqj',
 'eisqh': 'eisqj',
 'zpj': 'zph',
 'zpk': 'zpi',
 'zpl': 'forcezplanchor',
 'zpm': 'forcezpmanchor',
 'eisqi': 'forcezoqanchor',
 'zpq': 'eisqn',
 'zpr': 'eisqn'}
ROLE_DEFINITIONS={'zol': {'kind': 'definition',
         'name': 'forcezolrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'eisqc',
                  'arguments': [{'kind': 'variable', 'name': 'va'}, {'kind': 'variable', 'name': 'vb'}]}},
 'zom': {'kind': 'definition',
         'name': 'forcezomrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': 'individual',
                  'body': {'kind': 'exists',
                           'variable': 'vd',
                           'sort': 'individual',
                           'body': {'kind': 'call',
                                    'symbol': 'zoh',
                                    'arguments': [{'kind': 'variable', 'name': 'vc'},
                                                  {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                                  {'kind': 'variable', 'name': 'va'},
                                                  {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                                  {'kind': 'variable', 'name': 'vd'},
                                                  {'kind': 'variable', 'name': 'vb'}]}}}},
 'zon': {'kind': 'definition',
         'name': 'forcezonrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': 'individual',
                  'body': {'kind': 'call',
                           'symbol': 'zoh',
                           'arguments': [{'kind': 'variable', 'name': 'va'},
                                         {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zom', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'zoo': {'kind': 'definition',
         'name': 'forcezoorole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'zoh',
                  'arguments': [{'kind': 'call', 'symbol': 'zon', 'arguments': []},
                                {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                {'kind': 'call', 'symbol': 'zom', 'arguments': []},
                                {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zos': {'kind': 'definition',
         'name': 'forcezosrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'eisqb',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                {'kind': 'number', 'numerator': 0, 'denominator': 1},
                                {'kind': 'number', 'numerator': 0, 'denominator': 1},
                                {'kind': 'number', 'numerator': 1, 'denominator': 100},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zot': {'kind': 'definition',
         'name': 'forcezotrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'eisqb',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                {'kind': 'number', 'numerator': -2, 'denominator': 1},
                                {'kind': 'number', 'numerator': 1, 'denominator': 100000},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zou': {'kind': 'definition',
         'name': 'forcezourole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'zof',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'zor', 'arguments': []},
                                {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zop': {'kind': 'definition',
         'name': 'forcezoprole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'zof',
                  'arguments': [{'kind': 'call', 'symbol': 'zos', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'},
                                {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zoq': {'kind': 'definition',
         'name': 'forcezoqrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'zof',
                  'arguments': [{'kind': 'call', 'symbol': 'zot', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'},
                                {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zpo': {'kind': 'definition',
         'name': 'forcezporole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function',
                           'parameters': ['individual'],
                           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                  'body': {'kind': 'call',
                           'symbol': 'eisqd',
                           'arguments': [{'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                         {'kind': 'variable', 'name': 'va'},
                                         {'kind': 'call', 'symbol': 'ta', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'rb', 'arguments': []},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'zov': {'kind': 'definition',
         'name': 'forcezovrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'call',
                           'symbol': 'zog',
                           'arguments': [{'kind': 'variable', 'name': 'va'},
                                         {'kind': 'call', 'symbol': 'zon', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zop', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zos', 'arguments': []},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'zow': {'kind': 'definition',
         'name': 'forcezowrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'call',
                           'symbol': 'zog',
                           'arguments': [{'kind': 'variable', 'name': 'va'},
                                         {'kind': 'call', 'symbol': 'zon', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zoq', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zot', 'arguments': []},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'zox': {'kind': 'definition',
         'name': 'forcezoxrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'call',
                           'symbol': 'zog',
                           'arguments': [{'kind': 'variable', 'name': 'va'},
                                         {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zor', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zou', 'arguments': []},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'eisqf': {'kind': 'definition',
           'name': 'forceeisqfrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'exists',
                    'variable': 'vc',
                    'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                    'body': {'kind': 'call',
                             'symbol': 'zog',
                             'arguments': [{'kind': 'variable', 'name': 'va'},
                                           {'kind': 'call', 'symbol': 'zom', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'zor', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'zou', 'arguments': []},
                                           {'kind': 'variable', 'name': 'vc'},
                                           {'kind': 'variable', 'name': 'vb'}]}}},
 'zpd': {'kind': 'definition',
         'name': 'forcezpdrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'call',
                           'symbol': 'zog',
                           'arguments': [{'kind': 'variable', 'name': 'va'},
                                         {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zor', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zou', 'arguments': []},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'zpp': {'kind': 'definition',
         'name': 'forcezpprole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'call',
                           'symbol': 'zog',
                           'arguments': [{'kind': 'variable', 'name': 'va'},
                                         {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zor', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                         {'kind': 'call', 'symbol': 'zou', 'arguments': []},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'eisqk': {'kind': 'definition',
           'name': 'forceeisqkrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'exists',
                    'variable': 'vc',
                    'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                    'body': {'kind': 'call',
                             'symbol': 'zog',
                             'arguments': [{'kind': 'variable', 'name': 'va'},
                                           {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'zor', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                           {'kind': 'call', 'symbol': 'zou', 'arguments': []},
                                           {'kind': 'variable', 'name': 'vc'},
                                           {'kind': 'variable', 'name': 'vb'}]}}},
 'zpe': {'kind': 'definition',
         'name': 'forcezperole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function',
                           'parameters': ['individual'],
                           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                  'body': {'kind': 'and',
                           'arguments': [{'kind': 'call',
                                          'symbol': 'zpc',
                                          'arguments': [{'kind': 'variable', 'name': 'va'},
                                                        {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zpn', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zot', 'arguments': []},
                                                        {'kind': 'variable', 'name': 'vc'},
                                                        {'kind': 'variable', 'name': 'vb'}]},
                                         {'kind': 'call',
                                          'symbol': 'eirl',
                                          'arguments': [{'kind': 'variable', 'name': 'va'},
                                                        {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                                        {'kind': 'variable', 'name': 'vb'}]}]}}},
 'zpf': {'kind': 'definition',
         'name': 'forcezpfrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': {'kind': 'function',
                           'parameters': ['individual'],
                           'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                  'body': {'kind': 'and',
                           'arguments': [{'kind': 'call',
                                          'symbol': 'zpc',
                                          'arguments': [{'kind': 'variable', 'name': 'va'},
                                                        {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zpn', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zot', 'arguments': []},
                                                        {'kind': 'variable', 'name': 'vc'},
                                                        {'kind': 'variable', 'name': 'vb'}]},
                                         {'kind': 'call',
                                          'symbol': 'eirl',
                                          'arguments': [{'kind': 'variable', 'name': 'va'},
                                                        {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                                        {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                                        {'kind': 'variable', 'name': 'vb'}]}]}}},
 'eisqg': {'kind': 'definition',
           'name': 'forceeisqgrole',
           'parameters': [{'name': 'va',
                           'sort': {'kind': 'function',
                                    'parameters': ['individual'],
                                    'result': {'kind': 'function',
                                               'parameters': ['number'],
                                               'result': 'truth'}}},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'and',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisqd',
                                   'arguments': [{'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zos', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zik', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'variable', 'name': 'vb'}]},
                                  {'kind': 'call',
                                   'symbol': 'shn',
                                   'arguments': [{'kind': 'call', 'symbol': 'shx', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'function_ref', 'symbol': 'ba'}]}]}},
 'eisqh': {'kind': 'definition',
           'name': 'forceeisqhrole',
           'parameters': [{'name': 'va',
                           'sort': {'kind': 'function',
                                    'parameters': ['individual'],
                                    'result': {'kind': 'function',
                                               'parameters': ['number'],
                                               'result': 'truth'}}},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'and',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisqd',
                                   'arguments': [{'kind': 'call', 'symbol': 'zom', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zos', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zik', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'variable', 'name': 'vb'}]},
                                  {'kind': 'call',
                                   'symbol': 'shn',
                                   'arguments': [{'kind': 'call', 'symbol': 'shx', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'function_ref', 'symbol': 'ba'}]}]}},
 'zpj': {'kind': 'definition',
         'name': 'forcezpjrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['individual'],
                                  'result': {'kind': 'function',
                                             'parameters': ['number'],
                                             'result': 'truth'}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'eisqd',
                                 'arguments': [{'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'ta', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'rb', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'variable', 'name': 'vb'}]},
                                {'kind': 'call',
                                 'symbol': 'shn',
                                 'arguments': [{'kind': 'call', 'symbol': 'shx', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'function_ref', 'symbol': 'ba'}]}]}},
 'zpk': {'kind': 'definition',
         'name': 'forcezpkrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['individual'],
                                  'result': {'kind': 'function',
                                             'parameters': ['number'],
                                             'result': 'truth'}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'eisqd',
                                 'arguments': [{'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'ta', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'rb', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'variable', 'name': 'vb'}]},
                                {'kind': 'call',
                                 'symbol': 'shn',
                                 'arguments': [{'kind': 'call', 'symbol': 'shx', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'function_ref', 'symbol': 'ba'}]}]}},
 'zpl': {'kind': 'definition',
         'name': 'forcezplrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['individual'],
                                  'result': {'kind': 'function',
                                             'parameters': ['number'],
                                             'result': 'truth'}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'zpc',
                                 'arguments': [{'kind': 'call', 'symbol': 'zpe', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zpn', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zot', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'variable', 'name': 'vb'}]},
                                {'kind': 'call',
                                 'symbol': 'shn',
                                 'arguments': [{'kind': 'sequence',
                                                'element': 'individual',
                                                'items': [{'kind': 'call', 'symbol': 'yn', 'arguments': []},
                                                          {'kind': 'call', 'symbol': 'yo', 'arguments': []},
                                                          {'kind': 'call', 'symbol': 'yp', 'arguments': []}]},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'function_ref', 'symbol': 'ba'}]}]}},
 'zpm': {'kind': 'definition',
         'name': 'forcezpmrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['individual'],
                                  'result': {'kind': 'function',
                                             'parameters': ['number'],
                                             'result': 'truth'}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'zpc',
                                 'arguments': [{'kind': 'call', 'symbol': 'zpf', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zpn', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zpo', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zot', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'variable', 'name': 'vb'}]},
                                {'kind': 'call',
                                 'symbol': 'shn',
                                 'arguments': [{'kind': 'sequence',
                                                'element': 'individual',
                                                'items': [{'kind': 'call', 'symbol': 'yn', 'arguments': []},
                                                          {'kind': 'call', 'symbol': 'yo', 'arguments': []},
                                                          {'kind': 'call', 'symbol': 'yp', 'arguments': []}]},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'function_ref', 'symbol': 'ba'}]}]}},
 'eisqi': {'kind': 'definition',
           'name': 'forceeisqirole',
           'parameters': [{'name': 'va',
                           'sort': {'kind': 'function',
                                    'parameters': ['individual'],
                                    'result': {'kind': 'function',
                                               'parameters': ['number'],
                                               'result': 'truth'}}},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'and',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisqe',
                                   'arguments': [{'kind': 'call', 'symbol': 'zow', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zon', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zol', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zom', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zoo', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'zot', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'variable', 'name': 'vb'}]},
                                  {'kind': 'call',
                                   'symbol': 'shn',
                                   'arguments': [{'kind': 'sequence',
                                                  'element': 'individual',
                                                  'items': [{'kind': 'call', 'symbol': 'yn', 'arguments': []},
                                                            {'kind': 'call', 'symbol': 'yo', 'arguments': []},
                                                            {'kind': 'call',
                                                             'symbol': 'yp',
                                                             'arguments': []}]},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'function_ref', 'symbol': 'ba'}]}]}},
 'zpq': {'kind': 'definition',
         'name': 'forcezpqrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'eislk',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'eisqn', 'arguments': []},
                                {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'zpr': {'kind': 'definition',
         'name': 'forcezprrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'eislk',
                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                {'kind': 'call', 'symbol': 'eisqn', 'arguments': []},
                                {'kind': 'number', 'numerator': 2, 'denominator': 1},
                                {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                {'kind': 'variable', 'name': 'vb'}]}}}
LOCAL_NAMES=['sbz2',
 'scc2',
 'ejwb',
 'ejwc',
 'ejwd',
 'ejwe',
 'ejwf',
 'ejwg',
 'ejwh',
 'ejwi',
 'ejwj',
 'ejwk',
 'ejwl',
 'ejwm',
 'ejwn',
 'ejwo',
 'ejwp',
 'ejwq',
 'ejwr',
 'ejws',
 'ejwt',
 'ejwu',
 'ejwv',
 'ejww',
 'ejwx',
 'ejwy',
 'ejwz',
 'ejw2',
 'ejw3',
 'ejw4',
 'ejw5',
 'ejw6',
 'ejw7',
 'ejxa',
 'ejxb',
 'ejxc',
 'ejxd',
 'ejxe',
 'ejxf',
 'ejxg',
 'ejxh',
 'ejxi',
 'eisqm',
 'zoy',
 'zpg',
 'zph',
 'zpi',
 'eisqn',
 'eisqj',
 'forcezolanchor',
 'forcezomanchor',
 'forcezosanchor',
 'forcezotanchor',
 'forcezopanchor',
 'forcezoqanchor',
 'forcezpoanchor',
 'forcezoxanchor',
 'forcezpdanchor',
 'forcezplanchor',
 'forcezpmanchor',
 'zol',
 'zom',
 'zon',
 'zoo',
 'zos',
 'zot',
 'zou',
 'zop',
 'zoq',
 'zpo',
 'zov',
 'zow',
 'zox',
 'eisqf',
 'zpd',
 'zpp',
 'eisqk',
 'zpe',
 'zpf',
 'eisqg',
 'eisqh',
 'zpj',
 'zpk',
 'zpl',
 'zpm',
 'eisqi',
 'zpq',
 'zpr',
 'forcezolrole',
 'forcezomrole',
 'forcezonrole',
 'forcezoorole',
 'forcezosrole',
 'forcezotrole',
 'forcezourole',
 'forcezoprole',
 'forcezoqrole',
 'forcezporole',
 'forcezovrole',
 'forcezowrole',
 'forcezoxrole',
 'forceeisqfrole',
 'forcezpdrole',
 'forcezpprole',
 'forceeisqkrole',
 'forcezperole',
 'forcezpfrole',
 'forceeisqgrole',
 'forceeisqhrole',
 'forcezpjrole',
 'forcezpkrole',
 'forcezplrole',
 'forcezpmrole',
 'forceeisqirole',
 'forcezpqrole',
 'forcezprrole']
READINGS=('data/einstein-force-interpretation-source-reading-v1.json',)
REVIEWS=('data/einstein-force-interpretation-u0173-review-v1.json',)
SEMANTIC_REVIEW=['採用済みの全六文の意味判断を保存し、最新原稿の主張194,32,33,34,35,195を本文順で追加する。旧保存番号と本文順を取り違えない。',
 '点状電気量は第一担体の理想化。第二担体の点状性・静止は補わない。電気量を慣性質量や座標点へ替えない。',
 'cmは長さ尺度1/100、Dynは次元(1,1,-2)と尺度1/100000、秒は時間尺度1。原著へ現代の標準器や定義定数を加えない。',
 '校正は同じK・同じ出来事・同じ明示単位の二位置の同時刻距離1と、第一対象から第二対象への力の大きさ1。力の方向や測定済みを補わない。',
 'kで同じ単位電気量1という内容は別記録。相対性原理に基づく著者の推論として引用し、物理的な不変性の自動証明にしない。',
 'Kへの静止とkへの当該瞬間の静止は別の条件文。後者は同じ座標時刻の三微分0で、非零加速度も許す。',
 '校正の出来事zooと力評価の出来事zpoの同一性・非同一性を補わず、校正cm/秒の数値を場のta/rbの座標へ代入しない。',
 '相手へ及ぼす校正力と第一担体自身への局所的な試験力を区別する。重力・支持力などを含む合力や真空内の実在試験体を追加しない。',
 '最初の三式は同じ六式の電気側。磁気側の変換三式を含めず、同じ全領域と物理設定を保持する。',
 '二つの言い表しの可能性とmithinの帰結を著者に帰属する。二つだけという排他性、後続の近似を除いた厳密同義性、実際の発話完了を補わない。',
 '参照の役割28定義を本文に置き、対象・系・出来事・単位を共有する。距離1・力の大きさ1・静止・場との等値を取得成功の条件にしない。',
 '四座標と三成分の力は同じ関数型でも役割を区別する。後続二項だけは番号付き列挙の既存introduceditemで参照し、その内容を先取りしない。',
 '継承したRelativitätsprinzipと二組の場の成分表記は初出参照を保存する。新しい表記や静止系Kへ読み替えない。']
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
        chain=ForceInterpretationVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return ForceInterpretationVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==255,'Force-interpretation source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','fruit',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,(node,start,end) in SPANS.items():add(old,call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    for old,(first,last) in MULTI_SPANS.items():add(old,call(voc._symbols['sentencespanreference'],k('eirf'),k(first),k(last),k('ri')))
    for old,(node,index) in DESIGNATIONS.items():add(old,call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri')))
    doc['declarations']+=voc.imports(set(profile.ALL_CONTRACTS))
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:
        add(old,call(voc._symbols[reference_kind(old)],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')),REFERENCE_SORTS[old])
    inherited={d['name']:d for d in doc['declarations']}
    for d in renamed([d for d in source_excerpt()['declarations'] if d['name'] in REUSED_DEFINITIONS],m):
        require(inherited.get(d['name'])==d,'Inherited mathematical definition differs: '+d['name'])
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown force-interpretation reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown force-interpretation reference')
    return 'describedreference' if REFERENCE_SORTS[old]=='individual' else 'describedindividualcutfunctionreference'


def role_definitions():
    role_mapping=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|mapping()
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
    result['statements']=renamed(doc['statements'][207:213],inverse);return normalize_document(result)



def text_boundaries():
    prior=previous.text_boundaries()['sentences']['fieldsymmetrysentence']
    require(prior['position']==[75,1] and list(SENTENCES.values())==[(76,i) for i in range(1,7)],'Paragraph/sentence sequence changed')
    units={u['id']:u for u in author.read(author.UNITS)['units']};unit=units['einstein-1905:u0173']
    reading=author.read(READINGS[0]);require(reading['text']==unit['text'] and reading['unit_sha256']==unit['text_sha256'],'Six-sentence transcription changed')
    require(len(reading['sentences'])==len(SOURCE_SENTENCES)==6,'Sentence count changed')
    end=0
    for (name,row),saved in zip(SOURCE_SENTENCES.items(),reading['sentences'],strict=True):
        start,stop=row['range']
        require(start==end and unit['text'][start:stop]==row['text']==saved['text'] and row['range']==saved['range'],'Sentence source range changed')
        require(row['tokens']==row['text'].split() and len(row['tokens'])==TOKEN_COUNTS[name],'Sentence tokenization changed');end=stop
    require(end==len(unit['text']) and SOURCE_SENTENCES['zoy']['tokens'][17:19]==['d.','h.'],'Abbreviation or paragraph ending changed')
    for node,start,stop in SPANS.values():require(node in SENTENCES and 1<=start<=stop<=TOKEN_COUNTS[node],'Invalid token anchor')
    require(SPANS['eisqj']==('zoy',18,36),'Calibration explanation changed')
    require(SPANS[REFERENCE_ANCHORS['zpo']]==('zpi',8,12) and SPANS[REFERENCE_ANCHORS['zpm']]==('zpi',15,24),'Moment or force phrase anchor incomplete')
    require(all(names()[n]==previous.names()[n] for n in ('eisk3','eispj','eispv','ra')),'Inherited designation or frame was replaced')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph76 has six sentences. The d. h. explanation belongs to sentence2. The final colon introduces two later numbered wordings without integrating their contents yet.',
        sentences={n:dict(row,position=list(SENTENCES[n])) for n,row in SOURCE_SENTENCES.items()},
        spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},designations={},designation_forms={},inherited_designations=INHERITED_DESIGNATIONS)



def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math={};coverage={}
    for path in READINGS:
        for row in (author.read(path),):
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Force interpretation source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={'einstein-1905:u0173'}
    require(set(coverage)==expected,'Force interpretation source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old force interpretation review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old force interpretation review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Force interpretation review coverage differs')
    require(SOURCE_ORDER==[194,32,33,34,35,195],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Force interpretation source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-force-interpretation-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),inherited_designations=INHERITED_DESIGNATIONS,reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=7,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=72,core_edition=12,new_source_assertions=6,total_source_assertions=175,total_annotations=38,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible force-interpretation document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    from scripts.field_symmetry_visible_profile import IndividualCutFunctionReferences
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(roles,{})
    require(kind=='describedindividualcutfunctionreference','Unknown force-interpretation reference type')
    return IndividualCutFunctionReferences(roles)





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
        if first in {values[n] for n in TEXT_SENTENCES} or last in {values[n] for n in TEXT_SENTENCES}:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    def passage(document,first,last,context):
        if first in {values[n] for n in TEXT_SENTENCES} or last in {values[n] for n in TEXT_SENTENCES}:
            return MovingTextReferences({(values['eirf'],values[a],values[b],values['ri']):values[n] for n,(a,b) in MULTI_SPANS.items()},{}).span(document,first,last,context)
        return result['sentencespanreference'](document,first,last,context)
    def designation(document,node,index,context):
        if node in {values[n] for n in (*SENTENCES,*HEADINGS,*SPANS)}:
            return DesignationReferences({(values['eirf'],values[a],i,values['ri']):values[n] for n,(a,i) in DESIGNATIONS.items()}).reference(document,node,index,context)
        return result['designationreference'](document,node,index,context)
    def typed(kind):
        nodes={values[reference_anchor(old)] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
        def lookup(document,node,role,context):
            if node in nodes:return reference_model(values,kind).described(document,node,role,context)
            require(kind in result,'Unknown typed reference')
            return result[kind](document,node,role,context)
        return lookup
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedindividualcutfunctionreference')}



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-field-symmetry-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/force_interpretation_visible_profile.py','scripts/force_interpretation_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_force_interpretation_visible.py','scripts/visible_force_interpretation_visible_collection.py',
        'tests/test_force_interpretation_visible.py','docs/einstein-force-interpretation-visible-v1.md'}
    for name in ('force_interpretation','point_charge_calibration','moving_unit_charge','resting_charge_force'):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256)
        paths.update(getattr(module,'DEPENDENCIES',()));paths.update(getattr(module,'PRIORS',()))
    paths.update(annotations()['source_sha256'])
    paths.update(row['path'] for row in SOURCE_VISUAL_REVIEW)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved force-interpretation bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-force-interpretation-visible-evidence-1',core_words=375,profile_words=887,profile_edition=72,
        new_public_relations=7,new_reference_primitives=0,new_source_assertions=6,total_source_assertions=175,annotations=38,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
