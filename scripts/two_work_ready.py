"""Bounded integration prerequisites for project_work check, not semantic review."""
from scripts.two_work_run import checked_pins,BASE
from scripts.two_work_inventory import read,sha
from scripts.two_work_fastparse import parse_source
from noema.constructed import format_graph


def build_report():
    pins=checked_pins();counts={}
    for work in ('kant','einstein'):
        d=read(BASE+work+'.json');toc=read(BASE+work+'-toc.json');catalog=read(BASE+work+'-catalog.json')
        if parse_source(format_graph(d))!=d:raise ValueError('Native publication export changes syntax')
        counts[work]=dict(declarations=len(d['declarations']),statements=len(d['statements']),units=len(toc['units']),
                          main_statements=toc['main_statements'],native_export_exact=True)
        for declaration in d['declarations']:
            if declaration['kind']=='primitive' and not catalog[declaration['name']].get('contract'):raise ValueError('Missing primitive contract')
    for path in ('scripts/two_work_ready.py','tests/test_two_work_batch.py','tests/test_two_work_edition.py','tests/test_two_work_publish.py'):
        pins[path]=sha(path)
    return dict(schema='noema-two-work-ready-1',source_sha256=pins,works=counts,
                status='Prepared; full ink decoding remains pending. Existing semantic judgments are unchanged.')
