"""Connect the kinematic summary, prospective application and second part."""
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
from scripts import kinematic_transition_visible_profile as profile
from scripts.kinematic_transition_visible_profile import ROOT,KinematicTransitionVisibleVocabulary,write_once
from scripts import check_einstein_velocity_parallel_visible as previous
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

SOURCE='examples/v016/einstein-kinematic-transition-visible-v1.noema'
BRIDGE='data/einstein-kinematic-transition-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-kinematic-transition-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[19, 20, 192]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg',
  'sha256': '82cc01197ef77b18fa71b3cd625580cbce8171a78af66be70df05a20311443e5',
  'actually_displayed': True,
  'independent_human_reading': False,
  'observations': ['907頁上部の独立段落Wir haben nunからzu zeigenまで一文。',
                   'hergeleitet und gehenで総括と今後の課題を接続する。',
                   'II. Elektrodynamischer Teil.はその後の独立見出しで、直後は§6。']}]
PUBLIC_RELATIONS={'zna': 'taskrequiredproposition',
 'zng': 'presentedexample',
 'znh': 'prospectivetaskentry',
 'eisdh': 'kinematicinquirydomain'}
REUSED_DEFINITIONS=['senz']
NEW_DEFINITIONS=['eig4',
 'eihn',
 'ejrz',
 'ejr2',
 'ejr3',
 'ejr4',
 'ejr5',
 'ejr6',
 'ejr7',
 'ejsa',
 'ejsb',
 'ejsc',
 'ejsd',
 'ejse',
 'ejsg',
 'ejsf',
 'ejsh',
 'ejsi']
FORWARD_MAPS={}
HEADINGS={'eispc': 7}
SENTENCES={'transitionstatement': (69, 1)}
TOKEN_COUNTS={'transitionstatement': 26}
SPANS={'zni': ('transitionstatement', 1, 15), 'znj': ('transitionstatement', 16, 26)}
MULTI_SPANS={}
DESIGNATIONS={}
FORMS={}
ROLE_ASSIGNMENTS={'zm7': 'transitiontaskrole',
 'znb': 'transitionfirstpartrole',
 'znc': 'transitiontheoryrole',
 'eispb': 'transitionsecondpartrole'}
REFERENCE_SORTS={'zm7': 'individual', 'znb': 'individual', 'znc': 'individual', 'eispb': 'individual'}
REFERENCE_ANCHORS={'zm7': 'znj', 'znb': 'zni', 'znc': 'zni', 'eispb': 'eispc'}
ROLE_DEFINITIONS={'zm7': {'kind': 'definition',
         'name': 'transitiontaskrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'exists',
                  'variable': 'vc',
                  'sort': 'individual',
                  'body': {'kind': 'call',
                           'symbol': 'zna',
                           'arguments': [{'kind': 'call', 'symbol': 'rd', 'arguments': []},
                                         {'kind': 'variable', 'name': 'va'},
                                         {'kind': 'variable', 'name': 'vc'},
                                         {'kind': 'variable', 'name': 'vb'}]}}},
 'znb': {'kind': 'definition',
         'name': 'transitionfirstpartrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'eisdv',
                                 'arguments': [{'kind': 'call', 'symbol': 'firstpartheading', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                               {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                               {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                               {'kind': 'variable', 'name': 'vb'}]},
                                {'kind': 'equal',
                                 'arguments': [{'kind': 'variable', 'name': 'va'},
                                               {'kind': 'call', 'symbol': 'eisdx', 'arguments': []}]}]}},
 'znc': {'kind': 'definition',
         'name': 'transitiontheoryrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'ejrz',
                                 'arguments': [{'kind': 'variable', 'name': 'va'},
                                               {'kind': 'variable', 'name': 'vb'}]},
                                {'kind': 'and',
                                 'arguments': [{'kind': 'call',
                                                'symbol': 'zt',
                                                'arguments': [{'kind': 'variable', 'name': 'va'},
                                                              {'kind': 'quote',
                                                               'body': {'kind': 'call',
                                                                        'symbol': 'eion',
                                                                        'arguments': []}},
                                                              {'kind': 'call',
                                                               'symbol': 'znb',
                                                               'arguments': []},
                                                              {'kind': 'variable', 'name': 'vb'}]},
                                               {'kind': 'call',
                                                'symbol': 'zt',
                                                'arguments': [{'kind': 'variable', 'name': 'va'},
                                                              {'kind': 'quote',
                                                               'body': {'kind': 'call',
                                                                        'symbol': 'eiot',
                                                                        'arguments': []}},
                                                              {'kind': 'call',
                                                               'symbol': 'znb',
                                                               'arguments': []},
                                                              {'kind': 'variable', 'name': 'vb'}]}]}]}},
 'eispb': {'kind': 'definition',
           'name': 'transitionsecondpartrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'and',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisdv',
                                   'arguments': [{'kind': 'call', 'symbol': 'eispc', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                                 {'kind': 'number', 'numerator': 1, 'denominator': 1},
                                                 {'kind': 'number', 'numerator': 2, 'denominator': 1},
                                                 {'kind': 'variable', 'name': 'vb'}]},
                                  {'kind': 'not',
                                   'arguments': [{'kind': 'equal',
                                                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                                                {'kind': 'call',
                                                                 'symbol': 'eisdx',
                                                                 'arguments': []}]}]}]}}}
