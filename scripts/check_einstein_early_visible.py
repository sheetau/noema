"""Connect the complete title, opening arguments and first headings."""
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
from scripts import early_reference_visible_profile as profile
from scripts import early_visible_profile as opening_profile
from scripts import frontmatter_reference_visible_profile as front_profile
from scripts.early_reference_visible_profile import ROOT,EarlyReferenceVisibleVocabulary,write_once
from scripts import check_einstein_tenth_closing_visible as previous
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

from scripts.early_individual_reference_roles import build_roles
from scripts.early_text_references import declarations as text_reference_declarations
SOURCE='examples/v016/einstein-early-visible-v1.noema'
BRIDGE='data/einstein-early-visible-bridge-v1.json'
SOURCE_ORDER=[48, 47, 43, 44, 45, 46, 49, 50, 51, 52, 53, 54, 55, 56]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/einstein-opening-v1/page-891.jpg',
  'sha256': '715ba57296f3c1535e1122f7ea63844a3b163301d0ba1a0be7dd55c05dbd5382',
  'actually_displayed': True,
  'display_method': 'functions.exec/tools.view_image forwarded with image(), current goal turn after '
                    'Git inspection',
  'independent_human_reading': False},
 {'path': 'artifacts/einstein-principles-v1/page-892.jpg',
  'sha256': '4cf33cfe479721aa1f6deb6d140033815294579fa9c46fb910e171fbaf4d563f',
  'actually_displayed': True,
  'display_method': 'functions.exec/tools.view_image forwarded with image(), current goal turn after '
                    'Git inspection',
  'independent_human_reading': False}]
PUBLIC_RELATIONS={'eir2': 'contentconsideration',
 'eir4': 'intendeddocumentreader',
 'eisa4': 'attributedcommonknowledge',
 'eisal': 'bodysurroundingregion',
 'eisam': 'sourceelectricfieldgeneration',
 'eisan': 'regionalelectricfieldenergy',
 'eisao': 'electricfielddrivencurrent',
 'eisap': 'admissibleinteractioncase',
 'eisas': 'motionmagneticdrive',
 'eisat': 'driveintrinsicstoredenergy',
 'eisau': 'localdrivencurrent',
 'eisaw': 'scopedcomponentcontrast',
 'eisb3': 'positivealternativeformulation',
 'eisba': 'documenttitlepresentation',
 'eisbb': 'documenttopiccontribution',
 'eisbp': 'attributedpriorconfirmation',
 'eisbq': 'conjecturalgrounds',
 'eisbr': 'conjecturalstatus',
 'eisbs': 'analogouscasekind',
 'eisbt': 'contextualexampledomain',
 'eisbu': 'contextualattemptdomain',
 'eisbv': 'observationalverificationattempt',
 'eisbw': 'observationalgoalachievement',
 'eisbz': 'hypothesizedmediumframe',
 'eisc2': 'spatialpointmembership',
 'eisc4': 'velocityvectorrecord',
 'eisc5': 'velocityvectorcomponents',
 'eisc6': 'intrinsicspacepointvelocity',
 'eisc7': 'scopepreservingtheoreticalalternative',
 'eisck': 'apparentclaimcandidate',
 'eiscx': 'privilegedrestspaceconcept',
 'eiscy': 'privilegedspatialproperty',
 'eiscz': 'materialmediumfreevacuumregion',
 'eisda': 'scopequalifiedexplanation',
 'eisde': 'physicalframebody',
 'eisdg': 'physicalreferentialinterpretation',
 'eisdm': 'treatmentofinquiryfact',
 'eisdn': 'sufficientfactconsideration',
 'eisdo': 'conceptualinquirydifficulty',
 'eisdp': 'historicallyunresolveddifficulty',
 'eisdq': 'foundationalinquirydifficultycause',
 'eisdr': 'contextualdifficultydomain',
 'eisdt': 'simultaneityrelationinquiry'}
