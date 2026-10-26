"""Connect the same axial light roundtrip, midpoint and expanded time arguments."""
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
from scripts import axial_expansion_visible_profile as profile
from scripts.axial_expansion_visible_profile import ROOT,AxialExpansionVisibleVocabulary,write_once
from scripts import check_einstein_auxiliary_time_visible as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts import check_einstein_two_principles as principles
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-axial-expansion-visible-v1.noema'
BRIDGE='data/einstein-axial-expansion-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-axial-expansion-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='ei2a ei2b ei2c ei2d ei2e ei2f ei2g ei2h ei2i ei2j ei2k ei2l ei2m ei2n ei2o ei2p ei2q ei2r ei2s ei2t ei2u eiz5 eiz6 eiz7 sit sjf sjg sjh sji sjk'.split()
SENTENCES=dict(zdu=(34,1))
SPANS=dict(zdv=('zdu',34,38),zd2=('zdu',39,60))
ROLE_ASSIGNMENTS=dict(zdq='trial',zdr='firstclock',zds='secondclock',zdt='reflectioncut',zdx='outsegment',zdy='backsegment',zd4='timefunction')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*['axialrole'+n for n in ROLE_ASSIGNMENTS.values()]]
READINGS=('data/einstein-axial-time-condition-source-reading-v1.json','data/einstein-light-time-expansion-source-reading-v1.json')
REVIEWS=tuple('data/einstein-axial-time-condition-u00'+n+'-review-v1.json' for n in ('49','50'))+tuple('data/einstein-light-time-expansion-u00'+n+'-review-v1.json' for n in ('51','52','53'))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0049全245文字・167本文文字と、数式だけのu0050（M0098）を一つの文と表示式として扱う。出発、軸方向、反射地点、反射と帰着の読取り、同じ原点への復帰、so muß dann '
 'seinの必要性と中点式を保持する。',
 'werde gesandt・reflektiert・anlangeは仮想設定の導入である。前段の同期したk時計を使う同じ設定として読む。物理的な発射命令、実験済みや一般的な光速の導出へ置き換えない。',
 '原刊の大文字Xは、この設定の共通の縦方向を指すと読む。既出の初期X支持線一致・同じ正X並進・全時点で対応軸が平行というeixtの設定を保持し、光の全往復経路をk原点から出る同じ縦軸の支持線へ結ぶ。単なる二端の配置や任意の平行な別線だけへ弱めない。両原点の一致や正方向一致を別途追加しない。',
 'x′は反射地点の補助座標値x-vtで、ξや静止系時刻tを意味しない。現在の同じ出来事のK四座標へ結ぶ。この文では原点の補助値を零に固定せず、反射値の符号や零でないことも数値の原点とは独立に補わない。非退化性は異なる両端と三出来事、厳密な時刻順序で保つ。',
 '旧siwの0,x′,0およびy=z=0は使わない。後続u0051–u0053で出る零座標の規約はそこで確認する。一般的な軸方向の往復に、まだ指定されていない座標原点の選択を先取りしない。',
 'τ₀,τ₁,τ₂は同じ試行の出発・反射・帰着でのk局所時計の値である。出発と帰着は同じ時計・同じ原点、反射は別の静止した配備時計へ結ぶ。全時計の自系静止・校正・共通参照・全対全試行の同期と、選択試行がその範囲に含まれることを保持する。',
 '中点式は既存sitで有効な三実数切断の和の半分と反射値の等値を表す。二つの差が等しいという同期規約からの読みを保ち、近似一致、切断の関数個体同一性、三数の大小を等式だけから導くこととは分ける。',
 'u0049末尾とu0050は同じ条件付き結論に属し、同じ主張選択を共有して判断する。著者の必要性の提示、有限の接続検査・有理数代数、全実数上の物理的導出、原文全体の意味判断を区別する。具体的なτ変換式は未導出である。',
 'u0051全142文字・116本文文字と、数式だけのu0052 M0100・u0053 '
 'M0101を一つの文と表示式として扱う。oder、τの四引数を付すこと、静止系の光速度原理の適用、左辺の半和と右辺を保持する。',
 '表示式に現れる0,x′,0およびy=z=0を、この縦方向の試行で採る座標規約として明示する。k原点の補助座標x-vtが零となるよう原点を選ぶ読みであり、両原点が全時刻で一致すること、出発時刻t=0、t=τ、x′=ξは追加しない。先行u0049では未指定だった零を遡及して強制しない。',
 '正の縦方向へ進む非退化な往復としてx′>0、既出v>0、v<Vを保つ。二分母V-vとV+vは正となり、二つの商を正の経過時間と解釈する。負の補助座標を許す先行の抽象往復に、この向きの経過時間式を無条件に適用しない。',
 '各K四座標は同じ出来事の現在のeiyxから得る。zdzの取得だけで座標の有効性を認めず、同じ組のx,tからx-vtを作る。候補τは現在の全対応と全k時計指示へ結ぶeizzを満たすという前提の下で用い、具体形や解の発見済みは補わない。',
 'eitiで両端点の同じ等速履歴、往路・復路の完全な光の履歴、同じ三出来事での出会いと真空・反射を保持する。Kの出発位置は同じ座標組のxであり、数値零へ置き換えない。端点差だけから光の全経路を推定しない。',
 '全真空伝播区間と全部分区間に同じVを与える既存eiosを静止系で適用する。両選択区間をその範囲eiscdへ含め、光・放出元・出来事・校正・幾何学的弧長をeifw/eiorへ結ぶ。Kの局所時計をkの動く時計へ交換せず、現在の表示対応eiyg/eiyi/eiyjも保持する。',
 '三関数値はτ(0,0,0,t)、τ(x′,0,0,t+x′/(V-v))、τ(0,0,0,t+x′/(V-v)+x′/(V+v))である。中点式の左辺は第一と第三の半和、右辺は第二であり、反射・帰着や二分母を交換しない。同じ関数の同じ時点に値を結ぶ。',
 '書換えの帰属zd3は著者が同じ前提の下で同値な形として提示する関係である。全実数上の逆数の一般法則や現実の光速度原理の実証を、この通読判断が証明したとはしない。旧数値核・有理代数の証拠は保存する。u0054以降の無限小・微分や具体的τ変換式はまだ記述しない。',
 '原刊898頁の一続きの段落を再確認し、34段落の一文の冒頭・中点式の必要性・oder以下の書換えを、同じ本文の位置と範囲へ結んだ。収録単位を別段落にしない。',
 '30旧合成定義と3旧契約を保存する。試行・二時計・補助座標・二区間・四引数関数は本文の閉じた役割から参照し、役割の引用を実行しない。参照の取得は役割の真理・存在の証明・唯一性や解の発見を含意しない。',
 '四切断引数から切断値を返す関数の型付き参照だけを追加する。時刻関数候補の役割は既存のeizvの答え条件に合成し、一文や数式全体を原始語にしない。共通375語は不変。']


