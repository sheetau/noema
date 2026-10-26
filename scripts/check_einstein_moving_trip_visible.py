"""Connect the moving light trial, both equations and the local author note."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import _references
from noema.identifiers import load_annotations
from scripts import moving_trip_visible_profile as profile
from scripts.moving_trip_visible_profile import ROOT,MovingTripVisibleVocabulary,MovingTextReferences,write_once,CUT
from scripts import check_einstein_carried_clock_synchrony as previous
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

SOURCE='examples/v016/einstein-moving-trip-visible-v1.noema'
BRIDGE='data/einstein-moving-trip-visible-bridge-v1.json'
OUT=ROOT/'output/einstein-moving-trip-visible-v1'
LABEL=previous.LABEL
RELATIONS=previous.RELATIONS|profile.SOURCE_RELATIONS
NEW_DEFINITIONS='eitd eite eitf eitg eith eiti eitj eitk eitl eitm eitn eito eitp eitq eitr eits eitt eitu eitv eitw eitx eity eitz sdb sde sdi'.split()
SENTENCES=dict(tripfirst=(26,1),tripsecond=(26,2),za3=(26,3))
DESIGNATIONS=dict(eismm=('eismk',1))
ROLE_ASSIGNMENTS=dict(zax=('za2','ray'),zaw=('za2','trial'),zas=('za2','depart'),zat=('za2','reflect'),zau=('za2','return'),zay=('za2','observera'),zaz=('za2','observerb'))
CUT_ASSIGNMENTS=dict(zav=('za3','length'))
ROLE_HELPERS=['triprole'+role for _,role in (ROLE_ASSIGNMENTS|CUT_ASSIGNMENTS).values()]
LOCAL_NAMES=[*NEW_DEFINITIONS,*SENTENCES,*DESIGNATIONS,*ROLE_ASSIGNMENTS,*CUT_ASSIGNMENTS,'za2','eisml','eismk',*ROLE_HELPERS]
READINGS=('data/einstein-moving-trip-reading-source-reading-v1.json',)
REVIEWS=tuple('data/einstein-moving-trip-reading-'+unit+'-review-v1.json' for unit in ('u0036','u0037','u0038','u0039','u0280'))
FORMS=dict(eismm='Zeit')
MATH=previous.MATH
MATH_LIBRARY=previous.MATH_LIBRARY
canonical=temporal.canonical
qf=previous.qf


@lru_cache(maxsize=1)
def vocabulary():return MovingTripVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    for n in _references(c.document['statements'][97:100]):visit(n)
    require(len(seen)==247,'Moving-trip source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=deepcopy(c.document['statements'][97:100])))


@lru_cache(maxsize=1)
def names():
    result=dict(previous.names());proper=set(SENTENCES)|set(DESIGNATIONS)|set(ROLE_ASSIGNMENTS)|{'za2','eisml','eismk'}
    for i,old in enumerate(LOCAL_NAMES):
        require(old not in result,'Inherited name would be shadowed: '+old)
        result[old]=symbol(Word('proper' if old in proper else 'compound',('above','round','inside',temporal.PARTS[i//16],temporal.PARTS[i%16])),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision');return result


@lru_cache(maxsize=1)
def mapping():
    selected={d['name'] for d in source_excerpt()['declarations']}
    candidates=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{old:temporal.authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    require(selected<=set(candidates),'Unplanned source dependency: '+str(sorted(selected-set(candidates))))
    result={old:candidates[old] for old in sorted(selected)};require(len(set(result.values()))==len(result),'Source names merged');return result


def reference_roles(assignments=ROLE_ASSIGNMENTS):return {old:names()['triprole'+role] for old,(_,role) in assignments.items()}


def role_definitions():
    n=names();m=mapping();voc=vocabulary();x=v('va');ctx=v('vb');k=lambda old:call(n[old]);f=lambda old,*args:call(m[old],*args)
    # This is a reference to a light at the trial passage, not a proof of its path.
    bodies={'ray':f('eisb5',x,k('ra'),k('yd'))}
    trial=op('and',f('za4',x,k('zax'),v('vc'),v('vd'),v('ve'),k('ra'),k('yd')),
        f('sde',k('zax'),v('vc'),v('vd'),v('ve'),k('ra'),*[dict(kind='function_ref',symbol=m[a]) for a in ('cf','cg','ch')]))
    for slot in reversed(('vc','vd','ve')):trial=dict(kind='exists',variable=slot,sort='individual',body=trial)
    bodies['trial']=trial
    for role,clock,endpoint,index in [('depart','zaj','xn',2),('reflect','zak','xo',3),('return','zaj','xn',4)]:
        fields=[f(a,x) for a in ('zad','zae','zaf','zag','zah')]
        bodies[role]=op('and',f('zac',x,k(clock),k('yd')),
            op('and',op('equal',fields[0],call(voc._symbols['roundtripentity'],k('zaw'),author.num(index))),f('eiq2',k(clock),k(endpoint),*fields,k('yd'))))
    for role,clock,endpoint in [('observera','zaj','xn'),('observerb','zak','xo')]:bodies[role]=f('eitl',x,k(clock),k(endpoint),k('yd'))
    bodies['length']=op('and',f('yx',k('yd'),k('yf')),f('eip6',x,k('yf')))
    return [definition(n['triprole'+role],[('va',CUT if role=='length' else 'individual'),('vb','situation')],'truth',body) for role,body in bodies.items()]


@lru_cache(maxsize=1)
def document():
    doc=deepcopy(previous.document());n=names();voc=vocabulary();m=mapping();k=lambda old:call(n[old])
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))+role_definitions()
    def add(old,result,body):doc['declarations'].append(definition(n[old],[],result,body))
    for old,(paragraph,sentence) in SENTENCES.items():add(old,'individual',call(voc._symbols['sentencereference'],k('ri'),author.num(paragraph),author.num(sentence)))
    add('za2','individual',call(voc._symbols['sentencespanreference'],k('eirf'),k('tripfirst'),k('tripsecond'),k('ri')))
    add('eisml','individual',call(voc._symbols['footnoteattachmentreference'],k('eirf'),k('tripsecond'),author.num(1),author.num(1),k('ri')))
    add('eismk','individual',call(voc._symbols['footnotereference'],k('eirf'),k('eisml'),author.num(1),k('ri')))
    for old,(node,ordinal) in DESIGNATIONS.items():add(old,'individual',call(voc._symbols['designationreference'],k('eirf'),k(node),author.num(ordinal),k('ri')))
    for assignments,function,result in [(ROLE_ASSIGNMENTS,'describedreference','individual'),(CUT_ASSIGNMENTS,'describedcutreference',CUT)]:
        for old,role in reference_roles(assignments).items():add(old,result,call(voc._symbols[function],k('eirf'),k(assignments[old][0]),qf(role),k('ri')))
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['name'] in NEW_DEFINITIONS],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    for old,form in FORMS.items():doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k(old),author.text_expression('de'),author.text_expression(form),k('ri'))))
    return link(doc,[parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))],vocabulary=voc)


def backprojection(doc):
    require(doc==document(),'Changed migration cannot reuse old evidence')
    ds={d['name']:d for d in doc['declarations']};m=mapping();inverse={v:k for k,v in m.items()};result=deepcopy(source_excerpt())
    forwarded=set(temporal.FIELDS)|set(principles.FIELDS)|{'zz4'}
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name'] in forwarded) else renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=renamed(doc['statements'][55:58],inverse);return normalize_document(result)


@lru_cache(maxsize=1)
def annotations():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    data=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations']);rows={r['symbol']:r for r in data.annotations['entries'] if r['symbol'] in FORMS}
    for old,text in FORMS.items():require(rows[old]==dict(symbol=old,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]),'Designation annotation changed')
    return dict(entries=rows,source_sha256=data.show()['source_sha256'])


def bridge():
    c=catalogs()['einstein-1905'];units={u['id']:u for u in author.read(author.UNITS)['units']};reading=author.read(READINGS[0]);sources={}
    for row in reading['segments']:
        unit=units[row['unit']];a,b=row['range']
        require(row['unit_sha256']==unit['text_sha256'] and row['text']==unit['text'][a:b] and a==0 and b==len(unit['text']),'Original reading differs')
        sources[unit['id']]=dict(sha256=unit['text_sha256'],text=unit['text'],range=[a,b])
    require(set(sources)=={'einstein-1905:'+u for u in ('u0036','u0037','u0038','u0039','u0280')},'Source boundary changed')
    for path in REVIEWS:
        review=author.read(path);unit=units[review['unit']]
        require(review['source']['unit_sha256']==unit['text_sha256'] and review['source']['text']==unit['text'],'Old review source changed')
        require(review['decision']=='equivalent_under_stated_reading' and review['unresolved']==[],'Old review incomplete')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];d=e['declaration'];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        require(profile.CONTRACTS[new]==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),'Public contract changed')
    require(backprojection(document())==source_excerpt(),'Source backprojection differs')
    text=sources['einstein-1905:u0036']['text'];second=text.index('Zur Zeit');third=text.index('Unter Berücksichtigung')
    return dict(schema='noema-einstein-moving-trip-visible-bridge-1',reviewer='assistant',source_document=c.document_path,
        source_statement_indices=[97,98,99],source_units=sources,source_declarations=source_excerpt()['declarations'],source_statements=source_excerpt()['statements'],mapping=mapping(),
        sentence_positions={old:list(pos) for old,pos in SENTENCES.items()},sentence_ranges={'einstein-1905:u0036':[[0,second-1],[second,third-1],[third,len(text)]]},
        span=dict(za2=['tripfirst','tripsecond']),attachment=dict(eisml=dict(sentence='tripsecond',printed_number=1,occurrence=1,after='Zur Zeit',before='M0054')),
        math=[r for segment in reading['segments'] for r in segment['math']],annotations=annotations()['entries'],
        role_assignments={old:list(role) for old,role in (ROLE_ASSIGNMENTS|CUT_ASSIGNMENTS).items()},reference_roles=role_definitions(),
        semantic_review=[
            '原刊896/897頁の想定二文・結果導入と二式・脚注を同じ文脈で接続する。za2は第一文そのものではなく最初の二文の連続範囲、za3は第三文の結果提示箇所とする。',
            'eismlは第二文の最初の注1)の局所付着箇所で、Zur Zeitの直後、t_Aの直前。eismkはその注本文、eismmは注頭のZeit呼称。インベントリ末尾を本文順序にしない。',
            '同じ光と試行から三出来事を選び、各時計の照合記録を結ぶ。参照役割を引用し、物理的成立の探索や推論で参照先を決めない。未知キーは拒否する。',
            '観測者の巨視的代表位置は三成分の相対変位を全時刻対で保持する。近接・共動・時計への取り付け・判定適用を区別し、身体内部の運動を停止させない。',
            '設定eitoは光の同じ端点出来事と真空条件を保持する。一定Vの直線軌道と交点eitk、二式sdbは結果eitpの内側にあり、結論を設定に戻さない。',
            'r_ABは現在の静止系測定eip6と同じ設定継承yxに結ぶ。初期長yaや光路全長ではない。後端A・前端Bの向きは今回の式V−v/V+vに従う。',
            '著者の原理を考慮した現在の結果提示を保ち、未来の予告・必然性・実測済み・処理系による原理の証明へ替えない。',
            '脚注eitqは二時計の任意の適格記録に同じ値と局所出来事を要求する。三記録だけへの制限や別周期の数値一致で代用せず、同時に二通りに読む意味を保つ。'],
        profile_edition=32,core_edition=12,new_source_assertions=3,total_source_assertions=44,total_annotations=15,
        original_manuscript_modified=False,old_judgments_rebound=False,full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible moving-trip document differs');return result


BASE=previous.BASE|{n:n for n in (*SENTENCES,*DESIGNATIONS,*ROLE_ASSIGNMENTS,'za2','eisml','eismk')}
SITUATIONS=previous.SITUATIONS


def role_model(values):
    return previous.role_model(values)|{(values['eirf'],values[ROLE_ASSIGNMENTS[old][0]],canonical(dict(kind='function_ref',symbol=role)),values['ri']):values[old] for old,role in reference_roles().items()}


def context_handlers(values,roles=None,cuts=None):
    from scripts.text_reference_profile import TextPresentation
    from scripts.temporal_discourse_profile import TemporalReferences
    from scripts.light_speed_time_profile import CutReferences
    result=previous.context_handlers(values);old_sentence=result['sentencereference'];old_designation=result['designationreference'];old_note=result['footnotereference'];old_cut=result['describedcutreference']
    layout={(values['ri'],*pos):values[old] for old,pos in SENTENCES.items()}
    def sentence(context,paragraph,item):
        key=(context,TextPresentation.coordinate(paragraph),TextPresentation.coordinate(item))
        return layout[key] if key in layout else old_sentence(context,paragraph,item)
    def designation(document,node,item,context):
        key=(document,node,TextPresentation.coordinate(item),context)
        if key==(values['eirf'],values['eismk'],1,values['ri']):return values['eismm']
        return old_designation(document,node,item,context)
    def note(document,node,number,context):
        key=(document,node,TextPresentation.coordinate(number),context)
        if key==(values['eirf'],values['eisml'],1,values['ri']):return values['eismk']
        return old_note(document,node,number,context)
    cutroles=cuts if cuts is not None else {(values['eirf'],values['za3'],canonical(dict(kind='function_ref',symbol=names()['triprolelength'])),values['ri']):FunctionValue(('number',),'truth',lambda q:q<6)}
    refs=CutReferences(cutroles)
    def cut(document,node,role,context):
        if (document,node,role.syntax,context) in cutroles:return refs.described(document,node,role,context)
        return old_cut(document,node,role,context)
    textrefs=MovingTextReferences({(values['eirf'],values['tripfirst'],values['tripsecond'],values['ri']):values['za2']},
        {(values['eirf'],values['tripsecond'],1,1,values['ri']):values['eisml']})
    return result|textrefs.handlers()|dict(sentencereference=sentence,designationreference=designation,footnotereference=note,describedcutreference=cut,
        describedreference=TemporalReferences(role_model(values) if roles is None else roles,{}).described)


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Saved moving-trip bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-carried-clock-synchrony-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,*annotations()['source_sha256'],prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,*READINGS,*REVIEWS,
        'scripts/moving_trip_visible_profile.py','scripts/moving_trip_visible_profile_contracts.py','scripts/check_einstein_moving_trip_visible.py',
        'scripts/visible_moving_trip_visible_collection.py','tests/test_moving_trip_visible_profile.py','docs/einstein-moving-trip-visible-v1.md'}
    for path in READINGS:paths.update(author.read(path)['source_sha256'])
    return dict(schema='noema-einstein-moving-trip-visible-evidence-1',core_words=375,profile_words=696,profile_edition=32,
        preserved_source_relations=7,new_reference_primitives=2,new_source_assertions=3,total_source_assertions=44,annotations=15,
        declarations=len(document()['declarations']),statements=len(document()['statements']),pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        full_real_domain_evaluated=False,full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},limits=profile.LIMITS)
