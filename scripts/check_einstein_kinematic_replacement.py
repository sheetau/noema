"""Connect tacit kinematic assumptions and their geometric rewording."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import kinematic_replacement_profile as profile
from scripts.kinematic_replacement_profile import ROOT,KinematicReplacementVocabulary,write_once
from scripts import check_einstein_rod_length_claims as previous
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

SOURCE='examples/v016/einstein-kinematic-replacement-v1.noema'
BRIDGE='data/einstein-kinematic-replacement-bridge-v1.json'
OUT=ROOT/'output/einstein-kinematic-replacement-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eiaf eiag eiqq eiqr eiqs eiqt eiqu eiqv eiqw eiqx eiqy scj sck'.split()
SENTENCES=dict(zv=(24,1))
ROLE_ASSIGNMENTS=dict(zr=('zv','system'),zw=('zv','rewording'))
CUT_ASSIGNMENTS=dict(zp=('zv','epoch'))
ROLE_HELPERS=['kinematicrole'+role for _,role in (*ROLE_ASSIGNMENTS.values(),*CUT_ASSIGNMENTS.values())]
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*ROLE_ASSIGNMENTS,*CUT_ASSIGNMENTS,*ROLE_HELPERS]
READINGS=('data/einstein-kinematic-replacement-source-reading-v1.json',)
REVIEWS=('data/einstein-kinematic-replacement-review-v1.json',)
FORMS={}
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical


@lru_cache(maxsize=1)
def vocabulary():return KinematicReplacementVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    for n in _references(c.document['statements'][95:96]):visit(n)
    require(len(seen)==192,'Kinematic-replacement source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][95:96])))


@lru_cache(maxsize=1)
def names():
    n=dict(previous.names());proper=set(SENTENCES)|set(ROLE_ASSIGNMENTS)
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in n,'Inherited name would be shadowed: '+old)
        n[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','give',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(n.values()))==len(n) and not set(n.values())&set(vocabulary()._by_symbol),'Local name collision');return n


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def qf(name):return dict(kind='quote',body=dict(kind='function_ref',symbol=name))
def qc(name):return dict(kind='quote',body=call(name))
def reference_roles():return {old:names()['kinematicrole'+role] for old,(_,role) in ROLE_ASSIGNMENTS.items()}
def cut_roles():return {old:names()['kinematicrole'+role] for old,(_,role) in CUT_ASSIGNMENTS.items()}


def role_definitions():
    n=names();m=mapping();x=v('va');s=v('vb');k=lambda old:call(n[old]);f=lambda old:dict(kind='function_ref',symbol=m[old])
    bodies=dict(system=op('and',call(m['zs'],x,s),call(n['scj'],x,qc(n['eiqv']),k('xy'),s,f('zt'),f('zu'))),
        rewording=call(m['zx'],x,k('rd'),k('zr'),qc(n['eiqv']),qc(n['eiqu']),k('xy'),s))
    result=[definition(n['kinematicrole'+role],[('va','individual'),('vb','situation')],'truth',body) for role,body in bodies.items()]
    # Parameterize the existing epoch-dependent comparison without capturing its binders.
    content=next(d for d in source_excerpt()['declarations'] if d['name']=='eiqu')['body']
    assert content['kind']=='content' and content['variable']=='va'
    def epoch(node):
        if node==call('zp'):return v('vd')
        if isinstance(node,dict):return {k:epoch(value) for k,value in node.items()}
        if isinstance(node,list):return [epoch(value) for value in node]
        return node
    result.append(definition(n['kinematicroleepoch'],[('vd',profile.CUT),('ve','situation')],'truth',renamed(epoch(content['body']),m)))
    return result


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    for old,(paragraph,sentence) in SENTENCES.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence))))
    for assignments,roles,sort,relation in ((ROLE_ASSIGNMENTS,reference_roles(),'individual','describedreference'),(CUT_ASSIGNMENTS,cut_roles(),profile.CUT,'describedcutreference')):
        for old,role in roles.items():
            node=assignments[old][0]
            doc['declarations'].append(definition(n[old],[],sort,call(voc._symbols[relation],k('eirf'),k(node),qf(role),k('ri'))))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][50:51],inverse);return normalize_document(result)


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
    require(set(sources)=={'einstein-1905:u0034'} and len(sources['einstein-1905:u0034']['text'])==348,'Source boundary changed')
    math=[r for segment in reading['segments'] for r in segment['math']]
    require(len(math)==1 and math[0]==dict(id='M0051',sha256='5d313ada269dfc2378f1e53604207c23be5b19c12a7415b78f9838fcdfea5eef',printed='t',binding='zp: arbitrarily specified comparison epoch; not identified with xv'),'Comparison epoch changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    return dict(schema='noema-einstein-visible-kinematic-replacement-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[95],source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_positions={old:list(pos) for old,pos in SENTENCES.items()},sentence_ranges={'einstein-1905:u0034':[[0,348]]},math=math,
        role_assignments={old:list(role) for old,role in ROLE_ASSIGNMENTS.items()},cut_assignments={old:list(role) for old,role in CUT_ASSIGNMENTS.items()},reference_roles=role_definitions(),
        semantic_review=[
            '原刊896頁、段落24の第一文をzvとする。通常の運動学zrと埋込の言い換えzwは、同じ文をアンカーとする引用された役割から参照する。文全体との同一視を要求しない。',
            '二操作の値の存在・値としての一意性・相互の厳密な一致をsckで記述する。初期長yaとの比較や測定の実施へ置き換えない。',
            '暗黙の仮定は同じ体系・内容・範囲・文脈での使用と明示の否定である。未知の明示状態を偽とはしない。両内容は著者が通常の運動学に帰属させた内容として引用する。',
            '幾何学的な完全な置換は全物質点の三座標像の双方向の一致と読む。点ラベルや重複数、密度や運動状態の同一性は要求しない。端点や有限標本だけで代用しない。',
            '同じ物体・全物質点の範囲・校正系・尺度と完全な剛体履歴を保持する。静止形状と寸法を保つ許容配置zlを物理的入力とし、移動中の形を凍結した任意の模型で補わない。',
            '指定時刻zpは両方の正の幅の区間に含まれる比較時刻であり、xvや初期長とは別である。参照役割は既存eiquの時刻を引数へ置き換えた引用記述とし、その真理を参照検索で実行しない。',
            '非空の全対象範囲znの各対象に少なくとも一つの静止配置を要求する。配置の唯一性や現実の停止過程は加えない。',
            '長さの一致と任意の剛体の形状の一致を論理的に同値とはしない。zxで原文の言い換えを帰属させる。有限の束縛診断は全実数領域の証明ではない。'],
        profile_edition=30,core_edition=12,new_source_assertions=1,total_source_assertions=40,total_annotations=11,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible kinematic-replacement document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*ROLE_ASSIGNMENTS)}
SITUATIONS=previous.SITUATIONS


def role_model(values):
    return previous.role_model(values)|{(values['eirf'],values[ROLE_ASSIGNMENTS[old][0]],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old]
        for old,role in reference_roles().items()}


def cut_model(values):
    from noema.constructed_semantics import FunctionValue
    return {(values['eirf'],values[CUT_ASSIGNMENTS[old][0]],canonical(dict(kind='function_ref',symbol=role)),values['ri']):FunctionValue(('number',),'truth',lambda q:q<7)
        for old,role in cut_roles().items()}


def context_handlers(values,roles=None,cuts=None):
    result=previous.context_handlers(values);old_sentence=result['sentencereference'];old_cut=result['describedcutreference']
    from scripts.text_reference_profile import TextPresentation
    from scripts.temporal_discourse_profile import TemporalReferences
    from scripts.light_speed_time_profile import CutReferences
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        if key in layout:return layout[key]
        return old_sentence(context,paragraph,item)
    described=TemporalReferences(role_model(values) if roles is None else roles,{}).described
    new_cut=CutReferences(cut_model(values) if cuts is None else cuts).described
    syntax={canonical(dict(kind='function_ref',symbol=role)) for role in cut_roles().values()}
    def cut(document,node,role,context):
        if role.syntax in syntax:return new_cut(document,node,role,context)
        return old_cut(document,node,role,context)
    return result|dict(sentencereference=sentence,describedreference=described,describedcutreference=cut)


def attribution_facts():
    return dict(eir3=[('zv','author','doc',('call','eiqx'),'body')],ue=[('zh','zv','body')])


def presentation_facts():
    return dict(zs=[('zr','body')],zt=[('zr',('call',n),'xy','body') for n in ('eiqv','eiqu')],zu=[],
        zx=[('zw','author','zr',('call','eiqv'),('call','eiqu'),'xy','body')])


def discourse_case(inner=False,changed=None,failed=None,explicit=None):
    values=BASE|(changed or {});answers=[];traces=[];facts=presentation_facts() if inner else attribution_facts()
    if inner and explicit:facts['zu']=[('zr',('call',explicit),'xy','body')]
    slots=dict(eir3=(3,),zt=(1,),zu=(1,),zx=(3,4))
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
            trace.append(dict(relation=name,arguments=json.loads(json.dumps(args))));return name!=failed and tuple(args) in facts[name]
        relations={name:(lambda *args,name=name:relation(name,args)) for name in facts}
        if original:
            doc=deepcopy(source_excerpt());h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({n:(lambda value=value:value) for n,value in values.items() if n in h});h.update(relations)
            selected=lambda name:call(name)
        else:
            doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][50:51]
            h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            h.update({vocabulary()._symbols[n]:f for n,f in context_handlers(values).items()});h.update({mapping()[n]:f for n,f in relations.items()})
            selected=lambda name:call(mapping()[name])
        if inner:doc['statements']=[dict(kind='ask',body=dict(kind='evaluate',content=selected(name),situation=selected('ri'))) for name in ('eiqw',)]
        answers.append(evaluate_document(doc,individuals=tuple(set(values.values())|set(BASE.values())|{'other','setting','frame'}),situations=SITUATIONS,primitives=h))
    require(answers[0]==answers[1] and traces[0]==traces[1],'Kinematic-replacement discourse differs')
    return dict(changed=changed or {},failed=failed,explicit=explicit,values=[r['value'] for r in answers[0]],calls=traces[0])


@lru_cache(maxsize=1)
def diagnostics():
    rows=[discourse_case()];require(rows[0]['values']==[True],'Baseline attribution differs')
    for field in ('rd','eirf','ri','zh','zv'):
        row=discourse_case(changed={field:'front' if field=='ri' else 'other'});require(row['values']==[False],'Ignored attribution role: '+field);rows.append(row)
    for name in attribution_facts():
        row=discourse_case(failed=name);require(row['values']==[False],'Wrong attribution scope: '+name);rows.append(row)
    return rows


@lru_cache(maxsize=1)
def presentation_diagnostics():
    rows=[discourse_case(True)];require(rows[0]['values']==[True],'Baseline presentation differs')
    for field in ('rd','ri','xy','zr','zw'):
        row=discourse_case(True,{field:'front' if field=='ri' else 'other'});require(row['values']==[False],'Ignored presentation role: '+field);rows.append(row)
    for name in ('zs','zt','zx'):
        row=discourse_case(True,failed=name);require(row['values']==[False],'Wrong presentation scope: '+name);rows.append(row)
    for name in ('eiqv','eiqu'):
        row=discourse_case(True,explicit=name);require(row['values']==[False],'Explicit assumption accepted as tacit');rows.append(row)
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n')
    if (ROOT/BRIDGE).exists():require(author.read(BRIDGE)==bridge(),'Published kinematic-replacement bridge differs')
    else:write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved kinematic-replacement bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-rod-length-claims-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/kinematic_replacement_profile.py','scripts/kinematic_replacement_profile_contracts.py','scripts/check_einstein_kinematic_replacement.py',
        'scripts/visible_kinematic_replacement_collection.py','tests/test_kinematic_replacement_profile.py','docs/einstein-kinematic-replacement-v1.md'}
    for path in READINGS:paths.update(author.read(path)['images'])
    return dict(schema='noema-einstein-kinematic-replacement-evidence-1',core_words=375,profile_words=674,profile_edition=30,
        preserved_source_relations=6,new_reference_primitives=0,new_source_assertions=1,total_source_assertions=40,annotations=11,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=diagnostics(),presentation_diagnostics=presentation_diagnostics(),full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