REUSED_DEFINITIONS=['da', 'db', 'eia2', 'eia4', 'eia5', 'eia6', 'eia7', 'eiac', 'eiad', 'eiae', 'eiaf', 'eiag', 'eiah', 'eiaj', 'eiak', 'eial', 'eiam', 'eian', 'eiao', 'eiap', 'eiaq', 'eiar', 'eiav', 'eiaw', 'eiax', 'eiay', 'eiaz', 'eiba', 'eibe', 'eibf', 'eibg', 'eibk', 'eibq', 'eibr', 'eibs', 'eice', 'eicf', 'eicg', 'eich', 'eici', 'eicj', 'eicn', 'eico', 'eicq', 'eicr', 'eics', 'eicw', 'eida', 'eidd', 'eide', 'eidf', 'eidh', 'eidz', 'eie5', 'eie6', 'eieu', 'eiev', 'eiew', 'eiex', 'eiey', 'eiez', 'eif5', 'eifb', 'eifc', 'eifd', 'eife', 'eiff', 'eifg', 'eifh', 'eifi', 'eifj', 'eifk', 'eifw', 'eifx', 'eify', 'eig3', 'eig4', 'eige', 'eigf', 'eigg', 'eigh', 'eigi', 'eigj', 'eigw', 'eigx', 'eigy', 'eihm', 'eihn', 'eihq', 'la', 'lb', 'lc', 'ld', 'lg', 'li', 'qm', 'qn', 'qo', 's7s', 'sa', 'sad', 'sae', 'saf', 'sak', 'sap', 'saq', 'sar', 'sax', 'sb', 'sbg', 'sbw2', 'scb2', 'scg2', 'sch2', 'sd', 'se', 'seg', 'seh', 'seoa', 'seob', 'seoc', 'sepw', 'sexb', 'sexc', 'sexd', 'shx', 'sqh', 'szi', 'zzba', 'zzbb', 'zzbc', 'zzbd', 'zzbe', 'zzbf', 'zzbg', 'zzbh', 'zzbi', 'zzbj', 'zzbk', 'zzbl', 'zzbm', 'ba', 'bb', 'bc', 'bd', 'be', 'bf', 'bg', 'bi', 'sag', 'sah', 'sca', 'shm', 'shn', 'sho', 'shu', 'shv', 'sjd', 'sju', 'sjt', 'sjo', 'sjp', 'sjq', 'sjr', 'sjs', 'senz']
NEW_DEFINITIONS=['eibb', 'eibc', 'eibi', 'eica', 'eic2', 'eic3', 'eic4', 'eic5', 'eic6', 'eic7', 'eidb', 'eidc', 'eidg', 'eidi', 'eidj', 'eidk', 'eidl', 'eidm', 'eidn', 'eido', 'eidp', 'eidq', 'eidr', 'eids', 'eidt', 'eidu', 'eidv', 'eidw', 'eidx', 'eidy', 'eid2', 'eid3', 'eid4', 'eid5', 'eid6', 'eid7', 'eiea', 'eieq', 'eier', 'eies', 'eiet', 'eieb', 'eiec', 'eied', 'eiee', 'eief', 'eieg', 'eieh', 'eiei', 'eiej', 'eiek', 'eiel', 'eiem', 'eie2', 'eie3', 'eie4', 'eie7', 'eifa', 'eifl', 'eifm', 'eifn', 'eifo', 'eifp', 'eifq', 'eifr', 'eifs', 'eift', 'eifu', 'eifv', 'eifz', 'eif2', 'eif3', 'eif4', 'eif6', 'eif7', 'eigd', 'eiga', 'eigb', 'eigc', 'eigk', 'eigl', 'eigm', 'eign', 'eigo', 'eigp', 'eigq', 'eigr', 'eigs', 'eigt', 'eigu', 'eigv', 'eigz', 'eig2', 'eig5', 'eig6', 'eig7', 'eiha', 'eihb', 'eihc', 'eihd', 'eihe', 'eihf', 'eihg', 'eihh', 'eihi', 'eihj', 'eihk', 'eihl', 'eiho', 'eihp', 'eihr', 'eihs']
REUSED_BODIES={}
FORWARD_MAPS={}
HEADINGS={'eisdz': 1}
SENTENCES={'eir6': [1, 2],
 'eisaq': [1, 4],
 'eisav': [1, 5],
 'eisb4': [2, 1],
 'eiscl': [2, 2],
 'eiscu': [2, 3],
 'eisdc': [2, 4],
 'eisdl': [3, 1],
 'eisds': [3, 2]}
SPANS={'earlyearthtoken': ['eisb4', 11, 'eisb4', 11],
 'earlymediumtoken': ['eisb4', 14, 'eisb4', 14],
 'earlyfirstordertoken': ['eisb4', 66, 'eisb4', 68],
 'earlyethertoken': ['eisdc', 4, 'eisdc', 4]}
MULTI_SPANS={}
DESIGNATIONS={'earlyearthdesignation': ['earlyearthtoken', 1]}
FORMS={'earlyearthdesignation': 'Erde'}
ROLE_ASSIGNMENTS={'eisbo': 'earlyroleeisbo', 'eisbx': 'earlyroleeisbx', 'eisby': 'earlyroleeisby'}
REFERENCE_ANCHORS={'eisbo': 'earlyfirstordertoken', 'eisbx': 'earlyearthtoken', 'eisby': 'earlymediumtoken'}
REFERENCE_SORTS={'eisbo': 'individual', 'eisbx': 'individual', 'eisby': 'individual'}
REFERENCE_KINDS={'eisbo': 'describedreference', 'eisbx': 'describedreference', 'eisby': 'describedreference'}
LOCAL_NAMES=['eir6',
 'eisaq',
 'eisav',
 'eisb4',
 'eiscl',
 'eiscu',
 'eisdc',
 'eisdl',
 'eisds',
 'eisbc',
 'eisdz',
 'earlyearthtoken',
 'earlymediumtoken',
 'earlyfirstordertoken',
 'earlyethertoken',
 'eisbo',
 'eisbx',
 'eisby',
 'earlyearthdesignation',
 'earlyroleeisbo',
 'earlyroleeisbx',
 'earlyroleeisby',
 'ba',
 'bb',
 'bc',
 'bd',
 'be',
 'bf',
 'bg',
 'bi',
 'sag',
 'sah',
 'sca',
 'shm',
 'shn',
 'sho',
 'shu',
 'shv',
 'sjd',
 'sju',
 'sjt',
 'sjo',
 'sjp',
 'sjq',
 'sjr',
 'sjs',
 'senz',
 'eibb',
 'eibc',
 'eibi',
 'eica',
 'eic2',
 'eic3',
 'eic4',
 'eic5',
 'eic6',
 'eic7',
 'eidb',
 'eidc',
 'eidg',
 'eidi',
 'eidj',
 'eidk',
 'eidl',
 'eidm',
 'eidn',
 'eido',
 'eidp',
 'eidq',
 'eidr',
 'eids',
 'eidt',
 'eidu',
 'eidv',
 'eidw',
 'eidx',
 'eidy',
 'eid2',
 'eid3',
 'eid4',
 'eid5',
 'eid6',
 'eid7',
 'eiea',
 'eieq',
 'eier',
 'eies',
 'eiet',
 'eieb',
 'eiec',
 'eied',
 'eiee',
 'eief',
 'eieg',
 'eieh',
 'eiei',
 'eiej',
 'eiek',
 'eiel',
 'eiem',
 'eie2',
 'eie3',
 'eie4',
 'eie7',
 'eifa',
 'eifl',
 'eifm',
 'eifn',
 'eifo',
 'eifp',
 'eifq',
 'eifr',
 'eifs',
 'eift',
 'eifu',
 'eifv',
 'eifz',
 'eif2',
 'eif3',
 'eif4',
 'eif6',
 'eif7',
 'eigd',
 'eiga',
 'eigb',
 'eigc',
 'eigk',
 'eigl',
 'eigm',
 'eign',
 'eigo',
 'eigp',
 'eigq',
 'eigr',
 'eigs',
 'eigt',
 'eigu',
 'eigv',
 'eigz',
 'eig2',
 'eig5',
 'eig6',
 'eig7',
 'eiha',
 'eihb',
 'eihc',
 'eihd',
 'eihe',
 'eihf',
 'eihg',
 'eihh',
 'eihi',
 'eihj',
 'eihk',
 'eihl',
 'eiho',
 'eihp',
 'eihr',
 'eihs']
