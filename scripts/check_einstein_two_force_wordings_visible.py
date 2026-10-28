"""Connect all six two-force-wordings sentences with explicit units, objects and references."""
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
from scripts import two_force_wordings_visible_profile as profile
from scripts.two_force_wordings_visible_profile import ROOT,TwoForceWordingsVisibleVocabulary,write_once
from scripts import check_einstein_force_interpretation_visible as previous
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

SOURCE='examples/v016/einstein-two-force-wordings-visible-v1.noema'
BRIDGE='data/einstein-two-force-wordings-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-two-force-wordings-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[36, 37]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
  'sha256': '68b45874f2d701b5270ff8c1a1ae9b3658c54058748eb483a53663368b6df049',
  'actually_displayed': True,
  'independent_human_reading': False,
  'inspection': 'current goal turn; image emitted alongside a32dfc',
  'observations': ['u0173はZur Interpretationから二つの言い表しを導入するコロンまでの六文。d. h.を文の境界にしない。',
                   '直前の最初の三式は左列X′・Y′・Z′。第一の番号付き言い表しは909頁末から始まる。']},
 {'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg',
  'sha256': 'e634a38acf3bf76e5d99086296c70a267368c684501148cc789ede1def276ea5',
  'actually_displayed': True,
  'independent_human_reading': False,
  'inspection': 'current goal turn; image emitted alongside ced5d1',
  'observations': ['第一項の続きとAlte Ausdrucksweiseの括弧書き、独立した番号2とNeue Ausdrucksweiseを確認。',
                   '二項の後にAnalogesの段落が続く。後続二項の内容は今回の六文の完了件数へ加えない。']}]
PUBLIC_RELATIONS={'eisqp': 'movingtestforceresponse',
 'eisqq': 'quotedvectorquantityterm',
 'eisqr': 'establishednewwordingcontrast',
 'eisqt': 'physicalcoordinatecorrespondence'}
REUSED_DEFINITIONS=['sexb']
NEW_DEFINITIONS=['sci2',
 'ejxj',
 'ejxk',
 'ejxl',
 'ejxm',
 'ejxy',
 'ejxz',
 'ejx2',
 'ejx3',
 'ejx4',
 'ejx5',
 'ejx6',
 'ejx7',
 'ejya',
 'ejyb',
 'ejyc',
 'ejyd',
 'ejye',
 'ejyg',
 'ejyh',
 'ejyi',
 'ejyj',
 'ejyk',
 'ejyl',
 'ejym',
 'ejyn',
 'ejyo',
 'ejyp',
 'ejyq',
 'ejyr',
 'ejys',
 'ejyt',
 'ejyu',
 'ejyv',
 'ejyw',
 'ejyx',
 'ejyz',
 'ejy2']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={}
