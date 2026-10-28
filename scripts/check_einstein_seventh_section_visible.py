"""Connect the seventh-section wave, Doppler, aberration and amplitude dependency group."""
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
from scripts import seventh_section_visible_profile as profile
from scripts.seventh_section_visible_profile import ROOT,SeventhSectionVisibleVocabulary,write_once
from scripts import check_einstein_seat_questions_visible as previous
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

SOURCE='examples/v016/einstein-seventh-section-visible-v1.noema'
BRIDGE='data/einstein-seventh-section-visible-bridge-v1.json'
SOURCE_ORDER=[220, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg',
  'sha256': 'e634a38acf3bf76e5d99086296c70a267368c684501148cc789ede1def276ea5',
  'actually_displayed': True,
  'inspection': 'view_image in the tool result paired with shell chunk 38ce7e',
  'independent_human_reading': False,
  'observations': ['第7節見出しのDoppelerschen PrinzipsとAberration、同じ源と局所領域の仮定を確認。',
                   '六成分は同じsin Φ、位相はω(t−(ax+by+cz)/V)。二振幅ベクトルと三方向余弦の説明を確認。']},
 {'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p911-0.jpg',
  'sha256': 'cfeedb92c7118833f305cb7295322d6f405e8b9d299b046038b7cf97acd85fc5',
  'actually_displayed': True,
  'inspection': 'view_image in the tool result paired with shell chunk 38ce7e',
  'independent_human_reading': False,
  'observations': ['u0182の文は前頁末から継続。§6の場と§3の座標時刻変換、unmittelbarを確認。',
                   '変換後六成分の交差項と符号、独立した位相、ω′と三方向の四補足式を確認。',
                   '周期数νと位相率ωを区別し、源から観測者への結線、速度との角、ν′式の根号分母を確認。']},
 {'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg',
  'sha256': '3c4e8e8b3ec6413d97d8ce9cd3f28c404e51abe3871541570b6a78d9dfc91520',
  'actually_displayed': True,
  'inspection': 'view_image in the tool result paired with shell chunk 38ce7e',
  'independent_human_reading': False,
  'observations': ['φ=0のν′式はνを根号の外に置く。印字v=−∞と無印ν=∞を都合よく訂正しない。',
                   'φ′は移動系波面法線と源―観測者結線との角。cosφ′表示とφ=π/2の負比を確認。',
                   'AとA′は同じ電気又は磁気側の振幅。一般二乗比の分母に根号なし、零角特殊式にも根号なし。',
                   '最後の光速接近はnäherte/müßteという仮定的提示。現実の光速観測者の測定へ置換しない。']}]