TEXT_SENTENCES={'eir7': 'Daß die Elektrodynamik Maxwells — wie dieselbe gegenwärtig aufgefaßt zu werden pflegt — in '
         'ihrer Anwendung auf bewegte Körper zu Asymmetrien führt, welche den Phänomenen nicht '
         'anzuhaften scheinen, ist bekannt.',
 'eir6': 'Man denke z. B. an die elektrodynamische Wechselwirkung zwischen einem Magneten und einem '
         'Leiter.',
 'eisaj': 'Das beobachtbare Phänomen hängt hier nur ab von der Relativbewegung von Leiter und Magnet, '
          'während nach der üblichen Auffassung die beiden Fälle, daß der eine oder der andere dieser '
          'Körper der bewegte sei, streng voneinander zu trennen sind.',
 'eisaq': 'Bewegt sich nämlich der Magnet und ruht der Leiter, so entsteht in der Umgebung des Magneten '
          'ein elektrisches Feld von gewissem Energiewerte, welches an den Orten, wo sich Teile des '
          'Leiters befinden, einen Strom erzeugt.',
 'eisav': 'Ruht aber der Magnet und bewegt sich der Leiter, so entsteht in der Umgebung des Magneten '
          'kein elektrisches Feld, dagegen im Leiter eine elektromotorische Kraft, welcher an sich '
          'keine Energie entspricht, die aber — Gleichheit der Relativbewegung bei den beiden ins Auge '
          'gefaßten Fällen vorausgesetzt — zu elektrischen Strömen von derselben Größe und demselben '
          'Verlaufe Veranlassung gibt, wie im ersten Falle die elektrischen Kräfte.',
 'eisb4': 'Beispiele ähnlicher Art, sowie die mißlungenen Versuche, eine Bewegung der Erde relativ zum '
          '„Lichtmedium“ zu konstatieren, führen zu der Vermutung, daß dem Begriffe der absoluten Ruhe '
          'nicht nur in der Mechanik, sondern auch in der Elektrodynamik keine Eigenschaften der '
          'Erscheinungen entsprechen, sondern daß vielmehr für alle Koordinatensysteme, für welche die '
          'mechanischen Gleichungen gelten, auch die gleichen elektrodynamischen und optischen Gesetze '
          'gelten, wie dies für die Größen erster Ordnung bereits erwiesen ist.',
 'eiscl': 'Wir wollen diese Vermutung (deren Inhalt im folgenden „Prinzip der Relativität“ genannt '
          'werden wird) zur Voraussetzung erheben und außerdem die mit ihm nur scheinbar unverträgliche '
          'Voraussetzung einführen, daß sich das Licht im leeren Raume stets mit einer bestimmten, vom '
          'Bewegungszustande des emittierenden Körpers unabhängigen Geschwindigkeit [M0001] '
          'fortpflanze.',
 'eiscu': 'Diese beiden Voraussetzungen genügen, um zu einer einfachen und widerspruchsfreien '
          'Elektrodynamik bewegter Körper zu gelangen unter Zugrundelegung der Maxwellschen Theorie für '
          'ruhende Körper.',
 'eisdc': 'Die Einführung eines „Lichtäthers“ wird sich insofern als überflüssig erweisen, als nach der '
          'zu entwickelnden Auffassung weder ein mit besonderen Eigenschaften ausgestatteter „absolut '
          'ruhender Raum“ eingeführt, noch einem Punkte des leeren Raumes, in welchem '
          'elektromagnetische Prozesse stattfinden, ein Geschwindigkeitsvektor zugeordnet wird.',
 'eisdl': 'Die zu entwickelnde Theorie stützt sich — wie jede andere Elektrodynamik — auf die Kinematik '
          'des starren Körpers, da die Aussagen einer jeden Theorie Beziehungen zwischen starren '
          'Körpern (Koordinatensystemen), Uhren und elektromagnetischen Prozessen betreffen.',
 'eisds': 'Die nicht genügende Berücksichtigung dieses Umstandes ist die Wurzel der Schwierigkeiten, '
          'mit denen die Elektrodynamik bewegter Körper gegenwärtig zu kämpfen hat.'}
