"""Connect the affine time formula, unfixed coefficient and origin assumption."""
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
from scripts import affine_time_visible_profile as profile
from scripts.affine_time_visible_profile import ROOT,AffineTimeVisibleVocabulary,write_once
from scripts import check_einstein_transverse_visible as previous
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

SOURCE='examples/v016/einstein-affine-time-visible-v1.noema'
BRIDGE='data/einstein-affine-time-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-affine-time-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='sma smb smc smd sme smf smg smh smi smj smr smn sms smq smp ei4g ei4h ei4i ei4j ei4k ei4l ei4m ei4n ei4o ei4p ei4q ei4r ei4u ei4x ei4s ei4t ei4v ei4w ei4y ei4z'.split()
SENTENCES=dict(affinetimesentence=(38,1))
SPANS=dict(zeu=('affinetimesentence',1,11),zew=('affinetimesentence',12,19),zev=('affinetimesentence',20,34),affinecoefficientanchor=('affinetimesentence',18,18))
ROLE_ASSIGNMENTS=dict(zes='stage',zeq='coefficient',zer='family')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*ROLE_ASSIGNMENTS,'affinestagerole','affinecoefficientrole','affinefamilyrole']
READINGS=('data/einstein-affine-time-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-affine-time-u'+str(i).zfill(4)+'-review-v1.json' for i in range(62,65))
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=temporal.quote_function
SEMANTIC_REVIEW=['u0062–u0064を式の導入・表示式・係数と仮定の説明として接続する。原刊899頁の本文順序は帰結、未知係数、原点仮定であり、論理上の前提を定義した順序とは区別する。',
 'linearは先行の現在測定対応のアフィン性を引き継ぎ、同じ五係数を補助座標上の全実数へ延長する読みである。時間係数D+vAをφ(v)に結び、偏微分だけで定数Eを零にしない。',
 '同じτの四偏微分が同じアフィン係数であることをsmrで明示する。先行する全空間の縦横条件は同じ出発時刻で参照し、アフィン係数は全入力で一定とする。一般の微分の一意性と実数体の法則の自動証明ではない。',
 '原点条件ei4lの非空の時刻規約と別の空間ラベル選択を継承する。k原点でτ=0ならt=0を保ち、全時刻のt=τや全空間成分が零という時刻条件への追加にはしない。',
 'vorläufig '
 'unbekanntは現在の考察段階で異なる速度関数候補が残るという読みとする。現在のφも同じ許容速度域で候補族に結ぶ。唯一の解を知らないという知識一般や、全候補が後続の条件を満たすことまでは述べない。',
 '係数aは同じφの同じvでの値。1、符号、後段の係数へ固定しない。未測定の全実数入力が実際の出来事として存在することも要求しない。',
 '帰結zc、未決定内容uh、原点仮定ug、簡潔さzexは引用した内容の著者帰属であり、検査器がその物理的真理を証明したことにしない。文全体を置き換える物理の原始関係は追加しない。汎用の型付き参照二つは下記に示す。',
 '原刊899頁のAus diesen '
 'Gleichungenからsei.までを一文として接続する。全34token、第38段落第一文。式の帰結1–11、未知係数12–19、簡潔さと仮定20–34、φ(v)のanchor18を区別する。',
 '35旧合成定義と2旧関係を再利用する。係数関数と状況別の候補関数族には、型を明示した二つの汎用参照を用いる。本文の閉じた役割と同じ文書・箇所・提示文脈を照合する解釈入力であり、役割から任意の関数を選択したり具体式や唯一性を補ったりしない。',
 '考察段階は同じ主体がその段階自体を排除していないという役割へ結ぶ。関数の役割は同じ許容速度域で値が有効なこと、関数族の役割は同じ主体・段階の全候補状況での有効性を述べる。参照取得時にはこれらの全実数条件を実行しない。現在の関数と族の同じ速度域での一致・複数候補の差異は本文smpで別に要求する。',
 '共通375語、任意45版769語。有限の係数代入・束縛診断を全実数のアフィン性や一般物理的導出の証明としない。']


