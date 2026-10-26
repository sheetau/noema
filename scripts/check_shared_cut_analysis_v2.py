"""Add the legacy composition-basis dependency without replacing v1 evidence."""
import json
from scripts.shared_cut_analysis import ROOT,require,digest
from scripts.check_shared_cut_analysis import prepare,build_report as previous_report


def build_report():
    prior='reports/shared-cut-analysis-v1.json'
    report=previous_report()
    require(report==json.loads((ROOT/prior).read_text(encoding='utf-8')),'Original analysis evidence changed')
    report['schema']='noema-shared-cut-analysis-evidence-2'
    report['previous_evidence']=prior
    report['dependency_completion']={
        'added':'data/real-products-basis-v1.json',
        'reason':'compose_limits loads the legacy basis while constructing the rational analogue test inputs',
        'definitions_or_judgments_changed':False}
    for path in (prior,'data/real-products-basis-v1.json','scripts/check_shared_cut_analysis_v2.py',
                 'docs/shared-cut-analysis-evidence-v2.md'):
        report['source_sha256'][path]=digest((ROOT/path).read_bytes())
    report['source_sha256']=dict(sorted(report['source_sha256'].items()))
    return report
