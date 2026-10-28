"""Connect symmetry, the attached probe example and the claimed final field equations."""
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
from scripts import field_symmetry_visible_profile as profile
from scripts.field_symmetry_visible_profile import ROOT,FieldSymmetryVisibleVocabulary,write_once
from scripts import check_einstein_inverse_field_visible as previous
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

SOURCE='examples/v016/einstein-field-symmetry-visible-v1.noema'
BRIDGE='data/einstein-field-symmetry-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-field-symmetry-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[26, 27, 28, 29, 30]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
  'sha256': '68b45874f2d701b5270ff8c1a1ae9b3658c54058748eb483a53663368b6df049',
  'actually_displayed': True,
  'independent_human_reading': False,
  'inspection': 'current goal turn, view_image before tool chunk415f64',
  'observations': ['Fernerから最終六式まで、偶性表示の後はセミコロン、値1表示の後はコンマ、最終六式へコロンで続く一文。',
                   '脚注1はSymmetriegründenの直後に付く。同頁下部に仮定例と符号・大きさの比較。',
                   '次のZur Interpretationから別段落。脚注のz. B.を文の終端にしない。']}]
PUBLIC_RELATIONS={}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['sao2',
 'sar2',
 'sat2',
 'sau2',
 'sba2',
 'sbb2',
 'sbc2',
 'sbd2',
 'sbe2',
 'sbf2',
 'ejvf',
 'ejvg',
 'ejvh',
 'ejvi',
 'ejvj',
 'ejvk',
 'ejvl',
 'ejvm',
 'ejvn',
 'ejvo',
 'ejvp',
 'ejvq',
 'ejvr',
 'ejvs',
 'ejvt',
 'ejvu',
 'ejvv',
 'ejvw',
 'ejvx',
 'ejvy',
 'ejvz',
 'ejwa']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'fieldsymmetrysentence': (75, 1)}
TEXT_SENTENCES={'fieldsymmetrysentence': (75, 1)}
TOKEN_COUNTS={'fieldsymmetrysentence': 17}
SENTENCE_SEGMENTS=[{'unit': 'einstein-1905:u0167',
  'text': 'Ferner folgt aus Symmetriegründen',
  'sha256': '00a0346ddce28cd4d7abae73377c7d51a5ef32a9ce870644ce7dd5a4db49babb'},
 {'unit': 'einstein-1905:u0168',
  'text': '[M0312];',
  'sha256': 'b4dc20d77852eacbcd2b182c0fe74bdc252e53dff5213ddda77b25bb268b1945'},
 {'unit': 'einstein-1905:u0169',
  'text': 'es ist also',
  'sha256': '9696376709603a27d2efdcda785ba4fb3ae02df86046b4ea6cbb6bb08222b2d2'},
 {'unit': 'einstein-1905:u0170',
  'text': '[M0313],',
  'sha256': '99282275d6c8f5dfb0feaff11a021d797369651cec3e757a04e3109f566fb146'},
 {'unit': 'einstein-1905:u0171',
  'text': 'und unsere Gleichungen nehmen die Form an:',
  'sha256': '4e6f1cbaca1652fbfda2ef0be4ae271da49a7ce6dd8a7fabd19429ca05b051ad'},
 {'unit': 'einstein-1905:u0172',
  'text': '[M0314]',
  'sha256': 'd06dbb7cb339b10448d8eb449b989426dc32df7e138101181fa53cb1a2c141cf'}]
SPANS={'zn4': ('fieldsymmetrysentence', 1, 4),
 'eisp6': ('fieldsymmetrysentence', 5, 5),
 'zn5': ('fieldsymmetrysentence', 6, 8),
 'eisp7': ('fieldsymmetrysentence', 9, 9),
 'zn6': ('fieldsymmetrysentence', 10, 16),
 'eisqa': ('fieldsymmetrysentence', 17, 17)}
