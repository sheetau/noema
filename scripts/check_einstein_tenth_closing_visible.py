"""Connect the acknowledgment, month dateline and editorial receipt notice."""
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
from scripts import closing_function_reference_visible_profile as profile
from scripts import tenth_closing_visible_profile as closing_profile
from scripts.closing_function_reference_visible_profile import ROOT,ClosingFunctionReferenceVisibleVocabulary,write_once
from scripts import check_einstein_tenth_observables_visible as previous
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

from scripts.tenth_closing_reference_roles import build_roles
SOURCE='examples/v016/einstein-tenth-closing-visible-v1.noema'
BRIDGE='data/einstein-tenth-closing-visible-bridge-v1.json'
SOURCE_ORDER=[277, 278, 279]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-p921-0.jpg',
  'sha256': '29767bdc575e6f71bbd89fa298314413315cf508ad2afe515c5c5940fe726a88',
  'actually_displayed': True,
  'display_method': 'Current goal turn: tools.view_image forwarded with image()',
  'independent_human_reading': False}]
PUBLIC_RELATIONS={'eis5t': 'mutualfriendship',
 'eis5u': 'professionalcolleagues',
 'eis5v': 'investigationtask',
 'eis5w': 'documentproblemfocus',
 'eis5x': 'closingremark',
 'eis5y': 'workepisodecoverage',
 'eis5z': 'calendaryearnumber',
 'eis6a': 'orderedcalendarmonths',
 'eis6b': 'orderedcalendardays',
 'eis6c': 'datelineplace',
 'eis6d': 'datelineperiod',
 'eis6e': 'documentreceipt',
 'eis6f': 'editorialreport',
 'eis6g': 'documentutterancepresentation',
 'eis6h': 'periodcontainsmoment',
 'zrradvances': 'workadvancement'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['et2',
 'et3',
 'et4',
 'et5',
 'et6',
 'etm',
 'etn',
 'eto',
 'etq',
 'etr',
 'ets',
 'ett',
 'etu',
 'etv',
 'etw',
 'etx',
 'ety',
 'etz',
 'sewc',
 'sewd',
 'sewg',
 'sewm',
 'sewn',
 'sewo',
 'sewp',
 'sewq',
 'sewr',
 'sewt',
 'sewv',
 'sewx']
REUSED_BODIES={}
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'eis6i': [121, 1], 'eis6m': [122, 1], 'eis6n': [123, 1]}
SPANS={'tenthclosingbessotoken': ['eis6i', 18, 'eis6i', 19], 'tenthclosingberntoken': ['eis6m', 1, 'eis6m', 1]}
MULTI_SPANS={}
DESIGNATIONS={'eis6l': ['tenthclosingbessotoken', 1], 'eis6s': ['tenthclosingberntoken', 1]}
FORMS={'eis6l': 'M. Besso', 'eis6s': 'Bern'}
ROLE_ASSIGNMENTS={'zrqwork': 'closingrolezrqwork',
 'eis6k': 'closingroleeis6k',
 'zrqperson': 'closingrolezrqperson',
 'eis6t': 'closingroleeis6t',
 'eis6o': 'closingroleeis6o',
 'eis6p': 'closingroleeis6p',
 'eis6q': 'closingroleeis6q',
 'eis6r': 'closingroleeis6r',
 'eis6u': 'closingroleeis6u',
 'zrrhistory': 'closingrolezrrhistory',
 'zrrscope': 'closingrolezrrscope',
 'zrroccasions': 'closingrolezrroccasions',
 'zrrbefore': 'closingrolezrrbefore',
 'zrrworking': 'closingrolezrrworking',
 'zrqoccurs': 'closingrolezrqoccurs',
 'zrqperforms': 'closingrolezrqperforms',
 'zrqproduces': 'closingrolezrqproduces',
 'zrquses': 'closingrolezrquses',
 'zrqstandard': 'closingrolezrqstandard',
 'zrqmeets': 'closingrolezrqmeets',
 'zrqjudgments': 'closingrolezrqjudgments',
 'zrqmatters': 'closingrolezrqmatters',
 'zrqlinked': 'closingrolezrqlinked',
 'zrqcandidates': 'closingrolezrqcandidates',
 'zrraims': 'closingrolezrraims',
 'zrrgoalfor': 'closingrolezrrgoalfor',
 'zrqscope': 'closingrolezrqscope'}