TOKENS={'eir7': ['Daß',
          'die',
          'Elektrodynamik',
          'Maxwells',
          '—',
          'wie',
          'dieselbe',
          'gegenwärtig',
          'aufgefaßt',
          'zu',
          'werden',
          'pflegt',
          '—',
          'in',
          'ihrer',
          'Anwendung',
          'auf',
          'bewegte',
          'Körper',
          'zu',
          'Asymmetrien',
          'führt,',
          'welche',
          'den',
          'Phänomenen',
          'nicht',
          'anzuhaften',
          'scheinen,',
          'ist',
          'bekannt.'],
 'eir6': ['Man',
          'denke',
          'z.',
          'B.',
          'an',
          'die',
          'elektrodynamische',
          'Wechselwirkung',
          'zwischen',
          'einem',
          'Magneten',
          'und',
          'einem',
          'Leiter.'],
 'eisaj': ['Das',
           'beobachtbare',
           'Phänomen',
           'hängt',
           'hier',
           'nur',
           'ab',
           'von',
           'der',
           'Relativbewegung',
           'von',
           'Leiter',
           'und',
           'Magnet,',
           'während',
           'nach',
           'der',
           'üblichen',
           'Auffassung',
           'die',
           'beiden',
           'Fälle,',
           'daß',
           'der',
           'eine',
           'oder',
           'der',
           'andere',
           'dieser',
           'Körper',
           'der',
           'bewegte',
           'sei,',
           'streng',
           'voneinander',
           'zu',
           'trennen',
           'sind.'],
 'eisaq': ['Bewegt',
           'sich',
           'nämlich',
           'der',
           'Magnet',
           'und',
           'ruht',
           'der',
           'Leiter,',
           'so',
           'entsteht',
           'in',
           'der',
           'Umgebung',
           'des',
           'Magneten',
           'ein',
           'elektrisches',
           'Feld',
           'von',
           'gewissem',
           'Energiewerte,',
           'welches',
           'an',
           'den',
           'Orten,',
           'wo',
           'sich',
           'Teile',
           'des',
           'Leiters',
           'befinden,',
           'einen',
           'Strom',
           'erzeugt.'],
 'eisav': ['Ruht',
           'aber',
           'der',
           'Magnet',
           'und',
           'bewegt',
           'sich',
           'der',
           'Leiter,',
           'so',
           'entsteht',
           'in',
           'der',
           'Umgebung',
           'des',
           'Magneten',
           'kein',
           'elektrisches',
           'Feld,',
           'dagegen',
           'im',
           'Leiter',
           'eine',
           'elektromotorische',
           'Kraft,',
           'welcher',
           'an',
           'sich',
           'keine',
           'Energie',
           'entspricht,',
           'die',
           'aber',
           '—',
           'Gleichheit',
           'der',
           'Relativbewegung',
           'bei',
           'den',
           'beiden',
           'ins',
           'Auge',
           'gefaßten',
           'Fällen',
           'vorausgesetzt',
           '—',
           'zu',
           'elektrischen',
           'Strömen',
           'von',
           'derselben',
           'Größe',
           'und',
           'demselben',
           'Verlaufe',
           'Veranlassung',
           'gibt,',
           'wie',
           'im',
           'ersten',
           'Falle',
           'die',
           'elektrischen',
           'Kräfte.'],
 'eisb4': ['Beispiele',
           'ähnlicher',
           'Art,',
           'sowie',
           'die',
           'mißlungenen',
           'Versuche,',
           'eine',
           'Bewegung',
           'der',
           'Erde',
           'relativ',
           'zum',
           '„Lichtmedium“',
           'zu',
           'konstatieren,',
           'führen',
           'zu',
           'der',
           'Vermutung,',
           'daß',
           'dem',
           'Begriffe',
           'der',
           'absoluten',
           'Ruhe',
           'nicht',
           'nur',
           'in',
           'der',
           'Mechanik,',
           'sondern',
           'auch',
           'in',
           'der',
           'Elektrodynamik',
           'keine',
           'Eigenschaften',
           'der',
           'Erscheinungen',
           'entsprechen,',
           'sondern',
           'daß',
           'vielmehr',
           'für',
           'alle',
           'Koordinatensysteme,',
           'für',
           'welche',
           'die',
           'mechanischen',
           'Gleichungen',
           'gelten,',
           'auch',
           'die',
           'gleichen',
           'elektrodynamischen',
           'und',
           'optischen',
           'Gesetze',
           'gelten,',
           'wie',
           'dies',
           'für',
           'die',
           'Größen',
           'erster',
           'Ordnung',
           'bereits',
           'erwiesen',
           'ist.'],
 'eiscl': ['Wir',
           'wollen',
           'diese',
           'Vermutung',
           '(deren',
           'Inhalt',
           'im',
           'folgenden',
           '„Prinzip',
           'der',
           'Relativität“',
           'genannt',
           'werden',
           'wird)',
           'zur',
           'Voraussetzung',
           'erheben',
           'und',
           'außerdem',
           'die',
           'mit',
           'ihm',
           'nur',
           'scheinbar',
           'unverträgliche',
           'Voraussetzung',
           'einführen,',
           'daß',
           'sich',
           'das',
           'Licht',
           'im',
           'leeren',
           'Raume',
           'stets',
           'mit',
           'einer',
           'bestimmten,',
           'vom',
           'Bewegungszustande',
           'des',
           'emittierenden',
           'Körpers',
           'unabhängigen',
           'Geschwindigkeit',
           '[M0001]',
           'fortpflanze.'],
 'eiscu': ['Diese',
           'beiden',
           'Voraussetzungen',
           'genügen,',
           'um',
           'zu',
           'einer',
           'einfachen',
           'und',
           'widerspruchsfreien',
           'Elektrodynamik',
           'bewegter',
           'Körper',
           'zu',
           'gelangen',
           'unter',
           'Zugrundelegung',
           'der',
           'Maxwellschen',
           'Theorie',
           'für',
           'ruhende',
           'Körper.'],
 'eisdc': ['Die',
           'Einführung',
           'eines',
           '„Lichtäthers“',
           'wird',
           'sich',
           'insofern',
           'als',
           'überflüssig',
           'erweisen,',
           'als',
           'nach',
           'der',
           'zu',
           'entwickelnden',
           'Auffassung',
           'weder',
           'ein',
           'mit',
           'besonderen',
           'Eigenschaften',
           'ausgestatteter',
           '„absolut',
           'ruhender',
           'Raum“',
           'eingeführt,',
           'noch',
           'einem',
           'Punkte',
           'des',
           'leeren',
           'Raumes,',
           'in',
           'welchem',
           'elektromagnetische',
           'Prozesse',
           'stattfinden,',
           'ein',
           'Geschwindigkeitsvektor',
           'zugeordnet',
           'wird.'],
 'eisdl': ['Die',
           'zu',
           'entwickelnde',
           'Theorie',
           'stützt',
           'sich',
           '—',
           'wie',
           'jede',
           'andere',
           'Elektrodynamik',
           '—',
           'auf',
           'die',
           'Kinematik',
           'des',
           'starren',
           'Körpers,',
           'da',
           'die',
           'Aussagen',
           'einer',
           'jeden',
           'Theorie',
           'Beziehungen',
           'zwischen',
           'starren',
           'Körpern',
           '(Koordinatensystemen),',
           'Uhren',
           'und',
           'elektromagnetischen',
           'Prozessen',
           'betreffen.'],
 'eisds': ['Die',
           'nicht',
           'genügende',
           'Berücksichtigung',
           'dieses',
           'Umstandes',
           'ist',
           'die',
           'Wurzel',
           'der',
           'Schwierigkeiten,',
           'mit',
           'denen',
           'die',
           'Elektrodynamik',
           'bewegter',
           'Körper',
           'gegenwärtig',
           'zu',
           'kämpfen',
           'hat.']}
