"""Connect the third frame, alternative derivation and parallel transformation group."""
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
from scripts import velocity_axial_visible_profile as profile
from scripts.velocity_axial_visible_profile import ROOT,VelocityAxialVisibleVocabulary,write_once
from scripts import check_einstein_velocity_bound_light_visible as previous
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

SOURCE='examples/v016/einstein-velocity-parallel-visible-v1.noema'
BRIDGE='data/einstein-velocity-parallel-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-velocity-parallel-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[14, 15, 16, 17, 18]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg',
  'sha256': 'fda62af14de6978b5938e09fa98e63bbf2b29010c1b4250a4b7f41e62bc57591',
  'actually_displayed': True,
  'tool_chunk': 'df68eb',
  'independent_human_reading': False},
 {'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg',
  'sha256': '82cc01197ef77b18fa71b3cd625580cbce8171a78af66be70df05a20311443e5',
  'actually_displayed': True,
  'tool_chunk': 'f58e24',
  'independent_human_reading': False,
  'observations': ['Page begins with tritt; followed by the group claim and the parenthetical wie dies sein '
                   'muß.',
                   'No paragraph break before the group claim; the next paragraph begins Wir haben nun.']}]
PUBLIC_RELATIONS={}
NEW_DEFINITIONS=['s4l',
 's4m',
 's4y',
 's4z',
 's42',
 's43',
 's44',
 's45',
 's46',
 's47',
 's5a',
 's5b',
 's5c',
 's5d',
 's5e',
 's5f',
 's5g',
 's5h',
 's5i',
 'ejpr',
 'ejqv',
 'ejqw',
 'ejqx',
 'ejqy',
 'ejqz',
 'ejq2',
 'ejq3',
 'ejq4',
 'ejq5',
 'ejq6',
 'ejq7',
 'ejra',
 'ejrb',
 'ejrc',
 'ejrd',
 'ejre',
 'ejrf',
 'ejrg',
 'ejrh',
 'ejri',
 'ejrj',
 'ejrk',
 'ejrl',
 'ejrm',
 'ejrn',
 'ejro',
 'ejrp',
 'ejrq',
 'ejrr',
 'ejrs',
 'ejrt',
 'ejru',
 'ejrv',
 'ejrw',
 'ejrx',
 'ejry']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'zm2': (68, 1), 'parallelstatement': (68, 2)}
TOKEN_COUNTS={'zm2': 26, 'parallelstatement': 83}
SPANS={'zlr': ('parallelstatement', 1, 34),
 'zls': ('parallelstatement', 35, 68),
 'zlu': ('parallelstatement', 69, 83),
 'zm3': ('parallelstatement', 76, 79),
 'parallelframeanchor': ('parallelstatement', 22, 22),
 'parallelspeedanchor': ('parallelstatement', 33, 33)}
MULTI_SPANS={}
DESIGNATIONS={'eispa': ('parallelstatement', 1)}
FORMS={'eispa': 'k′'}
ROLE_ASSIGNMENTS={'zlo': 'parallelframerole',
 'zlt': 'parallelspeedrole',
 'zlv': 'parallelpreviousmethodrole',
 'zly': 'parallelpaststagerole'}
REFERENCE_SORTS={'zlo': 'individual',
 'zlt': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
 'zlv': 'individual',
 'zly': 'situation'}
