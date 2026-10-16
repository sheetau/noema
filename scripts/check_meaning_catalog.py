"""Reproduce the current manuscripts' meaning-convention catalog audit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from noema.meaning_catalog import load_catalog
from noema.constructed_discourse import definition_audit as constructed_audit
from noema.discourse import definition_audit as legacy_audit

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/meaning-catalog-v1.json'
KANT='data/definition-question-basis-v1.json'
EINSTEIN='data/einstein-positive-axis-calibration-basis-v1.json'
LIBRARY='examples/v016/definition-question.noema'


def build():
    catalogs=[load_catalog(ROOT,KANT),load_catalog(ROOT,EINSTEIN),
        load_catalog(ROOT,KANT,document_path=LIBRARY)]
    summaries=[];hashes={}
    for catalog,old_audit in zip(catalogs,(constructed_audit,legacy_audit,constructed_audit)):
        result=catalog.audit();prior=old_audit(catalog.document)
        for key in ('definition_primitive_dependencies','statement_primitive_dependencies'):
            if result[key]!=prior[key]:raise ValueError('Dependency audits disagree: '+catalog.document_path+' / '+key)
        summaries.append({key:result[key] for key in ('document','basis','edition','primitive_count','definition_count',
            'statement_count','signature_and_documentation_coverage','projection')})
        # Full caveats remain available through the catalog and their pinned
        # basis files. Do not duplicate the large base conventions in a summary.
        summaries[-1]['lineage']=[dict({key:value for key,value in row.items() if key!='caveats'},
            caveat_fields=sorted(row['caveats'])) for row in result['lineage']]
        summaries[-1]['existing_dependency_audit_matches']=True
        for path,digest in result['source_sha256'].items():
            if path in hashes and hashes[path]!=digest:raise ValueError('Input changed: '+path)
            hashes[path]=digest
    title=catalogs[0].explain(['hzic'])
    primitives=[dict(symbol=row['symbol'],meaning_ja=row['meaning_ja'],meaning_basis=row['meaning_basis'])
        for row in title['entries'] if row['kind']=='primitive']
    paths={'scripts/check_meaning_catalog.py','tests/test_meaning_catalog.py','docs/meaning-catalog-v1.md',
        'noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    # Pin the local Python modules actually imported by this audit, including
    # the original parser and independent dependency visitor implementations.
    for name,module in tuple(sys.modules.items()):
        if name=='noema' or name.startswith('noema.'):
            file=getattr(module,'__file__',None)
            if file and Path(file).resolve().is_relative_to(ROOT):paths.add(Path(file).resolve().relative_to(ROOT).as_posix())
    for path in paths:hashes[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    for path,digest in hashes.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Input changed: '+path)
    return dict(status='meaning_convention_catalog_audited',documents=summaries,
        title_question=dict(symbol='hzic',retained_symbols=title['retained_symbols'],declaration_count=len(title['entries']),
            primitive_count=len(primitives),primitive_conventions=primitives),
        semantic_equivalence_to_source_proven=False,primitive_grounding_proven=False,
        new_source_coverage_claimed=False,source_sha256=dict(sorted(hashes.items())))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Create a new report; refuse to replace one')
    args=parser.parse_args();result=build()
    if args.write:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    elif result!=json.loads(REPORT.read_text(encoding='utf-8')):
        raise ValueError('Committed report differs from reproduced audit')
    print(json.dumps(dict(status=result['status'],documents=len(result['documents']),
        pinned_inputs=len(result['source_sha256']),title_declarations=result['title_question']['declaration_count'],
        title_primitives=result['title_question']['primitive_count']),ensure_ascii=False))


if __name__=='__main__':main()
