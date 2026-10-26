"""Connect motion adoption, definite axis states and scoped symmetry permission."""
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
from scripts import parallel_choice_visible_profile as profile
from scripts.parallel_choice_visible_profile import ROOT,ParallelChoiceVisibleVocabulary,write_once
from scripts import check_einstein_standard_configuration_visible as previous
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

SOURCE='examples/v016/einstein-parallel-choice-visible-v1.noema'
BRIDGE='data/einstein-parallel-choice-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-parallel-choice-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiv2 eiv3 eiv4 eiv5 eiv6 eiv7 eivu eivv eivw eivx eivy eivz eiw2 eiw3 eiwa eiwb eiwc eiwd eiwe eiwf eiwg eiwh eiwi eiwj eiwk eiwl eiwm eiwn eiwo eiwp eiwq eiwr eiws eiwt eiwu eiwv eiww eiwx eiwy eiwz sfi sfj sfs sfu'.split()
SENTENCES=dict(zcg=(29,1),zco=(29,2))
SPANS=dict(zcp=('zco',24,60),zcq=('zco',21,22))
DESIGNATIONS=dict(eisna=('zcg',1),eisnb=('zcg',2),eism5=('zco',1))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*SPANS,*DESIGNATIONS,'zb6','zb7','zcj','motionsettingrole','motionspeedrole','motionhistoryrole']
READINGS=('data/einstein-parallel-choice-source-reading-v1.json',)
REVIEWS=('data/einstein-parallel-choice-review-v1.json',)
FORMS=dict(eism5='t',eisna='k',eisnb='K')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return ParallelChoiceVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][104:106]):visit(n)
    require(len(seen)==175,'Parallel choice source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][104:106])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(SPANS)|set(DESIGNATIONS)|{'zcj'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','birdone',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def qf(name):return dict(kind='quote',body=dict(kind='function_ref',symbol=names()[name]))


def role_definitions():
    m=mapping();n=names();k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    x=v('va');setting=r('eivx',x)
    speed=allof(r('ba',x),r('bg',r('bb',author.num(0)),x),r('sca',x,r('zbi',k('ra'),k('zbm'),k('ta'),k('rb'),k('zb6'))))
    history=allof(r('zch',x,k('zb6')),op('equal',r('zci',x),k('zb6')))
    return [definition(n[name],[('va',sort),('vb','situation')],'truth',body)
        for name,sort,body in [('motionsettingrole','situation',setting),('motionspeedrole',profile.CUT,speed),('motionhistoryrole','individual',history)]]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    for old,(node,start,end) in SPANS.items():add(old,'individual',call(voc._symbols['sentencetokenspanreference'],k('eirf'),k(node),author.num(start),k(node),author.num(end),k('ri')))
    for old,(node,index) in DESIGNATIONS.items():add(old,'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(index),k('ri')))
    doc['declarations']+=role_definitions()
    for old,node,role,primitive,result in [('zb6','zcg','motionsettingrole','describedsettingreference','situation'),('zb7','zcg','motionspeedrole','describedcutreference',profile.CUT),('zcj','zco','motionhistoryrole','describedreference','individual')]:
        add(old,result,call(voc._symbols[primitive],k('eirf'),k(node),qf(role),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,text in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(text),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][64:66],inverse);return normalize_document(result)



@lru_cache(maxsize=1)
def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def text_boundaries():
    text=author.read(READINGS[0])['segments'][0]['text'];first,second=text.split(' Jeder Zeit ',1)
    tokens={'zcg':first.split(),'zco':('Jeder Zeit '+second).split()}
    require(tuple(map(len,tokens.values()))==(39,60),'Sentence token boundary changed')
    require(tokens['zco'][20:22]==['aus','Symmetriegründen'] and tokens['zco'][23]=='anzunehmen,' and tokens['zco'][-1]=='seien.','Scoped clause boundary changed')
    return dict(rule='Whitespace-delimited transcription; math placeholders are atomic; attached punctuation stays attached; 1-based inclusive positions.',
        sentences={n:dict(position=list(SENTENCES[n]),tokens=ts) for n,ts in tokens.items()},spans={n:list(pos) for n,pos in SPANS.items()},
        second_sentence_anchor='The whole second sentence is anchored at its opening definite-placement clause; adoption and reason have separately scoped spans.')


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0]);row=reading['segments'][0];unit=units[row['unit']]
    require(len(reading['segments'])==1 and row['unit']=='einstein-1905:u0044','Source boundary changed')
    require(row['range']==[0,len(unit['text'])] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'],'Original reading differs')
    review=author.read(REVIEWS[0]);require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-parallel-choice-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[104,105],source_units={row['unit']:dict(sha256=unit['text_sha256'],text=unit['text'],range=row['range'])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_coordinates={n:list(pos) for n,pos in SENTENCES.items()},text_boundaries=text_boundaries(),math=row['math'],annotations=annotations()['entries'],semantic_review=[
            '原刊897頁u0044の二文全687文字526非空白文字を保持。第一文は運動付与の採用指示、第二文は定まった配置・対称性による採用許容・tの使用規則の主張。第二文全体の帰属箇所zcoを冒頭の配置記述に固定し、仮定句zcpは24–60、理由句zcqは21–22トークンへ別に結ぶ。',
            '同じ初期の系・原点・全軸・物差し・全時計群を後の設定へ引き継ぐeivxを候補設定の役割とする。速度を役割へ戻さず参照循環を避ける。速度は同じ系順・単位・後の設定で正の符号付きX速度と一致するCUT。選択履歴は同じ運動問題に属しその設定がzb6である候補。参照取得は役割を実行せず存在・唯一性・真理を主張しない。',
            '全物質点の運動と原点・時計の代表位置の全期間の正のX方向等速並進を区別して保持する。端点だけに縮めず、加速機構・時計同期・運動前後の測定値一致を加えない。',
            '動く軸の直線性・原点世界線との一致・各時刻の平行直交を保持する。三組の対応軸の全期間の平行は逆方向と異なる原点を許し、初期のX支持線一致を運動中の横ずれ禁止へ転用しない。',
            '各静止系時刻に全原点・軸物質点の座標を持つ断面が存在し、座標上同値な断面まで一意であることを保持する。同じ座標を持つ別記録を許す。全実数時刻の被覆を有限標本から認定しない。',
            '静止基準の同じ初期原点・全軸の静止条件を動く系へ混入しない。選択済み履歴の配置確定と、全期間平行を満たす一つの許容候補の存在を分ける。時刻ごとに別候補を選ばない。',
            '空間的対称操作の物理的分類、非空領域・逆写像・許容性保存を保持する。それだけで平行候補の存在や推論の十分性を証明しない。著者の採用許容と理由提示は引用された採用行為・対称性の真理を実行しない。',
            'k/Kの呼称導入と、tが常に静止系時刻を指す全作品範囲の使用規則を保持する。tの一例・本文のみへ縮めず、移動時計時刻に替えない。括弧の説明・先行仮定からの帰結提示・著者帰属・順序を保持する。',
            '旧意味判断の逆投影、有限境界診断、円文字復号、全頁表示、独立した人の読解は別の検証である。'],
        profile_edition=37,core_edition=12,new_source_assertions=2,total_source_assertions=50,total_annotations=19,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible parallel choice document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*SPANS,*DESIGNATIONS,'zb6','zcj')}
