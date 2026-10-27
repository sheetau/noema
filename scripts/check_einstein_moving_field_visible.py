"""Connect physical moving fields and the conditional relativity requirement."""
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
from scripts import moving_field_visible_profile as profile
from scripts.moving_field_visible_profile import ROOT,MovingFieldVisibleVocabulary,write_once
from scripts import check_einstein_field_application_visible as previous
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

SOURCE='examples/v016/einstein-moving-field-visible-v1.noema'
BRIDGE='data/einstein-moving-field-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-moving-field-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[23]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p908-0.jpg',
  'sha256': '511201da1a9dca7175cdbf604c522c5339de25b98b954060e169aee35111f4ac',
  'actually_displayed': True,
  'independent_human_reading': False,
  'observations': ['β指定の終止点の後、Das Relativitätsprinzipから新段落が始まる。前のWenden wirの文とは分かれる。',
                   'wenn sie im System K geltenが条件を置き、同じ文のd. h.以下で電気的・磁気的試験量への作用による二場の定義を説明する。略記d. '
                   'h.とbez.を文の終端にしない。',
                   'プライム付き電気側(X′,Y′,Z′)が先、磁気側(L′,M′,N′)が後。gelten:のコロンに六式が続く。',
                   '六式は三行二列で、電気側の回転の符号と磁気側の逆符号を保持する。次のOffenbarから別段落で比較推論へ進む。']}]
PUBLIC_RELATIONS={'eisps': 'magneticpolestrengthkind',
 'eispt': 'signedtestforceresponse',
 'eispu': 'amountfieldforcecalibration'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['ejtq',
 'ejtr',
 'ejts',
 'ejtt',
 'ejtu',
 'ejtv',
 'ejtw',
 'ejtx',
 'ejty',
 'ejtz',
 'ejt2',
 'ejt3',
 'ejt4',
 'ejt5',
 'ejt6',
 'ejt7',
 'ejua']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'movingfielddefinitionsentence': (72, 1)}
TEXT_SENTENCES={'movingfielddefinitionsentence': (72, 1)}
TOKEN_COUNTS={'movingfielddefinitionsentence': 59}
SENTENCE_SEGMENTS=[{'unit': 'einstein-1905:u0161',
  'text': 'Das Relativitätsprinzip fordert nun, daß die Maxwell-Hertzschen Gleichungen für den leeren Raum '
          'auch im System [M0294] gelten, wenn sie im System [M0295] gelten, d. h. daß für die im bewegten '
          'System [M0296] durch ihre ponderomotorischen Wirkungen auf elektrische bez. magnetische Massen '
          'definierten Vektoren der elektrischen und magnetischen Kraft ([M0297] und [M0298]) des bewegten '
          'Systems [M0299] die Gleichungen gelten:',
  'sha256': 'd49332ea5463a84500dc696bfcdf5d94f6c30db19037d6c2986e615fdb0fc336'},
 {'unit': 'einstein-1905:u0162',
  'text': '[M0300]',
  'sha256': 'ee53e8f28f15655593d2361d2e90958b11f44976e8be69f6aa6ee53e10702da0'}]
EXPECTED_TOKENS=['Das',
 'Relativitätsprinzip',
 'fordert',
 'nun,',
 'daß',
 'die',
 'Maxwell-Hertzschen',
 'Gleichungen',
 'für',
 'den',
 'leeren',
 'Raum',
 'auch',
 'im',
 'System',
 '[M0294]',
 'gelten,',
 'wenn',
 'sie',
 'im',
 'System',
 '[M0295]',
 'gelten,',
 'd.',
 'h.',
 'daß',
 'für',
 'die',
 'im',
 'bewegten',
 'System',
 '[M0296]',
 'durch',
 'ihre',
 'ponderomotorischen',
 'Wirkungen',
 'auf',
 'elektrische',
 'bez.',
 'magnetische',
 'Massen',
 'definierten',
 'Vektoren',
 'der',
 'elektrischen',
 'und',
 'magnetischen',
 'Kraft',
 '([M0297]',
 'und',
 '[M0298])',
 'des',
 'bewegten',
 'Systems',
 '[M0299]',
 'die',
 'Gleichungen',
 'gelten:',
 '[M0300]']
