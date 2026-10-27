"""Connect straight and polygonal clock transport, the explicit curve assumption and Earth comparison."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.moving_trip_visible_profile import MovingTextReferences
from scripts.designation_purpose_profile import DesignationReferences
from scripts.shared_reference import definition
from scripts import clock_transport_visible_profile as profile
from scripts.clock_transport_visible_profile import ROOT,ClockTransportVisibleVocabulary,write_once
from scripts import check_einstein_origin_clock_visible as previous
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

SOURCE='examples/v016/einstein-clock-transport-visible-v1.noema'
BRIDGE='data/einstein-clock-transport-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-clock-transport-visible-v1'
LABEL=previous.LABEL
PUBLIC_RELATIONS={'zjg': 'mechanicalpart',
 'zjh': 'restoringrotationaloscillator',
 'zji': 'regulatesclockrate',
 'zjj': 'clockcondition',
 'zjk': 'othercomparisoncondition',
 'zjl': 'completecomparisonconditions',
 'zjm': 'attachedsurfaceclock',
 'zjn': 'uniformbodyrotation',
 'zjo': 'axialcoordinatequantity',
 'zjp': 'axisdistancequantity',
 'zjq': 'bodysurfacepoint',
 'zjv': 'verysmallratedifference',
 'eisoi': 'presentsdistinctivefocus',
 'eisol': 'physicalinferencecandidate',
 'eison': 'designatescurveelapsedtimerule'}
RELATIONS=previous.RELATIONS|PUBLIC_RELATIONS
NEW_DEFINITIONS=['swo',
 'swp',
 'swv',
 'swy',
 'swk',
 'sww',
 'sxc',
 'sxf',
 'sxi',
 'sxn',
 'sxo',
 'syh',
 'sxv',
 'syi',
 'syj',
 'syk',
 'syl',
 's5k',
 'ejj5',
 'ejj6',
 'ejj7',
 'ejka',
 'ejkc',
 'ejkb',
 'ejkd',
 'ejke',
 'ejkf',
 'ejkg',
 'ejkh',
 'ejki',
 'ejkj',
 'ejkk',
 'ejkl',
 'ejkm',
 'ejkn',
 'ejko',
 'ejkp',
 'ejkq',
 'ejkr',
 'ejks',
 'ejkt',
 'ejkv',
 'ejku',
 'ejkw',
 'sxd',
 'sxj',
 'sxk',
 'ejkx',
 'ejky',
 'ejkz',
 'ejk2',
 'ejk3',
 'ejk4',
 'ejk6',
 'ejk5',
 'ejk7',
 'ejla',
 'ejlb',
 'ejlc',
 'ejld',
 'ejle',
 'ejlf',
 'ejlg',
 'ejlh',
 'ejli',
 'ejlk',
 'ejlj',
 'ejll',
 'ejlm',
 'ejln',
 'ejlo',
 'ejlp',
 'ejlq',
 'ejlr',
 'ejls',
 'ejlt',
 'ejlu',
 'ejlv',
 'ejlw',
 'ejlx',
 'ejly',
 'ejlz',
 'ejma',
 'ejmb',
 'ejmc',
 'ejmd',
 'ejme',
 'ejmf',
 'ejmg',
 'ejmh',
 'ejmi',
 'ejmj',
 'ejmk',
 'ejml',
 'ejmm',
 'ejmo',
 'ejmq',
 'ejmn',
 'ejmp',
 'ejmr']
SENTENCES={'eisoj': (59, 1), 'zi7': (59, 2), 'polygonwhole': (60, 1), 'curvewhole': (61, 1), 'zjy': (61, 2)}
SPANS={'zjb': ('polygonwhole', 1, 24),
 'zjc': ('polygonwhole', 25, 35),
 'zje': ('curvewhole', 1, 18),
 'zjf': ('curvewhole', 19, 73),
 'earthnamespan': ('zjy', 7, 7),
 'earthconditionsspan': ('zjy', 23, 26)}
ROLE_ASSIGNMENTS={'zip': 'transportrolezip',
 'zis': 'transportrolezis',
 'zit': 'transportrolezit',
 'ziu': 'transportroleziu',
 'ziv': 'transportroleziv',
 'ziw': 'transportroleziw',
 'zix': 'transportrolezix',
 'ziy': 'transportroleziy',
 'ziz': 'transportroleziz',
 'zi2': 'transportrolezi2',
 'zi3': 'transportrolezi3',
 'zi4': 'transportrolezi4',
 'zi5': 'transportrolezi5',
 'zjr': 'transportrolezjr',
 'zjs': 'transportrolezjs',
 'zjt': 'transportrolezjt',
 'zjw': 'transportrolezjw',
 'zja': 'transportrolezja',
 'zjd': 'transportrolezjd'}
FORWARD_MAPS={}
TRANSFER_TUPLE=['zie',
 'zip',
 'ziq',
 'zir',
 'zis',
 'zit',
 'ziu',
 'ziv',
 'ziw',
 'zix',
 'ziy',
 'ziz',
 'zi2',
 'zi3',
 'zi4',
 'zi5']
TRANSFER_ORDER=['zip', 'zis', 'zit', 'ziu', 'ziv', 'ziw', 'zix', 'ziy', 'ziz', 'zi2', 'zi3', 'zi4', 'zi5']
REFERENCE_SORTS={'zip': 'individual',
 'zis': 'individual',
 'zit': 'individual',
 'ziu': 'individual',
 'ziv': 'individual',
 'ziw': 'individual',
 'zix': 'individual',
 'ziy': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'ziz': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zi2': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zi3': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zi4': 'situation',
 'zi5': 'situation',
 'zjr': 'individual',
 'zjs': 'individual',
 'zjt': 'situation',
 'zjw': 'individual',
 'zja': 'individual',
 'zjd': 'individual'}
DESIGNATIONS={'eisok': ('zi7', 12), 'eisom': ('curvewhole', 3)}
MULTI_SPANS={'curveearthpassage': ('curvewhole', 'zjy')}
TOKEN_COUNTS={'eisoj': 6, 'zi7': 89, 'polygonwhole': 35, 'curvewhole': 73, 'zjy': 31}
LOCAL_NAMES=['zip',
 'zis',
 'zit',
 'ziu',
 'ziv',
 'ziw',
 'zix',
 'ziy',
 'ziz',
 'zi2',
 'zi3',
 'zi4',
 'zi5',
 'zi7',
 'zja',
 'swo',
 'swp',
 'swv',
 'swy',
 'swk',
 'sww',
 'sxc',
 'sxf',
 'sxi',
 'sxn',
 'sxo',
 'zjb',
 'zjc',
 'syh',
 'sxv',
 'zjd',
 'zje',
 'zjf',
 'zjr',
 'zjs',
 'zjt',
 'zjw',
 'zjy',
 'syi',
 'syj',
 'syk',
 'syl',
 's5k',
 'ejj5',
 'ejj6',
 'ejj7',
 'ejka',
 'ejkc',
 'ejkb',
 'ejkd',
 'ejke',
 'ejkf',
 'ejkg',
 'ejkh',
 'eisoj',
 'eisok',
 'ejki',
 'ejkj',
 'ejkk',
 'ejkl',
 'ejkm',
 'ejkn',
 'ejko',
 'ejkp',
 'ejkq',
 'ejkr',
 'ejks',
 'ejkt',
 'ejkv',
 'ejku',
 'ejkw',
 'sxd',
 'sxj',
 'sxk',
 'ejkx',
 'ejky',
 'ejkz',
 'ejk2',
 'ejk3',
 'ejk4',
 'ejk6',
 'ejk5',
 'ejk7',
 'ejla',
 'ejlb',
 'ejlc',
 'ejld',
 'ejle',
 'ejlf',
 'ejlg',
 'ejlh',
 'ejli',
 'ejlk',
 'ejlj',
 'ejll',
 'ejlm',
 'ejln',
 'ejlo',
 'ejlp',
 'ejlq',
 'ejlr',
 'ejls',
 'ejlt',
 'ejlu',
 'ejlv',
 'ejlw',
 'ejlx',
 'ejly',
 'eisom',
 'ejlz',
 'ejma',
 'ejmb',
 'ejmc',
 'ejmd',
 'ejme',
 'ejmf',
 'ejmg',
 'ejmh',
 'ejmi',
 'ejmj',
 'ejmk',
 'ejml',
 'ejmm',
 'ejmo',
 'ejmq',
 'ejmn',
 'ejmp',
 'ejmr',
 'transportrolezip',
 'transportrolezis',
 'transportrolezit',
 'transportroleziu',
 'transportroleziv',
 'transportroleziw',
 'transportrolezix',
 'transportroleziy',
 'transportroleziz',
 'transportrolezi2',
 'transportrolezi3',
 'transportrolezi4',
 'transportrolezi5',
 'transportrolezjr',
 'transportrolezjs',
 'transportrolezjt',
 'transportrolezjw',
 'transportrolezja',
 'transportrolezjd',
 'polygonwhole',
 'curvewhole',
 'earthnamespan',
 'earthconditionsspan',
 'curveearthpassage']
READINGS=('data/einstein-clock-transfer-claim-source-reading-v1.json',
 'data/einstein-polygon-clock-claim-source-reading-v1.json',
 'data/einstein-curve-earth-claim-source-reading-v1.json')
REVIEWS=('data/einstein-clock-transfer-u0126-review-v1.json',
 'data/einstein-polygon-clock-u0127-review-v1.json',
 'data/einstein-curve-earth-u0128-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['Initial synchrony holds throughout the initial interval with a shared reading origin. Departure/arrival '
 'compare actual local readings bound to the same clocks, events, records and places.',
 'Straight motion uses the entire 3D line at constant positive speed; the reference clock stays at B '
 'throughout. Arrival mismatch and lag have the same event and place, without a claim about unspecified '
 'future readjustments.',
 'Use the same positive seconds scale for elapsed K time and observed lag. Keep fixed-duration O(u^4) '
 'qualification separate from the second-order value; do not turn it into exact equality or uniformity at '
 'fixed distance.',
 'Ideal interval rates and absence of additional startup/turn/stop jumps remain embedded interpretation '
 'annotations outside the attributed conditional antecedents. Do not infer physical acceleration response '
 'from the inertial formula.',
 'Any nonempty finite polygonal path shares the same boundary event and reading across adjacent legs. Permit '
 'crossings and return to the same place at a different time; exclude zero legs and inserted waits under the '
 'stated reading.',
 'The curve step explicitly assumes extension of the result presented as proved for polygons. Preserve C1 '
 'positions, continuous velocities and endpoint one-sided derivatives; do not replace full histories with '
 'vertex samples.',
 'Earth comparison separates mechanical balance regulation, same construction, complete other conditions, '
 'geographic configuration, and contextual very-small rate difference. Permit either pole and independent '
 'dial origins.',
 'Inferential necessity ranges over a nonempty, reference-containing candidate class fixed independently of '
 'the conclusion; do not equate it with physical proof, logical necessity or obligation.',
 'Retain all seven original assertions and every embedded annotation. Core375, alphabet, old manuscripts, '
 'judgments and validators remain fixed.']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=ClockTransportVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return ClockTransportVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][179:186]):visit(n)
    require(len(seen)==397,'Origin-clock source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][179:186])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','red',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.CONTRACTS))
    def add(old,body,result='individual'):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    for old,(first,last) in MULTI_SPANS.items():add(old,call(voc._symbols['sentencespanreference'],k('eirf'),k(first),k(last),k('ri')))
    for old,(node,index) in DESIGNATIONS.items():add(old,call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri')))
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:
        add(old,call(voc._symbols[reference_kind(old)],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')),REFERENCE_SORTS[old])
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown clock-transport reference')
    if old in TRANSFER_ORDER or old=='zja':return 'zi7'
    return {'zjr':'earthnamespan','zjs':'zjy','zjt':'zjy','zjw':'earthconditionsspan','zjd':'curveearthpassage'}[old]


def reference_kind(old):
    sort=REFERENCE_SORTS[old]
    return 'describedsettingreference' if sort=='situation' else 'describedcutreference' if sort==profile.CUT else 'describedreference'


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old]);x=v('va');context=v('vb');rows=[]
    ds={d['name']:d for d in source_excerpt()['declarations']}
    def exists(name,sort,body):return dict(kind='exists',variable=name,sort=sort,body=body)
    def add(old,body):rows.append(definition(n[ROLE_ASSIGNMENTS[old]],[('va',REFERENCE_SORTS[old]),('vb','situation')],'truth',body))
    require([p['sort'] for p in ds['ejkf']['parameters']]==[ds[old]['result'] for old in TRANSFER_TUPLE],'Transport tuple sorts changed')
    for index,old in enumerate(TRANSFER_ORDER):
        later=TRANSFER_ORDER[index+1:];variables={other:'v'+chr(99+i) for i,other in enumerate(later)}
        arguments=[x if name==old else v(variables[name]) if name in variables else k(name) for name in TRANSFER_TUPLE]
        body=call(m['ejkf'],*arguments)
        for name in reversed(later):body=exists(variables[name],REFERENCE_SORTS[name],body)
        add(old,body)
    earth=op('and',call(vocabulary()._symbols['introducesreferent'],k('earthnamespan'),x,k('eirf'),context),
        exists('vc','individual',exists('vd','situation',call(m['zjn'],x,v('vc'),k('ra'),v('vd')))))
    add('zjr',earth)
    add('zjs',exists('vc','situation',call(m['zjn'],k('zjr'),x,k('ra'),v('vc'))))
    add('zjt',call(m['zjn'],k('zjr'),k('zjs'),k('ra'),x))
    add('zjw',call(m['zjl'],x,k('zjt')))
    quote=lambda old:dict(kind='quote',body=call(m[old]))
    add('zja',call(m['zfl'],x,k('rd'),quote('ejkn'),quote('ejkl'),k('eisn5'),context))
    add('zjd',op('and',call(m['ug'],k('zje'),k('rd'),quote('ejlx'),x,context),
        op('and',call(m['uh'],k('zjf'),k('rd'),quote('ejlw'),x,context),
            call(m['uh'],k('zjy'),k('rd'),quote('ejmg'),x,context))))
    return rows


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
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*previous.previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][154:161],inverse);return normalize_document(result)



def text_boundaries():
    texts=[' '.join(row['text'] for row in author.read(path)['segments']) for path in READINGS]
    intro,transfer=texts[0].split(' Sind ',1);transfer='Sind '+transfer
    curve,earth=texts[2].split(' Man schließt ',1);earth='Man schließt '+earth
    sentences={}
    for old,value in zip(SENTENCES,(intro,transfer,texts[1],curve,earth),strict=True):
        tokens=value.split();require(len(tokens)==TOKEN_COUNTS[old],'Clock transport sentence boundary changed')
        sentences[old]=dict(position=list(SENTENCES[old]),tokens=tokens,text=value)
    require(intro+' '+transfer==texts[0] and curve+' '+earth==texts[2],'Transport source sentence split changed')
    require(transfer.split()[77]=='[M0230]' and curve.split()[51]=='[M0239]','Elapsed seconds designation position changed')
    require(earth.split()[6]=='Erdäquator' and earth.split()[22:26]==['sonst','gleichen','Bedingungen','unterworfene,'],'Earth reference span changed')
    return dict(rule='Pages904–905: paragraph59 has two sentences, paragraph60 one polygonal sentence, paragraph61 the curve assumption/result and Earth comparison. Sek. does not end a sentence; the colon and unbewegt page break remain internal.',
        sentences=sentences,spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={n:list(p) for n,p in MULTI_SPANS.items()},designations={n:list(p) for n,p in DESIGNATIONS.items()})



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Clock transport source reading differs')
            require([start,end]==[0,len(unit['text'])],'Clock unit is only partially selected')
            require(unit['id'] not in source_units,'Duplicate clock unit')
            source_units[unit['id']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(source_units)=={f'einstein-1905:u{i:04d}' for i in range(126,129)},'Clock transport source selection differs')
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old clock transport review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old clock transport review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==set(source_units),'Clock transport review coverage differs')
    require(backprojection(document())==source_excerpt(),'Clock transport source backprojection differs')
    return dict(schema='noema-einstein-clock-transport-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=list(range(179,186)),source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=15,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=61,core_edition=12,new_source_assertions=7,total_source_assertions=129,total_annotations=32,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible clock-transport document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedcutreference':return CutReferences(roles)
    if kind=='describedsettingreference':return SettingReferences(roles)
    require(kind=='describedreference','Unknown reference type');return TemporalReferences(roles,{})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    def passage(document,first,last,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:
            return MovingTextReferences({(values['eirf'],values[a],values[b],values['ri']):values[n] for n,(a,b) in MULTI_SPANS.items()},{}).span(document,first,last,context)
        return result['sentencespanreference'](document,first,last,context)
    def designation(document,node,index,context):
        if node in {values[n] for n in SENTENCES}:
            return DesignationReferences({(values['eirf'],values[a],i,values['ri']):values[n] for n,(a,i) in DESIGNATIONS.items()}).reference(document,node,index,context)
        return result['designationreference'](document,node,index,context)
    def typed(kind):
        nodes={values[reference_anchor(old)] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
        def lookup(document,node,role,context):
            if node in nodes:return reference_model(values,kind).described(document,node,role,context)
            return result[kind](document,node,role,context)
        return lookup
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedcutreference','describedsettingreference')}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-origin-clock-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/clock_transport_visible_profile.py','scripts/clock_transport_visible_profile_contracts.py',
        'scripts/check_einstein_clock_transport_visible.py','scripts/visible_clock_transport_visible_collection.py',
        'tests/test_clock_transport_visible.py','docs/einstein-clock-transport-visible-v1.md'}
    for name in ('clock_transfer_records','clock_transfer_claim','polygon_clock_claim','curved_clock_records','curve_earth_claim'):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256);paths.update(module.DEPENDENCIES)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved clock-transport bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-clock-transport-visible-evidence-1',core_words=375,profile_words=851,profile_edition=61,
        new_public_relations=15,new_reference_primitives=0,new_source_assertions=7,total_source_assertions=129,annotations=32,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