@lru_cache(maxsize=1)
def vocabulary():return AxialExpansionVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][113:116]):visit(n)
    require(len(seen)==359,'AxialExpansion source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][113:116])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|(set(ROLE_ASSIGNMENTS)-{'zdt','zd4'})
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','red',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    for old,role in reference_roles().items():
        relation,result=('describedcutreference',profile.CUT) if old=='zdt' else ('describedfourcutfunctionreference',profile.TAU) if old=='zd4' else ('describedreference','individual')
        add(old,result,call(voc._symbols[relation],k('eirf'),k(reference_anchor(old)),qf(role),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()['axialrole'+role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):return 'zd2' if old in ('zdx','zdy','zd4') else 'zdu'


def role_definitions():
    n=names();m=mapping();x=v('va');ctx=v('vb');k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    def exists(name,body):return dict(kind='exists',variable=name,sort='individual',body=body)
    trial=k('zdq');physical=k('zb6');first=r('qe',trial);middle=r('qf',trial);last=r('qg',trial);ray=r('qh',trial)
    bodies=dict(trial=exists('vc',exists('vd',r('ei2a',x,v('vc'),v('vd'),physical))),
        firstclock=exists('vc',r('ei2a',trial,x,v('vc'),physical)),
        secondclock=exists('vc',r('ei2a',trial,v('vc'),x,physical)),
        reflectioncut=r('eiz6',middle,x,physical),
        outsegment=r('ei2m',x,ray,first,middle,r('bf',r('sji',middle,physical),r('sji',first,physical)),physical),
        backsegment=r('ei2m',x,ray,middle,last,r('bf',r('sji',middle,physical),r('sji',last,physical)),physical),
        timefunction=dict(kind='answer_matches',question=k('eizv'),arguments=[x]))
    return [definition(n['axialrole'+role],[('va',profile.CUT if role=='reflectioncut' else profile.TAU if role=='timefunction' else 'individual'),('vb','situation')],'truth',body) for role,body in bodies.items()]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][83:86],inverse);return normalize_document(result)



def text_boundaries():
    segments=[s for path in READINGS for s in author.read(path)['segments']]
    text=' '.join(s['text'] for s in segments);tokens=text.split()
    require(len(tokens)==60 and tokens[11]=='[M0093]längs','Fixed transcription token boundary changed')
    require(tokens[33:38]==['so','muß','dann','sein:','[M0098]'],'Midpoint boundary changed')
    require(tokens[38]=='oder,' and tokens[-2:]==['[M0100]','[M0101]'],'Expansion boundary changed')
    require([m['id'] for s in segments for m in s['math']]==['M'+str(i).zfill(4) for i in range(92,102)],'Math boundaries changed')
    return dict(rule='Whitespace-delimited fixed transcription; punctuation remains attached; 1-based inclusive positions. The joined placeholder [M0093]längs is one transcription token.',
        sentences={'zdu':dict(position=[34,1],tokens=tokens,text=text)},spans={n:list(p) for n,p in SPANS.items()},
        anchor='One continuous paragraph and sentence, from Vom through the final displayed equation. Source extraction units do not create new paragraphs.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(49,54)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-axial-expansion-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[113,114,115],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=42,core_edition=12,new_source_assertions=3,total_source_assertions=60,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible axial_expansion document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS) if n not in ('zdt','zd4')}
SITUATIONS=previous.SITUATIONS

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['zdu'],60)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[n] for n,(node,start,end) in SPANS.items()})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def span(document,first,start,last,end,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:
            return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    roles=reference_roles()
    def key(old):return (values['eirf'],values[reference_anchor(old)],canonical(dict(kind='function_ref',symbol=roles[old])),values['ri'])
    individuals=TemporalReferences({key(old):values[old] for old in ROLE_ASSIGNMENTS if old not in ('zdt','zd4')},{})
    cuts=CutReferences({key('zdt'):values['zdt']} if 'zdt' in values else {})
    functions=profile.FourCutFunctionReferences({key('zd4'):values['zd4']} if 'zd4' in values else {})
    nodes={values[n] for n in (*SENTENCES,*SPANS)}
    def individual(doc,node,role,context):
        return individuals.described(doc,node,role,context) if node in nodes else result['describedreference'](doc,node,role,context)
    def cut(doc,node,role,context):
        return cuts.described(doc,node,role,context) if node in nodes else result['describedcutreference'](doc,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedreference=individual,describedcutreference=cut)|functions.handlers()


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved axial_expansion bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-auxiliary-time-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/axial_expansion_visible_profile.py','scripts/axial_expansion_visible_profile_contracts.py','scripts/check_einstein_axial_expansion_visible.py',
        'scripts/visible_axial_expansion_visible_collection.py','tests/test_axial_expansion_visible_profile.py','docs/einstein-axial-expansion-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-axial-expansion-visible-evidence-1',core_words=375,profile_words=757,profile_edition=42,
        preserved_source_relations=3,new_reference_primitives=1,new_source_assertions=3,total_source_assertions=60,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
