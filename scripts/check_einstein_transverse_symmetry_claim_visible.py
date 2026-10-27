"""Connect measured length, full spatial symmetry and the signed-phi equivalence."""
from copy import deepcopy
from functools import lru_cache,wraps
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.observer_contrast_visible_profile import TokenSpanReferences
from scripts.temporal_discourse_profile import TemporalReferences
from scripts.rod_experiment_profile import SettingReferences
from scripts.shared_reference import definition
from scripts import transverse_symmetry_claim_visible_profile as profile
from scripts.transverse_symmetry_claim_visible_profile import ROOT,TransverseSymmetryClaimVisibleVocabulary,write_once
from scripts import check_einstein_transverse_endpoint_claim_visible as previous
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

SOURCE='examples/v016/einstein-transverse-symmetry-claim-visible-v1.noema'
BRIDGE='data/einstein-transverse-symmetry-claim-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-transverse-symmetry-claim-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['ssk',
 'ejcx',
 'ejcy',
 'ejcz',
 'ejc2',
 'ejc3',
 'ejc4',
 'ejc5',
 'ejc6',
 'ejc7',
 'ejda',
 'ejdb',
 'ejdc',
 'ejdd',
 'ejde',
 'ejdf',
 'ejdg',
 'ejdh',
 'ejdi',
 'ejdk',
 'ejdl',
 'ejdm',
 'ejdn',
 'ejdo',
 'ejdp',
 'ejdq',
 'ejdr',
 'ejds',
 'ejdt',
 'ejdu',
 'ejdv',
 'ejdw',
 'ejdx',
 'ejdy',
 'ejdz',
 'ejd2',
 'ejd3',
 'ejd4',
 'ejd5',
 'ejd6',
 'ejd7']
SENTENCES={'zhk': (52, 1), 'zhl': (52, 2), 'zhm': (52, 3), 'symmetrydisplays': (52, 4)}
SPANS={'eisn3': ('symmetrydisplays', 1, 3), 'zhn': ('symmetrydisplays', 4, 5)}
ROLE_ASSIGNMENTS={'zg2': 'reversedrodsettingrole', 'measuredlengthfamily': 'measuredlengthfamilyrole'}
FORWARD_MAPS={'zha': 'measuredlengthfamily'}
LOCAL_NAMES=['ssk',
 'ejcx',
 'ejcy',
 'ejcz',
 'ejc2',
 'ejc3',
 'ejc4',
 'ejc5',
 'ejc6',
 'ejc7',
 'ejda',
 'ejdb',
 'ejdc',
 'ejdd',
 'ejde',
 'ejdf',
 'ejdg',
 'ejdh',
 'ejdi',
 'ejdk',
 'ejdl',
 'ejdm',
 'ejdn',
 'ejdo',
 'ejdp',
 'ejdq',
 'ejdr',
 'ejds',
 'ejdt',
 'ejdu',
 'ejdv',
 'ejdw',
 'ejdx',
 'ejdy',
 'ejdz',
 'ejd2',
 'ejd3',
 'ejd4',
 'ejd5',
 'ejd6',
 'ejd7',
 'zhk',
 'zhl',
 'zhm',
 'symmetrydisplays',
 'eisn3',
 'zhn',
 'zg2',
 'measuredlengthfamily',
 'zha',
 'reversedrodsettingrole',
 'measuredlengthfamilyrole']
