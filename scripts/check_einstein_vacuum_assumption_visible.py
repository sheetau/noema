"""Connect the vacuum assumption, six equations and two vector designations."""
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
from scripts import vacuum_assumption_visible_profile as profile
from scripts.vacuum_assumption_visible_profile import ROOT,VacuumAssumptionVisibleVocabulary,write_once
from scripts import check_einstein_sixth_heading_visible as previous
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

SOURCE='examples/v016/einstein-vacuum-assumption-visible-v1.noema'
BRIDGE='data/einstein-vacuum-assumption-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-vacuum-assumption-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[21]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg',
  'sha256': '82cc01197ef77b18fa71b3cd625580cbce8171a78af66be70df05a20311443e5',
  'actually_displayed': True,
  'independent_human_reading': False,
  'observations': ['907頁の第六節見出しの直下にDie Maxwell-Hertzschenからgelten möge:までの仮定導入がある。Kはruhende Systemの直後に置かれる。',
                   '続く表示式は三行二列の六式。左列はX,Y,Zの時間微分、右列はL,M,Nの時間微分で、全て左辺に1/Vを持つ。',
                   '右辺は順にN_y-M_z、L_z-N_x、M_x-L_y、およびY_z-Z_y、Z_x-X_z、X_y-Y_x。既存s5wの電気側正回転・磁気側負回転と一致する。',
                   '式の直後の小文字wobeiが同じ文を続け、(X,Y,Z)を電気側、(L,M,N)を磁気側のベクトルとして説明し、bedeutet.で文を閉じる。',
                   '次のWenden wirからは別の変換適用の文。今回の三箇所には含めない。']}]
PUBLIC_RELATIONS={'uf': 'authorexplainsby', 'eispi': 'threecomponentfielddesignation'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['ejsx', 'ejsy', 'ejsz', 'ejs2', 'ejs3', 'ejs4', 'ejs5', 'ejs6', 'ejs7', 'ejta', 'ejtb', 'ejtc', 'ejtd']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={}
TEXT_SENTENCES={'sixthopeningsentence': (70, 1)}
TOKEN_COUNTS={'sixthopeningsentence': 32}
SENTENCE_SEGMENTS=[{'unit': 'einstein-1905:u0153',
  'text': 'Die Maxwell-Hertzschen Gleichungen für den leeren Raum mögen gültig sein für das ruhende System '
          '[M0286], so daß gelten möge:',
  'sha256': '5583b75d073d20c24ee74a508b5da01e71a2e3d034a43c013445417db7d2569c'},
 {'unit': 'einstein-1905:u0154',
  'text': '[M0287]',
  'sha256': '5210acf0253bf9322a235e5f2bbf70b3a851ff75bcb4ffab2103853d27c375f1'},
 {'unit': 'einstein-1905:u0155',
  'text': 'wobei ([M0288]) den Vektor der elektrischen, ([M0289]) den der magnetischen Kraft bedeutet.',
  'sha256': 'e36963f4b3631aed5d118008860002d0e36cb9922530340ee53c610175f3ff33'}]
EXPECTED_TOKENS=['Die',
 'Maxwell-Hertzschen',
 'Gleichungen',
 'für',
 'den',
 'leeren',
 'Raum',
 'mögen',
 'gültig',
 'sein',
 'für',
 'das',
 'ruhende',
 'System',
 '[M0286],',
 'so',
 'daß',
 'gelten',
 'möge:',
 '[M0287]',
 'wobei',
 '([M0288])',
 'den',
 'Vektor',
 'der',
 'elektrischen,',
 '([M0289])',
 'den',
 'der',
 'magnetischen',
 'Kraft',
 'bedeutet.']
SPANS={'znp': ('sixthopeningsentence', 1, 19),
 'eispl': ('sixthopeningsentence', 20, 20),
 'eispm': ('sixthopeningsentence', 21, 32)}
MULTI_SPANS={}
DESIGNATIONS={'eispj': ('eispm', 1), 'eispk': ('eispm', 2)}
FORMS={'eispj': '(X,Y,Z)', 'eispk': '(L,M,N)'}
ROLE_ASSIGNMENTS={'znk': 'vacuumregionrole', 'znl': 'vacuumelectricfieldrole', 'znm': 'vacuummagneticfieldrole'}
REFERENCE_SORTS={'znk': {'kind': 'function',
         'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                        {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                        {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                        {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
         'result': 'truth'},
 'znl': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function',
                    'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                    'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}},
 'znm': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function',
                    'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                                   {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
                    'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}}}