REFERENCE_ANCHORS={'zrqwork': 'eis6i',
 'eis6k': 'eis6i',
 'zrqperson': 'tenthclosingbessotoken',
 'eis6t': 'tenthclosingberntoken',
 'eis6o': 'eis6m',
 'eis6p': 'eis6m',
 'eis6q': 'eis6m',
 'eis6r': 'eis6n',
 'eis6u': 'eis6n',
 'zrrhistory': 'eis6i',
 'zrrscope': 'eis6i',
 'zrroccasions': 'eis6i',
 'zrrbefore': 'eis6i',
 'zrrworking': 'eis6i',
 'zrqoccurs': 'eis6i',
 'zrqperforms': 'eis6i',
 'zrqproduces': 'eis6i',
 'zrquses': 'eis6i',
 'zrqstandard': 'eis6i',
 'zrqmeets': 'eis6i',
 'zrqjudgments': 'eis6i',
 'zrqmatters': 'eis6i',
 'zrqlinked': 'eis6i',
 'zrqcandidates': 'eis6i',
 'zrraims': 'eis6i',
 'zrrgoalfor': 'eis6i',
 'zrqscope': 'eis6i'}
REFERENCE_SORTS={'zrqwork': 'individual',
 'eis6k': 'individual',
 'zrqperson': 'individual',
 'eis6t': 'individual',
 'eis6o': 'individual',
 'eis6p': 'individual',
 'eis6q': 'individual',
 'eis6r': 'individual',
 'eis6u': 'individual',
 'zrrhistory': {'kind': 'function', 'parameters': ['situation'], 'result': 'truth'},
 'zrrscope': {'kind': 'function', 'parameters': ['situation'], 'result': 'truth'},
 'zrroccasions': {'kind': 'function', 'parameters': ['situation'], 'result': 'truth'},
 'zrrbefore': {'kind': 'function', 'parameters': ['situation', 'situation'], 'result': 'truth'},
 'zrrworking': {'kind': 'function',
                'parameters': ['individual', 'individual', 'situation'],
                'result': 'truth'},
 'zrqoccurs': {'kind': 'function', 'parameters': ['individual', 'situation'], 'result': 'truth'},
 'zrqperforms': {'kind': 'function',
                 'parameters': ['individual', 'individual', 'situation'],
                 'result': 'truth'},
 'zrqproduces': {'kind': 'function',
                 'parameters': ['individual', 'individual', 'situation'],
                 'result': 'truth'},
 'zrquses': {'kind': 'function',
             'parameters': ['individual', 'individual', 'individual', 'situation'],
             'result': 'truth'},
 'zrqstandard': {'kind': 'function',
                 'parameters': ['individual', 'individual', 'individual', 'situation'],
                 'result': 'truth'},
 'zrqmeets': {'kind': 'function',
              'parameters': ['individual', 'individual', 'situation'],
              'result': 'truth'},
 'zrqjudgments': {'kind': 'function',
                  'parameters': ['individual', 'individual', 'situation'],
                  'result': 'truth'},
 'zrqmatters': {'kind': 'function',
                'parameters': ['individual', 'individual', 'situation'],
                'result': 'truth'},
 'zrqlinked': {'kind': 'function',
               'parameters': ['individual',
                              {'kind': 'description',
                               'result': {'kind': 'function',
                                          'parameters': [{'kind': 'sequence', 'element': 'individual'}],
                                          'result': 'content'}},
                              {'kind': 'sequence', 'element': 'individual'},
                              'situation'],
               'result': 'truth'},
 'zrqcandidates': {'kind': 'function',
                   'parameters': ['individual', 'situation', 'situation'],
                   'result': 'truth'},
 'zrraims': {'kind': 'function',
             'parameters': ['individual',
                            'individual',
                            {'kind': 'description',
                             'result': {'kind': 'function',
                                        'parameters': [{'kind': 'sequence', 'element': 'individual'}],
                                        'result': 'content'}},
                            {'kind': 'sequence', 'element': 'individual'},
                            'situation'],
             'result': 'truth'},
 'zrrgoalfor': {'kind': 'function',
                'parameters': ['individual',
                               'individual',
                               {'kind': 'description',
                                'result': {'kind': 'function',
                                           'parameters': [{'kind': 'sequence', 'element': 'individual'}],
                                           'result': 'content'}},
                               'situation'],
                'result': 'truth'},
 'zrqscope': 'individual'}