MULTI_SPANS={}
DESIGNATIONS={}
FORMS={}
FOOTNOTE={'reference': 'zoa',
 'attachment': 'fieldsymmetryattachment',
 'sentence': 'fieldsymmetrysentence',
 'printed_number': 1,
 'occurrence': 1,
 'after_token': 4,
 'after': 'Symmetriegründen',
 'unit': 'einstein-1905:u0282',
 'text': 'Ist z. B. [M0443] und [M0444], so ist aus Symmetriegründen klar, daß bei Zeichenwechsel von '
         '[M0445] ohne Änderung des numerischen Wertes auch [M0446] sein Vorzeichen ändern muß, ohne seinen '
         'numerischen Wert zu ändern.',
 'sha256': '42215d4873a1b4421d188f7226f5251597d1ca2202db4e89e22d92472c726dad',
 'tokens': ['Ist',
            'z.',
            'B.',
            '[M0443]',
            'und',
            '[M0444],',
            'so',
            'ist',
            'aus',
            'Symmetriegründen',
            'klar,',
            'daß',
            'bei',
            'Zeichenwechsel',
            'von',
            '[M0445]',
            'ohne',
            'Änderung',
            'des',
            'numerischen',
            'Wertes',
            'auch',
            '[M0446]',
            'sein',
            'Vorzeichen',
            'ändern',
            'muß,',
            'ohne',
            'seinen',
            'numerischen',
            'Wert',
            'zu',
            'ändern.'],
 'original_page': '909',
 'inventory_page_at_end': '921',
 'html_reference': 'A0023/cite_ref-4',
 'html_target': 'cite_note-4'}
ROLE_ASSIGNMENTS={'zn7': 'symmetryproberole'}
REFERENCE_SORTS={'zn7': {'kind': 'function',
         'parameters': ['individual'],
         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}}
REFERENCE_ANCHORS={'zn7': 'zoa'}
ROLE_DEFINITIONS={'zn7': {'kind': 'definition',
         'name': 'symmetryproberole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': ['individual'],
                                  'result': {'kind': 'function',
                                             'parameters': ['number'],
                                             'result': 'truth'}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'and',
                  'arguments': [{'kind': 'call',
                                 'symbol': 'shn',
                                 'arguments': [{'kind': 'call', 'symbol': 'shx', 'arguments': []},
                                               {'kind': 'variable', 'name': 'va'},
                                               {'kind': 'function_ref', 'symbol': 'ba'}]},
                                {'kind': 'apply',
                                 'function': {'kind': 'call', 'symbol': 'znk', 'arguments': []},
                                 'arguments': [{'kind': 'apply',
                                                'function': {'kind': 'variable', 'name': 'va'},
                                                'arguments': [{'kind': 'call',
                                                               'symbol': 'yn',
                                                               'arguments': []}]},
                                               {'kind': 'apply',
                                                'function': {'kind': 'variable', 'name': 'va'},
                                                'arguments': [{'kind': 'call',
                                                               'symbol': 'yo',
                                                               'arguments': []}]},
                                               {'kind': 'apply',
                                                'function': {'kind': 'variable', 'name': 'va'},
                                                'arguments': [{'kind': 'call',
                                                               'symbol': 'yp',
                                                               'arguments': []}]},
                                               {'kind': 'apply',
                                                'function': {'kind': 'variable', 'name': 'va'},
                                                'arguments': [{'kind': 'call',
                                                               'symbol': 'zc7',
                                                               'arguments': []}]}]}]}}}
LOCAL_NAMES=['sao2',
 'sar2',
 'sat2',
 'sau2',
 'sba2',
 'sbb2',
 'sbc2',
 'sbd2',
 'sbe2',
 'sbf2',
 'ejvf',
 'ejvg',
 'ejvh',
 'ejvi',
 'ejvj',
 'ejvk',
 'ejvl',
 'ejvm',
 'ejvn',
 'ejvo',
 'ejvp',
 'ejvq',
 'ejvr',
 'ejvs',
 'ejvt',
 'ejvu',
 'ejvv',
 'ejvw',
 'ejvx',
 'ejvy',
 'ejvz',
 'ejwa',
 'fieldsymmetrysentence',
 'zn4',
 'eisp6',
 'zn5',
 'eisp7',
 'zn6',
 'eisqa',
 'fieldsymmetryattachment',
 'zoa',
 'zn7',
 'symmetryproberole']
READINGS=('data/einstein-field-symmetry-conclusion-source-reading-v1.json',)
REVIEWS=('data/einstein-field-symmetry-conclusion-u0167-review-v1.json',
 'data/einstein-field-symmetry-conclusion-u0168-review-v1.json',
 'data/einstein-field-symmetry-conclusion-u0169-review-v1.json',
 'data/einstein-field-symmetry-conclusion-u0170-review-v1.json',
 'data/einstein-field-symmetry-conclusion-u0171-review-v1.json',
 'data/einstein-field-symmetry-conclusion-u0172-review-v1.json',
 'data/einstein-field-symmetry-conclusion-u0282-review-v1.json')
