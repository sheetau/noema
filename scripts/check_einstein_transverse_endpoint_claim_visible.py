"""Connect the physical-meaning question, selected transverse rod and both endpoint displays."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.light_speed_time_profile import CutReferences
from scripts.shared_reference import definition
from scripts import transverse_endpoint_claim_visible_profile as profile
from scripts.transverse_endpoint_claim_visible_profile import ROOT,TransverseEndpointClaimVisibleVocabulary,write_once
from scripts import check_einstein_reciprocal_claim_visible as previous
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

SOURCE='examples/v016/einstein-transverse-endpoint-claim-visible-v1.noema'
BRIDGE='data/einstein-transverse-endpoint-claim-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-transverse-endpoint-claim-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['srw',
 'srx',
 'sry',
 'ejb7',
 'ejca',
 'ejcb',
 'ejcc',
 'ejcd',
 'ejce',
 'ejcf',
 'ejcg',
 'ejch',
 'ejci',
 'ejcj',
 'ejck',
 'ejcl',
 'ejcm',
 'ejcn',
 'ejco',
 'ejcp',
 'ejcq',
 'ejcr',
 'ejcs',
 'ejct',
 'ejcu',
 'ejcv',
 'ejcw']
SENTENCES={'zhh': (51, 1), 'zhi': (51, 2), 'endpointdisplays': (51, 3)}
SPANS={'zhj': ('endpointdisplays', 1, 27),
 'eisny': ('endpointdisplays', 28, 28),
 'eisnz': ('endpointdisplays', 30, 30)}
ROLE_ASSIGNMENTS={'zgu': 'rod', 'zgv': 'low', 'zgw': 'high', 'zgz': 'extent'}
FORWARD_MAPS={}
LOCAL_NAMES=['srw',
 'srx',
 'sry',
 'ejb7',
 'ejca',
 'ejcb',
 'ejcc',
 'ejcd',
 'ejce',
 'ejcf',
 'ejcg',
 'ejch',
 'ejci',
 'ejcj',
 'ejck',
 'ejcl',
 'ejcm',
 'ejcn',
 'ejco',
 'ejcp',
 'ejcq',
 'ejcr',
 'ejcs',
 'ejct',
 'ejcu',
 'ejcv',
 'ejcw',
 'zhh',
 'zhi',
 'endpointdisplays',
 'zhj',
 'eisny',
 'eisnz',
 'zgu',
 'zgv',
 'zgw',
 'zgz',
 'endpointrodrole',
 'endpointlowrole',
 'endpointhighrole',
 'endpointextentrole']
READINGS=('data/einstein-transverse-endpoint-source-reading-v1.json',)
REVIEWS=('data/einstein-transverse-endpoint-u0097-review-v1.json',
 'data/einstein-transverse-endpoint-u0098-review-v1.json',
 'data/einstein-transverse-endpoint-u0099-review-v1.json',
 'data/einstein-transverse-endpoint-u0100-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0097の三文とu0098/u0099/u0100の二端座標・undを一つの意味群として読む。原刊902頁の印字Hをkのη軸の役割とし、ξ=ζ=0、0≤η≤lの全閉区間を理想化した線状棒とする。材料の実際の切断を追加しない。',
 'nunは相反積を述べた後で同じφの物理的意味へ進む談話上の現在。wirは著者の論述上の声。ins Auge '
 'fassenは対象を考察へ取り上げる関係eisnxと読み、単なる仮定の採用ugや視覚的目撃だけに置き換えない。',
 'Dieses Stückとdessen '
 'Endenは直前に取り上げた同じzguと二端標識zgv/zgw。全物質点と全時刻の履歴・区間の占有・並進・自軸との直交をejcfへ保持する。厚い一般の棒を零厚みとする一般論ではない。',
 '表示はKの対象区間の任意時刻tについての両端の式と読む。各時刻に同じ端の同じ出来事の現在二系記録を要求し、全該当記録へ式を適用する。各系の時計・位置測定・履歴・時間区間はejceで結び、t=τは加えない。対象区間は既存eisls/eisltであり全宇宙の時間へ広げない。',
 'M0179の第一項はη=l側、M0180の第二項はη=0側。添字はこの端の番号であって時間番号ではない。両項は同じtの任意値について述べられ、各時刻の存在と全称により同じK時刻で両端を選べる。',
 'l/φ(v)は保存MathMLの分数。srxは正の分母φ²を用いる等価な除算であり、負のφを絶対値へ変えない。φは同じ正規化後spcで非零、速度は同じzb7。正値性、反転対称性、φ=1、棒の測定長の物理的解釈の結論はここで要求しない。',
 '表示を著者の主張として帰属し、検証器が現実の測定を行い又は全物理的導出を証明したとはしない。既存の物理履歴、現在の測定、純粋数式の意味規約を再利用する。全実数量化は有限標本へ縮めず、局所の例化検査と原刊通読の判断を区別する。',
 '第51段落の3文は8/18/30トークン。第三文の1–27がコロンまで、28が第一表示、29がund、30が句点を含む第二表示。参照は固定転記の境界を保つ。',
 '固有長を正のパラメータとして参照し、その同じ長さ・設定の棒、下端、上端を順にejccへ結ぶ閉じた役割で参照する。未参照の端は存在量化する。参照取得で役割や物理履歴を評価しない。',
 '旧27定義と旧2規約を再利用する。共通375語とアルファベット不変、任意profile56/798語、新参照型0。']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=TransverseEndpointClaimVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return TransverseEndpointClaimVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][151:154]):visit(n)
    require(len(seen)==248,'Transverse-endpoint-claim source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][151:154])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|{'zgu','zgv','zgw'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','treeone',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=role_definitions()
    for old in ROLE_ASSIGNMENTS:
        kind='describedcutreference' if old=='zgz' else 'describedreference'
        add(old,profile.CUT if old=='zgz' else 'individual',call(voc._symbols[kind],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()['endpoint'+role+'role'] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown transverse endpoint reference');return 'zhi'


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old])
    exists=lambda name,body:dict(kind='exists',variable=name,sort='individual',body=body)
    segment=lambda *args:call(m['ejcc'],*args,k('zb6'),k('zgz'))
    bodies={
        'zgz':call(m['sbg'],v('va')),
        'zgu':exists('vc',exists('vd',segment(v('va'),v('vc'),v('vd')))),
        'zgv':exists('vc',segment(k('zgu'),v('va'),v('vc'))),
        'zgw':segment(k('zgu'),k('zgv'),v('va')),
    }
    return [definition(reference_roles()[old],[('va',profile.CUT if old=='zgz' else 'individual'),('vb','situation')],'truth',bodies[old]) for old in ROLE_ASSIGNMENTS]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][126:129],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==4,'Source selection changed')
    pieces=segments[0]['text'].split('. ')
    require(len(pieces)==3 and pieces[0].startswith('Wir fragen') and pieces[1].startswith('Wir fassen') and pieces[2].startswith('Dieses Stück') and [s['text'] for s in segments[1:]]==['[M0179]','und','[M0180]'],'Sentence boundary changed')
    texts=[pieces[0]+'.',pieces[1]+'.',' '.join([pieces[2],*[s['text'] for s in segments[1:]]])]
    require([len(s.split()) for s in texts]==[8,18,30] and texts[2].split()[27:]==['[M0179]','und','[M0180]'],'Token boundary changed')
    return dict(rule='Fixed whitespace tokens; formula internal punctuation stays within the formula token; 1-based inclusive spans.',
        sentences={n:dict(position=list(SENTENCES[n]),tokens=text.split(),text=text) for n,text in zip(SENTENCES,texts,strict=True)},
        spans={n:list(p) for n,p in SPANS.items()},anchor='Paragraph51 after the reciprocal product, page902. The third sentence ends after the second displayed formula and its period.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(97,101)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        entry=c.entries[old];decl=entry['declaration'];contract=profile.CONTRACTS[new]
        require(decl['parameters']==contract['parameters'] and decl['result']==contract['result'] and entry['arguments']==contract['arguments'] and entry['meaning_ja'].split('] ',1)[-1]==contract['meaning_ja'],'Source contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-transverse-endpoint-claim-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[151,152,153],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=2,new_reference_primitives=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=56,core_edition=12,new_source_assertions=3,total_source_assertions=98,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible transverse-endpoint-claim document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS) if n!='zgz'}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],count) for n,count in zip(SENTENCES,(8,18,30),strict=True)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_models(values):
    key=lambda old:(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri'])
    individuals=TemporalReferences({key(old):values[old] for old in ROLE_ASSIGNMENTS if old!='zgz'}, {})
    cuts=CutReferences({key('zgz'):values['zgz']} if 'zgz' in values else {})
    return individuals,cuts


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
    def described(document,node,role,context):
        if node==values['zhi']:return reference_models(values)[0].described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    def cut(document,node,role,context):
        if node==values['zhi']:return reference_models(values)[1].described(document,node,role,context)
        return result['describedcutreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described,describedcutreference=cut)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-reciprocal-claim-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/transverse_endpoint_claim_visible_profile.py','scripts/check_einstein_transverse_endpoint_claim_visible.py',
        'scripts/visible_transverse_endpoint_claim_visible_collection.py','tests/test_transverse_endpoint_claim_visible.py','docs/einstein-transverse-endpoint-claim-visible-v1.md',
        'scripts/check_transverse_endpoint_claim.py','scripts/compose_transverse_endpoint_claim.py',
        'scripts/check_transverse_segment.py','scripts/compose_transverse_segment.py','reports/transverse-segment-v1.json','examples/v014/transverse-segment-core.noema','scripts/check_translated_light_trial.py',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','scripts/check_first_principle.py','scripts/check_material_relative_frame.py','scripts/check_four_coordinate_claim.py','examples/v014/transverse-endpoint-claim-core.noema','reports/transverse-endpoint-claim-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved transverse-endpoint-claim bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-transverse-endpoint-claim-visible-evidence-1',core_words=375,profile_words=798,profile_edition=56,
        new_public_relations=2,new_reference_primitives=0,new_source_assertions=3,total_source_assertions=98,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
