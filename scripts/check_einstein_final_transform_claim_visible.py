"""Connect the attributed phi-one inference, separate branch note, final four equations and beta."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.shared_reference import definition
from scripts import transverse_symmetry_claim_visible_profile as profile
from scripts.transverse_symmetry_claim_visible_profile import ROOT,TransverseSymmetryClaimVisibleVocabulary,write_once
from scripts import check_einstein_transverse_symmetry_claim_visible as previous
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

SOURCE='examples/v016/einstein-final-transform-claim-visible-v1.noema'
BRIDGE='data/einstein-final-transform-claim-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-final-transform-claim-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS
NEW_DEFINITIONS=['ssn',
 'ejea',
 'ejeb',
 'ejec',
 'ejee',
 'ejef',
 'ejeg',
 'ejeh',
 'ejei',
 'ejej',
 'ejek',
 'ejel',
 'ejem',
 'ejen',
 'ejeo',
 'ejep',
 'ejeq']
SENTENCES={'finaltransformsentence': (53, 1)}
SPANS={'zho': ('finaltransformsentence', 1, 12),
 'zhp': ('finaltransformsentence', 13, 20),
 'eisn4': ('finaltransformsentence', 21, 22)}
ROLE_ASSIGNMENTS={'zhq': 'positivebranchnoterole'}
FORWARD_MAPS={}
LOCAL_NAMES=['ssn',
 'ejea',
 'ejeb',
 'ejec',
 'ejee',
 'ejef',
 'ejeg',
 'ejeh',
 'ejei',
 'ejej',
 'ejek',
 'ejel',
 'ejem',
 'ejen',
 'ejeo',
 'ejep',
 'ejeq',
 'finaltransformsentence',
 'zho',
 'zhp',
 'eisn4',
 'zhq',
 'positivebranchnoterole']
READINGS=('data/einstein-final-transform-source-reading-v1.json',)
REVIEWS=('data/einstein-final-transform-u0105-review-v1.json',
 'data/einstein-final-transform-u0106-review-v1.json',
 'data/einstein-final-transform-u0107-review-v1.json',
 'data/einstein-final-transform-u0108-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0105–u0108を原刊902頁の段落末・四式・wobei・βまで照合する。dieserは直前のssk、vorhin gefundenen Relationは前のsroを指す。sein '
 'mußは既存zcの前提からの必要な帰結の提示として読む。',
 '正負の二値の一致と積1だけなら共通値−1も残る。原文が列挙する前提ejeaを改変せず、その推論を著者へ帰属する。直前の正の測定長と符号付き商l/φの一致ejdlが正の枝を選ぶ読みは、ejeeの解釈注記として発話の外に置く。',
 '正の枝を合わせたejedならφ(v)=1への十分条件となるが、有限有理例を実切断の一般定理・原論文の物理的導出・意味同値の自動証明にしない。原文の表示はφ(v)=1であり、φ(−v)=1の式を別に追加しない。',
 'φは先の四式と同じspcで、再正規化しない。既出の式ei7cと現在の全記録対応ei7lを再利用し、同じ対象出来事の全K/k四成分を扱う。全実数四組の測定記録の実在までは要求しない。同じ値の別記録は許す。',
 '最終四式はτ=β(t−vx/V²)、ξ=β(x−vt)、η=y、ζ=z。横二式にβを掛けず、時間式のV²やt/τの役割を変えない。四式列と双方向の全対応条件の両方を保持する。',
 'wobeiは同じ四式で使うβの指定。既存spqによる正の1/√(1−(v/V)²)と同値表示を用い、同じ光速Vと対象速度vを保つ。現行物理設定は0<v<Vで、負の根や別慣習のv/Vをβとしない。',
 '原刊902頁末はβ表示の後にコンマ、固定したMathMLは句点を持つ。この句読点差を記録し、β式の意味を変えない。続く§4の見出しと剛体・時計の考察はu0109以降へ残す。',
 '第53段落の一文を22トークンで参照し、1–12をφ=1の推論、13–20を最終四式への書換え、21–22を同じβの指定へ結ぶ。',
 '正の枝の解釈注記zhqは、同じ測定長ejdlから同じφの正値ejecへの注記関係zflを役割とする。参照取得で役割や引用内容を実行しない。著者の二前提へ正値を追加しない。',
 '旧17定義を再利用し、語彙と参照型を追加しない。共通375語とアルファベット、任意profile57/801語を維持する。']


_AUTHORING=previous._AUTHORING


def _with_authoring_session(function):
    @wraps(function)
    def run(*args,**kwargs):
        if getattr(_AUTHORING,'active',False):return function(*args,**kwargs)
        # QuantityVocabulary adds behavior as well as data; stop before it.
        chain=TransverseSymmetryClaimVisibleVocabulary.__mro__
        chain=chain[:chain.index(SelectionVocabulary)+1]
        with vocabulary_session(chain,root=ROOT,pins=source_pins(include_outputs=False)):
            _AUTHORING.active=True
            try:return function(*args,**kwargs)
            finally:_AUTHORING.active=False
    return run


@lru_cache(maxsize=1)
def vocabulary():return TransverseSymmetryClaimVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][159:162]):visit(n)
    require(len(seen)==278,'Final-transform-claim source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][159:162])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','nao',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    doc['declarations']+=role_definitions()
    add('zhq','individual',call(voc._symbols['describedreference'],k('eirf'),k('zho'),qf(reference_roles()['zhq']),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old=='zhq','Unknown positive branch note reference')
    return 'zho'


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old])
    body=call(m['zfl'],v('va'),k('rd'),dict(kind='quote',body=call(m['ejdl'])),dict(kind='quote',body=call(m['ejec'])),k('eisms'),v('vb'))
    return [definition(n['positivebranchnoterole'],[('va','individual'),('vb','situation')],'truth',body)]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][134:137],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==4,'Source selection changed')
    text=' '.join(s['text'] for s in segments);tokens=text.split()
    require(len(tokens)==22 and tokens[:2]==['Aus','dieser'] and tokens[9]=='[M0188]' and tokens[12:14]==['so','daß'] and tokens[19:]==['[M0189]','wobei','[M0190]'],'Token boundary changed')
    return dict(rule='Fixed whitespace tokens, including formula placeholders and source punctuation; 1-based inclusive spans.',
        sentences={'finaltransformsentence':dict(position=[53,1],tokens=tokens,text=text)},
        spans={n:list(p) for n,p in SPANS.items()},anchor='Paragraph53, page902. Fixed M0190 ends with a period; the preserved reading records the original comma. Section4 is outside this selection.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(105,109)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-final-transform-claim-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[159,160,161],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=0,new_reference_primitives=0,
        semantic_review=SEMANTIC_REVIEW,profile_edition=57,core_edition=12,new_source_assertions=3,total_source_assertions=106,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible final-transform-claim document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],count) for n,count in zip(SENTENCES,(22,),strict=True)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_model(values):
    key=(values['eirf'],values['zho'],canonical(dict(kind='function_ref',symbol=reference_roles()['zhq'])),values['ri'])
    return TemporalReferences({key:values['zhq']},{})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    def described(document,node,role,context):
        if node==values['zho']:return reference_model(values).described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-transverse-symmetry-claim-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/transverse_symmetry_claim_visible_profile.py','scripts/check_einstein_final_transform_claim_visible.py',
        'scripts/visible_transverse_symmetry_claim_visible_collection.py','tests/test_final_transform_claim_visible.py','docs/einstein-final-transform-claim-visible-v1.md',
        'scripts/check_final_transform_claim.py','scripts/compose_final_transform_claim.py',
        'scripts/check_transverse_measured_length.py','scripts/compose_transverse_measured_length.py','reports/transverse-measured-length-v1.json','examples/v014/transverse-measured-length-core.noema',
        'scripts/check_transverse_comparison_scope.py','scripts/compose_transverse_comparison_scope.py','reports/transverse-comparison-scope-v1.json','examples/v014/transverse-comparison-scope-core.noema',
        'scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','scripts/check_first_principle.py','scripts/check_material_relative_frame.py','scripts/check_four_coordinate_claim.py','examples/v014/final-transform-claim-core.noema','reports/final-transform-claim-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved final-transform-claim bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-final-transform-claim-visible-evidence-1',core_words=375,profile_words=801,profile_edition=57,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=3,total_source_assertions=106,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