REFERENCE_ANCHORS={'zlo': 'parallelframeanchor', 'zlt': 'parallelspeedanchor', 'zlv': 'zm2', 'zly': 'zm2'}
ROLE_DEFINITIONS={'zlo': {'kind': 'definition',
         'name': 'parallelframerole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'va',
                                 'arguments': [{'kind': 'variable', 'name': 'va'}]},
                                {'kind': 'and',
                                 'arguments': [{'kind': 'not',
                                                'arguments': [{'kind': 'equal',
                                                               'arguments': [{'kind': 'variable',
                                                                              'name': 'va'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'ra',
                                                                              'arguments': []}]}]},
                                               {'kind': 'and',
                                                'arguments': [{'kind': 'not',
                                                               'arguments': [{'kind': 'equal',
                                                                              'arguments': [{'kind': 'variable',
                                                                                             'name': 'va'},
                                                                                            {'kind': 'call',
                                                                                             'symbol': 'zbm',
                                                                                             'arguments': []}]}]},
                                                              {'kind': 'call',
                                                               'symbol': 'eisd3',
                                                               'arguments': [{'kind': 'call',
                                                                              'symbol': 'zlr',
                                                                              'arguments': []},
                                                                             {'kind': 'variable',
                                                                              'name': 'va'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'eirf',
                                                                              'arguments': []},
                                                                             {'kind': 'variable',
                                                                              'name': 'vb'}]}]}]}]}},
 'zlt': {'kind': 'definition',
         'name': 'parallelspeedrole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'eja2',
                                 'arguments': [{'kind': 'call', 'symbol': 'zbm', 'arguments': []},
                                               {'kind': 'call', 'symbol': 'zlo', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'call', 'symbol': 'zb6', 'arguments': []}]},
                                {'kind': 'call',
                                 'symbol': 's45',
                                 'arguments': [{'kind': 'call', 'symbol': 'tc', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'}]}]}},
 'zlv': {'kind': 'definition',
         'name': 'parallelpreviousmethodrole',
         'parameters': [{'name': 'va', 'sort': 'individual'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 's2w',
                                 'arguments': [{'kind': 'call',
                                                'symbol': 'zlx',
                                                'arguments': [{'kind': 'variable', 'name': 'va'},
                                                              {'kind': 'call',
                                                               'symbol': 'zly',
                                                               'arguments': []}]},
                                               {'kind': 'quote',
                                                'body': {'kind': 'call', 'symbol': 'ejpb', 'arguments': []}},
                                               {'kind': 'quote',
                                                'body': {'kind': 'call', 'symbol': 'ejpr', 'arguments': []}},
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
                                                                       {'kind': 'call',
                                                                        'symbol': 'zly',
                                                                        'arguments': []}]}}]},
                                {'kind': 'and',
                                 'arguments': [{'kind': 'call',
                                                'symbol': 's5h',
                                                'arguments': [{'kind': 'call',
                                                               'symbol': 'zlx',
                                                               'arguments': [{'kind': 'variable',
                                                                              'name': 'va'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'zly',
                                                                              'arguments': []}]},
                                                              {'kind': 'quote',
                                                               'body': {'kind': 'call',
                                                                        'symbol': 'ejpb',
                                                                        'arguments': []}},
                                                              {'kind': 'quote',
                                                               'body': {'kind': 'call',
                                                                        'symbol': 'ejpc',
                                                                        'arguments': []}}]},
                                               {'kind': 'call',
                                                'symbol': 's5h',
                                                'arguments': [{'kind': 'call',
                                                               'symbol': 'zlx',
                                                               'arguments': [{'kind': 'variable',
                                                                              'name': 'va'},
                                                                             {'kind': 'call',
                                                                              'symbol': 'zly',
                                                                              'arguments': []}]},
                                                              {'kind': 'quote',
                                                               'body': {'kind': 'call',
                                                                        'symbol': 'ejpc',
                                                                        'arguments': []}},
                                                              {'kind': 'quote',
                                                               'body': {'kind': 'call',
                                                                        'symbol': 'ejpr',
                                                                        'arguments': []}}]}]}]}},
 'zly': {'kind': 'definition',
         'name': 'parallelpaststagerole',
         'parameters': [{'name': 'va', 'sort': 'situation'}, {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'call',
                  'symbol': 'zm4',
                  'arguments': [{'kind': 'variable', 'name': 'va'}, {'kind': 'variable', 'name': 'vb'}]}}}
LOCAL_NAMES=['s4l',
 's4m',
 'zlo',
 'zlr',
 'zls',
 'zlt',
 's4y',
 's4z',
 's42',
 's43',
 's44',
 's45',
 's46',
 's47',
 's5a',
 's5b',
 's5c',
 's5d',
 's5e',
 's5f',
 's5g',
 'zlu',
 's5h',
 's5i',
 'zlv',
 'zly',
 'zm2',
 'zm3',
 'ejpr',
 'ejqv',
 'ejqw',
 'ejqx',
 'ejqy',
 'ejqz',
 'ejq2',
 'ejq3',
 'ejq4',
 'ejq5',
 'ejq6',
 'ejq7',
 'ejra',
 'ejrb',
 'ejrc',
 'ejrd',
 'ejre',
 'ejrf',
 'ejrg',
 'ejrh',
 'ejri',
 'eispa',
 'ejrj',
 'ejrk',
 'ejrl',
 'ejrm',
 'ejrn',
 'ejro',
 'ejrp',
 'ejrq',
 'ejrr',
 'ejrs',
 'ejrt',
 'ejru',
 'ejrv',
 'ejrw',
 'ejrx',
 'ejry',
 'parallelstatement',
 'parallelframeanchor',
 'parallelspeedanchor',
 'parallelframerole',
 'parallelspeedrole',
 'parallelpreviousmethodrole',
 'parallelpaststagerole']
