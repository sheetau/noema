"""Connect asymmetry resolution, the machine annotation and inquiry-premise rejection."""
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
from scripts import seat_questions_visible_profile as profile
from scripts.seat_questions_visible_profile import ROOT,SeatQuestionsVisibleVocabulary,write_once
from scripts import check_einstein_magnetic_auxiliary_visible as previous
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

SOURCE='examples/v016/einstein-seat-questions-visible-v1.noema'
BRIDGE='data/einstein-seat-questions-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-seat-questions-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[196, 197, 198]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg',
  'observations': ['Analoges段落の次の独立段落は二文。fernerとAuch、Sitzの引用符、単極機の括弧、gegenstandslosを照合。'],
  'sha256': 'e634a38acf3bf76e5d99086296c70a267368c684501148cc789ede1def276ea5',
  'actually_displayed': True,
  'independent_human_reading': False,
  'inspection': 'Displayed with view_image during the seat-questions planning '
                'turn; paired shell chunks 8ab9ba and 791674 respectively.'},
 {'path': 'artifacts/einstein-opening-v1/page-891.jpg',
  'observations': ['本文第一段落の最初の三文と仮定的な磁石・導体・結合設定、通常の見方の句を照合。z. B.の略記で文を分割しない。'],
  'sha256': '715ba57296f3c1535e1122f7ea63844a3b163301d0ba1a0be7dd55c05dbd5382',
  'actually_displayed': True,
  'independent_human_reading': False,
  'inspection': 'Displayed with view_image during the seat-questions planning '
                'turn; paired shell chunks 8ab9ba and 791674 respectively.'}]
PUBLIC_RELATIONS={'zrdpossible': 'physicalpossibleresults',
 'eirk': 'materialpreservingtrial',
 'eirp': 'transportassessmentstandard',
 'eirq': 'electricaldrivingtrial',
 'eirr': 'trialtransportresponse',
 'eirs': 'motioncomparisonpreparation',
 'eirw': 'bodyelectromagneticfields',
 'eirx': 'internalmagneticsourcestate',
 'eiry': 'sourceattributedforce',
 'eirz': 'electromagneticcouplingprocess',
 'eisad': 'physicalcomparisoncase',
 'eisae': 'observabletransporthistory',
 'eisaf': 'permittedexplanatoryaccount',
 'eisag': 'explanatorymechanismclassification',
 'eisah': 'customarytheoreticalview',
 'eisay': 'theoryinterpretationview',
 'eisaz': 'motiontheoryapplication',
 'eisa2': 'observablemotiondistinction',
 'eisa3': 'appearanceassessmentcandidate',
 'eisq5': 'relativemotioncurrentgeneration',
 'eisra': 'priortopicresumption',
 'eisrb': 'additivecontentpresentation',
 'eisrc': 'availabledeviceoperation',
 'eisrd': 'rotationalinductionoutput',
 'eisre': 'closedconductivepath',
 'eisrf': 'slidingconductivecontact',
 'eisrg': 'unwrappedrotationturns',
 'eisrj': 'expressionclassinterpretation',
 'eisrk': 'sourceinquirysetting',
 'eisrl': 'proposedoriginsite',
 'eisrm': 'autonomousphysicalsource',
 'eisrn': 'physicalsourcesite',
 'eisro': 'inquiryrequiredpremise',
 'eisrp': 'theoryrejectspremise',
 'eisrq': 'premisedinquirypractice',
 'eisrr': 'parentheticaltopicapplication'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['s7s',
 'eiak',
 'eial',
 'eian',
 'eiao',
 'eiap',
 'eiaq',
 'eiar',
 'eiav',
 'eiaw',
 'eiax',
 'eiay',
 'eiaz',
 'eia2',
 'eibg',
 'eibk',
 'eice',
 'eicf',
 'eicg',
 'eich',
 'eici',
 'eicj',
 'eicq',
 'eicr',
 'eics',
 'eicw',
 'eida',
 'eidd',
 'eide',
 'eidf',
 'eidh',
 'eieu',
 'eiev',
 'eiew',
 'eiex',
 'eiey',
 'eiez',
 'ejz5',
 'ejz6',
 'ejz7',
 'ekaa',
 'ekab',
 'ekac',
 'ekad',
 'ekae',
 'ekaf',
 'ekag',
 'ekah',
 'ekai',
 'ekaj',
 'ekak',
 'ekal',
 'ekam',
 'ekan',
 'ekao',
 'ekap',
 'ekaq',
 'ekar',
 'ekas']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'eir7': [1, 1],
 'seatexamplesentence': [1, 2],
 'eisaj': [1, 3],
 'eisq7': [80, 1],
 'eisrs': [80, 2]}
