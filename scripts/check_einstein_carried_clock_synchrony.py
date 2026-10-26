"""Connect carried clocks, complete local-time agreement and attributed naming."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import carried_clock_synchrony_profile as profile
from scripts.carried_clock_synchrony_profile import ROOT,CarriedClockSynchronyVocabulary,write_once
from scripts import check_einstein_kinematic_replacement as previous
from scripts import check_einstein_name_presentation as author
from scripts import check_einstein_temporal_discourse as temporal
from scripts import check_einstein_two_principles as principles
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.shared_reference import definition
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-carried-clock-synchrony-v1.noema'
BRIDGE='data/einstein-carried-clock-synchrony-bridge-v1.json'
OUT=ROOT/'output/einstein-carried-clock-synchrony-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiqz eiq2 eiq3 eiq4 eiq5 eiq6 eiq7 eita eitb eitc sct scu scv'.split()
SENTENCES=dict(zal=(25,1))
DESIGNATIONS=dict(eismf=('zal',1),eismg=('zal',2),eismd=('zal',3))
ROLE_ASSIGNMENTS=dict(zaj=('zal','clocka'),zak=('zal','clockb'),zam=('zal','naming'))
ROLE_HELPERS=['carriedrole'+role for _,role in ROLE_ASSIGNMENTS.values()]
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*DESIGNATIONS,*ROLE_ASSIGNMENTS,*ROLE_HELPERS]
READINGS=('data/einstein-carried-clock-synchrony-source-reading-v1.json',)
REVIEWS=('data/einstein-carried-clock-synchrony-review-v1.json',)
FORMS=dict(eismf='A',eismg='B',eismd='synchron im ruhenden System')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return CarriedClockSynchronyVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][96:97]):visit(n)
    require(len(seen)==147,'Carried-clock-synchrony source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][96:97])))


@lru_cache(maxsize=1)
def names():
    n=dict(previous.names());proper=set(SENTENCES)|set(DESIGNATIONS)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','above',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def qf(name):return dict(kind='quote',body=dict(kind='function_ref',symbol=name))
def reference_roles():return {old:names()['carriedrole'+role] for old,(_,role) in ROLE_ASSIGNMENTS.items()}


def role_definitions():
    n=names();m=mapping();x=v('va');s=v('vb');k=lambda old:call(n[old])
    bodies={role:call(n['eiqz'],x,k(endpoint),k('yd')) for role,endpoint in [('clocka','xn'),('clockb','xo')]}
    pair=dict(kind='sequence',element='individual',items=[k('zaj'),k('zak')])
    bodies['naming']=op('and',call(m['zan'],x,k('rd'),qf(n['eiq5']),k('ra'),k('xy'),s),
        call(m['eismc'],x,k('rd'),k('eismd'),qf(n['eiq5']),pair,k('ra'),k('xy'),k('eirf'),s))
    return [definition(n['carriedrole'+role],[('va','individual'),('vb','situation')],'truth',body) for role,body in bodies.items()]


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
    result['statements']=renamed(doc['statements'][51:52],inverse);return normalize_document(result)


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
    require(set(sources)=={'einstein-1905:u0035'} and len(sources['einstein-1905:u0035']['text'])==321,'Source boundary changed')
    math=[r for segment in reading['segments'] for r in segment['math']]
    expected=[dict(id='M0052',sha256='54d50fafeb332857187f47519e3fc74b679b89c2e3e779038dc2f566127bc4ff',printed='A',binding='eismf designates xn'),
        dict(id='M0053',sha256='22fdbca6cc3ccac3e6770e48b1a02c0b0895a7186c326abbd29d5f489f3f2843',printed='B',binding='eismg designates xo')]
    require(math==expected,'Endpoint designation changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-carried-clock-synchrony-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[96],source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_positions={old:list(pos) for old,pos in SENTENCES.items()},
        sentence_ranges={'einstein-1905:u0035':[[0,321]]},math=math,
        designation_positions={n:[node,i] for n,(node,i) in DESIGNATIONS.items()},annotations=annotations()['entries'],
        role_assignments={old:list(role) for old,role in ROLE_ASSIGNMENTS.items()},reference_roles=role_definitions(),
        semantic_review=['原刊896頁、段落25の第一文全体をzalとする。文中の命名箇所zamと同一視せず、同じ著者・条件・二時計・系・範囲の役割から参照する。',
 'この箇所で採用するA/B/同期呼称を順に1/2/3とする。既出のZeit des ruhenden Systemsはeisjdの再言及であり、新しい名称として数えない。A/Bを端点本体xn/xoに結ぶ。',
 'zaj/zakはeiqz(candidate,xn/ xo,yd)を引用した役割から参照する。呼称は全体文zalをアンカーにし、時計・命名箇所の参照循環を作らない。参照時に物理条件を実行しない。',
 '時計の代表点と棒端の全区間の同じ三座標履歴と、物理的取り付けzaaを保つ。時計内部の歯車や針の運動を停止させない。',
 '各比較は同じ出来事・現在位置の静止局所時計のeingと、動く時計自身の表示を比較する。qoは局所時計とrcの間に使い、動く時計自身に静止を課さない。',
 '記録zacの出来事・場所・局所時計・自時計表示・静止系時刻を区別し、全記録の条件と全実時刻の証人を両方保つ。有限の時間射影は束縛診断であり全実数の証明ではない。',
 'fernerを同じ先行設定への追加、d. h.を同期の資格の説明、alsoをその条件による命名の理由付けとして保つ。物理的実現や補正なしの時計の進み方の法則を補わない。'],
        profile_edition=31,core_edition=12,new_source_assertions=1,total_source_assertions=41,total_annotations=14,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible carried-clock-synchrony document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*DESIGNATIONS,*ROLE_ASSIGNMENTS,'rb')}
SITUATIONS=previous.SITUATIONS


def role_model(values):
    return previous.role_model(values)|{(values['eirf'],values[ROLE_ASSIGNMENTS[old][0]],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
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
    return dict(eir3=[('zal','author','doc',('call','eitb'),'body')],ue=[('zv','zal','body')])


def presentation_facts():
    return dict(ug=[('zal','author',('call','eiq6'),'xy','body')],zao=[('y2','zal','xy','body')],
        zan=[('zam','author',('function_ref','eiq5'),'frame','xy','body')],
        eismc=[('zam','author','eismd',('function_ref','eiq5'),('zaj','zak'),'frame','xy','doc','body')],
        eisku=[('eisjd',('function_ref','eing'),'frame','rb','doc','body')],
        eisme=[('zal','author',('call','eiq7'),('call','eiq6'),'doc','body')],
        eisdk=[('doc',('call','eiq6'),('call','eiq7'),'body')],
        eisd4=[('zal','author','eismf','xn','doc','body'),('zal','author','eismg','xo','doc','body')])


def discourse_case(inner=False,changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=presentation_facts() if inner else attribution_facts()
    slots=dict(eir3=(3,),ug=(2,),zan=(2,),eismc=(3,),eisku=(1,),eisme=(2,3),eisdk=(1,2))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted carried-clock content was executed')
        def description(value):
            node=json.loads(value.syntax)
            if not original:node=renamed(node,{v:k for k,v in mapping().items()})
            return (node['kind'],node['symbol']) if node.get('kind')=='function_ref' or (node.get('kind')=='call' and not node['arguments']) else ('different',)
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):args[i]=description(args[i])
            if name=='eismc':args[4]=tuple(args[4].items)
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=deepcopy(source_excerpt());h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
            selected=lambda name:call(name)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][51:52]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
            selected=lambda name:call(mapping()[name])
        if inner:doc['statements']=[dict(kind='ask',body=dict(kind='evaluate',content=selected(name),situation=selected('ri'))) for name in ('eita',)]
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=SITUATIONS,primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Carried-clock-synchrony discourse differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[discourse_case()];require(rows[0]['values']==[True],'Baseline attribution differs')
    for field in ('rd','eirf','ri','zv','zal'):
        row=discourse_case(changed={field:'front' if field=='ri' else 'other'});require(row['values']==[False],'Ignored attribution role: '+field);rows.append(row)
    for name in attribution_facts():
        row=discourse_case(failed=name);require(row['values']==[False],'Wrong attribution scope: '+name);rows.append(row)
    return rows


@lru_cache(maxsize=1)
def presentation_diagnostics():
    rows=[discourse_case(True)];require(rows[0]['values']==[True],'Baseline presentation differs')
    for field in ('rd','eirf','ri','xy','y2','zal','zam','zaj','zak','eismf','eismg','eismd','eisjd','ra','rb','xn','xo'):
        row=discourse_case(True,{field:'front' if field=='ri' else 'other'});require(row['values']==[False],'Ignored presentation role: '+field);rows.append(row)
    for name in presentation_facts():
        row=discourse_case(True,failed=name);require(row['values']==[False],'Wrong presentation scope: '+name);rows.append(row)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published carried-clock-synchrony bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved carried-clock-synchrony bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-kinematic-replacement-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/carried_clock_synchrony_profile.py','scripts/carried_clock_synchrony_profile_contracts.py','scripts/check_einstein_carried_clock_synchrony.py',
        'scripts/visible_carried_clock_synchrony_collection.py','tests/test_carried_clock_synchrony_profile.py','docs/einstein-carried-clock-synchrony-v1.md'}
    for path in READINGS:paths.update(author.read(path)['images'])
    return dict(schema='noema-einstein-carried-clock-synchrony-evidence-1',core_words=375,profile_words=687,profile_edition=31,
        preserved_source_relations=13,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=41,annotations=14,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),presentation_diagnostics=presentation_diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