TOKEN_COUNTS={'eir7': 30,
 'eir6': 14,
 'eisaj': 38,
 'eisaq': 35,
 'eisav': 64,
 'eisb4': 71,
 'eiscl': 47,
 'eiscu': 23,
 'eisdc': 41,
 'eisdl': 34,
 'eisds': 21}
SOURCE_UNITS={'einstein-1905:u0003': {'text': 'Daß die Elektrodynamik Maxwells — wie dieselbe gegenwärtig aufgefaßt '
                                 'zu werden pflegt — in ihrer Anwendung auf bewegte Körper zu '
                                 'Asymmetrien führt, welche den Phänomenen nicht anzuhaften scheinen, '
                                 'ist bekannt. Man denke z. B. an die elektrodynamische Wechselwirkung '
                                 'zwischen einem Magneten und einem Leiter. Das beobachtbare Phänomen '
                                 'hängt hier nur ab von der Relativbewegung von Leiter und Magnet, '
                                 'während nach der üblichen Auffassung die beiden Fälle, daß der eine '
                                 'oder der andere dieser Körper der bewegte sei, streng voneinander zu '
                                 'trennen sind. Bewegt sich nämlich der Magnet und ruht der Leiter, so '
                                 'entsteht in der Umgebung des Magneten ein elektrisches Feld von '
                                 'gewissem Energiewerte, welches an den Orten, wo sich Teile des '
                                 'Leiters befinden, einen Strom erzeugt. Ruht aber der Magnet und '
                                 'bewegt sich der Leiter, so entsteht in der Umgebung des Magneten kein '
                                 'elektrisches Feld, dagegen im Leiter eine elektromotorische Kraft, '
                                 'welcher an sich keine Energie entspricht, die aber — Gleichheit der '
                                 'Relativbewegung bei den beiden ins Auge gefaßten Fällen vorausgesetzt '
                                 '— zu elektrischen Strömen von derselben Größe und demselben Verlaufe '
                                 'Veranlassung gibt, wie im ersten Falle die elektrischen Kräfte.',
                         'sha256': '377c76ba06d566e0c4f90424296ba04b0f48a908fa55bfd275c40ac76a5c6fc9'},
 'einstein-1905:u0001': {'text': 'Zur Elektrodynamik bewegter Körper;',
                         'sha256': 'bd613c5b45d24af19c55b0e0ce72f649c7db7ac83e37dd241bdcd035fdc64f1c'},
 'einstein-1905:u0004': {'text': 'Beispiele ähnlicher Art, sowie die mißlungenen Versuche, eine '
                                 'Bewegung der Erde relativ zum „Lichtmedium“ zu konstatieren, führen '
                                 'zu der Vermutung, daß dem Begriffe der absoluten Ruhe nicht nur in '
                                 'der Mechanik, sondern auch in der Elektrodynamik keine Eigenschaften '
                                 'der Erscheinungen entsprechen, sondern daß vielmehr für alle '
                                 'Koordinatensysteme, für welche die mechanischen Gleichungen gelten, '
                                 'auch die gleichen elektrodynamischen und optischen Gesetze gelten, '
                                 'wie dies für die Größen erster Ordnung bereits erwiesen ist. Wir '
                                 'wollen diese Vermutung (deren Inhalt im folgenden „Prinzip der '
                                 'Relativität“ genannt werden wird) zur Voraussetzung erheben und '
                                 'außerdem die mit ihm nur scheinbar unverträgliche Voraussetzung '
                                 'einführen, daß sich das Licht im leeren Raume stets mit einer '
                                 'bestimmten, vom Bewegungszustande des emittierenden Körpers '
                                 'unabhängigen Geschwindigkeit [M0001] fortpflanze. Diese beiden '
                                 'Voraussetzungen genügen, um zu einer einfachen und widerspruchsfreien '
                                 'Elektrodynamik bewegter Körper zu gelangen unter Zugrundelegung der '
                                 'Maxwellschen Theorie für ruhende Körper. Die Einführung eines '
                                 '„Lichtäthers“ wird sich insofern als überflüssig erweisen, als nach '
                                 'der zu entwickelnden Auffassung weder ein mit besonderen '
                                 'Eigenschaften ausgestatteter „absolut ruhender Raum“ eingeführt, noch '
                                 'einem Punkte des leeren Raumes, in welchem elektromagnetische '
                                 'Prozesse stattfinden, ein Geschwindigkeitsvektor zugeordnet wird.',
                         'sha256': 'b0032d8dede15aee361ec5b5ac3ff617f47c896cbfd9e4cdbe06589b7acda3a7'},
 'einstein-1905:u0005': {'text': 'Die zu entwickelnde Theorie stützt sich — wie jede andere '
                                 'Elektrodynamik — auf die Kinematik des starren Körpers, da die '
                                 'Aussagen einer jeden Theorie Beziehungen zwischen starren Körpern '
                                 '(Koordinatensystemen), Uhren und elektromagnetischen Prozessen '
                                 'betreffen. Die nicht genügende Berücksichtigung dieses Umstandes ist '
                                 'die Wurzel der Schwierigkeiten, mit denen die Elektrodynamik bewegter '
                                 'Körper gegenwärtig zu kämpfen hat.',
                         'sha256': '1d9ffc551a1d85cb558700e2eee3f77716228bb3fb68d4d9cc306d816db21662'},
 'einstein-1905:u0006': {'text': 'I. Kinematischer Teil.',
                         'sha256': 'c7b1bc4c49956eab6575b9156f9351600655a3b69e8115887785aa9d9970f3ff'},
 'einstein-1905:u0007': {'text': '§ 1. Definition der Gleichzeitigkeit.',
                         'sha256': '4778c9a9da66d7cc1b8d022af99b21746f3c9584a6787e4b57218eeb85a5f8c0'}}
