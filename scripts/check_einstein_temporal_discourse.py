"""Connect the four temporal-discourse sentences and their author's footnote."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,DescriptionValue
from noema.meaning_catalog import _references
from scripts import temporal_discourse_profile as profile
from scripts.temporal_discourse_profile import ROOT,TemporalDiscourseVocabulary,TemporalReferences,write_once
from scripts import check_einstein_physical_position as previous
from scripts import check_einstein_name_presentation as author
from scripts.check_manuscript_context import catalogs
from scripts.check_visible_specialist_library import LIBRARY as MATH_LIBRARY,authoring_vocabulary
from scripts.shared_vectors import MAPPING as MATH
from scripts.shared_modality import call,renamed,v
from scripts.shared_reference import definition
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-temporal-discourse-v1.noema'
BRIDGE='data/einstein-temporal-discourse-bridge-v1.json'
OUT=ROOT/'output/einstein-temporal-discourse-v1'
LABEL=Word('proper',('above','book','give','book','red'))
RELATIONS=previous.RELATIONS|previous.previous.PREDICATES|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=('da db eihm eii2 eii3 eii4 eii5 eii6 eii7 eiii eiij eiik eiil eiim eiin eiio eiip eiiq eiir eiis eiit eiiu eiiv eiiw eiix eiiy eiiz eija eijb eijc eijd eije eijf eijg qm qn qo sad sae saf seg seh').split()
SENTENCES=dict(eiset=1,eiseu=2,eise3=3,eisfm=4)
REFERENTS=('eisff','eisfg','eisfh','eisfi','eisfj','eisfk','eisfl','eisfv')
FIELDS=tuple(profile.FIELD_CONTRACTS)
ROLE_HELPERS=('roleclock','rolehand','roleplace','roleunit','rolearrival','roledisplay','roleissue')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,'eisfn',*REFERENTS,*FIELDS,*ROLE_HELPERS]
PARTS=('rain','town','home','above','give','inside','birdone','treeone','aki','nao','book','fruit','red','round','bird','fly')


@lru_cache(maxsize=1)
def vocabulary():return TemporalDiscourseVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][60:65]):visit(n)
    require(len(seen)==148,'Temporal closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],
        statements=deepcopy(c.document['statements'][60:65])))


def names():
    result=previous.names()
    proper=set(SENTENCES)|set(REFERENTS)|{'eisfn'}
    for i,old in enumerate(LOCAL_NAMES):
        result[old]=symbol(Word('proper' if old in proper else 'compound',
            ('above','book','give',PARTS[i//16],PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision')
    return result


def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency')
    result={old:candidates[old] for old in selected};require(len(set(result.values()))==len(result),'Source names merged');return result


def field_definitions():
    n=names();voc=vocabulary();ds=[]
    for index,old in enumerate(FIELDS):
        function='roundtripentity' if index<6 else 'roundtripreading';slot=index if index<6 else index-6
        ds.append(definition(n[old],[('va','individual')],profile.FIELD_CONTRACTS[old]['result'],
            call(voc._symbols[function],v('va'),author.num(slot))))
    return ds


def role_definitions():
    n=names();m=mapping();I='individual';S='situation';x=v('va');ctx=v('vb')
    bodies=dict(
        roleclock=call(m['eise6'],x,call(n['rd']),ctx),
        rolehand=call(m['eise7'],x,call(n['eisfg']),ctx),
        roleplace=call(m['eise5'],x,call(n['rd']),ctx),
        roleunit=call(m['eisfa'],call(n['eisfg']),call(n['eisfh']),x,ctx),
        rolearrival=call(m['eisfb'],x,call(n['eisff']),call(n['eisfi']),call(n['ra']),ctx),
        roledisplay=call(m['eisfc'],x,call(n['eisfh']),call(n['eisfg']),call(m['bb'],author.num(7)),ctx),
        roleissue=call(m['eisfq'],x,quote_function(n['eihm']),quote_function(n['eijd']),call(n['eirf']),ctx))
    return [definition(n[key],[('va',I),('vb',S)],'truth',bodies[key]) for key in ROLE_HELPERS]


def quote_function(name):return dict(kind='quote',body=dict(kind='function_ref',symbol=name))


def reference_roles():
    n=names();return dict(eisff=mapping()['eise4'],eisfg=n['roleclock'],eisfh=n['rolehand'],
        eisfi=n['roleplace'],eisfj=n['roleunit'],eisfk=n['rolearrival'],eisfl=n['roledisplay'],eisfv=n['roleissue'])


@lru_cache(maxsize=1)
def document():
    n=names();m=mapping();voc=vocabulary();doc=deepcopy(previous.document())
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    doc['declarations']+=field_definitions()+role_definitions()
    for old,index in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],call(n['ri']),author.num(6),author.num(index))))
    doc['declarations'].append(definition(n['eisfn'],[],'individual',call(voc._symbols['footnotereference'],
        call(n['eirf']),call(n['eisfm']),author.num(1),call(n['ri']))))
    for old,role in reference_roles().items():
        node='eisfn' if old=='eisfv' else 'eisfm'
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],
            call(n['eirf']),call(n[node]),quote_function(role),call(n['ri']))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(migrated):
    require(migrated==document(),'Changed migration cannot be rebound to old evidence')
    ds={d['name']:d for d in migrated['declarations']};m=mapping();inverse={v:k for k,v in m.items()}
    result=deepcopy(source_excerpt())
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in FIELDS or d['name']=='zz4') else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(migrated['statements'][6:],inverse);return normalize_document(result)


def bridge():
    c=catalogs()['einstein-1905'];units=author.read(author.UNITS)['units']
    paragraph=[u for u in units if u['kind']=='body'][5];note=next(u for u in units if u['id']=='einstein-1905:u0279')
    require(paragraph['id']=='einstein-1905:u0010' and len(paragraph['text'])==666,'Temporal paragraph changed')
    review=author.read('data/einstein-time-paragraph-review-v1.json')
    require(review['source']['unit_sha256']==paragraph['text_sha256'] and review['source']['text']==paragraph['text'],'Paragraph reading differs')
    reading=author.read('data/einstein-time-continuation-source-reading-v1.json')
    note_reading=next(row for row in reading['segments'] if row['unit']==note['id'])
    require(note_reading['text']==note['text'] and note_reading['unit_sha256']==note['text_sha256'],'Footnote reading differs')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Temporal contract changed: '+old)
    for old in FIELDS:
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1]
        require(profile.FIELD_CONTRACTS[old]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Trial field contract changed')
    require(backprojection(document())==source_excerpt(),'Temporal source projection differs')
    ranges=[[0,126],[127,337],[338,481],[482,666]]
    require(all(paragraph['text'][a:b]==' ' for a,b in ((126,127),(337,338),(481,482))),'Sentence gap changed')
    return dict(schema='noema-einstein-visible-temporal-discourse-bridge-1',reviewer='assistant',source_statement_indices=list(range(60,65)),
        source_document=c.document_path,source_units=[dict(unit=paragraph['id'],sha256=paragraph['text_sha256'],text=paragraph['text'],ranges=ranges),
            dict(unit=note['id'],sha256=note['text_sha256'],text=note['text'],ranges=[note_reading['range']])],
        source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        contextual_roles=reference_roles(),field_definitions=field_definitions(),role_definitions=role_definitions(),
        reference_bindings=dict(sentences='body paragraph 6, sentences 1 through 4',note='author note 1 attached to sentence 4',
            participants='role descriptions at the same example node',issue='concept-imprecision role at the note node'),
        semantic_review=[
            '運動を記述する意図を前件とし、同じ点の三座標を同じ時間の関数として提示する方法を保つ。',
            '数学的記述の物理的意味には、同じ時間解釈についての理解が先に必要である。記述や理解の実施済みを補わない。',
            '時間が関わる全判断について、同じ対象・肯否・量化・条件を保持した同時性による説明を扱う。方法上の考慮要請を遵守済みに替えない。',
            '列車・時計・短針・ここ・時の単位・到着・表示の役割を本文定義で結び、原語の文字列で内容を代用しない。7時の周期表示と出来事の同時性を保つ。',
            '発言例の前件とおおよその約言を保持し、二内容の真理や厳密な同値を要求しない。',
            '脚注の局所同時性の不精密さ、抽象化による処理の必要性、この箇所では論じない方針、添加の意味を保つ。',
            '原文一覧末尾の脚注位置を本文順序にせず、第四文の注番号から参照する。脚注対応の関係の成立は参照取得と別に要求する。',
            '光往復の九項目は二つの型付き記録取得関数と九つの本文定義にまとめ、旧名・役割・値の型を保持する。'],
        preserved_source_relations=49,replaced_trial_field_primitives=9,record_component_primitives=2,new_reference_primitives=2,
        newly_connected_source_assertions=5,total_connected_source_assertions=9,orthographic_annotation_assertions=2,
        profile_edition=22,core_edition=12,original_manuscript_modified=False,old_judgments_rebound=False,
        full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible temporal discourse differs');return result


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def context_handlers(values,roles=None):
    from scripts.discourse_setting_profile import DiscourseReferences
    model=author.NamePresentation('front',{('front',2):('other','other',values['rd'],values['eirf'])},
        presented={},applied={},authors={},forms={})
    layout={(values['ri'],5,1):values['eisel']}|{(values['ri'],6,i):values[old] for old,i in SENTENCES.items()}
    refs=DiscourseReferences({values['eirf']:values['ri']},{},layout,{})
    temporal=TemporalReferences(roles or {},{(values['eirf'],values['eisfm'],1,values['ri']):values['eisfn']})
    return model.handlers()|refs.handlers()|temporal.handlers()


BASE=dict(rd='author',eirf='doc',ri='body',eisel='preceding',eiset='s1',eiseu='s2',eise3='s3',eisfm='s4',eisfn='note')
DOMAIN=('author','doc','preceding','s1','s2','s3','s4','note','other')


def attribution_case(changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[]
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted temporal content was executed')
        def described(value):
            node=json.loads(value.syntax)
            if not original:node=renamed(node,{v:k for k,v in mapping().items()})
            return node['symbol'] if node.get('kind')=='call' and not node['arguments'] else 'different'
        def relation(name,args,rows,description_slots=()):
            normalized=list(args)
            for index in description_slots:normalized[index]=described(args[index])
            normalized=[int(x) if isinstance(x,Fraction) and x.denominator==1 else x for x in normalized]
            trace.append(dict(relation=name,arguments=normalized));return name!=failed and tuple(normalized) in rows
        relations=dict(
            eir3=lambda node,agent,doc,msg,ctx:relation('eir3',(node,agent,doc,msg,ctx),
                {(node,'author','doc',message,'body') for node,message in zip(('s1','s2','s3','s4','note'),('eiin','eiis','eiiz','eijb','eijf'),strict=True)},(3,)),
            ue=lambda a,b,s:relation('ue',(a,b,s),{(a,b,'body') for a,b in zip(('preceding','s1','s2','s3'),('s1','s2','s3','s4'),strict=True)}),
            zei=lambda node,agent,scope,ctx:relation('zei',(node,agent,scope,ctx),{('s2','author','doc','body')}),
            eir5=lambda node,agent,prior,target,ctx:relation('eir5',(node,agent,prior,target,ctx),{('s4','author','s3','eija','body')},(3,)),
            eisfo=lambda node,note,doc,num,ctx:relation('eisfo',(node,note,doc,num,ctx),{('s4','note','doc',1,'body')}))
        if original:
            doc=source_excerpt();handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            handlers.update({n:lambda value=value:value for n,value in values.items()});handlers.update(relations)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][6:]
            handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            handlers.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()})
            handlers.update({mapping()[old]:f for old,f in relations.items()})
        answer=evaluate_document(doc,individuals=DOMAIN,situations=('front','body'),primitives=handlers)
        answers.append(answer)
    require(answers[0]==answers[1] and traces[0]==traces[1],'Temporal attribution binding differs')
    return dict(changed=changed or {},failed=failed,values=[a['value'] for a in answers[0]],calls=traces[0])


def diagnostics():
    rows=[attribution_case()]
    require(rows[0]['values']==[True]*5,'Baseline temporal attribution differs')
    for field in BASE:
        row=attribution_case({field:'front' if field=='ri' else 'other'});require(not all(row['values']),'A contextual role was ignored');rows.append(row)
    expected=dict(eir3=[False]*5,ue=[False]*4+[True],zei=[True,False,True,True,True],
        eir5=[True,True,True,False,True],eisfo=[True,True,True,False,False])
    for relation,values in expected.items():
        row=attribution_case(failed=relation);require(row['values']==values,'Presentation relation has wrong scope');rows.append(row)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Temporal bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-physical-position-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,MATH_LIBRARY,
        'scripts/temporal_discourse_profile.py','scripts/temporal_discourse_contracts.py','scripts/check_einstein_temporal_discourse.py',
        'scripts/visible_temporal_discourse_collection.py','tests/test_temporal_discourse_profile.py','docs/einstein-temporal-discourse-v1.md',
        'data/einstein-time-paragraph-review-v1.json','data/einstein-time-continuation-source-reading-v1.json'}
    return dict(schema='noema-einstein-temporal-discourse-evidence-1',core_words=375,profile_words=462,profile_edition=22,
        preserved_source_relations=49,replaced_trial_field_primitives=9,record_component_primitives=2,new_reference_primitives=2,
        newly_connected_source_assertions=5,total_connected_source_assertions=9,orthographic_annotation_assertions=2,
        declarations=len(document()['declarations']),statements=len(document()['statements']),
        pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),full_real_domain_evaluated=False,
        full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
