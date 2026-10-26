"""Connect the local-time proposal, reception alternative and forward comparison."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts import observer_time_profile as profile
from scripts.observer_time_profile import ROOT,ObserverTimeVocabulary,write_once
from scripts import check_einstein_temporal_discourse as previous
from scripts import check_einstein_name_presentation as author
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.shared_reference import definition
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-observer-time-v1.noema'
BRIDGE='data/einstein-observer-time-bridge-v1.json'
OUT=ROOT/'output/einstein-observer-time-v1'
LABEL=Word('proper',('above','book','give','book','fruit'))
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=('eij2 eij3 eij4 eij5 eij6 eij7 eijh eiji eijj eijk eijl eijm eijn eijo eijp eijq eijr eijs eijt eiju eijv eijw eijx eijy eijz eika eikb eikc eikd eike eikf eikg eikh eiki eikj eikk eikl eikm eikn eiko eikp eikq eikr eiks eikt eiku eikv eikw eikx qt qu').split()
SENTENCES=dict(eisgc=(7,1),eisgq=(7,2),eishg=(8,1),eishp=(8,2),eishs=(8,3),eish2=(9,1),rj=(13,2))
REFERENTS=('eisf5','eisf6','eisf7','eisga','eisgb','eisg7','eisha','eishb','eishc','eishd','eishe','eishf','eishq','eishr','eisht','rb')
ROLE_NAMES=('proposal','definitiontask','ownclock','hourhand','unit','scheme','observer','clock','displaypart','origin','valuationtask','convention','consideration','criterion')
ROLE_HELPERS=['role'+n for n in ROLE_NAMES]
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*REFERENTS,'rc',*ROLE_HELPERS]
READINGS=('data/einstein-clock-definition-source-reading-v1.json','data/einstein-reception-time-source-reading-v1.json')
REVIEWS=('data/einstein-clock-definition-paragraph-review-v1.json','data/einstein-reception-alternative-paragraph-review-v1.json')
qf=previous.quote_function


@lru_cache(maxsize=1)
def vocabulary():return ObserverTimeVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][65:70]):visit(n)
    require(len(seen)==182,'Observer-time closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][65:70])))


def names():
    n=previous.names();proper=set(SENTENCES)|set(REFERENTS)|{'rc'}
    for i,old in enumerate(LOCAL_NAMES):
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','book','fruit',previous.PARTS[i//16],previous.PARTS[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision')
    return n


def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:previous.authoring_vocabulary()._symbols[new] for old,new in previous.MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency')
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def role_definitions():
    n=names();m=mapping();x=v('va');s=v('vb');k=lambda old:call(n[old])
    relation=lambda old,*args:call(m[old],*args)
    bodies=dict(
        proposal=relation('eisfx',x,k('rd'),k('eisf6'),k('eisf7'),k('eisga'),k('ra'),k('eisgb'),k('eirf'),qf(n['eiji']),s),
        definitiontask=relation('eisfw',x,k('eirf'),s),
        ownclock=relation('eise6',x,k('rd'),s),hourhand=relation('eise7',x,k('eisf7'),s),unit=relation('ci',x),
        scheme=relation('eisg3',x,k('eishe'),k('eisha'),k('eishb'),k('eishc'),k('eishd'),k('ra'),k('eishf'),k('eirf'),qf(n['eikd']),s),
        observer=op('and',relation('eisgr',x,s),relation('cb',x,k('eishd'),k('ra'))),
        clock=op('and',relation('ca',x),relation('eisgf',x,k('eishd'),k('ra'),s)),
        displaypart=relation('eisgs',x,k('eishb'),s),origin=relation('zbv',k('ra'),x,s),
        valuationtask=relation('eisgg',x,k('eishb'),k('ra'),k('eishf'),k('eirf'),s),
        convention=relation('eishx',x,k('eishe'),qf(n['qu']),k('rj'),k('eirf'),s),
        consideration=relation('eishz',k('eishs'),k('rd'),x,k('eish2'),k('rj'),k('eirf'),s),
        criterion=dict(kind='exists',variable='vc',sort='individual',body=dict(kind='exists',variable='vd',sort='individual',body=op('and',
            relation('eishu',k('eishq'),k('eishe'),x,v('vc'),k('eirf'),s),relation('eishu',k('eisg7'),k('eishe'),x,v('vd'),k('eirf'),s)))))
    return [definition(n['role'+key],[('va','individual'),('vb','situation')],'truth',bodies[key]) for key in ROLE_NAMES]


def reference_roles():
    assignments=dict(eisf5='proposal',eisf6='definitiontask',eisf7='ownclock',eisga='hourhand',eisgb='unit',
        eisg7='scheme',eisha='observer',eishb='clock',eishc='displaypart',eishd='origin',eishe='valuationtask',eishf='unit',
        eishq='convention',eishr='consideration',eisht='criterion',rb='unit')
    return {old:names()['role'+role] for old,role in assignments.items()}


def reference_node(old):
    if old in ('eisf5','eisf6','eisf7','eisga','eisgb'):return 'eisgc'
    if old in ('eishq','eishr','eisht'):return 'eishs'
    return 'rj' if old=='rb' else 'eishg'


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping()
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],call(n['ri']),author.num(paragraph),author.num(sentence))))
    for old,role in reference_roles().items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],call(n['eirf']),call(n[reference_node(old)]),qf(role),call(n['ri']))))
    doc['declarations'].append(definition(n['rc'],[],'individual',call(voc._symbols['referenceclock'],call(n['ra']),call(n['ri']))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/previous.MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in previous.FIELDS or d['name']=='zz4') else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][11:],inverse);return normalize_document(result)


def bridge():
    c=catalogs()['einstein-1905'];units=author.read(author.UNITS)['units'];body=[u for u in units if u['kind']=='body'];sources=[]
    for i,(reading,review) in enumerate(zip(READINGS,REVIEWS,strict=True)):
        unit=body[6+i];require(unit['id']=='einstein-1905:u00'+str(11+i),'Paragraph position changed')
        r=author.read(review);require(r['source']['text']==unit['text'] and r['source']['unit_sha256']==unit['text_sha256'],'Old paragraph review changed')
        segments=author.read(reading)['segments'];cursor=0
        for row in segments:
            a,b=row['range'];require(row['unit']==unit['id'] and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][a:b],'Original reading differs')
            require(unit['text'][cursor:a] in ('',' '),'Uncovered source range');cursor=b
        require(cursor==len(unit['text']),'Source paragraph is incomplete');sources.append(dict(unit=unit['id'],sha256=unit['text_sha256'],text=unit['text'],ranges=[r['range'] for r in segments]))
    require(body[8]['id']=='einstein-1905:u0013' and body[12]['id']=='einstein-1905:u0018','Forward anchors changed')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-observer-time-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=list(range(65,70)),source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],
        mapping=mapping(),sentence_positions={n:list(pos) for n,pos in SENTENCES.items()},reference_roles=reference_roles(),reference_nodes={n:reference_node(n) for n in REFERENTS},role_definitions=role_definitions(),
        forward_reference=dict(begin=body[8]['id'],end=body[12]['id'],end_sentence=2,following_contents_asserted=False),
        semantic_review=['見かけの評価候補と採用の可能な結果を分け、全困難について同じ結果で克服できるという内容を保持する。',
            '局所だけの十分性と異所での不十分性を同じ案・課題に結ぶ。二つの遠隔課題の解の両方向一致、実際の確認、対比、挿入を保持する。',
            '先行列車例の時計と自分の時計、原点の時計、共通の参照時計を無条件に同一視しない。異なる参照を必ず異なる個体とも主張しない。',
            '原出来事・信号・出発・受信・表示・読取り候補を同じ到達記録で保つ。受信時刻を生起時刻へ置き換えず、伝播補正や同期済みを補わない。',
            '比較可能な二配置の観測者位置と割当値の差を保ち、経験による知識、方式の不都合、代案への譲歩を省かない。',
            '同じ実用性基準で新旧方式の程度・厳密な優越・顕著な差を区別し、最良性や数値閾値を追加しない。',
            '後続の考察は第九本文段落から第十三本文段落第二文までを指す。規則の引用を全適用や全後続本文の証明へ替えない。'],
        profile_edition=23,core_edition=12,new_source_assertions=5,total_source_assertions=14,annotations=2,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible observer-time document differs');return result


BASE={n:n for n in ('rd','eirf','ri','eisfm','eisgc','eisgq','eishg','eishp','eishs','eish2','rj','eisf6','eishe','eishr')}
BASE.update(rd='author',eirf='doc',ri='body')


def role_model(values):
    return {(values['eirf'],values[reference_node(old)],previous.canonical(dict(kind='function_ref',symbol=role)),values['ri']):values.get(old,old)
        for old,role in reference_roles().items()}


def context_handlers(values,roles=None):
    from scripts.discourse_setting_profile import DiscourseReferences
    from scripts.temporal_discourse_profile import TemporalReferences
    presentation=author.NamePresentation('front',{('front',2):('other','other',values['rd'],values['eirf'])},presented={},applied={},authors={},forms={})
    layout={(values['ri'],4,1):'setting',(values['ri'],6,4):values['eisfm']}|{(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    refs=DiscourseReferences({values['eirf']:values['ri']},{},layout,{(values['eirf'],'setting',1,values['ri']):'frame'})
    temporal=TemporalReferences(role_model(values) if roles is None else roles,{})
    def clock(frame,ctx):
        require((frame,ctx)==('frame',values['ri']),'Unknown common reference clock');return values.get('rc','rc')
    return presentation.handlers()|refs.handlers()|temporal.handlers()|dict(referenceclock=clock)


def attribution_case(changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[]
    facts=dict(eir3=[(BASE[node],'author','doc',msg,'body') for node,msg in zip(('eisgc','eisgq','eishg','eishp','eishs'),('eijp','eij6','eiki','eikq','eikw'),strict=True)],
        ue=[(BASE[a],BASE[b],'body') for a,b in zip(('eisfm','eisgc','eisgq','eishg','eishp','eishs','eish2'),('eisgc','eisgq','eishg','eishp','eishs','eish2','rj'),strict=True)],
        eisgo=[('eisgq','author','eij2','doc','body')],
        zbc=[('eisgq','author','eij2','eij3','eisf6','body'),('eishp','author','eikh','eikp','eishe','body')],
        eisgp=[('eisgq','author','eij3','eij4','doc','body')],eisg6=[('eishg','author','eij5','eikh','doc','body')],
        eisho=[('eishp','author','eikn','eiko','doc','body')],eishz=[('eishs','author','eishr','eish2','rj','doc','body')])
    slots=dict(eir3=(3,),eisgo=(2,),zbc=(2,3),eisgp=(2,3),eisg6=(2,3),eisho=(2,3))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted observer-time content was executed')
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):
                node=json.loads(args[i].syntax)
                if not original:node=renamed(node,{v:k for k,v in mapping().items()})
                args[i]=node['symbol'] if node.get('kind')=='call' and not node['arguments'] else 'different'
            trace.append(dict(relation=name,arguments=args));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=source_excerpt();h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items()});h.update(relations)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][11:]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
        answers.append(evaluate_document(doc,individuals=tuple(set(BASE.values())-{'body'})+('other','setting','frame'),situations=('front','body'),primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Observer-time attribution differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


def diagnostics():
    rows=[attribution_case()];require(rows[0]['values']==[True]*5,'Baseline attribution differs')
    for field in BASE:
        r=attribution_case({field:'front' if field=='ri' else 'other'});require(not all(r['values']),'Ignored context role');rows.append(r)
    for relation,indices in dict(eir3=range(5),ue=range(5),eisgo=(1,),zbc=(1,3),eisgp=(1,),eisg6=(2,),eisho=(3,),eishz=(4,)).items():
        r=attribution_case(failed=relation);require(r['values']==[i not in indices for i in range(5)],'Wrong discourse relation scope');rows.append(r)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    # JSON object key order is not a semantic difference. Existing bytes stay pinned.
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published observer bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved observer bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-temporal-discourse-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/observer_time_profile.py','scripts/observer_time_contracts.py','scripts/check_einstein_observer_time.py',
        'scripts/visible_observer_time_collection.py','tests/test_observer_time_profile.py','docs/einstein-observer-time-v1.md'}
    return dict(schema='noema-einstein-observer-time-evidence-1',core_words=375,profile_words=515,profile_edition=23,
        preserved_source_relations=53,new_reference_primitives=0,new_source_assertions=5,total_source_assertions=14,annotations=2,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