TEXT_SENTENCES={}
SPANS={}
MULTI_SPANS={}
TOKEN_COUNTS={'zpq': 54, 'zpr': 45}
TEXT_ITEMS={'zpq': {'unit': 'einstein-1905:u0174',
         'number': 1,
         'text': '1. Ist ein punktförmiger elektrischer Einheitspol in einem elektromagnetischen Felde '
                 'bewegt, so wirkt auf ihn außer der elektrischen Kraft eine „elektromotorische Kraft“, '
                 'welche unter Vernachlässigung von mit der zweiten und höheren Potenzen von [M0318] '
                 'multiplizierten Gliedern gleich ist dem mit der Lichtgeschwindigkeit dividierten '
                 'Vektorprodukt der Bewegungsgeschwindigkeit des Einheitspoles und der magnetischen Kraft. '
                 '(Alte Ausdrucksweise.)',
         'tokens': ['1.',
                    'Ist',
                    'ein',
                    'punktförmiger',
                    'elektrischer',
                    'Einheitspol',
                    'in',
                    'einem',
                    'elektromagnetischen',
                    'Felde',
                    'bewegt,',
                    'so',
                    'wirkt',
                    'auf',
                    'ihn',
                    'außer',
                    'der',
                    'elektrischen',
                    'Kraft',
                    'eine',
                    '„elektromotorische',
                    'Kraft“,',
                    'welche',
                    'unter',
                    'Vernachlässigung',
                    'von',
                    'mit',
                    'der',
                    'zweiten',
                    'und',
                    'höheren',
                    'Potenzen',
                    'von',
                    '[M0318]',
                    'multiplizierten',
                    'Gliedern',
                    'gleich',
                    'ist',
                    'dem',
                    'mit',
                    'der',
                    'Lichtgeschwindigkeit',
                    'dividierten',
                    'Vektorprodukt',
                    'der',
                    'Bewegungsgeschwindigkeit',
                    'des',
                    'Einheitspoles',
                    'und',
                    'der',
                    'magnetischen',
                    'Kraft.',
                    '(Alte',
                    'Ausdrucksweise.)'],
         'token_count': 54,
         'parenthetical_range': [53, 54],
         'source_sha256': '9039a02f355faa3859ec3f19fedeb5caec1130d0cfd932b8a4e462250d0e69df',
         'quoted_designation_range': [21, 22]},
 'zpr': {'unit': 'einstein-1905:u0175',
         'number': 2,
         'text': '2. Ist ein punktförmiger elektrischer Einheitspol in einem elektromagnetischen Felde '
                 'bewegt, so ist die auf ihn wirkende Kraft gleich der an dem Orte des Einheitspoles '
                 'vorhandenen elektrischen Kraft, welche man durch Transformation des Feldes auf ein relativ '
                 'zum elektrischen Einheitspol ruhendes Koordinatensystem erhält. (Neue Ausdrucksweise.)',
         'tokens': ['2.',
                    'Ist',
                    'ein',
                    'punktförmiger',
                    'elektrischer',
                    'Einheitspol',
                    'in',
                    'einem',
                    'elektromagnetischen',
                    'Felde',
                    'bewegt,',
                    'so',
                    'ist',
                    'die',
                    'auf',
                    'ihn',
                    'wirkende',
                    'Kraft',
                    'gleich',
                    'der',
                    'an',
                    'dem',
                    'Orte',
                    'des',
                    'Einheitspoles',
                    'vorhandenen',
                    'elektrischen',
                    'Kraft,',
                    'welche',
                    'man',
                    'durch',
                    'Transformation',
                    'des',
                    'Feldes',
                    'auf',
                    'ein',
                    'relativ',
                    'zum',
                    'elektrischen',
                    'Einheitspol',
                    'ruhendes',
                    'Koordinatensystem',
                    'erhält.',
                    '(Neue',
                    'Ausdrucksweise.)'],
         'token_count': 45,
         'parenthetical_range': [44, 45],
         'source_sha256': '703887f8dedf53addb609cc4e07b58015d18ba5d92973f35e9bf482a8c8afaa3'}}
DESIGNATIONS={'eisqs': ('zpq', 1)}
FORMS={'eisqs': '„elektromotorische Kraft“'}
INHERITED_DESIGNATIONS={}
ROLE_ASSIGNMENTS={}
REFERENCE_SORTS={}
REFERENCE_ANCHORS={}
ROLE_DEFINITIONS={}
LOCAL_NAMES=['sci2',
 'ejxj',
 'ejxk',
 'ejxl',
 'ejxm',
 'ejxy',
 'ejxz',
 'ejx2',
 'ejx3',
 'ejx4',
 'ejx5',
 'ejx6',
 'ejx7',
 'ejya',
 'ejyb',
 'ejyc',
 'ejyd',
 'ejye',
 'ejyg',
 'ejyh',
 'ejyi',
 'ejyj',
 'ejyk',
 'ejyl',
 'ejym',
 'ejyn',
 'ejyo',
 'ejyp',
 'ejyq',
 'ejyr',
 'ejys',
 'ejyt',
 'ejyu',
 'ejyv',
 'ejyw',
 'ejyx',
 'ejyz',
 'ejy2',
 'eisqs']
READINGS=('data/einstein-electromotive-wording-source-reading-v1.json',
 'data/einstein-comoving-wording-source-reading-v1.json')