BOUNDARY_RULE=('Frontmatter title item 1 and author item 2 remain separate from body paragraphs 1..3 and headings '
 '1..2. The second principle sentence crosses pages without creating a boundary; z. B. is internal to '
 'its sentence.')
REVIEWS=('data/einstein-opening-paragraph-review-v1.json',
 'data/electrodynamics-title-review-v1.json',
 'data/einstein-principles-paragraph-review-v1.json',
 'data/einstein-kinematics-paragraph-review-v1.json',
 'data/einstein-kinematics-heading-review-v1.json',
 'data/einstein-simultaneity-heading-review-v1.json')
REVIEW_SELECTION=[{'unit': 'einstein-1905:u0003',
  'review': 'data/einstein-opening-paragraph-review-v1.json',
  'statements': [43, 44, 45, 46, 47]},
 {'unit': 'einstein-1905:u0001',
  'review': 'data/electrodynamics-title-review-v1.json',
  'statements': [48]},
 {'unit': 'einstein-1905:u0004',
  'review': 'data/einstein-principles-paragraph-review-v1.json',
  'statements': [49, 50, 51, 52]},
 {'unit': 'einstein-1905:u0005',
  'review': 'data/einstein-kinematics-paragraph-review-v1.json',
  'statements': [53, 54]},
 {'unit': 'einstein-1905:u0006',
  'review': 'data/einstein-kinematics-heading-review-v1.json',
  'statements': [55]},
 {'unit': 'einstein-1905:u0007',
  'review': 'data/einstein-simultaneity-heading-review-v1.json',
  'statements': [56]}]
