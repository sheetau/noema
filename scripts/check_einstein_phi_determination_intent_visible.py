"""Connect the still-unknown function to its intended determination at the current stage."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from noema.identifiers import load_annotations
from scripts.shared_time import allof
from scripts.shared_reference import definition
from scripts import phi_determination_intent_visible_profile as profile
from scripts.phi_determination_intent_visible_profile import ROOT,PhiDeterminationIntentVisibleVocabulary,write_once
from scripts import check_einstein_wave_compatibility_conclusion_visible as previous
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

SOURCE='examples/v016/einstein-phi-determination-intent-visible-v1.noema'
BRIDGE='data/einstein-phi-determination-intent-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-phi-determination-intent-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['srp', 'ejaw', 'ejax', 'ejay', 'ejaz']
SENTENCES=dict(phideterminationsentence=(48,1))
SPANS=dict(zgt=('phideterminationsentence',1,13),zgn=('phideterminationsentence',14,18))
ROLE_ASSIGNMENTS=dict(zgl='stage')
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,'phideterminationstagerole']
READINGS=('data/einstein-phi-determination-intent-source-reading-v1.json',)
REVIEWS=('data/einstein-phi-determination-intent-u0092-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0092全文を原刊901頁へ照合する。entwickelten '
 'Transformationsgleichungenは現在の四式ei7c、φは同じ正規化後のspc、vは同じ相対速度の引数である。前の係数a=zeqとφ=aβを同一値にしない。',
 'unbekannte Funktionは、現在の関数を含む有効な候補族が残り、対象速度域のどこかで値が異なる候補も残るという既存の未決定性の読みを採る。関数の不存在、各速度で値が全て違うこと、現代の知識や著者の伝記的内心に替えない。',
 'nochは先行zfmのsqdから現在zglのsrpへ同じ未決定性が残ることと読む。両段階の候補集合が同一だとは要求せず、間の全瞬間について心理状態が連続したという主張は加えない。',
 '先行と同じ0≤v<Vの対象域で有効性・現在候補の保持・現在関数と候補値の一致・異なる候補値の存在を保持する。u0093以降で使う負速度の値をここで一意に補わず、原文にないφの正値・非零・φ=1を追加しない。',
 'welcheは未知として述べた同じ関数spcを受ける。wir nun bestimmen '
 'wollenは同じ著者が今の論述段階からその関数の値を決める意図を示すzgmとして読み、実行済み・成功・一意解・方法が見つかったことを含めない。',
 'この一文の既出式の指示、残存、未知関数の速度依存、同じ対象を受ける関係節、論述の現在と意図を記述する。第三系の導入・二回変換・相反性・符号規約は後続へ残す。',
 '有限対照は同じ段階・候補・関数・速度域の引数と引用・意図の帰属を検査する。実切断や関数全体への量化を有限標本で置換せず、例化した本体と有限境界を明示する。一般的な認識理論や意味同値の自動証明ではない。',
 '原刊901頁の独立段落を採用座標48/1へ接続する。前半1–13を未知性zgt、関係節14–18を意図zgnとする。',
 '現在段階zglは意図の箇所zgnを基準に、同じ著者・spcの引用・第三節・候補段階・候補文脈を結ぶ閉じた役割で参照する。参照取得はその役割や関数を実行しない。',
 '旧5定義と既存zgm規約を再利用する。共通375語、任意54版789語、新参照型0個。名前の衝突は親宣言・core・全公開profileに事前照合する。']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=PhiDeterminationIntentVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return PhiDeterminationIntentVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][145:146]):visit(n)
    require(len(seen)==230,'Phi-determination-intent source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][145:146])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','give',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=role_definitions()
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {'zgl':names()['phideterminationstagerole']}


def reference_anchor(old):
    require(old=='zgl','Unknown function-determination stage');return 'zgn'


def role_definitions():
    n=names();m=mapping();voc=vocabulary();k=lambda old:call(n[old])
    role=definition(n['phideterminationstagerole'],[('va','situation'),('vb','situation')],'truth',
        call(m['zgm'],k('zgn'),k('rd'),dict(kind='quote',body=call(m['spc'])),v('va'),k('eisms'),v('vb')))
    reference=definition(n['zgl'],[],'situation',call(voc._symbols['describedsettingreference'],
        k('eirf'),k('zgn'),qf(n['phideterminationstagerole']),k('ri')))
    return [role,reference]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][115:116],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==1,'Source selection changed')
    tokens=segments[0]['text'].split()
    require(len(tokens)==18 and tokens[:3]==['In','den','entwickelten'] and tokens[12:16]==['auf,','welche','wir','nun'] and tokens[-1]=='wollen.','Sentence boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; 1-based inclusive positions.',
        sentences={'phideterminationsentence':dict(position=[48,1],tokens=tokens,text=' '.join(tokens))},
        spans={n:list(p) for n,p in SPANS.items()},anchor='Separate paragraph between the compatibility conclusion and third-frame introduction, page 901.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(92,93)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        entry=c.entries[old];decl=entry['declaration'];contract=profile.CONTRACTS[new]
        require(decl['parameters']==contract['parameters'] and decl['result']==contract['result'] and entry['arguments']==contract['arguments'] and entry['meaning_ja'].split('] ',1)[-1]==contract['meaning_ja'],'Source contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-phi-determination-intent-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[145],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=54,core_edition=12,new_source_assertions=1,total_source_assertions=90,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible phi-determination-intent document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|dict(zgl='phideterminationstage')
SITUATIONS=tuple(dict.fromkeys([*previous.SITUATIONS,'phideterminationstage']))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['phideterminationsentence'],18)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    span_keys={(values['eirf'],values[node],start,values[node],end,values['ri']) for node,start,end in SPANS.values()}
    def span(document,first,start,last,end,context):
        key=(document,first,TextPresentation.coordinate(start),last,TextPresentation.coordinate(end),context)
        if key in span_keys:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    key=(values['eirf'],values['zgn'],canonical(dict(kind='function_ref',symbol=reference_roles()['zgl'])),values['ri'])
    settings=SettingReferences({key:values['zgl']})
    def setting(document,node,role,context):
        if node==values['zgn']:return settings.described(document,node,role,context)
        return result['describedsettingreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedsettingreference=setting)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-wave-compatibility-conclusion-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/phi_determination_intent_visible_profile.py','scripts/check_einstein_phi_determination_intent_visible.py',
        'scripts/visible_phi_determination_intent_visible_collection.py','tests/test_phi_determination_intent_visible.py','docs/einstein-phi-determination-intent-visible-v1.md',
        'scripts/check_phi_determination_intent.py','scripts/compose_phi_determination_intent.py',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','examples/v014/phi-determination-intent-core.noema','reports/phi-determination-intent-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved phi-determination-intent bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-phi-determination-intent-visible-evidence-1',core_words=375,profile_words=789,profile_edition=54,
        new_public_relations=1,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=90,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