LOCAL_NAMES=['zm7',
 'znb',
 'znc',
 'zni',
 'znj',
 'eig4',
 'eihn',
 'ejrz',
 'ejr2',
 'ejr3',
 'ejr4',
 'ejr5',
 'ejr6',
 'ejr7',
 'ejsa',
 'ejsb',
 'ejsc',
 'ejsd',
 'ejse',
 'ejsg',
 'ejsf',
 'ejsh',
 'eispb',
 'eispc',
 'ejsi',
 'transitionstatement',
 'transitiontaskrole',
 'transitionfirstpartrole',
 'transitiontheoryrole',
 'transitionsecondpartrole']
READINGS=('data/einstein-kinematic-transition-source-reading-v1.json',
 'data/einstein-electrodynamic-part-source-reading-v1.json')
REVIEWS=('data/einstein-kinematic-transition-u0150-review-v1.json',
 'data/einstein-electrodynamic-part-u0151-review-v1.json')
SEMANTIC_REVIEW=['必要集合は課題・主体・現在段階から選び、検査済みの項目だけへ絞らない。',
 '各命題の同じ閉じた内容を導出提示と前提使用へ渡す。真偽の一致だけでは代用しない。',
 '一つの応用体系は複数の説明を含められる。各命題に別の例を割り当てない。',
 'znhへ目標の引用を渡し、その場で目標を実行しない。',
 '課題参照の役割は非空の必要項目と著者・段階を固定し、本文アンカーが参照先を指定する。役割だけの一意性や達成を主張しない。',
 '理論参照は第一部の範囲を使い、課題参照を依存先にしない。自己参照する目標引用を役割へ埋め込まない。',
 '第一部の論述範囲を第一部区分と同じ対象として参照する読みを明示し、§5だけに狭めない。',
 '全閉記述への量化を保持する。二引用への有限置換は結合診断であり、定義同一性を検査してから適用する。',
 '末尾注は本文の参照位置に従い、配列位置だけで第二部へ移さない。']
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=['固定アルファベット・共通375語を維持し、採用済み4規約を任意profile65へ公開する。公開語数865。',*SEMANTIC_REVIEW]


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=KinematicTransitionVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return KinematicTransitionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==259,'Kinematic-transition source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','round',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown kinematic-transition reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown kinematic-transition reference')
    sort=REFERENCE_SORTS[old]
    return 'describedsettingreference' if sort=='situation' else 'describedcutreference' if sort==profile.CUT else 'describedreference'


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
    result['statements']=renamed(doc['statements'][187:190],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read(author.UNITS)['units'];units={u['id']:u['text'] for u in inventory}
    text=units['einstein-1905:u0150'];tokens=text.split()
    require(set(previous.SENTENCES.values())=={(68,1),(68,2)},'Previous paragraph boundary changed')
    require(len(tokens)==26 and tokens[14:17]==['hergeleitet','und','gehen'],'Summary/transition boundary changed')
    headings=[u for u in inventory if u['kind']=='heading']
    require(headings[6]['id']=='einstein-1905:u0151' and headings[7]['id']=='einstein-1905:u0152','Part heading order changed')
    require(headings[6]['text']=='II. Elektrodynamischer Teil.','Part heading text changed')
    require([u['text'].split('.')[0] for u in headings[7:]]==['§ 6','§ 7','§ 8','§ 9','§ 10'],'Subordinate section numbering changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph69 is one sentence: tokens1..15 summarize derivation, tokens16..26 introduce the application task. The separate second-part heading follows it.',
        headings={'eispc':dict(occurrence=7,depth=1,ordinal=2,parent='eirf',division='eispb',text=headings[6]['text'],first_unit='einstein-1905:u0151',subsections=[6,7,8,9,10],footnotes_follow_reference_positions=True)},
        sentences={'transitionstatement':dict(position=[69,1],tokens=tokens,text=text)},
        spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},designations={},designation_forms={})



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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Kinematic transition source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(150,152)}
    require(set(coverage)==expected,'Kinematic transition source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old kinematic transition review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old kinematic transition review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Kinematic transition review coverage differs')
    require(SOURCE_ORDER==[19,20,192],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Kinematic transition source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-kinematic-transition-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=4,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=65,core_edition=12,new_source_assertions=3,total_source_assertions=157,total_annotations=33,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible kinematic-transition document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedcutreference':return CutReferences(roles)
    if kind=='describedsettingreference':return SettingReferences(roles)
    require(kind=='describedreference','Unknown kinematic-transition reference type');return TemporalReferences(roles,{})


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
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedcutreference','describedsettingreference')}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-velocity-parallel-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/kinematic_transition_visible_profile.py','scripts/kinematic_transition_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_kinematic_transition_visible.py','scripts/visible_kinematic_transition_visible_collection.py',
        'tests/test_kinematic_transition_visible.py','docs/einstein-kinematic-transition-visible-v1.md'}
    for name in ('kinematic_transition_claim','electrodynamic_part_heading','kinematic_foundation'):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved kinematic-transition bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-kinematic-transition-visible-evidence-1',core_words=375,profile_words=865,profile_edition=65,
        new_public_relations=4,new_reference_primitives=0,new_source_assertions=3,total_source_assertions=157,annotations=33,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
