"""Connect convective fields, conditional foundations and charge constancy."""
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
from scripts import ninth_section_visible_profile as profile
from scripts.ninth_section_visible_profile import ROOT,NinthSectionVisibleVocabulary,write_once
from scripts import check_einstein_eighth_section_visible as previous
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

SOURCE='examples/v016/einstein-ninth-section-visible-v1.noema'
BRIDGE='data/einstein-ninth-section-visible-bridge-v1.json'
SOURCE_ORDER=[245, 244, 246, 247, 248]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-p916-0.jpg',
  'sha256': '449801d876af7a6a0d7ddecbbc8a43a970e22b4667995250e3c1e391b84e4c29',
  'actually_displayed': True,
  'inspection': 'functions.exec view_image batch with shell marker chunk a7984b',
  'independent_human_reading': False,
  'observations': ['§9は二行見出し。Wir gehen ausの字下げから六式、wobei、密度の式、意味説明まで一文。Denkt manの第二文も同じ段落で、字下げなし。',
                   'Transformiert manは新しい字下げ段落。六式、wobei、速度三式と密度の二等式を含み、頁末の式の句点で一文を閉じる。',
                   '下側の六式は電気側に1/Vがあり、磁気側三式には印刷されていない。意味判断の採用読解を維持する。']},
 {'path': 'artifacts/written-facsimiles-v1/einstein-p917-0.jpg',
  'sha256': 'f7bd2a3cfa0bc4ef39edb34bcf9dd9cfcc65e6d0354d9e720050efed6ce88130',
  'actually_displayed': True,
  'inspection': 'functions.exec view_image batch with shell marker chunk a7984b',
  'independent_human_reading': False,
  'observations': ['頁頭Daは独立した一文・段落。前頁末の式は句点で閉じており、継続文ではない。',
                   'Es mögeは新しい字下げ段落。kann:のコロン後にBewegt sichの条件付き定理が続き、konstant.で一文を閉じる。',
                   'その直後が§10見出し。第9節はこの四つの本文段落で終わる。']}]
