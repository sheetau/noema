"""Connect office-scoped permission denial and required obedience to the preceding mechanism."""
from copy import deepcopy
from functools import lru_cache
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts import check_kant_public_purpose_mechanism_visible as previous
from scripts import office_obedience_visible_profile as profile
from scripts.shared_modality import call,renamed
from scripts.shared_reference import definition
from scripts import convenience_assessment_visible_profile as specialization
from scripts.visible_word_forms import Word,symbol
from scripts.visible_selection_vocabulary import SelectionVocabulary
from scripts.visible_vocabulary_session import vocabulary_session
from scripts.visible_parallel_collection import decode_files
from scripts.visible_parallel_render import iter_rendered_volumes
from scripts.visible_syntax_geometry import to_svg
from scripts.visible_lexical_script import require

ROOT=profile.ROOT
SOURCE='examples/v016/kant-office-obedience-visible-v1.noema'
BRIDGE='data/kant-office-obedience-visible-bridge-v1.json'
ANCHORS='data/kant-office-obedience-text-anchors-v1.json'
OUT=ROOT/'output/kant-office-obedience-visible-v1'
SOURCE_ORDER=previous.SOURCE_ORDER+[76]
VISIBLE_ORDER=previous.VISIBLE_ORDER+[59]
PUBLIC=previous.PUBLIC|{old:r['public'] for old,r in profile.SOURCE_RELATIONS.items()}
SHARED=previous.SHARED
LABEL=Word('proper',('book','home','round','inside'))
read=previous.read;digest=previous.digest;num=previous.num;catalog=previous.catalog


@lru_cache(maxsize=1)
def vocabulary():return profile.OfficeObedienceVisibleVocabulary()


@lru_cache(maxsize=1)
def source_excerpt():
    source=catalog().document;ds={d['name']:d for d in source['declarations']};seen=set()
    pending=_references([source['statements'][i] for i in SOURCE_ORDER])
    while pending:
        name=pending.pop()
        if name not in seen:seen.add(name);pending.update(_references(ds[name].get('body')))
    require(len(seen)==1687,'OfficeObedience dependency group changed')
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in source['declarations'] if d['name'] in seen],
        statements=deepcopy([source['statements'][i] for i in SOURCE_ORDER])))


