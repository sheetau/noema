"""Close a real Kant ordering assertion using explicit paragraph/sentence references."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import text_reference_profile as profile
from scripts.text_reference_profile import ROOT,TextReferenceVocabulary,TextPresentation,write_once
from scripts.check_manuscript_context import catalogs,slice_for
from scripts.shared_modality import call,renamed,op
from scripts.shared_reference import definition
from scripts.shared_focus import quote
from scripts.visible_word_forms import Word,symbol
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require

SOURCE='examples/v016/kant-text-reference-v1.noema'
BRIDGE='data/kant-text-reference-bridge-v1.json'
OUT=ROOT/'output/kant-text-reference-v1'
LABEL=Word('proper',('book','inside','above','aki'))
UNITS='artifacts/written-units-v1/kant-1784.json'
READINGS=['data/nature-sentence-reading-v1.json','data/affection-sentence-reading-v1.json']
FORMS={'wh':Word('compound',('book','inside','above','home','book')),
       'hzzq':Word('proper',('book','above','aki')),
       'hzzr':Word('proper',('book','above','nao')),
       'r2em':Word('compound',('book','above','inside','book','home'))}


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def num(value):return dict(kind='number',numerator=value,denominator=1)


@lru_cache(maxsize=1)
def vocabulary():return TextReferenceVocabulary()


def names():
    v=vocabulary();result={n:symbol(word,v) for n,word in FORMS.items()}
    require(len(set(result.values()))==len(result) and not set(result.values())&set(v._by_symbol),'Local name collision')
    return result


@lru_cache(maxsize=1)
def source_excerpt():
    doc=slice_for('kant-1784');doc['statements']=[deepcopy(catalogs()['kant-1784'].document['statements'][12])]
    return normalize_document(doc)


@lru_cache(maxsize=1)
def document():
    n=names();doc=profile.library();doc=deepcopy(doc)
    doc['declarations'].append(definition(n['wh'],[],'situation',call('textpresentation')))
    for old,index in [('hzzq',1),('hzzr',2)]:
        doc['declarations'].append(definition(n[old],[],'individual',call('sentencereference',call(n['wh']),num(3),num(index))))
    original=next(d for d in source_excerpt()['declarations'] if d['name']=='r2em')
    mapping=n|{'ue':'textbefore'}
    doc['declarations'].append(renamed(original,mapping))
    doc['statements']=renamed(source_excerpt()['statements'],mapping)
    return vocabulary().encode(normalize_document(doc))


def backprojection(migrated):
    # Require the actual three reference definitions. Never replace an arbitrary
    # changed definition by the old primitive just to recover a matching hash.
    require(migrated==document(),'Changed migration cannot be rebound to old evidence')
    decoded=vocabulary().decode_names(migrated);by_name={d['name']:d for d in decoded['declarations']}
    inverse={v:k for k,v in names().items()}|{'textbefore':'ue'};result=deepcopy(source_excerpt())
    result['declarations']=[renamed(by_name['textbefore'],inverse) if d['name']=='ue' else
        renamed(by_name[names()['r2em']],inverse) if d['name']=='r2em' else deepcopy(d)
        for d in result['declarations']]
    result['statements']=renamed(decoded['statements'],inverse)
    return normalize_document(result)


def bridge():
    c=catalogs()['kant-1784'];units=read(UNITS)['units'];body=[u for u in units if u['kind']=='body']
    unit=body[2];require(unit['id']=='kant-1784:u0010','Third body paragraph changed')
    spans=[]
    for i,path in enumerate(READINGS):
        r=read(path)['source'];require(r['unit']==unit['id'] and r['unit_sha256']==unit['text_sha256'],'Source boundary evidence changed')
        start,end=r['range'];require(unit['text'][start:end]==r['text'],'Sentence boundary text differs')
        spans.append(dict(paragraph=3,sentence=i+1,unit=unit['id'],range=[start,end],
            text_sha256=hashlib.sha256(r['text'].encode('utf-8')).hexdigest(),source_symbol=['hzzq','hzzr'][i],reading=path))
    require(spans[0]['range']==[0,125] and spans[1]['range']==[126,292] and unit['text'][125:126]==' ',
            'Adopted adjacent sentence boundary differs')
    require(c.entries['ue']['meaning_ja']==profile.MEANINGS['textbefore'],'Public text-order meaning differs from source')
    require(backprojection(document())==source_excerpt(),'Source payload cannot be recovered under recorded reference bindings')
    return dict(schema='noema-kant-visible-reference-bridge-1',reviewer='assistant',document=c.document_path,
        source_statement_index=12,source_assertion=source_excerpt()['statements'][0],source_declarations=source_excerpt()['declarations'],
        profile=profile.MANIFEST,core_edition=12,profile_edition=17,local_names=names(),sentence_locations=spans,
        context_binding=dict(source_symbol='wh',source_meaning=c.entries['wh']['meaning_ja'],
            target='textpresentation',interpretation='この抜粋で扱うカント第三段落の提示文脈を基準とする。同じ文脈の本文段落番号で二つの文を指定する。'),
        bindings=[dict(source_symbol=n,source_meaning=c.entries[n]['meaning_ja'],meaning_basis=c.entries[n]['meaning_basis'])
                  for n in ['ue','wh','hzzq','hzzr','r2em']],
        preservation='The old relation and assertion are unchanged up to injective naming; the three old contextual constants are defined through the explicit anchor and verified sentence coordinates.',
        original_manuscript_modified=False,old_judgments_rebound=False,full_sentence_contents_migrated=False,
        closed_source_assertions=1,semantic_boundary='The assertion concerns textual order only. The contents of the two referred sentences remain in the preserved manuscript and are not encoded by their coordinates.')


@lru_cache(maxsize=1)
def compiled():return compile_collection(document(),LABEL,vocabulary(),payload=768)


@lru_cache(maxsize=1)
def restored():
    result=decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))],vocabulary())
    require(result['document']==document(),'Visible reference document differs');return result


def interpret(doc,model):
    v=vocabulary();handlers={v._symbols[n]:f for n,f in model.handlers().items()}
    return evaluate_document(doc,individuals=('x','y'),situations=('now','other'),primitives=handlers)


def diagnostics():
    rows=[]
    for anchor in ('now','other'):
        for first,second in [('x','y'),('y','x')]:
            model=TextPresentation(anchor,{anchor:{(3,1):first,(3,2):second},
                ('other' if anchor=='now' else 'now'):{(3,1):second,(3,2):first}})
            old_handlers=dict(wh=lambda:anchor,hzzq=lambda:first,hzzr=lambda:second,ue=model.before)
            old=evaluate_document(source_excerpt(),individuals=('x','y'),situations=('now','other'),primitives=old_handlers)
            new=interpret(restored()['document'],model)
            require(old==new and old[0]['value'] is True,'Source contextual instance changed')
            doc=deepcopy(restored()['document']);n=names();before=vocabulary()._symbols['textbefore']
            doc['statements']=[dict(kind='ask',body=call(before,call(n['hzzr']),call(n['hzzq']),call(n['wh']))),
                dict(kind='ask',body=op('equal',quote(call(n['hzzq'])),quote(call(n['hzzr'])))),
                dict(kind='ask',body=op('equal',call(n['hzzq']),call(n['hzzr'])))]
            checks=interpret(doc,model);require([r['value'] for r in checks]==[False,False,False],'Direction or reference identity collapsed')
            require(model.before(first,second,'other' if anchor=='now' else 'now') is False,'Presentation scope ignored')
            rows.append(dict(anchor=anchor,first=first,second=second,source_and_visible=old,
                             reverse_and_quoted_identity=checks,other_context_order=False))
    return rows


def prepare():
    profile.prepare();write_once(SOURCE,format_graph(document())+'\n');write_once(BRIDGE,bridge())
    for i,page in enumerate(compiled()['pages']):write_once(OUT/('page-'+str(i+1).zfill(5)+'.svg'),to_svg(page['shapes']))


def build_report():
    result=restored();require(read(BRIDGE)==bridge(),'Reference bridge differs')
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8'))==document(),'Saved Native differs')
    previous='reports/manuscript-context-v1.json';prior=read(previous);pins=prior['source_sha256']|prior['artifact_sha256']
    for path,stamp in pins.items():require(digest(path)==stamp,'Prior evidence changed: '+path)
    paths={*pins,previous,UNITS,*READINGS,SOURCE,BRIDGE,profile.LIBRARY,profile.BASIS,profile.MANIFEST,
        'scripts/text_reference_profile.py','scripts/check_kant_text_reference.py','scripts/visible_text_reference_collection.py',
        'tests/test_text_reference_profile.py','docs/kant-text-reference-v1.md'}
    return dict(schema='noema-kant-text-reference-evidence-1',core_words=375,optional_profile_words=3,profile_words=378,
        profile_edition=17,new_reference_primitives=2,preserved_text_order_primitive=1,
        closed_source_assertions=1,source_statement_index=12,full_sentence_contents_migrated=False,
        local_definitions=4,declarations=7,statements=1,paragraph=3,sentences=[1,2],
        pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        contextual_models=diagnostics(),independent_human_reading=False,
        source_sha256={p:digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        limits=profile.LIMITS+['One closed ordering assertion has a checked contextual reading. The two sentence contents, other reference kinds and both complete manuscripts still need visible integration.'])