PUBLIC_RELATIONS={'zqn': 'distributionmembershipfunction',
 'eisdi': 'theoryfoundationaldependence',
 'eisvx': 'distributionsignedamount',
 'eisvy': 'materialpartsignedamount',
 'eisvz': 'contextualsizebound',
 'eisv2': 'designationcarriermodel',
 'eisv7': 'inquiryproblemrange',
 'eiswa': 'conditionalfoundationaladoption',
 'eiswd': 'settingscalarfielddesignation',
 'eiswe': 'settingvectorfielddesignation',
 'eiswm': 'referstopriorcontent',
 'eiswp': 'conditionallawcontent',
 'eiswr': 'contentimportance',
 'eisws': 'conciseexposition',
 'eiswt': 'supplementaryremarkproposal'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['s6q',
 'semc',
 'semd',
 'seme',
 'semf',
 'semg',
 'semh',
 'seml',
 'semt',
 'sens',
 'sent',
 'seog',
 'seoh',
 'seoi',
 'seoj',
 'seoo',
 'seop',
 'seoq',
 'seor',
 'seot',
 'seow',
 'ekxe',
 'ekxf',
 'ekxg',
 'ekxh',
 'ekxi',
 'ekxk',
 'ekxl',
 'ekxn',
 'ekxo',
 'ekxp',
 'ekxq',
 'ekxr',
 'ekxs',
 'ekxt',
 'ekxu',
 'ekxv',
 'ekxw',
 'ekxx',
 'ekxz',
 'ekx2',
 'ekx3',
 'ekx4',
 'ekx5',
 'ekx6',
 'ekx7',
 'ekya',
 'ekyb',
 'ekyc',
 'ekyd',
 'ekye',
 'ekyg',
 'ekyh',
 'ekyi',
 'ekyj',
 'ekym',
 'ekyn',
 'ekyo',
 'ekyp',
 'ekyq',
 'ekyr',
 'ekys',
 'ekyt',
 'ekyu',
 'ekyv',
 'ekyw',
 'ekyx',
 'ekzq',
 'ekyy',
 'ekyz',
 'ekza',
 'ekzb',
 'ekzc',
 'ekzd',
 'ekze',
 'ekzf',
 'ekzg',
 'ekzh',
 'ekzi',
 'ekzj',
 'ekzk',
 'ekzl',
 'ekzm',
 'ekzn',
 'ekzo',
 'ekzp',
 'ekzr',
 'ekzs',
 'ekzt',
 'ekzu',
 'ekzv',
 'ekzw',
 'ekzx',
 'ekzy',
 'ekzz',
 'ekz2',
 'ekz6',
 'ekz3',
 'ekz4',
 'ekz5',
 'ekz7',
 'ek2a',
 'ek2b',
 'ek2c',
 'ek2d',
 'ek2e',
 'ek2f',
 'ek2g',
 'ek2h',
 'ek2i',
 'ek2j',
 'ek2k',
 'ek2l',
 'ek2n',
 'ek2o',
 'ek2p',
 'ek2q',
 'ek2r',
 'ek2s',
 'ek2t',
 'ek2u',
 'ek2v',
 'ek2w',
 'ek2x',
 'ek2y',
 'ek2z',
 'ek22',
 'ek23',
 'ek24',
 'ek25',
 'ek26',
 'ek27',
 'ek3a',
 'ek3b',
 'ek3c',
 'ek3d',
 'ek3e',
 'ek3f',
 'ek3g',
 'ek3h',
 'ek3i',
 'ek3j',
 'ek3k',
 'ek3l',
 'ek3m']
REUSED_BODIES={}
FORWARD_MAPS={}
HEADINGS={'eiswl': 11}
SENTENCES={'ninthopeningsentence': [99, 1],
 'eiswk': [99, 2],
 'ninthtransformsentence': [100, 1],
 'eiswq': [101, 1],
 'ninthconstancysentence': [102, 1]}
TEXT_SENTENCES={'ninthopeningsentence': 'Wir gehen aus von den Gleichungen: [M0383] wobei [M0384] die [M0385]-fache Dichte '
                         'der Elektrizität und ([M0386]) den Geschwindigkeitsvektor der Elektrizität '
                         'bedeutet.',
 'eiswk': 'Denkt man sich die elektrischen Massen unveränderlich an kleine, starre Körper (Ionen, '
          'Elektronen) gebunden, so sind diese Gleichungen die elektromagnetische Grundlage der Lorentzschen '
          'Elektrodynamik und Optik bewegter Körper.',
 'ninthtransformsentence': 'Transformiert man diese Gleichungen, welche im System [M0387] gelten mögen, mit '
                           'Hilfe der Transformationsgleichungen von § 3 und § 6 auf das System [M0388], so '
                           'erhält man die Gleichungen: [M0389] wobei [M0390]',
 'eiswq': 'Da — wie aus dem Additionstheorem der Geschwindigkeiten (§ 5) folgt — der Vektor ([M0391]) nichts '
          'anderes ist als die Geschwindigkeit der elektrischen Massen im System [M0392] gemessen, so ist '
          'damit gezeigt, daß unter Zugrundelegung unserer kinematischen Prinzipien die elektrodynamische '
          'Grundlage der Lorentzschen Theorie der Elektrodynamik bewegter Körper dem Relativitätsprinzip '
          'entspricht.',
 'ninthconstancysentence': 'Es möge noch kurz bemerkt werden, daß aus den entwickelten Gleichungen leicht '
                           'der folgende wichtige Satz gefolgert werden kann: Bewegt sich ein elektrisch '
                           'geladener Körper beliebig im Raume und ändert sich hierbei seine Ladung nicht, '
                           'von einem mit dem Körper bewegten Koordinatensystem aus betrachtet, so bleibt '
                           'seine Ladung auch — von dem „ruhenden“ System [M0393] aus betrachtet — konstant.'}
SPANS={'eiswf': ['ninthopeningsentence', 1, 'ninthopeningsentence', 6],
 'eiswg': ['ninthopeningsentence', 7, 'ninthopeningsentence', 7],
 'eiswh': ['ninthopeningsentence', 8, 'ninthopeningsentence', 8],
 'eiswi': ['ninthopeningsentence', 9, 'ninthopeningsentence', 9],
 'eiswj': ['ninthopeningsentence', 10, 'ninthopeningsentence', 21],
 'ninthquantitydefinitions': ['ninthopeningsentence', 9, 'ninthopeningsentence', 21],
 'eiswn': ['ninthtransformsentence', 1, 'ninthtransformsentence', 29],
 'eiswo': ['ninthtransformsentence', 31, 'ninthtransformsentence', 31],
 'eiswu': ['ninthconstancysentence', 1, 'ninthconstancysentence', 19],
 'eiswv': ['ninthconstancysentence', 20, 'ninthconstancysentence', 59],
 'zqa': ['ninthtransformsentence', 30, 'ninthtransformsentence', 30],
 'zqb': ['ninthtransformsentence', 32, 'ninthtransformsentence', 32],
 'ninthlorentztheoryanchor': ['eiswk', 22, 'eiswk', 28]}
MULTI_SPANS={}
TOKEN_COUNTS={'ninthopeningsentence': 21,
 'eiswk': 28,
 'ninthtransformsentence': 32,
 'eiswq': 51,
 'ninthconstancysentence': 59}
TOKENS={'ninthopeningsentence': ['Wir',
                          'gehen',
                          'aus',
                          'von',
                          'den',
                          'Gleichungen:',
                          '[M0383]',
                          'wobei',
                          '[M0384]',
                          'die',
                          '[M0385]-fache',
                          'Dichte',
                          'der',
                          'Elektrizität',
                          'und',
                          '([M0386])',
                          'den',
                          'Geschwindigkeitsvektor',
                          'der',
                          'Elektrizität',
                          'bedeutet.'],
 'eiswk': ['Denkt',
           'man',
           'sich',
           'die',
           'elektrischen',
           'Massen',
           'unveränderlich',
           'an',
           'kleine,',
           'starre',
           'Körper',
           '(Ionen,',
           'Elektronen)',
           'gebunden,',
           'so',
           'sind',
           'diese',
           'Gleichungen',
           'die',
           'elektromagnetische',
           'Grundlage',
           'der',
           'Lorentzschen',
           'Elektrodynamik',
           'und',
           'Optik',
           'bewegter',
           'Körper.'],
 'ninthtransformsentence': ['Transformiert',
                            'man',
                            'diese',
                            'Gleichungen,',
                            'welche',
                            'im',
                            'System',
                            '[M0387]',
                            'gelten',
                            'mögen,',
                            'mit',
                            'Hilfe',
                            'der',
                            'Transformationsgleichungen',
                            'von',
                            '§',
                            '3',
                            'und',
                            '§',
                            '6',
                            'auf',
                            'das',
                            'System',
                            '[M0388],',
                            'so',
                            'erhält',
                            'man',
                            'die',
                            'Gleichungen:',
                            '[M0389]',
                            'wobei',
                            '[M0390]'],
 'eiswq': ['Da',
           '—',
           'wie',
           'aus',
           'dem',
           'Additionstheorem',
           'der',
           'Geschwindigkeiten',
           '(§',
           '5)',
           'folgt',
           '—',
           'der',
           'Vektor',
           '([M0391])',
           'nichts',
           'anderes',
           'ist',
           'als',
           'die',
           'Geschwindigkeit',
           'der',
           'elektrischen',
           'Massen',
           'im',
           'System',
           '[M0392]',
           'gemessen,',
           'so',
           'ist',
           'damit',
           'gezeigt,',
           'daß',
           'unter',
           'Zugrundelegung',
           'unserer',
           'kinematischen',
           'Prinzipien',
           'die',
           'elektrodynamische',
           'Grundlage',
           'der',
           'Lorentzschen',
           'Theorie',
           'der',
           'Elektrodynamik',
           'bewegter',
           'Körper',
           'dem',
           'Relativitätsprinzip',
           'entspricht.'],
 'ninthconstancysentence': ['Es',
                            'möge',
                            'noch',
                            'kurz',
                            'bemerkt',
                            'werden,',
                            'daß',
                            'aus',
                            'den',
                            'entwickelten',
                            'Gleichungen',
                            'leicht',
                            'der',
                            'folgende',
                            'wichtige',
                            'Satz',
                            'gefolgert',
                            'werden',
                            'kann:',
                            'Bewegt',
                            'sich',
                            'ein',
                            'elektrisch',
                            'geladener',
                            'Körper',
                            'beliebig',
                            'im',
                            'Raume',
                            'und',
                            'ändert',
                            'sich',
                            'hierbei',
                            'seine',
                            'Ladung',
                            'nicht,',
                            'von',
                            'einem',
                            'mit',
                            'dem',
                            'Körper',
                            'bewegten',
                            'Koordinatensystem',
                            'aus',
                            'betrachtet,',
                            'so',
                            'bleibt',
                            'seine',
                            'Ladung',
                            'auch',
                            '—',
                            'von',
                            'dem',
                            '„ruhenden“',
                            'System',
                            '[M0393]',
                            'aus',
                            'betrachtet',
                            '—',
                            'konstant.']}
DESIGNATIONS={'eisv3': ['eiswk', 1],
 'eisv4': ['eiswk', 2],
 'eiswb': ['ninthquantitydefinitions', 1],
 'eiswc': ['ninthquantitydefinitions', 2]}
FORMS={'eisv3': 'Ionen', 'eisv4': 'Elektronen', 'eiswb': 'ϱ', 'eiswc': '(u_x,u_y,u_z)'}
ROLE_ASSIGNMENTS={'eisv5': 'ninthroleeisv5', 'eisv6': 'ninthroleeisv6'}
REFERENCE_SORTS={'eisv5': 'individual', 'eisv6': 'individual'}
REFERENCE_ANCHORS={'eisv5': 'ninthlorentztheoryanchor', 'eisv6': 'eiswl'}
SOURCE_UNITS={'einstein-1905:u0227': {'text': '§ 9. Transformation der Maxwell-Hertzschen Gleichungen mit '
                                 'Berücksichtigung der Konvektionsströme.',
                         'sha256': '35fd89a9e1099222fdc25fb72d1dee52c8a0338bf376b4a0e878ccf6cbca2e1a'},
 'einstein-1905:u0228': {'text': 'Wir gehen aus von den Gleichungen:',
                         'sha256': '83a65225e0d59ccaedd2a15c4aa854b0db93fef26120adedd03b564410ecbdd8'},
 'einstein-1905:u0229': {'text': '[M0383]',
                         'sha256': 'd877993df844d362c32770e618996b188913b79c116593f071e3916bd92eac00'},
 'einstein-1905:u0230': {'text': 'wobei',
                         'sha256': 'ad6f70890a12d8f25cf83a9ebb72fac6316cf86f4e2e27c3ef03027f2b994c84'},
 'einstein-1905:u0231': {'text': '[M0384]',
                         'sha256': '3e7465cbbc7e54aa6c1e49f2341a0f7dc7e40c0ddc2a88219561c6d1e6ea7e3a'},
 'einstein-1905:u0232': {'text': 'die [M0385]-fache Dichte der Elektrizität und ([M0386]) den '
                                 'Geschwindigkeitsvektor der Elektrizität bedeutet. Denkt man sich die '
                                 'elektrischen Massen unveränderlich an kleine, starre Körper (Ionen, '
                                 'Elektronen) gebunden, so sind diese Gleichungen die elektromagnetische '
                                 'Grundlage der Lorentzschen Elektrodynamik und Optik bewegter Körper.',
                         'sha256': 'c5d3907c6009e2aaaf3c1b32af93d3ae140127490bfe1ad28a0c2ed1f16c7afe'},
 'einstein-1905:u0233': {'text': 'Transformiert man diese Gleichungen, welche im System [M0387] gelten '
                                 'mögen, mit Hilfe der Transformationsgleichungen von § 3 und § 6 auf das '
                                 'System [M0388], so erhält man die Gleichungen:',
                         'sha256': '41649050d598bfd1f1ea3916972a18dd55323dc7f0e7b6ad901a3938b2716fb6'},
 'einstein-1905:u0234': {'text': '[M0389]',
                         'sha256': 'ed3c5bd4b7896fd42ec072f195ad64a85de062cd36c2f5a787d60ebbc91dd3e5'},
 'einstein-1905:u0235': {'text': 'wobei',
                         'sha256': 'ad6f70890a12d8f25cf83a9ebb72fac6316cf86f4e2e27c3ef03027f2b994c84'},
 'einstein-1905:u0236': {'text': '[M0390]',
                         'sha256': '700edab12dd884549e239b10102360c12af9c69e601aae14d42b2675090c77c7'},
 'einstein-1905:u0237': {'text': 'Da — wie aus dem Additionstheorem der Geschwindigkeiten (§ 5) folgt — der '
                                 'Vektor ([M0391]) nichts anderes ist als die Geschwindigkeit der '
                                 'elektrischen Massen im System [M0392] gemessen, so ist damit gezeigt, daß '
                                 'unter Zugrundelegung unserer kinematischen Prinzipien die '
                                 'elektrodynamische Grundlage der Lorentzschen Theorie der Elektrodynamik '
                                 'bewegter Körper dem Relativitätsprinzip entspricht.',
                         'sha256': '87b7017fa4f1b4d77700a8ee8edce1c5ced4d693d81c230217686dde59ea453e'},
 'einstein-1905:u0238': {'text': 'Es möge noch kurz bemerkt werden, daß aus den entwickelten Gleichungen '
                                 'leicht der folgende wichtige Satz gefolgert werden kann: Bewegt sich ein '
                                 'elektrisch geladener Körper beliebig im Raume und ändert sich hierbei '
                                 'seine Ladung nicht, von einem mit dem Körper bewegten Koordinatensystem '
                                 'aus betrachtet, so bleibt seine Ladung auch — von dem „ruhenden“ System '
                                 '[M0393] aus betrachtet — konstant.',
                         'sha256': '8eaf9f1f970146492512f7d30950e670a4825106063d82889c4a56d2e8e7c425'}}
SOURCE_FRAGMENTS={'ninthopeningsentence': [[228, 0, 34], [229, 0, 7], [230, 0, 5], [231, 0, 7], [232, 0, 109]],
 'eiswk': [[232, 110, 336]],
 'ninthtransformsentence': [[233, 0, 187], [234, 0, 7], [235, 0, 5], [236, 0, 7]],
 'eiswq': [[237, 0, 393]],
 'ninthconstancysentence': [[238, 0, 392]]}
BOUNDARY_RULE='原刊字下げによる99..102段落。数式はM番号一token。コロン・wobei・頁境界を追加の文境界にしない。'
REVIEWS=('data/einstein-ninth-section-opening-u0227-review-v1.json',
 'data/einstein-ninth-section-opening-u0228-review-v1.json',
 'data/einstein-ninth-section-opening-u0229-review-v1.json',
 'data/einstein-ninth-section-opening-u0230-review-v1.json',
 'data/einstein-ninth-section-opening-u0231-review-v1.json',
 'data/einstein-ninth-section-opening-u0232-review-v1.json',
 'data/einstein-convective-transformation-u0233-review-v1.json',
 'data/einstein-convective-transformation-u0234-review-v1.json',
 'data/einstein-convective-transformation-u0235-review-v1.json',
 'data/einstein-convective-transformation-u0236-review-v1.json',
 'data/einstein-convective-relativity-u0237-review-v1.json',
 'data/einstein-charge-constancy-u0238-review-v1.json')
REVIEW_SELECTION=[{'unit': 'einstein-1905:u0227',
  'review': 'data/einstein-ninth-section-opening-u0227-review-v1.json',
  'statements': [245]},
 {'unit': 'einstein-1905:u0228',
  'review': 'data/einstein-ninth-section-opening-u0228-review-v1.json',
  'statements': [244]},
 {'unit': 'einstein-1905:u0229',
  'review': 'data/einstein-ninth-section-opening-u0229-review-v1.json',
  'statements': [244]},
 {'unit': 'einstein-1905:u0230',
  'review': 'data/einstein-ninth-section-opening-u0230-review-v1.json',
  'statements': [244]},
 {'unit': 'einstein-1905:u0231',
  'review': 'data/einstein-ninth-section-opening-u0231-review-v1.json',
  'statements': [244]},
 {'unit': 'einstein-1905:u0232',
  'review': 'data/einstein-ninth-section-opening-u0232-review-v1.json',
  'statements': [244]},
 {'unit': 'einstein-1905:u0233',
  'review': 'data/einstein-convective-transformation-u0233-review-v1.json',
  'statements': [246]},
 {'unit': 'einstein-1905:u0234',
  'review': 'data/einstein-convective-transformation-u0234-review-v1.json',
  'statements': [246]},
 {'unit': 'einstein-1905:u0235',
  'review': 'data/einstein-convective-transformation-u0235-review-v1.json',
  'statements': [246]},
 {'unit': 'einstein-1905:u0236',
  'review': 'data/einstein-convective-transformation-u0236-review-v1.json',
  'statements': [246]},
 {'unit': 'einstein-1905:u0237',
  'review': 'data/einstein-convective-relativity-u0237-review-v1.json',
  'statements': [247]},
 {'unit': 'einstein-1905:u0238',
  'review': 'data/einstein-charge-constancy-u0238-review-v1.json',
  'statements': [248]}]
READINGS=('data/attached-material-charge-basis-v1.json',
 'data/carrier-charge-composition-basis-v1.json',
 'data/carrier-field-correspondence-basis-v1.json',
 'data/charge-constancy-claim-basis-v1.json',
 'data/complete-material-attachment-basis-v1.json',
 'data/convective-charge-setting-basis-v1.json',
 'data/convective-foundation-reading-basis-v1.json',
 'data/convective-relativity-claim-basis-v1.json',
 'data/convective-transformation-claim-basis-v1.json',
 'data/convective-transformed-quantities-basis-v1.json',
 'data/convective-velocity-interpretation-basis-v1.json',
 'data/einstein-author-credit-basis-v1.json',
 'data/kinematic-foundation-basis-v1.json',
 'data/moving-body-charge-history-basis-v1.json',
 'data/ninth-section-opening-basis-v1.json',
 'reports/charge-constancy-claim-v1.json',
 'reports/convective-relativity-claim-v1.json',
 'reports/convective-transformation-claim-v1.json',
 'reports/ninth-section-opening-v1.json')
DIAGNOSTIC_VALIDATORS=['scripts/check_attached_material_charge.py',
 'scripts/check_carrier_charge_composition.py',
 'scripts/check_carrier_field_correspondence.py',
 'scripts/check_charge_constancy_claim.py',
 'scripts/check_complete_material_attachment.py',
 'scripts/check_convective_charge_setting.py',
 'scripts/check_convective_foundation_reading.py',
 'scripts/check_convective_relativity_claim.py',
 'scripts/check_convective_transformation_claim.py',
 'scripts/check_convective_transformed_quantities.py',
 'scripts/check_convective_velocity_interpretation.py',
 'scripts/check_moving_body_charge_history.py',
 'scripts/check_ninth_section_opening.py']
SEMANTIC_REVIEW=['元の二場・領域・密度・流速・単位・評価点を共有し、六回転式と発散式を区別する。密度は電荷密度の4π倍。',
 '零密度から分布や流速の不在を推論しない。異なる種の速度を一つの場に自動的に合成しない。',
 '原系の提示は出発前提の採用。担体の不変付着と小剛体という第二文の条件を第一文の追加前提にしない。',
 '変換の成立仮定・手段・結果・補足を同じ設定で接続。第3節と第6節の最終規則を用い、逆向き同値や真理を付け加えない。',
 'M0389磁気側の1/V欠落を保持。M0390は同じ逆座標による三速度と密度の五等式。D非零を正に強めない。',
 '第5節からの実際の速度の同定は別の著者推論。適合対象は指定のLorentz基礎であり理論全体を共通体系に固定しない。',
 '相対性原理の絶対静止部分と真空光速度を含む同じ運動学的原理を保持。著者の示されたという提示を自動証明に変えない。',
 '総電荷の一定性は同じ全物体・期間を追い、共動系からKへの条件の向きを保持。二系の電荷数値等値や全部分の不変を追加しない。',
 '随伴系は同じ追跡点に原点を付ける採用読解。等速・剛体・共通静止慣性系を要求しない。',
 '注記の控えめさ、簡潔さ、重要さ、利用可能な低負担導出、真理を分ける。']
ROLE_DEFINITIONS={'eisv5': {'kind': 'definition',
           'name': 'ninthroleeisv5',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'ekyw',
                    'arguments': [{'kind': 'variable', 'name': 'va'}, {'kind': 'variable', 'name': 'vb'}]}},
 'eisv6': {'kind': 'definition',
           'name': 'ninthroleeisv6',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'and',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisdv',
                                   'arguments': [{'kind': 'call', 'symbol': 'eiswl', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'call', 'symbol': 'eispb', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                                 {'kind': 'number', 'numerator': 2, 'denominator': 1},
                                                 {'kind': 'number', 'numerator': 9, 'denominator': 1},
                                                 {'kind': 'variable', 'name': 'vb'}]},
                                  {'kind': 'not',
                                   'arguments': [{'kind': 'equal',
                                                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                                                {'kind': 'call',
                                                                 'symbol': 'eispb',
                                                                 'arguments': []}]}]}]}}}