REFERENCE_ANCHORS={'znk': 'znp', 'znl': 'eispj', 'znm': 'eispk'}
ROLE_DEFINITIONS={'znk': {'kind': 'definition',
         'name': 'vacuumregionrole',
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
                  'arguments': [{'kind': 'call', 'symbol': 'ra', 'arguments': []},
                                {'kind': 'call', 'symbol': 'ta', 'arguments': []},
                                {'kind': 'call', 'symbol': 'rb', 'arguments': []},
                                {'kind': 'variable', 'name': 'vb'},
                                {'kind': 'variable', 'name': 'va'}]}},
 'znl': {'kind': 'definition',
         'name': 'vacuumelectricfieldrole',
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
                                             'sort': 'individual',
                                             'body': {'kind': 'exists',
                                                      'variable': 'vg',
                                                      'sort': {'kind': 'function',
                                                               'parameters': ['number'],
                                                               'result': 'truth'},
                                                      'body': {'kind': 'exists',
                                                               'variable': 'vh',
                                                               'sort': {'kind': 'function',
                                                                        'parameters': ['number'],
                                                                        'result': 'truth'},
                                                               'body': {'kind': 'exists',
                                                                        'variable': 'vi',
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
                                                                                                       'result': 'truth'}}},
                                                                        'body': {'kind': 'call',
                                                                                 'symbol': 'ejsn',
                                                                                 'arguments': [{'kind': 'call',
                                                                                                'symbol': 'ra',
                                                                                                'arguments': []},
                                                                                               {'kind': 'call',
                                                                                                'symbol': 'ta',
                                                                                                'arguments': []},
                                                                                               {'kind': 'call',
                                                                                                'symbol': 'rb',
                                                                                                'arguments': []},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vb'},
                                                                                               {'kind': 'call',
                                                                                                'symbol': 'znk',
                                                                                                'arguments': []},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vc'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vd'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 've'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vf'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vg'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vh'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'va'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vi'}]}}}}}}}}},
 'znm': {'kind': 'definition',
         'name': 'vacuummagneticfieldrole',
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
                                             'sort': 'individual',
                                             'body': {'kind': 'exists',
                                                      'variable': 'vg',
                                                      'sort': {'kind': 'function',
                                                               'parameters': ['number'],
                                                               'result': 'truth'},
                                                      'body': {'kind': 'exists',
                                                               'variable': 'vh',
                                                               'sort': {'kind': 'function',
                                                                        'parameters': ['number'],
                                                                        'result': 'truth'},
                                                               'body': {'kind': 'exists',
                                                                        'variable': 'vi',
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
                                                                                                       'result': 'truth'}}},
                                                                        'body': {'kind': 'call',
                                                                                 'symbol': 'ejsn',
                                                                                 'arguments': [{'kind': 'call',
                                                                                                'symbol': 'ra',
                                                                                                'arguments': []},
                                                                                               {'kind': 'call',
                                                                                                'symbol': 'ta',
                                                                                                'arguments': []},
                                                                                               {'kind': 'call',
                                                                                                'symbol': 'rb',
                                                                                                'arguments': []},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vb'},
                                                                                               {'kind': 'call',
                                                                                                'symbol': 'znk',
                                                                                                'arguments': []},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vc'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vd'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 've'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vf'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vg'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vh'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'vi'},
                                                                                               {'kind': 'variable',
                                                                                                'name': 'va'}]}}}}}}}}}}
LOCAL_NAMES=['ejsx',
 'ejsy',
 'ejsz',
 'ejs2',
 'ejs3',
 'ejs4',
 'ejs5',
 'ejs6',
 'ejs7',
 'ejta',
 'ejtb',
 'ejtc',
 'ejtd',
 'znk',
 'znl',
 'znm',
 'znp',
 'eispj',
 'eispk',
 'eispl',
 'eispm',
 'vacuumregionrole',
 'vacuumelectricfieldrole',
 'vacuummagneticfieldrole']
READINGS=('data/einstein-vacuum-equation-assumption-source-reading-v1.json',)
REVIEWS=('data/einstein-vacuum-equation-assumption-u0153-review-v1.json',
 'data/einstein-vacuum-equation-assumption-u0154-review-v1.json',
 'data/einstein-vacuum-equation-assumption-u0155-review-v1.json')
