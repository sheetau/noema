"""Complete the visible coordinate-setting paragraph without executing its purposes."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.identifiers import load_annotations
from noema.meaning_catalog import _references
from scripts import designation_purpose_profile as profile
from scripts.designation_purpose_profile import ROOT,DesignationPurposeVocabulary,DesignationReferences,write_once
from scripts.discourse_setting_profile import DiscourseReferences
from scripts import check_einstein_discourse_setting as previous
from scripts import check_einstein_name_presentation as author
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed
from scripts.shared_reference import definition
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-designation-purpose-v1.noema'
BRIDGE='data/einstein-designation-purpose-bridge-v1.json'
OUT=ROOT/'output/einstein-designation-purpose-v1'
LABEL=Word('proper',('book','give','book','book','red'))
PREDICATES=profile.SOURCE_RELATIONS|{n:previous.PREDICATES[n] for n in ('eir3','ue','va')}
FORMS={
 'eiseb':Word('proper',('book','give','book','aki')),
 'eised':Word('proper',('book','give','book','book')),
 **{old:Word('compound',('book','give','book',part,'book')) for old,part in
    zip(('eihx','eihy','eihz','eih2','eih3','eih4','eih5'),
        ('home','inside','assessmentvalid','aki','above','give','round'),strict=True)}}


@lru_cache(maxsize=1)
def vocabulary():return DesignationPurposeVocabulary()


def names():
    result=previous.names()|{n:symbol(w,vocabulary()) for n,w in FORMS.items()}
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision')
    return result


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    statement=c.document['statements'][58]
    for n in _references(statement):visit(n)
    require(seen==set(PREDICATES)|set(FORMS)|{'rd','eirf','ri','ra','eisec'},'Source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=[deepcopy(statement)]))


@lru_cache(maxsize=1)
def annotation():
    state=author.read('data/work-state.json');spec=author.read(state['review_index'])['works']['einstein-1905']
    annotations=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations'])
    row=next(r for r in annotations.annotations['entries'] if r['symbol']=='eiseb')
    require(row==dict(symbol='eiseb',role='designation',forms=[dict(text='ruhende System',language='de',role='printed_identifying_form')]),
            'Selected designation form changed')
    return dict(path=spec['identifier_annotations'],entry=row,source_sha256=annotations.show()['source_sha256'])


@lru_cache(maxsize=1)
def document():
    n=names();v=vocabulary();doc=previous.vocabulary().decode_names(deepcopy(previous.document()))
    doc['declarations']+=v.decode_names(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=v.imports(set(profile.PARAMETERS)),statements=[]))['declarations']
    doc['declarations'] += [
        definition(n['eised'],[],'individual',call('sentencereference',call(n['ri']),author.num(4),author.num(2))),
        definition(n['eiseb'],[],'individual',call('designationreference',call(n['eirf']),call(n['eised']),author.num(1),call(n['ri'])))]
    mapping=n|PREDICATES
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['kind']=='definition'],mapping)
    doc['statements']+=renamed(source_excerpt()['statements'],mapping)
    form=annotation()['entry']['forms'][0]
    doc['statements'].append(dict(kind='assert',body=call('printedform',call(n['eiseb']),
        author.text_expression(form['language']),author.text_expression(form['text']),call(n['ri']))))
    return v.encode(normalize_document(doc))


def visible_form(doc):
    # Use the existing literal-scalar extractor, which does not consult the
    # annotation file. Stable inherited symbols also decode under profile 18.
    return author.visible_form(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=doc['declarations'],statements=[doc['statements'][0],doc['statements'][4]]))


def backprojection(migrated):
    require(migrated==document(),'Changed migration cannot be rebound to old evidence')
    decoded=vocabulary().decode_names(migrated);ds={d['name']:d for d in decoded['declarations']}
    inverse={v:k for k,v in (names()|PREDICATES).items()};source=deepcopy(source_excerpt())
    source['declarations']=[renamed(ds[PREDICATES[d['name']]],inverse) if d['name'] in PREDICATES else
        renamed(ds[names()[d['name']]],inverse) if d['kind']=='definition' else deepcopy(d) for d in source['declarations']]
    source['statements']=[renamed(decoded['statements'][3],inverse)]
    return normalize_document(source)


def bridge():
    c=catalogs()['einstein-1905'];unit=author.read(author.UNITS)['units'][7]
    require(unit['id']=='einstein-1905:u0008' and len(unit['text'])==266,'Paragraph changed')
    text=unit['text'][96:266];form=annotation()['entry']['forms'][0]
    require(text=='Wir nennen dies Koordinatensystem zur sprachlichen Unterscheidung von später einzuführenden Koordinatensystemen und zur Präzisierung der Vorstellung das „ruhende System“.',
        'Selected naming sentence changed')
    require('„'+form['text']+'“' in text,'Printed designation differs')
    require(unit['text'][95:96]==' ' and previous.bridge()['source_range']==[0,95],'Paragraph coverage has a gap')
    for old,new in profile.SOURCE_RELATIONS.items():
        require(c.entries[old]['meaning_ja']==profile.MEANINGS[new],'Source relation meaning changed: '+old)
    require(backprojection(document())==source_excerpt(),'Source projection differs')
    return dict(schema='noema-einstein-visible-designation-purpose-bridge-1',reviewer='assistant',
        source_statement_index=58,source_document=c.document_path,source_assertion=source_excerpt()['statements'][0],
        source_declarations=source_excerpt()['declarations'],source_unit=unit['id'],source_unit_sha256=unit['text_sha256'],
        source_range=[96,266],source_text=text,paragraph_ranges=[[0,95],[96,266]],inter_sentence_whitespace=[95,96],
        bindings=dict(eised='sentencereference(ri,4,2)',eiseb='designationreference(eirf,eised,1,ri)',
            ra='unchanged first-sentence referent',rd='unchanged displayed author',eirf='unchanged document',ri='unchanged body context'),
        local_names=names(),profile_edition=20,
        meanings={n:dict(meaning_ja=c.entries[n]['meaning_ja'],meaning_basis=c.entries[n]['meaning_basis'])
                  for n in [d['name'] for d in source_excerpt()['declarations']]},
        semantic_review=[
            '第一文で導入した同じraを、第二文で同じ著者がeisebと呼ぶ。新しい座標系の導入や命題の略称へ替えない。',
            'eihxは後で導入予定の、raとは異なる物理座標系の全範囲を指定する。存在量化を追加しない。',
            'eihyの言い分けとeihzの観念明確化を、同じ命名行為eih2の二目的としてeih3で結ぶ。二目的を一つに潰さない。',
            '二目的は閉じたcontentの記述として参照し、達成の真偽をこの命名と目的の内容で実行しない。',
            '第二文のmessageの力はassertであり、第一文のdirectと区別する。著者への帰属は引用を実行しない。',
            '静止系という表記から絶対静止、全物体の停止、唯一の基準系を導かない。',
            '既存speechadviceの目的は受け手付き内容関数の記述と助言関係を要求し、今回の閉じた命名行為の目的関係とは同義でない。',
            '段落全体で設定から命名へ同じraを保ち、本文順序と異なる箇所であることを維持する。'],
        identifier_annotation=annotation()['entry'],identifier_annotation_path=annotation()['path'],
        visible_identifier_form=visible_form(document()),
        newly_connected_source_assertions=1,total_connected_source_assertions=3,orthographic_annotation_assertions=2,
        original_manuscript_modified=False,old_judgments_rebound=False,
        limits=profile.LIMITS+['u0008の二文を接続した。前後の全段落・節見出しの意味・全文の移行と第三者読解は未完。'])


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible designation differs');return result


def probe_document(doc,target,original=False,candidate='y'):
    result=deepcopy(doc);n={x:x for x in names()} if original else names()
    if target=='eihx':
        # Both candidates are supplied through existing contextual references:
        # frame x, designation y. No large quantified function domain is used.
        body=call(n[target],call(n['ra'] if candidate=='x' else n['eiseb']),call(n['ri']))
    elif target in ('eihy','eihz','eih2','eih3'):
        body=dict(kind='evaluate',content=call(n[target]),situation=call(n['ri']))
    elif target=='eih4':
        body=dict(kind='evaluate',content=dict(kind='message_content',message=call(n[target])),situation=call(n['ri']))
    else:body=call(n[target])
    result['statements']=[dict(kind='ask',body=body)];return normalize_document(result)


def interpreted_pair(*,target='eih5',changed=None,truths=None,candidate='y'):
    values=dict(rd='y',eirf='y',ri='body',eisec='y',ra='x',eised='x',eiseb='y')
    if changed:values.update(changed)
    facts=dict(presentsmessage=True,textbefore=True,physicalframe=True,adoptsdesignation=True,
        purpose_distinguish=True,purpose_clarify=True,designationdistinguishes=True,anticipatedreferent=True,designationclarifies=True)
    if truths:facts.update(truths)
    traces=[];answers=[]
    for original in (True,False):
        trace=[];traces.append(trace);mapping={v:k for k,v in names().items()}
        def description(value):
            node=json.loads(value.syntax)
            if not original:node=renamed(node,mapping)
            if node.get('kind')=='call' and not node['arguments']:return node['symbol']
            if node.get('kind')=='function_ref':return '&'+node['symbol']
            return 'different-description'
        def relation(name,args,expected,descs=()):
            normalized=list(args)
            for index in descs:normalized[index]=description(args[index])
            trace.append(dict(relation=name,arguments=normalized))
            return facts[name] and tuple(normalized)==expected
        def purpose(agent,action,goal,scope,context):
            goal_name=description(goal)
            require(goal_name in ('eihy','eihz'),'Unknown purpose in diagnostic interpretation')
            return relation('purpose_distinguish' if goal_name=='eihy' else 'purpose_clarify',
                (agent,action,goal,scope,context),('y','eih2',goal_name,'y','body'),(1,2))
        relations=dict(
            presentsmessage=lambda node,person,doc,msg,s:relation('presentsmessage',(node,person,doc,msg,s),('x','y','y','eih4','body'),(3,)),
            textbefore=lambda first,second,s:relation('textbefore',(first,second,s),('y','x','body')),
            physicalframe=lambda ref:relation('physicalframe',(ref,),(ref,)),
            adoptsdesignation=lambda node,person,name,target,doc,s:relation('adoptsdesignation',(node,person,name,target,doc,s),('x','y','y','x','y','body')),
            actionpurpose=purpose,
            designationdistinguishes=lambda name,target,alts,doc,s:relation('designationdistinguishes',(name,target,alts,doc,s),('y','x','&eihx','y','body'),(2,)),
            anticipatedreferent=lambda ref,doc,after,s:relation('anticipatedreferent',(ref,doc,after,s),(ref,'y','x','body')),
            designationclarifies=lambda name,target,doc,s:relation('designationclarifies',(name,target,doc,s),('y','x','y','body')))
        if original:
            doc=source_excerpt();handlers={old:relations[new] for old,new in PREDICATES.items()}
            handlers.update({n:lambda value=value:value for n,value in values.items()})
        else:
            doc=restored()['document']
            model=author.NamePresentation('front',{('front',2):('x','x',values['rd'],values['eirf'])},
                presented={},applied={},authors={},forms={})
            refs=DiscourseReferences({values['eirf']:values['ri']},{(values['ri'],2):'x'},
                {(values['ri'],4,1):values['eisec'],(values['ri'],4,2):values['eised']},
                {(values['eirf'],values['eisec'],1,values['ri']):values['ra']})
            designations=DesignationReferences({(values['eirf'],values['eised'],1,values['ri']):values['eiseb']})
            def unexpected(*args):raise ValueError('Unrelated setting predicate executed')
            handlers=model.handlers()|refs.handlers()|designations.handlers()|relations|dict(
                adoptsassumption=unexpected,introducesreferent=unexpected,newtonianframe=unexpected)
            handlers={vocabulary()._symbols[n]:f for n,f in handlers.items()}
        answer=evaluate_document(probe_document(doc,target,original,candidate),individuals=('x','y'),situations=('front','body'),primitives=handlers)[0]
        answers.append(answer)
    require(answers[0]==answers[1] and traces[0]==traces[1],'Old/new naming interpretation differs')
    return dict(target=target,changed=changed or {},truths=truths or {},candidate=candidate,answer=answers[0],calls=traces[0])


def diagnostics():
    cases=[(True,dict(target=t)) for t in ('eihx','eihy','eihz','eih2','eih3','eih4','eih5')]
    slots={'eihx':('eirf','eised','ra','ri'),'eihy':('eiseb','ra','eirf','ri'),
           'eihz':('eiseb','ra','eirf','ri'),'eih2':('eised','rd','eiseb','ra','eirf','ri'),
           'eih3':('eised','rd','eiseb','ra','eirf','ri'),'eih4':('eised','rd','eiseb','ra','eirf','ri'),
           'eih5':('eised','rd','eirf','eisec','ri')}
    for target,fields in slots.items():
        for field in fields:
            cases.append((False,dict(target=target,changed={field:'front' if field=='ri' else 'y' if field in ('ra','eised') else 'x'})))
    for mask in range(8):
        cases.append((mask==7,dict(target='eih3',truths={name:bool(mask&(1<<i)) for i,name in
            enumerate(('adoptsdesignation','purpose_distinguish','purpose_clarify'))})))
    for target,relation in [('eihx','physicalframe'),('eihx','anticipatedreferent'),('eihy','designationdistinguishes'),
                            ('eihz','designationclarifies'),('eih5','presentsmessage'),('eih5','textbefore')]:
        cases.append((False,dict(target=target,truths={relation:False})))
    cases.extend([(False,dict(target='eihx',candidate='x')),
        (True,dict(target='eih3',truths=dict(designationdistinguishes=False,designationclarifies=False,anticipatedreferent=False,physicalframe=False))),
        (True,dict(target='eih5',truths=dict(adoptsdesignation=False,purpose_distinguish=False,purpose_clarify=False,
            designationdistinguishes=False,designationclarifies=False,anticipatedreferent=False,physicalframe=False)))])
    rows=[]
    for wanted,case in cases:
        row=interpreted_pair(**case);require(row['answer']['value'] is wanted,'Unexpected binding diagnostic outcome')
        rows.append(row|dict(expected=wanted))
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Designation bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    prior_path='reports/einstein-discourse-setting-v1.json';prior=author.read(prior_path);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,prior_path,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,
        'scripts/designation_purpose_profile.py','scripts/check_einstein_designation_purpose.py',
        'scripts/visible_designation_purpose_collection.py','tests/test_designation_purpose_profile.py','docs/einstein-designation-purpose-v1.md',
        *annotation()['source_sha256']}
    return dict(schema='noema-einstein-designation-purpose-evidence-1',core_words=375,profile_words=397,profile_edition=20,
        new_reference_primitives=1,preserved_source_relations=5,newly_connected_source_assertions=1,
        total_connected_source_assertions=3,orthographic_annotation_assertions=2,connected_body_paragraph='einstein-1905:u0008',
        declarations=len(document()['declarations']),statements=len(document()['statements']),
        pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        visible_identifier_form=visible_form(result['document']),binding_diagnostics=diagnostics(),
        full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        limits=profile.LIMITS+['Small distinguishing domains and one-slot variations are binding diagnostics, not exhaustive semantic proofs.'])
