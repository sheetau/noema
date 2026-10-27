"""Connect the sixth-section heading and its two research subjects."""
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
from scripts import sixth_heading_visible_profile as profile
from scripts.sixth_heading_visible_profile import ROOT,SixthHeadingVisibleVocabulary,write_once
from scripts import check_einstein_kinematic_transition_visible as previous
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

SOURCE='examples/v016/einstein-sixth-heading-visible-v1.noema'
BRIDGE='data/einstein-sixth-heading-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-sixth-heading-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[193]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg',
  'sha256': '82cc01197ef77b18fa71b3cd625580cbce8171a78af66be70df05a20311443e5',
  'actually_displayed': True,
  'independent_human_reading': False,
  'observations': ['907頁の第二部見出しと冒頭仮定の間に、§6の独立した太字見出しがある。',
                   'TransformationからRaum.までが第一主題、ÜberからKräfte.までが第二主題。三行の組版で一つの節題。',
                   'Maxwell-Hertzschen Gleichungenの呼称は第一主題内にあり、その後にfür den leeren Raumが続く。',
                   '続く通常本文Die Maxwell-Hertzschenからgelten möge:は見出しとは別で、直後に六つの方程式が並ぶ。']}]
PUBLIC_RELATIONS={'eiro': 'materialoccupancy',
 'eisar': 'localdrivingunit',
 'eispd': 'fieldequationtransformationinquiry',
 'eispe': 'physicalnatureinquiry'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['s5t',
 's5u',
 's5v',
 's5w',
 's5x',
 's5y',
 'eidz',
 'ejsj',
 'ejsk',
 'ejsl',
 'ejsm',
 'ejsn',
 'ejso',
 'ejsp',
 'ejsq',
 'ejsr',
 'ejss',
 'ejst',
 'ejsu',
 'ejsv',
 'ejsw']
FORWARD_MAPS={}
HEADINGS={'eisph': 8}
SENTENCES={'sixthopeningsentence': (70, 1)}
TOKEN_COUNTS={'sixthopeningsentence': 32}
SENTENCE_SEGMENTS=[{'unit': 'einstein-1905:u0153',
  'text': 'Die Maxwell-Hertzschen Gleichungen für den leeren Raum mögen gültig sein für das ruhende System '
          '[M0286], so daß gelten möge:',
  'text_sha256': '5583b75d073d20c24ee74a508b5da01e71a2e3d034a43c013445417db7d2569c'},
 {'unit': 'einstein-1905:u0154',
  'text': '[M0287]',
  'text_sha256': '5210acf0253bf9322a235e5f2bbf70b3a851ff75bcb4ffab2103853d27c375f1'},
 {'unit': 'einstein-1905:u0155',
  'text': 'wobei ([M0288]) den Vektor der elektrischen, ([M0289]) den der magnetischen Kraft bedeutet.',
  'text_sha256': 'e36963f4b3631aed5d118008860002d0e36cb9922530340ee53c610175f3ff33'}]
SPANS={}
MULTI_SPANS={}
DESIGNATIONS={'eispf': ('eisph', 1)}
FORMS={'eispf': 'Maxwell-Hertzschen Gleichungen'}
ROLE_ASSIGNMENTS={'eispg': 'sixthsectionrole', 'zno': 'sixthopeningscoperole'}
REFERENCE_SORTS={'eispg': 'individual', 'zno': 'individual'}
REFERENCE_ANCHORS={'eispg': 'eisph', 'zno': 'sixthopeningsentence'}
ROLE_DEFINITIONS={'eispg': {'kind': 'definition',
           'name': 'sixthsectionrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'and',
                    'arguments': [{'kind': 'call',
                                   'symbol': 'eisdv',
                                   'arguments': [{'kind': 'call', 'symbol': 'eisph', 'arguments': []},
                                                 {'kind': 'variable', 'name': 'va'},
                                                 {'kind': 'call', 'symbol': 'eispb', 'arguments': []},
                                                 {'kind': 'call', 'symbol': 'eirf', 'arguments': []},
                                                 {'kind': 'number', 'numerator': 2, 'denominator': 1},
                                                 {'kind': 'number', 'numerator': 6, 'denominator': 1},
                                                 {'kind': 'variable', 'name': 'vb'}]},
                                  {'kind': 'not',
                                   'arguments': [{'kind': 'equal',
                                                  'arguments': [{'kind': 'variable', 'name': 'va'},
                                                                {'kind': 'call',
                                                                 'symbol': 'eispb',
                                                                 'arguments': []}]}]}]}},
 'zno': {'kind': 'definition',
         'name': 'sixthopeningscoperole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'exists',
                                 'variable': 'vc',
                                 'sort': {'kind': 'description', 'result': 'content'},
                                 'body': {'kind': 'call',
                                          'symbol': 'ug',
                                          'arguments': [{'kind': 'call',
                                                         'symbol': 'sixthopeningsentence',
                                                         'arguments': []},
                                                        {'kind': 'call', 'symbol': 'rd', 'arguments': []},
                                                        {'kind': 'variable', 'name': 'vc'},
                                                        {'kind': 'variable', 'name': 'va'},
                                                        {'kind': 'variable', 'name': 'vb'}]}},
                                {'kind': 'and',
                                 'arguments': [{'kind': 'not',
                                                'arguments': [{'kind': 'equal',
                                                               'arguments': [{'kind': 'variable',
                                                                              'name': 'va'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'eispg',
                                                                              'arguments': []}]}]},
                                               {'kind': 'not',
                                                'arguments': [{'kind': 'equal',
                                                               'arguments': [{'kind': 'variable',
                                                                              'name': 'va'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'eisdx',
                                                                              'arguments': []}]}]}]}]}}}