READINGS=('data/apparent-asymmetry-basis-v1.json',
 'data/carrier-relative-motion-basis-v1.json',
 'data/charge-transport-capacity-basis-v1.json',
 'data/charge-transport-current-basis-v1.json',
 'data/conductor-cases-basis-v1.json',
 'data/conductor-reading-basis-v1.json',
 'data/conjecture-laws-basis-v1.json',
 'data/current-distribution-basis-v1.json',
 'data/early-individual-reference-reading-v1.json',
 'data/einstein-author-credit-basis-v1.json',
 'data/electric-action-basis-v1.json',
 'data/electric-response-basis-v1.json',
 'data/electrodynamics-title-basis-v1.json',
 'data/ether-dispensability-basis-v1.json',
 'data/interaction-example-basis-v1.json',
 'data/kinematic-difficulties-basis-v1.json',
 'data/kinematic-foundation-basis-v1.json',
 'data/kinematics-headings-basis-v1.json',
 'data/magnet-source-basis-v1.json',
 'data/magnetic-action-basis-v1.json',
 'data/material-body-motion-basis-v1.json',
 'data/material-relative-frame-basis-v1.json',
 'data/moving-conductor-case-basis-v1.json',
 'data/moving-magnet-case-basis-v1.json',
 'data/observable-contrast-basis-v1.json',
 'data/relative-history-match-basis-v1.json',
 'data/relativity-conjecture-basis-v1.json',
 'data/rigid-body-kinematics-basis-v1.json',
 'data/source-action-basis-v1.json',
 'data/sufficient-postulates-basis-v1.json',
 'data/two-postulates-basis-v1.json',
 'data/vacuum-light-postulate-basis-v1.json')
DIAGNOSTIC_VALIDATORS=['scripts/check_apparent_asymmetry.py',
 'scripts/check_conductor_cases.py',
 'scripts/check_conjecture_laws.py',
 'scripts/check_coordinate_correspondence.py',
 'scripts/check_einstein_kinematics_paragraph.py',
 'scripts/check_einstein_opening_paragraph.py',
 'scripts/check_einstein_principles_paragraph.py',
 'scripts/check_electrodynamics_title.py',
 'scripts/check_electrodynamics_title_review.py',
 'scripts/check_ether_dispensability.py',
 'scripts/check_interaction_example.py',
 'scripts/check_kinematic_difficulties.py',
 'scripts/check_kinematic_foundation.py',
 'scripts/check_kinematics_headings.py',
 'scripts/check_material_relative_frame.py',
 'scripts/check_moving_conductor_case.py',
 'scripts/check_moving_magnet_case.py',
 'scripts/check_observable_contrast.py',
 'scripts/check_relativity_conjecture.py',
 'scripts/check_rigid_body_kinematics.py',
 'scripts/check_sufficient_postulates.py',
 'scripts/check_tau_differential.py',
 'scripts/check_two_postulates.py',
 'scripts/check_vacuum_light_postulate.py',
 'scripts/compose_apparent_asymmetry.py',
 'scripts/compose_conductor_cases.py',
 'scripts/compose_conductor_reading.py',
 'scripts/compose_conjecture_laws.py',
 'scripts/compose_current_distribution.py',
 'scripts/compose_electric_action.py',
 'scripts/compose_electric_response.py',
 'scripts/compose_electrodynamics_title.py',
 'scripts/compose_ether_dispensability.py',
 'scripts/compose_field_equations.py',
 'scripts/compose_interaction_example.py',
 'scripts/compose_kinematic_difficulties.py',
 'scripts/compose_kinematic_foundation.py',
 'scripts/compose_kinematics_headings.py',
 'scripts/compose_limits.py',
 'scripts/compose_magnet_source.py',
 'scripts/compose_magnetic_action.py',
 'scripts/compose_material_body_motion.py',
 'scripts/compose_material_relative_frame.py',
 'scripts/compose_moving_conductor_case.py',
 'scripts/compose_moving_magnet_case.py',
 'scripts/compose_observable_contrast.py',
 'scripts/compose_relative_history_match.py',
 'scripts/compose_relativity_conjecture.py',
 'scripts/compose_rest_force.py',
 'scripts/compose_rigid_body_kinematics.py',
 'scripts/compose_source_action.py',
 'scripts/compose_sufficient_postulates.py',
 'scripts/compose_two_postulates.py',
 'scripts/compose_vacuum_light_postulate.py',
 'scripts/review_apparent_asymmetry.py',
 'scripts/review_ether_dispensability.py',
 'scripts/review_interaction_example.py',
 'scripts/review_kinematic_difficulties.py',
 'scripts/review_kinematic_foundation.py',
 'scripts/review_kinematics_headings.py',
 'scripts/review_moving_conductor_case.py',
 'scripts/review_moving_magnet_case.py',
 'scripts/review_observable_contrast.py',
 'scripts/review_relativity_conjecture.py',
 'scripts/review_sufficient_postulates.py',
 'scripts/review_two_postulates.py']
SEMANTIC_REVIEW=['Retain every original definition and complete title, opening comparison, conjecture, postulate, '
 'sufficiency, dispensability, foundation and heading statement.',
 'Thought invitations do not assert actual experiments; customary explanation and observed '
 'relative-motion dependence remain distinct.',
 'Field generation, field energy, magnetic driving and current comparisons preserve their participants, '
 'scopes and reference frames.',
 'Unsuccessful verification does not make its quoted goal false. The medium is hypothetically specified '
 'without asserting physical existence.',
 'Prior establishment to first order remains restricted and is not the same as the full conjecture or '
 'the later propagation postulate.',
 'The expansion parameter keeps its dimensionless velocity ratio, fixed-direction scaling and '
 'all-direction scope as distinct constraints.',
 'Apparent incompatibility is not actual contradiction; theoretical dispensability is not nonexistence.',
 'The title and headings keep their content and document hierarchy separate from positional references.',
 'Role descriptions do not establish existence, uniqueness, truth or a common physical witness. Source '
 'sentence composition remains authoritative.']