SEMANTIC_REVIEW=['原刊909頁のu0167–u0172を、さらに対称性から偶性が従い、したがって係数は1となり、われわれの式は最終六式となる、という連続した一文群として読む。著者脚注u0282と番号1)の参照も同じ意味依存群へ接続する。',
 '脚注は同じ旧系の同じ領域の一点で五成分が零、Nが非零という仮定例。場全体を定数場に限定せず、同じNとV・尺度・旧系の出来事を保持して速度の符号だけを変える。Y′は対応する新系の出来事で評価され、別の速度でも同じ数値の新座標だとはしない。',
 'numerischer '
 'Wertを符号から独立な大きさと読む。速度もY′も大きさを保って符号を反転する。非自明な反転例はv≠0であり、v=0では偶性は同じ引数の恒等である。零のY′同士を厳密な符号反転の証拠にはしない。',
 '脚注の必要性は、直前の六式・積1を背景にする非空の仮定状況全てで応答を要求する読み。候補選択へ応答の成功や偶性を混ぜない。対称性と明白さは著者の理由と評価として別に帰属させ、物理的な実験や定理の証明としない。',
 '積1と偶性だけでは係数-1も残る。本文が値1を結論する提示を記述し、正値・連続性・向きの規約を原文の前提へ無断で補わない。負の枝の反例を保持する。最終六式は著者が採った値1に従って構成する。',
 '原刊909頁のφは直前908頁のψと同じ第六節の係数znz。第三節の座標係数とは区別する。固定原文・MathML・原刊画像を変更しない。脚注の在庫のpage_at_end=921は集めた注の配置であり、原刊の実際の掲載頁は909。',
 '既存の数値・場・内容・必要性・著者帰属・理由・例示・脚注参照の関係を合成し、新しい基本関係を追加しない。有限対照、保存した記号的検証、原文の通読判断を区別し、全実数・全関数域の有限列挙拒否を保持する。',
 '四座標役割それぞれに有効な実数値を与え、同じ旧系の真空領域znk内にある点を役割とする。',
 '点の役割に五成分の零、N非零、速度非零、応答成功、係数の偶性・正値・値1を入れない。仮定例の条件は本文sbe2、応答はsbf2へ残す。',
 '既存の型別参照と同じ意味規約でindividual→CUT型を公開する。役割は引用し取得時非実行、存在唯一性は保証せず、未知入力は拒否する。',
 '現在の五つの原文主張を原文順26–30で追加する。本文の一文と脚注の付された位置・例示の方向を保持し、脚注を本文の時間順序へ挿入しない。',
 '固定アルファベットと共通375語を保持する。任意profile71の880語は、既存の型別参照と同じ規約のindividual→CUT取得を一つだけ追加する。']
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
        chain=FieldSymmetryVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return FieldSymmetryVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==159,'Field-symmetry source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)|{FOOTNOTE["attachment"],FOOTNOTE["reference"]}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','round',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.ALL_CONTRACTS))
    add(FOOTNOTE['attachment'],call(voc._symbols['footnoteattachmentreference'],k('eirf'),k(FOOTNOTE['sentence']),author.num(FOOTNOTE['printed_number']),author.num(FOOTNOTE['occurrence']),k('ri')))
    add(FOOTNOTE['reference'],call(voc._symbols['footnotereference'],k('eirf'),k(FOOTNOTE['attachment']),author.num(FOOTNOTE['printed_number']),k('ri')))
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
    require(old in ROLE_ASSIGNMENTS,'Unknown field-symmetry reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown field-symmetry point reference')
    return 'describedindividualcutfunctionreference'


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
    result['statements']=renamed(doc['statements'][202:207],inverse);return normalize_document(result)



