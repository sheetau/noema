"""Connect scoped equivalence, equation form and the common field coefficient."""
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
from scripts import check_einstein_moving_field_visible as previous
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

SOURCE='examples/v016/einstein-field-comparison-visible-v1.noema'
BRIDGE='data/einstein-field-comparison-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-field-comparison-visible-v1'
LABEL=previous.LABEL
SOURCE_ORDER=[24]
SOURCE_VISUAL_REVIEW=[{'path': 'artifacts/written-facsimiles-v1/einstein-1905-unlp-p908-0.jpg',
  'sha256': '511201da1a9dca7175cdbf604c522c5339de25b98b954060e169aee35111f4ac',
  'actually_displayed': True,
  'independent_human_reading': False,
  'observations': ['移動場の六式の後、Offenbarから新段落。äquivalent sind.で第一文、Da dieからmüssen.まで第二文。',
                   '第三文Es gelten also die Beziehungen:はコロンで下の六式へ続く。式の後で文を閉じる。',
                   'ψ(v)が共通係数で、ξ,η,ζ,τには依存せずvに依存してよいと読める。第三節のφを再使用しない。',
                   '原刊のM′の右辺はψ(v)β(M+v/V Z)。保存済みM0307のz→Z局所訂正と一致し、元資料は変更しない。']}]
PUBLIC_RELATIONS={'eispz': 'twofielddisplayform'}
REUSED_DEFINITIONS=[]
NEW_DEFINITIONS=['sag2',
 'sah2',
 'sai2',
 'saj2',
 'sak2',
 'ejub',
 'ejuc',
 'ejud',
 'ejue',
 'ejuf',
 'ejug',
 'ejuh',
 'ejui',
 'ejuj',
 'ejuk',
 'ejul',
 'ejum',
 'ejun',
 'ejuo',
 'ejup',
 'ejuq']
FORWARD_MAPS={}
HEADINGS={}
SENTENCES={'eisp2': (73, 1), 'eisp3': (73, 2), 'fieldresultssentence': (73, 3)}
TEXT_SENTENCES={'eisp2': (73, 1), 'eisp3': (73, 2), 'fieldresultssentence': (73, 3)}
TOKEN_COUNTS={'eisp2': 26, 'eisp3': 49, 'fieldresultssentence': 6}
SENTENCE_SEGMENTS=[{'unit': 'einstein-1905:u0163',
  'text': 'Offenbar müssen nun die beiden für das System [M0301] gefundenen Gleichungssysteme genau dasselbe '
          'ausdrücken, da beide Gleichungssysteme den Maxwell-Hertzschen Gleichungen für das System [M0302] '
          'äquivalent sind. Da die Gleichungen beider Systeme ferner bis auf die die Vektoren darstellenden '
          'Symbole übereinstimmen, so folgt, daß die in den Gleichungssystemen an entsprechenden Stellen '
          'auftretenden Funktionen bis auf einen für alle Funktionen des einen Gleichungssystems '
          'gemeinsamen, von [M0303] und [M0304] unabhängigen, eventuell von [M0305] abhängigen Faktor '
          '[M0306] übereinstimmen müssen. Es gelten also die Beziehungen:',
  'sha256': '5d94c2847e1cda5422bf0dc6f1ac40d12d70b65d8b223d887a9aedb9796d4195'},
 {'unit': 'einstein-1905:u0164',
  'text': '[M0307]',
  'sha256': 'a0ef77c6dae117bd6023e64681a492833aa636d572c1dfb478061cebef9cfd5e'}]
