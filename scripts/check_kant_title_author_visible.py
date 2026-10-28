"""Connect the adopted title question and author display with visible references."""
from copy import deepcopy
from functools import lru_cache,wraps
import hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts import action_occurrence_visible_profile as profile
from scripts.agency_inquiry_visible_profile_contracts import SOURCE_RELATIONS
from scripts import name_presentation_profile as names_profile
from scripts.shared_modality import call,renamed
from scripts.shared_reference import definition
from scripts.visible_word_forms import Word,symbol
from scripts.visible_selection_vocabulary import SelectionVocabulary
from scripts.visible_vocabulary_session import vocabulary_session
from scripts.visible_parallel_collection import decode_files
from scripts.visible_parallel_render import iter_rendered_volumes
from scripts.visible_syntax_geometry import to_svg
from scripts.visible_lexical_script import require

ROOT=profile.ROOT
SOURCE='examples/v016/kant-title-author-visible-v1.noema'
BRIDGE='data/kant-title-author-visible-bridge-v1.json'
OUT=ROOT/'output/kant-title-author-visible-v1'
ANCHORS='data/kant-paratext-anchors-v1.json'
SOURCE_ORDER=[0,16]
PUBLIC={old:r['public'] for old,r in SOURCE_RELATIONS.items()}|{'dg':'actionoccurrence','hzih':'nameapplies','hzij':'authordisplay'}
SHARED={'xa':'assessmentvalid','xd':'assessedability','xe':'methodsassessable'}
FIELDS={'hzig':'use','hzif':'designation','wa':'target','hzik':'document'}
LABEL=Word('proper',('book','home','aki','book'))


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def num(value):return dict(kind='number',numerator=value,denominator=1)


@lru_cache(maxsize=1)
def catalog():
    from noema.meaning_catalog import load_catalog
    state=read('data/work-state.json');active=read(state['review_index'])['works']['kant-1784']
    require(active['document']=='examples/v016/kant-reviewed-complete-v1.noema','Unplanned Kant source')
    return load_catalog(ROOT,active['meaning_basis'],document_path=active['document'])


