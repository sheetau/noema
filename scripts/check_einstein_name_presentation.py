"""Close the selected Einstein author display and visibly preserve its name form."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.identifiers import load_annotations
from scripts import name_presentation_profile as profile
from scripts.name_presentation_profile import ROOT,NamePresentationVocabulary,NamePresentation,write_once,text_expression,scalar_text
from scripts.check_manuscript_context import catalogs,slice_for
from scripts.shared_modality import call,renamed,op
from scripts.shared_reference import definition
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/einstein-name-presentation-v1.noema'
BRIDGE='data/einstein-name-presentation-bridge-v1.json'
UNITS='artifacts/written-units-v1/einstein-1905.json'
OUT=ROOT/'output/einstein-name-presentation-v1'
LABEL=Word('proper',('book','give','aki','book','red'))
PREDICATES=dict(eira='presentationholds',eirb='nameapplies',eirc='authordisplay')
FIELDS=dict(eire='use',eird='designation',rd='target',eirf='document')
FORMS={
 'eirg':Word('compound',('book','give','aki','home','book')),
 'packet':Word('compound',('book','give','aki','book','inside')),
 'eire':Word('proper',('book','give','aki','give')),
 'eird':Word('proper',('book','give','aki','book')),
 'rd':Word('proper',('book','give','aki','aki')),
 'eirf':Word('proper',('book','give','aki','home')),
 'eiaa':Word('compound',('book','aki','give','book')),
 'eiab':Word('compound',('book','aki','give','inside','home'))}


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def num(value):return dict(kind='number',numerator=value,denominator=1)


@lru_cache(maxsize=1)
def vocabulary():return NamePresentationVocabulary()


def names():
    forms=FORMS|{n:Word('compound',tuple(parts)) for n,parts in profile.HELPER_FORMS.items()}
    result={n:symbol(w,vocabulary()) for n,w in forms.items()}
    require(len(set(result.values()))==len(result) and not set(result.values())&set(vocabulary()._by_symbol),'Local name collision')
    return result


@lru_cache(maxsize=1)
def annotation():
    state=read('data/work-state.json');spec=read(state['review_index'])['works']['einstein-1905']
    annotations=load_annotations(ROOT,spec['meaning_basis'],spec['identifier_annotations'])
    row=next(r for r in annotations.annotations['entries'] if r['symbol']=='eird')
    require(row==dict(symbol='eird',role='designation',forms=[dict(text='A. Einstein',language='de',role='printed_identifying_form')]),
            'Selected printed identifying form changed')
    return dict(path=spec['identifier_annotations'],entry=row,source_sha256=annotations.show()['source_sha256'])


@lru_cache(maxsize=1)
def source_excerpt():
    doc=slice_for('einstein-1905');doc['statements']=[deepcopy(catalogs()['einstein-1905'].document['statements'][42])]
    return normalize_document(doc)


@lru_cache(maxsize=1)
def document():
    n=names();v=vocabulary();doc=dict(schema_version='0.16',lexicon_version='0.16',
        declarations=v.imports({'textpresentation',*profile.PARAMETERS}),statements=[])
    doc=v.decode_names(doc)
    doc['declarations']+=renamed(profile.accessors()['declarations'],n)
    doc['declarations'].append(definition(n['eirg'],[],'situation',call('textpresentation')))
    doc['declarations'].append(definition(n['packet'],[],profile.RECORD,call('presentationrecord',call(n['eirg']),num(2))))
    for old,field in FIELDS.items():
        doc['declarations'].append(definition(n[old],[],'individual',call(n['display'+field],call(n['packet']))))
    mapping=n|PREDICATES
    doc['declarations']+=renamed([d for d in source_excerpt()['declarations'] if d['kind']=='definition'],mapping)
    doc['statements']=renamed(source_excerpt()['statements'],mapping)
    form=annotation()['entry']['forms'][0]
    doc['statements'].append(dict(kind='assert',body=call('printedform',call(n['eird']),
        text_expression(form['language']),text_expression(form['text']),call(n['eirg']))))
    return v.encode(normalize_document(doc))


def visible_form(doc):
    decoded=vocabulary().decode_names(doc);statement=decoded['statements'][1]
    require(statement['kind']=='assert' and statement['body']['kind']=='call' and statement['body']['symbol']=='printedform',
            'Missing visible identifying-form assertion')
    args=statement['body']['arguments']
    require(len(args)==4 and all(args[i]['kind']=='call' and not args[i]['arguments'] for i in (0,3)),
            'Identifying form has an unsupported reference expression')
    def text(expr):
        require(expr['kind']=='sequence' and expr['element']=='number','Identifier is not a visible scalar sequence')
        require(all(x['kind']=='number' for x in expr['items']),'Identifier scalar expression is not literal')
        from fractions import Fraction
        return scalar_text([Fraction(x['numerator'],x['denominator']) for x in expr['items']])
    return dict(designation=args[0]['symbol'],language=text(args[1]),text=text(args[2]),context=args[3]['symbol'])


def backprojection(migrated):
    require(migrated==document(),'Changed migration cannot be rebound to old evidence')
    decoded=vocabulary().decode_names(migrated);by_name={d['name']:d for d in decoded['declarations']}
    inverse={v:k for k,v in names().items()}|{v:k for k,v in PREDICATES.items()};result=deepcopy(source_excerpt())
    result['declarations']=[renamed(by_name[PREDICATES[d['name']]],inverse) if d['name'] in PREDICATES else
        renamed(by_name[names()[d['name']]],inverse) if d['kind']=='definition' else deepcopy(d)
        for d in result['declarations']]
    result['statements']=[renamed(decoded['statements'][0],inverse)]
    return normalize_document(result)


def bridge():
    c=catalogs()['einstein-1905'];units=[u for u in read(UNITS)['units'] if u['kind']=='frontmatter'];unit=units[1]
    form=annotation()['entry']['forms'][0]
    require(unit['id']=='einstein-1905:u0002' and unit['text']=='von '+form['text']+'.','Frontmatter position or identifying form differs')
    for old,new in PREDICATES.items():
        require(c.entries[old]['meaning_ja']==profile.MEANINGS[new],'Public source relation meaning differs')
    require(backprojection(document())==source_excerpt(),'Recorded context bindings do not recover original source')
    return dict(schema='noema-einstein-visible-name-presentation-bridge-1',reviewer='assistant',document=c.document_path,
        source_statement_index=42,source_assertion=source_excerpt()['statements'][0],source_declarations=source_excerpt()['declarations'],
        profile=profile.MANIFEST,profile_edition=18,core_edition=12,frontmatter_item=2,source_unit=unit['id'],
        source_unit_sha256=unit['text_sha256'],reference_fields=profile.FIELDS,local_names=names(),
        context_binding=dict(source_symbol='eirg',target='textpresentation',
            interpretation='同じ1905年論説の前付の著者表示を読む提示文脈を指定する。本文の物理的設定や推論範囲ではない。'),
        bindings=[dict(source_symbol=n,source_meaning=c.entries[n]['meaning_ja'],meaning_basis=c.entries[n]['meaning_basis'])
                  for n in ['eirg',*FIELDS,*PREDICATES,'eiaa','eiab']],
        identifier_annotation=annotation()['entry'],identifier_annotation_path=annotation()['path'],
        visible_identifier_form=visible_form(document()),
        preservation='The original three relations, two definition bodies and assertion retain their types and content under injective naming. Five contextual constants are explicitly bound to the presentation and its four reference fields.',
        closed_source_assertions=1,orthographic_annotation_assertions=1,original_manuscript_modified=False,
        old_judgments_rebound=False,referent_identity_inferred_from_spelling=False,authenticity_inferred=False)


def model_for(values=('x','x','y','y'),context='now',mask=7,*,strict=False,form=True):
    base=('x','x','y','y');use,name,target,doc=base
    presented={(u,s):bool(mask&1) and (not strict or (u,s)==(use,'now')) for u,s in product(('x','y'),('now','other'))}
    applied={(u,n,t,s):bool(mask&2) and (not strict or (u,n,t,s)==(use,name,target,'now'))
             for u,n,t,s in product(('x','y'),('x','y'),('x','y'),('now','other'))}
    authors={(u,d,t,s):bool(mask&4) and (not strict or (u,d,t,s)==(use,doc,target,'now'))
             for u,d,t,s in product(('x','y'),('x','y'),('x','y'),('now','other'))}
    forms={(n,'de','A. Einstein',s):form for n,s in product(('x','y'),('now','other'))}
    return NamePresentation(context,{(s,2):values for s in ('now','other')},presented=presented,applied=applied,authors=authors,forms=forms)


def interpret(doc,model):
    handlers={vocabulary()._symbols[n]:f for n,f in model.handlers().items()}
    return evaluate_document(doc,individuals=('x','y'),situations=('now','other'),primitives=handlers)


def original_value(model):
    use,name,target,doc=model.records[(model.anchor,2)];values=dict(eire=use,eird=name,rd=target,eirf=doc,eirg=model.anchor)
    handlers={n:lambda value=value:value for n,value in values.items()}
    handlers.update({old:model.handlers()[new] for old,new in PREDICATES.items()})
    return evaluate_document(source_excerpt(),individuals=('x','y'),situations=('now','other'),primitives=handlers)


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible name presentation differs');return result


def diagnostics():
    cases=[]
    for same,mask in product((False,True),range(8)):
        values=('x','y' if same else 'x','y','y')
        cases.append((f'same-name-person={same}/mask={mask}',model_for(values,mask=mask),not same and mask==7,True))
    for i,field in enumerate(profile.FIELDS):
        values=list(('x','x','y','y'));values[i]='y' if values[i]=='x' else 'x'
        cases.append(('changed-'+field,model_for(tuple(values),strict=True),False,True))
    cases.append(('changed-presentation-context',model_for(context='other',strict=True),False,True))
    cases.append(('form-independent-from-author-display',model_for(form=False),True,False))
    rows=[]
    for label,model,wanted,form in cases:
        old=original_value(model);new=interpret(restored()['document'],model)
        require(old[0]==new[0] and [r['value'] for r in new]==[wanted,form],'Presentation binding differs: '+label)
        rows.append(dict(case=label,source=old,visible=new,expected_source=wanted,expected_form=form))
    return rows


def accessor_diagnostics():
    rows=[];doc=profile.accessors();tuples=[('x',)*4]+[tuple('y' if i==j else 'x' for i in range(4)) for j in range(4)]
    for values in tuples:
        for index,field in enumerate(profile.FIELDS):
            current=deepcopy(doc);handlers={};args=[]
            for i,value in enumerate(values):
                label='argument'+chr(97+i);current['declarations'].append(dict(kind='primitive',name=label,parameters=[],result='individual'))
                handlers[label]=lambda value=value:value;args.append(call(label))
            body=op('equal',call('display'+field,call('makepresentation',*args)),args[index])
            current['statements']=[dict(kind='ask',body=body)]
            answer=evaluate_document(current,individuals=('x','y'),situations=('now',),primitives=handlers)[0]['value']
            require(answer is True,'Native record selector changed position')
            rows.append(dict(values=list(values),field=field,answer=answer))
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(read(BRIDGE)==bridge(),'Name presentation bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    require(parse((ROOT/profile.ACCESSORS).read_text(encoding='utf-8'))==profile.accessors(),'Accessor library differs')
    previous='reports/kant-text-reference-v1.json';prior=read(previous);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,previous,UNITS,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,profile.ACCESSORS,
        'scripts/name_presentation_profile.py','scripts/check_einstein_name_presentation.py','scripts/visible_name_presentation_collection.py',
        'tests/test_name_presentation_profile.py','docs/einstein-name-presentation-v1.md',*annotation()['source_sha256']}
    return dict(schema='noema-einstein-name-presentation-evidence-1',core_words=375,optional_profile_words=8,profile_words=383,
        profile_edition=18,new_reference_primitives=1,new_orthographic_primitive=1,preserved_source_relations=3,
        closed_source_assertions=1,orthographic_annotation_assertions=1,source_statement_index=42,
        local_definitions=13,declarations=19,statements=2,pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        visible_identifier_form=visible_form(result['document']),contextual_diagnostics=diagnostics(),native_selector_diagnostics=accessor_diagnostics(),
        independent_human_reading=False,full_manuscript_visible_decoding=False,
        source_sha256={p:digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        limits=profile.LIMITS+['Binding diagnostics use small distinguishing domains; they are not exhaustive proofs over all relation interpretations.',
                             'This author display is connected under its stated context. No inference from spelling to person or authenticity is added.'])