READINGS=('data/einstein-parallel-group-source-reading-v1.json',)
REVIEWS=('data/einstein-parallel-group-u0147-review-v1.json',
 'data/einstein-parallel-group-u0148-review-v1.json',
 'data/einstein-parallel-group-u0149-review-v1.json')
SEMANTIC_REVIEW=['第三系k′と§3の逆変換用K′を同一化しない。新呼称の参照と対象の命名関係を別々に維持する。',
 'zltは同じkに対する第三系の符号付き相対速度。点の速さzkqとの同値はejrc内だけに置く。',
 '群の速度域は−V<v<V、負と零を含む。点の正方向条件を群に流用しない。',
 '同形式の四変換とβの引数に同じ合成速度を使用し、全四入力・全記録を省かない。',
 '既出方法の役割は同じ段階のejpb→ejpc→ejprの手順を指定する。本文箇所と方法の実行を同一化しない。',
 '過去段階の役割は文脈より前という関係で参照し、原文にない日時や実行済みの事実を追加しない。',
 '役割の引用照合では候補や内容を評価しない。役割間の依存は段階→方法、第三系→速度の順で非循環にする。',
 '必要性の候補は前提からだけ選ぶ。非空全称と、同じ群の内容への挿入句の結合を保つ。',
 '別方法の利用可能性、著者の帰結提示、証明の健全性、有限診断、全実域の証明を区別する。']
RELATIONS=previous.RELATIONS
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
LIMITS=['固定アルファベット・共通375語とprofile64の861語を再利用し、公開語を追加しない。',*SEMANTIC_REVIEW]


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
    require(len(seen)==412,'Velocity-parallel source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','book',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown velocity-parallel reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown parallel reference')
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
    result['statements']=renamed(doc['statements'][181:186],inverse);return normalize_document(result)



def text_boundaries():
    units={u['id']:u['text'] for u in author.read(author.UNITS)['units']}
    first,second=units['einstein-1905:u0147'].split(' Führen wir ',1)
    second='Führen wir '+second+' '+units['einstein-1905:u0148']+' '+units['einstein-1905:u0149']
    require(set(previous.SENTENCES.values())=={(66,1),(66,2),(67,1),(67,2)},'Previous paragraph boundary changed')
    sentences={}
    for old,value in zip(SENTENCES,(first,second),strict=True):
        tokens=value.split();require(len(tokens)==TOKEN_COUNTS[old],'Parallel sentence boundary changed')
        sentences[old]=dict(position=list(SENTENCES[old]),tokens=tokens,text=value)
    tokens=second.split()
    require(tokens[21]=='[M0279]' and tokens[32]=='[M0281]','Third frame or speed anchor changed')
    require(tokens[66:68]==['[M0285]','tritt;'] and tokens[75:79]==['wie','dies','sein','muß'],'Continuation or aside changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph68 has two sentences. The second crosses pages906/907, includes M0285 and tritt;, then the group claim and embedded necessity aside. Semicolon does not end the sentence.',
        headings={},sentences=sentences,spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},
        designations={n:list(p) for n,p in DESIGNATIONS.items()},designation_forms=FORMS)



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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Velocity parallel source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(147,150)}
    require(set(coverage)==expected,'Velocity parallel source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old velocity parallel review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old velocity parallel review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Velocity parallel review coverage differs')
    require(SOURCE_ORDER==list(range(14,19)),'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Velocity parallel source backprojection differs')
    return dict(schema='noema-einstein-velocity-parallel-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=0,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=64,core_edition=12,new_source_assertions=5,total_source_assertions=154,total_annotations=33,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible velocity-parallel document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedcutreference':return CutReferences(roles)
    if kind=='describedsettingreference':return SettingReferences(roles)
    require(kind=='describedreference','Unknown parallel reference type');return TemporalReferences(roles,{})


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
    prior_path='reports/einstein-velocity-bound-light-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_velocity_parallel_visible.py','scripts/visible_velocity_parallel_visible_collection.py',
        'tests/test_velocity_parallel_visible.py','docs/einstein-velocity-parallel-visible-v1.md'}
    for name in ('parallel_current_records','parallel_alternative_claim','parallel_group_claim'):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256);paths.update(module.DEPENDENCIES)
    paths.update(annotations()['source_sha256'])
    paths.update(row['path'] for row in SOURCE_VISUAL_REVIEW)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved velocity-parallel bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-velocity-parallel-visible-evidence-1',core_words=375,profile_words=861,profile_edition=64,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=5,total_source_assertions=154,annotations=33,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
