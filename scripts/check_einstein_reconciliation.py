"""Check namespace-safe recovery, current assertions and numerical witnesses."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import subprocess
import sys

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.linking import project_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.check_phi_normalization import number,call
from scripts.check_quantities import ARITHMETIC
from scripts.compose_einstein_reconciliation import ROOT,CURRENT,SOURCE,BASIS,MANIFEST,DONORS,assembly,build,document,load

REPORT=ROOT/'reports/einstein-reconciliation-v1.json'


def forbidden(*args):raise AssertionError('Unrelated interpretation executed')


@lru_cache(None)
def numeric_fixture():
    linked,inputs,*_=assembly()
    sample=deepcopy(linked.document);sample['statements']=[]
    mapping=linked.symbols['paths']
    bodies=[]
    for speed,light,rate in ((3,5,Fraction(4,5)),(-3,5,Fraction(4,5)),(3,5,Fraction(3,4)),(5,5,0)):
        bodies.append(call(mapping['ha'],*[number(n) for n in (speed,light,rate)]))
    # Same spelling and identical numerical signature do not identify local
    # descriptions from independent source documents.
    bodies.append('e[r[p '+mapping['aa']+']][r[p '+linked.symbols['worldlines']['aa']+']]')
    sample=parse(format_graph(sample,'compact')+''.join('q['+b+'].' for b in bodies))
    local=deepcopy(inputs['paths']);local['statements']=[]
    local=parse(format_graph(local,'compact')+''.join('q['+call('ha',*[number(n) for n in triple])+'].' for triple in (
        (3,5,Fraction(4,5)),(-3,5,Fraction(4,5)),(3,5,Fraction(3,4)),(5,5,0))))
    return sample,local


def numeric_checks():
    linked,*_=assembly();sample,local=numeric_fixture()
    model={d['name']:forbidden for d in sample['declarations'] if d['kind']=='primitive'}
    for name,fn in ARITHMETIC.items():
        if name in linked.symbols['paths']:model[linked.symbols['paths'][name]]=fn
    actual=[r['value'] for r in evaluate_document(sample,individuals=('object',),situations=('now',),primitives=model)]
    original_model={d['name']:ARITHMETIC.get(d['name'],forbidden) for d in local['declarations'] if d['kind']=='primitive'}
    expected=[r['value'] for r in evaluate_document(local,individuals=('object',),situations=('now',),primitives=original_model)]
    assert actual==expected+[False]==[True,True,False,False,False]
    return dict(clock_rate_examples=actual[:4],independent_arithmetic_descriptions_equal=actual[-1],
        original_and_linked_values_agree=True,unrelated_interpretations_executed=False)


def build_report():
    files=build()
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in files.items())
    doc=parse(files[SOURCE]);linked,inputs,pairs,checks,resolutions,used=assembly()
    assert doc==linked.document
    for label,original in inputs.items():assert project_document(linked,label,document=doc)==original
    for notation in ('full','compact'):
        text=format_graph(doc,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    command=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/SOURCE)],
        check=True,capture_output=True,text=True,encoding='utf-8')
    assert json.loads(command.stdout)==doc
    counts=audit_basis(doc,json.loads(files[BASIS]))
    manifest=json.loads(files[MANIFEST])
    assert len(resolutions)==143 and manifest['present_in_later_draft']==83
    assert manifest['imported_independent_candidates']==60
    assert doc['statements']==document(CURRENT)['statements']
    assert doc['statements'][-1]['body']['arguments'][-1]['body']['symbol']=='seoz'
    paths=used|set(files)|{
        'scripts/compose_einstein_reconciliation.py','scripts/check_einstein_reconciliation.py',
        'tests/test_einstein_reconciliation.py','docs/einstein-reconciliation-v1.md',
        'noema/linking.py','noema/extraction.py','noema/closed_document.py','noema/meaning_basis.py',
        'noema/language.py','noema/discourse.py','noema/finite_semantics.py','noema/grammar.py',
        'scripts/check_quantities.py','scripts/check_phi_normalization.py'}
    return dict(status=manifest['status'],document=SOURCE,characters=len(files[SOURCE]),
        declarations=len(doc['declarations']),primitive_count=counts['primitive_count'],definition_count=counts['definition_count'],
        source_projections=list(inputs),provenance_comparisons=len(checks),resolutions=manifest['resolutions'],
        prior_missing_symbols=143,present_in_later_draft=83,independent_library_candidates=60,
        current_statements_preserved=175,imported_author_assertions=0,
        revised_density_interpretation_preserved='seoz',numerical_checks=numeric_checks(),
        roundtrips=True,cli_parse=True,source_meaning_equivalence_proven=False,
        adds_new_text_coverage=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args(argv)
    report=build_report()
    if args.verify_only:assert load(REPORT)==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('143 symbol locations reconciled: 83 in later draft, 60 independent candidates; 175 statements preserved')


if __name__=='__main__':main()