PUBLIC_RELATIONS={'eisai': 'viewattributescontent',
 'eisrt': 'radiatingsourcesupport',
 'eisru': 'electromagneticradiationsource',
 'eisrv': 'largedistanceratiostandard',
 'eisrw': 'waveapproximationadequacy',
 'eissa': 'forwardwaveforminterpretation',
 'eissb': 'elaboratesattributedsetting',
 'eissd': 'investigateswaveprocess',
 'eisse': 'presentsconditionalfieldquestion',
 'eissg': 'presentssharedsettingderivation',
 'eissk': 'objectconfigurationmodels',
 'eissl': 'radiationphasecorrespondence',
 'eissp': 'perspicuousformassessment',
 'eiss4': 'presentsremainingamplitudequestion',
 'eistb': 'comparativeformperspicuity',
 'eiste': 'energyfluxunitcoefficient',
 'eistf': 'adoptswaveenergyfluxmodel',
 'eisth': 'theoreticalinquirytopic'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['sdl2',
 'sdm2',
 'sdn2',
 'sdo2',
 'sdp2',
 'sdq2',
 'sds2',
 'sdt2',
 'sdu2',
 'sdv2',
 'sdw2',
 'sdx2',
 'sdy2',
 'sdz2',
 'sd24',
 'seag',
 'seah',
 'seai',
 'seaj',
 'seal',
 'sear',
 'seas',
 'seat',
 'ekat',
 'ekau',
 'ekav',
 'ekaw',
 'ekax',
 'ekay',
 'ekaz',
 'ekba',
 'ekbb',
 'ekbc',
 'ekbd',
 'ekbe',
 'ekbf',
 'ekbg',
 'ekbh',
 'ekbi',
 'ekbj',
 'ekbk',
 'ekbl',
 'ekbm',
 'ekbn',
 'ekbo',
 'ekbp',
 'ekbq',
 'ekbr',
 'ekbs',
 'ekbt',
 'ekbu',
 'ekbv',
 'ekca',
 'ekcb',
 'ekcc',
 'ekcd',
 'ekb2',
 'ekb3',
 'ekb4',
 'ekb5',
 'ekb6',
 'ekb7',
 'seau',
 'seav',
 'ekce',
 'ekcf',
 'ekcg',
 'ekch',
 'ekci',
 'ekck',
 'ekcl',
 'ekcn',
 'ekco',
 'ekcp',
 'ekcs',
 'ekcv',
 'ekcq',
 'ekcr',
 'ekct',
 'ekcu',
 'ekcw',
 'ekcx',
 'ekcy',
 'ekcz',
 'ekc2',
 'ekc3',
 'ekc4',
 'ekc5',
 'ekc6',
 'ekc7',
 'ekda',
 'ekdb',
 'ekdc',
 'ekdg',
 'ekdh',
 'ekdi',
 'ekdj',
 'ekdk',
 'ekdl',
 'ekdm',
 'ekdn',
 'ekdp',
 'ekdq',
 'ekdr',
 'ekdv',
 'ekdw',
 'ekdx',
 'ekdy',
 'ekdz',
 'ekd2',
 'ekd3',
 'ekd4',
 'ekd5',
 'ekd6',
 'ekd7',
 'ekea',
 'ekeb',
 'ekec',
 'eked',
 'ekeg',
 'ekee',
 'ekef',
 'ekeh',
 'ekei',
 'ekej',
 'ekek',
 'ekel',
 'ekem',
 'eken',
 'ekeo',
 'ekep',
 'ekeq',
 'eker',
 'ekes',
 'eket',
 'ekeu',
 'ekev',
 'ekew',
 'ekey',
 'ekez',
 'eke2',
 'eke3',
 'eke4',
 'eke5',
 'eke6',
 'eke7',
 'ekfc',
 'ekfa',
 'ekfb',
 'ekfd',
 'ekfe',
 'ekff',
 'ekfg',
 'ekfh',
 'ekfi',
 'ekfj',
 'ekfk',
 'ekfl',
 'ekfm',
 'ekfn',
 'ekfo',
 'ekfp',
 'ekfq',
 'ekfr',
 'ekfs',
 'ekft',
 'ekfu',
 'ekfv',
 'ekfw',
 'ekfx',
 'ekfy',
 'ekga',
 'ekgs',
 'ekgb',
 'ekgc',
 'ekgd',
 'ekge',
 'ekgf',
 'ekgi',
 'ekgn',
 'ekgo',
 'ekgt',
 'ekgu',
 'ekgv',
 'ekgw',
 'ekgx',
 'ekhl',
 'ekgy',
 'ekgz',
 'ekha',
 'ekhb',
 'ekhc',
 'ekhd',
 'ekhe',
 'ekhf',
 'ekhi',
 'ekhg',
 'ekhh',
 'ekhj',
 'ekhk',
 'ekhm',
 'ekhn',
 'ekho',
 'ekhp',
 'ekhq',
 'ekhr',
 'ekhs',
 'ekht',
 'ekhw',
 'ekhu',
 'ekhv',
 'ekhx',
 'ekhy',
 'ekhz',
 'ekia',
 'ekib',
 'ekic',
 'ekid',
 'ekie',
 'ekif',
 'ekig',
 'ekih',
 'ekii',
 'ekij',
 'ekik',
 'ekim',
 'ekin',
 'ekio',
 'ekir',
 'ekip',
 'ekiq',
 'ekis',
 'ekit',
 'ekiu',
 'ekiv',
 'ekiw',
 'ekix',
 'ekiy',
 'ekiz',
 'ekjc',
 'ekja',
 'ekjb',
 'ekjd',
 'ekje',
 'ekjf',
 'ekjg',
 'ekjh',
 'ekjn',
 'ekjo',
 'ekjp',
 'ekjq',
 'ekjr',
 'ekjs',
 'ekjt',
 'ekjy',
 'ekjz',
 'ekka',
 'ekkb',
 'ekkc',
 'ekkd',
 'ekke',
 'ekkf',
 'ekkg',
 'ekkh',
 'ekki',
 'ekkj',
 'ekkk',
 'ekkl',
 'ekkm',
 'ekkn',
 'ekko',
 'ekkp',
 'ekkq',
 'ekkv',
 'ekkr',
 'ekks',
 'ekkt',
 'ekku']
REUSED_BODIES={'seag': 'ejc7'}
FORWARD_MAPS={}
HEADINGS={'eisti': 9}
SENTENCES={'seventhwaveassumption': [81, 1],
 'eissc': [81, 2],
 'eissf': [82, 1],
 'seventhwavetransform': [82, 2],
 'seventhdopplerconsequence': [83, 1],
 'seventhdoppleridentification': [83, 2],
 'seventhdopplerspecialization': [83, 3],
 'eisst': [83, 4],
 'seventhaberrationpresentation': [84, 1],
 'seventhaberrationidentification': [84, 2],
 'seventhaberrationspecialization': [84, 3],
 'seventhamplitudequestion': [85, 1],
 'seventhamplitudepresentation': [85, 2],
 'eistg': [86, 1]}
TEXT_SENTENCES={'seventhwaveassumption': 'Im Systeme [M0319] befinde sich sehr ferne vom Koordinatenursprung eine Quelle '
                          'elektrodynamischer Wellen, welche in einem den Koordinatenursprung enthaltenden '
                          'Raumteil mit genügender Annäherung durch die Gleichungen dargestellt sei: [M0320]',
 'eissc': 'Hierbei sind ([M0321]) und ([M0322]) die Vektoren, welche die Amplitude des Wellenzuges '
          'bestimmen, [M0323] die Richtungskosinus der Wellennormalen.',
 'eissf': 'Wir fragen nach der Beschaffenheit dieser Wellen, wenn dieselben von einem in dem bewegten System '
          '[M0324] ruhenden Beobachter untersucht werden.',
 'seventhwavetransform': '— Durch Anwendung der in § 6 gefundenen Transformationsgleichungen für die '
                         'elektrischen und magnetischen Kräfte und der in § 3 gefundenen '
                         'Transformationsgleichungen für die Koordinaten und die Zeit erhalten wir '
                         'unmittelbar: [M0325] [M0326], wobei [M0327] gesetzt ist.',
 'seventhdopplerconsequence': 'Aus der Gleichung für [M0328] folgt: Ist ein Beobachter relativ zu einer '
                              'unendlich fernen Lichtquelle von der Frequenz [M0329] mit der Geschwindigkeit '
                              '[M0330] derart bewegt, daß die Verbindungslinie „Lichtquelle-Beobachter“ mit '
                              'der auf ein relativ zur Lichtquelle ruhendes Koordinatensystem bezogenen '
                              'Geschwindigkeit des Beobachters den Winkel [M0331] bildet, so ist die von dem '
                              'Beobachter wahrgenommene Frequenz [M0332] des Lichtes durch die Gleichung '
                              'gegeben: [M0333]',
 'seventhdoppleridentification': 'Dies ist das Doppelersche Prinzip für beliebige Geschwindigkeiten.',
 'seventhdopplerspecialization': 'Für [M0334] nimmt die Gleichung die übersichtliche Form an: [M0335]',
 'eisst': 'Man sieht, daß — im Gegensatz zu der üblichen Auffassung — für [M0336], [M0337] ist.',
 'seventhaberrationpresentation': 'Nennt man [M0338] den Winkel zwischen Wellennormale (Strahlrichtung) im '
                                  'bewegten System und der Verbindungslinie „Lichtquelle-Beobachter“, so '
                                  'nimmt die Gleichung für [M0339] die Form an: [M0340]',
 'seventhaberrationidentification': 'Diese Gleichung drückt das Aberrationsgesetz in seiner allgemeinsten '
                                    'Form aus.',
 'seventhaberrationspecialization': 'Ist [M0341], so nimmt die Gleichung die einfache Gestalt an: [M0342]',
 'seventhamplitudequestion': 'Wir haben nun noch die Amplitude der Wellen, wie dieselbe im bewegten System '
                             'erscheint, zu suchen.',
 'seventhamplitudepresentation': 'Nennt man [M0343] bez. [M0344] die Amplitude der elektrischen oder '
                                 'magnetischen Kraft im ruhenden bez. im bewegten System gemessen, so erhält '
                                 'man: [M0345] welche Gleichung für [M0346] in die einfachere übergeht: '
                                 '[M0347]',
 'eistg': 'Es folgt aus den entwickelten Gleichungen, daß für einen Beobachter, der sich mit der '
          'Geschwindigkeit [M0348] einer Lichtquelle näherte, diese Lichtquelle unendlich intensiv '
          'erscheinen müßte.'}
SPANS={'eisry': ['seventhwaveassumption', 1, 'seventhwaveassumption', 28],
 'eisrz': ['seventhwaveassumption', 29, 'seventhwaveassumption', 29],
 'eissh': ['seventhwavetransform', 2, 'seventhwavetransform', 31],
 'eissi': ['seventhwavetransform', 32, 'seventhwavetransform', 33],
 'eissj': ['seventhwavetransform', 34, 'seventhwavetransform', 37],
 'seventhparametersanchor': ['seventhwavetransform', 35, 'seventhwavetransform', 35],
 'eissm': ['seventhdopplerconsequence', 1, 'seventhdopplerconsequence', 61],
 'eissn': ['seventhdopplerconsequence', 62, 'seventhdopplerconsequence', 62],
 'eissr': ['seventhdopplerspecialization', 10, 'seventhdopplerspecialization', 10],
 'eissu': ['eisst', 5, 'eisst', 10],
 'eissv': ['seventhaberrationpresentation', 1, 'seventhaberrationpresentation', 24],
 'eissw': ['seventhaberrationpresentation', 25, 'seventhaberrationpresentation', 25],
 'eiss2': ['seventhaberrationspecialization', 11, 'seventhaberrationspecialization', 11],
 'eiss6': ['seventhamplitudepresentation', 23, 'seventhamplitudepresentation', 23],
 'eistc': ['seventhamplitudepresentation', 24, 'seventhamplitudepresentation', 31],
 'eistd': ['seventhamplitudepresentation', 32, 'seventhamplitudepresentation', 32],
 'eissq': ['seventhdoppleridentification', 1, 'seventhdopplerspecialization', 9],
 'eissz': ['seventhaberrationidentification', 1, 'seventhaberrationspecialization', 10],
 'eiss5': ['seventhamplitudequestion', 1, 'seventhamplitudepresentation', 22]}
MULTI_SPANS={}
TOKEN_COUNTS={'seventhwaveassumption': 29,
 'eissc': 18,
 'eissf': 20,
 'seventhwavetransform': 37,
 'seventhdopplerconsequence': 62,
 'seventhdoppleridentification': 8,
 'seventhdopplerspecialization': 10,
 'eisst': 15,
 'seventhaberrationpresentation': 25,
 'seventhaberrationidentification': 10,
 'seventhaberrationspecialization': 11,
 'seventhamplitudequestion': 16,
 'seventhamplitudepresentation': 32,
 'eistg': 25}
TOKENS={'seventhwaveassumption': ['Im',
                           'Systeme',
                           '[M0319]',
                           'befinde',
                           'sich',
                           'sehr',
                           'ferne',
                           'vom',
                           'Koordinatenursprung',
                           'eine',
                           'Quelle',
                           'elektrodynamischer',
                           'Wellen,',
                           'welche',
                           'in',
                           'einem',
                           'den',
                           'Koordinatenursprung',
                           'enthaltenden',
                           'Raumteil',
                           'mit',
                           'genügender',
                           'Annäherung',
                           'durch',
                           'die',
                           'Gleichungen',
                           'dargestellt',
                           'sei:',
                           '[M0320]'],
 'eissc': ['Hierbei',
           'sind',
           '([M0321])',
           'und',
           '([M0322])',
           'die',
           'Vektoren,',
           'welche',
           'die',
           'Amplitude',
           'des',
           'Wellenzuges',
           'bestimmen,',
           '[M0323]',
           'die',
           'Richtungskosinus',
           'der',
           'Wellennormalen.'],
 'eissf': ['Wir',
           'fragen',
           'nach',
           'der',
           'Beschaffenheit',
           'dieser',
           'Wellen,',
           'wenn',
           'dieselben',
           'von',
           'einem',
           'in',
           'dem',
           'bewegten',
           'System',
           '[M0324]',
           'ruhenden',
           'Beobachter',
           'untersucht',
           'werden.'],
 'seventhwavetransform': ['—',
                          'Durch',
                          'Anwendung',
                          'der',
                          'in',
                          '§',
                          '6',
                          'gefundenen',
                          'Transformationsgleichungen',
                          'für',
                          'die',
                          'elektrischen',
                          'und',
                          'magnetischen',
                          'Kräfte',
                          'und',
                          'der',
                          'in',
                          '§',
                          '3',
                          'gefundenen',
                          'Transformationsgleichungen',
                          'für',
                          'die',
                          'Koordinaten',
                          'und',
                          'die',
                          'Zeit',
                          'erhalten',
                          'wir',
                          'unmittelbar:',
                          '[M0325]',
                          '[M0326],',
                          'wobei',
                          '[M0327]',
                          'gesetzt',
                          'ist.'],
 'seventhdopplerconsequence': ['Aus',
                               'der',
                               'Gleichung',
                               'für',
                               '[M0328]',
                               'folgt:',
                               'Ist',
                               'ein',
                               'Beobachter',
                               'relativ',
                               'zu',
                               'einer',
                               'unendlich',
                               'fernen',
                               'Lichtquelle',
                               'von',
                               'der',
                               'Frequenz',
                               '[M0329]',
                               'mit',
                               'der',
                               'Geschwindigkeit',
                               '[M0330]',
                               'derart',
                               'bewegt,',
                               'daß',
                               'die',
                               'Verbindungslinie',
                               '„Lichtquelle-Beobachter“',
                               'mit',
                               'der',
                               'auf',
                               'ein',
                               'relativ',
                               'zur',
                               'Lichtquelle',
                               'ruhendes',
                               'Koordinatensystem',
                               'bezogenen',
                               'Geschwindigkeit',
                               'des',
                               'Beobachters',
                               'den',
                               'Winkel',
                               '[M0331]',
                               'bildet,',
                               'so',
                               'ist',
                               'die',
                               'von',
                               'dem',
                               'Beobachter',
                               'wahrgenommene',
                               'Frequenz',
                               '[M0332]',
                               'des',
                               'Lichtes',
                               'durch',
                               'die',
                               'Gleichung',
                               'gegeben:',
                               '[M0333]'],
 'seventhdoppleridentification': ['Dies',
                                  'ist',
                                  'das',
                                  'Doppelersche',
                                  'Prinzip',
                                  'für',
                                  'beliebige',
                                  'Geschwindigkeiten.'],
 'seventhdopplerspecialization': ['Für',
                                  '[M0334]',
                                  'nimmt',
                                  'die',
                                  'Gleichung',
                                  'die',
                                  'übersichtliche',
                                  'Form',
                                  'an:',
                                  '[M0335]'],
 'eisst': ['Man',
           'sieht,',
           'daß',
           '—',
           'im',
           'Gegensatz',
           'zu',
           'der',
           'üblichen',
           'Auffassung',
           '—',
           'für',
           '[M0336],',
           '[M0337]',
           'ist.'],
 'seventhaberrationpresentation': ['Nennt',
                                   'man',
                                   '[M0338]',
                                   'den',
                                   'Winkel',
                                   'zwischen',
                                   'Wellennormale',
                                   '(Strahlrichtung)',
                                   'im',
                                   'bewegten',
                                   'System',
                                   'und',
                                   'der',
                                   'Verbindungslinie',
                                   '„Lichtquelle-Beobachter“,',
                                   'so',
                                   'nimmt',
                                   'die',
                                   'Gleichung',
                                   'für',
                                   '[M0339]',
                                   'die',
                                   'Form',
                                   'an:',
                                   '[M0340]'],
 'seventhaberrationidentification': ['Diese',
                                     'Gleichung',
                                     'drückt',
                                     'das',
                                     'Aberrationsgesetz',
                                     'in',
                                     'seiner',
                                     'allgemeinsten',
                                     'Form',
                                     'aus.'],
 'seventhaberrationspecialization': ['Ist',
                                     '[M0341],',
                                     'so',
                                     'nimmt',
                                     'die',
                                     'Gleichung',
                                     'die',
                                     'einfache',
                                     'Gestalt',
                                     'an:',
                                     '[M0342]'],
 'seventhamplitudequestion': ['Wir',
                              'haben',
                              'nun',
                              'noch',
                              'die',
                              'Amplitude',
                              'der',
                              'Wellen,',
                              'wie',
                              'dieselbe',
                              'im',
                              'bewegten',
                              'System',
                              'erscheint,',
                              'zu',
                              'suchen.'],
 'seventhamplitudepresentation': ['Nennt',
                                  'man',
                                  '[M0343]',
                                  'bez.',
                                  '[M0344]',
                                  'die',
                                  'Amplitude',
                                  'der',
                                  'elektrischen',
                                  'oder',
                                  'magnetischen',
                                  'Kraft',
                                  'im',
                                  'ruhenden',
                                  'bez.',
                                  'im',
                                  'bewegten',
                                  'System',
                                  'gemessen,',
                                  'so',
                                  'erhält',
                                  'man:',
                                  '[M0345]',
                                  'welche',
                                  'Gleichung',
                                  'für',
                                  '[M0346]',
                                  'in',
                                  'die',
                                  'einfachere',
                                  'übergeht:',
                                  '[M0347]'],
 'eistg': ['Es',
           'folgt',
           'aus',
           'den',
           'entwickelten',
           'Gleichungen,',
           'daß',
           'für',
           'einen',
           'Beobachter,',
           'der',
           'sich',
           'mit',
           'der',
           'Geschwindigkeit',
           '[M0348]',
           'einer',
           'Lichtquelle',
           'näherte,',
           'diese',
           'Lichtquelle',
           'unendlich',
           'intensiv',
           'erscheinen',
           'müßte.']}
DESIGNATIONS={'eisss': ['seventhdoppleridentification', 1],
 'eissx': ['eissv', 1],
 'eiss3': ['seventhaberrationidentification', 1],
 'eiss7': ['eiss5', 1],
 'eista': ['eiss5', 2]}
FORMS={'eisss': 'Doppelersche Prinzip',
 'eissx': 'φ′',
 'eiss3': 'Aberrationsgesetz',
 'eiss7': 'A',
 'eista': 'A′',
 'ekkv': 'Doppelerschen Prinzips'}
ROLE_ASSIGNMENTS={'eisrx': 'seventhsectionrole', 'eisso': 'seventhphaserateitemrole', 'eissy': 'seventhaxialitemrole'}
REFERENCE_SORTS={'eisrx': 'individual', 'eisso': 'individual', 'eissy': 'individual'}
REFERENCE_ANCHORS={'eisrx': 'eisti', 'eisso': 'seventhparametersanchor', 'eissy': 'seventhparametersanchor'}
SOURCE_UNITS={'einstein-1905:u0178': {'text': '§ 7. Theorie des Doppelerschen Prinzips und der Aberration.',
                         'sha256': '63b2608e5c43c7c9daca8325827c5ed2d2d543146b8f9e157feb1d763ff2b88e'},
 'einstein-1905:u0179': {'text': 'Im Systeme [M0319] befinde sich sehr ferne vom Koordinatenursprung eine '
                                 'Quelle elektrodynamischer Wellen, welche in einem den Koordinatenursprung '
                                 'enthaltenden Raumteil mit genügender Annäherung durch die Gleichungen '
                                 'dargestellt sei:',
                         'sha256': 'b255b74ba1b775dab4f36272c786aeace4f9079d93c64664c6a90e010120b057'},
 'einstein-1905:u0180': {'text': '[M0320]',
                         'sha256': '8831b5a9bb8d1a7666c851e616c7fc84503e4638bf35cf196c231ab5a3399696'},
 'einstein-1905:u0181': {'text': 'Hierbei sind ([M0321]) und ([M0322]) die Vektoren, welche die Amplitude '
                                 'des Wellenzuges bestimmen, [M0323] die Richtungskosinus der '
                                 'Wellennormalen.',
                         'sha256': '7a186d621c0e1c150815f1e19d8a5bd2c45a2438760572c73f48e27523124137'},
 'einstein-1905:u0182': {'text': 'Wir fragen nach der Beschaffenheit dieser Wellen, wenn dieselben von einem '
                                 'in dem bewegten System [M0324] ruhenden Beobachter untersucht werden. — '
                                 'Durch Anwendung der in § 6 gefundenen Transformationsgleichungen für die '
                                 'elektrischen und magnetischen Kräfte und der in § 3 gefundenen '
                                 'Transformationsgleichungen für die Koordinaten und die Zeit erhalten wir '
                                 'unmittelbar:',
                         'sha256': '55ae3d9e8635fb5816468e0fe840ba8715fc39df25c47701be352d250a2db523'},
 'einstein-1905:u0183': {'text': '[M0325]',
                         'sha256': '8bd565c638bb42d23c5ef743cf12312d361c4a4d7a1c887fa9f0200e88864d72'},
 'einstein-1905:u0184': {'text': '[M0326],',
                         'sha256': 'e2676076639faf48e63dd3f1e3a7dbb733f6fcbd9b130bfdd74a7157b16b68da'},
 'einstein-1905:u0185': {'text': 'wobei',
                         'sha256': 'ad6f70890a12d8f25cf83a9ebb72fac6316cf86f4e2e27c3ef03027f2b994c84'},
 'einstein-1905:u0186': {'text': '[M0327]',
                         'sha256': '574e67d429cccbc4a33164a6f244b7c7d1c7e4352fc8e14e26cc132ef1dba304'},
 'einstein-1905:u0187': {'text': 'gesetzt ist.',
                         'sha256': '0273298e96a203904bfefc2e9ebf4e5d88e985c5465dfc63391b6d009fa8fc36'},
 'einstein-1905:u0188': {'text': 'Aus der Gleichung für [M0328] folgt: Ist ein Beobachter relativ zu einer '
                                 'unendlich fernen Lichtquelle von der Frequenz [M0329] mit der '
                                 'Geschwindigkeit [M0330] derart bewegt, daß die Verbindungslinie '
                                 '„Lichtquelle-Beobachter“ mit der auf ein relativ zur Lichtquelle ruhendes '
                                 'Koordinatensystem bezogenen Geschwindigkeit des Beobachters den Winkel '
                                 '[M0331] bildet, so ist die von dem Beobachter wahrgenommene Frequenz '
                                 '[M0332] des Lichtes durch die Gleichung gegeben:',
                         'sha256': '8c8471cbc78827adde0ef6b73b35511b110fa9051493e50674181fe3b3960510'},
 'einstein-1905:u0189': {'text': '[M0333]',
                         'sha256': 'd03f5fa205bb03cb337d5fcd96d1961cc48d6be7cd0eeb7f387736615467575b'},
 'einstein-1905:u0190': {'text': 'Dies ist das Doppelersche Prinzip für beliebige Geschwindigkeiten. Für '
                                 '[M0334] nimmt die Gleichung die übersichtliche Form an:',
                         'sha256': '1bcf98a335439cb475a34077dc84a9aa1bf677f71f91b08062a91de6ea07ebe3'},
 'einstein-1905:u0191': {'text': '[M0335]',
                         'sha256': '05d9fe933235931251d9e2585b92057c861b48758621f80e4e170edb55e5c974'},
 'einstein-1905:u0192': {'text': 'Man sieht, daß — im Gegensatz zu der üblichen Auffassung — für [M0336], '
                                 '[M0337] ist.',
                         'sha256': '0b9cf1f13fc9d16fd2469831e6912eeea9467e59bfd789beea9f7db7781c9939'},
 'einstein-1905:u0193': {'text': 'Nennt man [M0338] den Winkel zwischen Wellennormale (Strahlrichtung) im '
                                 'bewegten System und der Verbindungslinie „Lichtquelle-Beobachter“, so '
                                 'nimmt die Gleichung für [M0339] die Form an:',
                         'sha256': '14f4d9a17e07c9a84f4a1fd6af4dd6926d5f3eb6889e4e025bc5d8d95562a74f'},
 'einstein-1905:u0194': {'text': '[M0340]',
                         'sha256': 'fba54e2ee85f3f1d94d93bbe1cee812f216f05c2f036a1ed4e4b7e075a1857aa'},
 'einstein-1905:u0195': {'text': 'Diese Gleichung drückt das Aberrationsgesetz in seiner allgemeinsten Form '
                                 'aus. Ist [M0341], so nimmt die Gleichung die einfache Gestalt an:',
                         'sha256': 'c741d5ba72952619b7c0821f4cf5013b60e63c56c99054b40a2eccfffcee62ca'},
 'einstein-1905:u0196': {'text': '[M0342]',
                         'sha256': 'cc6df068b6c89f42e559144e7141433419dd0913749b8582467947592355e354'},
 'einstein-1905:u0197': {'text': 'Wir haben nun noch die Amplitude der Wellen, wie dieselbe im bewegten '
                                 'System erscheint, zu suchen. Nennt man [M0343] bez. [M0344] die Amplitude '
                                 'der elektrischen oder magnetischen Kraft im ruhenden bez. im bewegten '
                                 'System gemessen, so erhält man:',
                         'sha256': '9b5c1b2fcaedff2b07ba1a34975f42814d1c35507a1bbd7d1cc2930f33f70157'},
 'einstein-1905:u0198': {'text': '[M0345]',
                         'sha256': 'bfabd833618dd7d9593e439b438b6e1da238eaad1b2b1762e3408fddca0e2f2a'},
 'einstein-1905:u0199': {'text': 'welche Gleichung für [M0346] in die einfachere übergeht:',
                         'sha256': '79300caf4a55ddfc44a9342b942cb7c0ff5471d5d3c75a698e113292a70b5303'},
 'einstein-1905:u0200': {'text': '[M0347]',
                         'sha256': '6a19e3533ab4a2bc61ca75cff509314c1254233000106c2cebd863f3129464b2'},
 'einstein-1905:u0201': {'text': 'Es folgt aus den entwickelten Gleichungen, daß für einen Beobachter, der '
                                 'sich mit der Geschwindigkeit [M0348] einer Lichtquelle näherte, diese '
                                 'Lichtquelle unendlich intensiv erscheinen müßte.',
                         'sha256': 'b9882c5ed573aa9a4c413b74870eab4958a3a13ceb047b248ac4b94816861f42'},
 'einstein-1905:u0202': {'text': '§ 8. Transformation der Energie der Lichtstrahlen. Theorie des auf '
                                 'vollkommene Spiegel ausgeübten Strahlungsdruckes.',
                         'sha256': '50e6edc5cb6ffe261788e6c9a7164ced4b0f51e4e789c3c3ef544507d0a19263'}}
BOUNDARY_RULE=('原刊の字下げに従い本文81..86段落。Hierbei/Dies/Für/Man '
 'sieht/Diese/Ist/welcheは直前段落の継続。数式内の終止符を文末とし、コロン・wobei・bez.では分割しない。式全体は既存規約の一トークン。ダッシュは82段落第2文の先頭に保持し、Durchからの参照は除外する。')
REVIEWS=('data/einstein-seventh-section-heading-u0178-review-v1.json',
 'data/einstein-distant-wave-source-u0179-review-v1.json',
 'data/einstein-wave-display-u0180-review-v1.json',
 'data/einstein-wave-display-u0181-review-v1.json',
 'data/einstein-wave-transform-u0182-review-v1.json',
 'data/einstein-wave-transform-u0183-review-v1.json',
 'data/einstein-wave-transform-u0184-review-v1.json',
 'data/einstein-wave-transform-u0185-review-v1.json',
 'data/einstein-wave-transform-u0186-review-v1.json',
 'data/einstein-wave-transform-u0187-review-v1.json',
 'data/einstein-observed-doppler-u0188-review-v1.json',
 'data/einstein-observed-doppler-u0189-review-v1.json',
 'data/einstein-doppler-specialization-u0190-review-v1.json',
 'data/einstein-doppler-specialization-u0191-review-v1.json',
 'data/einstein-doppler-infinity-u0192-review-v1.json',
 'data/einstein-aberration-presentation-u0193-review-v1.json',
 'data/einstein-aberration-presentation-u0194-review-v1.json',
 'data/einstein-aberration-specialization-u0195-review-v1.json',
 'data/einstein-aberration-specialization-u0196-review-v1.json',
 'data/einstein-observed-amplitude-u0197-review-v1.json',
 'data/einstein-observed-amplitude-u0198-review-v1.json',
 'data/einstein-amplitude-specialization-u0199-review-v1.json',
 'data/einstein-amplitude-specialization-u0200-review-v1.json',
 'data/einstein-observed-intensity-u0201-review-v1.json')
REVIEW_SELECTION=[{'unit': 'einstein-1905:u0178',
  'review': 'data/einstein-seventh-section-heading-u0178-review-v1.json',
  'statements': [220]},
 {'unit': 'einstein-1905:u0179',
  'review': 'data/einstein-distant-wave-source-u0179-review-v1.json',
  'statements': [199]},
 {'unit': 'einstein-1905:u0180',
  'review': 'data/einstein-wave-display-u0180-review-v1.json',
  'statements': [200]},
 {'unit': 'einstein-1905:u0181',
  'review': 'data/einstein-wave-display-u0181-review-v1.json',
  'statements': [201]},
 {'unit': 'einstein-1905:u0182',
  'review': 'data/einstein-wave-transform-u0182-review-v1.json',
  'statements': [202, 203]},
 {'unit': 'einstein-1905:u0183',
  'review': 'data/einstein-wave-transform-u0183-review-v1.json',
  'statements': [204]},
 {'unit': 'einstein-1905:u0184',
  'review': 'data/einstein-wave-transform-u0184-review-v1.json',
  'statements': [204]},
 {'unit': 'einstein-1905:u0185',
  'review': 'data/einstein-wave-transform-u0185-review-v1.json',
  'statements': [205]},
 {'unit': 'einstein-1905:u0186',
  'review': 'data/einstein-wave-transform-u0186-review-v1.json',
  'statements': [205]},
 {'unit': 'einstein-1905:u0187',
  'review': 'data/einstein-wave-transform-u0187-review-v1.json',
  'statements': [205]},
 {'unit': 'einstein-1905:u0188',
  'review': 'data/einstein-observed-doppler-u0188-review-v1.json',
  'statements': [206]},
 {'unit': 'einstein-1905:u0189',
  'review': 'data/einstein-observed-doppler-u0189-review-v1.json',
  'statements': [207]},
 {'unit': 'einstein-1905:u0190',
  'review': 'data/einstein-doppler-specialization-u0190-review-v1.json',
  'statements': [208]},
 {'unit': 'einstein-1905:u0191',
  'review': 'data/einstein-doppler-specialization-u0191-review-v1.json',
  'statements': [209]},
 {'unit': 'einstein-1905:u0192',
  'review': 'data/einstein-doppler-infinity-u0192-review-v1.json',
  'statements': [210]},
 {'unit': 'einstein-1905:u0193',
  'review': 'data/einstein-aberration-presentation-u0193-review-v1.json',
  'statements': [211]},
 {'unit': 'einstein-1905:u0194',
  'review': 'data/einstein-aberration-presentation-u0194-review-v1.json',
  'statements': [212]},
 {'unit': 'einstein-1905:u0195',
  'review': 'data/einstein-aberration-specialization-u0195-review-v1.json',
  'statements': [213]},
 {'unit': 'einstein-1905:u0196',
  'review': 'data/einstein-aberration-specialization-u0196-review-v1.json',
  'statements': [214]},
 {'unit': 'einstein-1905:u0197',
  'review': 'data/einstein-observed-amplitude-u0197-review-v1.json',
  'statements': [215]},
 {'unit': 'einstein-1905:u0198',
  'review': 'data/einstein-observed-amplitude-u0198-review-v1.json',
  'statements': [216]},
 {'unit': 'einstein-1905:u0199',
  'review': 'data/einstein-amplitude-specialization-u0199-review-v1.json',
  'statements': [217]},
 {'unit': 'einstein-1905:u0200',
  'review': 'data/einstein-amplitude-specialization-u0200-review-v1.json',
  'statements': [218]},
 {'unit': 'einstein-1905:u0201',
  'review': 'data/einstein-observed-intensity-u0201-review-v1.json',
  'statements': [219]}]
READINGS=('data/wave-amplitudes-facsimile-v1.json',
 'docs/seventh-section-heading-v1.md',
 'docs/distant-wave-source-v1.md',
 'docs/wave-display-v1.md',
 'docs/wave-observer-question-v1.md',
 'docs/wave-transform-application-v1.md',
 'docs/observed-doppler-v1.md',
 'docs/doppler-specialization-v1.md',
 'docs/doppler-infinity-v1.md',
 'docs/aberration-presentation-v1.md',
 'docs/aberration-specialization-v1.md',
 'docs/observed-amplitude-v1.md',
 'docs/amplitude-specialization-v1.md',
 'docs/observed-intensity-v1.md',
 'data/einstein-seventh-section-heading-u0178-review-v1.json',
 'data/einstein-distant-wave-source-u0179-review-v1.json',
 'data/einstein-wave-display-u0180-review-v1.json',
 'data/einstein-wave-display-u0181-review-v1.json',
 'data/einstein-wave-transform-u0182-review-v1.json',
 'data/einstein-wave-transform-u0183-review-v1.json',
 'data/einstein-wave-transform-u0184-review-v1.json',
 'data/einstein-wave-transform-u0185-review-v1.json',
 'data/einstein-wave-transform-u0186-review-v1.json',
 'data/einstein-wave-transform-u0187-review-v1.json',
 'data/einstein-observed-doppler-u0188-review-v1.json',
 'data/einstein-observed-doppler-u0189-review-v1.json',
 'data/einstein-doppler-specialization-u0190-review-v1.json',
 'data/einstein-doppler-specialization-u0191-review-v1.json',
 'data/einstein-doppler-infinity-u0192-review-v1.json',
 'data/einstein-aberration-presentation-u0193-review-v1.json',
 'data/einstein-aberration-presentation-u0194-review-v1.json',
 'data/einstein-aberration-specialization-u0195-review-v1.json',
 'data/einstein-aberration-specialization-u0196-review-v1.json',
 'data/einstein-observed-amplitude-u0197-review-v1.json',
 'data/einstein-observed-amplitude-u0198-review-v1.json',
 'data/einstein-amplitude-specialization-u0199-review-v1.json',
 'data/einstein-amplitude-specialization-u0200-review-v1.json',
 'data/einstein-observed-intensity-u0201-review-v1.json',
 'artifacts/written-units-v1/einstein-1905.json')
SEMANTIC_REVIEW=['同じ研究でDopplerと光行差を連言し、設定と定式化を別々に引用する。節7は第二部に属しu0178..u0201、次節直前で閉じる。',
 '遠さは全関連源位置と局所領域の尺度に対する条件。物理的源、場の校正、全領域の誤差、用途上の十分性を分ける。源の静止・一点性・真空・横波を先行仮定へ加えない。',
 '七表示式と二振幅ベクトル、同時刻等位相面の法線を同じ設定へ接続。実際の二場と近似表現場を混同せず、誤差を零にしない。',
 '観測者は移動系で全観測区間に静止し、同じ波の物理的二場を答えとする。候補の外で先行割当を固定する。問いは答えの存在・既知性・実測済みを含意しない。',
 '§6/§3の変換は同じ出来事・同じ波に適用し、旧領域と逆像新領域を保持。immediateは直接代入・式整理の著者帰属であり、計算時間や機械証明ではない。',
 '放射/受信位相と対象モデル族を同じ源・波・過程・単位へ結ぶ。ω/ν/周期を区別。速度一般化は物理設定まで同じ速度を伝達し0<v<Vを保持。',
 'u0192の採用読解v→−∞、放射ν→∞を保持。先行適用域との不整合を隠さず、空関係で発散を満たさない。',
 '光行差の結線読解を保持し、V=5,v=3で実角余弦4/5と印刷式−3/5の不一致を残す。表示の成立を命名の条件へ混ぜない。',
 '振幅は同じ電気又は磁気側の三係数ノルム。一般二乗比は原刊通り根号なし。非横波反例を隠す前件の追加をしない。',
 '簡明な形の単独評価と、より簡明という方向付き比較を分ける。同値性・真理・全読者の心理を自動認定しない。',
 '強度では局所真空横波の採用読解とエネルギー流の単位/物理的役割を明示し、先行振幅文へ遡及しない。正の入射流、固定背景、各速度での代替状況、v→V−の非空な接近と全出力の発散を保持。',
 '有限束縛診断では各slotを二値等の識別可能な域で動かし、他の証人を固定。Native本体確認と有限モデル診断を分け、全実数/全関数の証明とはしない。']
ROLE_DEFINITIONS={'eisrx': {'kind': 'definition',
           'name': 'seventhsectionrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'and',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisdv',
                                   'arguments': [{'kind': 'call', 'symbol': 'eisti', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'call', 'symbol': 'eispb', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                                 {'kind': 'number', 'numerator': 2, 'denominator': 1},
                                                 {'kind': 'number', 'numerator': 7, 'denominator': 1},
                                                 {'kind': 'variable', 'name': 'vb'}]},
                                  {'kind': 'not',
                                   'arguments': [{'kind': 'equal',
                                                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                                                {'kind': 'call',
                                                                 'symbol': 'eispb',
                                                                 'arguments': []}]}]}]}},
 'eisso': {'kind': 'definition',
           'name': 'seventhphaserateitemrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisox',
                    'arguments': [{'kind': 'variable', 'name': 'va'},
                                  {'kind': 'quote',
                                   'body': {'kind': 'call', 'symbol': 'ekec', 'arguments': []}},
                                  {'kind': 'variable', 'name': 'vb'}]}},
 'eissy': {'kind': 'definition',
           'name': 'seventhaxialitemrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisox',
                    'arguments': [{'kind': 'variable', 'name': 'va'},
                                  {'kind': 'quote',
                                   'body': {'kind': 'call', 'symbol': 'ekhb', 'arguments': []}},
                                  {'kind': 'variable', 'name': 'vb'}]}}}