REVIEWS=('data/einstein-electromotive-wording-u0174-review-v1.json',
 'data/einstein-comoving-wording-u0175-review-v1.json')
SEMANTIC_REVIEW=['既存二項参照zpq/zprと導入eisqnを維持する。番号を文終端と誤認しない。第一項は原刊909末尾から910へ続く。本文と括弧の旧/新位置付けを項目全体として接続し、引用用語の位置を原文tokenへ結ぶ。',
 '第一項は電気力に加わる機械的寄与。同じ背景・対象・出来事・単位の速度依存応答と零速度の電気基準を分け、電位差へ読み替えない。',
 '外積の順序u×H、光速度Vによる除算、三方向、非零だが光速未満の運動を維持する。x方向へ限定しない。',
 '固定した場・地点・方向で速度を小さくする一次式と(v/V)二次以上の留保を保存する。有限速度で厳密等値、全場一様性、解析性を加えない。',
 '第二項は当該瞬間に対象へ相対静止する系。同じ対象が前後も静止することや加速度0を要求せず、加速追従系を持ち込まない。',
 '任意方向の純粋boostの代表という採用済みの読みを維持する。新地点を同一出来事の逆写像で旧場へ結び、二場と領域を同じ写像で変換する。',
 '物理的座標対応を数値写像の名前から認定しない。共動系の存在証人を速度、位置、瞬間静止、場、量記録、力記録、単位と応答へ共有する。',
 'Kでの力の成分を共動系へコピーせず、第一項と第二項を無条件な数値の厳密同義にしない。旧/新の対置は歴史的初出・禁止・優劣を含意しない。',
 '引用用語eisqsは識別表記と閉じた物理的役割を別に保持する。用語の引用を発言再現、皮肉、否定、引用の実行へ変えない。']
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
        chain=TwoForceWordingsVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return TwoForceWordingsVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references([c.document['statements'][i] for i in SOURCE_ORDER]):visit(n)
    require(len(seen)==176,'Two-force-wordings source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','above',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown two-force-wordings reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown two-force-wordings reference')
    return 'describedreference' if REFERENCE_SORTS[old]=='individual' else 'describedindividualcutfunctionreference'


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
    result['statements']=renamed(doc['statements'][213:215],inverse);return normalize_document(result)



def text_boundaries():
    units={u['id']:u for u in author.read(author.UNITS)['units']}
    require(not SENTENCES and not SPANS and not ROLE_ASSIGNMENTS,'Inherited items must not be redefined')
    for old,row in TEXT_ITEMS.items():
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['source_sha256'],'Numbered item transcription changed')
        require(row['tokens']==row['text'].split() and len(row['tokens'])==TOKEN_COUNTS[old],'Numbered item tokenization changed')
        require(row['tokens'][0]==str(row['number'])+'.','Item number changed')
        require(names()[old]==previous.names()[old],'Inherited item reference changed')
        role=previous.ROLE_DEFINITIONS[old]
        require(role['body']['symbol']=='eislk' and role['body']['arguments'][1]['symbol']=='eisqn' and role['body']['arguments'][2]['numerator']==row['number'],'Item introduction changed')
        start,end=row['parenthetical_range']
        require(' '.join(row['tokens'][start-1:end])==('(Alte Ausdrucksweise.)' if row['number']==1 else '(Neue Ausdrucksweise.)'),'Old/new parenthesis changed')
    require(TEXT_ITEMS['zpq']['tokens'][20:22]==['„elektromotorische','Kraft“,'],'Quoted term position changed')
    require(FORMS=={'eisqs':'„elektromotorische Kraft“'} and DESIGNATIONS=={'eisqs':('zpq',1)},'Quoted term identity changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Preserve the two complete numbered items introduced by the preceding colon, including their old/new parentheses. The first item crosses the original page boundary.',
        items=TEXT_ITEMS,sentences={},spans={},multi_sentence_spans={},
        designations={n:list(p) for n,p in DESIGNATIONS.items()},designation_forms=FORMS)



