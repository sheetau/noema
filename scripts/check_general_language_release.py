"""Audit the general-language package and carry unchanged work evidence forward.

No historical model suite is rerun. Retained judgments are checked by content;
new finite diagnostics, syntax and visible decoding keep separate boundaries.
"""
import json
from collections import Counter
from scripts.two_work_inventory import ROOT, read, sha
from scripts.two_work_run import semantic_inputs
from scripts.long_run import LongRun, atomic_json
from scripts.general_language import entries, dependencies
from scripts.two_work_assemble import renamed
from scripts.two_work_fastparse import parse_source
from noema.constructed_discourse import normalize_document

RUN='.noema-project/runs/general-language-final-v1'


def prepare():
    paths=['data/general-language-release-v1.json','data/general-language-catalog-v1.json','data/work-state.json',
           'docs/general-language-v1.md','scripts/check_general_language_release.py','scripts/general_language.py',
           'scripts/general_language_publish.py','scripts/general_language_cases.py','scripts/two_work_run.py','scripts/long_run.py',
           'reports/general-language-review-v2.json','reports/general-pragmatics-v1.json','reports/general-probability-v1.json',
           'reports/general-scope-contrasts-v1.json','output/general-language-v1/report.json',
           'output/general-language-catalog-ink-v1/report.json','output/general-language-v1/publication.json',
           'output/general-language-v1/index.html','output/general-language-v1/link-check.json',
           'output/general-language-v1/browser-check.json','reports/written-progress-v433.json',
           '.noema-project/eighth-pin-snapshot-full-audit-v1-process.log']
    pins={p:sha(p) for p in paths}; actual={}
    def digest(path):
        if path not in actual:actual[path]=sha(path)
        return actual[path]
    def check_sources(report, *, selection_change=False):
        changed=[p for p,h in report['source_sha256'].items() if digest(p)!=h]
        if changed and not(selection_change and changed==['data/work-state.json']):
            raise ValueError('Changed evidence inputs: '+str(changed))
        return changed
    with LongRun(ROOT/RUN,dict(source_sha256=pins),resume=(ROOT/RUN).exists()) as run:
        baseline=semantic_inputs(run)
        if not baseline['unchanged']:raise ValueError('Preserved work evidence changed')
        catalog=read('data/general-language-catalog-v1.json');check_sources(catalog)
        report_paths={r['evidence'] for r in read('reports/general-language-review-v2.json')['cases'] if r['evidence']}
        report_paths|={'reports/general-probability-v1.json','reports/general-scope-contrasts-v1.json'}
        evidence=[]
        for i,path in enumerate(sorted(report_paths)):
            run.emit('progress',stage='Retained meaning diagnostics',completed=i,total=len(report_paths))
            changed=check_sources(read(path),selection_change=True)
            row=dict(report=path,sha256=digest(path),changed_inputs=changed,
                carry='fixed-input diagnostics only; active-manuscript selection is not carried' if changed else 'identical inputs')
            evidence.append(run.step('evidence:'+path,row,lambda row=row:row))
        for path,kind in [('output/general-language-catalog-ink-v1','catalog'),('output/general-language-v1','constructions')]:
            report=read(path+'/report.json');check_sources(report)
            assert report['validation_success'] and report['counts'].get('passed')==len(report['records'])
            for i,row in enumerate(report['records']):
                if i%128==0:run.emit('progress',stage='Ink hashes: '+kind,completed=i,total=len(report['records']))
                if digest(path+'/ink/'+row['cache_key']+'.svg')!=row['svg_sha256']:raise ValueError('Changed ink')
        mapping={n:r['symbol'] for n,r in entries().items()}
        expected=normalize_document(renamed(dict(schema_version='0.16',lexicon_version='0.16',declarations=dependencies(entries()),statements=[]),mapping))
        ink=read('output/general-language-catalog-ink-v1/report.json')
        assert [r['native'] for r in ink['records']]==expected['declarations']
        from scripts import general_probability, general_pragmatics, check_general_probability, check_general_scope
        for path,builder in [('examples/v016/general-probability-v1.noema',general_probability.composed),
                             ('examples/v016/general-pragmatics-v1.noema',general_pragmatics.composed),
                             (check_general_probability.LIBRARY,check_general_probability.document),
                             (check_general_scope.LIBRARY,check_general_scope.document)]:
            assert parse_source((ROOT/path).read_text(encoding='utf-8'))==builder(),path
            pins[path]=digest(path)
        link=read('output/general-language-v1/link-check.json');browser=read('output/general-language-v1/browser-check.json')
        assert not link['issues'] and browser['filtered']=='9項目' and not browser['initial']['overflow']
        assert not browser['mobile']['overflow'] and not browser['brokenLoadedImages'] and browser['linkedEntryRevealed']
        output=dict(schema='noema-general-language-completion-1',scope='Common vocabulary, compositional rules and specification organization',
            catalog=catalog['counts'],expression_domains=36,new_definitions=19,new_primitive_declarations=0,
            native_syntax='36 mapped documents and four exact newly generated sources',
            pragmatic_binding_slots=123,probability_contrast_values=11,scope_models=4,
            visible=dict(catalog=1909,constructions=148,inherited_catalog=sum(r['decoding']=='inherited-unchanged-content' for r in ink['records']),
                         fresh_catalog=sum(r['decoding']!='inherited-unchanged-content' for r in ink['records'])),
            evidence=evidence,preserved_works=baseline,links=link,browser=browser,
            source_sha256=pins,limits=['Finite contrasts are not a theorem covering every human meaning.',
                'Application sketches are not independently reviewed translations.',
                'Primitive meanings and contextual interpretation relations remain explicit inputs.',
                'Existing source judgments are retained; model tests and ink checks do not create new source judgments.'])
        # The source list is small; retain prior reports rather than copying all
        # their historical evidence into another aggregate.
        for p,h in pins.items():
            if sha(p)!=h:raise ValueError('Input changed during audit: '+p)
        atomic_json(ROOT/RUN/'result.json',output)
        run.emit('progress',stage='Complete',completed=1,total=1)


def build_report():
    return read(RUN+'/result.json')
