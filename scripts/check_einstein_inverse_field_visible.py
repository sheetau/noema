"""Connect two inverse methods, required identity and coefficient product one."""
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
from scripts import field_comparison_visible_profile as profile
from scripts.field_comparison_visible_profile import ROOT,FieldComparisonVisibleVocabulary,write_once
from scripts import check_einstein_field_comparison_visible as previous
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

SOURCE='examples/v016/einstein-inverse-field-visible-v1.noema'
BRIDGE='data/einstein-inverse-field-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-inverse-field-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[31, 25]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
  'sha256': '68b45874f2d701b5270ff8c1a1ae9b3658c54058748eb483a53663368b6df049',
  'actually_displayed': True,
  'tool_chunk': 'b742de',
  'independent_human_reading': False,
  'observation': 'Bildet manから二方法・必要性・コロン後の積1まで一文。次段落はFerner folgt aus Symmetriegründen。'}]
PUBLIC_RELATIONS={}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['sal2',
 'san2',
 'saq2',
 'sbi2',
 'sbj2',
 'sbk2',
 'sbl2',
 'sbm2',
 'sbn2',
 'sbo2',
 'sbp2',
 'sbq2',
 'sbr2',
 'sbs2',
 'ejur',
 'ejus',
 'ejut',
 'ejuu',
 'ejuv',
 'ejuw',
 'ejux',
 'ejuy',
 'ejuz',
 'ejva',
 'ejvb',
 'ejvc',
 'ejvd',
 'ejve']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'inversefieldsentence': (74, 1)}
TEXT_SENTENCES={'inversefieldsentence': (74, 1)}
TOKEN_COUNTS={'inversefieldsentence': 49}
SENTENCE_SEGMENTS=[{'unit': 'einstein-1905:u0165',
  'text': 'Bildet man nun die Umkehrung dieses Gleichungssystems, erstens durch Auflösen der soeben '
          'erhaltenen Gleichungen, zweitens durch Anwendung der Gleichungen auf die inverse Transformation '
          '(von [M0308] auf [M0309]), welche durch die Geschwindigkeit [M0310] charakterisiert ist, so '
          'folgt, indem man berücksichtigt, daß die beiden so erhaltenen Gleichungssysteme identisch sein '
          'müssen:',
  'sha256': 'b2311a850c965bd3057f9e5894af939a03ae04b32b0c880b80746bcae41a50d3'},
 {'unit': 'einstein-1905:u0166',
  'text': '[M0311].',
  'sha256': '4824f6b0e322b323d52fce2144e82291c007abe1907e4adfc354bef4c553732c'}]
SPANS={'zoe': ('inversefieldsentence', 1, 34),
 'zn3': ('inversefieldsentence', 35, 48),
 'eisp5': ('inversefieldsentence', 49, 49),
 'inversefirstanchor': ('inversefieldsentence', 8, 14),
 'inversesecondanchor': ('inversefieldsentence', 15, 34)}
