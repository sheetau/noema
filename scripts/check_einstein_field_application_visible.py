"""Connect the final transformation applied to the same electromagnetic process."""
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
from scripts import field_application_visible_profile as profile
from scripts.field_application_visible_profile import ROOT,FieldApplicationVisibleVocabulary,write_once
from scripts import check_einstein_vacuum_assumption_visible as previous
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

SOURCE='examples/v016/einstein-field-application-visible-v1.noema'
BRIDGE='data/einstein-field-application-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-field-application-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[22]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg',
  'sha256': '82cc01197ef77b18fa71b3cd625580cbce8171a78af66be70df05a20311443e5',
  'actually_displayed': True,
  'independent_human_reading': False,
  'observations': ['前のwobeiのベクトル説明を閉じた後、新段落Wenden wirから第三節の変換の適用を述べる。',
                   '導入はコロンで終わり、その下の四式がページ下端まで続く。これだけで一文を閉じない。',
                   '電気側の混合成分はX、β(Y−vN/V)、β(Z+vM/V)、磁気側はL、β(M+vZ/V)、β(N−vY/V)。']},
 {'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p908-0.jpg',
  'sha256': '511201da1a9dca7175cdbf604c522c5339de25b98b954060e169aee35111f4ac',
  'actually_displayed': True,
  'independent_human_reading': False,
  'observations': ['ページ先頭の二式が907頁の四式を継続し、六式の表示群を成す。',
                   '直後の小文字wobeiとβ=1/√(1−(v/V)²)が同じ一文の補足で、式の後の終止点で閉じる。',
                   'Das Relativitätsprinzipから新段落が始まる。移動系での物理場の定義や次の比較推論は今回へ含めない。']}]
PUBLIC_RELATIONS={'eisc3': 'electromagneticprocessdescription',
 'eispn': 'processfielddescription',
 'eispo': 'processeventmembership'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['s6d',
 's6e',
 's6f',
 's6g',
 's6h',
 's6i',
 's6j',
 's6k',
 's6l',
 's6m',
 's6n',
 's6o',
 'eig3',
 'ejte',
 'ejtf',
 'ejtg',
 'ejth',
 'ejti',
 'ejtj',
 'ejtk',
 'ejtl',
 'ejtm',
 'ejtn',
 'ejto',
 'ejtp']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'fieldapplicationsentence': (71, 1)}
TEXT_SENTENCES={'fieldapplicationsentence': (71, 1)}
TOKEN_COUNTS={'fieldapplicationsentence': 37}
SENTENCE_SEGMENTS=[{'unit': 'einstein-1905:u0156',
  'text': 'Wenden wir auf diese Gleichungen die in § 3 entwickelte Transformation an, indem wir die '
          'elektromagnetischen Vorgänge auf das dort eingeführte, mit der Geschwindigkeit [M0290] bewegte '
          'Koordinatensystem beziehen, so erhalten wir die Gleichungen:',
  'sha256': '440c63fc0b096ef3ebcb5b9a6055d05e1b8a9df7142d9b04dba9174516f3a40b'},
 {'unit': 'einstein-1905:u0157',
  'text': '[M0291]',
  'sha256': 'f1d88f38554845e7186284de8c626bb90b9d9f5fe23961d1e60cd86bec20f233'},
 {'unit': 'einstein-1905:u0158',
  'text': '[M0292]',
  'sha256': '56d2faa64087d7269f30a3b280882e7131db2c47bb332edc29b58b7e8fc587d7'},
 {'unit': 'einstein-1905:u0159',
  'text': 'wobei',
  'sha256': 'ad6f70890a12d8f25cf83a9ebb72fac6316cf86f4e2e27c3ef03027f2b994c84'},
 {'unit': 'einstein-1905:u0160',
  'text': '[M0293]',
  'sha256': 'b23620df14b7e10f5eaa5bf9d8905769928a25ad4cc321ab306cef8fd2467acf'}]
EXPECTED_TOKENS=['Wenden',
 'wir',
 'auf',
 'diese',
 'Gleichungen',
 'die',
 'in',
 '§',
 '3',
 'entwickelte',
 'Transformation',
 'an,',
 'indem',
 'wir',
 'die',
 'elektromagnetischen',
 'Vorgänge',
 'auf',
 'das',
 'dort',
 'eingeführte,',
 'mit',
 'der',
 'Geschwindigkeit',
 '[M0290]',
 'bewegte',
 'Koordinatensystem',
 'beziehen,',
 'so',
 'erhalten',
 'wir',
 'die',
 'Gleichungen:',
 '[M0291]',
 '[M0292]',
 'wobei',
 '[M0293]']
SPANS={'znq': ('fieldapplicationsentence', 1, 33),
 'eispq': ('fieldapplicationsentence', 34, 35),
 'eispr': ('fieldapplicationsentence', 36, 37)}
