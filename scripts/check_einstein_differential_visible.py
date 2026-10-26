"""Connect the same time candidate to a local limit and two derivative equations."""
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
from scripts import check_einstein_axial_expansion_visible as previous
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

SOURCE='examples/v016/einstein-differential-visible-v1.noema'
BRIDGE='data/einstein-differential-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-differential-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS
NEW_DEFINITIONS='ei22 ei23 ei24 ei25 ei2v ei2w ei2x ei2y ei2z sjv sjw sjx sjy skc skf skg'.split()
SENTENCES=dict(zea=(35,1))
SPANS=dict(zeb=('zea',10,11))
ROLE_ASSIGNMENTS=dict(zd5='radius',zd6='spacepartial',zd7='timepartial')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,*['differentialrole'+n for n in ROLE_ASSIGNMENTS.values()]]
READINGS=('data/einstein-differential-step-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-differential-step-u00'+str(n)+'-review-v1.json' for n in range(54,58))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0054全54文字・40本文文字、u0055 M0103、u0056 oderの4文字、u0057 M0104を一組として読む。原刊899頁の冒頭、x′の無限小への移行、二偏微分の関係、同じ式の整理を保持する。',
 '無限小は新たな非アルキメデス数ではなく、正の変位hを0へ近づける通常の実数の極限として読む。ある正の半径の内側の全ての0<h<radiusで同じ中点式を課す。固定された一回の反射距離だけや零変位の恒等式で済ませない。',
 '同じ候補τ、光速V、速度v、実際の出発K時刻tを先行ei2pへ接続する。微分点は(0,0,0,t)であり、tを零に固定せず、x′とt以外の二座標を固定する。原点以外への一般化はu0058で扱う。',
 '全微分可能性sjvのε–δ条件とsjwの二切片の差商極限を同じ係数に結ぶ。独立した偏微分の存在だけから全微分可能性を導かない。先行u0047の線形性の主張と整合する十分な正則性を明示した読みであり、同じ座標対応がアフィンであることから局所延長の性質を自動導出したとはしない。',
 'M0103は½(1/(V-v)+1/(V+v))*τt=τx′+τt/(V-v)、M0104はτx′+v/(V²-v²)*τt=0である。既存sjx/sjyとskf/skgを変更せず、両式で同じ候補偏微分zd6,zd7を使う。正速度とv<Vを保ち、分母を零にしない。',
 '原文のHieraus '
 'folgtは同じ中点式と極限の読みからの帰結の提示、oderはその式の同値な書換えとして記述する。著者・論説・第三節・順序を保持し、具体的なτ解の発見、無条件の物理事実、処理系の証明済み判断へ替えない。',
 '旧逆数・極限・有理代数の定義と証拠を保存する。有限の差分例は切片・引数・係数を区別する検査に限り、全実数の近傍、全微分可能性、連鎖律を有限標本で認定しない。新規原始語は追加しない。',
 '原刊899頁を再表示し、Hierausから二つの式とoderを経て最後の句点まで一文であると確認した。zeaは第35段落第一文、zebはその10–11トークンである。後続の任意の出発点への一般化は含めない。',
 '16旧合成定義を保存する。近傍半径と二偏微分候補は、それぞれ近傍の中点条件、空間切片の微分、時間切片の微分という閉じた役割から切断参照する。二偏微分の参照は互いの定数に依存せず、同じτ候補と実際の出発K時刻を保持する。',
 '新規の公開語彙・原始語を追加しない。既存の任意42版757語と共通375語を使い、参照取得から極限の成立や存在・唯一性を導かない。有限診断と全実数上の条件を区別する。']


@lru_cache(maxsize=1)
def vocabulary():return previous.vocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][116:118]):visit(n)
    require(len(seen)==369,'Differential source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][116:118])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','bird',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    doc['declarations']+=role_definitions()
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    for old,role in reference_roles().items():
        add(old,profile.CUT,call(voc._symbols['describedcutreference'],k('eirf'),k('zea'),qf(role),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def reference_roles():return {old:names()['differentialrole'+role] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown differential reference');return 'zea'


def role_definitions():
    n=names();m=mapping();x=v('va');k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    zero=r('bb',author.num(0));time=r('sjh',r('qe',k('zdq')),k('zb6'))
    def slice(axis):
        args=[zero,zero,zero,time];args[axis]=v('vc')
        return dict(kind='lambda',parameters=[dict(name='vc',sort=profile.CUT)],body=dict(kind='apply',function=k('zd4'),arguments=args))
    domain=dict(kind='function_ref',symbol=m['ba'])
    bodies=dict(radius=r('skc',k('zd4'),k('tc'),k('zb7'),time,x),
        spacepartial=r('sjs',domain,slice(0),zero,x),
        timepartial=r('sjs',domain,slice(3),time,x))
    return [definition(n['differentialrole'+role],[('va',profile.CUT),('vb','situation')],'truth',body) for role,body in bodies.items()]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][86:88],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];text=' '.join(s['text'] for s in segments);tokens=text.split()
    require(tokens==['Hieraus','folgt,','wenn','man','[M0102]','unendlich','klein','wählt:','[M0103]','oder','[M0104]'],'Fixed transcription boundary changed')
    require([m['id'] for s in segments for m in s['math']]==['M0102','M0103','M0104'],'Math boundaries changed')
    return dict(rule='Whitespace-delimited fixed transcription; punctuation attached; 1-based inclusive positions.',
        sentences={'zea':dict(position=[35,1],tokens=tokens,text=text)},spans={'zeb':['zea',10,11]},
        anchor='One sentence from Hieraus through the two displayed equations and final period. The following arbitrary-start claim begins a new paragraph.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(54,58)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-differential-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[116,117],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=42,core_edition=12,new_source_assertions=2,total_source_assertions=62,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible differential document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}
SITUATIONS=previous.SITUATIONS

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['zea'],11)]},
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
    def key(old):return (values['eirf'],values['zea'],canonical(dict(kind='function_ref',symbol=roles[old])),values['ri'])
    cuts=CutReferences({key(old):values[old] for old in ROLE_ASSIGNMENTS if old in values})
    nodes={values[n] for n in (*SENTENCES,*SPANS)}
    def cut(doc,node,role,context):
        return cuts.described(doc,node,role,context) if node in nodes else result['describedcutreference'](doc,node,role,context)
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedcutreference=cut)



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved differential bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-axial-expansion-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/check_einstein_differential_visible.py',
        'scripts/visible_axial_expansion_visible_collection.py','tests/test_differential_visible_profile.py','docs/einstein-differential-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-differential-visible-evidence-1',core_words=375,profile_words=757,profile_edition=42,
        new_public_relations=0,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=62,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