LOCAL_NAMES=['eiswl',
 'ninthopeningsentence',
 'eiswk',
 'ninthtransformsentence',
 'eiswq',
 'ninthconstancysentence',
 'eiswf',
 'eiswg',
 'eiswh',
 'eiswi',
 'eiswj',
 'ninthquantitydefinitions',
 'eiswn',
 'eiswo',
 'eiswu',
 'eiswv',
 'zqa',
 'zqb',
 'ninthlorentztheoryanchor',
 'eisv3',
 'eisv4',
 'eiswb',
 'eiswc',
 'eisv5',
 'eisv6',
 'ninthroleeisv5',
 'ninthroleeisv6',
 's6q',
 'semc',
 'semd',
 'seme',
 'semf',
 'semg',
 'semh',
 'seml',
 'semt',
 'sens',
 'sent',
 'seog',
 'seoh',
 'seoi',
 'seoj',
 'seoo',
 'seop',
 'seoq',
 'seor',
 'seot',
 'seow',
 'ekxe',
 'ekxf',
 'ekxg',
 'ekxh',
 'ekxi',
 'ekxk',
 'ekxl',
 'ekxn',
 'ekxo',
 'ekxp',
 'ekxq',
 'ekxr',
 'ekxs',
 'ekxt',
 'ekxu',
 'ekxv',
 'ekxw',
 'ekxx',
 'ekxz',
 'ekx2',
 'ekx3',
 'ekx4',
 'ekx5',
 'ekx6',
 'ekx7',
 'ekya',
 'ekyb',
 'ekyc',
 'ekyd',
 'ekye',
 'ekyg',
 'ekyh',
 'ekyi',
 'ekyj',
 'ekym',
 'ekyn',
 'ekyo',
 'ekyp',
 'ekyq',
 'ekyr',
 'ekys',
 'ekyt',
 'ekyu',
 'ekyv',
 'ekyw',
 'ekyx',
 'ekzq',
 'ekyy',
 'ekyz',
 'ekza',
 'ekzb',
 'ekzc',
 'ekzd',
 'ekze',
 'ekzf',
 'ekzg',
 'ekzh',
 'ekzi',
 'ekzj',
 'ekzk',
 'ekzl',
 'ekzm',
 'ekzn',
 'ekzo',
 'ekzp',
 'ekzr',
 'ekzs',
 'ekzt',
 'ekzu',
 'ekzv',
 'ekzw',
 'ekzx',
 'ekzy',
 'ekzz',
 'ekz2',
 'ekz6',
 'ekz3',
 'ekz4',
 'ekz5',
 'ekz7',
 'ek2a',
 'ek2b',
 'ek2c',
 'ek2d',
 'ek2e',
 'ek2f',
 'ek2g',
 'ek2h',
 'ek2i',
 'ek2j',
 'ek2k',
 'ek2l',
 'ek2n',
 'ek2o',
 'ek2p',
 'ek2q',
 'ek2r',
 'ek2s',
 'ek2t',
 'ek2u',
 'ek2v',
 'ek2w',
 'ek2x',
 'ek2y',
 'ek2z',
 'ek22',
 'ek23',
 'ek24',
 'ek25',
 'ek26',
 'ek27',
 'ek3a',
 'ek3b',
 'ek3c',
 'ek3d',
 'ek3e',
 'ek3f',
 'ek3g',
 'ek3h',
 'ek3i',
 'ek3j',
 'ek3k',
 'ek3l',
 'ek3m']