@lru_cache(maxsize=1)
def vocabulary():return AffineTimeVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][122:125]):visit(n)
    require(len(seen)==282,'Affine-time source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][122:125])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','treeone','treeone',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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


def reference_roles():return {old:names()['affine'+role+'role'] for old,role in ROLE_ASSIGNMENTS.items()}


def reference_anchor(old):
    require(old in ROLE_ASSIGNMENTS,'Unknown affine-time reference')
    return 'affinecoefficientanchor' if old=='zeq' else 'zew'


def role_definitions():
    n=names();m=mapping();voc=vocabulary();k=lambda old:call(n[old])
    zero=call(m['bb'],author.num(0))
    def domain(x):return allof(call(m['ba'],x),call(m['bc'],zero,x),call(m['bg'],x,k('tc')))
    def app(fn,*xs):return dict(kind='apply',function=fn,arguments=list(xs))
    def forall(name,sort,body):return dict(kind='forall',variable=name,sort=sort,body=body)
    def ref(old,sort,primitive):
        return definition(n[old],[],sort,call(voc._symbols[primitive],k('eirf'),k(reference_anchor(old)),qf(reference_roles()[old]),k('ri')))
    stage=definition(n['affinestagerole'],[('va','situation'),('vb','situation')],'truth',call(m['zet'],k('zee'),v('va'),v('va')))
    coefficient=definition(n['affinecoefficientrole'],[('va',profile.PHI),('vb','situation')],'truth',
        forall('vc',profile.CUT,op('implies',domain(v('vc')),call(m['ba'],app(v('va'),v('vc'))))))
    family=definition(n['affinefamilyrole'],[('va',profile.FAMILY),('vb','situation')],'truth',
        forall('vc','situation',op('implies',call(m['zet'],k('zee'),k('zes'),v('vc')),
            forall('vd',profile.CUT,op('implies',domain(v('vd')),call(m['ba'],app(app(v('va'),v('vc')),v('vd'))))))))
    return [stage,ref('zes','situation','describedsettingreference'),coefficient,family,
        ref('zeq',profile.PHI,'describedcutfunctionreference'),ref('zer',profile.FAMILY,'describedsituationcutfunctionfamilyreference')]


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][92:95],inverse);return normalize_document(result)



def text_boundaries():
    segments=author.read(READINGS[0])['segments'];require(len(segments)==3,'Source selection changed')
    text=' '.join(s['text'] for s in segments);tokens=text.split()
    require(len(tokens)==34 and tokens[:4]==['Aus','diesen','Gleichungen','folgt,'],'Fixed affine boundary changed')
    require(tokens[10:13]==['[M0112],','wobei','[M0113]'] and tokens[17]=='[M0114]','Coefficient boundary changed')
    require(tokens[19:24]==['und','der','Kürze','halber','angenommen'] and tokens[-1]=='sei.','Origin assumption boundary changed')
    return dict(rule='Whitespace-delimited fixed transcription; punctuation attached; 1-based inclusive positions.',
        sentences={'affinetimesentence':dict(position=[38,1],tokens=tokens,text=text)},spans={n:list(p) for n,p in SPANS.items()},
        anchor='One sentence containing the time formula, its unfixed coefficient and the brevity-motivated origin assumption.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={};math=[]
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']]
            require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
            sources[row['unit']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range']);math+=row['math']
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(62,65)},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-affine-time-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[122,123,124],source_units=sources,
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=math,
        reference_roles=reference_roles(),role_definitions=role_definitions(),
        reference_anchors={old:reference_anchor(old) for old in ROLE_ASSIGNMENTS},
        semantic_review=SEMANTIC_REVIEW,profile_edition=45,core_edition=12,new_source_assertions=3,total_source_assertions=69,total_annotations=26,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible affine-time document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS)}|{'zes':'affinestage'}
SITUATIONS=tuple(dict.fromkeys([*previous.SITUATIONS,'affinestage']))

def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['affinetimesentence'],34)]},
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
    settings=SettingReferences({key('zes'):values['zes']})
    nodes={values[x] for x in (*SENTENCES,*SPANS)}
    def setting(doc,node,role,context):
        return settings.described(doc,node,role,context) if node in nodes else result['describedsettingreference'](doc,node,role,context)
    functions={}
    for old,name in (('zeq','describedcutfunctionreference'),('zer','describedsituationcutfunctionfamilyreference')):
        functions.update(profile.TypedFunctionReferences(name,{key(old):values[old]} if old in values else {}).handlers())
    return result|dict(sentencereference=sentence,sentencetokenspanreference=span,describedsettingreference=setting)|functions



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved affine-time bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-transverse-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/affine_time_visible_profile.py','scripts/affine_time_visible_profile_contracts.py','scripts/check_einstein_affine_time_visible.py',
        'scripts/visible_affine_time_visible_collection.py','tests/test_affine_time_visible_profile.py','docs/einstein-affine-time-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-affine-time-visible-evidence-1',core_words=375,profile_words=769,profile_edition=45,
        new_public_relations=2,new_reference_primitives=2,new_source_assertions=3,total_source_assertions=69,annotations=26,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