REFERENCE_KINDS={'zrqwork': 'describedreference',
 'eis6k': 'describedreference',
 'zrqperson': 'describedreference',
 'eis6t': 'describedreference',
 'eis6o': 'describedreference',
 'eis6p': 'describedreference',
 'eis6q': 'describedreference',
 'eis6r': 'describedreference',
 'eis6u': 'describedreference',
 'zrrhistory': 'describedsituationtruthfunctionreference',
 'zrrscope': 'describedsituationtruthfunctionreference',
 'zrroccasions': 'describedsituationtruthfunctionreference',
 'zrrbefore': 'describedtwosituationtruthfunctionreference',
 'zrrworking': 'describedtwoindividualsituationtruthfunctionreference',
 'zrqoccurs': 'describedindividualsituationtruthfunctionreference',
 'zrqperforms': 'describedtwoindividualsituationtruthfunctionreference',
 'zrqproduces': 'describedtwoindividualsituationtruthfunctionreference',
 'zrquses': 'describedthreeindividualsituationtruthfunctionreference',
 'zrqstandard': 'describedthreeindividualsituationtruthfunctionreference',
 'zrqmeets': 'describedtwoindividualsituationtruthfunctionreference',
 'zrqjudgments': 'describedtwoindividualsituationtruthfunctionreference',
 'zrqmatters': 'describedtwoindividualsituationtruthfunctionreference',
 'zrqlinked': 'describedcriterionbindingfunctionreference',
 'zrqcandidates': 'describedindividualtwosituationtruthfunctionreference',
 'zrraims': 'describedpurposefunctionreference',
 'zrrgoalfor': 'describedbeneficiaryfunctionreference',
 'zrqscope': 'describedreference'}
LOCAL_NAMES=['eis6i',
 'eis6m',
 'eis6n',
 'tenthclosingbessotoken',
 'tenthclosingberntoken',
 'zrqwork',
 'eis6k',
 'zrqperson',
 'eis6t',
 'eis6o',
 'eis6p',
 'eis6q',
 'eis6r',
 'eis6u',
 'zrrhistory',
 'zrrscope',
 'zrroccasions',
 'zrrbefore',
 'zrrworking',
 'zrqoccurs',
 'zrqperforms',
 'zrqproduces',
 'zrquses',
 'zrqstandard',
 'zrqmeets',
 'zrqjudgments',
 'zrqmatters',
 'zrqlinked',
 'zrqcandidates',
 'zrraims',
 'zrrgoalfor',
 'zrqscope',
 'eis6l',
 'eis6s',
 'closingrolezrqwork',
 'closingroleeis6k',
 'closingrolezrqperson',
 'closingroleeis6t',
 'closingroleeis6o',
 'closingroleeis6p',
 'closingroleeis6q',
 'closingroleeis6r',
 'closingroleeis6u',
 'closingrolezrrhistory',
 'closingrolezrrscope',
 'closingrolezrroccasions',
 'closingrolezrrbefore',
 'closingrolezrrworking',
 'closingrolezrqoccurs',
 'closingrolezrqperforms',
 'closingrolezrqproduces',
 'closingrolezrquses',
 'closingrolezrqstandard',
 'closingrolezrqmeets',
 'closingrolezrqjudgments',
 'closingrolezrqmatters',
 'closingrolezrqlinked',
 'closingrolezrqcandidates',
 'closingrolezrraims',
 'closingrolezrrgoalfor',
 'closingrolezrqscope',
 'et2',
 'et3',
 'et4',
 'et5',
 'et6',
 'etm',
 'etn',
 'eto',
 'etq',
 'etr',
 'ets',
 'ett',
 'etu',
 'etv',
 'etw',
 'etx',
 'ety',
 'etz',
 'sewc',
 'sewd',
 'sewg',
 'sewm',
 'sewn',
 'sewo',
 'sewp',
 'sewq',
 'sewr',
 'sewt',
 'sewv',
 'sewx']
TEXT_SENTENCES={'eis6i': 'Zum Schlusse bemerke ich, daß mir beim Arbeiten an dem hier behandelten Probleme mein Freund '
          'und Kollege M. Besso treu zur Seite stand und daß ich demselben manche wertvolle Anregung '
          'verdanke.',
 'eis6m': 'Bern, Juni 1905.',
 'eis6n': '(Eingegangen 30. Juni 1905.)'}