LOCAL_NAMES=['s5t',
 's5u',
 's5v',
 's5w',
 's5x',
 's5y',
 'eidz',
 'ejsj',
 'ejsk',
 'ejsl',
 'ejsm',
 'ejsn',
 'ejso',
 'ejsp',
 'ejsq',
 'ejsr',
 'ejss',
 'ejst',
 'ejsu',
 'ejsv',
 'ejsw',
 'zno',
 'eispf',
 'eispg',
 'eisph',
 'sixthopeningsentence',
 'sixthsectionrole',
 'sixthopeningscoperole']
READINGS=('data/einstein-sixth-section-source-reading-v1.json',)
REVIEWS=('data/einstein-sixth-section-u0152-review-v1.json',)
SEMANTIC_REVIEW=['見出しの二つの文は一つの節題。現在の具体的な場や領域の仮定は後続本文に残す。',
 '起電力は採用済みの局所的な力/電荷という読みを保ち、閉回路だけに限定しない。',
 '真空領域の条件と、力を定義する試験電荷の条件を一つの実試行へ同時に要求しない。',
 '静止・磁場と平行な速度による零作用の比較例を保ち、運動だけから非零作用を補わない。',
 '閉じた規約の引用は参照として扱い、参照照合から内容を実行しない。',
 '有限の引数結合診断を全実数領域・軌跡・微分の証明として扱わない。',
 '冒頭仮定範囲の役割は同じ箇所・著者・文脈で何らかの内容を仮定として採用する範囲である。閉じた内容全体への存在量化を保ち、特定の後続の物理法則やその真理を参照取得の条件にしない。',
 '範囲は全節と第一部区分から区別する。役割だけで世界唯一の範囲とはせず、指定本文アンカーで参照先を固定する。',
 '節の役割から冒頭範囲を参照しない。範囲から節への一方向依存とし、自己参照を避ける。',
 '歴史的呼称は見出し箇所における最初の呼称として既存designationreferenceで参照する。本文文番号を見出しに付けず、綴りは別添えとする。']
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=['固定アルファベット・共通375語を維持し、採用済み4規約を任意profile66へ公開する。公開語数869。',*SEMANTIC_REVIEW]


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=SixthHeadingVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return SixthHeadingVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==172,'Sixth-heading source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown sixth-heading reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown sixth-heading reference')
    sort=REFERENCE_SORTS[old]
    return 'describedsettingreference' if sort=='situation' else 'describedcutreference' if sort==profile.CUT else 'describedreference'


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
    result['statements']=renamed(doc['statements'][190:191],inverse);return normalize_document(result)



def text_boundaries():
    inventory=author.read(author.UNITS)['units'];units={u['id']:u for u in inventory}
    require(previous.SENTENCES=={'transitionstatement':(69,1)},'Previous paragraph boundary changed')
    for row in SENTENCE_SEGMENTS:
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['text_sha256'],'Opening sentence segment changed')
    require([units[r['unit']]['kind'] for r in SENTENCE_SEGMENTS]==['body','equation','body'],'Opening sentence structure changed')
    text=' '.join(r['text'] for r in SENTENCE_SEGMENTS);tokens=text.split()
    require(len(tokens)==TOKEN_COUNTS['sixthopeningsentence'],'Opening sentence token count changed')
    headings=[u for u in inventory if u['kind']=='heading'];heading=headings[7]
    require(heading['id']=='einstein-1905:u0152' and headings[8]['id']=='einstein-1905:u0178','Section boundary changed')
    require(heading['text'].count(FORMS['eispf'])==1,'Heading designation occurrence changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph70 sentence1 includes u0153, six displayed equations u0154, and the lower-case wobei continuation u0155. The separate heading is occurrence8.',
        headings={'eisph':dict(occurrence=8,depth=2,ordinal=6,parent='eispb',division='eispg',text=heading['text'],first_unit='einstein-1905:u0152',last_unit='einstein-1905:u0177',next_unit='einstein-1905:u0178')},
        sentences={'sixthopeningsentence':dict(position=[70,1],tokens=tokens,text=text,segments=SENTENCE_SEGMENTS)},
        spans={},multi_sentence_spans={},designations={n:list(p) for n,p in DESIGNATIONS.items()},designation_forms=FORMS)



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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Sixth heading source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(152,153)}
    require(set(coverage)==expected,'Sixth heading source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old sixth heading review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old sixth heading review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Sixth heading review coverage differs')
    require(SOURCE_ORDER==[193],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Sixth heading source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-sixth-heading-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=4,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=66,core_edition=12,new_source_assertions=1,total_source_assertions=158,total_annotations=34,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible sixth-heading document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedcutreference':return CutReferences(roles)
    if kind=='describedsettingreference':return SettingReferences(roles)
    require(kind=='describedreference','Unknown sixth-heading reference type');return TemporalReferences(roles,{})


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
        if node in {values[n] for n in (*SENTENCES,*HEADINGS)}:
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
    prior_path='reports/einstein-kinematic-transition-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/sixth_heading_visible_profile.py','scripts/sixth_heading_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_sixth_heading_visible.py','scripts/visible_sixth_heading_visible_collection.py',
        'tests/test_sixth_heading_visible.py','docs/einstein-sixth-heading-visible-v1.md'}
    for name in ('sixth_section_heading','vacuum_field_domain','magnetic_action'):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved sixth-heading bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-sixth-heading-visible-evidence-1',core_words=375,profile_words=869,profile_edition=66,
        new_public_relations=4,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=158,annotations=34,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