@lru_cache(maxsize=1)
def names():
    prior=previous.names();existing={d['name'] for d in previous.source_excerpt()['declarations']}
    chosen=[d['name'] for d in source_excerpt()['declarations'] if d['name'] not in existing|set(PUBLIC)|set(SHARED)]
    chosen+=[n for n in (read(ANCHORS)['source_nodes']|read(ANCHORS)['source_spans']|read(ANCHORS)['source_character_spans']) if n not in chosen and n not in prior]
    parts=('home','above','give','inside','aki','nao','book','round')
    added={n:symbol(Word('compound',('book','home','round','inside',parts[i//64],parts[(i//8)%8],parts[i%8])),vocabulary()) for i,n in enumerate(chosen)}
    require(len(added)==9,'OfficeObedience local definition and span count changed')
    require(not set(added.values())&set(prior.values()),'Local spelling shadows parent')
    require(len(added)==len(set(added.values())) and not set(added.values())&set(vocabulary()._by_symbol),'Local spelling collision')
    return prior|added


def mapping():return names()|{old:vocabulary()._symbols[new] for old,new in (PUBLIC|SHARED).items()}


@lru_cache(maxsize=1)
def document():
    voc=vocabulary();m=mapping();doc=deepcopy(previous.document())
    existing={d['name'] for d in doc['declarations']}
    doc['declarations'] += [d for d in voc.imports(set(PUBLIC.values())|set(SHARED.values())|{'sentencetextspanreference','situationslot','sentencespanreference'}) if d['name'] not in existing]
    anchors=read(ANCHORS);n=names();k=lambda old:call(n[old])
    for old,paragraph in anchors['context_nodes'].items():
        doc['declarations'].append(definition(n[old],[],'situation',
            call(voc._symbols['paragraphpresentationcontext'],k('wh'),num(paragraph))))
    for old,(paragraph,sentence) in anchors['source_nodes'].items():
        doc['declarations'].append(definition(n[old],[],'individual',
            call(voc._symbols['sentencereference'],k('hzim'),num(paragraph),num(sentence))))
    for old,row in anchors['sentence_blocks'].items():
        doc['declarations'].append(definition(n[old],[],'individual',
            call(voc._symbols['sentencespanreference'],k('hzik'),k(row['first_sentence']),k(row['last_sentence']),k('hzim'))))
    for old,row in anchors['situation_nodes'].items():
        doc['declarations'].append(definition(n[old],[],'situation',
            call(voc._symbols[row['operation']],k(row['context']),num(row['address']))))
    for old,row in anchors['source_spans'].items():
        doc['declarations'].append(definition(n[old],[],'individual',
            call(voc._symbols['sentencetokenspanreference'],k('hzik'),k(row['sentence_reference']),num(row['first_token']),
                k(row['sentence_reference']),num(row['last_token']),k('hzim'))))
    for old,row in anchors['source_character_spans'].items():
        doc['declarations'].append(definition(n[old],[],'individual',
            call(voc._symbols['sentencetextspanreference'],k('hzik'),k(row['sentence_reference']),
                num(row['first_character']),num(row['past_last_character']),k('hzim'))))
    for old,row in anchors.get('referents',{}).items():
        doc['declarations'].append(definition(n[old],[],'individual',
            call(voc._symbols['discoursereferent'],k('hzik'),k(row['span']),num(row['ordinal']),k('hzim'))))
    existing={d['name']:d for d in doc['declarations']}
    prior={d['name'] for d in previous.source_excerpt()['declarations']}
    for d in source_excerpt()['declarations']:
        if d['name'] in PUBLIC:
            actual=existing[m[d['name']]]
            require(actual['kind']=='primitive' and actual['parameters']==d['parameters'] and actual['result']==d['result'],
                'Public relation signature changed: '+d['name'])
        elif d['name'] in SHARED:
            require(renamed(d,m)==existing[m[d['name']]],'Shared definition changed: '+d['name'])
        elif d['kind']=='definition' and d['name'] not in prior:doc['declarations'].append(renamed(d,m))
    doc['statements']+=renamed(source_excerpt()['statements'][-1:],m)
    return normalize_document(doc)


def backprojection(actual):
    require(previous.backprojection(actual)==previous.source_excerpt(),'Inherited source or description wrapper differs')
    ds={d['name']:d for d in actual['declarations']};inverse={value:key for key,value in mapping().items()}
    source=deepcopy(source_excerpt())
    source['declarations']=[renamed(ds[mapping()[d['name']]],inverse) if d['kind']=='definition' else d for d in source['declarations']]
    source['statements']=renamed([actual['statements'][i] for i in VISIBLE_ORDER],inverse)
    return normalize_document(source)


def specialized_source():
    source=deepcopy(source_excerpt())
    general=next(d for d in specialization.library()['declarations'] if d['name']=='stateconveniencecandidate')
    source['declarations']=[general]+[specialization.case_specialization() if d['name']=='uj' else d for d in source['declarations']]
    return normalize_document(source)


def specialized_backprojection(actual):
    source=backprojection(actual);ds={d['name']:d for d in actual['declarations']}
    inverse={value:key for key,value in mapping().items()}
    general=vocabulary()._symbols['stateconveniencecandidate'];inverse[general]='stateconveniencecandidate'
    source['declarations']=[renamed(ds[general],inverse)]+[
        renamed(ds[mapping()['uj']],inverse) if d['name']=='uj' else d for d in source['declarations']]
    return normalize_document(source)


def review_bindings():
    state=read('data/work-state.json');active=read(state['review_index'])['works']['kant-1784']
    rows=[r for r in active['reviews'] if read(r['review'])['unit']=='kant-1784:u0012']
    require(len(rows)==1 and {76}<=set(rows[0]['statements']),'OfficeObedience review selection changed')
    record=read(rows[0]['review'])
    require(record['decision']=='equivalent_under_stated_reading' and not record['unresolved'],'Incomplete source review')
    return previous.review_bindings()+[dict(unit='kant-1784:u0012',review=rows[0]['review'],source_statement=i) for i in (76,)]


def bridge():
    require(backprojection(document())==source_excerpt(),'Recovered source bodies or assertions differ')
    require(specialized_backprojection(document())==specialized_source(),'Inherited state-candidate specialization differs')
    anchors=read(ANCHORS)
    require(anchors['source_nodes']=={'h242c':[5,14]} and anchors['inherited_references']['h237w']==[5,13] and anchors['source_character_spans']=={} and anchors['text'].startswith('Hier ist'),'Source anchor changed')
    return dict(schema='noema-kant-office-obedience-visible-bridge-1',source_document=catalog().document_path,
        source_statement_indices=SOURCE_ORDER,visible_statement_indices=VISIBLE_ORDER,
        source_statements=source_excerpt()['statements'],source_declarations=source_excerpt()['declarations'],mapping=mapping(),
        parent_bridge=previous.BRIDGE,profile_edition=120,core_edition=12,public_relations=PUBLIC,shared_definitions=SHARED,
        source_specializations=specialization.SPECIALIZATIONS,review_bindings=review_bindings(),text_anchors=ANCHORS,
        sentence_blocks=anchors['sentence_blocks'],local_references=anchors.get('referents',{}),source_contexts=anchors['context_nodes'],situation_references=anchors['situation_nodes'],reused_contexts=anchors['reused_contexts'],inherited_sentence_reference=dict(hzp4=[4,1],hzp5=[4,2],thirdsentencereference=[4,3],h226h=[4,4],h227w=[4,5],h232h=[5,1],h232w=[5,2]),
        source_assertions=59,orthographic_annotations=1,formal_integration_credit=0,
        original_manuscript_modified=False,semantic_equivalence_automatically_proved=False)


@lru_cache(maxsize=1)
def restored():
    result=decode_files(sorted(OUT.glob('page-*.svg')),vocabulary(),workers=8)
    require(result['document']==document(),'Visible office_obedience sentence document differs')
    return result


def prepare_native():
    profile.write_once(SOURCE,format_graph(document())+'\n');profile.write_once(BRIDGE,bridge())


def source_pins(*,include_outputs=True):
    paths=set(previous.source_pins())|set(read('reports/office-obedience-visible-profile-v1.json')['source_sha256'])|set(catalog().source_sha256)|{
        SOURCE,BRIDGE,ANCHORS,previous.SOURCE,previous.BRIDGE,
        'scripts/check_kant_office_obedience_visible.py','tests/test_kant_office_obedience_visible.py'}
    paths.update(row['review'] for row in review_bindings());paths.update(read(ANCHORS)['source_sha256'])
    if not include_outputs:paths.difference_update((SOURCE,BRIDGE))
    return {p:digest(p) for p in sorted(paths)}


def build_report():
    result=restored();require(read(BRIDGE)==bridge(),'Saved office_obedience bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved office_obedience Native differs')
    require(backprojection(result['document'])==source_excerpt(),'Recovered office_obedience source differs')
    require(specialized_backprojection(result['document'])==specialized_source(),'Recovered specialized source differs')
    return dict(schema='noema-kant-office-obedience-visible-evidence-1',profile_edition=120,profile_words=1716,core_words=375,
        declarations=len(document()['declarations']),statements=60,source_assertions=59,annotations=1,
        pages=result['pages'],volumes=result['volumes'],source_sha256=source_pins(),
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        independent_human_reading=False,full_manuscript_visible_decoding=False,semantic_equivalence_automatically_proved=False)
