"""Connect the sublight bound, deficit explanation and light-speed fixed point."""
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
from scripts import velocity_axial_visible_profile as profile
from scripts.velocity_axial_visible_profile import ROOT,VelocityAxialVisibleVocabulary,write_once
from scripts import check_einstein_velocity_axial_visible as previous
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

SOURCE='examples/v016/einstein-velocity-bound-light-visible-v1.noema'
BRIDGE='data/einstein-velocity-bound-light-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-velocity-bound-light-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[8, 9, 10, 11, 12, 13]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg',
  'sha256': 'fda62af14de6978b5938e09fa98e63bbf2b29010c1b4250a4b7f41e62bc57591',
  'actually_displayed': True,
  'tool_chunk': 'df68eb',
  'independent_human_reading': False}]
PUBLIC_RELATIONS={}
NEW_DEFINITIONS=['s3o',
 's3q',
 's3r',
 's3s',
 's3t',
 's3u',
 's3v',
 's3w',
 's3x',
 's3y',
 's4a',
 's4b',
 's4d',
 's4e',
 's4f',
 's4g',
 's4i',
 'ejpv',
 'ejpw',
 'ejpx',
 'ejpy',
 'ejpz',
 'ejp2',
 'ejp3',
 'ejp4',
 'ejp5',
 'ejp6',
 'ejp7',
 'ejqa',
 'ejqb',
 'ejqc',
 'ejqd',
 'ejqe',
 'ejqf',
 'ejqg',
 'ejqh',
 'ejqi',
 'ejqj',
 'ejqk',
 'ejql',
 'ejqm',
 'ejqt',
 'ejqu',
 'ejqn',
 'ejqo',
 'ejqp',
 'ejqq',
 'ejqr',
 'ejqs']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'zli': (66, 1), 'zlk': (66, 2), 'zlm': (67, 1), 'lightdisplaysentence': (67, 2)}
TOKEN_COUNTS={'zli': 22, 'zlk': 18, 'zlm': 16, 'lightdisplaysentence': 6}
SPANS={'zlj': ('zlk', 1, 15),
 'zll': ('zlk', 18, 18),
 'zln': ('lightdisplaysentence', 6, 6),
 'kappadeficitanchor': ('zlk', 7, 7),
 'lambdadeficitanchor': ('zlk', 9, 9)}
