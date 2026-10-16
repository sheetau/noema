"""Check designation use, author-credit scope, annotations and source binding."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts.compose_author_signature import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build,closure

REPORT=ROOT/'reports/author-signature-v1.json'
REVIEW='data/author-signature-review-v1.json'
DOMAIN=('presenter','author','activity','name','document','other')
SCENES=('signature','opening')


def forbidden(*args):raise ValueError('Unspecified relation evaluated')


def fixture(path=LIBRARY):
    doc=parse((ROOT/path).read_text(encoding='utf-8'));doc['statements']=[]
    declarations='r jnap[] a.r jnaa[] a.r jnan[] a.r jnas[] a.r jnad[] a.r jnac[] d.'
    declarations+='r jno[a d] c.r jnp[a a d] c.r jna[a a a d] c.r jnc[a a a d] c.'
    return parse(format_graph(doc,'compact')+declarations+
        'q[k rqqw[k jnap[] k jnaa[] k jnan[] k jnas[] k jnad[] k jnac[] p jno p jnp p jna p jnc]].')


def model(doc,variant='baseline',bits=(True,True,True,True),source=False):
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    person='author' if source else 'presenter'
    def occurred(activity,scene):
        return bits[0] and (activity,scene)==('activity','signature')
    def presented(presenter,activity,scene):
        return bits[1] and (presenter,activity,scene)==(person,'other' if variant=='different_presenting_act' else 'activity','signature')
    def assigned(activity,name,subject,scene):
        if variant=='unknown_assignment':raise ValueError('Unknown designation assignment')
        return bits[2] and (activity,name,subject,scene)==('activity','other' if variant=='different_name' else 'name',
            'other' if variant=='different_named_person' else 'author','signature')
    def credited(activity,document,author,scene):
        if variant=='unknown_credit':raise ValueError('Unknown author display')
        return bits[3] and (activity,document,author,scene)==('other' if variant=='different_credit_act' else 'activity',
            'other' if variant=='different_document' else 'document','other' if variant=='different_credited_person' else 'author',
            'opening' if variant=='different_credit_context' else 'signature')
    if source:
        values.update(wa=lambda:'author',hzig=lambda:'activity',hzif=lambda:'author' if variant=='name_is_person' else 'name',
            hzik=lambda:'document',hzim=lambda:'signature',dg=occurred,f3=presented,hzih=assigned,hzij=credited)
    else:
        values.update(jnap=lambda:'presenter',jnaa=lambda:'activity',jnan=lambda:'name',jnas=lambda:'author',jnad=lambda:'document',jnac=lambda:'signature',
            jno=occurred,jnp=presented,jna=assigned,jnc=credited)
    return values


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=100000,memoize_definitions=False,memoize_expressions=False)]


def checks():
    doc=fixture();count=0
    for bits in product((False,True),repeat=4):
        assert evaluate(doc,model(doc,bits=bits))==[all(bits)];count+=1
    contrasts={};variants=('baseline','different_presenting_act','different_name','different_named_person','different_credit_act',
        'different_document','different_credited_person','different_credit_context')
    for path in (LIBRARY,FULL):
        doc=fixture(path);contrasts[path]={}
        for variant in variants:
            actual=evaluate(doc,model(doc,variant));assert actual==[variant=='baseline'],(path,variant,actual)
            contrasts[path][variant]=actual
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'));doc['statements']=doc['statements'][-1:];source={}
    for variant in variants+('name_is_person',):
        actual=evaluate(doc,model(doc,variant,source=True));assert actual==[variant=='baseline'],(variant,actual)
        source[variant]=actual
    # Distinguish the name object even when a model falsely makes the same
    # individual fill both positions and supplies an assignment to itself.
    values=model(doc,'name_is_person',source=True);values['hzih']=lambda a,n,p,s:(a,n,p,s)==('activity','author','author','signature')
    assert evaluate(doc,values)==[False]
    for variant in ('unknown_assignment','unknown_credit'):
        try:evaluate(doc,model(doc,variant,source=True))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    return dict(condition_combinations=count,generic_contrasts=contrasts,source_contrasts=source,
        presenter_may_differ_from_credited_author=True,unknown_assignment_and_credit_refused=True,
        original_paragraph_context_not_used=True,unlowered_uncached=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    size=len(old.document['declarations']);added=new.document['declarations'][size:]
    assert new.document['declarations'][:size]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==17
    assert {d['name'] for d in added if d['kind']=='primitive'}==set(PRIMITIVES)
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(new.document,['rqqw'])
    names=load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert names.find('Immanuel Kant')['matches'][0]['symbol']=='hzif'
    assert all(r['symbol']!='wa' for r in names.show()['entries'])
    return dict(parent_declarations_preserved=True,previous_statement_syntax_preserved=16,new_statements=1,
        new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),annotations_belong_to_name_not_person=True,
        library_declarations=len(lib.entries))


def alignment():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0018')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],source=unit['text'],
        status='partial_author_signature_and_identifier_forms',definitions=['rnh','rqqw','hzil'],
        remaining=['facsimile check of original spelling and typography','unit-level semantic completion review'])])


def build_report():
    files=build()
    for path,body in files.items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    finite=checks();structural=structure()
    for path in (FULL,LIBRARY):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    review=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'));row=alignment()['segments'][0]
    assert review['unit']==row['unit'] and review['source']==row['source'] and review['unit_sha256']==row['unit_sha256']
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|{
        REVIEW,'docs/author-signature-v1.md','tests/test_identifiers.py','tests/test_author_signature.py',
        'scripts/compose_author_signature.py','scripts/check_author_signature.py','scripts/compose_subject_bound_departure.py',
        'artifacts/written-units-v1/kant-1784.json','artifacts/written-sources-v1/kant-1784.html','reports/written-sources-v1.json',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path:paths.add(Path(path).resolve().relative_to(ROOT).as_posix())
    parent_size=len(load_catalog(ROOT,PARENT_BASIS).document['declarations'])
    current_size=len(load_catalog(ROOT,BASIS).document['declarations'])
    lines=files[FULL].splitlines()
    size_accounting=dict(manuscript_characters=len(files[FULL]),library_characters=len(files[LIBRARY]),
        signature_statement_characters=len(lines[-1]),new_declaration_characters=sum(len(line) for line in lines[1+parent_size:1+current_size]),
        identifier_form_characters=sum(len(form['text']) for entry in json.loads(files[ANNOTATIONS])['entries'] for form in entry['forms']),
        annotation_file_bytes=len(files[ANNOTATIONS].encode('utf-8')),
        note='Statement length excludes shared declarations and identifier forms; it is not a compression ratio for the source unit.')
    return dict(status='partial_author_signature_connected_to_existing_author',document=FULL,finite=finite,structure=structural,
        alignment=alignment(),source_review=REVIEW,identifier_annotations=ANNOTATIONS,roundtrips=True,cli_parse=True,
        size_accounting=size_accounting,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Signature naming, author-credit scope, identifier forms and source association checked')


if __name__=='__main__':main()