TEXT_SENTENCES={'eir7': 'Daß die Elektrodynamik Maxwells — wie dieselbe gegenwärtig aufgefaßt '
         'zu werden pflegt — in ihrer Anwendung auf bewegte Körper zu '
         'Asymmetrien führt, welche den Phänomenen nicht anzuhaften scheinen, '
         'ist bekannt.',
 'seatexamplesentence': 'Man denke z. B. an die elektrodynamische '
                        'Wechselwirkung zwischen einem Magneten und einem '
                        'Leiter.',
 'eisaj': 'Das beobachtbare Phänomen hängt hier nur ab von der Relativbewegung '
          'von Leiter und Magnet, während nach der üblichen Auffassung die '
          'beiden Fälle, daß der eine oder der andere dieser Körper der '
          'bewegte sei, streng voneinander zu trennen sind.',
 'eisq7': 'Es ist ferner klar, daß die in der Einleitung angeführte Asymmetrie '
          'bei der Betrachtung der durch Relativbewegung eines Magneten und '
          'eines Leiters erzeugten Ströme verschwindet.',
 'eisrs': 'Auch werden die Fragen nach dem „Sitz“ der elektrodynamischen '
          'elektromotorischen Kräfte (Unipolarmaschinen) gegenstandslos.',
 'magauxsecondsentence': 'Man sieht, daß in der entwickelten Theorie die '
                         'elektromotorische Kraft nur die Rolle eines '
                         'Hilfsbegriffes spielt, welcher seine Einführung dem '
                         'Umstande verdankt, daß die elektrischen und '
                         'magnetischen Kräfte keine von dem Bewegungszustande '
                         'des Koordinatensystems unabhängige Existenz '
                         'besitzen.'}
SPANS={'zpw': ['magauxsecondsentence', 17, 37],
 'seatmagnetanchor': ['seatexamplesentence', 10, 11],
 'seatconductoranchor': ['seatexamplesentence', 13, 14],
 'seatprocessanchor': ['seatexamplesentence', 7, 8],
 'seatcustomaryviewanchor': ['eisaj', 18, 19],
 'eisri': ['eisrs', 12, 12]}
MULTI_SPANS={}
TOKEN_COUNTS={'eir7': 30,
 'seatexamplesentence': 14,
 'eisaj': 38,
 'eisq7': 25,
 'eisrs': 13,
 'magauxsecondsentence': 37}
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
 'seatexamplesentence': ['Man',
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
 'eisq7': ['Es',
           'ist',
           'ferner',
           'klar,',
           'daß',
           'die',
           'in',
           'der',
           'Einleitung',
           'angeführte',
           'Asymmetrie',
           'bei',
           'der',
           'Betrachtung',
           'der',
           'durch',
           'Relativbewegung',
           'eines',
           'Magneten',
           'und',
           'eines',
           'Leiters',
           'erzeugten',
           'Ströme',
           'verschwindet.'],
 'eisrs': ['Auch',
           'werden',
           'die',
           'Fragen',
           'nach',
           'dem',
           '„Sitz“',
           'der',
           'elektrodynamischen',
           'elektromotorischen',
           'Kräfte',
           '(Unipolarmaschinen)',
           'gegenstandslos.'],
 'magauxsecondsentence': ['Man',
                          'sieht,',
                          'daß',
                          'in',
                          'der',
                          'entwickelten',
                          'Theorie',
                          'die',
                          'elektromotorische',
                          'Kraft',
                          'nur',
                          'die',
                          'Rolle',
                          'eines',
                          'Hilfsbegriffes',
                          'spielt,',
                          'welcher',
                          'seine',
                          'Einführung',
                          'dem',
                          'Umstande',
                          'verdankt,',
                          'daß',
                          'die',
                          'elektrischen',
                          'und',
                          'magnetischen',
                          'Kräfte',
                          'keine',
                          'von',
                          'dem',
                          'Bewegungszustande',
                          'des',
                          'Koordinatensystems',
                          'unabhängige',
                          'Existenz',
                          'besitzen.']}