LOCAL_NAMES=['eisti',
 'seventhwaveassumption',
 'eissc',
 'eissf',
 'seventhwavetransform',
 'seventhdopplerconsequence',
 'seventhdoppleridentification',
 'seventhdopplerspecialization',
 'eisst',
 'seventhaberrationpresentation',
 'seventhaberrationidentification',
 'seventhaberrationspecialization',
 'seventhamplitudequestion',
 'seventhamplitudepresentation',
 'eistg',
 'eisry',
 'eisrz',
 'eissh',
 'eissi',
 'eissj',
 'seventhparametersanchor',
 'eissm',
 'eissn',
 'eissr',
 'eissu',
 'eissv',
 'eissw',
 'eiss2',
 'eiss6',
 'eistc',
 'eistd',
 'eissq',
 'eissz',
 'eiss5',
 'eisss',
 'eissx',
 'eiss3',
 'eiss7',
 'eista',
 'eisrx',
 'eisso',
 'eissy',
 'seventhsectionrole',
 'seventhphaserateitemrole',
 'seventhaxialitemrole',
 'sdl2',
 'sdm2',
 'sdn2',
 'sdo2',
 'sdp2',
 'sdq2',
 'sds2',
 'sdt2',
 'sdu2',
 'sdv2',
 'sdw2',
 'sdx2',
 'sdy2',
 'sdz2',
 'sd24',
 'seag',
 'seah',
 'seai',
 'seaj',
 'seal',
 'sear',
 'seas',
 'seat',
 'ekat',
 'ekau',
 'ekav',
 'ekaw',
 'ekax',
 'ekay',
 'ekaz',
 'ekba',
 'ekbb',
 'ekbc',
 'ekbd',
 'ekbe',
 'ekbf',
 'ekbg',
 'ekbh',
 'ekbi',
 'ekbj',
 'ekbk',
 'ekbl',
 'ekbm',
 'ekbn',
 'ekbo',
 'ekbp',
 'ekbq',
 'ekbr',
 'ekbs',
 'ekbt',
 'ekbu',
 'ekbv',
 'ekca',
 'ekcb',
 'ekcc',
 'ekcd',
 'ekb2',
 'ekb3',
 'ekb4',
 'ekb5',
 'ekb6',
 'ekb7',
 'seau',
 'seav',
 'ekce',
 'ekcf',
 'ekcg',
 'ekch',
 'ekci',
 'ekck',
 'ekcl',
 'ekcn',
 'ekco',
 'ekcp',
 'ekcs',
 'ekcv',
 'ekcq',
 'ekcr',
 'ekct',
 'ekcu',
 'ekcw',
 'ekcx',
 'ekcy',
 'ekcz',
 'ekc2',
 'ekc3',
 'ekc4',
 'ekc5',
 'ekc6',
 'ekc7',
 'ekda',
 'ekdb',
 'ekdc',
 'ekdg',
 'ekdh',
 'ekdi',
 'ekdj',
 'ekdk',
 'ekdl',
 'ekdm',
 'ekdn',
 'ekdp',
 'ekdq',
 'ekdr',
 'ekdv',
 'ekdw',
 'ekdx',
 'ekdy',
 'ekdz',
 'ekd2',
 'ekd3',
 'ekd4',
 'ekd5',
 'ekd6',
 'ekd7',
 'ekea',
 'ekeb',
 'ekec',
 'eked',
 'ekeg',
 'ekee',
 'ekef',
 'ekeh',
 'ekei',
 'ekej',
 'ekek',
 'ekel',
 'ekem',
 'eken',
 'ekeo',
 'ekep',
 'ekeq',
 'eker',
 'ekes',
 'eket',
 'ekeu',
 'ekev',
 'ekew',
 'ekey',
 'ekez',
 'eke2',
 'eke3',
 'eke4',
 'eke5',
 'eke6',
 'eke7',
 'ekfc',
 'ekfa',
 'ekfb',
 'ekfd',
 'ekfe',
 'ekff',
 'ekfg',
 'ekfh',
 'ekfi',
 'ekfj',
 'ekfk',
 'ekfl',
 'ekfm',
 'ekfn',
 'ekfo',
 'ekfp',
 'ekfq',
 'ekfr',
 'ekfs',
 'ekft',
 'ekfu',
 'ekfv',
 'ekfw',
 'ekfx',
 'ekfy',
 'ekga',
 'ekgs',
 'ekgb',
 'ekgc',
 'ekgd',
 'ekge',
 'ekgf',
 'ekgi',
 'ekgn',
 'ekgo',
 'ekgt',
 'ekgu',
 'ekgv',
 'ekgw',
 'ekgx',
 'ekhl',
 'ekgy',
 'ekgz',
 'ekha',
 'ekhb',
 'ekhc',
 'ekhd',
 'ekhe',
 'ekhf',
 'ekhi',
 'ekhg',
 'ekhh',
 'ekhj',
 'ekhk',
 'ekhm',
 'ekhn',
 'ekho',
 'ekhp',
 'ekhq',
 'ekhr',
 'ekhs',
 'ekht',
 'ekhw',
 'ekhu',
 'ekhv',
 'ekhx',
 'ekhy',
 'ekhz',
 'ekia',
 'ekib',
 'ekic',
 'ekid',
 'ekie',
 'ekif',
 'ekig',
 'ekih',
 'ekii',
 'ekij',
 'ekik',
 'ekim',
 'ekin',
 'ekio',
 'ekir',
 'ekip',
 'ekiq',
 'ekis',
 'ekit',
 'ekiu',
 'ekiv',
 'ekiw',
 'ekix',
 'ekiy',
 'ekiz',
 'ekjc',
 'ekja',
 'ekjb',
 'ekjd',
 'ekje',
 'ekjf',
 'ekjg',
 'ekjh',
 'ekjn',
 'ekjo',
 'ekjp',
 'ekjq',
 'ekjr',
 'ekjs',
 'ekjt',
 'ekjy',
 'ekjz',
 'ekka',
 'ekkb',
 'ekkc',
 'ekkd',
 'ekke',
 'ekkf',
 'ekkg',
 'ekkh',
 'ekki',
 'ekkj',
 'ekkk',
 'ekkl',
 'ekkm',
 'ekkn',
 'ekko',
 'ekkp',
 'ekkq',
 'ekkv',
 'ekkr',
 'ekks',
 'ekkt',
 'ekku']
