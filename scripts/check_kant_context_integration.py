"""Bind the completed structural trial to its actual published artifacts."""
import hashlib
import json
from pathlib import Path
import sqlite3

from scripts.check_kant_page_public_context import build_report as structural_report

ROOT=Path(__file__).resolve().parents[1]
RUN='.noema-project/runs/kant-public-context-20261103-c'
OUT='output/kant-public-context'


def build_report():
    report=structural_report()
    status=json.loads((ROOT/RUN/'status.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/RUN/'manifest.json').read_text(encoding='utf-8'))
    if status['status']!='complete' or manifest['source_sha256']!=report['source_sha256']:
        raise ValueError('Structural trial is incomplete or has different inputs')
    checked={}
    with sqlite3.connect((ROOT/RUN/'steps.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        for raw,stamp in db.execute('SELECT value,sha FROM steps'):
            if hashlib.sha256(raw.encode('utf-8')).hexdigest()!=stamp:
                raise ValueError('Damaged structural checkpoint')
            row=json.loads(raw)
            checked[row['statement']]=row
    if len(checked)!=report['total'] or report['exact_public_roundtrips']!=40:
        raise ValueError('Full selected page has not been structurally decoded')
    for row in report['cases']:
        full=checked[row['statement']]
        if row!={k:v for k,v in full.items() if k!='svg'}:
            raise ValueError('Published report differs from its completed step')
        name=OUT+'/statement-'+str(row['statement'])+'.svg'
        raw=(ROOT/name).read_bytes()
        if raw!=full['svg'].encode('utf-8'):
            raise ValueError('Published SVG changed after its checked step')
        row['svg_sha256']=hashlib.sha256(raw).hexdigest()
    dictionary=json.loads((ROOT/OUT/'dictionary.json').read_text(encoding='utf-8'))
    if dictionary['native']['statements'] or dictionary['fingerprint']!=report['lexical_context']:
        raise ValueError('Dictionary contains source assertions or changed context')
    additional={
        'scripts/check_kant_context_integration.py',
        'tests/test_kant_public_fragment.py','tests/test_kant_shared_argument.py',
        'tests/test_kant_circle_pair_correction.py','tests/test_kant_public_words.py',
        'scripts/check_kant_public_fragment.py','scripts/check_kant_shared_argument.py',
        'scripts/check_kant_public_words.py',
        OUT+'/dictionary.json',OUT+'/structural-report.json',RUN+'/manifest.json'}
    report['source_sha256'].update({name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                   for name in sorted(additional)})
    report['dictionary_has_source_assertions']=False
    return report