MULTI_SPANS={}
DESIGNATIONS={}
ROLE_ASSIGNMENTS={'zlg': 'kappadeficitrole', 'zlh': 'lambdadeficitrole'}
REFERENCE_SORTS={'zlg': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zlh': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}
REFERENCE_ANCHORS={'zlg': 'kappadeficitanchor', 'zlh': 'lambdadeficitanchor'}
ROLE_DEFINITIONS={'zlg': {'kind': 'definition',
         'name': 'kappadeficitrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 's3o',
                  'arguments': [{'kind': 'call', 'symbol': 'tc', 'arguments': []},
                                {'kind': 'call', 'symbol': 'zb7', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'}]}},
 'zlh': {'kind': 'definition',
         'name': 'lambdadeficitrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 's3o',
                  'arguments': [{'kind': 'call', 'symbol': 'tc', 'arguments': []},
                                {'kind': 'call', 'symbol': 'zkq', 'arguments': []},
                                {'kind': 'variable', 'name': 'va'}]}}}
LOCAL_NAMES=['s3o',
 's3q',
 's3r',
 's3s',
 's3t',
 's3u',
 's3v',
 'zlg',
 'zlh',
 'zli',
 'zlj',
 'zlk',
 'zll',
 's3w',
 's3x',
 's3y',
 's4a',
 's4b',
 's4d',
 's4e',
 's4f',
 'zlm',
 'zln',
 's4g',
 's4i',
 'ejpv',
 'ejpw',
 'ejpx',
 'ejpy',
 'ejpz',
 'ejp2',
 'ejp3',
 'ejp4',
 'ejp5',
 'ejp6',
 'ejp7',
 'ejqa',
 'ejqb',
 'ejqc',
 'ejqd',
 'ejqe',
 'ejqf',
 'ejqg',
 'ejqh',
 'ejqi',
 'ejqj',
 'ejqk',
 'ejql',
 'ejqm',
 'ejqt',
 'ejqu',
 'ejqn',
 'ejqo',
 'ejqp',
 'ejqq',
 'ejqr',
 'ejqs',
 'lightdisplaysentence',
 'kappadeficitanchor',
 'lambdadeficitanchor',
 'kappadeficitrole',
 'lambdadeficitrole']
READINGS=('data/einstein-velocity-deficit-source-reading-v1.json',
 'data/einstein-velocity-light-source-reading-v1.json')
REVIEWS=('data/einstein-velocity-deficit-u0143-review-v1.json',
 'data/einstein-velocity-deficit-u0144-review-v1.json',
 'data/einstein-velocity-light-u0145-review-v1.json',
 'data/einstein-velocity-light-u0146-review-v1.json')
SEMANTIC_REVIEW=['一般主張の0≤v,w<Vと、不足量の0<κ,λ<Vに対応する0<v,w<Vを混同しない。',
 'κとλの交換で商が同じでも、元のv/wへの対応は別々に検査する。',
 '本文位置の違うzlj・zlk・zllは仮定提示、局所範囲、表示式に対応し、同一参照へ併合しない。',
 '役割記述は引用して照合する。参照検索により候補や仮定の真偽を評価しない。',
 '原刊M0273の分母1+w/Vと電子転記の差は既存訂正層を維持する。',
 '光速の点の条件付き適用と、系速度を光速とする実在仮定を混同しない。',
 '著者の論証提示、有限診断、有理多項式証拠、全実数の証明、独立読解は区別する。']
RELATIONS=previous.RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=['固定アルファベット・共通375語とprofile64の861語をそのまま使用し、公開語を追加しない。',*SEMANTIC_REVIEW]


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=VelocityAxialVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return VelocityAxialVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==335,'Velocity-bound-light source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','nao',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:
        add(old,call(voc._symbols[reference_kind(old)],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')),REFERENCE_SORTS[old])
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown velocity-bound-light reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown deficit reference');return 'describedcutreference'


def role_definitions():
    return renamed(list(ROLE_DEFINITIONS.values()),mapping()|names())


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
    result['statements']=renamed(doc['statements'][175:181],inverse);return normalize_document(result)



def text_boundaries():
    units={u['id']:u['text'] for u in author.read(author.UNITS)['units']}
    first,second=units['einstein-1905:u0143'].split(' Setzt man ',1)
    second='Setzt man '+second+' '+units['einstein-1905:u0144']
    third,fourth=units['einstein-1905:u0145'].split(' Man erhält ',1)
    fourth='Man erhält '+fourth+' '+units['einstein-1905:u0146']
    require(set(previous.SENTENCES.values())=={(65,1),(65,2)},'Previous paragraph boundary changed')
    sentences={}
    for old,value in zip(SENTENCES,(first,second,third,fourth),strict=True):
        tokens=value.split();require(len(tokens)==TOKEN_COUNTS[old],'Bound/light sentence boundary changed')
        sentences[old]=dict(position=list(SENTENCES[old]),tokens=tokens,text=value)
    require(second.split()[6]=='[M0268]' and second.split()[8]=='[M0269]','Deficit reference anchors changed')
    require(second.endswith('so ist: [M0271]') and fourth.endswith('Fall: [M0273]'),'Displayed formula boundary changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Page906 paragraphs66 and67 each contain a general claim followed by its explanation or displayed specialization. The assumption clause, local scope and formula are distinct locations within sentence66.2.',
        headings={},sentences=sentences,spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},designations={})



def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math={};coverage={}
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Velocity bound/light source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(143,147)}
    require(set(coverage)==expected,'Velocity bound/light source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old velocity bound/light review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old velocity bound/light review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Velocity bound/light review coverage differs')
    require(SOURCE_ORDER==list(range(8,14)),'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Velocity bound/light source backprojection differs')
    return dict(schema='noema-einstein-velocity-bound-light-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=0,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=64,core_edition=12,new_source_assertions=6,total_source_assertions=149,total_annotations=32,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible velocity-bound-light document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedcutreference'):
    require(kind=='describedcutreference','Unknown deficit reference type')
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS}
    return CutReferences(roles)


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
            require(kind in result,'Unknown typed reference')
            return result[kind](document,node,role,context)
        return lookup
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedcutreference',)}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-velocity-axial-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_velocity_bound_light_visible.py','scripts/visible_velocity_bound_light_visible_collection.py',
        'tests/test_velocity_bound_light_visible.py','docs/einstein-velocity-bound-light-visible-v1.md'}
    for name in ('velocity_deficit_claim','velocity_light_claim'):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256);paths.update(module.DEPENDENCIES)
    paths.update(row['path'] for row in SOURCE_VISUAL_REVIEW)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved velocity-bound-light bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-velocity-bound-light-visible-evidence-1',core_words=375,profile_words=861,profile_edition=64,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=6,total_source_assertions=149,annotations=32,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