DESIGNATIONS={}
FORMS={}
INHERITED_DESIGNATIONS={}
ROLE_ASSIGNMENTS={'eisaa': 'seatroleeisaa',
 'eisab': 'seatroleeisab',
 'eisac': 'seatroleeisac',
 'eisak': 'seatcustomaryviewrole',
 'eisq6': 'seatdevelopedviewrole',
 'eisrh': 'seatmachineexpressionrole'}
REFERENCE_SORTS={'eisaa': 'individual',
 'eisab': 'individual',
 'eisac': 'individual',
 'eisak': 'individual',
 'eisq6': 'individual',
 'eisrh': 'individual'}
REFERENCE_ANCHORS={'eisaa': 'seatmagnetanchor',
 'eisab': 'seatconductoranchor',
 'eisac': 'seatprocessanchor',
 'eisak': 'seatcustomaryviewanchor',
 'eisq6': 'eisq7',
 'eisrh': 'eisri'}
ROLE_DEFINITIONS={'eisaa': {'kind': 'definition',
           'name': 'seatroleeisaa',
           'parameters': [{'name': 'va', 'sort': 'individual'},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisd3',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'seatmagnetanchor',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'va'},
                                  {'kind': 'call',
                                   'symbol': 'eirf',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'vb'}]}},
 'eisab': {'kind': 'definition',
           'name': 'seatroleeisab',
           'parameters': [{'name': 'va', 'sort': 'individual'},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisd3',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'seatconductoranchor',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'va'},
                                  {'kind': 'call',
                                   'symbol': 'eirf',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'vb'}]}},
 'eisac': {'kind': 'definition',
           'name': 'seatroleeisac',
           'parameters': [{'name': 'va', 'sort': 'individual'},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisd3',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'seatprocessanchor',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'va'},
                                  {'kind': 'call',
                                   'symbol': 'eirf',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'vb'}]}},
 'eisak': {'kind': 'definition',
           'name': 'seatcustomaryviewrole',
           'parameters': [{'name': 'va', 'sort': 'individual'},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisah',
                    'arguments': [{'kind': 'variable', 'name': 'va'},
                                  {'kind': 'call',
                                   'symbol': 'eirf',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'vb'}]}},
 'eisq6': {'kind': 'definition',
           'name': 'seatdevelopedviewrole',
           'parameters': [{'name': 'va', 'sort': 'individual'},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisay',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisqw',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'va'},
                                  {'kind': 'call',
                                   'symbol': 'eirf',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'vb'}]}},
 'eisrh': {'kind': 'definition',
           'name': 'seatmachineexpressionrole',
           'parameters': [{'name': 'va', 'sort': 'individual'},
                          {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'eisrj',
                    'arguments': [{'kind': 'variable', 'name': 'va'},
                                  {'kind': 'quote',
                                   'body': {'kind': 'function_ref',
                                            'symbol': 'ekaj'}},
                                  {'kind': 'call',
                                   'symbol': 'eirf',
                                   'arguments': []},
                                  {'kind': 'call',
                                   'symbol': 'eisri',
                                   'arguments': []},
                                  {'kind': 'variable', 'name': 'vb'}]}}}
