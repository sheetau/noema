"""Connect the rod setting, imagined motion and two-method question."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import rod_experiment_profile as profile
from scripts.rod_experiment_profile import ROOT,RodExperimentVocabulary,write_once,CUT
from scripts import check_einstein_two_principles as previous
from scripts import check_einstein_name_presentation as author
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.shared_reference import definition
from scripts.shared_time import allof
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require
from scripts.check_einstein_temporal_discourse import canonical

SOURCE='examples/v016/einstein-rod-experiment-v1.noema'
BRIDGE='data/einstein-rod-experiment-bridge-v1.json'
OUT=ROOT/'output/einstein-rod-experiment-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiae eiah eio7 eipa eipb eipc eipd eipe eipf eipg eiph eipi eipj eipk eipl eipm eipn eipo eipp eipq eipr eips eipt eipu eipv sat sbe sbf sbg sbh sbi sbj sbk sbm sbo sbp sbq sbu sbv'.split()
SENTENCES=dict(y2=(19,1),eisly=(19,2),y3=(19,3),xw=(20,1),xx=(21,1))
ROLE_ASSIGNMENTS=dict(xi=('y2','rod'),xj=('y2','ruler'),xk=('xw','observer'),xl=('xw','comoving'),xy=('y2','scope'))
SETTING_ASSIGNMENTS=dict(yc=('y2','initial'),eislr=('eisly','placed'),yd=('eisly','moving'),ye=('xw','methoda'),yf=('xx','methodb'))
CUT_ASSIGNMENTS=dict(ya=('y2','length'),yb=('eisly','speed'))
FIELDS={n:('endpointmeasuremententity',i) for i,n in enumerate('xn xo xp xq xr xs xt xu'.split())}|{n:('endpointmeasurementreading',i) for i,n in enumerate('x2 x3 xv'.split())}
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*ROLE_ASSIGNMENTS,*SETTING_ASSIGNMENTS,*CUT_ASSIGNMENTS,*FIELDS,
    *['rodrole'+r for _,r in (ROLE_ASSIGNMENTS|SETTING_ASSIGNMENTS|CUT_ASSIGNMENTS).values()]]
READINGS=('data/einstein-rod-experiment-source-reading-v1.json',)
REVIEWS=('data/einstein-rod-experiment-review-v1.json',)
FORMS={}
qf=previous.qf
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY



@lru_cache(maxsize=1)
def vocabulary():return RodExperimentVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][88:91]):visit(n)
    require(len(seen)==179,'Rod-experiment source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][88:91])))


@lru_cache(maxsize=1)
def names():
    n=dict(previous.names());proper=set(SENTENCES)|set(ROLE_ASSIGNMENTS)|{n for n,(field,_) in FIELDS.items() if field=='endpointmeasuremententity'}
    parts=previous.previous.previous.previous.previous.PARTS
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','book','town',parts[i//16],parts[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:previous.previous.previous.previous.previous.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def reference_roles(assignments=ROLE_ASSIGNMENTS):return {old:names()['rodrole'+role] for old,(_,role) in assignments.items()}


def role_definitions():
    n=names();m=mapping();x=v('va');s=v('vb');k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    individuals=dict(rod=r('xa',x),ruler=r('xc',x),observer=r('xb',x),
        comoving=allof(r('va',x),*[r('x4',k(old),x,k('ye')) for old in ('xi','xj','xk')]),
        scope=r('ug',k('y2'),k('rd'),dict(kind='quote',body=k('eipl')),x,s))
    settings=dict(initial=op('and',r('x4',k('xi'),k('ra'),x),r('x4',k('xj'),k('ra'),x)),
        placed=r('eislx',k('xi'),k('yc'),x),moving=r('yv',k('xi'),k('eislr'),x),
        methoda=r('yx',k('yd'),x),methodb=r('yx',k('yd'),x))
    length=op('and',r('sbg',x),dict(kind='exists',variable='vc',sort='individual',
        body=op('and',r('xb',v('vc')),r('xe',v('vc'),k('xj'),k('xi'),k('ra'),k('ta'),x,k('yc')))))
    # Parameterize the existing complete motion condition, rather than naming
    # another primitive for the sentence or selecting an arbitrary numeric speed.
    body=next(d for d in source_excerpt()['declarations'] if d['name']=='eipk')['body']
    def substitute(node):
        if isinstance(node,list):return [substitute(item) for item in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='variable' and node.get('name')=='va':return call('yd')
        if node.get('kind')=='call' and node.get('symbol')=='yb':return v('va')
        return {key:substitute(value) for key,value in node.items()}
    cuts=dict(length=length,speed=renamed(substitute(body),m))
    return [definition(n['rodrole'+name],[('va',sort),('vb','situation')],'truth',body)
        for sort,bodies in [('individual',individuals),('situation',settings),(CUT,cuts)] for name,body in bodies.items()]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    for assignments,primitive,sort in [(ROLE_ASSIGNMENTS,'describedreference','individual'),
            (SETTING_ASSIGNMENTS,'describedsettingreference','situation'),(CUT_ASSIGNMENTS,'describedcutreference',CUT)]:
        for old,role in reference_roles(assignments).items():
            node=assignments[old][0]
            doc['declarations'].append(definition(n[old],[],sort,call(voc._symbols[primitive],k('eirf'),k(node),qf(role),k('ri'))))
    for old,(field,slot) in FIELDS.items():
        result='individual' if field=='endpointmeasuremententity' else CUT
        doc['declarations'].append(definition(n[old],[],result,call(voc._symbols[field],k('xi'),k('ra'),k('yf'),author.num(slot))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(previous.previous.previous.previous.previous.FIELDS)|set(previous.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][40:43],inverse);return normalize_document(result)



@lru_cache(maxsize=1)
def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations'])
    rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():
        require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0])
    row=reading['segments'][0];unit=units[row['unit']];a,b=row['range']
    require(row['unit']=='einstein-1905:u0029' and row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][a:b],'Original reading differs')
    require(a==0 and b==len(unit['text']),'Incomplete source unit')
    for sentence in reading['sentences']:
        left,right=sentence['range'];require(sentence['text']==unit['text'][left:right],'Sentence reading differs')
    require([s['range'] for s in reading['sentences']]==[[0,126],[127,380],[381,496]],'Sentence boundaries changed')
    require([m['id'] for m in row['math']]==['M0043','M0044','M0045','M0046','M0047'],'Math attachments changed')
    for path in REVIEWS:
        review=author.read(path)
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-rod-experiment-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[88,89,90],source_units={unit['id']:dict(sha256=unit['text_sha256'],text=unit['text'],range=[a,b])},
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_positions={n:list(pos) for n,pos in SENTENCES.items()},sentence_ranges=[s['range'] for s in reading['sentences']],math=row['math'],
        reference_roles=reference_roles(),setting_roles=reference_roles(SETTING_ASSIGNMENTS),cut_roles=reference_roles(CUT_ASSIGNMENTS),
        role_definitions=role_definitions(),endpoint_fields={n:[field,slot] for n,(field,slot) in FIELDS.items()},
        reused_argument_labels=dict(introducesreferent=dict(source=profile.CONTRACTS['introducesreferent']['arguments'],public=profile.REUSED_ARGUMENTS['introducesreferent'])),
        semantic_review=[
            '三文を段落19に置く。初期設定を置く指示、配置と運動の想定を述べる文、長さへの問いと二方法で調べる想定を述べる文を区別する。',
            '初期測定yc、配置後eislr、運動後yd、二方法ye/yfを別々の設定として参照する。取得は設定の物理的実在や内容の真理を主張しない。',
            '同じ棒・物差し・静止系・長さ単位・時間単位を保つ。初期観測者は存在だけを要求し、後の観測者や静止観測者へ固定しない。',
            '初期長は正の直接測定の読みとして参照し、数値を補わない。速度は元のeipkの完全な運動条件から値をパラメータ化した役割で参照し、正のX方向と全物質点への適用を保持する。',
            '配置後には初期長を保つが運動後には固定しない。加速機構・加速中の剛性・実現可能性を追加しない。端面中心は幾何学的標識を許し、棒の厚みを零にしない。',
            '方法a/bは後続段落20/21の第一文へ前方参照し、同じ運動設定を継承する。候補判定と問いを保持し、値の存在・唯一性・一致、実際の測定完了を導かない。',
            '二端点の出来事・時計・場所・読み・指定時刻を同じ物体/系/測定設定の公開記録へまとめる。未知の記録や欄を補わず、時刻一致や同期は本文の条件として残す。'],
        profile_edition=27,core_edition=12,new_source_assertions=3,total_source_assertions=35,annotations=8,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)



@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible rod-experiment document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*ROLE_ASSIGNMENTS,*[n for n,(field,_) in FIELDS.items() if field=='endpointmeasuremententity'])}|dict(ra='frame',yc='initial',eislr='placed',yd='moving',ye='methoda',yf='methodb')
SITUATIONS=('front','body','initial','placed','moving','methoda','methodb')


def model_roles(values,assignments):
    return {(values['eirf'],values[assignments[old][0]],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
        for old,role in reference_roles(assignments).items()}


def role_model(values):return previous.role_model(values)|model_roles(values,ROLE_ASSIGNMENTS)


def cut_model(values):
    return {(values['eirf'],values[node],canonical(dict(kind='function_ref',symbol=reference_roles(CUT_ASSIGNMENTS)[old])),values['ri']):FunctionValue(('number',),'truth',lambda q:q<1)
        for old,(node,_) in CUT_ASSIGNMENTS.items()}


def context_handlers(values,roles=None,settings=None,cuts=None,records=None):
    from scripts.discourse_setting_profile import DiscourseReferences
    from scripts.temporal_discourse_profile import TemporalReferences
    from scripts.light_speed_time_profile import CutReferences
    result=previous.context_handlers(values)
    positions=previous.previous.previous.previous.SENTENCES|previous.previous.previous.SENTENCES|previous.previous.SENTENCES|previous.SENTENCES|SENTENCES
    layout={(values['ri'],4,1):'setting',(values['ri'],6,4):values['eisfm']}|{(values['ri'],*pos):values[old] for old,pos in positions.items()}
    headings={(values['ri'],i):values[old] for old,i in (previous.HEADINGS|{'eisd2':2}).items()}
    refs=DiscourseReferences({values['eirf']:values['ri']},headings,layout,{(values['eirf'],'setting',1,values['ri']):values['ra']})
    temporal=TemporalReferences(role_model(values) if roles is None else roles,{})
    setting=profile.SettingReferences(model_roles(values,SETTING_ASSIGNMENTS) if settings is None else settings)
    cutrefs=CutReferences(cut_model(values) if cuts is None else cuts)
    if records is None:
        key=(values['xi'],values['ra'],values['yf'])
        records=profile.RodExperimentRecords(entities={key:tuple(values[n] for n,(field,_) in FIELDS.items() if field=='endpointmeasuremententity')},
            readings={key:[FunctionValue(('number',),'truth',lambda q:q<1) for _ in range(3)]})
    return result|refs.handlers()|temporal.handlers()|setting.handlers()|cutrefs.handlers()|records.handlers()


def attribution_facts():
    return dict(eir3=[(node,'author','doc',('call',content),'body') for node,content in [('y2','eipo'),('eisly','eipr'),('y3','eipu')]],
        ue=[('eisll','y2','body'),('y2','eisly','body'),('eisly','y3','body')])



def attribution_case(changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=attribution_facts()
    slots=dict(eir3=(3,))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted rod-experiment content was executed')
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):
                node=json.loads(args[i].syntax)
                if not original:node=renamed(node,{v:k for k,v in mapping().items()})
                args[i]=(node['kind'],node['symbol']) if node.get('kind')=='function_ref' or (node.get('kind')=='call' and not node['arguments']) else ('different',)
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=source_excerpt();h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][40:43]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=SITUATIONS,primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Rod-experiment attribution differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[attribution_case()];require(rows[0]['values']==[True]*3,'Baseline attribution differs')
    for field in ('rd','eirf','ri','eisll','y2','eisly','y3'):
        row=attribution_case({field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored context role: '+field);rows.append(row)
    for relation in ('eir3','ue'):
        row=attribution_case(failed=relation);require(row['values']==[False]*3,'Wrong discourse relation scope: '+relation);rows.append(row)
    return rows


def presentation_facts():
    return dict(eisd3=[('y2','xi','doc','body'),('y2','xj','doc','body')],
        ug=[('y2','author',('call','eipl'),'xy','body'),('eisly','author',('call','eipm'),'xy','body')],
        eislz=[('eisly','author',('call','eipm'),'xy','body')],
        yz=[('y3','author',('call','sbv'),'xy','body')],
        eiskw=[('y3',('function_ref','th'),'body')],
        eisl2=[('y3','author','xi','frame','moving',('function_ref','eipk'),('call','sbv'),('xw','xx'),'xy','doc','body')],
        eiskj=[('xw','y3',1,'doc','body'),('xx','y3',2,'doc','body')],
        ue=[('y3','xw','body'),('xw','xx','body')])


def presentation_case(changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=presentation_facts()
    slots=dict(ug=(2,),eislz=(2,),yz=(2,),eiskw=(1,),eisl2=(5,6))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted rod experiment was executed')
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):
                node=json.loads(args[i].syntax)
                if not original:node=renamed(node,{v:k for k,v in mapping().items()})
                args[i]=(node['kind'],node['symbol']) if node.get('kind')=='function_ref' or (node.get('kind')=='call' and not node['arguments']) else ('different',)
            if name=='eisl2':args[7]=tuple(args[7].items)
            if name=='eiskj':args[2]=int(args[2])
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))))
            return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=deepcopy(source_excerpt());h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
            selected=lambda name:call(name)
        else:
            doc=deepcopy(restored()['document']);h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
            selected=lambda name:call(mapping()[name])
        doc['statements']=[dict(kind='ask',body=dict(kind='evaluate',content=selected(name),situation=selected('ri'))) for name in ('eipn','eipq','eipt')]
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=SITUATIONS,primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Rod presentation differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def presentation_diagnostics():
    rows=[presentation_case()];require(rows[0]['values']==[True]*3,'Baseline presentation differs')
    for field in ('rd','eirf','ri','xi','xj','xy','y2','eisly','y3','xw','xx','yd','ra'):
        value='front' if field=='ri' else 'initial' if field=='yd' else 'other'
        row=presentation_case({field:value});require(not all(row['values']),'Ignored presentation role: '+field);rows.append(row)
    effects=dict(eisd3=(0,),ug=(0,1),eislz=(1,),yz=(2,),eiskw=(2,),eisl2=(2,),eiskj=(2,),ue=(2,))
    for relation,indices in effects.items():
        row=presentation_case(failed=relation);require(row['values']==[i not in indices for i in range(3)],'Wrong presentation relation scope: '+relation);rows.append(row)
    return rows



def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published rod-experiment bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved rod-experiment bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-two-principles-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/rod_experiment_profile.py','scripts/rod_experiment_contracts.py','scripts/check_einstein_rod_experiment.py',
        'scripts/visible_rod_experiment_collection.py','tests/test_rod_experiment_profile.py','docs/einstein-rod-experiment-v1.md'}
    for path in READINGS:paths.update(author.read(path)['images'])
    return dict(schema='noema-einstein-rod-experiment-evidence-1',core_words=375,profile_words=660,profile_edition=27,
        preserved_source_relations=26,reused_source_relations=1,endpoint_fields=11,new_reference_primitives=3,new_source_assertions=3,total_source_assertions=35,annotations=8,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),presentation_diagnostics=presentation_diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
