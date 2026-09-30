"""Recheck the original law model without changing its scope or its step budget."""
import argparse
from copy import deepcopy
import hashlib
import json

from noema.finite_semantics import evaluate_document
from scripts.check_law_invariance import DOMAIN, base_facts, source_document, source_model
from scripts.compose_event_time import ROOT

REPORT=ROOT/'reports/expression-memoization-v1.json'
BUDGET=15_000_000


def expected_principle(facts):
    pairs={(a,b) for a in facts['frames'] for b in facts['frames'] if a!=b
           and (a,b,'text') in facts['orientation'] and (a,b,'text') in facts['velocity']}
    if not pairs or not facts['laws'] or not facts['histories']:return False
    if any((h,'system','text') not in facts['systems'] for h in facts['histories']):return False
    for a,b in pairs:
        if (a,b,'text') not in facts['complete']:return False
        for history in facts['histories']:
            left={r for h,f,r,c in facts['representations'] if (h,f,c)==(history,a,'text')}
            right={r for h,f,r,c in facts['representations'] if (h,f,c)==(history,b,'text')}
            if not left or not right:return False
            for law in facts['laws']:
                left_values={(law,r,'text') in facts['allowed'] for r in left}
                right_values={(law,r,'text') in facts['allowed'] for r in right}
                if left_values!=right_values or len(left_values)!=1:return False
    return True


def model_cases():
    base=base_facts()
    cases={'original_two_laws_two_histories':base}
    changed=deepcopy(base);changed['allowed'].remove(('lawtwo','righttwo','text'))
    cases['second_law_second_history_disagrees']=changed
    changed=deepcopy(base);changed['representations'].remove(('historytwo','second','righttwo','text'))
    cases['second_history_missing_representation']=changed
    changed=deepcopy(base);changed['complete'].remove(('second','first','text'))
    cases['reverse_scope_incomplete']=changed
    changed=deepcopy(base);changed['laws']=set()
    cases['empty_laws']=changed
    changed=deepcopy(base);changed['velocity']=set()
    cases['no_eligible_pair']=changed
    changed=deepcopy(base);changed['frames'].add('third')
    for key in ('orientation','velocity','complete'):
        changed[key].update({('first','third','text'),('third','first','text')})
    changed['representations'].update({('historyone','third','rightone','text'),('historytwo','third','extra','text')})
    cases['additional_frame_disagrees']=changed
    return cases


def build_report():
    doc=source_document('q[t[k saw[]][k ri[]]].')
    try:
        evaluate_document(doc,individuals=DOMAIN,situations=('text',),primitives=source_model(doc,base_facts()),
            max_steps=BUDGET,memoize_definitions=True,memoize_expressions=False)
    except ValueError as error:
        if str(error)!='Finite interpretation step budget exceeded':raise
    else:
        raise ValueError('The recorded baseline no longer exhausts this budget; review the performance claim')
    cases={}
    for name,facts in model_cases().items():
        actual=evaluate_document(doc,individuals=DOMAIN,situations=('text',),primitives=source_model(doc,facts),
            max_steps=BUDGET,memoize_definitions=True,memoize_expressions=True)[0]['value']
        expected=expected_principle(facts)
        if actual!=expected:raise ValueError('Cached full principle differs from independent set comparison: '+name)
        cases[name]={'actual':actual,'expected':expected}
    files=['noema/finite_semantics.py','scripts/check_expression_memoization.py','scripts/check_law_invariance.py',
        'tests/test_expression_memoization.py','examples/v014/einstein-law-invariance.noema']
    return {'status':'full_original_finite_model_evaluated_with_expression_memoization',
        'individual_domain':list(DOMAIN),'step_budget':BUDGET,
        'baseline':{'memoize_definitions':True,'memoize_expressions':False,'status':'step_budget_exceeded'},
        'optimized':{'memoize_definitions':True,'memoize_expressions':True,'cases':cases},
        'source_semantics_changed':False,'arbitrary_physical_systems_verified':False,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Expression memoization report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Original 13-object model and six countermodels checked at the unchanged budget')


if __name__=='__main__':main()