LOCAL_NAMES=['eir7',
 'seatexamplesentence',
 'eisaj',
 'eisq7',
 'eisrs',
 'zpw',
 'seatmagnetanchor',
 'seatconductoranchor',
 'seatprocessanchor',
 'seatcustomaryviewanchor',
 'eisri',
 'eisrh',
 'eisaa',
 'eisab',
 'eisac',
 'eisak',
 'eisq6',
 'seatroleeisaa',
 'seatroleeisab',
 'seatroleeisac',
 'seatcustomaryviewrole',
 'seatdevelopedviewrole',
 's7s',
 'eiak',
 'eial',
 'eian',
 'eiao',
 'eiap',
 'eiaq',
 'eiar',
 'eiav',
 'eiaw',
 'eiax',
 'eiay',
 'eiaz',
 'eia2',
 'eibg',
 'eibk',
 'eice',
 'eicf',
 'eicg',
 'eich',
 'eici',
 'eicj',
 'eicq',
 'eicr',
 'eics',
 'eicw',
 'eida',
 'eidd',
 'eide',
 'eidf',
 'eidh',
 'eieu',
 'eiev',
 'eiew',
 'eiex',
 'eiey',
 'eiez',
 'ejz5',
 'ejz6',
 'ejz7',
 'ekaa',
 'ekab',
 'ekac',
 'ekad',
 'ekae',
 'ekaf',
 'ekag',
 'ekah',
 'ekai',
 'ekaj',
 'ekak',
 'ekal',
 'ekam',
 'ekan',
 'ekao',
 'ekap',
 'ekaq',
 'ekar',
 'ekas',
 'seatmachineexpressionrole']
READINGS=('data/einstein-seat-questions-source-reading-v1.json',
 'data/einstein-opening-source-reading-v1.json',
 'data/einstein-auxiliary-reference-order-reading-v1.json')
REVIEWS=('data/einstein-seat-questions-u0177-review-v1.json',)
SEMANTIC_REVIEW=['導体の許容試行・可能結果・応答・評価基準・持続を分ける。未知を許容済みや成功済みへ補わない。',
 '同じ物質点・相対履歴・準備・場の源・電荷と時間の単位・全有向断面を保つ。生成への帰属は数値一致から導かない。',
 '非対称性解消は新理論の全許容説明の共通機構への接続。序文への後方参照と追加提示は先行の真理や論理的導出ではない。',
 '単極機は既存ekajの装置構成。回転と滑り接触、固定経路、局所磁気作用、仕事/電荷と極性の履歴を保つ。実在装置や全条件での成功は要求しない。',
 'Sitzは自立した作用源の場所を求める採用解釈。一般の局所力の位置を問うことまで否定しない。',
 'gegenstandslosは必要前提の理論的拒絶。無回答、不明、候補集合の空性、単なる前提の偽とは区別する。',
 'werdenは理論移行による問いの扱いの変化。力の時間的消滅ではない。全適用設定の非空性・網羅性・同じ概念を保持する。',
 '括弧は適用先の装置類を指定するが全問題をその類だけへ限定しない。閉じた引用は自動実行しない。',
 '談話上の対象導入は同じ名詞句からの参照取得であり、磁石・導体・相互作用の物理的実在や成立を追加しない。',
 '物理的性質は引用された既存定義eicr/eici/eicw等の条件内に保持する。',
 '通常の見方eisakと展開した理論の見方eisq6を区別する。eisayの引数順序はtheory,view,document,reference。',
 'zpwは前段第二文17..37の導入理由を述べる相対節。既存zptの23..37とは同一視しない。',
 'eisrhは一般の装置類を指す表現。eisrjの閉じた語義注記を役割として参照し、新しい名称の採用・印刷名称の注記を追加しない。']
PARENT_BINDING='reports/auxiliary-reference-order-visible-parent-binding-v1.json'
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
        chain=SeatQuestionsVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return SeatQuestionsVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==431,'Seat-questions source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','town',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown seat-questions reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown seat-questions reference')
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
    result['statements']=renamed(doc['statements'][221:224],inverse);return normalize_document(result)