TOKENS={'eis6i': ['Zum',
           'Schlusse',
           'bemerke',
           'ich,',
           'daß',
           'mir',
           'beim',
           'Arbeiten',
           'an',
           'dem',
           'hier',
           'behandelten',
           'Probleme',
           'mein',
           'Freund',
           'und',
           'Kollege',
           'M.',
           'Besso',
           'treu',
           'zur',
           'Seite',
           'stand',
           'und',
           'daß',
           'ich',
           'demselben',
           'manche',
           'wertvolle',
           'Anregung',
           'verdanke.'],
 'eis6m': ['Bern,', 'Juni', '1905.'],
 'eis6n': ['(Eingegangen', '30.', 'Juni', '1905.)']}
TOKEN_COUNTS={'eis6i': 31, 'eis6m': 3, 'eis6n': 4}
SOURCE_UNITS={'einstein-1905:u0276': {'text': 'Zum Schlusse bemerke ich, daß mir beim Arbeiten an dem hier '
                                 'behandelten Probleme mein Freund und Kollege M. Besso treu zur Seite '
                                 'stand und daß ich demselben manche wertvolle Anregung verdanke.',
                         'sha256': '40901cd0d9c9667dec7a06154ecbbe5ebcf68623b55b7580b86f2506dafd37d6'},
 'einstein-1905:u0277': {'text': 'Bern, Juni 1905.',
                         'sha256': '407b3188a2ce93c14db7b0692d347a66a92128f374820ff55f57dae7a3014c96'},
 'einstein-1905:u0278': {'text': '(Eingegangen 30. Juni 1905.)',
                         'sha256': '706ced2c62858d398b24f1a02988fd83c27392d47ef1b3a5ef66911d66bd4304'}}
BOUNDARY_RULE=('Text blocks 121..123 follow inspected page 921. M. and the ordinal 30. are not sentence boundaries. '
 'The month dateline and parenthesized editorial receipt notice remain separate blocks.')
REVIEWS=('data/einstein-closing-acknowledgment-u0276-review-v1.json',
 'data/einstein-closing-acknowledgment-u0277-review-v1.json',
 'data/einstein-closing-acknowledgment-u0278-review-v1.json')
REVIEW_SELECTION=[{'unit': 'einstein-1905:u0276',
  'review': 'data/einstein-closing-acknowledgment-u0276-review-v1.json',
  'statements': [277]},
 {'unit': 'einstein-1905:u0277',
  'review': 'data/einstein-closing-acknowledgment-u0277-review-v1.json',
  'statements': [278]},
 {'unit': 'einstein-1905:u0278',
  'review': 'data/einstein-closing-acknowledgment-u0278-review-v1.json',
  'statements': [279]}]
READINGS=('data/closing-acknowledgment-basis-v1.json', 'data/einstein-author-credit-basis-v1.json')
DIAGNOSTIC_VALIDATORS=['scripts/check_calendar_dateline.py',
 'scripts/check_closing_acknowledgment.py',
 'scripts/check_dated_reading.py',
 'scripts/check_described_appraisals.py',
 'scripts/check_intellectual_credit.py',
 'scripts/check_rod_setup.py',
 'scripts/check_sustained_assistance.py',
 'scripts/check_unreceived_reference.py',
 'scripts/compose_calendar_dateline.py',
 'scripts/compose_closing_acknowledgment.py',
 'scripts/compose_dated_reading.py',
 'scripts/compose_intellectual_credit.py',
 'scripts/compose_limits.py',
 'scripts/compose_origin_clock.py',
 'scripts/compose_parameterized_goals.py',
 'scripts/compose_personal_criteria.py',
 'scripts/compose_situated_criticism.py',
 'scripts/compose_subject_bound_departure.py',
 'scripts/compose_sustained_assistance.py',
 'scripts/compose_unreceived_reference.py',
 'scripts/review_closing_acknowledgment.py']
SEMANTIC_REVIEW=['Preserve the complete acknowledgment and its explicit reading of sustained purposeful assistance and '
 'credited intellectual inputs.',
 'Mutual friendship and professional colleague relations do not by themselves assert help or '
 'coauthorship.',
 'Past contribution and present appraisal share the same participants and research but retain their '
 'distinct contexts.',
 'The work history and opportunities are selected independently of successful assistance.',
 'Quoted purposes and judgments remain nonfactive; role lookup does not require a goal to be achieved '
 'or feasible.',
 'The criterion remains the statically specialized etq body, with the eto quotation preserved.',
 'Use the same explicit civil Gregorian calendar reading; the month dateline does not acquire the '
 'receipt notice day.',
 'Editorial receipt is distinct from acceptance, publication and author assertion.',
 'Candidate descriptions do not prove existence, uniqueness or shared witnesses; preserve all complete '
 'source statements.']
