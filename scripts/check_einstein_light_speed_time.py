"""Connect empirical light speed and the naming of rest-system time."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import light_speed_time_profile as profile
from scripts.light_speed_time_profile import ROOT,LightSpeedTimeVocabulary,write_once,CUT
from scripts import check_einstein_synchrony as previous
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

SOURCE='examples/v016/einstein-light-speed-time-v1.noema'
BRIDGE='data/einstein-light-speed-time-bridge-v1.json'
OUT=ROOT/'output/einstein-light-speed-time-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='ein2 ein3 ein4 ein5 ein6 einq einr eins eint einu einv einw einx einy einz sai sak sal sam san'.split()
SENTENCES=dict(tm=(14,1),eiskt=(15,1))
ROLE_ASSIGNMENTS=dict(ta='lengthunit',tb='speedunit',tn='experience')
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*ROLE_ASSIGNMENTS,'tc','eisks',*['speedrole'+n for n in ROLE_ASSIGNMENTS.values()]]
READINGS=('data/einstein-empirical-light-constant-source-reading-v1.json','data/einstein-rest-system-time-source-reading-v1.json')
REVIEWS=tuple('data/einstein-empirical-light-constant-u00'+n+'-review-v1.json' for n in ('19','20','21'))+('data/einstein-rest-system-time-review-v1.json',)
FORMS=dict(eisks='die Zeit des ruhenden Systems')
qf=previous.qf
MATH=previous.previous.previous.MATH
MATH_LIBRARY=previous.previous.previous.MATH_LIBRARY


@lru_cache(maxsize=1)
def vocabulary():return LightSpeedTimeVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][81:83]):visit(n)
    require(len(seen)==119,'Light-speed-time source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][81:83])))


@lru_cache(maxsize=1)
def names():
    n=dict(previous.names());proper=set(SENTENCES)|set(ROLE_ASSIGNMENTS)|{'eisks'}
    parts=previous.previous.previous.PARTS
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','book','treeone',parts[i//16],parts[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:previous.previous.previous.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def reference_roles():return {old:names()['speedrole'+role] for old,role in ROLE_ASSIGNMENTS.items()}


def role_definitions():
    n=names();m=mapping();x=v('va');s=v('vb');k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    bodies=dict(lengthunit=r('ti',x),speedunit=r('tj',k('ta'),k('rb'),x),experience=r('to',k('tm'),k('rd'),x,k('eirf'),s))
    return [definition(n['speedrole'+name],[('va','individual'),('vb','situation')],'truth',body) for name,body in bodies.items()]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    for old,role in reference_roles().items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],k('eirf'),k('tm'),qf(role),k('ri'))))
    doc['declarations'].append(definition(n['eisks'],[],'individual',call(voc._symbols['designationreference'],k('eirf'),k('eiskt'),author.num(1),k('ri'))))
    doc['declarations'].append(definition(n['tc'],[],CUT,call(voc._symbols['describedcutreference'],k('eirf'),k('tm'),qf(n['san']),k('ri'))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k('eisks'),author.text_expression('de'),author.text_expression(FORMS['eisks']),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in previous.previous.previous.FIELDS or d['name']=='zz4') else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][29:31],inverse);return normalize_document(result)


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
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(19,23)},'Source units changed')
    light=author.read(READINGS[0]);rest=author.read(READINGS[1]);equation=light['segments'][1]['math'][0]
    require(equation['id']=='M0040' and equation['definition']=='eins' and equation['bindings']==dict(A_place='ziq',B_place='zir',departure='eisjo',**{'return':'eisjq'},distance='tg(eisjj)',V='tc'),'Equation binding changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-light-speed-time-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[81,82],source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],
        mapping=mapping(),sentence_positions={n:list(pos) for n,pos in SENTENCES.items()},reference_roles=reference_roles(),role_definitions=role_definitions(),
        cut_reference=dict(value='tc',node='tm',role='san',numeric_value_supplied=False),
        equation_attachment=dict(node='tm',units=['einstein-1905:u0019','einstein-1905:u0020','einstein-1905:u0021'],math=equation,one_sentence=True,one_paragraph=True),
        page_continuation=dict(node='eiskt',pages=['894','895'],one_sentence=True,annotations=rest['editorial_annotations']),
        printed_designations=FORMS,identifier_annotations=annotations(),
        semantic_review=['導入節・数式・続きの文は一文かつ一段落である。収録単位を段落として数えず、tm=(14,1)、eiskt=(15,1)へ結ぶ。',
            '同じ静止系の全適用光往復に共通の一つの値を、非空性・範囲の完全性・普遍性を保持したsanの役割で参照する。値を試行ごとに取り替えず、数値を補わない。',
            '同じ代表往復のA側出発・帰着の差、正の一方向距離の二倍、両区間の真空条件と整合単位を保持する。反射時刻を分母に入れず、同期式を追加しない。',
            '経験に従う追加採用と括弧内の同じ速度への説明を保持する。参照の成立は役割の真理、実測済み、実数妥当性や唯一性を含意しない。',
            '直前に定義した同じ時間規約と同じ静止系への条件を維持する。重要性の提示を論理的必然性へ替えず、系への依存から命名への理由を逆転しない。',
            '呼称は識別表記だけを綴り注記にし、時計と系への条件は合成定義で保持する。原刊の改頁標識を新しい命題としない。'],
        profile_edition=25,core_edition=12,new_source_assertions=2,total_source_assertions=27,annotations=5,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible light-speed-time document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*ROLE_ASSIGNMENTS,'eisks')}


def role_model(values):
    return previous.role_model(values)|{(values['eirf'],values['tm'],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
        for old,role in reference_roles().items()}


def context_handlers(values,roles=None,cut_roles=None):
    from scripts.discourse_setting_profile import DiscourseReferences
    from scripts.temporal_discourse_profile import TemporalReferences
    from scripts.designation_purpose_profile import DesignationReferences
    result=previous.context_handlers(values)
    positions=previous.previous.SENTENCES|previous.SENTENCES|SENTENCES
    layout={(values['ri'],4,1):'setting',(values['ri'],6,4):values['eisfm']}|{(values['ri'],*pos):values[old] for old,pos in positions.items()}
    refs=DiscourseReferences({values['eirf']:values['ri']},{},layout,{(values['eirf'],'setting',1,values['ri']):'frame'})
    temporal=TemporalReferences(role_model(values) if roles is None else roles,{})
    designations=DesignationReferences({(values['eirf'],values['eiskt'],1,values['ri']):values['eisks']})
    if cut_roles is None:
        cut_roles={(values['eirf'],values['tm'],canonical(dict(kind='function_ref',symbol=names()['san'])),values['ri']):FunctionValue(('number',),'truth',lambda q:q<1)}
    return result|refs.handlers()|temporal.handlers()|designations.handlers()|profile.CutReferences(cut_roles).handlers()


def attribution_facts():
    return dict(eir3=[('tm','author','doc',('call','einu'),'body'),('eiskt','author','doc',('call','ein5'),'body')],
        ue=[('rj','tm','body'),('tm','eiskt','body')],
        eisjt=[('tm','author',('call','einr'),('call','eins'),'doc','body')],
        eisa5=[('tm','author',('call','einr'),('call','einv'),'body')],
        eisb2=[('tm','author',('call','eini'),('call','eint'),'doc','body')],
        eiskq=[('eiskt','author','rj','doc','body')])


def attribution_case(changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=attribution_facts()
    slots=dict(eir3=(3,),eisjt=(2,3),eisa5=(2,3),eisb2=(2,3))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted light-speed-time content was executed')
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):
                node=json.loads(args[i].syntax)
                if not original:node=renamed(node,{v:k for k,v in mapping().items()})
                args[i]=(node['kind'],node['symbol']) if node.get('kind')=='call' and not node['arguments'] else ('different',)
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=source_excerpt();h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][29:31]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=('front','body'),primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Light-speed-time attribution differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[attribution_case()];require(rows[0]['values']==[True,True],'Baseline attribution differs')
    for field in ('rd','eirf','ri','rj','tm','eiskt'):
        row=attribution_case({field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored context role: '+field);rows.append(row)
    effects=dict(eir3=(0,1),ue=(0,1),eisjt=(0,),eisa5=(0,),eisb2=(0,),eiskq=(1,))
    for relation,indices in effects.items():
        row=attribution_case(failed=relation);require(row['values']==[i not in indices for i in range(2)],'Wrong discourse relation scope: '+relation);rows.append(row)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published light-speed-time bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved light-speed-time bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-synchrony-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/light_speed_time_profile.py','scripts/light_speed_time_contracts.py','scripts/check_einstein_light_speed_time.py',
        'scripts/visible_light_speed_time_collection.py','tests/test_light_speed_time_profile.py','docs/einstein-light-speed-time-v1.md'}
    for path in READINGS:paths.update(author.read(path)['images'])
    return dict(schema='noema-einstein-light-speed-time-evidence-1',core_words=375,profile_words=579,profile_edition=25,
        preserved_source_relations=15,new_reference_primitives=1,new_source_assertions=2,total_source_assertions=27,annotations=5,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
