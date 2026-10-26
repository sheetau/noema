"""Connect stationary-point measurement to inline mathematics and visible discourse."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts import physical_position_profile as profile
from scripts.physical_position_profile import ROOT,PhysicalPositionVocabulary,write_once
from scripts import check_einstein_designation_purpose as previous
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

SOURCE='examples/v016/einstein-physical-position-v1.noema'
BRIDGE='data/einstein-physical-position-bridge-v1.json'
OUT=ROOT/'output/einstein-physical-position-v1'
LABEL=Word('proper',('town','book','give','book','red'))
RELATIONS=profile.SOURCE_RELATIONS|dict(eir3='presentsmessage',ue='textbefore')
PARTS=dict(eiac=['town'],eiad=['home'],eiaj=['above'],eiam=['inside'],eigw=['give'],eigx=['aki'],eigy=['nao'],
    eih6=['town','above'],eih7=['town','inside'],eiia=['town','home'],eiib=['give','home'],eiic=['book','home'],
    eiid=['give','inside'],eiie=['assessmentvalid','home'],eiif=['book','inside'],eiig=['book','give'],eiih=['book','above'],
    la=['round','home'],lg=['round','inside'],sa=['town','rain'],sb=['town','aki'],sd=['town','round'],se=['town','give'],
    sexb=['round','give'],zzba=['round','book'],zzbc=['round','above'],zzbg=['round','red'],zz4=['round','rain'])


@lru_cache(maxsize=1)
def vocabulary():return PhysicalPositionVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    statement=c.document['statements'][59]
    for n in _references(statement):visit(n)
    require(len(seen)==63,'Source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=[deepcopy(statement)]))


def names():
    result=previous.names()|{old:symbol(Word('compound',('town','book','give',*parts)),vocabulary()) for old,parts in PARTS.items()}
    result['eisel']=symbol(Word('proper',('town','book','give','book')),vocabulary())
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision')
    return result


def mapping():
    ds=source_excerpt()['declarations'];selected={d['name'] for d in ds}
    mapped=names()|{old:vocabulary()._symbols[new] for old,new in RELATIONS.items()}|{
        old:authoring_vocabulary()._symbols[new] for old,new in MATH.items() if old in selected}
    result={old:mapped[old] for old in selected}
    require(len(set(result.values()))==len(result),'Source names merged');return result


def order_alias():
    return definition(names()['zz4'],[('va','number'),('vb','number')],'truth',
        call(vocabulary()._symbols['rationalbelow'],v('va'),v('vb')))


@lru_cache(maxsize=1)
def document():
    m=mapping();n=names();voc=vocabulary();doc=deepcopy(previous.document())
    doc['declarations']+=voc.imports(set(profile.PARAMETERS))
    doc['declarations'].append(definition(n['eisel'],[],'individual',
        call(voc._symbols['sentencereference'],call(n['ri']),author.num(5),author.num(1))))
    doc['declarations'].append(order_alias())
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['kind']=='definition' and d['name'] not in MATH],m)
    doc['statements']+=renamed(source_excerpt()['statements'],m)
    library=parse((ROOT/MATH_LIBRARY).read_text(encoding='utf-8'))
    return link(doc,[library],vocabulary=voc)


def backprojection(migrated):
    require(migrated==document(),'Changed migration cannot be rebound to old evidence')
    ds={d['name']:d for d in migrated['declarations']};m=mapping();inverse={v:k for k,v in m.items()}
    result=deepcopy(source_excerpt())
    result['declarations']=[deepcopy(d) if d['kind']=='primitive' and (not d['parameters'] or d['name']=='zz4') else
        renamed(ds[m[d['name']]],inverse) for d in result['declarations']]
    result['statements']=[renamed(migrated['statements'][5],inverse)];return normalize_document(result)


def bridge():
    c=catalogs()['einstein-1905'];units=author.read(author.UNITS)['units'];unit=[u for u in units if u['kind']=='body'][4]
    require(unit['id']=='einstein-1905:u0009' and len(unit['text'])==242,'Source paragraph changed')
    source_reading=author.read('data/einstein-point-position-source-reading-v1.json')
    require(source_reading['text']==unit['text'] and source_reading['unit_sha256']==unit['text_sha256'],'Source reading differs')
    for old,new in profile.SOURCE_RELATIONS.items():
        e=c.entries[old];meaning=e['meaning_ja'].split('] ',1)[-1] if e['meaning_ja'].startswith('[') else e['meaning_ja']
        contract=profile.CONTRACTS[new];d=e['declaration']
        require(contract==dict(parameters=d['parameters'],result=d['result'],arguments=e['arguments'],meaning_ja=meaning),
            'Physical relation contract changed: '+old)
    require(backprojection(document())==source_excerpt(),'Source projection differs')
    m=mapping();ds={d['name']:d for d in document()['declarations']}
    math_rows=[]
    for d in source_excerpt()['declarations']:
        if d['name'] in MATH:
            require(renamed(d,m)==ds[m[d['name']]],'Inline mathematics changed: '+d['name'])
            math_rows.append(dict(source=d['name'],library_name=MATH[d['name']],visible_name=m[d['name']],kind=d['kind']))
    require(len(math_rows)==15 and ds[names()['zz4']]==order_alias(),'Mathematics or alias changed')
    def unlabel(text):return text.split('] ',1)[-1] if text.startswith('[') else text
    require(unlabel(c.entries['zz4']['meaning_ja'])==unlabel(c.entries['aa']['meaning_ja']),
        'Rational order alias meaning differs')
    return dict(schema='noema-einstein-visible-physical-position-bridge-1',reviewer='assistant',source_statement_index=59,
        source_document=c.document_path,source_unit=unit['id'],source_range=[0,242],source_text=unit['text'],source_unit_sha256=unit['text_sha256'],
        source_declarations=source_excerpt()['declarations'],source_assertion=source_excerpt()['statements'][0],mapping=m,
        meanings={d['name']:dict(meaning_ja=c.entries[d['name']]['meaning_ja'],meaning_basis=c.entries[d['name']]['meaning_basis'])
            for d in source_excerpt()['declarations']},
        bindings=dict(eisel='sentencereference(ri,5,1)',eised='unchanged naming sentence',ra='unchanged chosen frame',
            rd='unchanged displayed author',eirf='unchanged document',ri='unchanged body context'),
        optional_mathematics_library=MATH_LIBRARY,inline_mathematics=math_rows,
        order_alias=dict(source='zz4',definition=order_alias(),reason='Same exact rational order, but the second quoted name remains distinct from aa.'),
        semantic_review=[
            '全静止物質点を条件の前件に置き、静止点の現在の存在を加えない。',
            '静止の全対象期間、同じ系と単位、全実数軌跡を保持し、一瞬や有限標本で代用しない。',
            '使用物差しが少なくとも一つあり、全ての使用物差しに同じ使用期間の剛性と校正を要求する。',
            '同じ点・方法・系・単位・幾何記録を位置決定とCartesian射影の両方に結ぶ。全18成分を保持する。',
            '許容された実施設定での結果を要求し、参照状況で既に実測したことは要求しない。',
            '命名済みの同じraを使用し、全条件文のassert messageを同じ著者・論説へ帰属する。引用を実行しない。',
            '15の数学対応を型付き本体で照合し、11定義を本文に展開する。zz4とaaを同じ引用名へ統合しない。'],
        newly_connected_source_assertions=1,total_connected_source_assertions=4,orthographic_annotation_assertions=2,
        profile_edition=21,core_edition=12,original_manuscript_modified=False,old_judgments_rebound=False,
        full_real_domain_evaluated=False,limits=profile.LIMITS)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible measurement differs');return result


def presentation_diagnostics():
    # The full source and decoded Native body are evaluated, with every inner
    # physical or numeric callback forbidden. Only the attribution is asserted.
    rows=[]
    base=dict(rd='y',eirf='y',ri='body',eised='x',eisel='y')
    cases=[dict()]+[dict(changed={name:'front' if name=='ri' else 'y' if name=='eised' else 'x'}) for name in base]
    cases += [dict(presentation=False),dict(order=False)]
    for case in cases:
        values=base|case.get('changed',{});results=[];traces=[]
        for original in (True,False):
            trace=[];traces.append(trace)
            def forbidden(*args):raise ValueError('Quoted measurement content was executed')
            def presented(node,person,doc,message,context):
                syntax=json.loads(message.syntax)
                if not original:syntax=renamed(syntax,{v:k for k,v in mapping().items()})
                trace.append([node,person,doc,syntax,context])
                return case.get('presentation',True) and (node,person,doc,context)==('y','y','y','body') and syntax==call('eiig')
            def before(first,second,context):
                trace.append([first,second,context]);return case.get('order',True) and (first,second,context)==('x','y','body')
            if original:
                doc=source_excerpt();handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
                handlers.update({n:lambda value=value:value for n,value in values.items()});handlers.update(eir3=presented,ue=before)
            else:
                doc=deepcopy(restored()['document']);doc['statements']=doc['statements'][5:]
                voc=vocabulary();handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
                model=author.NamePresentation('front',{('front',2):('x','x',values['rd'],values['eirf'])},
                    presented={},applied={},authors={},forms={})
                from scripts.discourse_setting_profile import DiscourseReferences
                refs=DiscourseReferences({values['eirf']:values['ri']},{},
                    {(values['ri'],4,2):values['eised'],(values['ri'],5,1):values['eisel']},{})
                handlers.update({voc._symbols[n]:f for n,f in (model.handlers()|refs.handlers()|dict(presentsmessage=presented,textbefore=before)).items()})
            result=evaluate_document(doc,individuals=('x','y'),situations=('front','body'),primitives=handlers)[0]
            results.append(result)
        require(results[0]==results[1] and traces[0]==traces[1],'Attribution binding differs')
        require(results[0]['value'] is (not case),'Unexpected attribution outcome')
        rows.append(dict(case=case,value=results[0]['value'],calls=traces[0]))
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Measurement bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-designation-purpose-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,MATH_LIBRARY,
        'scripts/physical_position_profile.py','scripts/physical_position_contracts.py','scripts/check_einstein_physical_position.py',
        'scripts/visible_physical_position_collection.py','tests/test_physical_position_profile.py','docs/einstein-physical-position-v1.md',
        'data/einstein-point-position-review-v1.json','data/einstein-point-position-source-reading-v1.json'}
    return dict(schema='noema-einstein-physical-position-evidence-1',core_words=375,profile_words=409,profile_edition=21,
        new_reference_primitives=0,preserved_source_relations=12,inline_shared_mathematics_definitions=11,shared_rational_primitives=4,
        newly_connected_source_assertions=1,total_connected_source_assertions=4,orthographic_annotation_assertions=2,
        declarations=len(document()['declarations']),statements=len(document()['statements']),
        pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        attribution_diagnostics=presentation_diagnostics(),full_real_domain_evaluated=False,
        full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        limits=profile.LIMITS+['Inner mathematical and physical definitions preserve the reviewed bodies; attribution diagnostics do not prove measurement or real-field theorems.'])