SITUATIONS=(*previous.SITUATIONS,BASE['zb6'])


def role_key(values,node,role):return (values['eirf'],values[node],canonical(dict(kind='function_ref',symbol=names()[role])),values['ri'])
def reference_model(values):return TemporalReferences({role_key(values,'zco','motionhistoryrole'):values['zcj']},{})
def setting_model(values):return SettingReferences({role_key(values,'zcg','motionsettingrole'):values['zb6']})
def cut_model(values):return CutReferences({role_key(values,'zcg','motionspeedrole'):values['zb7']})
def token_model(values):
    return TokenSpanReferences({(values['eirf'],values['ri']):[(values['zcg'],39),(values['zco'],60)]},
        {(values['eirf'],values[node],start,values[node],end,values['ri']):values[old] for old,(node,start,end) in SPANS.items()})


def context_handlers(values):
    from scripts.text_reference_profile import TextPresentation
    result=previous.context_handlers(values)
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else result['sentencereference'](context,paragraph,item)
    def designation(document,node,item,context):
        key=(document,node,TextPresentation.coordinate(item),context)
        rows={(values['eirf'],values[n],i,values['ri']):values[old] for old,(n,i) in DESIGNATIONS.items()}
        return rows[key] if key in rows else result['designationreference'](document,node,item,context)
    def span(document,first,start,last,end,context):
        if first in {values[n] for n in SENTENCES} or last in {values[n] for n in SENTENCES}:return token_model(values).span(document,first,start,last,end,context)
        return result['sentencetokenspanreference'](document,first,start,last,end,context)
    def described(document,node,role,context):
        if node==values['zco']:return reference_model(values).described(document,node,role,context)
        return result['describedreference'](document,node,role,context)
    def setting(document,node,role,context):
        if node==values['zcg']:return setting_model(values).described(document,node,role,context)
        return result['describedsettingreference'](document,node,role,context)
    def cut(document,node,role,context):
        if node==values['zcg']:return cut_model(values).described(document,node,role,context)
        return result['describedcutreference'](document,node,role,context)
    return result|dict(sentencereference=sentence,designationreference=designation,sentencetokenspanreference=span,
        describedreference=described,describedsettingreference=setting,describedcutreference=cut)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved parallel choice bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-standard-configuration-visible-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/parallel_choice_visible_profile.py','scripts/parallel_choice_visible_profile_contracts.py','scripts/check_einstein_parallel_choice_visible.py',
        'scripts/visible_parallel_choice_visible_collection.py','tests/test_parallel_choice_visible_profile.py','docs/einstein-parallel-choice-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-parallel-choice-visible-evidence-1',core_words=375,profile_words=736,profile_edition=37,
        preserved_source_relations=17,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=50,annotations=19,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