OUT=ROOT/'output/einstein-early-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|opening_profile.SOURCE_RELATIONS
MATH=previous.MATH|opening_profile.MATH_ALIASES
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=[*opening_profile.LIMITS,*front_profile.LIMITS,*profile.LIMITS,*SEMANTIC_REVIEW]

_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=EarlyReferenceVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return EarlyReferenceVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==501,'Opening source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','give','fruit','fruit','fruit','fruit','fruit',temporal.PARTS[i//256],temporal.PARTS[(i//16)%16],temporal.PARTS[i%16])),vocabulary())
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
    anchors=author.read('data/early-text-anchors-v1.json')
    doc['declarations']+=text_reference_declarations(anchors,n,voc)
    for old,(node,index) in DESIGNATIONS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri'))))
    doc['declarations']+=voc.imports(set(opening_profile.CONTRACTS)|set(front_profile.EXTRA)|set(profile.EXTRA))
    doc['declarations']+=role_definitions()+forwarder_definitions()
    for old in ROLE_ASSIGNMENTS:
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],
            k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri'))))
    inherited={d['name']:d for d in doc['declarations']}
    for d in renamed([d for d in source_excerpt()['declarations'] if d['name'] in REUSED_DEFINITIONS],m):
        require(inherited.get(d['name'])==d,'Inherited typed definition differs: '+d['name'])
    doc['declarations']+=new_definitions()
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-closing reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-closing reference')
    return REFERENCE_KINDS[old]


def role_definitions():
    role_mapping={n:s for n,s in vocabulary()._symbols.items()}|names()
    planned=build_roles()
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
    result['statements']=renamed(doc['statements'][364:378],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    units={r['id']:r for r in inventory['units']}
    for name,row in SOURCE_UNITS.items():
        require(units[name]['text']==row['text'] and units[name]['text_sha256']==row['sha256'],'Source text boundary changed')
    require(author.read('data/early-text-anchors-v1.json')['sentences']==SENTENCES|{n:__import__('json').loads(__import__('json').dumps(pos)) for n,pos in [('eir7',[1,1]),('eisaj',[1,3])]},'Early paragraph coordinates changed')
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
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations'])
    reading=author.read('data/early-individual-reference-reading-v1.json')
    require(reading['new_visible_designation_forms']==FORMS and reading['designation_anchors']==DESIGNATIONS,'Reviewed designation changed')
    require(not set(FORMS)&{r['symbol'] for r in data.annotations['entries']},'New visible designation shadows a source annotation')
    rows={n:dict(symbol=n,role='designation',forms=[dict(text=t,language='de',role='printed_identifying_form')]) for n,t in FORMS.items()}
    paths=set(data.show()['source_sha256'])|{'data/early-text-anchors-v1.json','data/early-individual-reference-reading-v1.json'}
    return dict(entries={},new_visible_entries=rows,source_identifier_annotations_modified=False,
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
    require(SOURCE_ORDER==[48,47,43,44,45,46,49,50,51,52,53,54,55,56],'Selection changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    contracts=opening_profile.CONTRACTS
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=contracts[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-early-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=SOURCE_UNITS,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        reused_typed_bodies=REUSED_BODIES,new_public_relations=47,new_reference_primitives=1,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=89,core_edition=12,new_source_assertions=14,
        total_source_assertions=282,total_annotations=97,source_reviews=REVIEW_SELECTION,parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,
        document_integration_credit=0,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible opening document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS,'eisbc')}
BASE.update({old:BASE[target] for old,target in {'eir6': 'seatexamplesentence', 'eiscl': 'eighthoriginalprinciplename', 'eisdz': 'firstpartheading'}.items()})
BASE['eirg']='front'
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[first],start,values[last],end,values['ri']):values[n] for n,(first,start,last,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    require(kind=='describedreference','Unknown opening reference kind')
    return TemporalReferences({(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old]
        for old in ROLE_ASSIGNMENTS},{})


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
    frontmatter=front_profile.FrontmatterReferences({(values['eirg'],1):values['eisbc']})
    return result|dict(textpresentation=lambda:values['eirg'],frontmatterreference=frontmatter.reference,headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in tuple(sorted(set(REFERENCE_KINDS.values())))}



def prepare():
    opening_profile.prepare();front_profile.prepare();profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
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
        *READINGS,*REVIEWS,*DIAGNOSTIC_VALIDATORS,'scripts/check_einstein_early_visible.py',
        'scripts/early_individual_reference_roles.py','scripts/early_text_references.py',
        'scripts/visible_early_visible_collection.py','tests/test_early_visible.py',
        'tests/test_early_individual_reference_roles.py','tests/test_early_text_references.py',
        'data/early-text-anchors-v1.json','data/early-individual-reference-reading-v1.json','docs/einstein-early-visible-v1.md'}
    for mod in (opening_profile,front_profile,profile):
        paths.update((mod.LIBRARY,mod.BASIS,mod.MANIFEST))
        stem=mod.__name__.replace('.','/')
        paths.update((stem+'.py',stem+'_contracts.py','tests/test_'+stem.rsplit('/',1)[1]+'.py'))
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved opening bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-early-visible-evidence-1',core_words=375,profile_words=1134,profile_edition=89,
        new_public_relations=47,new_reference_primitives=1,new_source_assertions=14,total_source_assertions=282,annotations=97,
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