def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};source_units={};math={};coverage={}
    for path in READINGS:
        for row in (author.read(path),):
            unit=units[row['unit']];start,end=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Two force wordings source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in ([row['math']] if isinstance(row['math'],dict) else row['math']):
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={'einstein-1905:u0174','einstein-1905:u0175'}
    require(set(coverage)==expected,'Two force wordings source selection differs')
    for uid in sorted(expected):
        unit=units[uid]
        require(all(i in coverage[uid] for i,ch in enumerate(unit['text']) if not ch.isspace()),'Uncovered source text')
        source_units[uid]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])])
    reviewed=set()
    for path in REVIEWS:
        review=author.read(path);unit=source_units[review['unit']]
        require(review['source']['unit_sha256']==unit['sha256'] and review['source']['text']==unit['text'],'Old force interpretation review source differs')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old force interpretation review incomplete')
        reviewed.add(review['unit'])
    require(reviewed==expected,'Two force wordings review coverage differs')
    require(SOURCE_ORDER==[36,37],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Two force wordings source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-two-force-wordings-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),inherited_designations=INHERITED_DESIGNATIONS,reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=4,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=73,core_edition=12,new_source_assertions=2,total_source_assertions=177,total_annotations=39,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible two-force-wordings document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedreference'):
    from scripts.field_symmetry_visible_profile import IndividualCutFunctionReferences
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
    if kind=='describedreference':return TemporalReferences(roles,{})
    require(kind=='describedindividualcutfunctionreference','Unknown two-force-wordings reference type')
    return IndividualCutFunctionReferences(roles)





def designation_model(values):
    # Earlier fixture layers sometimes replaced the entire designation handler.
    # Recover retained lookups represented by this finite fixture from the
    # actual linked Native definitions. Earlier paragraphs outside BASE keep
    # their own diagnostic models; this is not a model of every individual.
    inverse={value:key for key,value in names().items()}
    getter=vocabulary()._symbols['designationreference'];rows={}
    for declaration in document()['declarations']:
        body=declaration.get('body',{})
        if declaration.get('parameters') or body.get('kind')!='call' or body['symbol']!=getter:continue
        old=inverse[declaration['name']]
        if old not in values:continue
        args=body['arguments'];require(len(args)==4,'Unexpected designation lookup arity')
        require(all(args[i].get('kind')=='call' and not args[i]['arguments'] for i in (0,1,3)),'Designation anchor is not a closed reference')
        require(args[2].get('kind')=='number' and args[2]['denominator']==1,'Designation ordinal changed')
        key=(values[inverse[args[0]['symbol']]],values[inverse[args[1]['symbol']]],args[2]['numerator'],values[inverse[args[3]['symbol']]])
        value=values[old]
        require(key not in rows or rows[key]==value,'Conflicting retained designation lookup')
        rows[key]=value
    require(rows,'No Native designation references')
    return DesignationReferences(rows)


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
    designations=designation_model(values)
    def designation(document,node,index,context):
        return designations.reference(document,node,index,context)
    def typed(kind):
        nodes={values[reference_anchor(old)] for old in ROLE_ASSIGNMENTS if reference_kind(old)==kind}
        def lookup(document,node,role,context):
            if node in nodes:return reference_model(values,kind).described(document,node,role,context)
            require(kind in result,'Unknown typed reference')
            return result[kind](document,node,role,context)
        return lookup
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedreference','describedindividualcutfunctionreference')}



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-force-interpretation-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/two_force_wordings_visible_profile.py','scripts/two_force_wordings_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_two_force_wordings_visible.py','scripts/visible_two_force_wordings_visible_collection.py',
        'tests/test_two_force_wordings_visible.py','docs/einstein-two-force-wordings-visible-v1.md'}
    for name in ('electromotive_wording','comoving_wording','force_motion_binding'):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved two-force-wordings bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-two-force-wordings-visible-evidence-1',core_words=375,profile_words=891,profile_edition=73,
        new_public_relations=4,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=177,annotations=39,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
