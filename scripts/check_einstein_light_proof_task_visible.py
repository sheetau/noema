"""Connect the light-law proof task, prior adoption and scoped proof gap."""
from copy import deepcopy
from functools import lru_cache
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
from scripts import light_proof_task_visible_profile as profile
from scripts.light_proof_task_visible_profile import ROOT,LightProofTaskVisibleVocabulary,write_once
from scripts import check_einstein_origin_constants_visible as previous
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

SOURCE='examples/v016/einstein-light-proof-task-visible-v1.noema'
BRIDGE='data/einstein-light-proof-task-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-light-proof-task-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=['sqh', 'sqi', 'eif5', 'ei7v', 'ei7w', 'ei7x', 'ei7y', 'ei7z', 'ei72']
SENTENCES=dict(lightprooftasksentence=(44,1))
SPANS=dict(zfz=('lightprooftasksentence',1,30),zfy=('lightprooftasksentence',31,51))
ROLE_ASSIGNMENTS=dict(zfx='stage')
FORWARD_MAPS={}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,'lightproofstagerole']
READINGS=('data/einstein-light-proof-task-source-reading-v1.json',)
REVIEWS=('data/einstein-light-proof-task-u0086-review-v1.json',)
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0086の一文全体とM0140を原刊900–901頁へ照合する。Wir haben nun zu beweisenは、この論述段階でこれから示す数学的・物理的課題の提示と読む。著者の一人称複数に読者全員の参加や人数を加えない。',
 'jeder '
 'Lichtstrahlは、先行の真空光伝播の全適用区間を意味する。現在のei43は完全・非空な全区間、各系の同期時計・局所表示・幾何学的光路長を保持し、特定の縦光線や球面波上の標本だけに狭めない。両系へ同じV=tcを渡し、距離と時間の個別の数値一致は要求しない。',
 'fallsの前件はKでの同じ速度法則、後件はkで測った同じ速度法則。条件内容を課題として引用し、両法則の現実の成立や四式からの導出済みとはしない。現在の測定規約によるei43を使い、旧sbc/smwの固定時計を流用しない。',
 'wie wir angenommen '
 'habenは、先行wuでの同じeifyの仮定採用への振り返りとして読む。eifyの系別のeifxを現在の時計条件と結ぶei43がこの箇所の前件であり、一般原理の採用を前件の実証と同一視しない。採用の範囲wvと、現在の課題を述べる第三節eismsを区別する。',
 'noch nicht '
 'geliefertはこの段階zfxまでの論説eirfでの証明未提示。既存zfr/sqiの提示関係を用い、現在の第三節内だけを探索して先行節の証明を見落とすことはしない。段階と対象内容を固定し、別の対象・著者・論説・後の段階の提示は該当しない。',
 '両立性は既存eif5により、同じ意味を保つ一つの許容設定で既出eifjとeifyが共に成り立つ余地と読む。原理ごとに別の設定を使うこと、現在点での両法則の真理、一般の証明認定とは区別する。',
 'dennは両立性の証明未提示を、現在の課題を行う理由として著者が挙げる関係zgbへ結ぶ。この理由の提示を論理的十分性の証明にはしない。未提示の内容と光速度保存の課題は異なる引用対象として保持する。',
 '次の球面波の放出設定と計算、両立性が示されたという結論は後続u0087–u0091の範囲。今回の課題提示からそれらの達成やφの決定を先取りしない。有限検査は結合と範囲の検査であり、一般物理的導出や意味同値の自動証明ではない。',
 '第44段落第一文51トークンのうち、課題と条件を1–30、dennからの証明未提示の理由を31–51として指す。セミコロンと改頁で一文を分断しない。',
 '段階zfxは、指定課題を候補段階で提示する閉じた役割と課題箇所zfzによる既存describedsettingreferenceで照合する。取得は役割や引用した物理法則を実行せず、先行zfmへ別名を与えたものではない。',
 '既存の合成定義9個と意味規約4個を再利用する。新参照型は0個、共通375語、任意51版786語。仮定採用の理由と証明課題を行う理由は同じ型でも意味が異なるので同一視しない。']


@lru_cache(maxsize=1)
def vocabulary():return LightProofTaskVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][140:141]):visit(n)
    require(len(seen)==181,'Light-proof-task source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][140:141])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone','aki',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


@lru_cache(maxsize=1)
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


def reference_roles():return {'zfx':names()['lightproofstagerole']}


def reference_anchor(old):
    require(old=='zfx','Unknown proof-task stage reference');return 'zfz'


def role_definitions():
    n=names();m=mapping();voc=vocabulary();k=lambda old:call(n[old])
    role=definition(n['lightproofstagerole'],[('va','situation'),('vb','situation')],'truth',
        call(m['zga'],k('zfz'),k('rd'),dict(kind='quote',body=call(m['ei7v'])),v('va'),k('eisms'),v('vb')))
    reference=definition(n['zfx'],[],'situation',call(voc._symbols['describedsettingreference'],
        k('eirf'),k('zfz'),qf(n['lightproofstagerole']),k('ri')))
    return [role,reference]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4',*previous.FORWARD_MAPS,*FORWARD_MAPS}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][110:111],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==1,'Source selection changed')
    text=segments[0]['text'];tokens=text.split()
    require(len(tokens)==51 and tokens[:5]==['Wir','haben','nun','zu','beweisen,'],'Proof task opening changed')
    require(tokens[29:32]==['ist;','denn','wir'] and tokens[-2:]==['vereinbar','sei.'],'Conditional or reason boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; mathematical placeholders retained; 1-based inclusive positions.',
        sentences={'lightprooftasksentence':dict(position=[44,1],tokens=tokens,text=text)},
        spans={n:list(p) for n,p in SPANS.items()},
        anchor='One sentence across pages 900 and 901, with a conditional task and its stated reason.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(86,87)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-light-proof-task-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[140],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),forwarded_reference_signatures={d['name']:d for d in source_excerpt()['declarations'] if d['name'] in FORWARD_MAPS},
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=51,core_edition=12,new_source_assertions=1,total_source_assertions=85,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=4)
    require(result['document']==document(),'Visible light-proof-task document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|dict(zfx='lightprooftaskstage')
SITUATIONS=tuple(dict.fromkeys([*previous.SITUATIONS,'lightprooftaskstage']))


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['lightprooftasksentence'],51)]},
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
    key=(values['eirf'],values['zfz'],canonical(dict(kind='function_ref',symbol=reference_roles()['zfx'])),values['ri'])
    settings=SettingReferences({key:values['zfx']})
    def setting(document,node,role,context):
        if node==values['zfz']:return settings.described(document,node,role,context)
        return result['describedsettingreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedsettingreference=setting)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=4,payload=768):
        for page in volume['pages']:
            count+=1;write_once(OUT/('page-'+str(count).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved light-proof-task bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-origin-constants-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/visible_parallel_collection.py','scripts/visible_parallel_render.py',
        'scripts/light_proof_task_visible_profile.py','scripts/check_einstein_light_proof_task_visible.py',
        'scripts/visible_light_proof_task_visible_collection.py','tests/test_light_proof_task_visible_profile.py','docs/einstein-light-proof-task-visible-v1.md',
        'scripts/check_light_proof_task.py','scripts/compose_light_proof_task.py',
        'scripts/check_frame_light_law.py','examples/v014/light-proof-task-core.noema',
        'reports/light-proof-task-v1.json'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-light-proof-task-visible-evidence-1',core_words=375,profile_words=786,profile_edition=51,
        new_public_relations=4,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=85,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
