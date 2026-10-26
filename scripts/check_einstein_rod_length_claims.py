"""Connect rod length names, attributed necessity and future determination."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import rod_length_claims_profile as profile
from scripts.rod_length_claims_profile import ROOT,RodLengthClaimsVocabulary,write_once
from scripts import check_einstein_rod_methods as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts import check_einstein_two_principles as principles
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v
from scripts.shared_reference import definition
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-rod-length-claims-v1.noema'
BRIDGE='data/einstein-rod-length-claims-bridge-v1.json'
OUT=ROOT/'output/einstein-rod-length-claims-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiqf eiqg eiqh eiqi eiqj eiqk eiql eiqm eiqn eiqo eiqp sbx sby sbz scb sce'.split()
SENTENCES=dict(zg=(22,1),zh=(23,1))
DESIGNATIONS=dict(eisma=('zg',1),eismb=('zh',1))
ROLE_ASSIGNMENTS=dict(ze=('zg','naminga'),zf=('zh','namingb'),zi=('zh','later'))
ROLE_HELPERS=['lengthrole'+role for _,role in ROLE_ASSIGNMENTS.values()]
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*DESIGNATIONS,*ROLE_ASSIGNMENTS,*ROLE_HELPERS]
READINGS=('data/einstein-rod-length-claims-source-reading-v1.json',)
REVIEWS=('data/einstein-comoving-length-necessity-review-v1.json','data/einstein-rest-frame-length-announcement-review-v1.json')
FORMS=dict(eisma='die Länge des Stabes im bewegten System',eismb='die Länge des (bewegten) Stabes im ruhenden System')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return RodLengthClaimsVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][93:95]):visit(n)
    require(len(seen)==247,'Rod-length-claims source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][93:95])))


@lru_cache(maxsize=1)
def names():
    n=dict(previous.names());proper=set(SENTENCES)|set(DESIGNATIONS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','book','book',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def qf(name):return dict(kind='quote',body=dict(kind='function_ref',symbol=name))
def reference_roles():return {old:names()['lengthrole'+role] for old,(_,role) in ROLE_ASSIGNMENTS.items()}


def role_definitions():
    n=names();m=mapping();x=v('va');s=v('vb');k=lambda old:call(n[old])
    bodies={}
    for role,label,method,quantity in [('naminga','eisma','eip2','eiqf'),('namingb','eismb','eip6','eiqg')]:
        bodies[role]=call(m['eisl7'],x,k('rd'),k(label),qf(n[method]),qf(n[quantity]),k('xy'),k('eirf'),s)
    bodies['later']=call(m['eisci'],x,k('eirf'),k('zh'),s)
    return [definition(n['lengthrole'+role],[('va','individual'),('vb','situation')],'truth',body) for role,body in bodies.items()]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    for old,(node,ordinal) in DESIGNATIONS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(ordinal),k('ri'))))
    for old,role in reference_roles().items():
        node=ROLE_ASSIGNMENTS[old][0]
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],k('eirf'),k(node),qf(role),k('ri'))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,form in FORMS.items():
        doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(form),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][46:48],inverse);return normalize_document(result)


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
    require(set(sources)=={'einstein-1905:u0032','einstein-1905:u0033'},'Source units changed')
    require([len(sources[k]['text']) for k in sorted(sources)]==[195,239],'Sentence boundary changed')
    math=[r for segment in reading['segments'] for r in segment['math']]
    require([r['id'] for r in math]==['M0049','M0050'] and all(r['binding']=='ya; initial rest length from u0029' for r in math),'Initial length binding changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    for row in reading['later_context']['units']:require(row['unit_sha256']==units[row['unit']]['text_sha256'],'Later context changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-rod-length-claims-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[93,94],source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_positions={old:list(pos) for old,pos in SENTENCES.items()},
        sentence_ranges={'einstein-1905:u0032':[[0,195]],'einstein-1905:u0033':[[0,239]]},math=math,
        designation_positions={n:[node,i] for n,(node,i) in DESIGNATIONS.items()},annotations=annotations()['entries'],
        role_assignments={old:list(role) for old,role in ROLE_ASSIGNMENTS.items()},reference_roles=role_definitions(),later_context=reading['later_context'],
        semantic_review=[
            '原刊896頁の二文を段落22/23とする。埋込の命名箇所ze/zfは文全体zg/zhをアンカーに命名意向の役割で参照し、同一視を強制しない。呼称個体は文全体の実位置から取得し、参照を循環させない。',
            '二つの引用呼称は原文の綴りと括弧付きbewegtenを保持する。概念の意味は同じ棒・系・単位・区間・端点に結ぶ数量記述で示し、原語の表記で代用しない。',
            '方法aの値を移動系での棒の長さと呼ぶ意向と、相対性原理によれば初期静止長yaと等しくなければならないという著者の主張を分ける。',
            '方法bの値を静止系での動く棒の長さと呼ぶ意向と、二原理に基づき値を決めてyaとの差異を見いだすという将来の論述予告を結ぶ。',
            'その長さという読解の存在と数値としての一意性を、元の全実切断の量化を保ったsbz/sbyで示す。表現の異なる同値な切断を異なる数値として数えない。',
            '命名・必要性・予告は引用内容を実行しない。測定済み、導出済み、実在の真理、収縮の向きや割合を追加しない。',
            'ziは同じ論説でzhより後の議論というeisciの役割で参照する。後続u0110–116との文脈を記録するが、単独の段落と同一視したり、予告された導出をこの二文で完了扱いにしない。'],
        profile_edition=29,core_edition=12,new_source_assertions=2,total_source_assertions=39,total_annotations=11,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible rod-length-claims document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*DESIGNATIONS,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def role_model(values):
    return previous.previous.role_model(values)|{(values['eirf'],values[ROLE_ASSIGNMENTS[old][0]],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
        for old,role in reference_roles().items()}


def context_handlers(values,roles=None):
    result=previous.context_handlers(values);old_sentence=result['sentencereference'];old_designation=result['designationreference']
    from scripts.text_reference_profile import TextPresentation
    from scripts.temporal_discourse_profile import TemporalReferences
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    designations={(values['eirf'],values[node],ordinal,values['ri']):values[old] for old,(node,ordinal) in DESIGNATIONS.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        if key in layout:return layout[key]
        return old_sentence(context,paragraph,item)
    def designation(document,node,item,context):
        key=(document,node,TextPresentation.coordinate(item),context)
        if key in designations:return designations[key]
        return old_designation(document,node,item,context)
    described=TemporalReferences(role_model(values) if roles is None else roles,{}).described
    return result|dict(sentencereference=sentence,designationreference=designation,describedreference=described)


def attribution_facts():
    return dict(eir3=[('zg','author','doc',('call','eiql'),'body'),('zh','author','doc',('call','eiqo'),'body')],
        ue=[('xx','zg','body'),('zg','zh','body')])


def presentation_facts():
    return dict(zb=[('ze','author',('function_ref','eip2'),('function_ref','eiqf'),'xy','body'),('zf','author',('function_ref','eip6'),('function_ref','eiqg'),'xy','body')],
        eisl7=[('ze','author','eisma',('function_ref','eip2'),('function_ref','eiqf'),'xy','doc','body'),('zf','author','eismb',('function_ref','eip6'),('function_ref','eiqg'),'xy','doc','body')],
        zc=[('zg','author',('call','eion'),('call','eiqh'),'xy','body')],
        zd=[('zh','author',('call','eiqj'),('call','eiqi'),(('call','eion'),('call','eiot')),'zi','xy','body')],
        eisci=[('zi','doc','zh','body')])


def discourse_case(inner=False,changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=presentation_facts() if inner else attribution_facts()
    slots=dict(eir3=(3,),zb=(2,3),eisl7=(3,4),zc=(2,3),zd=(2,3))
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
            if name=='zd':args[4]=tuple(description(item) for item in args[4].items)
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=deepcopy(source_excerpt());h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
            selected=lambda name:call(name)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][46:48]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
            selected=lambda name:call(mapping()[name])
        if inner:doc['statements']=[dict(kind='ask',body=dict(kind='evaluate',content=selected(name),situation=selected('ri'))) for name in ('eiqk','eiqn')]
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=SITUATIONS,primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Rod-length-claims discourse differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[discourse_case()];require(rows[0]['values']==[True]*2,'Baseline attribution differs')
    for field in ('rd','eirf','ri','xx','zg','zh'):
        row=discourse_case(changed={field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored attribution role: '+field);rows.append(row)
    for name in attribution_facts():
        row=discourse_case(failed=name);require(row['values']==[False]*2,'Wrong attribution scope: '+name);rows.append(row)
    return rows


@lru_cache(maxsize=1)
def presentation_diagnostics():
    rows=[discourse_case(True)];require(rows[0]['values']==[True]*2,'Baseline presentation differs')
    for field in ('rd','eirf','ri','xy','ze','zf','zg','zh','zi','eisma','eismb'):
        row=discourse_case(True,{field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored presentation role: '+field);rows.append(row)
    for name,expected in dict(zb=[False,False],eisl7=[False,False],zc=[False,True],zd=[True,False],eisci=[True,False]).items():
        row=discourse_case(True,failed=name);require(row['values']==expected,'Wrong presentation scope: '+name);rows.append(row)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published rod-length-claims bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved rod-length-claims bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-rod-methods-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/rod_length_claims_profile.py','scripts/rod_length_claims_profile_contracts.py','scripts/check_einstein_rod_length_claims.py',
        'scripts/visible_rod_length_claims_collection.py','tests/test_rod_length_claims_profile.py','docs/einstein-rod-length-claims-v1.md'}
    for path in READINGS:paths.update(author.read(path)['images'])
    return dict(schema='noema-einstein-rod-length-claims-evidence-1',core_words=375,profile_words=668,profile_edition=29,
        preserved_source_relations=4,new_reference_primitives=0,new_source_assertions=2,total_source_assertions=39,annotations=11,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),presentation_diagnostics=presentation_diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