READINGS=('data/einstein-transverse-symmetry-source-reading-v1.json',)
REVIEWS=('data/einstein-transverse-symmetry-u0101-review-v1.json',
 'data/einstein-transverse-symmetry-u0102-review-v1.json',
 'data/einstein-transverse-symmetry-u0103-review-v1.json',
 'data/einstein-transverse-symmetry-u0104-review-v1.json')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['原刊902頁のu0101–u0104を、Kで測る長さからφの物理的意味へ進む説明、方向一般の対称性と明白さ、正負速度の長さ不変、二つの商の等値、oderによる同値書換えとして読む。M0186の平坦化文字列を積と読まない。',
 '測定長は現在の同時刻両端記録と校正計量から得る正の距離。原文のl/φ(v)との等値は、符号付き商を正の距離へ等置する向きの読みとして明示する。端点式だけが与えるl/|φ(v)|からφの正値を無断で導出したとはしない。',
 '同じ特定の棒は同じ全物質点・固有形状・固有長を保つ。比較する両系と尺度を固定し、配置の位置と向きは変えられる。各系の時刻・区間端や、別設定の時計原点を等置しない。',
 '方向と向きへの独立性は、0<|v⃗|<Vの各速度三成分に適格設定が存在する理想化した比較群で、同速なら長さが等しいという全称として読む。速度零・光速以上は先行する動く系の設定の範囲外。有限実験の網羅や加速による全設定の実現を主張しない。候補選択に長さの等値を含めない。',
 'Aus Symmetriegründenは同じ背景・尺度で空間の向きを特別扱いしないという理由の帰属eisn2、einleuchtendは同じ内容の明白さzdgで保持する。nur von der '
 'Geschwindigkeitはこの対称性比較における速度の大きさだけへの依存で、他の独立な物理条件を変える場合まで無条件に同じ長さとしない。',
 '正負交換では同じK/kと同じ棒を保ち、別設定で速度だけを(v,0,0)から(−v,0,0)へ変える。同じφを正負の引数で評価し、K/kの交換や別関数への交換としない。',
 'alsoとHieraus '
 'folgtは著者の帰結提示。damitは同じ測定内容による物理的解釈。oderは非零φと同じ正のlを保つ二つの等値の同値書換えであり、単なる選択肢ではない。著者の主張の真理と処理系の検査を分ける。',
 'φ(v)=φ(−v)だけから各値1を導かず、前の相反積との合成と最終四式・βの定義はu0105–u0108へ残す。有限対照・全実数域の拒否・原刊通読を別の証拠として保持する。',
 '第52段落の四文を18/39/20/5トークンで参照する。第四文の1–3はHieraus folgtと分数等値、4–5はoderとφの等値・句点。',
 '逆向き設定は同じ棒の符号反転ejdg、測定長関数は同じ棒の各設定の測定ejczに結ぶ閉じた役割で参照する。測定のない設定の値を補わず、参照取得で役割や関数を実行しない。',
 '旧41定義と旧2規約を再利用する。共通375語とアルファベット不変、任意profile57/801語、新参照型1。']


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
    for n in _references(c.document['statements'][154:159]):visit(n)
    require(len(seen)==293,'Transverse-symmetry-claim source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][154:159])))


@lru_cache(maxsize=1)
@_with_authoring_session
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','home','aki',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    for old,kind,sort in [('zg2','describedsettingreference','situation'),('measuredlengthfamily','describedsituationcutfunctionreference',profile.FAMILY)]:
        add(old,sort,call(voc._symbols[kind],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')))
    doc['declarations'].append(definition(n['zha'],[('va','situation')],profile.CUT,dict(kind='apply',function=k('measuredlengthfamily'),arguments=[v('va')])))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()[role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown transverse symmetry reference')
    return 'zhm' if old=='zg2' else 'zhk'


def role_definitions():
    n=names();m=mapping();k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    quant=lambda kind,name,sort,body:dict(kind=kind,variable=name,sort=sort,body=body)
    reverse=r('bf',r('bb',author.num(0)),k('zb7'))
    setting=op('and',op('not',op('equal',v('va'),k('zb6'))),quant('exists','vc',profile.CUT,r('ejdg',v('va'),reverse,v('vc'))))
    measured=r('ejcz',k('zgu'),k('zgv'),k('zgw'),k('ra'),v('vc'),v('vd'))
    same=r('sca',dict(kind='apply',function=v('va'),arguments=[v('vc')]),v('vd'))
    family=quant('forall','vc','situation',quant('forall','vd',profile.CUT,op('implies',measured,same)))
    return [definition(n['reversedrodsettingrole'],[('va','situation'),('vb','situation')],'truth',setting),
        definition(n['measuredlengthfamilyrole'],[('va',profile.FAMILY),('vb','situation')],'truth',family)]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][129:134],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==4,'Source selection changed')
    pieces=segments[0]['text'].split('. ')
    require(len(pieces)==4 and [s['text'] for s in segments[1:]]==['[M0186]','oder','[M0187].'],'Sentence boundary changed')
    texts=[s+'.' for s in pieces[:3]]+[' '.join([pieces[3],*[s['text'] for s in segments[1:]]])]
    require([len(s.split()) for s in texts]==[18,39,20,5] and texts[3].split()==['Hieraus','folgt:','[M0186]','oder','[M0187].'],'Token boundary changed')
    return dict(rule='Fixed whitespace tokens, punctuation retained; 1-based inclusive spans.',
        sentences={n:dict(position=list(SENTENCES[n]),tokens=text.split(),text=text) for n,text in zip(SENTENCES,texts,strict=True)},
        spans={n:list(p) for n,p in SPANS.items()},anchor='Paragraph52, page902. The final sentence includes the fraction equality, oder and phi equality with the period.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(101,105)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        entry=c.entries[old];decl=entry['declaration'];contract=profile.CONTRACTS[new]
        require(decl['parameters']==contract['parameters'] and decl['result']==contract['result'] and entry['arguments']==contract['arguments'] and entry['meaning_ja'].split('] ',1)[-1]==contract['meaning_ja'],'Source contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-transverse-symmetry-claim-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[154,155,156,157,158],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        new_public_relations=2,new_reference_primitives=1,
        semantic_review=SEMANTIC_REVIEW,profile_edition=57,core_edition=12,new_source_assertions=5,total_source_assertions=103,total_annotations=31,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible transverse-symmetry-claim document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|dict(zg2='other')
SITUATIONS=previous.SITUATIONS+('other',)


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values[n],count) for n,count in zip(SENTENCES,(18,39,20,5),strict=True)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def reference_models(values):
    key=lambda old:(values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=reference_roles()[old])),values['ri'])
    settings=SettingReferences({key('zg2'):values['zg2']})
    families=profile.SituationCutFunctionReferences({key('measuredlengthfamily'):values['measuredlengthfamily']} if 'measuredlengthfamily' in values else {})
    return settings,families


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
    def setting(document,node,role,context):
        if node==values['zhm']:return reference_models(values)[0].described(document,node,role,context)
        return result['describedsettingreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedsettingreference=setting)|reference_models(values)[1].handlers()


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def source_pins(*,include_outputs=True):
    prior_path='reports/einstein-transverse-endpoint-claim-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/visible_vocabulary_session.py','tests/test_visible_vocabulary_session.py',
        'scripts/transverse_symmetry_claim_visible_profile.py','scripts/check_einstein_transverse_symmetry_claim_visible.py',
        'scripts/visible_transverse_symmetry_claim_visible_collection.py','tests/test_transverse_symmetry_claim_visible.py','docs/einstein-transverse-symmetry-claim-visible-v1.md',
        'scripts/check_transverse_symmetry_claim.py','scripts/compose_transverse_symmetry_claim.py',
        'scripts/check_transverse_measured_length.py','scripts/compose_transverse_measured_length.py','reports/transverse-measured-length-v1.json','examples/v014/transverse-measured-length-core.noema',
        'scripts/check_transverse_comparison_scope.py','scripts/compose_transverse_comparison_scope.py','reports/transverse-comparison-scope-v1.json','examples/v014/transverse-comparison-scope-core.noema',
        'scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py',
        'scripts/check_clock_site_time.py','scripts/check_moving_trip_geometry.py','scripts/check_first_principle.py','scripts/check_material_relative_frame.py','scripts/check_four_coordinate_claim.py','examples/v014/transverse-symmetry-claim-core.noema','reports/transverse-symmetry-claim-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:author.digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved transverse-symmetry-claim bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    return dict(schema='noema-einstein-transverse-symmetry-claim-visible-evidence-1',core_words=375,profile_words=801,profile_edition=57,
        new_public_relations=2,new_reference_primitives=1,new_source_assertions=5,total_source_assertions=103,annotations=31,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256=source_pins(),artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