MULTI_SPANS={}
DESIGNATIONS={}
FORMS={}
ROLE_ASSIGNMENTS={'eispp': 'fieldprocessrole'}
REFERENCE_SORTS={'eispp': 'individual'}
REFERENCE_ANCHORS={'eispp': 'znq'}
ROLE_DEFINITIONS={'eispp': {'kind': 'definition',
           'name': 'fieldprocessrole',
           'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
           'result': 'truth',
           'body': {'kind': 'call',
                    'symbol': 'ejte',
                    'arguments': [{'kind': 'variable', 'name': 'va'}, {'kind': 'variable', 'name': 'vb'}]}}}
LOCAL_NAMES=['s6d',
 's6e',
 's6f',
 's6g',
 's6h',
 's6i',
 's6j',
 's6k',
 's6l',
 's6m',
 's6n',
 's6o',
 'eig3',
 'ejte',
 'ejtf',
 'ejtg',
 'ejth',
 'ejti',
 'ejtj',
 'ejtk',
 'ejtl',
 'ejtm',
 'ejtn',
 'ejto',
 'ejtp',
 'znq',
 'eispp',
 'eispq',
 'eispr',
 'fieldapplicationsentence',
 'fieldprocessrole']
READINGS=('data/einstein-field-transformation-application-source-reading-v1.json',)
REVIEWS=('data/einstein-field-transformation-application-u0156-review-v1.json',
 'data/einstein-field-transformation-application-u0157-review-v1.json',
 'data/einstein-field-transformation-application-u0158-review-v1.json',
 'data/einstein-field-transformation-application-u0159-review-v1.json',
 'data/einstein-field-transformation-application-u0160-review-v1.json')
SEMANTIC_REVIEW=['対象はu0156–160の一文。変換後の混合成分をu0161以降の移動系における独立した物理場の定義へ先取りしない。',
 '同じ過程の全所属出来事を対象とし、成功例だけへ狭めず、別の出来事の片側記録を合わせない。',
 '既出zb6、K/k、v、Vと直前の仮定ejs6、第三節の最終四式ejehを保持し、途中のφ付き変換へ戻さない。',
 '成分の混合と座標引数の逆写像を区別し、速度−vを両場と領域へ共通に用いる。全四成分と正のVの定義域を保つ。',
 'βは同じV,vによる正の根。改頁や式の配置を追加の法則として扱わない。',
 '六回転式だけでは変換後の六式を一般に導けないという既存反例を保持する。発散条件や全微分の仮定を黙って補わない。',
 '型付き記述の参照・著者帰属は内容を実行せず、全実数・全関数域を有限例で証明したとは扱わない。']
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
        chain=FieldApplicationVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return FieldApplicationVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==382,'Field-application source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','inside',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown field-application reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown field-application reference')
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
    result['statements']=renamed(doc['statements'][195:196],inverse);return normalize_document(result)



def text_boundaries():
    prior=previous.text_boundaries()['sentences']['sixthopeningsentence']
    require(prior['position']==[70,1] and SENTENCES=={'fieldapplicationsentence':(71,1)},'Paragraph sequence changed')
    inventory=author.read(author.UNITS)['units'];units={u['id']:u for u in inventory}
    for row in SENTENCE_SEGMENTS:
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['sha256'],'Application sentence segment changed')
    text=' '.join(r['text'] for r in SENTENCE_SEGMENTS);tokens=text.split()
    require(tokens==EXPECTED_TOKENS and len(tokens)==37,'Application sentence tokens changed')
    require(SPANS=={'znq':('fieldapplicationsentence',1,33),'eispq':('fieldapplicationsentence',34,35),'eispr':('fieldapplicationsentence',36,37)},'Application clause boundary changed')
    require(tokens[32:] == ['Gleichungen:','[M0291]','[M0292]','wobei','[M0293]'],'Display/beta continuation changed')
    require(units['einstein-1905:u0155']['text'].endswith('bedeutet.') and units['einstein-1905:u0161']['text'].startswith('Das Relativitätsprinzip'),'Adjacent sentence boundary changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph71 sentence1 covers the application, the six displayed equations across pages907/908, and the lower-case wobei beta supplement. The subsequent moving-field statement is separate.',
        sentences={'fieldapplicationsentence':dict(position=[71,1],tokens=tokens,text=text,segments=SENTENCE_SEGMENTS)},
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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Field application source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(156,161)}
    require(set(coverage)==expected,'Field application source selection differs')
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
    require(reviewed==expected,'Field application review coverage differs')
    require(SOURCE_ORDER==[22],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Field application source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-field-application-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=3,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=68,core_edition=12,new_source_assertions=1,total_source_assertions=160,total_annotations=36,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible field-application document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    require(kind=='describedreference','Unknown field-application reference type')
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
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference',)}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-vacuum-assumption-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/field_application_visible_profile.py','scripts/field_application_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_field_application_visible.py','scripts/visible_field_application_visible_collection.py',
        'tests/test_field_application_visible.py','docs/einstein-field-application-visible-v1.md'}
    for name in ('field_transformation_application',):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved field-application bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-field-application-visible-evidence-1',core_words=375,profile_words=875,profile_edition=68,
        new_public_relations=3,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=160,annotations=36,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