MULTI_SPANS={}
DESIGNATIONS={}
FORMS={}
ROLE_ASSIGNMENTS={'inversefirstmethod': 'inversefirstmethodrole', 'inversesecondmethod': 'inversesecondmethodrole'}
REFERENCE_SORTS={'inversefirstmethod': 'individual', 'inversesecondmethod': 'individual'}
REFERENCE_ANCHORS={'inversefirstmethod': 'inversefirstanchor', 'inversesecondmethod': 'inversesecondanchor'}
ROLE_DEFINITIONS={'inversefirstmethod': {'kind': 'definition',
                        'name': 'inversefirstmethodrole',
                        'parameters': [{'name': 'va', 'sort': 'individual'},
                                       {'name': 'vb', 'sort': 'situation'}],
                        'result': 'truth',
                        'body': {'kind': 'call',
                                 'symbol': 's2w',
                                 'arguments': [{'kind': 'call',
                                                'symbol': 'zlx',
                                                'arguments': [{'kind': 'variable', 'name': 'va'},
                                                              {'kind': 'variable', 'name': 'vb'}]},
                                               {'kind': 'quote',
                                                'body': {'kind': 'call', 'symbol': 'ejuh', 'arguments': []}},
                                               {'kind': 'quote',
                                                'body': {'kind': 'call', 'symbol': 'ejus', 'arguments': []}},
                                               {'kind': 'lambda',
                                                'parameters': [{'name': 'vc',
                                                                'sort': {'kind': 'description',
                                                                         'result': 'content'}},
                                                               {'name': 'vd',
                                                                'sort': {'kind': 'description',
                                                                         'result': 'content'}}],
                                                'body': {'kind': 'call',
                                                         'symbol': 'zla',
                                                         'arguments': [{'kind': 'variable', 'name': 'vc'},
                                                                       {'kind': 'variable', 'name': 'vd'},
                                                                       {'kind': 'variable',
                                                                        'name': 'vb'}]}}]}},
 'inversesecondmethod': {'kind': 'definition',
                         'name': 'inversesecondmethodrole',
                         'parameters': [{'name': 'va', 'sort': 'individual'},
                                        {'name': 'vb', 'sort': 'situation'}],
                         'result': 'truth',
                         'body': {'kind': 'call',
                                  'symbol': 's2w',
                                  'arguments': [{'kind': 'call',
                                                 'symbol': 'zlx',
                                                 'arguments': [{'kind': 'variable', 'name': 'va'},
                                                               {'kind': 'variable', 'name': 'vb'}]},
                                                {'kind': 'quote',
                                                 'body': {'kind': 'call', 'symbol': 'ejuh', 'arguments': []}},
                                                {'kind': 'quote',
                                                 'body': {'kind': 'call', 'symbol': 'ejut', 'arguments': []}},
                                                {'kind': 'lambda',
                                                 'parameters': [{'name': 'vc',
                                                                 'sort': {'kind': 'description',
                                                                          'result': 'content'}},
                                                                {'name': 'vd',
                                                                 'sort': {'kind': 'description',
                                                                          'result': 'content'}}],
                                                 'body': {'kind': 'call',
                                                          'symbol': 'zla',
                                                          'arguments': [{'kind': 'variable', 'name': 'vc'},
                                                                        {'kind': 'variable', 'name': 'vd'},
                                                                        {'kind': 'variable',
                                                                         'name': 'vb'}]}}]}}}
DERIVED_REFERENCES={'zoc': {'relation': 'zlx', 'arguments': ['inversefirstmethod', 'ri']},
 'zod': {'relation': 'zlx', 'arguments': ['inversesecondmethod', 'ri']}}
LOCAL_NAMES=['sal2',
 'san2',
 'saq2',
 'sbi2',
 'sbj2',
 'sbk2',
 'sbl2',
 'sbm2',
 'sbn2',
 'sbo2',
 'sbp2',
 'sbq2',
 'sbr2',
 'sbs2',
 'ejur',
 'ejus',
 'ejut',
 'ejuu',
 'ejuv',
 'ejuw',
 'ejux',
 'ejuy',
 'ejuz',
 'ejva',
 'ejvb',
 'ejvc',
 'ejvd',
 'ejve',
 'inversefieldsentence',
 'zoe',
 'zn3',
 'eisp5',
 'inversefirstanchor',
 'inversesecondanchor',
 'inversefirstmethod',
 'inversesecondmethod',
 'inversefirstmethodrole',
 'inversesecondmethodrole',
 'zoc',
 'zod']
READINGS=('data/einstein-inverse-field-claim-source-reading-v1.json',)
REVIEWS=('data/einstein-inverse-field-claim-u0165-review-v1.json',
 'data/einstein-inverse-field-claim-u0166-review-v1.json')
SEMANTIC_REVIEW=['第一係数の非零性は逆数の定義域。負の係数を許し、正値・偶性・係数自身が1は補わない。',
 '第一法の1/ψ(v)と第二法のψ(-v)を別に構成する。同じ物理的両場・座標域・逆速度の対応を保持する。',
 '式の同一性は全有効入力での係数写像一致。零の場の一例での一致から積1を導かない。',
 '必要性は非空の全選択状況への条件。著者の推論提示と外部の数学・物理的証明を区別する。',
 '原刊909頁のφは直前908頁のψと同じ第六節の係数。第三節のφを参照せず、固定MathMLと字形差を残す。',
 '既存describedreferenceで第一・第二の方法を別の原文位置へ結び、既存methodsteps(zlx)で各有限手順列を得る。任意型の新しい取得規約は足さない。',
 '役割は同じ現在の六式ejuhからejus/ejutへ至る非空のs2w手順を要求し、同じ文脈のzlaだけを許容関係に用いる。',
 '役割を引用して参照を取得し、その取得自体で役割を実行しない。存在・唯一性、式の真理、実行済み、積1を補わない。',
 'ejus/ejutからzoc/zod/方法参照への逆依存がないことを、参照→役割の辺を含む前検査で確認する。',
 'zoe anchors the two-method introduction; zn3 anchors so folgt with its explicit necessity reason. Both '
 'statements are supported by the whole single sentence, not isolated quotations of their anchor spans.',
 '現在の二つの原文主張を原文順31→25で追加する。原文のファイル上の順序と著者の叙述順を区別する。',
 '固定アルファベット・共通375語・任意profile70の879語をそのまま用い、新しい基本関係や参照規約を追加しない。']