def text_boundaries():
    prior=previous.text_boundaries()['sentences']['inversefieldsentence']
    require(prior['position']==[74,1] and SENTENCES=={'fieldsymmetrysentence':(75,1)},'Paragraph sequence changed')
    units={u['id']:u for u in author.read(author.UNITS)['units']}
    for row in SENTENCE_SEGMENTS:
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['sha256'],'Field-symmetry source segment changed')
    text=' '.join(row['text'] for row in SENTENCE_SEGMENTS);tokens=text.split()
    require(tokens==['Ferner','folgt','aus','Symmetriegründen','[M0312];','es','ist','also','[M0313],','und','unsere','Gleichungen','nehmen','die','Form','an:','[M0314]'],'Symmetry sentence boundary changed')
    require(SPANS=={'zn4':('fieldsymmetrysentence',1,4),'eisp6':('fieldsymmetrysentence',5,5),'zn5':('fieldsymmetrysentence',6,8),'eisp7':('fieldsymmetrysentence',9,9),'zn6':('fieldsymmetrysentence',10,16),'eisqa':('fieldsymmetrysentence',17,17)},'Symmetry clause or display reference changed')
    note=units[FOOTNOTE['unit']]
    require(note['text']==FOOTNOTE['text'] and note['text_sha256']==FOOTNOTE['sha256'] and note['text'].split()==FOOTNOTE['tokens'],'Attached footnote text changed')
    require(len(FOOTNOTE['tokens'])==33 and FOOTNOTE['tokens'][1:3]==['z.','B.'],'Footnote abbreviation split as a sentence')
    require(FOOTNOTE['after_token']==4 and tokens[3]==FOOTNOTE['after'] and FOOTNOTE['printed_number']==FOOTNOTE['occurrence']==1,'Footnote attachment changed')
    require(units['einstein-1905:u0173']['text'].startswith('Zur Interpretation'),'Next paragraph boundary changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph75 is one sentence: symmetry, evenness, the claimed unit coefficient and the final six equations. Author footnote1 is attached after Symmetriegründen, not inserted into the narrative sequence.',
        sentences={'fieldsymmetrysentence':dict(position=[75,1],text=text,tokens=tokens,source_segments=SENTENCE_SEGMENTS)},
        spans={n:list(p) for n,p in SPANS.items()},footnote=FOOTNOTE,multi_sentence_spans={},designations={},designation_forms={})



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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Field symmetry source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in (167,168,169,170,171,172,282)}
    require(set(coverage)==expected,'Field symmetry source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old field symmetry review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old field symmetry review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Field symmetry review coverage differs')
    require(SOURCE_ORDER==[26,27,28,29,30],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Field symmetry source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-field-symmetry-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),footnote=FOOTNOTE,reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=0,new_reference_primitives=1,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=71,core_edition=12,new_source_assertions=5,total_source_assertions=169,total_annotations=38,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible field-symmetry document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS,FOOTNOTE["attachment"],FOOTNOTE["reference"])}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedindividualcutfunctionreference'):
    require(kind=='describedindividualcutfunctionreference','Unknown field-symmetry reference type')
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS}
    return profile.IndividualCutFunctionReferences(roles)


def footnote_models(values):
    note=TemporalReferences({},{(values['eirf'],values[FOOTNOTE['attachment']],FOOTNOTE['printed_number'],values['ri']):values[FOOTNOTE['reference']]})
    attachment=MovingTextReferences({},{(values['eirf'],values[FOOTNOTE['sentence']],FOOTNOTE['printed_number'],FOOTNOTE['occurrence'],values['ri']):values[FOOTNOTE['attachment']]})
    return note,attachment


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
    def attachment(document,node,number,occurrence,context):
        if node==values[FOOTNOTE['sentence']]:return footnote_models(values)[1].attachment(document,node,number,occurrence,context)
        return result['footnoteattachmentreference'](document,node,number,occurrence,context)
    def note(document,node,number,context):
        if node==values[FOOTNOTE['attachment']]:return footnote_models(values)[0].footnote(document,node,number,context)
        return result['footnotereference'](document,node,number,context)
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation,footnoteattachmentreference=attachment,footnotereference=note)|{kind:typed(kind) for kind in ('describedindividualcutfunctionreference',)}



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-inverse-field-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/field_symmetry_visible_profile.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_field_symmetry_visible.py','scripts/visible_field_symmetry_visible_collection.py',
        'tests/test_field_symmetry_visible.py','docs/einstein-field-symmetry-visible-v1.md'}
    for name in ('field_symmetry_conclusion',):
        from importlib import import_module
        from noema.meaning_catalog import load_catalog
        module=import_module('scripts.check_'+name)
        paths.update(('scripts/check_'+name+'.py','scripts/compose_'+name+'.py',module.CORE,module.BASIS,module.DOC))
        paths.update(load_catalog(ROOT,module.BASIS).source_sha256)
        paths.update(getattr(module,'DEPENDENCIES',()));paths.update(getattr(module,'PRIORS',()))
    parity=author.read('reports/field-parity-v1.json')
    for path,stamp in parity['source_sha256'].items():require(author.digest(path)==stamp,'Prior parity evidence changed: '+path)
    paths.update(parity['source_sha256'])
    paths.update(annotations()['source_sha256'])
    paths.update(row['path'] for row in SOURCE_VISUAL_REVIEW)
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved field-symmetry bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-field-symmetry-visible-evidence-1',core_words=375,profile_words=880,profile_edition=71,
        new_public_relations=0,new_reference_primitives=1,new_source_assertions=5,total_source_assertions=169,annotations=38,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