def text_boundaries():
    reading=author.read(READINGS[0]);opening=author.read(READINGS[1]);prior=author.read(READINGS[2])
    require(SENTENCES=={'eir7':[1,1],'seatexamplesentence':[1,2],'eisaj':[1,3],'eisq7':[80,1],'eisrs':[80,2]},'Adopted paragraph division changed')
    expected={old:opening['body_sentence_ranges'][i]['text'] for i,old in enumerate(('eir7','seatexamplesentence','eisaj'))}
    expected.update(eisq7=reading['text'][:177],eisrs=reading['text'][178:],magauxsecondsentence=prior['locations']['magauxsecondsentence']['text'])
    require(TEXT_SENTENCES==expected and reading['text'][177]==' ','Sentence or prior clause changed')
    for old,sentence in TEXT_SENTENCES.items():
        require(sentence.split()==TOKENS[old] and len(TOKENS[old])==TOKEN_COUNTS[old],'Token boundary changed')
    phrases={'zpw':'welcher seine Einführung dem Umstande verdankt, daß die elektrischen und magnetischen Kräfte keine von dem Bewegungszustande des Koordinatensystems unabhängige Existenz besitzen.',
        'seatmagnetanchor':'einem Magneten','seatconductoranchor':'einem Leiter.',
        'seatprocessanchor':'elektrodynamische Wechselwirkung','seatcustomaryviewanchor':'üblichen Auffassung','eisri':'(Unipolarmaschinen)'}
    for old,(node,start,end) in SPANS.items():
        require(' '.join(TOKENS[node][start-1:end])==phrases[old],'Reference span changed')
    require(not FORMS and not DESIGNATIONS,'Ordinary class expression became an adopted designation')
    require(TOKENS['eisrs'][11]=='(Unipolarmaschinen)','Parenthetical expression moved')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Original facsimile changed')
    return dict(rule='Body paragraph 1 contains the five introductory sentences; abbreviation z. B. does not split sentence 2. Paragraph 80 follows paragraph 79 and precedes section 7.',
        sentences=TEXT_SENTENCES,coordinates=SENTENCES,tokens=TOKENS,spans=SPANS,
        designations=DESIGNATIONS,designation_forms=FORMS,source_locations=reading['clauses'])



def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];review=author.read(REVIEWS[0]);reading=author.read(READINGS[0])
    require(c.document_path=='examples/v014/einstein-auxiliary-reference-order-v1.noema','Unreviewed source selection')
    require(review['decision']=='equivalent_under_stated_reading' and not review['unresolved'],'Source review incomplete')
    require(review['source']['text']==reading['text'] and review['source']['unit_sha256']==reading['unit_sha256'],'Source evidence differs')
    require(SOURCE_ORDER==[196,197,198],'Selection changed')
    require([s['body']['symbol'] for s in source_excerpt()['statements']]==['ekaf','ekak','ekas'],'Reviewed roots changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-seat-questions-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units={reading['unit']:dict(sha256=reading['unit_sha256'],text=reading['text'],range=reading['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),math=[],annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        new_public_relations=36,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=75,core_edition=12,new_source_assertions=3,total_source_assertions=184,total_annotations=40,
        source_review=REVIEWS[0],parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible seat-questions document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    from scripts.field_symmetry_visible_profile import IndividualCutFunctionReferences
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(roles,{})
    require(kind=='describedindividualcutfunctionreference','Unknown seat-questions reference type')
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
        own={(values['eirf'],values[node],a,values[node],b,values['ri']) for node,a,b in SPANS.values()}
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
        'scripts/seat_questions_visible_profile.py','scripts/seat_questions_visible_profile_contracts.py',
        'scripts/check_einstein_seat_questions_visible.py','scripts/visible_seat_questions_visible_collection.py',
        'tests/test_seat_questions_visible.py','docs/einstein-seat-questions-visible-v1.md'}
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved seat-questions bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-seat-questions-visible-evidence-1',core_words=375,profile_words=935,profile_edition=75,
        new_public_relations=36,new_reference_primitives=0,new_source_assertions=3,total_source_assertions=184,annotations=40,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