OUT=ROOT/'output/einstein-seventh-section-visible-v1'
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
        chain=SeventhSectionVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return SeventhSectionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==776,'Seventh-section source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','home',temporal.PARTS[i//256],temporal.PARTS[(i//16)%16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.ALL_CONTRACTS))
    doc['declarations']+=role_definitions()
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
    require(old in ROLE_ASSIGNMENTS,'Unknown seventh-section reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown seventh-section reference')
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
    result['statements']=renamed(doc['statements'][224:246],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    units={r['id']:r for r in inventory['units']}
    for name,row in SOURCE_UNITS.items():
        require(units[name]['text']==row['text'] and units[name]['text_sha256']==row['sha256'],'Source text boundary changed')
    require(previous.SENTENCES['eisrs']==[80,2],'Previous paragraph boundary changed')
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
    require(SOURCE_ORDER==[220,*range(199,220)],'Selection changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-seventh-section-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=SOURCE_UNITS,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        reused_typed_bodies=REUSED_BODIES,new_public_relations=18,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=76,core_edition=12,new_source_assertions=22,
        total_source_assertions=206,total_annotations=46,source_reviews=REVIEW_SELECTION,parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,
        document_integration_credit=0,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible seventh-section document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[first],start,values[last],end,values['ri']):values[n] for n,(first,start,last,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    from scripts.field_symmetry_visible_profile import IndividualCutFunctionReferences
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(roles,{})
    require(kind=='describedindividualcutfunctionreference','Unknown seventh-section reference type')
    return IndividualCutFunctionReferences(roles)





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
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedindividualcutfunctionreference')}



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    from noema.semantic_reviews import validate_hashes
    pins=previous.source_pins()
    state=author.read('data/work-state.json');active=author.read(state['review_index'])['works']['einstein-1905']
    require(active['document']=='examples/v014/einstein-auxiliary-reference-order-v1.noema','Unplanned active manuscript')
    paths={*pins,'data/work-state.json',state['review_index'],active['identifier_annotations'],
        SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/seventh_section_visible_profile.py','scripts/seventh_section_visible_profile_contracts.py',
        'scripts/check_einstein_seventh_section_visible.py','scripts/visible_seventh_section_visible_collection.py',
        'tests/test_seventh_section_visible.py','docs/einstein-seventh-section-visible-v1.md'}
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved seventh-section bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-seventh-section-visible-evidence-1',core_words=375,profile_words=953,profile_edition=76,
        new_public_relations=18,new_reference_primitives=0,new_source_assertions=22,total_source_assertions=206,annotations=46,
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
