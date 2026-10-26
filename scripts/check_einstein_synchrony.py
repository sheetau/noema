"""Connect local clocks, synchrony, consistency assumptions and event-time rules."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import synchrony_profile as profile
from scripts.synchrony_profile import ROOT,SynchronyVocabulary,write_once
from scripts import check_einstein_observer_time as previous
from scripts import check_einstein_name_presentation as author
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed,v,op
from scripts.shared_reference import definition
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-synchrony-v1.noema'
BRIDGE='data/einstein-synchrony-bridge-v1.json'
OUT=ROOT/'output/einstein-synchrony-v1'
LABEL=Word('proper',('above','book','give','book','red'))
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS=('eik2 eik3 eik4 eik5 eik6 eik7 eiky eikz eil2 eil3 eil4 eil5 eil6 eil7 eila eilb eilc eild eile eilf eilg eilh eili eilj eilk eill eilm eiln eilo eilp eilq eilr eils eilt eilu eilv eilw eilx eily eilz eim2 eim3 eim4 eim5 eim6 eim7 eima eimb eimc eimd eime eimf eimg eimh eimi eimj eimk eiml eimm eimn eimo eimp eimq eimr eims eimt eimu eimv eimw eimx eimy eimz eina einb einc eind eine einf eing einh eini einj eink einl einm einn eino einp qp qq qr qv saa sab sxb').split()
SENTENCES=dict(eisio=(9,2),eisiz=(9,3),eisjh=(9,4),eisjr=(9,5),eisjs=(9,6),eiskc=(10,1),eiskd=(11,1),eiske=(12,1),eiskk=(13,1))
STAGES=dict(eisiy='eisio',eisjg='eisjh')
DESIGNATIONS=dict(eisi2=1,eisi3=2)
TRIAL_FIELDS=dict(eisjk='qe',eisjl='qf',eisjm='qg',eisjn='qh',eisjo='qi',eisjp='qj',eisjq='qk')
ROLE_ASSIGNMENTS=dict(ziq='point',zir='point',eiskh='point',eisib='clocka',eisik='clockb',eiskg='clockc',
    eisic='observera',eisil='observerb',eisid='displaya',eisim='displayb',eisie='taska',eisin='taskb',
    eisiw='timea',eisix='timeb',eisjd='commontime',eisje='proposal',eisjf='definitiontask',eisjj='trial',eiskl='material')
ROLE_NAMES=list(dict.fromkeys(ROLE_ASSIGNMENTS.values()))
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*STAGES,*DESIGNATIONS,*TRIAL_FIELDS,*ROLE_ASSIGNMENTS,*['syncrole'+n for n in ROLE_NAMES]]
READINGS=tuple('data/einstein-'+n+'-source-reading-v1.json' for n in ('local-clock','second-local-clock','local-times-only','equal-light-times','light-roundtrip-definition','consistent-synchrony','synchrony-laws','event-time-summary'))
REVIEWS=tuple('data/einstein-'+n+'-review-v1.json' for n in ('local-synchrony-paragraph','synchrony-equation','consistent-synchrony','synchrony-symmetry','synchrony-three-clock','event-time-summary'))
FORMS=dict(eisi2='A-Zeit',eisi3='B-Zeit')
qf=previous.qf
qc=lambda old:dict(kind='quote',body=call(old))


@lru_cache(maxsize=1)
def vocabulary():return SynchronyVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][70:81]):visit(n)
    require(len(seen)==251,'Synchrony source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][70:81])))


@lru_cache(maxsize=1)
def names():
    n=previous.names();proper=set(SENTENCES)|set(STAGES)|set(DESIGNATIONS)|set(ROLE_ASSIGNMENTS)|set(TRIAL_FIELDS)-{'eisjo','eisjp','eisjq'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','book','bird',previous.previous.PARTS[i//16],previous.previous.PARTS[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:previous.previous.authoring_vocabulary()._symbols[new] for old,new in previous.previous.MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def reference_node(old):
    if old in ('ziq','eisib','eisic','eisid','eisie'):return 'eish2'
    if old in ('zir','eisik','eisil','eisim','eisin'):return 'eisio'
    if old in ('eisiw','eisix'):return 'eisiz'
    if old in ('eiskg','eiskh'):return 'eiske'
    if old=='eisjj':return 'eisjr'
    if old=='eiskl':return 'eiskk'
    return 'eisjh'


def reference_roles():return {old:names()['syncrole'+role] for old,role in ROLE_ASSIGNMENTS.items()}


def role_definitions():
    n=names();m=mapping()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()};x=v('va');s=v('vb');k=lambda old:call(n[old]);r=lambda old,*args:call(m[old],*args)
    bodies=dict(point=r('eisjv',x,k('ra'),s),definitiontask=r('eisfw',x,k('eirf'),s),
        commontime=op('and',r('eisir',x,k('ziq'),k('ra'),k('rb'),k('eirf'),s),r('eisir',x,k('zir'),k('ra'),k('rb'),k('eirf'),s)),
        proposal=r('eisjc',x,k('eisjf'),k('eisjd'),k('eisiw'),k('eisix'),k('eisib'),k('eisik'),k('ziq'),k('zir'),k('ra'),k('rb'),k('rd'),k('eisiy'),k('eisjg'),k('eirf'),s),
        trial=r('qb',k('eisib'),k('eisik'),k('ra'),k('rb'),s,x),
        material=op('and',r('eiskn',x,k('eirf'),s),op('and',r('eisko',x,k('eirf'),s),op('and',
            r('eiskm',x,qc(n['eik7']),k('eirf'),s),r('eiskm',x,qc(n['eiml']),k('eirf'),s)))))
    for suffix,clock,observer,hand,task,place in [('a','eisib','eisic','eisid','eisie','ziq'),('b','eisik','eisil','eisim','eisin','zir')]:
        bodies['clock'+suffix]=r('eiky',x,k(place),k('ra'),s)
        bodies['observer'+suffix]=op('and',r('eisgr',x,s),r('cb',x,k(place),k('ra')))
        bodies['display'+suffix]=r('eisgs',x,k(clock),s)
        bodies['task'+suffix]=r('eish7',x,k(place),k('ra'),k('eirf'),s)
        bodies['time'+suffix]=r('eilp',x,k(task),k(observer),k(clock),k(hand),k(place),k('ra'),k('rb'),k('eirf'),s)
    bodies['clockc']=r('eiky',x,k('eiskh'),k('ra'),s)
    return [definition(n['syncrole'+name],[('va','individual'),('vb','situation')],'truth',bodies[name]) for name in ROLE_NAMES]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    # The inherited document already declares the reused assumption relation.
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    for old,role in reference_roles().items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['describedreference'],k('eirf'),k(reference_node(old)),qf(role),k('ri'))))
    for old,node in STAGES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['discoursestageafter'],k('eirf'),k(node),k('ri'))))
    for old,index in DESIGNATIONS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['designationreference'],k('eirf'),k('eisiz'),author.num(index),k('ri'))))
    ds={d['name']:d for d in source_excerpt()['declarations']}
    for old,field in TRIAL_FIELDS.items():
        doc['declarations'].append(definition(n[old],[],ds[old]['result'],call(n[field],k('eisjj'))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,spelling in FORMS.items():
        doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(spelling),k('ri'))))
    return link(doc,[parse((ROOT/previous.previous.MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in previous.previous.FIELDS or d['name']=='zz4') else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][16:27],inverse);return normalize_document(result)


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
            sources.setdefault(unit['id'],dict(sha256=unit['text_sha256'],text=unit['text'],ranges=[]))['ranges'].append([a,b])
    require(set(sources)=={'einstein-1905:u'+str(i).zfill(4) for i in range(13,19)},'Source units changed')
    ordered=list(units.values());body=[u for u in ordered if u['kind']=='body']
    require([u['id'] for u in body[8:13]]==['einstein-1905:u'+str(i).zfill(4) for i in (13,15,16,17,18)],'Paragraph positions changed')
    require(ordered[13]['id']=='einstein-1905:u0014' and ordered[12]['id']=='einstein-1905:u0013','Equation attachment changed')
    text=sources['einstein-1905:u0013']['text']
    require(text[1071:1291].endswith('zurück.') and text[1292:]=='Die beiden Uhren laufen definitionsgemäß synchron, wenn','Sixth sentence boundary changed')
    require(sources['einstein-1905:u0016']['text'].startswith('1. Wenn ') and sources['einstein-1905:u0017']['text'].startswith('2. Wenn '),'Printed item numbering changed')
    for row in sources.values():
        cursor=0
        for a,b in sorted(row['ranges']):
            require(row['text'][cursor:a] in ('',' '),'Source coverage gap');cursor=b
        require(cursor==len(row['text']),'Source paragraph incomplete')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-synchrony-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=list(range(70,81)),source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],
        mapping=mapping(),sentence_positions={n:list(pos) for n,pos in SENTENCES.items()},reference_roles=reference_roles(),
        reference_nodes={n:reference_node(n) for n in ROLE_ASSIGNMENTS},role_definitions=role_definitions(),stages=STAGES,trial_fields=TRIAL_FIELDS,
        source_sentence_boundaries={'einstein-1905:u0013':[[0,251],[252,560],[561,821],[822,1070],[1071,1291],[1292,1347]],
            'einstein-1905:u0018':[[0,265],[266,515]]},
        equation_attachment=dict(node='eisjs',body=[1292,1347],equation_unit='einstein-1905:u0014',math='M0030',one_sentence=True),
        numbered_items=dict(eiskd=1,eiske=2),printed_designations=FORMS,identifier_annotations=annotations(),
        semantic_review=['二地点の条件付き局所評価、構成の完全一致、追加の意思と二つのauchを保持する。',
            '局所時間だけという範囲を第二文までの論述段階へ限定し、第四文の新しい候補と区別する。',
            '等片道光時間の定義可能性、同じ光の往復設定、全関連試行への同期条件を区別する。式M0030は第六文の続きである。',
            '試行の三出来事・光・三読みは既存の成分取得へ結ぶ。取得は実測済みや同期成立を保証しない。',
            '無矛盾性は上限のない有限点列への共有配置の実現可能性を仮定する内容であり、二法則だけへ縮めない。',
            '番号付き二法則の一般性、代表配置、順序を保持する。A/B/Cの文字だけから実際の設置を主張しない。',
            '思考上の物理的経験からのまとめと明白さの提示、同じ参照時計への時刻付与と同時性の定義を保持する。',
            '役割による参照は同じ文書・導入箇所・閉じた役割・文脈に固定する。引用した役割の真理や世界唯一性を主張しない。'],
        profile_edition=24,core_edition=12,new_source_assertions=11,total_source_assertions=25,annotations=4,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible synchrony document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*ROLE_ASSIGNMENTS,*DESIGNATIONS,*STAGES,'eishs')}
NODES=('eish2','eisio','eisiz','eisjh','eisjr','eisjs','eiskc','eiskd','eiske','eiskk','rj')
MESSAGES=('eila','eiln','eil5','eimf','eimn','eimq','eim5','einc','eind','eino','einj')


def role_model(values):
    return previous.role_model(values)|{(values['eirf'],values[reference_node(old)],previous.previous.canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
        for old,role in reference_roles().items()}


def context_handlers(values,roles=None):
    from scripts.discourse_setting_profile import DiscourseReferences
    from scripts.temporal_discourse_profile import TemporalReferences
    from scripts.designation_purpose_profile import DesignationReferences
    result=previous.context_handlers(values)
    positions=previous.SENTENCES|SENTENCES
    layout={(values['ri'],4,1):'setting',(values['ri'],6,4):values['eisfm']}|{(values['ri'],*pos):values[old] for old,pos in positions.items()}
    refs=DiscourseReferences({values['eirf']:values['ri']},{},layout,{(values['eirf'],'setting',1,values['ri']):'frame'})
    temporal=TemporalReferences(role_model(values) if roles is None else roles,{})
    designations=DesignationReferences({(values['eirf'],values['eisiz'],index,values['ri']):values[old] for old,index in DESIGNATIONS.items()})
    stages=profile.SynchronyRecords(stages={(values['eirf'],values[node],values['ri']):values[old] for old,node in STAGES.items()})
    return result|refs.handlers()|temporal.handlers()|designations.handlers()|stages.handlers()


def attribution_facts():
    facts=dict(eir3=[(BASE[node],'author','doc',('call',msg),'body') for node,msg in zip(NODES,MESSAGES,strict=True)],
        ue=[(a,b,'body') for a,b in zip(('eishs',*NODES[:-1]),NODES,strict=True)],
        eisij=[('eisio','author',('call','eile'),('call','eilf'),'doc','body'),('eisio','author',('call','eilh'),('call','eili'),'doc','body')],
        eisii=[('eisio','author',('call','eilj'),('call','eilg'),('call','eill'),'doc','body')],
        zbc=[('eisiz','author',('call','eilm'),('call','eily'),'doc','body'),('eisiz','author',('call','eilz'),('call','eil2'),'doc','body')],
        eisi4=[('eisi2','eisiw','ziq','doc','body'),('eisi3','eisix','zir','doc','body')],
        eisji=[('eisjh','author','eisiz',('call','eil2'),'eisjd','ziq','zir','doc','body')],
        eisjt=[('eisjr','author',('call','eime'),('call','eiml'),'doc','body')],
        eiskb=[('eiskc','author','eisjs',('function_ref','eimk'),'doc','body')],
        eiskf=[('eiskc','author','eiskd','eiske',('call','qp'),('call','qq'),'doc','body')],
        eiski=[('eiskd','author',('call','qp'),('call','eina'),'doc','body'),('eiske','author',('call','qq'),('call','einb'),'doc','body')],
        eiskj=[('eiskd','eiskc',1,'doc','body'),('eiske','eiskc',2,'doc','body')],
        eiskq=[('eiskk','author','eisjs','doc','body'),('eiskk','author','eiskc','doc','body')])
    return facts


def attribution_case(changed=None,failed=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=attribution_facts()
    slots=dict(eir3=(3,),eisij=(2,3),eisii=(2,3,4),zbc=(2,3),eisji=(3,),eisjt=(2,3),eiskb=(3,),eiskf=(4,5),eiski=(2,3))
    for original in (True,False):
        trace=[];traces.append(trace)
        def forbidden(*args):raise ValueError('Quoted synchrony content was executed')
        def relation(name,args):
            args=list(args)
            for i in slots.get(name,()):
                node=json.loads(args[i].syntax)
                if not original:node=renamed(node,{v:k for k,v in mapping().items()})
                args[i]=(node['kind'],node['symbol']) if node.get('kind')=='function_ref' or node.get('kind')=='call' and not node['arguments'] else ('different',)
            # JSON-compatible, exact numeric list ordinal for the evidence report.
            if name=='eiskj':args[2]=int(args[2])
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=source_excerpt();h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][16:27]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=('front','body'),primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Synchrony attribution differs')
    return dict(changed=changed or {},failed=failed,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[attribution_case()];require(rows[0]['values']==[True]*11,'Baseline attribution differs')
    for field in ('rd','eirf','ri','eishs',*NODES,'eisi2','eisi3','eisiw','eisix','ziq','zir','eisjd'):
        row=attribution_case({field:'front' if field=='ri' else 'other'});require(not all(row['values']),'Ignored context role: '+field);rows.append(row)
    effects=dict(eir3=range(11),ue=range(11),eisij=(1,),eisii=(1,),zbc=(2,),eisi4=(2,4),eisji=(3,),eisjt=(4,),eiskb=(6,),eiskf=(6,),eiski=(7,8),eiskj=(7,8),eiskq=(9,))
    for relation,indices in effects.items():
        row=attribution_case(failed=relation);require(row['values']==[i not in indices for i in range(11)],'Wrong discourse relation scope: '+relation);rows.append(row)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published synchrony bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved synchrony bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-observer-time-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/synchrony_profile.py','scripts/synchrony_contracts.py','scripts/check_einstein_synchrony.py',
        'scripts/visible_synchrony_collection.py','tests/test_synchrony_profile.py','docs/einstein-synchrony-v1.md'}
    return dict(schema='noema-einstein-synchrony-evidence-1',core_words=375,profile_words=563,profile_edition=24,
        preserved_source_relations=48,reused_public_relations=1,new_reference_primitives=1,new_source_assertions=11,total_source_assertions=25,annotations=4,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
