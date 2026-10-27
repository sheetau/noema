"""Connect one origin clock, its rate question, exact equations and qualified delay."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.shared_reference import definition
from scripts import origin_clock_visible_profile as profile
from scripts.origin_clock_visible_profile import ROOT,OriginClockVisibleVocabulary,write_once
from scripts import check_einstein_shape_dimension_visible as previous
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

SOURCE='examples/v016/einstein-origin-clock-visible-v1.noema'
BRIDGE='data/einstein-origin-clock-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-origin-clock-visible-v1'
LABEL=previous.LABEL
PUBLIC_RELATIONS={'zid': 'clockrestcalibrationtrial',
 'zih': 'describedrealquestionpresentation',
 'zil': 'timeunitlinearconversion'}
RELATIONS=previous.RELATIONS|PUBLIC_RELATIONS
NEW_DEFINITIONS=['stx',
 'svf',
 'svg',
 'svj',
 'svm',
 'svp',
 'svq',
 'svt',
 'svu',
 'svv',
 'svw',
 'svx',
 'svy',
 'svz',
 'swa',
 'swb',
 'swc',
 'ejij',
 'ejik',
 'ejil',
 'ejim',
 'ejin',
 'ejio',
 'ejja',
 'ejip',
 'ejiq',
 'ejjb',
 'ejir',
 'ejis',
 'ejit',
 'ejiu',
 'ejiv',
 'ejiw',
 'ejix',
 'ejiy',
 'eji2',
 'eji3',
 'ejiz',
 'eji4',
 'ejjc',
 'ejjd',
 'ejje',
 'ejjf',
 'ejjg',
 'ejjh',
 'ejji',
 'ejjj',
 'ejjk',
 'ejjl',
 'ejjm',
 'ejjn',
 'ejjo',
 'ejjp',
 'ejjq',
 'ejjr',
 'ejjs',
 'ejjt',
 'ejju',
 'ejjv',
 'ejjw',
 'ejjx',
 'ejjy',
 'ejjz',
 'ejj2',
 'ejj3',
 'ejj4']
SENTENCES={'zif': (57, 1), 'zig': (57, 2), 'zii': (58, 1), 'clockresultssentence': (58, 2)}
SPANS={'zij': ('clockresultssentence', 1, 4),
 'zim': ('clockresultssentence', 5, 20),
 'zin': ('clockresultssentence', 21, 33),
 'clocksecondspan': ('clockresultssentence', 17, 17)}
ROLE_ASSIGNMENTS={'zie': 'originclockrole', 'zik': 'secondunitrole'}
FORWARD_MAPS={}
LOCAL_NAMES=['stx',
 'svf',
 'svg',
 'svj',
 'svm',
 'svp',
 'svq',
 'svt',
 'svu',
 'svv',
 'svw',
 'svx',
 'svy',
 'svz',
 'swa',
 'swb',
 'swc',
 'ejij',
 'ejik',
 'ejil',
 'ejim',
 'ejin',
 'ejio',
 'ejja',
 'ejip',
 'ejiq',
 'ejjb',
 'ejir',
 'ejis',
 'ejit',
 'ejiu',
 'ejiv',
 'ejiw',
 'ejix',
 'ejiy',
 'eji2',
 'eji3',
 'ejiz',
 'eji4',
 'ejjc',
 'ejjd',
 'ejje',
 'ejjf',
 'ejjg',
 'ejjh',
 'ejji',
 'ejjj',
 'ejjk',
 'ejjl',
 'ejjm',
 'ejjn',
 'ejjo',
 'ejjp',
 'ejjq',
 'ejjr',
 'ejjs',
 'ejjt',
 'ejju',
 'ejjv',
 'ejjw',
 'ejjx',
 'ejjy',
 'ejjz',
 'ejj2',
 'ejj3',
 'ejj4',
 'zif',
 'zig',
 'zii',
 'clockresultssentence',
 'zij',
 'zim',
 'zin',
 'zie',
 'zik',
 'clocksecondspan',
 'originclockrole',
 'secondunitrole']
READINGS=('data/einstein-origin-clock-question-source-reading-v1.json',
 'data/einstein-origin-clock-equations-source-reading-v1.json',
 'data/einstein-origin-clock-time-source-reading-v1.json',
 'data/einstein-clock-seconds-claim-source-reading-v1.json')
REVIEWS=('data/einstein-origin-clock-u0118-review-v1.json',
 'data/einstein-origin-clock-equations-u0119-review-v1.json',
 'data/einstein-origin-clock-equations-u0120-review-v1.json',
 'data/einstein-origin-clock-equations-u0121-review-v1.json',
 'data/einstein-origin-clock-equations-u0122-review-v1.json',
 'data/einstein-origin-clock-time-u0123-review-v1.json',
 'data/einstein-origin-clock-time-u0124-review-v1.json',
 'data/einstein-clock-seconds-u0125-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['One clock identity through capabilities, actual origin configuration, question, equations and elapsed '
 'readings.',
 'Admissible K-rest/t and k-rest/tau alternatives are distinct situations; current placement is k origin. '
 'Representative position is at rest, not every internal moving part.',
 'Every self-frame time has a calibrated local display; all candidate displays give that coordinate time. '
 'Reject a second wrong display and preserve exact scale/origin.',
 'All observer times have same-event paired records; preserve histories, current position, nonempty positive '
 'intervals and full candidate coverage.',
 'The described question takes a positive rate candidate and all ordered record pairs, but contains neither '
 'the square-root answer nor answer existence/uniqueness.',
 'Keep both tau=beta*(t-v*x/V^2) and x=v*t for the same clock location and event; retain zero k spatial '
 'coordinates and signed t.',
 'Keep both equalities tau=t*sqrt(1-(v/V)^2)=t-(1-sqrt(1-(v/V)^2))*t, positive root and reciprocal beta.',
 'Use differences for positive elapsed time and same positive conversion scale for both K and tau '
 'differences and all record pairs. No requirement for a measured exactly-one-second pair.',
 'Exact unit delay 1-f and quadratic approximation (v/V)^2/2 stay distinct; common positive constants and '
 'neighborhoods quantify the O(u^4) residual, not finite samples.',
 'Keep author thought-setting, question, obviousness, consequence, qualified alternative, attribution and '
 'text order. Quoted premises do not execute.',
 'Do not import the later A/B transport or acceleration discussion or add concrete residual bounds to the '
 'source assertion.']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=OriginClockVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return OriginClockVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][173:179]):visit(n)
    require(len(seen)==303,'Origin-clock source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][173:179])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','fruit',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    def add(old,body):doc['declarations'].append(definition(n[old],[],'individual',body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:add(old,call(voc._symbols['describedreference'],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown origin-clock reference')
    return {'zie':'zif','zik':'clocksecondspan'}[old]


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old]);x=v('va');scale=v('vc')
    clock=op('and',call(m['ejio'],x,k('zb6')),call(m['ejip'],x,k('zb6')))
    conversion=dict(kind='exists',variable='vc',sort=profile.CUT,
        body=op('and',call(m['sbg'],scale),call(m['zil'],k('rb'),x,scale,k('zb6'))))
    unit=op('and',call(m['ci'],k('rb')),op('and',call(m['ci'],x),conversion))
    return [definition(n['originclockrole'],[('va','individual'),('vb','situation')],'truth',clock),
            definition(n['secondunitrole'],[('va','individual'),('vb','situation')],'truth',unit)]


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
    result['statements']=renamed(doc['statements'][148:154],inverse);return normalize_document(result)



def text_boundaries():
    setting=author.read(READINGS[0])['segments'][0]['text']
    first,last=setting.split(' Wie schnell ',1);last='Wie schnell '+last
    equations=' '.join(row['text'] for row in author.read(READINGS[1])['segments'])
    result=' '.join(row['text'] for path in READINGS[2:] for row in author.read(path)['segments'])
    texts=(first,last,equations,result);sentences={}
    require(first+' '+last==setting,'Clock setting/question split changed')
    for (old,position),value,count in zip(SENTENCES.items(),texts,(41,10,22,33),strict=True):
        tokens=value.split();require(len(tokens)==count,'Clock sentence token boundary changed')
        sentences[old]=dict(position=list(position),tokens=tokens,text=value)
    require(first.endswith('angibt.') and last.endswith('betrachtet?'),'Clock setting/question ending changed')
    require(equations.endswith('[M0214] und [M0215].'),'Joined equations or final period changed')
    tokens=result.split()
    require(tokens[:4]==['Es','ist','also','[M0216]'] and tokens[4:6]==['woraus','folgt,'],'Time-to-delay connection changed')
    require(tokens[16]=='Sekunde' and tokens[19]=='Sek.' and tokens[20:23]==['oder','—','bis'] and tokens[31]=='Sek.' and tokens[-1]=='zurückbleibt.','Seconds and approximation boundaries changed')
    return dict(rule='Pages903–904: paragraph57 has the setting and question; paragraph58 has the two-equation sentence followed by the combined proportional-time and delay sentence. M0216 ends with a comma; Sek. is an abbreviation. Fixed whitespace tokens and 1-based inclusive spans.',
        sentences=sentences,spans={n:list(p) for n,p in SPANS.items()})



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Clock source reading differs')
            require([start,end]==[0,len(unit['text'])],'Clock unit is only partially selected')
            require(unit['id'] not in source_units,'Duplicate clock unit')
            source_units[unit['id']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(source_units)=={f'einstein-1905:u{i:04d}' for i in range(118,126)},'Clock source selection differs')
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old clock review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old clock review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==set(source_units),'Clock review coverage differs')
    require(backprojection(document())==source_excerpt(),'Clock source backprojection differs')
    return dict(schema='noema-einstein-origin-clock-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=list(range(173,179)),source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=3,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=60,core_edition=12,new_source_assertions=6,total_source_assertions=122,total_annotations=32,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible origin-clock document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],count) for n,count in zip(SENTENCES,(41,10,22,33),strict=True)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values):
    return TemporalReferences({(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS},{})


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
        if node in {values[reference_anchor(old)] for old in ROLE_ASSIGNMENTS}:return reference_model(values).described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-shape-dimension-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/origin_clock_visible_profile.py','scripts/origin_clock_visible_profile_contracts.py',
        'scripts/check_einstein_origin_clock_visible.py','scripts/visible_origin_clock_visible_collection.py',
        'tests/test_origin_clock_visible.py','docs/einstein-origin-clock-visible-v1.md',
        'data/einstein-origin-clock-basis-v1.json','data/einstein-clock-delay-basis-v1.json',
        'examples/v014/einstein-origin-clock.noema','examples/v014/einstein-clock-delay.noema'}
    for name in ('origin_clock_question','origin_clock_equations','origin_clock_time','clock_seconds_claim'):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256)
        paths.update(module.DEPENDENCIES)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved origin-clock bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-origin-clock-visible-evidence-1',core_words=375,profile_words=836,profile_edition=60,
        new_public_relations=3,new_reference_primitives=0,new_source_assertions=6,total_source_assertions=122,annotations=32,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
