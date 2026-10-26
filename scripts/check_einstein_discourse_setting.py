"""Integrate the first coordinate setting with the existing visible author record."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import _references
from scripts import discourse_setting_profile as profile
from scripts.discourse_setting_profile import ROOT,DiscourseSettingVocabulary,DiscourseReferences,write_once
from scripts import check_einstein_name_presentation as author
from scripts.check_manuscript_context import catalogs
from scripts.shared_modality import call,renamed
from scripts.shared_reference import definition
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-discourse-setting-v1.noema'
BRIDGE='data/einstein-discourse-setting-bridge-v1.json'
OUT=ROOT/'output/einstein-discourse-setting-v1'
LABEL=Word('proper',('book','give','inside','book','red'))
PREDICATES=profile.SOURCE_RELATIONS|dict(ue='textbefore')
FORMS={
 'ri':Word('compound',('book','give','inside','home','book')),
 'eisd2':Word('proper',('book','give','inside','above')),
 'eisec':Word('proper',('book','give','inside','book')),
 'ra':Word('proper',('book','give','inside','aki')),
 **{old:Word('compound',('book','give','inside',part,'book')) for old,part in
    zip(('eifb','eiht','eihu','eihv','eihw'),('town','round','inside','give','assessmentvalid'),strict=True)}}


@lru_cache(maxsize=1)
def vocabulary():return DiscourseSettingVocabulary()


def names():
    result=author.names()|{n:symbol(w,vocabulary()) for n,w in FORMS.items()}
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision')
    return result


@lru_cache(maxsize=1)
def source_excerpt():
    c=catalogs()['einstein-1905'];ds={d['name']:d for d in c.document['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for r in _references(ds[n].get('body')):visit(r)
    statement=c.document['statements'][57]
    for n in _references(statement):visit(n)
    require(seen==set(PREDICATES)|set(FORMS)|{'rd','eirf'},'Source closure changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in seen],statements=[deepcopy(statement)]))


@lru_cache(maxsize=1)
def document():
    n=names();v=vocabulary();doc=author.vocabulary().decode_names(deepcopy(author.document()))
    additional={*profile.PARAMETERS,'textbefore','sentencereference'}
    doc['declarations']+=v.decode_names(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=v.imports(additional),statements=[]))['declarations']
    doc['declarations'] += [
        definition(n['ri'],[],'situation',call('documentcontext',call(n['eirf']))),
        definition(n['eisd2'],[],'individual',call('headingreference',call(n['ri']),author.num(2))),
        definition(n['eisec'],[],'individual',call('sentencereference',call(n['ri']),author.num(4),author.num(1))),
        definition(n['ra'],[],'individual',call('discoursereferent',call(n['eirf']),call(n['eisec']),author.num(1),call(n['ri'])))]
    mapping=n|PREDICATES
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['kind']=='definition'],mapping)
    doc['statements']+=renamed(source_excerpt()['statements'],mapping)
    return v.encode(normalize_document(doc))


def backprojection(migrated):
    require(migrated==document(),'Changed migration cannot be rebound to old evidence')
    decoded=vocabulary().decode_names(migrated);ds={d['name']:d for d in decoded['declarations']}
    inverse={v:k for k,v in (names()|PREDICATES).items()};source=deepcopy(source_excerpt())
    source['declarations']=[renamed(ds[PREDICATES[d['name']]],inverse) if d['name'] in PREDICATES else
        renamed(ds[names()[d['name']]],inverse) if d['kind']=='definition' else deepcopy(d) for d in source['declarations']]
    source['statements']=[renamed(decoded['statements'][2],inverse)]
    return normalize_document(source)


def bridge():
    c=catalogs()['einstein-1905'];units=author.read(author.UNITS)['units']
    heading=[u for u in units if u['kind']=='heading'][1];paragraph=[u for u in units if u['kind']=='body'][3]
    require(heading['id']=='einstein-1905:u0007' and paragraph['id']=='einstein-1905:u0008','Text positions changed')
    text=paragraph['text'][:95]
    require(text=='Es liege ein Koordinatensystem vor, in welchem die Newtonschen mechanischen Gleichungen gelten.','Selected source sentence changed')
    for old,new in profile.SOURCE_RELATIONS.items():
        require(c.entries[old]['meaning_ja'].removeprefix('[current の記号名] ')==profile.MEANINGS[new],
            'Source relation meaning changed: '+old)
    require(c.entries['ue']['meaning_ja'].removeprefix('[current の記号名] ')==vocabulary().document()['compounds']['textbefore']['meaning'],
        'Text order meaning changed')
    require(backprojection(document())==source_excerpt(),'Source projection differs')
    return dict(schema='noema-einstein-visible-discourse-setting-bridge-1',reviewer='assistant',
        source_statement_index=57,source_document=c.document_path,source_assertion=source_excerpt()['statements'][0],
        source_declarations=source_excerpt()['declarations'],source_unit=paragraph['id'],source_unit_sha256=paragraph['text_sha256'],
        source_range=[0,95],source_text=text,heading_unit=heading['id'],heading_sha256=heading['text_sha256'],
        bindings=dict(rd='existing author display target',eirf='existing author display document',
            ri='documentcontext(eirf)',eisd2='headingreference(ri,2)',eisec='sentencereference(ri,4,1)',
            ra='discoursereferent(eirf,eisec,1,ri)'),local_names=names(),profile_edition=19,
        meanings={n:dict(meaning_ja=c.entries[n]['meaning_ja'],meaning_basis=c.entries[n]['meaning_basis'])
                  for n in [d['name'] for d in source_excerpt()['declarations']]},
        semantic_review=[
            'Es liegeを、同じ対象参照を導入し条件内容を仮定に採用して議論を進める指示として保持する。',
            'Newtonの方程式が成り立つ条件はeihtのcontent内にあり、その真理を外側で断言しない。',
            'eihuは参照導入と仮定採用を同じ箇所・著者・論説へ結ぶ。eihvはdirectのmessageである。',
            'eihwはその閉じたmessageの記述を著者へ帰属する。指示内容の実行や読者の遵守を要求しない。',
            '第一節見出しとは異なる箇所で、同じ本文提示文脈の後続位置であることを保つ。',
            '既存のspeechpresentedは受け手を取るmessage関数の記述と行為関係を要求するため、今回の閉じたmessageの帰属へ同義とみなして代用しない。'],
        newly_connected_source_assertions=1,total_connected_source_assertions=2,orthographic_annotation_assertions=1,
        original_manuscript_modified=False,old_judgments_rebound=False,
        limits=profile.LIMITS+['見出しの主題と段落の残りはまだこの文書に接続していない。全文の移行や第三者読解ではない。'])


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible setting differs');return result


def probe_document(doc,target):
    result=deepcopy(doc)
    n=names() if doc!=source_excerpt() else {x:x for x in FORMS}
    if target=='eifb':body=call(n[target],call(n['ra']),call(n['ri']))
    elif target in ('eiht','eihu'):
        body=dict(kind='evaluate',content=call(n[target]),situation=call(n['ri']))
    elif target=='eihv':
        body=dict(kind='evaluate',content=dict(kind='message_content',message=call(n[target])),situation=call(n['ri']))
    else:body=call(n[target])
    result['statements']=[dict(kind='ask',body=body)];return normalize_document(result)


def interpreted_pair(*,target='eihw',changed=None,truths=None):
    """Single-binding diagnostics with two individuals and two situations.

    Changed references vary one slot at a time; description spelling is mapped
    only for this comparison. The executable reader never uses the source map.
    """
    values=dict(rd='y',eirf='y',ri='body',eisd2='x',eisec='y',ra='x')
    if changed:values.update(changed)
    facts=dict(presentsmessage=True,textbefore=True,introducesreferent=True,
        adoptsassumption=True,physicalframe=True,newtonianframe=True)
    if truths:facts.update(truths)
    traces=[];answers=[]
    for original in (True,False):
        trace=[];traces.append(trace);mapping={v:k for k,v in names().items()}
        def description(value,expected):
            node=json.loads(value.syntax)
            if not original:node=renamed(node,mapping)
            return node==call(expected)
        def relation(name,args,expected,desc=None):
            normalized=list(args)
            if desc:
                slot,expected_name=desc
                normalized[slot]=expected_name if description(args[slot],expected_name) else 'different-description'
            trace.append(dict(relation=name,arguments=normalized))
            return facts[name] and tuple(normalized)==expected
        relations=dict(
            presentsmessage=lambda node,person,doc,msg,s:relation('presentsmessage',(node,person,doc,msg,s),('y','y','y','eihv','body'),(3,'eihv')),
            textbefore=lambda first,second,s:relation('textbefore',(first,second,s),('x','y','body')),
            introducesreferent=lambda node,ref,doc,s:relation('introducesreferent',(node,ref,doc,s),('y','x','y','body')),
            adoptsassumption=lambda node,person,content,doc,s:relation('adoptsassumption',(node,person,content,doc,s),('y','y','eiht','y','body'),(2,'eiht')),
            physicalframe=lambda ref:relation('physicalframe',(ref,),('x',)),
            newtonianframe=lambda ref,s:relation('newtonianframe',(ref,s),('x','body')))
        if original:
            doc=source_excerpt();handlers={old:relations[new] for old,new in PREDICATES.items()}
            handlers.update({n:lambda value=value:value for n,value in values.items()})
        else:
            doc=restored()['document']
            # The frontmatter anchor is deliberately distinct from body.
            model=author.NamePresentation('front',{('front',2):('x','x',values['rd'],values['eirf'])},
                presented={},applied={},authors={},forms={})
            handlers=model.handlers()
            refs=DiscourseReferences({values['eirf']:values['ri']},
                {(values['ri'],2):values['eisd2']},{(values['ri'],4,1):values['eisec']},
                {(values['eirf'],values['eisec'],1,values['ri']):values['ra']})
            handlers.update(refs.handlers());handlers.update(relations)
            handlers={vocabulary()._symbols[n]:f for n,f in handlers.items()}
        answer=evaluate_document(probe_document(doc,target),individuals=('x','y'),situations=('front','body'),primitives=handlers)[0]
        answers.append(answer)
    require(answers[0]==answers[1] and traces[0]==traces[1],'Old/new context interpretation differs')
    return dict(target=target,changed=changed or {},truths=truths or {},answer=answers[0],calls=traces[0])


def diagnostics():
    cases=[dict(target=t) for t in ('eifb','eiht','eihu','eihv','eihw')]
    for target,fields in [('eifb',('ra','ri')),('eiht',('ra','ri')),('eihu',('rd','eirf','eisec','ra','ri')),
                          ('eihv',('rd','eirf','eisec','ra','ri')),('eihw',('rd','eirf','eisd2','eisec','ri'))]:
        for field in fields:cases.append(dict(target=target,changed={field:'front' if field=='ri' else 'y' if field in ('ra','eisd2') else 'x'}))
    cases += [dict(target=target,truths={relation:False}) for target,relations in
        [('eifb',('physicalframe','newtonianframe')),('eiht',('physicalframe','newtonianframe')),
         ('eihu',('introducesreferent','adoptsassumption')),('eihv',('introducesreferent','adoptsassumption')),
         ('eihw',('presentsmessage','textbefore'))] for relation in relations]
    # All inner predicates can be false while the attribution stays true.
    cases.append(dict(truths=dict(introducesreferent=False,adoptsassumption=False,physicalframe=False,newtonianframe=False)))
    return [interpreted_pair(**case) for case in cases]


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(author.read(BRIDGE)==bridge(),'Setting bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    previous='reports/einstein-name-presentation-v1.json';prior=author.read(previous);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(author.digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,previous,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,
        'scripts/discourse_setting_profile.py','scripts/check_einstein_discourse_setting.py',
        'scripts/visible_discourse_setting_collection.py','tests/test_discourse_setting_profile.py','docs/einstein-discourse-setting-v1.md'}
    return dict(schema='noema-einstein-discourse-setting-evidence-1',core_words=375,profile_words=391,profile_edition=19,
        new_reference_primitives=3,preserved_source_relations=5,newly_connected_source_assertions=1,
        total_connected_source_assertions=2,orthographic_annotation_assertions=1,
        declarations=len(document()['declarations']),statements=len(document()['statements']),
        pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        binding_diagnostics=diagnostics(),full_manuscript_visible_decoding=False,independent_human_reading=False,
        source_sha256={p:author.digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():author.digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        limits=profile.LIMITS+['Single-binding diagnostics are not exhaustive proofs over every relation interpretation.'])
