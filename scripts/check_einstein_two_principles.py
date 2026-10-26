"""Connect the two principles, their discourse scope and speed definition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import two_principles_profile as profile
from scripts.two_principles_profile import ROOT,TwoPrinciplesVocabulary,write_once,CUT
from scripts import check_einstein_light_speed_time as previous
from scripts import check_einstein_name_presentation as author
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.shared_reference import definition
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require
from scripts.check_einstein_temporal_discourse import canonical

SOURCE='examples/v016/einstein-two-principles-v1.noema'
BRIDGE='data/einstein-two-principles-bridge-v1.json'
OUT=ROOT/'output/einstein-two-principles-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eifc eifd eife eiff eifg eifh eifi eifj eifw eifx eify eihq ein7 eio2 eio3 eio4 eio5 eio6 eioa eiob eioc eiod eioe eiof eiog eioh eioi eioj eiok eiol eiom eion eioo eiop eioq eior eios eiot eiou eiov eiow eiox eioy eioz sap saq sar sax saz sbn'.split()
SENTENCES=dict(wu=(16,1),vk=(17,1),wt=(18,1),eisll=(18,2))
DESIGNATIONS=dict(eisk3=('wu',1),eisk4=('wu',2),eisln=('eisll',1))
HEADINGS=dict(firstpartheading=1,eisk2=3)
ROLE_ASSIGNMENTS=dict(eisdx=('firstpartheading','part'),eisdy=('eisd2','firstsection'),eiskz=('eisk2','secondsection'),wv=('wu','following'))
AXES=dict(yn=1,yo=2,yp=3)
FIELDS={n:('segmententity',i) for i,n in enumerate('wf wg wh wi wj wk wl wm wn'.split())}|{n:('segmentreading',i) for i,n in enumerate('wo wp wq'.split())}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*DESIGNATIONS,*HEADINGS,*ROLE_ASSIGNMENTS,*AXES,*FIELDS,*['principlerole'+r for _,r in ROLE_ASSIGNMENTS.values()]]
READINGS=('data/einstein-second-section-opening-source-reading-v1.json','data/einstein-first-principle-source-reading-v1.json','data/einstein-second-principle-source-reading-v1.json')
REVIEWS=tuple('data/einstein-'+name+'-review-v1.json' for name in ('second-section-heading','two-principle-introduction','first-principle','second-principle-u0026','second-principle-u0027','second-principle-u0028'))
FORMS=dict(eisk3='Relativitätsprinzip',eisk4='Prinzip der Konstanz der Lichtgeschwindigkeit',eisln='Zeitdauer')
qf=previous.qf
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY



@lru_cache(maxsize=1)
def vocabulary():return TwoPrinciplesVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][83:88]):visit(n)
    require(len(seen)==206,'Light-speed-time source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][83:88])))


@lru_cache(maxsize=1)
def names():
    n=dict(previous.names());proper=set(SENTENCES)|set(ROLE_ASSIGNMENTS)|set(DESIGNATIONS)|set(HEADINGS)|set(AXES)
    parts=previous.previous.previous.previous.PARTS
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','book','nao',parts[i//16],parts[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:previous.previous.previous.previous.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def reference_roles():return {old:names()['principlerole'+role] for old,(_,role) in ROLE_ASSIGNMENTS.items()}


def role_definitions():
    n=names();m=mapping();x=v('va');s=v('vb');k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    bodies=dict(part=r('eisdv',k('firstpartheading'),x,k('eirf'),k('eirf'),author.num(1),author.num(1),s),
        firstsection=r('eisdv',k('eisd2'),x,k('eisdx'),k('eirf'),author.num(2),author.num(1),s),
        secondsection=r('eisdv',k('eisk2'),x,k('eisdx'),k('eirf'),author.num(2),author.num(2),s),
        following=r('eisci',x,k('eirf'),k('wu'),s))
    return [definition(n['principlerole'+name],[('va','individual'),('vb','situation')],'truth',body) for name,body in bodies.items()]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    for old,ordinal in HEADINGS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['headingreference'],k('ri'),author.num(ordinal))))
    for old,role in reference_roles().items():
        node=ROLE_ASSIGNMENTS[old][0]
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],k('eirf'),k(node),qf(role),k('ri'))))
    for old,(node,ordinal) in DESIGNATIONS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(ordinal),k('ri'))))
    for old,axis in AXES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['frameaxisreference'],k('ra'),author.num(axis),k('ri'))))
    for old,(field,slot) in FIELDS.items():
        doc['declarations'].append(definition(n[old],[('va','individual')],profile.FIELD_CONTRACTS[old]['result'],call(voc._symbols[field],v('va'),author.num(slot))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,form in FORMS.items():
        doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(form),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(previous.previous.previous.previous.FIELDS)|set(FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][32:37],inverse);return normalize_document(result)



@lru_cache(maxsize=1)
def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations'])
    rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():
        require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};sources={}
    for path in READINGS:
        for row in author.read(path)['segments']:
            unit=units[row['unit']];a,b=row['range']
            require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][a:b],'Original reading differs')
            require(a==0 and b==len(unit['text']),'Incomplete source unit')
            sources[unit['id']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[a,b])
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(23,29)},'Source units changed')
    split=sources['einstein-1905:u0026']['text'].index('Hierbei ist')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    for old,contract in profile.FIELD_CONTRACTS.items():
        e=c.entries[old];d=e['declaration']
        meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(contract==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Field meaning changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-two-principles-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=list(range(83,88)),source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],
        mapping=mapping(),sentence_positions={n:list(pos) for n,pos in SENTENCES.items()},heading_positions=HEADINGS,
        reference_roles=reference_roles(),role_definitions=role_definitions(),field_contracts=profile.FIELD_CONTRACTS,
        equation_attachment=dict(node='eisll',units=['einstein-1905:u0026','einstein-1905:u0027','einstein-1905:u0028'],
            first_unit_range=[split,len(sources['einstein-1905:u0026']['text'])],one_sentence=True,paragraph=18,
            math=author.read(READINGS[2])['segments'][1]['math'][0]),
        printed_designations=FORMS,identifier_annotations=annotations(),
        semantic_review=[
            '番号付き項目は段落17と18に対応する。第二項のHierbei ist以降、表示式とwobeiは段落18の第二文である。',
            '部と節は見出しの箇所と区別し、既存の階層・番号関係を役割参照に使う。第一部を親とする第二節、第一節への時間規約参照を保持する。',
            '二原理の呼称、採用、後続範囲、直後の定式化の予告を結ぶ。導入部の電磁気学・光学に関する表現と一般の物理系の定式化を論理的同値とは主張しない。',
            '第一原理は比較可能な系の非空性、同一の理論、全対象系対・法則・履歴・両表現にわたる量化を保持する。軸名だけから系間の方向一致を導かない。',
            '第二原理は同じ静止系と同じ光速値、放出元の静止・運動の排他分類、各区間の真空条件と時刻規約を保持する。',
            '速度の定義は幾何学的光路長を正の時間差で割る。一方向の区間を往復へ替えず、係数2を追加しない。定義の速度を定数tcへ固定しない。',
            '十二の区間欄は公開記録の成分に集約し、原文の関数を文書内の転送定義として残して引用の識別も保持する。'],
        profile_edition=26,core_edition=12,new_source_assertions=5,total_source_assertions=32,annotations=8,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible two-principles document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*ROLE_ASSIGNMENTS,*HEADINGS,*DESIGNATIONS,*AXES)}|{'eisd2':'firstsectionheading'}


def role_model(values):
    return previous.role_model(values)|{(values['eirf'],values[ROLE_ASSIGNMENTS[old][0]],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
        for old,role in reference_roles().items()}


def context_handlers(values,roles=None):
    from scripts.discourse_setting_profile import DiscourseReferences
    from scripts.temporal_discourse_profile import TemporalReferences
    from scripts.designation_purpose_profile import DesignationReferences
    result=previous.context_handlers(values)
    positions=previous.previous.previous.SENTENCES|previous.previous.SENTENCES|previous.SENTENCES|SENTENCES
    layout={(values['ri'],4,1):'setting',(values['ri'],6,4):values['eisfm']}|{(values['ri'],*pos):values[old] for old,pos in positions.items()}
    headings={(values['ri'],i):values[old] for old,i in (HEADINGS|{'eisd2':2}).items()}
    refs=DiscourseReferences({values['eirf']:values['ri']},headings,layout,{(values['eirf'],'setting',1,values['ri']):'frame'})
    temporal=TemporalReferences(role_model(values) if roles is None else roles,{})
    designations=DesignationReferences({(values['eirf'],values[node],i,values['ri']):values[old] for old,(node,i) in DESIGNATIONS.items()})
    axes=profile.PrincipleRecords(axes={('frame',values['ri']):tuple(values[n] for n in AXES)})
    return result|refs.handlers()|temporal.handlers()|designations.handlers()|axes.handlers()


def attribution_facts():
    return dict(eisdv=[('eisk2','eiskz','eisdx','doc',2,2,'body')],
        eisdw=[('eisk2','eiskz',('function_ref','eiob'),'body')],
        eir3=[(node,'author','doc',('call',content),'body') for node,content in [('wu','eiof'),('vk','eiop'),('wt','eio3'),('eisll','eio5')]],
        eislk=[('vk','wu',1,'doc','body'),('wt','wu',2,'doc','body')],
        eisa5=[('eisll','author',('call','eiot'),('call','eioz'),'body')],
        ue=[('eiskt','eisk2','body'),('eisk2','wu','body'),('wu','vk','body'),('vk','wt','body'),('wt','eisll','body')])



def attribution_case(changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=attribution_facts()
    slots=dict(eisdw=(2,),eir3=(3,),eisa5=(2,3))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted two-principles content was executed')
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):
                node=json.loads(args[i].syntax)
                if not original:node=renamed(node,{v:k for k,v in mapping().items()})
                args[i]=(node['kind'],node['symbol']) if node.get('kind')=='function_ref' or (node.get('kind')=='call' and not node['arguments']) else ('different',)
            for i in dict(eisdv=(4,5),eislk=(2,)).get(name,()):args[i]=int(args[i])
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=source_excerpt();h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][32:37]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=('front','body'),primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Light-speed-time attribution differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[attribution_case()];require(rows[0]['values']==[True]*5,'Baseline attribution differs')
    for field in ('rd','eirf','ri','eiskt','eisk2','eisdx','eiskz','wu','vk','wt','eisll'):
        row=attribution_case({field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored context role: '+field);rows.append(row)
    effects=dict(eisdv=(0,),eisdw=(0,),eir3=(1,2,3,4),eislk=(2,3),eisa5=(4,),ue=(0,1,2,3,4))
    for relation,indices in effects.items():
        row=attribution_case(failed=relation);require(row['values']==[i not in indices for i in range(5)],'Wrong discourse relation scope: '+relation);rows.append(row)
    return rows



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published two-principles bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved two-principles bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-light-speed-time-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/two_principles_profile.py','scripts/two_principles_contracts.py','scripts/check_einstein_two_principles.py',
        'scripts/visible_two_principles_collection.py','tests/test_two_principles_profile.py','docs/einstein-two-principles-v1.md'}
    for path in READINGS:paths.update(author.read(path)['images'])
    return dict(schema='noema-einstein-two-principles-evidence-1',core_words=375,profile_words=632,profile_edition=26,
        preserved_source_relations=51,reused_source_relations=1,forwarded_fields=12,new_reference_primitives=3,new_source_assertions=5,total_source_assertions=32,annotations=8,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