SENTENCE_DETAILS={'eisp2': {'position': [73, 1],
           'unit': 'einstein-1905:u0163',
           'range': [0, 211],
           'text': 'Offenbar müssen nun die beiden für das System [M0301] gefundenen Gleichungssysteme genau '
                   'dasselbe ausdrücken, da beide Gleichungssysteme den Maxwell-Hertzschen Gleichungen für '
                   'das System [M0302] äquivalent sind.',
           'tokens': ['Offenbar',
                      'müssen',
                      'nun',
                      'die',
                      'beiden',
                      'für',
                      'das',
                      'System',
                      '[M0301]',
                      'gefundenen',
                      'Gleichungssysteme',
                      'genau',
                      'dasselbe',
                      'ausdrücken,',
                      'da',
                      'beide',
                      'Gleichungssysteme',
                      'den',
                      'Maxwell-Hertzschen',
                      'Gleichungen',
                      'für',
                      'das',
                      'System',
                      '[M0302]',
                      'äquivalent',
                      'sind.']},
 'eisp3': {'position': [73, 2],
           'unit': 'einstein-1905:u0163',
           'range': [212, 593],
           'text': 'Da die Gleichungen beider Systeme ferner bis auf die die Vektoren darstellenden Symbole '
                   'übereinstimmen, so folgt, daß die in den Gleichungssystemen an entsprechenden Stellen '
                   'auftretenden Funktionen bis auf einen für alle Funktionen des einen Gleichungssystems '
                   'gemeinsamen, von [M0303] und [M0304] unabhängigen, eventuell von [M0305] abhängigen '
                   'Faktor [M0306] übereinstimmen müssen.',
           'tokens': ['Da',
                      'die',
                      'Gleichungen',
                      'beider',
                      'Systeme',
                      'ferner',
                      'bis',
                      'auf',
                      'die',
                      'die',
                      'Vektoren',
                      'darstellenden',
                      'Symbole',
                      'übereinstimmen,',
                      'so',
                      'folgt,',
                      'daß',
                      'die',
                      'in',
                      'den',
                      'Gleichungssystemen',
                      'an',
                      'entsprechenden',
                      'Stellen',
                      'auftretenden',
                      'Funktionen',
                      'bis',
                      'auf',
                      'einen',
                      'für',
                      'alle',
                      'Funktionen',
                      'des',
                      'einen',
                      'Gleichungssystems',
                      'gemeinsamen,',
                      'von',
                      '[M0303]',
                      'und',
                      '[M0304]',
                      'unabhängigen,',
                      'eventuell',
                      'von',
                      '[M0305]',
                      'abhängigen',
                      'Faktor',
                      '[M0306]',
                      'übereinstimmen',
                      'müssen.']},
 'fieldresultssentence': {'position': [73, 3],
                          'unit': 'einstein-1905:u0163',
                          'range': [594, 625],
                          'text': 'Es gelten also die Beziehungen: [M0307]',
                          'tokens': ['Es', 'gelten', 'also', 'die', 'Beziehungen:', '[M0307]']}}
SPANS={'zn2': ('fieldresultssentence', 1, 5),
 'eisp4': ('fieldresultssentence', 6, 6),
 'fieldscaleanchor': ('eisp3', 47, 47)}
