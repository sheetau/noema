"""Connect the two rod measurement procedures and the permitted length designation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import rod_methods_profile as profile
from scripts.rod_methods_profile import ROOT,RodMethodsVocabulary,write_once
from scripts import check_einstein_rod_experiment as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed
from scripts.shared_reference import definition
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-rod-methods-v1.noema'
BRIDGE='data/einstein-rod-methods-bridge-v1.json'
OUT=ROOT/'output/einstein-rod-methods-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eip2 eip3 eip4 eip5 eip6 eip7 eipw eipx eipy eipz eiqa eiqb eiqc eiqd eiqe'.split()
SENTENCES=dict(methodbnaming=(21,2))
DESIGNATIONS=dict(eisl6=('methodbnaming',1))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*DESIGNATIONS]
READINGS=('data/einstein-rod-methods-source-reading-v1.json',)
REVIEWS=('data/einstein-comoving-ruler-method-review-v1.json','data/einstein-synchronized-endpoints-method-review-v1.json')
FORMS=dict(eisl6='Länge des Stabes')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return RodMethodsVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][91:93]):visit(n)
    require(len(seen)==180,'Rod-methods source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][91:93])))


@lru_cache(maxsize=1)
def names():
    n=dict(previous.names());proper=set(SENTENCES)|set(DESIGNATIONS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','book','above',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    for old,(node,ordinal) in DESIGNATIONS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(ordinal),k('ri'))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,form in FORMS.items():
        doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(form),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(previous.previous.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][43:45],inverse);return normalize_document(result)


@lru_cache(maxsize=1)
def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations'])
    rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():
        require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0]);sources={}
    for row in reading['segments']:
        unit=units[row['unit']];a,b=row['range']
        require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][a:b],'Original reading differs')
        require(a==0 and b==len(unit['text']),'Incomplete source unit')
        sources[unit['id']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[a,b])
    require(set(sources)=={'einstein-1905:u0030','einstein-1905:u0031'},'Source units changed')
    text=sources['einstein-1905:u0031']['text'];require(len(text)==420 and text.index('Die Entfernung')==239,'Method-b sentence boundary changed')
    require(reading['segments'][1]['math'][0]['id']=='M0048','Specified time attachment changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-rod-methods-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[91,92],source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_positions=dict(xw=[20,1],xx=[21,1],methodbnaming=[21,2]),
        sentence_ranges={'einstein-1905:u0030':[[0,243]],'einstein-1905:u0031':[[0,238],[239,420]]},
        math=reading['segments'][1]['math'],designation_positions={n:[node,i] for n,(node,i) in DESIGNATIONS.items()},annotations=annotations()['entries'],
        semantic_review=[
            '方法a/bの箇所は前版の段落20/21への前方参照を再利用する。bの第二文は改頁後も段落21に属し、引用呼称の箇所を第二文に置く。',
            '方法aは同じ棒・物差し・観測者・単位による直接接触測定と、静止していた場合への手順比較を区別する。比較側の実在や二結果の数値的一致を導かない。',
            '同伴する巨視的配置の静止系に対する等速並進、同伴系での静止、同じ全物質点履歴への条件を保持する。初期測定の観測者を後の観測者へ固定しない。',
            '方法bは静止系の静止時計と第一節の同期・局所時刻規約を使い、同じ指定時刻xvの両端の出来事・場所・表示・世界線座標を結ぶ。遠隔受信時刻を混ぜない。',
            '同じ物差しを今回は静止系で静止させ、二地点の距離・測定の読み・棒の軸長を同じ値に結ぶ。観測者の静止は追加しない。二方法を別設定として保つ。',
            '二方法の値を棒の長さと呼び得る分類上の許容を保持する。呼称の義務、値の存在・唯一性・一致・相違、実測完了、後続u0032の結論を先取りしない。'],
        profile_edition=28,core_edition=12,new_source_assertions=2,total_source_assertions=37,total_annotations=9,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible rod-methods document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*DESIGNATIONS)}
SITUATIONS=previous.SITUATIONS


def context_handlers(values):
    result=previous.context_handlers(values);old_sentence=result['sentencereference'];old_designation=result['designationreference']
    from scripts.text_reference_profile import TextPresentation
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        if key==(values['ri'],21,2):return values['methodbnaming']
        return old_sentence(context,paragraph,item)
    def designation(document,node,item,context):
        key=(document,node,TextPresentation.coordinate(item),context)
        if key==(values['eirf'],values['methodbnaming'],1,values['ri']):return values['eisl6']
        return old_designation(document,node,item,context)
    return result|dict(sentencereference=sentence,designationreference=designation)


def attribution_facts():
    return dict(eir3=[('xw','author','doc',('call','eiqa'),'body'),('xx','author','doc',('call','eiqd'),'body')],
        eiskj=[('xw','y3',1,'doc','body'),('xx','y3',2,'doc','body')],ue=[('y3','xw','body'),('xw','xx','body')])


def presentation_facts():
    return dict(xz=[('xw','author',('function_ref','eip2'),'xy','body'),('xx','author',('function_ref','eip6'),'xy','body')],
        eisl3=[('xw','author',('function_ref','eipz'),'xl','frame',('function_ref','eip2'),('function_ref','eip3'),'xy','doc','body')],
        eislp=[('xx','author','eisdy',('function_ref','eing'),'doc','body')],
        eisl5=[('xx','author','xi','eisl6',(('function_ref','eip2'),('function_ref','eip6')),'xy','doc','body')])


def discourse_case(inner=False,changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=presentation_facts() if inner else attribution_facts()
    slots=dict(eir3=(3,),xz=(2,),eisl3=(2,5,6),eislp=(3,))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted rod-method content was executed')
        def description(value):
            node=json.loads(value.syntax)
            if not original:node=renamed(node,{v:k for k,v in mapping().items()})
            return (node['kind'],node['symbol']) if node.get('kind')=='function_ref' or (node.get('kind')=='call' and not node['arguments']) else ('different',)
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):args[i]=description(args[i])
            if name=='eisl5':args[4]=tuple(description(item) for item in args[4].items)
            if name=='eiskj':args[2]=int(args[2])
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=deepcopy(source_excerpt());h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
            selected=lambda name:call(name)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][43:45]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
            selected=lambda name:call(mapping()[name])
        if inner:doc['statements']=[dict(kind='ask',body=dict(kind='evaluate',content=selected(name),situation=selected('ri'))) for name in ('eip7','eiqc')]
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=SITUATIONS,primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Rod-methods discourse differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[discourse_case()];require(rows[0]['values']==[True]*2,'Baseline attribution differs')
    for field in ('rd','eirf','ri','y3','xw','xx'):
        row=discourse_case(changed={field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored attribution role: '+field);rows.append(row)
    for name in attribution_facts():
        row=discourse_case(failed=name);require(row['values']==[False]*2,'Wrong attribution scope: '+name);rows.append(row)
    return rows


@lru_cache(maxsize=1)
def presentation_diagnostics():
    rows=[discourse_case(True)];require(rows[0]['values']==[True]*2,'Baseline presentation differs')
    for field in ('rd','eirf','ri','xi','xl','ra','xy','xw','xx','eisdy','eisl6'):
        row=discourse_case(True,{field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored presentation role: '+field);rows.append(row)
    for name,expected in dict(xz=[False,False],eisl3=[False,True],eislp=[True,False],eisl5=[True,False]).items():
        row=discourse_case(True,failed=name);require(row['values']==expected,'Wrong presentation scope: '+name);rows.append(row)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published rod-methods bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved rod-methods bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-rod-experiment-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/rod_methods_profile.py','scripts/rod_methods_profile_contracts.py','scripts/check_einstein_rod_methods.py',
        'scripts/visible_rod_methods_collection.py','tests/test_rod_methods_profile.py','docs/einstein-rod-methods-v1.md'}
    for path in READINGS:paths.update(author.read(path)['images'])
    return dict(schema='noema-einstein-rod-methods-evidence-1',core_words=375,profile_words=664,profile_edition=28,
        preserved_source_relations=4,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=37,annotations=9,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),presentation_diagnostics=presentation_diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
