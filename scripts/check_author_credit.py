"""Check author credit without inventing the person who presented the name."""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

from noema.constructed import parse,format_graph
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts.check_author_signature import model,evaluate,forbidden
from scripts.compose_author_credit import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,build,closure

REPORT=ROOT/'reports/author-credit-v1.json'
FACSIMILE='data/author-signature-facsimile-v1.json'


def fixture(path=LIBRARY):
    doc=parse((ROOT/path).read_text(encoding='utf-8'));doc['statements']=[]
    return parse(format_graph(doc,'compact')+
        'r jnaa[] a.r jnan[] a.r jnas[] a.r jnad[] a.r jnac[] d.'+
        'r jno[a d] c.r jna[a a a d] c.r jnc[a a a d] c.'+
        'q[k rqqx[k jnaa[] k jnan[] k jnas[] k jnad[] k jnac[] p jno p jna p jnc]].')


def checks():
    combinations=0
    for bits in product((False,True),repeat=3):
        doc=fixture();values=model(doc,bits=(bits[0],False,bits[1],bits[2]))
        values.pop('jnp',None);values.pop('jnap',None)
        assert evaluate(doc,values)==[all(bits)];combinations+=1
    variants=('baseline','different_name','different_named_person','different_credit_act',
        'different_document','different_credited_person','different_credit_context')
    generic={}
    for path in (LIBRARY,FULL):
        doc=fixture(path);generic[path]={}
        for variant in variants:
            values=model(doc,variant);values.pop('jnp',None);values.pop('jnap',None)
            actual=evaluate(doc,values);assert actual==[variant=='baseline'],(path,variant,actual)
            generic[path][variant]=actual
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'));doc['statements']=doc['statements'][-1:]
    source={}
    for variant in variants+('name_is_person',):
        values=model(doc,variant,source=True);values['f3']=forbidden
        actual=evaluate(doc,values);assert actual==[variant=='baseline'],(variant,actual)
        source[variant]=actual
    values=model(doc,'name_is_person',source=True)
    values['hzih']=lambda a,n,p,s:(a,n,p,s)==('activity','author','author','signature')
    assert evaluate(doc,values)==[False]
    for variant in ('unknown_assignment','unknown_credit'):
        values=model(doc,variant,source=True);values['f3']=forbidden
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));old['statements']=old['statements'][-1:]
    old_values=model(old,bits=(True,False,True,True),source=True)
    new_values=model(doc,bits=(True,False,True,True),source=True)
    assert evaluate(old,old_values)==[False] and evaluate(doc,new_values)==[True]
    return dict(condition_combinations=combinations,generic_contrasts=generic,source_contrasts=source,
        old_requires_author_as_presenter=True,new_does_not_evaluate_presenter=True,
        unknown_assignment_and_credit_refused=True,unlowered_uncached=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    before={d['name']:d for d in old.document['declarations']}
    after={d['name']:d for d in new.document['declarations']}
    assert set(after)-set(before)=={'rqqx'} and not set(before)-set(after)
    assert [n for n in before if before[n]!=after[n]]==['hzil']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==17
    assert [d['name'] for d in new.document['declarations'] if d['name']!='rqqx']==list(before)
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(new.document,['rqqx']) and len(lib.entries)==1
    names=load_annotations(ROOT,BASIS,ANNOTATIONS)
    for spelling in ('I.[mmanuel] Kant.','Immanuel Kant','I. Kant.'):
        assert names.find(spelling)['matches'][0]['symbol']=='hzif'
    return dict(changed_definition='hzil',new_definitions=1,new_primitives=0,previous_statements_preserved=17,
        identifier_forms_on_name_object=True,library_declarations=1)


def source_check():
    record=json.loads((ROOT/FACSIMILE).read_text(encoding='utf-8'))
    for name,expected in record['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    manifest=json.loads((ROOT/record['manifest']['path']).read_text(encoding='utf-8'))
    canvas=manifest['sequences'][0]['canvases'][record['canvas']['index']]
    assert canvas['@id']==record['canvas']['id'] and canvas['label']==record['canvas']['label']
    resource=canvas['images'][0]['resource']
    assert resource['@id']==record['image']['url']
    assert [resource['width'],resource['height']]==record['image']['dimensions']
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==record['unit'])
    assert unit['text']==record['electronic_transcription'] and unit['text_sha256']==record['unit_sha256']
    return record,unit


def build_report():
    files=build()
    for path,body in files.items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    finite=checks();structural=structure();record,unit=source_check()
    for path in (FULL,LIBRARY):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(record['source_sha256'])|{
        FACSIMILE,PARENT,PARENT_BASIS,'docs/author-credit-v1.md','tests/test_author_credit.py',
        'scripts/compose_author_credit.py','scripts/check_author_credit.py','scripts/check_author_signature.py',
        'scripts/compose_author_signature.py','scripts/compose_subject_bound_departure.py',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path:paths.add(Path(path).resolve().relative_to(ROOT).as_posix())
    return dict(status='author_credit_without_presenter_inference_checked',document=FULL,finite=finite,structure=structural,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],
            source=unit['text'],status='partial_author_credit_formal_checks',definitions=['rqqx','hzil'],
            remaining=['Whole-unit judgment is recorded separately; finite checks alone do not establish equivalence.'])]),
        facsimile_record=FACSIMILE,identifier_annotations=ANNOTATIONS,roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),library_characters=len(files[LIBRARY]),
            source_statement_characters=len(files[FULL].splitlines()[-1]),
            identifier_form_characters=sum(len(f['text']) for e in json.loads(files[ANNOTATIONS])['entries'] for f in e['forms']),
            annotation_file_bytes=len(files[ANNOTATIONS].encode('utf-8')),
            note='Shared declarations and orthographic annotations are not free; the short statement is not a compression ratio.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Author credit checked without an inferred presenter; semantic judgment remains separate')


if __name__=='__main__':main()