OUT=ROOT/'output/einstein-ninth-section-visible-v1'
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
        chain=NinthSectionVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return NinthSectionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==678,'Ninth-section source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','give',temporal.PARTS[i//256],temporal.PARTS[(i//16)%16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown ninth-section reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown ninth-section reference')
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
    result['statements']=renamed(doc['statements'][295:300],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    units={r['id']:r for r in inventory['units']}
    for name,row in SOURCE_UNITS.items():
        require(units[name]['text']==row['text'] and units[name]['text_sha256']==row['sha256'],'Source text boundary changed')
    require(previous.SENTENCES['eisvu']==[98,3],'Previous paragraph boundary changed')
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
    require(SOURCE_ORDER==[245,244,246,247,248],'Selection changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-ninth-section-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=SOURCE_UNITS,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        reused_typed_bodies=REUSED_BODIES,new_public_relations=15,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=78,core_edition=12,new_source_assertions=5,
        total_source_assertions=234,total_annotations=70,source_reviews=REVIEW_SELECTION,parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,
        document_integration_credit=0,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible ninth-section document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[first],start,values[last],end,values['ri']):values[n] for n,(first,start,last,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    from scripts.field_symmetry_visible_profile import IndividualCutFunctionReferences
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(roles,{})
    require(kind=='describedindividualcutfunctionreference','Unknown ninth-section reference type')
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
    from scripts.visible_pin_snapshot import digest_snapshot
    with digest_snapshot(author,root=ROOT):
        return _source_pins(include_outputs=include_outputs)


def _source_pins(*,include_outputs=True):
    from noema.semantic_reviews import validate_hashes
    pins=previous.source_pins()
    state=author.read('data/work-state.json');active=author.read(state['review_index'])['works']['einstein-1905']
    require(active['document']=='examples/v014/einstein-auxiliary-reference-order-v1.noema','Unplanned active manuscript')
    paths={*pins,'data/work-state.json',state['review_index'],active['identifier_annotations'],
        SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/ninth_section_visible_profile.py','scripts/ninth_section_visible_profile_contracts.py',
        'scripts/check_einstein_ninth_section_visible.py','scripts/visible_ninth_section_visible_collection.py',
        'tests/test_ninth_section_visible.py','tests/test_ninth_section_physics_visible.py',
        'data/ninth-section-visible-diagnostic-controls-v2.json',*DIAGNOSTIC_VALIDATORS,
        'scripts/visible_pin_snapshot.py','tests/test_visible_pin_snapshot.py',
        'docs/einstein-ninth-section-visible-v1.md'}
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved ninth-section bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-ninth-section-visible-evidence-1',core_words=375,profile_words=990,profile_edition=78,
        new_public_relations=15,new_reference_primitives=0,new_source_assertions=5,total_source_assertions=234,annotations=70,
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