@lru_cache(maxsize=1)
def vocabulary():return profile.ActionOccurrenceVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    source=catalog().document;ds={d['name']:d for d in source['declarations']};seen=set()
    pending=_references([source['statements'][i] for i in SOURCE_ORDER])
    while pending:
        name=pending.pop()
        if name not in seen:seen.add(name);pending.update(_references(ds[name].get('body')))
    require(len(seen)==60,'Title/author dependency group changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in source['declarations'] if d['name'] in seen],
        statements=deepcopy([source['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
def names():
    selected=[d['name'] for d in source_excerpt()['declarations'] if d['name'] not in PUBLIC|SHARED]
    selected+=['packet',*('display'+field for field in names_profile.FIELDS)]
    parts=('home','above','give','inside','aki','nao','book','round')
    values={n:symbol(Word('compound',('book','home','aki','nao',parts[i//8],parts[i%8])),vocabulary())
        for i,n in enumerate(selected)}
    require(len(values)==len(set(values.values())) and not set(values.values())&set(vocabulary()._by_symbol),'Local spelling collision')
    return values


def mapping():return names()|{old:vocabulary()._symbols[new] for old,new in (PUBLIC|SHARED).items()}


@lru_cache(maxsize=1)
def document():
    voc=vocabulary();n=names();m=mapping();k=lambda old:call(n[old])
    imported=set(PUBLIC.values())|set(SHARED.values())|{'textpresentation','closingpresentationrecord','documentcontext','frontmatterreference','printedform'}
    doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=voc.imports(imported),statements=[])
    accessors=[d for d in names_profile.accessors()['declarations'] if d['name'].startswith('display')]
    doc['declarations']+=renamed(accessors,n)
    doc['declarations'].append(definition(n['hzim'],[],'situation',call(voc._symbols['textpresentation'])))
    doc['declarations'].append(definition(n['packet'],[],names_profile.RECORD,
        call(voc._symbols['closingpresentationrecord'],k('hzim'),num(1))))
    for old,field in FIELDS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(n['display'+field],k('packet'))))
    doc['declarations'].append(definition(n['wh'],[],'situation',call(voc._symbols['documentcontext'],k('hzik'))))
    doc['declarations'].append(definition(n['hzia'],[],'individual',call(voc._symbols['frontmatterreference'],k('hzim'),num(6))))
    existing={d['name']:d for d in doc['declarations']}
    for d in source_excerpt()['declarations']:
        if d['name'] in PUBLIC:
            actual=existing[m[d['name']]]
            require(actual['kind']=='primitive' and actual['parameters']==d['parameters'] and actual['result']==d['result'],
                'Public relation signature changed: '+d['name'])
        if d['name'] in SHARED:require(existing[m[d['name']]]==renamed(d,m),'Shared ability body changed: '+d['name'])
        elif d['kind']=='definition':doc['declarations'].append(renamed(d,m))
    doc['statements']=renamed(source_excerpt()['statements'],m)
    form=read(ANCHORS)['author_printed_form']
    require(form['text']=='I. Kant.' and form['language']=='de','Adopted author form changed')
    doc['statements'].append(dict(kind='assert',body=call(voc._symbols['printedform'],k('hzif'),
        names_profile.text_expression(form['language']),names_profile.text_expression(form['text']),k('hzim'))))
    return normalize_document(doc)


def backprojection(actual):
    ds={d['name']:d for d in actual['declarations']};inverse={value:key for key,value in mapping().items()}
    recovered=deepcopy(source_excerpt())
    recovered['declarations']=[renamed(ds[mapping()[d['name']]],inverse) if d['kind']=='definition' else d
        for d in recovered['declarations']]
    recovered['statements']=renamed(actual['statements'][:2],inverse)
    return normalize_document(recovered)


def review_bindings():
    state=read('data/work-state.json');active=read(state['review_index'])['works']['kant-1784'];result=[]
    for unit,index in [('kant-1784:u0006',0),('kant-1784:u0018',16)]:
        rows=[row for row in active['reviews'] if read(row['review'])['unit']==unit]
        require(len(rows)==1 and rows[0]['statements']==[index],'Review selection changed')
        record=read(rows[0]['review'])
        require(record['decision']=='equivalent_under_stated_reading' and record['unresolved']==[],'Source review incomplete')
        result.append(dict(unit=unit,review=rows[0]['review'],source_statement=index))
    return result


def bridge():
    require(backprojection(document())==source_excerpt(),'Recovered source definitions or assertions differ')
    anchors=read(ANCHORS)
    require(anchors['title_question_frontmatter_item']==6 and anchors['author_closing_item']==1,'Reference positions changed')
    return dict(schema='noema-kant-title-author-visible-bridge-1',source_document=catalog().document_path,
        source_statement_indices=SOURCE_ORDER,source_statements=source_excerpt()['statements'],
        source_declarations=source_excerpt()['declarations'],mapping=mapping(),profile_edition=92,core_edition=12,
        shared_definitions=SHARED,public_relations=PUBLIC,review_bindings=review_bindings(),
        reference_bindings=dict(hzim='textpresentation()',packet='closingpresentationrecord(hzim,1)',
            hzig='displayuse(packet)',hzif='displaydesignation(packet)',wa='displaytarget(packet)',
            hzik='displaydocument(packet)',wh='documentcontext(hzik)',hzia='frontmatterreference(hzim,6)'),
        public_relation_review=[
            dict(source='hzih',public='nameapplies',decision='same_adopted_relation',
                 reason='同じ提示行為・名称・対象・文脈の適用関係を保つ。綴りから同一性を補わず、別の提示の適用先を流用しない。'),
            dict(source='hzij',public='authordisplay',decision='same_adopted_relation',
                 reason='同じ提示行為が同じ文書の対象を著者として表示する役割。表示の真実性、自筆性、物理的な提示者の同定を補わない。')],
        source_assertions=2,orthographic_annotations=1,formal_integration_credit=0,
        original_manuscript_modified=False,semantic_equivalence_automatically_proved=False)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible Kant title/author document differs')
    return result


def prepare_native():
    profile.write_once(SOURCE,format_graph(document())+'\n');profile.write_once(BRIDGE,bridge())


def prepare():
    prepare_native();count=0
    for volume in iter_rendered_volumes(document(),LABEL,vocabulary(),workers=8,payload=768):
        for page in volume['pages']:
            count+=1;profile.write_once(OUT/f'page-{count:05d}.svg',to_svg(page['shapes']))


def source_pins():
    from scripts.check_einstein_early_visible import source_pins as parent_pins
    paths=set(parent_pins())|set(catalog().source_sha256)|{
        SOURCE,BRIDGE,ANCHORS,'scripts/check_kant_title_author_visible.py','tests/test_kant_title_author_visible.py',
        'scripts/check_author_credit.py','scripts/check_explanatory_question.py',
        'scripts/visible_action_occurrence_collection.py','tests/test_kant_title_author_semantics_visible.py',
        'reports/explanatory-question-v1.json'}
    paths.update(row['review'] for row in review_bindings())
    for stem in ('agency-inquiry-visible-profile','closing-presentation-profile','action-occurrence-visible-profile'):
        paths.update((f'examples/v016/{stem}-v1.noema',f'data/{stem}-basis-v1.json',f'noema/resources/visible-{stem}-v1.json',
            'scripts/'+stem.replace('-','_')+'.py','scripts/'+stem.replace('-','_')+'_contracts.py','tests/test_'+stem.replace('-','_')+'.py'))
    paths.update(read(ANCHORS)['source_sha256'])
    return {p:digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(read(BRIDGE)==bridge(),'Saved Kant bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Kant Native differs')
    require(backprojection(result['document'])==source_excerpt(),'Recovered source body differs')
    return dict(schema='noema-kant-title-author-visible-evidence-1',profile_edition=92,profile_words=1156,core_words=375,
        declarations=len(document()['declarations']),statements=3,source_assertions=2,annotations=1,
        pages=result['pages'],volumes=result['volumes'],source_sha256=source_pins(),
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        independent_human_reading=False,full_manuscript_visible_decoding=False,semantic_equivalence_automatically_proved=False)