SPANS={'zny': ('movingfielddefinitionsentence', 1, 23),
 'eispy': ('movingfielddefinitionsentence', 24, 58),
 'eispx': ('movingfielddefinitionsentence', 59, 59)}
MULTI_SPANS={}
DESIGNATIONS={'eispv': ('eispy', 1), 'eispw': ('eispy', 2)}
FORMS={'eispv': '(X′,Y′,Z′)', 'eispw': '(L′,M′,N′)'}
ROLE_ASSIGNMENTS={'znt': 'movingvacuumregionrole',
 'znr': 'movingelectricfieldrole',
 'zns': 'movingmagneticfieldrole',
 'znu': 'movinglawrole',
 'znv': 'movinghistoryrole',
 'znw': 'resthistorydescriptionrole',
 'znx': 'movinghistorydescriptionrole'}
REFERENCE_SORTS={'znt': {'kind': 'function',
         'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                        {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                        {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                        {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
         'result': 'truth'},
 'znr': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function',
                    'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                    'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'zns': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function',
                    'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                    'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'znu': 'individual',
 'znv': 'individual',
 'znw': 'individual',
 'znx': 'individual'}
REFERENCE_ANCHORS={'znt': 'zny', 'znr': 'eispv', 'zns': 'eispw', 'znu': 'zny', 'znv': 'zny', 'znw': 'zny', 'znx': 'zny'}
ROLE_DEFINITIONS={'znt': {'kind': 'definition',
         'name': 'movingvacuumregionrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': [{'kind': 'function',
                                                  'parameters': ['number'],
                                                  'result': 'truth'},
                                                 {'kind': 'function',
                                                  'parameters': ['number'],
                                                  'result': 'truth'},
                                                 {'kind': 'function',
                                                  'parameters': ['number'],
                                                  'result': 'truth'},
                                                 {'kind': 'function',
                                                  'parameters': ['number'],
                                                  'result': 'truth'}],
                                  'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'ejsm',
                  'arguments': [{'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                {'kind': 'call', 'symbol': 'ta', 'arguments': []},
                                {'kind': 'call', 'symbol': 'rb', 'arguments': []},
                                {'kind': 'variable', 'name': 'vb'},
                                {'kind': 'variable', 'name': 'va'}]}},
 'znr': {'kind': 'definition',
         'name': 'movingelectricfieldrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['individual'],
                                  'result': {'kind': 'function',
                                             'parameters': [{'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'},
                                                            {'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'},
                                                            {'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'},
                                                            {'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'}],
                                             'result': {'kind': 'function',
                                                        'parameters': ['number'],
                                                        'result': 'truth'}}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': 'individual',
                  'body': {'kind': 'exists',
                           'variable': 'vd',
                           'sort': 'individual',
                           'body': {'kind': 'exists',
                                    'variable': 've',
                                    'sort': 'individual',
                                    'body': {'kind': 'exists',
                                             'variable': 'vf',
                                             'sort': {'kind': 'function',
                                                      'parameters': ['number'],
                                                      'result': 'truth'},
                                             'body': {'kind': 'exists',
                                                      'variable': 'vg',
                                                      'sort': {'kind': 'function',
                                                               'parameters': [{'kind': 'function',
                                                                               'parameters': ['individual'],
                                                                               'result': {'kind': 'function',
                                                                                          'parameters': ['number'],
                                                                                          'result': 'truth'}},
                                                                              {'kind': 'function',
                                                                               'parameters': ['number'],
                                                                               'result': 'truth'}],
                                                               'result': {'kind': 'function',
                                                                          'parameters': ['individual'],
                                                                          'result': {'kind': 'function',
                                                                                     'parameters': ['number'],
                                                                                     'result': 'truth'}}},
                                                      'body': {'kind': 'call',
                                                               'symbol': 'ejts',
                                                               'arguments': [{'kind': 'call',
                                                                              'symbol': 'zor',
                                                                              'arguments': []},
                                                                             {'kind': 'call',
                                                                              'symbol': 'zbm',
                                                                              'arguments': []},
                                                                             {'kind': 'call',
                                                                              'symbol': 'ta',
                                                                              'arguments': []},
                                                                             {'kind': 'call',
                                                                              'symbol': 'rb',
                                                                              'arguments': []},
                                                                             {'kind': 'variable',
                                                                              'name': 'vc'},
                                                                             {'kind': 'variable',
                                                                              'name': 'vd'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'znt',
                                                                              'arguments': []},
                                                                             {'kind': 'variable',
                                                                              'name': 'vb'},
                                                                             {'kind': 'variable',
                                                                              'name': 'vg'},
                                                                             {'kind': 'variable',
                                                                              'name': 've'},
                                                                             {'kind': 'variable',
                                                                              'name': 'vf'},
                                                                             {'kind': 'variable',
                                                                              'name': 'va'}]}}}}}}},
 'zns': {'kind': 'definition',
         'name': 'movingmagneticfieldrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['individual'],
                                  'result': {'kind': 'function',
                                             'parameters': [{'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'},
                                                            {'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'},
                                                            {'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'},
                                                            {'kind': 'function',
                                                             'parameters': ['number'],
                                                             'result': 'truth'}],
                                             'result': {'kind': 'function',
                                                        'parameters': ['number'],
                                                        'result': 'truth'}}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': 'individual',
                  'body': {'kind': 'exists',
                           'variable': 'vd',
                           'sort': 'individual',
                           'body': {'kind': 'exists',
                                    'variable': 've',
                                    'sort': 'individual',
                                    'body': {'kind': 'exists',
                                             'variable': 'vf',
                                             'sort': {'kind': 'function',
                                                      'parameters': ['number'],
                                                      'result': 'truth'},
                                             'body': {'kind': 'exists',
                                                      'variable': 'vg',
                                                      'sort': {'kind': 'function',
                                                               'parameters': [{'kind': 'function',
                                                                               'parameters': ['individual'],
                                                                               'result': {'kind': 'function',
                                                                                          'parameters': ['number'],
                                                                                          'result': 'truth'}},
                                                                              {'kind': 'function',
                                                                               'parameters': ['number'],
                                                                               'result': 'truth'}],
                                                               'result': {'kind': 'function',
                                                                          'parameters': ['individual'],
                                                                          'result': {'kind': 'function',
                                                                                     'parameters': ['number'],
                                                                                     'result': 'truth'}}},
                                                      'body': {'kind': 'call',
                                                               'symbol': 'ejts',
                                                               'arguments': [{'kind': 'call',
                                                                              'symbol': 'eisps',
                                                                              'arguments': []},
                                                                             {'kind': 'call',
                                                                              'symbol': 'zbm',
                                                                              'arguments': []},
                                                                             {'kind': 'call',
                                                                              'symbol': 'ta',
                                                                              'arguments': []},
                                                                             {'kind': 'call',
                                                                              'symbol': 'rb',
                                                                              'arguments': []},
                                                                             {'kind': 'variable',
                                                                              'name': 'vc'},
                                                                             {'kind': 'variable',
                                                                              'name': 'vd'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'znt',
                                                                              'arguments': []},
                                                                             {'kind': 'variable',
                                                                              'name': 'vb'},
                                                                             {'kind': 'variable',
                                                                              'name': 'vg'},
                                                                             {'kind': 'variable',
                                                                              'name': 've'},
                                                                             {'kind': 'variable',
                                                                              'name': 'vf'},
                                                                             {'kind': 'variable',
                                                                              'name': 'va'}]}}}}}}},
 'znu': {'kind': 'definition',
         'name': 'movinglawrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': 'individual',
                  'body': {'kind': 'call',
                           'symbol': 'eisle',
                           'arguments': [{'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'va'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'znv': {'kind': 'definition',
         'name': 'movinghistoryrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': 'individual',
                  'body': {'kind': 'call',
                           'symbol': 'eislf',
                           'arguments': [{'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'va'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'znw': {'kind': 'definition',
         'name': 'resthistorydescriptionrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'vh',
                  'arguments': [{'kind': 'call', 'symbol': 'znv', 'arguments': []},
                                {'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'},
                                {'kind': 'variable', 'name': 'vb'}]}},
 'znx': {'kind': 'definition',
         'name': 'movinghistorydescriptionrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'vh',
                  'arguments': [{'kind': 'call', 'symbol': 'znv', 'arguments': []},
                                {'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'},
                                {'kind': 'variable', 'name': 'vb'}]}}}
LOCAL_NAMES=['ejtq',
 'ejtr',
 'ejts',
 'ejtt',
 'ejtu',
 'ejtv',
 'ejtw',
 'ejtx',
 'ejty',
 'ejtz',
 'ejt2',
 'ejt3',
 'ejt4',
 'ejt5',
 'ejt6',
 'ejt7',
 'ejua',
 'znr',
 'zns',
 'znt',
 'znu',
 'znv',
 'znw',
 'znx',
 'zny',
 'eispv',
 'eispw',
 'eispx',
 'eispy',
 'movingfielddefinitionsentence',
 'movingvacuumregionrole',
 'movingelectricfieldrole',
 'movingmagneticfieldrole',
 'movinglawrole',
 'movinghistoryrole',
 'resthistorydescriptionrole',
 'movinghistorydescriptionrole']
READINGS=('data/einstein-moving-field-definition-source-reading-v1.json',)
REVIEWS=('data/einstein-moving-field-definition-u0161-review-v1.json',
 'data/einstein-moving-field-definition-u0162-review-v1.json')
SEMANTIC_REVIEW=['u0161–u0162を原刊908頁で一文として読む。相対性原理が要求する条件文、d. h.の言い換え、同じ移動系の場の物理的定義、六式を保持する。',
 '電気的質量は符号付き電荷、磁気的質量は符号付き磁極強度を担う試験系と読む。磁極は歴史的な局所的理想化で、孤立磁荷の発見や慣性質量、磁石全体の合力を主張しない。',
 '場は同じ系に静止した試験系への局所的な機械力の一次応答により同定する。試験系を小さくして元の場への影響を除く規約を明示し、実際の試験体によって真空を占有したとはしない。極限手順を実験した証明ではなく、基本量の物理的同定規約である。',
 '同じ地点時刻、量種・単位、正負の試験量と三成分を合成する。二つの新しい一般関係は物理的な理想応答の帰属と単位積の校正であり、文全体を一基本記号へ隠さない。',
 '第一原理の現在の定式化eionと同じ本体で、一つの理論の全適格系対・全法則・全候補記述と個別適用を共有する。適用条件は明示した読みであり、原文が条件を別々に列挙したとはしない。',
 '移動系の新しい二場znr/znsと領域zntを維持し、前文のs6k/s6lとの等値、共通係数、同じ六式だけから成分が比例するという後続主張は先取りしない。',
 '表示六式は原理の条件付き要求の具体化として読む。著者の導出提示と内容の真偽・推論の自動証明を区別し、全実数・全関数域の有限列挙拒否を保つ。',
 '旧文154以外の357主張と旧意味規約・証拠を保持する。旧znr/znsの意味規約に残る未完という履歴説明は上書きせず、現在の物理的定義はejtu以下で接続する。']
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
        chain=MovingFieldVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return MovingFieldVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==149,'Moving-field source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','aki',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    inherited={d['name']:d for d in doc['declarations']}
    for d in renamed([d for d in source_excerpt()['declarations'] if d['name'] in REUSED_DEFINITIONS],m):
        require(inherited.get(d['name'])==d,'Inherited mathematical definition differs: '+d['name'])
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown moving-field reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown moving-field reference')
    if old=='znt':return 'describedfourcuttruthfunctionreference'
    if old in ('znr','zns'):return 'describedindividualfourcutfunctionfamilyreference'
    return 'describedreference'


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
    result['statements']=renamed(doc['statements'][196:197],inverse);return normalize_document(result)



def text_boundaries():
    prior=previous.text_boundaries()['sentences']['fieldapplicationsentence']
    require(prior['position']==[71,1] and SENTENCES=={'movingfielddefinitionsentence':(72,1)},'Paragraph sequence changed')
    inventory=author.read(author.UNITS)['units'];units={u['id']:u for u in inventory}
    for row in SENTENCE_SEGMENTS:
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['sha256'],'Moving-field sentence segment changed')
    text=' '.join(r['text'] for r in SENTENCE_SEGMENTS);tokens=text.split()
    require(tokens==EXPECTED_TOKENS and len(tokens)==59,'Moving-field sentence tokens changed')
    require(SPANS=={'zny':('movingfielddefinitionsentence',1,23),'eispy':('movingfielddefinitionsentence',24,58),'eispx':('movingfielddefinitionsentence',59,59)},'Moving-field clause boundary changed')
    require(tokens[23:26]==['d.','h.','daß'] and tokens[-2:]==['gelten:','[M0300]'],'Explanation/display continuation changed')
    require(DESIGNATIONS=={'eispv':('eispy',1),'eispw':('eispy',2)} and FORMS=={'eispv':'(X′,Y′,Z′)','eispw':'(L′,M′,N′)'},'Physical field designation order changed')
    require(units['einstein-1905:u0160']['text']=='[M0293]' and units['einstein-1905:u0163']['text'].startswith('Offenbar'),'Adjacent sentence boundary changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph72 sentence1 joins the conditional requirement, its d. h. explanation, two ordered field designations, and six displayed equations. Abbreviations do not end the sentence; the subsequent Offenbar paragraph is separate.',
        sentences={'movingfielddefinitionsentence':dict(position=[72,1],tokens=tokens,text=text,segments=SENTENCE_SEGMENTS)},
        spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},designations={n:list(p) for n,p in DESIGNATIONS.items()},designation_forms=FORMS)



def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math={};coverage={}
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Moving field source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(161,163)}
    require(set(coverage)==expected,'Moving field source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old field application review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old field application review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Moving field review coverage differs')
    require(SOURCE_ORDER==[23],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Moving field source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-moving-field-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=3,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=69,core_edition=12,new_source_assertions=1,total_source_assertions=161,total_annotations=38,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible moving-field document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    from scripts.four_coordinate_visible_profile import IndividualFourCutFamilyReferences
    from scripts.vacuum_assumption_visible_profile import FourCutTruthFunctionReferences
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(roles,{})
    if kind=='describedfourcuttruthfunctionreference':return FourCutTruthFunctionReferences(roles)
    require(kind=='describedindividualfourcutfunctionfamilyreference','Unknown moving-field reference type')
    return IndividualFourCutFamilyReferences(roles)


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
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedfourcuttruthfunctionreference','describedindividualfourcutfunctionfamilyreference')}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-field-application-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/moving_field_visible_profile.py','scripts/moving_field_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_moving_field_visible.py','scripts/visible_moving_field_visible_collection.py',
        'tests/test_moving_field_visible.py','docs/einstein-moving-field-visible-v1.md'}
    for name in ('moving_field_definition',):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved moving-field bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-moving-field-visible-evidence-1',core_words=375,profile_words=878,profile_edition=69,
        new_public_relations=3,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=161,annotations=38,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