OUT=ROOT/'output/einstein-tenth-closing-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|closing_profile.SOURCE_RELATIONS|profile.SOURCE_RELATIONS|{'eira':'presentationholds','eirb':'nameapplies'}
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=[*closing_profile.LIMITS,*profile.LIMITS,*SEMANTIC_REVIEW]

_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=ClosingFunctionReferenceVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return ClosingFunctionReferenceVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==87,'Tenth-closing source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','give','fruit','fruit','fruit','fruit',temporal.PARTS[i//256],temporal.PARTS[(i//16)%16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(closing_profile.CONTRACTS)|set(profile.ALL_CONTRACTS))
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
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-closing reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown tenth-closing reference')
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
    result['statements']=renamed(doc['statements'][359:362],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read('artifacts/written-units-v1/einstein-1905.json')
    units={r['id']:r for r in inventory['units']}
    for name,row in SOURCE_UNITS.items():
        require(units[name]['text']==row['text'] and units[name]['text_sha256']==row['sha256'],'Source text boundary changed')
    require(previous.SENTENCES['eis6j']==[120,1],'Previous paragraph boundary changed')
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
    rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    require(set(rows)=={'eis6l','eis6s'},'Closing designation inventory changed')
    for old,row in rows.items():require(any(f['text']==FORMS[old] for f in row['forms']),'Retained printed form changed')
    anchor=author.read('data/tenth-closing-text-anchors-v1.json')
    require(anchor['forms']==FORMS and anchor['designations']==DESIGNATIONS,'Reviewed designation changed')
    require(anchor['new_visible_designation_forms']=={},'Unplanned new designation')
    paths=set(data.show()['source_sha256'])|{'data/tenth-closing-text-anchors-v1.json'}
    return dict(entries=rows,new_visible_entries={},source_identifier_annotations_modified=False,
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
    require(SOURCE_ORDER==[277,278,279],'Selection changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    contracts=closing_profile.CONTRACTS|profile.CONTRACTS
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=contracts[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public meaning differs')
    return dict(schema='noema-einstein-tenth-closing-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=SOURCE_UNITS,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates=SENTENCES,text_boundaries=text_boundaries(),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors=REFERENCE_ANCHORS,
        reused_typed_bodies=REUSED_BODIES,new_public_relations=16,new_reference_primitives=9,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=86,core_edition=12,new_source_assertions=3,
        total_source_assertions=268,total_annotations=96,source_reviews=REVIEW_SELECTION,parent_visible_source=previous.SOURCE,
        original_manuscript_modified_during_visible_integration=False,full_real_domain_evaluated=False,
        document_integration_credit=0,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible tenth-closing document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[first],start,values[last],end,values['ri']):values[n] for n,(first,start,last,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    require(kind in REFERENCE_KINDS.values(),'Unknown closing reference kind')
    rows={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old]
          for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(rows,{})
    return profile.TypedFunctionReferences(kind,rows)


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
    closing_profile.prepare();profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
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
        profile.LIBRARY,profile.BASIS,profile.MANIFEST,closing_profile.LIBRARY,closing_profile.BASIS,closing_profile.MANIFEST,
        *READINGS,*REVIEWS,*DIAGNOSTIC_VALIDATORS,
        'scripts/tenth_closing_visible_profile.py','scripts/tenth_closing_visible_profile_contracts.py',
        'scripts/closing_function_reference_visible_profile.py','scripts/closing_function_reference_visible_profile_contracts.py',
        'scripts/tenth_closing_reference_roles.py','scripts/check_einstein_tenth_closing_visible.py',
        'scripts/visible_tenth_closing_visible_collection.py','tests/test_tenth_closing_visible.py',
        'tests/test_tenth_closing_reference_roles.py','tests/test_closing_function_reference_visible_profile.py',
        'data/tenth-closing-text-anchors-v1.json','docs/einstein-tenth-closing-visible-v1.md'}
    paths.update(catalogs()['einstein-1905'].source_sha256)
    for review in REVIEWS:
        record=author.read(review);validate_hashes(ROOT,record['source_sha256']);paths.update(record['source_sha256'])
    paths.update(annotations()['source_sha256'])
    for row in SOURCE_VISUAL_REVIEW:paths.add(row['path'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved closing bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-tenth-closing-visible-evidence-1',core_words=375,profile_words=1086,profile_edition=86,
        new_public_relations=16,new_reference_primitives=9,new_source_assertions=3,total_source_assertions=268,annotations=96,
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