RELATIONS=previous.RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=SEMANTIC_REVIEW


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=FieldComparisonVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return FieldComparisonVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==146,'Inverse-field source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','book',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,ref in DERIVED_REFERENCES.items():
        add(old,call(voc._symbols[RELATIONS[ref['relation']]],*(k(n) for n in ref['arguments'])),next(d['result'] for d in source_excerpt()['declarations'] if d['name']==old))
    inherited={d['name']:d for d in doc['declarations']}
    for d in renamed([d for d in source_excerpt()['declarations'] if d['name'] in REUSED_DEFINITIONS],m):
        require(inherited.get(d['name'])==d,'Inherited mathematical definition differs: '+d['name'])
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown inverse-field reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown inverse-field method reference')
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
    result['statements']=renamed(doc['statements'][200:202],inverse);return normalize_document(result)



def text_boundaries():
    prior=previous.text_boundaries()['sentences']['fieldresultssentence']
    require(prior['position']==[73,3] and SENTENCES=={'inversefieldsentence':(74,1)},'Paragraph sequence changed')
    units={u['id']:u for u in author.read(author.UNITS)['units']}
    for row in SENTENCE_SEGMENTS:
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['sha256'],'Inverse-field source segment changed')
    text=' '.join(row['text'] for row in SENTENCE_SEGMENTS);tokens=text.split()
    require(len(tokens)==49 and tokens[7]=='erstens' and tokens[14]=='zweitens','Two-method sentence boundary changed')
    require(tokens[34:36]==['so','folgt,'] and tokens[45:48]==['identisch','sein','müssen:'] and tokens[-1]=='[M0311].','Necessity, consequence or display boundary changed')
    require(SPANS=={'zoe':('inversefieldsentence',1,34),'zn3':('inversefieldsentence',35,48),'eisp5':('inversefieldsentence',49,49),'inversefirstanchor':('inversefieldsentence',8,14),'inversesecondanchor':('inversefieldsentence',15,34)},'Inverse method text reference changed')
    require(tokens[24:27]==['[M0308]','auf','[M0309]),'] and tokens[31]=='[M0310]','Reverse frame or speed reference changed')
    require(units['einstein-1905:u0167']['text'].startswith('Ferner folgt aus Symmetriegründen'),'Next paragraph boundary changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph74 is one sentence: two inverse constructions, the necessity of their identity considered as reason, and coefficient product one after the colon. Text anchors identify positions; the semantic judgment covers the whole sentence.',
        sentences={'inversefieldsentence':dict(position=[74,1],text=text,tokens=tokens,source_segments=SENTENCE_SEGMENTS)},
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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Inverse field source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(165,167)}
    require(set(coverage)==expected,'Inverse field source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old field comparison review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old field comparison review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Inverse field review coverage differs')
    require(SOURCE_ORDER==[31,25],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Inverse field source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-inverse-field-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),derived_references=DERIVED_REFERENCES,reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=0,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=70,core_edition=12,new_source_assertions=2,total_source_assertions=164,total_annotations=38,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible inverse-field document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS,*DERIVED_REFERENCES)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    require(kind=='describedreference','Unknown inverse-field reference type')
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS}
    return TemporalReferences(roles,{})


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
    def methodsteps(method,context):
        methods={values[ref['arguments'][0]]:old for old,ref in DERIVED_REFERENCES.items()}
        if method in methods:
            require(context==values['ri'],'Unknown inverse-field method context')
            return values[methods[method]]
        require('methodsteps' in result,'Unknown method steps')
        return result['methodsteps'](method,context)
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation,methodsteps=methodsteps)|{kind:typed(kind) for kind in ('describedreference',)}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-field-comparison-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/field_comparison_visible_profile.py','scripts/field_comparison_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_inverse_field_visible.py','scripts/visible_inverse_field_visible_collection.py',
        'tests/test_inverse_field_visible.py','docs/einstein-inverse-field-visible-v1.md'}
    for name in ('inverse_field_claim',):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved inverse-field bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-inverse-field-visible-evidence-1',core_words=375,profile_words=879,profile_edition=70,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=164,annotations=38,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