SEMANTIC_REVIEW=['u0153・六式u0154・wobei以下u0155を第70段落の一文として扱う。見出しは別箇所。',
 '四単位と二換算係数は存在量化を保持し、係数を1や1/Vへ固定しない。',
 '真空は全領域に物質占有がないという既存ejsmを用い、外部源や非零場を排除しない。',
 '領域は非空で、全有効点・実際の偏微分を本文から有限標本へ置換しない。',
 'M0287の六回転式・18偏微分の符号と軸順を保ち、発散条件や変換後の結果を追加しない。',
 '古いznk/znl/znmの説明に残る未完という語と、採用済みejsm/ejsnによる物理的条件の合成を区別する。過去の意味記録を黙って書き換えない。']
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
        chain=VacuumAssumptionVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return VacuumAssumptionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==92,'Vacuum-assumption source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','give',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown vacuum-assumption reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown vacuum-assumption reference')
    return 'describedfourcuttruthfunctionreference' if old=='znk' else 'describedindividualfourcutfunctionfamilyreference'


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
    result['statements']=renamed(doc['statements'][192:193],inverse);return normalize_document(result)



def text_boundaries():
    prior=previous.text_boundaries();sentence=prior['sentences']['sixthopeningsentence']
    require(sentence['position']==[70,1] and sentence['tokens']==EXPECTED_TOKENS,'Inherited sentence changed')
    units={u['id']:u for u in author.read(author.UNITS)['units']}
    for row in SENTENCE_SEGMENTS:
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['sha256'],'Assumption sentence segment changed')
    require(SPANS=={'znp':('sixthopeningsentence',1,19),'eispl':('sixthopeningsentence',20,20),'eispm':('sixthopeningsentence',21,32)},'Clause positions changed')
    tokens=sentence['tokens']
    require(tokens[18]=='möge:' and tokens[19]=='[M0287]' and tokens[20]=='wobei' and tokens[-1]=='bedeutet.','Assumption/display/explanation boundary changed')
    require(tokens[21]=='([M0288])' and tokens[26]=='([M0289])','Vector designation order changed')
    require(DESIGNATIONS=={'eispj':('eispm',1),'eispk':('eispm',2)},'Designation anchor changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='The inherited paragraph70 sentence1 covers introduction, six displayed equations, and the lower-case wobei continuation. The vector designations are anchored inside that continuation.',
        sentences={'sixthopeningsentence':sentence},spans={n:list(p) for n,p in SPANS.items()},
        multi_sentence_spans={},designations={n:list(p) for n,p in DESIGNATIONS.items()},designation_forms=FORMS)



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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Vacuum assumption source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(153,156)}
    require(set(coverage)==expected,'Vacuum assumption source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old vacuum assumption review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old vacuum assumption review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Vacuum assumption review coverage differs')
    require(SOURCE_ORDER==[21],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Vacuum assumption source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-vacuum-assumption-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=2,new_reference_primitives=1,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=67,core_edition=12,new_source_assertions=1,total_source_assertions=159,total_annotations=36,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible vacuum-assumption document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedfourcuttruthfunctionreference'):
    from scripts.four_coordinate_visible_profile import IndividualFourCutFamilyReferences
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedfourcuttruthfunctionreference':return profile.FourCutTruthFunctionReferences(roles)
    require(kind=='describedindividualfourcutfunctionfamilyreference','Unknown vacuum-assumption reference type')
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
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedfourcuttruthfunctionreference','describedindividualfourcutfunctionfamilyreference')}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-sixth-heading-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/vacuum_assumption_visible_profile.py','scripts/vacuum_assumption_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_vacuum_assumption_visible.py','scripts/visible_vacuum_assumption_visible_collection.py',
        'tests/test_vacuum_assumption_visible.py','tests/test_vacuum_assumption_profile.py','docs/einstein-vacuum-assumption-visible-v1.md'}
    for name in ('vacuum_equation_assumption',):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved vacuum-assumption bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-vacuum-assumption-visible-evidence-1',core_words=375,profile_words=872,profile_edition=67,
        new_public_relations=2,new_reference_primitives=1,new_source_assertions=1,total_source_assertions=159,annotations=36,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
