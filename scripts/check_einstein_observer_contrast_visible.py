"""Connect the length gloss and scoped observer contrast without changing its reading."""
from copy import deepcopy
from functools import lru_cache
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import observer_contrast_visible_profile as profile
from scripts.observer_contrast_visible_profile import ROOT,ObserverContrastVisibleVocabulary,TokenSpanReferences,write_once
from scripts import check_einstein_moving_trip_visible as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts import check_einstein_two_principles as principles
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-observer-contrast-visible-v1.noema'
BRIDGE='data/einstein-observer-contrast-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-observer-contrast-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eit2 eit3 eit4 eit5 eit6 eit7 eiua eiub eiuc eiud eiue eiuf eiug eiuh sdk sdm sdo'.split()
SENTENCES=dict(contrastsecond=(26,4))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,'zbb','eismn']
READINGS=('data/einstein-observer-contrast-source-reading-v1.json',)
REVIEWS=('data/einstein-observer-contrast-review-v1.json',)
FORMS=dict(eismn='r_AB')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return ObserverContrastVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][100:101]):visit(n)
    require(len(seen)==219,'Observer contrast source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][100:101])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|{'zbb','eismn'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','nao',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
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
    def add(old,result,body):doc['declarations'].append(dict(kind='definition',name=n[old],parameters=[],result=result,body=body))
    for old,pos in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),*[author.num(x) for x in pos]))
    add('zbb','individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k('za3'),author.num(15),k('contrastsecond'),author.num(28),k('ri')))
    add('eismn','individual',call(voc._symbols['designationreference'],k('eirf'),k('zbb'),author.num(1),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k('eismn'),author.text_expression('und'),author.text_expression('r_AB'),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][59:60],inverse);return normalize_document(result)


@lru_cache(maxsize=1)
def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    require(rows['eismn']==dict(symbol='eismn',role='designation',forms=[dict(text='r_AB',language='und',role='linearized_subscript_notation')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def text_boundaries():
    units={u['id'].split(':')[-1]:u['text'] for u in author.read(author.UNITS)['units']}
    lead=units['u0036'].split('Unter Berücksichtigung',1)[1]
    gloss,contrast=units['u0040'].split(' Mit dem ',1);contrast='Mit dem '+contrast
    prefix=' '.join(['Unter Berücksichtigung'+lead,units['u0037'],units['u0038'],units['u0039']])
    first=(prefix+' '+gloss).split();last=contrast.split()
    require((len(prefix.split())+1,len(first),len(last))==(15,28,28),'Source token boundaries changed')
    require(first[14]=='wobei' and first[15]=='[M0062]' and first[-1]=='bedeutet.' and last[0]=='Mit' and last[-1]=='würden.','Partial source boundary changed')
    return dict(rule='Whitespace-delimited transcription; each inline or displayed math placeholder is one atomic token; attached punctuation stays attached; isolated dashes are tokens; 1-based inclusive positions.',
        sentences={'za3':dict(position=[26,3],tokens=first),'contrastsecond':dict(position=[26,4],tokens=last)},
        span=dict(first_sentence='za3',first_token=15,last_sentence='contrastsecond',last_token=28),
        source_range=[0,len(units['u0040'])],starts_after_equation='einstein-1905:u0039',includes_whole_first_sentence=False)


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0]);row=reading['segments'][0];unit=units[row['unit']]
    require(len(reading['segments'])==1 and row['unit']=='einstein-1905:u0040','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-observer-contrast-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[100],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        text_boundaries=text_boundaries(),math=row['math'],annotations=annotations()['entries'],semantic_review=[
            '原刊897頁u0040全体。冒頭wobeiは前文と二式の続き、Mit demから同じ段落の次文。zbbは第三文15番目のトークンから第四文28番目のトークンまでであり、第三文全体でも別段落でもない。',
            'r_ABの呼称はこの部分範囲の最初の識別呼称。eit4は同じ棒xi・現在の静止系測定eip6・数量条件eiqg・同じ値zav・yxによる想定継承を結ぶ。初期長や光路全長を入れない。',
            'eit2は巨視的代表位置の全se履歴と同じ下端位置から零速度の全履歴を同じ対象へ結ぶ。端点だけの静止や身体内部全点の停止ではない。eit3の観測者・系・単位・区間を保持する。',
            '共動する同じ二人は同じ三記録の中点条件sdoについて明示的に否定と判断する。判定の適用と否定判断と数値的不成立は別であり、引用内容を実行しない。',
            '静止側は同じ想定でeit3を満たす非空の範囲。全員が両時計の全区間の局所静止系時刻一致eit6を肯定と判断し、その内容を宣言する。単なる判断へ発言を縮めず、現実の全人類へ量化しない。',
            'würdenは先行仮定範囲内の帰結を述べるuh、alsoは先行往復結果eitpを理由とするeisdk、währendは否定判断と肯定宣言の順序ある対照zbc。異なる基準を一命題の矛盾へ替えない。',
            'wobeiの補足、著者・文書・範囲・本文順序を保持する。本文順序は開始箇所の順序であり、文全体の参照za3とその後半から始まる部分範囲zbbが非重複だとは主張しない。',
            '全実数時刻の検査や心理法則の証明は行わない。有限診断・構文復号・既存意味判断・独立した人の読解を区別する。'],
        profile_edition=33,core_edition=12,new_source_assertions=1,total_source_assertions=45,total_annotations=16,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible observer contrast document differs');return result


BASE=previous.BASE|dict(contrastsecond='contrastsecond',zbb='zbb',eismn='eismn')
SITUATIONS=previous.SITUATIONS


def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['za3'],28),(values['contrastsecond'],28)]},
        {(values['eirf'],values['za3'],15,values['contrastsecond'],28,values['ri']):values['zbb']})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values);old_sentence=result['sentencereference'];old_designation=result['designationreference']
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return values['contrastsecond'] if key==(values['ri'],26,4) else old_sentence(context,paragraph,item)
    def designation(document,node,item,context):
        key=(document,node,TextPresentation.coordinate(item),context)
        if key==(values['eirf'],values['zbb'],1,values['ri']):return values['eismn']
        return old_designation(document,node,item,context)
    return result|token_model(values).handlers()|dict(sentencereference=sentence,designationreference=designation)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved observer contrast bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-moving-trip-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/observer_contrast_visible_profile.py','scripts/observer_contrast_visible_profile_contracts.py','scripts/check_einstein_observer_contrast_visible.py',
        'scripts/visible_observer_contrast_visible_collection.py','tests/test_observer_contrast_visible_profile.py','docs/einstein-observer-contrast-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-observer-contrast-visible-evidence-1',core_words=375,profile_words=699,profile_edition=33,
        preserved_source_relations=2,new_reference_primitives=1,new_source_assertions=1,total_source_assertions=45,annotations=16,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