MULTI_SPANS={}
DESIGNATIONS={}
FORMS={}
ROLE_ASSIGNMENTS={'znz': 'fieldscalerole'}
REFERENCE_SORTS={'znz': {'kind': 'function',
         'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}],
         'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}}
REFERENCE_ANCHORS={'znz': 'fieldscaleanchor'}
ROLE_DEFINITIONS={'znz': {'kind': 'definition',
         'name': 'fieldscalerole',
         'parameters': [{'name': 'va',
                         'sort': {'kind': 'function',
                                  'parameters': [{'kind': 'function',
                                                  'parameters': ['number'],
                                                  'result': 'truth'}],
                                  'result': {'kind': 'function',
                                             'parameters': ['number'],
                                             'result': 'truth'}}},
                        {'name': 'vb', 'sort': 'situation'}],
         'result': 'truth',
         'body': {'kind': 'forall',
                  'variable': 'vc',
                  'sort': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'},
                  'body': {'kind': 'implies',
                           'arguments': [{'kind': 'call',
                                          'symbol': 's45',
                                          'arguments': [{'kind': 'call', 'symbol': 'tc', 'arguments': []},
                                                        {'kind': 'variable', 'name': 'vc'}]},
                                         {'kind': 'call',
                                          'symbol': 'ba',
                                          'arguments': [{'kind': 'apply',
                                                         'function': {'kind': 'variable', 'name': 'va'},
                                                         'arguments': [{'kind': 'variable',
                                                                        'name': 'vc'}]}]}]}}}}
LOCAL_NAMES=['sag2',
 'sah2',
 'sai2',
 'saj2',
 'sak2',
 'ejub',
 'ejuc',
 'ejud',
 'ejue',
 'ejuf',
 'ejug',
 'ejuh',
 'ejui',
 'ejuj',
 'ejuk',
 'ejul',
 'ejum',
 'ejun',
 'ejuo',
 'ejup',
 'ejuq',
 'znz',
 'zn2',
 'eisp2',
 'eisp3',
 'eisp4',
 'fieldresultssentence',
 'fieldscaleanchor',
 'fieldscalerole']
READINGS=('data/einstein-field-comparison-claim-source-reading-v1.json',)
REVIEWS=('data/einstein-field-comparison-claim-u0163-review-v1.json',
 'data/einstein-field-comparison-claim-u0164-review-v1.json')
SEMANTIC_REVIEW=['u0163の三文とu0164の六式を原刊908頁で連続して読む。理由付き等価性、明白さ、さらに同形であること、必要性、全六関数への共通係数、座標時刻への非依存、速度依存の許容、結果表示を保持する。',
 '等価性は同じ比較設定の非空全域で成立条件が一致するという読みであり、単独の真偽一致ではない。比較設定は物理的な両場・同じ過程・真空・座標域の対応を保ち、方程式や比例の成功例だけを選ばない。',
 '同形性は同じ六回転式の閉じた型と場引数の対応として構成する。正のVでの分母払い、二列配置と論理的な六条件の順の差を明示し、偏微分軸・符号・係数は変更しない。',
 'ψは速度だけを引数とするznzを同じ六成分と全点で共有する。原文の一組の全関数をこの六成分と読む。別の場の組全てについて同じ係数を選ぶという追加の普遍主張は補わない。速度依存を許すが実際の依存、非零性、正値、偶性、値1を要求しない。',
 '元の場からの混合と逆座標写像はs6k/s6l、全領域一致はsaj2、比例の全点・全成分はsai2/sak2を再利用する。現在の物理的な場の意味はejsy/ejtuへ接続する。',
 '六回転式だけでは変換後の式が導けない既存反例、同じ微分方程式を満たすだけでは比例が得られない定数場の反例を保持する。著者の理由と結論を記述し、原理の適用の片方向条件文を処理系が双方向同値へ格上げしない。',
 '固定M0307のM′右辺の小文字zは保存した原刊908頁の大文字Zへ局所訂正して読む。生資料・旧訂正記録は保持する。909頁のφ/ψの表記差と逆変換は後続。',
 '旧文155以外の357主張・旧意味規約・旧証拠を保持し、原文の全単位判断を有限検査や型検査から区別する。全実数・全関数域の有限列挙拒否を保持する。']
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
    require(len(seen)==151,'Field-comparison source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy([c.document['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(HEADINGS)|set(SENTENCES)|set(SPANS)|{n for n in ROLE_ASSIGNMENTS if REFERENCE_SORTS[n]=='individual'}|set(DESIGNATIONS)|set(MULTI_SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','book','town','nao',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    require(old in ROLE_ASSIGNMENTS,'Unknown field-comparison reference')
    return REFERENCE_ANCHORS[old]


def reference_kind(old):
    require(old=='znz','Unknown field-comparison reference')
    return 'describedcutfunctionreference'


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
    result['statements']=renamed(doc['statements'][199:200],inverse);return normalize_document(result)



def text_boundaries():
    prior=previous.text_boundaries()['sentences']['movingfielddefinitionsentence']
    require(prior['position']==[72,1] and SENTENCES=={'eisp2':(73,1),'eisp3':(73,2),'fieldresultssentence':(73,3)},'Paragraph sequence changed')
    units={u['id']:u for u in author.read(author.UNITS)['units']}
    for row in SENTENCE_SEGMENTS:
        unit=units[row['unit']]
        require(unit['text']==row['text'] and unit['text_sha256']==row['sha256'],'Comparison paragraph segment changed')
    covered=set();rows={}
    for name,row in SENTENCE_DETAILS.items():
        start,end=row['range'];part=units[row['unit']]['text'][start:end]
        if name=='fieldresultssentence':part+=' '+units['einstein-1905:u0164']['text']
        require(part==row['text'] and part.split()==row['tokens'] and len(row['tokens'])==TOKEN_COUNTS[name],'Comparison sentence boundary changed')
        covered.update(range(start,end));rows[name]=dict(position=list(SENTENCES[name]),text=part,tokens=row['tokens'],source_range=row['range'])
    require(all(i in covered for i,ch in enumerate(units['einstein-1905:u0163']['text']) if not ch.isspace()),'Comparison sentences omit source text')
    require(rows['eisp2']['tokens'][-1]=='sind.' and rows['eisp3']['tokens'][-1]=='müssen.','Comparison sentence endings changed')
    require(rows['fieldresultssentence']['tokens']==['Es','gelten','also','die','Beziehungen:','[M0307]'],'Result/display continuation changed')
    require(SPANS=={'zn2':('fieldresultssentence',1,5),'eisp4':('fieldresultssentence',6,6),'fieldscaleanchor':('eisp3',47,47)},'Comparison text reference changed')
    require(rows['eisp3']['tokens'][46]=='[M0306]','Current psi coefficient anchor changed')
    require(units['einstein-1905:u0162']['text']=='[M0300]' and units['einstein-1905:u0165']['text'].startswith('Bildet man nun'),'Adjacent paragraph boundary changed')
    for row in SOURCE_VISUAL_REVIEW:require(author.digest(row['path'])==row['sha256'],'Inspected original page changed')
    return dict(rule='Paragraph73 has three sentences: equivalence with obviousness and reason; shared equation form and the common coefficient; result introduction continued by six displayed equations. The subsequent inverse derivation is separate.',
        sentences=rows,spans={n:list(p) for n,p in SPANS.items()},multi_sentence_spans={},designations={},designation_forms={})



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
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][start:end],'Field comparison source reading differs')
            coverage.setdefault(unit['id'],set()).update(range(start,end))
            for item in row['math']:
                require(item['id'] not in math or math[item['id']]==item,'Conflicting mathematical source record')
                math[item['id']]=item
    expected={f'einstein-1905:u{i:04d}' for i in range(163,165)}
    require(set(coverage)==expected,'Field comparison source selection differs')
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
    require(reviewed==expected,'Field comparison review coverage differs')
    require(SOURCE_ORDER==[24],'Source selection duplicate or omission')
    require(backprojection(document())==source_excerpt(),'Field comparison source backprojection differs')
    for old,new in PUBLIC_RELATIONS.items():
        entry=c.entries[old];contract=profile.CONTRACTS[new];d=entry['declaration']
        require(contract['parameters']==d['parameters'] and contract['result']==d['result'],'Public contract type differs')
        require(contract['arguments']==entry['arguments'] and contract['meaning_ja']==entry['meaning_ja'].removeprefix('[current の記号名] '),'Public contract meaning differs')
    return dict(schema='noema-einstein-field-comparison-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=SOURCE_ORDER,source_units=source_units,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=list(math.values()),annotations=annotations(),
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=1,new_reference_primitives=0,new_core_words=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=70,core_edition=12,new_source_assertions=1,total_source_assertions=162,total_annotations=38,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible field-comparison document differs');return result


BASE=previous.BASE|{n:n for n in (*HEADINGS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*MULTI_SPANS)}
SITUATIONS=(*previous.SITUATIONS,*(BASE[n] for n,s in REFERENCE_SORTS.items() if s=='situation'))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],TOKEN_COUNTS[n]) for n in TEXT_SENTENCES]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values,kind='describedcutfunctionreference'):
    from scripts.affine_time_visible_profile import TypedFunctionReferences
    require(kind=='describedcutfunctionreference','Unknown field-comparison reference type')
    roles={(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri']):values[old] for old in ROLE_ASSIGNMENTS}
    return TypedFunctionReferences(kind,roles)


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
    return result|dict(headingreference=heading,sentencereference=sentence,sentencetokenspanreference=span,sentencespanreference=passage,designationreference=designation)|{kind:typed(kind) for kind in ('describedcutfunctionreference',)}


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-moving-field-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/field_comparison_visible_profile.py','scripts/field_comparison_visible_profile_contracts.py',
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/check_einstein_field_comparison_visible.py','scripts/visible_field_comparison_visible_collection.py',
        'tests/test_field_comparison_visible.py','docs/einstein-field-comparison-visible-v1.md'}
    for name in ('field_comparison_claim',):
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
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved field-comparison bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-field-comparison-visible-evidence-1',core_words=375,profile_words=879,profile_edition=70,
        new_public_relations=1,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=162,annotations=38,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=LIMITS)
