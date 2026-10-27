"""Connect finite material dimensions, the lower-speed planar limit and the physical forecast."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.shared_reference import definition
from scripts import shape_dimension_visible_profile as profile
from scripts.shape_dimension_visible_profile import ROOT,ShapeDimensionVisibleVocabulary,write_once
from scripts import check_einstein_moving_ellipsoid_visible as previous
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

SOURCE='examples/v016/einstein-shape-dimension-visible-v1.noema'
BRIDGE='data/einstein-shape-dimension-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-shape-dimension-visible-v1'
LABEL=previous.LABEL
PUBLIC_RELATIONS={'znn': 'electromagneticfieldassignment',
 'zof': 'quantityunitscale',
 'zog': 'quantityresultrecord',
 'zor': 'electricchargekind',
 'zpb': 'bodyeventcoordinates',
 'zpc': 'forceresultrecord',
 'zpn': 'signedforcevectorkind',
 'zrdpointlike': 'pointbodycondition',
 'eiri': 'orientedmaterialsectionnetflow',
 'eirj': 'materialsectiondomain',
 'eirl': 'electricforcecontribution',
 'eirm': 'electricfieldunitconversion',
 'eirn': 'fieldunitassignment',
 'eirt': 'magneticforcecontribution',
 'eiru': 'magneticfieldunitconversion',
 'eisax': 'maxwellelectrodynamicstheory',
 'eisa6': 'electrodynamicinquiry',
 'eisa7': 'restrictsinquirytomotion',
 'eiscm': 'theoryofinquiry',
 'eiscn': 'restscopedtheorybasis',
 'eisco': 'theoryconstructionroute',
 'eiscp': 'additionalphysicalpremisedomain',
 'eiscq': 'premisecontentcorrespondence',
 'eiscr': 'theoryconsequencecontent',
 'eiscs': 'contradictorycontent',
 'eisct': 'explanationalsimplicity',
 'eiscv': 'plannedtheoryview',
 'eisdb': 'forecasttheoryresult',
 'eisoe': 'physicallyadmissiblesituation',
 'eisof': 'physicalfamilyapplication',
 'eisog': 'supplementaryviewpresentation'}
RELATIONS=previous.RELATIONS|PUBLIC_RELATIONS
NEW_DEFINITIONS=['stw',
 'stv',
 'sui',
 'suj',
 'suk',
 'suo',
 'szi',
 'sbw2',
 'scb2',
 'scg2',
 'sch2',
 'seoa',
 'seob',
 'seoc',
 'zzbb',
 'zzbd',
 'zzbe',
 'zzbf',
 'zzbh',
 'zzbi',
 'zzbj',
 'zzbk',
 'zzbl',
 'zzbm',
 'lb',
 'lc',
 'ld',
 'li',
 'sepw',
 'eia4',
 'eia5',
 'eia6',
 'eia7',
 'eiba',
 'eibe',
 'eibf',
 'eibq',
 'eibr',
 'eibs',
 'eicn',
 'eico',
 'eie5',
 'eie6',
 'eige',
 'eigf',
 'eigg',
 'eigh',
 'eigi',
 'eigj',
 'ejgg',
 'ejgh',
 'ejgi',
 'ejgj',
 'ejgk',
 'ejgl',
 'ejgm',
 'ejgp',
 'ejgq',
 'ejgr',
 'ejgs',
 'ejgt',
 'ejgu',
 'ejgv',
 'ejgw',
 'ejgx',
 'ejgy',
 'ejgz',
 'ejg2',
 'ejg3',
 'ejg4',
 'ejg5',
 'ejg6',
 'ejg7',
 'ejha',
 'ejhb',
 'ejhc',
 'ejhd',
 'ejhe',
 'ejhf',
 'ejhg',
 'ejhh',
 'ejhi',
 'ejhj',
 'ejhk',
 'ejhl',
 'ejhm',
 'ejhn',
 'ejho',
 'ejhp',
 'ejhq',
 'ejhr',
 'ejhs',
 'ejht',
 'ejhu',
 'ejhv']
RECIPROCAL_DEFINITIONS=['ejhw','ejhx','ejii','ejhy','ejhz','ejh2','ejh3','ejh4','ejh5','ejh6','ejh7','ejia','ejib','ejic','ejid','ejie','ejif','ejig','ejih']
NEW_DEFINITIONS+=RECIPROCAL_DEFINITIONS
SENTENCES={'zh6': (55, 1), 'zh7': (55, 2), 'zia': (55, 3), 'zib': (56, 1)}
SPANS={'eisob': ('zh6', 1, 22),
 'eisoc': ('zh6', 23, 29),
 'zic': ('zh6', 30, 37),
 'eisoh': ('zia', 7, 28)}
ROLE_ASSIGNMENTS={'eisod': 'planarlimitnoterole'}
FORWARD_MAPS={'zz5': 'rationaladd', 'zz6': 'rationalnegate', 'zz7': 'rationalmultiply'}
LOCAL_NAMES=['stw',
 'stv',
 'sui',
 'suj',
 'suk',
 'suo',
 'szi',
 'sbw2',
 'scb2',
 'scg2',
 'sch2',
 'seoa',
 'seob',
 'seoc',
 'zzbb',
 'zzbd',
 'zzbe',
 'zzbf',
 'zzbh',
 'zzbi',
 'zzbj',
 'zzbk',
 'zzbl',
 'zzbm',
 'lb',
 'lc',
 'ld',
 'li',
 'sepw',
 'eia4',
 'eia5',
 'eia6',
 'eia7',
 'eiba',
 'eibe',
 'eibf',
 'eibq',
 'eibr',
 'eibs',
 'eicn',
 'eico',
 'eie5',
 'eie6',
 'eige',
 'eigf',
 'eigg',
 'eigh',
 'eigi',
 'eigj',
 'ejgg',
 'ejgh',
 'ejgi',
 'ejgj',
 'ejgk',
 'ejgl',
 'ejgm',
 'ejgp',
 'ejgq',
 'ejgr',
 'ejgs',
 'ejgt',
 'ejgu',
 'ejgv',
 'ejgw',
 'ejgx',
 'ejgy',
 'ejgz',
 'ejg2',
 'ejg3',
 'ejg4',
 'ejg5',
 'ejg6',
 'ejg7',
 'ejha',
 'ejhb',
 'ejhc',
 'ejhd',
 'ejhe',
 'ejhf',
 'ejhg',
 'ejhh',
 'ejhi',
 'ejhj',
 'ejhk',
 'ejhl',
 'ejhm',
 'ejhn',
 'ejho',
 'ejhp',
 'ejhq',
 'ejhr',
 'ejhs',
 'ejht',
 'ejhu',
 'ejhv',
 'zh6',
 'zh7',
 'zia',
 'zic',
 'eisob',
 'eisoc',
 'eisod',
 'eisoh',
 'zz5',
 'zz6',
 'zz7',
 'planarlimitnoterole']
LOCAL_NAMES+=RECIPROCAL_DEFINITIONS+['zib']
READINGS=('data/einstein-directional-contraction-source-reading-v1.json',
 'data/einstein-planar-shape-limit-source-reading-v1.json',
 'data/einstein-speed-boundary-forecast-source-reading-v1.json',
 'data/einstein-reciprocal-shape-results-source-reading-v1.json')
REVIEWS=('data/einstein-shape-dimension-u0116-review-v1.json','data/einstein-reciprocal-shape-u0117-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['Preserve arbitrary occupied shapes, including holes, nonconvexity and '
 'disconnection. Whole-population inclusion and whole-region coverage both '
 'apply; do not fill a convex hull or substitute a sphere.',
 'Dimensions are finite widths of axial projections, based on supremum and '
 'infimum. Do not require attained endpoints. Require existence of the rest '
 'widths and each moving width; do not give an empty or unbounded set a finite '
 'width.',
 'Keep the same body and full material histories, separate K/k time '
 'conventions, the k reference time and all target K times. A simultaneous '
 'coordinate shape is not an optical image.',
 'Preserve both unchanged transverse widths and the axial rest-to-moving ratio '
 '1:sqrt(1-(v/V)^2). Positive axial widths shrink strictly; zero widths remain '
 'zero.',
 'The larger-speed comparison fixes the same light speed and positive original '
 'width, and compares admissible velocities. Do not infer acceleration '
 'histories or compare unrelated body sizes.',
 'Während is contrast. The first also and parenthesized also auch extend the '
 'preceding sphere and final transforms to arbitrary shapes; the last also '
 'attributes the speed comparison as a consequence.',
 'For each fixed finite shape and K time, all original points approach the V*t '
 'plane with one precision and a common neighborhood for those points. The '
 'neighborhood may depend on shape, time and precision; do not require it '
 'uniformly over all bodies and times.',
 'The limiting planar image preserves the full transverse projection with its '
 'holes and disconnected parts, including degeneracies. It need not fill a '
 'plane or have two-dimensional interior. For v<V, keep forward-image and '
 'inverse-substitution agreement at all positions.',
 'Keep ejhj as a separate interpretive annotation for the lower-speed limit. '
 'Do not evaluate a finite beta or regular inverse transform at v=V and do not '
 'claim an actual light-speed material body.',
 'The superluminal caveat combines lack of a finite beta and lack of a '
 'meaningful physical application of the same considerations and closed '
 'equation family. Do not derive the latter solely from the former or make a '
 'claim about all languages or theories.',
 'The forecast uses the same theory view and all its admissible alternative '
 'situations, preserving the same body, full material membership, frames and '
 'units. Treat light speed as an unattained bound for the specified material '
 'objects; exclude light propagation from that body-speed domain.',
 'Represent the role of infinite comparison speed by neighborhoods above every '
 'finite bound, not an infinite real value or actual object speed. Preserve '
 'nonemptiness, arbitrarily close approach and nonattainment in the common '
 'endpoint-role definition.',
 'Keep the future forecast and übrigens supplement as attributed discourse. Do '
 'not execute the quoted conclusion, assert completed proof now, derive the '
 'supplement causally from the caveat, or restrict the forecast to the later '
 'energy paragraph.',
 'The same-theory reference introduces transitive electrodynamic and '
 'theory-construction dependencies. Preserve their adopted source contracts '
 'instead of replacing the whole theory or a source sentence with a new '
 'primitive.',
 'Reuse the existing rational arithmetic primitives after checking exact '
 'signatures. Audit each other public candidate for existing equivalents; '
 'document reference names become sentence/span/annotation definitions. Keep '
 'the alphabet and common375 vocabulary frozen.',
 'Apply the same full-shape rule to both frame orders with opposite signed velocities. Body identity stays within each application; do not require one body at rest in both frames.',
 'Preserve separate observer times and complete histories, both signed coordinate transforms, equal positive contraction factors and opposite center drift and limit planes. Keep the full transverse image.',
 'The same results include shapes, widths, speed comparison and the stated lower-speed limit. Do not promote the future forecast to a proved result or include the subsequent clock argument. Obviousness remains author attribution.']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=ShapeDimensionVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return ShapeDimensionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][168:173]):visit(n)
    require(len(seen)==468,'Shape-dimension source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][168:173])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','fruit',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=role_definitions()+forwarder_definitions()
    add('eisod','individual',call(voc._symbols['describedreference'],k('eirf'),k('zh7'),qf(reference_roles()['eisod']),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old=='eisod','Unknown planar-limit annotation reference')
    return 'zh7'


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old])
    body=call(m['zfl'],v('va'),k('rd'),dict(kind='quote',body=call(m['ejgt'])),dict(kind='quote',body=call(m['ejhf'])),k('eisn5'),v('vb'))
    return [definition(n['planarlimitnoterole'],[('va','individual'),('vb','situation')],'truth',body)]


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
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][143:148],inverse);return normalize_document(result)



def text_boundaries():
    sentences={}
    for (old,position),path,count,expected_range in zip(SENTENCES.items(),READINGS,(37,17,28,24),((0,270),(271,390),(391,634),(0,160)),strict=True):
        rows=author.read(path)['segments'];require(len(rows)==1,'Sentence reading selection changed')
        row=rows[0];tokens=row['text'].split()
        require(len(tokens)==count and row['range']==list(expected_range),'Sentence range or token boundary changed')
        sentences[old]=dict(position=list(position),tokens=tokens,text=row['text'],range=row['range'])
    require(sentences['zh6']['tokens'][:2]==['Während','also'] and sentences['zh7']['tokens'][1]=='[M0206]' and sentences['zia']['tokens'][5]=='sinnlos;','Paragraph markers changed')
    require(sentences['zib']['tokens'][:3]==['Es','ist','klar,'] and sentences['zib']['tokens'][-2:]==['werden.','—'],'Reciprocal conclusion boundary changed')
    return dict(rule='Page903: indented Während opens paragraph55; the following two sentences remain in it. Es ist klar opens paragraph56. Whitespace tokens, 1-based inclusive spans; semicolon does not split sentence3. The trailing dash marks the next topic without adding an assertion.',sentences=sentences,spans={n:list(p) for n,p in SPANS.items()})



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};unit=units['einstein-1905:u0116'];segments=[];math=[]
    for path in READINGS[:3]:
        for row in author.read(path)['segments']:
            start,end=row['range']
            require(row['unit']==unit['id'] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Original reading differs')
            segments.append(dict(text=row['text'],range=row['range']));math+=row['math']
    require(' '.join(s['text'] for s in segments)==unit['text'] and len(unit['text'])==634,'Whole paragraph changed')
    review=author.read(REVIEWS[0])
    require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    source_units={unit['id']:dict(sha256=unit['text_sha256'],text=unit['text'],segments=segments)}
    reciprocal=units['einstein-1905:u0117'];rows=author.read(READINGS[3])['segments'];require(len(rows)==1,'Reciprocal reading changed')
    row=rows[0]
    require(row['unit']==reciprocal['id'] and row['unit_sha256']==reciprocal['text_sha256'] and row['range']==[0,160] and row['text']==reciprocal['text'],'Reciprocal source differs')
    review=author.read(REVIEWS[1])
    require(review['source']['unit_sha256']==reciprocal['text_sha256'] and review['source']['text']==reciprocal['text'],'Reciprocal review source differs')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Reciprocal review incomplete')
    source_units[reciprocal['id']]=dict(sha256=reciprocal['text_sha256'],text=reciprocal['text'],segments=[dict(text=row['text'],range=row['range'])])
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-shape-dimension-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[168,169,170,171,172],source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        arithmetic_forwarders=forwarder_definitions(),forwarded_arithmetic_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        new_public_relations=31,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=59,core_edition=12,new_source_assertions=4,total_source_assertions=116,total_annotations=32,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible shape-dimension document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],count) for n,count in zip(SENTENCES,(37,17,28,24),strict=True)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values):
    key=(values['eirf'],values['zh7'],canonical(dict(kind='function_ref',symbol=reference_roles()['eisod'])),values['ri'])
    return TemporalReferences({key:values['eisod']},{})


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
    def described(document,node,role,context):
        if node==values['zh7']:return reference_model(values).described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-moving-ellipsoid-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/shape_dimension_visible_profile.py','scripts/check_einstein_shape_dimension_visible.py',
        'scripts/visible_shape_dimension_visible_collection.py','tests/test_shape_dimension_visible.py','docs/einstein-shape-dimension-visible-v1.md',
        'scripts/check_moving_ellipsoid.py','scripts/compose_moving_ellipsoid.py','examples/v014/moving-ellipsoid-core.noema','reports/moving-ellipsoid-v1.json',
        'scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py',
        'scripts/check_final_transform_claim.py','scripts/check_four_coordinate_claim.py','scripts/check_transverse_measured_length.py',
        'scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py'}
    paths.add('scripts/shape_dimension_visible_profile_contracts.py')
    paths.update(('data/apparent-asymmetry-basis-v1.json', 'data/charge-transport-current-basis-v1.json',
        'data/current-distribution-basis-v1.json', 'data/einstein-author-credit-basis-v1.json',
        'data/electric-action-basis-v1.json', 'data/electrodynamics-title-basis-v1.json',
        'data/ether-dispensability-basis-v1.json', 'data/magnetic-action-basis-v1.json',
        'data/speed-boundary-forecast-basis-v1.json', 'data/sufficient-postulates-basis-v1.json',
        'examples/v014/einstein-apparent-asymmetry.noema', 'examples/v014/einstein-author-credit.noema',
        'examples/v014/einstein-charge-transport-current.noema', 'examples/v014/einstein-current-distribution.noema',
        'examples/v014/einstein-electric-action.noema', 'examples/v014/einstein-electrodynamics-title.noema',
        'examples/v014/einstein-ether-dispensability.noema', 'examples/v014/einstein-magnetic-action.noema',
        'examples/v014/einstein-speed-boundary-forecast.noema', 'examples/v014/einstein-sufficient-postulates.noema'))
    for name in ('material_shape_dimensions','directional_contraction_claim','planar_shape_limit','speed_boundary_forecast','reciprocal_shape_results'):
        from importlib import import_module
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        from noema.meaning_catalog import load_catalog
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256)
        paths.update(module.DEPENDENCIES)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved shape-dimension bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-shape-dimension-visible-evidence-1',core_words=375,profile_words=833,profile_edition=59,
        new_public_relations=31,new_reference_primitives=0,new_source_assertions=4,total_source_assertions=116,annotations=32,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
